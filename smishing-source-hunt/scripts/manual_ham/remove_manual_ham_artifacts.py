"""Remove clear UI/OCR artifact rows from approved manual ham."""

from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "manual_ham_drive" / "final" / "approved_manual_ham_merged.csv"
CANDIDATES = ROOT / "data" / "manual_ham_drive" / "final" / "manual_ham_artifact_candidates.csv"
OUT = ROOT / "data" / "manual_ham_drive" / "final" / "approved_manual_ham_cleaned.csv"
ARCHIVE_OUT = ROOT / "data" / "manual_ham_drive" / "final" / "manual_ham_artifact_removed_archive.csv"
REVIEW_OUT = ROOT / "data" / "manual_ham_drive" / "final" / "manual_ham_artifact_manual_review.csv"
REPORT = ROOT / "reports" / "manual_ham_artifact_cleanup_report.md"

ADDED = ["artifact_status", "artifact_notes"]
ARCHIVE_ADDED = ["artifact_flag", "artifact_type", "artifact_reason", "suggested_action", "artifact_status", "artifact_notes", "removal_reason"]
BLOCKED_EXACT_RE = re.compile(r"(?i)^\s*(?:tap\s+to\s+load\s+preview|tap\s+to\s+view|load\s+preview|tap\s+to\s+download)\.?\s*$")


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


def main() -> None:
    rows, fields = read_csv(INPUT)
    candidates, candidate_fields = read_csv(CANDIDATES)
    candidate_by_id = {row.get("manual_id", ""): row for row in candidates}
    remove_ids = {
        row.get("manual_id", "")
        for row in candidates
        if row.get("artifact_flag") == "True" and row.get("suggested_action") == "remove_artifact"
    }
    review_rows = [row for row in candidates if row.get("suggested_action") == "manual_review"]

    cleaned: list[dict[str, str]] = []
    archived: list[dict[str, str]] = []
    for row in rows:
        manual_id = row.get("manual_id", "")
        candidate = candidate_by_id.get(manual_id, {})
        if manual_id in remove_ids:
            out = dict(row)
            out["artifact_flag"] = candidate.get("artifact_flag", "True")
            out["artifact_type"] = candidate.get("artifact_type", "ui_preview_artifact")
            out["artifact_reason"] = candidate.get("artifact_reason", "")
            out["suggested_action"] = candidate.get("suggested_action", "remove_artifact")
            out["artifact_status"] = "removed_artifact"
            out["artifact_notes"] = candidate.get("artifact_reason", "")
            out["removal_reason"] = "ui_or_ocr_artifact_not_sms"
            archived.append(out)
            continue

        out = dict(row)
        out["final_label"] = "ham"
        out["review_status"] = "approved"
        if candidate.get("suggested_action") == "manual_review":
            out["artifact_status"] = "manual_review_artifact_candidate"
            out["artifact_notes"] = candidate.get("artifact_reason", "")
        else:
            out["artifact_status"] = "not_artifact"
            out["artifact_notes"] = ""
        cleaned.append(out)

    review_fields = candidate_fields if candidate_fields else fields + ARCHIVE_ADDED
    write_csv(OUT, cleaned, fields + ADDED)
    write_csv(ARCHIVE_OUT, archived, fields + ARCHIVE_ADDED)
    write_csv(REVIEW_OUT, review_rows, review_fields)

    validation = {
        "empty_message_raw": sum(1 for r in cleaned if not (r.get("message_raw") or "").strip()),
        "empty_message_clean": sum(1 for r in cleaned if not (r.get("message_clean") or "").strip()),
        "non_ham_final_label": sum(1 for r in cleaned if r.get("final_label") != "ham"),
        "not_approved_review_status": sum(1 for r in cleaned if r.get("review_status") != "approved"),
        "blocked_exact_ui_rows": sum(
            1
            for r in cleaned
            if BLOCKED_EXACT_RE.search(r.get("message_raw", "")) or BLOCKED_EXACT_RE.search(r.get("message_clean", ""))
        ),
        "missing_reviewer_notes_column": 0 if "reviewer_notes" in fields else 1,
        "missing_merge_trace_columns": 0
        if {"merge_status", "merged_from_manual_ids", "merged_row_count", "original_split_messages"}.issubset(set(fields))
        else 1,
    }
    status_counts = Counter(r.get("artifact_status", "") for r in cleaned)
    lines = [
        "# Manual Ham Artifact Cleanup Report",
        "",
        f"- Input file: `{INPUT.relative_to(ROOT)}`",
        f"- Input row count: {len(rows):,}",
        f"- Artifact candidates found: {len(candidates):,}",
        f"- Artifacts removed: {len(archived):,}",
        f"- Manual review artifacts count: {len(review_rows):,}",
        f"- Final cleaned manual ham row count: {len(cleaned):,}",
        "",
        "## Validation",
        "",
    ]
    for key, value in validation.items():
        lines.append(f"- {key}: {value:,}")
    lines += [
        "",
        "## Artifact Status Counts",
        "",
        "| artifact_status | rows |",
        "| --- | ---: |",
    ]
    for key, value in status_counts.items():
        lines.append(f"| {key} | {value:,} |")
    lines += [
        "",
        "## Files Generated",
        "",
        f"- `{OUT.relative_to(ROOT)}`",
        f"- `{ARCHIVE_OUT.relative_to(ROOT)}`",
        f"- `{REVIEW_OUT.relative_to(ROOT)}`",
        f"- `{REPORT.relative_to(ROOT)}`",
        "",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"input file path: {INPUT.relative_to(ROOT)}")
    print(f"input row count: {len(rows)}")
    print(f"artifact candidates found: {len(candidates)}")
    print(f"artifacts removed: {len(archived)}")
    print(f"manual review artifacts count: {len(review_rows)}")
    print(f"final cleaned manual ham row count: {len(cleaned)}")
    print(f"approved_manual_ham_cleaned.csv: {OUT.relative_to(ROOT)}")
    print(f"manual_ham_artifact_removed_archive.csv: {ARCHIVE_OUT.relative_to(ROOT)}")
    print(f"manual_ham_artifact_candidates.csv: {CANDIDATES.relative_to(ROOT)}")
    print(f"manual_ham_artifact_cleanup_report.md: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
