"""Shared organization rules for the thesis dataset workspace."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CopyRule:
    source: str
    destination: str
    notes: str = ""


TARGET_DIRECTORIES = [
    "docs",
    "data/00_raw_sources/public_baseline",
    "data/00_raw_sources/gathered_candidates",
    "data/00_raw_sources/manual_ham_drive",
    "data/01_working/public_source_organization",
    "data/01_working/raw_text_verification",
    "data/01_working/raw_recovery",
    "data/01_working/raw_quality",
    "data/01_working/content_quality",
    "data/01_working/campaign_family_quality",
    "data/02_manual_ham/extracted",
    "data/02_manual_ham/reviewed",
    "data/02_manual_ham/cleaned",
    "data/02_manual_ham/templates",
    "data/02_manual_ham/archives",
    "data/03_synthetic_ham/manual_template_based",
    "data/03_synthetic_ham/research_backed",
    "data/03_synthetic_ham/template_research",
    "data/03_synthetic_ham/archives",
    "data/04_expert_review_iaa/active_packet",
    "data/04_expert_review_iaa/drafts",
    "data/04_expert_review_iaa/pools",
    "data/04_expert_review_iaa/reports",
    "data/04_expert_review_iaa/archives",
    "data/05_final_datasets/active",
    "data/05_final_datasets/previous_versions",
    "data/05_final_datasets/reserves",
    "data/05_final_datasets/reports",
    "data/99_archive/old_exports",
    "data/99_archive/old_interim",
    "data/99_archive/old_reports",
    "data/99_archive/superseded_outputs",
    "scripts/public_sources",
    "scripts/raw_text",
    "scripts/content_quality",
    "scripts/manual_ham",
    "scripts/synthetic_ham",
    "scripts/final_dataset_build",
    "scripts/expert_review_iaa",
    "scripts/maintenance",
    "reports/active",
    "reports/archive",
    "manifests",
    "prompts/archive",
]


ACTIVE_OUTPUT_RULES = [
    CopyRule(
        "data/final_dataset_build/final/dataset_v3_public_manual_research_synthetic_ham_balanced.csv",
        "data/05_final_datasets/active/final_v3_research_synthetic_balanced_10544.csv",
        "Main expanded research-backed dataset.",
    ),
    CopyRule(
        "data/final_dataset_build/final/dataset_v1_public_real_only_balanced.csv",
        "data/05_final_datasets/active/baseline_v1_public_real_only_balanced_9908.csv",
        "Real-only baseline dataset.",
    ),
    CopyRule(
        "data/final_dataset_build/final/dataset_v2_public_plus_manual_ham_balanced.csv",
        "data/05_final_datasets/active/baseline_v2_public_manual_ham_balanced.csv",
        "Public plus manual ham baseline dataset.",
    ),
    CopyRule(
        "data/organized/campaign_family_quality/combined_public_thesis_sources_campaign_family_filtered.csv",
        "data/05_final_datasets/active/public_master_campaign_family_filtered_10226.csv",
        "Best public master before manual and synthetic expansion.",
    ),
    CopyRule(
        "data/manual_ham_drive/final/approved_manual_ham_cleaned.csv",
        "data/02_manual_ham/cleaned/approved_manual_ham_cleaned_320.csv",
        "Active cleaned manual ham.",
    ),
]


FINAL_REPORT_RULES = [
    CopyRule("data/final_dataset_build/reports/research_backed_v3_build_report.md", "data/05_final_datasets/reports/research_backed_v3_build_report.md"),
    CopyRule("data/final_dataset_build/reports/research_backed_v3_validation_report.md", "data/05_final_datasets/reports/research_backed_v3_validation_report.md"),
    CopyRule("data/final_dataset_build/reports/final_dataset_build_report.md", "data/05_final_datasets/reports/final_dataset_build_report.md"),
    CopyRule("data/final_dataset_build/reports/final_combined_dataset_validation_report.md", "data/05_final_datasets/reports/final_combined_dataset_validation_report.md"),
]


EXPERT_REVIEW_RULES = [
    CopyRule("data/expert_review_iaa/expert_spam_review_500_balanced_raw_complete.xlsx", "data/04_expert_review_iaa/active_packet/expert_review_packet_500_balanced_raw_complete.xlsx", "Preferred active expert review packet."),
    CopyRule("data/expert_review_iaa/expert_spam_review_500_balanced_raw_complete.csv", "data/04_expert_review_iaa/active_packet/expert_review_packet_500_balanced_raw_complete.csv", "CSV copy of preferred active expert review packet."),
    CopyRule("data/expert_review_iaa/expert_spam_review_codebook.md", "data/04_expert_review_iaa/active_packet/expert_review_codebook.md"),
    CopyRule("data/expert_review_iaa/expert_spam_review_balanced_report.md", "data/04_expert_review_iaa/active_packet/expert_review_packet_report.md"),
    CopyRule("data/expert_review_iaa/expert_spam_review_500.csv", "data/04_expert_review_iaa/drafts/expert_spam_review_500.csv"),
    CopyRule("data/expert_review_iaa/expert_spam_review_500.xlsx", "data/04_expert_review_iaa/drafts/expert_spam_review_500.xlsx"),
    CopyRule("data/expert_review_iaa/expert_spam_review_500_raw_complete.csv", "data/04_expert_review_iaa/drafts/expert_spam_review_500_raw_complete.csv"),
    CopyRule("data/expert_review_iaa/expert_spam_review_500_raw_complete.xlsx", "data/04_expert_review_iaa/drafts/expert_spam_review_500_raw_complete.xlsx"),
    CopyRule("data/expert_review_iaa/conversational_spam_candidate_pool.csv", "data/04_expert_review_iaa/pools/conversational_spam_candidate_pool.csv"),
    CopyRule("data/expert_review_iaa/raw_complete_expert_replacement_pool.csv", "data/04_expert_review_iaa/pools/raw_complete_expert_replacement_pool.csv"),
    CopyRule("data/expert_review_iaa/expert_spam_review_source_pool.csv", "data/04_expert_review_iaa/pools/expert_spam_review_source_pool.csv"),
    CopyRule("data/expert_review_iaa/expert_spam_review_sampling_log.csv", "data/04_expert_review_iaa/reports/expert_spam_review_sampling_log.csv"),
    CopyRule("data/expert_review_iaa/expert_spam_review_raw_quality_report.md", "data/04_expert_review_iaa/reports/expert_spam_review_raw_quality_report.md"),
    CopyRule("data/expert_review_iaa/expert_spam_review_raw_complete_report.md", "data/04_expert_review_iaa/reports/expert_spam_review_raw_complete_report.md"),
    CopyRule("data/expert_review_iaa/expert_spam_review_replaced_archive.csv", "data/04_expert_review_iaa/archives/expert_spam_review_replaced_archive.csv"),
    CopyRule("data/expert_review_iaa/expert_spam_review_excluded_archive.csv", "data/04_expert_review_iaa/archives/expert_spam_review_excluded_archive.csv"),
    CopyRule("data/expert_review_iaa/expert_spam_review_balanced_removed_archive.csv", "data/04_expert_review_iaa/archives/expert_spam_review_balanced_removed_archive.csv"),
]


MANUAL_HAM_RULES = [
    CopyRule("data/manual_ham_drive/extracted", "data/02_manual_ham/extracted", "Manual ham extracted and review files."),
    CopyRule("data/manual_ham_drive/templates", "data/02_manual_ham/templates", "Manual ham template files."),
    CopyRule("data/manual_ham_drive/final/approved_manual_ham_merged.csv", "data/02_manual_ham/reviewed/approved_manual_ham_merged.csv"),
    CopyRule("data/manual_ham_drive/final/manual_ham_merge_log.csv", "data/02_manual_ham/reviewed/manual_ham_merge_log.csv"),
    CopyRule("data/manual_ham_drive/final/manual_ham_artifact_manual_review.csv", "data/02_manual_ham/reviewed/manual_ham_artifact_manual_review.csv"),
    CopyRule("data/manual_ham_drive/final/manual_ham_artifact_removed_archive.csv", "data/02_manual_ham/archives/manual_ham_artifact_removed_archive.csv"),
    CopyRule("data/manual_ham_drive/rejected", "data/02_manual_ham/archives/rejected"),
]


SYNTHETIC_HAM_RULES = [
    CopyRule("data/final_dataset_build/interim/synthetic_service_ham_research_backed_generated.csv", "data/03_synthetic_ham/research_backed/synthetic_service_ham_research_backed_generated.csv"),
    CopyRule("data/final_dataset_build/interim/synthetic_service_ham_research_backed_approved.csv", "data/03_synthetic_ham/research_backed/synthetic_service_ham_research_backed_approved.csv"),
    CopyRule("data/final_dataset_build/reports/synthetic_ham_family_cap_report.md", "data/03_synthetic_ham/research_backed/synthetic_ham_family_cap_report.md"),
    CopyRule("data/final_dataset_build/reports/research_backed_synthetic_ham_quality_report.md", "data/03_synthetic_ham/research_backed/research_backed_synthetic_ham_quality_report.md"),
    CopyRule("data/final_dataset_build/template_research/research_backed_ham_template_sources.csv", "data/03_synthetic_ham/template_research/research_backed_ham_template_sources.csv"),
    CopyRule("data/final_dataset_build/template_research/research_backed_ham_template_families.csv", "data/03_synthetic_ham/template_research/research_backed_ham_template_families.csv"),
    CopyRule("data/final_dataset_build/template_research/research_template_generation_rules.md", "data/03_synthetic_ham/template_research/research_template_generation_rules.md"),
    CopyRule("data/final_dataset_build/reports/research_template_library_report.md", "data/03_synthetic_ham/template_research/research_template_library_report.md"),
    CopyRule("data/final_dataset_build/interim/synthetic_service_ham_generated.csv", "data/03_synthetic_ham/manual_template_based/synthetic_service_ham_generated.csv"),
    CopyRule("data/final_dataset_build/interim/synthetic_service_ham_approved.csv", "data/03_synthetic_ham/manual_template_based/synthetic_service_ham_approved.csv"),
    CopyRule("data/final_dataset_build/interim/synthetic_service_ham_family_capped.csv", "data/03_synthetic_ham/manual_template_based/synthetic_service_ham_family_capped.csv"),
    CopyRule("data/final_dataset_build/archives", "data/03_synthetic_ham/archives", "Synthetic and final-build archives."),
]


WORKING_DATA_RULES = [
    CopyRule("data/organized/text_verified", "data/01_working/raw_text_verification"),
    CopyRule("data/organized/raw_recovery", "data/01_working/raw_recovery"),
    CopyRule("data/organized/raw_quality", "data/01_working/raw_quality"),
    CopyRule("data/organized/content_quality", "data/01_working/content_quality"),
    CopyRule("data/organized/campaign_family_quality", "data/01_working/campaign_family_quality"),
    CopyRule("data/organized/uci_sms_spam_collection_uniform.csv", "data/01_working/public_source_organization/uci_sms_spam_collection_uniform.csv"),
    CopyRule("data/organized/smishtank_uniform.csv", "data/01_working/public_source_organization/smishtank_uniform.csv"),
    CopyRule("data/organized/gathered_approved_smishing_7k_uniform.csv", "data/01_working/public_source_organization/gathered_approved_smishing_7k_uniform.csv"),
    CopyRule("data/organized/mishra_soni_sms_dataset_uniform.csv", "data/01_working/public_source_organization/mishra_soni_sms_dataset_uniform.csv"),
    CopyRule("data/organized/combined_public_thesis_sources_uniform.csv", "data/01_working/public_source_organization/combined_public_thesis_sources_uniform.csv"),
    CopyRule("data/organized/combined_public_thesis_sources_deduped_representatives.csv", "data/01_working/public_source_organization/combined_public_thesis_sources_deduped_representatives.csv"),
    CopyRule("data/organized/duplicate_overlap_clusters.csv", "data/01_working/public_source_organization/duplicate_overlap_clusters.csv"),
    CopyRule("data/organized/source_manifest.csv", "data/01_working/public_source_organization/source_manifest.csv"),
]


RAW_SOURCE_RULES = [
    CopyRule("data/source_archives/public_baseline", "data/00_raw_sources/public_baseline"),
    CopyRule("data/raw/collected_smishing_candidates.csv", "data/00_raw_sources/gathered_candidates/collected_smishing_candidates.csv"),
    CopyRule("data/external_datasets", "data/00_raw_sources/public_baseline/external_datasets"),
    CopyRule("data/manual_ham_drive/raw", "data/00_raw_sources/manual_ham_drive/raw"),
    CopyRule("data/manual_ham_drive/THESIS-20260510T114611Z-3-001.zip", "data/00_raw_sources/manual_ham_drive/THESIS-20260510T114611Z-3-001.zip"),
]


ARCHIVE_RULES = [
    CopyRule("data/exports/archive", "data/99_archive/old_exports"),
    CopyRule("data/interim", "data/99_archive/old_interim"),
    CopyRule("reports", "reports/archive", "Report compatibility copy; excludes reports/archive recursion at runtime."),
    CopyRule("prompts", "prompts/archive", "Prompt compatibility copy; excludes prompts/archive recursion at runtime."),
]


SCRIPT_STAGE_MAP = {
    "public_sources": [
        "organize_public_sources.py",
        "validate_uniform_sources.py",
        "analyze_uniform_duplicates.py",
    ],
    "raw_text": [
        "verify_and_add_raw_clean_text_columns.py",
        "classify_raw_text_availability.py",
        "recover_gathered_7k_raw_text.py",
        "recover_or_replace_redacted_gathered_smishing.py",
        "audit_strict_raw_text_quality.py",
        "repair_strict_raw_text_dataset.py",
    ],
    "content_quality": [
        "audit_smishing_content_quality.py",
        "detect_smishing_campaign_templates.py",
        "build_content_quality_filtered_dataset.py",
        "audit_strong_campaign_families.py",
        "build_campaign_family_filtered_dataset.py",
    ],
    "manual_ham": [
        "import_manual_ham_drive.py",
        "create_manual_ham_review_excel.py",
        "validate_manual_ham_review.py",
        "detect_manual_ham_split_messages.py",
        "fix_manual_ham_split_messages.py",
        "detect_manual_ham_artifacts.py",
        "remove_manual_ham_artifacts.py",
        "standardize_manual_ham_for_final_dataset.py",
        "check_manual_ham_final_overlap.py",
        "check_manual_ham_overlap.py",
        "check_manual_ham_public_duplicates.py",
    ],
    "synthetic_ham": [
        "extract_service_ham_templates.py",
        "extract_ham_templates.py",
        "generate_service_ham_from_templates.py",
        "generate_synthetic_ham.py",
        "approve_synthetic_ham_candidates.py",
        "create_research_backed_ham_template_library.py",
        "generate_research_backed_synthetic_ham.py",
        "audit_and_cap_synthetic_ham_families.py",
        "approve_research_backed_synthetic_ham.py",
        "research_synthetic_ham_common.py",
    ],
    "final_dataset_build": [
        "final_dataset_build_utils.py",
        "build_final_combined_dataset_with_manual_and_synthetic_ham.py",
        "rebuild_v3_with_research_backed_synthetic_ham.py",
        "validate_final_combined_datasets.py",
        "validate_research_backed_v3_dataset.py",
    ],
    "expert_review_iaa": [
        "build_expert_spam_review_pool.py",
        "create_expert_spam_review_packet.py",
        "validate_expert_spam_review_packet.py",
        "audit_expert_spam_review_raw_quality.py",
        "build_raw_complete_expert_replacement_pool.py",
        "repair_expert_spam_review_packet_raw_complete.py",
        "validate_expert_spam_review_raw_complete_packet.py",
        "build_conversational_spam_candidate_pool.py",
        "create_balanced_expert_spam_review_packet.py",
        "validate_balanced_expert_spam_review_packet.py",
    ],
    "maintenance": [
        "organize_project_structure.py",
        "generate_project_manifests.py",
        "validate_active_outputs.py",
        "project_organization_config.py",
    ],
}


SCRIPT_PURPOSE = {
    "organize_public_sources.py": "Standardize public source files into uniform schema.",
    "validate_uniform_sources.py": "Validate uniform public source outputs.",
    "analyze_uniform_duplicates.py": "Audit duplicate overlap across public sources.",
    "verify_and_add_raw_clean_text_columns.py": "Verify raw and clean text fields.",
    "classify_raw_text_availability.py": "Classify raw text availability.",
    "recover_gathered_7k_raw_text.py": "Recover raw text for gathered 7k candidates when available.",
    "recover_or_replace_redacted_gathered_smishing.py": "Recover or replace redacted gathered smishing rows.",
    "audit_strict_raw_text_quality.py": "Audit strict raw text quality.",
    "repair_strict_raw_text_dataset.py": "Repair strict raw text dataset.",
    "audit_smishing_content_quality.py": "Audit smishing content quality.",
    "detect_smishing_campaign_templates.py": "Detect campaign-template repeats.",
    "build_content_quality_filtered_dataset.py": "Build content-quality-filtered dataset.",
    "audit_strong_campaign_families.py": "Audit strong campaign families.",
    "build_campaign_family_filtered_dataset.py": "Build campaign-family-filtered public master.",
    "import_manual_ham_drive.py": "Import manual ham Drive exports.",
    "create_manual_ham_review_excel.py": "Create manual ham review workbook.",
    "validate_manual_ham_review.py": "Validate reviewed manual ham.",
    "detect_manual_ham_split_messages.py": "Detect split manual ham messages.",
    "fix_manual_ham_split_messages.py": "Merge high-confidence split manual ham messages.",
    "detect_manual_ham_artifacts.py": "Detect UI/OCR artifacts in manual ham.",
    "remove_manual_ham_artifacts.py": "Remove and archive manual ham artifacts.",
    "standardize_manual_ham_for_final_dataset.py": "Standardize manual ham for final builds.",
    "check_manual_ham_final_overlap.py": "Check manual ham overlap against final data.",
    "extract_service_ham_templates.py": "Extract service ham templates.",
    "generate_service_ham_from_templates.py": "Generate service ham from templates.",
    "approve_synthetic_ham_candidates.py": "Approve synthetic ham candidates.",
    "create_research_backed_ham_template_library.py": "Create research-backed template library.",
    "generate_research_backed_synthetic_ham.py": "Generate research-backed synthetic ham.",
    "audit_and_cap_synthetic_ham_families.py": "Audit and cap synthetic ham families.",
    "approve_research_backed_synthetic_ham.py": "Approve research-backed synthetic ham.",
    "research_synthetic_ham_common.py": "Shared helpers for research-backed synthetic ham.",
    "final_dataset_build_utils.py": "Shared final dataset build utilities.",
    "build_final_combined_dataset_with_manual_and_synthetic_ham.py": "Build combined final datasets.",
    "rebuild_v3_with_research_backed_synthetic_ham.py": "Rebuild V3 with research-backed synthetic ham.",
    "validate_final_combined_datasets.py": "Validate final combined datasets.",
    "validate_research_backed_v3_dataset.py": "Validate V3 research-backed dataset.",
    "build_expert_spam_review_pool.py": "Build expert review source pool.",
    "create_expert_spam_review_packet.py": "Create expert review packet.",
    "validate_expert_spam_review_packet.py": "Validate expert review packet.",
    "audit_expert_spam_review_raw_quality.py": "Audit expert packet raw quality.",
    "build_raw_complete_expert_replacement_pool.py": "Build replacement pool for raw-complete expert packet.",
    "repair_expert_spam_review_packet_raw_complete.py": "Repair expert packet raw completeness.",
    "validate_expert_spam_review_raw_complete_packet.py": "Validate raw-complete expert packet.",
    "build_conversational_spam_candidate_pool.py": "Build conversational spam candidate pool.",
    "create_balanced_expert_spam_review_packet.py": "Create balanced expert review packet.",
    "validate_balanced_expert_spam_review_packet.py": "Validate balanced expert review packet.",
    "organize_project_structure.py": "Create thesis-friendly folder structure and copy files safely.",
    "generate_project_manifests.py": "Generate active dataset, script, and pipeline manifests.",
    "validate_active_outputs.py": "Validate active output files and copied checksums.",
}


ALL_COPY_RULES = (
    ACTIVE_OUTPUT_RULES
    + FINAL_REPORT_RULES
    + EXPERT_REVIEW_RULES
    + MANUAL_HAM_RULES
    + SYNTHETIC_HAM_RULES
    + WORKING_DATA_RULES
    + RAW_SOURCE_RULES
    + ARCHIVE_RULES
)
