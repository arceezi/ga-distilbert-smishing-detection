# Smishing Content Quality Audit

## Purpose

This audit flags smishing-labeled rows that appear to be replies, commentary, generic spam, or otherwise weak smishing examples.

- Smishing rows inspected: 6,972
- Flagged for review/removal: 815
- Obvious non-smishing rows: 3

## Status Counts

| content_quality_status | rows |
| --- | --- |
| pass_likely_smishing | 6157 |
| review_unclear_smishing | 796 |
| review_possible_spam_not_smishing | 16 |
| fail_obvious_non_smishing | 3 |

## Flag Counts

| flag | rows |
| --- | --- |
| action_request | 4829 |
| url_or_domain | 4020 |
| account_payment_credential | 3549 |
| urgency_or_security | 1259 |
| weak_actionable_signal | 762 |
| delivery_theme | 705 |
| callback_phone | 525 |
| government_theme | 360 |
| reward_with_action | 314 |
| abusive_or_reply_text | 3 |
| profanity_reply | 1 |

## Obvious Non-Smishing Examples

- `replacement_imc25_english_smish_02996`: I sent money to the wrong person (single digit error).
- `replacement_imc25_english_smish_04370`: Who is this if I don't know you please stop texting me before I report it to the police
- `strict_replacement_imc25_english_smish_17399`: Fuck you scammer! I'll find you and I'm coming for you. 💀

## Files Generated

- `data\organized\content_quality\smishing_content_quality_flags.csv`
- `data\organized\content_quality\obvious_non_smishing_review.csv`
- `reports\smishing_content_quality_audit.md`
