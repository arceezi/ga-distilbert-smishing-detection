"""Validate the research-backed V3 final dataset."""

from __future__ import annotations

from collections import Counter

import pandas as pd

from final_dataset_build_utils import FINAL_DIR, PUBLIC_DATASET, REPORTS_DIR, read_csv
from research_synthetic_ham_common import BANNED_RE, exact_key, normalize_family_key


IN_CSV = FINAL_DIR / "dataset_v3_public_manual_research_synthetic_ham_balanced.csv"
REPORT_OUT = REPORTS_DIR / "research_backed_v3_validation_report.md"


def bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "yes"])


def main() -> None:
    df = read_csv(IN_CSV)
    public = read_csv(PUBLIC_DATASET)
    issues = []
    warnings = []
    counts = Counter(df["normalized_label"])
    synth_mask = bool_series(df["is_synthetic"])
    synth = df[synth_mask].copy()
    synth_ham = synth[synth["normalized_label"].eq("ham")].copy()
    smish = df[df["normalized_label"].eq("smishing")].copy()
    manual = df[df["data_origin"].eq("manual_real")].copy()
    ham = df[df["normalized_label"].eq("ham")].copy()

    if counts["ham"] != 5272:
        issues.append(f"ham count is {counts['ham']}, expected 5272")
    if counts["smishing"] != 5272:
        issues.append(f"smishing count is {counts['smishing']}, expected 5272")
    if len(df) != 10544:
        issues.append(f"total count is {len(df)}, expected 10544")
    if (synth_mask & df["normalized_label"].eq("smishing")).any():
        issues.append("synthetic smishing rows found")
    if not synth.empty and not synth["data_origin"].eq("synthetic_template").all():
        issues.append("synthetic rows not all data_origin=synthetic_template")
    if not manual.empty and not manual["data_origin"].eq("manual_real").all():
        issues.append("manual rows not all marked data_origin=manual_real")
    if not synth_ham.empty:
        missing_basis = synth_ham["template_basis"].astype(str).str.strip().eq("") & synth_ham["research_source_id"].astype(str).str.strip().eq("")
        if missing_basis.any():
            issues.append(f"synthetic rows missing template_basis or research_source_id: {int(missing_basis.sum())}")
        banned = synth_ham["message_raw"].astype(str).str.contains(BANNED_RE) | synth_ham["message_clean"].astype(str).str.contains(BANNED_RE)
        if banned.any():
            issues.append(f"banned phrases in synthetic ham: {int(banned.sum())}")
    if df["message_raw"].astype(str).str.strip().eq("").any():
        issues.append("empty message_raw found")
    if df["message_clean"].astype(str).str.strip().eq("").any():
        issues.append("empty message_clean found")

    raw_keys = df["message_raw"].map(exact_key)
    clean_keys = df["message_clean"].map(exact_key)
    raw_dupes = int(raw_keys[raw_keys.ne("")].duplicated().sum())
    clean_dupes = int(clean_keys[clean_keys.ne("")].duplicated().sum())
    synth_raw_dupes = int(synth_ham["message_raw"].map(exact_key).duplicated().sum()) if not synth_ham.empty else 0
    synth_clean_dupes = int(synth_ham["message_clean"].map(exact_key).duplicated().sum()) if not synth_ham.empty else 0
    if synth_raw_dupes:
        issues.append(f"synthetic exact duplicate raw keys: {synth_raw_dupes}")
    if synth_clean_dupes:
        issues.append(f"synthetic exact duplicate clean keys: {synth_clean_dupes}")
    if raw_dupes:
        warnings.append(f"dataset-level duplicate raw keys, likely inherited public/manual rows: {raw_dupes}")
    if clean_dupes:
        warnings.append(f"dataset-level duplicate clean keys, likely inherited public/manual rows: {clean_dupes}")

    family_counts = Counter(synth_ham["synthetic_template_family_id"]) if not synth_ham.empty else Counter()
    family_over = {k: v for k, v in family_counts.items() if k and v > 100}
    if family_over:
        issues.append(f"template family cap exceeded: {family_over}")
    family_key_counts = Counter(synth_ham["message_raw"].map(normalize_family_key)) if not synth_ham.empty else Counter()
    key_over = {k: v for k, v in family_key_counts.items() if k and v > 20}
    if key_over:
        issues.append(f"normalized family key cap exceeded: {len(key_over)} keys")

    uci_ham = int(ham["source_name"].eq("UCI SMS Spam Collection").sum())
    mishra_ham = int(ham["source_name"].eq("Mishra & Soni").sum())
    manual_ham = int(ham["data_origin"].eq("manual_real").sum())
    synthetic_ham = int(ham["data_origin"].eq("synthetic_template").sum())
    uci_pct = uci_ham / len(ham) * 100 if len(ham) else 0
    public_smish_ids = set(public.loc[public["normalized_label"].eq("smishing"), "unified_id"])
    smish_nonpublic = int((~smish["unified_id"].isin(public_smish_ids)).sum()) if "unified_id" in smish.columns else len(smish)
    if smish_nonpublic:
        issues.append(f"smishing rows not found in public source ids: {smish_nonpublic}")

    status = "PASSED" if not issues else "FAILED"
    lines = [
        "# Research-Backed V3 Validation Report",
        "",
        f"- Validation status: {status}",
        f"- Ham: {counts['ham']}",
        f"- Smishing: {counts['smishing']}",
        f"- Total: {len(df)}",
        f"- Manual real ham: {manual_ham}",
        f"- Research-backed synthetic ham: {synthetic_ham}",
        f"- Mishra ham: {mishra_ham}",
        f"- UCI ham: {uci_ham}",
        f"- UCI ham share: {uci_pct:.2f}%",
        f"- Synthetic duplicate raw keys: {synth_raw_dupes}",
        f"- Synthetic duplicate clean keys: {synth_clean_dupes}",
        "",
        "## Issues",
        "",
    ]
    lines.extend(f"- {issue}" for issue in issues) if issues else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {warning}" for warning in warnings) if warnings else lines.append("- None")
    lines.extend(["", "## Synthetic Category Distribution", "", "| Category | Count |", "| --- | ---: |"])
    lines.extend(f"| {cat} | {count} |" for cat, count in sorted(Counter(synth_ham["service_category"]).items()))
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Validation status: {status}")
    print(f"Final V3 composition: ham={counts['ham']}, smishing={counts['smishing']}, total={len(df)}")
    print(f"Manual real ham count: {manual_ham}")
    print(f"Research-backed synthetic ham count: {synthetic_ham}")
    print(f"Mishra ham count: {mishra_ham}")
    print(f"UCI ham count: {uci_ham}")
    print(f"UCI ham percentage: {uci_pct:.2f}%")
    print(f"Smishing count: {counts['smishing']}")
    print(f"Report: {REPORT_OUT}")
    if issues:
        print("Validation issues:")
        for issue in issues:
            print(f"- {issue}")


if __name__ == "__main__":
    main()
