# Smishing Source Hunt

This folder is a research and data-acquisition workspace for finding additional smishing SMS messages for the thesis dataset. It is not a web app.

The immediate research need is to move the dataset toward a roughly balanced binary classification setup:

- ham / legitimate SMS: about 5,000 messages
- smishing SMS: about 5,000 messages

The current thesis sources provide fewer verified smishing messages than needed, so this workspace prioritizes finding already-labeled public smishing, phishing SMS, or scam SMS datasets before collecting individual examples manually.

## What This Workspace Does

- Search for public labeled smishing or SMS phishing datasets.
- Evaluate whether datasets are usable for thesis integration.
- Preserve original labels and document mappings to thesis labels.
- Track source URLs, file formats, license notes, and overlap risks.
- Collect candidate messages only when dataset sources are not enough.
- Clean, redact, validate, deduplicate, and approve messages.
- Export approved smishing messages for later integration with the main thesis dataset.

## Main Workflow

1. Search for already-labeled datasets.
2. Log each dataset or source in `DATASET_SEARCH_LOG.md` and `SOURCE_LOG.md`.
3. Add dataset metadata to `data/external_datasets/dataset_inventory.csv`.
4. Import safe public candidate rows into `data/raw/collected_smishing_candidates.csv`.
5. Run cleaning and redaction.
6. Validate schema and source traceability.
7. Deduplicate exact and near-duplicate messages.
8. Manually review only unclear cases.
9. Export approved smishing rows to `data/final/approved_smishing_messages.csv`.

## Key Files

- `AGENTS.md`: instructions for future Codex sessions.
- `PROJECT_CONTEXT.md`: thesis context and dataset target.
- `docs/ACTIVE_OUTPUTS.md`: current files to use for thesis experiments and review.
- `docs/DATASET_PIPELINE_OVERVIEW.md`: ordered dataset-building pipeline.
- `docs/ARCHIVE_POLICY.md`: archive and provenance rules.
- `DATA_COLLECTION_PLAN.md`: practical acquisition workflow.
- `LABELING_GUIDE.md`: thesis label definitions.
- `ETHICS_AND_PRIVACY.md`: collection and redaction rules.
- `DEDUPLICATION_RULES.md`: duplicate handling rules.
- `SEARCH_QUERIES.md`: reusable search query bank.
- `scripts/`: standard-library Python helper scripts.

## Current Organized Outputs

The thesis-friendly organized structure is copy-based. Legacy folders are retained for script compatibility and should be treated as superseded when an equivalent active file exists under `data/05_final_datasets/active/`, `data/04_expert_review_iaa/active_packet/`, or `data/02_manual_ham/cleaned/`.

Main expanded dataset:

`data/05_final_datasets/active/final_v3_research_synthetic_balanced_10544.csv`

Real-only baseline:

`data/05_final_datasets/active/baseline_v1_public_real_only_balanced_9908.csv`

Expert review packet:

`data/04_expert_review_iaa/active_packet/expert_review_packet_500_balanced_raw_complete.xlsx`

Manual ham:

`data/02_manual_ham/cleaned/approved_manual_ham_cleaned_320.csv`

Use `manifests/file_move_manifest.csv` and `manifests/active_dataset_manifest.csv` for provenance.
