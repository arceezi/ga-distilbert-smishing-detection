"""Build a campaign-family filtered dataset with safe smishing replacements."""

from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

from audit_smishing_content_quality import ABUSIVE_REPLY_RE, classify, score_smishing
from audit_strict_raw_text_quality import sms_likeness
from audit_strong_campaign_families import (
    ADDED as STRONG_ADDED,
    ANGLE_PLACEHOLDER_RE,
    explicit_family_key,
    family_cap,
    strong_campaign_family_key,
)
from classify_raw_text_availability import is_rejected, is_smishing_label
from verify_and_add_raw_clean_text_columns import clean_cell, clean_message


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "organized" / "content_quality" / "combined_public_thesis_sources_content_filtered.csv"
GROUPS_INPUT = ROOT / "data" / "organized" / "campaign_family_quality" / "strong_campaign_family_groups.csv"
CANDIDATES_INPUT = ROOT / "data" / "organized" / "raw_recovery" / "collected_smishing_candidates_raw_classified.csv"
OUT_DIR = ROOT / "data" / "organized" / "campaign_family_quality"
FILTERED_OUT = OUT_DIR / "combined_public_thesis_sources_campaign_family_filtered.csv"
LOG_OUT = OUT_DIR / "strong_campaign_family_replacement_log.csv"
EXCLUDED_OUT = OUT_DIR / "strong_campaign_family_excluded_archive.csv"
REPORT = ROOT / "reports" / "campaign_family_filtered_dataset_report.md"

BUILD_ADDED = [
    "campaign_family_filter_status",
    "campaign_family_filter_reason",
    "campaign_family_replacement_candidate_id",
    "campaign_family_removed_original_unified_id",
]

LOG_FIELDS = [
    "removed_unified_id",
    "removed_row_position_1based",
    "removed_strong_campaign_family_key",
    "removed_message_raw",
    "removed_reason",
    "replacement_candidate_id",
    "replacement_message_raw",
    "replacement_source_name",
    "replacement_dataset_name",
    "replacement_strong_campaign_family_key",
    "replacement_reason",
    "duplicate_check_status",
    "notes",
]

URL_OR_DOMAIN_RE = re.compile(r"(?i)\b(?:https?://|www\.|[a-z0-9.-]+\.(?:com|net|org|ph|co|uk|io|biz|xyz|top|site|online|click|shop|app|info|live|vip))\b")
PLACEHOLDER_ANY_RE = re.compile(r"<[^>]{1,40}>")
ACTIONABLE_RE = re.compile(
    r"(?i)\b(login|log in|verify|update|confirm|validate|click|visit|open|tap|call|reply|text|claim|pay|activate|"
    r"unlock|secure|cancel|account|bank|card|wallet|payment|delivery|package|parcel|otp|code|password|pin|alert|"
    r"suspended|locked|blocked|refund|prize|reward)\b"
)


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as h:
        reader = csv.DictReader(h)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as h:
        writer = csv.DictWriter(h, fieldnames=list(dict.fromkeys(fieldnames)), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def norm_key(text: str) -> str:
    return re.sub(r"\s+", " ", clean_message(text or "").lower()).strip()


def has_bad_placeholder(text: str) -> bool:
    return bool(ANGLE_PLACEHOLDER_RE.search(text or ""))


def candidate_english(candidate: dict[str, str]) -> bool:
    lang = clean_cell(candidate.get("language")).lower()
    notes = clean_cell(candidate.get("candidate_raw_quality_notes")).lower()
    return lang in {"english", "unknown", ""} or "english" in notes


def candidate_sms_like(text: str) -> bool:
    if not text or len(text.strip()) < 12:
        return False
    if len(text) > 280:
        return False
    return sms_likeness(text) != "possible_report_or_article_text"


def candidate_ok(candidate: dict[str, str]) -> tuple[bool, str]:
    raw = clean_cell(candidate.get("candidate_raw_text"))
    if clean_cell(candidate.get("candidate_raw_text_available")) != "True":
        return False, "raw_unavailable"
    if clean_cell(candidate.get("candidate_raw_text_status")) not in {"original_looking_raw", "original_unredacted"}:
        return False, "bad_raw_status"
    if not is_smishing_label(candidate):
        return False, "not_smishing_label"
    if is_rejected(candidate):
        return False, "rejected"
    if not raw:
        return False, "empty_raw"
    if PLACEHOLDER_ANY_RE.search(raw):
        return False, "angle_bracket_placeholder"
    if not candidate_english(candidate):
        return False, "non_english"
    if not candidate_sms_like(raw):
        return False, "not_sms_like"
    score, _ = score_smishing(raw)
    if score < 3 or not ACTIONABLE_RE.search(raw) or ABUSIVE_REPLY_RE.search(raw):
        return False, "weak_or_bad_smishing_signal"
    if not (clean_cell(candidate.get("source_name")) or clean_cell(candidate.get("dataset_name"))):
        return False, "missing_traceability"
    key = strong_campaign_family_key(raw)
    if key in {"family_usdtferc_account_reset", "family_trxm_login_balance", "family_usdtrxm_login_code"}:
        return False, "same_known_repeated_family"
    return True, "ok"


def replacement_score(candidate: dict[str, str]) -> tuple[int, int, int, int, str]:
    raw = clean_cell(candidate.get("candidate_raw_text"))
    signal, _ = score_smishing(raw)
    quality = int(float(clean_cell(candidate.get("candidate_raw_quality_score")) or 0))
    category_present = 1 if clean_cell(candidate.get("scam_category")) else 0
    source_present = 1 if clean_cell(candidate.get("source_name")) else 0
    return (-signal, -category_present, -source_present, len(raw), f"{-quality:04d}:{clean_cell(candidate.get('id'))}")


def annotate_strong(row: dict[str, str], row_position: int, status: str, reason: str, family_size: int = 1) -> None:
    key = strong_campaign_family_key(row.get("message_raw", ""))
    row["strong_campaign_family_key"] = key
    row["strong_campaign_family_id"] = ""
    row["strong_campaign_family_size"] = str(family_size)
    row["strong_campaign_family_status"] = status
    row["strong_campaign_family_reason"] = reason
    row["row_position_1based"] = str(row_position)


def make_replacement(removed: dict[str, str], candidate: dict[str, str]) -> dict[str, str]:
    raw = clean_cell(candidate.get("candidate_raw_text"))
    clean = clean_cell(candidate.get("candidate_clean_text")) or clean_message(raw)
    cid = clean_cell(candidate.get("id"))
    row = dict(removed)
    row["unified_id"] = f"campaign_family_replacement_{cid}"
    row["source_name"] = clean_cell(candidate.get("source_name"))
    row["dataset_name"] = clean_cell(candidate.get("dataset_name"))
    row["source_group"] = "campaign_family_replacement_91k_pool"
    row["source_row_id"] = cid
    row["message_raw"] = raw
    row["message_clean"] = clean
    row["source_label"] = clean_cell(candidate.get("original_label")) or clean_cell(candidate.get("label")) or "smishing"
    row["normalized_label"] = "smishing"
    row["label_status"] = "accepted"
    row["review_status"] = clean_cell(candidate.get("review_status")) or "candidate"
    row["raw_text_available"] = "True"
    row["raw_text_status"] = "original_unredacted"
    row["raw_quality_status"] = "pass_raw"
    row["raw_lookup_status"] = "replaced_from_91k_pool_campaign_family"
    row["raw_lookup_notes"] = "Campaign-family replacement from raw-available 91k candidate pool."
    row["replacement_status"] = "campaign_family_replacement"
    row["replacement_candidate_id"] = cid
    row["original_replaced_unified_id"] = removed.get("unified_id", "")
    cq = classify({"message_raw": raw})
    for col in ["content_quality_status", "content_quality_flags", "smishing_signal_score", "non_smishing_reason", "suggested_action"]:
        row[col] = cq[col]
    row["campaign_family_filter_status"] = "replacement_accepted"
    row["campaign_family_filter_reason"] = "replaced excluded strong campaign-family repeat"
    row["campaign_family_replacement_candidate_id"] = cid
    row["campaign_family_removed_original_unified_id"] = removed.get("unified_id", "")
    return row


def log_row(removed: dict[str, str], candidate: dict[str, str] | None, status: str, notes: str) -> dict[str, str]:
    return {
        "removed_unified_id": removed.get("unified_id", ""),
        "removed_row_position_1based": removed.get("row_position_1based", ""),
        "removed_strong_campaign_family_key": removed.get("strong_campaign_family_key", ""),
        "removed_message_raw": removed.get("message_raw", ""),
        "removed_reason": removed.get("campaign_family_filter_reason") or removed.get("strong_campaign_family_reason", ""),
        "replacement_candidate_id": clean_cell(candidate.get("id")) if candidate else "",
        "replacement_message_raw": clean_cell(candidate.get("candidate_raw_text")) if candidate else "",
        "replacement_source_name": clean_cell(candidate.get("source_name")) if candidate else "",
        "replacement_dataset_name": clean_cell(candidate.get("dataset_name")) if candidate else "",
        "replacement_strong_campaign_family_key": strong_campaign_family_key(candidate.get("candidate_raw_text", "")) if candidate else "",
        "replacement_reason": status,
        "duplicate_check_status": status,
        "notes": notes,
    }


def refresh_family_annotations(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], Counter[str]]:
    counts = Counter(strong_campaign_family_key(r.get("message_raw", "")) for r in rows if r.get("normalized_label") == "smishing")
    family_ids = {
        key: f"strongfam_final_{idx:06d}"
        for idx, (key, count) in enumerate(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])), start=1)
        if count > 1
    }
    seen = Counter()
    refreshed = []
    for pos, row in enumerate(rows, start=1):
        out = dict(row)
        if out.get("normalized_label") == "smishing":
            key = strong_campaign_family_key(out.get("message_raw", ""))
            seen[key] += 1
            out["strong_campaign_family_key"] = key
            out["strong_campaign_family_id"] = family_ids.get(key, "")
            out["strong_campaign_family_size"] = str(counts[key])
            out["strong_campaign_family_status"] = "unique_family" if counts[key] == 1 else "family_representative"
            out["strong_campaign_family_reason"] = "final dataset row kept under strong campaign-family cap"
            out["row_position_1based"] = str(pos)
        else:
            for col in STRONG_ADDED:
                out.setdefault(col, "")
            out["row_position_1based"] = str(pos)
        refreshed.append(out)
    return refreshed, counts


def main() -> None:
    rows, fields = read_csv(INPUT)
    groups, _ = read_csv(GROUPS_INPUT)
    candidates, _ = read_csv(CANDIDATES_INPUT)

    groups_by_id = {r.get("unified_id", ""): r for r in groups}
    start_counts = Counter(r.get("normalized_label", "") for r in rows)
    before_family_counts = Counter(
        r.get("strong_campaign_family_key") or strong_campaign_family_key(r.get("message_raw", ""))
        for r in groups
        if r.get("normalized_label") == "smishing"
    )

    final: list[dict[str, str]] = []
    excluded: list[dict[str, str]] = []
    logs: list[dict[str, str]] = []
    raw_keys: set[str] = set()
    clean_keys: set[str] = set()
    family_counts: Counter[str] = Counter()

    for pos, row in enumerate(rows, start=1):
        out = dict(row)
        group = groups_by_id.get(out.get("unified_id", ""), {})
        if out.get("normalized_label") == "ham":
            out["campaign_family_filter_status"] = "kept_ham_passthrough"
            out["campaign_family_filter_reason"] = "ham row copied through without content changes"
            for col in STRONG_ADDED:
                out.setdefault(col, "")
            out["row_position_1based"] = str(pos)
            final.append(out)
            raw_keys.add(norm_key(out.get("message_raw", "")))
            clean_keys.add(norm_key(out.get("message_clean", "")))
            continue

        for col in STRONG_ADDED:
            out[col] = group.get(col, out.get(col, ""))
        if not out.get("strong_campaign_family_key"):
            annotate_strong(out, pos, "unique_family", explicit_family_key(out.get("message_raw", ""))[1])

        if group.get("strong_campaign_family_status") == "family_repeat_exclude":
            out["campaign_family_filter_status"] = "excluded_archived"
            out["campaign_family_filter_reason"] = "strong_campaign_family_repeat_exclude"
            excluded.append(out)
            continue

        rk, ck = norm_key(out.get("message_raw", "")), norm_key(out.get("message_clean", ""))
        key = out["strong_campaign_family_key"]
        if score_smishing(out.get("message_raw", ""))[0] < 2 or ABUSIVE_REPLY_RE.search(out.get("message_raw", "")):
            out["campaign_family_filter_status"] = "excluded_archived"
            out["campaign_family_filter_reason"] = "weak_or_bad_smishing_signal"
            excluded.append(out)
            continue
        if not rk or has_bad_placeholder(out.get("message_raw", "")):
            out["campaign_family_filter_status"] = "excluded_archived"
            out["campaign_family_filter_reason"] = "empty_or_placeholder_raw"
            excluded.append(out)
            continue
        if rk in raw_keys or (ck and ck in clean_keys):
            out["campaign_family_filter_status"] = "excluded_archived"
            out["campaign_family_filter_reason"] = "duplicate_raw_or_clean_key"
            excluded.append(out)
            continue
        if family_counts[key] >= family_cap(key, before_family_counts.get(key, 1)):
            out["campaign_family_filter_status"] = "excluded_archived"
            out["campaign_family_filter_reason"] = "post_build_family_cap"
            excluded.append(out)
            continue
        out["campaign_family_filter_status"] = "kept"
        out["campaign_family_filter_reason"] = "kept under strong campaign-family cap"
        final.append(out)
        raw_keys.add(rk)
        if ck:
            clean_keys.add(ck)
        family_counts[key] += 1

    skip_reasons = Counter()
    usable_candidates = []
    for candidate in candidates:
        ok, reason = candidate_ok(candidate)
        if ok:
            usable_candidates.append(candidate)
        else:
            skip_reasons[reason] += 1
    usable_candidates.sort(key=replacement_score)

    selected_ids: set[str] = set()
    duplicate_skips = 0
    same_family_skips = 0
    campaign_cap_skips = 0
    replacements_accepted = 0
    unavailable = 0
    source_counts = Counter()
    category_counts = Counter()

    for removed in [r for r in excluded if r.get("normalized_label") == "smishing"]:
        chosen = None
        for candidate in usable_candidates:
            cid = clean_cell(candidate.get("id"))
            if cid in selected_ids:
                continue
            raw = clean_cell(candidate.get("candidate_raw_text"))
            clean = clean_cell(candidate.get("candidate_clean_text")) or clean_message(raw)
            rk, ck = norm_key(raw), norm_key(clean)
            if rk in raw_keys or (ck and ck in clean_keys):
                duplicate_skips += 1
                selected_ids.add(cid)
                continue
            key = strong_campaign_family_key(raw)
            if key == removed.get("strong_campaign_family_key"):
                same_family_skips += 1
                selected_ids.add(cid)
                continue
            if family_counts[key] >= family_cap(key, family_counts[key] + 1):
                campaign_cap_skips += 1
                selected_ids.add(cid)
                continue
            chosen = candidate
            break

        if not chosen:
            unavailable += 1
            logs.append(log_row(removed, None, "replacement_unavailable", "No safe non-duplicate raw-available replacement remained."))
            continue

        cid = clean_cell(chosen.get("id"))
        replacement = make_replacement(removed, chosen)
        key = strong_campaign_family_key(replacement.get("message_raw", ""))
        final.append(replacement)
        selected_ids.add(cid)
        raw_keys.add(norm_key(replacement.get("message_raw", "")))
        clean_keys.add(norm_key(replacement.get("message_clean", "")))
        family_counts[key] += 1
        replacements_accepted += 1
        source_counts[clean_cell(chosen.get("source_name")) or clean_cell(chosen.get("dataset_name"))] += 1
        category_counts[clean_cell(chosen.get("scam_category"))] += 1
        logs.append(log_row(removed, chosen, "accepted", "Raw-available SMS-like smishing replacement accepted under strong family cap."))

    final, final_family_counts = refresh_family_annotations(final)
    final_counts = Counter(r.get("normalized_label", "") for r in final)
    known_after = {
        key: final_family_counts.get(key, 0)
        for key in [
            "family_usdtferc_account_reset",
            "family_trxm_login_balance",
            "family_usdtrxm_login_code",
            "family_crypto_login_balance",
        ]
    }
    known_before = {
        key: before_family_counts.get(key, 0)
        for key in [
            "family_usdtferc_account_reset",
            "family_trxm_login_balance",
            "family_usdtrxm_login_code",
            "family_crypto_login_balance",
        ]
    }
    row9227_repeats = sum(
        1
        for r in groups
        if int(r.get("row_position_1based") or 0) >= 9200 and int(r.get("strong_campaign_family_size") or 1) > 1
    )
    usdtferc_excluded = sum(1 for r in excluded if r.get("strong_campaign_family_key") == "family_usdtferc_account_reset")
    campaign_repeat_excluded = sum(
        1
        for r in excluded
        if r.get("campaign_family_filter_reason")
        in {"strong_campaign_family_repeat_exclude", "post_build_family_cap", "duplicate_raw_or_clean_key"}
    )
    weak_signal_excluded = sum(1 for r in excluded if r.get("campaign_family_filter_reason") == "weak_or_bad_smishing_signal")

    fields_out = fields + STRONG_ADDED + BUILD_ADDED
    write_csv(FILTERED_OUT, final, fields_out)
    write_csv(EXCLUDED_OUT, excluded, fields_out)
    write_csv(LOG_OUT, logs, LOG_FIELDS)

    placeholder_left = sum(1 for r in final if r.get("normalized_label") == "smishing" and has_bad_placeholder(r.get("message_raw", "")))
    empty_left = sum(1 for r in final if not clean_cell(r.get("message_raw")))
    raw_unavailable_left = sum(1 for r in final if r.get("normalized_label") == "smishing" and r.get("raw_text_available") == "False")
    already_redacted_left = sum(1 for r in final if r.get("normalized_label") == "smishing" and r.get("raw_text_status") == "already_redacted")
    duplicate_raw_left = len([k for k, v in Counter(norm_key(r.get("message_raw", "")) for r in final).items() if k and v > 1])
    duplicate_clean_left = len([k for k, v in Counter(norm_key(r.get("message_clean", "")) for r in final).items() if k and v > 1])
    angry_left = sum(1 for r in final if r.get("normalized_label") == "smishing" and ABUSIVE_REPLY_RE.search(r.get("message_raw", "")))
    weak_left = sum(1 for r in final if r.get("normalized_label") == "smishing" and score_smishing(r.get("message_raw", ""))[0] < 2)
    over_cap = {k: v for k, v in final_family_counts.items() if v > family_cap(k, v)}

    top_before = before_family_counts.most_common(10)
    top_after = final_family_counts.most_common(10)
    lines = [
        "# Campaign Family Filtered Dataset Report",
        "",
        "## 1. Starting Dataset Counts",
        "",
        f"- Total rows: {len(rows):,}",
        f"- Ham rows: {start_counts.get('ham', 0):,}",
        f"- Smishing rows: {start_counts.get('smishing', 0):,}",
        "",
        "## 2. Row 9227 Finding",
        "",
        "Row 9226/9227 onward had many SMS Phishing Dataset rows with repeated usdtferc/account-reset/login-code/remaining-value templates.",
        f"- Row 9200+ repeated-family rows found: {row9227_repeats:,}",
        f"- `family_usdtferc_account_reset` found before filtering: {known_before['family_usdtferc_account_reset']:,}",
        f"- `family_usdtferc_account_reset` excluded: {usdtferc_excluded:,}",
        f"- `family_usdtferc_account_reset` kept after filtering: {known_after['family_usdtferc_account_reset']:,}",
        "",
        "## 3. Campaign Families Found",
        "",
        f"- Total strong campaign families before filtering: {len(before_family_counts):,}",
        f"- Largest family before filtering: {max(before_family_counts.values() or [0]):,}",
        f"- Total strong campaign families after filtering: {len(final_family_counts):,}",
        f"- Largest family after filtering: {max(final_family_counts.values() or [0]):,}",
        "",
        "| largest before family | rows |",
        "| --- | ---: |",
    ]
    for key, value in top_before:
        lines.append(f"| `{key[:120]}` | {value:,} |")
    lines += ["", "| largest after family | rows |", "| --- | ---: |"]
    for key, value in top_after:
        lines.append(f"| `{key[:120]}` | {value:,} |")
    lines += [
        "",
        "## 4. Family Cap Rules Used",
        "",
        "- Default repeated-family cap: keep max 3 rows per `strong_campaign_family_key`.",
        "- Very large families, including size >= 20, >= 100, and >= 500, remain capped at 3.",
        "- Explicit usdtferc, TRXM, usdtrxm, and broad crypto login-balance families are capped at 3.",
        "",
        "## 5. Replacement Results",
        "",
        f"- Excluded campaign repeats: {campaign_repeat_excluded:,}",
        f"- Other weak-signal smishing rows archived: {weak_signal_excluded:,}",
        f"- Replacements accepted: {replacements_accepted:,}",
        f"- Replacements unavailable: {unavailable:,}",
        f"- Replacements skipped due to duplication: {duplicate_skips:,}",
        f"- Replacements skipped due to being same family: {same_family_skips:,}",
        f"- Replacements skipped due to campaign cap: {campaign_cap_skips:,}",
        f"- Replacements skipped due to raw quality: {skip_reasons.get('raw_unavailable', 0) + skip_reasons.get('bad_raw_status', 0) + skip_reasons.get('empty_raw', 0) + skip_reasons.get('angle_bracket_placeholder', 0):,}",
        f"- Replacements skipped due to weak signal: {skip_reasons.get('weak_or_bad_smishing_signal', 0):,}",
        f"- Final row count: {len(final):,}",
        "",
        "## 6. Final Dataset Counts",
        "",
        f"- Total rows: {len(final):,}",
        f"- Ham rows: {final_counts.get('ham', 0):,}",
        f"- Smishing rows: {final_counts.get('smishing', 0):,}",
        f"- Largest remaining family size: {max(final_family_counts.values() or [0]):,}",
        f"- `family_usdtferc_account_reset` remaining: {known_after['family_usdtferc_account_reset']:,}",
        f"- `family_trxm_login_balance` remaining: {known_after['family_trxm_login_balance']:,}",
        f"- `family_usdtrxm_login_code` remaining: {known_after['family_usdtrxm_login_code']:,}",
        f"- `family_crypto_login_balance` remaining: {known_after['family_crypto_login_balance']:,}",
        "",
        "## 7. Validation",
        "",
        f"- Empty `message_raw` rows: {empty_left:,}",
        f"- Smishing placeholder-token rows: {placeholder_left:,}",
        f"- Smishing `raw_text_available=False` rows: {raw_unavailable_left:,}",
        f"- Smishing `raw_text_status=already_redacted` rows: {already_redacted_left:,}",
        f"- Duplicate raw keys: {duplicate_raw_left:,}",
        f"- Duplicate clean keys: {duplicate_clean_left:,}",
        f"- Angry-reply smishing patterns: {angry_left:,}",
        f"- Weak/no smishing-signal rows: {weak_left:,}",
        f"- Families over cap: {len(over_cap):,}",
        f"- Ham rows unchanged by content fields: {start_counts.get('ham', 0) == final_counts.get('ham', 0)}",
        f"- Excluded rows archived: {len(excluded):,}",
        f"- Replacement decisions logged: {len(logs):,}",
        "",
        "## 8. Thesis Methodology Note",
        "",
        "To reduce campaign memorization, repeated smishing campaign families were detected using aggressive normalization and explicit campaign-family rules. Near-identical variants differing only in codes, balances, domains, suffixes, or user-specific values were capped. Excluded campaign repeats were replaced only with raw-available, SMS-like, deduplicated smishing candidates from the larger acquisition pool. No synthetic smishing messages were generated.",
        "",
        "## Files Generated",
        "",
        f"- `{FILTERED_OUT.relative_to(ROOT)}`",
        f"- `{LOG_OUT.relative_to(ROOT)}`",
        f"- `{EXCLUDED_OUT.relative_to(ROOT)}`",
        f"- `{REPORT.relative_to(ROOT)}`",
        "",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"input dataset path: {INPUT.relative_to(ROOT)}")
    print(f"rows inspected: {len(rows)}")
    print(f"row 9227 section repeated-family count: {row9227_repeats}")
    print(f"largest campaign family before filtering: {max(before_family_counts.values() or [0])}")
    print(f"campaign repeats excluded: {campaign_repeat_excluded}")
    print(f"replacements accepted: {replacements_accepted}")
    print(f"replacements unavailable: {unavailable}")
    print(f"largest campaign family after filtering: {max(final_family_counts.values() or [0])}")
    print(f"final row count: {len(final)}")
    print(f"final ham/smishing counts: ham={final_counts.get('ham', 0)}, smishing={final_counts.get('smishing', 0)}")
    print(f"output files: {FILTERED_OUT.relative_to(ROOT)}, {LOG_OUT.relative_to(ROOT)}, {EXCLUDED_OUT.relative_to(ROOT)}")
    print(f"report files: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
