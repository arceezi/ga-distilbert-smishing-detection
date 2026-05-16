"""Summarize candidate counts by source, review status, label, and category."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from review_rules import is_approval_safe_english, is_readable_sms, normalized_message


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "interim" / "deduplicated_candidates.csv"


def print_counter(title: str, counter: Counter[tuple[str, ...]]) -> None:
    print(f"\n{title}")
    for key, count in counter.most_common():
        print(f"{count:>6}  " + " | ".join(value or "(blank)" for value in key))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()

    by_source: Counter[tuple[str, ...]] = Counter()
    by_source_status_label: Counter[tuple[str, ...]] = Counter()
    approved_by_category: Counter[tuple[str, ...]] = Counter()
    approved_not_english_safe = 0
    approved_not_readable = 0
    total = 0

    with args.input.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            total += 1
            source = (row.get("source_name") or "").strip()
            status = (row.get("review_status") or "").strip()
            label = (row.get("label") or "").strip()
            category = (row.get("scam_category") or "").strip()
            by_source[(source,)] += 1
            by_source_status_label[(source, status, label)] += 1
            if status == "approved" and label == "smishing":
                approved_by_category[(source, category or "other")] += 1
                text = normalized_message(row)
                if not is_approval_safe_english(text):
                    approved_not_english_safe += 1
                if not is_readable_sms(text):
                    approved_not_readable += 1

    print(f"Total rows: {total}")
    print_counter("Rows by source", by_source)
    print_counter("Rows by source / review_status / label", by_source_status_label)
    print_counter("Approved smishing rows by source / scam_category", approved_by_category)
    print("\nStrict approved-content checks")
    print(f"approved_but_not_english_safe: {approved_not_english_safe}")
    print(f"approved_but_not_readable: {approved_not_readable}")


if __name__ == "__main__":
    main()
