# Manual Ham Drive Workflow

## Why this workflow exists

The current public thesis dataset has only around 4,963 clean deduplicated ham messages, and the ham class is heavily dominated by UCI-style casual or personal SMS. That is a weakness for English text-only smishing detection because real smishing often imitates legitimate service messages rather than casual conversation.

This workflow adds a defensible path for importing, reviewing, and optionally augmenting legitimate service-like ham messages from a Google Drive or manual-curation source.

Target ham types include OTP and verification messages, bank transaction alerts, e-wallet notifications, delivery updates, telecom advisories, government reminders, account/security notices, payment confirmations, and appointment reminders.

## Google Drive and local import

Source Drive folder:

https://drive.google.com/drive/folders/17QPkkHmConRJY9WUEqVJXtKsgNPJLPJC

If direct Drive access is unavailable, manually export or download the files and place them under:

`data/manual_ham_drive/raw/`

If the Drive export is a `.zip`, place it under:

`data/manual_ham_drive/`

The import script extracts zip files into `data/manual_ham_drive/raw/drive_export/` and preserves the original archive. For the current thesis Drive export, `THESIS/CLEANED/cleaned_dataset.csv` is treated as the manually curated review list, and matching `record_id` values from `THESIS/TEXT EXTRACTED/raw_extracted_dataset.csv` are used for `message_raw`.

Source text note: in the active 331-row import, `message_raw` comes from the raw OCR extracted text file when a matching `record_id` exists. `message_clean` comes from the cleaned/redacted source and may preserve placeholders such as `<OTP>`, `<PHONE>`, `<URL>`, `<ACCT>`, and `<NAME>`. Do not invent or reconstruct values that are not present in the source files.

Current import rule:

- include only the structured rows from `cleaned_dataset.csv`
- stop at the end of that file, which is `331` data rows in the current archive
- do not import any `PRECLEANED` screenshot rows into the active review dataset

Known public-source branch excluded from manual ham import:

- `THESIS/CLEANED/analysisdataset (2)_cleaned.csv`
- `THESIS/TEXT EXTRACTED/analysisdataset (2)_text_extracted.csv`
- `THESIS/PRECLEANED/analysisdataset (2).csv`

That `analysisdataset` branch matches the repo's public `SmishTank` source lineage and should not be reviewed as manual ham.

Supported import files are `.csv`, `.xlsx`, and `.txt`. For this manual ham workflow, screenshots remain raw evidence only and are not added as separate review rows.

Run:

```bash
python scripts/import_manual_ham_drive.py
```

This creates:

`data/manual_ham_drive/extracted/manual_ham_extracted.csv`

Imported rows are provisional only. The script does not assume every message is ham.

Canonical active review files:

- `data/manual_ham_drive/extracted/manual_ham_extracted.csv`
- `data/manual_ham_drive/extracted/manual_ham_review.csv`
- `data/manual_ham_drive/extracted/manual_ham_review.xlsx`

If a temporary recovery export is needed because the canonical extracted file is locked by Excel or OneDrive, move that recovery file into `data/manual_ham_drive/extracted/archive/` once the canonical file is writable again.

## Review process

Create a review workbook:

```bash
python scripts/create_manual_ham_review_excel.py
```

Primary review file:

`data/manual_ham_drive/extracted/manual_ham_review.xlsx`

If `openpyxl` is unavailable, the script writes:

`data/manual_ham_drive/extracted/manual_ham_review.csv`

Reviewers should set `final_label` to `ham`, `smishing`, `spam`, `unsure`, or `reject`, and set `review_status` to `approved` only when the row is ready for downstream use.

Approve only legitimate ham rows for template extraction.

Reviewers must keep `reviewer_notes` available and use it for auditability and thesis defensibility. Notes should explain suspicious reasons, why a row is legitimate ham, why it is smishing or spam, why it is unsure/rejected, OCR or extraction issues, and duplicate or overlap observations.

Final label rules:

- `ham`: Use only if the message is clearly legitimate/non-malicious, such as OTP or verification code with no suspicious action, bank transaction alert, payment confirmation, delivery status update, telecom/service advisory, government/public service notification, appointment/reminder message, or legitimate promo without suspicious demand.
- `smishing`: Use if the message asks the user to verify/login/update account through a link, threatens account lock/suspension, asks for OTP/password/PIN/credentials, impersonates bank/e-wallet/delivery/government, uses urgent financial/security bait, or contains suspicious link/callback instruction.
- `spam`: Use if it is promotional/unwanted but not clearly phishing, including gambling/free spins/casino offers, aggressive promos, random reward offers without clear credential theft, or ads that are not clearly legitimate service messages.
- `unsure`: Use if the message is unclear, cropped, incomplete, OCR-damaged, or needs another reviewer.
- `reject`: Use if not SMS-like, non-English, too incomplete, duplicate, unsafe/private data cannot be redacted, or not useful for the thesis dataset.

Rows labeled `spam`, `smishing`, `unsure`, or `reject` must not be used for ham template extraction.

Validate the reviewed file:

```bash
python scripts/validate_manual_ham_review.py
```

Outputs:

- `data/manual_ham_drive/final/approved_manual_ham.csv`
- `data/manual_ham_drive/rejected/rejected_manual_ham.csv`
- `data/manual_ham_drive/final/manual_ham_needs_review_remaining.csv`
- `data/manual_ham_drive/final/manual_ham_smishing_found.csv`
- `data/manual_ham_drive/final/manual_ham_spam_found.csv`
- `reports/manual_ham_drive_summary.md`

Before any future merge into combined public thesis sources, check approved manual ham for public-source duplicates:

```bash
python scripts/check_manual_ham_overlap.py
```

This writes `data/manual_ham_drive/final/manual_ham_overlap_report.csv`.

## Split SMS/OCR Line Merge

OCR and spreadsheet extraction can occasionally split one SMS across multiple sequential rows. Before final approval/template extraction, run the split-message workflow:

```bash
python scripts/detect_manual_ham_split_messages.py
python scripts/fix_manual_ham_split_messages.py
```

The detector checks adjacent rows for continuation patterns, incomplete endings, shared source context, and specific known OCR splits such as Smart GigaPoints promo messages split before `purchase! Simple. Easy. Smart.`.

High-confidence split rows are merged automatically. Uncertain candidates remain in `data/manual_ham_drive/extracted/manual_ham_split_candidates.csv` for review and are not merged automatically. Original split row IDs are preserved in `merged_from_manual_ids`, `original_split_messages`, `manual_ham_merge_log.csv`, and `manual_ham_rows_removed_by_merge.csv`.

The final approved manual ham file for downstream use after this step is:

`data/manual_ham_drive/final/approved_manual_ham_merged.csv`

Final approved manual ham uses merged messages only; continuation rows removed by merge are archived rather than deleted.

## UI/OCR Artifact Cleanup

OCR or screenshot extraction may capture phone/app UI text as standalone rows. These fragments are not SMS messages and must not be used for template extraction.

Run the artifact cleanup workflow after split-message merging:

```bash
python scripts/detect_manual_ham_artifacts.py
python scripts/remove_manual_ham_artifacts.py
```

Rows like `Tap to load preview` are removed before template extraction. Removed artifacts are archived in `data/manual_ham_drive/final/manual_ham_artifact_removed_archive.csv` for traceability. Longer SMS-like rows that merely contain UI text are kept and marked for manual review rather than removed automatically.

Only this cleaned file should be used for template extraction:

`data/manual_ham_drive/final/approved_manual_ham_cleaned.csv`

## Template extraction

Template extraction is deferred for the current stage. The files and scripts remain in the repo, but they are not part of the active manual ham review flow until the manual-only set is reviewed and duplicate-checked.

Templates are extracted only from approved real manual ham:

```bash
python scripts/extract_ham_templates.py
```

Output:

`data/manual_ham_drive/templates/ham_template_patterns.csv`

Sensitive or variable values are replaced with placeholders such as `<OTP>`, `<AMOUNT>`, `<DATE_TIME>`, `<PHONE>`, `<EMAIL>`, `<URL>`, `<REF_NUM>`, `<NAME>`, `<BRAND>`, and `<LOCATION>`.

Template extraction skips approved rows whose `reviewer_notes` indicate uncertainty, suspiciousness, OCR/extraction issues, or unresolved conflicts. Useful reviewer notes are carried into the template `notes` field for traceability.

Manual ham candidates should not be assumed safe ham. Promotional, gambling, reward, urgent verification, and link-heavy rows must be reviewed carefully.

## Current next-step workflow

1. Run import/summary if needed: `python scripts/import_manual_ham_drive.py`
2. Create review Excel: `python scripts/create_manual_ham_review_excel.py`
3. Manually review all 331 rows.
4. Mark only clearly legitimate rows as `final_label=ham` and `review_status=approved`.
5. Validate reviewed workbook: `python scripts/validate_manual_ham_review.py`
6. Export `approved_manual_ham.csv`.
7. Check overlap with the existing public dataset: `python scripts/check_manual_ham_overlap.py`
8. Extract ham templates only from `approved_manual_ham.csv`: `python scripts/extract_ham_templates.py`
9. Generate synthetic ham later in a separate step.

## Synthetic generation

Generate synthetic ham candidates:

```bash
python scripts/generate_synthetic_ham.py --target-count 1000 --max-per-template 20 --seed 42
```

Output:

`data/manual_ham_drive/templates/generated_synthetic_ham.csv`

Synthetic rows default to `generated_needs_review` and `synthetic_candidate`. They are not automatically final training data.

## Exporting augmented ham resources

Create candidate and approved synthetic exports:

```bash
python scripts/export_augmented_ham.py
```

To mark all generated synthetic rows approved for a controlled experiment:

```bash
python scripts/export_augmented_ham.py --approve-all
```

Outputs:

- `data/manual_ham_drive/final/approved_synthetic_ham.csv`
- `data/manual_ham_drive/final/manual_plus_synthetic_ham_candidates.csv`

## Why synthetic ham stays separate

Synthetic ham can improve service-like coverage, but it can also change class priors, introduce template artifacts, or inflate performance if mixed into experiments without clear reporting. For thesis defensibility, every generated row carries synthetic source metadata and should be analyzed separately from real manual ham and public-source ham.

## Recommended thesis usage

Main clean experiment:

- Use real ham and real smishing only.

Expanded or augmentation experiment:

- Add approved manual ham to improve legitimate service-message coverage.
- Optionally add approved synthetic ham in a separate experiment.
- Report synthetic rows separately by count, generation method, and service category.

Do not modify or merge into existing public source deduped files yet. A later model-ready dataset builder should choose among real-only, real plus approved manual ham, and real plus approved manual plus approved synthetic ham.
