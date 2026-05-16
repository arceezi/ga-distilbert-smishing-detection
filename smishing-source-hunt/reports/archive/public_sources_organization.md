# Public Sources Organization

## Summary

- Combined row-level total: 19,607
- Ham: 9,671
- Spam / relabel review: 1,236
- Smishing: 8,700
- Deduped representative rows: 13,712
- Duplicate clusters: 5,170
- Extra duplicate rows: 5,895
- Label-conflict duplicate clusters: 277

## Source Counts

| Source | Total | Ham | Spam | Smishing |
|---|---:|---:|---:|---:|
| UCI SMS Spam Collection | 5,574 | 4,827 | 747 | 0 |
| Mishra & Soni | 5,971 | 4,844 | 489 | 638 |
| SmishTank | 1,062 | 0 | 0 | 1,062 |
| Gathered approved smishing 7k | 7,000 | 0 | 0 | 7,000 |

## Duplicate Clusters By Source

| Sources | Clusters |
|---|---:|
| Mishra & Soni + UCI SMS Spam Collection | 4,931 |
| SmishTank + Smishing-Dataset-IMC25 | 96 |
| UCI SMS Spam Collection | 37 |
| SmishTank | 36 |
| Smishing-Dataset-IMC25 | 32 |
| Mishra & Soni | 18 |
| SmishTank + SmishX | 11 |
| Mishra & Soni + SmishX | 4 |
| Mishra & Soni + SmishX + UCI SMS Spam Collection | 3 |
| SmishTank + SmishX + Smishing-Dataset-IMC25 | 2 |

## Duplicate Clusters By Label

| Labels | Clusters |
|---|---:|
| ham | 4,399 |
| spam | 298 |
| smishing + spam | 277 |
| smishing | 196 |

## Files

- `data/final/approved_smishing_messages.csv` is the only retained file in `data/final`.
- Uniform source CSVs are in `data/organized/`.
- Raw public baseline files were moved to `data/source_archives/public_baseline/`.
- Duplicate round exports were moved to `data/exports/archive/`.

## Notes

- This is an organized source catalog, not the final model-ready training split.
- Spam rows are preserved for later smishing relabel review.
- Label-conflict duplicate clusters are marked `conflict_needs_review` and are not forced into a final training label.
