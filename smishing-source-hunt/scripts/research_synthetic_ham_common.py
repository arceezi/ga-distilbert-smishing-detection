"""Shared helpers for research-backed synthetic ham generation and validation."""

from __future__ import annotations

import random
import re
from collections import Counter

from final_dataset_build_utils import clean_synthetic_text


BANNED_PATTERNS = [
    "Tap to load preview",
    "Unread",
    "Your telecom providera",
    "Your courierDELIVERY",
    "COD amount ts",
    "Pho20",
    "free spins",
    "casino",
    "betting",
    "gambling",
    "claim prize",
    "win reward now",
    "urgent action required",
    "account will be locked",
    "account will be suspended",
    "verify now or lose access",
    "click this link to unlock",
    "send your OTP",
    "share your OTP",
    "reply with your PIN",
    "password",
    "CVV",
    "seed phrase",
    "crypto investment",
    "double your money",
    "bit.ly",
    "tinyurl",
]

BANNED_RE = re.compile("|".join(re.escape(p) for p in BANNED_PATTERNS), re.I)
SHORT_URL_RE = re.compile(r"\b(?:bit\.ly|tinyurl\.com|t\.co|goo\.gl|ow\.ly|is\.gd|cutt\.ly)\b", re.I)
PLACEHOLDER_RE = re.compile(r"\{[A-Z0-9_]+\}|<[A-Z0-9_]+>")
SMS_LIKE_RE = re.compile(r"[A-Za-z].{8,}")
OTP_CONTEXT_RE = re.compile(r"\b(?:otp|verification code|security code|code|authentication)\b", re.I)
NUM_RE = re.compile(r"\b\d{4,18}\b")
AMOUNT_RE = re.compile(r"\b(?:PHP|P)\s?[\d,]+(?:\.\d{1,2})?\b", re.I)
DATE_TIME_RE = re.compile(r"\b(?:today|tomorrow|\d{1,2} [A-Z][a-z]{2}(?: \d{1,2}:\d{2} [AP]M)?|\d{1,2}:\d{2} [AP]M)\b")
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)


AMOUNTS = ["50.00", "100.00", "300.00", "500.00", "1,250.00", "2,450.75"]
P_AMOUNTS = ["P50", "P100", "P300", "P500"]
DATE_TIMES = ["today", "tomorrow", "12 May 3:45 PM", "15 May 10:20 AM", "27 Aug 6:00 PM"]
DATES = ["12 May", "15 May", "27 Aug", "tomorrow", "today"]
TIMES = ["3:45 PM", "10:20 AM", "6:00 PM", "9:30 AM", "2:14 PM"]
MERCHANTS = ["ACME MART", "Sample Store", "Online Store", "Grocery Hub", "Payment Center"]
LOCATIONS = ["Quezon City", "Makati", "Manila", "Cebu City", "Davao City"]
URLS = ["https://example.com", "https://example.com/track", "https://example.com/account"]


def fake_otp(rng: random.Random) -> str:
    return "".join(str(rng.randint(0, 9)) for _ in range(rng.choice([4, 5, 6])))


def fake_last4(rng: random.Random) -> str:
    return f"{rng.randint(0, 9999):04d}"


def fake_ref(rng: random.Random, digits_min: int = 10, digits_max: int = 18) -> str:
    digits = rng.randint(digits_min, digits_max)
    return "".join(str(rng.randint(0, 9)) for _ in range(digits))


def fake_tracking(rng: random.Random, brand: str = "") -> str:
    if brand == "UPS":
        return "1Z" + "".join(rng.choice("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(16))
    if brand == "USPS":
        return "94" + "".join(str(rng.randint(0, 9)) for _ in range(20))
    if brand in {"DHL", "DHL Express"}:
        return fake_ref(rng, 10, 10)
    return "".join(rng.choice("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(rng.randint(10, 14)))


def split_allowed(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").split("|") if item.strip()]


def fill_research_template(template: str, allowed_brands: str, rng: random.Random) -> tuple[str, str]:
    brands = split_allowed(allowed_brands) or ["Your service"]
    brand = rng.choice(brands)
    replacements = {
        "BRAND": brand,
        "OTP": fake_otp(rng),
        "LAST4": fake_last4(rng),
        "AMOUNT": rng.choice(AMOUNTS),
        "DATE_TIME": rng.choice(DATE_TIMES),
        "DATE": rng.choice(DATES),
        "TIME": rng.choice(TIMES),
        "MERCHANT": rng.choice(MERCHANTS),
        "LOCATION": rng.choice(LOCATIONS),
        "REF_NUM": fake_ref(rng),
        "TRACKING_NUM": fake_tracking(rng, brand),
        "URL": rng.choice(URLS),
    }
    value = template
    for slot, replacement in replacements.items():
        value = value.replace("{" + slot + "}", replacement)
    return re.sub(r"\s+", " ", value).strip(), brand


def normalize_family_key(text: str) -> str:
    value = str(text or "")
    value = URL_RE.sub("<URL>", value)
    value = AMOUNT_RE.sub("<AMOUNT>", value)
    value = DATE_TIME_RE.sub("<DATE_TIME>", value)
    value = re.sub(r"\b(?:acct|account|card) ending \d{4}\b", r"account ending <NUM>", value, flags=re.I)
    value = NUM_RE.sub("<NUM>", value)
    value = re.sub(r"\s+", " ", value.lower()).strip()
    return value


def exact_key(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w<>]+", " ", str(text or "").lower())).strip()


def quality_reject_reason(row: dict, seen_raw: set[str] | None = None, seen_clean: set[str] | None = None) -> str:
    raw = str(row.get("message_raw", "") or "").strip()
    clean = str(row.get("message_clean", "") or "").strip()
    if not raw or not clean:
        return "empty_raw_or_clean"
    if len(raw) > 320:
        return "too_long"
    if PLACEHOLDER_RE.search(raw):
        return "raw_contains_placeholder"
    if BANNED_RE.search(raw) or BANNED_RE.search(clean):
        return "banned_artifact_or_scam_phrase"
    if SHORT_URL_RE.search(raw):
        return "shortened_url"
    if not SMS_LIKE_RE.search(raw):
        return "not_sms_like"
    if str(row.get("is_synthetic", "")).lower() not in {"true", "1", "yes"}:
        return "not_marked_synthetic"
    if row.get("data_origin") != "synthetic_template":
        return "wrong_data_origin"
    if not (row.get("synthetic_template_family_id") or row.get("synthetic_template_id")):
        return "missing_template_family_or_id"
    raw_key = exact_key(raw)
    clean_key = exact_key(clean)
    if seen_raw is not None and raw_key in seen_raw:
        return "duplicate_raw"
    if seen_clean is not None and clean_key in seen_clean:
        return "duplicate_clean"
    return ""


def clean_message(raw: str) -> str:
    clean = clean_synthetic_text(raw)
    clean = re.sub(r"\b(?:card|acct|account) ending <REF_NUM>\b", "account ending <ACCT>", clean, flags=re.I)
    return clean


def count_by(rows: list[dict], key: str) -> Counter:
    return Counter(str(r.get(key, "") or "blank") for r in rows)
