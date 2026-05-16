"""Rebuild V3 with manual ham and research-backed synthetic ham."""

from __future__ import annotations

from collections import Counter

import pandas as pd
from pandas.errors import EmptyDataError

from final_dataset_build_utils import (
    FINAL_DIR,
    INTERIM_DIR,
    MANUAL_CLEANED,
    PUBLIC_DATASET,
    REPORTS_DIR,
    ensure_dirs,
    final_project,
    normalize_for_overlap,
    public_to_unified,
    read_csv,
    write_csv,
)


MANUAL_OPTIONS = [
    INTERIM_DIR / "manual_ham_no_overlap.csv",
    INTERIM_DIR / "manual_ham_standardized.csv",
    MANUAL_CLEANED,
]
SYNTH_IN = INTERIM_DIR / "synthetic_service_ham_research_backed_approved.csv"
SYNTH_GENERATED = INTERIM_DIR / "synthetic_service_ham_research_backed_generated.csv"
SYNTH_CAPPED = INTERIM_DIR / "synthetic_service_ham_family_capped.csv"
SYNTH_FAMILY_EXCLUDED = INTERIM_DIR.parent / "archives" / "synthetic_ham_family_excluded_archive.csv"
SYNTH_REJECTED = INTERIM_DIR.parent / "archives" / "synthetic_service_ham_research_backed_rejected_archive.csv"
OUT_CSV = FINAL_DIR / "dataset_v3_public_manual_research_synthetic_ham_balanced.csv"
REPORT_OUT = REPORTS_DIR / "research_backed_v3_build_report.md"


def read_manual() -> tuple[pd.DataFrame, str]:
    for path in MANUAL_OPTIONS:
        if path.exists():
            return read_csv(path), str(path)
    raise FileNotFoundError("No manual ham input found.")


def append_without_dupes(selected: list[pd.DataFrame], candidates: pd.DataFrame, limit: int, allow_internal_dupes: bool = False) -> pd.DataFrame:
    current = pd.concat(selected, ignore_index=True) if selected else pd.DataFrame()
    used = set()
    if not current.empty:
        used.update(current["message_raw"].map(normalize_for_overlap))
        used.update(current["message_clean"].map(normalize_for_overlap))
    take = []
    for _, row in candidates.iterrows():
        if len(take) >= limit:
            break
        raw_key = normalize_for_overlap(row.get("message_raw", ""))
        clean_key = normalize_for_overlap(row.get("message_clean", ""))
        if allow_internal_dupes or (raw_key not in used and clean_key not in used):
            take.append(row.to_dict())
            used.add(raw_key)
            used.add(clean_key)
    return pd.DataFrame(take)


def breakdown(df: pd.DataFrame) -> dict[str, int]:
    ham = df[df["normalized_label"].eq("ham")]
    return {
        "manual_real_ham": int(ham["data_origin"].eq("manual_real").sum()),
        "research_synthetic_ham": int(ham["data_origin"].eq("synthetic_template").sum()),
        "mishra_ham": int(ham["source_name"].eq("Mishra & Soni").sum()),
        "uci_ham": int(ham["source_name"].eq("UCI SMS Spam Collection").sum()),
    }


def table(counter: Counter, name: str) -> list[str]:
    lines = [f"| {name} | Count |", "| --- | ---: |"]
    lines.extend(f"| {key or 'blank'} | {value} |" for key, value in sorted(counter.items()))
    return lines


def safe_read(path) -> pd.DataFrame:
    try:
        if path.exists() and path.stat().st_size:
            return read_csv(path)
    except EmptyDataError:
        return pd.DataFrame()
    return pd.DataFrame()


def main() -> None:
    ensure_dirs()
    public = public_to_unified(read_csv(PUBLIC_DATASET))
    manual, manual_path = read_manual()
    synth = read_csv(SYNTH_IN)
    synth_generated = safe_read(SYNTH_GENERATED)
    synth_capped = safe_read(SYNTH_CAPPED)
    synth_family_excluded = safe_read(SYNTH_FAMILY_EXCLUDED)
    synth_rejected = safe_read(SYNTH_REJECTED)
    public_ham = public[public["normalized_label"].eq("ham")].copy()
    public_smish = public[public["normalized_label"].eq("smishing")].copy()
    mishra = public_ham[public_ham["source_name"].eq("Mishra & Soni")].copy()
    uci = public_ham[public_ham["source_name"].eq("UCI SMS Spam Collection")].sample(frac=1, random_state=42).copy()

    target_ham = 5272
    selected: list[pd.DataFrame] = []
    selected.append(append_without_dupes(selected, manual, len(manual), allow_internal_dupes=True))
    selected.append(append_without_dupes(selected, mishra, len(mishra)))
    synth_take = min(1300, len(synth), target_ham - sum(len(x) for x in selected))
    selected.append(append_without_dupes(selected, synth, synth_take))
    remaining = target_ham - sum(len(x) for x in selected)
    selected.append(append_without_dupes(selected, uci, remaining))
    v3_ham = pd.concat(selected, ignore_index=True)
    if len(v3_ham) < target_ham:
        other_ham = public_ham[~public_ham["unified_id"].isin(v3_ham["unified_id"])].sample(frac=1, random_state=43)
        v3_ham = pd.concat([v3_ham, append_without_dupes([v3_ham], other_ham, target_ham - len(v3_ham))], ignore_index=True)
    if len(v3_ham) != target_ham:
        raise RuntimeError(f"Could not build target ham count: {len(v3_ham)}")

    v3 = pd.concat([v3_ham, public_smish], ignore_index=True)
    final = final_project(v3, "v3_public_manual_research_synthetic")
    write_csv(final, OUT_CSV)

    bd = breakdown(final)
    counts = Counter(final["normalized_label"])
    uci_pct = bd["uci_ham"] / counts["ham"] * 100
    shortage = max(0, 1300 - bd["research_synthetic_ham"])
    reject_reasons = Counter(synth_rejected["rejection_reason"]) if not synth_rejected.empty and "rejection_reason" in synth_rejected else Counter()
    family_excluded_reasons = Counter(synth_family_excluded["family_cap_exclusion_reason"]) if not synth_family_excluded.empty and "family_cap_exclusion_reason" in synth_family_excluded else Counter()
    accepted_examples = synth["message_raw"].head(8).tolist() if not synth.empty else []
    rejected_examples = synth_rejected[["message_raw", "rejection_reason"]].head(5).to_dict("records") if not synth_rejected.empty and "rejection_reason" in synth_rejected else []
    lines = [
        "# Research-Backed V3 Build Report",
        "",
        "## Purpose",
        "",
        "Research-backed legitimate service templates were added to improve synthetic ham diversity and reduce UCI dominance.",
        "",
        "## Research Basis",
        "",
        "- Microsoft, Google, Apple, Amazon, PayPal",
        "- BDO, BPI",
        "- GCash, Maya",
        "- Globe, Smart",
        "- UPS, USPS, DHL",
        "- VA, NHS/GOV.UK, USCIS",
        "",
        "## Template Generation Rules",
        "",
        "- Fixed-format OTPs were kept stable and family-capped.",
        "- Bank/card alerts use neutral transaction wording.",
        "- Telecom and delivery messages provide non-scam service-message diversity.",
        "- Customs/payment-like messages are sparse because they resemble smishing.",
        "- No scam-like urgency, gambling/free-spin promos, or synthetic smishing were generated.",
        "",
        "## Synthetic Generation Summary",
        "",
        f"- Generated synthetic candidates: {len(synth_generated)}",
        f"- Synthetic after family caps: {len(synth_capped)}",
        f"- Family-cap excluded rows: {len(synth_family_excluded)}",
        f"- Approved synthetic available: {len(synth)}",
        f"- Rejected synthetic rows: {len(synth_rejected)}",
        f"- Approved synthetic used in V3: {bd['research_synthetic_ham']}",
        f"- Synthetic shortage versus 1,300 target: {shortage}",
        "",
        "### Family Cap Results",
        "",
        *table(family_excluded_reasons, "Family cap exclusion reason"),
        "",
        "### Rejected Reasons",
        "",
        *table(reject_reasons, "Rejected reason"),
        "",
        "### Approved Synthetic By Category",
        "",
        *table(Counter(synth["service_category"]), "Category"),
        "",
        "### Accepted Synthetic Examples",
        "",
        *[f"- {msg}" for msg in accepted_examples],
        "",
        "### Rejected Examples",
        "",
        *([f"- {row.get('rejection_reason', '')}: {row.get('message_raw', '')}" for row in rejected_examples] if rejected_examples else ["- None"]),
        "",
        "## Final V3 Composition",
        "",
        f"- Ham: {counts['ham']}",
        f"- Smishing: {counts['smishing']}",
        f"- Total: {len(final)}",
        f"- Manual real ham: {bd['manual_real_ham']}",
        f"- Synthetic research-backed ham: {bd['research_synthetic_ham']}",
        f"- Mishra ham: {bd['mishra_ham']}",
        f"- UCI ham: {bd['uci_ham']}",
        f"- UCI ham share: {uci_pct:.2f}%",
        "",
        "## Thesis Methodology Note",
        "",
        "To improve legitimate service-message diversity, synthetic ham messages were generated from manually curated service-message templates and research-backed legitimate SMS style rules derived from official or trustworthy sources. Synthetic rows contain fake generated values in the raw text field and a privacy-safe cleaned version. All synthetic rows are explicitly marked as synthetic. The smishing class remains entirely real/public-source based; no synthetic smishing messages were generated.",
        "",
        "## Limitations",
        "",
        "- Synthetic ham is not collected real-world SMS.",
        "- V1 real-only dataset should remain available as a baseline.",
        "- Research-backed templates are style-inspired, not copied official message rows.",
        "- Link-bearing official-style messages are sparse because they resemble smishing.",
        "",
        "## Files",
        "",
        f"- Public source: `{PUBLIC_DATASET}`",
        f"- Manual source: `{manual_path}`",
        f"- Synthetic source: `{SYNTH_IN}`",
        f"- Final dataset: `{OUT_CSV}`",
    ]
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Final V3 output path: {OUT_CSV}")
    print(f"Final V3 composition: ham={counts['ham']}, smishing={counts['smishing']}, total={len(final)}")
    print(f"Manual real ham count: {bd['manual_real_ham']}")
    print(f"Research-backed synthetic ham count: {bd['research_synthetic_ham']}")
    print(f"Mishra ham count: {bd['mishra_ham']}")
    print(f"UCI ham count: {bd['uci_ham']}")
    print(f"UCI ham percentage: {uci_pct:.2f}%")
    print(f"Smishing count: {counts['smishing']}")
    print(f"Report: {REPORT_OUT}")


if __name__ == "__main__":
    main()
