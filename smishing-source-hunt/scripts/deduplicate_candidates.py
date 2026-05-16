"""Remove exact duplicate cleaned candidate messages.

Near-duplicate detection can be added later with a documented fuzzy matcher.
Suggested fuzzy similarity threshold: 0.95.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "interim" / "cleaned_candidates.csv"
OUTPUT_PATH = ROOT / "data" / "interim" / "deduplicated_candidates.csv"
WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = WHITESPACE_RE.sub(" ", text)
    return text


def main() -> None:
    if not INPUT_PATH.exists():
        raise SystemExit(f"Input file not found: {INPUT_PATH}")

    seen: set[str] = set()
    kept: list[dict[str, str]] = []
    duplicate_count = 0

    with INPUT_PATH.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []

        for row in reader:
            text = row.get("message_clean") or row.get("message_raw") or ""
            key = normalize_text(text)
            if not key:
                if (row.get("duplicate_status") or "").strip() in {"", "unchecked"}:
                    row["duplicate_status"] = "needs_review"
                kept.append(row)
                continue
            if key in seen:
                duplicate_count += 1
                continue
            seen.add(key)
            if (row.get("duplicate_status") or "").strip() in {"", "unchecked"}:
                row["duplicate_status"] = "unique"
            kept.append(row)

    # TODO: Add fuzzy near-duplicate detection with a documented 0.95 threshold.
    # Keep the clearest and most source-traceable version when near-duplicates exist.

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept)

    print(f"Wrote {len(kept)} rows to {OUTPUT_PATH}")
    print(f"Removed {duplicate_count} exact duplicate rows")


if __name__ == "__main__":
    main()
