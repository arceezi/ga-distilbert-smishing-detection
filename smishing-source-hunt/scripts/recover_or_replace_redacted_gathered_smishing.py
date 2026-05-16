"""Recover or replace redacted-only gathered smishing rows with raw-available candidates."""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

from classify_raw_text_availability import is_rejected, is_smishing_label
from verify_and_add_raw_clean_text_columns import (
    EMAIL_RE,
    LONG_NUMBER_RE,
    PHONE_RE,
    URL_RE,
    clean_cell,
    clean_message,
    redaction_detected,
)


ROOT = Path(__file__).resolve().parents[1]
RAW_RECOVERY_DIR = ROOT / "data" / "organized" / "raw_recovery"
GATHERED_INPUT = ROOT / "data" / "organized" / "text_verified" / "gathered_approved_smishing_7k_text_verified.csv"
DEDUPED_INPUT = ROOT / "data" / "organized" / "text_verified" / "combined_public_thesis_sources_deduped_representatives_text_verified.csv"
CANDIDATE_INPUT = RAW_RECOVERY_DIR / "collected_smishing_candidates_raw_classified.csv"

GATHERED_OUTPUT = RAW_RECOVERY_DIR / "gathered_7k_raw_recovered_or_replaced.csv"
REMOVED_OUTPUT = RAW_RECOVERY_DIR / "gathered_7k_redacted_removed_archive.csv"
MATCH_LOG_OUTPUT = RAW_RECOVERY_DIR / "replacement_match_log.csv"
RAW_REQUIRED_OUTPUT = RAW_RECOVERY_DIR / "combined_public_thesis_sources_deduped_raw_required.csv"
REPORT_PATH = ROOT / "reports" / "gathered_7k_raw_replacement_report.md"

TRACE_COLUMNS = [
    "replacement_status",
    "replacement_candidate_id",
    "original_replaced_unified_id",
    "final_dataset_eligible",
    "exclusion_reason",
]

MATCH_LOG_COLUMNS = [
    "old_unified_id",
    "old_message_clean",
    "replacement_candidate_id",
    "replacement_message_raw",
    "replacement_message_clean",
    "replacement_source_name",
    "replacement_dataset_name",
    "match_method",
    "duplicate_check_status",
    "replacement_status",
    "notes",
]

RAW_REQUIRED_COLUMNS = [
    "unified_id",
    "source_name",
    "dataset_name",
    "source_group",
    "source_row_id",
    "message_raw",
    "message_clean",
    "source_label",
    "normalized_label",
    "label_status",
    "review_status",
    "raw_text_available",
    "raw_text_status",
    "cleaning_status",
    "raw_lookup_status",
    "raw_lookup_notes",
    "replacement_status",
    "replacement_candidate_id",
    "original_replaced_unified_id",
    "contains_url",
    "contains_email",
    "contains_phone",
    "notes",
]

NON_ALNUM_RE = re.compile(r"[^a-z0-9<>]+")
WHITESPACE_RE = re.compile(r"\s+")
PLACEHOLDER_RAW_RE = re.compile(
    r"(?i)<\s*(URL|PHONE|PHONE_NUMBER|OTP|EMAIL|ACCT|REF_NUM|NAME|AMOUNT|DATE_TIME|NAMED_ENTITY)\s*>"
)


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


def bool_value(value: str) -> bool:
    return clean_cell(value).lower() == "true"


def normalize_key(text: str) -> str:
    text = clean_message(text or "").lower()
    text = NON_ALNUM_RE.sub(" ", text)
    return WHITESPACE_RE.sub(" ", text).strip()


def signal_flags(text: str) -> tuple[str, str, str]:
    return (
        "true" if URL_RE.search(text or "") else "false",
        "true" if EMAIL_RE.search(text or "") else "false",
        "true" if PHONE_RE.search(text or "") else "false",
    )


def row_needs_replacement(row: dict[str, str]) -> bool:
    return (
        not bool_value(row.get("raw_text_available", ""))
        or clean_cell(row.get("raw_text_status")) == "already_redacted"
        or bool_value(row.get("redaction_detected_in_raw", ""))
        or redaction_detected(row.get("message_raw", ""))
    )


def candidate_usable(candidate: dict[str, str]) -> bool:
    if candidate.get("candidate_raw_text_available") != "True":
        return False
    if candidate.get("candidate_raw_text_status") != "original_looking_raw":
        return False
    if not is_smishing_label(candidate):
        return False
    if is_rejected(candidate):
        return False
    if not clean_cell(candidate.get("candidate_clean_text")):
        return False
    if not (clean_cell(candidate.get("source_name")) or clean_cell(candidate.get("dataset_name"))):
        return False
    language = clean_cell(candidate.get("language")).lower()
    notes = clean_cell(candidate.get("candidate_raw_quality_notes")).lower()
    if language not in {"english", ""} and "english inferred" not in notes:
        return False
    return True


def candidate_sort_key(candidate: dict[str, str]) -> tuple:
    score = int(candidate.get("candidate_raw_quality_score") or 0)
    return (-score, clean_cell(candidate.get("id")))


def apply_candidate_to_row(
    old_row: dict[str, str],
    candidate: dict[str, str],
    *,
    status: str,
    lookup_status: str,
    notes: str,
) -> dict[str, str]:
    row = dict(old_row)
    candidate_id = clean_cell(candidate.get("id"))
    raw = clean_cell(candidate.get("candidate_raw_text"))
    clean = clean_cell(candidate.get("candidate_clean_text")) or clean_message(raw)
    contains_url, contains_email, contains_phone = signal_flags(raw)

    row["unified_id"] = old_row.get("unified_id") if status == "recovered_same_message" else f"replacement_{candidate_id}"
    row["source_name"] = clean_cell(candidate.get("source_name")) or old_row.get("source_name", "")
    row["dataset_name"] = clean_cell(candidate.get("dataset_name")) or old_row.get("dataset_name", "")
    row["source_group"] = "raw_recovery_91k_pool" if status != "recovered_same_message" else old_row.get("source_group", "")
    row["source_row_id"] = candidate_id
    row["message_text"] = clean
    row["message_raw"] = raw
    row["message_clean"] = clean
    row["source_label"] = clean_cell(candidate.get("original_label")) or clean_cell(candidate.get("label")) or "smishing"
    row["normalized_label"] = "smishing"
    row["label_status"] = "accepted"
    row["review_status"] = clean_cell(candidate.get("review_status")) or "candidate"
    row["contains_url"] = contains_url
    row["contains_email"] = contains_email
    row["contains_phone"] = contains_phone
    row["source_file"] = str(CANDIDATE_INPUT.relative_to(ROOT))
    row["notes"] = (
        f"{clean_cell(old_row.get('notes'))} | raw_recovery: source candidate {candidate_id}; "
        f"source_url={clean_cell(candidate.get('source_url'))}; scam_category={clean_cell(candidate.get('scam_category'))}"
    ).strip(" |")
    row["raw_text_available"] = "True"
    row["raw_text_status"] = "original_unredacted"
    row["cleaning_status"] = "cleaned_from_raw"
    row["redaction_detected_in_raw"] = "False"
    row["raw_lookup_status"] = lookup_status
    row["raw_lookup_notes"] = notes
    row["replacement_status"] = status
    row["replacement_candidate_id"] = candidate_id
    row["original_replaced_unified_id"] = old_row.get("unified_id", "")
    row["final_dataset_eligible"] = "True"
    row["exclusion_reason"] = ""
    return row


def archive_removed_row(row: dict[str, str], reason: str) -> dict[str, str]:
    archived = dict(row)
    if reason == "redacted_only_no_raw_available":
        archived["replacement_status"] = "removed_no_raw_available"
    elif reason == "duplicate_against_raw_required_dataset":
        archived["replacement_status"] = "excluded_duplicate_raw_available"
    else:
        archived["replacement_status"] = "excluded_from_raw_required_dataset"
    archived["replacement_candidate_id"] = ""
    archived["original_replaced_unified_id"] = row.get("unified_id", "")
    archived["final_dataset_eligible"] = "False"
    archived["exclusion_reason"] = reason
    return archived


def make_log(
    old_row: dict[str, str],
    candidate: dict[str, str] | None,
    *,
    method: str,
    duplicate_status: str,
    replacement_status: str,
    notes: str,
) -> dict[str, str]:
    return {
        "old_unified_id": old_row.get("unified_id", ""),
        "old_message_clean": old_row.get("message_clean", ""),
        "replacement_candidate_id": clean_cell(candidate.get("id")) if candidate else "",
        "replacement_message_raw": clean_cell(candidate.get("candidate_raw_text")) if candidate else "",
        "replacement_message_clean": clean_cell(candidate.get("candidate_clean_text")) if candidate else "",
        "replacement_source_name": clean_cell(candidate.get("source_name")) if candidate else "",
        "replacement_dataset_name": clean_cell(candidate.get("dataset_name")) if candidate else "",
        "match_method": method,
        "duplicate_check_status": duplicate_status,
        "replacement_status": replacement_status,
        "notes": notes,
    }


def build_candidate_indexes(candidates: list[dict[str, str]]) -> tuple[dict[str, dict[str, str]], dict[str, list[dict[str, str]]]]:
    by_id: dict[str, dict[str, str]] = {}
    by_clean: dict[str, list[dict[str, str]]] = defaultdict(list)
    for candidate in candidates:
        if not candidate_usable(candidate):
            continue
        candidate_id = clean_cell(candidate.get("id"))
        if candidate_id:
            by_id[candidate_id] = candidate
        key = normalize_key(candidate.get("candidate_clean_text", ""))
        if key:
            by_clean[key].append(candidate)
    return by_id, by_clean


def build_replacement_pools(candidates: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    pools: dict[str, list[dict[str, str]]] = defaultdict(list)
    for candidate in candidates:
        if not candidate_usable(candidate):
            continue
        source_key = clean_cell(candidate.get("source_name")) or clean_cell(candidate.get("dataset_name")) or "unknown_source"
        pools[source_key].append(candidate)
    for source_key in pools:
        pools[source_key].sort(key=candidate_sort_key)
    return dict(pools)


def choose_replacement_candidate(
    replacement_pools: dict[str, list[dict[str, str]]],
    source_counts: Counter[str],
    category_counts: Counter[str],
    selected_candidate_ids: set[str],
    accepted_keys: set[str],
) -> tuple[dict[str, str] | None, int]:
    duplicate_skips = 0
    while True:
        available_sources = [source for source, pool in replacement_pools.items() if pool]
        if not available_sources:
            return None, duplicate_skips
        available_sources.sort(
            key=lambda source: (
                source_counts[source],
                category_counts[clean_cell(replacement_pools[source][0].get("scam_category"))],
                -int(replacement_pools[source][0].get("candidate_raw_quality_score") or 0),
                source,
            )
        )
        made_progress = False
        for source in available_sources:
            pool = replacement_pools[source]
            while pool:
                made_progress = True
                candidate = pool.pop(0)
                candidate_id = clean_cell(candidate.get("id"))
                if candidate_id in selected_candidate_ids:
                    continue
                candidate_key = normalize_key(candidate.get("candidate_clean_text", ""))
                if candidate_key in accepted_keys:
                    duplicate_skips += 1
                    continue
                return candidate, duplicate_skips
        if not made_progress:
            return None, duplicate_skips


def add_raw_required_row(
    row: dict[str, str],
    accepted_keys: set[str],
    output_rows: list[dict[str, str]],
    *,
    allow_same_key: bool = False,
) -> str:
    key = normalize_key(row.get("message_clean", ""))
    if not key:
        return "empty_clean_rejected"
    if key in accepted_keys and not allow_same_key:
        return "exact_duplicate_rejected"
    if row.get("raw_text_available") != "True":
        return "raw_unavailable_rejected"
    if row.get("raw_text_status") == "already_redacted" or redaction_detected(row.get("message_raw", "")):
        return "redacted_raw_rejected"
    if clean_cell(row.get("normalized_label")) not in {"ham", "smishing"}:
        return "spam_or_review_label_rejected"
    if clean_cell(row.get("label_status")) == "conflict_needs_review":
        return "label_conflict_rejected"
    output_rows.append(row)
    accepted_keys.add(key)
    return "accepted"


def clean_contains_private_artifacts(text: str) -> bool:
    compact_long_number = bool(LONG_NUMBER_RE.search(text or ""))
    return bool(URL_RE.search(text or "") or EMAIL_RE.search(text or "") or PHONE_RE.search(text or "") or compact_long_number)


def validation_checks(rows: list[dict[str, str]], removed_rows: list[dict[str, str]], report_exists: bool) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []

    def add(name: str, ok: bool, details: str) -> None:
        checks.append({"check": name, "status": "PASS" if ok else "FAIL", "details": details})

    add("No raw_text_available=False rows", all(row.get("raw_text_available") == "True" for row in rows), str(sum(row.get("raw_text_available") != "True" for row in rows)))
    add("No already_redacted rows", all(row.get("raw_text_status") != "already_redacted" for row in rows), str(sum(row.get("raw_text_status") == "already_redacted" for row in rows)))
    add("No empty message_raw", all(clean_cell(row.get("message_raw")) for row in rows), str(sum(not clean_cell(row.get("message_raw")) for row in rows)))
    add("No empty message_clean", all(clean_cell(row.get("message_clean")) for row in rows), str(sum(not clean_cell(row.get("message_clean")) for row in rows)))
    raw_placeholder_count = sum(bool(PLACEHOLDER_RAW_RE.search(row.get("message_raw", ""))) for row in rows)
    clean_artifact_count = sum(clean_contains_private_artifacts(row.get("message_clean", "")) for row in rows)
    add("No obvious placeholders remain in message_raw", raw_placeholder_count == 0, f"flagged={raw_placeholder_count}")
    add("message_clean privacy-safe artifacts", clean_artifact_count == 0, f"flagged={clean_artifact_count}")
    add("Excluded rows archived", all(row.get("final_dataset_eligible") == "False" for row in removed_rows), f"archived={len(removed_rows)}")
    add("Final report written", report_exists, str(REPORT_PATH.relative_to(ROOT)))
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


def write_report(
    *,
    candidates: list[dict[str, str]],
    gathered_rows: list[dict[str, str]],
    needing: list[dict[str, str]],
    recovered_count: int,
    replaced_count: int,
    removed_rows: list[dict[str, str]],
    skipped_duplicate_count: int,
    skipped_low_confidence_count: int,
    skipped_label_conflict_count: int,
    raw_required_rows: list[dict[str, str]],
    checks: list[dict[str, str]],
) -> None:
    smishing_candidates = [row for row in candidates if is_smishing_label(row)]
    raw_available_candidates = [row for row in candidates if row.get("candidate_raw_text_available") == "True" and is_smishing_label(row)]
    already_redacted = sum(row.get("candidate_raw_text_status") == "already_redacted" for row in candidates)
    rejected_or_unusable = sum(is_rejected(row) or row.get("candidate_raw_text_status") in {"empty_or_missing", "non_english_or_unclear", "not_smishing", "needs_review"} for row in candidates)
    final_counts = Counter(row.get("normalized_label", "") for row in raw_required_rows)
    redacted_remaining = sum(row.get("raw_text_status") == "already_redacted" or redaction_detected(row.get("message_raw", "")) for row in raw_required_rows)
    removed_no_raw_count = sum(row.get("replacement_status") == "removed_no_raw_available" for row in removed_rows)
    excluded_duplicate_count = sum(row.get("replacement_status") == "excluded_duplicate_raw_available" for row in removed_rows)

    def top_counts(column: str, limit: int = 15) -> list[dict[str, str]]:
        counts = Counter(clean_cell(row.get(column)) or "(blank)" for row in candidates)
        return [{column: key, "rows": str(value)} for key, value in counts.most_common(limit)]

    lines = [
        "# Gathered 7k Raw Replacement Report",
        "",
        "## 1. Purpose",
        "",
        "This workflow tries to make the final thesis candidate dataset compatible with paired raw and cleaned text. It classifies raw availability in the 91k candidate pool, recovers exact raw versions where possible, replaces unrecoverable redacted-only gathered rows with separate raw-available smishing candidates, and archives any row that cannot be used without inventing raw text.",
        "",
        "## 2. Starting Point",
        "",
        f"- Gathered 7k total rows: {len(gathered_rows):,}",
        f"- Gathered raw available: {sum(row.get('raw_text_available') == 'True' for row in gathered_rows):,}",
        f"- Gathered redacted-only needing recovery/replacement: {len(needing):,}",
        "",
        "## 3. 91k Candidate Pool Summary",
        "",
        f"- Total candidate rows: {len(candidates):,}",
        f"- Smishing-labeled rows: {len(smishing_candidates):,}",
        f"- Candidate rows with original-looking raw text: {len(raw_available_candidates):,}",
        f"- Candidate rows already redacted: {already_redacted:,}",
        f"- Candidate rows rejected/not usable: {rejected_or_unusable:,}",
        "",
        "### Top Dataset Names",
        "",
        *markdown_table(top_counts("dataset_name"), ["dataset_name", "rows"]),
        "",
        "### Top Source Names",
        "",
        *markdown_table(top_counts("source_name"), ["source_name", "rows"]),
        "",
        "### Scam Categories",
        "",
        *markdown_table(top_counts("scam_category"), ["scam_category", "rows"]),
        "",
        "### Languages",
        "",
        *markdown_table(top_counts("language"), ["language", "rows"]),
        "",
        "## 4. Recovery Results",
        "",
        f"- Recovered same-message raw count: {recovered_count:,}",
        f"- Replaced with different raw-available candidate count: {replaced_count:,}",
        f"- Removed due to no raw available count: {removed_no_raw_count:,}",
        f"- Excluded exact duplicate raw-available gathered rows archived: {excluded_duplicate_count:,}",
        f"- Skipped duplicate count: {skipped_duplicate_count:,}",
        f"- Skipped low-confidence count: {skipped_low_confidence_count:,}",
        f"- Skipped label-conflict count: {skipped_label_conflict_count:,}",
        "",
        "## 5. Final Raw-Required Dataset Count",
        "",
        f"- Total rows: {len(raw_required_rows):,}",
        f"- Ham count: {final_counts.get('ham', 0):,}",
        f"- Smishing count: {final_counts.get('smishing', 0):,}",
        f"- Spam/review count retained in raw-required file: {sum(value for label, value in final_counts.items() if label not in {'ham', 'smishing'}):,}",
        f"- Rows with raw_text_available=True: {sum(row.get('raw_text_available') == 'True' for row in raw_required_rows):,}",
        f"- Redacted-only text remaining: {redacted_remaining:,}",
        "",
        "### Validation",
        "",
        *markdown_table(checks, ["check", "status", "details"]),
        "",
        "## 6. Thesis Methodology Note",
        "",
        "Rows were included in the raw-required dataset only when an original-looking raw message was available. Redacted-only rows were not de-redacted or reconstructed. When a redacted gathered smishing row could not be linked to a raw version, it was either replaced by a separate raw-available smishing candidate from the 91k source pool or excluded from the raw-required dataset. All replacements preserve source traceability and are deduplicated against existing public sources.",
        "",
        "## 7. Files Generated",
        "",
        f"- `{GATHERED_OUTPUT.relative_to(ROOT)}`",
        f"- `{REMOVED_OUTPUT.relative_to(ROOT)}`",
        f"- `{MATCH_LOG_OUTPUT.relative_to(ROOT)}`",
        f"- `{RAW_REQUIRED_OUTPUT.relative_to(ROOT)}`",
        f"- `{REPORT_PATH.relative_to(ROOT)}`",
        "",
        "## 8. Recommended Next Step",
        "",
        "Build model-ready datasets from this audit output as separate, explicitly named artifacts: a real raw-required balanced dataset, a cleaned-text version derived only from the raw-required rows, and an optional redacted-only sensitivity dataset kept separate from the main thesis dataset.",
        "",
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if not CANDIDATE_INPUT.exists():
        raise SystemExit("Classified candidate file is missing. Run: python scripts/classify_raw_text_availability.py")

    gathered_rows, gathered_fieldnames = read_csv(GATHERED_INPUT)
    deduped_rows, _deduped_fieldnames = read_csv(DEDUPED_INPUT)
    candidates, _candidate_fieldnames = read_csv(CANDIDATE_INPUT)

    by_id, by_clean = build_candidate_indexes(candidates)
    needing = [row for row in gathered_rows if row_needs_replacement(row)]
    selected_candidate_ids: set[str] = set()
    accepted_keys: set[str] = set()
    raw_required_rows: list[dict[str, str]] = []
    gathered_output_rows: list[dict[str, str]] = []
    removed_rows: list[dict[str, str]] = []
    match_logs: list[dict[str, str]] = []

    skipped_duplicate_count = 0
    skipped_low_confidence_count = sum(
        row.get("candidate_raw_text_status") == "needs_review" or int(row.get("candidate_raw_quality_score") or 0) < 35
        for row in candidates
    )
    skipped_label_conflict_count = sum(clean_cell(row.get("label_status")) == "conflict_needs_review" for row in deduped_rows)

    for row in deduped_rows:
        if clean_cell(row.get("source_group")) == "gathered_approved_smishing":
            continue
        status = add_raw_required_row(dict(row), accepted_keys, raw_required_rows)
        if status == "exact_duplicate_rejected":
            skipped_duplicate_count += 1

    source_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    replacement_pools = build_replacement_pools(candidates)

    recovered_count = 0
    replaced_count = 0
    replacement_index = 0

    for old_row in gathered_rows:
        if not row_needs_replacement(old_row):
            kept = dict(old_row)
            kept["replacement_status"] = "kept_original_raw_available"
            kept["replacement_candidate_id"] = ""
            kept["original_replaced_unified_id"] = ""
            kept["final_dataset_eligible"] = "True"
            kept["exclusion_reason"] = ""
            duplicate_status = add_raw_required_row(kept, accepted_keys, raw_required_rows)
            if duplicate_status == "exact_duplicate_rejected":
                skipped_duplicate_count += 1
                kept["final_dataset_eligible"] = "False"
                kept["exclusion_reason"] = "duplicate_against_raw_required_dataset"
                removed_rows.append(archive_removed_row(kept, "duplicate_against_raw_required_dataset"))
            gathered_output_rows.append(kept)
            continue

        match_candidate: dict[str, str] | None = None
        match_method = ""
        old_source_id = clean_cell(old_row.get("source_row_id"))
        if old_source_id in by_id:
            match_candidate = by_id[old_source_id]
            match_method = "stable_id"
        else:
            key = normalize_key(old_row.get("message_clean", ""))
            clean_matches = [candidate for candidate in by_clean.get(key, []) if clean_cell(candidate.get("id")) not in selected_candidate_ids]
            if clean_matches:
                match_candidate = sorted(clean_matches, key=lambda row: -int(row.get("candidate_raw_quality_score") or 0))[0]
                match_method = "normalized_clean_exact"

        if match_candidate:
            recovered = apply_candidate_to_row(
                old_row,
                match_candidate,
                status="recovered_same_message",
                lookup_status="recovered_from_91k_pool",
                notes=f"Recovered raw text from 91k candidate pool using {match_method}; candidate_id={clean_cell(match_candidate.get('id'))}.",
            )
            duplicate_status = add_raw_required_row(recovered, accepted_keys, raw_required_rows, allow_same_key=False)
            if duplicate_status == "accepted":
                selected_candidate_ids.add(clean_cell(match_candidate.get("id")))
                recovered_count += 1
                gathered_output_rows.append(recovered)
                match_logs.append(make_log(old_row, match_candidate, method=match_method, duplicate_status=duplicate_status, replacement_status="recovered_same_message", notes=recovered["raw_lookup_notes"]))
                continue
            skipped_duplicate_count += 1
            match_logs.append(make_log(old_row, match_candidate, method=match_method, duplicate_status=duplicate_status, replacement_status="skipped_duplicate", notes="Recovered candidate duplicated an already accepted raw-required row."))

        duplicate_status = ""
        replacement_candidate, duplicate_skips = choose_replacement_candidate(
            replacement_pools,
            source_counts,
            category_counts,
            selected_candidate_ids,
            accepted_keys,
        )
        skipped_duplicate_count += duplicate_skips
        if replacement_candidate:
            duplicate_status = "accepted"

        if replacement_candidate:
            replacement = apply_candidate_to_row(
                old_row,
                replacement_candidate,
                status="replaced_with_raw_available_candidate",
                lookup_status="replaced_from_91k_pool",
                notes="Redacted-only gathered row replaced by raw-available smishing candidate from 91k pool.",
            )
            duplicate_status = add_raw_required_row(replacement, accepted_keys, raw_required_rows)
            if duplicate_status == "accepted":
                selected_candidate_ids.add(clean_cell(replacement_candidate.get("id")))
                source_counts[clean_cell(replacement_candidate.get("source_name")) or clean_cell(replacement_candidate.get("dataset_name"))] += 1
                category_counts[clean_cell(replacement_candidate.get("scam_category"))] += 1
                replaced_count += 1
                gathered_output_rows.append(replacement)
                match_logs.append(make_log(old_row, replacement_candidate, method="replacement_pool", duplicate_status=duplicate_status, replacement_status="replaced_with_raw_available_candidate", notes=replacement["raw_lookup_notes"]))
                continue

        removed = archive_removed_row(old_row, "redacted_only_no_raw_available")
        removed_rows.append(removed)
        gathered_output_rows.append(removed)
        match_logs.append(make_log(old_row, None, method="none", duplicate_status=duplicate_status or "no_candidate_available", replacement_status="removed_no_raw_available", notes="No non-duplicate raw-available smishing candidate was available."))

    gathered_fieldnames_out = list(dict.fromkeys(gathered_fieldnames + TRACE_COLUMNS))
    write_csv(GATHERED_OUTPUT, gathered_output_rows, gathered_fieldnames_out)
    write_csv(REMOVED_OUTPUT, removed_rows, gathered_fieldnames_out)
    write_csv(MATCH_LOG_OUTPUT, match_logs, MATCH_LOG_COLUMNS)
    write_csv(RAW_REQUIRED_OUTPUT, raw_required_rows, RAW_REQUIRED_COLUMNS)

    checks = validation_checks(raw_required_rows, removed_rows, False)
    write_report(
        candidates=candidates,
        gathered_rows=gathered_rows,
        needing=needing,
        recovered_count=recovered_count,
        replaced_count=replaced_count,
        removed_rows=removed_rows,
        skipped_duplicate_count=skipped_duplicate_count,
        skipped_low_confidence_count=skipped_low_confidence_count,
        skipped_label_conflict_count=skipped_label_conflict_count,
        raw_required_rows=raw_required_rows,
        checks=checks,
    )
    checks = validation_checks(raw_required_rows, removed_rows, REPORT_PATH.exists())
    write_report(
        candidates=candidates,
        gathered_rows=gathered_rows,
        needing=needing,
        recovered_count=recovered_count,
        replaced_count=replaced_count,
        removed_rows=removed_rows,
        skipped_duplicate_count=skipped_duplicate_count,
        skipped_low_confidence_count=skipped_low_confidence_count,
        skipped_label_conflict_count=skipped_label_conflict_count,
        raw_required_rows=raw_required_rows,
        checks=checks,
    )

    final_counts = Counter(row.get("normalized_label", "") for row in raw_required_rows)
    raw_available_candidates_found = sum(row.get("candidate_raw_text_available") == "True" and is_smishing_label(row) for row in candidates)
    removed_no_raw_count = sum(row.get("replacement_status") == "removed_no_raw_available" for row in removed_rows)

    print(f"91k candidate pool path used: {CANDIDATE_INPUT.relative_to(ROOT)}")
    print(f"Number of 91k rows inspected: {len(candidates)}")
    print(f"Number of raw-available smishing candidates found: {raw_available_candidates_found}")
    print(f"Number of gathered 7k redacted rows needing recovery/replacement: {len(needing)}")
    print(f"Number recovered as same message: {recovered_count}")
    print(f"Number replaced by raw-available candidates: {replaced_count}")
    print(f"Number removed/no raw available: {removed_no_raw_count}")
    print(f"Final raw-required dataset row count: {len(raw_required_rows)}")
    print(f"Final raw-required ham/smishing counts: ham={final_counts.get('ham', 0)}; smishing={final_counts.get('smishing', 0)}")
    print("Output files:")
    for path in [GATHERED_OUTPUT, REMOVED_OUTPUT, MATCH_LOG_OUTPUT, RAW_REQUIRED_OUTPUT]:
        print(f"- {path.relative_to(ROOT)}")
    print(f"Report: {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
