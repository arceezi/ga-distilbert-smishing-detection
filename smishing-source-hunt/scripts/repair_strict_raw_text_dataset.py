"""Repair or exclude rows that fail strict raw text quality."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

from audit_strict_raw_text_quality import ANGLE_PLACEHOLDER_RE, classify_row, sms_likeness
from classify_raw_text_availability import is_rejected, is_smishing_label
from verify_and_add_raw_clean_text_columns import clean_cell, clean_message


ROOT = Path(__file__).resolve().parents[1]
RAW_QUALITY_DIR = ROOT / "data" / "organized" / "raw_quality"
INPUT_DATASET = ROOT / "data" / "organized" / "raw_recovery" / "combined_public_thesis_sources_deduped_raw_required.csv"
VIOLATIONS_INPUT = RAW_QUALITY_DIR / "raw_placeholder_violations.csv"
CANDIDATE_INPUT = ROOT / "data" / "organized" / "raw_recovery" / "collected_smishing_candidates_raw_classified.csv"

STRICT_OUTPUT = RAW_QUALITY_DIR / "combined_public_thesis_sources_deduped_strict_raw.csv"
REMOVED_OUTPUT = RAW_QUALITY_DIR / "strict_raw_removed_archive.csv"
REPLACEMENT_LOG_OUTPUT = RAW_QUALITY_DIR / "strict_raw_replacement_log.csv"
REPORT_PATH = ROOT / "reports" / "strict_raw_text_repair_report.md"

REPAIR_COLUMNS = [
    "raw_placeholder_detected",
    "raw_placeholder_count",
    "raw_placeholder_types",
    "raw_quality_status",
    "raw_quality_notes",
    "raw_length",
    "token_count",
    "long_message_flag",
    "sms_likeness_status",
    "repair_status",
    "final_strict_raw_eligible",
    "exclusion_reason",
]

LOG_COLUMNS = [
    "old_unified_id",
    "old_source_name",
    "old_dataset_name",
    "old_normalized_label",
    "old_message_raw",
    "raw_placeholder_types",
    "replacement_candidate_id",
    "replacement_source_name",
    "replacement_dataset_name",
    "replacement_message_raw",
    "replacement_method",
    "duplicate_check_status",
    "repair_status",
    "notes",
]


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(dict.fromkeys(fieldnames)), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalized_key(text: str) -> str:
    cleaned = clean_message(text or "").lower()
    return " ".join(cleaned.replace("\n", " ").split())


def strict_raw_ok(text: str) -> bool:
    text = clean_cell(text)
    return bool(text) and len(text) >= 5 and not ANGLE_PLACEHOLDER_RE.search(text)


def candidate_usable(candidate: dict[str, str]) -> bool:
    if candidate.get("candidate_raw_text_available") != "True":
        return False
    if candidate.get("candidate_raw_text_status") not in {"original_looking_raw", "original_unredacted"}:
        return False
    if not is_smishing_label(candidate):
        return False
    if is_rejected(candidate):
        return False
    raw = clean_cell(candidate.get("candidate_raw_text"))
    if not strict_raw_ok(raw):
        return False
    if sms_likeness(raw) == "possible_report_or_article_text":
        return False
    if not clean_cell(candidate.get("candidate_clean_text")):
        return False
    if not (clean_cell(candidate.get("source_name")) or clean_cell(candidate.get("dataset_name"))):
        return False
    return True


def candidate_sort_key(candidate: dict[str, str]) -> tuple:
    return (-int(candidate.get("candidate_raw_quality_score") or 0), clean_cell(candidate.get("id")))


def build_candidate_indexes(candidates: list[dict[str, str]]) -> tuple[dict[str, dict[str, str]], dict[str, list[dict[str, str]]]]:
    by_id: dict[str, dict[str, str]] = {}
    by_clean: dict[str, list[dict[str, str]]] = defaultdict(list)
    for candidate in candidates:
        if not candidate_usable(candidate):
            continue
        candidate_id = clean_cell(candidate.get("id"))
        if candidate_id:
            by_id[candidate_id] = candidate
        key = normalized_key(candidate.get("candidate_clean_text", ""))
        if key:
            by_clean[key].append(candidate)
    for key in by_clean:
        by_clean[key].sort(key=candidate_sort_key)
    return by_id, by_clean


def build_replacement_pools(candidates: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    pools: dict[str, list[dict[str, str]]] = defaultdict(list)
    for candidate in candidates:
        if not candidate_usable(candidate):
            continue
        source = clean_cell(candidate.get("source_name")) or clean_cell(candidate.get("dataset_name")) or "unknown_source"
        pools[source].append(candidate)
    for source in pools:
        pools[source].sort(key=candidate_sort_key)
    return dict(pools)


def choose_replacement(
    pools: dict[str, list[dict[str, str]]],
    source_counts: Counter[str],
    category_counts: Counter[str],
    selected_ids: set[str],
    accepted_raw_keys: set[str],
    accepted_clean_keys: set[str],
) -> tuple[dict[str, str] | None, int]:
    duplicate_skips = 0
    while True:
        available = [source for source, pool in pools.items() if pool]
        if not available:
            return None, duplicate_skips
        available.sort(
            key=lambda source: (
                source_counts[source],
                category_counts[clean_cell(pools[source][0].get("scam_category"))],
                -int(pools[source][0].get("candidate_raw_quality_score") or 0),
                source,
            )
        )
        for source in available:
            pool = pools[source]
            while pool:
                candidate = pool.pop(0)
                candidate_id = clean_cell(candidate.get("id"))
                raw_key = normalized_key(candidate.get("candidate_raw_text", ""))
                clean_key = normalized_key(candidate.get("candidate_clean_text", ""))
                if candidate_id in selected_ids or raw_key in accepted_raw_keys or clean_key in accepted_clean_keys:
                    duplicate_skips += 1
                    continue
                return candidate, duplicate_skips


def audit_for_final(row: dict[str, str], repair_status: str, eligible: bool, exclusion_reason: str = "") -> dict[str, str]:
    audited = classify_row(row)
    audited["repair_status"] = repair_status
    audited["final_strict_raw_eligible"] = "True" if eligible else "False"
    audited["exclusion_reason"] = exclusion_reason
    if eligible and strict_raw_ok(audited.get("message_raw", "")):
        original_status = audited["raw_quality_status"]
        audited["raw_quality_status"] = "pass_raw"
        audited["raw_quality_notes"] = (
            f"Strict raw accepted after repair validation; original audit status={original_status}; "
            f"sms_likeness_status={audited.get('sms_likeness_status', '')}."
        )
    return audited


def make_replacement_row(old: dict[str, str], candidate: dict[str, str], repair_status: str, method: str) -> dict[str, str]:
    row = dict(old)
    candidate_id = clean_cell(candidate.get("id"))
    raw = clean_cell(candidate.get("candidate_raw_text"))
    clean = clean_cell(candidate.get("candidate_clean_text")) or clean_message(raw)
    row["unified_id"] = old.get("unified_id", "") if repair_status == "recovered_same_message_raw" else f"strict_replacement_{candidate_id}"
    row["source_name"] = clean_cell(candidate.get("source_name")) or old.get("source_name", "")
    row["dataset_name"] = clean_cell(candidate.get("dataset_name")) or old.get("dataset_name", "")
    row["source_group"] = old.get("source_group", "") if repair_status == "recovered_same_message_raw" else "strict_raw_replacement_91k_pool"
    row["source_row_id"] = candidate_id
    row["message_raw"] = raw
    row["message_clean"] = clean
    row["source_label"] = clean_cell(candidate.get("original_label")) or clean_cell(candidate.get("label")) or old.get("source_label", "")
    row["normalized_label"] = "smishing"
    row["label_status"] = "accepted"
    row["review_status"] = clean_cell(candidate.get("review_status")) or old.get("review_status", "")
    row["raw_text_available"] = "True"
    row["raw_text_status"] = "original_unredacted"
    row["raw_lookup_status"] = "recovered_strict_raw" if repair_status == "recovered_same_message_raw" else "replaced_from_91k_pool"
    row["raw_lookup_notes"] = (
        f"Strict raw repair via {method}; candidate_id={candidate_id}."
        if repair_status == "recovered_same_message_raw"
        else "Placeholder/anonymized raw row replaced by strict raw-available smishing candidate from 91k pool."
    )
    row["replacement_candidate_id"] = candidate_id
    row["original_replaced_unified_id"] = old.get("unified_id", "")
    return row


def make_log(old: dict[str, str], candidate: dict[str, str] | None, method: str, duplicate_status: str, repair_status: str, notes: str) -> dict[str, str]:
    return {
        "old_unified_id": old.get("unified_id", ""),
        "old_source_name": old.get("source_name", ""),
        "old_dataset_name": old.get("dataset_name", ""),
        "old_normalized_label": old.get("normalized_label", ""),
        "old_message_raw": old.get("message_raw", ""),
        "raw_placeholder_types": old.get("raw_placeholder_types", ""),
        "replacement_candidate_id": clean_cell(candidate.get("id")) if candidate else "",
        "replacement_source_name": clean_cell(candidate.get("source_name")) if candidate else "",
        "replacement_dataset_name": clean_cell(candidate.get("dataset_name")) if candidate else "",
        "replacement_message_raw": clean_cell(candidate.get("candidate_raw_text")) if candidate else "",
        "replacement_method": method,
        "duplicate_check_status": duplicate_status,
        "repair_status": repair_status,
        "notes": notes,
    }


def validation_checks(rows: list[dict[str, str]], removed: list[dict[str, str]], input_count: int) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    def add(name: str, ok: bool, details: str) -> None:
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "details": details})

    raw_keys = [normalized_key(row.get("message_raw", "")) for row in rows]
    clean_keys = [normalized_key(row.get("message_clean", "")) for row in rows]
    add("No empty message_raw", all(clean_cell(row.get("message_raw")) for row in rows), str(sum(not clean_cell(row.get("message_raw")) for row in rows)))
    add("No raw placeholders", all(not ANGLE_PLACEHOLDER_RE.search(row.get("message_raw", "")) for row in rows), str(sum(bool(ANGLE_PLACEHOLDER_RE.search(row.get("message_raw", ""))) for row in rows)))
    add("No raw_text_available=False", all(row.get("raw_text_available") == "True" for row in rows), str(sum(row.get("raw_text_available") != "True" for row in rows)))
    add("No already_redacted status", all(row.get("raw_text_status") != "already_redacted" for row in rows), str(sum(row.get("raw_text_status") == "already_redacted" for row in rows)))
    add("All included rows pass strict raw quality", all(row.get("raw_quality_status") == "pass_raw" for row in rows), str(sum(row.get("raw_quality_status") != "pass_raw" for row in rows)))
    add("message_clean exists", all(clean_cell(row.get("message_clean")) for row in rows), str(sum(not clean_cell(row.get("message_clean")) for row in rows)))
    add("No duplicate raw keys", len(raw_keys) == len(set(raw_keys)), f"duplicates={len(raw_keys) - len(set(raw_keys))}")
    add("No duplicate clean keys", len(clean_keys) == len(set(clean_keys)), f"duplicates={len(clean_keys) - len(set(clean_keys))}")
    add("No ham rows replaced with smishing", all(not (row.get("normalized_label") == "ham" and row.get("repair_status") == "replaced_with_strict_raw_candidate") for row in rows), "checked")
    add("Removed rows archived", len(rows) + len(removed) <= input_count and all(row.get("final_strict_raw_eligible") == "False" for row in removed), f"archived={len(removed)}")
    return checks


def markdown_table(rows: list[dict[str, str]], columns: list[str], limit: int | None = None) -> list[str]:
    rows = rows[:limit] if limit else rows
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return lines


def counter_rows(counter: Counter[str], name: str) -> list[dict[str, str]]:
    return [{name: key or "(blank)", "rows": str(value)} for key, value in counter.most_common()]


def write_report(
    *,
    input_rows: list[dict[str, str]],
    violation_rows: list[dict[str, str]],
    final_rows: list[dict[str, str]],
    removed_rows: list[dict[str, str]],
    recovered_count: int,
    replaced_count: int,
    duplicate_skips: int,
    checks: list[dict[str, str]],
) -> None:
    start_counts = Counter(row.get("normalized_label", "") for row in input_rows)
    final_counts = Counter(row.get("normalized_label", "") for row in final_rows)
    placeholder_counts: Counter[str] = Counter()
    for row in violation_rows:
        for token in row.get("raw_placeholder_types", "").split(";"):
            if token:
                placeholder_counts[token] += 1
    long_rows = [audit_for_final(row, "", True) for row in input_rows if len(clean_cell(row.get("message_raw"))) > 320]
    possible_report_removed = sum(row.get("exclusion_reason") == "possible_report_or_article_text" for row in removed_rows)
    long_kept = sum(row.get("long_message_flag") == "True" for row in final_rows)
    removed_counts = Counter(row.get("normalized_label", "") for row in removed_rows)
    source_counts = Counter(row.get("source_name", "") for row in input_rows)
    final_source_counts = Counter(row.get("source_name", "") for row in final_rows)

    ratio = "n/a"
    if final_counts.get("ham", 0):
        ratio = f"{final_counts.get('smishing', 0) / final_counts.get('ham', 0):.2f}:1 smishing:ham"

    lines = [
        "# Strict Raw Text Repair Report",
        "",
        "## 1. Purpose",
        "",
        "This step ensures the raw-required dataset truly contains original-looking raw messages. Any source-anonymized angle-bracket token in `message_raw` is treated as not fully raw.",
        "",
        "## 2. Starting Dataset",
        "",
        f"- Total rows: {len(input_rows):,}",
        f"- Ham count: {start_counts.get('ham', 0):,}",
        f"- Smishing count: {start_counts.get('smishing', 0):,}",
        "",
        "### Starting Source Counts",
        "",
        *markdown_table(counter_rows(source_counts, "source_name"), ["source_name", "rows"], limit=20),
        "",
        "## 3. Raw Placeholder Violations",
        "",
        f"- Total rows with placeholders or strict raw failures: {len(violation_rows):,}",
        "",
        "### Placeholder Type Counts",
        "",
        *markdown_table(counter_rows(placeholder_counts, "placeholder_type"), ["placeholder_type", "rows"]),
        "",
        "### By Source",
        "",
        *markdown_table(counter_rows(Counter(row.get("source_name", "") for row in violation_rows), "source_name"), ["source_name", "rows"]),
        "",
        "### By Dataset",
        "",
        *markdown_table(counter_rows(Counter(row.get("dataset_name", "") for row in violation_rows), "dataset_name"), ["dataset_name", "rows"]),
        "",
        "### By Label",
        "",
        *markdown_table(counter_rows(Counter(row.get("normalized_label", "") for row in violation_rows), "normalized_label"), ["normalized_label", "rows"]),
        "",
        "## 4. Repair Results",
        "",
        f"- Recovered same-message raw count: {recovered_count:,}",
        f"- Replaced with strict raw candidate count: {replaced_count:,}",
        f"- Removed/no strict raw available count: {len(removed_rows):,}",
        f"- Ham rows removed: {removed_counts.get('ham', 0):,}",
        f"- Smishing rows removed/replaced: removed {removed_counts.get('smishing', 0):,}; replaced {replaced_count:,}",
        f"- Duplicates skipped: {duplicate_skips:,}",
        "",
        "## 5. Long Message Review",
        "",
        f"- Number of rows > 320 characters: {len(long_rows):,}",
        f"- Kept as likely SMS/multipart SMS or review-allowed SMS-like raw: {long_kept:,}",
        f"- Marked possible report/article text: {sum(row.get('sms_likeness_status') == 'possible_report_or_article_text' for row in long_rows):,}",
        f"- Archived/removed due to non-SMS-like format: {possible_report_removed:,}",
        "",
        "## 6. Final Strict Raw Dataset",
        "",
        f"- Total rows: {len(final_rows):,}",
        f"- Ham count: {final_counts.get('ham', 0):,}",
        f"- Smishing count: {final_counts.get('smishing', 0):,}",
        f"- Class ratio: {ratio}",
        f"- Row count compared to previous raw-required dataset: {len(final_rows):,} vs {len(input_rows):,} ({len(final_rows) - len(input_rows):+,})",
        "",
        "### Final Source Distribution",
        "",
        *markdown_table(counter_rows(final_source_counts, "source_name"), ["source_name", "rows"], limit=20),
        "",
        "### Validation",
        "",
        *markdown_table(checks, ["check", "status", "details"]),
        "",
        "## 7. Thesis Methodology Note",
        "",
        "Rows with anonymized or placeholder-containing raw text were not treated as fully raw. The workflow attempted to recover exact raw versions from source archives and the 91k candidate pool. When exact recovery was unavailable, smishing rows were replaced only with deduplicated raw-available smishing candidates from the same candidate pool. Rows without acceptable raw text were archived and excluded. No placeholders were reversed, reconstructed, or invented.",
        "",
        "## 8. Files Generated",
        "",
        f"- `{STRICT_OUTPUT.relative_to(ROOT)}`",
        f"- `{REMOVED_OUTPUT.relative_to(ROOT)}`",
        f"- `{REPLACEMENT_LOG_OUTPUT.relative_to(ROOT)}`",
        f"- `{REPORT_PATH.relative_to(ROOT)}`",
        "",
        "## 9. Recommended Next Steps",
        "",
        "- Build the balanced model-ready dataset later from the strict raw output.",
        "- Clean or standardize `message_clean` in a separate task.",
        "- Add manually curated ham later if needed.",
        "- Review the long-message audit file manually before final thesis freezing.",
        "",
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    input_rows, input_fieldnames = read_csv(INPUT_DATASET)
    violation_rows, _violation_fieldnames = read_csv(VIOLATIONS_INPUT)
    candidates, _candidate_fieldnames = read_csv(CANDIDATE_INPUT)
    violation_ids = {row.get("unified_id", "") for row in violation_rows}
    by_id, by_clean = build_candidate_indexes(candidates)
    pools = build_replacement_pools(candidates)

    final_rows: list[dict[str, str]] = []
    removed_rows: list[dict[str, str]] = []
    logs: list[dict[str, str]] = []
    accepted_raw_keys: set[str] = set()
    accepted_clean_keys: set[str] = set()
    selected_candidate_ids: set[str] = set()
    source_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    recovered_count = 0
    replaced_count = 0
    duplicate_skips = 0

    for original in input_rows:
        audited_original = audit_for_final(original, "kept_strict_raw", True)
        label = clean_cell(original.get("normalized_label"))
        raw_key = normalized_key(original.get("message_raw", ""))
        clean_key = normalized_key(original.get("message_clean", ""))
        must_repair = original.get("unified_id", "") in violation_ids
        report_like_long = audited_original.get("sms_likeness_status") == "possible_report_or_article_text"

        if not must_repair and not report_like_long:
            if raw_key in accepted_raw_keys or clean_key in accepted_clean_keys:
                archived = audit_for_final(original, "removed_duplicate_existing_row", False, "duplicate_against_strict_raw_dataset")
                removed_rows.append(archived)
                duplicate_skips += 1
                continue
            final_rows.append(audited_original)
            accepted_raw_keys.add(raw_key)
            accepted_clean_keys.add(clean_key)
            continue

        if report_like_long and not must_repair:
            archived = audit_for_final(original, "removed_non_sms_like_long_message", False, "possible_report_or_article_text")
            removed_rows.append(archived)
            logs.append(make_log(archived, None, "long_message_sms_likeness", "not_applicable", "removed_no_strict_raw_available", "Long raw text looked like report/article text."))
            continue

        replacement: dict[str, str] | None = None
        method = ""
        source_row_id = clean_cell(original.get("source_row_id"))
        if source_row_id in by_id:
            candidate = by_id[source_row_id]
            if clean_cell(candidate.get("label")).lower() == label or label == "smishing":
                replacement = candidate
                method = "stable_source_row_id"
        if not replacement:
            key = normalized_key(original.get("message_clean", ""))
            for candidate in by_clean.get(key, []):
                if clean_cell(candidate.get("id")) not in selected_candidate_ids:
                    replacement = candidate
                    method = "normalized_message_clean"
                    break

        if replacement:
            repaired = make_replacement_row(original, replacement, "recovered_same_message_raw", method)
            repaired_audited = audit_for_final(repaired, "recovered_same_message_raw", True)
            repaired_raw_key = normalized_key(repaired_audited.get("message_raw", ""))
            repaired_clean_key = normalized_key(repaired_audited.get("message_clean", ""))
            if repaired_raw_key not in accepted_raw_keys and repaired_clean_key not in accepted_clean_keys and strict_raw_ok(repaired_audited.get("message_raw", "")):
                final_rows.append(repaired_audited)
                accepted_raw_keys.add(repaired_raw_key)
                accepted_clean_keys.add(repaired_clean_key)
                selected_candidate_ids.add(clean_cell(replacement.get("id")))
                recovered_count += 1
                logs.append(make_log(original, replacement, method, "accepted", "recovered_same_message_raw", repaired_audited.get("raw_lookup_notes", "")))
                continue
            duplicate_skips += 1
            logs.append(make_log(original, replacement, method, "exact_duplicate_rejected", "skipped_duplicate", "Same-message candidate duplicated an accepted strict raw row."))

        if label == "smishing":
            candidate, skipped = choose_replacement(pools, source_counts, category_counts, selected_candidate_ids, accepted_raw_keys, accepted_clean_keys)
            duplicate_skips += skipped
            if candidate:
                replaced = make_replacement_row(original, candidate, "replaced_with_strict_raw_candidate", "replacement_pool")
                replaced_audited = audit_for_final(replaced, "replaced_with_strict_raw_candidate", True)
                final_rows.append(replaced_audited)
                accepted_raw_keys.add(normalized_key(replaced_audited.get("message_raw", "")))
                accepted_clean_keys.add(normalized_key(replaced_audited.get("message_clean", "")))
                selected_candidate_ids.add(clean_cell(candidate.get("id")))
                source = clean_cell(candidate.get("source_name")) or clean_cell(candidate.get("dataset_name"))
                source_counts[source] += 1
                category_counts[clean_cell(candidate.get("scam_category"))] += 1
                replaced_count += 1
                logs.append(make_log(original, candidate, "replacement_pool", "accepted", "replaced_with_strict_raw_candidate", replaced_audited.get("raw_lookup_notes", "")))
                continue

        archived = audit_for_final(original, "removed_no_strict_raw_available", False, "raw_contains_placeholder_or_anonymized_token")
        removed_rows.append(archived)
        logs.append(make_log(archived, None, "none", "no_candidate_available", "removed_no_strict_raw_available", "No acceptable strict raw same-message recovery or label-equivalent replacement was available."))

    final_fieldnames = list(dict.fromkeys(input_fieldnames + REPAIR_COLUMNS))
    removed_fieldnames = list(dict.fromkeys(input_fieldnames + REPAIR_COLUMNS))
    write_csv(STRICT_OUTPUT, final_rows, final_fieldnames)
    write_csv(REMOVED_OUTPUT, removed_rows, removed_fieldnames)
    write_csv(REPLACEMENT_LOG_OUTPUT, logs, LOG_COLUMNS)

    checks = validation_checks(final_rows, removed_rows, len(input_rows))
    write_report(
        input_rows=input_rows,
        violation_rows=violation_rows,
        final_rows=final_rows,
        removed_rows=removed_rows,
        recovered_count=recovered_count,
        replaced_count=replaced_count,
        duplicate_skips=duplicate_skips,
        checks=checks,
    )

    final_counts = Counter(row.get("normalized_label", "") for row in final_rows)
    long_flagged = sum(len(clean_cell(row.get("message_raw"))) > 320 for row in input_rows)
    long_removed = sum(row.get("exclusion_reason") == "possible_report_or_article_text" for row in removed_rows)

    print(f"Input dataset path: {INPUT_DATASET.relative_to(ROOT)}")
    print(f"Rows inspected: {len(input_rows)}")
    print(f"Raw placeholder violations found: {sum(row.get('raw_quality_status') == 'fail_placeholder_anonymized' for row in violation_rows)}")
    print(f"Same-message raw recoveries: {recovered_count}")
    print(f"Replacements made: {replaced_count}")
    print(f"Rows removed: {len(removed_rows)}")
    print(f"Long messages flagged: {long_flagged}")
    print(f"Long messages removed as non-SMS-like: {long_removed}")
    print(f"Final strict raw dataset row count: {len(final_rows)}")
    print(f"Final ham/smishing counts: ham={final_counts.get('ham', 0)}; smishing={final_counts.get('smishing', 0)}")
    print("Output paths:")
    for path in [STRICT_OUTPUT, REMOVED_OUTPUT, REPLACEMENT_LOG_OUTPUT]:
        print(f"- {path.relative_to(ROOT)}")
    print("Report paths:")
    print(f"- {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
