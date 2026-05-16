# Adversarial Validation Report

- Input: `data/06_model_ready/clean/val_clean.csv`
- Log: `data/06_model_ready/adversarial_validation/val_adversarial_log.csv`
- Purpose: GA fitness evaluation.
- Ham rows are unchanged; smishing rows are perturbed after splitting.

## Artifact Counts

| Artifact | Path | Rows | Ham | Smishing | Matches clean row count |
| --- | --- | --- | --- | --- | --- |
| val_adv_10 | data/06_model_ready/adversarial_validation/val_adv_10.csv | 1582 | 791 | 791 | True |
| val_adv_20 | data/06_model_ready/adversarial_validation/val_adv_20.csv | 1582 | 791 | 791 | True |

## Perturbation Quality

| Level | Average perturbation rate | Quality pass | Quality fail |
| --- | --- | --- | --- |
| 10 | 0.3927 | 791 | 0 |
| 20 | 0.6138 | 791 | 0 |

## Technique Counts

| Technique | Count |
| --- | --- |
| homoglyph_substitution | 1006 |
| institution_substitution | 25 |
| leetspeak_obfuscation | 505 |
| numeric_otp_variation | 403 |
| separator_injection | 346 |
| spacing_punctuation_case_noise | 977 |
| urgency_paraphrasing | 71 |
| url_variation | 563 |
