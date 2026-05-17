# DistilBERT Baselines Summary

- Device: `cuda` on Google Colab T4
- Model family: `distilbert-base-cased`
- Seeds: `42, 7, 123`
- Metrics file: `results/metrics/distilbert_baselines_full_metrics.csv`

## Mean Metrics by Model and Condition

| model | condition | accuracy_mean | precision_mean | recall_mean | f1_mean | fnr_mean | fpr_mean |
|---|---|---:|---:|---:|---:|---:|---:|
| ablation_b_augmented | adv_10 | 0.9901 | 0.9854 | 0.9949 | 0.9901 | 0.0051 | 0.0147 |
| ablation_b_augmented | adv_20 | 0.9899 | 0.9854 | 0.9945 | 0.9899 | 0.0055 | 0.0147 |
| ablation_b_augmented | adv_30 | 0.9909 | 0.9854 | 0.9966 | 0.9910 | 0.0034 | 0.0147 |
| ablation_b_augmented | clean | 0.9848 | 0.9852 | 0.9844 | 0.9848 | 0.0156 | 0.0147 |
| baseline2_clean | adv_10 | 0.9766 | 0.9804 | 0.9726 | 0.9765 | 0.0274 | 0.0194 |
| baseline2_clean | adv_20 | 0.9669 | 0.9801 | 0.9532 | 0.9664 | 0.0468 | 0.0194 |
| baseline2_clean | adv_30 | 0.9640 | 0.9799 | 0.9473 | 0.9633 | 0.0527 | 0.0194 |
| baseline2_clean | clean | 0.9817 | 0.9807 | 0.9827 | 0.9817 | 0.0173 | 0.0194 |

## Per-Seed F1 and Error Rates

| model | seed | condition | accuracy | precision | recall | f1 | fnr | fpr |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| ablation_b_augmented | 7 | adv_10 | 0.9899 | 0.9887 | 0.9912 | 0.9899 | 0.0088 | 0.0114 |
| ablation_b_augmented | 7 | adv_20 | 0.9912 | 0.9887 | 0.9937 | 0.9912 | 0.0063 | 0.0114 |
| ablation_b_augmented | 7 | adv_30 | 0.9912 | 0.9887 | 0.9937 | 0.9912 | 0.0063 | 0.0114 |
| ablation_b_augmented | 7 | clean | 0.9861 | 0.9886 | 0.9836 | 0.9861 | 0.0164 | 0.0114 |
| ablation_b_augmented | 42 | adv_10 | 0.9918 | 0.9863 | 0.9975 | 0.9918 | 0.0025 | 0.0139 |
| ablation_b_augmented | 42 | adv_20 | 0.9912 | 0.9862 | 0.9962 | 0.9912 | 0.0038 | 0.0139 |
| ablation_b_augmented | 42 | adv_30 | 0.9924 | 0.9863 | 0.9987 | 0.9925 | 0.0013 | 0.0139 |
| ablation_b_augmented | 42 | clean | 0.9855 | 0.9861 | 0.9848 | 0.9855 | 0.0152 | 0.0139 |
| ablation_b_augmented | 123 | adv_10 | 0.9886 | 0.9813 | 0.9962 | 0.9887 | 0.0038 | 0.0190 |
| ablation_b_augmented | 123 | adv_20 | 0.9874 | 0.9813 | 0.9937 | 0.9874 | 0.0063 | 0.0190 |
| ablation_b_augmented | 123 | adv_30 | 0.9893 | 0.9813 | 0.9975 | 0.9893 | 0.0025 | 0.0190 |
| ablation_b_augmented | 123 | clean | 0.9829 | 0.9811 | 0.9848 | 0.9830 | 0.0152 | 0.0190 |
| baseline2_clean | 7 | adv_10 | 0.9791 | 0.9785 | 0.9798 | 0.9792 | 0.0202 | 0.0215 |
| baseline2_clean | 7 | adv_20 | 0.9716 | 0.9782 | 0.9646 | 0.9714 | 0.0354 | 0.0215 |
| baseline2_clean | 7 | adv_30 | 0.9665 | 0.9780 | 0.9545 | 0.9661 | 0.0455 | 0.0215 |
| baseline2_clean | 7 | clean | 0.9836 | 0.9787 | 0.9886 | 0.9836 | 0.0114 | 0.0215 |
| baseline2_clean | 42 | adv_10 | 0.9671 | 0.9780 | 0.9558 | 0.9668 | 0.0442 | 0.0215 |
| baseline2_clean | 42 | adv_20 | 0.9583 | 0.9776 | 0.9381 | 0.9574 | 0.0619 | 0.0215 |
| baseline2_clean | 42 | adv_30 | 0.9551 | 0.9775 | 0.9317 | 0.9540 | 0.0683 | 0.0215 |
| baseline2_clean | 42 | clean | 0.9747 | 0.9783 | 0.9709 | 0.9746 | 0.0291 | 0.0215 |
| baseline2_clean | 123 | adv_10 | 0.9836 | 0.9848 | 0.9823 | 0.9835 | 0.0177 | 0.0152 |
| baseline2_clean | 123 | adv_20 | 0.9709 | 0.9844 | 0.9570 | 0.9705 | 0.0430 | 0.0152 |
| baseline2_clean | 123 | adv_30 | 0.9703 | 0.9844 | 0.9558 | 0.9699 | 0.0442 | 0.0152 |
| baseline2_clean | 123 | clean | 0.9867 | 0.9849 | 0.9886 | 0.9868 | 0.0114 | 0.0152 |
