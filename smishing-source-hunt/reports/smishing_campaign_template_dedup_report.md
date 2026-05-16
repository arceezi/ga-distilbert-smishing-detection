# Smishing Campaign Template Dedup Report

- Smishing rows inspected: 6,972
- Campaign clusters found: 6,516
- Repeated-template rows: 674
- Largest campaign cluster size: 140
- Rows excluded by campaign cap: 441
- Cap rule: keep max 3 rows for large clusters, 2-3 for medium clusters, and 1-2 for small repeated clusters.

## Files Generated

- `data\organized\content_quality\smishing_campaign_template_groups.csv`
- `data\organized\content_quality\smishing_campaign_template_repeats.csv`
- `data\organized\content_quality\campaign_repeat_excluded_archive.csv`
- `reports\smishing_campaign_template_dedup_report.md`
