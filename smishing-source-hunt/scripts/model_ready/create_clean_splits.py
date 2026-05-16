"""Create leakage-safe stratified clean train/validation/test splits."""

from __future__ import annotations

import random
from collections import Counter, defaultdict

import pandas as pd

from model_ready_common import (
    FINAL_CLEAN_DATASET,
    LABEL_TO_ID,
    MANIFESTS_DIR,
    REPORTS_DIR,
    SPLIT_RATIOS,
    SPLIT_SEED,
    TEST_CLEAN,
    TRAIN_CLEAN,
    VAL_CLEAN,
    count_table,
    deterministic_row_seed,
    ensure_model_ready_dirs,
    label_counts,
    markdown_table,
    normalized_message_key,
    read_csv,
    relpath,
    stable_int,
    write_csv,
    write_text,
)


SPLITS = ["train", "val", "test"]


def _target_counts(df: pd.DataFrame) -> dict[str, dict[str, int]]:
    targets: dict[str, dict[str, int]] = {}
    for label, total in label_counts(df).items():
        train = round(total * SPLIT_RATIOS["train"])
        val = round(total * SPLIT_RATIOS["val"])
        test = total - train - val
        targets[label] = {"train": train, "val": val, "test": test}
    return targets


def _add_split_group_keys(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    parent = {idx: idx for idx in out.index}

    def find(idx: int) -> int:
        while parent[idx] != idx:
            parent[idx] = parent[parent[idx]]
            idx = parent[idx]
        return idx

    def union(left: int, right: int) -> None:
        root_left = find(left)
        root_right = find(right)
        if root_left != root_right:
            parent[root_right] = root_left

    for column in ["normalized_message_key", "normalized_raw_message_key"]:
        seen: dict[str, int] = {}
        for idx, key in out[column].items():
            key = str(key)
            if not key:
                continue
            if key in seen:
                union(int(idx), int(seen[key]))
            else:
                seen[key] = int(idx)

    components: dict[int, list[int]] = defaultdict(list)
    for idx in out.index:
        components[find(int(idx))].append(int(idx))

    group_keys: dict[int, str] = {}
    for members in components.values():
        component_keys = sorted(
            {
                str(value)
                for value in out.loc[members, ["normalized_message_key", "normalized_raw_message_key"]].to_numpy().ravel()
                if str(value).strip()
            }
        )
        split_group_key = f"split_group_{stable_int(*component_keys, SPLIT_SEED)}"
        for idx in members:
            group_keys[idx] = split_group_key
    out["split_group_key"] = pd.Series(group_keys)
    return out


def _build_groups(df: pd.DataFrame) -> list[dict[str, object]]:
    groups: list[dict[str, object]] = []
    for key, group in df.groupby("split_group_key", sort=False):
        labels = Counter(group["normalized_label"])
        groups.append(
            {
                "key": key,
                "indices": group.index.tolist(),
                "label_counts": labels,
                "size": len(group),
                "sort_key": stable_int(key, SPLIT_SEED),
            }
        )
    return groups


def _choose_split_for_group(group: dict[str, object], counts: dict[str, Counter], targets: dict[str, dict[str, int]]) -> str:
    label_counts_for_group: Counter = group["label_counts"]  # type: ignore[assignment]
    best_split = "train"
    best_score: tuple[float, int, int] | None = None
    for split in SPLITS:
        score = 0.0
        overage = 0
        total_after = 0
        for label in LABEL_TO_ID:
            target = targets.get(label, {}).get(split, 0)
            after = counts[split][label] + label_counts_for_group.get(label, 0)
            total_after += after
            diff = after - target
            if diff > 0:
                overage += diff
                score += diff * diff * 100
            else:
                score += abs(diff)
        candidate = (score, overage, total_after)
        if best_score is None or candidate < best_score:
            best_score = candidate
            best_split = split
    return best_split


def assign_splits(df: pd.DataFrame) -> pd.Series:
    targets = _target_counts(df)
    groups = _build_groups(df)
    assignments: dict[int, str] = {}
    counts: dict[str, Counter] = {split: Counter() for split in SPLITS}

    mixed_groups = [group for group in groups if len(group["label_counts"]) > 1]  # type: ignore[arg-type]
    single_groups = [group for group in groups if len(group["label_counts"]) == 1]  # type: ignore[arg-type]

    for group in sorted(mixed_groups, key=lambda item: (-int(item["size"]), int(item["sort_key"]))):
        split = _choose_split_for_group(group, counts, targets)
        for idx in group["indices"]:  # type: ignore[union-attr]
            assignments[int(idx)] = split
        for label, value in group["label_counts"].items():  # type: ignore[union-attr]
            counts[split][label] += value

    by_label: dict[str, list[dict[str, object]]] = defaultdict(list)
    for group in single_groups:
        label = next(iter(group["label_counts"]))  # type: ignore[arg-type]
        by_label[label].append(group)

    for label in sorted(by_label):
        groups_for_label = sorted(by_label[label], key=lambda item: (-int(item["size"]), int(item["sort_key"])))
        for group in groups_for_label:
            size = int(group["size"])
            deficits = {split: targets[label][split] - counts[split][label] for split in SPLITS}
            fitting = [split for split in SPLITS if deficits[split] >= size]
            if fitting:
                split = max(fitting, key=lambda item: (deficits[item], -SPLITS.index(item)))
            else:
                split = max(SPLITS, key=lambda item: (deficits[item], -SPLITS.index(item)))
            for idx in group["indices"]:  # type: ignore[union-attr]
                assignments[int(idx)] = split
            counts[split][label] += size

    return pd.Series([assignments[idx] for idx in df.index], index=df.index)


def create_splits() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ensure_model_ready_dirs()
    df = read_csv(FINAL_CLEAN_DATASET)
    df["normalized_message_key"] = df["message_clean"].map(normalized_message_key)
    df["normalized_raw_message_key"] = df["message_raw"].map(normalized_message_key)
    blank_keys = df["normalized_message_key"].str.strip().eq("")
    df.loc[blank_keys, "normalized_message_key"] = df.loc[blank_keys, "final_row_id"]
    blank_raw_keys = df["normalized_raw_message_key"].str.strip().eq("")
    df.loc[blank_raw_keys, "normalized_raw_message_key"] = df.loc[blank_raw_keys, "final_row_id"]
    df = _add_split_group_keys(df)
    df["split"] = assign_splits(df)
    df["original_clean_row"] = "True"
    df["augmentation_status"] = "original_clean"
    df["original_final_row_id"] = df["final_row_id"]
    df["perturbation_level"] = "0"
    df["perturbation_techniques"] = ""
    df["variant_index"] = "0"

    outputs = {
        "train": TRAIN_CLEAN,
        "val": VAL_CLEAN,
        "test": TEST_CLEAN,
    }
    split_dfs = {}
    rng = random.Random(SPLIT_SEED)
    for split, path in outputs.items():
        split_df = df[df["split"].eq(split)].copy()
        order = split_df["final_row_id"].map(lambda value: deterministic_row_seed(value, split, 0, SPLIT_SEED))
        split_df = split_df.assign(_order=order).sort_values("_order").drop(columns=["_order"]).reset_index(drop=True)
        if split == "train":
            split_df = split_df.sample(frac=1, random_state=rng.randint(1, 2**31 - 1)).reset_index(drop=True)
        write_csv(split_df, path)
        split_dfs[split] = split_df

    manifest = df[
        [
            "final_row_id",
            "split",
            "normalized_label",
            "data_origin",
            "is_synthetic",
            "source_name",
            "dataset_name",
            "normalized_message_key",
            "normalized_raw_message_key",
            "split_group_key",
        ]
    ].copy()
    write_csv(manifest.sort_values(["split", "normalized_label", "final_row_id"]), MANIFESTS_DIR / "split_membership_manifest.csv")
    write_report(df)
    return split_dfs["train"], split_dfs["val"], split_dfs["test"]


def write_report(df: pd.DataFrame) -> None:
    targets = _target_counts(df)
    rows = []
    for split in SPLITS:
        split_df = df[df["split"].eq(split)]
        counts = label_counts(split_df)
        rows.append(
            [
                split,
                len(split_df),
                counts.get("ham", 0),
                counts.get("smishing", 0),
                int((split_df["is_synthetic"].eq("True") & split_df["normalized_label"].eq("ham")).sum()),
            ]
        )
    key_splits = df.groupby("normalized_message_key")["split"].nunique()
    cross_split_duplicate_keys = int((key_splits > 1).sum())
    raw_key_splits = df.groupby("normalized_raw_message_key")["split"].nunique()
    cross_split_raw_duplicate_keys = int((raw_key_splits > 1).sum())
    duplicate_key_rows = int(df["normalized_message_key"][df["normalized_message_key"].ne("")].duplicated().sum())
    duplicate_raw_key_rows = int(df["normalized_raw_message_key"][df["normalized_raw_message_key"].ne("")].duplicated().sum())
    lines = [
        "# Clean Split Report",
        "",
        f"- Input path: `{relpath(FINAL_CLEAN_DATASET)}`",
        f"- Train output: `{relpath(TRAIN_CLEAN)}`",
        f"- Validation output: `{relpath(VAL_CLEAN)}`",
        f"- Test output: `{relpath(TEST_CLEAN)}`",
        f"- Split seed: {SPLIT_SEED}",
        "- Split method: duplicate normalized message keys were assigned as indivisible groups before stratified allocation.",
        "",
        "## Target Label Counts",
        "",
        *markdown_table(["Label", "Train target", "Val target", "Test target"], [[label, values["train"], values["val"], values["test"]] for label, values in sorted(targets.items())]),
        "",
        "## Actual Split Counts",
        "",
        *markdown_table(["Split", "Rows", "Ham", "Smishing", "Synthetic ham"], rows),
        "",
        "## Synthetic Ham By Split",
        "",
        *count_table(Counter(df[df["is_synthetic"].eq("True")]["split"]), "Split"),
        "",
        "## Leakage Controls",
        "",
        f"- Duplicate normalized key rows in clean master: {duplicate_key_rows}",
        f"- Duplicate normalized raw key rows in clean master: {duplicate_raw_key_rows}",
        f"- Duplicate normalized key groups crossing splits: {cross_split_duplicate_keys}",
        f"- Duplicate normalized raw key groups crossing splits: {cross_split_raw_duplicate_keys}",
        f"- Final row IDs assigned to exactly one split: {'Yes' if df['final_row_id'].is_unique else 'No'}",
        "",
        "## Notes",
        "",
        "- Synthetic ham is stratified within the ham label and remains traceable through `is_synthetic` and `data_origin`.",
        "- Smishing rows remain public/real source rows only.",
    ]
    write_text(REPORTS_DIR / "split_report.md", lines)


def main() -> int:
    train, val, test = create_splits()
    print(f"Train clean: {relpath(TRAIN_CLEAN)} rows={len(train)} labels={dict(label_counts(train))}")
    print(f"Validation clean: {relpath(VAL_CLEAN)} rows={len(val)} labels={dict(label_counts(val))}")
    print(f"Test clean: {relpath(TEST_CLEAN)} rows={len(test)} labels={dict(label_counts(test))}")
    print(f"Split manifest: {relpath(MANIFESTS_DIR / 'split_membership_manifest.csv')}")
    print(f"Report: {relpath(REPORTS_DIR / 'split_report.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
