"""Report exact normalized overlaps between approved manual ham and public thesis data."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUAL_CSV = ROOT / "data" / "manual_ham_drive" / "final" / "approved_manual_ham.csv"
PUBLIC_CSV = ROOT / "data" / "organized" / "combined_public_thesis_sources_deduped_representatives.csv"
OUT_CSV = ROOT / "data" / "manual_ham_drive" / "final" / "manual_ham_overlap_report.csv"

FIELDNAMES = [
    "manual_id",
    "message_clean",
    "matched_public_unified_id",
    "matched_public_source_name",
    "matched_public_normalized_label",
    "match_type",
    "similarity_score",
    "notes",
]


def normalize_text(text: str) -> str:
    normalized = (text or "").lower()
    normalized = re.sub(r"https?://\S+|www\.\S+|[a-z0-9.-]+\.[a-z]{2,}\S*", "<url>", normalized)
    normalized = re.sub(r"\b(?:\+?63|0)\s?9\d{2}[\s.-]?\d{3}[\s.-]?\d{4}\b", "<phone>", normalized)
    normalized = re.sub(r"\b\d{4,}\b", "<num>", normalized)
    normalized = re.sub(r"[^a-z0-9<>]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


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
    overlap_count = 0
    for row in manual_rows:
        message = row.get("message_clean") or row.get("message_raw") or ""
        key = normalize_text(message)
        match = public_by_key.get(key)
        if match:
            overlap_count += 1
        output_rows.append(
            {
                "manual_id": row.get("manual_id", ""),
                "message_clean": message,
                "matched_public_unified_id": match.get("unified_id", "") if match else "",
                "matched_public_source_name": match.get("source_name", "") if match else "",
                "matched_public_normalized_label": match.get("normalized_label", "") if match else "",
                "match_type": "exact_normalized" if match else "no_exact_normalized_match",
                "similarity_score": "1.0" if match else "0.0",
                "notes": row.get("reviewer_notes", "") if row.get("reviewer_notes", "") else "Fuzzy matching not implemented yet.",
            }
        )

    write_csv(args.output, output_rows)
    print(f"Checked {len(manual_rows)} approved manual ham rows against {len(public_rows)} public rows.")
    print(f"Exact normalized overlaps found: {overlap_count}")
    print(f"Wrote overlap report to {args.output}")


if __name__ == "__main__":
    main()
