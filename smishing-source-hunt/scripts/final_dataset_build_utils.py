"""Shared helpers for the final manual/synthetic ham dataset build."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
FINAL_BUILD_DIR = ROOT / "data" / "final_dataset_build"
INTERIM_DIR = FINAL_BUILD_DIR / "interim"
FINAL_DIR = FINAL_BUILD_DIR / "final"
REPORTS_DIR = FINAL_BUILD_DIR / "reports"
ARCHIVES_DIR = FINAL_BUILD_DIR / "archives"

PUBLIC_DATASET = ROOT / "data" / "organized" / "campaign_family_quality" / "combined_public_thesis_sources_campaign_family_filtered.csv"
MANUAL_CLEANED = ROOT / "data" / "manual_ham_drive" / "final" / "approved_manual_ham_cleaned.csv"

UNIFIED_COLUMNS = [
    "unified_id",
    "source_name",
    "dataset_name",
    "source_group",
    "source_row_id",
    "message_raw",
    "message_clean",
    "source_label",
    "normalized_label",
    "label_status",
    "review_status",
    "raw_text_available",
    "raw_text_status",
    "cleaning_status",
    "raw_lookup_status",
    "raw_lookup_notes",
    "contains_url",
    "contains_email",
    "contains_phone",
    "contains_otp",
    "contains_amount",
    "contains_account_hint",
    "service_category",
    "institution_type",
    "source_file",
    "reviewer_notes",
    "data_origin",
    "is_synthetic",
    "synthetic_template_id",
    "template_basis",
    "research_source_id",
    "synthetic_template_family_id",
    "generation_method",
    "notes",
]

FINAL_COLUMNS = [
    "final_dataset_version",
    "final_row_id",
    "final_split_eligible",
    "final_dataset_role",
    "data_origin",
    "is_synthetic",
    "source_name",
    "dataset_name",
    "source_group",
    "normalized_label",
    "message_raw",
    "message_clean",
    "service_category",
    "scam_category",
    "label_status",
    "review_status",
    "notes",
    "unified_id",
    "source_row_id",
    "source_label",
    "raw_text_available",
    "raw_text_status",
    "cleaning_status",
    "raw_lookup_status",
    "raw_lookup_notes",
    "contains_url",
    "contains_email",
    "contains_phone",
    "contains_otp",
    "contains_amount",
    "contains_account_hint",
    "institution_type",
    "source_file",
    "reviewer_notes",
    "synthetic_template_id",
    "template_basis",
    "research_source_id",
    "synthetic_template_family_id",
    "generation_method",
]


URL_RE = re.compile(r"https?://\S+|www\.\S+|(?<!@)\b[a-z0-9][a-z0-9.-]*\.(?:com|net|org|ph|gov|edu|co|io|app)\S*", re.I)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", re.I)
PHONE_RE = re.compile(r"\b(?:\+?63|0)\s?9\d{2}[\s.-]?\d{3}[\s.-]?\d{4}\b")
AMOUNT_RE = re.compile(r"\b(?:PHP|Php|php|P|₱)\s?[\d,]+(?:\.\d{1,2})?\b|\b\d+(?:\.\d+)?\s?(?:GigaPoints|points|pts)\b", re.I)
DATE_TIME_RE = re.compile(
    r"\b(?:today|tomorrow|yesterday|"
    r"\d{1,2}[-/ ](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*(?:[-/ ]\d{2,4})?|"
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*[-/ ]\d{1,2}(?:[-/ ]\d{2,4})?|"
    r"\d{1,2}:\d{2}(?:\s?[AP]M)?)\b",
    re.I,
)
OTP_CONTEXT_RE = re.compile(r"\b(?:otp|one[- ]time|verification code|code is|security code|use code|passcode)\b", re.I)
LONG_NUM_RE = re.compile(r"\b\d{7,14}\b")
OTP_NUM_RE = re.compile(r"\b\d{4,6}\b")
MASKED_RE = re.compile(r"\b(?:X{2,}|\*{2,})\d{2,6}\b|\b(?:ending|acct ending|account ending|card ending)\s+(?:in\s+)?\d{2,6}\b", re.I)
REF_CONTEXT_RE = re.compile(r"\b(?:ref|reference|txn|transaction|trace|receipt|account|acct|card|case|ticket|order)\b", re.I)
PUNCT_RE = re.compile(r"[^\w<>]+", re.UNICODE)


def ensure_dirs() -> None:
    for path in [INTERIM_DIR, FINAL_DIR, REPORTS_DIR, ARCHIVES_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def bool_text(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def normalize_for_overlap(text: object) -> str:
    value = str(text or "").lower()
    value = EMAIL_RE.sub("<EMAIL>", value)
    value = URL_RE.sub("<URL>", value)
    value = PHONE_RE.sub("<PHONE>", value)
    value = AMOUNT_RE.sub("<AMOUNT>", value)
    value = MASKED_RE.sub("<REF_NUM>", value)
    value = LONG_NUM_RE.sub("<REF_NUM>", value)
    if OTP_CONTEXT_RE.search(value):
        value = OTP_NUM_RE.sub("<OTP>", value)
    else:
        value = OTP_NUM_RE.sub("<REF_NUM>", value)
    value = PUNCT_RE.sub(" ", value)
    return re.sub(r"\s+", " ", value).strip()


def clean_synthetic_text(text: str) -> str:
    value = str(text or "")
    value = EMAIL_RE.sub("<EMAIL>", value)
    value = URL_RE.sub("<URL>", value)
    value = PHONE_RE.sub("<PHONE>", value)
    value = AMOUNT_RE.sub("<AMOUNT>", value)
    value = DATE_TIME_RE.sub("<DATE_TIME>", value)
    value = MASKED_RE.sub("<REF_NUM>", value)
    value = LONG_NUM_RE.sub("<REF_NUM>", value)
    if OTP_CONTEXT_RE.search(value):
        value = OTP_NUM_RE.sub("<OTP>", value)
    return re.sub(r"\s+", " ", value).strip()


def has_placeholder(text: str) -> bool:
    return bool(re.search(r"<[A-Z_]+>", str(text or "")))


def detect_flags(text: str) -> dict[str, bool]:
    value = str(text or "")
    return {
        "contains_url": bool(URL_RE.search(value) or "<URL>" in value),
        "contains_email": bool(EMAIL_RE.search(value) or "<EMAIL>" in value),
        "contains_phone": bool(PHONE_RE.search(value) or "<PHONE>" in value),
        "contains_otp": bool(OTP_CONTEXT_RE.search(value) or "<OTP>" in value),
        "contains_amount": bool(AMOUNT_RE.search(value) or "<AMOUNT>" in value),
        "contains_account_hint": bool(MASKED_RE.search(value) or REF_CONTEXT_RE.search(value) or "<REF_NUM>" in value or "<ACCT>" in value),
    }


def to_json_list(values: list[str]) -> str:
    return json.dumps(sorted(set(v for v in values if v)), ensure_ascii=True)


def public_to_unified(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "data_origin" not in out.columns:
        out["data_origin"] = "public_real"
    if "is_synthetic" not in out.columns:
        out["is_synthetic"] = False
    if "synthetic_template_id" not in out.columns:
        out["synthetic_template_id"] = ""
    if "generation_method" not in out.columns:
        out["generation_method"] = "public_source"
    if "source_file" not in out.columns:
        out["source_file"] = str(PUBLIC_DATASET.relative_to(ROOT))
    if "reviewer_notes" not in out.columns:
        out["reviewer_notes"] = ""
    if "service_category" not in out.columns:
        out["service_category"] = ""
    if "institution_type" not in out.columns:
        out["institution_type"] = ""
    return out


def final_project(df: pd.DataFrame, version: str) -> pd.DataFrame:
    out = df.copy()
    out["final_dataset_version"] = version
    out["final_split_eligible"] = True
    out["final_dataset_role"] = "main_binary_classification"
    out["scam_category"] = out.get("scam_category", "")
    out.insert(1, "final_row_id", [f"{version}_row_{idx:06d}" for idx in range(1, len(out) + 1)])
    for col in FINAL_COLUMNS:
        if col not in out.columns:
            out[col] = ""
    return out[FINAL_COLUMNS]
