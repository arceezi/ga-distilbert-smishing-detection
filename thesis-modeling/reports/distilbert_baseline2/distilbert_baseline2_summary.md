# distilbert_baseline2 Summary

- Training data: clean/train_clean.csv only.
- Validation data: val_clean.csv only for validation/early stopping.
- Test data: held out for final evaluation only.
- Architecture: AutoModelForSequenceClassification(num_labels=2), equivalent binary classification using smishing as positive class probability.
- Class weights are used in CrossEntropyLoss; clean training is balanced, while augmented training may be smishing-heavy.

## Mean/Std Metrics

| model                | split       |   accuracy_mean |   accuracy_std |   precision_smishing_mean |   precision_smishing_std |   recall_smishing_mean |   recall_smishing_std |   f1_smishing_mean |   f1_smishing_std |   false_negative_rate_mean |   false_negative_rate_std |   false_positive_rate_mean |   false_positive_rate_std |
|:---------------------|:------------|----------------:|---------------:|--------------------------:|-------------------------:|-----------------------:|----------------------:|-------------------:|------------------:|---------------------------:|--------------------------:|---------------------------:|--------------------------:|
| distilbert_baseline2 | test_adv_10 |        0.980194 |     0.00587331 |                  0.983463 |               0.00105652 |               0.976823 |            0.0129132  |           0.980098 |       0.00605637  |                  0.0231774 |                0.0129132  |                  0.0164349 |                0.00126422 |
| distilbert_baseline2 | test_adv_20 |        0.969659 |     0.0021897  |                  0.9831   |               0.0011924  |               0.955752 |            0.00551062 |           0.969226 |       0.00232763  |                  0.0442478 |                0.00551062 |                  0.0164349 |                0.00126422 |
| distilbert_baseline2 | test_adv_30 |        0.969448 |     0.00597448 |                  0.983098 |               0.00106233 |               0.955331 |            0.0131584  |           0.96898  |       0.00630633  |                  0.0446692 |                0.0131584  |                  0.0164349 |                0.00126422 |
| distilbert_baseline2 | test_clean  |        0.985251 |     0.00036495 |                  0.983623 |               0.00120864 |               0.986936 |            0.00193113 |           0.985275 |       0.000386224 |                  0.0130636 |                0.00193113 |                  0.0164349 |                0.00126422 |

## Degradation

| model                |   clean_recall |   adv10_recall |   adv20_recall |   adv30_recall |   clean_f1 |   adv10_f1 |   adv20_f1 |   adv30_f1 |   clean_fnr |   adv30_fnr |   clean_to_adv30_recall_drop |   clean_to_adv30_f1_drop |   clean_to_adv30_fnr_increase |
|:---------------------|---------------:|---------------:|---------------:|---------------:|-----------:|-----------:|-----------:|-----------:|------------:|------------:|-----------------------------:|-------------------------:|------------------------------:|
| distilbert_baseline2 |       0.986936 |       0.976823 |       0.955752 |       0.955331 |   0.985275 |   0.980098 |   0.969226 |    0.96898 |   0.0130636 |   0.0446692 |                    0.0316056 |                0.0162953 |                     0.0316056 |
