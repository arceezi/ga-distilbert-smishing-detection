"""Verify and add raw/clean text columns to public thesis source catalogs."""

from __future__ import annotations

import csv
import html
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ORGANIZED_DIR = ROOT / "data" / "organized"
SOURCE_ARCHIVE_DIR = ROOT / "data" / "source_archives" / "public_baseline"
FINAL_DIR = ROOT / "data" / "final"
OUTPUT_DIR = ORGANIZED_DIR / "text_verified"
REPORT_PATH = ROOT / "reports" / "raw_clean_text_verification.md"

TEXT_COLUMNS = [
    "message_raw",
    "message_clean",
    "raw_text_available",
    "raw_text_status",
    "cleaning_status",
    "redaction_detected_in_raw",
    "raw_lookup_status",
    "raw_lookup_notes",
]

SOURCE_INPUTS = {
    "UCI SMS Spam Collection": {
        "uniform": ORGANIZED_DIR / "uci_sms_spam_collection_uniform.csv",
        "output": OUTPUT_DIR / "uci_sms_spam_collection_text_verified.csv",
        "expected_rows": 5574,
    },
    "Mishra & Soni": {
        "uniform": ORGANIZED_DIR / "mishra_soni_sms_dataset_uniform.csv",
        "output": OUTPUT_DIR / "mishra_soni_sms_dataset_text_verified.csv",
        "expected_rows": 5971,
    },
    "SmishTank": {
        "uniform": ORGANIZED_DIR / "smishtank_uniform.csv",
        "output": OUTPUT_DIR / "smishtank_text_verified.csv",
        "expected_rows": 1062,
    },
    "Gathered approved smishing 7k": {
        "uniform": ORGANIZED_DIR / "gathered_approved_smishing_7k_uniform.csv",
        "output": OUTPUT_DIR / "gathered_approved_smishing_7k_text_verified.csv",
        "expected_rows": 7000,
    },
}

COMBINED_INPUT = ORGANIZED_DIR / "combined_public_thesis_sources_uniform.csv"
DEDUPED_INPUT = ORGANIZED_DIR / "combined_public_thesis_sources_deduped_representatives.csv"
COMBINED_OUTPUT = OUTPUT_DIR / "combined_public_thesis_sources_text_verified.csv"
DEDUPED_OUTPUT = OUTPUT_DIR / "combined_public_thesis_sources_deduped_representatives_text_verified.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "raw_clean_text_verification_summary.csv"

EXPECTED_COMBINED_ROWS = 19607

PLACEHOLDER_VARIANTS = {
    "PHONE_NUMBER": "PHONE",
    "MOBILE": "PHONE",
    "LINK": "URL",
    "ACCOUNT_NUMBER": "ACCT",
    "ACCOUNT": "ACCT",
    "REFERENCE_NUMBER": "REF_NUM",
    "REF": "REF_NUM",
    "CODE": "OTP",
}

PLACEHOLDER_RE = re.compile(
    r"(?i)(<\s*(URL|PHONE|PHONE_NUMBER|MOBILE|OTP|EMAIL|ACCT|ACCOUNT|ACCOUNT_NUMBER|"
    r"REF_NUM|REFERENCE_NUMBER|NAME|AMOUNT|DATE_TIME|NAMED_ENTITY|LINK|CODE)\s*>|"
    r"\[\s*URL\s*\]|\bPHONE_NUMBER\b)"
)
URL_RE = re.compile(
    r"(?i)\b(?:https?://|hxxps?://|www\.)[^\s<>]+|"
    r"\b[a-z0-9][a-z0-9.-]*\.(?:com|net|org|info|us|co|uk|ph|io|biz|xyz|ly|me|site|online|top|click|shop|app)[^\s<>,;:!?)]*"
)
SPACED_DOMAIN_RE = re.compile(
    r"(?i)\b([a-z0-9][a-z0-9.-]*)\s+\.(com|net|org|info|us|co|uk|ph|io|biz|xyz|ly|me|site|online|top|click|shop|app)\b"
)
EMAIL_RE = re.compile(r"(?i)\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b")
MONEY_RE = re.compile(r"(?i)(?:[$£€₱]\s?\d[\d,]*(?:\.\d{1,2})?|\b(?:php|usd|gbp|eur|rs)\s?\d[\d,]*(?:\.\d{1,2})?)")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
OTP_CONTEXT_RE = re.compile(
    r"(?i)\b(?:otp|one[-\s]?time|verification|verify|security|auth(?:entication)?|login|passcode|pin|code)\b"
)
OTP_VALUE_RE = re.compile(r"(?<!\w)(?:\d{4,8}|[A-Z0-9]{5,10})(?!\w)")
ACCT_CONTEXT_RE = re.compile(r"(?i)\b(?:account|acct|card|debit|credit)\b")
REF_CONTEXT_RE = re.compile(r"(?i)\b(?:ref|reference|tracking|transaction|txn|order|case|ticket|parcel|package)\b")
LONG_NUMBER_RE = re.compile(r"(?<!\w)\d[\d\s-]{8,}\d(?!\w)")
WHITESPACE_RE = re.compile(r"\s+")
BROKEN_PUNCT_RE = re.compile(r"\s+([,.;:!?])(?=\s|$)")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    final_fieldnames = list(dict.fromkeys(fieldnames + TEXT_COLUMNS))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=final_fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_csv_exact(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def as_bool_text(value: bool) -> str:
    return "True" if value else "False"


def clean_cell(value: object) -> str:
    return "" if value is None else str(value).strip()


def redaction_detected(text: str) -> bool:
    text = html.unescape(text or "")
    if PLACEHOLDER_RE.search(text):
        return True
    return text.strip() in {"URL", "PHONE_NUMBER"}


def normalize_placeholders(text: str) -> str:
    text = html.unescape(text or "")

    def replace(match: re.Match[str]) -> str:
        token = match.group(2)
        whole = match.group(0)
        if not token:
            if whole.strip("[]").upper() == "URL" or whole.upper() == "URL":
                token = "URL"
            elif whole.upper() == "PHONE_NUMBER":
                token = "PHONE"
        token = (token or "").upper()
        token = PLACEHOLDER_VARIANTS.get(token, token)
        return f"<{token}>"

    return PLACEHOLDER_RE.sub(replace, text)


def replace_contextual_numbers(text: str) -> str:
    words = text.split(" ")
    output: list[str] = []
    previous_context = ""
    for word in words:
        stripped = word.strip(".,;:!?)(")
        prefix = word[: len(word) - len(word.lstrip("([{"))]
        suffix = word[len(word.rstrip(".,;:!?)]}")) :]
        candidate = stripped.strip("([{)]}")
        lower_context = f"{previous_context} {candidate}".lower()
        if OTP_CONTEXT_RE.search(lower_context) and OTP_VALUE_RE.fullmatch(candidate):
            output.append(f"{prefix}<OTP>{suffix}")
        elif ACCT_CONTEXT_RE.search(lower_context) and LONG_NUMBER_RE.fullmatch(candidate):
            output.append(f"{prefix}<ACCT>{suffix}")
        elif REF_CONTEXT_RE.search(lower_context) and LONG_NUMBER_RE.fullmatch(candidate):
            output.append(f"{prefix}<REF_NUM>{suffix}")
        else:
            output.append(word)
        previous_context = candidate
    return " ".join(output)


def clean_message(text: str) -> str:
    text = normalize_placeholders(text or "")
    text = SPACED_DOMAIN_RE.sub(r"\1.\2", text)
    text = EMAIL_RE.sub("<EMAIL>", text)
    text = URL_RE.sub("<URL>", text)
    text = MONEY_RE.sub("<AMOUNT>", text)
    text = replace_contextual_numbers(text)
    text = PHONE_RE.sub("<PHONE>", text)
    text = BROKEN_PUNCT_RE.sub(r"\1", text)
    text = WHITESPACE_RE.sub(" ", text).strip()
    return text


def load_uci_archive() -> dict[str, str]:
    path = SOURCE_ARCHIVE_DIR / "SMSSpamCollection 1.csv"
    if not path.exists():
        return {}
    lookup: dict[str, str] = {}
    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader, start=1):
            lookup[str(index)] = clean_cell(row.get("Maintext"))
    return lookup


def load_mishra_archive() -> dict[str, str]:
    path = SOURCE_ARCHIVE_DIR / "Dataset_5971 (1).zip"
    if not path.exists():
        return {}
    lookup: dict[str, str] = {}
    with zipfile.ZipFile(path) as archive:
        with archive.open("Dataset_5971.csv") as raw_handle:
            text_lines = (line.decode("utf-8", errors="replace") for line in raw_handle)
            reader = csv.DictReader(text_lines)
            for index, row in enumerate(reader, start=1):
                lookup[str(index)] = clean_cell(row.get("TEXT"))
    return lookup


def load_smishtank_archive() -> dict[str, str]:
    path = SOURCE_ARCHIVE_DIR / "analysisdataset.csv"
    if not path.exists():
        return {}
    lookup: dict[str, str] = {}
    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader, start=1):
            row_id = clean_cell(row.get("messageid")) or str(index)
            lookup[row_id] = clean_cell(row.get("MainText")) or clean_cell(row.get("Fulltext"))
            lookup.setdefault(str(index), lookup[row_id])
    return lookup


def choose_gathered_text(row: dict[str, str]) -> tuple[str, str, str]:
    candidates = [
        ("message_raw", clean_cell(row.get("message_raw"))),
        ("message", clean_cell(row.get("message"))),
        ("message_text", clean_cell(row.get("message_text"))),
        ("text", clean_cell(row.get("text"))),
        ("body", clean_cell(row.get("body"))),
        ("message_clean", clean_cell(row.get("message_clean"))),
    ]
    non_empty = [(name, value) for name, value in candidates if value]
    if not non_empty:
        return "", "", "No usable gathered source text column found."
    unredacted = [(name, value) for name, value in non_empty if not redaction_detected(value)]
    if unredacted:
        name, value = unredacted[0]
        return value, name, f"Selected gathered final `{name}` as the least-redacted available text."
    name, value = non_empty[0]
    return value, name, f"Selected gathered final `{name}`; available source text already contains placeholders."


def load_gathered_archive() -> dict[str, tuple[str, str]]:
    path = FINAL_DIR / "approved_smishing_messages.csv"
    if not path.exists():
        return {}
    lookup: dict[str, tuple[str, str]] = {}
    for index, row in enumerate(read_csv(path), start=1):
        row_id = clean_cell(row.get("id")) or str(index)
        text, _column, note = choose_gathered_text(row)
        lookup[row_id] = (text, note)
        lookup.setdefault(str(index), (text, note))
    return lookup


def annotate_row(
    row: dict[str, str],
    *,
    source_name: str,
    archive_lookup: dict[str, str] | dict[str, tuple[str, str]],
) -> dict[str, str]:
    source_row_id = clean_cell(row.get("source_row_id"))
    existing_text = clean_cell(row.get("message_text"))
    raw_text = ""
    lookup_status = "source_archive_missing"
    lookup_notes = "No source archive text lookup was available."

    if archive_lookup:
        if source_row_id in archive_lookup:
            value = archive_lookup[source_row_id]
            if isinstance(value, tuple):
                raw_text, lookup_notes = value
            else:
                raw_text = value
                lookup_notes = "Recovered source text from the original source archive using source_row_id."
            lookup_status = "found_in_source_archive"
        else:
            raw_text = existing_text
            lookup_status = "row_match_failed"
            lookup_notes = "Source archive was available, but source_row_id did not match; used existing message_text."
    else:
        raw_text = existing_text

    if not raw_text and existing_text:
        raw_text = existing_text
        lookup_status = "used_existing_message_text"
        lookup_notes = "Used existing message_text because no better source text was available."

    detected = redaction_detected(raw_text)
    if detected:
        raw_available = False
        raw_status = "already_redacted"
        cleaning_status = "cleaned_from_already_redacted"
        if lookup_status == "found_in_source_archive":
            lookup_status = "already_redacted_source"
    elif lookup_status == "found_in_source_archive":
        raw_available = True
        raw_status = "original_unredacted"
        cleaning_status = "cleaned_from_raw"
    elif raw_text:
        raw_available = False
        raw_status = "unavailable_used_existing_message_text"
        cleaning_status = "cleaned_from_already_redacted" if detected else "cleaned_from_raw"
        lookup_status = "used_existing_message_text" if lookup_status == "source_archive_missing" else lookup_status
    else:
        raw_available = False
        raw_status = "unknown_needs_review"
        cleaning_status = "failed_needs_review"
        lookup_status = "needs_manual_review"
        lookup_notes = "No raw or existing message text was found."

    if source_name == "Gathered approved smishing 7k" and detected:
        lookup_status = "already_redacted_source"
        raw_status = "already_redacted"
        raw_available = False
        cleaning_status = "cleaned_from_already_redacted"

    row["message_raw"] = raw_text
    row["message_clean"] = clean_message(raw_text)
    row["raw_text_available"] = as_bool_text(raw_available)
    row["raw_text_status"] = raw_status
    row["cleaning_status"] = cleaning_status if row["message_clean"] else "failed_needs_review"
    row["redaction_detected_in_raw"] = as_bool_text(detected)
    row["raw_lookup_status"] = lookup_status
    row["raw_lookup_notes"] = lookup_notes
    return row


def verify_source(source_name: str, archive_lookup: dict) -> tuple[list[dict[str, str]], list[str]]:
    config = SOURCE_INPUTS[source_name]
    rows = read_csv(config["uniform"])
    fieldnames = list(rows[0].keys()) if rows else []
    verified = [annotate_row(dict(row), source_name=source_name, archive_lookup=archive_lookup) for row in rows]
    write_csv(config["output"], verified, fieldnames)
    return verified, fieldnames


def combine_verified(source_rows: dict[str, list[dict[str, str]]], combined_fieldnames: list[str]) -> list[dict[str, str]]:
    combined: list[dict[str, str]] = []
    by_unified_id = {
        row.get("unified_id", ""): row
        for rows in source_rows.values()
        for row in rows
    }
    for original in read_csv(COMBINED_INPUT):
        unified_id = original.get("unified_id", "")
        replacement = by_unified_id.get(unified_id)
        if replacement:
            combined.append({**original, **{column: replacement.get(column, "") for column in TEXT_COLUMNS}})
        else:
            combined.append(annotate_row(dict(original), source_name=original.get("source_name", ""), archive_lookup={}))
    write_csv(COMBINED_OUTPUT, combined, combined_fieldnames)
    return combined


def write_deduped(combined_rows: list[dict[str, str]], deduped_fieldnames: list[str]) -> list[dict[str, str]]:
    existing_ids = [row.get("unified_id", "") for row in read_csv(DEDUPED_INPUT)]
    by_id = {row.get("unified_id", ""): row for row in combined_rows}
    deduped = [by_id[row_id] for row_id in existing_ids if row_id in by_id]
    write_csv(DEDUPED_OUTPUT, deduped, deduped_fieldnames)
    return deduped


def obvious_raw_artifacts(text: str) -> bool:
    return bool(URL_RE.search(text or "") or EMAIL_RE.search(text or "") or PHONE_RE.search(text or ""))


def summarize(rows: list[dict[str, str]]) -> dict[str, Counter]:
    return {
        "raw_status": Counter(row.get("raw_text_status", "") for row in rows),
        "cleaning_status": Counter(row.get("cleaning_status", "") for row in rows),
        "lookup_status": Counter(row.get("raw_lookup_status", "") for row in rows),
    }


def validation_checks(
    source_rows: dict[str, list[dict[str, str]]],
    combined_rows: list[dict[str, str]],
    deduped_rows: list[dict[str, str]],
) -> list[dict[str, str]]:
    current_deduped_count = len(read_csv(DEDUPED_INPUT))
    checks: list[dict[str, str]] = []

    def add(name: str, passed: bool, details: str) -> None:
        checks.append({"check": name, "status": "PASS" if passed else "FAIL", "details": details})

    for source_name, config in SOURCE_INPUTS.items():
        rows = source_rows[source_name]
        add(
            f"{source_name} row count",
            len(rows) == config["expected_rows"],
            f"expected={config['expected_rows']}; actual={len(rows)}",
        )

    add(
        "Combined raw total",
        len(combined_rows) == EXPECTED_COMBINED_ROWS,
        f"expected={EXPECTED_COMBINED_ROWS}; actual={len(combined_rows)}",
    )
    add(
        "Deduped representative count unchanged",
        len(deduped_rows) == current_deduped_count,
        f"expected_current={current_deduped_count}; actual={len(deduped_rows)}",
    )

    add(
        "Every row has message_clean",
        all(clean_cell(row.get("message_clean")) for row in combined_rows),
        f"empty={sum(1 for row in combined_rows if not clean_cell(row.get('message_clean')))}",
    )
    add(
        "Every row has message_raw or failure status",
        all(clean_cell(row.get("message_raw")) or row.get("cleaning_status") == "failed_needs_review" for row in combined_rows),
        f"empty_raw={sum(1 for row in combined_rows if not clean_cell(row.get('message_raw')))}",
    )

    raw_eq_clean_unredacted = sum(
        1
        for row in combined_rows
        if row.get("message_raw") == row.get("message_clean") and row.get("raw_text_status") == "original_unredacted"
    )
    raw_contains_placeholders = sum(1 for row in combined_rows if row.get("redaction_detected_in_raw") == "True")
    clean_contains_artifacts = sum(1 for row in combined_rows if obvious_raw_artifacts(row.get("message_clean", "")))
    add("Flag raw equals clean while unredacted", True, f"flagged={raw_eq_clean_unredacted}")
    add("Flag placeholders detected in raw", True, f"flagged={raw_contains_placeholders}")
    add("Flag obvious raw URLs/phones/emails in clean", clean_contains_artifacts == 0, f"flagged={clean_contains_artifacts}")
    return checks


def write_summary(source_rows: dict[str, list[dict[str, str]]]) -> list[dict[str, str]]:
    summary_rows: list[dict[str, str]] = []
    for source_name, rows in source_rows.items():
        status_counts = Counter(row["raw_text_status"] for row in rows)
        lookup_counts = Counter(row["raw_lookup_status"] for row in rows)
        summary_rows.append(
            {
                "source_name": source_name,
                "rows": str(len(rows)),
                "raw_text_available_true": str(sum(row["raw_text_available"] == "True" for row in rows)),
                "raw_text_available_false": str(sum(row["raw_text_available"] == "False" for row in rows)),
                "original_unredacted_count": str(status_counts.get("original_unredacted", 0)),
                "already_redacted_count": str(status_counts.get("already_redacted", 0)),
                "source_archive_missing_count": str(lookup_counts.get("source_archive_missing", 0)),
                "row_match_failed_count": str(lookup_counts.get("row_match_failed", 0)),
                "redaction_detected_in_raw_count": str(sum(row["redaction_detected_in_raw"] == "True" for row in rows)),
            }
        )
    write_csv_exact(
        SUMMARY_OUTPUT,
        summary_rows,
        [
            "source_name",
            "rows",
            "raw_text_available_true",
            "raw_text_available_false",
            "original_unredacted_count",
            "already_redacted_count",
            "source_archive_missing_count",
            "row_match_failed_count",
            "redaction_detected_in_raw_count",
        ],
    )
    return summary_rows


def markdown_table(rows: list[dict[str, str]], columns: list[str]) -> list[str]:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row.get(column, "") for column in columns) + " |")
    return lines


def write_report(
    *,
    source_rows: dict[str, list[dict[str, str]]],
    summary_rows: list[dict[str, str]],
    combined_rows: list[dict[str, str]],
    deduped_rows: list[dict[str, str]],
    checks: list[dict[str, str]],
) -> None:
    gathered_rows = source_rows["Gathered approved smishing 7k"]
    gathered_redacted = sum(row["raw_text_status"] == "already_redacted" for row in gathered_rows)
    gathered_original = sum(row["raw_text_status"] == "original_unredacted" for row in gathered_rows)
    source_findings = []
    for source in ["UCI SMS Spam Collection", "Mishra & Soni", "SmishTank"]:
        rows = source_rows[source]
        original = sum(row["raw_text_status"] == "original_unredacted" for row in rows)
        redacted = sum(row["raw_text_status"] == "already_redacted" for row in rows)
        source_findings.append(f"- {source}: {original:,} original/unredacted rows; {redacted:,} already-redacted rows.")

    raw_unavailable = sum(row["raw_text_available"] == "False" for row in combined_rows)
    raw_found = sum(row["raw_lookup_status"] == "found_in_source_archive" for row in combined_rows)
    already_redacted = sum(row["raw_text_status"] == "already_redacted" for row in combined_rows)

    status_by_source = []
    cleaning_by_source = []
    for source, rows in source_rows.items():
        for status, count in sorted(Counter(row["raw_text_status"] for row in rows).items()):
            status_by_source.append({"source_name": source, "raw_text_status": status, "rows": str(count)})
        for status, count in sorted(Counter(row["cleaning_status"] for row in rows).items()):
            cleaning_by_source.append({"source_name": source, "cleaning_status": status, "rows": str(count)})

    files = [
        str(SOURCE_INPUTS["UCI SMS Spam Collection"]["output"].relative_to(ROOT)),
        str(SOURCE_INPUTS["Mishra & Soni"]["output"].relative_to(ROOT)),
        str(SOURCE_INPUTS["SmishTank"]["output"].relative_to(ROOT)),
        str(SOURCE_INPUTS["Gathered approved smishing 7k"]["output"].relative_to(ROOT)),
        str(COMBINED_OUTPUT.relative_to(ROOT)),
        str(DEDUPED_OUTPUT.relative_to(ROOT)),
        str(SUMMARY_OUTPUT.relative_to(ROOT)),
        str(REPORT_PATH.relative_to(ROOT)),
    ]

    lines = [
        "# Raw/Clean Text Verification Report",
        "",
        "## 1. Purpose",
        "",
        "This workflow separates the best available source message text from a privacy-normalized modeling version. `message_raw` preserves the original source text when it is available, while `message_clean` standardizes placeholders and redacts obvious URLs, emails, phone-like values, OTP/code values, references, accounts, and amounts without removing scam cues such as urgency, brand names, banking terms, and delivery terms.",
        "",
        "## 2. Source Summary Table",
        "",
        *markdown_table(
            summary_rows,
            [
                "source_name",
                "rows",
                "raw_text_available_true",
                "raw_text_available_false",
                "original_unredacted_count",
                "already_redacted_count",
                "source_archive_missing_count",
                "row_match_failed_count",
                "redaction_detected_in_raw_count",
            ],
        ),
        "",
        "## 3. Gathered 7k Finding",
        "",
    ]
    if gathered_redacted and not gathered_original:
        lines.append(
            "The gathered approved smishing 7k source contains placeholder tokens in the available source text. Since no unredacted raw source was found, these rows are marked as already_redacted and raw_text_available=False."
        )
    elif gathered_redacted:
        lines.append(
            f"The gathered approved smishing 7k source is mixed: {gathered_original:,} rows use available original-looking raw text and {gathered_redacted:,} rows already contain placeholder tokens. Placeholder rows are not de-redacted."
        )
    else:
        lines.append(
            "The gathered approved smishing 7k source has an available `message_raw` column and no placeholder tokens were detected in that selected raw text."
        )

    lines.extend(
        [
            "",
            "## 4. UCI/Mishra/SmishTank Finding",
            "",
            *source_findings,
            "",
            "## 5. Cleaning Rules Used",
            "",
            "- Standardized placeholder variants such as `<PHONE_NUMBER>`, `<MOBILE>`, `<LINK>`, `[URL]`, `<ACCOUNT_NUMBER>`, `<REFERENCE_NUMBER>`, and contextual `<CODE>`.",
            "- Replaced URLs with `<URL>` and email addresses with `<EMAIL>`.",
            "- Replaced phone-like values with `<PHONE>`.",
            "- Replaced OTP/code-like values with `<OTP>` only near OTP, verification, login, security, PIN, passcode, or code context.",
            "- Replaced account/card-like long numbers with `<ACCT>` and reference/tracking/order-like long numbers with `<REF_NUM>` when context is present.",
            "- Replaced money amounts with `<AMOUNT>` and normalized whitespace/punctuation spacing.",
            "",
            "## 6. Validation Results",
            "",
            *markdown_table(checks, ["check", "status", "details"]),
            "",
            "### Counts By Raw Text Status",
            "",
            *markdown_table(status_by_source, ["source_name", "raw_text_status", "rows"]),
            "",
            "### Counts By Cleaning Status",
            "",
            *markdown_table(cleaning_by_source, ["source_name", "cleaning_status", "rows"]),
            "",
            f"- Combined rows: {len(combined_rows):,}",
            f"- Deduped representative rows: {len(deduped_rows):,}",
            f"- Rows where raw text was found in source archives: {raw_found:,}",
            f"- Rows where raw text is unavailable: {raw_unavailable:,}",
            f"- Rows already redacted: {already_redacted:,}",
            "",
            "Duplicate cluster fields were preserved from the existing uniform catalogs. They were not recomputed from `message_clean`, so representative selection remains comparable to the current deduped file.",
            "",
            "## 7. Files Generated",
            "",
            *[f"- `{path}`" for path in files],
            "",
            "## 8. Recommended Next Step",
            "",
            "Model-ready dataset building should use `message_raw` when evaluating real-world raw-message performance, or `message_clean` when evaluating privacy-normalized or placeholder-normalized performance. The choice should be consistent across train/test splits and explicitly reported in the thesis methodology.",
            "",
        ]
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    archive_lookups = {
        "UCI SMS Spam Collection": load_uci_archive(),
        "Mishra & Soni": load_mishra_archive(),
        "SmishTank": load_smishtank_archive(),
        "Gathered approved smishing 7k": load_gathered_archive(),
    }

    source_rows: dict[str, list[dict[str, str]]] = {}
    source_fieldnames: dict[str, list[str]] = {}
    for source_name in SOURCE_INPUTS:
        rows, fieldnames = verify_source(source_name, archive_lookups[source_name])
        source_rows[source_name] = rows
        source_fieldnames[source_name] = fieldnames

    combined_fieldnames = list(read_csv(COMBINED_INPUT)[0].keys())
    deduped_fieldnames = list(read_csv(DEDUPED_INPUT)[0].keys())
    combined_rows = combine_verified(source_rows, combined_fieldnames)
    deduped_rows = write_deduped(combined_rows, deduped_fieldnames)
    summary_rows = write_summary(source_rows)
    checks = validation_checks(source_rows, combined_rows, deduped_rows)
    write_report(
        source_rows=source_rows,
        summary_rows=summary_rows,
        combined_rows=combined_rows,
        deduped_rows=deduped_rows,
        checks=checks,
    )

    total_raw_found = sum(row["raw_lookup_status"] == "found_in_source_archive" for row in combined_rows)
    total_already_redacted = sum(row["raw_text_status"] == "already_redacted" for row in combined_rows)

    print("Files created:")
    for path in [
        SOURCE_INPUTS["UCI SMS Spam Collection"]["output"],
        SOURCE_INPUTS["Mishra & Soni"]["output"],
        SOURCE_INPUTS["SmishTank"]["output"],
        SOURCE_INPUTS["Gathered approved smishing 7k"]["output"],
        COMBINED_OUTPUT,
        DEDUPED_OUTPUT,
        SUMMARY_OUTPUT,
        REPORT_PATH,
    ]:
        print(f"- {path.relative_to(ROOT)}")
    print()
    print("Command to run text verification:")
    print("python scripts/verify_and_add_raw_clean_text_columns.py")
    print()
    print("Row counts per source:")
    for source_name, rows in source_rows.items():
        raw_found = sum(row["raw_lookup_status"] == "found_in_source_archive" for row in rows)
        redacted = sum(row["raw_text_status"] == "already_redacted" for row in rows)
        print(f"- {source_name}: {len(rows)} rows; raw found={raw_found}; already redacted={redacted}")
    print()
    print(f"Number of rows where raw text was found: {total_raw_found}")
    print(f"Number of rows already redacted: {total_already_redacted}")
    print(f"Path to report: {REPORT_PATH.relative_to(ROOT)}")
    print("Reminder: gathered 7k may remain redacted if no raw source exists; placeholders are never reversed.")


if __name__ == "__main__":
    main()
