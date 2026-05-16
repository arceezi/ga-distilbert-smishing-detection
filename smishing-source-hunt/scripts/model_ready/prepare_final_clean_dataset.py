"""Prepare the final clean, model-ready master dataset."""

from __future__ import annotations

from collections import Counter

import pandas as pd

from model_ready_common import (
    FINAL_CLEAN_DATASET,
    INPUT_DATASET,
    LABEL_TO_ID,
    REPORTS_DIR,
    count_table,
    ensure_model_ready_dirs,
    label_counts,
    light_clean_model_text,
    markdown_table,
    normalize_whitespace,
    normalized_label,
    normalized_message_key,
    read_csv,
    relpath,
    write_csv,
    write_text,
)


OUTPUT_COLUMNS = [
    "final_row_id",
    "source_final_row_id",
    "message_raw",
    "message_clean",
    "model_text",
    "normalized_label",
    "label_id",
    "source_name",
    "dataset_name",
    "source_group",
    "data_origin",
    "is_synthetic",
    "label_status",
    "review_status",
    "service_category",
    "scam_category",
    "source_file",
    "notes",
]


def _required_source_column(df: pd.DataFrame, column: str) -> None:
    if column not in df.columns:
        raise KeyError(f"Input dataset is missing required column: {column}")


def prepare_dataset() -> pd.DataFrame:
    ensure_model_ready_dirs()
    df = read_csv(INPUT_DATASET)
    for column in ["final_row_id", "message_raw", "message_clean", "normalized_label", "data_origin", "is_synthetic"]:
        _required_source_column(df, column)

    out = pd.DataFrame()
    out["final_row_id"] = df["final_row_id"].astype(str)
    out["source_final_row_id"] = df["final_row_id"].astype(str)
    out["message_raw"] = df["message_raw"].map(normalize_whitespace)
    out["message_clean"] = df["message_clean"].map(normalize_whitespace)
    out["model_text"] = out["message_clean"].where(out["message_clean"].str.strip().ne(""), out["message_raw"]).map(light_clean_model_text)
    out["normalized_label"] = df["normalized_label"].map(normalized_label)
    out["label_id"] = out["normalized_label"].map(LABEL_TO_ID).fillna("").astype(str)

    for column in [
        "source_name",
        "dataset_name",
        "source_group",
        "data_origin",
        "is_synthetic",
        "label_status",
        "review_status",
        "service_category",
        "scam_category",
        "source_file",
        "notes",
    ]:
        out[column] = df[column].astype(str) if column in df.columns else ""

    out["is_synthetic"] = out["is_synthetic"].map(lambda value: "True" if str(value).strip().lower() in {"true", "1", "yes"} else "False")
    out = out[OUTPUT_COLUMNS]

    issues: list[str] = []
    counts = label_counts(out)
    if len(out) != 10544:
        issues.append(f"total row count is {len(out)}, expected 10544")
    if counts.get("ham", 0) != 5272:
        issues.append(f"ham row count is {counts.get('ham', 0)}, expected 5272")
    if counts.get("smishing", 0) != 5272:
        issues.append(f"smishing row count is {counts.get('smishing', 0)}, expected 5272")
    invalid_labels = sorted(set(out["normalized_label"]) - set(LABEL_TO_ID))
    if invalid_labels:
        issues.append(f"invalid normalized_label values: {invalid_labels}")
    if out["message_raw"].str.strip().eq("").any():
        issues.append(f"empty message_raw rows: {int(out['message_raw'].str.strip().eq('').sum())}")
    if out["message_clean"].str.strip().eq("").any():
        issues.append(f"empty message_clean rows: {int(out['message_clean'].str.strip().eq('').sum())}")
    status_text = (out["label_status"].astype(str) + " " + out["review_status"].astype(str)).str.lower()
    rejected = status_text.str.contains("reject", regex=False)
    unsure = status_text.str.contains("unsure", regex=False)
    spam = out["normalized_label"].eq("spam")
    if rejected.any():
        issues.append(f"reject-status rows found: {int(rejected.sum())}")
    if unsure.any():
        issues.append(f"unsure-status rows found: {int(unsure.sum())}")
    if spam.any():
        issues.append(f"spam rows found: {int(spam.sum())}")
    synthetic_smishing = out["is_synthetic"].eq("True") & out["normalized_label"].eq("smishing")
    if synthetic_smishing.any():
        issues.append(f"synthetic smishing rows found: {int(synthetic_smishing.sum())}")
    synthetic_bad_origin = out["is_synthetic"].eq("True") & ~out["data_origin"].eq("synthetic_template")
    if synthetic_bad_origin.any():
        issues.append(f"synthetic rows not marked data_origin=synthetic_template: {int(synthetic_bad_origin.sum())}")
    manual_bad_origin = out["source_group"].eq("manual_curated_ham") & ~out["data_origin"].eq("manual_real")
    if manual_bad_origin.any():
        issues.append(f"manual rows not marked data_origin=manual_real: {int(manual_bad_origin.sum())}")

    if issues:
        write_report(out, issues)
        raise RuntimeError("Final clean dataset preparation failed validation: " + "; ".join(issues))

    write_csv(out, FINAL_CLEAN_DATASET)
    write_report(out, issues)
    return out


def write_report(df: pd.DataFrame, issues: list[str]) -> None:
    counts = label_counts(df)
    synthetic_ham = int((df["is_synthetic"].eq("True") & df["normalized_label"].eq("ham")).sum())
    synthetic_smishing = int((df["is_synthetic"].eq("True") & df["normalized_label"].eq("smishing")).sum())
    raw_lengths = df["message_raw"].astype(str).str.len()
    clean_lengths = df["message_clean"].astype(str).str.len()
    keys = df["message_clean"].map(normalized_message_key)
    duplicate_key_rows = int(keys[keys.ne("")].duplicated().sum())
    lines = [
        "# Final Clean Dataset Report",
        "",
        f"- Input path: `{relpath(INPUT_DATASET)}`",
        f"- Output path: `{relpath(FINAL_CLEAN_DATASET)}`",
        f"- Validation status: {'FAILED' if issues else 'PASSED'}",
        f"- Total rows: {len(df)}",
        f"- Ham rows: {counts.get('ham', 0)}",
        f"- Smishing rows: {counts.get('smishing', 0)}",
        f"- Synthetic ham rows: {synthetic_ham}",
        f"- Synthetic smishing rows: {synthetic_smishing}",
        "",
        "## Label Counts",
        "",
        *count_table(counts, "Label"),
        "",
        "## Source Distribution",
        "",
        *count_table(Counter(df["source_name"]), "Source"),
        "",
        "## Data Origin Distribution",
        "",
        *count_table(Counter(df["data_origin"]), "Data origin"),
        "",
        "## Basic Text Quality Checks",
        "",
        *markdown_table(
            ["Check", "Value"],
            [
                ("empty message_raw", int(df["message_raw"].str.strip().eq("").sum())),
                ("empty message_clean", int(df["message_clean"].str.strip().eq("").sum())),
                ("duplicate normalized message key rows", duplicate_key_rows),
                ("message_raw min length", int(raw_lengths.min()) if len(raw_lengths) else 0),
                ("message_raw median length", round(float(raw_lengths.median()), 2) if len(raw_lengths) else 0),
                ("message_raw max length", int(raw_lengths.max()) if len(raw_lengths) else 0),
                ("message_clean min length", int(clean_lengths.min()) if len(clean_lengths) else 0),
                ("message_clean median length", round(float(clean_lengths.median()), 2) if len(clean_lengths) else 0),
                ("message_clean max length", int(clean_lengths.max()) if len(clean_lengths) else 0),
            ],
        ),
        "",
        "## Issues",
        "",
    ]
    lines.extend(f"- {issue}" for issue in issues) if issues else lines.append("- None")
    write_text(REPORTS_DIR / "final_clean_dataset_report.md", lines)


def main() -> int:
    df = prepare_dataset()
    counts = label_counts(df)
    print(f"Input dataset path: {relpath(INPUT_DATASET)}")
    print(f"Final clean dataset path: {relpath(FINAL_CLEAN_DATASET)}")
    print(f"Final clean counts: ham={counts.get('ham', 0)}, smishing={counts.get('smishing', 0)}, total={len(df)}")
    print(f"Report: {relpath(REPORTS_DIR / 'final_clean_dataset_report.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

