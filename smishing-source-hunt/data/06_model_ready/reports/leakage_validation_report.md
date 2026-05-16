# Leakage Validation Report

- Validation status: PASSED
- Output folder: `data/06_model_ready`

## Clean Split Counts

| Artifact | Rows | Ham | Smishing | Synthetic ham |
| --- | --- | --- | --- | --- |
| train_clean | 7380 | 3690 | 3690 | 919 |
| val_clean | 1582 | 791 | 791 | 191 |
| test_clean | 1582 | 791 | 791 | 190 |

## Augmented Training Summary

| Metric | Value |
| --- | --- |
| train_clean rows | 7380 |
| train_augmented_for_ablation_b rows | 9580 |
| included augmented rows | 2200 |
| augmented label counts | {'ham': 3690, 'smishing': 5890} |
| technique counts | {'spacing_punctuation_case_noise': 1681, 'homoglyph_substitution': 1610, 'url_variation': 904, 'leetspeak_obfuscation': 848, 'numeric_otp_variation': 700, 'separator_injection': 590, 'institution_substitution': 48, 'urgency_paraphrasing': 93} |

## Adversarial Artifact Summary

| Artifact | Rows | Ham | Smishing | Smishing perturbed rows |
| --- | --- | --- | --- | --- |
| val_adv_10 | 1582 | 791 | 791 | 791 |
| val_adv_20 | 1582 | 791 | 791 | 791 |
| test_adv_10 | 1582 | 791 | 791 | 791 |
| test_adv_20 | 1582 | 791 | 791 | 791 |
| test_adv_30 | 1582 | 791 | 791 | 791 |

## Issues

- None

## Warnings

- None
