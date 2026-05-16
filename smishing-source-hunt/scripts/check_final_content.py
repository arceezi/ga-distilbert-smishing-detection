"""Validate strict English/readability rules for the final approved export."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from review_rules import (
    approval_english_failure_reason,
    is_approval_safe_english,
    is_readable_sms,
    normalized_message,
    readability_failure_reason,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "final" / "approved_smishing_messages.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--check-raw", action="store_true")
    args = parser.parse_args()

    errors: list[str] = []
    total = 0
    raw_empty_count = 0
    with args.input.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            total += 1
            if args.check_raw:
                if not (row.get("message_raw") or "").strip():
                    raw_empty_count += 1
                if row.get("approved_message_raw") is not None and row.get("approved_message_raw") != row.get("message_raw"):
                    errors.append(f"{row.get('id', '')}: approved_message_raw does not match message_raw")
            text = normalized_message(row)
            english_ok = is_approval_safe_english(text)
            readable_ok = is_readable_sms(text)
            if not english_ok or not readable_ok:
                reason = approval_english_failure_reason(text) or readability_failure_reason(text)
                errors.append(f"{row.get('id', '')}: {reason}")

    if raw_empty_count:
        errors.append(f"{raw_empty_count} rows have empty message_raw")

    if errors:
        print("Strict final content validation failed:")
        for error in errors[:100]:
            print(f"- {error}")
        if len(errors) > 100:
            print(f"- ... {len(errors) - 100} more failures")
        raise SystemExit(1)

    raw_note = " with raw checks" if args.check_raw else ""
    print(f"Strict final content validation passed{raw_note}: {total} rows")


if __name__ == "__main__":
    main()
