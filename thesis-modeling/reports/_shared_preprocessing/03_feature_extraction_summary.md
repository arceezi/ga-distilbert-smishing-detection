# 03 Corrected Feature Extraction Summary

Corrected engineered features are generated in the exact thesis order:

1. G1_URL_Signals
2. G2_OTP_Numeric_Density
3. G3_Obfuscation
4. G4_Urgency_Threat_Cues
5. G5_Action_Directives
6. G6_Financial_Terms
7. G7_Auth_Secrets_Request
8. G8_Brand_Impersonation

Engineered feature source column: message_raw

DistilBERT embedding source column: model_text

Feature extraction uses `message_raw` exactly. Embedding extraction uses `model_text` exactly.

## Split Checks

| split       |   dataset_rows |   feature_rows |   feature_columns | feature_text_source   |   label_0_count |   label_1_count |   missing_feature_values |
|:------------|---------------:|---------------:|------------------:|:----------------------|----------------:|----------------:|-------------------------:|
| train_clean |           7380 |           7380 |                 8 | message_raw           |            3690 |            3690 |                        0 |
| val_clean   |           1582 |           1582 |                 8 | message_raw           |             791 |             791 |                        0 |
| test_clean  |           1582 |           1582 |                 8 | message_raw           |             791 |             791 |                        0 |
| val_adv_10  |           1582 |           1582 |                 8 | message_raw           |             791 |             791 |                        0 |
| val_adv_20  |           1582 |           1582 |                 8 | message_raw           |             791 |             791 |                        0 |
| val_adv_30  |           1582 |           1582 |                 8 | message_raw           |             791 |             791 |                        0 |
| test_adv_10 |           1582 |           1582 |                 8 | message_raw           |             791 |             791 |                        0 |
| test_adv_20 |           1582 |           1582 |                 8 | message_raw           |             791 |             791 |                        0 |
| test_adv_30 |           1582 |           1582 |                 8 | message_raw           |             791 |             791 |                        0 |

## Leakage Routing

Feature extraction is deterministic preprocessing. val_adv_30 was created from val_clean only when needed. Test data was not used in feature extraction decisions, training, GA, or threshold tuning.
