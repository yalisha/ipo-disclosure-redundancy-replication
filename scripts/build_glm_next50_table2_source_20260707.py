#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pandas as pd


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
OUT_DIR = ROOT / "results/glm4_dewrap_join_glm_next50_table2_20260707"
DOC_OUT = ROOT / "docs/00_current/glm_next50_table2_source_20260707.md"

TABLE2_MASTER = ROOT / "results/cutoff552_table2_471_probe_20260707/table2_471_candidate_master_20260707.csv"
GLM50_CHUNK = ROOT / "results/siliconflow_glm4_32b_pilot50_20260707/ipo_redundancy_chunk_with_llm_cot_v3b_len132_tight.csv"

SOURCE_DIRS = [
    ROOT / "results/glm4_dewrap_join_full543_20260705",
    ROOT / "results/glm4_dewrap_join_first_batch25_20260706",
]
PROMPT_MODE = "cot_v3b_len132_tight"


def z6(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)


def read_source_file(filename: str) -> pd.DataFrame:
    frames = []
    for directory in SOURCE_DIRS:
        path = directory / filename
        if not path.exists():
            continue
        df = pd.read_csv(path, dtype={"sec_code": str, "code": str}, encoding="utf-8-sig", low_memory=False)
        if "sec_code" in df.columns:
            df["sec_code"] = z6(df["sec_code"])
        if "code" in df.columns:
            df["code"] = z6(df["code"])
        df["source_dir"] = directory.name
        frames.append(df)
    if not frames:
        raise FileNotFoundError(filename)
    out = pd.concat(frames, ignore_index=True, sort=False)
    if "custom_id" in out.columns:
        out = out.drop_duplicates("custom_id", keep="last")
    elif "sec_code" in out.columns:
        out = out.drop_duplicates("sec_code", keep="last")
    return out


def choose_codes() -> pd.DataFrame:
    master = pd.read_csv(TABLE2_MASTER, dtype={"code": str}, encoding="utf-8-sig", low_memory=False)
    master["code"] = z6(master["code"])
    master["first_trade_date"] = pd.to_datetime(master["first_trade_date"], errors="coerce")
    ran = pd.read_csv(GLM50_CHUNK, dtype={"sec_code": str}, encoding="utf-8-sig", usecols=["sec_code"])
    ran_codes = set(z6(ran["sec_code"]))
    sample = (
        master[~master["code"].isin(ran_codes)]
        .sort_values(["first_trade_date", "code"])
        .head(50)
        .copy()
    )
    if sample["code"].nunique() != 50:
        raise RuntimeError(f"Expected 50 codes, got {sample['code'].nunique()}")
    return sample[["code", "sec_name", "first_trade_date", "listing_year", "FInvention", "BHAR", "FSales_Growth"]]


def md_table(df: pd.DataFrame, cols: list[str]) -> list[str]:
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df.iterrows():
        vals = []
        for col in cols:
            val = row.get(col, "")
            if isinstance(val, float):
                vals.append(f"{val:.4f}")
            elif pd.isna(val):
                vals.append("")
            else:
                vals.append(str(val)[:80])
        out.append("| " + " | ".join(vals) + " |")
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sample = choose_codes()
    codes = set(sample["code"])

    chunks_all = read_source_file("ipo_business_technology_chunks.csv")
    sections_all = read_source_file("ipo_business_technology_sections.csv")
    llm_all = read_source_file(f"ipo_redundancy_chunk_with_llm_{PROMPT_MODE}.csv")

    chunks = chunks_all[chunks_all["sec_code"].isin(codes)].copy()
    sections = sections_all[sections_all["sec_code"].isin(codes)].copy()
    llm = llm_all[llm_all["sec_code"].isin(codes)].copy()

    missing_chunks = sorted(codes - set(chunks["sec_code"]))
    missing_llm = sorted(codes - set(llm["sec_code"]))
    if missing_chunks or missing_llm:
        raise RuntimeError(f"Missing chunks={missing_chunks} missing_llm={missing_llm}")
    if chunks["custom_id"].nunique() != llm["custom_id"].nunique():
        raise RuntimeError(
            f"Chunk/LLM custom_id mismatch: chunks={chunks['custom_id'].nunique()} llm={llm['custom_id'].nunique()}"
        )

    order_codes = {code: i for i, code in enumerate(sample["code"].tolist())}
    for df in [chunks, sections, llm]:
        df["_order"] = df["sec_code"].map(order_codes)
        sort_cols = ["_order"]
        if "chunk_index" in df.columns:
            df["_chunk_index_num"] = pd.to_numeric(df["chunk_index"], errors="coerce")
            sort_cols.append("_chunk_index_num")
        df.sort_values(sort_cols, inplace=True)
        df.drop(columns=[c for c in ["_order", "_chunk_index_num"] if c in df.columns], inplace=True)

    chunks.to_csv(OUT_DIR / "ipo_business_technology_chunks.csv", index=False, encoding="utf-8-sig")
    sections.to_csv(OUT_DIR / "ipo_business_technology_sections.csv", index=False, encoding="utf-8-sig")
    llm.to_csv(OUT_DIR / f"ipo_redundancy_chunk_with_llm_{PROMPT_MODE}.csv", index=False, encoding="utf-8-sig")
    sample.to_csv(OUT_DIR / "sample_firms_20260707.csv", index=False, encoding="utf-8-sig")
    (OUT_DIR / "sample_codes_20260707.txt").write_text("\n".join(sample["code"].tolist()) + "\n", encoding="utf-8")

    manifest = {
        "created_at": date.today().isoformat(),
        "purpose": "next 50 Table2 firms not yet run by SiliconFlow GLM-4-32B pilot50",
        "prompt_mode": PROMPT_MODE,
        "firm_n": int(sample["code"].nunique()),
        "chunk_n": int(chunks.shape[0]),
        "source_dirs": [p.name for p in SOURCE_DIRS],
        "selection_rule": "Table2 471 firms excluding existing SiliconFlow pilot50 codes, sorted by first_trade_date then code, take first 50",
    }
    (OUT_DIR / "manifest_20260707.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    doc = [
        "# GLM Next50 Table2 Source",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 说明",
        "",
        "- 目的：为 `GLM-only` 假说继续跑 50 家，优先覆盖 Table 2 471 家样本。",
        "- 选择规则：从 Table2 471 家中排除已经在 `siliconflow_glm4_32b_pilot50_20260707` 跑过的公司，按上市日和代码排序取前 50 家。",
        f"- firm N：`{sample['code'].nunique()}`。",
        f"- chunk N：`{chunks.shape[0]}`。",
        "- 本目录只生成 SiliconFlow 输入 source run；真正 GLM 输出写入下一步的 `siliconflow_glm4_32b_table2_next50_20260707`。",
        "",
        "## 公司清单",
        "",
        *md_table(sample, ["code", "sec_name", "first_trade_date", "listing_year", "FInvention", "BHAR", "FSales_Growth"]),
        "",
        "## 输出",
        "",
        f"- source run：`{OUT_DIR}`",
        f"- chunks：`{OUT_DIR / 'ipo_business_technology_chunks.csv'}`",
        f"- sections：`{OUT_DIR / 'ipo_business_technology_sections.csv'}`",
        f"- source Codex LLM comparison：`{OUT_DIR / f'ipo_redundancy_chunk_with_llm_{PROMPT_MODE}.csv'}`",
        "",
    ]
    DOC_OUT.write_text("\n".join(doc), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
