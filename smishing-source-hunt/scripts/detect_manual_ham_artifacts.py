"""Detect UI/OCR artifact rows in approved manual ham."""

from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "manual_ham_drive" / "final" / "approved_manual_ham_merged.csv"
OUT = ROOT / "data" / "manual_ham_drive" / "final" / "manual_ham_artifact_candidates.csv"
REPORT = ROOT / "reports" / "manual_ham_artifact_detection_report.md"

ADDED = ["artifact_flag", "artifact_type", "artifact_reason", "suggested_action"]

EXACT_ARTIFACT_RE = re.compile(
    r"(?i)^\s*(?:"
    r"tap\s+to\s+load\s+preview|tap\s+to\s+view|tap\s+to\s+preview|load\s+preview|"
    r"message\s+preview|view\s+preview|tap\s+for\s+more|see\s+more|load\s+more|"
    r"preview\s+unavailable|image|photo|attachment|screenshot|mms|multimedia\s+message|"
    r"download\s+message|tap\s+to\s+download|loading\.{0,3}|no\s+preview\s+available"
    r")\.?\s*$"
)
EMBEDDED_ARTIFACT_RE = re.compile(
    r"(?i)\b(?:"
    r"tap\s+to\s+load\s+preview|tap\s+to\s+view|tap\s+to\s+preview|load\s+preview|"
    r"message\s+preview|view\s+preview|tap\s+for\s+more|see\s+more|load\s+more|"
    r"preview\s+unavailable|download\s+message|tap\s+to\s+download|no\s+preview\s+available"
    r")\b"
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


def classify_artifact(row: dict[str, str]) -> tuple[bool, str, str, str]:
    raw = (row.get("message_raw") or "").strip()
    clean = (row.get("message_clean") or "").strip()
    if EXACT_ARTIFACT_RE.search(raw) or EXACT_ARTIFACT_RE.search(clean):
        return True, "ui_preview_artifact", "message text is exactly or nearly exactly a phone/app preview UI artifact", "remove_artifact"
    if EMBEDDED_ARTIFACT_RE.search(raw) or EMBEDDED_ARTIFACT_RE.search(clean):
        return True, "embedded_ui_preview_text", "UI preview phrase appears inside a longer row; keep for manual review to avoid removing a legitimate SMS", "manual_review"
    return False, "", "", "keep"


def main() -> None:
    rows, fields = read_csv(INPUT)
    candidates: list[dict[str, str]] = []
    for row in rows:
        flag, artifact_type, reason, action = classify_artifact(row)
        if not flag:
            continue
        out = dict(row)
        out["artifact_flag"] = "True"
        out["artifact_type"] = artifact_type
        out["artifact_reason"] = reason
        out["suggested_action"] = action
        candidates.append(out)

    write_csv(OUT, candidates, fields + ADDED)

    action_counts = Counter(r["suggested_action"] for r in candidates)
    type_counts = Counter(r["artifact_type"] for r in candidates)
    lines = [
        "# Manual Ham Artifact Detection Report",
        "",
        f"- Input file: `{INPUT.relative_to(ROOT)}`",
        f"- Input row count: {len(rows):,}",
        f"- Artifact candidates found: {len(candidates):,}",
        f"- Auto-remove candidates: {action_counts.get('remove_artifact', 0):,}",
        f"- Manual-review candidates: {action_counts.get('manual_review', 0):,}",
        "",
        "## Artifact Types",
        "",
        "| artifact_type | rows |",
        "| --- | ---: |",
    ]
    for key, value in type_counts.items():
        lines.append(f"| {key} | {value:,} |")
    lines += [
        "",
        "## Rules",
        "",
        "- Standalone UI strings such as `Tap to load preview` are marked `remove_artifact`.",
        "- UI phrases embedded inside longer SMS-like rows are marked `manual_review` and are not auto-removed.",
        "",
        "## Files Generated",
        "",
        f"- `{OUT.relative_to(ROOT)}`",
        f"- `{REPORT.relative_to(ROOT)}`",
        "",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"input file path: {INPUT.relative_to(ROOT)}")
    print(f"input row count: {len(rows)}")
    print(f"artifact candidates found: {len(candidates)}")
    print(f"auto-remove artifact candidates: {action_counts.get('remove_artifact', 0)}")
    print(f"manual review artifacts count: {action_counts.get('manual_review', 0)}")
    print(f"output file: {OUT.relative_to(ROOT)}")
    print(f"report file: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
