# Proposed GA v3 Final Summary

Proposed GA v3 trained final linear heads across seeds [42, 7, 123]. Mean and standard deviation metrics are saved in `results/metrics/proposed_ga_v3_metrics_mean_std.csv`.

## Mean/Std Metrics

```
         model       split  num_seeds  accuracy_mean  accuracy_std  precision_smishing_mean  precision_smishing_std  recall_smishing_mean  recall_smishing_std  f1_smishing_mean  f1_smishing_std  false_negative_rate_mean  false_negative_rate_std  false_positive_rate_mean  false_positive_rate_std    tp_mean   tp_std  tn_mean   tn_std  fp_mean   fp_std   fn_mean   fn_std  support_ham_mean  support_ham_std  support_smishing_mean  support_smishing_std  threshold_mean  threshold_std
proposed_ga_v3 test_adv_10          3       0.924989      0.002439                 0.883653                0.005485              0.978930             0.002384          0.928837         0.001987                  0.021070                 0.002384                  0.128951                 0.007226 774.333333 1.885618    689.0 5.715476    102.0 5.715476 16.666667 1.885618             791.0              0.0                  791.0                   0.0            0.25            0.0
proposed_ga_v3 test_adv_20          3       0.911504      0.002250                 0.880753                0.005554              0.951960             0.002731          0.914954         0.001750                  0.048040                 0.002731                  0.128951                 0.007226 753.000000 2.160247    689.0 5.715476    102.0 5.715476 38.000000 2.160247             791.0              0.0                  791.0                   0.0            0.25            0.0
proposed_ga_v3 test_adv_30          3       0.913401      0.002731                 0.881166                0.005646              0.955752             0.001788          0.916929         0.002257                  0.044248                 0.001788                  0.128951                 0.007226 756.000000 1.414214    689.0 5.715476    102.0 5.715476 35.000000 1.414214             791.0              0.0                  791.0                   0.0            0.25            0.0
proposed_ga_v3  test_clean          3       0.928361      0.003024                 0.884352                0.005583              0.985672             0.001192          0.932254         0.002585                  0.014328                 0.001192                  0.128951                 0.007226 779.666667 0.942809    689.0 5.715476    102.0 5.715476 11.333333 0.942809             791.0              0.0                  791.0                   0.0            0.25            0.0
```

## Degradation

```
         model seed  clean_accuracy  clean_recall  clean_f1  clean_fnr  clean_fpr  adv10_accuracy  adv10_recall  adv10_f1  adv10_fnr  adv10_fpr  adv20_accuracy  adv20_recall  adv20_f1  adv20_fnr  adv20_fpr  adv30_accuracy  adv30_recall  adv30_f1  adv30_fnr  adv30_fpr  accuracy_drop_clean_to_adv30  recall_drop  f1_drop  fnr_increase
proposed_ga_v3    7        0.931100      0.984829  0.934613   0.015171   0.122630        0.927307      0.977244  0.930765   0.022756   0.122630        0.913401      0.949431  0.916412   0.050569   0.122630        0.915929      0.954488  0.919051   0.045512   0.122630                      0.015171     0.030341 0.015563      0.030341
proposed_ga_v3   42        0.924147      0.987358  0.928656   0.012642   0.139064        0.921618      0.982301  0.926103   0.017699   0.139064        0.908344      0.955752  0.912492   0.044248   0.139064        0.909608      0.958281  0.913803   0.041719   0.139064                      0.014539     0.029077 0.014853      0.029077
proposed_ga_v3  123        0.929836      0.984829  0.933493   0.015171   0.125158        0.926043      0.977244  0.929645   0.022756   0.125158        0.912769      0.950695  0.915956   0.049305   0.125158        0.914665      0.954488  0.917933   0.045512   0.125158                      0.015171     0.030341 0.015560      0.030341
proposed_ga_v3 mean        0.928361      0.985672  0.932254   0.014328   0.128951        0.924989      0.978930  0.928837   0.021070   0.128951        0.911504      0.951960  0.914954   0.048040   0.128951        0.913401      0.955752  0.916929   0.044248   0.128951                      0.014960     0.029920 0.015325      0.029920
```

The GA-stage selected threshold was 0.35. Final Phase C used per-seed thresholds tuned after final training on validation splits only. The selected feature branch scale was 2.0. The selected global G1-G8 weights came from `best_seed_weights`.

## Comparison Notes

test_clean: v3 mean FN 11.33 vs Ablation C FN 44.00; v3 reduced false negatives.
test_adv_10: v3 mean FN 16.67 vs Ablation C FN 64.00; v3 reduced false negatives.
test_adv_20: v3 mean FN 38.00 vs Ablation C FN 74.00; v3 reduced false negatives.
test_adv_30: v3 mean FN 35.00 vs Ablation C FN 102.00; v3 reduced false negatives.

Ablation D: comparable FN columns unavailable.

Proposed GA v2: metrics unavailable.
