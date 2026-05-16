# Manual Ham Artifact Cleanup Report

- Input file: `data\manual_ham_drive\final\approved_manual_ham_merged.csv`
- Input row count: 326
- Artifact candidates found: 27
- Artifacts removed: 6
- Manual review artifacts count: 21
- Final cleaned manual ham row count: 320

## Validation

- empty_message_raw: 0
- empty_message_clean: 0
- non_ham_final_label: 0
- not_approved_review_status: 0
- blocked_exact_ui_rows: 0
- missing_reviewer_notes_column: 0
- missing_merge_trace_columns: 0

## Artifact Status Counts

| artifact_status | rows |
| --- | ---: |
| not_artifact | 299 |
| manual_review_artifact_candidate | 21 |

## Files Generated

- `data\manual_ham_drive\final\approved_manual_ham_cleaned.csv`
- `data\manual_ham_drive\final\manual_ham_artifact_removed_archive.csv`
- `data\manual_ham_drive\final\manual_ham_artifact_manual_review.csv`
- `reports\manual_ham_artifact_cleanup_report.md`
