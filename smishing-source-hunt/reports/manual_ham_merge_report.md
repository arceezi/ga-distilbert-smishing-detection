# Manual Ham Merge Report

- Input file: `data\manual_ham_drive\extracted\manual_ham_review.csv`
- Original row count: 331
- Split candidates read: 12
- High-confidence merge groups applied: 5
- Source rows involved in applied merges: 10
- Continuation rows merged into representatives: 5
- Continuation rows removed from final: 5
- Final approved manual ham count: 326

## Validation

- empty_message_raw: 0
- empty_message_clean: 0
- non_ham_final_label: 0
- not_approved_review_status: 0
- purchase_continuation_rows: 0

## Merge Status Counts

| merge_status | rows |
| --- | ---: |
| not_merged | 321 |
| merged_representative | 5 |

## Files Generated

- `data\manual_ham_drive\final\approved_manual_ham_merged.csv`
- `data\manual_ham_drive\final\manual_ham_merge_log.csv`
- `data\manual_ham_drive\final\manual_ham_rows_removed_by_merge.csv`
- `reports\manual_ham_merge_report.md`
