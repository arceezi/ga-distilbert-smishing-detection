"""Audit and cap repeated synthetic ham template families."""

from __future__ import annotations

from collections import Counter

import pandas as pd

from final_dataset_build_utils import ARCHIVES_DIR, INTERIM_DIR, REPORTS_DIR, read_csv, write_csv
from research_synthetic_ham_common import normalize_family_key


IN_CSV = INTERIM_DIR / "synthetic_service_ham_research_backed_generated.csv"
OUT_CSV = INTERIM_DIR / "synthetic_service_ham_family_capped.csv"
ARCHIVE_OUT = ARCHIVES_DIR / "synthetic_ham_family_excluded_archive.csv"
REPORT_OUT = REPORTS_DIR / "synthetic_ham_family_cap_report.md"


BIG_BRAND_OTP = {"Microsoft", "Google", "Apple", "Amazon", "PayPal"}


def infer_brand(text: str) -> str:
    for brand in sorted(BIG_BRAND_OTP | {"BDO", "BPI", "GCash", "Maya", "Globe", "Smart", "UPS", "USPS", "DHL", "DHL Express"}):
        if brand.lower() in str(text).lower():
            return brand
    return ""


def main() -> None:
    df = read_csv(IN_CSV)
    keep = []
    drop = []
    template_counts = Counter()
    family_counts = Counter()
    otp_brand_counts = Counter()
    generic_otp_counts = Counter()
    family_key_counts = Counter()

    for _, row in df.iterrows():
        item = row.to_dict()
        raw = item.get("message_raw", "")
        template_id = item.get("synthetic_template_id", "")
        family_id = item.get("synthetic_template_family_id", "") or template_id
        category = item.get("service_category", "")
        family_key = normalize_family_key(raw)
        brand = infer_brand(raw)
        reason = ""
        if template_counts[template_id] >= 15:
            reason = "max_15_per_exact_template"
        elif family_counts[family_id] >= 100:
            reason = "max_100_per_template_family"
        elif brand in BIG_BRAND_OTP and category in {"fixed_format_big_brand_otp", "generic_account_verification"} and otp_brand_counts[brand] >= 20:
            reason = "max_20_per_brand_specific_otp_family"
        elif not brand and "otp" in raw.lower() and generic_otp_counts[family_key] >= 30:
            reason = "max_30_per_generic_otp_family"
        elif family_key_counts[family_key] >= 20:
            reason = "normalized_family_key_repeat_cap"

        if reason:
            item["family_cap_exclusion_reason"] = reason
            item["normalized_synthetic_family_key"] = family_key
            drop.append(item)
            continue
        item["normalized_synthetic_family_key"] = family_key
        keep.append(item)
        template_counts[template_id] += 1
        family_counts[family_id] += 1
        family_key_counts[family_key] += 1
        if brand in BIG_BRAND_OTP and category in {"fixed_format_big_brand_otp", "generic_account_verification"}:
            otp_brand_counts[brand] += 1
        if not brand and "otp" in raw.lower():
            generic_otp_counts[family_key] += 1

    keep_df = pd.DataFrame(keep)
    drop_df = pd.DataFrame(drop, columns=list(df.columns) + ["family_cap_exclusion_reason", "normalized_synthetic_family_key"])
    write_csv(keep_df, OUT_CSV)
    write_csv(drop_df, ARCHIVE_OUT)
    reasons = Counter(drop_df["family_cap_exclusion_reason"]) if not drop_df.empty else Counter()
    lines = [
        "# Synthetic Ham Family Cap Report",
        "",
        f"- Input rows: {len(df)}",
        f"- Kept after caps: {len(keep_df)}",
        f"- Excluded by caps: {len(drop_df)}",
        "",
        "## Exclusions",
        "",
        "| Reason | Count |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {reason} | {count} |" for reason, count in sorted(reasons.items()))
    lines.extend(["", "## Category Counts After Caps", "", "| Category | Count |", "| --- | ---: |"])
    lines.extend(f"| {cat} | {count} |" for cat, count in sorted(Counter(keep_df["service_category"]).items()))
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Synthetic ham after family caps: {len(keep_df)}")
    print(f"Family-cap excluded: {len(drop_df)}")
    print(f"Wrote: {OUT_CSV}")
    print(f"Archive: {ARCHIVE_OUT}")
    print(f"Report: {REPORT_OUT}")


if __name__ == "__main__":
    main()
