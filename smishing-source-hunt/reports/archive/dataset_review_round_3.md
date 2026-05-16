# Dataset Review Round 3

Date: 2026-05-07

## Goal

Expand the strict-clean approved smishing set from 3,300 to 7,000 rows and create a separate unredacted raw export from locally stored `message_raw`.

## Rules Applied

- Kept the round 2 strict English/readability approval gates.
- Approved only additional IMC25 candidates in this pass.
- Kept Bengali and NCSU as unapproved reserve sources.
- Raw export uses local `message_raw` exactly as stored; it does not re-fetch sources, rewrite URLs, defang indicators, or restore source-level placeholders.

## Results

| Step | Count |
|---|---:|
| Previous strict-clean approved rows | 3,300 |
| New IMC25 rows reviewed for surplus approval | 6,065 |
| New strict-clean IMC25 approvals | 3,700 |
| Additional rows held as `needs_review` | 2,365 |
| Final approved smishing rows | 7,000 |
| Remaining approved English-safety failures | 0 |
| Remaining approved readability failures | 0 |

## Current Approved Source Mix

| Source | Approved Rows |
|---|---:|
| Smishing-Dataset-IMC25 | 6,869 |
| SmishX | 131 |

## Export Files

| File | Purpose |
|---|---|
| `data/final/approved_smishing_messages.csv` | Canonical redacted approved export, refreshed to 7,000 rows. |
| `data/final/approved_smishing_messages_round3_7k_clean.csv` | Round-specific redacted 7k export. |
| `data/final/approved_smishing_messages_unredacted_raw.csv` | Raw approved export with `approved_message_raw` copied from local `message_raw`. |

## Raw Export Caveat

The raw export may contain live scam URLs, phone numbers, account-like numbers, OTP-like values, or other source indicators where they were preserved locally. Some source datasets already store placeholders such as `<URL>` or `<PHONE_NUMBER>` in `message_raw`; those placeholders were not reconstructed in this pass.

Raw export quick counts:

| Raw Property | Rows |
|---|---:|
| Rows with apparent live URL text in `message_raw` | 265 |
| Rows with source/local placeholders in `message_raw` | 5,125 |
| Rows with digits in `message_raw` | 2,769 |

## QA Artifacts

| File | Purpose |
|---|---|
| `data/review_batches/round3_imc25_new_approvals.csv` | All 3,700 newly approved IMC25 rows. |
| `data/review_batches/round3_final_approved_spot_sample.csv` | 100-row spot sample from the final approved pool. |
| `data/review_batches/round3_unredacted_raw_spot_sample.csv` | 100-row spot sample including `approved_message_raw`. |

## Validation

- `scripts/validate_schema.py data/interim/deduplicated_candidates.csv`: passed.
- `scripts/validate_schema.py data/final/approved_smishing_messages.csv`: passed.
- `scripts/validate_schema.py data/final/approved_smishing_messages_round3_7k_clean.csv`: passed.
- `scripts/validate_schema.py data/final/approved_smishing_messages_unredacted_raw.csv`: passed.
- `scripts/check_final_content.py --input data/final/approved_smishing_messages.csv`: passed with 7,000 rows.
- `scripts/check_final_content.py --input data/final/approved_smishing_messages_unredacted_raw.csv --check-raw`: passed with 7,000 rows.
