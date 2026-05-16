# Source Review Prompt

Evaluate whether this smishing data source is acceptable for thesis use.

Check:

- Is the source public?
- Does it provide SMS-like text?
- Does it provide labels?
- Are the labels clear enough to map to `smishing`, `ham`, `unsure`, or `reject`?
- Is the language English or mostly English?
- Does the source include private personal data?
- Does the source have license, citation, or usage notes?
- Is the file format easy to convert?
- Is there likely overlap with UCI, Mishra & Soni, SmishTank, or existing thesis sources?

Return:

- status: candidate, approved, rejected, needs_review, or already_used
- reason
- cleaning needed
- redaction needed
- label mapping notes
- import recommendation

