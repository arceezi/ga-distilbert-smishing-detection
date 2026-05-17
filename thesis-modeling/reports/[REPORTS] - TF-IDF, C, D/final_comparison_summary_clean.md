# Clean Final Comparison Summary

This presentation-ready table standardizes the available model metrics into one schema.

- TF-IDF is Baseline 1: unweighted TF-IDF with Logistic Regression.
- Ablation C is frozen DistilBERT with uniform engineered-feature weighting.
- Ablation D is frozen DistilBERT with random engineered-feature weighting.
- Smishing is the positive class (`label_id = 1`) for precision, recall, F1, false negative rate, and false positive rate.
- The final table uses mean metrics for Ablation D, averaged over seeds 42, 7, and 123.

Source metric files read without recomputing results:

- `results/tfidf_logreg_metrics.csv`
- `results/ablation_c_metrics.csv`
- `results/ablation_d_metrics.csv`

Output table: `results/final_comparison_table_clean.csv`
