"""Shared helpers for the model-ready thesis dataset pipeline."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

INPUT_DATASET = ROOT / "data" / "final_dataset_build" / "final" / "dataset_v3_public_manual_research_synthetic_ham_balanced.csv"
MODEL_READY_DIR = ROOT / "data" / "06_model_ready"
CLEAN_DIR = MODEL_READY_DIR / "clean"
AUGMENTED_TRAINING_DIR = MODEL_READY_DIR / "augmented_training"
ADV_VALIDATION_DIR = MODEL_READY_DIR / "adversarial_validation"
ADV_TEST_DIR = MODEL_READY_DIR / "adversarial_test"
REPORTS_DIR = MODEL_READY_DIR / "reports"
MANIFESTS_DIR = MODEL_READY_DIR / "manifests"

FINAL_CLEAN_DATASET = CLEAN_DIR / "final_clean_dataset.csv"
TRAIN_CLEAN = CLEAN_DIR / "train_clean.csv"
VAL_CLEAN = CLEAN_DIR / "val_clean.csv"
TEST_CLEAN = CLEAN_DIR / "test_clean.csv"

TRAIN_AUGMENTED = AUGMENTED_TRAINING_DIR / "train_augmented_for_ablation_b.csv"
TRAIN_AUGMENTED_METADATA = AUGMENTED_TRAINING_DIR / "train_augmented_for_ablation_b_metadata.csv"
AUGMENTATION_LOG = AUGMENTED_TRAINING_DIR / "augmentation_log.csv"

VAL_ADV_10 = ADV_VALIDATION_DIR / "val_adv_10.csv"
VAL_ADV_20 = ADV_VALIDATION_DIR / "val_adv_20.csv"
VAL_ADV_LOG = ADV_VALIDATION_DIR / "val_adversarial_log.csv"

TEST_ADV_10 = ADV_TEST_DIR / "test_adv_10.csv"
TEST_ADV_20 = ADV_TEST_DIR / "test_adv_20.csv"
TEST_ADV_30 = ADV_TEST_DIR / "test_adv_30.csv"
TEST_ADV_LOG = ADV_TEST_DIR / "test_adversarial_log.csv"

GLOBAL_SEED = 42
SPLIT_SEED = 42
AUGMENTATION_SEED = 42
ADVERSARIAL_SEED = 42

SPLIT_RATIOS = {"train": 0.70, "val": 0.15, "test": 0.15}
AUGMENTATION_SELECTION_PERCENTAGE = 0.55
AUGMENTATION_VARIANT_DISTRIBUTION = {1: 0.70, 2: 0.25, 3: 0.05}
MAX_AUGMENTED_VARIANTS = 2200

LABEL_TO_ID = {"ham": 0, "smishing": 1}
ID_TO_LABEL = {v: k for k, v in LABEL_TO_ID.items()}

URL_RE = re.compile(
    r"https?://[^\s<>()]+|www\.[^\s<>()]+|(?<!@)\b[a-z0-9][a-z0-9.-]*\."
    r"(?:com|net|org|ph|gov|edu|co|io|app|info|me|ly|site|online|xyz|shop|biz)\S*",
    re.I,
)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b", re.I)
PHONE_RE = re.compile(r"\b(?:\+?63|0)\s?9\d{2}[\s.-]?\d{3}[\s.-]?\d{4}\b")
AMOUNT_RE = re.compile(r"\b(?:PHP|Php|php|P)\s?[\d,]+(?:\.\d{1,2})?\b|\b\d+(?:\.\d+)?\s?(?:points|pts)\b", re.I)
LONG_NUM_RE = re.compile(r"\b\d{7,14}\b")
OTP_CONTEXT_RE = re.compile(r"\b(?:otp|one[- ]time|verification|security code|passcode|code)\b", re.I)
OTP_NUM_RE = re.compile(r"\b\d{4,6}\b")
PUNCT_RE = re.compile(r"[^\w<>]+", re.UNICODE)
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

ENABLED_PERTURBATION_TECHNIQUES = [
    "homoglyph_substitution",
    "leetspeak_obfuscation",
    "separator_injection",
    "url_variation",
    "urgency_paraphrasing",
    "numeric_otp_variation",
    "spacing_punctuation_case_noise",
    "institution_substitution",
]


def ensure_model_ready_dirs() -> None:
    for path in [CLEAN_DIR, AUGMENTED_TRAINING_DIR, ADV_VALIDATION_DIR, ADV_TEST_DIR, REPORTS_DIR, MANIFESTS_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, dtype=str, keep_default_na=False)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def relpath(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_whitespace(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
    text = text.replace("\u00a0", " ").replace("\ufeff", "")
    text = CONTROL_RE.sub(" ", text)
    text = "".join(" " if unicodedata.category(char).startswith("C") else char for char in text)
    return re.sub(r"\s+", " ", text).strip()


def light_clean_model_text(value: object) -> str:
    """Clean only transport whitespace/control artifacts, preserving adversarial surface cues."""

    return normalize_whitespace(value)


def bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def bool_text(value: object) -> str:
    return "True" if bool_value(value) else "False"


def normalized_label(value: object) -> str:
    return str(value or "").strip().lower()


def normalized_message_key(value: object) -> str:
    text = unicodedata.normalize("NFKC", normalize_whitespace(value)).lower()
    text = EMAIL_RE.sub("<EMAIL>", text)
    text = URL_RE.sub("<URL>", text)
    text = PHONE_RE.sub("<PHONE>", text)
    text = AMOUNT_RE.sub("<AMOUNT>", text)
    text = LONG_NUM_RE.sub("<NUM>", text)
    if OTP_CONTEXT_RE.search(text):
        text = OTP_NUM_RE.sub("<OTP>", text)
    else:
        text = OTP_NUM_RE.sub("<NUM>", text)
    text = PUNCT_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def stable_int(*parts: object, modulo: int | None = None) -> int:
    joined = "||".join(str(part) for part in parts)
    value = int(hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16], 16)
    return value % modulo if modulo else value


def deterministic_row_seed(final_row_id: object, split: object, perturbation_level: object, base_seed: int = GLOBAL_SEED) -> int:
    return stable_int(str(final_row_id), str(split), str(perturbation_level), str(base_seed), modulo=2**32)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def label_counts(df: pd.DataFrame) -> Counter:
    if "normalized_label" not in df.columns:
        return Counter()
    return Counter(df["normalized_label"].astype(str))


def technique_counter(series: Iterable[object]) -> Counter:
    counts: Counter[str] = Counter()
    for value in series:
        for technique in str(value or "").split(";"):
            technique = technique.strip()
            if technique:
                counts[technique] += 1
    return counts


def markdown_table(headers: list[str], rows: Iterable[Iterable[object]]) -> list[str]:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return lines


def count_table(counter: Counter, key_name: str = "Value") -> list[str]:
    rows = [(key if key != "" else "blank", value) for key, value in sorted(counter.items(), key=lambda item: str(item[0]))]
    return markdown_table([key_name, "Count"], rows)


def write_text(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def output_files() -> list[Path]:
    if not MODEL_READY_DIR.exists():
        return []
    return sorted(path for path in MODEL_READY_DIR.rglob("*") if path.is_file())


def write_file_manifest() -> Path:
    ensure_model_ready_dirs()
    manifest_path = MANIFESTS_DIR / "model_ready_file_manifest.csv"
    rows = []
    for path in output_files():
        rel = relpath(path)
        if path == manifest_path:
            rows.append(
                {
                    "path": rel,
                    "bytes": path.stat().st_size,
                    "sha256": "",
                    "modified_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat(),
                    "notes": "Self hash omitted because writing this manifest changes the file.",
                }
            )
            continue
        rows.append(
            {
                "path": rel,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "modified_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).replace(microsecond=0).isoformat(),
                "notes": "",
            }
        )
    with manifest_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "bytes", "sha256", "modified_utc", "notes"])
        writer.writeheader()
        writer.writerows(rows)
    return manifest_path


def script_hashes() -> list[dict[str, str]]:
    scripts_dir = ROOT / "scripts" / "model_ready"
    rows = []
    for path in sorted(scripts_dir.glob("*.py")):
        rows.append({"path": relpath(path), "sha256": sha256_file(path)})
    return rows


def write_model_ready_config() -> Path:
    ensure_model_ready_dirs()
    config = {
        "input_dataset_path": relpath(INPUT_DATASET),
        "split_ratios": SPLIT_RATIOS,
        "seeds": {
            "global_split_seed": SPLIT_SEED,
            "augmentation_seed": AUGMENTATION_SEED,
            "adversarial_validation_test_seed": ADVERSARIAL_SEED,
        },
        "augmentation_selection_percentage": AUGMENTATION_SELECTION_PERCENTAGE,
        "augmentation_variant_distribution": AUGMENTATION_VARIANT_DISTRIBUTION,
        "perturbation_levels": {
            "training": [20],
            "validation": [10, 20],
            "test": [10, 20, 30],
        },
        "perturbation_techniques_enabled": ENABLED_PERTURBATION_TECHNIQUES,
        "max_augmented_train_variants": MAX_AUGMENTED_VARIANTS,
        "max_augmented_train_size_rule": "train_augmented_for_ablation_b <= 2x train_clean rows",
        "timestamp": now_utc(),
        "script_versions": script_hashes(),
    }
    path = MANIFESTS_DIR / "model_ready_config.json"
    path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def file_rows_summary(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"path": relpath(path), "exists": False, "rows": 0, "ham": 0, "smishing": 0}
    df = read_csv(path)
    counts = label_counts(df)
    return {
        "path": relpath(path),
        "exists": True,
        "rows": len(df),
        "ham": counts.get("ham", 0),
        "smishing": counts.get("smishing", 0),
    }
