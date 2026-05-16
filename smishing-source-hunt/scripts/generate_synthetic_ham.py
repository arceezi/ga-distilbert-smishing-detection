"""Generate synthetic ham candidates from approved legitimate ham templates."""

from __future__ import annotations

import argparse
import csv
import random
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_CSV = ROOT / "data" / "manual_ham_drive" / "templates" / "ham_template_patterns.csv"
OUT_CSV = ROOT / "data" / "manual_ham_drive" / "templates" / "generated_synthetic_ham.csv"
SUMMARY_MD = ROOT / "reports" / "synthetic_ham_generation_summary.md"

TARGET_DISTRIBUTION = {
    "otp_verification": 200,
    "banking": 180,
    "ewallet": 150,
    "delivery": 150,
    "telecom": 120,
    "government": 80,
    "account_security": 60,
    "payment_confirmation": 40,
    "appointment_reminder": 20,
}

FIELDNAMES = [
    "synthetic_id",
    "message_text",
    "normalized_label",
    "source_name",
    "source_group",
    "generation_method",
    "template_id",
    "service_category",
    "institution_type",
    "contains_url",
    "contains_email",
    "contains_phone",
    "contains_otp",
    "contains_amount",
    "review_status",
    "label_status",
    "notes",
]

SLOT_VALUES = {
    "BRAND": ["<BRAND>", "Your bank", "Your e-wallet", "Your courier", "Your telecom provider"],
    "OTP": ["<OTP>"],
    "AMOUNT": ["<AMOUNT>", "PHP <AMOUNT>"],
    "REF_NUM": ["<REF_NUM>"],
    "DATE_TIME": ["today", "tomorrow", "on <DATE_TIME>", "at <DATE_TIME>"],
    "PHONE": ["<PHONE>"],
    "EMAIL": ["<EMAIL>"],
    "URL": ["<URL>"],
    "NAME": ["<NAME>"],
    "LOCATION": ["<LOCATION>"],
}

def read_templates(path: Path) -> list[dict[str, str]]:
    if path.exists():
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            rows = [row for row in csv.DictReader(fh) if row.get("template_status", "active") == "active"]
        if rows:
            return rows
    return []


def slot_sample(template: str, rng: random.Random) -> str:
    text = template
    for slot, values in SLOT_VALUES.items():
        text = text.replace(f"<{slot}>", rng.choice(values))
    return re.sub(r"\s+", " ", text).strip()


def contains(pattern: str, text: str) -> str:
    return str(bool(re.search(pattern, text, re.I)))


def allocate_counts(templates: list[dict[str, str]], target_count: int, max_per_template: int) -> tuple[dict[str, int], list[str]]:
    available = Counter(row.get("service_category", "unsure") or "unsure" for row in templates)
    warnings = []
    desired = TARGET_DISTRIBUTION.copy()
    total_default = sum(desired.values())
    if target_count != total_default:
        desired = {key: round(value * target_count / total_default) for key, value in desired.items()}
    while sum(desired.values()) < target_count:
        desired[max(desired, key=desired.get)] += 1
    while sum(desired.values()) > target_count:
        desired[max(desired, key=desired.get)] -= 1

    allocated = {}
    overflow = 0
    for category, desired_count in desired.items():
        capacity = available.get(category, 0) * max_per_template
        if capacity == 0:
            overflow += desired_count
            warnings.append(f"No templates for {category}; redistributed {desired_count} rows.")
        else:
            allocated[category] = min(desired_count, capacity)
            overflow += max(0, desired_count - capacity)
            if desired_count > capacity:
                warnings.append(f"{category} capacity limited to {capacity}; redistributed {desired_count - capacity} rows.")

    categories_by_capacity = [
        category for category, count in available.items() if count * max_per_template > allocated.get(category, 0)
    ]
    index = 0
    while overflow > 0 and categories_by_capacity:
        category = categories_by_capacity[index % len(categories_by_capacity)]
        capacity = available[category] * max_per_template
        if allocated.get(category, 0) < capacity:
            allocated[category] = allocated.get(category, 0) + 1
            overflow -= 1
        index += 1
        if index > target_count * max(1, len(categories_by_capacity)):
            break
    if overflow:
        warnings.append(f"Could not allocate {overflow} rows because max-per-template capacity was reached.")
    return allocated, warnings


def generate(templates: list[dict[str, str]], target_count: int, max_per_template: int, seed: int) -> tuple[list[dict[str, str]], list[str]]:
    rng = random.Random(seed)
    if not templates:
        return [], ["No active templates found. Run review validation and template extraction first."]
    by_category: dict[str, list[dict[str, str]]] = defaultdict(list)
    for template in templates:
        by_category[template.get("service_category", "unsure") or "unsure"].append(template)
    allocated, warnings = allocate_counts(templates, target_count, max_per_template)
    per_template = Counter()
    rows = []
    for category, count in allocated.items():
        choices = list(by_category[category])
        attempts = 0
        while count > 0 and choices:
            template = rng.choice(choices)
            if per_template[template["template_id"]] >= max_per_template:
                choices = [item for item in choices if per_template[item["template_id"]] < max_per_template]
                continue
            message = slot_sample(template["template_text"], rng)
            if re.search(r"\b(verify now|account will be locked|provide your otp|send your password)\b", message, re.I):
                attempts += 1
                if attempts > 100:
                    warnings.append(f"Skipped repeated unsafe-looking generations for {category}.")
                    break
                continue
            per_template[template["template_id"]] += 1
            rows.append(
                {
                    "synthetic_id": f"synthetic_ham_{len(rows) + 1:06d}",
                    "message_text": message,
                    "normalized_label": "ham",
                    "source_name": "manual_ham_template_generation",
                    "source_group": "synthetic_ham_template",
                    "generation_method": "template_slot_sampling",
                    "template_id": template["template_id"],
                    "service_category": category,
                    "institution_type": template.get("institution_type", ""),
                    "contains_url": contains(r"<URL>|https?://|www\.", message),
                    "contains_email": contains(r"<EMAIL>|@", message),
                    "contains_phone": contains(r"<PHONE>|(\+?63|0)\s?9\d{2}", message),
                    "contains_otp": contains(r"<OTP>|\botp\b|\bcode\b", message),
                    "contains_amount": contains(r"<AMOUNT>|\bPHP\b|₱", message),
                    "review_status": "generated_needs_review",
                    "label_status": "synthetic_candidate",
                    "notes": "Synthetic candidate; review before training use.",
                }
            )
            count -= 1
    return rows, warnings


def write_summary(rows: list[dict[str, str]], templates: list[dict[str, str]], target_count: int, warnings: list[str]) -> None:
    category_counts = Counter(row["service_category"] for row in rows)
    template_counts = Counter(row["template_id"] for row in rows)
    avg = (sum(template_counts.values()) / len(template_counts)) if template_counts else 0
    lines = [
        "# Synthetic Ham Generation Summary",
        "",
        "Generated by `scripts/generate_synthetic_ham.py`.",
        "",
        f"- Target synthetic count: {target_count}",
        f"- Generated synthetic count: {len(rows)}",
        f"- Number of templates used: {len(template_counts)}",
        f"- Average generations per template: {avg:.2f}",
        "",
        "## Count by Service Category",
        "",
        "| Service category | Count |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {category} | {count} |" for category, count in category_counts.most_common())
    lines.extend(["", "## Warnings", ""])
    lines.extend(f"- {warning}" for warning in warnings) if warnings else lines.append("- None.")
    lines.extend(
        [
            "",
            "## Reminder",
            "",
            "Synthetic ham should be reviewed, tracked, and reported separately from real manual ham and public-source ham.",
        ]
    )
    SUMMARY_MD.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--templates", type=Path, default=TEMPLATES_CSV)
    parser.add_argument("--output", type=Path, default=OUT_CSV)
    parser.add_argument("--target-count", type=int, default=1000)
    parser.add_argument("--max-per-template", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    templates = read_templates(args.templates)
    rows, warnings = generate(templates, args.target_count, args.max_per_template, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    write_summary(rows, templates, args.target_count, warnings)
    print(f"Generated {len(rows)} synthetic ham candidates into {args.output}")
    print(f"Summary: {SUMMARY_MD}")


if __name__ == "__main__":
    main()
