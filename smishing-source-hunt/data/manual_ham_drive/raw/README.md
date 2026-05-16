# Manual Ham Drive Raw Imports

Place manually exported Google Drive files in this folder before running the import workflow.

Expected source folder:

https://drive.google.com/drive/folders/17QPkkHmConRJY9WUEqVJXtKsgNPJLPJC

Supported local inputs:

- `.csv`
- `.xlsx`
- `.txt`

Zip exports may also be placed one level up in `data/manual_ham_drive/`. The import script extracts them into `raw/drive_export/` and imports only the manual-curated `THESIS/CLEANED/cleaned_dataset.csv` branch for the current Drive export.

The `analysisdataset` branch in this archive is excluded because it matches the public SmishTank source lineage already present in the thesis public-source pipeline.

For the active manual ham workflow, only the structured rows in `THESIS/CLEANED/cleaned_dataset.csv` are imported. The `PRECLEANED` image files are kept as raw archive material only and are not added as separate review rows.

Image files are not OCR-processed by default. If screenshots are placed here, the import script records them as `needs_manual_transcription` so reviewers can transcribe usable SMS text into a CSV or text file.

Do not place final model-ready datasets here. This folder is for raw manual-curation exports only.
