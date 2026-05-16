# Expert Review / IAA Guide

## Packet To Send

Send the preferred active packet:

`data/04_expert_review_iaa/active_packet/expert_review_packet_500_balanced_raw_complete.xlsx`

If a CSV version is needed, use:

`data/04_expert_review_iaa/active_packet/expert_review_packet_500_balanced_raw_complete.csv`

The balanced raw-complete packet is preferred because it has complete review text and a balanced sampling design. Older drafts remain in `data/04_expert_review_iaa/drafts/`.

## Allowed Labels

Experts should use the packet columns for:

- `expert_label`
- `expert_confidence`
- `expert_notes`
- `reviewer_name`
- `review_date`

Allowed labels should stay aligned with the thesis labeling guide:

- `ham`
- `smishing`
- `spam`
- `unsure`
- `reject`

## After Expert Review

After review, compare expert labels against the current normalized labels and compute agreement only in a separate analysis workflow. Do not overwrite the active final dataset with expert labels.

Rows in the expert packet are not yet part of the final dataset as expert-labeled rows. They are an evaluation and agreement artifact until a later, intentional adjudication step.

## Supporting Files

- Codebook: `data/04_expert_review_iaa/active_packet/expert_review_codebook.md`
- Packet report: `data/04_expert_review_iaa/active_packet/expert_review_packet_report.md`
- Candidate pools: `data/04_expert_review_iaa/pools/`
- Older drafts: `data/04_expert_review_iaa/drafts/`
- Archives: `data/04_expert_review_iaa/archives/`
