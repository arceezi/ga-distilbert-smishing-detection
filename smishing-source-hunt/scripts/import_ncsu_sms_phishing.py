"""Import phishing rows from the public NCSU SMS phishing dataset."""

from __future__ import annotations

import csv
import io

from import_common import append_rows, base_candidate_row, fetch_text, load_existing_rows


SOURCE_URL = "https://github.com/wspr-ncsu/sms-phishing"
DOWNLOAD_URL = "https://raw.githubusercontent.com/wspr-ncsu/sms-phishing/main/phishing_messages.csv"


def main() -> None:
    _, seen_ids = load_existing_rows()
    text = fetch_text(DOWNLOAD_URL, timeout=180)
    reader = csv.reader(io.StringIO(text))

    rows: list[dict[str, str]] = []
    header_skipped = False
    next_number = 1
    for source_row in reader:
        if not header_skipped:
            header_skipped = True
            continue
        if len(source_row) < 7:
            continue
        message = (source_row[3] or "").strip()
        if not message:
            continue
        sender = (source_row[4] or "").strip()
        row_id = f"ncsu_sms_phishing_{next_number:06d}"
        next_number += 1
        if row_id in seen_ids:
            continue
        note = (
            f"Imported from wspr-ncsu/sms-phishing all-positive phishing corpus. "
            f"messageID={source_row[0]}; objectID={source_row[1]}; sender={sender or 'unknown'}; "
            f"timestamp={source_row[5]}; error_in_time={source_row[6]}."
        )
        rows.append(
            base_candidate_row(
                row_id=row_id,
                message_raw=message,
                label="smishing",
                original_label="phishing_messages_row",
                label_mapping_notes="Rows from phishing_messages.csv are treated as smishing/phishing SMS by dataset membership; English filtering still needed during review.",
                source_name="SMS Phishing Dataset",
                source_url=SOURCE_URL,
                source_type="GitHub_dataset",
                dataset_name="wspr-ncsu/sms-phishing",
                original_file_format="CSV",
                scam_category="other",
                country_or_region="",
                language="unknown",
                reviewer_notes=note,
            )
        )
        seen_ids.add(row_id)

    imported = append_rows(rows)
    print(f"Imported {imported} NCSU phishing candidate rows.")


if __name__ == "__main__":
    main()
