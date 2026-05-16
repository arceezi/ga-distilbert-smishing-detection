"""Clean and redact raw smishing candidate messages.

Input:
    data/raw/collected_smishing_candidates.csv

Output:
    data/interim/cleaned_candidates.csv
"""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "raw" / "collected_smishing_candidates.csv"
OUTPUT_PATH = ROOT / "data" / "interim" / "cleaned_candidates.csv"

URL_RE = re.compile(r"\b(?:https?://|www\.)\S+|\b[a-zA-Z0-9.-]+\.(?:com|net|org|ph|io|co|gov|edu)\S*")
EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
ACCT_RE = re.compile(r"(?<!\w)\d{10,20}(?!\w)")
OTP_RE = re.compile(
    r"(?i)\b(?:otp|code|pin|verification code|security code)[:\s#-]*([A-Z0-9-]{4,10})\b"
)
STANDALONE_CODE_RE = re.compile(r"(?<!\w)\d{4,8}(?!\w)")
WHITESPACE_RE = re.compile(r"\s+")


def redact_message(text: str) -> tuple[str, dict[str, bool]]:
    flags = {
        "contains_url": bool(URL_RE.search(text)),
        "contains_phone": bool(PHONE_RE.search(text)),
        "contains_otp": bool(OTP_RE.search(text) or STANDALONE_CODE_RE.search(text)),
    }

    cleaned = EMAIL_RE.sub("<EMAIL>", text)
    cleaned = URL_RE.sub("<URL>", cleaned)
    cleaned = ACCT_RE.sub("<ACCT>", cleaned)
    cleaned = PHONE_RE.sub("<PHONE>", cleaned)
    cleaned = OTP_RE.sub(lambda match: match.group(0).replace(match.group(1), "<OTP>"), cleaned)
    cleaned = STANDALONE_CODE_RE.sub("<OTP>", cleaned)
    cleaned = WHITESPACE_RE.sub(" ", cleaned).strip()

    return cleaned, flags


def truth_value(value: bool) -> str:
    return "true" if value else "false"


def clean_row(row: dict[str, str]) -> dict[str, str]:
    raw = row.get("message_raw", "") or row.get("message_clean", "")
    cleaned, flags = redact_message(raw)

    row["message_clean"] = cleaned
    row["contains_url"] = row.get("contains_url") or truth_value(flags["contains_url"])
    row["contains_phone"] = row.get("contains_phone") or truth_value(flags["contains_phone"])
    row["contains_otp"] = row.get("contains_otp") or truth_value(flags["contains_otp"])

    current_redaction_status = (row.get("redaction_status") or "").strip()
    if current_redaction_status in {"", "pending", "needs_review"}:
        row["redaction_status"] = "redacted" if cleaned != raw else "not_needed"

    row["review_status"] = row.get("review_status") or "candidate"
    return row


def main() -> None:
    if not INPUT_PATH.exists():
        raise SystemExit(f"Input file not found: {INPUT_PATH}")

    with INPUT_PATH.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = [clean_row(dict(row)) for row in reader]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} cleaned rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
