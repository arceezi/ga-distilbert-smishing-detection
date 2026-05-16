"""Import English smishing rows from the IMC25 public smishing dataset."""

from __future__ import annotations

import csv
import io

from import_common import append_rows, base_candidate_row, fetch_text, load_existing_rows


SOURCE_URL = "https://github.com/reportsmishing/Smishing-Dataset-IMC25"
DOWNLOAD_URL = "https://raw.githubusercontent.com/reportsmishing/Smishing-Dataset-IMC25/main/dataset/final_dataset_output.csv"


def main() -> None:
    _, seen_ids = load_existing_rows()
    text = fetch_text(DOWNLOAD_URL, timeout=180)
    reader = csv.DictReader(io.StringIO(text))

    rows: list[dict[str, str]] = []
    next_number = 1
    for source_row in reader:
        if (source_row.get("language") or "").strip() != "English":
            continue
        message = (source_row.get("text") or "").strip() or (source_row.get("translation") or "").strip()
        if not message:
            continue
        row_id = f"imc25_english_smish_{next_number:05d}"
        next_number += 1
        if row_id in seen_ids:
            continue
        scam_category = (source_row.get("scam_type") or "other").strip() or "other"
        lure_principles = (source_row.get("lure_principles") or "").strip()
        note = "Imported from IMC25 English-only smishing corpus."
        if lure_principles:
            note += f" Lure principles: {lure_principles}."
        if source_row.get("named_entity"):
            note += f" Named entity tag: {source_row['named_entity']}."
        rows.append(
            base_candidate_row(
                row_id=row_id,
                message_raw=message,
                label="smishing",
                original_label="smishing_corpus_row",
                label_mapping_notes="IMC25 rows are all smishing by dataset construction; imported only where language == English.",
                source_name="Smishing-Dataset-IMC25",
                source_url=SOURCE_URL,
                source_type="GitHub_dataset",
                dataset_name="reportsmishing/Smishing-Dataset-IMC25",
                original_file_format="CSV",
                scam_category=scam_category,
                country_or_region=(source_row.get("original_network_country") or "").strip(),
                language="English",
                reviewer_notes=note,
            )
        )
        seen_ids.add(row_id)

    imported = append_rows(rows)
    print(f"Imported {imported} IMC25 English candidate rows.")


if __name__ == "__main__":
    main()
