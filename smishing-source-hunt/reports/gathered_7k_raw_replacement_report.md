# Gathered 7k Raw Replacement Report

## 1. Purpose

This workflow tries to make the final thesis candidate dataset compatible with paired raw and cleaned text. It classifies raw availability in the 91k candidate pool, recovers exact raw versions where possible, replaces unrecoverable redacted-only gathered rows with separate raw-available smishing candidates, and archives any row that cannot be used without inventing raw text.

## 2. Starting Point

- Gathered 7k total rows: 7,000
- Gathered raw available: 967
- Gathered redacted-only needing recovery/replacement: 6,033

## 3. 91k Candidate Pool Summary

- Total candidate rows: 91,142
- Smishing-labeled rows: 91,142
- Candidate rows with original-looking raw text: 73,833
- Candidate rows already redacted: 16,852
- Candidate rows rejected/not usable: 457

### Top Dataset Names

| dataset_name | rows |
| --- | --- |
| wspr-ncsu/sms-phishing | 68029 |
| reportsmishing/Smishing-Dataset-IMC25 | 22078 |
| shariul-islam/bengali-sms-smishing-dataset | 776 |
| yizhu-joy/SmishX | 259 |

### Top Source Names

| source_name | rows |
| --- | --- |
| SMS Phishing Dataset | 68029 |
| Smishing-Dataset-IMC25 | 22078 |
| Bengali SMS Smishing Dataset | 776 |
| SmishX | 259 |

### Scam Categories

| scam_category | rows |
| --- | --- |
| other | 69065 |
| banking | 10495 |
| others | 4586 |
| government | 1922 |
| delivery | 1676 |
| telecom | 1630 |
| spam | 1387 |
| wrong number | 304 |
| hey mum/dad | 77 |

### Languages

| language | rows |
| --- | --- |
| unknown | 68029 |
| English | 23113 |

## 4. Recovery Results

- Recovered same-message raw count: 6
- Replaced with different raw-available candidate count: 6,027
- Removed due to no raw available count: 0
- Excluded exact duplicate raw-available gathered rows archived: 711
- Skipped duplicate count: 29,849
- Skipped low-confidence count: 17,057
- Skipped label-conflict count: 277

## 5. Final Raw-Required Dataset Count

- Total rows: 12,281
- Ham count: 4,959
- Smishing count: 7,322
- Spam/review count retained in raw-required file: 0
- Rows with raw_text_available=True: 12,281
- Redacted-only text remaining: 0

### Validation

| check | status | details |
| --- | --- | --- |
| No raw_text_available=False rows | PASS | 0 |
| No already_redacted rows | PASS | 0 |
| No empty message_raw | PASS | 0 |
| No empty message_clean | PASS | 0 |
| No obvious placeholders remain in message_raw | PASS | flagged=0 |
| message_clean privacy-safe artifacts | PASS | flagged=0 |
| Excluded rows archived | PASS | archived=711 |
| Final report written | PASS | reports\gathered_7k_raw_replacement_report.md |

## 6. Thesis Methodology Note

Rows were included in the raw-required dataset only when an original-looking raw message was available. Redacted-only rows were not de-redacted or reconstructed. When a redacted gathered smishing row could not be linked to a raw version, it was either replaced by a separate raw-available smishing candidate from the 91k source pool or excluded from the raw-required dataset. All replacements preserve source traceability and are deduplicated against existing public sources.

## 7. Files Generated

- `data\organized\raw_recovery\gathered_7k_raw_recovered_or_replaced.csv`
- `data\organized\raw_recovery\gathered_7k_redacted_removed_archive.csv`
- `data\organized\raw_recovery\replacement_match_log.csv`
- `data\organized\raw_recovery\combined_public_thesis_sources_deduped_raw_required.csv`
- `reports\gathered_7k_raw_replacement_report.md`

## 8. Recommended Next Step

Build model-ready datasets from this audit output as separate, explicitly named artifacts: a real raw-required balanced dataset, a cleaned-text version derived only from the raw-required rows, and an optional redacted-only sensitivity dataset kept separate from the main thesis dataset.
