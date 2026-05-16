"""Safely copy thesis dataset artifacts into a cleaner folder structure.

Default mode is copy-only. Use --move only after verifying the manifest.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import shutil
from pathlib import Path

from project_organization_config import ALL_COPY_RULES, SCRIPT_STAGE_MAP, TARGET_DIRECTORIES


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = ROOT / "manifests" / "file_move_manifest.csv"
MANIFEST_COLUMNS = [
    "original_path",
    "new_path",
    "action",
    "file_size_bytes",
    "sha256_before",
    "sha256_after",
    "status",
    "notes",
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_row(rows: list[dict[str, str]], src: Path, dst: Path, action: str, status: str, notes: str = "") -> None:
    before = sha256(src) if src.exists() and src.is_file() else ""
    after = sha256(dst) if dst.exists() and dst.is_file() else ""
    size = str(src.stat().st_size) if src.exists() and src.is_file() else ""
    rows.append(
        {
            "original_path": rel(src) if src.is_absolute() and src.exists() else src.as_posix(),
            "new_path": rel(dst) if dst.is_absolute() else dst.as_posix(),
            "action": action,
            "file_size_bytes": size,
            "sha256_before": before,
            "sha256_after": after,
            "status": status,
            "notes": notes,
        }
    )


def safe_copy_file(src: Path, dst: Path, rows: list[dict[str, str]], move: bool, notes: str = "") -> str:
    if not src.exists():
        write_row(rows, src, dst, "skipped_missing", "missing_source", notes)
        return "skipped_missing"

    dst.parent.mkdir(parents=True, exist_ok=True)
    before = sha256(src)
    if dst.exists():
        after = sha256(dst)
        if before == after:
            write_row(rows, src, dst, "retained_original", "already_current", notes)
            return "already_current"
        alternate = dst.with_name(f"{dst.stem}_copy_from_legacy{dst.suffix}")
        counter = 2
        while alternate.exists():
            alternate = dst.with_name(f"{dst.stem}_copy_from_legacy_{counter}{dst.suffix}")
            counter += 1
        dst = alternate

    if move:
        shutil.move(str(src), str(dst))
        action = "moved"
    else:
        shutil.copy2(src, dst)
        action = "copied"
    write_row(rows, src, dst, action, "ok", notes)
    return action


def copy_tree(src: Path, dst: Path, rows: list[dict[str, str]], move: bool, notes: str = "") -> dict[str, int]:
    counts = {"copied": 0, "moved": 0, "already_current": 0, "skipped_missing": 0}
    if not src.exists():
        write_row(rows, src, dst, "skipped_missing", "missing_source", notes)
        counts["skipped_missing"] += 1
        return counts

    for file_path in src.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.is_relative_to(dst):
            continue
        if dst.is_relative_to(src) and file_path.relative_to(src).parts[:1] == dst.relative_to(src).parts[:1]:
            continue
        relative = file_path.relative_to(src)
        status = safe_copy_file(file_path, dst / relative, rows, move, notes)
        counts[status if status in counts else "copied"] += 1
    return counts


def copy_scripts(rows: list[dict[str, str]], move: bool) -> dict[str, int]:
    counts = {"copied": 0, "moved": 0, "already_current": 0, "skipped_missing": 0}
    for stage, names in SCRIPT_STAGE_MAP.items():
        for name in names:
            dst = ROOT / "scripts" / stage / name
            src = dst if stage == "maintenance" else ROOT / "scripts" / name
            status = safe_copy_file(src, dst, rows, move, "Categorized script copy; original retained for compatibility unless --move is used.")
            counts[status if status in counts else "copied"] += 1
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Organize smishing thesis workspace without deleting files.")
    parser.add_argument("--move", action="store_true", help="Move files instead of copying. Default is copy-only.")
    args = parser.parse_args()

    rows: list[dict[str, str]] = []
    for directory in TARGET_DIRECTORIES:
        (ROOT / directory).mkdir(parents=True, exist_ok=True)

    totals = {"copied": 0, "moved": 0, "already_current": 0, "skipped_missing": 0}
    for rule in ALL_COPY_RULES:
        src = ROOT / rule.source
        dst = ROOT / rule.destination
        if src.exists() and src.is_dir():
            counts = copy_tree(src, dst, rows, args.move, rule.notes)
        else:
            status = safe_copy_file(src, dst, rows, args.move, rule.notes)
            counts = {status if status in totals else "copied": 1}
        for key, value in counts.items():
            totals[key] = totals.get(key, 0) + value

    script_counts = copy_scripts(rows, args.move)
    for key, value in script_counts.items():
        totals[key] = totals.get(key, 0) + value

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=MANIFEST_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print("Project organization complete.")
    print(f"Mode: {'move' if args.move else 'copy-only'}")
    print(f"Folders created: {len(TARGET_DIRECTORIES)}")
    print(f"Files copied: {totals.get('copied', 0)}")
    print(f"Files moved: {totals.get('moved', 0)}")
    print(f"Already current: {totals.get('already_current', 0)}")
    print(f"Missing sources skipped: {totals.get('skipped_missing', 0)}")
    print(f"File move manifest: {MANIFEST_PATH.relative_to(ROOT).as_posix()}")
    print("Active dataset path: data/05_final_datasets/active/final_v3_research_synthetic_balanced_10544.csv")
    print("Expert packet path: data/04_expert_review_iaa/active_packet/expert_review_packet_500_balanced_raw_complete.xlsx")
    print("Manual ham path: data/02_manual_ham/cleaned/approved_manual_ham_cleaned_320.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
