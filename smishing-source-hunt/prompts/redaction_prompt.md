# Redaction Prompt

Redact sensitive values from this SMS-like message while preserving the phishing pattern.

Replace:

- URLs with `<URL>`
- phone numbers with `<PHONE>`
- emails with `<EMAIL>`
- OTPs or verification codes with `<OTP>`
- account numbers with `<ACCT>`
- identifiable names with `<NAME>` when not necessary

Do not preserve real credentials, passwords, full OTPs, private account details, addresses, or phone numbers.

Return:

- redacted message
- list of redaction types applied
- whether the message should be rejected for unsafe private data

