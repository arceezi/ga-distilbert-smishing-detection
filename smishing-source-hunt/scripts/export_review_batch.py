"""Export source-aware batches for manual or spot review."""

from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "interim" / "deduplicated_candidates.csv"
DEFAULT_OUTPUT_DIR = ROOT / "data" / "review_batches"
REVIEW_COLUMNS = [
    "approved_message_raw",
    "id",
    "source_name",
    "dataset_name",
    "message_clean",
    "label",
    "review_status",
    "scam_category",
    "language",
    "duplicate_status",
    "reviewer_notes",
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--status", default="candidate")
    parser.add_argument("--note-contains")
    parser.add_argument("--note-not-contains")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--sample", action="store_true")
    parser.add_argument("--seed", type=int, default=20260507)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    with args.input.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            if args.source != "any" and (row.get("source_name") or "").strip() != args.source:
                continue
            if (row.get("review_status") or "").strip() != args.status and args.status != "any":
                continue
            if args.note_contains and args.note_contains not in (row.get("reviewer_notes") or ""):
                continue
            if args.note_not_contains and args.note_not_contains in (row.get("reviewer_notes") or ""):
                continue
            row["approved_message_raw"] = row.get("message_raw", "")
            rows.append(row)

    if args.sample:
        random.Random(args.seed).shuffle(rows)
    rows = rows[: args.limit]

    output = args.output or DEFAULT_OUTPUT_DIR / f"{args.source.lower().replace(' ', '_')}_{args.status}_batch.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REVIEW_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Exported {len(rows)} rows to {output}")


if __name__ == "__main__":
    main()
