"""Organize public thesis SMS sources into uniform CSV catalogs."""

from __future__ import annotations

import csv
import re
import shutil
import zipfile
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINAL_DIR = ROOT / "data" / "final"
SOURCE_ARCHIVE_DIR = ROOT / "data" / "source_archives" / "public_baseline"
EXPORT_ARCHIVE_DIR = ROOT / "data" / "exports" / "archive"
ORGANIZED_DIR = ROOT / "data" / "organized"
REPORT_PATH = ROOT / "reports" / "public_sources_organization.md"

CANONICAL_FINAL = "approved_smishing_messages.csv"
SOURCE_FILES = {
    "uci_csv": "SMSSpamCollection 1.csv",
    "uci_zip": "sms+spam+collection (1).zip",
    "mishra_zip": "Dataset_5971 (1).zip",
    "smishtank_csv": "analysisdataset.csv",
}
EXPORT_ARCHIVE_FILES = {
    "approved_smishing_messages_round3_7k_clean.csv",
    "approved_smishing_messages_unredacted_raw.csv",
}

BASE_FIELDNAMES = [
    "unified_id",
    "source_name",
    "dataset_name",
    "source_group",
    "source_row_id",
    "message_text",
    "source_label",
    "normalized_label",
    "label_status",
    "review_status",
    "contains_url",
    "contains_email",
    "contains_phone",
    "source_file",
    "notes",
]
DUPLICATE_FIELDNAMES = [
    "normalized_text_key",
    "duplicate_cluster_id",
    "duplicate_cluster_size",
    "is_dedup_representative",
    "duplicate_cluster_sources",
    "duplicate_cluster_labels",
]
FIELDNAMES = BASE_FIELDNAMES + DUPLICATE_FIELDNAMES
ALLOWED_LABELS = {"ham", "spam", "smishing"}
ALLOWED_LABEL_STATUSES = {"accepted", "needs_smishing_relabel", "conflict_needs_review"}

URL_RE = re.compile(r"\b(?:https?://|www\.)\S+|\b[a-zA-Z0-9.-]+\.(?:com|net|org|info|us|co|uk|ph|io|biz|xyz)\S*")
EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)")
LONG_NUMBER_RE = re.compile(r"\b\+?\d[\d\s().-]{6,}\d\b|\b\d{3,}\b")
NON_ALNUM_RE = re.compile(r"[^a-z0-9<>]+")
WHITESPACE_RE = re.compile(r"\s+")


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def find_file(filename: str) -> Path:
    candidates = [
        FINAL_DIR / filename,
        SOURCE_ARCHIVE_DIR / filename,
        EXPORT_ARCHIVE_DIR / filename,
    ]
    for path in candidates:
        if path.exists():
            return path
    raise SystemExit(f"Required file not found: {filename}")


def move_if_present(filename: str, target_dir: Path) -> None:
    source = FINAL_DIR / filename
    if not source.exists():
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / filename
    if target.exists():
        if target.stat().st_size == source.stat().st_size:
            source.unlink()
            return
        stem = target.stem
        suffix = target.suffix
        counter = 2
        while target.exists():
            target = target_dir / f"{stem}_{counter}{suffix}"
            counter += 1
    shutil.move(str(source), str(target))


def organize_final_folder() -> None:
    for filename in EXPORT_ARCHIVE_FILES:
        move_if_present(filename, EXPORT_ARCHIVE_DIR)
    for filename in SOURCE_FILES.values():
        move_if_present(filename, SOURCE_ARCHIVE_DIR)


def normalize_text_key(text: str) -> str:
    text = (text or "").lower().strip()
    text = URL_RE.sub("<url>", text)
    text = LONG_NUMBER_RE.sub("<num>", text)
    text = NON_ALNUM_RE.sub(" ", text)
    text = WHITESPACE_RE.sub(" ", text).strip()
    return text


def signal_flags(text: str) -> tuple[str, str, str]:
    return (
        bool_text(bool(URL_RE.search(text or ""))),
        bool_text(bool(EMAIL_RE.search(text or ""))),
        bool_text(bool(PHONE_RE.search(text or ""))),
    )


def make_row(
    *,
    unified_id: str,
    source_name: str,
    dataset_name: str,
    source_group: str,
    source_row_id: str,
    message_text: str,
    source_label: str,
    normalized_label: str,
    label_status: str,
    review_status: str,
    source_file: str,
    notes: str,
) -> dict[str, str]:
    contains_url, contains_email, contains_phone = signal_flags(message_text)
    return {
        "unified_id": unified_id,
        "source_name": source_name,
        "dataset_name": dataset_name,
        "source_group": source_group,
        "source_row_id": source_row_id,
        "message_text": message_text,
        "source_label": source_label,
        "normalized_label": normalized_label,
        "label_status": label_status,
        "review_status": review_status,
        "contains_url": contains_url,
        "contains_email": contains_email,
        "contains_phone": contains_phone,
        "source_file": source_file,
        "notes": notes,
        "normalized_text_key": "",
        "duplicate_cluster_id": "",
        "duplicate_cluster_size": "1",
        "is_dedup_representative": "true",
        "duplicate_cluster_sources": source_name,
        "duplicate_cluster_labels": normalized_label,
    }


def load_uci() -> list[dict[str, str]]:
    path = find_file(SOURCE_FILES["uci_csv"])
    rows: list[dict[str, str]] = []
    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        for index, source_row in enumerate(reader, start=1):
            source_label = (source_row.get("Label") or "").strip()
            normalized_label = source_label.lower()
            label_status = "accepted" if normalized_label == "ham" else "needs_smishing_relabel"
            rows.append(
                make_row(
                    unified_id=f"uci_{index:06d}",
                    source_name="UCI SMS Spam Collection",
                    dataset_name="SMS Spam Collection v.1",
                    source_group="public_baseline",
                    source_row_id=str(index),
                    message_text=(source_row.get("Maintext") or "").strip(),
                    source_label=source_label,
                    normalized_label=normalized_label,
                    label_status=label_status,
                    review_status=label_status,
                    source_file=str(path.relative_to(ROOT)),
                    notes="UCI spam is preserved for later smishing relabel review.",
                )
            )
    return rows


def load_mishra() -> list[dict[str, str]]:
    path = find_file(SOURCE_FILES["mishra_zip"])
    rows: list[dict[str, str]] = []
    with zipfile.ZipFile(path) as archive:
        with archive.open("Dataset_5971.csv") as raw_handle:
            text_lines = (line.decode("utf-8", errors="replace") for line in raw_handle)
            reader = csv.DictReader(text_lines)
            for index, source_row in enumerate(reader, start=1):
                source_label = (source_row.get("LABEL") or "").strip()
                label_lower = source_label.lower()
                normalized_label = "smishing" if label_lower == "smishing" else label_lower
                label_status = "needs_smishing_relabel" if normalized_label == "spam" else "accepted"
                flags = (
                    f"URL={source_row.get('URL', '')}; "
                    f"EMAIL={source_row.get('EMAIL', '')}; "
                    f"PHONE={source_row.get('PHONE', '')}"
                )
                rows.append(
                    make_row(
                        unified_id=f"mishra_{index:06d}",
                        source_name="Mishra & Soni",
                        dataset_name="SMS Phishing Dataset for Machine Learning and Pattern Recognition",
                        source_group="public_baseline",
                        source_row_id=str(index),
                        message_text=(source_row.get("TEXT") or "").strip(),
                        source_label=source_label,
                        normalized_label=normalized_label,
                        label_status=label_status,
                        review_status=label_status,
                        source_file=f"{path.relative_to(ROOT)}::Dataset_5971.csv",
                        notes=f"{flags}. Mishra spam is preserved for later smishing relabel review.",
                    )
                )
    return rows


def load_smishtank() -> list[dict[str, str]]:
    path = find_file(SOURCE_FILES["smishtank_csv"])
    rows: list[dict[str, str]] = []
    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        for index, source_row in enumerate(reader, start=1):
            source_row_id = (source_row.get("messageid") or str(index)).strip()
            notes = (
                f"category={source_row.get('Message Categories', '')}; "
                f"brand={source_row.get('Brand', '')}; "
                f"sender_type={source_row.get('SenderType', '')}; "
                f"url={source_row.get('Url', '')}; "
                f"domain={source_row.get('FullyQualifiedDomain', '')}"
            )
            rows.append(
                make_row(
                    unified_id=f"smishtank_{source_row_id}",
                    source_name="SmishTank",
                    dataset_name="SmishTank Dataset / Smishing Dataset I",
                    source_group="public_baseline",
                    source_row_id=source_row_id,
                    message_text=(source_row.get("MainText") or source_row.get("Fulltext") or "").strip(),
                    source_label="verified_smishing",
                    normalized_label="smishing",
                    label_status="accepted",
                    review_status="accepted",
                    source_file=str(path.relative_to(ROOT)),
                    notes=notes,
                )
            )
    return rows


def load_gathered() -> list[dict[str, str]]:
    path = find_file(CANONICAL_FINAL)
    rows: list[dict[str, str]] = []
    with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as handle:
        reader = csv.DictReader(handle)
        for index, source_row in enumerate(reader, start=1):
            source_name = (source_row.get("source_name") or "Gathered approved smishing").strip()
            source_row_id = (source_row.get("id") or str(index)).strip()
            notes = (
                f"original_source={source_name}; "
                f"scam_category={source_row.get('scam_category', '')}; "
                "strict-clean approved gathered smishing row."
            )
            rows.append(
                make_row(
                    unified_id=f"gathered_{source_row_id}",
                    source_name=source_name,
                    dataset_name="Gathered approved smishing 7k",
                    source_group="gathered_approved_smishing",
                    source_row_id=source_row_id,
                    message_text=(source_row.get("message_clean") or source_row.get("message_raw") or "").strip(),
                    source_label=(source_row.get("original_label") or "approved_smishing").strip(),
                    normalized_label="smishing",
                    label_status="accepted",
                    review_status="approved",
                    source_file=str(path.relative_to(ROOT)),
                    notes=notes,
                )
            )
    return rows


def representative_sort_key(row: dict[str, str]) -> tuple[int, int, str]:
    source_name = row["source_name"]
    label = row["normalized_label"]
    if label == "ham":
        source_priority = {"UCI SMS Spam Collection": 0, "Mishra & Soni": 1}.get(source_name, 5)
        label_priority = 0
    elif label == "smishing":
        source_priority = {"Smishing-Dataset-IMC25": 0, "SmishX": 1, "SmishTank": 2, "Mishra & Soni": 3}.get(source_name, 5)
        label_priority = 1
    elif label == "spam":
        source_priority = {"UCI SMS Spam Collection": 0, "Mishra & Soni": 1}.get(source_name, 5)
        label_priority = 2
    else:
        source_priority = 9
        label_priority = 9
    return (label_priority, source_priority, row["unified_id"])


def add_duplicate_metadata(rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]], Counter[str], Counter[str]]:
    clusters: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        key = normalize_text_key(row["message_text"])
        row["normalized_text_key"] = key
        clusters[key].append(row)

    duplicate_rows: list[dict[str, str]] = []
    representatives: list[dict[str, str]] = []
    source_cluster_counts: Counter[str] = Counter()
    label_cluster_counts: Counter[str] = Counter()
    cluster_number = 1

    for key, cluster_rows in sorted(clusters.items()):
        labels = sorted({row["normalized_label"] for row in cluster_rows})
        sources = sorted({row["source_name"] for row in cluster_rows})
        has_conflict = len(labels) > 1
        representative = sorted(cluster_rows, key=representative_sort_key)[0]
        cluster_id = f"dup_{cluster_number:06d}" if len(cluster_rows) > 1 else ""
        if len(cluster_rows) > 1:
            cluster_number += 1
            source_cluster_counts[" + ".join(sources)] += 1
            label_cluster_counts[" + ".join(labels)] += 1

        for row in cluster_rows:
            row["duplicate_cluster_id"] = cluster_id
            row["duplicate_cluster_size"] = str(len(cluster_rows))
            row["is_dedup_representative"] = "true" if row is representative else "false"
            row["duplicate_cluster_sources"] = " + ".join(sources)
            row["duplicate_cluster_labels"] = " + ".join(labels)
            if has_conflict:
                row["label_status"] = "conflict_needs_review"
                row["review_status"] = "conflict_needs_review"
            if len(cluster_rows) > 1:
                duplicate_rows.append(row)
        representatives.append(representative)

    return duplicate_rows, representatives, source_cluster_counts, label_cluster_counts


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_manifest(source_rows: dict[str, list[dict[str, str]]]) -> None:
    path = ORGANIZED_DIR / "source_manifest.csv"
    fieldnames = ["source_name", "row_file_status", "row_count", "ham", "spam", "smishing", "notes"]
    manifest_rows: list[dict[str, str]] = []
    for source_name, rows in source_rows.items():
        counts = Counter(row["normalized_label"] for row in rows)
        manifest_rows.append(
            {
                "source_name": source_name,
                "row_file_status": "available",
                "row_count": str(len(rows)),
                "ham": str(counts.get("ham", 0)),
                "spam": str(counts.get("spam", 0)),
                "smishing": str(counts.get("smishing", 0)),
                "notes": "Uniform row-level source file generated.",
            }
        )
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(manifest_rows)


def write_report(
    *,
    source_rows: dict[str, list[dict[str, str]]],
    combined_rows: list[dict[str, str]],
    duplicate_rows: list[dict[str, str]],
    representatives: list[dict[str, str]],
    source_cluster_counts: Counter[str],
    label_cluster_counts: Counter[str],
) -> None:
    label_counts = Counter(row["normalized_label"] for row in combined_rows)
    source_counts = {source: Counter(row["normalized_label"] for row in rows) for source, rows in source_rows.items()}
    duplicate_cluster_count = len({row["duplicate_cluster_id"] for row in duplicate_rows if row["duplicate_cluster_id"]})
    duplicate_extra_rows = len(combined_rows) - len(representatives)
    conflict_cluster_count = sum(count for key, count in label_cluster_counts.items() if " + " in key)

    lines = [
        "# Public Sources Organization",
        "",
        "## Summary",
        "",
        f"- Combined row-level total: {len(combined_rows):,}",
        f"- Ham: {label_counts.get('ham', 0):,}",
        f"- Spam / relabel review: {label_counts.get('spam', 0):,}",
        f"- Smishing: {label_counts.get('smishing', 0):,}",
        f"- Deduped representative rows: {len(representatives):,}",
        f"- Duplicate clusters: {duplicate_cluster_count:,}",
        f"- Extra duplicate rows: {duplicate_extra_rows:,}",
        f"- Label-conflict duplicate clusters: {conflict_cluster_count:,}",
        "",
        "## Source Counts",
        "",
        "| Source | Total | Ham | Spam | Smishing |",
        "|---|---:|---:|---:|---:|",
    ]
    for source, rows in source_rows.items():
        counts = source_counts[source]
        lines.append(
            f"| {source} | {len(rows):,} | {counts.get('ham', 0):,} | {counts.get('spam', 0):,} | {counts.get('smishing', 0):,} |"
        )

    lines.extend(
        [
            "",
            "## Duplicate Clusters By Source",
            "",
            "| Sources | Clusters |",
            "|---|---:|",
        ]
    )
    for key, count in source_cluster_counts.most_common(20):
        lines.append(f"| {key} | {count:,} |")

    lines.extend(
        [
            "",
            "## Duplicate Clusters By Label",
            "",
            "| Labels | Clusters |",
            "|---|---:|",
        ]
    )
    for key, count in label_cluster_counts.most_common(20):
        lines.append(f"| {key} | {count:,} |")

    lines.extend(
        [
            "",
            "## Files",
            "",
            "- `data/final/approved_smishing_messages.csv` is the only retained file in `data/final`.",
            "- Uniform source CSVs are in `data/organized/`.",
            "- Raw public baseline files were moved to `data/source_archives/public_baseline/`.",
            "- Duplicate round exports were moved to `data/exports/archive/`.",
            "",
            "## Notes",
            "",
            "- This is an organized source catalog, not the final model-ready training split.",
            "- Spam rows are preserved for later smishing relabel review.",
            "- Label-conflict duplicate clusters are marked `conflict_needs_review` and are not forced into a final training label.",
        ]
    )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    organize_final_folder()

    source_rows = {
        "UCI SMS Spam Collection": load_uci(),
        "Mishra & Soni": load_mishra(),
        "SmishTank": load_smishtank(),
        "Gathered approved smishing 7k": load_gathered(),
    }
    combined_rows = [
        row
        for rows in source_rows.values()
        for row in rows
    ]
    duplicate_rows, representatives, source_cluster_counts, label_cluster_counts = add_duplicate_metadata(combined_rows)

    write_csv(ORGANIZED_DIR / "uci_sms_spam_collection_uniform.csv", source_rows["UCI SMS Spam Collection"])
    write_csv(ORGANIZED_DIR / "mishra_soni_sms_dataset_uniform.csv", source_rows["Mishra & Soni"])
    write_csv(ORGANIZED_DIR / "smishtank_uniform.csv", source_rows["SmishTank"])
    write_csv(ORGANIZED_DIR / "gathered_approved_smishing_7k_uniform.csv", source_rows["Gathered approved smishing 7k"])
    write_csv(ORGANIZED_DIR / "combined_public_thesis_sources_uniform.csv", combined_rows)
    write_csv(ORGANIZED_DIR / "duplicate_overlap_clusters.csv", duplicate_rows)
    write_csv(ORGANIZED_DIR / "combined_public_thesis_sources_deduped_representatives.csv", representatives)
    write_manifest(source_rows)
    write_report(
        source_rows=source_rows,
        combined_rows=combined_rows,
        duplicate_rows=duplicate_rows,
        representatives=representatives,
        source_cluster_counts=source_cluster_counts,
        label_cluster_counts=label_cluster_counts,
    )

    print(f"Wrote organized files to {ORGANIZED_DIR}")
    print(f"Combined rows: {len(combined_rows)}")
    print(f"Deduped representative rows: {len(representatives)}")
    print(f"Duplicate clusters: {len({row['duplicate_cluster_id'] for row in duplicate_rows if row['duplicate_cluster_id']})}")
    print(f"Duplicate extra rows: {len(combined_rows) - len(representatives)}")


if __name__ == "__main__":
    main()
