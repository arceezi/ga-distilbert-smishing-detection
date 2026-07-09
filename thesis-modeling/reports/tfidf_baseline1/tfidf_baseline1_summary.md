# tfidf_baseline1 Summary

- Training split: train_clean.csv only.
- Validation split: val_clean.csv for reporting only; no threshold tuning.
- Test splits: test_clean, test_adv_10, test_adv_20, test_adv_30 for final evaluation only.
- Logistic Regression class_weight: `None`.
- TF-IDF: word n-grams (1,2), char n-grams (3,5), lowercase, sublinear TF, min_df=2, max_df=0.95.

## Mean/Std Metrics

| model           | split       |   accuracy_mean |   accuracy_std |   precision_smishing_mean |   precision_smishing_std |   recall_smishing_mean |   recall_smishing_std |   f1_smishing_mean |   f1_smishing_std |   false_negative_rate_mean |   false_negative_rate_std |   false_positive_rate_mean |   false_positive_rate_std |
|:----------------|:------------|----------------:|---------------:|--------------------------:|-------------------------:|-----------------------:|----------------------:|-------------------:|------------------:|---------------------------:|--------------------------:|---------------------------:|--------------------------:|
| tfidf_baseline1 | test_adv_10 |        0.945638 |              0 |                  0.984869 |                        0 |               0.905183 |                     0 |           0.943347 |                 0 |                  0.0948167 |                         0 |                  0.0139064 |                         0 |
| tfidf_baseline1 | test_adv_20 |        0.934893 |              0 |                  0.984507 |                        0 |               0.883692 |                     0 |           0.931379 |                 0 |                  0.116308  |                         0 |                  0.0139064 |                         0 |
| tfidf_baseline1 | test_adv_30 |        0.91909  |              0 |                  0.983942 |                        0 |               0.852086 |                     0 |           0.913279 |                 0 |                  0.147914  |                         0 |                  0.0139064 |                         0 |
| tfidf_baseline1 | test_clean  |        0.97914  |              0 |                  0.985897 |                        0 |               0.972187 |                     0 |           0.978994 |                 0 |                  0.0278129 |                         0 |                  0.0139064 |                         0 |

## Degradation

| model           |   clean_recall |   adv10_recall |   adv20_recall |   adv30_recall |   clean_f1 |   adv10_f1 |   adv20_f1 |   adv30_f1 |   clean_fnr |   adv30_fnr |   clean_to_adv30_recall_drop |   clean_to_adv30_f1_drop |   clean_to_adv30_fnr_increase |
|:----------------|---------------:|---------------:|---------------:|---------------:|-----------:|-----------:|-----------:|-----------:|------------:|------------:|-----------------------------:|-------------------------:|------------------------------:|
| tfidf_baseline1 |       0.972187 |       0.905183 |       0.883692 |       0.852086 |   0.978994 |   0.943347 |   0.931379 |   0.913279 |   0.0278129 |    0.147914 |                     0.120101 |                0.0657151 |                      0.120101 |
