# Ablation D Summary

Ablation D follows the manuscript definition: frozen DistilBERT embeddings fused with eight engineered feature groups weighted by random vectors sampled from Uniform(0, 2). Runs use seeds 42, 7, and 123 and report mean plus standard deviation. It does not implement combined veracity, rarity, or difficulty weighting. Primary metrics use smishing as positive class label_id=1.

## Mean/Std Metrics

                    model       split  n_rows    seeds  accuracy_mean  accuracy_std  precision_smishing_mean  precision_smishing_std  recall_smishing_mean  recall_smishing_std  f1_smishing_mean  f1_smishing_std  macro_f1_mean  macro_f1_std  weighted_f1_mean  weighted_f1_std  f1_ham_mean  f1_ham_std  false_negative_rate_mean  false_negative_rate_std  false_positive_rate_mean  false_positive_rate_std
ablation_d_random_weights test_adv_10    1582 42,7,123       0.916983      0.001316                 0.939214                0.003762              0.891698             0.005109          0.914826         0.001547       0.916928      0.001324          0.916928         0.001324     0.919031    0.001186                  0.108302                 0.005109                  0.057733                 0.004064
ablation_d_random_weights test_adv_20    1582 42,7,123       0.910662      0.001591                 0.938391                0.003884              0.879056             0.004440          0.907744         0.001727       0.910571      0.001595          0.910571         0.001595     0.913398    0.001538                  0.120944                 0.004440                  0.057733                 0.004064
ablation_d_random_weights test_adv_30    1582 42,7,123       0.901601      0.005109                 0.937173                0.003972              0.860936             0.010948          0.897409         0.005861       0.901434      0.005155          0.901434         0.005155     0.905460    0.004479                  0.139064                 0.010948                  0.057733                 0.004064
ablation_d_random_weights  test_clean    1582 42,7,123       0.934260      0.001095                 0.941345                0.003744              0.926254             0.003182          0.933730         0.001027       0.934256      0.001093          0.934256         0.001093     0.934781    0.001198                  0.073746                 0.003182                  0.057733                 0.004064

## Per-Seed Metrics

                    model       split  seed  n_rows  accuracy  precision_smishing  recall_smishing  f1_smishing  macro_f1  weighted_f1   f1_ham  false_negative_rate  false_positive_rate  tn  fp  fn  tp
ablation_d_random_weights  test_clean    42    1582  0.934893            0.939898         0.929204     0.934520  0.934890     0.934890 0.935261             0.070796             0.059418 744  47  56 735
ablation_d_random_weights test_adv_10    42    1582  0.918458            0.937831         0.896334     0.916613  0.918418     0.918418 0.920223             0.103666             0.059418 744  47  82 709
ablation_d_random_weights test_adv_20    42    1582  0.912137            0.936997         0.883692     0.909564  0.912065     0.912065 0.914567             0.116308             0.059418 744  47  92 699
ablation_d_random_weights test_adv_30    42    1582  0.907080            0.936314         0.873578     0.903859  0.906975     0.906975 0.910092             0.126422             0.059418 744  47 100 691
ablation_d_random_weights  test_clean     7    1582  0.932996            0.938540         0.926675     0.932570  0.932994     0.932994 0.933417             0.073325             0.060683 743  48  58 733
ablation_d_random_weights test_adv_10     7    1582  0.915929            0.936340         0.892541     0.913916  0.915883     0.915883 0.917851             0.107459             0.060683 743  48  85 706
ablation_d_random_weights test_adv_20     7    1582  0.908976            0.935397         0.878635     0.906128  0.908892     0.908892 0.911656             0.121365             0.060683 743  48  96 695
ablation_d_random_weights test_adv_30     7    1582  0.896966            0.933702         0.854614     0.892409  0.896781     0.896781 0.901152             0.145386             0.060683 743  48 115 676
ablation_d_random_weights  test_clean   123    1582  0.934893            0.945596         0.922882     0.934101  0.934883     0.934883 0.935665             0.077118             0.053097 749  42  61 730
ablation_d_random_weights test_adv_10   123    1582  0.916561            0.943472         0.886220     0.913950  0.916484     0.916484 0.919018             0.113780             0.053097 749  42  90 701
ablation_d_random_weights test_adv_20   123    1582  0.910872            0.942779         0.874842     0.907541  0.910756     0.910756 0.913972             0.125158             0.053097 749  42  99 692
ablation_d_random_weights test_adv_30   123    1582  0.900759            0.941504         0.854614     0.895958  0.900547     0.900547 0.905136             0.145386             0.053097 749  42 115 676