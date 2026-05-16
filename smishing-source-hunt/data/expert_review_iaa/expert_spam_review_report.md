# Expert Spam Review Packet Report

## 1. Purpose
This is a separate expert-review set for IAA/relabeling of spam or suspicious SMS messages. It is not part of the final training dataset.

## 2. Source Files Inspected
- data/organized/campaign_family_quality/strong_campaign_family_excluded_archive.csv
- data/organized/combined_public_thesis_sources_deduped_representatives.csv
- data/organized/combined_public_thesis_sources_uniform.csv
- data/organized/content_quality/content_removed_archive.csv
- data/organized/raw_quality/strict_raw_removed_archive.csv
- data/organized/raw_recovery/collected_smishing_candidates_raw_classified.csv
- data/organized/text_verified/combined_public_thesis_sources_deduped_representatives_text_verified.csv
- data/organized/text_verified/combined_public_thesis_sources_text_verified.csv
- data/raw/collected_smishing_candidates.csv

## 3. Candidate Pool Summary
- total raw candidates found: 11083
- valid candidates after filtering: 10452
- representative candidates available after deduplication: 4862
- duplicates removed: 5590
- final review packet size: 500

## 4. Sampling Strategy
Sampling used seed 42 by default, reason-based strata, one representative per exact normalized duplicate cluster, a maximum of 5 per normalized template family, and a maximum of 10 per detectable broad source/campaign family.

## 5. Review Packet Composition
### candidate_reason
- public_candidate_spam: 165
- weak_signal_suspicious: 148
- needs_smishing_relabel: 84
- conflict_needs_review: 50
- excluded_from_smishing_review: 50
- possible_spam_not_smishing: 3

### source_name
- Smishing-Dataset-IMC25: 276
- UCI SMS Spam Collection: 109
- SMS Phishing Dataset: 41
- Mishra & Soni: 29
- Bengali SMS Smishing Dataset: 24
- SmishTank: 17
- SmishX: 4

### dataset_name
- reportsmishing/Smishing-Dataset-IMC25: 275
- SMS Spam Collection v.1: 109
- wspr-ncsu/sms-phishing: 41
- SMS Phishing Dataset for Machine Learning and Pattern Recognition: 29
- shariul-islam/bengali-sms-smishing-dataset: 24
- SmishTank Dataset / Smishing Dataset I: 17
- Gathered approved smishing 7k: 3
- yizhu-joy/SmishX: 2

### source_label
- smishing_corpus_row: 276
- spam: 126
- phishing_messages_row: 41
- smish: 24
- verified_smishing: 17
- Smishing: 5
- Spam: 4
- smishing: 4
- ham: 3

### contains_url
- False: 336
- True: 164

### contains_otp
- False: 485
- True: 15

### contains_phone
- False: 376
- True: 124

### contains_amount
- False: 284
- True: 216

## 6. Expert Codebook Summary
Expert labels are ham, spam_not_smishing, smishing, unsure, and reject. Smishing requires deception, impersonation, credential/payment request, urgency, or social-engineering intent; a URL alone is not enough.

## 7. Important Limitation
This review packet is not yet part of the final training dataset. It is for expert review and IAA first.

## 8. Next Step After Expert Review
- import expert labels
- compute agreement / IAA
- resolve disagreements
- create approved relabeled rows
- decide whether to add confirmed smishing or ham/spam to future dataset versions
