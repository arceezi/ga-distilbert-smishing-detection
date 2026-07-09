# GA Interpretability Validation Summary

The thesis target for weight stability is Spearman rho >= 0.80 across seed runs.

## Spearman Rank Correlations

```text
 seed_a  seed_b  spearman_rho  p_value  meets_target_rho_ge_0_80
     42       7      0.761905 0.028005                     False
     42     123      0.714286 0.046528                     False
      7     123      0.690476 0.057990                     False
```

## Top Feature Group Stability

```text
 seed                                                   top3_features           top1_feature
    7     G3_Obfuscation, G6_Financial_Terms, G7_Auth_Secrets_Request         G3_Obfuscation
   42 G8_Brand_Impersonation, G7_Auth_Secrets_Request, G3_Obfuscation G8_Brand_Impersonation
  123      G8_Brand_Impersonation, G3_Obfuscation, G6_Financial_Terms G8_Brand_Impersonation
```

## Selected Final Weights

```text
                feature   weight selected_weight_source
         G1_URL_Signals 0.804101      best_seed_weights
 G2_OTP_Numeric_Density 0.600767      best_seed_weights
         G3_Obfuscation 1.142498      best_seed_weights
 G4_Urgency_Threat_Cues 0.818592      best_seed_weights
   G5_Action_Directives 0.628107      best_seed_weights
     G6_Financial_Terms 1.081732      best_seed_weights
G7_Auth_Secrets_Request 0.987574      best_seed_weights
 G8_Brand_Impersonation 1.295594      best_seed_weights
```

## Selected Threshold and Scale Metadata

```json
{
  "selected_threshold": 0.35,
  "selected_weight_source": "best_seed_weights",
  "feature_branch_scale": 2.0,
  "selection_rule": "Phase C thresholds are tuned per final seed on validation splits only using the FPR-aware rule.",
  "fpr_constraint_satisfied": true,
  "mean_recall": 0.9548040455120101,
  "mean_f1": 0.9309227522016481,
  "mean_fnr": 0.04519595448798989,
  "mean_fpr": 0.09608091024020228,
  "max_fnr": 0.09102402022756005,
  "robustness_gap": 0.06826801517067005,
  "threshold_score_formula": "0.30*mean_recall + 0.35*mean_f1 - 0.15*mean_fnr - 0.20*mean_fpr - 0.05*robustness_gap",
  "ga_fitness_formula": "0.30*mean_recall + 0.30*mean_f1 + 0.20*min_recall - 0.10*max_fnr - 0.05*mean_fpr - 0.05*robustness_gap - 0.05*weight_extremeness_penalty",
  "ga_weight_selection_threshold": 0.35,
  "phase_c_seed_thresholds": [
    {
      "seed": 42,
      "selected_threshold": 0.25,
      "fpr_constraint_satisfied": true,
      "mean_fpr": 0.11125158027812895,
      "mean_recall": 0.9557522123893805,
      "mean_f1": 0.9245948592291863,
      "mean_fnr": 0.04424778761061947,
      "robustness_gap": 0.06573957016434895
    },
    {
      "seed": 7,
      "selected_threshold": 0.25,
      "fpr_constraint_satisfied": true,
      "mean_fpr": 0.09987357774968394,
      "mean_recall": 0.949747155499368,
      "mean_f1": 0.9264951156411144,
      "mean_fnr": 0.05025284450063211,
      "robustness_gap": 0.07964601769911495
    },
    {
      "seed": 123,
      "selected_threshold": 0.25,
      "fpr_constraint_satisfied": true,
      "mean_fpr": 0.1011378002528445,
      "mean_recall": 0.950063211125158,
      "mean_f1": 0.9260776894460186,
      "mean_fnr": 0.04993678887484197,
      "robustness_gap": 0.08091024020227555
    }
  ]
}
```
