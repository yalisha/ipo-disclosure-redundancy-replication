#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
SOURCE = ROOT / "results/glm4_dewrap_rechunk_trial_20260705/dewrap_join"
OUT = ROOT / "results/glm4_dewrap_join_pilot5_20260705"


def select_sample(sections: pd.DataFrame) -> pd.DataFrame:
    sections = sections.copy()
    sections["year"] = sections["announcement_date"].astype(str).str[:4]
    sections["tech_text_glm4_tokens"] = pd.to_numeric(sections["tech_text_glm4_tokens"], errors="coerce")
    picks = []
    for year, group in sections.groupby("year", sort=True):
        median = group["tech_text_glm4_tokens"].median()
        ranked = group.assign(_dist=(group["tech_text_glm4_tokens"] - median).abs())
        picks.append(ranked.sort_values(["_dist", "sec_code"]).head(1))
    return pd.concat(picks, ignore_index=True).drop(columns=["_dist"])


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
        "out": str(OUT.relative_to(ROOT)),
        "sample_codes": sample_sections["sec_code"].astype(str).tolist(),
        "firms": int(len(sample_sections)),
        "chunks": int(len(sample_chunks)),
        "chunk_glm4_tokens_mean": float(pd.to_numeric(sample_chunks["chunk_glm4_tokens"], errors="coerce").mean()),
    }
    (OUT / "manifest_20260705.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(sample_sections[["sec_code", "sec_name", "announcement_date", "chunk_count", "tech_text_glm4_tokens"]].to_string(index=False))


if __name__ == "__main__":
    main()
