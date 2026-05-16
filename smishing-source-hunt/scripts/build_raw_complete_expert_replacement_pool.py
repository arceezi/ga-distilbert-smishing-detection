#!/usr/bin/env python
"""Build raw-complete replacement candidates for expert spam review repair."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "expert_review_iaa"
OUTPUT_PATH = OUT_DIR / "raw_complete_expert_replacement_pool.csv"
KEPT_PATH = OUT_DIR / "expert_spam_review_rows_kept.csv"
INITIAL_PATH = OUT_DIR / "expert_spam_review_500.csv"
FINAL_V3_PATH = ROOT / "data" / "final_dataset_build" / "final" / "dataset_v3_public_manual_research_synthetic_ham_balanced.csv"

SOURCE_FILES = [
    ROOT / "data" / "organized" / "combined_public_thesis_sources_uniform.csv",
    ROOT / "data" / "organized" / "combined_public_thesis_sources_deduped_representatives.csv",
    ROOT / "data" / "organized" / "text_verified" / "combined_public_thesis_sources_text_verified.csv",
    ROOT / "data" / "organized" / "text_verified" / "combined_public_thesis_sources_deduped_representatives_text_verified.csv",
    ROOT / "data" / "organized" / "raw_quality" / "strict_raw_removed_archive.csv",
    ROOT / "data" / "organized" / "content_quality" / "content_removed_archive.csv",
    ROOT / "data" / "organized" / "campaign_family_quality" / "strong_campaign_family_excluded_archive.csv",
    ROOT / "data" / "expert_review_iaa" / "expert_spam_review_source_pool.csv",
    ROOT / "data" / "organized" / "raw_recovery" / "collected_smishing_candidates_raw_classified.csv",
    ROOT / "data" / "raw" / "collected_smishing_candidates.csv",
]

PLACEHOLDER_RE = re.compile(r"<\s*[A-Z0-9_ -]+\s*>")
URL_RE = re.compile(r"https?://\S+|www\.\S+|(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/\S*)?", re.I)
PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{6,}\d)")
AMOUNT_RE = re.compile(r"(?:[$£€]|rs\.?|php|usd|gbp|eur)\s*\d+(?:[,.]\d+)*|\d+(?:[,.]\d+)*(?:\s?(?:php|usd|gbp|eur|rs|p))", re.I)

OUTPUT_COLUMNS = [
    "replacement_candidate_id",
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
    "raw_quality_status",
    "contains_url",
    "contains_phone",
    "contains_otp",
    "contains_amount",
    "suggested_category",
    "scam_category",
    "notes",
    "replacement_priority_score",
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


def token_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", str(text)))


def has_placeholder(text: str) -> bool:
    raw = str(text)
    return bool(PLACEHOLDER_RE.search(raw) or "&lt;" in raw.lower() or "&gt;" in raw.lower())


def multi_message_cell(text: str) -> bool:
    raw = str(text).strip()
    return bool(
        (raw.startswith("[") and raw.endswith("]") and (raw.count("',") or raw.count('",')))
        or raw.count("', '") >= 1
        or raw.count('", "') >= 1
    )


def artifact_like(text: str) -> bool:
    raw = str(text).strip()
    low = raw.lower()
    if any(term in low for term in ["screenshot", "ocr", "image may contain", "reported by", "commentary", "reply to scammer"]):
        return True
    if raw.count("|") >= 4 or raw.count("\t") >= 2:
        return True
    if re.search(r"\b(row|label|source|dataset)\s*[:=]", low) and len(raw) > 120:
        return True
    return False


def english_like(text: str) -> bool:
    raw = str(text)
    if not raw:
        return False
    ascii_letters = len(re.findall(r"[A-Za-z]", raw))
    letters = len(re.findall(r"[^\W\d_]", raw, re.UNICODE))
    if letters == 0:
        return False
    return ascii_letters / max(letters, 1) >= 0.85


def raw_quality_status(row: pd.Series, raw: str) -> str:
    raw_status = text_value(row, "raw_text_status", "candidate_raw_text_status", "redaction_status").lower()
    raw_available = text_value(row, "raw_text_available", "candidate_raw_text_available")
    if not raw.strip():
        return "fail_empty_raw"
    if raw_available and raw_available.lower() in {"false", "0", "no", "unavailable"}:
        return "fail_raw_unavailable"
    if raw_status in {"already_redacted", "redacted", "placeholder_only", "missing"}:
        return "fail_redacted_raw"
    if has_placeholder(raw):
        return "fail_placeholder_raw"
    if token_count(raw) < 3 or len(raw.strip()) < 12:
        return "fail_too_short"
    if multi_message_cell(raw):
        return "fail_multi_message_cell"
    if artifact_like(raw):
        return "fail_artifact"
    if not english_like(raw):
        return "fail_non_english"
    if len(raw) > 320:
        return "review_too_long"
    return "pass_raw_complete"


def candidate_reason(row: pd.Series, source_path: Path) -> tuple[str, int] | None:
    source_label = text_value(row, "source_label", "original_label", "label").lower()
    normalized_label = text_value(row, "normalized_label", "label").lower()
    label_status = text_value(row, "label_status").lower()
    review_status = text_value(row, "review_status").lower()
    suggested_action = text_value(row, "suggested_action").lower()
    reason_blob = " ".join(
        text_value(row, c).lower()
        for c in [
            "notes",
            "reviewer_notes",
            "raw_quality_notes",
            "content_quality_flags",
            "content_filter_reason",
            "campaign_family_filter_reason",
            "exclusion_reason",
            "non_smishing_reason",
            "label_mapping_notes",
            "scam_category",
            "candidate_reason",
        ]
    )
    path_blob = str(source_path).lower()
    if text_value(row, "is_synthetic").lower() in {"true", "1", "yes"}:
        return None
    if "synthetic" in reason_blob or "manual_ham" in path_blob:
        return None
    if "needs_smishing_relabel" in {label_status, review_status}:
        return ("needs_smishing_relabel", 100)
    if "conflict_needs_review" in {label_status, review_status}:
        return ("conflict_needs_review", 85)
    if source_label == "spam" or normalized_label == "spam":
        return ("original_spam_label", 95)
    if text_value(row, "candidate_reason") in {
        "possible_spam_not_smishing",
        "weak_signal_suspicious",
        "conflict_needs_review",
        "excluded_from_smishing_review",
        "public_candidate_spam",
    }:
        reason = text_value(row, "candidate_reason")
        score = {
            "possible_spam_not_smishing": 80,
            "weak_signal_suspicious": 75,
            "conflict_needs_review": 85,
            "excluded_from_smishing_review": 70,
            "public_candidate_spam": 65,
        }[reason]
        return reason, score
    if "weak_or_no_smishing_signal" in reason_blob or suggested_action == "manual_review":
        return ("weak_signal_suspicious", 75)
    if "not smishing" in reason_blob or "non_smishing" in reason_blob:
        return ("possible_spam_not_smishing", 80)
    if "removed_archive" in path_blob or "excluded_archive" in path_blob:
        if any(token in reason_blob for token in ["spam", "suspicious", "review", "campaign", "weak"]):
            return ("excluded_from_smishing_review", 70)
    if "collected_smishing_candidates" in path_blob and text_value(row, "scam_category").lower() == "spam":
        return ("public_candidate_spam", 65)
    return None


def features(text: str, existing: str, kind: str) -> bool:
    if boolish(existing):
        return True
    low = str(text).lower()
    if kind == "url":
        return bool(URL_RE.search(low))
    if kind == "phone":
        return bool(PHONE_RE.search(low))
    if kind == "otp":
        return bool(re.search(r"\b(otp|pin|passcode|verification code|security code)\b", low))
    if kind == "amount":
        return bool(AMOUNT_RE.search(low))
    return False


def suggested_category(text: str, scam_category: str = "") -> str:
    joined = f"{scam_category} {text}".lower()
    checks = [
        ("banking/account-like suspicious", r"\bbank|account|acct|card|wallet|paypal|login|verify|suspend|locked"),
        ("delivery-like suspicious", r"\bdelivery|parcel|package|shipment|courier|usps|ups|fedex|dhl"),
        ("gambling/casino/free spin", r"\bcasino|bet|gambl|slot|free spin|jackpot|my11circle"),
        ("reward/prize", r"\bprize|winner|won|reward|bonus|claim|gift|voucher"),
        ("job/business funding offer", r"\bjob|hiring|business|funding|grant|loan"),
        ("crypto/investment offer", r"\binvestment|crypto|bitcoin|forex|profit|trading"),
        ("adult/chat promo", r"\badult|xxx|sex|chat|dating|porn"),
        ("telecom/ringtone/subscription spam", r"\bmobile|ringtone|tone|txt|sms|subscription|stop to opt|unsubscribe"),
        ("promotional spam", r"\bfree|offer|discount|sale|promo"),
    ]
    for label, pattern in checks:
        if re.search(pattern, joined):
            return label
    return scam_category or "unclear suspicious message"


def load_exclusion_keys() -> tuple[set[str], set[str]]:
    final_keys: set[str] = set()
    final_synth_ham_keys: set[str] = set()
    if FINAL_V3_PATH.exists():
        final = pd.read_csv(FINAL_V3_PATH, dtype=str, keep_default_na=False)
        for _, row in final.iterrows():
            msg = text_value(row, "message_raw", "message_clean")
            key = normalize_text(msg)
            if key:
                final_keys.add(key)
                if text_value(row, "is_synthetic").lower() in {"true", "1", "yes"} and text_value(row, "normalized_label").lower() == "ham":
                    final_synth_ham_keys.add(key)
    kept_keys: set[str] = set()
    if KEPT_PATH.exists():
        kept = pd.read_csv(KEPT_PATH, dtype=str, keep_default_na=False)
    elif INITIAL_PATH.exists():
        kept = pd.read_csv(INITIAL_PATH, dtype=str, keep_default_na=False)
    else:
        kept = pd.DataFrame()
    if not kept.empty:
        kept_keys = set(kept.get("message_raw", pd.Series(dtype=str)).map(normalize_text))
    return final_keys | final_synth_ham_keys, kept_keys


def make_record(row: pd.Series, source_path: Path, reason: str, base_score: int) -> dict[str, object] | None:
    raw = text_value(row, "message_raw", "candidate_raw_text", "message_text")
    clean = text_value(row, "message_clean", "candidate_clean_text", "message_text")
    status = raw_quality_status(row, raw)
    if status != "pass_raw_complete":
        return None
    if not text_value(row, "source_name") and not text_value(row, "dataset_name"):
        return None
    key = normalize_text(raw)
    if not key:
        return None
    rel = source_path.relative_to(ROOT).as_posix()
    stable = hashlib.sha1(f"{rel}|{text_value(row, 'unified_id', 'id')}|{text_value(row, 'source_row_id', 'id')}|{key}".encode("utf-8")).hexdigest()[:12]
    text = f"{raw} {clean}"
    score = base_score
    if boolish(text_value(row, "raw_text_available", "candidate_raw_text_available")):
        score += 10
    if len(raw) <= 240:
        score += 5
    if text_value(row, "source_name") and text_value(row, "source_row_id", "id"):
        score += 5
    return {
        "replacement_candidate_id": f"rawrep_{stable}",
        "source_name": text_value(row, "source_name"),
        "dataset_name": text_value(row, "dataset_name"),
        "source_group": text_value(row, "source_group", "source_type"),
        "source_row_id": text_value(row, "source_row_id", "id"),
        "source_file": rel,
        "message_raw": raw,
        "message_clean": clean,
        "source_label": text_value(row, "source_label", "original_label", "label"),
        "normalized_label": text_value(row, "normalized_label", "label"),
        "label_status": text_value(row, "label_status"),
        "review_status": text_value(row, "review_status"),
        "candidate_reason": reason,
        "raw_quality_status": status,
        "contains_url": features(text, text_value(row, "contains_url"), "url"),
        "contains_phone": features(text, text_value(row, "contains_phone"), "phone"),
        "contains_otp": features(text, text_value(row, "contains_otp"), "otp"),
        "contains_amount": features(text, text_value(row, "contains_amount"), "amount"),
        "suggested_category": suggested_category(text, text_value(row, "scam_category")),
        "scam_category": text_value(row, "scam_category"),
        "notes": text_value(row, "notes", "reviewer_notes", "content_filter_reason", "campaign_family_filter_reason", "raw_quality_notes"),
        "replacement_priority_score": score,
        "duplicate_key": key,
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    final_keys, kept_keys = load_exclusion_keys()
    records: list[dict[str, object]] = []
    inspected: list[str] = []
    raw_candidates = 0

    for source_path in SOURCE_FILES:
        if not source_path.exists():
            continue
        inspected.append(source_path.relative_to(ROOT).as_posix())
        df = pd.read_csv(source_path, dtype=str, keep_default_na=False)
        for _, row in df.iterrows():
            reason_tuple = candidate_reason(row, source_path)
            if reason_tuple is None:
                continue
            raw_candidates += 1
            reason, score = reason_tuple
            rec = make_record(row, source_path, reason, score)
            if rec is None:
                continue
            if rec["duplicate_key"] in kept_keys or rec["duplicate_key"] in final_keys:
                continue
            records.append(rec)

    if records:
        pool = pd.DataFrame(records)
        pool = pool.sort_values(["replacement_priority_score", "candidate_reason"], ascending=[False, True], kind="mergesort")
        pool = pool.drop_duplicates("duplicate_key", keep="first")
        pool = pool.drop_duplicates("replacement_candidate_id", keep="first")
    else:
        pool = pd.DataFrame(columns=OUTPUT_COLUMNS)
    for col in OUTPUT_COLUMNS:
        if col not in pool.columns:
            pool[col] = ""
    pool[OUTPUT_COLUMNS].to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print("Raw-complete replacement pool built")
    print(f"source files inspected: {len(inspected)}")
    for item in inspected:
        print(f"- {item}")
    print(f"candidate rows considered: {raw_candidates}")
    print(f"replacement pool size: {len(pool)}")
    print("candidate reason breakdown:")
    if len(pool):
        print(pool["candidate_reason"].value_counts().to_string())
    print(f"output: {OUTPUT_PATH.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
