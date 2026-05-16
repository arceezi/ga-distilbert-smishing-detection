# Acquisition Progress

Track progress toward finding additional smishing samples.

## Current Goal

- Additional smishing messages needed: around 3,000+
- Preferred source type: already-labeled public datasets
- Secondary source type: public warning pages and cybersecurity reports with real smishing examples

## Progress Table

| Date | Source/Dataset | Status | Smishing Added | Ham Added | Rejected | Notes |
|---|---|---|---:|---:|---:|---|
| 2026-05-06 | Thesis baseline records | completed | 0 | 0 | 0 | Confirmed existing public-source counts: UCI 5,574; Mishra & Soni 5,971; SmishTank 1,062; total verified smishing from Mishra + SmishTank = 1,700. |
| 2026-05-06 | Dataset discovery batch A-D | completed | 0 | 0 | 3 dataset sources rejected | Logged first shortlist in `DATASET_SEARCH_LOG.md` and `dataset_inventory.csv`; no message rows imported yet. |
| 2026-05-06 | Sting9 Phishing and Scam Message Dataset | needs_review | 0 | 0 | 0 | Promising because it advertises sms/smishing fields, anonymized body text, and bulk/API access; must resolve access and license conflict before import. |
| 2026-05-06 | DIFrauD SMS Domain | needs_review | 0 | 0 | 0 | Public labeled English SMS, but built from UCI + Mishra & Soni, so likely not useful for new samples. Useful for duplicate/label cross-checking. |
| 2026-05-06 | Zenodo Multiclass NLP Phishing/Social Engineering Dataset | needs_review | 0 | 0 | 0 | Labeled English phishing/benign content, but not SMS-only. Review only if SMS-like rows can be isolated. |
| 2026-05-06 | Bengali SMS Smishing Dataset | needs_review | 0 | 0 | 0 | Labeled SMS dataset; English-only subset must be checked because most scope appears multilingual/Bengali/Banglish/Code-Mixed. |
| 2026-05-06 | Kaggle SMS Smishing Collection, BangalaBarta, itsG synthetic | rejected | 0 | 0 | 3 | Rejected for high overlap/modified UCI text, non-English scope, or synthetic prompt-style format. |
| 2026-05-06 | Round 2 Sting9 resolution | blocked | 0 | 0 | 0 | Public dump/API not usable in this pass; API requires auth and license conflicts remain. |
| 2026-05-06 | Round 2 conditional dataset inspection | completed | 0 | 0 | 0 | DIFrauD confirmed overlap-only; Zenodo has possible small SMS-like subset; Bengali dataset needs English-smish cross-count. |
| 2026-05-06 | Round 2 new source search | completed | 0 | 0 | 4 dataset sources rejected | Added MIMICS-3500 and Smishing-4C as `needs_review`; rejected ealvaradob compilation, angelfonsecar compilation, MOZ-Smishing, and ScamNet. |
| 2026-05-07 | Round 3 high-value source closure | completed | 0 | 0 | 0 | Sting9 remains blocked; MIMICS-3500 and Smishing-4C remain access/license/contact targets. |
| 2026-05-07 | Bengali SMS Smishing Dataset English subset | candidate_imported | 776 raw candidates; 663 exact-unique after deduplication | 0 | 113 exact duplicates removed | Imported only `source == English` and `label == smish`; rows remain `candidate`, not final-approved. |
| 2026-05-07 | IMC25 English subset | candidate_imported | 22,078 raw candidates; 15,433 exact-unique after full-pool deduplication | 0 | Exact duplicates collapsed in combined pool | Imported only English rows from `final_dataset_output.csv`; primary new positive-class source. |
| 2026-05-07 | NCSU SMS Phishing Dataset | candidate_imported | 68,029 raw candidates; 27,571 exact-unique after full-pool deduplication | 0 | Exact duplicates collapsed in combined pool | Imported `phishing_messages.csv` as candidate smishing reservoir; language review still pending. |
| 2026-05-07 | SmishX smishing subset | candidate_imported | 259 raw candidates; 214 exact-unique after full-pool deduplication | 0 | Exact duplicates collapsed in combined pool | Imported only `label == smishing`; useful quality supplement. |
| 2026-05-07 | Candidate review round 1: SmishX + IMC25 | reviewed | 3,300 approved after source-aware triage | 0 | 2,351 held as `needs_review` | Approved 182 SmishX and 3,118 IMC25 rows; exported `data/final/approved_smishing_messages.csv`. Bengali and NCSU remain unapproved reserves. |
| 2026-05-07 | Candidate review round 2: strict English/readability cleanup | reviewed | 3,300 strict-clean approved in candidate file | 0 | 195 former-approved rows moved to `needs_review` | Downgraded non-English/noisy rows, approved 195 IMC25 replacements, and wrote `data/final/approved_smishing_messages_round2_clean.csv`; canonical final CSV is open in Excel and needs refresh after closing. |
| 2026-05-07 | Candidate review round 3: 7k surplus + raw export | reviewed | 7,000 strict-clean approved in candidate file | 0 | 2,365 new IMC25 rows held as `needs_review` | Added 3,700 strict-clean IMC25 approvals, refreshed canonical redacted export, and wrote unredacted local-raw export. |

## Running Notes

- Dataset-first strategy is active.
- First candidate review pass is complete from SmishX and IMC25.
- The strict-clean approved pool now contains 7,000 source-traceable smishing rows in `deduplicated_candidates.csv`.
- The canonical redacted export and separate unredacted raw export are both refreshed.
- Treat `data/final/approved_smishing_messages_unredacted_raw.csv` as a research-use artifact because it may contain live scam indicators from local `message_raw`.
