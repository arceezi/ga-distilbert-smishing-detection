# Error Analysis Summary

This report summarizes representative-run confusion matrices, false negatives, false positives, and clean-to-adversarial false-negative shifts.

## Confusion Matrix Summary

```text
            model_key                             display_name       split split_label  tp  tn  fp  fn  support_ham  support_smishing      fnr      fpr
      tfidf_baseline1          Baseline 1 (TF-IDF, unweighted)  test_clean       clean 769 780  11  22          791               791 0.027813 0.013906
      tfidf_baseline1          Baseline 1 (TF-IDF, unweighted) test_adv_10       adv10 716 780  11  75          791               791 0.094817 0.013906
      tfidf_baseline1          Baseline 1 (TF-IDF, unweighted) test_adv_20       adv20 699 780  11  92          791               791 0.116308 0.013906
      tfidf_baseline1          Baseline 1 (TF-IDF, unweighted) test_adv_30       adv30 674 780  11 117          791               791 0.147914 0.013906
     tfidf_ablation_a      Ablation A (TF-IDF, class-weighted)  test_clean       clean 769 780  11  22          791               791 0.027813 0.013906
     tfidf_ablation_a      Ablation A (TF-IDF, class-weighted) test_adv_10       adv10 716 780  11  75          791               791 0.094817 0.013906
     tfidf_ablation_a      Ablation A (TF-IDF, class-weighted) test_adv_20       adv20 699 780  11  92          791               791 0.116308 0.013906
     tfidf_ablation_a      Ablation A (TF-IDF, class-weighted) test_adv_30       adv30 674 780  11 117          791               791 0.147914 0.013906
 distilbert_baseline2       Baseline 2 (DistilBERT fine-tuned)  test_clean       clean 781 778  13  10          791               791 0.012642 0.016435
 distilbert_baseline2       Baseline 2 (DistilBERT fine-tuned) test_adv_10       adv10 777 778  13  14          791               791 0.017699 0.016435
 distilbert_baseline2       Baseline 2 (DistilBERT fine-tuned) test_adv_20       adv20 758 778  13  33          791               791 0.041719 0.016435
 distilbert_baseline2       Baseline 2 (DistilBERT fine-tuned) test_adv_30       adv30 759 778  13  32          791               791 0.040455 0.016435
distilbert_ablation_b   Ablation B (DistilBERT + augmentation)  test_clean       clean 781 775  16  10          791               791 0.012642 0.020228
distilbert_ablation_b   Ablation B (DistilBERT + augmentation) test_adv_10       adv10 783 780  11   8          791               791 0.010114 0.013906
distilbert_ablation_b   Ablation B (DistilBERT + augmentation) test_adv_20       adv20 787 778  13   4          791               791 0.005057 0.016435
distilbert_ablation_b   Ablation B (DistilBERT + augmentation) test_adv_30       adv30 787 780  11   4          791               791 0.005057 0.013906
           ablation_c Ablation C (Frozen DistilBERT + uniform)  test_clean       clean 747 745  46  44          791               791 0.055626 0.058154
           ablation_c Ablation C (Frozen DistilBERT + uniform) test_adv_10       adv10 727 745  46  64          791               791 0.080910 0.058154
           ablation_c Ablation C (Frozen DistilBERT + uniform) test_adv_20       adv20 717 745  46  74          791               791 0.093552 0.058154
           ablation_c Ablation C (Frozen DistilBERT + uniform) test_adv_30       adv30 689 745  46 102          791               791 0.128951 0.058154
           ablation_d  Ablation D (Frozen DistilBERT + random)  test_clean       clean 742 748  43  49          791               791 0.061947 0.054362
           ablation_d  Ablation D (Frozen DistilBERT + random) test_adv_10       adv10 729 750  41  62          791               791 0.078382 0.051833
           ablation_d  Ablation D (Frozen DistilBERT + random) test_adv_20       adv20 713 750  41  78          791               791 0.098609 0.051833
           ablation_d  Ablation D (Frozen DistilBERT + random) test_adv_30       adv30 688 750  41 103          791               791 0.130215 0.051833
       proposed_ga_v3     Proposed Model (GA-optimized fusion)  test_clean       clean 779 692  99  12          791               791 0.015171 0.125158
       proposed_ga_v3     Proposed Model (GA-optimized fusion) test_adv_10       adv10 773 692  99  18          791               791 0.022756 0.125158
       proposed_ga_v3     Proposed Model (GA-optimized fusion) test_adv_20       adv20 752 692  99  39          791               791 0.049305 0.125158
       proposed_ga_v3     Proposed Model (GA-optimized fusion) test_adv_30       adv30 755 692  99  36          791               791 0.045512 0.125158
```

## False Negative Counts

```text
            model_key                             display_name       split  false_negative_count
      tfidf_baseline1          Baseline 1 (TF-IDF, unweighted)  test_clean                    22
      tfidf_baseline1          Baseline 1 (TF-IDF, unweighted) test_adv_10                    75
      tfidf_baseline1          Baseline 1 (TF-IDF, unweighted) test_adv_20                    92
      tfidf_baseline1          Baseline 1 (TF-IDF, unweighted) test_adv_30                   117
     tfidf_ablation_a      Ablation A (TF-IDF, class-weighted)  test_clean                    22
     tfidf_ablation_a      Ablation A (TF-IDF, class-weighted) test_adv_10                    75
     tfidf_ablation_a      Ablation A (TF-IDF, class-weighted) test_adv_20                    92
     tfidf_ablation_a      Ablation A (TF-IDF, class-weighted) test_adv_30                   117
 distilbert_baseline2       Baseline 2 (DistilBERT fine-tuned)  test_clean                    10
 distilbert_baseline2       Baseline 2 (DistilBERT fine-tuned) test_adv_10                    14
 distilbert_baseline2       Baseline 2 (DistilBERT fine-tuned) test_adv_20                    33
 distilbert_baseline2       Baseline 2 (DistilBERT fine-tuned) test_adv_30                    32
distilbert_ablation_b   Ablation B (DistilBERT + augmentation)  test_clean                    10
distilbert_ablation_b   Ablation B (DistilBERT + augmentation) test_adv_10                     8
distilbert_ablation_b   Ablation B (DistilBERT + augmentation) test_adv_20                     4
distilbert_ablation_b   Ablation B (DistilBERT + augmentation) test_adv_30                     4
           ablation_c Ablation C (Frozen DistilBERT + uniform)  test_clean                    44
           ablation_c Ablation C (Frozen DistilBERT + uniform) test_adv_10                    64
           ablation_c Ablation C (Frozen DistilBERT + uniform) test_adv_20                    74
           ablation_c Ablation C (Frozen DistilBERT + uniform) test_adv_30                   102
           ablation_d  Ablation D (Frozen DistilBERT + random)  test_clean                    49
           ablation_d  Ablation D (Frozen DistilBERT + random) test_adv_10                    62
           ablation_d  Ablation D (Frozen DistilBERT + random) test_adv_20                    78
           ablation_d  Ablation D (Frozen DistilBERT + random) test_adv_30                   103
       proposed_ga_v3     Proposed Model (GA-optimized fusion)  test_clean                    12
       proposed_ga_v3     Proposed Model (GA-optimized fusion) test_adv_10                    18
       proposed_ga_v3     Proposed Model (GA-optimized fusion) test_adv_20                    39
       proposed_ga_v3     Proposed Model (GA-optimized fusion) test_adv_30                    36
```

## False Positive Counts

```text
            model_key                             display_name       split  false_positive_count
      tfidf_baseline1          Baseline 1 (TF-IDF, unweighted)  test_clean                    11
      tfidf_baseline1          Baseline 1 (TF-IDF, unweighted) test_adv_10                    11
      tfidf_baseline1          Baseline 1 (TF-IDF, unweighted) test_adv_20                    11
      tfidf_baseline1          Baseline 1 (TF-IDF, unweighted) test_adv_30                    11
     tfidf_ablation_a      Ablation A (TF-IDF, class-weighted)  test_clean                    11
     tfidf_ablation_a      Ablation A (TF-IDF, class-weighted) test_adv_10                    11
     tfidf_ablation_a      Ablation A (TF-IDF, class-weighted) test_adv_20                    11
     tfidf_ablation_a      Ablation A (TF-IDF, class-weighted) test_adv_30                    11
 distilbert_baseline2       Baseline 2 (DistilBERT fine-tuned)  test_clean                    13
 distilbert_baseline2       Baseline 2 (DistilBERT fine-tuned) test_adv_10                    13
 distilbert_baseline2       Baseline 2 (DistilBERT fine-tuned) test_adv_20                    13
 distilbert_baseline2       Baseline 2 (DistilBERT fine-tuned) test_adv_30                    13
distilbert_ablation_b   Ablation B (DistilBERT + augmentation)  test_clean                    16
distilbert_ablation_b   Ablation B (DistilBERT + augmentation) test_adv_10                    11
distilbert_ablation_b   Ablation B (DistilBERT + augmentation) test_adv_20                    13
distilbert_ablation_b   Ablation B (DistilBERT + augmentation) test_adv_30                    11
           ablation_c Ablation C (Frozen DistilBERT + uniform)  test_clean                    46
           ablation_c Ablation C (Frozen DistilBERT + uniform) test_adv_10                    46
           ablation_c Ablation C (Frozen DistilBERT + uniform) test_adv_20                    46
           ablation_c Ablation C (Frozen DistilBERT + uniform) test_adv_30                    46
           ablation_d  Ablation D (Frozen DistilBERT + random)  test_clean                    43
           ablation_d  Ablation D (Frozen DistilBERT + random) test_adv_10                    41
           ablation_d  Ablation D (Frozen DistilBERT + random) test_adv_20                    41
           ablation_d  Ablation D (Frozen DistilBERT + random) test_adv_30                    41
       proposed_ga_v3     Proposed Model (GA-optimized fusion)  test_clean                    99
       proposed_ga_v3     Proposed Model (GA-optimized fusion) test_adv_10                    99
       proposed_ga_v3     Proposed Model (GA-optimized fusion) test_adv_20                    99
       proposed_ga_v3     Proposed Model (GA-optimized fusion) test_adv_30                    99
```

## Clean TP to Adversarial FN Shift

```text
            model_key                             display_name adversarial_split  clean_tp_to_adversarial_fn_count  clean_tp_count  shift_rate_among_clean_tp
      tfidf_baseline1          Baseline 1 (TF-IDF, unweighted)       test_adv_10                                53             769                   0.068921
      tfidf_baseline1          Baseline 1 (TF-IDF, unweighted)       test_adv_20                                72             769                   0.093628
      tfidf_baseline1          Baseline 1 (TF-IDF, unweighted)       test_adv_30                                96             769                   0.124837
     tfidf_ablation_a      Ablation A (TF-IDF, class-weighted)       test_adv_10                                53             769                   0.068921
     tfidf_ablation_a      Ablation A (TF-IDF, class-weighted)       test_adv_20                                72             769                   0.093628
     tfidf_ablation_a      Ablation A (TF-IDF, class-weighted)       test_adv_30                                96             769                   0.124837
 distilbert_baseline2       Baseline 2 (DistilBERT fine-tuned)       test_adv_10                                 5             781                   0.006402
 distilbert_baseline2       Baseline 2 (DistilBERT fine-tuned)       test_adv_20                                26             781                   0.033291
 distilbert_baseline2       Baseline 2 (DistilBERT fine-tuned)       test_adv_30                                26             781                   0.033291
distilbert_ablation_b   Ablation B (DistilBERT + augmentation)       test_adv_10                                 3             781                   0.003841
distilbert_ablation_b   Ablation B (DistilBERT + augmentation)       test_adv_20                                 2             781                   0.002561
distilbert_ablation_b   Ablation B (DistilBERT + augmentation)       test_adv_30                                 2             781                   0.002561
           ablation_c Ablation C (Frozen DistilBERT + uniform)       test_adv_10                                31             747                   0.041499
           ablation_c Ablation C (Frozen DistilBERT + uniform)       test_adv_20                                44             747                   0.058902
           ablation_c Ablation C (Frozen DistilBERT + uniform)       test_adv_30                                68             747                   0.091031
           ablation_d  Ablation D (Frozen DistilBERT + random)       test_adv_10                                26             742                   0.035040
           ablation_d  Ablation D (Frozen DistilBERT + random)       test_adv_20                                44             742                   0.059299
           ablation_d  Ablation D (Frozen DistilBERT + random)       test_adv_30                                64             742                   0.086253
       proposed_ga_v3     Proposed Model (GA-optimized fusion)       test_adv_10                                 9             779                   0.011553
       proposed_ga_v3     Proposed Model (GA-optimized fusion)       test_adv_20                                29             779                   0.037227
       proposed_ga_v3     Proposed Model (GA-optimized fusion)       test_adv_30                                27             779                   0.034660
```
