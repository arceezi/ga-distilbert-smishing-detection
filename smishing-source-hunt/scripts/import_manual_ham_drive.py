"""Import manually curated ham/service SMS files from data/manual_ham_drive/raw."""

from __future__ import annotations

import argparse
import csv
import re
import zipfile
from pathlib import Path

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None


ROOT = Path(__file__).resolve().parents[1]
MANUAL_DIR = ROOT / "data" / "manual_ham_drive"
RAW_DIR = ROOT / "data" / "manual_ham_drive" / "raw"
DRIVE_EXPORT_DIR = RAW_DIR / "drive_export"
OUT_CSV = ROOT / "data" / "manual_ham_drive" / "extracted" / "manual_ham_extracted.csv"
MAX_MANUAL_CLEANED_ROWS = 331

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".heic"}
TEXT_COLUMNS = (
    "cleaned_text",
    "extracted_text",
    "maintext",
    "message",
    "sms",
    "text",
    "body",
    "message_raw",
    "message_text",
    "content",
    "fulltext",
)
MANUAL_ARCHIVE_CSVS = {"THESIS/CLEANED/CLEANED_DATASET.CSV"}
MANUAL_RAW_EXTRACTED_CSVS = {"THESIS/TEXT EXTRACTED/RAW_EXTRACTED_DATASET.CSV"}
KNOWN_PUBLIC_ARCHIVE_CSVS = {
    "THESIS/CLEANED/ANALYSISDATASET (2)_CLEANED.CSV",
    "THESIS/TEXT EXTRACTED/ANALYSISDATASET (2)_TEXT_EXTRACTED.CSV",
    "THESIS/PRECLEANED/ANALYSISDATASET (2).CSV",
}

FIELDNAMES = [
    "manual_id",
    "source_file",
    "source_row_id",
    "message_raw",
    "message_clean",
    "raw_text_available",
    "text_privacy_status",
    "provisional_label",
    "service_category",
    "institution_type",
    "country_or_region",
    "language",
    "contains_url",
    "contains_phone",
    "contains_otp",
    "contains_amount",
    "contains_account_hint",
    "extraction_status",
    "review_status",
    "reviewer_notes",
]


def clean_message(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def has_url(text: str) -> bool:
    return bool(re.search(r"<URL>|https?://|www\.|[a-z0-9-]+\.(com|net|org|ph|gov|edu)\b", text, re.I))


def has_phone(text: str) -> bool:
    return bool(
        re.search(r"<PHONE>|(\+?63|0)\s?9\d{2}[\s.-]?\d{3}[\s.-]?\d{4}\b|\b\d{3,4}[- .]\d{3,4}\b", text, re.I)
    )


def has_otp(text: str) -> bool:
    return bool(
        re.search(r"<OTP>|\b(otp|one[- ]time|verification code|security code|login code|passcode|pin)\b", text, re.I)
    ) or bool(re.search(r"\b(code|pin|otp)\s*(?:is|:)?\s*\d{4,8}\b", text, re.I))


def has_amount(text: str) -> bool:
    return bool(re.search(r"\b(PHP|P|₱)\s?\d|(?:peso|pesos)\b", text, re.I))


def has_account_hint(text: str) -> bool:
    return bool(
        re.search(
            r"<ACCT>|\b(acct|account|card|ending|ref(?:erence)?|txn|transaction|trace|loan|policy)\b",
            text,
            re.I,
        )
    )


def infer_category(text: str) -> str:
    checks = [
        ("otp_verification", r"\b(otp|one[- ]time|verification code|login code|security code)\b"),
        ("banking", r"\b(bank|bdo|bpi|metrobank|unionbank|transaction|debit|credit|card)\b"),
        ("ewallet", r"\b(gcash|maya|paymaya|wallet|cash in|cash-out|cashout)\b"),
        ("delivery", r"\b(parcel|delivery|courier|rider|tracking|j&t|lbc|shopee|lazada)\b"),
        ("telecom", r"\b(globe|smart|dito|load|prepaid|postpaid|sim|data promo)\b"),
        ("government", r"\b(gov|sss|philhealth|pag-ibig|bir|lto|psa|dswd)\b"),
        ("account_security", r"\b(password|login|signed in|security alert|device|account)\b"),
        ("payment_confirmation", r"\b(payment|paid|receipt|confirmed|successful)\b"),
        ("appointment_reminder", r"\b(appointment|schedule|reminder|booking|reservation)\b"),
        ("school_work_admin", r"\b(class|school|student|office|admin|meeting|hr)\b"),
        ("promo_legitimate", r"\b(promo|discount|reward|points|offer)\b"),
    ]
    for category, pattern in checks:
        if re.search(pattern, text, re.I):
            return category
    return "unsure"


def infer_country(text: str) -> str:
    if re.search(r"\b(PHP|₱|Philippines|GCash|Maya|BDO|BPI|Globe|Smart|DITO|SSS|PhilHealth|Pag-IBIG)\b", text, re.I):
        return "Philippines"
    return "unknown"


def infer_language(text: str) -> str:
    if not text:
        return "unsure"
    ascii_letters = sum(1 for ch in text if ch.isascii() and ch.isalpha())
    all_letters = sum(1 for ch in text if ch.isalpha())
    return "English" if all_letters and ascii_letters / all_letters >= 0.85 else "unsure"


def make_row(
    index: int,
    source_file: str,
    source_row_id: str,
    message: str,
    status: str = "imported",
    *,
    message_clean: str | None = None,
    institution_type: str = "",
    reviewer_notes: str = "",
    raw_text_available: bool = True,
    text_privacy_status: str = "raw_ocr_extracted_text",
) -> dict[str, str]:
    clean = clean_message(message_clean if message_clean is not None else message)
    flag_text = f"{message or ''} {clean}"
    return {
        "manual_id": f"manual_ham_{index:06d}",
        "source_file": source_file,
        "source_row_id": str(source_row_id),
        "message_raw": message or "",
        "message_clean": clean,
        "raw_text_available": str(raw_text_available),
        "text_privacy_status": text_privacy_status,
        "provisional_label": "unsure",
        "service_category": infer_category(clean),
        "institution_type": institution_type,
        "country_or_region": infer_country(clean),
        "language": infer_language(clean),
        "contains_url": str(has_url(flag_text)),
        "contains_phone": str(has_phone(flag_text)),
        "contains_otp": str(has_otp(flag_text)),
        "contains_amount": str(has_amount(flag_text)),
        "contains_account_hint": str(has_account_hint(flag_text)),
        "extraction_status": status,
        "review_status": "needs_review",
        "reviewer_notes": reviewer_notes,
    }


def safe_extract_zip(zip_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    destination_root = destination.resolve()
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.infolist():
            target = (destination / member.filename).resolve()
            if destination_root != target and destination_root not in target.parents:
                raise ValueError(f"Unsafe zip member path: {member.filename}")
        zf.extractall(destination)


def extract_available_archives(manual_dir: Path, destination: Path) -> list[Path]:
    zip_paths = sorted(manual_dir.glob("*.zip"))
    for zip_path in zip_paths:
        print(f"Extracting archive {zip_path.name} to {destination}")
        safe_extract_zip(zip_path, destination)
    return zip_paths


def normalize_archive_path(path: Path, raw_dir: Path) -> str:
    return path.relative_to(raw_dir).as_posix()


def is_structured_archive_csv(path: Path, raw_dir: Path) -> bool:
    relative = normalize_archive_path(path, raw_dir)
    archive_relative = relative.removeprefix("drive_export/").upper()
    return archive_relative in MANUAL_ARCHIVE_CSVS


def is_manual_raw_extracted_csv(path: Path, raw_dir: Path) -> bool:
    relative = normalize_archive_path(path, raw_dir)
    archive_relative = relative.removeprefix("drive_export/").upper()
    return archive_relative in MANUAL_RAW_EXTRACTED_CSVS


def is_known_public_archive_csv(path: Path, raw_dir: Path) -> bool:
    relative = normalize_archive_path(path, raw_dir)
    archive_relative = relative.removeprefix("drive_export/").upper()
    return archive_relative in KNOWN_PUBLIC_ARCHIVE_CSVS


def csv_priority(path: Path, raw_dir: Path) -> tuple[int, str]:
    relative = normalize_archive_path(path, raw_dir)
    archive_relative = relative.removeprefix("drive_export/").upper()
    if archive_relative in MANUAL_ARCHIVE_CSVS:
        return (0, relative)
    return (9, relative)


def first_value(row: dict[str, str], candidates: tuple[str, ...]) -> str:
    lowered = {key.lower().strip(): value for key, value in row.items()}
    for candidate in candidates:
        value = lowered.get(candidate)
        if value:
            return str(value)
    return ""


def read_csv(path: Path) -> list[tuple[str, str]]:
    rows = []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            return rows
        text_col = next((c for c in reader.fieldnames if c.lower().strip() in TEXT_COLUMNS), reader.fieldnames[0])
        for idx, row in enumerate(reader, start=1):
            rows.append((str(idx), row.get(text_col, "")))
    return rows


def read_raw_extracted_lookup(path: Path) -> dict[str, str]:
    lookup = {}
    if not path.exists():
        return lookup
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            return lookup
        for idx, row in enumerate(reader, start=1):
            record_id = first_value(row, ("record_id", "messageid", "id")) or str(idx)
            raw_text = first_value(row, ("extracted_text", "maintext", "fulltext", "message_raw", "message_text"))
            if raw_text:
                lookup[record_id] = raw_text
    return lookup


def read_structured_csv(
    path: Path,
    max_rows: int | None = None,
    raw_extracted_lookup: dict[str, str] | None = None,
) -> list[dict[str, str]]:
    rows = []
    with path.open("r", encoding="utf-8-sig", errors="replace", newline="") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames:
            return rows
        for idx, row in enumerate(reader, start=1):
            if max_rows is not None and idx > max_rows:
                break
            record_id = first_value(row, ("record_id", "messageid", "id")) or str(idx)
            raw_text = (raw_extracted_lookup or {}).get(record_id) or first_value(
                row, ("extracted_text", "maintext", "fulltext", "cleaned_text")
            )
            cleaned_text = first_value(row, ("cleaned_text", "extracted_text", "maintext", "fulltext"))
            source = first_value(row, ("source", "sender", "brand"))
            notes = first_value(row, ("notes",))
            trace_notes = []
            if source:
                trace_notes.append(f"source_hint={source}")
            if notes:
                trace_notes.append(f"archive_notes={notes}")
            rows.append(
                {
                    "source_row_id": record_id,
                    "message_raw": raw_text,
                    "message_clean": cleaned_text,
                    "institution_type": source,
                    "reviewer_notes": "; ".join(trace_notes),
                    "dedupe_key": record_id,
                    "raw_text_available": bool((raw_extracted_lookup or {}).get(record_id)),
                }
            )
    return rows


def read_txt(path: Path) -> list[tuple[str, str]]:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return [(str(idx), line) for idx, line in enumerate(lines, start=1)]


def read_xlsx(path: Path) -> list[tuple[str, str]]:
    if pd is None:
        return []
    try:
        frame = pd.read_excel(path)
    except Exception as exc:
        print(f"Skipped {path.name}: pandas could not read workbook ({exc})")
        return []
    if frame.empty:
        return []
    text_col = next((c for c in frame.columns if str(c).lower().strip() in TEXT_COLUMNS), frame.columns[0])
    return [(str(idx + 1), "" if pd.isna(value) else str(value)) for idx, value in enumerate(frame[text_col].tolist())]


def import_rows(raw_dir: Path) -> list[dict[str, str]]:
    rows = []
    next_id = 1
    seen_structured_rows = set()
    raw_extracted_lookup: dict[str, str] = {}
    for raw_path in raw_dir.rglob("*.csv"):
        if is_manual_raw_extracted_csv(raw_path, raw_dir):
            raw_extracted_lookup.update(read_raw_extracted_lookup(raw_path))
    paths = sorted(
        raw_dir.rglob("*"),
        key=lambda p: csv_priority(p, raw_dir) if p.suffix.lower() == ".csv" else (5, str(p)),
    )
    for path in paths:
        if not path.is_file() or path.name.lower() == "readme.md":
            continue
        suffix = path.suffix.lower()
        relative_name = path.relative_to(raw_dir).as_posix()
        if relative_name.startswith("drive_export/") and suffix in {".xlsx", ".txt"}:
            continue
        if suffix == ".csv" and is_known_public_archive_csv(path, raw_dir):
            continue
        if suffix == ".csv" and is_manual_raw_extracted_csv(path, raw_dir):
            continue
        if suffix == ".csv" and relative_name.startswith("drive_export/") and not is_structured_archive_csv(path, raw_dir):
            continue
        if suffix == ".csv" and is_structured_archive_csv(path, raw_dir):
            for item in read_structured_csv(path, max_rows=MAX_MANUAL_CLEANED_ROWS, raw_extracted_lookup=raw_extracted_lookup):
                if not item["message_raw"] and not item["message_clean"]:
                    continue
                if item["dedupe_key"] in seen_structured_rows:
                    continue
                seen_structured_rows.add(item["dedupe_key"])
                rows.append(
                    make_row(
                        next_id,
                        relative_name,
                        item["source_row_id"],
                        item["message_raw"],
                        "imported_structured_archive_text_with_raw_ocr",
                        message_clean=item["message_clean"],
                        institution_type=item["institution_type"],
                        reviewer_notes=item["reviewer_notes"],
                        raw_text_available=item["raw_text_available"],
                        text_privacy_status="raw_ocr_extracted_text",
                    )
                )
                next_id += 1
            continue
        if suffix == ".csv":
            extracted = read_csv(path)
            status = "imported"
        elif suffix == ".txt":
            extracted = read_txt(path)
            status = "imported"
        elif suffix == ".xlsx":
            extracted = read_xlsx(path)
            status = "imported"
        elif suffix in IMAGE_EXTENSIONS:
            continue
        else:
            extracted = [("unsupported", "")]
            status = "unsupported_file_type"
        for source_row_id, message in extracted:
            rows.append(make_row(next_id, relative_name, source_row_id, message, status))
            next_id += 1
    return rows


def write_rows(rows: list[dict[str, str]], out_csv: Path) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with out_csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--output", type=Path, default=OUT_CSV)
    parser.add_argument("--skip-zip-extract", action="store_true", help="Do not extract zip files before importing.")
    args = parser.parse_args()

    if not args.skip_zip_extract:
        extracted = extract_available_archives(MANUAL_DIR, DRIVE_EXPORT_DIR)
        if extracted:
            print(f"Prepared {len(extracted)} archive(s) for local import.")

    rows = import_rows(args.raw_dir)
    write_rows(rows, args.output)
    print(f"Imported {len(rows)} rows into {args.output}")
    print("Image files, if any, are marked needs_manual_transcription.")


if __name__ == "__main__":
    main()
