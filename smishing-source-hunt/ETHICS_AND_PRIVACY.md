# Ethics and Privacy

This workspace must avoid collecting private, sensitive, or personally identifying information. The dataset should support defensive smishing detection research, not preserve real victim data.

## Strict Rules

- Do not collect personal identifying information.
- Do not collect real credentials, passwords, recovery phrases, or full personal data.
- Do not collect private phone numbers, names, addresses, account numbers, or real OTPs.
- Do not bypass website restrictions.
- Do not scrape aggressively.
- Do not import data from private forums, private chats, leaked databases, credential dumps, or sources without a clear public research or awareness purpose.
- Every row must preserve source traceability through `source_url` or `source_name`.

## Redaction Rules

In cleaned and final versions:

- Replace phone numbers with `<PHONE>`.
- Replace URLs with `<URL>`, while keeping the source URL separately in `source_url`.
- Replace OTPs and verification codes with `<OTP>`.
- Replace emails with `<EMAIL>`.
- Replace names with `<NAME>` when the name is identifiable and not necessary.
- Replace account numbers with `<ACCT>`.

## Raw Data Handling

- Keep original raw candidates only if they are safe and public.
- If a public example contains sensitive values, redact before saving or reject the row.
- Do not store credentials, passwords, real OTPs, or full private account details in raw files.
- Prefer dataset-level source traceability over copying excessive source page text.

## Final Dataset Principle

The final exported dataset should contain English, SMS-like, text-only messages with sensitive details redacted. It should be suitable for defensive research and reproducible academic documentation.

