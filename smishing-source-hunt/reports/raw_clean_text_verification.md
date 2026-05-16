# Raw/Clean Text Verification Report

## 1. Purpose

This workflow separates the best available source message text from a privacy-normalized modeling version. `message_raw` preserves the original source text when it is available, while `message_clean` standardizes placeholders and redacts obvious URLs, emails, phone-like values, OTP/code values, references, accounts, and amounts without removing scam cues such as urgency, brand names, banking terms, and delivery terms.

## 2. Source Summary Table

| source_name | rows | raw_text_available_true | raw_text_available_false | original_unredacted_count | already_redacted_count | source_archive_missing_count | row_match_failed_count | redaction_detected_in_raw_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UCI SMS Spam Collection | 5574 | 5570 | 4 | 5570 | 4 | 0 | 0 | 4 |
| Mishra & Soni | 5971 | 5969 | 2 | 5969 | 2 | 0 | 0 | 2 |
| SmishTank | 1062 | 1062 | 0 | 1062 | 0 | 0 | 0 | 0 |
| Gathered approved smishing 7k | 7000 | 967 | 6033 | 967 | 6033 | 0 | 0 | 6033 |

## 3. Gathered 7k Finding

The gathered approved smishing 7k source is mixed: 967 rows use available original-looking raw text and 6,033 rows already contain placeholder tokens. Placeholder rows are not de-redacted.

## 4. UCI/Mishra/SmishTank Finding

- UCI SMS Spam Collection: 5,570 original/unredacted rows; 4 already-redacted rows.
- Mishra & Soni: 5,969 original/unredacted rows; 2 already-redacted rows.
- SmishTank: 1,062 original/unredacted rows; 0 already-redacted rows.

## 5. Cleaning Rules Used

- Standardized placeholder variants such as `<PHONE_NUMBER>`, `<MOBILE>`, `<LINK>`, `[URL]`, `<ACCOUNT_NUMBER>`, `<REFERENCE_NUMBER>`, and contextual `<CODE>`.
- Replaced URLs with `<URL>` and email addresses with `<EMAIL>`.
- Replaced phone-like values with `<PHONE>`.
- Replaced OTP/code-like values with `<OTP>` only near OTP, verification, login, security, PIN, passcode, or code context.
- Replaced account/card-like long numbers with `<ACCT>` and reference/tracking/order-like long numbers with `<REF_NUM>` when context is present.
- Replaced money amounts with `<AMOUNT>` and normalized whitespace/punctuation spacing.

## 6. Validation Results

| check | status | details |
| --- | --- | --- |
| UCI SMS Spam Collection row count | PASS | expected=5574; actual=5574 |
| Mishra & Soni row count | PASS | expected=5971; actual=5971 |
| SmishTank row count | PASS | expected=1062; actual=1062 |
| Gathered approved smishing 7k row count | PASS | expected=7000; actual=7000 |
| Combined raw total | PASS | expected=19607; actual=19607 |
| Deduped representative count unchanged | PASS | expected_current=13712; actual=13712 |
| Every row has message_clean | PASS | empty=0 |
| Every row has message_raw or failure status | PASS | empty_raw=0 |
| Flag raw equals clean while unredacted | PASS | flagged=9584 |
| Flag placeholders detected in raw | PASS | flagged=6039 |
| Flag obvious raw URLs/phones/emails in clean | PASS | flagged=0 |

### Counts By Raw Text Status

| source_name | raw_text_status | rows |
| --- | --- | --- |
| UCI SMS Spam Collection | already_redacted | 4 |
| UCI SMS Spam Collection | original_unredacted | 5570 |
| Mishra & Soni | already_redacted | 2 |
| Mishra & Soni | original_unredacted | 5969 |
| SmishTank | original_unredacted | 1062 |
| Gathered approved smishing 7k | already_redacted | 6033 |
| Gathered approved smishing 7k | original_unredacted | 967 |

### Counts By Cleaning Status

| source_name | cleaning_status | rows |
| --- | --- | --- |
| UCI SMS Spam Collection | cleaned_from_already_redacted | 4 |
| UCI SMS Spam Collection | cleaned_from_raw | 5570 |
| Mishra & Soni | cleaned_from_already_redacted | 2 |
| Mishra & Soni | cleaned_from_raw | 5969 |
| SmishTank | cleaned_from_raw | 1062 |
| Gathered approved smishing 7k | cleaned_from_already_redacted | 6033 |
| Gathered approved smishing 7k | cleaned_from_raw | 967 |

- Combined rows: 19,607
- Deduped representative rows: 13,712
- Rows where raw text was found in source archives: 13,568
- Rows where raw text is unavailable: 6,039
- Rows already redacted: 6,039

Duplicate cluster fields were preserved from the existing uniform catalogs. They were not recomputed from `message_clean`, so representative selection remains comparable to the current deduped file.

## 7. Files Generated

- `data\organized\text_verified\uci_sms_spam_collection_text_verified.csv`
- `data\organized\text_verified\mishra_soni_sms_dataset_text_verified.csv`
- `data\organized\text_verified\smishtank_text_verified.csv`
- `data\organized\text_verified\gathered_approved_smishing_7k_text_verified.csv`
- `data\organized\text_verified\combined_public_thesis_sources_text_verified.csv`
- `data\organized\text_verified\combined_public_thesis_sources_deduped_representatives_text_verified.csv`
- `data\organized\text_verified\raw_clean_text_verification_summary.csv`
- `reports\raw_clean_text_verification.md`

## 8. Recommended Next Step

Model-ready dataset building should use `message_raw` when evaluating real-world raw-message performance, or `message_clean` when evaluating privacy-normalized or placeholder-normalized performance. The choice should be consistent across train/test splits and explicitly reported in the thesis methodology.
