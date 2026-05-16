# Adversarial Test Report

- Input: `data/06_model_ready/clean/test_clean.csv`
- Log: `data/06_model_ready/adversarial_test/test_adversarial_log.csv`
- Purpose: final robustness evaluation for all seven models.
- Ham rows are unchanged; smishing rows are perturbed after splitting.

## Artifact Counts

| Artifact | Path | Rows | Ham | Smishing | Matches clean row count |
| --- | --- | --- | --- | --- | --- |
| test_adv_10 | data/06_model_ready/adversarial_test/test_adv_10.csv | 1582 | 791 | 791 | True |
| test_adv_20 | data/06_model_ready/adversarial_test/test_adv_20.csv | 1582 | 791 | 791 | True |
| test_adv_30 | data/06_model_ready/adversarial_test/test_adv_30.csv | 1582 | 791 | 791 | True |

## Perturbation Quality

| Level | Average perturbation rate | Quality pass | Quality fail |
| --- | --- | --- | --- |
| 10 | 0.392 | 791 | 0 |
| 20 | 0.5915 | 791 | 0 |
| 30 | 0.7861 | 791 | 0 |

## Technique Counts

| Technique | Count |
| --- | --- |
| homoglyph_substitution | 1773 |
| institution_substitution | 69 |
| leetspeak_obfuscation | 956 |
| numeric_otp_variation | 767 |
| separator_injection | 612 |
| spacing_punctuation_case_noise | 1788 |
| urgency_paraphrasing | 90 |
| url_variation | 992 |
