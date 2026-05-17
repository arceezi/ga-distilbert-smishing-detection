# Ablation C Summary

Ablation C follows the manuscript definition: frozen DistilBERT embeddings fused with eight engineered feature groups, all weighted at 1.0. It does not implement verification-only weighting. Primary metrics use smishing as positive class label_id=1.

                     model       split  seed  n_rows  accuracy  precision_smishing  recall_smishing  f1_smishing  macro_f1  weighted_f1   f1_ham  false_negative_rate  false_positive_rate  tn  fp  fn  tp
ablation_c_uniform_weights  test_clean    42    1582  0.929836            0.934783         0.924147     0.929434  0.929833     0.929833 0.930233             0.075853             0.064475 740  51  60 731
ablation_c_uniform_weights test_adv_10    42    1582  0.914033            0.932629         0.892541     0.912145  0.913993     0.913993 0.915842             0.107459             0.064475 740  51  85 706
ablation_c_uniform_weights test_adv_20    42    1582  0.907080            0.931635         0.878635     0.904359  0.907004     0.907004 0.909650             0.121365             0.064475 740  51  96 695
ablation_c_uniform_weights test_adv_30    42    1582  0.900126            0.930612         0.864728     0.896461  0.900001     0.900001 0.903541             0.135272             0.064475 740  51 107 684