"""Apply conservative source-aware review decisions to deduplicated candidates."""

from __future__ import annotations

import argparse
import csv
from collections import Counter
from datetime import date
from pathlib import Path

from review_rules import review_row, template_signature, normalized_message


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data" / "interim" / "deduplicated_candidates.csv"
ROUND1_TAG = "round1_source_triage"
ROUND2_TAG = "round2_english_readability_cleanup"


def append_note(existing: str, note: str) -> str:
    existing = (existing or "").strip()
    if note in existing:
        return existing
    if not existing:
        return note
    return f"{existing} | {note}"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source")
    parser.add_argument("--limit-approvals", type=int)
    parser.add_argument("--target-total-approved", type=int)
    parser.add_argument("--max-per-template", type=int, default=1)
    parser.add_argument("--audit-approved", action="store_true")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--round-tag")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    if not args.source and not args.audit_approved:
        raise SystemExit("--source is required unless --audit-approved is used")

    with args.input.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = [dict(row) for row in reader]

    current_approved_total = sum(
        1
        for row in rows
        if (row.get("label") or "").strip() == "smishing"
        and (row.get("review_status") or "").strip() == "approved"
    )
    approved_count = 0
    downgraded_count = 0
    reviewed_count = 0
    decisions: Counter[str] = Counter()
    template_approvals: Counter[str] = Counter()

    for row in rows:
        if args.source and (row.get("source_name") or "").strip() != args.source:
            continue
        current_status = (row.get("review_status") or "").strip()
        if args.audit_approved:
            if current_status != "approved":
                continue
        elif current_status != "candidate":
            continue

        decision = review_row(row)
        status = decision.status
        signature = template_signature(normalized_message(row))

        if args.audit_approved:
            if status == "approved":
                reason = decision.reason
            else:
                status = "needs_review"
                reason = f"Removed from approved set by strict English/readability cleanup; {decision.reason}"
                downgraded_count += 1
        elif status == "approved":
            if args.limit_approvals is not None and approved_count >= args.limit_approvals:
                break
            if (
                args.target_total_approved is not None
                and current_approved_total + approved_count >= args.target_total_approved
            ):
                break
            if signature and template_approvals[signature] >= args.max_per_template:
                status = "needs_review"
                reason = "Likely near-duplicate/campaign repetition; representative approved first."
            else:
                approved_count += 1
                if signature:
                    template_approvals[signature] += 1
                reason = decision.reason
        else:
            reason = decision.reason

        reviewed_count += 1
        decisions[status] += 1

        if args.apply:
            if args.audit_approved and status == "approved":
                continue
            row["review_status"] = status
            row["label"] = decision.label if status != "approved" else "smishing"
            if status == "approved" and not row.get("scam_category"):
                row["scam_category"] = "other"
            round_tag = args.round_tag or (ROUND2_TAG if args.audit_approved or args.target_total_approved else ROUND1_TAG)
            note = f"{round_tag} {date.today().isoformat()}: {status}; {reason} confidence={decision.confidence}"
            row["reviewer_notes"] = append_note(row.get("reviewer_notes", ""), note)
            if status == "needs_review" and "near-duplicate" in reason.lower():
                row["duplicate_status"] = "near_duplicate"

    print(f"Source: {args.source or 'all'}")
    print(f"Mode: {'audit-approved' if args.audit_approved else 'candidate-triage'}")
    print(f"Reviewed rows: {reviewed_count}")
    print(f"Approved rows: {approved_count}")
    print(f"Downgraded approved rows: {downgraded_count}")
    for status, count in decisions.most_common():
        print(f"{status}: {count}")

    if args.apply:
        with args.output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Updated {args.output}")
    else:
        print("Dry run only. Add --apply to update the CSV.")


if __name__ == "__main__":
    main()
