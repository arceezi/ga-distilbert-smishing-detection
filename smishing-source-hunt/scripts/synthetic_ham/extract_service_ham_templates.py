"""Extract auditable legitimate service-ham templates from manual ham rows."""

from __future__ import annotations

import re
from collections import Counter

import pandas as pd

from final_dataset_build_utils import INTERIM_DIR, ensure_dirs, to_json_list, write_csv
from final_dataset_build_utils import AMOUNT_RE, DATE_TIME_RE, EMAIL_RE, LONG_NUM_RE, MASKED_RE, OTP_CONTEXT_RE, OTP_NUM_RE, PHONE_RE, URL_RE


MANUAL_IN = INTERIM_DIR / "manual_ham_no_overlap.csv"
OUT_CSV = INTERIM_DIR / "service_ham_template_patterns.csv"

ALLOWED_CATEGORIES = {
    "otp_verification",
    "banking",
    "telecom",
    "delivery",
    "ewallet",
    "account_security",
    "payment_confirmation",
    "promo_legitimate",
    "government",
    "appointment_reminder",
    "school_work_admin",
}
UNCERTAIN_NOTE_RE = re.compile(r"\b(uncertain|unclear|unsure|conflict|artifact|not readable|illegible|ambiguous)\b", re.I)
BAD_TEMPLATE_RE = re.compile(
    r"\b(free spins?|casino|gambling|crypto|investment bait|login now|mind-blowing|win car|smartphone|ai glasses|al glasses)\b",
    re.I,
)
BRAND_RE = re.compile(r"\b(BDO|BPI|Metrobank|UnionBank|GCash|Maya|PayMaya|Smart|Globe|DITO|J&T Express|J&T|LBC|Lazada|Shopee|Meralco|SSS|PhilHealth|Microsoft|TikTok|Grab)\b", re.I)


def make_template(text: str) -> tuple[str, list[str]]:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    slots = []

    def sub(slot: str, pattern: re.Pattern[str], source: str) -> str:
        nonlocal slots
        new, count = pattern.subn(f"<{slot}>", source)
        if count:
            slots.append(slot)
        return new

    value = sub("EMAIL", EMAIL_RE, value)
    value = sub("URL", URL_RE, value)
    value = sub("PHONE", PHONE_RE, value)
    value = sub("AMOUNT", AMOUNT_RE, value)
    value = sub("DATE_TIME", DATE_TIME_RE, value)
    value = sub("REF_NUM", MASKED_RE, value)
    value = sub("REF_NUM", LONG_NUM_RE, value)
    if OTP_CONTEXT_RE.search(value):
        value = sub("OTP", OTP_NUM_RE, value)
    value, brand_count = BRAND_RE.subn("<BRAND>", value)
    if brand_count:
        slots.append("BRAND")
    value = re.sub(r"(?:<([A-Z_]+)>\s*){2,}", lambda m: f"<{m.group(1)}>", value)
    return value.strip(), slots


def quality_score(template: str, slots: list[str], category: str) -> tuple[str, float, str]:
    words = re.findall(r"[A-Za-z]+", template)
    if len(words) < 4:
        return "low", 0.35, "too short or vague"
    if not slots and category in {"otp_verification", "banking", "delivery", "payment_confirmation"}:
        return "medium", 0.70, "clear category but few variable slots"
    if category in {"otp_verification", "banking", "telecom", "delivery", "ewallet"}:
        return "high", 0.92, "clear service-like template"
    return "medium", 0.78, "legitimate service-like template"


def main() -> None:
    ensure_dirs()
    manual = pd.read_csv(MANUAL_IN, dtype=str, keep_default_na=False)
    grouped: dict[tuple[str, str, str], dict[str, object]] = {}
    skipped = Counter()
    for _, row in manual.iterrows():
        category = row.get("service_category", "") or "unsure"
        notes = f"{row.get('reviewer_notes', '')} {row.get('notes', '')}"
        if category not in ALLOWED_CATEGORIES:
            skipped["disallowed_category"] += 1
            continue
        if row.get("artifact_status", "") and row.get("artifact_status") != "not_artifact":
            skipped["artifact_status"] += 1
            continue
        if UNCERTAIN_NOTE_RE.search(notes):
            skipped["uncertain_note"] += 1
            continue
        source_text = row.get("message_clean") or row.get("message_raw")
        if BAD_TEMPLATE_RE.search(str(source_text or "")):
            skipped["disallowed_scam_or_gambling_language"] += 1
            continue
        template, slots = make_template(source_text)
        if not template:
            skipped["empty_template"] += 1
            continue
        quality, score, note = quality_score(template, slots, category)
        if quality == "low":
            skipped["low_quality"] += 1
            continue
        key = (category, row.get("institution_type", ""), template)
        item = grouped.setdefault(key, {"ids": [], "slots": [], "example": row.get("message_raw", ""), "quality": quality, "score": score, "note": note})
        item["ids"].append(row.get("unified_id", ""))
        item["slots"].extend(slots)

    rows = []
    for idx, ((category, institution_type, template), item) in enumerate(sorted(grouped.items()), start=1):
        rows.append(
            {
                "template_id": f"service_ham_template_{idx:05d}",
                "service_category": category,
                "institution_type": institution_type,
                "template_text": template,
                "variable_slots": to_json_list(item["slots"]),
                "derived_from_unified_ids": ";".join(item["ids"]),
                "example_original_message": item["example"],
                "template_status": "approved_template_candidate",
                "template_quality_score": item["score"],
                "notes": f"{item['quality']} quality; {item['note']}. Derived from approved manual ham.",
            }
        )
    out = pd.DataFrame(rows)
    write_csv(out, OUT_CSV)
    print(f"Templates extracted: {len(out)}")
    print(f"Template rows skipped: {sum(skipped.values())}")
    print(f"Wrote: {OUT_CSV}")


if __name__ == "__main__":
    main()
