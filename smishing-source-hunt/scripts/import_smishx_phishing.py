"""Import smishing rows from the SmishX manually relabeled dataset."""

from __future__ import annotations

import csv
import io

from import_common import append_rows, base_candidate_row, fetch_text, load_existing_rows


SOURCE_URL = "https://github.com/yizhu-joy/SmishX"
DOWNLOAD_URL = "https://raw.githubusercontent.com/yizhu-joy/SmishX/main/data/dataset.csv"


def main() -> None:
    _, seen_ids = load_existing_rows()
    text = fetch_text(DOWNLOAD_URL, timeout=60)
    reader = csv.DictReader(io.StringIO(text))

    rows: list[dict[str, str]] = []
    next_number = 1
    for source_row in reader:
        if (source_row.get("label") or "").strip().lower() != "smishing":
            continue
        message = (source_row.get("SMS") or "").strip()
        if not message:
            continue
        row_id = f"smishx_smishing_{next_number:04d}"
        next_number += 1
        if row_id in seen_ids:
            continue
        note = (
            "Imported from SmishX manually relabeled dataset. "
            f"if_URL={source_row.get('if_URL','')}; if_phone={source_row.get('if_phone','')}; if_email={source_row.get('if_email','')}."
        )
        rows.append(
            base_candidate_row(
                row_id=row_id,
                message_raw=message,
                label="smishing",
                original_label="smishing",
                label_mapping_notes="SmishX original label 'smishing' maps directly to thesis label 'smishing'.",
                source_name="SmishX",
                source_url=SOURCE_URL,
                source_type="GitHub_dataset",
                dataset_name="yizhu-joy/SmishX",
                original_file_format="CSV",
                scam_category="other",
                country_or_region="",
                language="English",
                reviewer_notes=note,
            )
        )
        seen_ids.add(row_id)

    imported = append_rows(rows)
    print(f"Imported {imported} SmishX smishing candidate rows.")


if __name__ == "__main__":
    main()
