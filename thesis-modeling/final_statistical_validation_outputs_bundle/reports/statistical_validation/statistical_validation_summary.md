# Statistical Validation Summary

Notebook 06 is validation-only. It does not train models, load checkpoints, tune thresholds, or select models.

## Thesis Alignment

- Table 3.40: all nine pairwise comparisons are included.
- Table 3.44: McNemar statistic, p-value, discordant pairs, and Bonferroni significance are reported.
- Section 3.7.6: confusion matrices, false negatives, false positives, and adversarial false-negative shifts are summarized.
- Section 3.7.4: GA weight rank stability is summarized with Spearman correlations and top feature groups.

## Representative Run Rule

For stochastic models, the representative run is the median F1 seed on the same split. Ties use seed priority 42, then 7, then 123. Ablation C uses its only available run.

## Pairing Audit

All representative prediction files were paired by `final_row_id`; labels were checked for alignment before McNemar testing.

## Bonferroni Thresholds

- Per-split Bonferroni alpha: 0.00555556
- Global Bonferroni alpha: 0.00138889

## McNemar Summary

```text
split_label  comparisons  significant_uncorrected  significant_bonferroni_per_split  significant_bonferroni_global
      adv10            9                        4                                 2                              2
      adv20            9                        5                                 3                              3
      adv30            9                        3                                 3                              3
      clean            9                        5                                 4                              4
```
