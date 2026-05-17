# Overall Performance Analysis for Assigned Models

## 1. Executive Summary

Among the assigned models, TF-IDF Logistic Regression performed best overall. It achieved the strongest clean-test results and retained the strongest adversarial performance across the evaluated perturbation levels. On the clean test set, TF-IDF reached accuracy 0.981, smishing recall 0.973, and smishing F1 0.981. Under the strongest adversarial condition, `test_adv_30`, TF-IDF still retained smishing recall 0.904 and smishing F1 0.944.

Ablation C and Ablation D performed similarly to each other and did not outperform TF-IDF. Ablation D was slightly higher than Ablation C on several clean and adversarial metrics, but the difference was small and both remained below TF-IDF by a clear margin. These results indicate that, for the assigned models currently available, the unweighted TF-IDF Logistic Regression baseline is the strongest performer.

## 2. Model Definitions

- **TF-IDF Logistic Regression** is **Baseline 1**, implemented as unweighted TF-IDF with Logistic Regression.
- **Ablation C** is Frozen DistilBERT plus engineered features with uniform weights, where all eight engineered feature-group weights are fixed equally.
- **Ablation D** is Frozen DistilBERT plus engineered features with random weights sampled from `Uniform(0, 2)`, averaged over seeds 42, 7, and 123.
- **Smishing** is the positive class, represented by `label_id = 1`. Precision, recall, F1, false negative rate, and false positive rate are interpreted with smishing as the positive class.

## 3. Clean Test Performance

On `test_clean`, TF-IDF had the highest clean performance among the assigned models. It achieved accuracy 0.981, precision_smishing 0.988, recall_smishing 0.973, f1_smishing 0.981, FNR 0.027, and FPR 0.011.

Ablation C reached accuracy 0.930, recall_smishing 0.924, f1_smishing 0.929, and FNR 0.076. Ablation D reached accuracy 0.934, recall_smishing 0.926, f1_smishing 0.934, and FNR 0.074. Although Ablation D slightly exceeded Ablation C on clean recall and F1, neither ablation matched the TF-IDF baseline.

## 4. Adversarial Robustness Performance

Across `test_adv_10`, `test_adv_20`, and `test_adv_30`, all three models showed declining smishing recall and F1 as perturbation strength increased. This pattern is expected because stronger surface perturbations make smishing messages harder to detect while preserving their labels.

TF-IDF retained the best adversarial performance at every perturbation level. Its smishing recall declined from 0.930 at `test_adv_10` to 0.922 at `test_adv_20` and 0.904 at `test_adv_30`. Its smishing F1 similarly declined from 0.958 to 0.954 and then 0.944.

Ablation C declined from recall 0.893 at `test_adv_10` to 0.865 at `test_adv_30`. Ablation D declined from recall 0.892 at `test_adv_10` to 0.861 at `test_adv_30`. TF-IDF therefore retains the best performance under adversarial perturbation among the assigned models.

## 5. False Negative Analysis

False negative rate is especially important for this thesis because a false negative means a smishing message is missed and classified as benign. In operational smishing detection, this failure mode is risky because the user may receive no warning before interacting with a fraudulent link, verification request, payment prompt, or credential-harvesting message.

TF-IDF has the lowest FNR among the three assigned models on every evaluated split. On `test_clean`, TF-IDF's FNR is 0.027, compared with 0.076 for Ablation C and 0.074 for Ablation D. Under `test_adv_30`, TF-IDF's FNR rises to 0.096, but remains lower than Ablation C at 0.135 and Ablation D at 0.139. This makes TF-IDF the safest of the assigned models with respect to missed smishing messages.

## 6. Ablation C vs Ablation D Interpretation

Ablation C and Ablation D are close across the clean and adversarial test sets. Ablation D, which uses random engineered-feature weights averaged over seeds 42, 7, and 123, slightly outperforms Ablation C on clean recall and F1 and is marginally stronger on several adversarial metrics. However, the differences are small, and random weighting does not provide a clear or principled advantage over uniform weighting.

This comparison supports the need to evaluate both ablations later against the proposed GA-optimized model. Since uniform and random weights perform similarly, the central question is whether GA-optimized weights can produce a meaningful improvement beyond naive engineered-feature weighting strategies.

## 7. Thesis-Ready Discussion Paragraph

The partial experimental results for the assigned models show that Baseline 1, the unweighted TF-IDF Logistic Regression model, achieved the strongest performance across both clean and adversarial test conditions. On the clean test set, the TF-IDF baseline produced the highest accuracy, smishing recall, and smishing F1, while also maintaining the lowest false negative rate. As adversarial perturbation increased from 10% to 30%, all models exhibited degradation in recall and F1, indicating that surface-level obfuscation reduced detection effectiveness. However, the TF-IDF baseline retained the strongest robustness among the evaluated models. Ablation C and Ablation D produced similar results, suggesting that random engineered-feature weighting does not offer a clear advantage over uniform weighting in the absence of optimization. These findings should be interpreted as preliminary and partial because they include only TF-IDF, Ablation C, and Ablation D, rather than the complete seven-model comparison specified in the thesis methodology.

## 8. Summary Table

| model | clean_recall | adv_10_recall | adv_20_recall | adv_30_recall | clean_fnr | adv_30_fnr |
| --- | --- | --- | --- | --- | --- | --- |
| TF-IDF Logistic Regression | 0.973 | 0.930 | 0.922 | 0.904 | 0.027 | 0.096 |
| Ablation C | 0.924 | 0.893 | 0.879 | 0.865 | 0.076 | 0.135 |
| Ablation D | 0.926 | 0.892 | 0.879 | 0.861 | 0.074 | 0.139 |

## Source Files

This report uses only existing output files and does not recompute metrics or modify dataset files. Source files read: `results/final_comparison_table_clean.csv`, `reports/final_comparison_summary_clean.md`, `reports/tfidf_logreg_summary.md`, `reports/ablation_c_summary.md`, and `reports/ablation_d_summary.md`.
