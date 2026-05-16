"""Build a content-quality filtered strict raw dataset with smishing replacements."""

from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict, deque
from pathlib import Path

from audit_smishing_content_quality import ABUSIVE_REPLY_RE, classify, score_smishing
from audit_strict_raw_text_quality import ANGLE_PLACEHOLDER_RE, sms_likeness
from classify_raw_text_availability import is_rejected, is_smishing_label
from detect_smishing_campaign_templates import campaign_template_key, cap_for
from verify_and_add_raw_clean_text_columns import clean_cell, clean_message


ROOT = Path(__file__).resolve().parents[1]
STRICT_INPUT = ROOT / "data" / "organized" / "raw_quality" / "combined_public_thesis_sources_deduped_strict_raw.csv"
FLAGS_INPUT = ROOT / "data" / "organized" / "content_quality" / "smishing_content_quality_flags.csv"
GROUPS_INPUT = ROOT / "data" / "organized" / "content_quality" / "smishing_campaign_template_groups.csv"
REPEATS_INPUT = ROOT / "data" / "organized" / "content_quality" / "smishing_campaign_template_repeats.csv"
CANDIDATES_INPUT = ROOT / "data" / "organized" / "raw_recovery" / "collected_smishing_candidates_raw_classified.csv"

OUT_DIR = ROOT / "data" / "organized" / "content_quality"
FILTERED_OUT = OUT_DIR / "combined_public_thesis_sources_content_filtered.csv"
REMOVED_OUT = OUT_DIR / "content_removed_archive.csv"
LOG_OUT = OUT_DIR / "content_replacement_log.csv"
REPORT = ROOT / "reports" / "content_quality_filtered_dataset_report.md"

ADDED = [
    "content_quality_status",
    "content_quality_flags",
    "smishing_signal_score",
    "non_smishing_reason",
    "suggested_action",
    "campaign_template_key",
    "campaign_cluster_id",
    "campaign_cluster_size",
    "campaign_duplicate_status",
    "is_campaign_representative",
    "campaign_representative_reason",
    "content_filter_status",
    "content_filter_reason",
    "content_replacement_candidate_id",
    "removed_original_unified_id",
]

LOG_FIELDS = [
    "removed_unified_id",
    "removed_message_raw",
    "removed_reason",
    "replacement_candidate_id",
    "replacement_message_raw",
    "replacement_source_name",
    "replacement_dataset_name",
    "replacement_campaign_template_key",
    "replacement_reason",
    "duplicate_check_status",
    "notes",
]


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as h:
        r = csv.DictReader(h)
        return list(r), list(r.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=list(dict.fromkeys(fields)), extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def norm_key(text: str) -> str:
    return re.sub(r"\s+", " ", clean_message(text or "").lower()).strip()


def strict_raw_ok(text: str) -> bool:
    return bool(clean_cell(text)) and not ANGLE_PLACEHOLDER_RE.search(text or "")


def candidate_english(candidate: dict[str, str]) -> bool:
    lang = clean_cell(candidate.get("language")).lower()
    notes = clean_cell(candidate.get("candidate_raw_quality_notes")).lower()
    return lang in {"english", ""} or "english inferred" in notes


def candidate_ok(candidate: dict[str, str]) -> tuple[bool, str]:
    raw = clean_cell(candidate.get("candidate_raw_text"))
    if candidate.get("candidate_raw_text_available") != "True":
        return False, "raw_unavailable"
    if candidate.get("candidate_raw_text_status") not in {"original_looking_raw", "original_unredacted"}:
        return False, "bad_raw_status"
    if not is_smishing_label(candidate):
        return False, "not_smishing_label"
    if is_rejected(candidate):
        return False, "rejected"
    if not strict_raw_ok(raw):
        return False, "placeholder_or_empty_raw"
    if not candidate_english(candidate):
        return False, "non_english"
    if sms_likeness(raw) == "possible_report_or_article_text":
        return False, "report_text"
    score, flags = score_smishing(raw)
    if score < 2 or ABUSIVE_REPLY_RE.search(raw):
        return False, "weak_or_bad_smishing_signal"
    if not clean_cell(candidate.get("candidate_clean_text")):
        return False, "empty_clean"
    if not (clean_cell(candidate.get("source_name")) or clean_cell(candidate.get("dataset_name"))):
        return False, "missing_traceability"
    return True, "ok"


def annotate_campaign(row: dict[str, str], key_counts: Counter[str]) -> None:
    key = campaign_template_key(row.get("message_raw", ""))
    key_counts[key] += 1
    row["campaign_template_key"] = key
    row["campaign_cluster_id"] = ""
    row["campaign_cluster_size"] = str(key_counts[key])
    row["campaign_duplicate_status"] = "unique_campaign" if key_counts[key] == 1 else "campaign_representative"
    row["is_campaign_representative"] = "True"
    row["campaign_representative_reason"] = "accepted in content-quality filtered dataset"


def log_row(removed: dict[str, str], candidate: dict[str, str] | None, reason: str, status: str, notes: str) -> dict[str, str]:
    return {
        "removed_unified_id": removed.get("unified_id", ""),
        "removed_message_raw": removed.get("message_raw", ""),
        "removed_reason": reason,
        "replacement_candidate_id": clean_cell(candidate.get("id")) if candidate else "",
        "replacement_message_raw": clean_cell(candidate.get("candidate_raw_text")) if candidate else "",
        "replacement_source_name": clean_cell(candidate.get("source_name")) if candidate else "",
        "replacement_dataset_name": clean_cell(candidate.get("dataset_name")) if candidate else "",
        "replacement_campaign_template_key": campaign_template_key(candidate.get("candidate_raw_text", "")) if candidate else "",
        "replacement_reason": status,
        "duplicate_check_status": status,
        "notes": notes,
    }


def make_replacement(removed: dict[str, str], candidate: dict[str, str]) -> dict[str, str]:
    raw = clean_cell(candidate.get("candidate_raw_text"))
    clean = clean_cell(candidate.get("candidate_clean_text")) or clean_message(raw)
    cid = clean_cell(candidate.get("id"))
    row = dict(removed)
    row["unified_id"] = f"content_replacement_{cid}"
    row["source_name"] = clean_cell(candidate.get("source_name"))
    row["dataset_name"] = clean_cell(candidate.get("dataset_name"))
    row["source_group"] = "content_quality_replacement_91k_pool"
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
    row["raw_lookup_status"] = "replaced_from_91k_pool"
    row["raw_lookup_notes"] = "Content-quality replacement from raw-available 91k candidate pool."
    row["content_filter_status"] = "replacement_accepted"
    row["content_filter_reason"] = "replaced removed smishing row with raw-available content-quality candidate"
    row["content_replacement_candidate_id"] = cid
    row["removed_original_unified_id"] = removed.get("unified_id", "")
    cq = classify({"message_raw": raw})
    for col in ["content_quality_status", "content_quality_flags", "smishing_signal_score", "non_smishing_reason", "suggested_action"]:
        row[col] = cq[col]
    return row


def main() -> None:
    strict_rows, strict_fields = read_csv(STRICT_INPUT)
    flags, _ = read_csv(FLAGS_INPUT)
    repeats, _ = read_csv(REPEATS_INPUT)
    candidates, _ = read_csv(CANDIDATES_INPUT)
    flags_by_id = {r["unified_id"]: r for r in flags}
    campaign_by_id = {r["unified_id"]: r for r in repeats}
    excluded_campaign_ids = {r["unified_id"] for r in repeats if r.get("campaign_duplicate_status") == "campaign_repeat_excluded"}

    final: list[dict[str, str]] = []
    removed: list[dict[str, str]] = []
    logs: list[dict[str, str]] = []
    raw_keys: set[str] = set()
    clean_keys: set[str] = set()
    campaign_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()

    def accept(row: dict[str, str]) -> bool:
        rk, ck = norm_key(row.get("message_raw", "")), norm_key(row.get("message_clean", ""))
        key = campaign_template_key(row.get("message_raw", ""))
        if not rk or not ck or rk in raw_keys or ck in clean_keys:
            return False
        if row.get("normalized_label") == "smishing" and campaign_counts[key] >= cap_for(campaign_counts[key] + 1):
            return False
        raw_keys.add(rk); clean_keys.add(ck)
        annotate_campaign(row, campaign_counts)
        final.append(row)
        return True

    for row in strict_rows:
        out = dict(row)
        if row.get("normalized_label") == "ham":
            out["content_filter_status"] = "kept_ham_passthrough"
            out["content_filter_reason"] = "ham rows copied through in this step"
            accept(out)
            continue
        flag = flags_by_id.get(row["unified_id"], {})
        camp = campaign_by_id.get(row["unified_id"], {})
        for col in ["content_quality_status", "content_quality_flags", "smishing_signal_score", "non_smishing_reason", "suggested_action"]:
            out[col] = flag.get(col, "pass_likely_smishing" if col == "content_quality_status" else "")
        for col in ["campaign_template_key", "campaign_cluster_id", "campaign_cluster_size", "campaign_duplicate_status", "is_campaign_representative", "campaign_representative_reason"]:
            out[col] = camp.get(col, out.get(col, ""))
        remove = False
        reason = ""
        if out["content_quality_status"] == "fail_obvious_non_smishing":
            remove = True; reason = out.get("non_smishing_reason") or "obvious_non_smishing"
        elif out["content_quality_status"] == "review_possible_report_text":
            remove = True; reason = "possible_report_text"
        elif row["unified_id"] in excluded_campaign_ids:
            remove = True; reason = "campaign_repeat_excluded"
        elif int(out.get("smishing_signal_score") or score_smishing(row.get("message_raw", ""))[0]) <= 0:
            remove = True; reason = "weak_or_no_smishing_signal"
        elif not strict_raw_ok(row.get("message_raw", "")):
            remove = True; reason = "strict_raw_failure"
        if remove:
            out["content_filter_status"] = "removed"
            out["content_filter_reason"] = reason
            removed.append(out)
        else:
            out["content_filter_status"] = "kept"
            out["content_filter_reason"] = "passed content-quality and campaign cap"
            if not accept(out):
                out["content_filter_status"] = "removed"
                out["content_filter_reason"] = "duplicate_or_campaign_cap_during_build"
                removed.append(out)

    usable_candidates = []
    skip_reasons = Counter()
    for c in candidates:
        ok, why = candidate_ok(c)
        if ok:
            usable_candidates.append(c)
        else:
            skip_reasons[why] += 1
    usable_candidates.sort(key=lambda c: (-score_smishing(c.get("candidate_raw_text", ""))[0], int(c.get("candidate_raw_quality_score") or 0) * -1, len(c.get("candidate_raw_text", ""))))
    candidate_queue = deque(usable_candidates)

    selected: set[str] = set()
    replacements = 0
    duplicate_skips = 0
    campaign_skips = 0
    for rem in [r for r in removed if r.get("normalized_label") == "smishing"]:
        chosen = None
        deferred = deque()
        while candidate_queue:
            c = candidate_queue.popleft()
            cid = clean_cell(c.get("id"))
            if cid in selected:
                continue
            raw, clean = c["candidate_raw_text"], c["candidate_clean_text"]
            rk, ck = norm_key(raw), norm_key(clean)
            if rk in raw_keys or ck in clean_keys:
                duplicate_skips += 1
                continue
            camp_key = campaign_template_key(raw)
            if campaign_counts[camp_key] >= cap_for(campaign_counts[camp_key] + 1):
                campaign_skips += 1
                continue
            chosen = c
            break
        if deferred:
            candidate_queue.extendleft(reversed(deferred))
        if not chosen:
            logs.append(log_row(rem, None, rem.get("content_filter_reason", ""), "replacement_unavailable", "No acceptable non-duplicate content-quality replacement found."))
            continue
        rep = make_replacement(rem, chosen)
        if accept(rep):
            selected.add(clean_cell(chosen.get("id")))
            replacements += 1
            source_counts[clean_cell(chosen.get("source_name")) or clean_cell(chosen.get("dataset_name"))] += 1
            category_counts[clean_cell(chosen.get("scam_category"))] += 1
            logs.append(log_row(rem, chosen, rem.get("content_filter_reason", ""), "accepted", "Raw-available SMS-like smishing replacement accepted."))
        else:
            logs.append(log_row(rem, chosen, rem.get("content_filter_reason", ""), "post_accept_rejected", "Candidate failed final duplicate/campaign cap check."))

    fields = strict_fields + ADDED
    write_csv(FILTERED_OUT, final, fields)
    write_csv(REMOVED_OUT, removed, fields)
    write_csv(LOG_OUT, logs, LOG_FIELDS)

    final_counts = Counter(r.get("normalized_label", "") for r in final)
    largest = max(campaign_counts.values()) if campaign_counts else 0
    smishing_campaign_counts = Counter(r.get("campaign_template_key", "") for r in final if r.get("normalized_label") == "smishing")
    angry_left = sum(1 for r in final if r.get("normalized_label") == "smishing" and ABUSIVE_REPLY_RE.search(r.get("message_raw", "")))
    low_score_left = sum(1 for r in final if r.get("normalized_label") == "smishing" and int(r.get("smishing_signal_score") or score_smishing(r.get("message_raw", ""))[0]) <= 0)
    source_dist = Counter(r.get("source_name", "") for r in final)
    ratio = f"{final_counts.get('smishing',0)/final_counts.get('ham',1):.2f}:1 smishing:ham"
    report_lines = [
        "# Content Quality Filtered Dataset Report",
        "",
        "## 1. Purpose",
        "",
        "This pass removes obvious non-smishing artifacts and caps repeated campaign templates to reduce memorization risk.",
        "",
        "## 2. Starting Dataset",
        "",
        f"- Total rows: {len(strict_rows):,}",
        f"- Ham count: {sum(r.get('normalized_label')=='ham' for r in strict_rows):,}",
        f"- Smishing count: {sum(r.get('normalized_label')=='smishing' for r in strict_rows):,}",
        "",
        "## 3. Non-Smishing Content Flags",
        "",
        f"- Obvious non-smishing count: {sum(r.get('content_quality_status')=='fail_obvious_non_smishing' for r in flags):,}",
        f"- Abusive/reply count: {sum('abusive_or_reply_text' in r.get('content_quality_flags','') for r in flags):,}",
        f"- Report/commentary count: {sum(r.get('content_quality_status')=='review_possible_report_text' for r in flags):,}",
        f"- Possible spam-not-smishing count: {sum(r.get('content_quality_status')=='review_possible_spam_not_smishing' for r in flags):,}",
        "",
        "## 4. Campaign/Template Duplicate Analysis",
        "",
        f"- Number of campaign clusters: {len(smishing_campaign_counts):,}",
        f"- Number of repeated-template rows: {len(repeats):,}",
        f"- Largest campaign cluster size before filtering: {max([int(r.get('campaign_cluster_size') or 1) for r in repeats] or [1]):,}",
        f"- Number of rows excluded by campaign cap: {sum(r.get('content_filter_reason')=='campaign_repeat_excluded' for r in removed):,}",
        "- Cap rule used: max 3 for large/medium campaigns, 1-2 for small repeated campaigns.",
        "",
        "## 5. Replacement From 91k Pool",
        "",
        f"- Replacement candidates inspected: {len(candidates):,}",
        f"- Replacements accepted: {replacements:,}",
        f"- Replacements skipped as duplicates: {duplicate_skips:,}",
        f"- Replacements skipped due to weak smishing signal: {skip_reasons.get('weak_or_bad_smishing_signal',0):,}",
        f"- Replacements skipped due to raw quality: {skip_reasons.get('placeholder_or_empty_raw',0)+skip_reasons.get('raw_unavailable',0)+skip_reasons.get('bad_raw_status',0):,}",
        f"- Replacements skipped due to campaign repetition: {campaign_skips:,}",
        "",
        "## 6. Final Dataset",
        "",
        f"- Total rows: {len(final):,}",
        f"- Ham count: {final_counts.get('ham',0):,}",
        f"- Smishing count: {final_counts.get('smishing',0):,}",
        f"- Class ratio: {ratio}",
        f"- Largest remaining campaign cluster size: {largest:,}",
        f"- Number of rows remaining from original strict raw dataset: {len(final)-replacements:,}",
        f"- Number of rows replaced from 91k: {replacements:,}",
        "",
        "### Source Distribution",
        "",
        "| source_name | rows |",
        "| --- | --- |",
    ]
    for k, v in source_dist.most_common(20):
        report_lines.append(f"| {k or '(blank)'} | {v} |")
    report_lines += [
        "",
        "### Validation",
        "",
        f"- Empty `message_raw`: {sum(not clean_cell(r.get('message_raw')) for r in final)}",
        f"- Angle-bracket placeholders in `message_raw`: {sum(bool(ANGLE_PLACEHOLDER_RE.search(r.get('message_raw',''))) for r in final)}",
        f"- `raw_text_available=False`: {sum(r.get('raw_text_available')!='True' for r in final)}",
        f"- `raw_text_status=already_redacted`: {sum(r.get('raw_text_status')=='already_redacted' for r in final)}",
        f"- Duplicate raw keys: {len(final)-len(set(norm_key(r.get('message_raw','')) for r in final))}",
        f"- Duplicate clean keys: {len(final)-len(set(norm_key(r.get('message_clean','')) for r in final))}",
        f"- Campaign keys over cap: {sum(1 for k,v in campaign_counts.items() if v > cap_for(v))}",
        f"- Obvious angry-reply patterns remaining: {angry_left}",
        f"- Smishing rows with signal score <= 0: {low_score_left}",
        f"- Removed rows archived: {len(removed):,}",
        f"- Replacement log rows: {len(logs):,}",
        "",
        "## 7. Thesis Methodology Note",
        "",
        "After strict raw validation, an additional content-quality pass was applied to remove non-smishing artifacts such as replies to scammers, abusive responses, report/commentary text, and repeated campaign templates. Near-identical smishing templates were capped to reduce campaign memorization. Removed smishing rows were replaced only with raw-available, SMS-like, deduplicated smishing candidates from the larger acquisition pool. No synthetic smishing messages were generated.",
        "",
        "## 8. Files Generated",
        "",
        f"- `{FILTERED_OUT.relative_to(ROOT)}`",
        f"- `{REMOVED_OUT.relative_to(ROOT)}`",
        f"- `{LOG_OUT.relative_to(ROOT)}`",
        f"- `{REPORT.relative_to(ROOT)}`",
        "",
        "## 9. Recommended Next Step",
        "",
        "- Build the balanced model-ready dataset later.",
        "- Clean `message_clean` later.",
        "- Add manual service-like ham later.",
        "",
    ]
    REPORT.write_text("\n".join(report_lines), encoding="utf-8")

    print(f"Input dataset path: {STRICT_INPUT.relative_to(ROOT)}")
    print(f"Rows inspected: {len(strict_rows)}")
    print(f"Smishing rows inspected: {sum(r.get('normalized_label')=='smishing' for r in strict_rows)}")
    print(f"Obvious non-smishing rows removed: {sum(r.get('content_quality_status')=='fail_obvious_non_smishing' for r in removed)}")
    print(f"Campaign/template clusters found: {len(smishing_campaign_counts)}")
    print(f"Campaign repeat rows excluded: {sum(r.get('content_filter_reason')=='campaign_repeat_excluded' for r in removed)}")
    print(f"Replacements accepted from 91k: {replacements}")
    print(f"Replacements unavailable count: {sum(1 for l in logs if l['duplicate_check_status']=='replacement_unavailable')}")
    print(f"Final content-filtered row count: {len(final)}")
    print(f"Final ham/smishing counts: ham={final_counts.get('ham',0)}; smishing={final_counts.get('smishing',0)}")
    print(f"Largest remaining campaign cluster size: {largest}")
    print("Output file paths:")
    for p in [FILTERED_OUT, REMOVED_OUT, LOG_OUT]:
        print(f"- {p.relative_to(ROOT)}")
    print("Report file paths:")
    print(f"- {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
