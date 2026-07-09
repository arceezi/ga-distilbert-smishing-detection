# Ablation C Corrected Summary

Frozen DistilBERT embeddings plus corrected G1-G8 engineered features with uniform weights `[1,1,1,1,1,1,1,1]`. The linear head is trained on `train_clean` only; `val_clean` is used only for validation/early stopping. Because train_clean is balanced, unweighted BCEWithLogitsLoss is acceptable for Ablation C/D. False-negative prioritization is mainly handled in the proposed GA model.

Best epoch: 60; early stopping epoch: 60.

| model      | split       |   seed |   n_rows |   accuracy |   precision_smishing |   recall_smishing |   f1_smishing |   false_negative_rate |   false_positive_rate |   tp |   tn |   fp |   fn |   support_ham |   support_smishing |
|:-----------|:------------|-------:|---------:|-----------:|---------------------:|------------------:|--------------:|----------------------:|----------------------:|-----:|-----:|-----:|-----:|--------------:|-------------------:|
| ablation_c | test_clean  |     42 |     1582 |   0.94311  |             0.941992 |          0.944374 |      0.943182 |             0.0556258 |             0.0581542 |  747 |  745 |   46 |   44 |           791 |                791 |
| ablation_c | test_adv_10 |     42 |     1582 |   0.930468 |             0.940492 |          0.91909  |      0.929668 |             0.0809102 |             0.0581542 |  727 |  745 |   46 |   64 |           791 |                791 |
| ablation_c | test_adv_20 |     42 |     1582 |   0.924147 |             0.939712 |          0.906448 |      0.92278  |             0.0935525 |             0.0581542 |  717 |  745 |   46 |   74 |           791 |                791 |
| ablation_c | test_adv_30 |     42 |     1582 |   0.906448 |             0.937415 |          0.871049 |      0.903014 |             0.128951  |             0.0581542 |  689 |  745 |   46 |  102 |           791 |                791 |