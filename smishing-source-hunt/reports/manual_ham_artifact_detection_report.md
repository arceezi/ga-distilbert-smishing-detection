# Manual Ham Artifact Detection Report

- Input file: `data\manual_ham_drive\final\approved_manual_ham_merged.csv`
- Input row count: 326
- Artifact candidates found: 27
- Auto-remove candidates: 6
- Manual-review candidates: 21

## Artifact Types

| artifact_type | rows |
| --- | ---: |
| ui_preview_artifact | 6 |
| embedded_ui_preview_text | 21 |

## Rules

- Standalone UI strings such as `Tap to load preview` are marked `remove_artifact`.
- UI phrases embedded inside longer SMS-like rows are marked `manual_review` and are not auto-removed.

## Files Generated

- `data\manual_ham_drive\final\manual_ham_artifact_candidates.csv`
- `reports\manual_ham_artifact_detection_report.md`
