"""Build final balanced dataset versions with public, manual, and synthetic ham."""

from __future__ import annotations

from collections import Counter

import pandas as pd
from pandas.errors import EmptyDataError

from final_dataset_build_utils import (
    FINAL_DIR,
    INTERIM_DIR,
    PUBLIC_DATASET,
    REPORTS_DIR,
    ensure_dirs,
    final_project,
    normalize_for_overlap,
    public_to_unified,
    read_csv,
    write_csv,
)


MANUAL_IN = INTERIM_DIR / "manual_ham_no_overlap.csv"
SYNTH_IN = INTERIM_DIR / "synthetic_service_ham_approved.csv"
V1_OUT = FINAL_DIR / "dataset_v1_public_real_only_balanced.csv"
V2_OUT = FINAL_DIR / "dataset_v2_public_plus_manual_ham_balanced.csv"
V3_OUT = FINAL_DIR / "dataset_v3_public_manual_synthetic_ham_balanced.csv"
RESERVED_SMISHING = FINAL_DIR / "reserved_extra_smishing.csv"
RESERVED_HAM = FINAL_DIR / "reserved_unused_ham.csv"
RESERVED_SYNTH = FINAL_DIR / "reserved_synthetic_ham_unused.csv"
REPORT_OUT = REPORTS_DIR / "final_dataset_build_report.md"
OVERLAP_ARCHIVE = FINAL_DIR.parent / "archives" / "manual_ham_overlap_archive.csv"
SYNTH_REJECTED = FINAL_DIR.parent / "archives" / "synthetic_service_ham_rejected_archive.csv"


def sample(df: pd.DataFrame, n: int, seed: int = 42) -> pd.DataFrame:
    if len(df) <= n:
        return df.copy()
    return df.sample(n=n, random_state=seed).copy()


def append_without_dupes(selected: list[pd.DataFrame], candidates: pd.DataFrame, limit: int, reserve_rows: list[pd.DataFrame], allow_internal_dupes: bool = False) -> pd.DataFrame:
    current = pd.concat(selected, ignore_index=True) if selected else pd.DataFrame()
    used = set()
    if not current.empty:
        used.update(current["message_raw"].map(normalize_for_overlap))
        used.update(current["message_clean"].map(normalize_for_overlap))
    take = []
    reserve = []
    for _, row in candidates.iterrows():
        raw_key = normalize_for_overlap(row.get("message_raw", ""))
        clean_key = normalize_for_overlap(row.get("message_clean", ""))
        if len(take) < limit and (allow_internal_dupes or (raw_key not in used and clean_key not in used)):
            take.append(row.to_dict())
            used.add(raw_key)
            used.add(clean_key)
        else:
            reserve.append(row.to_dict())
    if reserve:
        reserve_rows.append(pd.DataFrame(reserve))
    return pd.DataFrame(take)


def breakdown(df: pd.DataFrame) -> dict[str, int]:
    ham = df[df["normalized_label"].eq("ham")]
    return {
        "Manual Ham": int(ham["data_origin"].eq("manual_real").sum()),
        "Synthetic Ham": int(ham["data_origin"].eq("synthetic_template").sum()),
        "UCI Ham": int(ham["source_name"].eq("UCI SMS Spam Collection").sum()),
        "Mishra Ham": int(ham["source_name"].eq("Mishra & Soni").sum()),
    }


def md_count_table(counter: Counter, left: str) -> list[str]:
    lines = [f"| {left} | Count |", "| --- | ---: |"]
    if not counter:
        lines.append("| None | 0 |")
    else:
        lines.extend(f"| {key or 'blank'} | {value} |" for key, value in sorted(counter.items()))
    return lines


def safe_read(path) -> pd.DataFrame:
    try:
        if path.exists() and path.stat().st_size:
            return pd.read_csv(path, dtype=str, keep_default_na=False)
    except EmptyDataError:
        return pd.DataFrame()
    return pd.DataFrame()


def main() -> None:
    ensure_dirs()
    public = public_to_unified(read_csv(PUBLIC_DATASET))
    manual = read_csv(MANUAL_IN)
    synth = read_csv(SYNTH_IN)
    public_ham = public[public["normalized_label"].eq("ham")].copy()
    public_smish = public[public["normalized_label"].eq("smishing")].copy()
    uci_ham = public_ham[public_ham["source_name"].eq("UCI SMS Spam Collection")].copy()
    mishra_ham = public_ham[public_ham["source_name"].eq("Mishra & Soni")].copy()

    v1_ham = public_ham.copy()
    v1_smish = sample(public_smish, len(v1_ham))
    v1 = pd.concat([v1_ham, v1_smish], ignore_index=True)
    write_csv(final_project(v1, "v1_public_real_only"), V1_OUT)

    v2_target = min(len(public_ham) + len(manual), len(public_smish))
    v2_public_take = max(0, v2_target - len(manual))
    v2_ham = pd.concat([manual, sample(public_ham, v2_public_take)], ignore_index=True)
    v2_smish = sample(public_smish, v2_target)
    v2 = pd.concat([v2_ham, v2_smish], ignore_index=True)
    write_csv(final_project(v2, "v2_public_manual"), V2_OUT)

    target_ham = len(public_smish)
    selected: list[pd.DataFrame] = []
    reserves: list[pd.DataFrame] = []
    selected.append(append_without_dupes(selected, manual, len(manual), reserves, allow_internal_dupes=True))
    selected.append(append_without_dupes(selected, mishra_ham, len(mishra_ham), reserves))
    synth_take = min(1300, len(synth), target_ham - sum(len(x) for x in selected))
    selected.append(append_without_dupes(selected, synth, synth_take, reserves))
    remaining = target_ham - sum(len(x) for x in selected)
    selected.append(append_without_dupes(selected, uci_ham.sample(frac=1, random_state=42), remaining, reserves))
    v3_ham = pd.concat(selected, ignore_index=True)
    if len(v3_ham) < target_ham:
        other_ham = public_ham[~public_ham["unified_id"].isin(v3_ham["unified_id"])].sample(frac=1, random_state=43)
        v3_ham = pd.concat([v3_ham, append_without_dupes([v3_ham], other_ham, target_ham - len(v3_ham), reserves)], ignore_index=True)
    v3 = pd.concat([v3_ham, public_smish], ignore_index=True)
    write_csv(final_project(v3, "v3_public_manual_synthetic"), V3_OUT)

    reserved_smish = public_smish[~public_smish["unified_id"].isin(v1_smish["unified_id"])].copy()
    write_csv(reserved_smish, RESERVED_SMISHING)
    selected_ham_ids = set(v3_ham["unified_id"])
    reserved_ham = public_ham[~public_ham["unified_id"].isin(selected_ham_ids)].copy()
    write_csv(reserved_ham, RESERVED_HAM)
    reserved_synth = synth[~synth["unified_id"].isin(v3_ham["unified_id"])].copy()
    write_csv(reserved_synth, RESERVED_SYNTH)

    rows = []
    for name, df in [("V1", v1), ("V2", v2), ("V3", v3)]:
        counts = Counter(df["normalized_label"])
        bd = breakdown(df)
        rows.append(
            {
                "version": name,
                "ham": counts["ham"],
                "smishing": counts["smishing"],
                "total": len(df),
                **bd,
            }
        )
    v3_bd = breakdown(v3)
    v1_uci_share = breakdown(v1)["UCI Ham"] / Counter(v1["normalized_label"])["ham"] * 100
    v3_uci_share = v3_bd["UCI Ham"] / Counter(v3["normalized_label"])["ham"] * 100
    templates = pd.read_csv(INTERIM_DIR / "service_ham_template_patterns.csv", dtype=str, keep_default_na=False)
    synth_generated = pd.read_csv(INTERIM_DIR / "synthetic_service_ham_generated.csv", dtype=str, keep_default_na=False)
    synth_rejected = safe_read(SYNTH_REJECTED)
    overlap_archive = safe_read(OVERLAP_ARCHIVE)
    manual_category = Counter(manual["service_category"])
    template_category = Counter(templates["service_category"])
    synth_category = Counter(synth["service_category"])
    synth_reject_category = Counter(synth_rejected["rejection_reason"]) if not synth_rejected.empty and "rejection_reason" in synth_rejected else Counter()
    template_examples = templates.head(5).to_dict("records")
    lines = [
        "# Final Dataset Build Report",
        "",
        "## Purpose",
        "",
        "This build integrates manually curated service ham and synthetic service ham to address UCI-dominated ham in the public thesis dataset.",
        "",
        "## Source Inputs",
        "",
        f"- Public campaign-family-filtered dataset: `{PUBLIC_DATASET}`",
        f"- Approved cleaned manual ham standardized through: `{MANUAL_IN}`",
        f"- Generated synthetic service ham approved through: `{SYNTH_IN}`",
        "",
        "## Manual Ham Processing",
        "",
        f"- Manual input rows: {len(manual) + len(overlap_archive)}",
        f"- Overlap removed/archive rows: {len(overlap_archive)}",
        f"- Final manual ham included in V3: {len(manual)}",
        "",
        "### Manual Category Distribution",
        "",
        *md_count_table(manual_category, "Service category"),
        "",
        "## Template Extraction",
        "",
        f"- Templates extracted: {len(templates)}",
        f"- Templates rejected/skipped: {len(manual) - len(templates)} row-level inputs not converted to unique approved template candidates",
        "",
        "### Templates By Category",
        "",
        *md_count_table(template_category, "Service category"),
        "",
        "### Template Examples",
        "",
        "| Template ID | Category | Template |",
        "| --- | --- | --- |",
        *[f"| {row['template_id']} | {row['service_category']} | {str(row['template_text']).replace('|', '/')} |" for row in template_examples],
        "",
        "## Synthetic Ham Generation",
        "",
        "- Target synthetic count: 1,300",
        f"- Generated synthetic count: {len(synth_generated)}",
        f"- Approved synthetic count available: {len(synth)}",
        f"- Rejected synthetic count: {len(synth_rejected)}",
        f"- Approved synthetic count used in V3: {v3_bd['Synthetic Ham']}",
        "- Max per template: 20",
        "- Max per family: 50 command-line option retained for auditability; template-level cap controlled generation.",
        "",
        "### Approved Synthetic By Category",
        "",
        *md_count_table(synth_category, "Service category"),
        "",
        "### Synthetic Rejections",
        "",
        *md_count_table(synth_reject_category, "Reason"),
        "",
        "## Final Dataset Versions",
        "",
        "| Dataset Version | Ham | Smishing | Total | Manual Ham | Synthetic Ham | UCI Ham | Mishra Ham | Purpose |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in rows:
        purpose = {"V1": "Public real-only baseline", "V2": "Public plus manual real ham", "V3": "Expanded ham-diversity dataset"}[row["version"]]
        lines.append(f"| {row['version']} | {row['ham']} | {row['smishing']} | {row['total']} | {row['Manual Ham']} | {row['Synthetic Ham']} | {row['UCI Ham']} | {row['Mishra Ham']} | {purpose} |")
    lines.extend(
        [
            "",
            "## Ham Diversity Improvement",
            "",
            f"- V1 UCI ham share: {v1_uci_share:.2f}%",
            f"- V3 UCI ham share: {v3_uci_share:.2f}%",
            "",
            "## Thesis Methodology Note",
            "",
            "To reduce the dominance of casual UCI ham messages, the final expanded dataset incorporated manually curated legitimate service SMS messages and synthetic service-ham messages generated from approved manual templates. Synthetic messages were limited to legitimate non-malicious service notifications and were clearly marked as synthetic. The smishing class remained fully real/public-source based; no synthetic smishing messages were generated.",
            "",
            "Synthetic ham messages were generated from manually approved legitimate service-message templates. Unlike collected public data, these messages are synthetic and contain fake/generated values in the raw text field. A privacy-safe cleaned version was also generated for each synthetic message. Synthetic rows are clearly marked with is_synthetic=True and data_origin=synthetic_template.",
            "",
            "## Limitations",
            "",
            "- Synthetic ham is not real-world collected SMS and is marked separately.",
            "- V1 real-only dataset remains the baseline.",
            "- V3 should be treated as the expanded ham-diversity dataset.",
            "",
            "## Files Generated",
            "",
            f"- `{V1_OUT}`",
            f"- `{V2_OUT}`",
            f"- `{V3_OUT}`",
            f"- `{RESERVED_SMISHING}`",
            f"- `{RESERVED_HAM}`",
            f"- `{RESERVED_SYNTH}`",
        ]
    )
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Public dataset input count: {len(public)}")
    print(f"V1 dataset count and composition: ham={Counter(v1['normalized_label'])['ham']}, smishing={Counter(v1['normalized_label'])['smishing']}, total={len(v1)}")
    print(f"V2 dataset count and composition: ham={Counter(v2['normalized_label'])['ham']}, smishing={Counter(v2['normalized_label'])['smishing']}, total={len(v2)}")
    print(f"V3 dataset count and composition: ham={Counter(v3['normalized_label'])['ham']}, smishing={Counter(v3['normalized_label'])['smishing']}, total={len(v3)}")
    print(f"V3 ham source breakdown: {v3_bd}")
    print(f"V3 UCI ham percentage: {v3_uci_share:.2f}%")
    print(f"Final target dataset: {V3_OUT}")
    print(f"Report: {REPORT_OUT}")


if __name__ == "__main__":
    main()
