# Expert Spam/Smishing Review Codebook

Purpose: label each SMS independently for expert review and inter-annotator agreement.

## HAM
Legitimate/non-malicious SMS.

Examples:
- normal OTP
- transaction alert
- delivery update
- telecom notice
- appointment reminder
- personal message

## SPAM_NOT_SMISHING
Unwanted promotional or irrelevant message but not clearly phishing.

Examples:
- generic ads
- gambling/casino/free-spin promos without credential theft
- adult/chat promo
- aggressive marketing
- random prize/reward promo without clear impersonation or credential/payment request

## SMISHING
SMS phishing/social-engineering attempt.

Examples:
- impersonates a bank, e-wallet, courier, telecom, government, or known service
- asks for login, OTP, password, PIN, payment, or account verification
- contains suspicious link/callback instruction
- threatens account lock/suspension
- uses financial/security/delivery urgency to make user act
- attempts credential theft or fraudulent payment

## UNSURE
Unclear, ambiguous, incomplete, or needs another reviewer.

## REJECT
Not useful for dataset.

Examples:
- not SMS-like
- OCR artifact
- non-English if out of scope
- abusive reply to scammer
- report/commentary text
- too incomplete
- duplicate fragment

Important: do not label a message as smishing only because it contains a URL. Look for deception, impersonation, credential/payment request, urgency, or social-engineering intent.

Allowed expert_label values: ham, spam_not_smishing, smishing, unsure, reject.

Allowed expert_confidence values: high, medium, low.

Generated: 2026-05-13
