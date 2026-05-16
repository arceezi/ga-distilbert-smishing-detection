"""Archive manual ham rows that overlap with the current public master dataset."""

from __future__ import annotations

from collections import Counter

import pandas as pd

from final_dataset_build_utils import (
    ARCHIVES_DIR,
    INTERIM_DIR,
    PUBLIC_DATASET,
    REPORTS_DIR,
    ensure_dirs,
    normalize_for_overlap,
    read_csv,
    write_csv,
)


MANUAL_IN = INTERIM_DIR / "manual_ham_standardized.csv"
NO_OVERLAP_OUT = INTERIM_DIR / "manual_ham_no_overlap.csv"
ARCHIVE_OUT = ARCHIVES_DIR / "manual_ham_overlap_archive.csv"
REPORT_OUT = REPORTS_DIR / "manual_ham_overlap_report.md"


def add_keys(df: pd.DataFrame, prefix: str) -> pd.DataFrame:
    out = df.copy()
    out[f"{prefix}_raw_key"] = out["message_raw"].map(normalize_for_overlap)
    out[f"{prefix}_clean_key"] = out["message_clean"].map(normalize_for_overlap)
    return out


def main() -> None:
    ensure_dirs()
    public = add_keys(read_csv(PUBLIC_DATASET), "public")
    manual = add_keys(read_csv(MANUAL_IN), "manual")

    key_to_public: dict[str, list[dict[str, str]]] = {}
    for _, row in public.iterrows():
        for key_col in ["public_raw_key", "public_clean_key"]:
            key = row.get(key_col, "")
            if key:
                key_to_public.setdefault(key, []).append(row.to_dict())

    kept = []
    archived = []
    reason_counts = Counter()
    for _, row in manual.iterrows():
        matches = []
        for match_type, key in [("exact_normalized_raw", row["manual_raw_key"]), ("exact_normalized_clean", row["manual_clean_key"])]:
            if key:
                for match in key_to_public.get(key, []):
                    matches.append((match_type, match))
        if not matches:
            kept.append(row.drop(labels=["manual_raw_key", "manual_clean_key"]).to_dict())
            continue
        labels = {m[1].get("normalized_label", "") for m in matches}
        if "smishing" in labels:
            archive_reason = "conflict_needs_review_public_smishing_overlap"
        else:
            archive_reason = "duplicate_public_ham_overlap"
        reason_counts[archive_reason] += 1
        first_type, first = matches[0]
        item = row.drop(labels=["manual_raw_key", "manual_clean_key"]).to_dict()
        item.update(
            {
                "overlap_archive_reason": archive_reason,
                "matched_public_unified_id": first.get("unified_id", ""),
                "matched_public_label": first.get("normalized_label", ""),
                "matched_public_source_name": first.get("source_name", ""),
                "match_type": first_type,
                "near_duplicate_check": "not_run_optional_dependency_not_required",
            }
        )
        archived.append(item)

    kept_df = pd.DataFrame(kept)
    arch_df = pd.DataFrame(archived)
    write_csv(kept_df, NO_OVERLAP_OUT)
    write_csv(arch_df, ARCHIVE_OUT)

    lines = [
        "# Manual Ham Overlap Report",
        "",
        f"- Public dataset input count: {len(public)}",
        f"- Manual ham input count: {len(manual)}",
        f"- Non-overlap count: {len(kept_df)}",
        f"- Overlap with ham count: {reason_counts['duplicate_public_ham_overlap']}",
        f"- Overlap with smishing count: {reason_counts['conflict_needs_review_public_smishing_overlap']}",
        f"- Archived count: {len(arch_df)}",
        "",
        "Near-duplicate matching was left as a documented extension point; this script performs exact normalized raw and clean matching.",
    ]
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Manual ham input rows: {len(manual)}")
    print(f"Manual ham overlap count: {len(arch_df)}")
    print(f"Manual ham included rows: {len(kept_df)}")
    print(f"Wrote: {NO_OVERLAP_OUT}")
    print(f"Archived: {ARCHIVE_OUT}")
    print(f"Report: {REPORT_OUT}")


if __name__ == "__main__":
    main()
