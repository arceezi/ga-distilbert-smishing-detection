# thesis-modeling

This folder is the Google Colab modeling workspace for the smishing thesis.

## Folder purpose

* `data/06_model_ready/`
  Contains the frozen model-ready dataset package. Do not edit these files unless the dataset is intentionally rebuilt.

* `notebooks/`
  Contains the Colab notebooks for dataset checking, baseline training, DistilBERT training, engineered feature/embedding extraction, GA model training, and final evaluation.

* `artifacts/features/`
  Stores extracted engineered feature arrays, especially the 8 feature-group scores.

* `artifacts/embeddings/`
  Stores cached frozen DistilBERT embeddings so they do not need to be recomputed repeatedly.

* `artifacts/ga_runs/`
  Stores GA outputs such as best feature weights, fitness history, and GA configuration logs.

* `trained_models/`
  Stores saved trained models and classification heads.

* `results/metrics/`
  Stores model performance scores such as accuracy, precision, recall, F1, FNR, and FPR.

* `results/predictions/`
  Stores row-level predictions for each model and test set.

* `results/degradation_tables/`
  Stores robustness degradation tables comparing clean vs adversarial test performance.

* `results/figures/`
  Stores plots such as confusion matrices, degradation curves, and GA feature-weight charts.

* `reports/`
  Stores human-readable experiment summaries and final evaluation reports.

## Notebook run order

1. `00_dataset_check.ipynb`
2. `01_tfidf_logreg_baselines.ipynb`
3. `02_distilbert_baselines.ipynb`
4. `03_engineered_features_and_embeddings.ipynb`
5. `04_frozen_distilbert_ga_model.ipynb`
6. `05_final_evaluation_tables.ipynb`

## Important note

This folder does not generate the dataset. Dataset generation and source hunting remain in `smishing-source-hunt/`.
