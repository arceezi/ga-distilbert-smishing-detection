"""Validate model-ready clean, augmented, and adversarial artifacts."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pandas as pd

from model_ready_common import (
    AUGMENTATION_LOG,
    FINAL_CLEAN_DATASET,
    LABEL_TO_ID,
    MANIFESTS_DIR,
    MODEL_READY_DIR,
    REPORTS_DIR,
    TEST_ADV_10,
    TEST_ADV_20,
    TEST_ADV_30,
    TEST_CLEAN,
    TRAIN_AUGMENTED,
    TRAIN_AUGMENTED_METADATA,
    TRAIN_CLEAN,
    VAL_ADV_10,
    VAL_ADV_20,
    VAL_CLEAN,
    file_rows_summary,
    label_counts,
    markdown_table,
    normalized_message_key,
    read_csv,
    relpath,
    technique_counter,
    write_csv,
    write_file_manifest,
    write_model_ready_config,
    write_text,
)


OUTPUT_PATHS = [
    FINAL_CLEAN_DATASET,
    TRAIN_CLEAN,
    VAL_CLEAN,
    TEST_CLEAN,
    TRAIN_AUGMENTED,
    TRAIN_AUGMENTED_METADATA,
    AUGMENTATION_LOG,
    VAL_ADV_10,
    VAL_ADV_20,
    TEST_ADV_10,
    TEST_ADV_20,
    TEST_ADV_30,
]


def _load_required(path: Path, issues: list[str]) -> pd.DataFrame:
    if not path.exists():
        issues.append(f"missing required file: {relpath(path)}")
        return pd.DataFrame()
    return read_csv(path)


def _status_text(df: pd.DataFrame) -> pd.Series:
    left = df["label_status"].astype(str) if "label_status" in df.columns else ""
    right = df["review_status"].astype(str) if "review_status" in df.columns else ""
    return (left + " " + right).str.lower()


def _ids(df: pd.DataFrame, column: str = "final_row_id") -> set[str]:
    return set(df[column].astype(str)) if column in df.columns else set()


def _ensure_key(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "normalized_message_key" not in out.columns:
        out["normalized_message_key"] = out["message_clean"].map(normalized_message_key)
    return out


def validate_clean(final_df: pd.DataFrame, issues: list[str], warnings: list[str]) -> None:
    counts = label_counts(final_df)
    if not FINAL_CLEAN_DATASET.exists():
        issues.append("final_clean_dataset does not exist")
    if counts.get("ham", 0) != 5272:
        issues.append(f"clean ham count is {counts.get('ham', 0)}, expected 5272")
    if counts.get("smishing", 0) != 5272:
        issues.append(f"clean smishing count is {counts.get('smishing', 0)}, expected 5272")
    if len(final_df) != 10544:
        issues.append(f"clean total count is {len(final_df)}, expected 10544")
    invalid_labels = sorted(set(final_df.get("normalized_label", [])) - set(LABEL_TO_ID))
    if invalid_labels:
        issues.append(f"invalid clean labels: {invalid_labels}")
    status_text = _status_text(final_df)
    if status_text.str.contains("reject", regex=False).any():
        issues.append("reject-status rows found in clean dataset")
    if status_text.str.contains("unsure", regex=False).any():
        issues.append("unsure-status rows found in clean dataset")
    if (final_df.get("is_synthetic", "").astype(str).eq("True") & final_df["normalized_label"].eq("smishing")).any():
        issues.append("synthetic smishing rows found in clean dataset")
    if final_df["message_raw"].astype(str).str.strip().eq("").any():
        issues.append("empty message_raw found in clean dataset")
    if final_df["message_clean"].astype(str).str.strip().eq("").any():
        issues.append("empty message_clean found in clean dataset")
    expected_label_ids = final_df["normalized_label"].map(LABEL_TO_ID).astype(str)
    if not final_df["label_id"].astype(str).eq(expected_label_ids).all():
        issues.append("label_id mapping is incorrect in clean dataset")
    if not final_df["final_row_id"].is_unique:
        issues.append("final_row_id is not unique in clean dataset")


def validate_splits(final_df: pd.DataFrame, train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, issues: list[str], warnings: list[str]) -> None:
    split_total = len(train) + len(val) + len(test)
    if split_total != len(final_df):
        issues.append(f"train/val/test rows sum to {split_total}, expected {len(final_df)}")
    all_ids = list(train["final_row_id"]) + list(val["final_row_id"]) + list(test["final_row_id"])
    if len(all_ids) != len(set(all_ids)):
        issues.append("a final_row_id appears in more than one clean split")
    if set(all_ids) != set(final_df["final_row_id"]):
        issues.append("clean split IDs do not exactly match final_clean_dataset IDs")
    if _ids(test) & (_ids(train) | _ids(val)):
        issues.append("test rows appear in train or validation")

    combined = pd.concat([train, val, test], ignore_index=True)
    combined = _ensure_key(combined)
    key_split_counts = combined.groupby("normalized_message_key")["split"].nunique()
    crossing = key_split_counts[key_split_counts > 1]
    if not crossing.empty:
        issues.append(f"normalized duplicate clean keys cross train/val/test splits: {len(crossing)} groups")

    raw_keys = combined["message_raw"].map(normalized_message_key)
    raw_key_split_counts = pd.DataFrame({"raw_key": raw_keys, "split": combined["split"]}).groupby("raw_key")["split"].nunique()
    raw_crossing = raw_key_split_counts[raw_key_split_counts > 1]
    if not raw_crossing.empty:
        issues.append(f"normalized duplicate raw keys cross train/val/test splits: {len(raw_crossing)} groups")

    for split_name, split_df in [("train", train), ("val", val), ("test", test)]:
        counts = label_counts(split_df)
        total = len(split_df)
        if total:
            ham_share = counts.get("ham", 0) / total
            if abs(ham_share - 0.5) > 0.03:
                warnings.append(f"{split_name} split ham share is {ham_share:.3f}; duplicate grouping may have shifted exact stratification")


def validate_augmented_training(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, augmented: pd.DataFrame, issues: list[str], warnings: list[str]) -> None:
    if augmented.empty:
        issues.append("augmented training artifact is empty")
        return
    train_ids = _ids(train)
    train_smish_ids = set(train.loc[train["normalized_label"].eq("smishing"), "final_row_id"])
    val_test_ids = _ids(val) | _ids(test)
    aug_rows = augmented[augmented["row_type"].eq("augmented")].copy()
    original_rows = augmented[augmented["row_type"].eq("original")].copy()
    if len(augmented) > 2 * len(train):
        issues.append("augmented training set exceeds 2x original train size")
    if set(original_rows["final_row_id"]) != train_ids:
        issues.append("original rows in augmented training do not exactly match train_clean")
    if not aug_rows.empty:
        if not aug_rows["normalized_label"].eq("smishing").all():
            issues.append("non-smishing augmented rows found in augmented training")
        if not set(aug_rows["original_final_row_id"]).issubset(train_smish_ids):
            issues.append("augmented rows were generated from non-train or non-smishing source IDs")
        if set(aug_rows["original_final_row_id"]) & val_test_ids:
            issues.append("augmented training uses validation/test source IDs")
        if "quality_status" in aug_rows.columns and not aug_rows["quality_status"].eq("pass").all():
            issues.append("included augmented rows contain non-pass quality_status")
        identical = aug_rows["message_raw"].astype(str).eq(aug_rows["original_message_raw"].astype(str))
        if identical.any():
            issues.append(f"generated augmented variants identical to original: {int(identical.sum())}")
        for column in ["augmentation_id", "perturbation_techniques", "seed", "variant_index"]:
            if column not in aug_rows.columns or aug_rows[column].astype(str).str.strip().eq("").any():
                issues.append(f"augmented rows missing metadata column values: {column}")
    else:
        issues.append("no augmented smishing rows found in augmented training")


def _validate_adversarial_artifact(
    clean_split: pd.DataFrame,
    adv: pd.DataFrame,
    level: int,
    split_name: str,
    forbidden_ids: set[str],
    issues: list[str],
    final_evaluation_required: bool = False,
) -> None:
    if len(adv) != len(clean_split):
        issues.append(f"{split_name}_adv_{level} row count {len(adv)} does not match clean split {len(clean_split)}")
    if set(adv["final_row_id"]) != set(clean_split["final_row_id"]):
        issues.append(f"{split_name}_adv_{level} source IDs do not exactly match {split_name}_clean")
    if set(adv["final_row_id"]) & forbidden_ids:
        issues.append(f"{split_name}_adv_{level} contains IDs from another clean split")

    clean_index = clean_split.set_index("final_row_id")
    adv_index = adv.set_index("final_row_id")
    common_ids = clean_index.index.intersection(adv_index.index)
    labels_match = adv_index.loc[common_ids, "normalized_label"].astype(str).eq(clean_index.loc[common_ids, "normalized_label"].astype(str))
    if not labels_match.all():
        issues.append(f"{split_name}_adv_{level} labels changed for {int((~labels_match).sum())} rows")

    ham_ids = clean_index[clean_index["normalized_label"].eq("ham")].index.intersection(common_ids)
    if len(ham_ids):
        ham_raw_same = adv_index.loc[ham_ids, "message_raw"].astype(str).eq(clean_index.loc[ham_ids, "message_raw"].astype(str))
        ham_clean_same = adv_index.loc[ham_ids, "message_clean"].astype(str).eq(clean_index.loc[ham_ids, "message_clean"].astype(str))
        if not ham_raw_same.all() or not ham_clean_same.all():
            issues.append(f"{split_name}_adv_{level} changed ham rows")

    smish_ids = clean_index[clean_index["normalized_label"].eq("smishing")].index.intersection(common_ids)
    if len(smish_ids):
        smish_changed = ~adv_index.loc[smish_ids, "message_raw"].astype(str).eq(clean_index.loc[smish_ids, "message_raw"].astype(str))
        if not smish_changed.all():
            issues.append(f"{split_name}_adv_{level} has unperturbed smishing rows: {int((~smish_changed).sum())}")
        if "quality_status" in adv_index.columns:
            smish_quality = adv_index.loc[smish_ids, "quality_status"].astype(str).eq("pass")
            if not smish_quality.all():
                issues.append(f"{split_name}_adv_{level} smishing quality failures: {int((~smish_quality).sum())}")
    if final_evaluation_required:
        if "final_evaluation_only" not in adv.columns or not adv["final_evaluation_only"].astype(str).eq("True").all():
            issues.append(f"{split_name}_adv_{level} is not marked final_evaluation_only=True")
        if "artifact_purpose" not in adv.columns or not adv["artifact_purpose"].astype(str).eq("final_evaluation_only").all():
            issues.append(f"{split_name}_adv_{level} artifact_purpose is not final_evaluation_only")


def validate_adversarial_sets(train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame, artifacts: dict[str, pd.DataFrame], issues: list[str]) -> None:
    train_ids = _ids(train)
    val_ids = _ids(val)
    test_ids = _ids(test)
    _validate_adversarial_artifact(val, artifacts["val_adv_10"], 10, "val", train_ids | test_ids, issues)
    _validate_adversarial_artifact(val, artifacts["val_adv_20"], 20, "val", train_ids | test_ids, issues)
    _validate_adversarial_artifact(test, artifacts["test_adv_10"], 10, "test", train_ids | val_ids, issues, final_evaluation_required=True)
    _validate_adversarial_artifact(test, artifacts["test_adv_20"], 20, "test", train_ids | val_ids, issues, final_evaluation_required=True)
    _validate_adversarial_artifact(test, artifacts["test_adv_30"], 30, "test", train_ids | val_ids, issues, final_evaluation_required=True)

    for name in ["test_adv_10", "test_adv_20", "test_adv_30"]:
        if artifacts[name].get("artifact_purpose", pd.Series(dtype=str)).astype(str).str.contains("ga", case=False, regex=False).any():
            issues.append(f"{name} contains GA fitness metadata")


def write_manifests(augmented: pd.DataFrame, artifacts: dict[str, pd.DataFrame]) -> None:
    aug_rows = augmented[augmented["row_type"].eq("augmented")].copy() if "row_type" in augmented.columns else pd.DataFrame()
    aug_columns = [
        "augmentation_id",
        "original_final_row_id",
        "normalized_label",
        "perturbation_level",
        "perturbation_techniques",
        "variant_index",
        "seed",
        "quality_status",
        "augmentation_purpose",
    ]
    for column in aug_columns:
        if column not in aug_rows.columns:
            aug_rows[column] = ""
    aug_manifest = aug_rows[aug_columns].copy()
    aug_manifest.insert(0, "artifact_path", relpath(TRAIN_AUGMENTED))
    write_csv(aug_manifest, MANIFESTS_DIR / "augmentation_manifest.csv")

    adversarial_rows = []
    for name, df in artifacts.items():
        counts = label_counts(df)
        level = name.rsplit("_", 1)[-1]
        purpose = "GA fitness evaluation" if name.startswith("val") else "final robustness evaluation"
        adversarial_rows.append(
            {
                "artifact_name": name,
                "artifact_path": relpath(_artifact_path(name)),
                "perturbation_level": level,
                "rows": len(df),
                "ham": counts.get("ham", 0),
                "smishing": counts.get("smishing", 0),
                "purpose": purpose,
                "smishing_perturbed": int(df.get("row_type", pd.Series(dtype=str)).eq("adversarial_smishing").sum()),
                "ham_unchanged": int(df.get("row_type", pd.Series(dtype=str)).eq("original_ham_unchanged").sum()),
            }
        )
    write_csv(pd.DataFrame(adversarial_rows), MANIFESTS_DIR / "adversarial_manifest.csv")


def _artifact_path(name: str) -> Path:
    return {
        "val_adv_10": VAL_ADV_10,
        "val_adv_20": VAL_ADV_20,
        "test_adv_10": TEST_ADV_10,
        "test_adv_20": TEST_ADV_20,
        "test_adv_30": TEST_ADV_30,
    }[name]


def write_reports(
    issues: list[str],
    warnings: list[str],
    final_df: pd.DataFrame,
    train: pd.DataFrame,
    val: pd.DataFrame,
    test: pd.DataFrame,
    augmented: pd.DataFrame,
    artifacts: dict[str, pd.DataFrame],
) -> None:
    status = "PASSED" if not issues else "FAILED"
    split_rows = []
    for name, df in [("train_clean", train), ("val_clean", val), ("test_clean", test)]:
        counts = label_counts(df)
        split_rows.append([name, len(df), counts.get("ham", 0), counts.get("smishing", 0), int((df["is_synthetic"].eq("True") & df["normalized_label"].eq("ham")).sum())])
    adv_rows = []
    for name, df in artifacts.items():
        counts = label_counts(df)
        adv_rows.append([name, len(df), counts.get("ham", 0), counts.get("smishing", 0), int(df.get("row_type", pd.Series(dtype=str)).eq("adversarial_smishing").sum())])
    aug_rows = augmented[augmented["row_type"].eq("augmented")] if "row_type" in augmented.columns else pd.DataFrame()
    lines = [
        "# Leakage Validation Report",
        "",
        f"- Validation status: {status}",
        f"- Output folder: `{relpath(MODEL_READY_DIR)}`",
        "",
        "## Clean Split Counts",
        "",
        *markdown_table(["Artifact", "Rows", "Ham", "Smishing", "Synthetic ham"], split_rows),
        "",
        "## Augmented Training Summary",
        "",
        *markdown_table(
            ["Metric", "Value"],
            [
                ("train_clean rows", len(train)),
                ("train_augmented_for_ablation_b rows", len(augmented)),
                ("included augmented rows", len(aug_rows)),
                ("augmented label counts", dict(label_counts(augmented))),
                ("technique counts", dict(technique_counter(aug_rows.get("perturbation_techniques", []))) if not aug_rows.empty else {}),
            ],
        ),
        "",
        "## Adversarial Artifact Summary",
        "",
        *markdown_table(["Artifact", "Rows", "Ham", "Smishing", "Smishing perturbed rows"], adv_rows),
        "",
        "## Issues",
        "",
    ]
    lines.extend(f"- {issue}" for issue in issues) if issues else lines.append("- None")
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {warning}" for warning in warnings) if warnings else lines.append("- None")
    write_text(REPORTS_DIR / "leakage_validation_report.md", lines)

    manifest_lines = [
        "# Model-Ready Dataset Manifest",
        "",
        f"- Validation status: {status}",
        f"- Clean master: `{relpath(FINAL_CLEAN_DATASET)}`",
        f"- Output folder: `{relpath(MODEL_READY_DIR)}`",
        "",
        "## Main Clean Dataset",
        "",
        *markdown_table(["Path", "Rows", "Ham", "Smishing", "Purpose"], [[relpath(FINAL_CLEAN_DATASET), len(final_df), label_counts(final_df).get("ham", 0), label_counts(final_df).get("smishing", 0), "Balanced clean English SMS binary dataset"]]),
        "",
        "## Files",
        "",
        *markdown_table(
            ["Artifact", "Path", "Rows", "Ham", "Smishing", "Purpose"],
            [
                ["train_clean", relpath(TRAIN_CLEAN), len(train), label_counts(train).get("ham", 0), label_counts(train).get("smishing", 0), "Clean training"],
                ["val_clean", relpath(VAL_CLEAN), len(val), label_counts(val).get("ham", 0), label_counts(val).get("smishing", 0), "Clean validation"],
                ["test_clean", relpath(TEST_CLEAN), len(test), label_counts(test).get("ham", 0), label_counts(test).get("smishing", 0), "Clean final test"],
                ["train_augmented_for_ablation_b", relpath(TRAIN_AUGMENTED), len(augmented), label_counts(augmented).get("ham", 0), label_counts(augmented).get("smishing", 0), "Ablation B only"],
                ["val_adv_10", relpath(VAL_ADV_10), len(artifacts["val_adv_10"]), label_counts(artifacts["val_adv_10"]).get("ham", 0), label_counts(artifacts["val_adv_10"]).get("smishing", 0), "GA fitness evaluation"],
                ["val_adv_20", relpath(VAL_ADV_20), len(artifacts["val_adv_20"]), label_counts(artifacts["val_adv_20"]).get("ham", 0), label_counts(artifacts["val_adv_20"]).get("smishing", 0), "GA fitness evaluation"],
                ["test_adv_10", relpath(TEST_ADV_10), len(artifacts["test_adv_10"]), label_counts(artifacts["test_adv_10"]).get("ham", 0), label_counts(artifacts["test_adv_10"]).get("smishing", 0), "Final robustness evaluation"],
                ["test_adv_20", relpath(TEST_ADV_20), len(artifacts["test_adv_20"]), label_counts(artifacts["test_adv_20"]).get("ham", 0), label_counts(artifacts["test_adv_20"]).get("smishing", 0), "Final robustness evaluation"],
                ["test_adv_30", relpath(TEST_ADV_30), len(artifacts["test_adv_30"]), label_counts(artifacts["test_adv_30"]).get("ham", 0), label_counts(artifacts["test_adv_30"]).get("smishing", 0), "Final robustness evaluation"],
            ],
        ),
        "",
        "## Model Usage Table",
        "",
        *model_usage_table(),
    ]
    write_text(REPORTS_DIR / "model_ready_dataset_manifest.md", manifest_lines)


def model_usage_table() -> list[str]:
    return markdown_table(
        ["Model", "Training file", "Validation file", "GA fitness file", "Final evaluation files"],
        [
            ["Baseline 1 TF-IDF Logistic Regression", "train_clean.csv", "val_clean.csv", "N/A", "test_clean.csv; test_adv_10/20/30.csv"],
            ["Ablation A TF-IDF class-weighted", "train_clean.csv", "val_clean.csv", "N/A", "test_clean.csv; test_adv_10/20/30.csv"],
            ["Baseline 2 Fine-tuned DistilBERT", "train_clean.csv", "val_clean.csv", "N/A", "test_clean.csv; test_adv_10/20/30.csv"],
            ["Ablation B Fine-tuned DistilBERT with adversarial augmentation", "train_augmented_for_ablation_b.csv", "val_clean.csv", "N/A", "test_clean.csv; test_adv_10/20/30.csv"],
            ["Proposed GA model", "Phase A train_clean.csv; Phase C train_clean.csv", "val_clean.csv", "val_clean.csv + val_adv_10.csv + val_adv_20.csv", "test_clean.csv + test_adv_10/20/30.csv"],
            ["Ablation C Frozen DistilBERT with uniform weights", "train_clean.csv", "val_clean.csv", "N/A", "test_clean.csv; test_adv_10/20/30.csv"],
            ["Ablation D Frozen DistilBERT with random weights", "train_clean.csv", "val_clean.csv", "N/A", "test_clean.csv; test_adv_10/20/30.csv"],
        ],
    )


def validate_all() -> tuple[str, list[str], list[str]]:
    issues: list[str] = []
    warnings: list[str] = []
    for path in OUTPUT_PATHS:
        if not path.exists():
            issues.append(f"missing required output: {relpath(path)}")

    final_df = _load_required(FINAL_CLEAN_DATASET, issues)
    train = _load_required(TRAIN_CLEAN, issues)
    val = _load_required(VAL_CLEAN, issues)
    test = _load_required(TEST_CLEAN, issues)
    augmented = _load_required(TRAIN_AUGMENTED, issues)
    artifacts = {
        "val_adv_10": _load_required(VAL_ADV_10, issues),
        "val_adv_20": _load_required(VAL_ADV_20, issues),
        "test_adv_10": _load_required(TEST_ADV_10, issues),
        "test_adv_20": _load_required(TEST_ADV_20, issues),
        "test_adv_30": _load_required(TEST_ADV_30, issues),
    }

    if not final_df.empty:
        validate_clean(final_df, issues, warnings)
    if not final_df.empty and not train.empty and not val.empty and not test.empty:
        validate_splits(final_df, train, val, test, issues, warnings)
    if not train.empty and not val.empty and not test.empty and not augmented.empty:
        validate_augmented_training(train, val, test, augmented, issues, warnings)
    if not train.empty and not val.empty and not test.empty and all(not df.empty for df in artifacts.values()):
        validate_adversarial_sets(train, val, test, artifacts, issues)

    write_manifests(augmented, artifacts)
    write_model_ready_config()
    write_reports(issues, warnings, final_df, train, val, test, augmented, artifacts)
    write_file_manifest()

    status = "PASSED" if not issues else "FAILED"
    return status, issues, warnings


def main() -> int:
    status, issues, warnings = validate_all()
    print(f"Leakage validation status: {status}")
    print(f"Issues: {len(issues)}")
    print(f"Warnings: {len(warnings)}")
    print(f"Leakage report: {relpath(REPORTS_DIR / 'leakage_validation_report.md')}")
    print(f"Model-ready manifest: {relpath(REPORTS_DIR / 'model_ready_dataset_manifest.md')}")
    print(f"File manifest: {relpath(MANIFESTS_DIR / 'model_ready_file_manifest.csv')}")
    if issues:
        for issue in issues:
            print(f"- {issue}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

