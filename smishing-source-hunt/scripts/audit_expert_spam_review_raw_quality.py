#!/usr/bin/env python
"""Audit the initial expert review packet for raw-complete SMS quality."""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "expert_review_iaa"
INPUT_PATH = OUT_DIR / "expert_spam_review_500.csv"
FLAGS_PATH = OUT_DIR / "expert_spam_review_raw_quality_flags.csv"
REPLACE_PATH = OUT_DIR / "expert_spam_review_rows_to_replace.csv"
KEPT_PATH = OUT_DIR / "expert_spam_review_rows_kept.csv"
REPORT_PATH = OUT_DIR / "expert_spam_review_raw_quality_report.md"

PLACEHOLDER_RE = re.compile(r"<\s*[A-Z0-9_ -]+\s*>")
URL_RE = re.compile(r"https?://\S+|www\.\S+|(?:[a-z0-9-]+\.)+[a-z]{2,}(?:/\S*)?", re.I)
PHONE_RE = re.compile(r"(?:\+?\d[\d\s().-]{6,}\d)")
AMOUNT_RE = re.compile(r"(?:[$£€]|rs\.?|php|usd|gbp|eur)\s*\d+(?:[,.]\d+)*|\d+(?:[,.]\d+)*(?:\s?(?:php|usd|gbp|eur|rs|p))", re.I)


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


def placeholder_types(text: str) -> str:
    return ";".join(sorted({m.group(0).strip() for m in PLACEHOLDER_RE.finditer(str(text))}))


def is_multi_message_cell(text: str) -> bool:
    raw = str(text).strip()
    if re.match(r"^\s*\[(['\"])", raw) and raw.endswith("]"):
        try:
            parsed = ast.literal_eval(raw)
            if isinstance(parsed, list) and len(parsed) > 1:
                return True
        except Exception:
            return True
    if raw.count("', '") >= 1 or raw.count('", "') >= 1:
        return True
    if len(re.findall(r"\bmessage[_ ]?(?:raw|clean|text)\b", raw, re.I)) > 1:
        return True
    return False


def artifact_like(text: str) -> bool:
    raw = str(text).strip()
    low = raw.lower()
    artifact_terms = [
        "screenshot",
        "ocr",
        "image may contain",
        "this message was",
        "reported by",
        "commentary",
        "conversation with scammer",
        "reply to scammer",
        "not a sms",
    ]
    if any(term in low for term in artifact_terms):
        return True
    if raw.count("|") >= 4 or raw.count("\t") >= 2:
        return True
    if re.search(r"\b(row|label|source|dataset)\s*[:=]", low) and len(raw) > 120:
        return True
    return False


def audit_row(row: pd.Series) -> dict[str, object]:
    raw = str(row.get("message_raw", "")).strip()
    flags: list[str] = []
    if not raw:
        flags.append("empty_raw")
    ph = placeholder_types(raw)
    if ph:
        flags.append("placeholder_raw")
    if "&lt;#&gt;" in raw.lower() or "&lt;" in raw.lower() or "&gt;" in raw.lower():
        flags.append("html_encoded_placeholder")
    if token_count(raw) < 3 or len(raw) < 12:
        flags.append("too_short")
    if len(raw) > 320:
        flags.append("too_long")
    if is_multi_message_cell(raw):
        flags.append("multi_message_cell")
    if artifact_like(raw):
        flags.append("not_sms_like_artifact")

    if "empty_raw" in flags:
        status = "fail_empty_raw"
    elif "placeholder_raw" in flags or "html_encoded_placeholder" in flags:
        status = "fail_placeholder_raw"
    elif "multi_message_cell" in flags:
        status = "fail_multi_message_cell"
    elif "too_short" in flags:
        status = "fail_too_short"
    elif "not_sms_like_artifact" in flags:
        status = "review_sms_likeness"
    elif "too_long" in flags:
        status = "review_too_long"
    else:
        status = "pass_raw_complete"

    return {
        "raw_quality_status": status,
        "raw_quality_flags": ";".join(flags),
        "raw_placeholder_detected": bool(ph or "html_encoded_placeholder" in flags),
        "raw_placeholder_types": ph,
        "raw_length": len(raw),
        "raw_token_count": token_count(raw),
        "multi_message_cell_detected": "multi_message_cell" in flags,
        "duplicate_key": normalize_text(raw),
    }


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(INPUT_PATH, dtype=str, keep_default_na=False)
    audited = pd.concat([df, df.apply(audit_row, axis=1, result_type="expand")], axis=1)

    dup_mask = audited["duplicate_key"].duplicated(keep="first") & audited["duplicate_key"].ne("")
    dup_first_mask = audited["duplicate_key"].duplicated(keep=False) & ~dup_mask & audited["duplicate_key"].ne("")
    audited["duplicate_status"] = "unique"
    audited.loc[dup_first_mask, "duplicate_status"] = "duplicate_representative_kept"
    audited.loc[dup_mask, "duplicate_status"] = "duplicate_needs_replacement"
    audited.loc[dup_mask, "raw_quality_status"] = "fail_duplicate"
    audited.loc[dup_mask, "raw_quality_flags"] = audited.loc[dup_mask, "raw_quality_flags"].where(
        audited.loc[dup_mask, "raw_quality_flags"].eq(""),
        audited.loc[dup_mask, "raw_quality_flags"] + ";",
    ) + "duplicate"

    fail_statuses = {
        "fail_placeholder_raw",
        "fail_empty_raw",
        "fail_too_short",
        "fail_multi_message_cell",
        "fail_duplicate",
        "review_sms_likeness",
    }
    # Long rows are not automatically replaced unless another quality failure is present.
    audited["suggested_action"] = audited["raw_quality_status"].apply(lambda x: "replace" if x in fail_statuses else "keep")
    audited["replacement_needed_reason"] = audited["raw_quality_flags"].where(audited["suggested_action"].eq("replace"), "")

    kept = audited[audited["suggested_action"].eq("keep")].copy()
    replace = audited[audited["suggested_action"].eq("replace")].copy()

    audited.to_csv(FLAGS_PATH, index=False, encoding="utf-8-sig")
    kept.to_csv(KEPT_PATH, index=False, encoding="utf-8-sig")
    replace.to_csv(REPLACE_PATH, index=False, encoding="utf-8-sig")

    report = [
        "# Expert Spam Review Raw Quality Audit",
        "",
        f"- initial rows: {len(audited)}",
        f"- rows passed raw quality / kept: {len(kept)}",
        f"- rows needing replacement: {len(replace)}",
        f"- placeholder/anonymized rows found: {int(audited['raw_placeholder_detected'].astype(str).str.lower().eq('true').sum())}",
        f"- duplicate rows found: {int(audited['duplicate_status'].eq('duplicate_needs_replacement').sum())}",
        f"- long rows found (>320 chars): {int(audited['raw_length'].astype(int).gt(320).sum())}",
        f"- too-short rows found: {int(audited['raw_quality_flags'].str.contains('too_short', regex=False).sum())}",
        f"- multi-message cells found: {int(audited['multi_message_cell_detected'].astype(str).str.lower().eq('true').sum())}",
        "",
        "Rows marked `replace` are archived in `expert_spam_review_rows_to_replace.csv`; rows marked `keep` are preserved in `expert_spam_review_rows_kept.csv`.",
    ]
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")

    print("Expert packet raw-quality audit complete")
    print(f"initial packet rows: {len(audited)}")
    print(f"rows passed raw quality: {len(kept)}")
    print(f"rows needing replacement: {len(replace)}")
    print(f"placeholder/anonymized rows found: {int(audited['raw_placeholder_detected'].astype(str).str.lower().eq('true').sum())}")
    print(f"duplicate rows found: {int(audited['duplicate_status'].eq('duplicate_needs_replacement').sum())}")
    print(f"long rows found: {int(audited['raw_length'].astype(int).gt(320).sum())}")
    print(f"too-short rows found: {int(audited['raw_quality_flags'].str.contains('too_short', regex=False).sum())}")
    print(f"multi-message cells found: {int(audited['multi_message_cell_detected'].astype(str).str.lower().eq('true').sum())}")
    print(f"flags: {FLAGS_PATH.relative_to(ROOT).as_posix()}")
    print(f"rows to replace: {REPLACE_PATH.relative_to(ROOT).as_posix()}")
    print(f"rows kept: {KEPT_PATH.relative_to(ROOT).as_posix()}")
    print(f"report: {REPORT_PATH.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
