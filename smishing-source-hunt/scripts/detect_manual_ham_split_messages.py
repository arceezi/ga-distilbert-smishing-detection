"""Detect likely OCR/extraction split rows in manually reviewed ham."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "manual_ham_drive" / "extracted" / "manual_ham_review.csv"
OUT = ROOT / "data" / "manual_ham_drive" / "extracted" / "manual_ham_split_candidates.csv"
REPORT = ROOT / "reports" / "manual_ham_split_detection_report.md"

OUTPUT_FIELDS = [
    "merge_group_id",
    "row_position_start",
    "row_position_end",
    "manual_ids",
    "original_messages",
    "proposed_merged_message",
    "merge_confidence",
    "merge_reason",
    "suggested_action",
]

STRONG_END_RE = re.compile(r"[.!?]['\")\]]?$")
GIGAPOINTS_START_RE = re.compile(r"(?i)^you earned \d+(?:\.\d+)? gigapoints on your promo\s*$")
GIGAPOINTS_CONT_RE = re.compile(r"(?i)^purchase!\s+simple\.\s+easy\.\s+smart\.")
UNFINISHED_END_RE = re.compile(
    r"(?i)\b(?:promo|your|for|to|at|on|from|account|transaction|reference|otp|code|purchase|with|in|of|the|a|an)\s*$"
)
CONTINUATION_START_RE = re.compile(
    r"(?i)^(?:purchase|account|app|code|transaction|reference|today|tomorrow|at|for|from|to|and|or|with|in|of|the)\b"
)


def read_csv(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as h:
        reader = csv.DictReader(h)
        return list(reader), list(reader.fieldnames or [])


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as h:
        writer = csv.DictWriter(h, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def text_of(row: dict[str, str]) -> str:
    return (row.get("message_raw") or row.get("message_clean") or "").strip()


def same_context(a: dict[str, str], b: dict[str, str]) -> bool:
    if a.get("source_file") and a.get("source_file") == b.get("source_file"):
        return True
    if a.get("service_category") and a.get("service_category") == b.get("service_category"):
        return True
    return False


def is_lower_or_continuation(text: str) -> bool:
    stripped = text.strip()
    return bool(stripped) and (stripped[0].islower() or CONTINUATION_START_RE.search(stripped))


def score_pair(current: dict[str, str], nxt: dict[str, str]) -> tuple[float, str, str]:
    cur = text_of(current)
    cont = text_of(nxt)
    reasons: list[str] = []
    score = 0.0

    if GIGAPOINTS_START_RE.search(cur) and GIGAPOINTS_CONT_RE.search(cont):
        return (
            0.99,
            "specific GigaPoints promo-purchase split rule; sequential rows complete one Smart App message",
            "merge",
        )

    if not cur or not cont:
        return 0.0, "empty current or next text", "keep_separate"
    if not same_context(current, nxt):
        return 0.0, "different source/context", "keep_separate"

    if not STRONG_END_RE.search(cur):
        score += 0.22
        reasons.append("first row lacks strong sentence-ending punctuation")
    if UNFINISHED_END_RE.search(cur):
        score += 0.25
        reasons.append("first row ends with unfinished connector/domain word")
    if is_lower_or_continuation(cont):
        score += 0.25
        reasons.append("next row starts like a continuation")
    if len(cont) <= 80:
        score += 0.12
        reasons.append("next row is unusually short")
    if len(cur) <= 80:
        score += 0.08
        reasons.append("first row is short enough to be a fragment")
    if current.get("source_file") == nxt.get("source_file"):
        score += 0.08
        reasons.append("same source_file")

    if score >= 0.62:
        action = "review"
    else:
        action = "keep_separate"
    return min(score, 0.89), "; ".join(reasons) or "weak split evidence", action


def main() -> None:
    rows, _ = read_csv(INPUT)
    candidates: list[dict[str, str]] = []
    group_num = 1

    for idx in range(len(rows) - 1):
        current = rows[idx]
        nxt = rows[idx + 1]
        confidence, reason, action = score_pair(current, nxt)
        if action == "keep_separate":
            continue
        cur_text = text_of(current)
        next_text = text_of(nxt)
        candidates.append(
            {
                "merge_group_id": f"manual_ham_merge_{group_num:04d}",
                "row_position_start": str(idx + 1),
                "row_position_end": str(idx + 2),
                "manual_ids": f"{current.get('manual_id', '')} + {nxt.get('manual_id', '')}",
                "original_messages": f"{cur_text} ||| {next_text}",
                "proposed_merged_message": f"{cur_text} {next_text}".strip(),
                "merge_confidence": f"{confidence:.2f}",
                "merge_reason": reason,
                "suggested_action": action,
            }
        )
        group_num += 1

    write_csv(OUT, candidates, OUTPUT_FIELDS)

    merge_count = sum(1 for r in candidates if r["suggested_action"] == "merge")
    review_count = sum(1 for r in candidates if r["suggested_action"] == "review")
    lines = [
        "# Manual Ham Split Detection Report",
        "",
        f"- Input file: `{INPUT.relative_to(ROOT)}`",
        f"- Original row count: {len(rows):,}",
        f"- Split candidates found: {len(candidates):,}",
        f"- High-confidence auto-merge candidates: {merge_count:,}",
        f"- Review-only candidates: {review_count:,}",
        "",
        "## Detection Rules",
        "",
        "- Sequential rows are checked for incomplete endings, continuation starts, short fragments, and shared source context.",
        "- The GigaPoints promo/purchase Smart App split has a specific high-confidence rule.",
        "- Rows below the confidence threshold are not exported as merge candidates.",
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
    print(f"original row count: {len(rows)}")
    print(f"split candidates found: {len(candidates)}")
    print(f"high-confidence merge candidates: {merge_count}")
    print(f"review-only candidates: {review_count}")
    print(f"output file: {OUT.relative_to(ROOT)}")
    print(f"report file: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
