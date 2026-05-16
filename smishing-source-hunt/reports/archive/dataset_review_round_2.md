# Dataset Review Round 2

Date: 2026-05-07

## Goal

Clean the approved smishing export so approved rows are English-only and plainly readable under a strict policy.

## Rules Added

- Approved rows must pass a stricter English gate.
- Approved rows must not contain mojibake, emoji/decorative symbols, dense alert-token formatting, or excessive punctuation/symbol density.
- Failing approved rows are moved to `needs_review`, not rejected.
- Replacement approvals are drawn from remaining IMC25 candidates only.

## Results

| Step | Count |
|---|---:|
| Previously approved rows audited | 3,300 |
| Approved rows downgraded to `needs_review` | 195 |
| Clean IMC25 replacement rows approved | 195 |
| Final strict-clean approved rows | 3,300 |
| Remaining approved English-safety failures | 0 |
| Remaining approved readability failures | 0 |

## Current Approved Source Mix

| Source | Approved Rows |
|---|---:|
| Smishing-Dataset-IMC25 | 3,169 |
| SmishX | 131 |

## QA Artifacts

| File | Purpose |
|---|---|
| `data/review_batches/round2_downgraded_approved_rows.csv` | All 195 rows removed from the approved set. |
| `data/review_batches/round2_imc25_replacement_approvals.csv` | All 195 strict-clean replacement approvals. |
| `data/review_batches/round2_final_approved_spot_sample.csv` | 100-row spot sample from the refreshed approved rows in `deduplicated_candidates.csv`. |

## Export Status

- Strict-clean export written to `data/final/approved_smishing_messages_round2_clean.csv`.
- The canonical `data/final/approved_smishing_messages.csv` could not be overwritten because it was open in Excel.
- After closing that workbook, run `python scripts/export_final.py` to refresh the canonical final filename.

## Validation

- `scripts/validate_schema.py data/interim/deduplicated_candidates.csv`: passed.
- `scripts/validate_schema.py data/final/approved_smishing_messages_round2_clean.csv`: passed.
- `scripts/check_final_content.py --input data/final/approved_smishing_messages_round2_clean.csv`: passed.
