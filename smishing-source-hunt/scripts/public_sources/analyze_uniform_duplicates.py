"""Summarize duplicate overlap clusters from the organized uniform catalog."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "organized" / "combined_public_thesis_sources_uniform.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()

    source_clusters: Counter[str] = Counter()
    label_clusters: Counter[str] = Counter()
    cluster_ids: set[str] = set()
    total_rows = 0
    duplicate_rows = 0
    representatives = 0

    with args.input.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        seen_cluster_sources: dict[str, str] = {}
        seen_cluster_labels: dict[str, str] = {}
        for row in reader:
            total_rows += 1
            if row.get("is_dedup_representative") == "true":
                representatives += 1
            cluster_id = row.get("duplicate_cluster_id", "")
            if not cluster_id:
                continue
            duplicate_rows += 1
            cluster_ids.add(cluster_id)
            seen_cluster_sources.setdefault(cluster_id, row.get("duplicate_cluster_sources", ""))
            seen_cluster_labels.setdefault(cluster_id, row.get("duplicate_cluster_labels", ""))

    for value in seen_cluster_sources.values():
        source_clusters[value] += 1
    for value in seen_cluster_labels.values():
        label_clusters[value] += 1

    print(f"Total rows: {total_rows}")
    print(f"Deduped representative rows: {representatives}")
    print(f"Duplicate clusters: {len(cluster_ids)}")
    print(f"Duplicate rows in clusters: {duplicate_rows}")
    print(f"Extra duplicate rows: {total_rows - representatives}")
    print("\nDuplicate clusters by source:")
    for key, count in source_clusters.most_common(20):
        print(f"{count:>6}  {key}")
    print("\nDuplicate clusters by label:")
    for key, count in label_clusters.most_common(20):
        print(f"{count:>6}  {key}")


if __name__ == "__main__":
    main()
