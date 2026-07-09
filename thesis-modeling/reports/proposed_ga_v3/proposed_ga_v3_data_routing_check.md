# Proposed GA v3 Data Routing Check

- Engineered features were required to come from `message_raw`: True.
- DistilBERT embeddings were required to come from `model_text`: True.
- G1-G8 order was checked exactly: ['G1_URL_Signals', 'G2_OTP_Numeric_Density', 'G3_Obfuscation', 'G4_Urgency_Threat_Cues', 'G5_Action_Directives', 'G6_Financial_Terms', 'G7_Auth_Secrets_Request', 'G8_Brand_Impersonation'].
- Fusion dimension remained 768 + 8 = 776.
- Phase A training used `train_clean`; early stopping used `val_clean`.
- GA validation used only: ['val_clean', 'val_adv_10', 'val_adv_20', 'val_adv_30'].
- Phase C training used `train_clean`; early stopping used `val_clean`.
- Threshold tuning used validation splits only: ['val_clean', 'val_adv_10', 'val_adv_20', 'val_adv_30'].
- Final evaluation used only: ['test_clean', 'test_adv_10', 'test_adv_20', 'test_adv_30'].
- Test sets were excluded from GA, threshold tuning, early stopping, and model selection.
- `val_adv_30` was treated as validation-only and was not used for final test reporting.
