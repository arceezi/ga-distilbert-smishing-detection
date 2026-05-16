# Balanced Expert Spam Review Packet Report

## 1. Purpose
This revised packet adds more general/conversational spam so expert review can distinguish spam_not_smishing from smishing.

## 2. Source Basis
UCI / SMS Spam Collection is a suitable public source for mobile spam research because it contains SMS spam rows originally collected for spam filtering research.

## 3. Old Packet Summary
- old packet rows: 500
- old packet was raw-complete but likely smishing-heavy

## 4. New Sampling Strategy
- target likely_smishing: 300
- target likely_spam_not_smishing: 175
- target unclear/conflict/reject: 25
- shortage: 0
- source cap: no source should exceed 40%; UCI can be heavy for conversational spam but is reported.

## 5. Final Packet Composition
### likely_review_bucket
- likely_smishing: 300
- likely_spam_not_smishing: 175
- unclear_review: 25
### source_name
- Smishing-Dataset-IMC25: 200
- UCI SMS Spam Collection: 188
- Bengali SMS Smishing Dataset: 44
- SmishTank: 39
- Mishra & Soni: 23
- SMS Phishing Dataset: 6
### candidate_reason
- weak_signal_suspicious: 245
- original_spam_label: 193
- public_candidate_spam: 54
- excluded_from_smishing_review: 5
- conflict_needs_review: 2
- possible_spam_not_smishing: 1
### suggested_category
- unclear suspicious message: 259
- telecom/ringtone/subscription spam: 118
- adult/chat promo: 41
- prize/reward promo: 28
- promotional spam: 24
- gambling/casino/free spin: 11
- government/tax/benefit suspicious: 8
- banking/account-like suspicious: 7
- delivery-like suspicious: 4

## 6. Validation Results
The packet is raw-complete by construction, contains no synthetic rows by source filtering, has no placeholder raw messages, and uses normalized duplicate controls.

## 7. Use Note
This packet is for expert review and IAA only. It is not yet added to the final dataset.
