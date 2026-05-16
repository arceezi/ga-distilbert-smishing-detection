# Model-Ready Dataset Manifest

## Main Clean Dataset

- The clean dataset remains the primary final dataset and stays balanced.
- Augmented training, adversarial validation, and adversarial test artifacts are separate files.

## Artifact Summary

| Artifact | Path | Rows | Ham | Smishing | Purpose |
| --- | --- | --- | --- | --- | --- |
| final_clean_dataset | data/06_model_ready/clean/final_clean_dataset.csv | 10544 | 5272 | 5272 | Balanced clean English SMS binary master dataset |
| train_clean | data/06_model_ready/clean/train_clean.csv | 7380 | 3690 | 3690 | Clean training |
| val_clean | data/06_model_ready/clean/val_clean.csv | 1582 | 791 | 791 | Clean validation |
| test_clean | data/06_model_ready/clean/test_clean.csv | 1582 | 791 | 791 | Clean final test |
| train_augmented_for_ablation_b | data/06_model_ready/augmented_training/train_augmented_for_ablation_b.csv | 9580 | 3690 | 5890 | Ablation B only |
| val_adv_10 | data/06_model_ready/adversarial_validation/val_adv_10.csv | 1582 | 791 | 791 | GA fitness evaluation |
| val_adv_20 | data/06_model_ready/adversarial_validation/val_adv_20.csv | 1582 | 791 | 791 | GA fitness evaluation |
| test_adv_10 | data/06_model_ready/adversarial_test/test_adv_10.csv | 1582 | 791 | 791 | Final robustness evaluation |
| test_adv_20 | data/06_model_ready/adversarial_test/test_adv_20.csv | 1582 | 791 | 791 | Final robustness evaluation |
| test_adv_30 | data/06_model_ready/adversarial_test/test_adv_30.csv | 1582 | 791 | 791 | Final robustness evaluation |

## Model Usage Table

| Model | Training file | Validation file | GA fitness file | Final evaluation files |
| --- | --- | --- | --- | --- |
| Baseline 1 TF-IDF Logistic Regression | train_clean.csv | val_clean.csv | N/A | test_clean.csv, test_adv_10/20/30.csv |
| Ablation A TF-IDF class-weighted | train_clean.csv | val_clean.csv | N/A | test_clean.csv, test_adv_10/20/30.csv |
| Baseline 2 Fine-tuned DistilBERT | train_clean.csv | val_clean.csv | N/A | test_clean.csv, test_adv_10/20/30.csv |
| Ablation B Fine-tuned DistilBERT with adversarial augmentation | train_augmented_for_ablation_b.csv | val_clean.csv | N/A | test_clean.csv, test_adv_10/20/30.csv |
| Proposed GA model | Phase A train_clean.csv; Phase C train_clean.csv | val_clean.csv | val_clean.csv + val_adv_10.csv + val_adv_20.csv | test_clean.csv + test_adv_10/20/30.csv |
| Ablation C Frozen DistilBERT with uniform weights | train_clean.csv | val_clean.csv | N/A | test_clean.csv, test_adv_10/20/30.csv |
| Ablation D Frozen DistilBERT with random weights | train_clean.csv | val_clean.csv | N/A | test_clean.csv, test_adv_10/20/30.csv |

## Reports

| Report | Path |
| --- | --- |
| Final clean dataset report | data/06_model_ready/reports/final_clean_dataset_report.md |
| Split report | data/06_model_ready/reports/split_report.md |
| Augmentation report | data/06_model_ready/reports/augmentation_report.md |
| Adversarial validation report | data/06_model_ready/reports/adversarial_validation_report.md |
| Adversarial test report | data/06_model_ready/reports/adversarial_test_report.md |
| Leakage validation report | data/06_model_ready/reports/leakage_validation_report.md |
