"""Programmatically approve synthetic ham candidates while archiving rejects."""

from __future__ import annotations

import re
from collections import Counter

import pandas as pd

from final_dataset_build_utils import ARCHIVES_DIR, INTERIM_DIR, REPORTS_DIR, has_placeholder, normalize_for_overlap, read_csv, write_csv


IN_CSV = INTERIM_DIR / "synthetic_service_ham_generated.csv"
APPROVED_OUT = INTERIM_DIR / "synthetic_service_ham_approved.csv"
REJECTED_OUT = ARCHIVES_DIR / "synthetic_service_ham_rejected_archive.csv"
REPORT_OUT = REPORTS_DIR / "synthetic_ham_quality_report.md"

THREAT_RE = re.compile(r"\b(verify now|account (?:will be )?(?:locked|suspended|closed)|avoid account closure|urgent|immediately|final warning|limited time claim|free spin|casino|gambling|crypto investment)\b", re.I)
CREDENTIAL_RE = re.compile(r"\b(share|send|provide|reply with|enter)\b.{0,30}\b(otp|pin|password|credential)\b", re.I)
PROTECTIVE_SECRET_RE = re.compile(r"\b(do not|don't|never)\s+(?:share|send|provide|reply with|enter)\b.{0,40}\b(otp|pin|password|credential|code)\b", re.I)
SUSPICIOUS_LINK_RE = re.compile(r"\b(bit\.ly|tinyurl|t\.co|click now|click here to avoid)\b", re.I)


def reject_reason(row: pd.Series, seen_raw: set[str], seen_clean: set[str]) -> str:
    raw = str(row.get("message_raw", "") or "").strip()
    clean = str(row.get("message_clean", "") or "").strip()
    raw_key = normalize_for_overlap(raw)
    clean_key = normalize_for_overlap(clean)
    if not raw or not clean:
        return "empty_raw_or_clean"
    if len(raw) > 320:
        return "too_long"
    if raw_key in seen_raw or clean_key in seen_clean:
        return "exact_duplicate"
    if THREAT_RE.search(raw) or THREAT_RE.search(clean):
        return "smishing_like_threat_or_scam_urgency"
    if (CREDENTIAL_RE.search(raw) or CREDENTIAL_RE.search(clean)) and not (PROTECTIVE_SECRET_RE.search(raw) or PROTECTIVE_SECRET_RE.search(clean)):
        return "asks_for_sensitive_secret"
    if SUSPICIOUS_LINK_RE.search(raw):
        return "suspicious_link_language"
    if has_placeholder(raw):
        return "raw_contains_placeholders"
    if "low quality" in str(row.get("notes", "")).lower():
        return "low_quality_template"
    return ""


def main() -> None:
    df = read_csv(IN_CSV)
    approved = []
    rejected = []
    seen_raw: set[str] = set()
    seen_clean: set[str] = set()
    for _, row in df.iterrows():
        reason = reject_reason(row, seen_raw, seen_clean)
        if reason:
            item = row.to_dict()
            item["rejection_reason"] = reason
            rejected.append(item)
            continue
        item = row.to_dict()
        item["review_status"] = "approved_synthetic"
        item["label_status"] = "synthetic_ham_approved"
        approved.append(item)
        seen_raw.add(normalize_for_overlap(item["message_raw"]))
        seen_clean.add(normalize_for_overlap(item["message_clean"]))

    app_df = pd.DataFrame(approved)
    rej_df = pd.DataFrame(rejected)
    write_csv(app_df, APPROVED_OUT)
    write_csv(rej_df, REJECTED_OUT)
    reason_counts = Counter(rej_df["rejection_reason"]) if not rej_df.empty else Counter()
    cat_counts = Counter(app_df["service_category"]) if not app_df.empty else Counter()
    lines = [
        "# Synthetic Ham Quality Report",
        "",
        "Synthetic ham messages were generated from manually approved legitimate service-message templates. Unlike collected public data, these messages are synthetic and contain fake/generated values in the raw text field. A privacy-safe cleaned version was also generated for each synthetic message. Synthetic rows are clearly marked with is_synthetic=True and data_origin=synthetic_template.",
        "",
        f"- Generated candidates: {len(df)}",
        f"- Approved synthetic rows: {len(app_df)}",
        f"- Rejected synthetic rows: {len(rej_df)}",
        "",
        "## Approved By Category",
        "",
        "| Category | Count |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {cat} | {count} |" for cat, count in sorted(cat_counts.items()))
    lines.extend(["", "## Rejections", "", "| Reason | Count |", "| --- | ---: |"])
    lines.extend(f"| {reason} | {count} |" for reason, count in sorted(reason_counts.items()))
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Synthetic ham approved: {len(app_df)}")
    print(f"Synthetic ham rejected: {len(rej_df)}")
    print(f"Wrote: {APPROVED_OUT}")
    print(f"Archived: {REJECTED_OUT}")
    print(f"Report: {REPORT_OUT}")


if __name__ == "__main__":
    main()
