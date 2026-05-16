"""Classify raw text availability in the collected smishing candidate pool."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

from verify_and_add_raw_clean_text_columns import (
    EMAIL_RE,
    LONG_NUMBER_RE,
    PHONE_RE,
    URL_RE,
    clean_cell,
    clean_message,
    redaction_detected,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "raw" / "collected_smishing_candidates.csv"
OUTPUT_DIR = ROOT / "data" / "organized" / "raw_recovery"
DEFAULT_OUTPUT = OUTPUT_DIR / "collected_smishing_candidates_raw_classified.csv"

RAW_TEXT_CANDIDATE_COLUMNS = [
    "message_raw",
    "message",
    "text",
    "body",
    "sms",
    "content",
    "MainText",
    "Maintext",
    "TEXT",
]

ADDED_COLUMNS = [
    "candidate_raw_text",
    "candidate_clean_text",
    "candidate_raw_text_available",
    "candidate_raw_text_status",
    "candidate_redaction_detected",
    "candidate_placeholder_count",
    "candidate_placeholder_types",
    "candidate_raw_quality_score",
    "candidate_raw_quality_notes",
]

PLACEHOLDER_TYPE_RE = re.compile(
    r"(?i)<\s*(URL|PHONE|PHONE_NUMBER|OTP|EMAIL|ACCT|ACCOUNT|REF_NUM|NAME|AMOUNT|DATE_TIME|NAMED_ENTITY)\s*>|"
    r"\[\s*(URL)\s*\]|\b(PHONE_NUMBER)\b"
)
ASCII_WORD_RE = re.compile(r"[A-Za-z]{2,}")
SMS_CUE_RE = re.compile(
    r"(?i)\b(account|bank|card|verify|verification|otp|code|click|visit|link|urgent|blocked|suspend|parcel|package|delivery|refund|claim|login|update|confirm|security|alert|limited|prize|won)\b"
)


def find_candidate_pool() -> Path:
    if DEFAULT_INPUT.exists():
        return DEFAULT_INPUT
    matches = list(ROOT.rglob("collected_smishing_candidates.csv"))
    if not matches:
        raise SystemExit("Could not locate collected_smishing_candidates.csv")
    return matches[0]


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(dict.fromkeys(fieldnames + ADDED_COLUMNS)), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def is_smishing_label(row: dict[str, str]) -> bool:
    values = [
        clean_cell(row.get("label")).lower(),
        clean_cell(row.get("original_label")).lower(),
    ]
    return any(value in {"smishing", "phishing", "sms phishing", "verified_smishing"} or "smish" in value for value in values)


def is_rejected(row: dict[str, str]) -> bool:
    return "reject" in clean_cell(row.get("review_status")).lower()


def is_duplicate(row: dict[str, str]) -> bool:
    value = clean_cell(row.get("duplicate_status")).lower()
    return bool(value and value not in {"unchecked", "unique", "not_duplicate", "not duplicate"})


def language_is_english_or_clear(row: dict[str, str], text: str) -> tuple[bool, str]:
    language = clean_cell(row.get("language")).lower()
    if language == "english":
        return True, "language=English"
    words = ASCII_WORD_RE.findall(text)
    if len(words) >= 4 and len("".join(words)) >= 18:
        return True, "English inferred from ASCII word content"
    return False, "language is non-English, unknown, or unclear"


def choose_raw_text(row: dict[str, str]) -> tuple[str, str]:
    for column in RAW_TEXT_CANDIDATE_COLUMNS:
        value = clean_cell(row.get(column))
        if value:
            return value, column
    clean_value = clean_cell(row.get("message_clean"))
    if clean_value:
        return clean_value, "message_clean"
    return "", ""


def placeholder_details(text: str) -> tuple[int, str]:
    types: list[str] = []
    for match in PLACEHOLDER_TYPE_RE.finditer(text or ""):
        token = next((group for group in match.groups() if group), "")
        if token:
            types.append(token.upper())
    return len(types), ";".join(sorted(set(types)))


def score_quality(row: dict[str, str], text: str, clean_text: str, redacted: bool, smishing: bool, english: bool) -> tuple[int, str]:
    score = 0
    notes: list[str] = []
    length = len(text.strip())
    word_count = len(ASCII_WORD_RE.findall(text))

    if length >= 40 and word_count >= 6:
        score += 25
        notes.append("meaningful length")
    elif length >= 18 and word_count >= 3:
        score += 10
        notes.append("short but usable length")
    else:
        score -= 20
        notes.append("too short or incomplete")

    if URL_RE.search(text) or PHONE_RE.search(text) or LONG_NUMBER_RE.search(text) or EMAIL_RE.search(text):
        score += 20
        notes.append("contains original-looking URL/phone/number/email evidence")
    if SMS_CUE_RE.search(text):
        score += 10
        notes.append("contains SMS/scam cues")
    if clean_cell(row.get("source_name")) or clean_cell(row.get("source_url")) or clean_cell(row.get("dataset_name")):
        score += 15
        notes.append("source traceability present")
    if smishing:
        score += 20
        notes.append("label maps to smishing")
    else:
        score -= 50
        notes.append("label does not map to smishing")
    if english:
        score += 10
        notes.append("English or English-inferred")
    else:
        score -= 30
    if is_rejected(row):
        score -= 50
        notes.append("review status rejected")
    elif clean_cell(row.get("review_status")).lower() in {"approved", "candidate"}:
        score += 8
        notes.append("review status usable")
    if is_duplicate(row):
        score -= 15
        notes.append("duplicate status not unique/unchecked")
    if redacted:
        score -= 80
        notes.append("placeholder redaction detected")
    if not clean_text:
        score -= 25
        notes.append("clean text empty")
    if "\ufffd" in text or text.count("?") > max(5, word_count // 2):
        score -= 15
        notes.append("possible OCR/encoding breakage")
    return max(0, min(100, score)), "; ".join(notes)


def classify_row(row: dict[str, str]) -> dict[str, str]:
    raw_text, source_column = choose_raw_text(row)
    redacted = redaction_detected(raw_text)
    placeholder_count, placeholder_types = placeholder_details(raw_text)
    smishing = is_smishing_label(row)
    english, english_note = language_is_english_or_clear(row, raw_text)
    clean_text = clean_message(raw_text) if raw_text else ""
    score, notes = score_quality(row, raw_text, clean_text, redacted, smishing, english)

    if not raw_text:
        status = "empty_or_missing"
        available = False
    elif not smishing:
        status = "not_smishing"
        available = False
    elif redacted:
        status = "already_redacted"
        available = False
    elif not english:
        status = "non_english_or_unclear"
        available = False
    elif score < 35:
        status = "needs_review"
        available = False
    else:
        status = "original_looking_raw"
        available = True

    row["candidate_raw_text"] = raw_text
    row["candidate_clean_text"] = clean_text
    row["candidate_raw_text_available"] = "True" if available else "False"
    row["candidate_raw_text_status"] = status
    row["candidate_redaction_detected"] = "True" if redacted else "False"
    row["candidate_placeholder_count"] = str(placeholder_count)
    row["candidate_placeholder_types"] = placeholder_types
    row["candidate_raw_quality_score"] = str(score)
    row["candidate_raw_quality_notes"] = f"raw_column={source_column or 'none'}; {english_note}; {notes}".strip("; ")
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=find_candidate_pool())
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    rows, fieldnames = read_csv(args.input)
    classified = [classify_row(dict(row)) for row in rows]
    write_csv(args.output, classified, fieldnames)

    status_counts = Counter(row["candidate_raw_text_status"] for row in classified)
    raw_available_smishing = sum(
        row["candidate_raw_text_available"] == "True" and is_smishing_label(row)
        for row in classified
    )
    print(f"91k candidate pool path used: {args.input.relative_to(ROOT) if args.input.is_relative_to(ROOT) else args.input}")
    print(f"Number of 91k rows inspected: {len(classified)}")
    print(f"Number of raw-available smishing candidates found: {raw_available_smishing}")
    print("Raw text status counts:")
    for status, count in status_counts.most_common():
        print(f"- {status}: {count}")
    print(f"Output file: {args.output.relative_to(ROOT) if args.output.is_relative_to(ROOT) else args.output}")


if __name__ == "__main__":
    main()
