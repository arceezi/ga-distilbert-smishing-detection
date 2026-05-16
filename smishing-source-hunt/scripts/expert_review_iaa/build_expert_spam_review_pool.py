#!/usr/bin/env python
"""Build a traceable public spam/suspicious SMS pool for expert IAA review."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "expert_review_iaa"
POOL_PATH = OUT_DIR / "expert_spam_review_source_pool.csv"
ARCHIVE_PATH = OUT_DIR / "expert_spam_review_excluded_archive.csv"
FINAL_V3_PATH = ROOT / "data" / "final_dataset_build" / "final" / "dataset_v3_public_manual_research_synthetic_ham_balanced.csv"

SOURCE_FILES = [
    ROOT / "data" / "organized" / "combined_public_thesis_sources_uniform.csv",
    ROOT / "data" / "organized" / "combined_public_thesis_sources_deduped_representatives.csv",
    ROOT / "data" / "organized" / "text_verified" / "combined_public_thesis_sources_text_verified.csv",
    ROOT / "data" / "organized" / "text_verified" / "combined_public_thesis_sources_deduped_representatives_text_verified.csv",
    ROOT / "data" / "organized" / "raw_recovery" / "combined_public_thesis_sources_deduped_raw_required.csv",
    ROOT / "data" / "organized" / "raw_quality" / "strict_raw_removed_archive.csv",
    ROOT / "data" / "organized" / "content_quality" / "content_removed_archive.csv",
    ROOT / "data" / "organized" / "campaign_family_quality" / "strong_campaign_family_excluded_archive.csv",
    ROOT / "data" / "raw" / "collected_smishing_candidates.csv",
    ROOT / "data" / "organized" / "raw_recovery" / "collected_smishing_candidates_raw_classified.csv",
]

POOL_COLUMNS = [
    "review_candidate_id",
    "original_unified_id",
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
    "raw_text_available",
    "raw_text_status",
    "data_origin",
    "is_synthetic",
    "source_priority",
    "candidate_reason",
    "contains_url",
    "contains_phone",
    "contains_otp",
    "contains_amount",
    "contains_account_hint",
    "scam_category",
    "service_category",
    "notes",
    "expert_review_normalized_key",
    "duplicate_cluster_id",
    "duplicate_cluster_size",
    "is_duplicate_representative",
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


def normalize_review_text(text: str) -> str:
    text = str(text).lower()
    text = re.sub(r"https?://\S+|www\.\S+|(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/\S*)?", " <URL> ", text)
    text = re.sub(r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", " <EMAIL> ", text)
    text = re.sub(r"(?:\+?\d[\d\s().-]{6,}\d)", " <PHONE> ", text)
    text = re.sub(r"\b(?:otp|pin|code|passcode|verification)\s*[:#-]?\s*[a-z0-9-]{4,10}\b", " <OTP> ", text)
    text = re.sub(r"\b[a-z]{1,4}\d{4,10}\b|\b\d{4,8}[a-z]{1,4}\b", " <OTP> ", text)
    text = re.sub(r"\b\d{9,}\b", " <REF_NUM> ", text)
    text = re.sub(r"(?:[$£€]|rs\.?|php|usd|gbp|eur)\s*\d+(?:[,.]\d+)*|\d+(?:[,.]\d+)*(?:\s?(?:php|usd|gbp|eur|rs|p))", " <AMOUNT> ", text)
    text = re.sub(r"[^a-z0-9<>]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def feature_contains(text: str, kind: str) -> bool:
    low = str(text).lower()
    if kind == "url":
        return bool(re.search(r"https?://|www\.|(?:[a-z0-9-]+\.)+(?:com|net|org|co|uk|ph|info|biz)\b|<url>", low))
    if kind == "phone":
        return bool(re.search(r"<phone|phone_number|\+?\d[\d\s().-]{6,}\d", low))
    if kind == "otp":
        return bool(re.search(r"\b(otp|pin|passcode|verification code|security code)\b|<otp>", low))
    if kind == "amount":
        return bool(re.search(r"[$£€]|rs\.?|php|usd|gbp|eur|\b\d+(?:[,.]\d+)*p\b|<amount>", low))
    if kind == "account":
        return bool(re.search(r"\b(account|acct|bank|card|wallet|login|password|verify|suspend|locked|blocked)\b", low))
    return False


def infer_category(text: str, scam_category: str = "", service_category: str = "") -> str:
    joined = f"{scam_category} {service_category} {text}".lower()
    checks = [
        ("banking/account-like suspicious", r"\bbank|account|acct|card|wallet|paypal|cash app|venmo|zelle|login|verify|suspend|locked"),
        ("delivery-like suspicious", r"\bdelivery|parcel|package|shipment|courier|usps|ups|fedex|dhl"),
        ("gambling/casino/free spin", r"\bcasino|bet|gambl|slot|free spin|jackpot|my11circle"),
        ("reward/prize", r"\bprize|winner|won|reward|bonus|claim|gift|voucher"),
        ("job/investment offer", r"\bjob|hiring|income|earn|investment|crypto|forex|profit"),
        ("adult/chat promo", r"\badult|xxx|sex|chat|dating|hot singles|porn"),
        ("telecom promo", r"\bmobile|ringtone|tone|txt|sms|call rate|airtime|telecom"),
        ("promotional spam", r"\bfree|offer|discount|sale|promo|unsubscribe|stop to opt"),
    ]
    for label, pattern in checks:
        if re.search(pattern, joined):
            return label
    return "generic scam-like or unclear"


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
        ]
    )
    path_blob = str(source_path).lower()

    if "manual_ham" in path_blob or "synthetic" in reason_blob:
        return None
    if "needs_smishing_relabel" in {label_status, review_status}:
        return ("needs_smishing_relabel", 2)
    if "conflict_needs_review" in {label_status, review_status}:
        return ("conflict_needs_review", 4)
    if source_label == "spam":
        return ("original_spam_label", 1)
    if normalized_label == "spam":
        return ("original_spam_label", 1)
    if source_label in {"unsure", "unknown", "candidate_spam"}:
        return ("public_candidate_spam", 6)
    if "weak_or_no_smishing_signal" in reason_blob or "manual_review" == suggested_action:
        return ("weak_signal_suspicious", 5)
    if "not smishing" in reason_blob or "non_smishing" in reason_blob:
        return ("possible_spam_not_smishing", 3)
    if "removed_archive" in path_blob or "excluded_archive" in path_blob:
        if any(token in reason_blob for token in ["spam", "suspicious", "review", "campaign", "weak"]):
            return ("excluded_from_smishing_review", 5)
    if "collected_smishing_candidates" in path_blob and text_value(row, "scam_category").lower() == "spam":
        return ("public_candidate_spam", 6)
    return None


def load_final_reference() -> tuple[set[str], set[str], set[str]]:
    if not FINAL_V3_PATH.exists():
        return set(), set(), set()
    final = pd.read_csv(FINAL_V3_PATH, dtype=str, keep_default_na=False)
    unified_ids = set(final.get("unified_id", pd.Series(dtype=str)).astype(str))
    source_rows = set(
        (
            final.get("source_name", pd.Series("", index=final.index)).astype(str)
            + "||"
            + final.get("source_row_id", pd.Series("", index=final.index)).astype(str)
        )
    )
    keys = set()
    for _, row in final.iterrows():
        message = text_value(row, "message_raw", "message_clean")
        if message:
            keys.add(normalize_review_text(message))
    return unified_ids, source_rows, keys


def source_trace(row: pd.Series) -> str:
    return text_value(row, "source_name") + "||" + text_value(row, "source_row_id", "id")


def build_record(row: pd.Series, source_path: Path, reason: str, priority: int, final_keys: set[str]) -> dict[str, object] | None:
    raw = text_value(row, "message_raw", "candidate_raw_text", "message_text")
    clean = text_value(row, "message_clean", "candidate_clean_text", "message_text")
    message = raw or clean
    if not message:
        return None

    label_status = text_value(row, "label_status")
    review_status = text_value(row, "review_status")
    normalized_label = text_value(row, "normalized_label", "label")
    key = normalize_review_text(message)
    if not key:
        return None

    # Do not bring already accepted final training rows into this review packet.
    if key in final_keys and "review" not in f"{label_status} {review_status}".lower() and normalized_label.lower() != "spam":
        return None

    source_rel = source_path.relative_to(ROOT).as_posix()
    raw_available = text_value(row, "raw_text_available", "candidate_raw_text_available")
    if raw_available == "":
        raw_available = str(bool(raw))

    text_for_features = " ".join([raw, clean])
    is_synth = text_value(row, "is_synthetic").lower()
    if is_synth in {"true", "1", "yes"}:
        return None

    original_id = text_value(row, "unified_id", "id")
    stable = hashlib.sha1(f"{source_rel}|{original_id}|{source_trace(row)}|{key}".encode("utf-8")).hexdigest()[:12]
    return {
        "review_candidate_id": f"erc_{stable}",
        "original_unified_id": original_id,
        "source_name": text_value(row, "source_name"),
        "dataset_name": text_value(row, "dataset_name"),
        "source_group": text_value(row, "source_group", "source_type"),
        "source_row_id": text_value(row, "source_row_id", "id"),
        "source_file": source_rel,
        "message_raw": raw,
        "message_clean": clean,
        "source_label": text_value(row, "source_label", "original_label", "label"),
        "normalized_label": normalized_label,
        "label_status": label_status,
        "review_status": review_status,
        "raw_text_available": raw_available,
        "raw_text_status": text_value(row, "raw_text_status", "candidate_raw_text_status", "redaction_status"),
        "data_origin": text_value(row, "data_origin") or "public_source",
        "is_synthetic": False,
        "source_priority": priority,
        "candidate_reason": reason,
        "contains_url": boolish(text_value(row, "contains_url")) or feature_contains(text_for_features, "url"),
        "contains_phone": boolish(text_value(row, "contains_phone")) or feature_contains(text_for_features, "phone"),
        "contains_otp": boolish(text_value(row, "contains_otp")) or feature_contains(text_for_features, "otp"),
        "contains_amount": boolish(text_value(row, "contains_amount")) or feature_contains(text_for_features, "amount"),
        "contains_account_hint": boolish(text_value(row, "contains_account_hint")) or feature_contains(text_for_features, "account"),
        "scam_category": text_value(row, "scam_category"),
        "service_category": text_value(row, "service_category"),
        "notes": text_value(row, "notes", "reviewer_notes", "raw_quality_notes", "content_quality_flags", "content_filter_reason", "campaign_family_filter_reason"),
        "expert_review_normalized_key": key,
    }


def representative_sort_frame(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["_raw_rank"] = df["raw_text_available"].astype(str).str.lower().isin(["true", "yes", "1", "available"]).astype(int)
    df["_trace_rank"] = (df["source_name"].astype(str).str.len() > 0).astype(int) + (df["source_row_id"].astype(str).str.len() > 0).astype(int)
    df["_reason_rank"] = df["candidate_reason"].map(
        {
            "original_spam_label": 6,
            "needs_smishing_relabel": 5,
            "possible_spam_not_smishing": 4,
            "weak_signal_suspicious": 3,
            "excluded_from_smishing_review": 2,
            "conflict_needs_review": 2,
            "public_candidate_spam": 1,
        }
    ).fillna(0)
    lengths = df["message_raw"].fillna("").astype(str).str.len()
    df["_sms_rank"] = lengths.between(20, 240).astype(int)
    df["_length_sort"] = (lengths - 120).abs()
    return df.sort_values(
        ["expert_review_normalized_key", "_raw_rank", "_trace_rank", "_reason_rank", "_sms_rank", "source_priority", "_length_sort"],
        ascending=[True, False, False, False, False, True, True],
        kind="mergesort",
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    final_unified_ids, final_source_rows, final_keys = load_final_reference()
    records: list[dict[str, object]] = []
    excluded: list[dict[str, object]] = []
    inspected: list[str] = []
    raw_candidates_found = 0

    for source_path in SOURCE_FILES:
        if not source_path.exists():
            continue
        inspected.append(source_path.relative_to(ROOT).as_posix())
        df = pd.read_csv(source_path, dtype=str, keep_default_na=False)
        for _, row in df.iterrows():
            reason_tuple = candidate_reason(row, source_path)
            if reason_tuple is None:
                continue
            raw_candidates_found += 1
            reason, priority = reason_tuple
            uid = text_value(row, "unified_id", "id")
            src_trace = source_trace(row)
            label_status = text_value(row, "label_status").lower()
            review_status = text_value(row, "review_status").lower()
            if (uid in final_unified_ids or src_trace in final_source_rows) and "review" not in f"{label_status} {review_status}" and reason not in {"original_spam_label", "needs_smishing_relabel", "conflict_needs_review"}:
                excluded.append({"exclusion_type": "already_in_final_v3", "source_file": source_path.relative_to(ROOT).as_posix(), "original_unified_id": uid})
                continue
            record = build_record(row, source_path, reason, priority, final_keys)
            if record is None:
                excluded.append({"exclusion_type": "invalid_or_synthetic_or_final", "source_file": source_path.relative_to(ROOT).as_posix(), "original_unified_id": uid})
                continue
            records.append(record)

    if not records:
        raise SystemExit("No expert review candidates found.")

    pool = pd.DataFrame(records).drop_duplicates("review_candidate_id")
    sorted_pool = representative_sort_frame(pool)
    cluster_info = sorted_pool.groupby("expert_review_normalized_key", sort=False).size().rename("duplicate_cluster_size")
    cluster_ids = {key: f"expdup_{i:06d}" for i, key in enumerate(cluster_info.index, start=1)}
    sorted_pool["duplicate_cluster_id"] = sorted_pool["expert_review_normalized_key"].map(cluster_ids)
    sorted_pool["duplicate_cluster_size"] = sorted_pool["expert_review_normalized_key"].map(cluster_info)
    sorted_pool["is_duplicate_representative"] = ~sorted_pool.duplicated("expert_review_normalized_key", keep="first")
    sorted_pool = sorted_pool.drop(columns=[c for c in sorted_pool.columns if c.startswith("_")])

    duplicate_archive = sorted_pool[~sorted_pool["is_duplicate_representative"]].copy()
    if excluded:
        excluded_df = pd.DataFrame(excluded)
        duplicate_archive = pd.concat([duplicate_archive, excluded_df], ignore_index=True, sort=False)

    for col in POOL_COLUMNS:
        if col not in sorted_pool.columns:
            sorted_pool[col] = ""
    sorted_pool[POOL_COLUMNS].to_csv(POOL_PATH, index=False, encoding="utf-8-sig")
    duplicate_archive.to_csv(ARCHIVE_PATH, index=False, encoding="utf-8-sig")

    valid = len(sorted_pool)
    duplicate_removed = int((~sorted_pool["is_duplicate_representative"]).sum())
    print("Expert spam review source pool built")
    print(f"source files inspected: {len(inspected)}")
    for item in inspected:
        print(f"- {item}")
    print(f"total candidates found: {raw_candidates_found}")
    print(f"valid candidates after filtering: {valid}")
    print(f"duplicates removed: {duplicate_removed}")
    print(f"representative candidates available: {int(sorted_pool['is_duplicate_representative'].sum())}")
    print(f"source pool: {POOL_PATH.relative_to(ROOT).as_posix()}")
    print(f"excluded archive: {ARCHIVE_PATH.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
