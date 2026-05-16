"""Deterministic adversarial perturbation engine for smishing SMS text."""

from __future__ import annotations

import random
import re
import unicodedata
from dataclasses import asdict, dataclass
from urllib.parse import urlsplit

from model_ready_common import (
    ADVERSARIAL_SEED,
    ENABLED_PERTURBATION_TECHNIQUES,
    URL_RE,
    deterministic_row_seed,
    light_clean_model_text,
    normalize_whitespace,
)


HOMOGLYPHS = {
    "a": ["а"],
    "e": ["е"],
    "o": ["ο", "о"],
    "p": ["р"],
    "c": ["с"],
    "x": ["х"],
    "i": ["ı"],
}

LEET_MAP = {
    "o": "0",
    "i": "1",
    "l": "1",
    "e": "3",
    "a": "@",
    "s": "$",
    "t": "7",
}

SUSPICIOUS_KEYWORDS = [
    "verify",
    "login",
    "account",
    "update",
    "secure",
    "security",
    "password",
    "wallet",
    "claim",
    "prize",
    "blocked",
    "suspended",
    "locked",
    "limited",
    "delivery",
    "package",
    "payment",
    "refund",
]

SEPARATOR_VARIANTS = {
    "verify": ["v.e.r.i.f.y", "v e r i f y", "ver-ify"],
    "login": ["l o g i n", "log-in", "lo.gin"],
    "account": ["acc-ount", "ac.count", "a c c o u n t"],
    "update": ["up.date", "up-date", "u p d a t e"],
    "secure": ["se-cure", "s.e.c.u.r.e"],
    "claim": ["cl.aim", "c l a i m"],
    "password": ["pass-word", "p a s s w o r d"],
    "wallet": ["wal-let", "w.al.let"],
}

URGENCY_REPLACEMENTS = [
    (re.compile(r"\bact now\b", re.I), ["respond immediately", "take action today"]),
    (re.compile(r"\burgent\b", re.I), ["immediate", "time-sensitive"]),
    (re.compile(r"\bfinal notice\b", re.I), ["last reminder", "last notice"]),
    (re.compile(r"\baccount locked\b", re.I), ["access restricted", "account access limited"]),
    (re.compile(r"\bexpires today\b", re.I), ["ends today", "valid today only"]),
    (re.compile(r"\bimmediately\b", re.I), ["right away", "without delay"]),
    (re.compile(r"\blast chance\b", re.I), ["last reminder", "final opportunity"]),
]

INSTITUTION_SWAPS = [
    (re.compile(r"\bBDO\b", re.I), "BPI", lambda text: True),
    (re.compile(r"\bBPI\b", re.I), "BDO", lambda text: True),
    (re.compile(r"\bGCash\b", re.I), "Maya", lambda text: True),
    (re.compile(r"\bMaya\b", re.I), "GCash", lambda text: True),
    (re.compile(r"\bDHL\b", re.I), "UPS", lambda text: _delivery_context(text)),
    (re.compile(r"\bUPS\b", re.I), "USPS", lambda text: _delivery_context(text)),
    (re.compile(r"\bUSPS\b", re.I), "DHL", lambda text: _delivery_context(text)),
    (re.compile(r"\bPayPal\b", re.I), "Amazon", lambda text: _commerce_context(text)),
    (re.compile(r"\bAmazon\b", re.I), "PayPal", lambda text: _commerce_context(text)),
]

CONTROL_CATEGORY_PREFIXES = ("C",)


@dataclass
class PerturbationResult:
    adv_message_raw: str
    perturbation_techniques: str
    num_chars_changed: int
    changed_token_count: int
    achieved_perturbation_rate: float
    quality_status: str
    label_preserved: bool
    seed: int
    notes: str


def _delivery_context(text: str) -> bool:
    return bool(re.search(r"\b(package|parcel|delivery|shipment|tracking|customs|courier)\b", text, re.I))


def _commerce_context(text: str) -> bool:
    return bool(re.search(r"\b(order|payment|invoice|refund|purchase|account|card|wallet)\b", text, re.I))


def _sample_indices(rng: random.Random, indices: list[int], count: int) -> list[int]:
    if not indices or count <= 0:
        return []
    count = min(count, len(indices))
    return rng.sample(indices, count)


def _homoglyph_substitution(text: str, rng: random.Random, level: int) -> tuple[str, bool, str]:
    chars = list(text)
    eligible = [idx for idx, char in enumerate(chars) if char.lower() in HOMOGLYPHS and not _inside_angle_placeholder(chars, idx)]
    target = max(1, min(6, round(len(eligible) * (0.02 if level <= 10 else 0.04 if level <= 20 else 0.06))))
    changed = 0
    for idx in _sample_indices(rng, eligible, target):
        lower = chars[idx].lower()
        replacement = rng.choice(HOMOGLYPHS[lower])
        chars[idx] = replacement
        changed += 1
    return "".join(chars), changed > 0, f"homoglyph_chars={changed}"


def _inside_angle_placeholder(chars: list[str], idx: int) -> bool:
    left = "".join(chars[max(0, idx - 12) : idx + 1])
    right = "".join(chars[idx : min(len(chars), idx + 12)])
    return "<" in left and ">" in right


def _leet_obfuscation(text: str, rng: random.Random, level: int) -> tuple[str, bool, str]:
    pattern = re.compile(r"\b(" + "|".join(re.escape(word) for word in SUSPICIOUS_KEYWORDS) + r")\b", re.I)
    matches = list(pattern.finditer(text))
    if not matches:
        matches = list(re.finditer(r"\b[a-zA-Z]{5,}\b", text))
    if not matches:
        return text, False, "no_eligible_keyword"
    chosen = rng.sample(matches, min(len(matches), 1 if level <= 10 else 2 if level <= 20 else 3))
    spans = {match.span() for match in chosen}
    changed = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal changed
        if match.span() not in spans:
            return match.group(0)
        out = []
        per_word_cap = 1 if level <= 10 else 2 if level <= 20 else 3
        used = 0
        for char in match.group(0):
            lower = char.lower()
            if lower in LEET_MAP and used < per_word_cap and rng.random() < 0.75:
                out.append(LEET_MAP[lower])
                used += 1
                changed += 1
            else:
                out.append(char)
        return "".join(out)

    return pattern.sub(repl, text), changed > 0, f"leet_chars={changed}"


def _separator_injection(text: str, rng: random.Random, level: int) -> tuple[str, bool, str]:
    candidates = [word for word in SEPARATOR_VARIANTS if re.search(rf"\b{re.escape(word)}\b", text, re.I)]
    if not candidates:
        return text, False, "no_separator_keyword"
    word = rng.choice(candidates)
    replacement = rng.choice(SEPARATOR_VARIANTS[word])
    new_text, count = re.subn(rf"\b{re.escape(word)}\b", replacement, text, count=1, flags=re.I)
    return new_text, count > 0, f"separator_keyword={word}"


def _url_variation(text: str, rng: random.Random, level: int) -> tuple[str, bool, str]:
    matches = list(URL_RE.finditer(text))
    if not matches:
        return text, False, "no_url_found"
    match = rng.choice(matches)
    token = match.group(0)
    trailing = ""
    while token and token[-1] in ".,!?)];":
        trailing = token[-1] + trailing
        token = token[:-1]
    try:
        parsed = urlsplit(token if re.match(r"^[a-z]+://", token, re.I) else f"https://{token}")
    except ValueError:
        return text, False, "url_parse_failed"
    host = parsed.netloc or parsed.path.split("/")[0]
    host_core = re.sub(r"[^a-z0-9-]+", "-", host.lower()).strip("-")
    host_core = re.sub(r"-(com|net|org|ph|info|site|online|xyz|shop|biz)$", "", host_core)
    if not host_core:
        return text, False, "url_host_parse_failed"
    prefix = "https://" if token.lower().startswith("http") else ""
    subdomain = rng.choice(["secure", "verify", "login", "support"])
    path = rng.choice(["/verify", "/account", "/sms", "/ref"])
    replacement = f"{prefix}{subdomain}-{host_core}.invalid{path}{trailing}"
    new_text = text[: match.start()] + replacement + text[match.end() :]
    return new_text, True, "url_domain_changed_to_safe_invalid_tld"


def _urgency_paraphrasing(text: str, rng: random.Random, level: int) -> tuple[str, bool, str]:
    options = [(pattern, replacements) for pattern, replacements in URGENCY_REPLACEMENTS if pattern.search(text)]
    if not options:
        return text, False, "no_urgency_phrase"
    pattern, replacements = rng.choice(options)
    replacement = rng.choice(replacements)
    new_text, count = pattern.subn(replacement, text, count=1)
    return new_text, count > 0, f"urgency_phrase={pattern.pattern}"


def _numeric_otp_variation(text: str, rng: random.Random, level: int) -> tuple[str, bool, str]:
    matches = list(re.finditer(r"\b\d{2,14}\b", text))
    if not matches:
        return text, False, "no_digit_sequence"
    target = min(len(matches), 1 if level <= 10 else 2 if level <= 20 else 3)
    chosen = {match.span() for match in rng.sample(matches, target)}
    changed = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal changed
        if match.span() not in chosen:
            return match.group(0)
        length = len(match.group(0))
        if 4 <= length <= 6:
            new_length = rng.choice([length, max(4, length - 1)])
        else:
            new_length = length
        first = str(rng.randint(1, 9))
        rest = "".join(str(rng.randint(0, 9)) for _ in range(max(0, new_length - 1)))
        changed += 1
        return first + rest

    return re.sub(r"\b\d{2,14}\b", repl, text), changed > 0, f"numeric_sequences={changed}"


def _spacing_punctuation_case_noise(text: str, rng: random.Random, level: int) -> tuple[str, bool, str]:
    tokens = text.split(" ")
    if not tokens:
        return text, False, "empty_text"
    changed = 0
    token_indices = [idx for idx, token in enumerate(tokens) if len(token) >= 3 and not token.startswith("<")]
    if token_indices:
        for idx in _sample_indices(rng, token_indices, 1 if level <= 10 else 2 if level <= 20 else 3):
            token = tokens[idx]
            action = rng.choice(["case", "punct", "space"])
            if action == "case":
                tokens[idx] = "".join(char.upper() if rng.random() < 0.45 else char.lower() for char in token)
            elif action == "punct":
                tokens[idx] = token + rng.choice(["!", ".", "-"])
            else:
                midpoint = max(1, len(token) // 2)
                tokens[idx] = token[:midpoint] + " " + token[midpoint:]
            changed += 1
    new_text = " ".join(tokens)
    if rng.random() < (0.25 if level <= 10 else 0.4 if level <= 20 else 0.55):
        new_text = re.sub(r" ", "  ", new_text, count=1)
        changed += 1
    return new_text, changed > 0, f"noise_edits={changed}"


def _institution_substitution(text: str, rng: random.Random, level: int) -> tuple[str, bool, str]:
    candidates = [(pattern, replacement) for pattern, replacement, guard in INSTITUTION_SWAPS if pattern.search(text) and guard(text)]
    if not candidates:
        return text, False, "no_context_safe_institution_swap"
    pattern, replacement = rng.choice(candidates)
    new_text, count = pattern.subn(replacement, text, count=1)
    return new_text, count > 0, f"institution_swap={replacement}"


TECHNIQUE_FUNCTIONS = {
    "homoglyph_substitution": _homoglyph_substitution,
    "leetspeak_obfuscation": _leet_obfuscation,
    "separator_injection": _separator_injection,
    "url_variation": _url_variation,
    "urgency_paraphrasing": _urgency_paraphrasing,
    "numeric_otp_variation": _numeric_otp_variation,
    "spacing_punctuation_case_noise": _spacing_punctuation_case_noise,
    "institution_substitution": _institution_substitution,
}


def _changed_chars(original: str, perturbed: str) -> int:
    overlap = sum(1 for left, right in zip(original, perturbed) if left != right)
    return overlap + abs(len(original) - len(perturbed))


def _changed_tokens(original: str, perturbed: str) -> int:
    left_tokens = original.split()
    right_tokens = perturbed.split()
    overlap = sum(1 for left, right in zip(left_tokens, right_tokens) if left != right)
    return overlap + abs(len(left_tokens) - len(right_tokens))


def _quality_check(original: str, perturbed: str, require_difference: bool = True) -> tuple[str, list[str]]:
    notes = []
    text = normalize_whitespace(perturbed)
    if not text:
        notes.append("empty_output")
    if require_difference and text == normalize_whitespace(original):
        notes.append("unchanged_output")
    if len(text) < max(5, min(12, len(normalize_whitespace(original)) // 3)):
        notes.append("too_short")
    max_len = max(320, int(len(normalize_whitespace(original)) * 1.5) + 20)
    if len(text) > max_len:
        notes.append("too_long")
    if any(unicodedata.category(char).startswith(CONTROL_CATEGORY_PREFIXES) for char in text):
        notes.append("unicode_control_character")
    if re.search(r"([!?.,])\1{4,}", text):
        notes.append("excessive_repeated_punctuation")
    alpha_num = sum(1 for char in text if char.isalnum())
    if alpha_num / max(1, len(text)) < 0.25:
        notes.append("low_readability_ratio")
    status = "pass" if not notes else "fail"
    return status, notes


def perturb_smishing_message(
    message_raw: str,
    perturbation_level: int,
    seed: int = ADVERSARIAL_SEED,
    allowed_techniques: list[str] | None = None,
    row_seed: int | None = None,
) -> dict[str, object]:
    """Return a deterministic, label-preserving adversarial smishing variant."""

    original = normalize_whitespace(message_raw)
    actual_seed = row_seed if row_seed is not None else deterministic_row_seed(original[:32], "adversarial", perturbation_level, seed)
    rng = random.Random(actual_seed)
    allowed = [tech for tech in (allowed_techniques or ENABLED_PERTURBATION_TECHNIQUES) if tech in TECHNIQUE_FUNCTIONS]
    desired_changes = 2 if perturbation_level <= 10 else 3 if perturbation_level <= 20 else 5
    technique_order = allowed[:]
    rng.shuffle(technique_order)
    text = original
    applied: list[str] = []
    notes: list[str] = []

    for technique in technique_order:
        if len(applied) >= desired_changes:
            break
        new_text, did_apply, note = TECHNIQUE_FUNCTIONS[technique](text, rng, perturbation_level)
        if did_apply and normalize_whitespace(new_text) != normalize_whitespace(text):
            text = normalize_whitespace(new_text)
            applied.append(technique)
        notes.append(f"{technique}:{note}")

    if normalize_whitespace(text) == original:
        for fallback in ["separator_injection", "leetspeak_obfuscation", "spacing_punctuation_case_noise", "homoglyph_substitution"]:
            new_text, did_apply, note = TECHNIQUE_FUNCTIONS[fallback](text, rng, perturbation_level)
            notes.append(f"fallback_{fallback}:{note}")
            if did_apply and normalize_whitespace(new_text) != original:
                text = normalize_whitespace(new_text)
                if fallback not in applied:
                    applied.append(fallback)
                break

    if normalize_whitespace(text) == original and original:
        text = normalize_whitespace(original + "!")
        applied.append("spacing_punctuation_case_noise")
        notes.append("fallback_terminal_punctuation")

    if re.search(r"([!?.,])\1{4,}", text):
        text = re.sub(r"([!?.,])\1{4,}", r"\1\1\1", text)
        notes.append("collapsed_excessive_repeated_punctuation")

    max_len = max(320, int(len(original) * 1.5) + 20)
    if len(text) > max_len:
        text = text[:max_len].rstrip()
        notes.append("trimmed_to_length_guard")

    status, quality_notes = _quality_check(original, text, require_difference=True)
    notes.extend(quality_notes)
    changed_chars = _changed_chars(original, text)
    changed_tokens = _changed_tokens(original, text)
    result = PerturbationResult(
        adv_message_raw=text,
        perturbation_techniques=";".join(applied),
        num_chars_changed=changed_chars,
        changed_token_count=changed_tokens,
        achieved_perturbation_rate=round(changed_chars / max(1, len(original)), 4),
        quality_status=status,
        label_preserved=True,
        seed=actual_seed,
        notes=" | ".join(notes),
    )
    return asdict(result)


def clean_adversarial_text_for_model(text: str) -> str:
    return light_clean_model_text(text)


def sample_engine_smoke_test() -> list[dict[str, object]]:
    samples = [
        "URGENT: Your BDO account is locked. Verify now at https://secure-bdo-login.example/otp ref 123456.",
        "GCash notice: claim your refund before it expires today. Use code 482991 at gcash-help.example.",
    ]
    return [perturb_smishing_message(sample, level, row_seed=deterministic_row_seed(idx, "smoke", level, 42)) for idx, sample in enumerate(samples) for level in (10, 20, 30)]


if __name__ == "__main__":
    for row in sample_engine_smoke_test():
        print(row)
