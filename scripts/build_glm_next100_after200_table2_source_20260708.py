#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import math
from datetime import date
from pathlib import Path

import pandas as pd


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
PROMPT_MODE = "cot_v3b_len132_tight"
DATE_TAG = "20260708"
OUT_STEM = "glm_next100_after200_table2"
SOURCE_STEM = "glm4_dewrap_join_glm_next100_after200_table2"
OUT_DIR = ROOT / f"results/{SOURCE_STEM}_{DATE_TAG}"
DOC_OUT = ROOT / f"docs/00_current/{OUT_STEM}_source_{DATE_TAG}.md"

TABLE2_MASTER = ROOT / "results/cutoff552_table2_471_probe_20260707/table2_471_candidate_master_20260707.csv"
EXCLUDE_CHUNK = ROOT / "results/siliconflow_glm4_32b_glm200_merged_20260708/chunk_metrics_glm4_cot_v3b_len132_tight_20260708.csv"
SHARD_N = 5
SAMPLE_N = 100


def import_base():
    path = ROOT / "scripts/build_glm_next100_table2_source_20260708.py"
    spec = importlib.util.spec_from_file_location("glm_next100_source_base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = import_base()


def choose_codes() -> pd.DataFrame:
    master = pd.read_csv(TABLE2_MASTER, dtype={"code": str, "sec_code": str}, encoding="utf-8-sig", low_memory=False)
    master["code"] = base.z6(master["code"])
    master["first_trade_date"] = pd.to_datetime(master["first_trade_date"], errors="coerce")
    ran = pd.read_csv(EXCLUDE_CHUNK, dtype={"sec_code": str}, encoding="utf-8-sig", usecols=["sec_code"])
    ran_codes = set(base.z6(ran["sec_code"]))
    sample = (
        master[~master["code"].isin(ran_codes)]
        .sort_values(["first_trade_date", "code"])
        .head(SAMPLE_N)
        .copy()
    )
    if sample["code"].nunique() != SAMPLE_N:
        raise RuntimeError(f"Expected {SAMPLE_N} codes, got {sample['code'].nunique()}")
    keep = ["code", "sec_name", "first_trade_date", "listing_year", "FInvention", "BHAR", "FSales_Growth"]
    return sample[keep]


def write_source_run(
    out_dir: Path,
    sample: pd.DataFrame,
    chunks: pd.DataFrame,
    sections: pd.DataFrame,
    llm: pd.DataFrame,
    suffix: str,
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    chunks.to_csv(out_dir / "ipo_business_technology_chunks.csv", index=False, encoding="utf-8-sig")
    sections.to_csv(out_dir / "ipo_business_technology_sections.csv", index=False, encoding="utf-8-sig")
    llm.to_csv(out_dir / f"ipo_redundancy_chunk_with_llm_{PROMPT_MODE}.csv", index=False, encoding="utf-8-sig")
    sample.to_csv(out_dir / f"sample_firms_{DATE_TAG}.csv", index=False, encoding="utf-8-sig")
    (out_dir / f"sample_codes_{DATE_TAG}.txt").write_text("\n".join(sample["code"].tolist()) + "\n", encoding="utf-8")
    manifest = {
        "created_at": date.today().isoformat(),
        "purpose": "third 100 Table2 firms not yet run by SiliconFlow GLM-4-32B GLM200",
        "prompt_mode": PROMPT_MODE,
        "firm_n": int(sample["code"].nunique()),
        "chunk_n": int(chunks.shape[0]),
        "source_dirs": [p.name for p in base.SOURCE_DIRS],
        "selection_rule": "Table2 471 firms excluding existing GLM200 codes, sorted by first_trade_date then code, take next 100",
        "suffix": suffix,
    }
    (out_dir / f"manifest_{DATE_TAG}.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    sample = choose_codes()
    codes = set(sample["code"])

    chunks_all = base.read_source_file("ipo_business_technology_chunks.csv")
    sections_all = base.read_source_file("ipo_business_technology_sections.csv")
    llm_all = base.read_source_file(f"ipo_redundancy_chunk_with_llm_{PROMPT_MODE}.csv")

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

    base.order_dataframes(sample, [chunks, sections, llm])
    manifest = write_source_run(OUT_DIR, sample, chunks, sections, llm, "all")

    shard_rows = []
    per_shard = math.ceil(SAMPLE_N / SHARD_N)
    for i in range(SHARD_N):
        shard_sample = sample.iloc[i * per_shard : (i + 1) * per_shard].copy()
        shard_codes = set(shard_sample["code"])
        if shard_sample.empty:
            continue
        shard_chunks = chunks[chunks["sec_code"].isin(shard_codes)].copy()
        shard_sections = sections[sections["sec_code"].isin(shard_codes)].copy()
        shard_llm = llm[llm["sec_code"].isin(shard_codes)].copy()
        base.order_dataframes(shard_sample, [shard_chunks, shard_sections, shard_llm])
        shard_dir = ROOT / f"results/{SOURCE_STEM}_shard{i + 1}_{DATE_TAG}"
        shard_manifest = write_source_run(shard_dir, shard_sample, shard_chunks, shard_sections, shard_llm, f"shard{i + 1}")
        shard_rows.append(
            {
                "shard": i + 1,
                "source_run_name": shard_dir.name,
                "firm_n": shard_manifest["firm_n"],
                "chunk_n": shard_manifest["chunk_n"],
                "first_code": shard_sample["code"].iloc[0],
                "last_code": shard_sample["code"].iloc[-1],
            }
        )
    shard_plan = pd.DataFrame(shard_rows)
    shard_plan.to_csv(OUT_DIR / f"shard_plan_{DATE_TAG}.csv", index=False, encoding="utf-8-sig")

    doc = [
        "# GLM Next100 After GLM200 Table2 Source",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 说明",
        "",
        "- 目的：继续验证 `GLM-only` 假说，新增第三个 100 家并把 GLM 样本推进到 300 家。",
        "- 选择规则：从 Table2 471 家中排除已在 GLM200 中出现的公司，按上市日和代码排序取下一组 100 家。",
        f"- firm N：`{sample['code'].nunique()}`。",
        f"- chunk N：`{chunks.shape[0]}`。",
        "- 本目录只生成 SiliconFlow 输入 source run；实际 API 输出写入 `siliconflow_glm4_32b_table2_next100_after200_shard*_20260708`。",
        "",
        "## Shards",
        "",
        *base.md_table(shard_plan, ["shard", "source_run_name", "firm_n", "chunk_n", "first_code", "last_code"]),
        "",
        "## 公司清单",
        "",
        *base.md_table(sample, ["code", "sec_name", "first_trade_date", "listing_year", "FInvention", "BHAR", "FSales_Growth"]),
        "",
        "## 输出",
        "",
        f"- source run：`{OUT_DIR}`",
        f"- shard plan：`{OUT_DIR / f'shard_plan_{DATE_TAG}.csv'}`",
        f"- chunks：`{OUT_DIR / 'ipo_business_technology_chunks.csv'}`",
        f"- sections：`{OUT_DIR / 'ipo_business_technology_sections.csv'}`",
        f"- source Codex LLM comparison：`{OUT_DIR / f'ipo_redundancy_chunk_with_llm_{PROMPT_MODE}.csv'}`",
        "",
    ]
    DOC_OUT.write_text("\n".join(doc), encoding="utf-8")
    print(json.dumps({"manifest": manifest, "shards": shard_rows}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
