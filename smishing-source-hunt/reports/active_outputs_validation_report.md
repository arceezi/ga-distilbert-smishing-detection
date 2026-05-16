# Active Outputs Validation Report

Validation status: PASS

- [x] active final V3 file exists: data/05_final_datasets/active/final_v3_research_synthetic_balanced_10544.csv
- [x] V3 has ham=5,272 and smishing=5,272: ham=5272, smishing=5272
- [x] V3 has no synthetic smishing: synthetic_smishing=0
- [x] active expert packet exists: data/04_expert_review_iaa/active_packet/expert_review_packet_500_balanced_raw_complete.xlsx
- [x] expert packet has 500 rows if available: rows=500
- [x] manual ham cleaned file exists: data/02_manual_ham/cleaned/approved_manual_ham_cleaned_320.csv
- [x] manual ham cleaned file has 320 rows: rows=320
- [x] public master campaign-family file exists: data/05_final_datasets/active/public_master_campaign_family_filtered_10226.csv
- [x] file_move_manifest.csv exists: manifests/file_move_manifest.csv
- [x] active_dataset_manifest.csv exists: manifests/active_dataset_manifest.csv
- [x] script_inventory.csv exists: manifests/script_inventory.csv
- [x] pipeline_stage_manifest.csv exists: manifests/pipeline_stage_manifest.csv
- [x] final_v3_research_synthetic_balanced_10544.csv is not empty: data/05_final_datasets/active/final_v3_research_synthetic_balanced_10544.csv
- [x] expert_review_packet_500_balanced_raw_complete.xlsx is not empty: data/04_expert_review_iaa/active_packet/expert_review_packet_500_balanced_raw_complete.xlsx
- [x] approved_manual_ham_cleaned_320.csv is not empty: data/02_manual_ham/cleaned/approved_manual_ham_cleaned_320.csv
- [x] public_master_campaign_family_filtered_10226.csv is not empty: data/05_final_datasets/active/public_master_campaign_family_filtered_10226.csv
- [x] checksums match copied files: 379 files checked; mismatches: 0

## Active Output Paths

- Main expanded dataset: data/05_final_datasets/active/final_v3_research_synthetic_balanced_10544.csv
- Real-only baseline: data/05_final_datasets/active/baseline_v1_public_real_only_balanced_9908.csv
- Expert packet: data/04_expert_review_iaa/active_packet/expert_review_packet_500_balanced_raw_complete.xlsx
- Manual ham: data/02_manual_ham/cleaned/approved_manual_ham_cleaned_320.csv
- Manifest: manifests/active_dataset_manifest.csv