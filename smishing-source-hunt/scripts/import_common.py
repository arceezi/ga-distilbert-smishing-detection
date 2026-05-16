"""Shared helpers for source-specific candidate import scripts."""

from __future__ import annotations

import csv
import json
import re
import urllib.request
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW_CANDIDATES_PATH = ROOT / "data" / "raw" / "collected_smishing_candidates.csv"

URL_RE = re.compile(r"\b(?:https?://|www\.)\S+|\b[a-zA-Z0-9.-]+\.(?:com|net|org|ph|io|co|gov|edu|bd|uk|de|fr|it|es|jp)\S*")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
OTP_RE = re.compile(r"(?i)\b(?:otp|code|pin|verification code|security code)[:\s#-]*[A-Z0-9-]{4,10}\b")


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def default_signal_flags(text: str) -> tuple[str, str, str]:
    return (
        bool_text(bool(URL_RE.search(text))),
        bool_text(bool(PHONE_RE.search(text))),
        bool_text(bool(OTP_RE.search(text))),
    )


def load_existing_rows() -> tuple[list[str], set[str]]:
    if not RAW_CANDIDATES_PATH.exists() or RAW_CANDIDATES_PATH.stat().st_size == 0:
        return [], set()
    with RAW_CANDIDATES_PATH.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return reader.fieldnames or [], {row.get("id", "") for row in reader}


def append_rows(rows: list[dict[str, str]]) -> int:
    fieldnames, _ = load_existing_rows()
    if not fieldnames:
        raise SystemExit(f"Missing CSV header in {RAW_CANDIDATES_PATH}. Run create_schema.py first.")
    if not rows:
        return 0
    with RAW_CANDIDATES_PATH.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writerows(rows)
    return len(rows)


def fetch_text(url: str, timeout: int = 120) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "thesis-smishing-source-hunt/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def today_iso() -> str:
    return date.today().isoformat()


def base_candidate_row(
    *,
    row_id: str,
    message_raw: str,
    label: str,
    original_label: str,
    label_mapping_notes: str,
    source_name: str,
    source_url: str,
    source_type: str,
    dataset_name: str,
    original_file_format: str,
    scam_category: str,
    country_or_region: str,
    language: str,
    reviewer_notes: str,
) -> dict[str, str]:
    contains_url, contains_phone, contains_otp = default_signal_flags(message_raw)
    return {
        "id": row_id,
        "message_raw": message_raw.strip(),
        "message_clean": "",
        "label": label,
        "original_label": original_label,
        "label_mapping_notes": label_mapping_notes,
        "source_name": source_name,
        "source_url": source_url,
        "source_type": source_type,
        "dataset_name": dataset_name,
        "original_file_format": original_file_format,
        "date_collected": today_iso(),
        "scam_category": scam_category,
        "country_or_region": country_or_region,
        "language": language,
        "contains_url": contains_url,
        "contains_phone": contains_phone,
        "contains_otp": contains_otp,
        "redaction_status": "pending",
        "duplicate_status": "unchecked",
        "review_status": "candidate",
        "reviewer_notes": reviewer_notes,
    }
