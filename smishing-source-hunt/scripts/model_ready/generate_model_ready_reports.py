"""Generate consolidated reports and manifests for model-ready artifacts."""

from __future__ import annotations

from collections import Counter

import pandas as pd

from model_ready_common import (
    AUGMENTATION_LOG,
    FINAL_CLEAN_DATASET,
    MANIFESTS_DIR,
    REPORTS_DIR,
    TEST_ADV_10,
    TEST_ADV_20,
    TEST_ADV_30,
    TEST_ADV_LOG,
    TEST_CLEAN,
    TRAIN_AUGMENTED,
    TRAIN_AUGMENTED_METADATA,
    TRAIN_CLEAN,
    VAL_ADV_10,
    VAL_ADV_20,
    VAL_ADV_LOG,
    VAL_CLEAN,
    count_table,
    file_rows_summary,
    label_counts,
    markdown_table,
    normalized_message_key,
    read_csv,
    relpath,
    technique_counter,
    write_file_manifest,
    write_text,
)


def _read(path):
    return read_csv(path) if path.exists() else pd.DataFrame()


def report_final_clean() -> None:
    df = _read(FINAL_CLEAN_DATASET)
    if df.empty:
        return
    counts = label_counts(df)
    synthetic_ham = int((df["is_synthetic"].eq("True") & df["normalized_label"].eq("ham")).sum())
    synthetic_smishing = int((df["is_synthetic"].eq("True") & df["normalized_label"].eq("smishing")).sum())
    keys = df["message_clean"].map(normalized_message_key)
    lines = [
        "# Final Clean Dataset Report",
        "",
        f"- Output path: `{relpath(FINAL_CLEAN_DATASET)}`",
        f"- Rows: {len(df)}",
        f"- Ham: {counts.get('ham', 0)}",
        f"- Smishing: {counts.get('smishing', 0)}",
        f"- Synthetic ham: {synthetic_ham}",
        f"- Synthetic smishing: {synthetic_smishing}",
        "",
        "## Source Distribution",
        "",
        *count_table(Counter(df["source_name"]), "Source"),
        "",
        "## Data Origin Distribution",
        "",
        *count_table(Counter(df["data_origin"]), "Data origin"),
        "",
        "## Text Quality",
        "",
        *markdown_table(
            ["Check", "Value"],
            [
                ("empty message_raw", int(df["message_raw"].astype(str).str.strip().eq("").sum())),
                ("empty message_clean", int(df["message_clean"].astype(str).str.strip().eq("").sum())),
                ("duplicate normalized key rows", int(keys[keys.ne("")].duplicated().sum())),
                ("raw max length", int(df["message_raw"].astype(str).str.len().max())),
                ("clean max length", int(df["message_clean"].astype(str).str.len().max())),
            ],
        ),
    ]
    write_text(REPORTS_DIR / "final_clean_dataset_report.md", lines)


def report_splits() -> None:
    split_files = [("train_clean", TRAIN_CLEAN), ("val_clean", VAL_CLEAN), ("test_clean", TEST_CLEAN)]
    rows = []
    synthetic_rows = []
    combined = []
    for name, path in split_files:
        df = _read(path)
        if df.empty:
            continue
        counts = label_counts(df)
        synth = int((df["is_synthetic"].eq("True") & df["normalized_label"].eq("ham")).sum())
        rows.append([name, relpath(path), len(df), counts.get("ham", 0), counts.get("smishing", 0), synth])
        synthetic_rows.append([name, synth])
        combined.append(df)
    cross = 0
    if combined:
        all_splits = pd.concat(combined, ignore_index=True)
        keys = all_splits["normalized_message_key"] if "normalized_message_key" in all_splits.columns else all_splits["message_clean"].map(normalized_message_key)
        cross = int((pd.DataFrame({"key": keys, "split": all_splits["split"]}).groupby("key")["split"].nunique() > 1).sum())
    lines = [
        "# Clean Split Report",
        "",
        "- Split: stratified 70/15/15 by label with duplicate normalized message keys kept in the same split.",
        "- Seed: 42",
        "",
        "## Split Counts",
        "",
        *markdown_table(["Artifact", "Path", "Rows", "Ham", "Smishing", "Synthetic ham"], rows),
        "",
        "## Synthetic Ham Distribution",
        "",
        *markdown_table(["Split", "Synthetic ham"], synthetic_rows),
        "",
        "## Leakage Check",
        "",
        f"- Duplicate normalized key groups crossing splits: {cross}",
    ]
    write_text(REPORTS_DIR / "split_report.md", lines)


def report_augmentation() -> None:
    train = _read(TRAIN_CLEAN)
    augmented = _read(TRAIN_AUGMENTED)
    metadata = _read(TRAIN_AUGMENTED_METADATA)
    if augmented.empty:
        return
    aug_rows = augmented[augmented["row_type"].eq("augmented")] if "row_type" in augmented.columns else pd.DataFrame()
    rates = pd.to_numeric(metadata.get("achieved_perturbation_rate", pd.Series(dtype=str)), errors="coerce")
    lines = [
        "# Augmentation Report",
        "",
        f"- Input: `{relpath(TRAIN_CLEAN)}`",
        f"- Output: `{relpath(TRAIN_AUGMENTED)}`",
        f"- Metadata: `{relpath(TRAIN_AUGMENTED_METADATA)}`",
        f"- Log: `{relpath(AUGMENTATION_LOG)}`",
        "- Purpose: Ablation B training only.",
        "- Selection: 55% of train smishing rows, variant distribution 70%/25%/5% for 1/2/3 variants, capped at 2,200 variants.",
        "",
        "## Counts",
        "",
        *markdown_table(
            ["Metric", "Value"],
            [
                ("original train rows", len(train)),
                ("augmented training rows", len(augmented)),
                ("augmented smishing variants", len(aug_rows)),
                ("ham rows", label_counts(augmented).get("ham", 0)),
                ("smishing rows", label_counts(augmented).get("smishing", 0)),
                ("<= 2x train_clean", len(augmented) <= 2 * len(train)),
            ],
        ),
        "",
        "## Technique Counts",
        "",
        *markdown_table(["Technique", "Count"], sorted(technique_counter(metadata.get("perturbation_techniques", [])).items())),
        "",
        "## Quality",
        "",
        *markdown_table(
            ["Metric", "Value"],
            [
                ("quality pass", int(metadata.get("quality_status", pd.Series(dtype=str)).eq("pass").sum()) if not metadata.empty else 0),
                ("quality fail", int(metadata.get("quality_status", pd.Series(dtype=str)).ne("pass").sum()) if not metadata.empty else 0),
                ("average perturbation rate", round(float(rates.mean()), 4) if len(rates.dropna()) else 0),
            ],
        ),
        "",
        "## Usage Warning",
        "",
        "- This artifact is intentionally smishing-heavy and must be used only for Ablation B.",
        "- The proposed GA model trains on clean splits, not this augmented training file.",
    ]
    write_text(REPORTS_DIR / "augmentation_report.md", lines)


def report_adversarial(kind: str) -> None:
    if kind == "validation":
        clean_path = VAL_CLEAN
        files = [("val_adv_10", VAL_ADV_10), ("val_adv_20", VAL_ADV_20)]
        log_path = VAL_ADV_LOG
        title = "Adversarial Validation Report"
        purpose = "GA fitness evaluation"
    else:
        clean_path = TEST_CLEAN
        files = [("test_adv_10", TEST_ADV_10), ("test_adv_20", TEST_ADV_20), ("test_adv_30", TEST_ADV_30)]
        log_path = TEST_ADV_LOG
        title = "Adversarial Test Report"
        purpose = "final robustness evaluation for all seven models"
    clean = _read(clean_path)
    log = _read(log_path)
    rows = []
    for name, path in files:
        df = _read(path)
        if df.empty:
            continue
        counts = label_counts(df)
        rows.append([name, relpath(path), len(df), counts.get("ham", 0), counts.get("smishing", 0), len(df) == len(clean)])
    smish_log = log[log["row_type"].eq("adversarial_smishing")] if not log.empty and "row_type" in log.columns else pd.DataFrame()
    quality_rows = []
    if not smish_log.empty:
        for level, group in smish_log.groupby("perturbation_level"):
            rates = pd.to_numeric(group["achieved_perturbation_rate"], errors="coerce")
            quality_rows.append([level, round(float(rates.mean()), 4), int(group["quality_status"].eq("pass").sum()), int(group["quality_status"].ne("pass").sum())])
    lines = [
        f"# {title}",
        "",
        f"- Input: `{relpath(clean_path)}`",
        f"- Log: `{relpath(log_path)}`",
        f"- Purpose: {purpose}.",
        "- Ham rows are unchanged; smishing rows are perturbed after splitting.",
        "",
        "## Artifact Counts",
        "",
        *markdown_table(["Artifact", "Path", "Rows", "Ham", "Smishing", "Matches clean row count"], rows),
        "",
        "## Perturbation Quality",
        "",
        *markdown_table(["Level", "Average perturbation rate", "Quality pass", "Quality fail"], quality_rows),
        "",
        "## Technique Counts",
        "",
        *markdown_table(["Technique", "Count"], sorted(technique_counter(smish_log.get("perturbation_techniques", [])).items()) if not smish_log.empty else []),
    ]
    out_name = "adversarial_validation_report.md" if kind == "validation" else "adversarial_test_report.md"
    write_text(REPORTS_DIR / out_name, lines)


def model_usage_table() -> list[str]:
    return markdown_table(
        ["Model", "Training file", "Validation file", "GA fitness file", "Final evaluation files"],
        [
            ["Baseline 1 TF-IDF Logistic Regression", "train_clean.csv", "val_clean.csv", "N/A", "test_clean.csv, test_adv_10/20/30.csv"],
            ["Ablation A TF-IDF class-weighted", "train_clean.csv", "val_clean.csv", "N/A", "test_clean.csv, test_adv_10/20/30.csv"],
            ["Baseline 2 Fine-tuned DistilBERT", "train_clean.csv", "val_clean.csv", "N/A", "test_clean.csv, test_adv_10/20/30.csv"],
            ["Ablation B Fine-tuned DistilBERT with adversarial augmentation", "train_augmented_for_ablation_b.csv", "val_clean.csv", "N/A", "test_clean.csv, test_adv_10/20/30.csv"],
            ["Proposed GA model", "Phase A train_clean.csv; Phase C train_clean.csv", "val_clean.csv", "val_clean.csv + val_adv_10.csv + val_adv_20.csv", "test_clean.csv + test_adv_10/20/30.csv"],
            ["Ablation C Frozen DistilBERT with uniform weights", "train_clean.csv", "val_clean.csv", "N/A", "test_clean.csv, test_adv_10/20/30.csv"],
            ["Ablation D Frozen DistilBERT with random weights", "train_clean.csv", "val_clean.csv", "N/A", "test_clean.csv, test_adv_10/20/30.csv"],
        ],
    )


def report_manifest() -> None:
    artifacts = [
        ("final_clean_dataset", FINAL_CLEAN_DATASET, "Balanced clean English SMS binary master dataset"),
        ("train_clean", TRAIN_CLEAN, "Clean training"),
        ("val_clean", VAL_CLEAN, "Clean validation"),
        ("test_clean", TEST_CLEAN, "Clean final test"),
        ("train_augmented_for_ablation_b", TRAIN_AUGMENTED, "Ablation B only"),
        ("val_adv_10", VAL_ADV_10, "GA fitness evaluation"),
        ("val_adv_20", VAL_ADV_20, "GA fitness evaluation"),
        ("test_adv_10", TEST_ADV_10, "Final robustness evaluation"),
        ("test_adv_20", TEST_ADV_20, "Final robustness evaluation"),
        ("test_adv_30", TEST_ADV_30, "Final robustness evaluation"),
    ]
    rows = []
    for name, path, purpose in artifacts:
        summary = file_rows_summary(path)
        rows.append([name, summary["path"], summary["rows"], summary["ham"], summary["smishing"], purpose])
    lines = [
        "# Model-Ready Dataset Manifest",
        "",
        "## Main Clean Dataset",
        "",
        "- The clean dataset remains the primary final dataset and stays balanced.",
        "- Augmented training, adversarial validation, and adversarial test artifacts are separate files.",
        "",
        "## Artifact Summary",
        "",
        *markdown_table(["Artifact", "Path", "Rows", "Ham", "Smishing", "Purpose"], rows),
        "",
        "## Model Usage Table",
        "",
        *model_usage_table(),
        "",
        "## Reports",
        "",
        *markdown_table(
            ["Report", "Path"],
            [
                ["Final clean dataset report", relpath(REPORTS_DIR / "final_clean_dataset_report.md")],
                ["Split report", relpath(REPORTS_DIR / "split_report.md")],
                ["Augmentation report", relpath(REPORTS_DIR / "augmentation_report.md")],
                ["Adversarial validation report", relpath(REPORTS_DIR / "adversarial_validation_report.md")],
                ["Adversarial test report", relpath(REPORTS_DIR / "adversarial_test_report.md")],
                ["Leakage validation report", relpath(REPORTS_DIR / "leakage_validation_report.md")],
            ],
        ),
    ]
    write_text(REPORTS_DIR / "model_ready_dataset_manifest.md", lines)


def main() -> int:
    report_final_clean()
    report_splits()
    report_augmentation()
    report_adversarial("validation")
    report_adversarial("test")
    if not (REPORTS_DIR / "leakage_validation_report.md").exists():
        write_text(REPORTS_DIR / "leakage_validation_report.md", ["# Leakage Validation Report", "", "- Run `python scripts/model_ready/validate_model_ready_datasets.py` to generate validation details."])
    report_manifest()
    write_file_manifest()
    print("Generated model-ready reports:")
    for report in [
        "final_clean_dataset_report.md",
        "split_report.md",
        "augmentation_report.md",
        "adversarial_validation_report.md",
        "adversarial_test_report.md",
        "leakage_validation_report.md",
        "model_ready_dataset_manifest.md",
    ]:
        print(f"- {relpath(REPORTS_DIR / report)}")
    print(f"File manifest: {relpath(MANIFESTS_DIR / 'model_ready_file_manifest.csv')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

