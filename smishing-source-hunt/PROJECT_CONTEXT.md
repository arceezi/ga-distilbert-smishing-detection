# Project Context

Thesis title:

> Genetic Algorithm-Evolved Feature-Group Importance Weighting Fused with Frozen DistilBERT Embeddings for Adversarially Robust English Smishing Detection

## Classification Task

The thesis uses binary SMS classification:

- `0`: ham / legitimate SMS
- `1`: smishing SMS

The scope is English, text-only, SMS-like messages. Messages should be short enough to plausibly represent SMS or text-message content, even when collected from public datasets or scam-awareness pages.

## Dataset Direction

Target final experimental dataset:

- total messages: about 10,000
- ham / legitimate: about 5,000
- smishing: about 5,000

Current issue:

- the smishing class is underrepresented
- current known verified smishing from thesis sources is around 1,700 before additional dataset searching
- additional smishing needed is around 3,000+

## Existing Thesis Source Context

The thesis has used or considered sources such as:

- UCI SMS Spam Collection
- Mishra & Soni SMS dataset
- SmishTank Dataset
- manually curated legitimate service messages
- manually reviewed or relabelled spam/smishing samples

This workspace should check whether newly found datasets overlap with those sources before approval.

## Research Focus

The preferred strategy is to find public labeled datasets that are directly usable or nearly usable. Manual collection from individual web pages should be secondary and used only when labeled datasets are not enough.

