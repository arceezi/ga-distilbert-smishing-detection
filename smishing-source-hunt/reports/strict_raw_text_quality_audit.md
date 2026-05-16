# Strict Raw Text Quality Audit

## Purpose

This audit checks whether `message_raw` in the raw-required dataset is truly original-looking. Any angle-bracket entity placeholder is treated as source-anonymized raw text and is not acceptable for the strict raw dataset.

## Summary

| metric | value |
| --- | --- |
| rows_inspected | 12281 |
| placeholder_violation_rows | 669 |
| long_message_rows | 262 |
| ham_rows | 4959 |
| smishing_rows | 7322 |

## Raw Quality Status Counts

| raw_quality_status | rows |
| --- | --- |
| pass_raw | 6706 |
| review_sms_likeness | 4675 |
| fail_placeholder_anonymized | 665 |
| review_too_long | 231 |
| fail_too_short | 4 |

## Placeholder Types

| placeholder_type | rows |
| --- | --- |
| US_DRIVER_LICENSE | 195 |
| LOCATION | 190 |
| US_BANK_NUMBER | 125 |
| EMAIL_ADDRESS | 96 |
| NRP | 69 |
| IP_ADDRESS | 46 |
| UK_NHS | 35 |
| US_PASSPORT | 7 |
| MEDICAL_LICENSE | 3 |
| US_SSN | 3 |
| ATTENTION | 2 |
| CRYPTO | 2 |
| BANK OF AMERICA MSG 088 | 1 |
| SCAM ALERT | 1 |
| ROAD-LINK | 1 |
| MISTAKE | 1 |
| LKT-NOTICE | 1 |

## Violations By Source

| source_name | rows |
| --- | --- |
| Smishing-Dataset-IMC25 | 662 |
| UCI SMS Spam Collection | 4 |
| SmishTank | 3 |

## Violations By Dataset

| dataset_name | rows |
| --- | --- |
| reportsmishing/Smishing-Dataset-IMC25 | 638 |
| Gathered approved smishing 7k | 24 |
| SMS Spam Collection v.1 | 4 |
| SmishTank Dataset / Smishing Dataset I | 3 |

## Violations By Label

| normalized_label | rows |
| --- | --- |
| smishing | 665 |
| ham | 4 |

## Long Message Review

- Rows longer than 320 characters: 262
- Possible report/article text: 1
- Likely SMS or multipart SMS: 228

## Files Generated

- `data\organized\raw_quality\raw_placeholder_violations.csv`
- `data\organized\raw_quality\raw_long_message_review.csv`
- `data\organized\raw_quality\raw_quality_audit_summary.csv`
- `reports\strict_raw_text_quality_audit.md`
