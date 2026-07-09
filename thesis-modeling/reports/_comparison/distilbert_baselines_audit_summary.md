# DistilBERT Baselines Audit Summary

- Did Baseline 2 use only train_clean.csv for training? Yes.
- Did Ablation B use only train_augmented_for_ablation_b.csv for training? Yes.
- Was val_clean.csv used only for validation/early stopping? Yes.
- Were test sets used only for final evaluation? Yes.
- Are there signs of overfitting from train/val loss curves? Inspect per-seed training curves and histories in results/.
- Why might Ablation B perform strongly on adversarial sets? It is trained on adversarially augmented text and may learn perturbation-invariant or perturbation-specific cues.
- Did adversarial performance degrade reasonably from clean to adv30? See degradation tables.
- Are adversarial perturbations too easy or label cues? Review adversarial gains, false negatives, and whether perturbation artifacts become predictive.
