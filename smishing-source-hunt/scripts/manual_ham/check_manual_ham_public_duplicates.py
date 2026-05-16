"""Check approved manual ham rows against public thesis sources before any merge."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUAL_CSV = ROOT / "data" / "manual_ham_drive" / "final" / "approved_manual_ham.csv"
PUBLIC_CSV = ROOT / "data" / "organized" / "combined_public_thesis_sources_uniform.csv"
OUT_CSV = ROOT / "data" / "manual_ham_drive" / "final" / "manual_ham_public_duplicate_check.csv"

FIELDNAMES = [
    "manual_id",
    "manual_message_text",
    "reviewer_notes",
    "raw_text_available",
    "text_privacy_status",
    "duplicate_status",
    "matched_public_unified_id",
    "matched_public_source_name",
    "matched_public_dataset_name",
    "matched_public_label",
    "matched_public_message_text",
    "normalized_text_key",
]


def normalize_text(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"https?://\S+|www\.\S+|[a-z0-9.-]+\.[a-z]{2,}\S*", "<url>", text)
    text = re.sub(r"\b\d{4,}\b", "<num>", text)
    text = re.sub(r"[^a-z0-9<>]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manual", type=Path, default=MANUAL_CSV)
    parser.add_argument("--public", type=Path, default=PUBLIC_CSV)
    parser.add_argument("--output", type=Path, default=OUT_CSV)
    args = parser.parse_args()

    manual_rows = read_csv(args.manual)
    public_rows = read_csv(args.public)
    public_by_key: dict[str, dict[str, str]] = {}
    for row in public_rows:
        key = normalize_text(row.get("message_text", ""))
        if key and key not in public_by_key:
            public_by_key[key] = row

    output_rows = []
    counts = Counter()
    for row in manual_rows:
        message = row.get("message_clean") or row.get("message_text") or row.get("message_raw") or ""
        key = normalize_text(message)
        match = public_by_key.get(key)
        status = "duplicate_exact_normalized" if match else "no_public_duplicate_found"
        counts[status] += 1
        output_rows.append(
            {
                "manual_id": row.get("manual_id", ""),
                "manual_message_text": message,
                "reviewer_notes": row.get("reviewer_notes", ""),
                "raw_text_available": row.get("raw_text_available", ""),
                "text_privacy_status": row.get("text_privacy_status", ""),
                "duplicate_status": status,
                "matched_public_unified_id": match.get("unified_id", "") if match else "",
                "matched_public_source_name": match.get("source_name", "") if match else "",
                "matched_public_dataset_name": match.get("dataset_name", "") if match else "",
                "matched_public_label": match.get("normalized_label", "") if match else "",
                "matched_public_message_text": match.get("message_text", "") if match else "",
                "normalized_text_key": key,
            }
        )

    write_csv(args.output, output_rows)
    print(f"Checked {len(manual_rows)} approved manual rows against {len(public_rows)} public rows.")
    for status, count in counts.most_common():
        print(f"{status}: {count}")
    print(f"Wrote duplicate check to {args.output}")


if __name__ == "__main__":
    main()
