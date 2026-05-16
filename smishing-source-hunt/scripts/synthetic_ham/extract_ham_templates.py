"""Extract reusable legitimate ham SMS templates from approved manual ham rows."""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APPROVED_CSV = ROOT / "data" / "manual_ham_drive" / "final" / "approved_manual_ham.csv"
OUT_CSV = ROOT / "data" / "manual_ham_drive" / "templates" / "ham_template_patterns.csv"

FIELDNAMES = [
    "template_id",
    "service_category",
    "institution_type",
    "template_text",
    "variable_slots",
    "derived_from_manual_ids",
    "example_original_message",
    "template_status",
    "notes",
]


REPLACEMENTS = [
    ("URL", re.compile(r"https?://\S+|www\.\S+|[a-z0-9-]+\.(?:com|net|org|ph|gov|edu)\S*", re.I)),
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", re.I)),
    ("PHONE", re.compile(r"\b(?:\+?63|0)\s?9\d{2}[\s.-]?\d{3}[\s.-]?\d{4}\b")),
    ("DATE_TIME", re.compile(r"\b(?:today|tomorrow|yesterday|mon|tue|wed|thu|fri|sat|sun|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d{1,2}[:/.-]\d{1,2}(?:[:/.-]\d{2,4})?(?:\s?[ap]m)?)\b", re.I)),
    ("AMOUNT", re.compile(r"\b(?:PHP|P|₱)\s?[\d,]+(?:\.\d{2})?\b", re.I)),
    ("REF_NUM", re.compile(r"\b(?:ref|reference|txn|transaction|trace|account|acct|card)\s*(?:no\.?|#|:)?\s*[A-Z0-9* -]{4,}\b", re.I)),
    ("OTP", re.compile(r"\b\d{4,8}\b")),
]

EXISTING_PLACEHOLDER_PATTERN = re.compile(r"<(OTP|PHONE|URL|ACCT|NAME|EMAIL|AMOUNT|DATE_TIME|REF_NUM|BRAND|LOCATION)>", re.I)
EXCLUDE_NOTE_PATTERN = re.compile(
    r"\b(uncertain|uncertainty|unsure|suspicious|smishing|spam|ocr issue|extraction issue|cropped|low contrast|unresolved conflict|conflict)\b",
    re.I,
)


BRAND_PATTERN = re.compile(
    r"\b(BDO|BPI|Metrobank|UnionBank|GCash|Maya|PayMaya|Globe|Smart|DITO|J&T|LBC|Shopee|Lazada|SSS|PhilHealth|Pag-IBIG)\b",
    re.I,
)


def normalize_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())


def template_message(text: str) -> tuple[str, list[str]]:
    templated = normalize_spaces(text)
    slots = {match.group(1).upper() for match in EXISTING_PLACEHOLDER_PATTERN.finditer(templated)}
    for slot, pattern in REPLACEMENTS:
        templated, count = pattern.subn(f"<{slot}>", templated)
        if count:
            slots.add(slot)
    templated, count = BRAND_PATTERN.subn("<BRAND>", templated)
    if count:
        slots.add("BRAND")
    templated = re.sub(r"(?:<([A-Z_]+)>\s*){2,}", lambda m: f"<{m.group(1)}>", templated)
    return templated, sorted(slots)


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=APPROVED_CSV)
    parser.add_argument("--output", type=Path, default=OUT_CSV)
    args = parser.parse_args()

    if not args.input.exists():
        raise SystemExit(f"Refusing to extract templates: approved manual ham file does not exist: {args.input}")

    rows = read_rows(args.input)
    approved_rows = [
        row for row in rows if row.get("final_label") == "ham" and row.get("review_status") == "approved"
    ]
    if not approved_rows:
        raise SystemExit("Refusing to extract templates: approved_manual_ham.csv has zero approved ham rows.")

    grouped: dict[tuple[str, str, str], dict[str, object]] = {}
    for row in approved_rows:
        reviewer_notes = row.get("reviewer_notes", "")
        if EXCLUDE_NOTE_PATTERN.search(reviewer_notes):
            continue
        message = row.get("message_clean") or row.get("message_raw") or row.get("message_text") or ""
        template_text, slots = template_message(message)
        if not template_text:
            continue
        key = (row.get("service_category", "unsure"), row.get("institution_type", ""), template_text)
        item = grouped.setdefault(
            key,
            {
                "manual_ids": [],
                "example": message,
                "slots": set(),
                "reviewer_notes": set(),
            },
        )
        item["manual_ids"].append(row.get("manual_id", ""))
        item["slots"].update(slots)
        if reviewer_notes:
            item["reviewer_notes"].add(reviewer_notes)

    output_rows = []
    for idx, ((category, institution_type, template_text), item) in enumerate(sorted(grouped.items()), start=1):
        notes = ["Derived only from approved manual ham; examples come from the approved row's available message text."]
        if item["reviewer_notes"]:
            notes.append("Reviewer notes: " + " | ".join(sorted(item["reviewer_notes"])))
        output_rows.append(
            {
                "template_id": f"ham_template_{idx:05d}",
                "service_category": category or "unsure",
                "institution_type": institution_type,
                "template_text": template_text,
                "variable_slots": json.dumps(sorted(item["slots"])),
                "derived_from_manual_ids": ";".join(mid for mid in item["manual_ids"] if mid),
                "example_original_message": item["example"],
                "template_status": "active",
                "notes": " ".join(notes),
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"Wrote {len(output_rows)} templates to {args.output}")


if __name__ == "__main__":
    main()
