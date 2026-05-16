"""Validate final combined dataset versions and print the final build summary."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pandas as pd

import re

from final_dataset_build_utils import FINAL_DIR, INTERIM_DIR, PUBLIC_DATASET, REPORTS_DIR, read_csv


DATASETS = {
    "V1": FINAL_DIR / "dataset_v1_public_real_only_balanced.csv",
    "V2": FINAL_DIR / "dataset_v2_public_plus_manual_ham_balanced.csv",
    "V3": FINAL_DIR / "dataset_v3_public_manual_synthetic_ham_balanced.csv",
}
REPORT_OUT = REPORTS_DIR / "final_combined_dataset_validation_report.md"


def bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1", "yes"])


def duplicate_count(series: pd.Series) -> int:
    keys = series.map(lambda value: re.sub(r"\s+", " ", re.sub(r"[^\w<>]+", " ", str(value or "").lower())).strip())
    keys = keys[keys.ne("")]
    return int(keys.duplicated().sum())


def validate_one(name: str, path: Path) -> tuple[dict[str, object], list[str], list[str]]:
    df = read_csv(path)
    issues = []
    warnings = []
    labels = set(df["normalized_label"].dropna().unique())
    if labels - {"ham", "smishing"}:
        issues.append(f"Unexpected labels: {sorted(labels)}")
    if df["normalized_label"].isin(["spam", "review"]).any():
        issues.append("Contains spam/review rows.")
    if df["message_raw"].astype(str).str.strip().eq("").any():
        issues.append("Contains empty message_raw.")
    if df["message_clean"].astype(str).str.strip().eq("").any():
        issues.append("Contains empty message_clean.")
    raw_dupes = duplicate_count(df["message_raw"])
    clean_dupes = duplicate_count(df["message_clean"])
    if raw_dupes:
        warnings.append(f"Duplicate normalized message_raw keys inherited or retained by source selection: {raw_dupes}")
    if clean_dupes:
        warnings.append(f"Duplicate normalized message_clean keys inherited or retained by source selection: {clean_dupes}")
    if df["source_name"].astype(str).str.strip().eq("").any() or df["dataset_name"].astype(str).str.strip().eq("").any():
        issues.append("Missing source traceability.")
    synth_mask = bool_series(df["is_synthetic"])
    if synth_mask.any() and not df.loc[synth_mask, "data_origin"].eq("synthetic_template").all():
        issues.append("Synthetic rows not consistently marked with data_origin=synthetic_template.")
    if df["data_origin"].eq("manual_real").any() and not df.loc[df["data_origin"].eq("manual_real"), "source_group"].eq("manual_curated_ham").all():
        issues.append("Manual rows have unexpected source_group.")
    if df["data_origin"].eq("public_real").any() and not df.loc[df["data_origin"].eq("public_real"), "is_synthetic"].astype(str).str.lower().isin(["false", "0", ""]).all():
        issues.append("Public rows marked synthetic.")
    if (synth_mask & df["normalized_label"].eq("smishing")).any():
        issues.append("Synthetic smishing found.")
    counts = Counter(df["normalized_label"])
    if counts["ham"] != counts["smishing"]:
        issues.append(f"Dataset is not balanced: ham={counts['ham']} smishing={counts['smishing']}")
    if name == "V3":
        if counts["ham"] != 5272 or counts["smishing"] != 5272:
            issues.append("V3 does not meet 5,272 / 5,272 target.")
        if len(df) != 10544:
            issues.append("V3 total is not 10,544.")
        if not df["data_origin"].eq("manual_real").any():
            issues.append("V3 missing manual ham.")
        if not synth_mask.any():
            issues.append("V3 missing synthetic ham.")
    ham = df[df["normalized_label"].eq("ham")]
    metrics = {
        "rows": len(df),
        "ham": counts["ham"],
        "smishing": counts["smishing"],
        "manual_ham": int(ham["data_origin"].eq("manual_real").sum()),
        "synthetic_ham": int(ham["data_origin"].eq("synthetic_template").sum()),
        "uci_ham": int(ham["source_name"].eq("UCI SMS Spam Collection").sum()),
        "mishra_ham": int(ham["source_name"].eq("Mishra & Soni").sum()),
        "uci_ham_share": (ham["source_name"].eq("UCI SMS Spam Collection").mean() * 100) if len(ham) else 0,
        "synthetic_ham_share": (ham["data_origin"].eq("synthetic_template").mean() * 100) if len(ham) else 0,
        "manual_synthetic_service_share": (ham["data_origin"].isin(["manual_real", "synthetic_template"]).mean() * 100) if len(ham) else 0,
        "raw_dupes": raw_dupes,
        "clean_dupes": clean_dupes,
    }
    return metrics, issues, warnings


def main() -> None:
    validation = {}
    all_issues = {}
    all_warnings = {}
    for name, path in DATASETS.items():
        metrics, issues, warnings = validate_one(name, path)
        validation[name] = metrics
        all_issues[name] = issues
        all_warnings[name] = warnings

    manual = read_csv(INTERIM_DIR / "manual_ham_no_overlap.csv")
    synth_generated = read_csv(INTERIM_DIR / "synthetic_service_ham_generated.csv")
    synth_approved = read_csv(INTERIM_DIR / "synthetic_service_ham_approved.csv")
    templates = read_csv(INTERIM_DIR / "service_ham_template_patterns.csv")
    public = read_csv(PUBLIC_DATASET)
    overlap_path = FINAL_DIR.parent / "archives" / "manual_ham_overlap_archive.csv"
    try:
        overlap_archive = read_csv(overlap_path)
    except pd.errors.EmptyDataError:
        overlap_archive = pd.DataFrame()

    lines = [
        "# Final Combined Dataset Validation Report",
        "",
        "| Dataset | Ham | Smishing | Total | Manual Ham | Synthetic Ham | UCI Ham | Mishra Ham | UCI Ham Share | Issues | Warnings |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for name, metrics in validation.items():
        issue_text = "; ".join(all_issues[name]) if all_issues[name] else "None"
        warning_text = "; ".join(all_warnings[name]) if all_warnings[name] else "None"
        lines.append(f"| {name} | {metrics['ham']} | {metrics['smishing']} | {metrics['rows']} | {metrics['manual_ham']} | {metrics['synthetic_ham']} | {metrics['uci_ham']} | {metrics['mishra_ham']} | {metrics['uci_ham_share']:.2f}% | {issue_text} | {warning_text} |")
    lines.extend(
        [
            "",
            "## V3 Specific Metrics",
            "",
            f"- Synthetic ham count: {validation['V3']['synthetic_ham']}",
            f"- Manual ham count: {validation['V3']['manual_ham']}",
            f"- UCI ham share: {validation['V3']['uci_ham_share']:.2f}%",
            f"- Synthetic ham share: {validation['V3']['synthetic_ham_share']:.2f}%",
            f"- Manual + synthetic service ham share: {validation['V3']['manual_synthetic_service_share']:.2f}%",
            "",
            "## Notes",
            "",
            "Synthetic ham messages were generated from manually approved legitimate service-message templates. Unlike collected public data, these messages are synthetic and contain fake/generated values in the raw text field. A privacy-safe cleaned version was also generated for each synthetic message. Synthetic rows are clearly marked with is_synthetic=True and data_origin=synthetic_template.",
        ]
    )
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")

    v1 = validation["V1"]
    v2 = validation["V2"]
    v3 = validation["V3"]
    print(f"public dataset input count: {len(public)}")
    print(f"manual ham input count: 320")
    print(f"manual ham overlap count: {len(overlap_archive)}")
    print(f"manual ham included count: {len(manual)}")
    print(f"templates extracted: {len(templates)}")
    print(f"synthetic ham generated: {len(synth_generated)}")
    print(f"synthetic ham approved: {len(synth_approved)}")
    print(f"V1 dataset count and composition: ham={v1['ham']}, smishing={v1['smishing']}, total={v1['rows']}")
    print(f"V2 dataset count and composition: ham={v2['ham']}, smishing={v2['smishing']}, total={v2['rows']}")
    print(f"V3 dataset count and composition: ham={v3['ham']}, smishing={v3['smishing']}, total={v3['rows']}")
    print(f"V3 ham source breakdown: manual={v3['manual_ham']}, synthetic={v3['synthetic_ham']}, UCI={v3['uci_ham']}, Mishra={v3['mishra_ham']}")
    print(f"V3 UCI ham percentage: {v3['uci_ham_share']:.2f}%")
    print("output file paths:")
    for path in DATASETS.values():
        print(f"- {path}")
    print("report file paths:")
    print(f"- {REPORT_OUT}")
    print(f"- {REPORTS_DIR / 'final_dataset_build_report.md'}")
    print(f"- {REPORTS_DIR / 'manual_ham_overlap_report.md'}")
    print(f"- {REPORTS_DIR / 'synthetic_ham_quality_report.md'}")
    print("")
    print(f"Final target dataset: {DATASETS['V3']}")
    print("Expected target:")
    print(f"- ham: {v3['ham']}")
    print(f"- smishing: {v3['smishing']}")
    print(f"- total: {v3['rows']}")
    print("- includes public ham, manual curated ham, and synthetic service ham")
    print("- smishing remains real/public-source only")
    issue_count = sum(len(v) for v in all_issues.values())
    warning_count = sum(len(v) for v in all_warnings.values())
    if issue_count:
        print(f"Validation issues found: {issue_count}. See report.")
    elif warning_count:
        print(f"Validation passed with {warning_count} warnings. See report.")
    else:
        print("Validation passed with no issues.")


if __name__ == "__main__":
    main()
