# Dataset Pipeline Overview

This workspace preserves the full thesis dataset-building trail while making the active outputs easier to find. The organized folders are compatibility copies unless a future run intentionally uses `--move`.

## Pipeline Stages

1. Raw public/source gathering
   - Collect public SMS spam, phishing, smishing, and gathered candidate sources.
   - Organized under `data/00_raw_sources/`.

2. Public source standardization
   - Convert public sources into the shared thesis schema.
   - Organized under `data/01_working/public_source_organization/`.

3. Duplicate/overlap audit
   - Identify exact and near overlap across public sources.
   - Retain audit files for source traceability.

4. Raw/clean text verification
   - Verify availability and quality of raw and cleaned message text.
   - Organized under `data/01_working/raw_text_verification/`.

5. Redacted raw recovery/replacement
   - Recover or replace redacted gathered smishing rows when defensible.
   - Organized under `data/01_working/raw_recovery/`.

6. Strict raw quality validation
   - Audit placeholders, long messages, and raw SMS-likeness.
   - Organized under `data/01_working/raw_quality/`.

7. Smishing content quality filtering
   - Remove or replace obvious non-smishing and weak content rows.
   - Organized under `data/01_working/content_quality/`.

8. Strong campaign-family deduplication
   - Reduce large repeated campaign families while preserving representative examples.
   - Active public master: `data/05_final_datasets/active/public_master_campaign_family_filtered_10226.csv`.

9. Manual ham extraction/review
   - Import Google Drive/manual ham exports, create review workbooks, and validate approved ham.
   - Organized under `data/02_manual_ham/`.

10. Manual ham split/artifact cleanup
    - Merge split SMS rows and archive OCR/UI artifacts.
    - Active cleaned source: `data/02_manual_ham/cleaned/approved_manual_ham_cleaned_320.csv`.

11. Research-backed synthetic ham generation
    - Build template families from defensible research-backed service-message types.
    - Organized under `data/03_synthetic_ham/`.

12. Final dataset builds
    - Build balanced real-only, public-plus-manual, and research-backed synthetic-expanded datasets.
    - Active final outputs are under `data/05_final_datasets/active/`.

13. Expert review / IAA packet construction
    - Build a raw-complete 500-row expert review packet and supporting pools.
    - Active packet is under `data/04_expert_review_iaa/active_packet/`.

## Compatibility Note

Legacy locations such as `data/organized/`, `data/final_dataset_build/`, `data/manual_ham_drive/`, and `data/expert_review_iaa/` remain in place so existing scripts continue to work. Use `manifests/file_move_manifest.csv` for provenance between legacy and organized paths.
