# Dataset Discovery Round 1

Date: 2026-05-06

## Baseline Confirmed From Thesis Records

The local thesis text confirms the current public-source composition:

| Source | Total | Ham | Verified Smishing | Spam / Review |
|---|---:|---:|---:|---:|
| UCI SMS Spam Collection | 5,574 | 4,827 | 0 | 747 |
| Mishra & Soni SMS dataset | 5,971 | 4,844 | 638 | 489 |
| SmishTank | 1,062 | 0 | 1,062 | 0 |
| Total public sources | 12,607 | 9,671 | 1,700 | 1,236 |

The revised dataset strategy still needs around 3,000+ additional verified smishing rows.

## Most Promising Candidate

### Sting9 Phishing and Scam Message Dataset

- URL: https://sting9.org/dataset
- Why promising: advertises anonymized phishing, smishing, and scam messages with `message_type`, `attack_type`, `body_text`, language, and verification fields.
- Main blockers: dataset page and research hub appear inconsistent about access; license text conflicts between CC0/Public Domain and ODC-BY-NC.
- Status: `needs_review`
- Next action: verify whether a no-auth GitHub dump or API export is actually available, then filter to `message_type = sms`, `attack_type = smishing`, `detected_language = en`, and preferably `verified = true`.

## Useful But Probably Not New

### DIFrauD SMS Domain

- URL: https://huggingface.co/datasets/difraud/difraud
- Why useful: English SMS domain, JSONL format, MIT license, 1,274 deceptive and 5,300 non-deceptive SMS after deduplication.
- Main blocker: source documentation says the SMS domain is built from UCI SMS Spam Collection and Mishra & Soni, both already used in the thesis.
- Status: `needs_review`
- Next action: use for overlap and duplicate cross-checking, not as a primary source of new smishing rows.

## Conditional Review Sources

### Zenodo Multiclass NLP Dataset for Phishing and Social Engineering Threat Detection

- URL: https://zenodo.org/records/15235123
- Why useful: 624 anonymized English messages with phishing and benign labels.
- Main blocker: described as email or SMS-like, not SMS-only.
- Status: `needs_review`
- Next action: inspect rows only if source license is acceptable and SMS-like rows can be reliably isolated.

### Bengali SMS Smishing Dataset

- URL: https://huggingface.co/datasets/shariul-islam/bengali-sms-smishing-dataset
- Why useful: SMS-specific labels `smish`, `promo`, and `normal`, with an English linguistic-variety field.
- Main blocker: multilingual dataset; thesis scope is English-only.
- Status: `needs_review`
- Next action: inspect English-only subset counts. Reject Bengali, Banglish, and Code-Mixed rows.

## Rejected Sources

| Source | Reason |
|---|---|
| Kaggle SMS Smishing Collection Data Set | Modified UCI-like 5,574-message collection; text altered to increase URL count; high overlap risk. |
| BangalaBarta / Bangla smishing dataset | Directly smishing-labeled but not English. |
| itsG/smishing-synthetic | Synthetic/prompt-style scam analysis, not real labeled SMS rows. |

## Round 1 Decision

No rows should be imported yet. The next acquisition step should focus on verifying Sting9 and searching for more English SMS-specific labeled datasets that do not merely repackage UCI, Mishra & Soni, or SmishTank.
