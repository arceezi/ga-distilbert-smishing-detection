# Proposed GA v3 Overfitting Check

The final model was trained across seeds [42, 7, 123]. The report should be interpreted using the mean and standard deviation across seeds rather than one lucky run.

## Training Histories

Training histories are saved under `results/metrics/proposed_ga_v3_seed*_training_history.csv` and training curves under `results/figures/proposed_phase_c_training_curve_seed*.png`.

## Validation-Only Selection

Feature branch scale, GA weights, and threshold were selected using validation splits only. Test splits were not used during selection.

## Scale Search

```
 feature_branch_scale  mean_seed_fitness  std_seed_fitness  best_validation_fitness  mean_fpr  mean_recall                                                                                         selection_rule
                  2.0           0.741528          0.000250                 0.741850  0.155499     0.972398 highest mean_seed_fitness, then lower std_seed_fitness, lower mean_fpr, higher best_validation_fitness
                  3.0           0.740813          0.000146                 0.740952  0.168142     0.974926 highest mean_seed_fitness, then lower std_seed_fitness, lower mean_fpr, higher best_validation_fitness
                  1.0           0.738517          0.000332                 0.738986  0.139907     0.969027 highest mean_seed_fitness, then lower std_seed_fitness, lower mean_fpr, higher best_validation_fitness
                  5.0           0.734065          0.000471                 0.734716  0.235567     0.978298 highest mean_seed_fitness, then lower std_seed_fitness, lower mean_fpr, higher best_validation_fitness
                 10.0           0.726934          0.000382                 0.727235  0.250737     0.977665 highest mean_seed_fitness, then lower std_seed_fitness, lower mean_fpr, higher best_validation_fitness
```

## Weight Selection

```
selected_weight_source  feature_branch_scale  selected_threshold  validation_score  mean_recall  mean_f1  mean_fpr  mean_fnr  max_fnr  robustness_gap                             selection_rule  fpr_constraint_satisfied
     best_seed_weights                   2.0                0.35          0.582855     0.954804 0.930923  0.096081  0.045196 0.091024        0.068268 best threshold_score with mean_fpr <= 0.12                      True
  average_seed_weights                   2.0                0.35          0.581903     0.955752 0.929149  0.101138  0.044248 0.087231        0.063211 best threshold_score with mean_fpr <= 0.12                      True
```

## Test Mean/Std Summary

```
         model       split  num_seeds  accuracy_mean  accuracy_std  precision_smishing_mean  precision_smishing_std  recall_smishing_mean  recall_smishing_std  f1_smishing_mean  f1_smishing_std  false_negative_rate_mean  false_negative_rate_std  false_positive_rate_mean  false_positive_rate_std    tp_mean   tp_std  tn_mean   tn_std  fp_mean   fp_std   fn_mean   fn_std  support_ham_mean  support_ham_std  support_smishing_mean  support_smishing_std  threshold_mean  threshold_std
proposed_ga_v3 test_adv_10          3       0.924989      0.002439                 0.883653                0.005485              0.978930             0.002384          0.928837         0.001987                  0.021070                 0.002384                  0.128951                 0.007226 774.333333 1.885618    689.0 5.715476    102.0 5.715476 16.666667 1.885618             791.0              0.0                  791.0                   0.0            0.25            0.0
proposed_ga_v3 test_adv_20          3       0.911504      0.002250                 0.880753                0.005554              0.951960             0.002731          0.914954         0.001750                  0.048040                 0.002731                  0.128951                 0.007226 753.000000 2.160247    689.0 5.715476    102.0 5.715476 38.000000 2.160247             791.0              0.0                  791.0                   0.0            0.25            0.0
proposed_ga_v3 test_adv_30          3       0.913401      0.002731                 0.881166                0.005646              0.955752             0.001788          0.916929         0.002257                  0.044248                 0.001788                  0.128951                 0.007226 756.000000 1.414214    689.0 5.715476    102.0 5.715476 35.000000 1.414214             791.0              0.0                  791.0                   0.0            0.25            0.0
proposed_ga_v3  test_clean          3       0.928361      0.003024                 0.884352                0.005583              0.985672             0.001192          0.932254         0.002585                  0.014328                 0.001192                  0.128951                 0.007226 779.666667 0.942809    689.0 5.715476    102.0 5.715476 11.333333 0.942809             791.0              0.0                  791.0                   0.0            0.25            0.0
```

Large gaps between validation-selected behavior and test behavior should be treated as possible validation overfitting. Clean-to-adv30 changes are summarized in the degradation table.
