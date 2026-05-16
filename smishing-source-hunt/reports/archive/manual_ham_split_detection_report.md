# Manual Ham Split Detection Report

- Input file: `data\manual_ham_drive\extracted\manual_ham_review.csv`
- Original row count: 331
- Split candidates found: 12
- High-confidence auto-merge candidates: 5
- Review-only candidates: 7

## Detection Rules

- Sequential rows are checked for incomplete endings, continuation starts, short fragments, and shared source context.
- The GigaPoints promo/purchase Smart App split has a specific high-confidence rule.
- Rows below the confidence threshold are not exported as merge candidates.

## Files Generated

- `data\manual_ham_drive\extracted\manual_ham_split_candidates.csv`
- `reports\manual_ham_split_detection_report.md`
