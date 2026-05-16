"""Create the training-only adversarial augmentation artifact for Ablation B."""

from __future__ import annotations

import random
from collections import Counter

import pandas as pd

from adversarial_perturbation_engine import clean_adversarial_text_for_model, perturb_smishing_message
from model_ready_common import (
    AUGMENTATION_LOG,
    AUGMENTATION_SEED,
    AUGMENTATION_SELECTION_PERCENTAGE,
    AUGMENTATION_VARIANT_DISTRIBUTION,
    MAX_AUGMENTED_VARIANTS,
    REPORTS_DIR,
    TRAIN_AUGMENTED,
    TRAIN_AUGMENTED_METADATA,
    TRAIN_CLEAN,
    deterministic_row_seed,
    ensure_model_ready_dirs,
    label_counts,
    markdown_table,
    read_csv,
    relpath,
    stable_int,
    technique_counter,
    write_csv,
    write_text,
)


TRAINING_PERTURBATION_LEVEL = 20


def _variant_count_for_row(final_row_id: str) -> int:
    rng = random.Random(deterministic_row_seed(final_row_id, "train_augmented_variant_count", TRAINING_PERTURBATION_LEVEL, AUGMENTATION_SEED))
    value = rng.random()
    cumulative = 0.0
    for variant_count, probability in sorted(AUGMENTATION_VARIANT_DISTRIBUTION.items()):
        cumulative += probability
        if value <= cumulative:
            return int(variant_count)
    return 1


def _prepare_original_rows(train: pd.DataFrame) -> pd.DataFrame:
    out = train.copy()
    out["row_type"] = "original"
    out["augmentation_purpose"] = "clean_training"
    out["augmentation_id"] = ""
    out["adv_message_raw"] = ""
    out["adv_message_clean"] = ""
    out["original_message_raw"] = out["message_raw"]
    out["original_message_clean"] = out["message_clean"]
    out["model_text_raw_surface"] = out["message_raw"]
    out["model_text_clean"] = out["message_clean"]
    out["label_preserved"] = "True"
    out["seed"] = ""
    out["quality_status"] = "original_clean"
    out["augmentation_notes"] = ""
    return out


def create_augmented_training_set() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ensure_model_ready_dirs()
    train = read_csv(TRAIN_CLEAN)
    original_rows = _prepare_original_rows(train)
    smishing = train[train["normalized_label"].eq("smishing")].copy()
    selected_count = round(len(smishing) * AUGMENTATION_SELECTION_PERCENTAGE)
    smishing["_selection_order"] = smishing["final_row_id"].map(lambda value: stable_int(value, "ablation_b_selection", AUGMENTATION_SEED))
    selected = smishing.sort_values("_selection_order").head(selected_count).copy()

    augmented_rows: list[dict[str, object]] = []
    log_rows: list[dict[str, object]] = []
    variant_total = 0
    for _, row in selected.iterrows():
        if variant_total >= MAX_AUGMENTED_VARIANTS:
            break
        variant_count = _variant_count_for_row(row["final_row_id"])
        for variant_index in range(1, variant_count + 1):
            if variant_total >= MAX_AUGMENTED_VARIANTS:
                break
            row_seed = deterministic_row_seed(row["final_row_id"], f"train_augmented_v{variant_index}", TRAINING_PERTURBATION_LEVEL, AUGMENTATION_SEED)
            result = perturb_smishing_message(
                row["message_raw"],
                perturbation_level=TRAINING_PERTURBATION_LEVEL,
                seed=AUGMENTATION_SEED,
                row_seed=row_seed,
            )
            augmentation_id = f"aug_train_{row['final_row_id']}_v{variant_index}"
            log_row = {
                "augmentation_id": augmentation_id,
                "original_final_row_id": row["final_row_id"],
                "variant_index": variant_index,
                "perturbation_level": TRAINING_PERTURBATION_LEVEL,
                "perturbation_techniques": result["perturbation_techniques"],
                "num_chars_changed": result["num_chars_changed"],
                "changed_token_count": result["changed_token_count"],
                "achieved_perturbation_rate": result["achieved_perturbation_rate"],
                "quality_status": result["quality_status"],
                "label_preserved": result["label_preserved"],
                "seed": row_seed,
                "notes": result["notes"],
            }
            log_rows.append(log_row)
            if result["quality_status"] != "pass" or result["adv_message_raw"] == row["message_raw"]:
                continue

            augmented = row.drop(labels=[col for col in ["_selection_order"] if col in row.index]).to_dict()
            adv_raw = str(result["adv_message_raw"])
            adv_clean = clean_adversarial_text_for_model(adv_raw)
            augmented.update(
                {
                    "final_row_id": augmentation_id,
                    "source_final_row_id": row.get("source_final_row_id", row["final_row_id"]),
                    "message_raw": adv_raw,
                    "message_clean": adv_clean,
                    "model_text": adv_clean,
                    "normalized_label": "smishing",
                    "label_id": "1",
                    "split": "train",
                    "original_clean_row": "False",
                    "augmentation_status": "augmented_smishing",
                    "original_final_row_id": row["final_row_id"],
                    "perturbation_level": str(TRAINING_PERTURBATION_LEVEL),
                    "perturbation_techniques": result["perturbation_techniques"],
                    "variant_index": str(variant_index),
                    "row_type": "augmented",
                    "augmentation_purpose": "ablation_b_training",
                    "augmentation_id": augmentation_id,
                    "adv_message_raw": adv_raw,
                    "adv_message_clean": adv_clean,
                    "original_message_raw": row["message_raw"],
                    "original_message_clean": row["message_clean"],
                    "model_text_raw_surface": adv_raw,
                    "model_text_clean": adv_clean,
                    "label_preserved": "True",
                    "seed": str(row_seed),
                    "quality_status": result["quality_status"],
                    "augmentation_notes": result["notes"],
                }
            )
            augmented_rows.append(augmented)
            variant_total += 1

    augmented_df = pd.DataFrame(augmented_rows)
    combined = pd.concat([original_rows, augmented_df], ignore_index=True, sort=False)
    metadata_columns = [
        "augmentation_id",
        "original_final_row_id",
        "variant_index",
        "perturbation_level",
        "perturbation_techniques",
        "num_chars_changed",
        "changed_token_count",
        "achieved_perturbation_rate",
        "quality_status",
        "label_preserved",
        "seed",
        "notes",
    ]
    metadata = pd.DataFrame(log_rows)
    if not metadata.empty:
        metadata = metadata[metadata_columns]
    log = metadata.copy()

    if len(combined) > 2 * len(train):
        raise RuntimeError(f"Augmented training set exceeds 2x train_clean rows: {len(combined)} > {2 * len(train)}")

    write_csv(combined, TRAIN_AUGMENTED)
    write_csv(metadata, TRAIN_AUGMENTED_METADATA)
    write_csv(log, AUGMENTATION_LOG)
    write_report(train, combined, metadata, selected_count)
    return combined, metadata, log


def write_report(train: pd.DataFrame, combined: pd.DataFrame, metadata: pd.DataFrame, selected_count: int) -> None:
    original_counts = label_counts(train)
    final_counts = label_counts(combined)
    row_type_counts = Counter(combined["row_type"]) if "row_type" in combined.columns else Counter()
    technique_counts = technique_counter(metadata["perturbation_techniques"]) if not metadata.empty else Counter()
    pass_count = int(metadata["quality_status"].eq("pass").sum()) if not metadata.empty else 0
    fail_count = int(metadata["quality_status"].ne("pass").sum()) if not metadata.empty else 0
    avg_rate = round(float(pd.to_numeric(metadata["achieved_perturbation_rate"], errors="coerce").mean()), 4) if not metadata.empty else 0
    lines = [
        "# Augmentation Report",
        "",
        f"- Input path: `{relpath(TRAIN_CLEAN)}`",
        f"- Output path: `{relpath(TRAIN_AUGMENTED)}`",
        f"- Metadata path: `{relpath(TRAIN_AUGMENTED_METADATA)}`",
        f"- Augmentation log path: `{relpath(AUGMENTATION_LOG)}`",
        f"- Augmentation seed: {AUGMENTATION_SEED}",
        f"- Perturbation level for training variants: {TRAINING_PERTURBATION_LEVEL}",
        f"- Selected smishing rows requested: {selected_count}",
        f"- Included augmented variants: {int(row_type_counts.get('augmented', 0))}",
        f"- Variant cap: {MAX_AUGMENTED_VARIANTS}",
        f"- 2x train size cap compliance: {'PASS' if len(combined) <= 2 * len(train) else 'FAIL'}",
        "",
        "## Original Train Counts",
        "",
        *markdown_table(["Label", "Count"], sorted(original_counts.items())),
        "",
        "## Final Augmented Train Counts",
        "",
        *markdown_table(["Label", "Count"], sorted(final_counts.items())),
        "",
        "## Row Type Counts",
        "",
        *markdown_table(["Row type", "Count"], sorted(row_type_counts.items())),
        "",
        "## Technique Counts",
        "",
        *markdown_table(["Technique", "Count"], sorted(technique_counts.items())),
        "",
        "## Quality Summary",
        "",
        *markdown_table(
            ["Metric", "Value"],
            [
                ("quality pass attempts", pass_count),
                ("quality fail attempts", fail_count),
                ("average achieved perturbation rate", avg_rate),
                ("final augmented train rows", len(combined)),
                ("original train rows", len(train)),
            ],
        ),
        "",
        "## Usage Warning",
        "",
        "- This file is intentionally smishing-heavy because it appends adversarial smishing variants.",
        "- Use it only for Ablation B fine-tuned DistilBERT with adversarial augmentation.",
        "- Do not use this artifact for clean baselines, proposed GA Phase A, proposed GA Phase C, validation, GA fitness, or final test evaluation.",
        "- `model_text` is lightly cleaned adversarial surface text; `model_text_raw_surface` and `model_text_clean` are included for explicit experiment reporting.",
    ]
    write_text(REPORTS_DIR / "augmentation_report.md", lines)


def main() -> int:
    combined, metadata, _ = create_augmented_training_set()
    counts = label_counts(combined)
    print(f"Augmented training path: {relpath(TRAIN_AUGMENTED)}")
    print(f"Augmented training rows: {len(combined)} labels={dict(counts)}")
    print(f"Augmented variants included: {len(metadata[metadata['quality_status'].eq('pass')]) if not metadata.empty else 0}")
    print(f"Report: {relpath(REPORTS_DIR / 'augmentation_report.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

