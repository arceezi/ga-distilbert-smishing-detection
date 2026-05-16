# CSV Schema

This schema is used for candidate, cleaned, deduplicated, rejected, and final smishing message files.

## Main Candidate Columns

| Column | Description |
|---|---|
| id | Stable row identifier. |
| message_raw | Source text as stored by the workflow. For manual Google Drive ham, this is raw OCR extracted text from `raw_extracted_dataset.csv` when available. |
| message_clean | Cleaned/normalized message text derived from the curated cleaned source; placeholders may be present when the source applied redactions. |
| raw_text_available | `true`/`false`; manual Google Drive ham rows are `true` when matched raw OCR extracted text is available. |
| text_privacy_status | Example: `raw_ocr_extracted_text`, `redacted`, `not_needed`, `needs_review`. |
| label | Thesis workspace label: `smishing`, `ham`, `reject`, or `unsure`. |
| original_label | Label exactly as provided by the source dataset. |
| label_mapping_notes | Notes explaining how original labels map to thesis labels. |
| source_name | Dataset/source name. Required if `source_url` is empty. |
| source_url | Source URL. Required if `source_name` is empty. |
| source_type | Example: `labeled_dataset`, `GitHub_dataset`, `scam_warning_page`. |
| dataset_name | Dataset name when imported from a dataset. |
| original_file_format | CSV, JSON, TXT, TSV, XLSX, HTML, PDF, etc. |
| date_collected | Date row was collected or imported. |
| scam_category | Scam category if smishing. |
| country_or_region | Country/region if relevant and known. |
| language | Expected value is usually English. |
| contains_url | `true`/`false` after inspecting available text, including `<URL>` placeholders. |
| contains_phone | `true`/`false` after inspecting available text, including `<PHONE>` placeholders. |
| contains_otp | `true`/`false` after inspecting available text, including `<OTP>` placeholders. |
| contains_account_hint | `true`/`false` after inspecting available text, including `<ACCT>` and account/card/reference patterns. |
| redaction_status | Example: `not_needed`, `redacted`, `needs_review`. |
| duplicate_status | Example: `unique`, `exact_duplicate`, `near_duplicate`, `needs_review`. |
| review_status | `candidate`, `needs_review`, `approved`, or `rejected`. |
| reviewer_notes | Human or agent review notes required for auditability and thesis defensibility. |

## Allowed Labels

- `smishing`
- `ham`
- `reject`
- `unsure`

## Allowed Review Status Values

- `candidate`
- `needs_review`
- `approved`
- `rejected`

## Allowed Scam Category Examples

- `banking`
- `ewallet`
- `delivery`
- `otp_verification`
- `account_suspension`
- `prize_reward`
- `government`
- `telecom`
- `job_offer`
- `crypto_investment`
- `other`

## Source Traceability Rule

Every row must have at least one of:

- `source_name`
- `source_url`

When importing from an already-labeled dataset, preserve `original_label` and fill `label_mapping_notes`.
