# Dataset Search Prompt

Find already-labeled public datasets for English smishing, SMS phishing, scam SMS, or malicious SMS detection.

Prioritize:

1. Datasets with SMS text and labels.
2. Datasets in CSV, JSON, TXT, TSV, XLSX, or another easy-to-convert format.
3. Public academic datasets or repositories from GitHub, Kaggle, Hugging Face, Zenodo, Mendeley Data, IEEE DataPort, or university pages.
4. Datasets with clear license or citation notes.

For each dataset, report:

- dataset name
- source URL
- file format
- original text column
- original label column
- original labels
- estimated smishing/phishing count
- estimated ham/legitimate count
- language
- license or usage note
- whether it overlaps with UCI, Mishra & Soni, SmishTank, or existing thesis sources
- recommended status: candidate, approved, rejected, needs_review, or already_used

Do not prioritize individual example pages until dataset options have been exhausted.

