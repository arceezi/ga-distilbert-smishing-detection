# Research-Backed V3 Build Report

## Purpose

Research-backed legitimate service templates were added to improve synthetic ham diversity and reduce UCI dominance.

## Research Basis

- Microsoft, Google, Apple, Amazon, PayPal
- BDO, BPI
- GCash, Maya
- Globe, Smart
- UPS, USPS, DHL
- VA, NHS/GOV.UK, USCIS

## Template Generation Rules

- Fixed-format OTPs were kept stable and family-capped.
- Bank/card alerts use neutral transaction wording.
- Telecom and delivery messages provide non-scam service-message diversity.
- Customs/payment-like messages are sparse because they resemble smishing.
- No scam-like urgency, gambling/free-spin promos, or synthetic smishing were generated.

## Synthetic Generation Summary

- Generated synthetic candidates: 1300
- Synthetic after family caps: 1300
- Family-cap excluded rows: 0
- Approved synthetic available: 1300
- Rejected synthetic rows: 0
- Approved synthetic used in V3: 1300
- Synthetic shortage versus 1,300 target: 0

### Family Cap Results

| Family cap exclusion reason | Count |
| --- | ---: |

### Rejected Reasons

| Rejected reason | Count |
| --- | ---: |

### Approved Synthetic By Category

| Category | Count |
| --- | ---: |
| appointment_reminder | 26 |
| bank_card_transaction_alert | 45 |
| customs_or_fee_request_low_volume | 13 |
| delivery_tracking_update | 45 |
| ewallet_login_verification | 45 |
| fixed_format_big_brand_otp | 50 |
| generic_account_verification | 45 |
| government_application_acknowledgment | 22 |
| manual_ph_service_templates | 904 |
| risk_based_signin_device_alert | 45 |
| telecom_otp_service_advisory | 60 |

### Accepted Synthetic Examples

- Microsoft security code: 433218. Use this to verify your sign-in.
- Amazon security code: 18495. Enter this code to continue signing in.
- Google verification code: 7672. Enter this code to continue.
- Microsoft security code: 281489. Use this to verify your sign-in. Do not share this code.
- Apple Account verification code: 713315. Enter this code to sign in.
- Microsoft security code: 51333. Use this to verify your sign-in. Enter it only in the official app or site.
- Amazon security code: 4309. Enter this code to continue signing in. Do not share this code.
- Apple Account verification code: 10799. Enter this code to sign in. Do not share this code.

### Rejected Examples

- None

## Final V3 Composition

- Ham: 5272
- Smishing: 5272
- Total: 10544
- Manual real ham: 320
- Synthetic research-backed ham: 1300
- Mishra ham: 462
- UCI ham: 3190
- UCI ham share: 60.51%

## Thesis Methodology Note

To improve legitimate service-message diversity, synthetic ham messages were generated from manually curated service-message templates and research-backed legitimate SMS style rules derived from official or trustworthy sources. Synthetic rows contain fake generated values in the raw text field and a privacy-safe cleaned version. All synthetic rows are explicitly marked as synthetic. The smishing class remains entirely real/public-source based; no synthetic smishing messages were generated.

## Limitations

- Synthetic ham is not collected real-world SMS.
- V1 real-only dataset should remain available as a baseline.
- Research-backed templates are style-inspired, not copied official message rows.
- Link-bearing official-style messages are sparse because they resemble smishing.

## Files

- Public source: `C:\Users\Lenovo\OneDrive\Documents\Coding\Some other\Thesis Data Source research\smishing-source-hunt\data\organized\campaign_family_quality\combined_public_thesis_sources_campaign_family_filtered.csv`
- Manual source: `C:\Users\Lenovo\OneDrive\Documents\Coding\Some other\Thesis Data Source research\smishing-source-hunt\data\final_dataset_build\interim\manual_ham_no_overlap.csv`
- Synthetic source: `C:\Users\Lenovo\OneDrive\Documents\Coding\Some other\Thesis Data Source research\smishing-source-hunt\data\final_dataset_build\interim\synthetic_service_ham_research_backed_approved.csv`
- Final dataset: `C:\Users\Lenovo\OneDrive\Documents\Coding\Some other\Thesis Data Source research\smishing-source-hunt\data\final_dataset_build\final\dataset_v3_public_manual_research_synthetic_ham_balanced.csv`
