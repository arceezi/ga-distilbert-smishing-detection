"""Audit smishing rows for obvious non-smishing content quality issues."""

from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "organized" / "raw_quality" / "combined_public_thesis_sources_deduped_strict_raw.csv"
OUT_DIR = ROOT / "data" / "organized" / "content_quality"
FLAGS_OUT = OUT_DIR / "smishing_content_quality_flags.csv"
NON_SMISHING_OUT = OUT_DIR / "obvious_non_smishing_review.csv"
REPORT = ROOT / "reports" / "smishing_content_quality_audit.md"

ADDED = [
    "content_quality_status",
    "content_quality_flags",
    "smishing_signal_score",
    "non_smishing_reason",
    "suggested_action",
]

URL_RE = re.compile(r"(?i)\b(?:https?://|www\.|bit\.ly|tinyurl|t\.co|[a-z0-9.-]+\.(?:com|net|org|ph|co|uk|io|biz|xyz|top|site|online|click|shop|app))\b")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
ACTION_RE = re.compile(r"(?i)\b(login|log in|verify|update|confirm|validate|click|visit|open|tap|call|reply|text|claim|pay|activate|reactivate|unlock|secure|cancel)\b")
ACCOUNT_RE = re.compile(r"(?i)\b(account|bank|wallet|payment|transaction|card|debit|credit|balance|fund|securities|broker|password|pin|otp|code)\b")
DELIVERY_RE = re.compile(r"(?i)\b(parcel|package|delivery|customs|address|warehouse|post office|usps|dhl|fedex)\b")
GOV_RE = re.compile(r"(?i)\b(tax|refund|benefit|fine|police|irs|hmrc|nhs|government|court|license|licence)\b")
URGENT_RE = re.compile(r"(?i)\b(urgent|immediately|blocked|suspended|restricted|locked|unauthorized|fraud|security|alert|warning|expire|limited|final notice)\b")
REWARD_RE = re.compile(r"(?i)\b(prize|won|winner|reward|bonus|gift|claim)\b")

ABUSIVE_REPLY_RE = re.compile(
    r"(?i)\b(fuck you scammer|stop texting(?: me)?|leave me alone|i know (?:this|it) is a scam|"
    r"i'?ll find you|coming for you|reported you|report (?:you|it) to the police|go away scammer|"
    r"nice try|wrong person|who is this|don'?t know you|scammer!|you scammer)\b"
)
PROFANITY_RE = re.compile(r"(?i)\b(fuck|shit|bitch|asshole|idiot|moron)\b")
REPORT_RE = re.compile(r"(?i)\b(this message says|the scammer sent|example of phishing|reported on|news report|article|dataset row|screenshot caption|the sms says|the text says)\b")
GENERIC_SPAM_RE = re.compile(r"(?i)\b(adult|casino|betting|porn|dating|loan offer|promo|discount|sale)\b")
SMS_LIKE_RE = re.compile(r"(?i)\b(dear|customer|user|member|account|verify|click|visit|call|reply|text|claim|delivery|bank|card|otp|code|alert)\b")


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as h:
        r = csv.DictReader(h)
        return list(r), list(r.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=list(dict.fromkeys(fieldnames)), extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def score_smishing(text: str) -> tuple[int, list[str]]:
    score = 0
    flags: list[str] = []
    checks = [
        (URL_RE.search(text), 2, "url_or_domain"),
        (PHONE_RE.search(text), 1, "callback_phone"),
        (ACTION_RE.search(text), 2, "action_request"),
        (ACCOUNT_RE.search(text), 2, "account_payment_credential"),
        (DELIVERY_RE.search(text), 1, "delivery_theme"),
        (GOV_RE.search(text), 1, "government_theme"),
        (URGENT_RE.search(text), 1, "urgency_or_security"),
        (REWARD_RE.search(text) and ACTION_RE.search(text), 1, "reward_with_action"),
    ]
    for ok, points, flag in checks:
        if ok:
            score += points
            flags.append(flag)
    if ABUSIVE_REPLY_RE.search(text):
        score -= 5
        flags.append("abusive_or_reply_text")
    if REPORT_RE.search(text):
        score -= 4
        flags.append("report_or_commentary_text")
    if not (URL_RE.search(text) or PHONE_RE.search(text) or ACTION_RE.search(text) or ACCOUNT_RE.search(text)):
        score -= 1
        flags.append("weak_actionable_signal")
    if PROFANITY_RE.search(text) and "abusive_or_reply_text" in flags:
        score -= 2
        flags.append("profanity_reply")
    return score, flags


def classify(row: dict[str, str]) -> dict[str, str]:
    text = row.get("message_raw", "")
    score, flags = score_smishing(text)
    reason = ""
    status = "pass_likely_smishing"
    action = "keep"

    if not text.strip() or len(text.strip()) < 5:
        status = "fail_obvious_non_smishing"
        reason = "empty or garbled text"
        action = "replace_with_raw_candidate"
    elif ABUSIVE_REPLY_RE.search(text) or (PROFANITY_RE.search(text) and re.search(r"(?i)\bscammer\b", text)):
        status = "fail_obvious_non_smishing"
        reason = "abusive/threatening reply to scammer, not smishing"
        action = "remove"
    elif REPORT_RE.search(text):
        status = "review_possible_report_text"
        reason = "report/commentary text rather than an SMS attack message"
        action = "replace_with_raw_candidate"
    elif GENERIC_SPAM_RE.search(text) and score < 2:
        status = "review_possible_spam_not_smishing"
        reason = "generic promotional spam without clear smishing signal"
        action = "manual_review"
    elif score <= 0:
        status = "review_unclear_smishing"
        reason = "weak or missing actionable smishing signal"
        action = "manual_review"
    elif score == 1:
        status = "review_unclear_smishing"
        reason = "borderline smishing signal"
        action = "manual_review"

    out = dict(row)
    out["content_quality_status"] = status
    out["content_quality_flags"] = ";".join(sorted(set(flags)))
    out["smishing_signal_score"] = str(score)
    out["non_smishing_reason"] = reason
    out["suggested_action"] = action
    return out


def table(counter: Counter[str], name: str) -> list[str]:
    lines = [f"| {name} | rows |", "| --- | --- |"]
    for k, v in counter.most_common(20):
        lines.append(f"| {k or '(blank)'} | {v} |")
    return lines


def main() -> None:
    rows, fields = read_csv(INPUT)
    smish = [classify(r) for r in rows if r.get("normalized_label") == "smishing"]
    flagged = [r for r in smish if r["content_quality_status"] != "pass_likely_smishing"]
    obvious = [r for r in smish if r["content_quality_status"] == "fail_obvious_non_smishing"]
    write_csv(FLAGS_OUT, smish, fields + ADDED)
    write_csv(NON_SMISHING_OUT, obvious, fields + ADDED)

    status_counts = Counter(r["content_quality_status"] for r in smish)
    flag_counts = Counter(f for r in smish for f in r["content_quality_flags"].split(";") if f)
    examples = obvious[:10]
    lines = [
        "# Smishing Content Quality Audit",
        "",
        "## Purpose",
        "",
        "This audit flags smishing-labeled rows that appear to be replies, commentary, generic spam, or otherwise weak smishing examples.",
        "",
        f"- Smishing rows inspected: {len(smish):,}",
        f"- Flagged for review/removal: {len(flagged):,}",
        f"- Obvious non-smishing rows: {len(obvious):,}",
        "",
        "## Status Counts",
        "",
        *table(status_counts, "content_quality_status"),
        "",
        "## Flag Counts",
        "",
        *table(flag_counts, "flag"),
        "",
        "## Obvious Non-Smishing Examples",
        "",
    ]
    for r in examples:
        sample = r["message_raw"].replace("|", "/")[:180]
        lines.append(f"- `{r['unified_id']}`: {sample}")
    lines += [
        "",
        "## Files Generated",
        "",
        f"- `{FLAGS_OUT.relative_to(ROOT)}`",
        f"- `{NON_SMISHING_OUT.relative_to(ROOT)}`",
        f"- `{REPORT.relative_to(ROOT)}`",
        "",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"Input dataset path: {INPUT.relative_to(ROOT)}")
    print(f"Rows inspected: {len(rows)}")
    print(f"Smishing rows inspected: {len(smish)}")
    print(f"Obvious non-smishing rows flagged: {len(obvious)}")
    print(f"Output file paths: {FLAGS_OUT.relative_to(ROOT)}, {NON_SMISHING_OUT.relative_to(ROOT)}")
    print(f"Report file path: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
