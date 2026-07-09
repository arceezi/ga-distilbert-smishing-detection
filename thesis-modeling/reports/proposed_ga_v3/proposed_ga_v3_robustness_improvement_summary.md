# Proposed GA v3 Robustness Improvement Summary

V3 keeps the same core thesis architecture but improves the optimization procedure.

- GA fitness became threshold-aware using: `0.30*mean_recall + 0.30*mean_f1 + 0.20*min_recall - 0.10*max_fnr - 0.05*mean_fpr - 0.05*robustness_gap - 0.05*weight_extremeness_penalty`.
- Threshold tuning used: `0.30*mean_recall + 0.35*mean_f1 - 0.15*mean_fnr - 0.20*mean_fpr - 0.05*robustness_gap`.
- Preferred threshold rule: choose the best score with mean FPR <= 0.12; otherwise use the unconstrained best score.
- GA weight-selection threshold: 0.35.
- Final Phase C per-seed thresholds were tuned after final training on validation splits only.

```
 seed  threshold  threshold_score  mean_recall  min_recall  mean_f1  mean_fnr  max_fnr  mean_fpr  robustness_gap                             selection_rule  fpr_constraint_satisfied
   42       0.25         0.578159     0.955752    0.911504 0.924595  0.044248 0.088496  0.111252        0.065740 best threshold_score with mean_fpr <= 0.12                      True
    7       0.25         0.577702     0.949747    0.896334 0.926495  0.050253 0.103666  0.099874        0.079646 best threshold_score with mean_fpr <= 0.12                      True
  123       0.25         0.577383     0.950063    0.895070 0.926078  0.049937 0.104930  0.101138        0.080910 best threshold_score with mean_fpr <= 0.12                      True
```

- GA-stage FPR constraint satisfied: True.
- Selected feature branch scale: 2.0.
- Scale selection rule: highest mean seed fitness, then lower std seed fitness, lower mean FPR, higher best validation fitness.
- Selected weights came from: best_seed_weights.

The target is not necessarily to beat a fully fine-tuned DistilBERT model trained with adversarial augmentation. The Proposed GA target is to improve interpretability, reduce false negatives versus C/D when possible, control false positives more defensibly than v2 threshold behavior, and maintain low clean-to-adversarial degradation.
