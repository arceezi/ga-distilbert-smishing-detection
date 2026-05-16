# Clean Split Report

- Split: stratified 70/15/15 by label with duplicate normalized message keys kept in the same split.
- Seed: 42

## Split Counts

| Artifact | Path | Rows | Ham | Smishing | Synthetic ham |
| --- | --- | --- | --- | --- | --- |
| train_clean | data/06_model_ready/clean/train_clean.csv | 7380 | 3690 | 3690 | 919 |
| val_clean | data/06_model_ready/clean/val_clean.csv | 1582 | 791 | 791 | 191 |
| test_clean | data/06_model_ready/clean/test_clean.csv | 1582 | 791 | 791 | 190 |

## Synthetic Ham Distribution

| Split | Synthetic ham |
| --- | --- |
| train_clean | 919 |
| val_clean | 191 |
| test_clean | 190 |

## Leakage Check

- Duplicate normalized key groups crossing splits: 0
