#!/usr/bin/env python
"""Build raw-complete conversational/general spam candidates for IAA balancing."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "expert_review_iaa"
OUT_PATH = OUT_DIR / "conversational_spam_candidate_pool.csv"
REPORT_PATH = OUT_DIR / "conversational_spam_candidate_pool_report.md"
CURRENT_PACKET = OUT_DIR / "expert_spam_review_500_raw_complete.csv"
FINAL_V3 = ROOT / "data" / "final_dataset_build" / "final" / "dataset_v3_public_manual_research_synthetic_ham_balanced.csv"

SOURCES = [
    ROOT / "data" / "organized" / "uci_sms_spam_collection_uniform.csv",
    ROOT / "data" / "organized" / "mishra_soni_sms_dataset_uniform.csv",
    ROOT / "data" / "organized" / "combined_public_thesis_sources_uniform.csv",
    ROOT / "data" / "organized" / "combined_public_thesis_sources_deduped_representatives.csv",
    ROOT / "data" / "organized" / "text_verified" / "combined_public_thesis_sources_text_verified.csv",
    ROOT / "data" / "organized" / "raw_recovery" / "collected_smishing_candidates_raw_classified.csv",
    ROOT / "data" / "raw" / "collected_smishing_candidates.csv",
    OUT_DIR / "expert_spam_review_source_pool.csv",
    OUT_DIR / "raw_complete_expert_replacement_pool.csv",
]

PLACEHOLDER_RE = re.compile(r"<\s*[A-Z0-9_ -]+\s*>")
URL_RE = re.compile(r"https?://\S+|www\.\S+|(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/\S*)?", re.I)
PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{6,}\d)")
AMOUNT_RE = re.compile(r"(?:[$£€]|rs\.?|php|usd|gbp|eur)\s*\d+(?:[,.]\d+)*|\d+(?:[,.]\d+)*(?:\s?(?:php|usd|gbp|eur|rs|p))", re.I)

OUT_COLS = [
    "candidate_id",
    "source_name",
    "dataset_name",
    "source_group",
    "source_row_id",
    "source_file",
    "message_raw",
    "message_clean",
    "source_label",
    "normalized_label",
    "label_status",
    "review_status",
    "candidate_reason",
    "spam_signal_score",
    "smishing_signal_score",
    "likely_review_bucket",
    "bucket_reason",
    "raw_quality_status",
    "contains_url",
    "contains_phone",
    "contains_otp",
    "contains_amount",
    "suggested_category",
    "scam_category",
    "notes",
    "selection_priority_score",
    "duplicate_key",
]


def text_value(row: pd.Series, *cols: str) -> str:
    for col in cols:
        if col in row.index:
            value = str(row.get(col, "")).strip()
            if value and value.lower() not in {"nan", "none", "null"}:
                return value
    return ""


def boolish(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y", "available"}


def normalize_text(text: str) -> str:
    text = str(text).lower()
    text = URL_RE.sub(" <URL> ", text)
    text = re.sub(r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", " <EMAIL> ", text)
    text = PHONE_RE.sub(" <PHONE> ", text)
    text = re.sub(r"\b(?:otp|pin|code|passcode|verification)\s*[:#-]?\s*[a-z0-9-]{4,10}\b", " <OTP> ", text)
    text = re.sub(r"\b[a-z]{1,4}\d{4,10}\b|\b\d{4,8}[a-z]{1,4}\b", " <OTP> ", text)
    text = re.sub(r"\b\d{9,}\b", " <REF_NUM> ", text)
    text = AMOUNT_RE.sub(" <AMOUNT> ", text)
    text = re.sub(r"[^a-z0-9<>]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def raw_complete(raw: str, row: pd.Series) -> bool:
    raw = str(raw).strip()
    if not raw or len(raw) < 12 or len(re.findall(r"\b\w+\b", raw)) < 3:
        return False
    if PLACEHOLDER_RE.search(raw) or "&lt;" in raw.lower() or "&gt;" in raw.lower():
        return False
    raw_available = text_value(row, "raw_text_available", "candidate_raw_text_available")
    if raw_available and raw_available.lower() in {"false", "0", "no", "unavailable"}:
        return False
    raw_status = text_value(row, "raw_text_status", "candidate_raw_text_status", "redaction_status").lower()
    if raw_status in {"already_redacted", "redacted", "placeholder_only", "missing"}:
        return False
    if raw.strip().startswith("[") and raw.strip().endswith("]") and (raw.count("',") or raw.count('",')):
        return False
    if any(term in raw.lower() for term in ["screenshot", "ocr", "image may contain", "reported by", "commentary", "reply to scammer"]):
        return False
    letters = len(re.findall(r"[^\W\d_]", raw, re.UNICODE))
    ascii_letters = len(re.findall(r"[A-Za-z]", raw))
    return letters > 0 and ascii_letters / max(letters, 1) >= 0.85


def signals(text: str, source_label: str = "", normalized_label: str = "") -> tuple[int, int, str, str, str]:
    low = text.lower()
    spam_score = 0
    smish_score = 0
    reasons: list[str] = []

    spam_patterns = [
        (r"\bfree\b|\boffer\b|discount|sale|promo|voucher", 2, "promotional_offer"),
        (r"ringtone|poly|tone|music|sms subscription|mobile content|txt .* to \d|text .* to \d", 3, "ringtone_subscription"),
        (r"adult|xxx|sex|chat|dating|hot singles|porn", 3, "adult_chat_promo"),
        (r"casino|bet|gambl|free spin|jackpot", 2, "gambling_promo"),
        (r"reply stop|txt stop|text stop|unsubscribe|opt out|stop to", 3, "opt_out_ad"),
        (r"\bcall \d|premium|per min|p per|150p|50p|£1\.50", 2, "premium_number_ad"),
        (r"prize|winner|won|reward|claim", 2, "prize_reward_ad"),
    ]
    smish_patterns = [
        (r"bank|account|acct|card|wallet|paypal|venmo|zelle|cash app", 3, "bank_account_bait"),
        (r"login|password|otp|pin|cvv|credential|verification code", 4, "credential_or_otp_request"),
        (r"verify|verification|update your|confirm|validate|restore", 3, "verification_action"),
        (r"locked|suspend|restricted|blocked|unauthorized|security alert", 4, "account_threat"),
        (r"delivery|parcel|package|shipment|courier|usps|ups|fedex|dhl|address issue|redelivery", 3, "delivery_bait"),
        (r"government|tax|irs|hmrc|benefit|fine|refund", 3, "government_bait"),
        (r"https?://|www\.", 1, "link_present"),
        (r"urgent|immediately|within \d+ hours|today only|final notice", 2, "urgency"),
        (r"payment|pay fee|unpaid|billing|charge|refund", 3, "payment_bait"),
    ]
    for pattern, points, reason in spam_patterns:
        if re.search(pattern, low):
            spam_score += points
            reasons.append(reason)
    for pattern, points, reason in smish_patterns:
        if re.search(pattern, low):
            smish_score += points
            reasons.append(reason)

    if source_label.lower() == "spam" or normalized_label.lower() == "spam":
        spam_score += 3
        reasons.append("original_spam_label")
    if "smish" in source_label.lower() or normalized_label.lower() == "smishing":
        smish_score += 2

    if any(term in low for term in ["stop texting me", "fuck off", "who is this"]) or len(text) > 320:
        bucket = "unclear_review"
        reasons.append("possible_reply_or_length_review")
    elif spam_score >= smish_score + 2 and smish_score < 5:
        bucket = "likely_spam_not_smishing"
    elif smish_score >= 5 or smish_score > spam_score:
        bucket = "likely_smishing"
    elif spam_score >= 3:
        bucket = "likely_spam_not_smishing"
    else:
        bucket = "unclear_review"

    category = "unclear suspicious message"
    if "ringtone_subscription" in reasons:
        category = "telecom/ringtone/subscription spam"
    elif "adult_chat_promo" in reasons:
        category = "adult/chat promo"
    elif "gambling_promo" in reasons:
        category = "gambling/casino/free spin"
    elif "bank_account_bait" in reasons:
        category = "banking/account-like suspicious"
    elif "delivery_bait" in reasons:
        category = "delivery-like suspicious"
    elif "government_bait" in reasons:
        category = "government/tax/benefit suspicious"
    elif "prize_reward_ad" in reasons:
        category = "prize/reward promo"
    elif spam_score >= 3:
        category = "promotional spam"
    return spam_score, smish_score, bucket, ";".join(dict.fromkeys(reasons)), category


def candidate_reason(row: pd.Series, path: Path) -> str | None:
    source_label = text_value(row, "source_label", "original_label", "label").lower()
    normalized_label = text_value(row, "normalized_label", "label").lower()
    label_status = text_value(row, "label_status").lower()
    current_reason = text_value(row, "candidate_reason")
    if current_reason:
        return current_reason
    if source_label == "spam" or normalized_label == "spam":
        return "original_spam_label"
    if label_status == "needs_smishing_relabel":
        return "needs_smishing_relabel"
    if text_value(row, "scam_category").lower() == "spam":
        return "public_candidate_spam"
    return None


def load_exclusion_keys() -> set[str]:
    keys: set[str] = set()
    if FINAL_V3.exists():
        final = pd.read_csv(FINAL_V3, dtype=str, keep_default_na=False)
        for _, row in final.iterrows():
            msg = text_value(row, "message_raw", "message_clean")
            if msg:
                keys.add(normalize_text(msg))
    if CURRENT_PACKET.exists():
        current = pd.read_csv(CURRENT_PACKET, dtype=str, keep_default_na=False)
        # The balanced sampler may intentionally keep current rows, so do not exclude them here.
        _ = current
    return keys


def make_record(row: pd.Series, path: Path, final_keys: set[str]) -> dict[str, object] | None:
    reason = candidate_reason(row, path)
    if not reason:
        return None
    if text_value(row, "is_synthetic").lower() in {"true", "1", "yes"}:
        return None
    raw = text_value(row, "message_raw", "candidate_raw_text", "message_text")
    clean = text_value(row, "message_clean", "candidate_clean_text", "message_text")
    if not raw_complete(raw, row):
        return None
    key = normalize_text(raw)
    if key in final_keys:
        return None
    source_name = text_value(row, "source_name")
    dataset_name = text_value(row, "dataset_name")
    if not source_name and not dataset_name:
        return None
    source_label = text_value(row, "source_label", "original_label", "label")
    normalized_label = text_value(row, "normalized_label", "label")
    spam_score, smish_score, bucket, bucket_reason, category = signals(raw, source_label, normalized_label)
    if bucket == "reject_candidate":
        return None
    rel = path.relative_to(ROOT).as_posix()
    stable = hashlib.sha1(f"{rel}|{text_value(row,'unified_id','id')}|{text_value(row,'source_row_id','id')}|{key}".encode("utf-8")).hexdigest()[:12]
    priority = spam_score * 10 - smish_score * 4
    if source_name == "UCI SMS Spam Collection":
        priority += 100
    if source_name == "Mishra & Soni":
        priority += 40
    if bucket == "likely_spam_not_smishing":
        priority += 60
    return {
        "candidate_id": f"convspam_{stable}",
        "source_name": source_name,
        "dataset_name": dataset_name,
        "source_group": text_value(row, "source_group", "source_type"),
        "source_row_id": text_value(row, "source_row_id", "id"),
        "source_file": rel,
        "message_raw": raw,
        "message_clean": clean,
        "source_label": source_label,
        "normalized_label": normalized_label,
        "label_status": text_value(row, "label_status"),
        "review_status": text_value(row, "review_status"),
        "candidate_reason": reason,
        "spam_signal_score": spam_score,
        "smishing_signal_score": smish_score,
        "likely_review_bucket": bucket,
        "bucket_reason": bucket_reason,
        "raw_quality_status": "pass_raw_complete",
        "contains_url": boolish(text_value(row, "contains_url")) or bool(URL_RE.search(raw)),
        "contains_phone": boolish(text_value(row, "contains_phone")) or bool(PHONE_RE.search(raw)),
        "contains_otp": boolish(text_value(row, "contains_otp")) or bool(re.search(r"\b(otp|pin|passcode|verification code)\b", raw, re.I)),
        "contains_amount": boolish(text_value(row, "contains_amount")) or bool(AMOUNT_RE.search(raw)),
        "suggested_category": category,
        "scam_category": text_value(row, "scam_category"),
        "notes": text_value(row, "notes", "reviewer_notes", "label_mapping_notes"),
        "selection_priority_score": priority,
        "duplicate_key": key,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    final_keys = load_exclusion_keys()
    records = []
    inspected = []
    considered = 0
    for path in SOURCES:
        if not path.exists():
            continue
        inspected.append(path.relative_to(ROOT).as_posix())
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
        for _, row in df.iterrows():
            if not candidate_reason(row, path):
                continue
            considered += 1
            rec = make_record(row, path, final_keys)
            if rec:
                records.append(rec)
    pool = pd.DataFrame(records)
    if len(pool):
        pool = pool.sort_values("selection_priority_score", ascending=False, kind="mergesort").drop_duplicates("duplicate_key", keep="first")
    for col in OUT_COLS:
        if col not in pool.columns:
            pool[col] = ""
    pool[OUT_COLS].to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    report = [
        "# Conversational Spam Candidate Pool Report",
        "",
        f"- source files inspected: {len(inspected)}",
        *[f"- {x}" for x in inspected],
        f"- candidate rows considered: {considered}",
        f"- raw-complete conversational candidates found: {len(pool)}",
        f"- likely_spam_not_smishing candidates found: {int(pool['likely_review_bucket'].eq('likely_spam_not_smishing').sum()) if len(pool) else 0}",
        f"- likely_smishing candidates found: {int(pool['likely_review_bucket'].eq('likely_smishing').sum()) if len(pool) else 0}",
        "",
        "UCI / SMS Spam Collection rows with original spam labels were prioritized because they are useful public SMS spam examples for distinguishing spam_not_smishing from smishing.",
    ]
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
    print("Conversational/general spam candidate pool built")
    print(f"conversational spam candidates found: {len(pool)}")
    print(f"likely_spam_not_smishing candidates found: {int(pool['likely_review_bucket'].eq('likely_spam_not_smishing').sum()) if len(pool) else 0}")
    print(f"likely_smishing candidates found: {int(pool['likely_review_bucket'].eq('likely_smishing').sum()) if len(pool) else 0}")
    print("source breakdown:")
    if len(pool):
        print(pool["source_name"].value_counts().to_string())
    print(f"CSV path: {OUT_PATH.relative_to(ROOT).as_posix()}")
    print(f"report path: {REPORT_PATH.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
