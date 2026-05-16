"""Export approved synthetic ham and a manual-plus-synthetic candidate file."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APPROVED_MANUAL = ROOT / "data" / "manual_ham_drive" / "final" / "approved_manual_ham.csv"
GENERATED_SYNTHETIC = ROOT / "data" / "manual_ham_drive" / "templates" / "generated_synthetic_ham.csv"
APPROVED_SYNTHETIC = ROOT / "data" / "manual_ham_drive" / "final" / "approved_synthetic_ham.csv"
CANDIDATES = ROOT / "data" / "manual_ham_drive" / "final" / "manual_plus_synthetic_ham_candidates.csv"

FIELDNAMES = [
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
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def manual_to_unified(row: dict[str, str], idx: int) -> dict[str, str]:
    return {
        "unified_id": f"manual_ham_real_{idx:06d}",
        "source_name": "manual_ham_drive",
        "dataset_name": "manual_ham_drive_approved",
        "source_group": "manual_real_ham",
        "source_row_id": row.get("manual_id", ""),
        "message_text": row.get("message_clean") or row.get("message_raw", ""),
        "source_label": row.get("final_label", "ham"),
        "normalized_label": "ham",
        "label_status": "manual_approved",
        "review_status": row.get("review_status", "approved"),
        "contains_url": row.get("contains_url", ""),
        "contains_email": row.get("contains_email", "False"),
        "contains_phone": row.get("contains_phone", ""),
        "source_file": row.get("source_file", ""),
        "notes": row.get("reviewer_notes", ""),
    }


def synthetic_to_unified(row: dict[str, str], idx: int, approve_all: bool = False) -> dict[str, str]:
    review_status = "approved" if approve_all else row.get("review_status", "generated_needs_review")
    label_status = "synthetic_approved" if review_status == "approved" else row.get("label_status", "synthetic_candidate")
    return {
        "unified_id": f"synthetic_ham_{idx:06d}",
        "source_name": row.get("source_name", "manual_ham_template_generation"),
        "dataset_name": "manual_ham_synthetic_candidates",
        "source_group": row.get("source_group", "synthetic_ham_template"),
        "source_row_id": row.get("synthetic_id", ""),
        "message_text": row.get("message_text", ""),
        "source_label": "ham",
        "normalized_label": "ham",
        "label_status": label_status,
        "review_status": review_status,
        "contains_url": row.get("contains_url", ""),
        "contains_email": row.get("contains_email", ""),
        "contains_phone": row.get("contains_phone", ""),
        "source_file": row.get("template_id", ""),
        "notes": row.get("notes", ""),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approve-all", action="store_true", help="Mark all generated synthetic rows approved for export.")
    args = parser.parse_args()

    manual_rows = [row for row in read_csv(APPROVED_MANUAL) if row.get("final_label") == "ham" and row.get("review_status") == "approved"]
    synthetic_rows = read_csv(GENERATED_SYNTHETIC)
    unified_manual = [manual_to_unified(row, idx) for idx, row in enumerate(manual_rows, start=1)]
    unified_synthetic = [synthetic_to_unified(row, idx, args.approve_all) for idx, row in enumerate(synthetic_rows, start=1)]
    approved_synthetic = [row for row in unified_synthetic if row["review_status"] == "approved"]

    write_csv(APPROVED_SYNTHETIC, approved_synthetic)
    write_csv(CANDIDATES, unified_manual + unified_synthetic)
    print(f"Approved synthetic ham rows: {len(approved_synthetic)} -> {APPROVED_SYNTHETIC}")
    print(f"Combined candidate rows: {len(unified_manual) + len(unified_synthetic)} -> {CANDIDATES}")


if __name__ == "__main__":
    main()
