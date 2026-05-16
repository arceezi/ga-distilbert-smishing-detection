"""Export approved smishing messages from deduplicated candidates."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "interim" / "deduplicated_candidates.csv"
OUTPUT_PATH = ROOT / "data" / "final" / "approved_smishing_messages.csv"
VALID_MESSAGE_VERSIONS = {"clean", "raw"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=INPUT_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument(
        "--message-version",
        choices=sorted(VALID_MESSAGE_VERSIONS),
        default="clean",
        help="Export approved rows with either the redacted clean message or an added raw approved message column.",
    )
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Input file not found: {args.input}")

    with args.input.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = [
            row
            for row in reader
            if (row.get("label") or "").strip() == "smishing"
            and (row.get("review_status") or "").strip() == "approved"
        ]

    output_fieldnames = list(fieldnames)
    if args.message_version == "raw":
        output_fieldnames = ["approved_message_raw", *output_fieldnames]
        for row in rows:
            row["approved_message_raw"] = row.get("message_raw", "")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Exported {len(rows)} approved smishing rows to {args.output} ({args.message_version})")


if __name__ == "__main__":
    main()
