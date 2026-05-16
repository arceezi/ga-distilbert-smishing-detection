# AGENTS.md

This workspace is for thesis-oriented smishing data source research and acquisition. The main goal is to find around 3,000 additional English, SMS-like smishing messages so the thesis dataset can move toward a roughly balanced 50:50 ham/smishing experimental set.

## Primary Goal

Find, evaluate, document, clean, deduplicate, and prepare additional smishing SMS messages for the thesis:

> Genetic Algorithm-Evolved Feature-Group Importance Weighting Fused with Frozen DistilBERT Embeddings for Adversarially Robust English Smishing Detection

The target final dataset is about 10,000 messages:

- around 5,000 ham / legitimate SMS messages
- around 5,000 smishing SMS messages
- around 3,000+ additional smishing messages still needed

## Source Priority

Always prioritize already-labeled datasets before collecting individual examples manually.

Preferred order:

1. Public datasets already labeled as smishing / phishing SMS.
2. Public academic datasets with SMS text and labels.
3. Public datasets from GitHub, Kaggle, Hugging Face, Zenodo, Mendeley Data, IEEE DataPort, or university repositories.
4. Datasets already in CSV, JSON, TXT, or other easily convertible formats.
5. Public cybersecurity reports or scam-awareness pages that show real smishing examples.
6. Manually collected individual examples only if labeled datasets are not enough.

## Conduct Rules

- Do not scrape aggressively.
- Do not bypass website restrictions, paywalls, CAPTCHAs, login walls, robots restrictions, or rate limits.
- Do not collect private credentials, passwords, recovery phrases, real OTPs, full phone numbers, names, addresses, account numbers, or other personal identifying information.
- Do not invent fake messages unless the file explicitly says the row is synthetic or template-generated.
- Preserve source traceability. Every collected row must have a `source_url` or `source_name`.
- Keep original labels when importing labeled datasets. Document how the original labels map to thesis labels.
- Treat general spam that is not clearly phishing as `unsure` or `needs_review`, not automatically smishing.
- Keep the workflow research-focused, reproducible, and auditable.

## Label Mapping

Use these thesis labels:

- `smishing`: smishing / phishing SMS / scam SMS / malicious SMS.
- `ham`: ham / legitimate / normal SMS.
- `unsure`: general spam, unclear intent, unclear label, or requires manual review.
- `reject`: non-English, non-SMS-like, unsafe/private, duplicate-only, no source, or unusable.

## Data Safety

Cleaned and final versions must redact sensitive values:

- URLs: `<URL>`
- phone numbers: `<PHONE>`
- OTPs or verification codes: `<OTP>`
- emails: `<EMAIL>`
- names: `<NAME>` when identifiable
- account numbers: `<ACCT>`

Raw candidates should only contain safe public examples. If a raw example includes sensitive personal data, reject it or redact before saving.

## Required Documentation

For every dataset or source reviewed, update the relevant logs:

- `DATASET_SEARCH_LOG.md`
- `SOURCE_LOG.md`
- `data/external_datasets/dataset_inventory.csv`
- `reports/acquisition_progress.md`
- `reports/dataset_balance_tracker.md`

Record:

- dataset/source name
- source URL
- original file format
- original labels
- estimated smishing count
- estimated ham count
- language
- license or usage note
- usability status
- cleaning needs
- possible overlap with UCI, Mishra & Soni, SmishTank, or other thesis sources
- status: `candidate`, `approved`, `rejected`, `needs_review`, or `already_used`

