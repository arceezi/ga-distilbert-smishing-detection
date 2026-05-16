"""Standardize approved manual ham into the final dataset build schema."""

from __future__ import annotations

from final_dataset_build_utils import INTERIM_DIR, MANUAL_CLEANED, UNIFIED_COLUMNS, ensure_dirs, read_csv, write_csv


OUT_CSV = INTERIM_DIR / "manual_ham_standardized.csv"


def main() -> None:
    ensure_dirs()
    src = read_csv(MANUAL_CLEANED)
    required = {"message_raw", "message_clean", "final_label", "review_status"}
    missing = required - set(src.columns)
    if missing:
        raise SystemExit(f"Missing required manual ham columns: {sorted(missing)}")

    rows = []
    for idx, row in src.iterrows():
        raw = str(row.get("message_raw", "") or "").strip()
        clean = str(row.get("message_clean", "") or "").strip()
        cleaning_status = "manual_cleaned"
        if not clean and raw:
            clean = raw
            cleaning_status = "copied_from_raw_pending_cleaning"
        trace_bits = []
        for col in ["merge_status", "merged_from_manual_ids", "merged_row_count", "original_split_messages", "artifact_status", "artifact_notes", "text_privacy_status"]:
            if col in src.columns and str(row.get(col, "") or "").strip():
                trace_bits.append(f"{col}={row.get(col)}")
        notes = "; ".join(trace_bits)
        raw_status = str(row.get("text_privacy_status", "") or "").strip() or "manual_extracted_cleaned_or_raw"
        rows.append(
            {
                "unified_id": f"manual_ham_final_{idx + 1:06d}",
                "source_name": "manual_google_drive_ham",
                "dataset_name": "manually_curated_service_ham",
                "source_group": "manual_curated_ham",
                "source_row_id": row.get("manual_id", f"manual_source_row_{idx + 1:06d}"),
                "message_raw": raw,
                "message_clean": clean,
                "source_label": "ham",
                "normalized_label": "ham",
                "label_status": "accepted_manual_ham",
                "review_status": "approved",
                "raw_text_available": bool(raw),
                "raw_text_status": raw_status,
                "cleaning_status": cleaning_status,
                "raw_lookup_status": "manual_source_available",
                "raw_lookup_notes": "Approved cleaned manual ham from Google Drive extraction.",
                "contains_url": row.get("contains_url", ""),
                "contains_email": row.get("contains_email", False),
                "contains_phone": row.get("contains_phone", ""),
                "contains_otp": row.get("contains_otp", ""),
                "contains_amount": row.get("contains_amount", ""),
                "contains_account_hint": row.get("contains_account_hint", ""),
                "service_category": row.get("service_category", ""),
                "institution_type": row.get("institution_type", ""),
                "source_file": row.get("source_file", str(MANUAL_CLEANED)),
                "reviewer_notes": row.get("reviewer_notes", ""),
                "data_origin": "manual_real",
                "is_synthetic": False,
                "synthetic_template_id": "",
                "generation_method": "manual_curated",
                "notes": notes,
            }
        )
    out = read_csv(MANUAL_CLEANED).iloc[0:0]
    import pandas as pd

    out = pd.DataFrame(rows)
    for col in UNIFIED_COLUMNS:
        if col not in out.columns:
            out[col] = ""
    out = out[UNIFIED_COLUMNS]
    write_csv(out, OUT_CSV)
    print(f"Manual ham input rows: {len(src)}")
    print(f"Manual ham standardized rows: {len(out)}")
    print(f"Wrote: {OUT_CSV}")


if __name__ == "__main__":
    main()
