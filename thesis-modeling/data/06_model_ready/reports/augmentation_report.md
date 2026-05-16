# Augmentation Report

- Input: `data/06_model_ready/clean/train_clean.csv`
- Output: `data/06_model_ready/augmented_training/train_augmented_for_ablation_b.csv`
- Metadata: `data/06_model_ready/augmented_training/train_augmented_for_ablation_b_metadata.csv`
- Log: `data/06_model_ready/augmented_training/augmentation_log.csv`
- Purpose: Ablation B training only.
- Selection: 55% of train smishing rows, variant distribution 70%/25%/5% for 1/2/3 variants, capped at 2,200 variants.

## Counts

| Metric | Value |
| --- | --- |
| original train rows | 7380 |
| augmented training rows | 9580 |
| augmented smishing variants | 2200 |
| ham rows | 3690 |
| smishing rows | 5890 |
| <= 2x train_clean | True |

## Technique Counts

| Technique | Count |
| --- | --- |
| homoglyph_substitution | 1610 |
| institution_substitution | 48 |
| leetspeak_obfuscation | 848 |
| numeric_otp_variation | 700 |
| separator_injection | 590 |
| spacing_punctuation_case_noise | 1681 |
| urgency_paraphrasing | 93 |
| url_variation | 904 |

## Quality

| Metric | Value |
| --- | --- |
| quality pass | 2200 |
| quality fail | 0 |
| average perturbation rate | 0.6225 |

## Usage Warning

- This artifact is intentionally smishing-heavy and must be used only for Ablation B.
- The proposed GA model trains on clean splits, not this augmented training file.
