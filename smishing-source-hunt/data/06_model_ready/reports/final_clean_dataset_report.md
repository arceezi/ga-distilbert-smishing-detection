# Final Clean Dataset Report

- Output path: `data/06_model_ready/clean/final_clean_dataset.csv`
- Rows: 10544
- Ham: 5272
- Smishing: 5272
- Synthetic ham: 1300
- Synthetic smishing: 0

## Source Distribution

| Source | Count |
| --- | --- |
| Bengali SMS Smishing Dataset | 557 |
| Mishra & Soni | 625 |
| SMS Phishing Dataset | 2010 |
| SmishTank | 744 |
| SmishX | 192 |
| Smishing-Dataset-IMC25 | 1606 |
| UCI SMS Spam Collection | 3190 |
| manual_google_drive_ham | 320 |
| service_ham_template_generator | 1300 |

## Data Origin Distribution

| Data origin | Count |
| --- | --- |
| manual_real | 320 |
| public_real | 8924 |
| synthetic_template | 1300 |

## Text Quality

| Check | Value |
| --- | --- |
| empty message_raw | 0 |
| empty message_clean | 0 |
| duplicate normalized key rows | 309 |
| raw max length | 946 |
| clean max length | 925 |
