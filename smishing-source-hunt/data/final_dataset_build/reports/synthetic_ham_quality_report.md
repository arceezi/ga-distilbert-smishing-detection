# Synthetic Ham Quality Report

Synthetic ham messages were generated from manually approved legitimate service-message templates. Unlike collected public data, these messages are synthetic and contain fake/generated values in the raw text field. A privacy-safe cleaned version was also generated for each synthetic message. Synthetic rows are clearly marked with is_synthetic=True and data_origin=synthetic_template.

- Generated candidates: 1263
- Approved synthetic rows: 1153
- Rejected synthetic rows: 110

## Approved By Category

| Category | Count |
| --- | ---: |
| banking | 252 |
| delivery | 192 |
| ewallet | 64 |
| otp_verification | 292 |
| promo_legitimate | 123 |
| telecom | 230 |

## Rejections

| Reason | Count |
| --- | ---: |
| exact_duplicate | 95 |
| smishing_like_threat_or_scam_urgency | 15 |
