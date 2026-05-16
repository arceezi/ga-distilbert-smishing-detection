# Source Coverage

Use this report to check whether the collected smishing messages cover varied scam types and source types.

## Source Type Coverage

| Source Type | Count | Notes |
|---|---:|---|
| labeled_dataset | 19 | Four discovery rounds logged in `DATASET_SEARCH_LOG.md`; four sources now approved for candidate import. |
| academic_dataset | 6 | Mishra & Soni, SmishTank, Zenodo multiclass, BangalaBarta, MIMICS-3500, Smishing-4C. |
| GitHub_dataset | 4 | IMC25, NCSU SMS Phishing Dataset, and SmishX are now approved for candidate import; angelfonsecar compilation remains rejected. |
| Kaggle_dataset | 1 | Kaggle SMS Smishing Collection rejected due modified UCI-like content. |
| HuggingFace_dataset | 5 | Bengali SMS Smishing Dataset English smish subset imported as candidates; DIFrauD is overlap-only; others rejected. |
| Zenodo_dataset | 1 | Multiclass NLP phishing/social engineering dataset needs review. |
| Mendeley_dataset | 2 | Mishra & Soni already used; BangalaBarta rejected for non-English. |
| IEEE_DataPort_dataset | 0 | Review access and usage restrictions |
| scam_warning_page | 0 | Secondary only |

## Round 4 Candidate Coverage

| Source | Candidate Rows | Exact-Unique After Dedup | Status |
|---|---:|---:|---|
| SMS Phishing Dataset (`wspr-ncsu/sms-phishing`) | 68,029 | 27,571 | reserve_candidate; no approvals until English/campaign triage |
| Smishing-Dataset-IMC25 | 22,078 | 15,433 | 6,869 strict-clean approved after review round 3 |
| Bengali SMS Smishing Dataset, English smish subset | 776 | 663 | candidate_imported; spot review only |
| SmishX | 259 | 214 | 131 strict-clean approved after review round 2 |

## Scam Category Coverage

| Scam Category | Count | Notes |
|---|---:|---|
| banking | 4,057 | Approved from IMC25 after strict review round 3. |
| ewallet | 0 | Not separately mapped yet; some wallet rows may be under IMC25 `banking` or `others`. |
| delivery | 768 | Approved from IMC25 after strict review round 3. |
| otp_verification | 0 | Not separately mapped yet. |
| account_suspension | 0 | Not separately mapped yet; many account-risk rows remain under source categories. |
| prize_reward | 0 | Not separately mapped yet. |
| government | 726 | Approved from IMC25 after strict review round 3. |
| telecom | 94 | Approved from IMC25 after strict review round 3. |
| job_offer | 0 | Not separately mapped yet. |
| crypto_investment | 0 | Not separately mapped yet. |
| other | 1,335 | 805 IMC25 `others`, 345 IMC25 `spam`, 49 IMC25 `wrong number`, 25 IMC25 `hey mum/dad`, and 131 SmishX rows currently map outside the tracker categories. |
