# Deduplication Rules

Deduplication is required before approval or thesis integration.

## Exact Duplicates

Remove exact duplicates using normalized message text.

Recommended normalization:

- lowercase
- strip leading and trailing spaces
- collapse repeated whitespace
- normalize redaction placeholders
- remove harmless punctuation spacing differences where appropriate

## Near-Duplicates

Use fuzzy similarity or another documented method for near-duplicates.

Suggested threshold:

- `0.95` similarity or higher

Near-duplicates may include:

- same message with a different URL
- same message with a different phone number
- same template with small spelling differences
- same scam script from multiple pages

## Which Duplicate to Keep

Keep the clearest and most source-traceable version:

- public and stable source URL
- clear original label
- English and SMS-like
- least sensitive raw text
- best dataset documentation

## Train/Validation/Test Warning

Do not split duplicates or near-duplicates across future train, validation, and test sets. This can inflate evaluation performance and weaken claims about adversarial robustness.

## Existing Thesis Source Overlap

Check whether newly found datasets overlap with:

- UCI SMS Spam Collection
- Mishra & Soni SMS dataset
- SmishTank Dataset
- any manually curated thesis messages
- any manually relabelled thesis samples

If overlap is found, mark the duplicate rows in `duplicate_status` and document the likely source.

