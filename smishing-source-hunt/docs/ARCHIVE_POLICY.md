# Archive Policy

Archive files are retained for traceability, reproducibility, and thesis audit support.

## Rules

- Do not delete archive files until the thesis is complete.
- Do not rebuild the final dataset from archive files unless intentionally reproducing a specific stage.
- Do not treat archive files as active training inputs unless the relevant pipeline stage is being rerun intentionally.
- Use `manifests/file_move_manifest.csv` to trace where copied or organized files came from.
- Use `manifests/pipeline_stage_manifest.csv` to identify which stage produced each organized output.

## Active Versus Archive

Active files live in:

- `data/05_final_datasets/active/`
- `data/04_expert_review_iaa/active_packet/`
- `data/02_manual_ham/cleaned/`

Archive and superseded files live in:

- `data/99_archive/`
- `data/02_manual_ham/archives/`
- `data/03_synthetic_ham/archives/`
- `data/04_expert_review_iaa/archives/`
- `reports/archive/`
- `prompts/archive/`

Legacy source folders are kept for compatibility. Their contents are not deleted by the organization script.
