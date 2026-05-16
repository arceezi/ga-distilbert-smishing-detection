"""Create starter CSV files for the smishing source hunt workspace."""

from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MAIN_COLUMNS = [
    "id",
    "message_raw",
    "message_clean",
    "label",
    "original_label",
    "label_mapping_notes",
    "source_name",
    "source_url",
    "source_type",
    "dataset_name",
    "original_file_format",
    "date_collected",
    "scam_category",
    "country_or_region",
    "language",
    "contains_url",
    "contains_phone",
    "contains_otp",
    "redaction_status",
    "duplicate_status",
    "review_status",
    "reviewer_notes",
]

DATASET_COLUMNS = [
    "dataset_name",
    "source_url",
    "local_filename",
    "file_format",
    "original_label_column",
    "original_text_column",
    "smishing_count",
    "ham_count",
    "language",
    "license_notes",
    "status",
    "notes",
]

MAIN_FILES = [
    ROOT / "data" / "raw" / "collected_smishing_candidates.csv",
    ROOT / "data" / "interim" / "cleaned_candidates.csv",
    ROOT / "data" / "interim" / "deduplicated_candidates.csv",
    ROOT / "data" / "final" / "approved_smishing_messages.csv",
    ROOT / "data" / "rejected" / "rejected_candidates.csv",
]

DATASET_INVENTORY = ROOT / "data" / "external_datasets" / "dataset_inventory.csv"


def write_header_if_missing(path: Path, columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)


def main() -> None:
    for path in MAIN_FILES:
        write_header_if_missing(path, MAIN_COLUMNS)
    write_header_if_missing(DATASET_INVENTORY, DATASET_COLUMNS)
    print("Schema files are present.")


if __name__ == "__main__":
    main()

