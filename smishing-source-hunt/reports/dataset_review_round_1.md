# Dataset Review Round 1

Date: 2026-05-07

## Goal

Move from acquisition to source-aware curation and produce the first meaningful approved smishing export without adding new sources.

## Review Rules Applied

- SmishX was reviewed first because it is small and manually relabeled.
- IMC25 was reviewed second as the main English, structured approval source.
- Bengali English subset and NCSU were not promoted in this round.
- Exact deduplication remains in place; a rough template-signature pass now exports near-duplicate/campaign clusters for QA.
- NCSU remains reserve-only until English filtering and campaign repetition review are completed.

## Round 1 Results

| Source | Rows Reviewed | Approved | Needs Review | Rejected | Notes |
|---|---:|---:|---:|---:|---|
| SmishX | 214 | 182 | 32 | 0 | Approved rows were SMS-like, English, and had a clear phishing action/contact hook. |
| Smishing-Dataset-IMC25 | 5,437 | 3,118 | 2,319 | 0 | Approved high-confidence English SMS-like rows only; fragments and weaker wrong-number lures were held. |
| Bengali SMS Smishing Dataset | 0 | 0 | 0 | 0 | Exported for spot review only; no bulk promotion. |
| SMS Phishing Dataset | 0 | 0 | 0 | 0 | Exported for English/campaign triage only; no approval in this round. |

## Approved Export

- Approved smishing rows exported: 3,300
- Final export path: `data/final/approved_smishing_messages.csv`
- Export condition: `label == smishing` and `review_status == approved`
- Remaining immediate smishing gap from the additional-source target: effectively closed for this phase, subject to manual QA and thesis balancing.

## Approved Rows By Source And Category

| Source | Category | Approved Rows |
|---|---|---:|
| Smishing-Dataset-IMC25 | banking | 1,590 |
| Smishing-Dataset-IMC25 | others | 557 |
| Smishing-Dataset-IMC25 | spam | 369 |
| Smishing-Dataset-IMC25 | delivery | 273 |
| SmishX | other | 182 |
| Smishing-Dataset-IMC25 | government | 161 |
| Smishing-Dataset-IMC25 | telecom | 97 |
| Smishing-Dataset-IMC25 | wrong number | 49 |
| Smishing-Dataset-IMC25 | hey mum/dad | 22 |

## Current Review Status

| Source | Candidate | Approved | Needs Review | Rejected |
|---|---:|---:|---:|---:|
| SMS Phishing Dataset | 27,571 | 0 | 0 | 0 |
| Smishing-Dataset-IMC25 | 9,996 | 3,118 | 2,319 | 0 |
| Bengali SMS Smishing Dataset | 663 | 0 | 0 | 0 |
| SmishX | 0 | 182 | 32 | 0 |

## QA Artifacts Created

| File | Purpose |
|---|---|
| `data/review_batches/smishx_approved_spot_round1.csv` | 100 approved SmishX rows for spot QA. |
| `data/review_batches/smishx_needs_review_round1.csv` | All 32 SmishX rows held from approval. |
| `data/review_batches/imc25_approved_spot_round1.csv` | 100 approved IMC25 rows for spot QA. |
| `data/review_batches/imc25_needs_review_spot_round1.csv` | 100 IMC25 rows held from approval. |
| `data/review_batches/imc25_near_duplicate_clusters_round1.csv` | IMC25 rough template/campaign clusters. |
| `data/review_batches/bengali_candidate_spot_round1.csv` | Bengali English subset spot-review sample. |
| `data/review_batches/ncsu_candidate_english_triage_spot_round1.csv` | NCSU spot-review sample before English triage. |
| `data/review_batches/ncsu_near_duplicate_clusters_round1.csv` | NCSU rough template/campaign clusters. |

## Validation

- `scripts/validate_schema.py data/interim/deduplicated_candidates.csv`: passed.
- `scripts/export_final.py`: exported 3,300 approved smishing rows.
- `scripts/validate_schema.py data/final/approved_smishing_messages.csv`: passed.

## Next Actions

1. Manually spot-check the approved SmishX and IMC25 batches before thesis freeze.
2. Review the 32 SmishX `needs_review` rows and either approve or reject with short notes.
3. Use IMC25 near-duplicate clusters to decide whether some approved categories need downsampling for diversity.
4. Review Bengali naturalness only if more diversity is needed.
5. Keep NCSU as reserve and run English/campaign triage before any approval.
