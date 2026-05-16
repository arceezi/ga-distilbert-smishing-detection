"""Approve research-backed synthetic ham using stricter quality gates."""

from __future__ import annotations

from collections import Counter

import pandas as pd

from final_dataset_build_utils import ARCHIVES_DIR, INTERIM_DIR, REPORTS_DIR, read_csv, write_csv
from research_synthetic_ham_common import exact_key, normalize_family_key, quality_reject_reason


IN_CSV = INTERIM_DIR / "synthetic_service_ham_family_capped.csv"
APPROVED_OUT = INTERIM_DIR / "synthetic_service_ham_research_backed_approved.csv"
REJECTED_OUT = ARCHIVES_DIR / "synthetic_service_ham_research_backed_rejected_archive.csv"
REPORT_OUT = REPORTS_DIR / "research_backed_synthetic_ham_quality_report.md"


def main() -> None:
    df = read_csv(IN_CSV)
    approved = []
    rejected = []
    seen_raw: set[str] = set()
    seen_clean: set[str] = set()
    family_counts = Counter()
    template_counts = Counter()
    family_key_counts = Counter()

    for _, row in df.iterrows():
        item = row.to_dict()
        reason = quality_reject_reason(item, seen_raw, seen_clean)
        family_id = item.get("synthetic_template_family_id", "") or item.get("synthetic_template_id", "")
        template_id = item.get("synthetic_template_id", "")
        family_key = item.get("normalized_synthetic_family_key", "") or normalize_family_key(item.get("message_raw", ""))
        if not reason and template_counts[template_id] >= 15:
            reason = "template_cap_violation"
        if not reason and family_counts[family_id] >= 100:
            reason = "template_family_cap_violation"
        if not reason and family_key_counts[family_key] >= 20:
            reason = "normalized_family_key_cap_violation"
        if reason:
            item["rejection_reason"] = reason
            rejected.append(item)
            continue
        item["review_status"] = "approved_synthetic"
        item["label_status"] = "synthetic_ham_approved"
        approved.append(item)
        seen_raw.add(exact_key(item["message_raw"]))
        seen_clean.add(exact_key(item["message_clean"]))
        family_counts[family_id] += 1
        template_counts[template_id] += 1
        family_key_counts[family_key] += 1

    app_df = pd.DataFrame(approved)
    rej_df = pd.DataFrame(rejected, columns=list(df.columns) + ["rejection_reason"])
    write_csv(app_df, APPROVED_OUT)
    write_csv(rej_df, REJECTED_OUT)
    reason_counts = Counter(rej_df["rejection_reason"]) if not rej_df.empty else Counter()
    category_counts = Counter(app_df["service_category"]) if not app_df.empty else Counter()
    sample_accept = app_df["message_raw"].head(8).tolist() if not app_df.empty else []
    lines = [
        "# Research-Backed Synthetic Ham Quality Report",
        "",
        f"- Input after family caps: {len(df)}",
        f"- Approved synthetic rows: {len(app_df)}",
        f"- Rejected synthetic rows: {len(rej_df)}",
        "",
        "## Approved By Category",
        "",
        "| Category | Count |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {cat} | {count} |" for cat, count in sorted(category_counts.items()))
    lines.extend(["", "## Rejected Reasons", "", "| Reason | Count |", "| --- | ---: |"])
    lines.extend(f"| {reason} | {count} |" for reason, count in sorted(reason_counts.items()))
    lines.extend(["", "## Accepted Synthetic Examples", ""])
    lines.extend(f"- {msg}" for msg in sample_accept)
    lines.extend(
        [
            "",
            "Synthetic rows contain fake generated values in `message_raw` and privacy-safe placeholders in `message_clean`. They are generated ham candidates only, not collected real-world SMS.",
        ]
    )
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Synthetic ham approved: {len(app_df)}")
    print(f"Synthetic ham rejected: {len(rej_df)}")
    print(f"Wrote: {APPROVED_OUT}")
    print(f"Archive: {REJECTED_OUT}")
    print(f"Report: {REPORT_OUT}")


if __name__ == "__main__":
    main()
