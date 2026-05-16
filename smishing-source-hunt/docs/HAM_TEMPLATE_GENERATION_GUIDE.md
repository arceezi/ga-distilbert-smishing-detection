# Ham Template Generation Guide

## Allowed ham template types

Use only approved legitimate ham patterns, especially:

- OTP and verification messages
- Bank transaction alerts
- E-wallet notifications
- Delivery updates
- Telecom notices
- Government advisories
- Account/security notifications
- Payment confirmations
- Appointment and reminder messages
- School, work, or administrative notices
- Clearly legitimate promos

## Unsafe template types to avoid

Reject templates that:

- Ask the user to provide passwords, OTPs, PINs, or credentials
- Use urgent threat language such as account closure unless the reviewed source is clearly a normal security notice
- Ask the user to click suspicious, shortened, or unknown links
- Contain private personal data that cannot be safely replaced
- Are non-English, incomplete, not SMS-like, duplicated, or copied from smishing examples
- Were derived from rows labeled `smishing`, `unsure`, or `reject`
- Have `reviewer_notes` indicating uncertainty, suspiciousness, OCR/extraction issues, or unresolved conflicts

## Placeholder rules

Replace variable or sensitive content consistently:

- OTP/code: `<OTP>`
- Money amount: `<AMOUNT>`
- Date/time: `<DATE_TIME>`
- Phone number: `<PHONE>`
- Email address: `<EMAIL>`
- URL: `<URL>`
- Account, card, transaction, tracking, or reference number: `<REF_NUM>`
- Person name: `<NAME>`
- Institution or brand when variable: `<BRAND>`
- Location: `<LOCATION>`

Prefer placeholders over realistic sensitive values in final synthetic messages.

For manual Google Drive ham, extracted text is already privacy-redacted. Preserve existing placeholders such as `<OTP>`, `<PHONE>`, `<URL>`, `<ACCT>`, and `<NAME>`; never reconstruct real OTPs, phone numbers, names, URLs, or account numbers.

## Good template examples

Redacted source example:

`Your BDO OTP is 839201. Do not share this code with anyone.`

Template:

`Your <BRAND> OTP is <OTP>. Do not share this code with anyone.`

Redacted source example:

`J&T Express: Your parcel is out for delivery today. Track using ref 123456789.`

Template:

`<BRAND>: Your parcel is out for delivery <DATE_TIME>. Track using ref <REF_NUM>.`

Redacted source example:

`GCash: You received PHP 500.00 from Juan. Ref 123456.`

Template:

`<BRAND>: You received PHP <AMOUNT> from <NAME>. Ref <REF_NUM>.`

## Rejected template examples

Reject:

`Your account will be locked. Verify now at bit.ly/example.`

Reason: threat and suspicious link pattern.

Reject:

`Send your OTP to continue receiving rewards.`

Reason: asks user to provide OTP.

Reject:

`Please login with your password at <URL>.`

Reason: credential collection pattern.

## Review checklist

Before approving a template or synthetic output:

- Confirm it was derived only from approved ham.
- Confirm reviewer notes do not describe uncertainty, suspiciousness, OCR/extraction issues, or unresolved conflicts.
- Confirm no private personal data remains.
- Confirm the text is English and SMS-like.
- Confirm links are placeholders, not suspicious real domains.
- Confirm the message does not request credentials, OTP disclosure, or payment to an unknown party.
- Confirm the service category is appropriate.
- Keep synthetic rows marked and reported separately from real ham.
