"""Import English smishing rows from the Bengali SMS Smishing Dataset.

This script imports only rows where:
    source == "English"
    label == "smish"

Rows are added as candidates, not final approved thesis rows. They still need
cleaning, deduplication, and spot/manual review before export.
"""

from __future__ import annotations

import csv
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "raw" / "collected_smishing_candidates.csv"

DATASET_ID = "shariul-islam/bengali-sms-smishing-dataset"
DATASET_URL = "https://huggingface.co/datasets/shariul-islam/bengali-sms-smishing-dataset"
SPLIT_TOTALS = {"train": 5604, "validation": 700, "test": 1401}
PAGE_SIZE = 100

URL_RE = re.compile(r"\b(?:https?://|www\.)\S+|\b[a-zA-Z0-9.-]+\.(?:com|net|org|ph|io|co|gov|edu|bd|tk)\S*")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
OTP_RE = re.compile(r"(?i)\b(?:otp|code|pin|verification code|security code)[:\s#-]*[A-Z0-9-]{4,10}\b")


def fetch_rows(split: str, offset: int) -> list[dict[str, str]]:
    params = urllib.parse.urlencode(
        {
            "dataset": DATASET_ID,
            "config": "default",
            "split": split,
            "offset": offset,
            "length": PAGE_SIZE,
        }
    )
    url = f"https://datasets-server.huggingface.co/rows?{params}"
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "thesis-smishing-source-review/1.0"},
    )

    for attempt in range(8):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.load(response)
            return [item["row"] for item in payload["rows"]]
        except urllib.error.HTTPError as error:
            if error.code == 429 and attempt < 7:
                time.sleep(5 + attempt * 5)
                continue
            raise

    return []


def existing_ids(path: Path) -> tuple[list[str], set[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return [], set()
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames or [], {row.get("id", "") for row in reader}


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def build_row(row: dict[str, str], row_number: int) -> dict[str, str]:
    text = row["text"].strip()
    return {
        "id": f"hf_bengali_sms_smishing_english_smish_{row_number:04d}",
        "message_raw": text,
        "message_clean": "",
        "label": "smishing",
        "original_label": row["label"],
        "label_mapping_notes": "Hugging Face original label 'smish' maps to thesis label 'smishing'; only source == English rows imported.",
        "source_name": "Bengali SMS Smishing Dataset",
        "source_url": DATASET_URL,
        "source_type": "HuggingFace_dataset",
        "dataset_name": "shariul-islam/bengali-sms-smishing-dataset",
        "original_file_format": "Parquet",
        "date_collected": date.today().isoformat(),
        "scam_category": "other",
        "country_or_region": "Bangladesh",
        "language": "English",
        "contains_url": bool_text(bool(URL_RE.search(text))),
        "contains_phone": bool_text(bool(PHONE_RE.search(text))),
        "contains_otp": bool_text(bool(OTP_RE.search(text))),
        "redaction_status": "pending",
        "duplicate_status": "unchecked",
        "review_status": "candidate",
        "reviewer_notes": "Imported as candidate from English-only smish subset; requires cleaning, deduplication, and thesis spot review before approval.",
    }


def main() -> None:
    fieldnames, seen_ids = existing_ids(OUTPUT_PATH)
    if not fieldnames:
        raise SystemExit(f"Missing CSV header in {OUTPUT_PATH}. Run create_schema.py first.")

    imported_rows: list[dict[str, str]] = []
    next_number = 1

    for split, total in SPLIT_TOTALS.items():
        for offset in range(0, total, PAGE_SIZE):
            rows = fetch_rows(split, offset)
            for row in rows:
                if row.get("source") != "English" or row.get("label") != "smish":
                    continue
                candidate = build_row(row, next_number)
                next_number += 1
                if candidate["id"] in seen_ids:
                    continue
                imported_rows.append(candidate)
                seen_ids.add(candidate["id"])
            time.sleep(0.4)

    if imported_rows:
        with OUTPUT_PATH.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writerows(imported_rows)

    print(f"Imported {len(imported_rows)} new English smish candidate rows.")


if __name__ == "__main__":
    main()
