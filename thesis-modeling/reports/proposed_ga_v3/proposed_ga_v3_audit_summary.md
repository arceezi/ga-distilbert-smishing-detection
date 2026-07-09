# Proposed GA v3 Audit Summary

## Source Columns

- Features extracted from `message_raw`: True.
- Embeddings extracted from `model_text`: True.

## Dataset Use

- Phase A: train_clean only, val_clean for early stopping.
- Phase B GA: ['val_clean', 'val_adv_10', 'val_adv_20', 'val_adv_30'] only.
- Phase C: train_clean only, val_clean for early stopping.
- Threshold tuning: ['val_clean', 'val_adv_10', 'val_adv_20', 'val_adv_30'] only.
- Test evaluation: ['test_clean', 'test_adv_10', 'test_adv_20', 'test_adv_30'] only.

## Selection Decisions

- Feature branch scale selected: 2.0.
- Threshold selected: 0.35.
- Threshold FPR constraint satisfied: True.
- Weight source selected: best_seed_weights.

## Weight Stability

```
                feature     mean      std      min      max
         G1_URL_Signals 0.760425 0.050286 0.705451 0.804101
 G2_OTP_Numeric_Density 0.812495 0.189121 0.600767 0.964674
         G3_Obfuscation 1.115686 0.033306 1.078402 1.142498
 G4_Urgency_Threat_Cues 0.853225 0.075622 0.801121 0.939961
   G5_Action_Directives 0.743146 0.121720 0.628107 0.870596
     G6_Financial_Terms 1.025426 0.090117 0.921489 1.081732
G7_Auth_Secrets_Request 1.029044 0.069215 0.987574 1.108948
 G8_Brand_Impersonation 1.195216 0.196297 0.969028 1.321027
```

## Degradation Summary

```
         model seed  clean_accuracy  clean_recall  clean_f1  clean_fnr  clean_fpr  adv10_accuracy  adv10_recall  adv10_f1  adv10_fnr  adv10_fpr  adv20_accuracy  adv20_recall  adv20_f1  adv20_fnr  adv20_fpr  adv30_accuracy  adv30_recall  adv30_f1  adv30_fnr  adv30_fpr  accuracy_drop_clean_to_adv30  recall_drop  f1_drop  fnr_increase
proposed_ga_v3    7        0.931100      0.984829  0.934613   0.015171   0.122630        0.927307      0.977244  0.930765   0.022756   0.122630        0.913401      0.949431  0.916412   0.050569   0.122630        0.915929      0.954488  0.919051   0.045512   0.122630                      0.015171     0.030341 0.015563      0.030341
proposed_ga_v3   42        0.924147      0.987358  0.928656   0.012642   0.139064        0.921618      0.982301  0.926103   0.017699   0.139064        0.908344      0.955752  0.912492   0.044248   0.139064        0.909608      0.958281  0.913803   0.041719   0.139064                      0.014539     0.029077 0.014853      0.029077
proposed_ga_v3  123        0.929836      0.984829  0.933493   0.015171   0.125158        0.926043      0.977244  0.929645   0.022756   0.125158        0.912769      0.950695  0.915956   0.049305   0.125158        0.914665      0.954488  0.917933   0.045512   0.125158                      0.015171     0.030341 0.015560      0.030341
proposed_ga_v3 mean        0.928361      0.985672  0.932254   0.014328   0.128951        0.924989      0.978930  0.928837   0.021070   0.128951        0.911504      0.951960  0.914954   0.048040   0.128951        0.913401      0.955752  0.916929   0.044248   0.128951                      0.014960     0.029920 0.015325      0.029920
```

## Ablation Availability

- Ablation C metrics found: True.
- Ablation D metrics found: True.
- Proposed GA v2 metrics found: False.

## False Negative Comparison Notes

test_clean: v3 mean FN 11.33 vs Ablation C FN 44.00; v3 reduced false negatives.
test_adv_10: v3 mean FN 16.67 vs Ablation C FN 64.00; v3 reduced false negatives.
test_adv_20: v3 mean FN 38.00 vs Ablation C FN 74.00; v3 reduced false negatives.
test_adv_30: v3 mean FN 35.00 vs Ablation C FN 102.00; v3 reduced false negatives.

Ablation D: comparable FN columns unavailable.

Proposed GA v2: metrics unavailable.

Manual review should inspect false negatives, false positives, and whether any feature weight dominates too strongly.
