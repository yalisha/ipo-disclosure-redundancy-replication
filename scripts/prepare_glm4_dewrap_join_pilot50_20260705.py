#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
SOURCE = ROOT / "results/glm4_dewrap_rechunk_trial_20260705/dewrap_join"
ANCHOR = ROOT / "results/glm4_dewrap_join_pilot5_20260705"
OUT = ROOT / "results/glm4_dewrap_join_pilot50_20260705"
MODE = "cot_v3b_len132_tight"
QUOTA_PER_YEAR = 10


def quantile_pick(group: pd.DataFrame, n: int) -> pd.DataFrame:
    group = group.sort_values(["tech_text_glm4_tokens", "sec_code"]).reset_index(drop=True)
    if n <= 0:
        return group.head(0)
    if len(group) <= n:
        return group
    positions = np.linspace(0, len(group) - 1, n).round().astype(int)
    positions = list(dict.fromkeys(int(x) for x in positions))
    picked = group.iloc[positions].copy()
    if len(picked) < n:
        remaining = group.drop(index=positions).copy()
        picked = pd.concat([picked, remaining.head(n - len(picked))], ignore_index=True)
    return picked.head(n)


def select_sample(sections: pd.DataFrame) -> pd.DataFrame:
    sections = sections.copy()
    sections["year"] = sections["announcement_date"].astype(str).str[:4]
    sections["tech_text_glm4_tokens"] = pd.to_numeric(sections["tech_text_glm4_tokens"], errors="coerce")
    anchor_codes: set[str] = set()
    if (ANCHOR / "sample_firms_20260705.csv").exists():
        anchor_df = pd.read_csv(ANCHOR / "sample_firms_20260705.csv", dtype={"sec_code": str})
        anchor_codes = set(anchor_df["sec_code"].astype(str))

    picks = []
    for year, group in sections.groupby("year", sort=True):
        if year not in {"2019", "2020", "2021", "2022", "2023"}:
            continue
        year_anchor = group[group["sec_code"].astype(str).isin(anchor_codes)].copy()
        if len(year_anchor) > QUOTA_PER_YEAR:
            year_anchor = year_anchor.sort_values(["tech_text_glm4_tokens", "sec_code"]).head(QUOTA_PER_YEAR)
        need = QUOTA_PER_YEAR - len(year_anchor)
        pool = group[~group["sec_code"].astype(str).isin(set(year_anchor["sec_code"].astype(str)))].copy()
        picks.append(pd.concat([year_anchor, quantile_pick(pool, need)], ignore_index=True))

    sample = pd.concat(picks, ignore_index=True)
    sample = sample.sort_values(["year", "tech_text_glm4_tokens", "sec_code"]).reset_index(drop=True)
    return sample


def copy_text_files(sample_sections: pd.DataFrame, sample_chunks: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    sample_sections = sample_sections.copy()
    sample_chunks = sample_chunks.copy()
    for src_rel in sample_sections["section_file"]:
        src = ROOT / str(src_rel)
        dst = OUT / "business_technology_text" / src.name
        shutil.copy2(src, dst)
    sample_sections["section_file"] = sample_sections["section_file"].map(
        lambda p: str((OUT / "business_technology_text" / Path(str(p)).name).relative_to(ROOT))
    )

    for src_rel in sample_chunks["chunk_file"]:
        src = ROOT / str(src_rel)
        dst = OUT / "chunks" / src.name
        shutil.copy2(src, dst)
    sample_chunks["chunk_file"] = sample_chunks["chunk_file"].map(
        lambda p: str((OUT / "chunks" / Path(str(p)).name).relative_to(ROOT))
    )
    return sample_sections, sample_chunks


def seed_anchor_outputs(sample_chunks: pd.DataFrame) -> int:
    src = ANCHOR / f"ipo_redundancy_llm_outputs_{MODE}.jsonl"
    dst = OUT / f"ipo_redundancy_llm_outputs_{MODE}.jsonl"
    if not src.exists():
        return 0
    sample_ids = set(sample_chunks["custom_id"].astype(str))
    rows = []
    with src.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if str(row.get("custom_id", "")) in sample_ids:
                rows.append(row)
    if rows:
        with dst.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(rows)


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "business_technology_text").mkdir(parents=True)
    (OUT / "chunks").mkdir(parents=True)

    sections = pd.read_csv(SOURCE / "ipo_business_technology_sections.csv", dtype={"sec_code": str}).fillna("")
    chunks = pd.read_csv(SOURCE / "ipo_business_technology_chunks.csv", dtype={"sec_code": str}).fillna("")
    sample_sections = select_sample(sections)
    sample_codes = set(sample_sections["sec_code"].astype(str))
    sample_chunks = chunks[chunks["sec_code"].astype(str).isin(sample_codes)].copy()

    for df in [sample_sections, sample_chunks]:
        if "chunk_glm4_tokens" in df.columns:
            df["chunk_token_proxy"] = pd.to_numeric(df["chunk_glm4_tokens"], errors="coerce")
        if "tech_text_glm4_tokens" in df.columns:
            df["tech_text_token_proxy"] = pd.to_numeric(df["tech_text_glm4_tokens"], errors="coerce")
            df["token_mode"] = "glm4_dewrap_join"

    sample_sections, sample_chunks = copy_text_files(sample_sections, sample_chunks)
    seeded_chunks = seed_anchor_outputs(sample_chunks)

    sample_sections.to_csv(OUT / "ipo_business_technology_sections.csv", index=False, encoding="utf-8-sig")
    sample_chunks.to_csv(OUT / "ipo_business_technology_chunks.csv", index=False, encoding="utf-8-sig")
    sample_sections[["sec_code", "sec_name", "announcement_date", "chunk_count", "tech_text_glm4_tokens"]].to_csv(
        OUT / "sample_firms_20260705.csv", index=False, encoding="utf-8-sig"
    )
    (OUT / "sample_codes_20260705.txt").write_text(
        ",".join(sample_sections["sec_code"].astype(str)),
        encoding="utf-8",
    )
    manifest = {
        "source": str(SOURCE.relative_to(ROOT)),
        "anchor": str(ANCHOR.relative_to(ROOT)),
        "out": str(OUT.relative_to(ROOT)),
        "quota_per_year": QUOTA_PER_YEAR,
        "sample_codes": sample_sections["sec_code"].astype(str).tolist(),
        "firms": int(len(sample_sections)),
        "chunks": int(len(sample_chunks)),
        "seeded_chunks_from_pilot5": int(seeded_chunks),
        "remaining_chunks_for_llm": int(len(sample_chunks) - seeded_chunks),
        "chunk_glm4_tokens_mean": float(pd.to_numeric(sample_chunks["chunk_glm4_tokens"], errors="coerce").mean()),
    }
    (OUT / "manifest_20260705.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(sample_sections[["sec_code", "sec_name", "announcement_date", "chunk_count", "tech_text_glm4_tokens"]].to_string(index=False))


if __name__ == "__main__":
    main()
