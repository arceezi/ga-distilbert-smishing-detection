"""Audit strict raw text quality for the raw-required public thesis dataset."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "organized" / "raw_recovery" / "combined_public_thesis_sources_deduped_raw_required.csv"
OUTPUT_DIR = ROOT / "data" / "organized" / "raw_quality"
VIOLATIONS_OUTPUT = OUTPUT_DIR / "raw_placeholder_violations.csv"
LONG_REVIEW_OUTPUT = OUTPUT_DIR / "raw_long_message_review.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "raw_quality_audit_summary.csv"
REPORT_PATH = ROOT / "reports" / "strict_raw_text_quality_audit.md"

ANGLE_PLACEHOLDER_RE = re.compile(r"<\s*([A-Z0-9_ -]+)\s*>")
WORD_RE = re.compile(r"[A-Za-z0-9]+")
SMS_CUE_RE = re.compile(
    r"(?i)\b(account|bank|card|verify|verification|otp|code|click|visit|link|urgent|blocked|suspend|parcel|package|delivery|refund|claim|login|update|confirm|security|alert|limited|prize|won|call|text|reply|stop|pay|fee|charge|transaction)\b"
)
REPORT_CUE_RE = re.compile(
    r"(?i)\b(this message says|the message says|the sms says|the text says|reported by|victim reported|news report|"
    r"article|author|researcher|dataset row|screenshot caption|the scammer sent)\b"
)

AUDIT_COLUMNS = [
    "raw_placeholder_detected",
    "raw_placeholder_count",
    "raw_placeholder_types",
    "raw_quality_status",
    "raw_quality_notes",
    "raw_length",
    "token_count",
    "long_message_flag",
    "sms_likeness_status",
]

LONG_COLUMNS = [
    "raw_length",
    "token_count",
    "source_name",
    "dataset_name",
    "normalized_label",
    "review_reason",
    "suggested_action",
]


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(dict.fromkeys(fieldnames)), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def clean_cell(value: object) -> str:
    return "" if value is None else str(value).strip()


def placeholder_types(text: str) -> list[str]:
    return [match.group(1).strip().upper() for match in ANGLE_PLACEHOLDER_RE.finditer(text or "")]


def sms_likeness(text: str) -> str:
    text = text or ""
    length = len(text)
    sentence_count = len(re.findall(r"[.!?]+", text))
    newline_count = text.count("\n")
    has_sms_cue = bool(SMS_CUE_RE.search(text))
    has_report_cue = bool(REPORT_CUE_RE.search(text))
    has_link_or_phone = bool(re.search(r"(?i)\b(?:https?://|www\.|bit\.ly|tinyurl|t\.co|\.com|\.net|\.org|\.ph)\b|\+?\d[\d\s().-]{7,}\d", text))
    direct_address = bool(re.search(r"(?i)\b(?:dear|hi|hello|customer|user|member|cardholder)\b", text))

    if has_report_cue or (length > 900 and sentence_count >= 8 and not has_sms_cue and not has_link_or_phone):
        return "possible_report_or_article_text"
    if length <= 320 and (has_sms_cue or has_link_or_phone or direct_address):
        return "likely_sms"
    if length > 320 and (has_sms_cue or has_link_or_phone or direct_address) and newline_count <= 8:
        return "possible_multipart_sms"
    return "needs_review"


def classify_row(row: dict[str, str]) -> dict[str, str]:
    raw = clean_cell(row.get("message_raw"))
    tokens = placeholder_types(raw)
    token_count = len(WORD_RE.findall(raw))
    raw_length = len(raw)
    likeness = sms_likeness(raw)

    if not raw:
        status = "fail_empty_raw"
        notes = "message_raw is empty."
    elif raw_length < 5:
        status = "fail_too_short"
        notes = "message_raw has fewer than 5 meaningful characters."
    elif tokens:
        status = "fail_placeholder_anonymized"
        notes = "message_raw contains angle-bracket placeholder/anonymized tokens."
    elif raw_length > 320:
        status = "review_too_long"
        notes = "message_raw is longer than 320 characters; manual SMS-likeness review recommended."
    elif likeness == "needs_review":
        status = "review_sms_likeness"
        notes = "message_raw lacks strong SMS-like cues."
    else:
        status = "pass_raw"
        notes = "No strict raw placeholder issues detected."

    audited = dict(row)
    audited["raw_placeholder_detected"] = "True" if tokens else "False"
    audited["raw_placeholder_count"] = str(len(tokens))
    audited["raw_placeholder_types"] = ";".join(sorted(set(tokens)))
    audited["raw_quality_status"] = status
    audited["raw_quality_notes"] = notes
    audited["raw_length"] = str(raw_length)
    audited["token_count"] = str(token_count)
    audited["long_message_flag"] = "True" if raw_length > 320 else "False"
    audited["sms_likeness_status"] = likeness
    return audited


def long_review_row(row: dict[str, str]) -> dict[str, str]:
    likeness = row["sms_likeness_status"]
    if likeness == "possible_report_or_article_text":
        suggested = "remove_if_not_sms_like"
    elif likeness in {"likely_sms", "possible_multipart_sms"}:
        suggested = "keep_if_sms_like"
    else:
        suggested = "review_if_report_text"
    output = dict(row)
    output["review_reason"] = "message_raw length > 320"
    output["suggested_action"] = suggested
    return output


def markdown_table(rows: list[dict[str, str]], columns: list[str]) -> list[str]:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return lines


def counter_rows(counter: Counter[str], key_name: str) -> list[dict[str, str]]:
    return [{key_name: key or "(blank)", "rows": str(count)} for key, count in counter.most_common()]


def write_report(audited: list[dict[str, str]], violations: list[dict[str, str]], long_rows: list[dict[str, str]]) -> None:
    label_counts = Counter(row.get("normalized_label", "") for row in audited)
    status_counts = Counter(row.get("raw_quality_status", "") for row in audited)
    placeholder_counts: Counter[str] = Counter()
    for row in violations:
        for token in row.get("raw_placeholder_types", "").split(";"):
            if token:
                placeholder_counts[token] += 1

    summary_rows = [
        {"metric": "rows_inspected", "value": str(len(audited))},
        {"metric": "placeholder_violation_rows", "value": str(len(violations))},
        {"metric": "long_message_rows", "value": str(len(long_rows))},
        {"metric": "ham_rows", "value": str(label_counts.get("ham", 0))},
        {"metric": "smishing_rows", "value": str(label_counts.get("smishing", 0))},
    ]
    write_csv(SUMMARY_OUTPUT, summary_rows, ["metric", "value"])

    lines = [
        "# Strict Raw Text Quality Audit",
        "",
        "## Purpose",
        "",
        "This audit checks whether `message_raw` in the raw-required dataset is truly original-looking. Any angle-bracket entity placeholder is treated as source-anonymized raw text and is not acceptable for the strict raw dataset.",
        "",
        "## Summary",
        "",
        *markdown_table(summary_rows, ["metric", "value"]),
        "",
        "## Raw Quality Status Counts",
        "",
        *markdown_table(counter_rows(status_counts, "raw_quality_status"), ["raw_quality_status", "rows"]),
        "",
        "## Placeholder Types",
        "",
        *markdown_table(counter_rows(placeholder_counts, "placeholder_type"), ["placeholder_type", "rows"]),
        "",
        "## Violations By Source",
        "",
        *markdown_table(counter_rows(Counter(row.get("source_name", "") for row in violations), "source_name"), ["source_name", "rows"]),
        "",
        "## Violations By Dataset",
        "",
        *markdown_table(counter_rows(Counter(row.get("dataset_name", "") for row in violations), "dataset_name"), ["dataset_name", "rows"]),
        "",
        "## Violations By Label",
        "",
        *markdown_table(counter_rows(Counter(row.get("normalized_label", "") for row in violations), "normalized_label"), ["normalized_label", "rows"]),
        "",
        "## Long Message Review",
        "",
        f"- Rows longer than 320 characters: {len(long_rows):,}",
        f"- Possible report/article text: {sum(row.get('sms_likeness_status') == 'possible_report_or_article_text' for row in long_rows):,}",
        f"- Likely SMS or multipart SMS: {sum(row.get('sms_likeness_status') in {'likely_sms', 'possible_multipart_sms'} for row in long_rows):,}",
        "",
        "## Files Generated",
        "",
        f"- `{VIOLATIONS_OUTPUT.relative_to(ROOT)}`",
        f"- `{LONG_REVIEW_OUTPUT.relative_to(ROOT)}`",
        f"- `{SUMMARY_OUTPUT.relative_to(ROOT)}`",
        f"- `{REPORT_PATH.relative_to(ROOT)}`",
        "",
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    args = parser.parse_args()

    rows, fieldnames = read_csv(args.input)
    audited = [classify_row(row) for row in rows]
    violations = [row for row in audited if row["raw_quality_status"] in {"fail_placeholder_anonymized", "fail_empty_raw", "fail_too_short"}]
    long_rows = [long_review_row(row) for row in audited if row["long_message_flag"] == "True"]

    audit_fieldnames = list(dict.fromkeys(fieldnames + AUDIT_COLUMNS))
    write_csv(VIOLATIONS_OUTPUT, violations, audit_fieldnames)
    write_csv(LONG_REVIEW_OUTPUT, long_rows, list(dict.fromkeys(audit_fieldnames + LONG_COLUMNS)))
    write_report(audited, violations, long_rows)

    print(f"Input dataset path: {args.input.relative_to(ROOT) if args.input.is_relative_to(ROOT) else args.input}")
    print(f"Rows inspected: {len(audited)}")
    print(f"Raw placeholder violations found: {sum(row['raw_quality_status'] == 'fail_placeholder_anonymized' for row in audited)}")
    print(f"Empty/too-short raw failures found: {sum(row['raw_quality_status'] in {'fail_empty_raw', 'fail_too_short'} for row in audited)}")
    print(f"Long messages flagged: {len(long_rows)}")
    print("Output paths:")
    for path in [VIOLATIONS_OUTPUT, LONG_REVIEW_OUTPUT, SUMMARY_OUTPUT]:
        print(f"- {path.relative_to(ROOT)}")
    print(f"Report path: {REPORT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
