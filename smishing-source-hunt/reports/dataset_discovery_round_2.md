# Dataset Discovery Round 2

Date: 2026-05-06

## Goal

Resolve Round 1 `needs_review` sources and search for more already-labeled English smishing/SMS-phishing datasets that are not just mirrors of UCI, Mishra & Soni, or SmishTank.

## Sting9 Resolution

Status: `needs_review`

Findings:

- Dataset page advertises a GitHub dump, REST API, SMS schema fields, privacy redaction, and CC0/Public Domain release.
- Research hub says dataset access is authentication-required and "Coming Soon".
- The advertised API path in the dataset example returned `404`.
- The `/api/v1/submissions` API path returned `401` without an authorization header.
- License remains conflicting: dataset page says CC0, but license page/footer say ODC-BY-NC with clarifications.

Decision:

- Do not import Sting9 rows.
- Keep as `needs_review`.
- Next action is manual contact or later re-check for a public dump/API and final license terms.

## Conditional Dataset Inspection

### DIFrauD SMS Domain

Status: `needs_review`, overlap reference only

- Public Hugging Face dataset under MIT.
- SMS domain has 6,574 samples: 1,274 deceptive and 5,300 non-deceptive.
- Documentation says SMS was created from UCI SMS Spam Collection plus Mishra & Soni SMS Phishing Dataset.

Decision:

- Do not import as new data.
- Use only as an overlap/deduplication reference if needed.

### Zenodo Multiclass NLP Dataset

Status: `needs_review`

- Public Zenodo dataset under CC BY 4.0.
- 624 English-language anonymized messages.
- File has two columns: `Corpus` and `Labels`.
- Label counts after local temporary inspection: Phishing 114, Scareware 100, Malware 78, Baiting 80, Pretexting 78, NOT-Malicious General Class 171, plus 3 malformed/long phishing-like rows.
- 84 phishing rows are short enough to plausibly be SMS-like using a rough `<= 240` character heuristic.

Decision:

- Do not bulk import.
- Candidate for manual row-level review only, because source says "email or SMS-like" rather than SMS-only.

### Bengali SMS Smishing Dataset

Status: `needs_review`

- Public Hugging Face dataset under MIT.
- Dataset statistics show 7,705 rows total.
- Total labels across splits: 3,088 `smish`, 1,880 `promo`, 2,737 `normal`.
- Source/language-variety counts across splits: English 1,908, Bengali 1,968, Banglish 1,981, CodeMix 1,848.
- English-only `smish` cross-count was not completed because the Hugging Face rows API returned rate limiting during row enumeration.

Decision:

- Do not import yet.
- Re-check later with a slower batched script or downloaded parquet support.
- Only English-source `smish` rows could be considered; Bengali, Banglish, and CodeMix rows must be rejected for this thesis.

## New Round 2 Sources

| Source | Status | Decision Reason |
|---|---|---|
| MIMICS-3500 | needs_review | Highly relevant 3,500 English smishing sample dataset described in ScienceDirect article, but public download/license not found. Likely overlaps with Kaggle, Mendeley, SmishTank, SpamHunter, and INCIBE. |
| Smishing-4C | needs_review | Relevant 120-sample English multi-class smishing dataset. Dataset URL returned a bot-check page; do not bypass. License not confirmed. |
| ealvaradob/phishing-dataset | rejected | Compilation includes Mishra & Soni SMS plus email, URL, and HTML data. Not new SMS data. |
| angelfonsecar/phishing-compilation | rejected | Compilation includes UCI and Mishra & Soni plus email datasets. Not new SMS data. |
| MOZ-Smishing | rejected | SMS-specific and labeled, but Portuguese, not English. |
| ScamNet Fraud Communications Dataset | rejected | Advertises SMS/Text smishing, but contact-only/custom license and not directly public/downloadable. |

## Round 2 Decision

No rows should be imported yet.

The most realistic near-term path is:

1. Re-check Sting9 later or contact maintainers about public access and license.
2. Try to resolve MIMICS-3500 and Smishing-4C access through official author/project pages.
3. Inspect the Zenodo dataset manually for a small, clearly SMS-like subset only if the thesis team accepts row-level manual review.
4. Continue dataset-first searching before moving to manual scam-warning pages.

