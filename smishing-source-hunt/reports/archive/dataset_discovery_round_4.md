# Dataset Discovery Round 4

Date: 2026-05-07

## Goal

Implement the deep-research acquisition path by importing the strongest new public positive-class sources and measuring how much exact-unique smishing volume they actually add.

## Imported Sources

### Smishing-Dataset-IMC25

Status: `approved`

Why approved:

- Public GitHub repository with a stable CSV artifact.
- Clear CC BY 4.0 license.
- All rows are smishing by dataset construction.
- English rows can be filtered directly using the `language` column.

Import rule used:

- Keep only `language == English`.
- Use `text`; fall back to `translation` only when `text` is empty.
- Preserve `scam_type`, `lure_principles`, and country metadata in side columns or notes.

Pipeline outcome:

- Raw imported candidates: 22,078
- Exact-unique survivors after deduplication: 15,433

### SMS Phishing Dataset (`wspr-ncsu/sms-phishing`)

Status: `approved`

Why approved:

- Public GitHub repository with stable CSV artifacts.
- MIT license.
- `phishing_messages.csv` is an all-positive phishing message file.

Import rule used:

- Import all rows from `phishing_messages.csv` as candidate smishing rows.
- Preserve source message IDs and message metadata in `reviewer_notes`.
- Keep `language = unknown` because the file does not label language per row.

Implementation note:

- The CSV header is malformed by one field. Data rows have 7 fields while the header has 6.
- The importer therefore maps fields positionally:
  - messageID
  - objectID
  - destination number
  - message
  - sender
  - timestamp
  - error in time

Pipeline outcome:

- Raw imported candidates: 68,029
- Exact-unique survivors after deduplication: 27,571

### SmishX

Status: `approved`

Why approved:

- Public GitHub repository with a stable `data/dataset.csv`.
- MIT license.
- Manually relabeled dataset that distinguishes `smishing`, `spam`, and `legitimate`.

Import rule used:

- Import only rows where `label == smishing`.
- Preserve URL/phone/email indicator fields in `reviewer_notes`.

Pipeline outcome:

- Raw imported candidates: 259
- Exact-unique survivors after deduplication: 214

## Combined Round 4 Outcome

Total candidate pool after all imports:

- Raw candidate rows: 91,142
- Cleaned rows: 91,142
- Exact duplicates removed: 47,261
- Deduplicated candidate rows remaining: 43,881
- Final approved rows exported: 0

Deduplicated source breakdown:

- NCSU SMS Phishing Dataset: 27,571
- IMC25 English subset: 15,433
- Bengali SMS Smishing Dataset English subset: 663
- SmishX smishing subset: 214

## Interpretation

The deep-research report was right: the problem is no longer dataset discovery. We now have a very large public candidate pool with enough volume to close the thesis smishing gap multiple times over.

The next bottleneck is quality control:

- English filtering for NCSU
- spot review of IMC25 and SmishX rows
- source-aware near-duplicate collapse
- promotion from `candidate` to `approved`

## Remaining Blockers

- `Sting9` remains blocked by access/license ambiguity.
- `MIMICS-3500` still lacks a clear public artifact and is likely overlap-heavy.
- `Smishing-4C` remains behind a bot-check page and appears derivative of existing public sources.

These are now lower priority than reviewing and approving the rows already imported.

