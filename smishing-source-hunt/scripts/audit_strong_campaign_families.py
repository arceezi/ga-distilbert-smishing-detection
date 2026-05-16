"""Audit broad smishing campaign families with aggressive normalization."""

from __future__ import annotations

import csv
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "organized" / "content_quality" / "combined_public_thesis_sources_content_filtered.csv"
OUT_DIR = ROOT / "data" / "organized" / "campaign_family_quality"
GROUPS_OUT = OUT_DIR / "strong_campaign_family_groups.csv"
REPEATS_OUT = OUT_DIR / "strong_campaign_family_repeats.csv"
ROW_9227_OUT = OUT_DIR / "row_9227_section_review.csv"
REPORT = ROOT / "reports" / "strong_campaign_family_audit.md"

ADDED = [
    "strong_campaign_family_key",
    "strong_campaign_family_id",
    "strong_campaign_family_size",
    "strong_campaign_family_status",
    "strong_campaign_family_reason",
    "row_position_1based",
]

EMAIL_RE = re.compile(r"(?i)\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b")
URL_RE = re.compile(
    r"(?ix)"
    r"\b(?:https?://|hxxps?://|www\.)\S+"
    r"|(?<!@)\b[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
    r"(?:\s*\.\s*[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+"
    r"\s*\.\s*(?:com|net|org|ph|co|uk|io|biz|xyz|top|site|online|click|shop|app|info|live|vip|cc)\b\S*"
)
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
AMOUNT_RE = re.compile(
    r"(?ix)(?:[$£€₱]\s*)?\b\d{1,3}(?:,\d{2,3})+(?:\.\d+)?\b"
    r"|(?:[$£€₱]\s*)\d+(?:\.\d+)?"
    r"|\b(?:php|usd|gbp|eur|rs|tk|aud|bhd|usdt|trx)\s*[:#-]?\s*\d[\d,]*(?:\.\d+)?\b"
)
CODE_VALUE_RE = re.compile(r"(?i)\b(?:lv#?\d{2,8}|trxn|[a-z0-9]{4,12})\b")
CODE_CONTEXT_RE = re.compile(
    r"(?i)\b((?:new\s+)?(?:login\s+)?(?:code|otp|pin|password|verification(?:\s+code)?))\s*[:#-]?\s*"
    r"([a-z0-9#-]{3,16})"
)
LONG_TOKEN_RE = re.compile(r"\b[a-z0-9]{16,}\b", re.I)
LONG_NUM_RE = re.compile(r"\b\d[\d,.\s-]{2,}\d\b")
NAME_RE = re.compile(r"(?i)\bdear\s+([a-z][a-z.'-]{1,24})\b")
RAND_SUFFIX_RE = re.compile(r"(?i)(?:\s|^)([a-z]{4,8}|[a-z0-9]{4,10})\s*$")
ANGLE_PLACEHOLDER_RE = re.compile(r"(?i)<\s*(url|email|phone|name|amount|code|num|rand|token|ip)\s*>")
ROW_SECTION_RE = re.compile(
    r"(?i)usdtferc|dear\s+lisa|account has been reset|remaining\s*value|remainingvalue|"
    r"new login code|trxm|txrm|l0gin|usdtrxm|crypto|balance|total|usdt|login code"
)


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as h:
        reader = csv.DictReader(h)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as h:
        writer = csv.DictWriter(h, fieldnames=list(dict.fromkeys(fieldnames)), extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def base_text(text: str) -> str:
    t = unicodedata.normalize("NFKC", text or "")
    t = t.replace("\u00a0", " ")
    t = t.replace("～", "~").replace("﹣", "-").replace("–", "-").replace("—", "-")
    t = t.replace("ÙŠÐТ", " ").replace("Ù Š Ð Т", " ")
    t = t.lower()
    replacements = {
        "remainingvalue": "remaining value",
        "l0gin": "login",
        "verificacion": "verification",
        "txrm": "trxm",
        "0nline": "online",
        "acc0unt": "account",
    }
    for src, dst in replacements.items():
        t = t.replace(src, dst)
    return re.sub(r"\s+", " ", t).strip()


def explicit_family_key(text: str) -> tuple[str | None, str]:
    t = base_text(text)
    if all(x in t for x in ["usdtferc", "account has been reset", "new login code"]) and (
        "remaining value" in t or "remainingvalue" in t
    ) and ("dear lisa" in t or "dear " in t):
        return "family_usdtferc_account_reset", "explicit usdtferc account reset rule"
    if "usdtrxm" in t and "trxm" in t and "login code" in t:
        return "family_usdtrxm_login_code", "explicit usdtrxm login-code rule"
    if ("trxm" in t or " trx " in f" {t} ") and "login" in t and "login code" in t and (
        "balance" in t or "total" in t or "usdt" in t
    ):
        return "family_trxm_login_balance", "explicit TRXM login/balance rule"
    crypto_terms = ["login code", "balance", "remaining value", "usdt", "total"]
    if sum(term in t for term in crypto_terms) >= 3 and (
        re.search(r"\busdt[a-z0-9-]*\.", t) or "crypto" in t or "trxm" in t or re.search(r"\btrx\b", t)
    ):
        return "family_crypto_login_balance", "broad crypto login/balance rule"
    return None, "aggressive normalized key"


def strong_campaign_family_key(text: str) -> str:
    explicit, _ = explicit_family_key(text)
    if explicit:
        return explicit

    t = base_text(text)
    t = re.sub(r"[\[\]{}()（）【】<>]", " ", t)
    t = EMAIL_RE.sub(" <EMAIL> ", t)
    t = URL_RE.sub(" <URL> ", t)
    t = PHONE_RE.sub(" <PHONE> ", t)
    t = CODE_CONTEXT_RE.sub(lambda m: f" {m.group(1)} <CODE> ", t)
    t = NAME_RE.sub("dear <NAME>", t)
    t = AMOUNT_RE.sub(" <AMOUNT> ", t)
    t = LONG_TOKEN_RE.sub(" <TOKEN> ", t)
    t = LONG_NUM_RE.sub(" <NUM> ", t)
    t = re.sub(r"\b\d{3,}\b", " <NUM> ", t)
    t = re.sub(r"(?:~+|\|+|-{2,}|_+|[!@#$%^&*=+/\\:;,.?]{2,})", " ", t)
    t = RAND_SUFFIX_RE.sub(" <RAND>", t)
    t = re.sub(r"[^a-zA-Z0-9<>]+", " ", t)
    t = re.sub(r"\b(?:rand|token)\b\s*$", "<RAND>", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t.lower()


def family_cap(key: str, size: int) -> int:
    if key in {
        "family_usdtferc_account_reset",
        "family_trxm_login_balance",
        "family_usdtrxm_login_code",
        "family_crypto_login_balance",
    }:
        return 3
    if size >= 2:
        return 3
    return 1


def representative_score(row: dict[str, str]) -> tuple[int, int, int, str]:
    text = row.get("message_raw", "")
    t = base_text(text)
    score = 0
    if re.search(r"\b(account|login|verify|security|locked|balance|delivery|claim|bank|card|otp|code)\b", t):
        score += 4
    if URL_RE.search(t) or "http" in t:
        score += 2
    if row.get("raw_text_available") == "True":
        score += 2
    if row.get("raw_text_status") in {"original_looking_raw", "original_unredacted"}:
        score += 2
    if not re.search(r"[^\x00-\x7f]{2,}", text):
        score += 1
    if 25 <= len(text) <= 180:
        score += 1
    return (-score, len(text), int(row.get("row_position_1based") or 0), row.get("unified_id", ""))


def annotate(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    smish = []
    for pos, row in enumerate(rows, start=1):
        if row.get("normalized_label") == "smishing":
            out = dict(row)
            out["row_position_1based"] = str(pos)
            key = strong_campaign_family_key(out.get("message_raw", ""))
            out["strong_campaign_family_key"] = key
            out["strong_campaign_family_reason"] = explicit_family_key(out.get("message_raw", ""))[1]
            smish.append(out)

    clusters: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in smish:
        clusters[row["strong_campaign_family_key"]].append(row)

    family_ids = {
        key: f"strongfam_{idx:06d}"
        for idx, (key, members) in enumerate(sorted(clusters.items(), key=lambda kv: (-len(kv[1]), kv[0])), start=1)
        if len(members) > 1
    }
    annotated = []
    for key, members in clusters.items():
        size = len(members)
        cap = family_cap(key, size)
        representatives = {id(r) for r in sorted(members, key=representative_score)[:cap]}
        for row in members:
            out = dict(row)
            out["strong_campaign_family_id"] = family_ids.get(key, "")
            out["strong_campaign_family_size"] = str(size)
            if size == 1:
                out["strong_campaign_family_status"] = "unique_family"
                out["strong_campaign_family_reason"] = "single-row strong campaign family"
            elif id(row) in representatives:
                out["strong_campaign_family_status"] = "family_representative"
                out["strong_campaign_family_reason"] = f"selected under max {cap} per strong family cap"
            else:
                out["strong_campaign_family_status"] = "family_repeat_exclude"
                out["strong_campaign_family_reason"] = f"excluded by max {cap} per strong family cap"
            annotated.append(out)
    return sorted(annotated, key=lambda r: int(r["row_position_1based"]))


def row_9227_review(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    return [
        r
        for r in rows
        if int(r.get("row_position_1based") or 0) >= 9200
        and (
            r.get("source_name") == "SMS Phishing Dataset"
            or ROW_SECTION_RE.search(r.get("message_raw", ""))
            or r.get("strong_campaign_family_key", "").startswith("family_")
        )
    ]


def md_table(counter: Counter[str], name: str, limit: int = 15) -> list[str]:
    lines = [f"| {name} | rows |", "| --- | ---: |"]
    for key, value in counter.most_common(limit):
        lines.append(f"| `{key[:120]}` | {value:,} |")
    return lines


def main() -> None:
    rows, fields = read_csv(INPUT)
    annotated = annotate(rows)
    repeated = [r for r in annotated if int(r["strong_campaign_family_size"]) > 1]
    review = row_9227_review(annotated)
    groups = annotated
    repeats = repeated
    write_csv(GROUPS_OUT, groups, fields + ADDED)
    write_csv(REPEATS_OUT, repeats, fields + ADDED)
    write_csv(ROW_9227_OUT, review, fields + ADDED)

    family_counts = Counter(r["strong_campaign_family_key"] for r in annotated)
    status_counts = Counter(r["strong_campaign_family_status"] for r in annotated)
    review_counts = Counter(r["strong_campaign_family_key"] for r in review)
    known = {
        key: family_counts.get(key, 0)
        for key in [
            "family_usdtferc_account_reset",
            "family_trxm_login_balance",
            "family_usdtrxm_login_code",
            "family_crypto_login_balance",
        ]
    }
    row_usdtferc = [r for r in review if r["strong_campaign_family_key"] == "family_usdtferc_account_reset"]
    row_9200_repeated = [
        r
        for r in annotated
        if int(r.get("row_position_1based") or 0) >= 9200 and int(r.get("strong_campaign_family_size") or 1) > 1
    ]
    lines = [
        "# Strong Campaign Family Audit",
        "",
        "## Summary",
        "",
        f"- Input dataset: `{INPUT.relative_to(ROOT)}`",
        f"- Rows inspected: {len(rows):,}",
        f"- Smishing rows audited: {len(annotated):,}",
        f"- Strong campaign families: {len(family_counts):,}",
        f"- Largest family before filtering: {max(family_counts.values() or [0]):,}",
        f"- Repeated-family rows: {len(repeated):,}",
        f"- Rows marked `family_repeat_exclude`: {status_counts.get('family_repeat_exclude', 0):,}",
        "",
        "## Row 9227 Section Finding",
        "",
        "Rows 9226/9227 onward include repeated SMS Phishing Dataset crypto/account-reset/login-code/remaining-value templates.",
        f"- Row 9200+ review rows written: {len(review):,}",
        f"- Row 9200+ repeated-family rows found: {len(row_9200_repeated):,}",
        f"- usdtferc account-reset family found in row 9200+ section: {len(row_usdtferc):,}",
        f"- usdtferc account-reset kept by cap: {sum(r['strong_campaign_family_status']=='family_representative' for r in row_usdtferc):,}",
        f"- usdtferc account-reset excluded by cap: {sum(r['strong_campaign_family_status']=='family_repeat_exclude' for r in row_usdtferc):,}",
        "",
        "## Known Explicit Families",
        "",
        f"- `family_usdtferc_account_reset`: {known['family_usdtferc_account_reset']:,}",
        f"- `family_trxm_login_balance`: {known['family_trxm_login_balance']:,}",
        f"- `family_usdtrxm_login_code`: {known['family_usdtrxm_login_code']:,}",
        f"- `family_crypto_login_balance`: {known['family_crypto_login_balance']:,}",
        "",
        "## Largest Families Before Filtering",
        "",
        *md_table(family_counts, "strong_campaign_family_key"),
        "",
        "## Row 9200+ Grouping",
        "",
        *md_table(review_counts, "strong_campaign_family_key"),
        "",
        "## Cap Rules",
        "",
        "- Default repeated-family cap: keep max 3 rows per `strong_campaign_family_key`.",
        "- Specific usdtferc/TRXM/usdtrxm/crypto login-balance family cap: keep max 3 rows.",
        "",
        "## Files Generated",
        "",
        f"- `{GROUPS_OUT.relative_to(ROOT)}`",
        f"- `{REPEATS_OUT.relative_to(ROOT)}`",
        f"- `{ROW_9227_OUT.relative_to(ROOT)}`",
        f"- `{REPORT.relative_to(ROOT)}`",
        "",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"input dataset path: {INPUT.relative_to(ROOT)}")
    print(f"rows inspected: {len(rows)}")
    print(f"row 9227 section repeated-family count: {len(row_9200_repeated)}")
    print(f"largest campaign family before filtering: {max(family_counts.values() or [0])}")
    print(f"campaign repeats excluded: {status_counts.get('family_repeat_exclude', 0)}")
    print(f"output files: {GROUPS_OUT.relative_to(ROOT)}, {REPEATS_OUT.relative_to(ROOT)}, {ROW_9227_OUT.relative_to(ROOT)}")
    print(f"report files: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
