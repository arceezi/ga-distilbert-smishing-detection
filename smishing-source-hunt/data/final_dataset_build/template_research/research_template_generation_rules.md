# Research Template Generation Rules

These templates are style-inspired from the Deep Research report, not copied official SMS datasets.

- Use fake/generated slot values only.
- Generate ham only; do not generate synthetic smishing.
- Keep big-brand OTP wording stable and cap each brand family.
- Prefer no-link templates, especially for Philippine finance and telecom.
- Keep customs/payment-like logistics messages sparse and shipment-specific.
- Reject scam-like urgency, gambling/free-spin language, account-lock threats, shortened URLs, and requests to share OTP/PIN/password/CVV.
- Produce `message_raw` with filled values and `message_clean` with privacy placeholders.
