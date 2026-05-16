# Extracted Working Files

This folder is the active working area for manual ham review.

Canonical files:

- `manual_ham_extracted.csv`
- `manual_ham_review_fallback.csv`
- `manual_ham_review.xlsx` when `openpyxl` is available

Only the `cleaned_dataset.csv` manual-curation branch should feed these files.

Source text status:

- `message_raw` is raw OCR extracted text from `THESIS/TEXT EXTRACTED/raw_extracted_dataset.csv` when a matching `record_id` exists.
- `message_clean` is the normalized version from `THESIS/CLEANED/cleaned_dataset.csv` and may preserve placeholders such as `<OTP>`, `<PHONE>`, `<URL>`, `<ACCT>`, and `<NAME>`.
- The current 331 rows set `raw_text_available=True` and `text_privacy_status=raw_ocr_extracted_text`.
- Keep `reviewer_notes` in all review/export files for reviewer rationale, OCR/extraction issues, duplicate notes, and auditability.

Current scope:

- structured rows only
- `331` data rows from the current `cleaned_dataset.csv`
- no separate `PRECLEANED` screenshot rows in the active review dataset

Do not leave temporary preview or recovery files here long-term. Move them into `extracted/archive/` once the canonical file is writable again.
