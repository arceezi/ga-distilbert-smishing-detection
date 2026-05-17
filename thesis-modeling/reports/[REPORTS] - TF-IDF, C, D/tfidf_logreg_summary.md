# TF-IDF Logistic Regression Summary

Baseline 1 uses separate word-level and character-level TF-IDF branches combined with FeatureUnion. The manuscript max_features=5,000 cap is enforced by allocating 2,500 features to each branch. Logistic Regression is unweighted with class_weight=None. Primary precision, recall, F1, FNR, and FPR use smishing as the positive class (label_id=1).

       model       split seed  n_rows  accuracy  precision_smishing  recall_smishing  f1_smishing  macro_f1  weighted_f1   f1_ham  false_negative_rate  false_positive_rate  tn  fp  fn  tp  tfidf_total_features
tfidf_logreg  test_clean None    1582  0.981037            0.988447         0.973451     0.980892  0.981036     0.981036 0.981179             0.026549             0.011378 782   9  21 770                  5000
tfidf_logreg test_adv_10 None    1582  0.959545            0.987919         0.930468     0.958333  0.959511     0.959511 0.960688             0.069532             0.011378 782   9  55 736                  5000
tfidf_logreg test_adv_20 None    1582  0.955120            0.987805         0.921618     0.953564  0.955070     0.955070 0.956575             0.078382             0.011378 782   9  62 729                  5000
tfidf_logreg test_adv_30 None    1582  0.946271            0.987569         0.903919     0.943894  0.946174     0.946174 0.948454             0.096081             0.011378 782   9  76 715                  5000