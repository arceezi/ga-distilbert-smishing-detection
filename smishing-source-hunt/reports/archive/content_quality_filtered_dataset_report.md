# Content Quality Filtered Dataset Report

## 1. Purpose

This pass removes obvious non-smishing artifacts and caps repeated campaign templates to reduce memorization risk.

## 2. Starting Dataset

- Total rows: 11,926
- Ham count: 4,954
- Smishing count: 6,972

## 3. Non-Smishing Content Flags

- Obvious non-smishing count: 3
- Abusive/reply count: 3
- Report/commentary count: 0
- Possible spam-not-smishing count: 16

## 4. Campaign/Template Duplicate Analysis

- Number of campaign clusters: 6,972
- Number of repeated-template rows: 674
- Largest campaign cluster size before filtering: 140
- Number of rows excluded by campaign cap: 441
- Cap rule used: max 3 for large/medium campaigns, 1-2 for small repeated campaigns.

## 5. Replacement From 91k Pool

- Replacement candidates inspected: 91,142
- Replacements accepted: 1,179
- Replacements skipped as duplicates: 2,756
- Replacements skipped due to weak smishing signal: 2,112
- Replacements skipped due to raw quality: 18,353
- Replacements skipped due to campaign repetition: 6,720

## 6. Final Dataset

- Total rows: 11,926
- Ham count: 4,954
- Smishing count: 6,972
- Class ratio: 1.41:1 smishing:ham
- Largest remaining campaign cluster size: 1
- Number of rows remaining from original strict raw dataset: 10,747
- Number of rows replaced from 91k: 1,179

### Source Distribution

| source_name | rows |
| --- | --- |
| UCI SMS Spam Collection | 4492 |
| SMS Phishing Dataset | 3718 |
| Smishing-Dataset-IMC25 | 1551 |
| SmishTank | 753 |
| Mishra & Soni | 635 |
| Bengali SMS Smishing Dataset | 589 |
| SmishX | 188 |

### Validation

- Empty `message_raw`: 0
- Angle-bracket placeholders in `message_raw`: 0
- `raw_text_available=False`: 0
- `raw_text_status=already_redacted`: 0
- Duplicate raw keys: 0
- Duplicate clean keys: 0
- Campaign keys over cap: 0
- Obvious angry-reply patterns remaining: 0
- Smishing rows with signal score <= 0: 0
- Removed rows archived: 1,179
- Replacement log rows: 1,179

## 7. Thesis Methodology Note

After strict raw validation, an additional content-quality pass was applied to remove non-smishing artifacts such as replies to scammers, abusive responses, report/commentary text, and repeated campaign templates. Near-identical smishing templates were capped to reduce campaign memorization. Removed smishing rows were replaced only with raw-available, SMS-like, deduplicated smishing candidates from the larger acquisition pool. No synthetic smishing messages were generated.

## 8. Files Generated

- `data\organized\content_quality\combined_public_thesis_sources_content_filtered.csv`
- `data\organized\content_quality\content_removed_archive.csv`
- `data\organized\content_quality\content_replacement_log.csv`
- `reports\content_quality_filtered_dataset_report.md`

## 9. Recommended Next Step

- Build the balanced model-ready dataset later.
- Clean `message_clean` later.
- Add manual service-like ham later.
