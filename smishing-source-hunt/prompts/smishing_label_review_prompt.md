# Smishing Label Review Prompt

Review whether the following SMS-like message should be labeled as `smishing`, `ham`, `unsure`, or `reject`.

Use `smishing` if the message:

- impersonates an institution or service
- asks for credentials, OTPs, login, verification, payment, or urgent action
- contains a suspicious link or callback instruction
- uses fear, urgency, reward, account lock, delivery failure, or financial bait
- attempts social engineering for fraud

Use `ham` for legitimate service messages, ordinary transactional SMS, OTPs without suspicious requests, delivery updates without malicious links, or ordinary personal SMS.

Use `unsure` for broad spam or ambiguous messages that are not clearly phishing.

Use `reject` for non-English, non-SMS-like, too long, duplicate-only, no source, unclear beyond review, or unsafe/private content that cannot be redacted.

Return:

- recommended label
- confidence
- scam category if smishing
- reason
- redaction needed
- reviewer notes

