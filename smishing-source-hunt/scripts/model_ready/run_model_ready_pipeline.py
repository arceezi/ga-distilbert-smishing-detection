"""Run the full model-ready dataset pipeline in the required order."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

STEPS = [
    "prepare_final_clean_dataset.py",
    "create_clean_splits.py",
    "create_augmented_training_set.py",
    "create_adversarial_validation_sets.py",
    "create_adversarial_test_sets.py",
    "validate_model_ready_datasets.py",
    "generate_model_ready_reports.py",
]


def main() -> int:
    scripts_dir = ROOT / "scripts" / "model_ready"
    for script in STEPS:
        path = scripts_dir / script
        print(f"\n=== Running {path.relative_to(ROOT).as_posix()} ===")
        result = subprocess.run([sys.executable, str(path)], cwd=ROOT)
        if result.returncode != 0:
            print(f"Pipeline stopped at {script} with exit code {result.returncode}.")
            return result.returncode
    print("\nModel-ready pipeline completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

