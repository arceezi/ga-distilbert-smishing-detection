# Labeling Guide

The thesis uses binary classification:

- Class `0`: legitimate / ham
- Class `1`: smishing

In this workspace, use the text labels `ham`, `smishing`, `unsure`, and `reject` until final thesis integration.

## Class 1: Smishing

Use `smishing` if the message attempts SMS-based phishing, fraud, credential theft, payment theft, or social engineering.

A message is likely smishing if it:

- impersonates an institution, company, bank, e-wallet, delivery service, government agency, employer, or telecom provider
- asks for credentials, OTPs, login, verification, payment, card details, or urgent account action
- contains a suspicious link or callback instruction
- uses fear, urgency, reward, account lock, delivery failure, financial bait, or legal/tax pressure
- attempts social engineering for fraud

Examples of smishing categories:

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

## Class 0: Legitimate / Ham

Use `ham` if the message appears legitimate and non-malicious.

Examples:

- normal service notifications
- OTP messages without suspicious requests
- delivery updates without malicious links
- ordinary personal SMS
- ordinary transactional SMS
- appointment reminders
- account activity notices without suspicious actions

## Unsure

Use `unsure` when:

- the message is spam but not clearly phishing
- the original label is broad, such as `spam`, and the text does not clearly show fraud intent
- the message has suspicious elements but not enough context
- the source label mapping is unclear

## Reject

Use `reject` when the row is:

- not SMS-like
- non-English
- too long and email-like
- duplicate-only
- unclear beyond useful review
- missing source name and source URL
- unsafe/private and cannot be redacted cleanly
- not text-only
- a real credential, password, full OTP, account number, address, or other personal data

