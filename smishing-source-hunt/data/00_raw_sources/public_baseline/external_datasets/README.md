# External Datasets

Use this folder to track public labeled datasets before importing any rows into the candidate CSV.

Do not place large downloaded datasets here unless they are safe to store, public, and permitted by the dataset license or usage terms. When in doubt, store metadata only and keep a note about where the dataset can be obtained.

## Inventory

Maintain `dataset_inventory.csv` for every dataset reviewed. Preserve:

- dataset name
- source URL
- local filename, if downloaded
- file format
- original text column
- original label column
- smishing count
- ham count
- language
- license notes
- status
- notes about cleaning, overlap, or rejection

## Status Values

- `candidate`
- `approved`
- `rejected`
- `needs_review`
- `already_used`

