# Data Collection Plan

The purpose of this plan is to minimize manual labeling while keeping the acquisition process reproducible, auditable, and privacy-conscious.

## Phase 1: Search for Already-Labeled Datasets

Prioritize sources that already include SMS text and labels:

- public smishing datasets
- public phishing SMS datasets
- academic SMS phishing datasets
- GitHub datasets
- Kaggle datasets
- Hugging Face datasets
- Zenodo datasets
- Mendeley Data datasets
- IEEE DataPort datasets
- university repositories
- SmishTank-style datasets

Record every promising source in `DATASET_SEARCH_LOG.md` and `data/external_datasets/dataset_inventory.csv`.

## Phase 2: Evaluate Dataset Usability

For each candidate dataset, check:

- Is SMS text included?
- Are labels included?
- Are labels clear enough to map to thesis labels?
- Is the dataset English or mostly English?
- Is the file format easy to convert?
- Is license or usage guidance available?
- Is the source public and stable?
- Does it contain unsafe private data?

## Phase 3: Check Label Mapping

Preserve original labels and document mappings:

- smishing / phishing SMS / scam SMS / malicious SMS -> `smishing`
- ham / legitimate / normal SMS -> `ham`
- general spam but not clearly phishing -> `unsure` or `needs_review`
- unclear, non-English, non-SMS, or unsafe/private -> `reject`

## Phase 4: Check Overlap With Existing Thesis Sources

Before approval, check likely overlap with:

- UCI SMS Spam Collection
- Mishra & Soni SMS dataset
- SmishTank Dataset
- other sources already integrated into the thesis dataset

Use exact duplicate checks and later near-duplicate checks. Do not allow duplicate or near-duplicate messages to be split across future train/validation/test partitions.

## Phase 5: Import or Document Suitable Datasets

For approved or promising datasets:

- save source metadata in the inventory
- preserve original label and text columns
- store local filenames when downloaded manually
- document cleaning needs and license notes
- import safe rows into `data/raw/collected_smishing_candidates.csv`

## Phase 6: Clean and Redact Sensitive Values

Use `scripts/clean_candidates.py` to generate `data/interim/cleaned_candidates.csv`.

Redact:

- URLs -> `<URL>`
- phone-like numbers -> `<PHONE>`
- emails -> `<EMAIL>`
- OTP/code-like values -> `<OTP>`
- account-like long numbers -> `<ACCT>`

## Phase 7: Remove Duplicates and Near-Duplicates

Use `scripts/deduplicate_candidates.py` for exact duplicate removal. Add fuzzy or embedding-based near-duplicate checks later if needed.

Suggested near-duplicate similarity threshold: `0.95`.

## Phase 8: Manual Review Only When Needed

Manual review is for:

- unclear label mappings
- general spam that may not be phishing
- messages with suspicious but ambiguous content
- sources with incomplete documentation
- borderline SMS-like examples

## Phase 9: Export Approved Smishing Messages

Use `scripts/export_final.py` to export only rows where:

- `label == "smishing"`
- `review_status == "approved"`

The output is `data/final/approved_smishing_messages.csv`.

## Secondary Sources

Use these only after labeled datasets have been prioritized:

- bank scam-warning pages
- government scam-warning pages
- telecom scam-warning pages
- cybersecurity reports
- consumer protection pages
- public scam-awareness pages that show real smishing examples

