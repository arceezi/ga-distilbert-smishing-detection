# TF-IDF Logistic Regression Audit Summary

- Did Baseline 1 use `train_clean.csv` only for training? Yes.
- Did Ablation A use `train_clean.csv` only for training? Yes.
- Was `class_weight=None` used for Baseline 1? Yes.
- Was `class_weight=balanced` used for Ablation A? Yes.
- Were test sets used only for final evaluation? Yes. Validation was reporting-only and no test threshold tuning was performed.
- How strong is clean-to-adv30 degradation? See degradation tables in `results/degradation_tables/`.
- Are there signs the high score may come from strong lexical cues? TF-IDF is lexical by design; high clean scores should be interpreted with adversarial degradation and false-negative counts.
