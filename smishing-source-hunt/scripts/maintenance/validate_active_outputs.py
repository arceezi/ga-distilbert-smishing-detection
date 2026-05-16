"""Validate active thesis outputs after project organization."""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT_PATH = ROOT / "reports" / "active_outputs_validation_report.md"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def check(name: str, condition: bool, detail: str, results: list[tuple[str, bool, str]]) -> None:
    results.append((name, condition, detail))


def validate_manifest_checksums(results: list[tuple[str, bool, str]]) -> None:
    manifest = ROOT / "manifests" / "file_move_manifest.csv"
    if not manifest.exists():
        check("file_move_manifest exists", False, "Missing manifests/file_move_manifest.csv", results)
        return

    mismatches = []
    checked = 0
    with manifest.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("action") not in {"copied", "moved", "retained_original"}:
                continue
            new_path = ROOT / row["new_path"]
            if not new_path.exists() or not new_path.is_file():
                mismatches.append(f"missing {row['new_path']}")
                continue
            checked += 1
            expected = row.get("sha256_before")
            actual = sha256(new_path)
            if expected and actual != expected:
                mismatches.append(row["new_path"])
    check("checksums match copied files", not mismatches, f"{checked} files checked; mismatches: {len(mismatches)}", results)


def main() -> int:
    results: list[tuple[str, bool, str]] = []

    v3 = ROOT / "data/05_final_datasets/active/final_v3_research_synthetic_balanced_10544.csv"
    expert = ROOT / "data/04_expert_review_iaa/active_packet/expert_review_packet_500_balanced_raw_complete.csv"
    expert_xlsx = ROOT / "data/04_expert_review_iaa/active_packet/expert_review_packet_500_balanced_raw_complete.xlsx"
    manual = ROOT / "data/02_manual_ham/cleaned/approved_manual_ham_cleaned_320.csv"
    public_master = ROOT / "data/05_final_datasets/active/public_master_campaign_family_filtered_10226.csv"

    check("active final V3 file exists", v3.exists(), v3.relative_to(ROOT).as_posix(), results)
    if v3.exists():
        rows = read_csv(v3)
        ham = sum(1 for row in rows if row.get("normalized_label") == "ham")
        smishing = sum(1 for row in rows if row.get("normalized_label") == "smishing")
        synthetic_smishing = sum(1 for row in rows if row.get("normalized_label") == "smishing" and str(row.get("is_synthetic", "")).lower() == "true")
        check("V3 has ham=5,272 and smishing=5,272", ham == 5272 and smishing == 5272, f"ham={ham}, smishing={smishing}", results)
        check("V3 has no synthetic smishing", synthetic_smishing == 0, f"synthetic_smishing={synthetic_smishing}", results)

    check("active expert packet exists", expert_xlsx.exists(), expert_xlsx.relative_to(ROOT).as_posix(), results)
    if expert.exists():
        expert_rows = read_csv(expert)
        check("expert packet has 500 rows if available", len(expert_rows) == 500, f"rows={len(expert_rows)}", results)
    else:
        check("expert packet has 500 rows if available", False, f"Missing {expert.relative_to(ROOT).as_posix()}", results)

    check("manual ham cleaned file exists", manual.exists(), manual.relative_to(ROOT).as_posix(), results)
    if manual.exists():
        manual_rows = read_csv(manual)
        check("manual ham cleaned file has 320 rows", len(manual_rows) == 320, f"rows={len(manual_rows)}", results)

    check("public master campaign-family file exists", public_master.exists(), public_master.relative_to(ROOT).as_posix(), results)

    for manifest_name in [
        "file_move_manifest.csv",
        "active_dataset_manifest.csv",
        "script_inventory.csv",
        "pipeline_stage_manifest.csv",
    ]:
        path = ROOT / "manifests" / manifest_name
        check(f"{manifest_name} exists", path.exists(), path.relative_to(ROOT).as_posix(), results)

    for path in [v3, expert_xlsx, manual, public_master]:
        check(f"{path.name} is not empty", path.exists() and path.stat().st_size > 0, path.relative_to(ROOT).as_posix(), results)

    validate_manifest_checksums(results)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# Active Outputs Validation Report", ""]
    failed = [item for item in results if not item[1]]
    lines.append(f"Validation status: {'PASS' if not failed else 'FAIL'}")
    lines.append("")
    for name, ok, detail in results:
        lines.append(f"- [{'x' if ok else ' '}] {name}: {detail}")
    lines.append("")
    lines.append("## Active Output Paths")
    lines.append("")
    lines.append("- Main expanded dataset: data/05_final_datasets/active/final_v3_research_synthetic_balanced_10544.csv")
    lines.append("- Real-only baseline: data/05_final_datasets/active/baseline_v1_public_real_only_balanced_9908.csv")
    lines.append("- Expert packet: data/04_expert_review_iaa/active_packet/expert_review_packet_500_balanced_raw_complete.xlsx")
    lines.append("- Manual ham: data/02_manual_ham/cleaned/approved_manual_ham_cleaned_320.csv")
    lines.append("- Manifest: manifests/active_dataset_manifest.csv")
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")

    print(f"Validation status: {'PASS' if not failed else 'FAIL'}")
    print(f"Report: {REPORT_PATH.relative_to(ROOT).as_posix()}")
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'} - {name}: {detail}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
