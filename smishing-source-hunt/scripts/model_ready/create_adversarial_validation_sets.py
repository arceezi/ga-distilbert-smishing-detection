"""Create adversarial validation sets for GA fitness evaluation."""

from __future__ import annotations

from collections import Counter

import pandas as pd

from adversarial_perturbation_engine import clean_adversarial_text_for_model, perturb_smishing_message
from model_ready_common import (
    ADVERSARIAL_SEED,
    REPORTS_DIR,
    VAL_ADV_10,
    VAL_ADV_20,
    VAL_ADV_LOG,
    VAL_CLEAN,
    deterministic_row_seed,
    ensure_model_ready_dirs,
    label_counts,
    markdown_table,
    read_csv,
    relpath,
    technique_counter,
    write_csv,
    write_text,
)


LEVELS = [10, 20]


def _build_level(df: pd.DataFrame, level: int) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    rows: list[dict[str, object]] = []
    logs: list[dict[str, object]] = []
    for _, row in df.iterrows():
        out = row.to_dict()
        out["artifact_purpose"] = "ga_fitness_evaluation"
        out["adversarial_id"] = f"val_adv_{level}_{row['final_row_id']}"
        out["original_final_row_id"] = row["final_row_id"]
        out["original_message_raw"] = row["message_raw"]
        out["original_message_clean"] = row["message_clean"]
        out["perturbation_level"] = str(level)
        out["model_text_raw_surface"] = row["message_raw"]
        out["model_text_clean"] = row["message_clean"]
        out["label_preserved"] = "True"
        if row["normalized_label"] == "ham":
            out.update(
                {
                    "row_type": "original_ham_unchanged",
                    "perturbation_applied": "False",
                    "unchanged_reason": "ham_not_perturbed",
                    "quality_status": "unchanged_ham",
                    "adv_message_raw": "",
                    "adv_message_clean": "",
                    "num_chars_changed": "0",
                    "changed_token_count": "0",
                    "achieved_perturbation_rate": "0",
                    "seed": "",
                    "adversarial_notes": "Ham rows are intentionally unchanged in adversarial validation artifacts.",
                }
            )
            logs.append(
                {
                    "artifact": f"val_adv_{level}",
                    "perturbation_level": level,
                    "final_row_id": row["final_row_id"],
                    "normalized_label": row["normalized_label"],
                    "row_type": out["row_type"],
                    "perturbation_applied": "False",
                    "perturbation_techniques": "",
                    "num_chars_changed": 0,
                    "changed_token_count": 0,
                    "achieved_perturbation_rate": 0,
                    "quality_status": out["quality_status"],
                    "label_preserved": "True",
                    "seed": "",
                    "notes": out["adversarial_notes"],
                }
            )
        else:
            row_seed = deterministic_row_seed(row["final_row_id"], "val", level, ADVERSARIAL_SEED)
            result = perturb_smishing_message(row["message_raw"], perturbation_level=level, seed=ADVERSARIAL_SEED, row_seed=row_seed)
            adv_raw = str(result["adv_message_raw"])
            adv_clean = clean_adversarial_text_for_model(adv_raw)
            out.update(
                {
                    "message_raw": adv_raw,
                    "message_clean": adv_clean,
                    "model_text": adv_clean,
                    "model_text_raw_surface": adv_raw,
                    "model_text_clean": adv_clean,
                    "row_type": "adversarial_smishing",
                    "perturbation_applied": "True",
                    "unchanged_reason": "",
                    "adv_message_raw": adv_raw,
                    "adv_message_clean": adv_clean,
                    "perturbation_techniques": result["perturbation_techniques"],
                    "num_chars_changed": result["num_chars_changed"],
                    "changed_token_count": result["changed_token_count"],
                    "achieved_perturbation_rate": result["achieved_perturbation_rate"],
                    "quality_status": result["quality_status"],
                    "seed": str(row_seed),
                    "adversarial_notes": result["notes"],
                }
            )
            logs.append(
                {
                    "artifact": f"val_adv_{level}",
                    "perturbation_level": level,
                    "final_row_id": row["final_row_id"],
                    "normalized_label": row["normalized_label"],
                    "row_type": out["row_type"],
                    "perturbation_applied": "True",
                    "perturbation_techniques": result["perturbation_techniques"],
                    "num_chars_changed": result["num_chars_changed"],
                    "changed_token_count": result["changed_token_count"],
                    "achieved_perturbation_rate": result["achieved_perturbation_rate"],
                    "quality_status": result["quality_status"],
                    "label_preserved": "True",
                    "seed": row_seed,
                    "notes": result["notes"],
                }
            )
        rows.append(out)
    return pd.DataFrame(rows), logs


def create_adversarial_validation_sets() -> tuple[dict[int, pd.DataFrame], pd.DataFrame]:
    ensure_model_ready_dirs()
    val = read_csv(VAL_CLEAN)
    outputs = {10: VAL_ADV_10, 20: VAL_ADV_20}
    built: dict[int, pd.DataFrame] = {}
    log_rows: list[dict[str, object]] = []
    for level in LEVELS:
        df, logs = _build_level(val, level)
        write_csv(df, outputs[level])
        built[level] = df
        log_rows.extend(logs)
    log = pd.DataFrame(log_rows)
    write_csv(log, VAL_ADV_LOG)
    write_report(val, built, log)
    return built, log


def write_report(val: pd.DataFrame, built: dict[int, pd.DataFrame], log: pd.DataFrame) -> None:
    clean_counts = label_counts(val)
    rows = []
    for level, df in built.items():
        counts = label_counts(df)
        rows.append([f"val_adv_{level}", len(df), counts.get("ham", 0), counts.get("smishing", 0), len(df) == len(val)])
    smish_perturbed = int(log["row_type"].eq("adversarial_smishing").sum()) if not log.empty else 0
    ham_unchanged = int(log["row_type"].eq("original_ham_unchanged").sum()) if not log.empty else 0
    smish_log = log[log["row_type"].eq("adversarial_smishing")].copy() if not log.empty else pd.DataFrame()
    avg_rate = round(float(pd.to_numeric(smish_log["achieved_perturbation_rate"], errors="coerce").mean()), 4) if not smish_log.empty else 0
    lines = [
        "# Adversarial Validation Report",
        "",
        f"- Input path: `{relpath(VAL_CLEAN)}`",
        f"- Output val_adv_10: `{relpath(VAL_ADV_10)}`",
        f"- Output val_adv_20: `{relpath(VAL_ADV_20)}`",
        f"- Log path: `{relpath(VAL_ADV_LOG)}`",
        f"- Seed: {ADVERSARIAL_SEED}",
        "- Purpose: GA fitness evaluation only.",
        "",
        "## Clean Validation Counts",
        "",
        *markdown_table(["Label", "Count"], sorted(clean_counts.items())),
        "",
        "## Adversarial Validation Counts",
        "",
        *markdown_table(["Artifact", "Rows", "Ham", "Smishing", "Matches val_clean row count"], rows),
        "",
        "## Perturbation Summary",
        "",
        *markdown_table(
            ["Metric", "Value"],
            [
                ("smishing perturbation log rows", smish_perturbed),
                ("ham unchanged log rows", ham_unchanged),
                ("average smishing perturbation rate", avg_rate),
                ("quality pass smishing rows", int(smish_log["quality_status"].eq("pass").sum()) if not smish_log.empty else 0),
                ("quality fail smishing rows", int(smish_log["quality_status"].ne("pass").sum()) if not smish_log.empty else 0),
            ],
        ),
        "",
        "## Technique Distribution",
        "",
        *markdown_table(["Technique", "Count"], sorted(technique_counter(smish_log["perturbation_techniques"]).items()) if not smish_log.empty else []),
    ]
    write_text(REPORTS_DIR / "adversarial_validation_report.md", lines)


def main() -> int:
    built, _ = create_adversarial_validation_sets()
    for level, df in built.items():
        print(f"Validation adversarial level {level}: rows={len(df)} labels={dict(label_counts(df))}")
    print(f"Report: {relpath(REPORTS_DIR / 'adversarial_validation_report.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

