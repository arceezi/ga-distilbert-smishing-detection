"""Generate thesis-friendly manifests for active datasets, scripts, and stages."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

from project_organization_config import SCRIPT_PURPOSE, SCRIPT_STAGE_MAP


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_DIR = ROOT / "manifests"


def count_csv(path: Path) -> dict[str, str]:
    if not path.exists() or path.suffix.lower() != ".csv":
        return {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    labels = Counter(row.get("normalized_label") or row.get("final_label") or row.get("source_label") for row in rows)
    origins = Counter(row.get("data_origin", "") for row in rows)
    synthetic = sum(1 for row in rows if str(row.get("is_synthetic", "")).lower() == "true" or row.get("data_origin") == "synthetic_template")
    manual = origins.get("manual_real", 0)
    public_ham = sum(1 for row in rows if row.get("normalized_label") == "ham" and row.get("data_origin") == "public_real")
    public_smishing = sum(1 for row in rows if row.get("normalized_label") == "smishing" and row.get("data_origin") == "public_real")
    return {
        "rows": str(len(rows)),
        "ham_count": str(labels.get("ham", 0)),
        "smishing_count": str(labels.get("smishing", 0)),
        "synthetic_ham_count": str(synthetic),
        "manual_ham_count": str(manual),
        "public_ham_count": str(public_ham),
        "public_smishing_count": str(public_smishing),
    }


def active_dataset_manifest() -> None:
    rows = [
        {
            "dataset_name": "final_v3_research_synthetic_balanced_10544",
            "active_path": "data/05_final_datasets/active/final_v3_research_synthetic_balanced_10544.csv",
            "original_path": "data/final_dataset_build/final/dataset_v3_public_manual_research_synthetic_ham_balanced.csv",
            "purpose": "Main expanded balanced thesis dataset with public, manual, and research-backed synthetic ham.",
            "status": "active_preferred",
            "notes": "Use for expanded thesis experiments; synthetic rows are ham only.",
        },
        {
            "dataset_name": "baseline_v1_public_real_only_balanced_9908",
            "active_path": "data/05_final_datasets/active/baseline_v1_public_real_only_balanced_9908.csv",
            "original_path": "data/final_dataset_build/final/dataset_v1_public_real_only_balanced.csv",
            "purpose": "Real-only public baseline.",
            "status": "active_baseline",
            "notes": "Use for real-only comparison.",
        },
        {
            "dataset_name": "baseline_v2_public_manual_ham_balanced",
            "active_path": "data/05_final_datasets/active/baseline_v2_public_manual_ham_balanced.csv",
            "original_path": "data/final_dataset_build/final/dataset_v2_public_plus_manual_ham_balanced.csv",
            "purpose": "Public data plus reviewed manual ham.",
            "status": "active_baseline",
            "notes": "Use to isolate the effect of manual ham before synthetic augmentation.",
        },
        {
            "dataset_name": "public_master_campaign_family_filtered_10226",
            "active_path": "data/05_final_datasets/active/public_master_campaign_family_filtered_10226.csv",
            "original_path": "data/organized/campaign_family_quality/combined_public_thesis_sources_campaign_family_filtered.csv",
            "purpose": "Best public master before manual and synthetic expansion.",
            "status": "active_reference",
            "notes": "Use for public-source provenance and pre-expansion reference.",
        },
        {
            "dataset_name": "expert_review_packet_500_balanced_raw_complete",
            "active_path": "data/04_expert_review_iaa/active_packet/expert_review_packet_500_balanced_raw_complete.csv",
            "original_path": "data/expert_review_iaa/expert_spam_review_500_balanced_raw_complete.csv",
            "purpose": "Expert review / IAA packet.",
            "status": "active_preferred_packet",
            "notes": "Rows are for expert review and are not yet part of the final dataset.",
        },
        {
            "dataset_name": "approved_manual_ham_cleaned_320",
            "active_path": "data/02_manual_ham/cleaned/approved_manual_ham_cleaned_320.csv",
            "original_path": "data/manual_ham_drive/final/approved_manual_ham_cleaned.csv",
            "purpose": "Reviewed and cleaned manual ham source.",
            "status": "active_source",
            "notes": "Use as manual ham provenance source.",
        },
    ]
    fieldnames = [
        "dataset_name",
        "active_path",
        "original_path",
        "rows",
        "ham_count",
        "smishing_count",
        "synthetic_ham_count",
        "manual_ham_count",
        "public_ham_count",
        "public_smishing_count",
        "purpose",
        "status",
        "notes",
    ]
    for row in rows:
        counts = count_csv(ROOT / row["active_path"])
        for key in fieldnames:
            row.setdefault(key, counts.get(key, ""))
        row.update(counts)
    with (MANIFEST_DIR / "active_dataset_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def script_inventory() -> None:
    rows = []
    for stage, names in SCRIPT_STAGE_MAP.items():
        for name in names:
            old_path = ROOT / "scripts" / name
            organized_path = ROOT / "scripts" / stage / name
            rows.append(
                {
                    "script_name": name,
                    "old_path": f"scripts/{name}",
                    "organized_path": f"scripts/{stage}/{name}",
                    "pipeline_stage": stage,
                    "purpose": SCRIPT_PURPOSE.get(name, ""),
                    "current_status": "organized_copy_present" if organized_path.exists() else "missing_organized_copy",
                    "notes": "Original retained for legacy compatibility." if old_path.exists() else "Original not present in legacy scripts root.",
                }
            )
    with (MANIFEST_DIR / "script_inventory.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["script_name", "old_path", "organized_path", "pipeline_stage", "purpose", "current_status", "notes"],
        )
        writer.writeheader()
        writer.writerows(rows)


def pipeline_stage_manifest() -> None:
    rows = [
        ["1", "Raw public/source gathering", "data/source_archives/public_baseline; data/raw/collected_smishing_candidates.csv; data/external_datasets", "data/00_raw_sources", "scripts/public_sources/*; import_* scripts", "reports/source_coverage.md; reports/acquisition_progress.md", "archive_and_reference", "Raw source files retained for traceability."],
        ["2", "Public source standardization", "data/00_raw_sources/public_baseline", "data/01_working/public_source_organization", "scripts/public_sources/organize_public_sources.py", "reports/public_sources_organization.md", "working", "Uniform source files are compatibility copies."],
        ["3", "Duplicate/overlap audit", "data/01_working/public_source_organization", "data/01_working/public_source_organization/duplicate_overlap_clusters.csv", "scripts/public_sources/analyze_uniform_duplicates.py", "reports/dataset_balance_tracker.md", "working", "Overlap artifacts retained."],
        ["4", "Raw/clean text verification", "data/01_working/public_source_organization", "data/01_working/raw_text_verification", "scripts/raw_text/verify_and_add_raw_clean_text_columns.py; scripts/raw_text/classify_raw_text_availability.py", "reports/raw_clean_text_verification.md", "working", "Verifies raw and clean text columns."],
        ["5", "Redacted raw recovery/replacement", "data/01_working/raw_text_verification", "data/01_working/raw_recovery", "scripts/raw_text/recover_or_replace_redacted_gathered_smishing.py", "reports/gathered_7k_raw_replacement_report.md", "working", "Raw recovery outputs retained."],
        ["6", "Strict raw quality validation", "data/01_working/raw_recovery", "data/01_working/raw_quality", "scripts/raw_text/audit_strict_raw_text_quality.py; scripts/raw_text/repair_strict_raw_text_dataset.py", "reports/strict_raw_text_quality_audit.md; reports/strict_raw_text_repair_report.md", "working", "Strict raw-quality outputs retained."],
        ["7", "Smishing content quality filtering", "data/01_working/raw_quality", "data/01_working/content_quality", "scripts/content_quality/audit_smishing_content_quality.py; scripts/content_quality/build_content_quality_filtered_dataset.py", "reports/smishing_content_quality_audit.md; reports/content_quality_filtered_dataset_report.md", "working", "Content-quality outputs retained."],
        ["8", "Strong campaign-family deduplication", "data/01_working/content_quality", "data/01_working/campaign_family_quality; data/05_final_datasets/active/public_master_campaign_family_filtered_10226.csv", "scripts/content_quality/audit_strong_campaign_families.py; scripts/content_quality/build_campaign_family_filtered_dataset.py", "reports/strong_campaign_family_audit.md; reports/campaign_family_filtered_dataset_report.md", "active_reference", "Current best public master."],
        ["9", "Manual ham extraction/review", "data/00_raw_sources/manual_ham_drive", "data/02_manual_ham/extracted; data/02_manual_ham/reviewed", "scripts/manual_ham/import_manual_ham_drive.py; scripts/manual_ham/create_manual_ham_review_excel.py; scripts/manual_ham/validate_manual_ham_review.py", "reports/manual_ham_drive_summary.md", "working", "Manual review artifacts retained."],
        ["10", "Manual ham split/artifact cleanup", "data/02_manual_ham/reviewed", "data/02_manual_ham/cleaned/approved_manual_ham_cleaned_320.csv", "scripts/manual_ham/detect_manual_ham_split_messages.py; scripts/manual_ham/remove_manual_ham_artifacts.py", "reports/manual_ham_split_detection_report.md; reports/manual_ham_artifact_cleanup_report.md", "active_source", "Cleaned manual ham source."],
        ["11", "Research-backed synthetic ham generation", "data/02_manual_ham/cleaned; data/03_synthetic_ham/template_research", "data/03_synthetic_ham/research_backed", "scripts/synthetic_ham/create_research_backed_ham_template_library.py; scripts/synthetic_ham/generate_research_backed_synthetic_ham.py", "data/03_synthetic_ham/research_backed/*.md", "working", "Synthetic rows remain separately marked."],
        ["12", "Final dataset builds", "data/01_working/campaign_family_quality; data/02_manual_ham/cleaned; data/03_synthetic_ham/research_backed", "data/05_final_datasets/active", "scripts/final_dataset_build/*", "data/05_final_datasets/reports", "active", "Use ACTIVE_OUTPUTS.md for current files."],
        ["13", "Expert review / IAA packet construction", "data/05_final_datasets/active/public_master_campaign_family_filtered_10226.csv; data/04_expert_review_iaa/pools", "data/04_expert_review_iaa/active_packet", "scripts/expert_review_iaa/*", "data/04_expert_review_iaa/reports", "active_packet", "Expert review rows are not final training labels yet."],
    ]
    with (MANIFEST_DIR / "pipeline_stage_manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["stage_number", "stage_name", "input_files", "output_files", "script_files", "report_files", "active_or_archive", "notes"])
        writer.writerows(rows)


def main() -> int:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    active_dataset_manifest()
    script_inventory()
    pipeline_stage_manifest()
    print("Generated manifests:")
    print("manifests/active_dataset_manifest.csv")
    print("manifests/script_inventory.csv")
    print("manifests/pipeline_stage_manifest.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
