"""Detect near-identical smishing campaign/template repeats."""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "organized" / "raw_quality" / "combined_public_thesis_sources_deduped_strict_raw.csv"
OUT_DIR = ROOT / "data" / "organized" / "content_quality"
GROUPS_OUT = OUT_DIR / "smishing_campaign_template_groups.csv"
REPEATS_OUT = OUT_DIR / "smishing_campaign_template_repeats.csv"
EXCLUDED_OUT = OUT_DIR / "campaign_repeat_excluded_archive.csv"
REPORT = ROOT / "reports" / "smishing_campaign_template_dedup_report.md"

URL_RE = re.compile(r"(?i)\b(?:https?://|www\.)\S+|\b[a-z0-9.-]+\.(?:com|net|org|ph|co|uk|io|biz|xyz|top|site|online|click|shop|app)\S*")
EMAIL_RE = re.compile(r"(?i)\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
MONEY_RE = re.compile(r"(?i)(?:[$£€₱]\s?\d[\d,]*(?:\.\d+)?|\b(?:php|usd|gbp|eur|rs|usdt)\s?\d[\d,]*(?:\.\d+)?)")
CODE_RE = re.compile(r"(?i)\b(code|otp|pin|password|login code|verification)\s*[:#-]?\s*[a-z0-9]{4,12}\b")
TOKEN_RE = re.compile(r"\b[a-zA-Z0-9]{18,}\b")
NUM_RE = re.compile(r"\b\d[\d,.\s-]{2,}\d\b")
PUNCT_RE = re.compile(r"[^a-z0-9<>]+")

ADDED = [
    "campaign_template_key",
    "campaign_cluster_id",
    "campaign_cluster_size",
    "campaign_duplicate_status",
    "is_campaign_representative",
    "campaign_representative_reason",
]


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


def campaign_template_key(text: str) -> str:
    t = (text or "").lower()
    t = IP_RE.sub(" <IP> ", t)
    t = EMAIL_RE.sub(" <EMAIL> ", t)
    t = URL_RE.sub(" <URL> ", t)
    t = MONEY_RE.sub(" <AMOUNT> ", t)
    t = CODE_RE.sub(lambda m: re.sub(r"[a-z0-9]{4,12}$", "<CODE>", m.group(0), flags=re.I), t)
    t = PHONE_RE.sub(" <PHONE> ", t)
    t = TOKEN_RE.sub(" <TOKEN> ", t)
    t = NUM_RE.sub(" <NUM> ", t)
    t = re.sub(r"\b\d{3,}\b", " <NUM> ", t)
    t = PUNCT_RE.sub(" ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def cap_for(size: int) -> int:
    if size >= 50:
        return 3
    if size >= 10:
        return 3
    if size >= 2:
        return 2 if size >= 5 else 1
    return 1


def representative_score(row: dict[str, str]) -> tuple:
    text = row.get("message_raw", "")
    score = 0
    if "<URL>" in campaign_template_key(text):
        score += 3
    if re.search(r"(?i)\b(verify|login|account|bank|card|delivery|claim|urgent|security|otp|code)\b", text):
        score += 3
    if row.get("source_name") or row.get("dataset_name"):
        score += 1
    if row.get("long_message_flag") != "True":
        score += 1
    return (-score, len(text), row.get("unified_id", ""))


def annotate(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    smish = [r for r in rows if r.get("normalized_label") == "smishing"]
    clusters: dict[str, list[dict[str, str]]] = defaultdict(list)
    for r in smish:
        clusters[campaign_template_key(r.get("message_raw", ""))].append(r)

    out = []
    cluster_num = 1
    for key, members in sorted(clusters.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        size = len(members)
        cap = cap_for(size)
        cluster_id = f"camp_{cluster_num:06d}" if size > 1 else ""
        if size > 1:
            cluster_num += 1
        reps = set(id(r) for r in sorted(members, key=representative_score)[:cap])
        for r in members:
            row = dict(r)
            row["campaign_template_key"] = key
            row["campaign_cluster_id"] = cluster_id
            row["campaign_cluster_size"] = str(size)
            if size == 1:
                status = "unique_campaign"
                is_rep = "True"
                reason = "single-row campaign key"
            elif id(r) in reps:
                status = "campaign_representative"
                is_rep = "True"
                reason = f"selected under max {cap} per template cap"
            else:
                status = "campaign_repeat_excluded"
                is_rep = "False"
                reason = f"excluded by max {cap} per template cap"
            row["campaign_duplicate_status"] = status
            row["is_campaign_representative"] = is_rep
            row["campaign_representative_reason"] = reason
            out.append(row)
    return out


def main() -> None:
    rows, fields = read_csv(INPUT)
    annotated = annotate(rows)
    groups = [r for r in annotated if int(r["campaign_cluster_size"]) > 1 and r["is_campaign_representative"] == "True"]
    repeats = [r for r in annotated if int(r["campaign_cluster_size"]) > 1]
    excluded = [r for r in annotated if r["campaign_duplicate_status"] == "campaign_repeat_excluded"]
    write_csv(GROUPS_OUT, groups, fields + ADDED)
    write_csv(REPEATS_OUT, repeats, fields + ADDED)
    write_csv(EXCLUDED_OUT, excluded, fields + ADDED)

    sizes = [int(r["campaign_cluster_size"]) for r in groups]
    largest = max(sizes) if sizes else 1
    lines = [
        "# Smishing Campaign Template Dedup Report",
        "",
        f"- Smishing rows inspected: {len(annotated):,}",
        f"- Campaign clusters found: {len(set(r['campaign_template_key'] for r in annotated)):,}",
        f"- Repeated-template rows: {len(repeats):,}",
        f"- Largest campaign cluster size: {largest:,}",
        f"- Rows excluded by campaign cap: {len(excluded):,}",
        "- Cap rule: keep max 3 rows for large clusters, 2-3 for medium clusters, and 1-2 for small repeated clusters.",
        "",
        "## Files Generated",
        "",
        f"- `{GROUPS_OUT.relative_to(ROOT)}`",
        f"- `{REPEATS_OUT.relative_to(ROOT)}`",
        f"- `{EXCLUDED_OUT.relative_to(ROOT)}`",
        f"- `{REPORT.relative_to(ROOT)}`",
        "",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Input dataset path: {INPUT.relative_to(ROOT)}")
    print(f"Smishing rows inspected: {len(annotated)}")
    print(f"Campaign/template clusters found: {len(set(r['campaign_template_key'] for r in annotated))}")
    print(f"Campaign repeat rows excluded: {len(excluded)}")
    print(f"Largest campaign cluster size: {largest}")
    print(f"Output file paths: {GROUPS_OUT.relative_to(ROOT)}, {REPEATS_OUT.relative_to(ROOT)}, {EXCLUDED_OUT.relative_to(ROOT)}")
    print(f"Report file path: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
