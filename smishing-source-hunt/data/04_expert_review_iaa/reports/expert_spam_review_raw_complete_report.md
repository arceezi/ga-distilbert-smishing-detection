# Expert Spam Review Raw-Complete Packet Report

## 1. Purpose
This is a raw-complete expert review set for IAA and future relabeling. Every final sample is intended to preserve complete original-looking SMS text.

## 2. Initial Packet Audit
- initial rows: 500
- placeholder/anonymized rows found: 161
- duplicate rows found: 0
- long rows found: 12
- too-short rows found: 2
- multi-message cells found: 0

## 3. Replacement Process
- rows kept: 320
- rows replaced/requested: 180
- replacement candidates available: 2457
- replacements accepted: 180
- shortage: 0

## 4. Final Packet Composition
### candidate_reason
- weak_signal_suspicious: 328
- needs_smishing_relabel: 84
- conflict_needs_review: 48
- excluded_from_smishing_review: 31
- public_candidate_spam: 6
- possible_spam_not_smishing: 3

### source_name
- Smishing-Dataset-IMC25: 200
- UCI SMS Spam Collection: 107
- Bengali SMS Smishing Dataset: 73
- SmishTank: 55
- Mishra & Soni: 35
- SMS Phishing Dataset: 28
- SmishX: 2

### dataset_name
- reportsmishing/Smishing-Dataset-IMC25: 195
- SMS Spam Collection v.1: 107
- shariul-islam/bengali-sms-smishing-dataset: 73
- SmishTank Dataset / Smishing Dataset I: 55
- SMS Phishing Dataset for Machine Learning and Pattern Recognition: 35
- wspr-ncsu/sms-phishing: 28
- Gathered approved smishing 7k: 5
- yizhu-joy/SmishX: 2

### source_label
- smishing_corpus_row: 200
- spam: 126
- smish: 73
- verified_smishing: 55
- phishing_messages_row: 28
- Smishing: 11
- Spam: 4
- smishing: 2
- ham: 1

### suggested_category
- banking/account-like suspicious: 97
- unclear suspicious message: 97
- generic scam-like or unclear: 72
- delivery-like suspicious: 53
- reward/prize: 49
- telecom promo: 32
- adult/chat promo: 26
- promotional spam: 21
- telecom/ringtone/subscription spam: 19
- job/business funding offer: 12
- job/investment offer: 10
- gambling/casino/free spin: 7
- spam: 4
- crypto/investment offer: 1

### contains_url
- False: 395
- True: 105

### contains_phone
- False: 379
- True: 121

### contains_otp
- False: 495
- True: 5

### contains_amount
- False: 336
- True: 164

## 5. Raw Completeness Validation
All final samples have complete raw message text, no placeholder/anonymized raw tokens remain, and no synthetic rows were intentionally included.

## 6. Expert Instructions Summary
HAM: Legitimate/non-malicious SMS.

SPAM_NOT_SMISHING: Unwanted promotional or irrelevant SMS but not clearly phishing.

SMISHING: SMS phishing/social-engineering attempt involving deception, impersonation, credential/payment request, suspicious link/callback, urgency, account/security/delivery bait, or fraudulent intent.

UNSURE: Ambiguous or needs another reviewer.

REJECT: Not useful, not SMS-like, non-English, artifact, duplicate fragment, abusive reply, or report/commentary text.

Important expert note: Do not label smishing only because there is a URL. Look for deception, impersonation, fraudulent intent, credential/payment request, urgency, or social-engineering purpose.


## 7. Future Use Note
These rows are not yet part of the final dataset. They are held for expert labeling and IAA. After expert review, confirmed labels may be imported, agreement can be computed, disagreements can be resolved, and approved rows can be added to a future dataset version.
