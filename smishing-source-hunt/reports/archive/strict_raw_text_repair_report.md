# Strict Raw Text Repair Report

## 1. Purpose

This step ensures the raw-required dataset truly contains original-looking raw messages. Any source-anonymized angle-bracket token in `message_raw` is treated as not fully raw.

## 2. Starting Dataset

- Total rows: 12,281
- Ham count: 4,959
- Smishing count: 7,322

### Starting Source Counts

| source_name | rows |
| --- | --- |
| UCI SMS Spam Collection | 4497 |
| Smishing-Dataset-IMC25 | 2773 |
| SMS Phishing Dataset | 2651 |
| SmishTank | 847 |
| Bengali SMS Smishing Dataset | 666 |
| Mishra & Soni | 651 |
| SmishX | 196 |

## 3. Raw Placeholder Violations

- Total rows with placeholders or strict raw failures: 669

### Placeholder Type Counts

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

### By Source

| source_name | rows |
| --- | --- |
| Smishing-Dataset-IMC25 | 662 |
| UCI SMS Spam Collection | 4 |
| SmishTank | 3 |

### By Dataset

| dataset_name | rows |
| --- | --- |
| reportsmishing/Smishing-Dataset-IMC25 | 638 |
| Gathered approved smishing 7k | 24 |
| SMS Spam Collection v.1 | 4 |
| SmishTank Dataset / Smishing Dataset I | 3 |

### By Label

| normalized_label | rows |
| --- | --- |
| smishing | 665 |
| ham | 4 |

## 4. Repair Results

- Recovered same-message raw count: 0
- Replaced with strict raw candidate count: 665
- Removed/no strict raw available count: 355
- Ham rows removed: 5
- Smishing rows removed/replaced: removed 350; replaced 665
- Duplicates skipped: 12,708

## 5. Long Message Review

- Number of rows > 320 characters: 262
- Kept as likely SMS/multipart SMS or review-allowed SMS-like raw: 234
- Marked possible report/article text: 1
- Archived/removed due to non-SMS-like format: 4

## 6. Final Strict Raw Dataset

- Total rows: 11,926
- Ham count: 4,954
- Smishing count: 6,972
- Class ratio: 1.41:1 smishing:ham
- Row count compared to previous raw-required dataset: 11,926 vs 12,281 (-355)

### Final Source Distribution

| source_name | rows |
| --- | --- |
| UCI SMS Spam Collection | 4492 |
| SMS Phishing Dataset | 2877 |
| Smishing-Dataset-IMC25 | 2195 |
| SmishTank | 844 |
| Bengali SMS Smishing Dataset | 667 |
| Mishra & Soni | 650 |
| SmishX | 201 |

### Validation

| check | status | details |
| --- | --- | --- |
| No empty message_raw | PASS | 0 |
| No raw placeholders | PASS | 0 |
| No raw_text_available=False | PASS | 0 |
| No already_redacted status | PASS | 0 |
| All included rows pass strict raw quality | PASS | 0 |
| message_clean exists | PASS | 0 |
| No duplicate raw keys | PASS | duplicates=0 |
| No duplicate clean keys | PASS | duplicates=0 |
| No ham rows replaced with smishing | PASS | checked |
| Removed rows archived | PASS | archived=355 |

## 7. Thesis Methodology Note

Rows with anonymized or placeholder-containing raw text were not treated as fully raw. The workflow attempted to recover exact raw versions from source archives and the 91k candidate pool. When exact recovery was unavailable, smishing rows were replaced only with deduplicated raw-available smishing candidates from the same candidate pool. Rows without acceptable raw text were archived and excluded. No placeholders were reversed, reconstructed, or invented.

## 8. Files Generated

- `data\organized\raw_quality\combined_public_thesis_sources_deduped_strict_raw.csv`
- `data\organized\raw_quality\strict_raw_removed_archive.csv`
- `data\organized\raw_quality\strict_raw_replacement_log.csv`
- `reports\strict_raw_text_repair_report.md`

## 9. Recommended Next Steps

- Build the balanced model-ready dataset later from the strict raw output.
- Clean or standardize `message_clean` in a separate task.
- Add manually curated ham later if needed.
- Review the long-message audit file manually before final thesis freezing.
