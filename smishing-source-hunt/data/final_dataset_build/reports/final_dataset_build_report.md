# Final Dataset Build Report

## Purpose

This build integrates manually curated service ham and synthetic service ham to address UCI-dominated ham in the public thesis dataset.

## Source Inputs

- Public campaign-family-filtered dataset: `C:\Users\Lenovo\OneDrive\Documents\Coding\Some other\Thesis Data Source research\smishing-source-hunt\data\organized\campaign_family_quality\combined_public_thesis_sources_campaign_family_filtered.csv`
- Approved cleaned manual ham standardized through: `C:\Users\Lenovo\OneDrive\Documents\Coding\Some other\Thesis Data Source research\smishing-source-hunt\data\final_dataset_build\interim\manual_ham_no_overlap.csv`
- Generated synthetic service ham approved through: `C:\Users\Lenovo\OneDrive\Documents\Coding\Some other\Thesis Data Source research\smishing-source-hunt\data\final_dataset_build\interim\synthetic_service_ham_approved.csv`

## Manual Ham Processing

- Manual input rows: 320
- Overlap removed/archive rows: 0
- Final manual ham included in V3: 320

### Manual Category Distribution

| Service category | Count |
| --- | ---: |
| account_security | 1 |
| banking | 82 |
| delivery | 10 |
| ewallet | 4 |
| otp_verification | 95 |
| payment_confirmation | 1 |
| promo_legitimate | 13 |
| telecom | 64 |
| unsure | 50 |

## Template Extraction

- Templates extracted: 173
- Templates rejected/skipped: 147 row-level inputs not converted to unique approved template candidates

### Templates By Category

| Service category | Count |
| --- | ---: |
| banking | 69 |
| delivery | 10 |
| ewallet | 4 |
| otp_verification | 20 |
| payment_confirmation | 1 |
| promo_legitimate | 13 |
| telecom | 56 |

### Template Examples

| Template ID | Category | Template |
| --- | --- | --- |
| service_ham_template_00001 | banking | Banks closed this Holy Week. Deposit or withdraw from your <BRAND> account for FREE at any of our participating partner stores nationwide. Just ask a store personnel for assistance. |
| service_ham_template_00002 | banking | Get up to <AMOUNT> eGCs for fuel, groceries, and more with a new <BRAND> Credit Card - plus waived annual fees*! Apply in just 3 minutes via the <BRAND> app or <BRAND> online - no docs needed. Just log in and tap the inbox/envelope icon to start! You can text BPICC (space) C-J5YS4 (space) FULL NAME & send to <ACCT> until 04/15/26. *T&Cs apply. DTI#250009, $2026. Text STOP to <PHONE> to unsubscribe. |
| service_ham_template_00003 | banking | Get a chance to win up to <BRAND>voucher when you buy at least <AMOUNT> regular <BRAND> load on the <BRAND> App. Just log in to your account, and tap 'Send Load". Promo runs from <DATE_TIME> to <DATE_TIME>, 2026. T&Cs apply. <BRAND> is BSP-regulated. DT1248176 |
| service_ham_template_00004 | banking | Score deals at the <BRAND> Birthday Sale with your RCBC Mastercard Credit Card! Enjoy extra <AMOUNT> OFF, min. spend <AMOUNT>. Offer is until Mar. 27, 2026. Discount auto-applied at checkout; no code needed. For info, search LAZBDAY26 on the RCBC Credit website. DTI#252224 |
| service_ham_template_00005 | banking | 1ue, Mar ot at 9-92 FM Last chance to earn eGCs! Start referring friends now to apply for their first <BRAND> credit card using your code ACO135. Earn <AMOUNT> eGCs for every successful referral until <DATE_TIME>, 2026 only! Visit our website for the application link & T&Cs. DTI245534S2025 CCPD26-041 |

## Synthetic Ham Generation

- Target synthetic count: 1,300
- Generated synthetic count: 1263
- Approved synthetic count available: 1153
- Rejected synthetic count: 110
- Approved synthetic count used in V3: 1112
- Max per template: 20
- Max per family: 50 command-line option retained for auditability; template-level cap controlled generation.

### Approved Synthetic By Category

| Service category | Count |
| --- | ---: |
| banking | 252 |
| delivery | 192 |
| ewallet | 64 |
| otp_verification | 292 |
| promo_legitimate | 123 |
| telecom | 230 |

### Synthetic Rejections

| Reason | Count |
| --- | ---: |
| exact_duplicate | 95 |
| smishing_like_threat_or_scam_urgency | 15 |

## Final Dataset Versions

| Dataset Version | Ham | Smishing | Total | Manual Ham | Synthetic Ham | UCI Ham | Mishra Ham | Purpose |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| V1 | 4954 | 4954 | 9908 | 0 | 0 | 4492 | 462 | Public real-only baseline |
| V2 | 5272 | 5272 | 10544 | 320 | 0 | 4490 | 462 | Public plus manual real ham |
| V3 | 5272 | 5272 | 10544 | 320 | 1112 | 3378 | 462 | Expanded ham-diversity dataset |

## Ham Diversity Improvement

- V1 UCI ham share: 90.67%
- V3 UCI ham share: 64.07%

## Thesis Methodology Note

To reduce the dominance of casual UCI ham messages, the final expanded dataset incorporated manually curated legitimate service SMS messages and synthetic service-ham messages generated from approved manual templates. Synthetic messages were limited to legitimate non-malicious service notifications and were clearly marked as synthetic. The smishing class remained fully real/public-source based; no synthetic smishing messages were generated.

Synthetic ham messages were generated from manually approved legitimate service-message templates. Unlike collected public data, these messages are synthetic and contain fake/generated values in the raw text field. A privacy-safe cleaned version was also generated for each synthetic message. Synthetic rows are clearly marked with is_synthetic=True and data_origin=synthetic_template.

## Limitations

- Synthetic ham is not real-world collected SMS and is marked separately.
- V1 real-only dataset remains the baseline.
- V3 should be treated as the expanded ham-diversity dataset.

## Files Generated

- `C:\Users\Lenovo\OneDrive\Documents\Coding\Some other\Thesis Data Source research\smishing-source-hunt\data\final_dataset_build\final\dataset_v1_public_real_only_balanced.csv`
- `C:\Users\Lenovo\OneDrive\Documents\Coding\Some other\Thesis Data Source research\smishing-source-hunt\data\final_dataset_build\final\dataset_v2_public_plus_manual_ham_balanced.csv`
- `C:\Users\Lenovo\OneDrive\Documents\Coding\Some other\Thesis Data Source research\smishing-source-hunt\data\final_dataset_build\final\dataset_v3_public_manual_synthetic_ham_balanced.csv`
- `C:\Users\Lenovo\OneDrive\Documents\Coding\Some other\Thesis Data Source research\smishing-source-hunt\data\final_dataset_build\final\reserved_extra_smishing.csv`
- `C:\Users\Lenovo\OneDrive\Documents\Coding\Some other\Thesis Data Source research\smishing-source-hunt\data\final_dataset_build\final\reserved_unused_ham.csv`
- `C:\Users\Lenovo\OneDrive\Documents\Coding\Some other\Thesis Data Source research\smishing-source-hunt\data\final_dataset_build\final\reserved_synthetic_ham_unused.csv`
