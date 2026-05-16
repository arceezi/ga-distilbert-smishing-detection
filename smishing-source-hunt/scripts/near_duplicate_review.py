"""Find likely near-duplicate/campaign clusters for source-aware QA."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

from review_rules import normalized_message, template_signature


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "interim" / "deduplicated_candidates.csv"
DEFAULT_OUTPUT = ROOT / "data" / "review_batches" / "near_duplicate_clusters.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True)
    parser.add_argument("--min-size", type=int, default=3)
    parser.add_argument("--max-examples", type=int, default=5)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    clusters: dict[str, list[dict[str, str]]] = defaultdict(list)
    with args.input.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if (row.get("source_name") or "").strip() != args.source:
                continue
            signature = template_signature(normalized_message(row))
            if signature:
                clusters[signature].append(row)

    output_rows: list[dict[str, str]] = []
    for signature, rows in sorted(clusters.items(), key=lambda item: len(item[1]), reverse=True):
        if len(rows) < args.min_size:
            continue
        for row in rows[: args.max_examples]:
            output_rows.append(
                {
                    "cluster_signature": signature,
                    "cluster_size": str(len(rows)),
                    "id": row.get("id", ""),
                    "source_name": row.get("source_name", ""),
                    "review_status": row.get("review_status", ""),
                    "message_clean": normalized_message(row),
                }
            )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = ["cluster_signature", "cluster_size", "id", "source_name", "review_status", "message_clean"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Exported {len(output_rows)} clustered example rows to {args.output}")


if __name__ == "__main__":
    main()
