# distilbert_ablation_b Summary

- Training data: augmented_training/train_augmented_for_ablation_b.csv only.
- Validation data: val_clean.csv only for validation/early stopping.
- Test data: held out for final evaluation only.
- Architecture: AutoModelForSequenceClassification(num_labels=2), equivalent binary classification using smishing as positive class probability.
- Class weights are used in CrossEntropyLoss; clean training is balanced, while augmented training may be smishing-heavy.

## Mean/Std Metrics

| model                 | split       |   accuracy_mean |   accuracy_std |   precision_smishing_mean |   precision_smishing_std |   recall_smishing_mean |   recall_smishing_std |   f1_smishing_mean |   f1_smishing_std |   false_negative_rate_mean |   false_negative_rate_std |   false_positive_rate_mean |   false_positive_rate_std |
|:----------------------|:------------|----------------:|---------------:|--------------------------:|-------------------------:|-----------------------:|----------------------:|-------------------:|------------------:|---------------------------:|--------------------------:|---------------------------:|--------------------------:|
| distilbert_ablation_b | test_adv_10 |        0.988622 |    0.00167241  |                  0.983337 |               0.00306098 |               0.9941   |            0.00386226 |           0.988683 |       0.00166965  |                 0.00589971 |                0.00386226 |                  0.0168563 |                0.00318156 |
| distilbert_ablation_b | test_adv_20 |        0.989254 |    0.000632111 |                  0.983357 |               0.00305597 |               0.995365 |            0.00193113 |           0.98932  |       0.000601333 |                 0.00463548 |                0.00193113 |                  0.0168563 |                0.00318156 |
| distilbert_ablation_b | test_adv_30 |        0.990097 |    0.000729899 |                  0.983385 |               0.00305359 |               0.99705  |            0.00193113 |           0.990166 |       0.000702684 |                 0.00294985 |                0.00193113 |                  0.0168563 |                0.00318156 |
| distilbert_ablation_b | test_clean  |        0.984197 |    0.00109485  |                  0.983189 |               0.00309285 |               0.985251 |            0.00193113 |           0.984215 |       0.00107206  |                 0.0147493  |                0.00193113 |                  0.0168563 |                0.00318156 |

## Degradation

| model                 |   clean_recall |   adv10_recall |   adv20_recall |   adv30_recall |   clean_f1 |   adv10_f1 |   adv20_f1 |   adv30_f1 |   clean_fnr |   adv30_fnr |   clean_to_adv30_recall_drop |   clean_to_adv30_f1_drop |   clean_to_adv30_fnr_increase |
|:----------------------|---------------:|---------------:|---------------:|---------------:|-----------:|-----------:|-----------:|-----------:|------------:|------------:|-----------------------------:|-------------------------:|------------------------------:|
| distilbert_ablation_b |       0.985251 |         0.9941 |       0.995365 |        0.99705 |   0.984215 |   0.988683 |    0.98932 |   0.990166 |   0.0147493 |  0.00294985 |                   -0.0117994 |              -0.00595146 |                    -0.0117994 |
