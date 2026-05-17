"""Train and evaluate DistilBERT baselines for the smishing thesis.

This script covers the manuscript's DistilBERT responsibility:

* Baseline 2: fine-tuned DistilBERT on clean training data.
* Ablation B: the same model trained on adversarially augmented training data.

It writes metrics, row-level predictions, confusion-matrix figures, and model
checkpoints into the thesis-modeling output folders.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer, get_linear_schedule_with_warmup


TEXT_COLUMN = "model_text"
LABEL_COLUMN = "label_id"
ID_COLUMN = "final_row_id"
MODEL_NAME = "distilbert-base-cased"
TEST_CONDITIONS = {
    "clean": ("clean", "test_clean.csv"),
    "adv_10": ("adversarial_test", "test_adv_10.csv"),
    "adv_20": ("adversarial_test", "test_adv_20.csv"),
    "adv_30": ("adversarial_test", "test_adv_30.csv"),
}


@dataclass
class TrainConfig:
    base_dir: str
    model_name: str = MODEL_NAME
    max_length: int = 128
    batch_size: int = 32
    learning_rate: float = 2e-5
    weight_decay: float = 0.01
    max_epochs: int = 10
    patience: int = 3
    warmup_ratio: float = 0.10
    grad_clip_norm: float = 1.0
    threshold: float = 0.5
    seeds: tuple[int, ...] = (42, 7, 123)
    smoke_test: bool = False
    smoke_train_rows: int = 96
    smoke_eval_rows: int = 64


class SmsDataset(Dataset):
    def __init__(self, frame: pd.DataFrame, tokenizer: AutoTokenizer, max_length: int):
        texts = frame[TEXT_COLUMN].fillna("").astype(str).tolist()
        labels = frame[LABEL_COLUMN].astype(int).to_numpy()
        self.ids = frame[ID_COLUMN].astype(str).tolist() if ID_COLUMN in frame.columns else [str(i) for i in range(len(frame))]
        self.labels = torch.tensor(labels, dtype=torch.long)
        self.encodings = tokenizer(
            texts,
            truncation=True,
            padding=True,
            max_length=max_length,
            return_tensors="pt",
        )

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, index: int) -> dict[str, torch.Tensor]:
        item = {key: value[index] for key, value in self.encodings.items()}
        item["labels"] = self.labels[index]
        return item


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def ensure_dirs(base_dir: Path) -> dict[str, Path]:
    paths = {
        "metrics": base_dir / "results" / "metrics",
        "predictions": base_dir / "results" / "predictions",
        "figures": base_dir / "results" / "figures",
        "models": base_dir / "trained_models",
        "reports": base_dir / "reports",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def read_csv(path: Path, smoke_rows: int | None = None) -> pd.DataFrame:
    frame = pd.read_csv(path)
    if smoke_rows is not None:
        frame = frame.head(smoke_rows).copy()
    missing = {TEXT_COLUMN, LABEL_COLUMN} - set(frame.columns)
    if missing:
        raise ValueError(f"{path} is missing required column(s): {sorted(missing)}")
    frame[TEXT_COLUMN] = frame[TEXT_COLUMN].fillna("").astype(str)
    frame[LABEL_COLUMN] = frame[LABEL_COLUMN].astype(int)
    return frame


def class_weights(labels: Iterable[int], device: torch.device) -> torch.Tensor:
    values = np.asarray(list(labels), dtype=np.int64)
    counts = np.bincount(values, minlength=2)
    total = counts.sum()
    weights = total / (2.0 * np.maximum(counts, 1))
    return torch.tensor(weights, dtype=torch.float32, device=device)


def make_loader(dataset: SmsDataset, batch_size: int, shuffle: bool) -> DataLoader:
    return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)


def batch_to_device(batch: dict[str, torch.Tensor], device: torch.device) -> dict[str, torch.Tensor]:
    return {key: value.to(device) for key, value in batch.items()}


def train_one_epoch(
    model: AutoModelForSequenceClassification,
    loader: DataLoader,
    optimizer: AdamW,
    scheduler,
    criterion: nn.Module,
    device: torch.device,
    grad_clip_norm: float,
) -> float:
    model.train()
    total_loss = 0.0
    total_count = 0
    for batch in loader:
        batch = batch_to_device(batch, device)
        labels = batch.pop("labels")
        optimizer.zero_grad(set_to_none=True)
        logits = model(**batch).logits
        loss = criterion(logits, labels)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), grad_clip_norm)
        optimizer.step()
        scheduler.step()
        total_loss += loss.item() * labels.size(0)
        total_count += labels.size(0)
    return total_loss / max(total_count, 1)


@torch.no_grad()
def predict(
    model: AutoModelForSequenceClassification,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> tuple[float, np.ndarray, np.ndarray]:
    model.eval()
    total_loss = 0.0
    total_count = 0
    all_probs: list[np.ndarray] = []
    all_labels: list[np.ndarray] = []
    for batch in loader:
        batch = batch_to_device(batch, device)
        labels = batch.pop("labels")
        logits = model(**batch).logits
        loss = criterion(logits, labels)
        probs = torch.softmax(logits, dim=1)[:, 1]
        total_loss += loss.item() * labels.size(0)
        total_count += labels.size(0)
        all_probs.append(probs.cpu().numpy())
        all_labels.append(labels.cpu().numpy())
    return total_loss / max(total_count, 1), np.concatenate(all_probs), np.concatenate(all_labels)


def compute_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float) -> dict[str, float | int]:
    y_pred = (y_prob >= threshold).astype(int)
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    accuracy = (tp + tn) / max(len(y_true), 1)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-12)
    fnr = fn / max(fn + tp, 1)
    fpr = fp / max(fp + tn, 1)
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fnr": fnr,
        "fpr": fpr,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "support": int(len(y_true)),
    }


def save_confusion_matrix(metrics: dict[str, float | int], title: str, path: Path) -> None:
    matrix = np.array([[metrics["tn"], metrics["fp"]], [metrics["fn"], metrics["tp"]]], dtype=int)
    fig, ax = plt.subplots(figsize=(4.8, 4.2))
    image = ax.imshow(matrix, cmap="Blues")
    ax.set_title(title)
    ax.set_xticks([0, 1], labels=["Pred 0", "Pred 1"])
    ax.set_yticks([0, 1], labels=["True 0", "True 1"])
    for row in range(2):
        for col in range(2):
            ax.text(col, row, str(matrix[row, col]), ha="center", va="center", color="black")
    fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def train_model(
    run_name: str,
    train_frame: pd.DataFrame,
    val_frame: pd.DataFrame,
    test_frames: dict[str, pd.DataFrame],
    tokenizer: AutoTokenizer,
    cfg: TrainConfig,
    output_paths: dict[str, Path],
    seed: int,
    device: torch.device,
) -> list[dict[str, float | int | str]]:
    set_seed(seed)
    model = AutoModelForSequenceClassification.from_pretrained(cfg.model_name, num_labels=2).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights(train_frame[LABEL_COLUMN], device))

    train_dataset = SmsDataset(train_frame, tokenizer, cfg.max_length)
    val_dataset = SmsDataset(val_frame, tokenizer, cfg.max_length)
    train_loader = make_loader(train_dataset, cfg.batch_size, shuffle=True)
    val_loader = make_loader(val_dataset, cfg.batch_size, shuffle=False)

    total_steps = max(len(train_loader) * cfg.max_epochs, 1)
    warmup_steps = int(math.ceil(total_steps * cfg.warmup_ratio))
    optimizer = AdamW(model.parameters(), lr=cfg.learning_rate, weight_decay=cfg.weight_decay)
    scheduler = get_linear_schedule_with_warmup(optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps)

    best_val_loss = float("inf")
    best_state = None
    stale_epochs = 0
    history = []
    start_time = time.time()

    for epoch in range(1, cfg.max_epochs + 1):
        train_loss = train_one_epoch(model, train_loader, optimizer, scheduler, criterion, device, cfg.grad_clip_norm)
        val_loss, val_prob, val_true = predict(model, val_loader, criterion, device)
        val_metrics = compute_metrics(val_true, val_prob, cfg.threshold)
        history.append({"epoch": epoch, "train_loss": train_loss, "val_loss": val_loss, **val_metrics})
        print(
            f"{run_name} seed={seed} epoch={epoch} "
            f"train_loss={train_loss:.4f} val_loss={val_loss:.4f} "
            f"val_recall={val_metrics['recall']:.4f} val_f1={val_metrics['f1']:.4f}"
        )
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state = {key: value.cpu().clone() for key, value in model.state_dict().items()}
            stale_epochs = 0
        else:
            stale_epochs += 1
            if stale_epochs >= cfg.patience:
                print(f"{run_name} seed={seed}: early stopping at epoch {epoch}")
                break

    if best_state is not None:
        model.load_state_dict(best_state)

    run_dir = output_paths["models"] / f"{run_name}_seed{seed}"
    run_dir.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(run_dir)
    tokenizer.save_pretrained(run_dir)

    history_path = output_paths["metrics"] / f"{run_name}_seed{seed}_training_history.csv"
    pd.DataFrame(history).to_csv(history_path, index=False)

    rows: list[dict[str, float | int | str]] = []
    for condition, frame in test_frames.items():
        dataset = SmsDataset(frame, tokenizer, cfg.max_length)
        loader = make_loader(dataset, cfg.batch_size, shuffle=False)
        test_loss, y_prob, y_true = predict(model, loader, criterion, device)
        metrics = compute_metrics(y_true, y_prob, cfg.threshold)
        metrics_row = {
            "model": run_name,
            "seed": seed,
            "condition": condition,
            "test_loss": test_loss,
            "threshold": cfg.threshold,
            "runtime_seconds": round(time.time() - start_time, 3),
            **metrics,
        }
        rows.append(metrics_row)

        prediction_frame = pd.DataFrame(
            {
                ID_COLUMN: dataset.ids,
                "model": run_name,
                "seed": seed,
                "condition": condition,
                "y_true": y_true,
                "y_prob_smishing": y_prob,
                "y_pred": (y_prob >= cfg.threshold).astype(int),
            }
        )
        prediction_frame.to_csv(output_paths["predictions"] / f"{run_name}_seed{seed}_{condition}_predictions.csv", index=False)
        save_confusion_matrix(
            metrics,
            f"{run_name} seed {seed} - {condition}",
            output_paths["figures"] / f"{run_name}_seed{seed}_{condition}_confusion_matrix.png",
        )

    with (run_dir / "run_config.json").open("w", encoding="utf-8") as handle:
        json.dump({"run_name": run_name, "seed": seed, **asdict(cfg)}, handle, indent=2)
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-dir", type=Path, default=Path("."), help="Path to thesis-modeling directory.")
    parser.add_argument("--models", nargs="+", default=["baseline2_clean", "ablation_b_augmented"], choices=["baseline2_clean", "ablation_b_augmented"])
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 7, 123])
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--smoke-test", action="store_true", help="Run on small row counts for a quick pipeline check.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = args.base_dir.resolve()
    cfg = TrainConfig(
        base_dir=str(base_dir),
        batch_size=args.batch_size,
        max_epochs=args.epochs,
        seeds=tuple(args.seeds),
        smoke_test=args.smoke_test,
    )
    output_paths = ensure_dirs(base_dir)
    data_dir = base_dir / "data" / "06_model_ready"
    smoke_train_rows = cfg.smoke_train_rows if cfg.smoke_test else None
    smoke_eval_rows = cfg.smoke_eval_rows if cfg.smoke_test else None

    clean_train = read_csv(data_dir / "clean" / "train_clean.csv", smoke_train_rows)
    augmented_train = read_csv(data_dir / "augmented_training" / "train_augmented_for_ablation_b.csv", smoke_train_rows)
    val_frame = read_csv(data_dir / "clean" / "val_clean.csv", smoke_eval_rows)
    test_frames = {
        name: read_csv(data_dir / folder / filename, smoke_eval_rows)
        for name, (folder, filename) in TEST_CONDITIONS.items()
    }

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    print(f"Loading tokenizer/model family: {cfg.model_name}")
    tokenizer = AutoTokenizer.from_pretrained(cfg.model_name)

    all_metrics: list[dict[str, float | int | str]] = []
    for model_key in args.models:
        train_frame = clean_train if model_key == "baseline2_clean" else augmented_train
        for seed in args.seeds:
            all_metrics.extend(train_model(model_key, train_frame, val_frame, test_frames, tokenizer, cfg, output_paths, seed, device))

    metrics_frame = pd.DataFrame(all_metrics)
    suffix = "smoke" if cfg.smoke_test else "full"
    metrics_path = output_paths["metrics"] / f"distilbert_baselines_{suffix}_metrics.csv"
    metrics_frame.to_csv(metrics_path, index=False)
    summary_path = output_paths["reports"] / f"distilbert_baselines_{suffix}_summary.md"
    with summary_path.open("w", encoding="utf-8") as handle:
        handle.write("# DistilBERT Baselines Summary\n\n")
        handle.write(f"- Device: `{device}`\n")
        handle.write(f"- Model family: `{cfg.model_name}`\n")
        handle.write(f"- Seeds: `{list(args.seeds)}`\n")
        handle.write(f"- Smoke test: `{cfg.smoke_test}`\n\n")
        handle.write("```text\n")
        handle.write(metrics_frame.to_string(index=False))
        handle.write("\n```\n")
        handle.write("\n")
    print(f"Wrote metrics: {metrics_path}")
    print(f"Wrote summary: {summary_path}")


if __name__ == "__main__":
    main()
