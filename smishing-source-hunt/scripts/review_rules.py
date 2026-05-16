"""Shared source-aware review heuristics for candidate smishing rows."""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher


URL_OR_CONTACT_RE = re.compile(
    r"(?i)(<url>|<phone>|<phone_number>|<email>|http|www\.|\b[a-z0-9.-]+\.(?:com|net|org|co|io|ph|bd|uk)\b)"
)
CTA_RE = re.compile(
    r"(?i)\b("
    r"click|tap|visit|verify|confirm|login|log in|sign in|update|reactivate|unlock|recover|"
    r"claim|call|text|reply|schedule|resolve|fix|appeal|pay|settle|open|view|message me"
    r")\b"
)
PHISHING_CONTEXT_RE = re.compile(
    r"(?i)\b("
    r"account|bank|wallet|card|payment|parcel|package|delivery|post office|amazon|apple|netflix|"
    r"paypal|zelle|wells|tax|refund|prize|reward|winner|bonus|security|suspended|locked|"
    r"unusual activity|failed login|verification|otp|mum|dad|whatsapp|phone is about to die"
    r")\b"
)
FRAGMENT_RE = re.compile(r"(?i)^(frm:|subj:|msg:|alert!!|hi mum$|you have a parcel pending for delivery\.?$)")
NON_ENGLISH_HINT_RE = re.compile(
    r"(?i)\b("
    r"einzigartiges|jetzt|spielen|bonusangebot|bonjour|salut|mon chou|rdv ici|"
    r"verification obligatoire|cuenta|envio|paquete|actualiza|premio|"
    r"din pakke|posthus|venligst|gebyrer|grundet|pakkest|opkr|levering|"
    r"uppdatering|ditt paket|betala|avgifterna|leveransen|"
    r"spinnaa|pelien|ilmaiskierrosta|yhteydess|talletuksen|"
    r"bangladesh bank|emergency-bank|nri account"
    r")\b"
)
MOJIBAKE_RE = re.compile(
    r"(?:\u00c2|\u00c3|\ufffd|\u00b7\u00b7\u00b7|\u00e2\u20ac|"
    r"\u00e2\u20ac\u2122|\u00e2\u20ac\u0153|\u00f0\u0178)"
)
DECORATIVE_SYMBOL_RE = re.compile(r"[\U0001F300-\U0001FAFF\u2190-\u21FF\u2600-\u27BF]")
DENSE_ALERT_FORMAT_RE = re.compile(
    r"(?i)("
    r"#\w+#|"
    r"(?:/\s*){2,}|"
    r"^\s*(?:\[[^\]]+\]\s*){1,}|"
    r"\b[A-Z][A-Z.-]{1,8}\s*ID#|"
    r"\bID\d{3,}\b|"
    r"\b[A-Z]{1,4}#ID\d+|"
    r"/\s*(?:no subject|notice|u-s-p-s|td\.alerts|tdbank)"
    r")"
)
PLACEHOLDER_RE = re.compile(r"<[^>]+>")
READABILITY_PLACEHOLDER_RE = re.compile(
    r"<(?:URL|OTP|EMAIL|PHONE|PHONE_NUMBER|ACCT|DATE_TIME|NAMED_ENTITY|US_DRIVER_LICENSE)>"
)
TOKEN_RE = re.compile(r"[a-z0-9]+")
ALLOWED_SYMBOLS = set("$\u00a3\u20ac\u00a5\u20b9\u20b1")


@dataclass(frozen=True)
class ReviewDecision:
    status: str
    label: str
    reason: str
    confidence: str


def normalized_message(row: dict[str, str]) -> str:
    return (row.get("message_clean") or row.get("message_raw") or "").strip()


def ascii_ratio(text: str) -> float:
    if not text:
        return 0.0
    ascii_chars = sum(1 for char in text if ord(char) < 128)
    return ascii_chars / len(text)


def word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z]{2,}", text))


def has_smishing_signal(text: str) -> bool:
    return bool(URL_OR_CONTACT_RE.search(text) or (CTA_RE.search(text) and PHISHING_CONTEXT_RE.search(text)))


def is_sms_length(text: str) -> bool:
    return 12 <= len(text) <= 320 and word_count(text) >= 3


def is_likely_english(text: str) -> bool:
    return ascii_ratio(text) >= 0.92 and not NON_ENGLISH_HINT_RE.search(text)


def approval_english_failure_reason(text: str) -> str:
    if MOJIBAKE_RE.search(text):
        return "contains mojibake or encoding artifacts"
    if NON_ENGLISH_HINT_RE.search(text):
        return "contains non-English leakage"
    if DECORATIVE_SYMBOL_RE.search(text):
        return "contains emoji or decorative symbols"
    if ascii_ratio(text) < 0.98:
        return "falls below strict English ASCII threshold"
    return ""


def is_approval_safe_english(text: str) -> bool:
    return approval_english_failure_reason(text) == ""


def symbol_ratio(text: str) -> float:
    readable = READABILITY_PLACEHOLDER_RE.sub("placeholder", text)
    if not readable:
        return 1.0
    symbol_count = sum(
        1
        for char in readable
        if not char.isalnum() and not char.isspace() and char not in ALLOWED_SYMBOLS
    )
    return symbol_count / len(readable)


def readability_failure_reason(text: str) -> str:
    if DENSE_ALERT_FORMAT_RE.search(text):
        return "contains dense alert/token formatting"
    if symbol_ratio(text) > 0.16:
        return "exceeds strict punctuation/symbol density"
    if re.search(r"(?i)(?:[A-Z0-9][#/_-]){4,}", text):
        return "contains token-heavy symbol formatting"
    return ""


def is_readable_sms(text: str) -> bool:
    return readability_failure_reason(text) == ""


def approval_safety_failure_reason(text: str) -> str:
    english_reason = approval_english_failure_reason(text)
    if english_reason:
        return english_reason
    return readability_failure_reason(text)


def template_signature(text: str) -> str:
    """Make a rough campaign/template key for repetition control."""
    lowered = PLACEHOLDER_RE.sub(" placeholder ", text.lower())
    lowered = re.sub(r"\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b", " placeholder ", lowered)
    lowered = re.sub(r"\b\d+\b", " number ", lowered)
    tokens = [token for token in TOKEN_RE.findall(lowered) if len(token) > 2]
    return " ".join(tokens[:18])


def near_duplicate_ratio(left: str, right: str) -> float:
    return SequenceMatcher(None, left, right, autojunk=True).ratio()


def review_smishx(row: dict[str, str]) -> ReviewDecision:
    text = normalized_message(row)
    if not is_sms_length(text):
        return ReviewDecision("needs_review", "smishing", "SmishX row is outside normal SMS length or too fragmentary.", "medium")
    approval_failure = approval_safety_failure_reason(text)
    if approval_failure:
        return ReviewDecision("needs_review", "smishing", f"SmishX row failed strict approval cleanup: {approval_failure}.", "high")
    if not has_smishing_signal(text):
        return ReviewDecision("needs_review", "smishing", "SmishX row lacks a clear phishing action, URL, or contact hook.", "medium")
    return ReviewDecision("approved", "smishing", "SmishX high-confidence SMS-like phishing row from manually relabeled source.", "high")


def review_imc25(row: dict[str, str]) -> ReviewDecision:
    text = normalized_message(row)
    category = (row.get("scam_category") or "").strip().lower()
    if not is_sms_length(text):
        return ReviewDecision("needs_review", "smishing", "IMC25 row is too short, too long, or fragmentary for direct approval.", "medium")
    approval_failure = approval_safety_failure_reason(text)
    if approval_failure:
        return ReviewDecision("needs_review", "smishing", f"IMC25 row failed strict approval cleanup: {approval_failure}.", "high")
    if FRAGMENT_RE.search(text) and not URL_OR_CONTACT_RE.search(text):
        return ReviewDecision("needs_review", "smishing", "IMC25 row reads like a fragment without enough phishing context.", "medium")
    if category == "wrong number" and not (URL_OR_CONTACT_RE.search(text) or CTA_RE.search(text)):
        return ReviewDecision("needs_review", "smishing", "IMC25 wrong-number lure lacks a clear phishing action in the message text.", "medium")
    if not has_smishing_signal(text):
        return ReviewDecision("needs_review", "smishing", "IMC25 row lacks a clear phishing action, URL, contact hook, or account-risk lure.", "medium")
    return ReviewDecision("approved", "smishing", "IMC25 English SMS-like phishing row with direct lure/action signal.", "high")


def review_bengali_english(row: dict[str, str]) -> ReviewDecision:
    text = normalized_message(row)
    if not is_sms_length(text):
        return ReviewDecision("needs_review", "smishing", "Bengali English subset row is too short/long or fragmentary.", "medium")
    approval_failure = approval_safety_failure_reason(text)
    if approval_failure:
        return ReviewDecision("needs_review", "smishing", f"Bengali English subset row failed strict approval cleanup: {approval_failure}.", "high")
    if re.search(r"(?i)\b(emergency-bank\.bd|nri account|tk:|bangladesh bank)\b", text):
        return ReviewDecision("needs_review", "smishing", "Bengali English subset row may be synthetic/template-heavy or geographically narrow.", "medium")
    if not has_smishing_signal(text):
        return ReviewDecision("needs_review", "smishing", "Bengali English subset row lacks a clear phishing action or contact hook.", "medium")
    return ReviewDecision("approved", "smishing", "Bengali English subset row passes natural English SMS-like phishing checks.", "medium")


def review_ncsu(row: dict[str, str]) -> ReviewDecision:
    text = normalized_message(row)
    if not is_sms_length(text):
        return ReviewDecision("rejected", "reject", "NCSU row is outside normal SMS length or too fragmentary.", "medium")
    if not is_likely_english(text):
        return ReviewDecision("rejected", "reject", "NCSU row appears non-English under conservative English triage.", "medium")
    if not has_smishing_signal(text):
        return ReviewDecision("needs_review", "smishing", "NCSU English row lacks enough direct phishing signal for automatic approval.", "medium")
    return ReviewDecision("needs_review", "smishing", "NCSU row passed English/phishing triage but needs campaign repetition review before approval.", "medium")


def review_row(row: dict[str, str]) -> ReviewDecision:
    source = (row.get("source_name") or "").strip().lower()
    if source == "smishx":
        return review_smishx(row)
    if source == "smishing-dataset-imc25":
        return review_imc25(row)
    if source == "bengali sms smishing dataset":
        return review_bengali_english(row)
    if source == "sms phishing dataset":
        return review_ncsu(row)
    return ReviewDecision("needs_review", row.get("label") or "smishing", "Source has no configured automatic approval rule.", "medium")
