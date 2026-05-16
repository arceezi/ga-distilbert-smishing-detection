"""Apply high-confidence manual ham OCR split merges."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "manual_ham_drive" / "extracted" / "manual_ham_review.csv"
CANDIDATES = ROOT / "data" / "manual_ham_drive" / "extracted" / "manual_ham_split_candidates.csv"
OUT = ROOT / "data" / "manual_ham_drive" / "final" / "approved_manual_ham_merged.csv"
LOG_OUT = ROOT / "data" / "manual_ham_drive" / "final" / "manual_ham_merge_log.csv"
REMOVED_OUT = ROOT / "data" / "manual_ham_drive" / "final" / "manual_ham_rows_removed_by_merge.csv"
REPORT = ROOT / "reports" / "manual_ham_merge_report.md"

MERGE_ADDED = [
    "merge_status",
    "merged_from_manual_ids",
    "merged_row_count",
    "original_split_messages",
]
REMOVED_ADDED = MERGE_ADDED + ["merged_into_manual_id"]
LOG_FIELDS = [
    "merge_group_id",
    "representative_manual_id",
    "merged_from_manual_ids",
    "merged_row_count",
    "row_position_start",
    "row_position_end",
    "original_messages",
    "merged_message_raw",
    "merged_message_clean",
    "merge_confidence",
    "merge_reason",
]


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


def append_note(existing: str, note: str) -> str:
    existing = (existing or "").strip()
    if not existing:
        return note
    if note in existing:
        return existing
    return f"{existing}; {note}"


def choose_specific(first: str, second: str) -> str:
    first = first or ""
    second = second or ""
    weak = {"", "unsure", "unknown", "other"}
    if first == second:
        return first
    if first.lower() in weak and second:
        return second
    if second.lower() in weak:
        return first
    if first == "promo_legitimate" and second == "telecom":
        return "telecom"
    return first


def bool_or(a: str, b: str) -> str:
    return "True" if str(a) == "True" or str(b) == "True" else "False"


def parse_manual_ids(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split("+") if part.strip()]


def main() -> None:
    rows, fields = read_csv(INPUT)
    candidates, _ = read_csv(CANDIDATES)
    by_manual_id = {row.get("manual_id", ""): row for row in rows}

    accepted = [
        row
        for row in candidates
        if row.get("suggested_action") == "merge" and float(row.get("merge_confidence") or 0) >= 0.90
    ]
    accepted.sort(key=lambda r: int(r.get("row_position_start") or 0))

    consumed: set[str] = set()
    merge_by_rep: dict[str, dict[str, str]] = {}
    removed_ids: set[str] = set()
    logs: list[dict[str, str]] = []

    for cand in accepted:
        manual_ids = parse_manual_ids(cand.get("manual_ids", ""))
        if len(manual_ids) < 2:
            continue
        if any(mid in consumed for mid in manual_ids):
            continue
        rep_id = manual_ids[0]
        continuation_ids = manual_ids[1:]
        rep = by_manual_id.get(rep_id)
        continuations = [by_manual_id[mid] for mid in continuation_ids if mid in by_manual_id]
        if not rep or len(continuations) != len(continuation_ids):
            continue

        merged_raw_parts = [rep.get("message_raw", "").strip()] + [r.get("message_raw", "").strip() for r in continuations]
        merged_clean_parts = [rep.get("message_clean", "").strip()] + [r.get("message_clean", "").strip() for r in continuations]
        merged_raw = " ".join(part for part in merged_raw_parts if part).strip()
        merged_clean = " ".join(part for part in merged_clean_parts if part).strip()

        out = dict(rep)
        out["message_raw"] = merged_raw
        out["message_clean"] = merged_clean
        out["final_label"] = "ham"
        out["review_status"] = "approved"
        out["service_category"] = choose_specific(rep.get("service_category", ""), continuations[0].get("service_category", ""))
        out["institution_type"] = choose_specific(rep.get("institution_type", ""), continuations[0].get("institution_type", ""))
        for flag in ["contains_url", "contains_phone", "contains_otp", "contains_amount", "contains_account_hint"]:
            if flag in out:
                out[flag] = bool_or(rep.get(flag, ""), continuations[0].get(flag, ""))
        merge_note = f"Merged OCR split rows: {' + '.join(manual_ids)}"
        out["reviewer_notes"] = append_note(out.get("reviewer_notes", ""), merge_note)
        out["merge_status"] = "merged_representative"
        out["merged_from_manual_ids"] = " + ".join(manual_ids)
        out["merged_row_count"] = str(len(manual_ids))
        out["original_split_messages"] = cand.get("original_messages", "")
        merge_by_rep[rep_id] = out

        removed_ids.update(continuation_ids)
        consumed.update(manual_ids)
        logs.append(
            {
                "merge_group_id": cand.get("merge_group_id", ""),
                "representative_manual_id": rep_id,
                "merged_from_manual_ids": " + ".join(manual_ids),
                "merged_row_count": str(len(manual_ids)),
                "row_position_start": cand.get("row_position_start", ""),
                "row_position_end": cand.get("row_position_end", ""),
                "original_messages": cand.get("original_messages", ""),
                "merged_message_raw": merged_raw,
                "merged_message_clean": merged_clean,
                "merge_confidence": cand.get("merge_confidence", ""),
                "merge_reason": cand.get("merge_reason", ""),
            }
        )

    final_rows: list[dict[str, str]] = []
    removed_rows: list[dict[str, str]] = []
    for row in rows:
        manual_id = row.get("manual_id", "")
        if manual_id in merge_by_rep:
            final_rows.append(merge_by_rep[manual_id])
            continue
        if manual_id in removed_ids:
            removed = dict(row)
            removed["final_label"] = "ham"
            removed["review_status"] = "approved"
            removed["merge_status"] = "merged_continuation_removed"
            rep_id = next(
                (log["representative_manual_id"] for log in logs if manual_id in parse_manual_ids(log["merged_from_manual_ids"])),
                "",
            )
            removed["merged_into_manual_id"] = rep_id
            removed["merged_from_manual_ids"] = manual_id
            removed["merged_row_count"] = "1"
            removed["original_split_messages"] = removed.get("message_raw", "")
            removed_rows.append(removed)
            continue

        out = dict(row)
        out["final_label"] = "ham"
        out["review_status"] = "approved"
        out["merge_status"] = "not_merged"
        out["merged_from_manual_ids"] = manual_id
        out["merged_row_count"] = "1"
        out["original_split_messages"] = ""
        final_rows.append(out)

    write_csv(OUT, final_rows, fields + MERGE_ADDED)
    write_csv(LOG_OUT, logs, LOG_FIELDS)
    write_csv(REMOVED_OUT, removed_rows, fields + REMOVED_ADDED)

    validation = {
        "empty_message_raw": sum(1 for r in final_rows if not (r.get("message_raw") or "").strip()),
        "empty_message_clean": sum(1 for r in final_rows if not (r.get("message_clean") or "").strip()),
        "non_ham_final_label": sum(1 for r in final_rows if r.get("final_label") != "ham"),
        "not_approved_review_status": sum(1 for r in final_rows if r.get("review_status") != "approved"),
        "purchase_continuation_rows": sum(
            1 for r in final_rows if (r.get("message_raw") or "").strip().lower().startswith("purchase! simple. easy. smart")
        ),
    }
    merge_status_counts = Counter(r.get("merge_status", "") for r in final_rows)

    lines = [
        "# Manual Ham Merge Report",
        "",
        f"- Input file: `{INPUT.relative_to(ROOT)}`",
        f"- Original row count: {len(rows):,}",
        f"- Split candidates read: {len(candidates):,}",
        f"- High-confidence merge groups applied: {len(logs):,}",
        f"- Source rows involved in applied merges: {sum(int(log['merged_row_count']) for log in logs):,}",
        f"- Continuation rows merged into representatives: {len(removed_rows):,}",
        f"- Continuation rows removed from final: {len(removed_rows):,}",
        f"- Final approved manual ham count: {len(final_rows):,}",
        "",
        "## Validation",
        "",
    ]
    for key, value in validation.items():
        lines.append(f"- {key}: {value:,}")
    lines += [
        "",
        "## Merge Status Counts",
        "",
        "| merge_status | rows |",
        "| --- | ---: |",
    ]
    for key, value in merge_status_counts.items():
        lines.append(f"| {key} | {value:,} |")
    lines += [
        "",
        "## Files Generated",
        "",
        f"- `{OUT.relative_to(ROOT)}`",
        f"- `{LOG_OUT.relative_to(ROOT)}`",
        f"- `{REMOVED_OUT.relative_to(ROOT)}`",
        f"- `{REPORT.relative_to(ROOT)}`",
        "",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"input file path: {INPUT.relative_to(ROOT)}")
    print(f"original row count: {len(rows)}")
    print(f"split candidates found: {len(candidates)}")
    print(f"high-confidence merges applied: {len(logs)}")
    print(f"final approved manual ham row count: {len(final_rows)}")
    print(f"approved_manual_ham_merged.csv: {OUT.relative_to(ROOT)}")
    print(f"manual_ham_merge_log.csv: {LOG_OUT.relative_to(ROOT)}")
    print(f"manual_ham_rows_removed_by_merge.csv: {REMOVED_OUT.relative_to(ROOT)}")
    print(f"manual_ham_split_candidates.csv: {CANDIDATES.relative_to(ROOT)}")
    print(f"manual_ham_merge_report.md: {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
