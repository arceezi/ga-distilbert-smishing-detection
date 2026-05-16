# Secondary Collection Workflow

Use this workflow only after the dataset-first search has been exhausted or blocked.

## When To Start

Begin secondary collection if:

- Sting9 remains inaccessible or license-blocked.
- MIMICS-3500 and Smishing-4C cannot provide public downloadable data.
- The English candidate pool remains far below the smishing target after review and deduplication.

## Allowed Source Types

Use only public, traceable pages such as:

- bank scam-warning pages
- telecom scam-warning pages
- courier/delivery scam-warning pages
- government consumer-protection pages
- cybersecurity awareness reports with real SMS examples
- public university or NGO scam-awareness pages

## Collection Rules

- Collect only English, SMS-like examples.
- Every row must have `source_name` or `source_url`.
- Do not scrape aggressively.
- Do not bypass website restrictions.
- Do not collect credentials, real OTPs, names, full phone numbers, addresses, or account numbers.
- Redact sensitive values before cleaned/final use.
- Label all manually collected examples as `candidate` until reviewed.

## Review Gate

Approve only if the message:

- is short-form and SMS-like
- is English
- shows smishing intent such as impersonation, suspicious link, credential request, urgent payment, account lock, prize bait, or callback fraud
- has source traceability
- can be safely redacted

Reject if:

- source is unclear
- message is email-like or too long
- message is non-English or code-mixed
- message contains unsafe private data that cannot be cleanly redacted
- message is synthetic but not explicitly marked as synthetic

## Suggested Categories

- banking
- ewallet
- delivery
- otp_verification
- account_suspension
- prize_reward
- government
- telecom
- job_offer
- crypto_investment
- other

