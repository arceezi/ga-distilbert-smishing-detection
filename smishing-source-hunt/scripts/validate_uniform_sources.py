"""Validate organized public-source uniform CSV outputs."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORGANIZED_DIR = ROOT / "data" / "organized"
FINAL_DIR = ROOT / "data" / "final"

REQUIRED_COLUMNS = [
    "unified_id",
    "source_name",
    "dataset_name",
    "source_group",
    "source_row_id",
    "message_text",
    "source_label",
    "normalized_label",
    "label_status",
    "review_status",
    "contains_url",
    "contains_email",
    "contains_phone",
    "source_file",
    "notes",
    "normalized_text_key",
    "duplicate_cluster_id",
    "duplicate_cluster_size",
    "is_dedup_representative",
    "duplicate_cluster_sources",
    "duplicate_cluster_labels",
]
VALID_LABELS = {"ham", "spam", "smishing"}
VALID_LABEL_STATUSES = {"accepted", "needs_smishing_relabel", "conflict_needs_review"}
EXPECTED_SOURCE_TOTALS = {
    "UCI SMS Spam Collection": {"total": 5574, "ham": 4827, "spam": 747, "smishing": 0},
    "Mishra & Soni": {"total": 5971, "ham": 4844, "spam": 489, "smishing": 638},
    "SmishTank": {"total": 1062, "ham": 0, "spam": 0, "smishing": 1062},
    "Gathered approved smishing 7k": {"total": 7000, "ham": 0, "spam": 0, "smishing": 7000},
}
EXPECTED_COMBINED = {"total": 19607, "ham": 9671, "spam": 1236, "smishing": 8700}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path}: missing columns: {', '.join(missing)}")
        return [dict(row) for row in reader]


def validate_rows(path: Path, rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    seen_ids: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        row_id = row.get("unified_id", "").strip()
        if not row_id:
            errors.append(f"{path}: row {row_number}: missing unified_id")
        elif row_id in seen_ids:
            errors.append(f"{path}: row {row_number}: duplicate unified_id {row_id}")
        seen_ids.add(row_id)

        for column in ["source_name", "message_text", "source_label", "normalized_label", "label_status"]:
            if not (row.get(column) or "").strip():
                errors.append(f"{path}: row {row_number}: missing {column}")
        if row.get("normalized_label") not in VALID_LABELS:
            errors.append(f"{path}: row {row_number}: invalid normalized_label {row.get('normalized_label')}")
        if row.get("label_status") not in VALID_LABEL_STATUSES:
            errors.append(f"{path}: row {row_number}: invalid label_status {row.get('label_status')}")
        if row.get("is_dedup_representative") not in {"true", "false"}:
            errors.append(f"{path}: row {row_number}: invalid is_dedup_representative")
    return errors


def source_label_counts(rows: list[dict[str, str]]) -> Counter[str]:
    return Counter(row["normalized_label"] for row in rows)


def validate_expected_counts(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    by_source: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        by_source.setdefault(row["source_name"], []).append(row)

    # Gathered rows retain original source names, so group them by source_group.
    gathered_rows = [row for row in rows if row["source_group"] == "gathered_approved_smishing"]
    grouped_sources = {
        "UCI SMS Spam Collection": by_source.get("UCI SMS Spam Collection", []),
        "Mishra & Soni": by_source.get("Mishra & Soni", []),
        "SmishTank": by_source.get("SmishTank", []),
        "Gathered approved smishing 7k": gathered_rows,
    }

    for source, expected in EXPECTED_SOURCE_TOTALS.items():
        source_rows = grouped_sources[source]
        counts = source_label_counts(source_rows)
        if len(source_rows) != expected["total"]:
            errors.append(f"{source}: expected {expected['total']} rows, found {len(source_rows)}")
        for label in ["ham", "spam", "smishing"]:
            if counts.get(label, 0) != expected[label]:
                errors.append(f"{source}: expected {expected[label]} {label}, found {counts.get(label, 0)}")

    counts = source_label_counts(rows)
    if len(rows) != EXPECTED_COMBINED["total"]:
        errors.append(f"Combined: expected {EXPECTED_COMBINED['total']} rows, found {len(rows)}")
    for label in ["ham", "spam", "smishing"]:
        if counts.get(label, 0) != EXPECTED_COMBINED[label]:
            errors.append(f"Combined: expected {EXPECTED_COMBINED[label]} {label}, found {counts.get(label, 0)}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--organized-dir", type=Path, default=ORGANIZED_DIR)
    args = parser.parse_args()

    errors: list[str] = []
    final_files = sorted(path.name for path in FINAL_DIR.iterdir() if path.is_file())
    if final_files != ["approved_smishing_messages.csv"]:
        errors.append(f"data/final should contain only approved_smishing_messages.csv, found: {final_files}")

    required_files = [
        "uci_sms_spam_collection_uniform.csv",
        "mishra_soni_sms_dataset_uniform.csv",
        "smishtank_uniform.csv",
        "gathered_approved_smishing_7k_uniform.csv",
        "combined_public_thesis_sources_uniform.csv",
        "duplicate_overlap_clusters.csv",
        "combined_public_thesis_sources_deduped_representatives.csv",
        "source_manifest.csv",
    ]
    for filename in required_files:
        path = args.organized_dir / filename
        if not path.exists():
            errors.append(f"Missing organized file: {path}")

    if not errors:
        combined_path = args.organized_dir / "combined_public_thesis_sources_uniform.csv"
        combined_rows = read_rows(combined_path)
        errors.extend(validate_rows(combined_path, combined_rows))
        errors.extend(validate_expected_counts(combined_rows))

        duplicates_path = args.organized_dir / "duplicate_overlap_clusters.csv"
        duplicate_rows = read_rows(duplicates_path)
        if not duplicate_rows:
            errors.append("duplicate_overlap_clusters.csv is empty")

        reps_path = args.organized_dir / "combined_public_thesis_sources_deduped_representatives.csv"
        representative_rows = read_rows(reps_path)
        represented_cluster_ids = {
            row["duplicate_cluster_id"]
            for row in representative_rows
            if row["duplicate_cluster_id"]
        }
        duplicate_cluster_ids = {
            row["duplicate_cluster_id"]
            for row in duplicate_rows
            if row["duplicate_cluster_id"]
        }
        if not duplicate_cluster_ids.issubset(represented_cluster_ids):
            errors.append("Not every duplicate cluster has a representative row")

        conflict_rows = [row for row in combined_rows if " + " in row.get("duplicate_cluster_labels", "")]
        if conflict_rows and any(row["label_status"] != "conflict_needs_review" for row in conflict_rows):
            errors.append("Some label-conflict duplicate rows are not marked conflict_needs_review")

    if errors:
        print("Uniform source validation failed:")
        for error in errors[:100]:
            print(f"- {error}")
        if len(errors) > 100:
            print(f"- ... {len(errors) - 100} more failures")
        raise SystemExit(1)

    print("Uniform source validation passed")


if __name__ == "__main__":
    main()
