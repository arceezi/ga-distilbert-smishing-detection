"""Generate synthetic ham from manual and research-backed template families."""

from __future__ import annotations

import argparse
import random
import re
from collections import Counter, defaultdict

import pandas as pd

from final_dataset_build_utils import FINAL_BUILD_DIR, INTERIM_DIR, PUBLIC_DATASET, UNIFIED_COLUMNS, detect_flags, ensure_dirs, normalize_for_overlap, read_csv, write_csv
from research_synthetic_ham_common import clean_message, exact_key, fill_research_template, quality_reject_reason


MANUAL_IN = INTERIM_DIR / "service_ham_template_patterns.csv"
RESEARCH_IN = FINAL_BUILD_DIR / "template_research" / "research_backed_ham_template_families.csv"
OUT_CSV = INTERIM_DIR / "synthetic_service_ham_research_backed_generated.csv"
MANUAL_HAM_IN = INTERIM_DIR / "manual_ham_no_overlap.csv"

TARGET_CATEGORY_DISTRIBUTION = {
    "fixed_format_big_brand_otp": 150,
    "generic_account_verification": 120,
    "risk_based_signin_device_alert": 120,
    "bank_card_transaction_alert": 190,
    "ewallet_login_verification": 150,
    "telecom_otp_service_advisory": 180,
    "delivery_tracking_update": 150,
    "customs_or_fee_request_low_volume": 30,
    "appointment_reminder": 60,
    "government_application_acknowledgment": 50,
}

MANUAL_BRANDS = {
    "otp_verification": ["BDO", "BPI", "Metrobank", "GCash", "Maya", "Your bank", "Your e-wallet"],
    "banking": ["BDO", "BPI", "Metrobank", "Your bank"],
    "telecom": ["Smart", "Globe", "Your telecom provider"],
    "delivery": ["J&T Express", "LBC", "Your courier"],
    "ewallet": ["GCash", "Maya", "Your e-wallet"],
    "payment_confirmation": ["Meralco", "Your bank", "Your e-wallet"],
    "account_security": ["Your bank", "Your e-wallet"],
    "government": ["SSS", "PhilHealth", "Government Service"],
    "appointment_reminder": ["Your clinic", "Clinic"],
}
SAFE_SUFFIXES = [
    "",
    " No reply is needed.",
    " This is an automated notice.",
    " For your reference.",
    " Please check your app for details.",
    " Keep this message for your records.",
    " Use official channels for help.",
    " This message is for your information.",
    " Standard rates may apply.",
    " Your service record has been updated.",
    " Please disregard if already completed.",
    " Check your official account for details.",
    " This confirms your request.",
    " Your reference has been recorded.",
    " Service message only.",
]


def fake_phone(rng: random.Random) -> str:
    return rng.choice(["0917", "0939", "0998"]) + f"{rng.randint(0, 9999999):07d}"


def fake_ref(rng: random.Random) -> str:
    return "".join(str(rng.randint(0, 9)) for _ in range(rng.randint(10, 14)))


def fill_manual_template(template: str, category: str, rng: random.Random, variant_index: int) -> tuple[str, str]:
    value = template
    replacements = {
        "OTP": lambda: "".join(str(rng.randint(0, 9)) for _ in range(rng.choice([4, 5, 6]))),
        "AMOUNT": lambda: rng.choice(["P50", "P100", "P300", "P500", "PHP 1,250.00", "PHP 2,450.75"]),
        "DATE_TIME": lambda: rng.choice(["today", "tomorrow", "12 May 3:45 PM", "15 May 10:20 AM", "27 Aug 6:00 PM"]),
        "PHONE": lambda: fake_phone(rng),
        "EMAIL": lambda: f"user{rng.randint(100, 999)}@example.com",
        "URL": lambda: rng.choice(["https://example.com", "https://example.com/account", "https://example.com/track"]),
        "REF_NUM": lambda: fake_ref(rng),
        "ACCT": lambda: fake_ref(rng),
        "NAME": lambda: "customer",
        "BRAND": lambda: rng.choice(MANUAL_BRANDS.get(category, ["Your service"])),
        "LOCATION": lambda: rng.choice(["Quezon City", "Makati", "Manila", "Cebu City", "Davao City"]),
    }
    for slot, fn in replacements.items():
        value = re.sub(rf"<{slot}>", lambda _: fn(), value)
        value = re.sub(rf"\{{{slot}\}}", lambda _: fn(), value)
    suffix = SAFE_SUFFIXES[variant_index % len(SAFE_SUFFIXES)]
    if suffix and len(value) + len(suffix) <= 300:
        value = value.rstrip(". ") + "." + suffix
    brand = next((b for b in MANUAL_BRANDS.get(category, []) if b in value), "")
    return re.sub(r"\s+", " ", value).strip(), brand


def append_safe_suffix(raw: str, variant_index: int, category: str) -> str:
    if category in {"customs_or_fee_request_low_volume"}:
        allowed = ["", " Use official channels for help.", " Check your official account for details."]
    elif category in {"fixed_format_big_brand_otp", "generic_account_verification", "ewallet_login_verification", "telecom_otp_service_advisory"}:
        allowed = [
            "",
            " Do not share this code.",
            " Enter it only in the official app or site.",
            " No reply is needed.",
            " This is an automated notice.",
            " Use official channels for help.",
            " This code is for your request.",
            " Keep this message for your records.",
            " Please disregard if already completed.",
            " Service message only.",
            " Check your official account for details.",
            " This confirms your request.",
            " Your reference has been recorded.",
            " This message is for your information.",
            " Standard rates may apply.",
        ]
    else:
        allowed = SAFE_SUFFIXES
    suffix = allowed[variant_index % len(allowed)]
    if suffix and len(raw) + len(suffix) <= 320:
        return raw.rstrip(". ") + "." + suffix
    return raw


def build_row(idx: int, raw: str, clean: str, category: str, institution_type: str, template_id: str, family_id: str, basis: str, source_id: str, source_summary: str, source_file: str, brand: str) -> dict:
    flags = detect_flags(raw + " " + clean)
    row = {
        "unified_id": f"synthetic_research_service_ham_{idx:06d}",
        "source_name": "service_ham_template_generator",
        "dataset_name": "synthetic_service_ham_research_backed",
        "source_group": "synthetic_ham_template",
        "source_row_id": f"synthetic_research_row_{idx:06d}",
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
        "raw_lookup_notes": "not applicable; synthetic template row",
        "contains_url": flags["contains_url"],
        "contains_email": flags["contains_email"],
        "contains_phone": flags["contains_phone"],
        "contains_otp": flags["contains_otp"],
        "contains_amount": flags["contains_amount"],
        "contains_account_hint": flags["contains_account_hint"],
        "service_category": category,
        "institution_type": institution_type,
        "source_file": source_file,
        "reviewer_notes": "",
        "data_origin": "synthetic_template",
        "is_synthetic": True,
        "synthetic_template_id": template_id,
        "template_basis": basis,
        "research_source_id": source_id,
        "synthetic_template_family_id": family_id,
        "generation_method": "research_and_manual_template_slot_sampling",
        "notes": f"{source_summary} Brand={brand}; synthetic values only.",
    }
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-count", type=int, default=1300)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--manual-share", type=float, default=0.60)
    parser.add_argument("--research-share", type=float, default=0.40)
    parser.add_argument("--max-per-template", type=int, default=15)
    parser.add_argument("--max-per-family", type=int, default=100)
    parser.add_argument("--max-per-brand-family", type=int, default=20)
    args = parser.parse_args()

    ensure_dirs()
    rng = random.Random(args.seed)
    manual = pd.read_csv(MANUAL_IN, dtype=str, keep_default_na=False) if MANUAL_IN.exists() else pd.DataFrame()
    research = pd.read_csv(RESEARCH_IN, dtype=str, keep_default_na=False)
    manual_ham = read_csv(MANUAL_HAM_IN) if MANUAL_HAM_IN.exists() else pd.DataFrame()
    public = read_csv(PUBLIC_DATASET)
    mishra_ham = public[(public["normalized_label"].eq("ham")) & (public["source_name"].eq("Mishra & Soni"))].copy()
    manual = manual[manual.get("template_status", "").eq("approved_template_candidate")].copy() if not manual.empty else manual

    rows: list[dict] = []
    seen_raw: set[str] = set()
    seen_clean: set[str] = set()
    seen_overlap: set[str] = set()
    for existing in [manual_ham, mishra_ham]:
        if not existing.empty:
            seen_overlap.update(existing["message_raw"].map(normalize_for_overlap))
            seen_overlap.update(existing["message_clean"].map(normalize_for_overlap))
    per_template = Counter()
    per_family = Counter()
    per_brand_family = Counter()

    manual_target = int(round(args.target_count * args.manual_share))
    research_target = args.target_count - manual_target

    def add_row(raw: str, category: str, institution_type: str, template_id: str, family_id: str, basis: str, source_id: str, summary: str, source_file: str, brand: str) -> bool:
        if raw in seen_raw:
            return False
        clean = clean_message(raw)
        if exact_key(clean) in seen_clean:
            return False
        raw_overlap = normalize_for_overlap(raw)
        clean_overlap = normalize_for_overlap(clean)
        if raw_overlap in seen_overlap or clean_overlap in seen_overlap:
            return False
        row = build_row(len(rows) + 1, raw, clean, category, institution_type, template_id, family_id, basis, source_id, summary, source_file, brand)
        if quality_reject_reason(row):
            return False
        rows.append(row)
        seen_raw.add(raw)
        seen_clean.add(exact_key(clean))
        seen_overlap.add(raw_overlap)
        seen_overlap.add(clean_overlap)
        per_template[template_id] += 1
        per_family[family_id] += 1
        per_brand_family[(family_id, brand)] += 1
        return True

    research_by_family = {k: g.to_dict("records") for k, g in research.groupby("family_name")}
    for family_name, desired in TARGET_CATEGORY_DISTRIBUTION.items():
        desired = int(round(desired * research_target / sum(TARGET_CATEGORY_DISTRIBUTION.values())))
        choices = research_by_family.get(family_name, [])
        attempts = 0
        while choices and sum(1 for r in rows if r["service_category"] == family_name) < desired and attempts < desired * 200:
            attempts += 1
            tpl = rng.choice(choices)
            fid = tpl["template_family_id"]
            if per_family[fid] >= min(args.max_per_family, int(tpl.get("max_family_count") or args.max_per_family)):
                continue
            raw, brand = fill_research_template(tpl["template_text"], tpl.get("allowed_brands", ""), rng)
            raw = append_safe_suffix(raw, per_template[fid], family_name)
            if "fixed_format_big_brand_otp" in fid and per_brand_family[(fid, brand)] >= args.max_per_brand_family:
                continue
            if per_template[fid] >= min(args.max_per_template, int(tpl.get("max_variant_count") or args.max_per_template)):
                continue
            add_row(raw, family_name, tpl.get("institution_type", ""), fid, fid, "research_backed_template", tpl.get("source_id", ""), tpl.get("source_basis_summary", ""), str(RESEARCH_IN), brand)

    manual_choices = manual.to_dict("records")
    attempts = 0
    while manual_choices and len(rows) < manual_target + research_target and attempts < args.target_count * 400:
        attempts += 1
        tpl = rng.choice(manual_choices)
        tid = tpl.get("template_id", "")
        family_id = f"manual_{tid}"
        if per_template[tid] >= args.max_per_template or per_family[family_id] >= args.max_per_family:
            continue
        raw, brand = fill_manual_template(tpl.get("template_text", ""), tpl.get("service_category", ""), rng, per_template[tid])
        add_row(raw, "manual_ph_service_templates", tpl.get("institution_type", ""), tid, family_id, "manual_template", "", f"Generated from approved manual service ham template {tid}.", str(MANUAL_IN), brand)

    attempts = 0
    research_choices = research.to_dict("records")
    while research_choices and len(rows) < args.target_count and attempts < args.target_count * 400:
        attempts += 1
        tpl = rng.choice(research_choices)
        fid = tpl["template_family_id"]
        if per_template[fid] >= args.max_per_template:
            continue
        if per_family[fid] >= min(args.max_per_family, int(tpl.get("max_family_count") or args.max_per_family)):
            continue
        raw, brand = fill_research_template(tpl["template_text"], tpl.get("allowed_brands", ""), rng)
        raw = append_safe_suffix(raw, per_template[fid], tpl.get("family_name", ""))
        if per_brand_family[(fid, brand)] >= args.max_per_brand_family:
            continue
        add_row(raw, tpl.get("family_name", ""), tpl.get("institution_type", ""), fid, fid, "research_backed_template", tpl.get("source_id", ""), tpl.get("source_basis_summary", ""), str(RESEARCH_IN), brand)

    out = pd.DataFrame(rows)
    for col in UNIFIED_COLUMNS:
        if col not in out.columns:
            out[col] = ""
    write_csv(out[UNIFIED_COLUMNS], OUT_CSV)
    print(f"Synthetic ham generated: {len(out)}")
    print("Category distribution:")
    for cat, count in sorted(Counter(out["service_category"]).items()):
        print(f"- {cat}: {count}")
    print(f"Wrote: {OUT_CSV}")


if __name__ == "__main__":
    main()
