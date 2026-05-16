"""Generate realistic filled-in synthetic ham from approved service templates."""

from __future__ import annotations

import argparse
import random
import re
from collections import Counter, defaultdict

import pandas as pd

from final_dataset_build_utils import INTERIM_DIR, UNIFIED_COLUMNS, clean_synthetic_text, detect_flags, ensure_dirs, has_placeholder, write_csv


TEMPLATES_IN = INTERIM_DIR / "service_ham_template_patterns.csv"
OUT_CSV = INTERIM_DIR / "synthetic_service_ham_generated.csv"

TARGET_DISTRIBUTION = {
    "otp_verification": 260,
    "banking": 260,
    "telecom": 200,
    "delivery": 150,
    "ewallet": 120,
    "payment_confirmation": 100,
    "account_security": 80,
    "promo_legitimate": 80,
    "government": 30,
    "appointment_reminder": 20,
}

BRANDS_BY_CATEGORY = {
    "otp_verification": ["BDO", "BPI", "Metrobank", "GCash", "Maya", "Your bank", "Your e-wallet"],
    "banking": ["BDO", "BPI", "Metrobank", "Your bank"],
    "telecom": ["Smart", "Globe", "Your telecom provider"],
    "delivery": ["J&T Express", "LBC", "Lazada", "Shopee", "Your courier"],
    "ewallet": ["GCash", "Maya", "Your e-wallet"],
    "payment_confirmation": ["Meralco", "Your bank", "Your e-wallet"],
    "account_security": ["Microsoft", "Your bank", "Your e-wallet"],
    "promo_legitimate": ["Smart", "Globe", "Lazada", "Shopee"],
    "government": ["SSS", "PhilHealth"],
    "appointment_reminder": ["Your clinic", "Your service provider"],
}
AMOUNTS = ["P50", "P100", "P150", "P300", "P500", "PHP 1,000.00", "PHP 2,450.75", "4.95 GigaPoints", "9.95 GigaPoints"]
DATE_TIMES = ["today", "tomorrow", "15-Aug 12:31", "27-Aug 18:05", "04-Oct 02:21", "at 3:45 PM", "on 12 May 2026"]
URLS = ["https://example.com/track", "https://example.com/account", "https://example.com/rewards"]
NAMES = ["Alex", "Maria", "Juan", "Customer"]
SAFE_VARIANTS = [
    "",
    " Thank you.",
    " This is an automated notice.",
    " Keep this message for your records.",
    " No reply is needed.",
    " Please disregard if already completed.",
    " Service message only.",
    " Have a nice day.",
    " For your reference.",
    " Transaction record updated.",
    " Your service record has been updated.",
    " This confirms your request.",
    " This message is for your information.",
    " Standard rates may apply.",
    " Your account record was updated.",
    " This is a legitimate service notification.",
    " Sent by your service provider.",
    " Please check your app for details.",
    " Your reference has been recorded.",
    " This notice does not require a reply.",
]


def fake_phone(rng: random.Random) -> str:
    prefix = rng.choice(["0939", "0917"])
    return prefix + f"{rng.randint(0, 9999999):07d}"


def fake_ref(rng: random.Random) -> str:
    style = rng.choice(["plain", "masked_x", "masked_star", "ending"])
    if style == "masked_x":
        return "XXXXXXXX" + f"{rng.randint(0, 9999):04d}"
    if style == "masked_star":
        return "****" + f"{rng.randint(0, 9999):04d}"
    if style == "ending":
        return "ending in " + f"{rng.randint(0, 9999):04d}"
    digits = rng.randint(8, 12)
    return "".join(str(rng.randint(0, 9)) for _ in range(digits))


def fill_template(template: str, category: str, rng: random.Random, variant_index: int) -> str:
    value = template
    replacements = {
        "OTP": lambda: "".join(str(rng.randint(0, 9)) for _ in range(rng.randint(4, 6))),
        "AMOUNT": lambda: rng.choice(AMOUNTS),
        "DATE_TIME": lambda: rng.choice(DATE_TIMES),
        "PHONE": lambda: fake_phone(rng),
        "EMAIL": lambda: f"user{rng.randint(100, 999)}@example.com",
        "URL": lambda: rng.choice(URLS),
        "REF_NUM": lambda: fake_ref(rng),
        "ACCT": lambda: fake_ref(rng),
        "NAME": lambda: rng.choice(NAMES),
        "BRAND": lambda: rng.choice(BRANDS_BY_CATEGORY.get(category, ["Your service provider"])),
        "LOCATION": lambda: rng.choice(["Makati", "Quezon City", "Cebu", "Davao"]),
    }
    for slot, fn in replacements.items():
        while f"<{slot}>" in value:
            value = value.replace(f"<{slot}>", fn(), 1)
    suffix = SAFE_VARIANTS[variant_index % len(SAFE_VARIANTS)]
    if suffix and len(value) + len(suffix) <= 300:
        value = value.rstrip(". ") + "." + suffix
    return re.sub(r"\s+", " ", value).strip()


def allocate(templates: pd.DataFrame, target_count: int, max_per_template: int) -> tuple[dict[str, int], list[str]]:
    available = Counter(templates["service_category"])
    desired = TARGET_DISTRIBUTION.copy()
    scale = target_count / sum(desired.values())
    desired = {cat: round(count * scale) for cat, count in desired.items()}
    while sum(desired.values()) < target_count:
        desired[max(desired, key=desired.get)] += 1
    while sum(desired.values()) > target_count:
        desired[max(desired, key=desired.get)] -= 1
    allocated = {}
    overflow = 0
    warnings = []
    for cat, count in desired.items():
        capacity = available.get(cat, 0) * max_per_template
        take = min(count, capacity)
        allocated[cat] = take
        if take < count:
            overflow += count - take
            warnings.append(f"{cat}: requested {count}, capacity {capacity}; redistributed {count - take}.")
    categories = [cat for cat in available if available[cat] * max_per_template > allocated.get(cat, 0)]
    cursor = 0
    while overflow and categories:
        cat = categories[cursor % len(categories)]
        if allocated.get(cat, 0) < available[cat] * max_per_template:
            allocated[cat] = allocated.get(cat, 0) + 1
            overflow -= 1
        cursor += 1
        if cursor > target_count * max(1, len(categories)):
            break
    if overflow:
        warnings.append(f"Unallocated rows after capacity limits: {overflow}.")
    return allocated, warnings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-count", type=int, default=1300)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-per-template", type=int, default=20)
    parser.add_argument("--max-per-family", type=int, default=50)
    args = parser.parse_args()

    ensure_dirs()
    rng = random.Random(args.seed)
    templates = pd.read_csv(TEMPLATES_IN, dtype=str, keep_default_na=False)
    templates = templates[templates["template_status"].eq("approved_template_candidate")].copy()
    by_cat = {cat: group.to_dict("records") for cat, group in templates.groupby("service_category")}
    allocated, warnings = allocate(templates, args.target_count, args.max_per_template)
    per_template = Counter()
    seen_raw = set()
    rows = []

    for category, count in allocated.items():
        choices = list(by_cat.get(category, []))
        attempts = 0
        while count > 0 and choices and attempts < count * 100:
            attempts += 1
            template = rng.choice(choices)
            tid = template["template_id"]
            if per_template[tid] >= args.max_per_template:
                continue
            raw = fill_template(template["template_text"], category, rng, per_template[tid])
            if not raw or raw in seen_raw or has_placeholder(raw) or len(raw) > 320:
                continue
            clean = clean_synthetic_text(raw)
            flags = detect_flags(raw + " " + clean)
            idx = len(rows) + 1
            rows.append(
                {
                    "unified_id": f"synthetic_service_ham_{idx:06d}",
                    "source_name": "service_ham_template_generator",
                    "dataset_name": "synthetic_service_ham_from_manual_templates",
                    "source_group": "synthetic_ham_template",
                    "source_row_id": f"synthetic_row_{idx:06d}",
                    "message_raw": raw,
                    "message_clean": clean,
                    "source_label": "ham",
                    "normalized_label": "ham",
                    "label_status": "synthetic_ham_candidate",
                    "review_status": "generated_needs_review",
                    "raw_text_available": True,
                    "raw_text_status": "synthetic_generated_raw",
                    "cleaning_status": "cleaned_from_synthetic_raw",
                    "raw_lookup_status": "not_applicable_synthetic",
                    "raw_lookup_notes": "synthetic row generated from approved manual ham template",
                    "contains_url": flags["contains_url"],
                    "contains_email": flags["contains_email"],
                    "contains_phone": flags["contains_phone"],
                    "contains_otp": flags["contains_otp"],
                    "contains_amount": flags["contains_amount"],
                    "contains_account_hint": flags["contains_account_hint"],
                    "service_category": category,
                    "institution_type": template.get("institution_type", ""),
                    "source_file": str(TEMPLATES_IN),
                    "reviewer_notes": "",
                    "data_origin": "synthetic_template",
                    "is_synthetic": True,
                    "synthetic_template_id": tid,
                    "generation_method": "template_slot_sampling",
                    "notes": f"Generated from {tid}; synthetic values only.",
                }
            )
            seen_raw.add(raw)
            per_template[tid] += 1
            count -= 1

    out = pd.DataFrame(rows)
    for col in UNIFIED_COLUMNS:
        if col not in out.columns:
            out[col] = ""
    write_csv(out[UNIFIED_COLUMNS], OUT_CSV)
    print(f"Synthetic ham generated: {len(out)}")
    if warnings:
        print("Generation warnings:")
        for warning in warnings:
            print(f"- {warning}")
    print(f"Wrote: {OUT_CSV}")


if __name__ == "__main__":
    main()
