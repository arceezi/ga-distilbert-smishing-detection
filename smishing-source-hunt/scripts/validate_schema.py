"""Validate candidate CSV schema and basic thesis data rules."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PATH = ROOT / "data" / "raw" / "collected_smishing_candidates.csv"

REQUIRED_COLUMNS = [
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

VALID_LABELS = {"smishing", "ham", "reject", "unsure", ""}
VALID_REVIEW_STATUSES = {"candidate", "needs_review", "approved", "rejected", ""}


def validate_file(path: Path) -> int:
    errors: list[str] = []

    if not path.exists():
        print(f"File not found: {path}")
        return 1

    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        missing = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
        if missing:
            errors.append(f"Missing required columns: {', '.join(missing)}")

        for row_number, row in enumerate(reader, start=2):
            label = (row.get("label") or "").strip()
            review_status = (row.get("review_status") or "").strip()
            source_name = (row.get("source_name") or "").strip()
            source_url = (row.get("source_url") or "").strip()
            message_raw = (row.get("message_raw") or "").strip()
            message_clean = (row.get("message_clean") or "").strip()
            original_label = (row.get("original_label") or "").strip()
            dataset_name = (row.get("dataset_name") or "").strip()
            mapping_notes = (row.get("label_mapping_notes") or "").strip()

            if label not in VALID_LABELS:
                errors.append(f"Row {row_number}: invalid label '{label}'")
            if review_status not in VALID_REVIEW_STATUSES:
                errors.append(f"Row {row_number}: invalid review_status '{review_status}'")
            if not source_name and not source_url:
                errors.append(f"Row {row_number}: source_name or source_url is required")
            if not message_raw and not message_clean:
                errors.append(f"Row {row_number}: message_raw or message_clean is required")
            if dataset_name and not original_label:
                errors.append(f"Row {row_number}: original_label should be preserved for dataset imports")
            if original_label and label and not mapping_notes:
                errors.append(f"Row {row_number}: label_mapping_notes should explain original_label mapping")

    if errors:
        print("Schema validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Schema validation passed: {path}")
    return 0


def main() -> None:
    path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_PATH
    raise SystemExit(validate_file(path))


if __name__ == "__main__":
    main()

