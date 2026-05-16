# Dataset Balance Tracker

## Current Revised Thesis Direction

- Target ham: ~5,000
- Target smishing: ~5,000
- Target total: ~10,000
- Current known smishing from thesis sources: around 1,700 verified smishing before additional dataset searching
- Additional smishing needed: around 3,000+

## Goal of This Folder

This folder helps close the smishing gap by prioritizing labeled public datasets first, then using public example sources only when dataset sources are not enough.

## Balance Tracker

| Category | Target | Current Known | Additional Needed | Notes |
|---|---:|---:|---:|---|
| Ham / legitimate | 5,000 | 9,671 public-source ham + 550 curated service messages before cleaning/deduplication | 0; likely oversupplied | Revised strategy may downsample or rebalance ham later. |
| Smishing | 5,000 | 1,700 verified smishing from Mishra & Soni + SmishTank before additional searching | ~3,300 before relabeling/rejection effects | Primary focus of this workspace. |

## Baseline Source Counts Confirmed

| Source | Total | Ham | Verified Smishing | Spam / Review |
|---|---:|---:|---:|---:|
| UCI SMS Spam Collection | 5,574 | 4,827 | 0 | 747 |
| Mishra & Soni SMS dataset | 5,971 | 4,844 | 638 | 489 |
| SmishTank | 1,062 | 0 | 1,062 | 0 |
| Public-source subtotal | 12,607 | 9,671 | 1,700 | 1,236 |
| Curated service messages | 550 | 550 | 0 | 0 |
| Pre-cleaning thesis total | 13,157 | 10,221 before relabeling/deduplication | 1,700 before added sources | 1,236 |

## Discovery Round 1 Status

- New approved smishing rows imported: 0
- Dataset candidates logged: 10
- Highest-priority unresolved source: Sting9 Phishing and Scam Message Dataset
- Main risk found: many public SMS datasets are repackaged UCI/Mishra sources and do not add genuinely new smishing rows.

## Discovery Round 2 Status

- New approved smishing rows imported: 0
- Dataset candidates logged after Round 2: 16
- Still approved for import: 0 new datasets
- Highest-priority unresolved sources: Sting9, MIMICS-3500, Smishing-4C
- Conditional small-source option: Zenodo multiclass NLP dataset, only after manual SMS-like row review
- Current estimated additional approved smishing found: 0
- Remaining smishing gap: ~3,300 before relabeling/rejection effects

## Discovery Round 3 Status

- New raw smishing candidates imported: 776
- Exact-unique cleaned candidates after deduplication: 663
- New final approved smishing rows exported: 0
- Current additional candidate pool toward smishing gap: 663
- Remaining smishing gap if all 663 candidates are later approved: ~2,637
- Remaining smishing gap currently approved: ~3,300

## Discovery Round 4 Status

- New raw candidates imported this round: 90,366
- Total raw candidate smishing pool: 91,142
- Total exact-unique candidate pool after deduplication: 43,881
- New final approved smishing rows exported: 0
- Remaining smishing gap if all 43,881 candidates were later approved: effectively closed
- Remaining smishing gap currently approved: ~3,300

## Review Round 1 Status

- Rows reviewed by source-aware helper: 5,651
- New final approved smishing rows exported: 3,300
- Approved SmishX rows: 182
- Approved IMC25 rows: 3,118
- Rows held as `needs_review`: 2,351
- Bengali English subset approvals: 0
- NCSU approvals: 0
- Remaining additional-source smishing gap after this export: approximately 0 for the current ~3,300 target, pending QA and final thesis balancing.

## Review Round 2 Status

- Previously approved rows audited under strict English/readability rules: 3,300
- Rows downgraded from `approved` to `needs_review`: 195
- Replacement approvals added from IMC25: 195
- Strict-clean approved rows in `deduplicated_candidates.csv`: 3,300
- Strict-clean export written to `data/final/approved_smishing_messages_round2_clean.csv`
- Canonical `approved_smishing_messages.csv` still needs refresh after closing the file in Excel.

## Review Round 3 Status

- Target approved smishing rows increased to: 7,000
- New strict-clean IMC25 approvals added: 3,700
- Final strict-clean approved rows in `deduplicated_candidates.csv`: 7,000
- Canonical redacted export refreshed at `data/final/approved_smishing_messages.csv`
- Round-specific redacted export written to `data/final/approved_smishing_messages_round3_7k_clean.csv`
- Unredacted raw export written to `data/final/approved_smishing_messages_unredacted_raw.csv`
- Raw export uses locally stored `message_raw`; source-level placeholders remain where present.

## Current Candidate Pool By Source

| Source | Raw Candidates Imported | Exact-Unique Candidates |
|---|---:|---:|
| SMS Phishing Dataset (`wspr-ncsu/sms-phishing`) | 68,029 | 27,571 |
| Smishing-Dataset-IMC25 | 22,078 | 15,433 |
| Bengali SMS Smishing Dataset, English subset | 776 | 663 |
| SmishX | 259 | 214 |

## Current Review Status By Source

| Source | Candidate | Approved | Needs Review | Rejected |
|---|---:|---:|---:|---:|
| SMS Phishing Dataset (`wspr-ncsu/sms-phishing`) | 27,571 | 0 | 0 | 0 |
| Smishing-Dataset-IMC25 | 3,625 | 6,869 | 4,939 | 0 |
| Bengali SMS Smishing Dataset, English subset | 663 | 0 | 0 | 0 |
| SmishX | 0 | 131 | 83 | 0 |

## Update Rules

- Update counts only after cleaning, deduplication, and approval.
- Keep imported candidate counts separate from approved final counts.
- Do not count `unsure`, `reject`, or duplicate rows toward the final smishing target.
