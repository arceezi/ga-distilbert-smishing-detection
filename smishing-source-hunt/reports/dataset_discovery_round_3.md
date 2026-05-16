# Dataset Discovery Round 3

Date: 2026-05-07

## Goal

Close the remaining high-value source decisions from Round 2 and import only rows that satisfy the dataset-first acquisition rules.

## Source Closure Decisions

### Sting9 Phishing and Scam Message Dataset

Status: `needs_review`

Round 3 findings:

- Dataset page still advertises a GitHub dump and REST API.
- The GitHub dump link routes to the research hub rather than a downloadable dump.
- Research hub says dataset access requires authentication and is "Coming Soon".
- The license page says ODC-BY-NC with clarifications, while the dataset page still says CC0/Public Domain.

Decision:

- No import.
- Keep blocked pending maintainer clarification on public access and license.

### MIMICS-3500

Status: `needs_review`

Round 3 findings:

- ScienceDirect page describes 3,500 English smishing samples.
- Source data is said to come from Kaggle, Mendeley, SmishTank, SpamHunter, and INCIBE.
- No official public dataset artifact or license was found during this pass.

Decision:

- No import.
- Keep as author-contact / artifact-locator target.
- Treat as likely overlap-heavy until row-level source provenance is available.

### Smishing-4C

Status: `needs_review`

Round 3 findings:

- CEUR paper describes 120 English smishing samples in four categories.
- Dataset is created from Kaggle Smishing and Mendeley Smishing.
- Official dataset URL returned a bot-check page; restrictions were not bypassed.

Decision:

- No import.
- Keep as contact/manual-access target.
- Treat as likely overlap-heavy because it derives from already-used Mendeley/Mishra-related samples.

## Conditional Dataset Resolution

### Bengali SMS Smishing Dataset

Status: `approved` for English smish candidate import only

Evidence:

- Hugging Face dataset card identifies it as SMS phishing/smishing data with `label`, `text`, and `source` fields.
- License is MIT.
- Dataset includes Bengali, English, Banglish, and Code-Mixed varieties.
- Slow, rate-safe enumeration found:
  - English `smish`: 776
  - English `promo`: 471
  - English `normal`: 661
  - English total: 1,908

Import decision:

- Imported only `source == English` and `label == smish`.
- Imported rows are candidates, not final-approved thesis rows.
- Non-English, Banglish, and Code-Mixed rows remain excluded.

Pipeline result:

- Raw imported candidates: 776
- Cleaned candidates: 776
- Exact duplicates removed: 113
- Deduplicated candidates remaining: 663
- Final approved export: 0, because imported rows still have `review_status = candidate`

### Zenodo Multiclass NLP Dataset

Status: `needs_review`

Decision:

- No import in Round 3.
- Keep as optional small manual-review pool only.
- It is English and CC BY 4.0, but source scope is email or SMS-like rather than SMS-only.

### DIFrauD SMS Domain

Status: `needs_review`, overlap reference only

Decision:

- No import.
- Use only for duplicate/overlap checking because the SMS domain is built from UCI and Mishra & Soni.

## Round 3 Result

Round 3 produced the first candidate import:

- 776 raw English smishing candidates from the Bengali SMS Smishing Dataset.
- 663 exact-unique cleaned candidates after deduplication.
- 0 final approved rows until manual/spot review changes `review_status` to `approved`.

This does not close the full smishing gap, but it gives the thesis a defensible candidate pool while preserving the approval gate.

