#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import math
from datetime import date
from pathlib import Path

import pandas as pd


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
DATE_TAG = "20260708"
PROMPT_MODE = "cot_v3b_len132_tight"
TABLE2_MASTER = ROOT / "results/cutoff552_table2_471_probe_20260707/table2_471_candidate_master_20260707.csv"
DEFAULT_COMPLETED = ROOT / "results/glm300_tailmerge_floor_candidates_20260708/proxy_tailmerge1600_floor50_firm_metrics_20260708.csv"
SOURCE_STEM = "glm4_dewrap_join_glm_remaining_to471_table2"
OUT_DIR = ROOT / f"results/{SOURCE_STEM}_{DATE_TAG}"
DOC_OUT = ROOT / f"docs/00_current/glm_remaining_to471_table2_source_{DATE_TAG}.md"


def import_base():
    path = ROOT / "scripts/build_glm_next100_table2_source_20260708.py"
    spec = importlib.util.spec_from_file_location("glm_next100_source_base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = import_base()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--table2-master", type=Path, default=TABLE2_MASTER)
    parser.add_argument("--completed-firm-metrics", type=Path, default=DEFAULT_COMPLETED)
    parser.add_argument("--shard-n", type=int, default=6)
    parser.add_argument("--source-stem", default=SOURCE_STEM)
    return parser.parse_args()


def completed_codes(path: Path) -> set[str]:
    df = pd.read_csv(path, dtype={"sec_code": str}, encoding="utf-8-sig", low_memory=False)
    if "sec_code" in df.columns:
        return set(base.z6(df["sec_code"]))
    if "code" in df.columns:
        return set(base.z6(df["code"]))
    raise ValueError(f"No sec_code/code column in {path}")


def choose_remaining(table2_master: Path, completed_path: Path) -> pd.DataFrame:
    master = pd.read_csv(table2_master, dtype={"code": str, "sec_code": str}, encoding="utf-8-sig", low_memory=False)
    master["code"] = base.z6(master["code"])
    master["sec_code"] = base.z6(master["sec_code"])
    master["first_trade_date"] = pd.to_datetime(master["first_trade_date"], errors="coerce")
    done = completed_codes(completed_path)
    sample = master[~master["sec_code"].isin(done)].sort_values(["first_trade_date", "sec_code"]).copy()
    keep = [
        "code",
        "sec_code",
        "sec_name",
        "first_trade_date",
        "listing_year",
        "chunk_count",
        "FInvention",
        "BHAR",
        "FSales_Growth",
    ]
    return sample[[c for c in keep if c in sample.columns]]


def write_source_run(
    out_dir: Path,
    sample: pd.DataFrame,
    chunks: pd.DataFrame,
    sections: pd.DataFrame,
    llm: pd.DataFrame,
    suffix: str,
    source_dirs: list[str],
    selection_rule: str,
) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    chunks.to_csv(out_dir / "ipo_business_technology_chunks.csv", index=False, encoding="utf-8-sig")
    sections.to_csv(out_dir / "ipo_business_technology_sections.csv", index=False, encoding="utf-8-sig")
    llm.to_csv(out_dir / f"ipo_redundancy_chunk_with_llm_{PROMPT_MODE}.csv", index=False, encoding="utf-8-sig")
    sample.to_csv(out_dir / f"sample_firms_{DATE_TAG}.csv", index=False, encoding="utf-8-sig")
    (out_dir / f"sample_codes_{DATE_TAG}.txt").write_text("\n".join(sample["sec_code"].tolist()) + "\n", encoding="utf-8")
    manifest = {
        "created_at": date.today().isoformat(),
        "purpose": "remaining Table2 471 firms not yet run by SiliconFlow GLM-4-32B",
        "prompt_mode": PROMPT_MODE,
        "firm_n": int(sample["sec_code"].nunique()),
        "chunk_n": int(chunks.shape[0]),
        "source_dirs": source_dirs,
        "selection_rule": selection_rule,
        "suffix": suffix,
    }
    (out_dir / f"manifest_{DATE_TAG}.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def validate_inputs(codes: set[str], chunks: pd.DataFrame, sections: pd.DataFrame, llm: pd.DataFrame) -> None:
    missing_chunks = sorted(codes - set(chunks["sec_code"]))
    missing_sections = sorted(codes - set(sections["sec_code"]))
    missing_llm = sorted(codes - set(llm["sec_code"]))
    if missing_chunks or missing_sections or missing_llm:
        raise RuntimeError(
            f"Missing chunks={missing_chunks} sections={missing_sections} source_llm={missing_llm}"
        )
    if chunks["custom_id"].nunique() != llm["custom_id"].nunique():
        raise RuntimeError(
            f"Chunk/LLM custom_id mismatch: chunks={chunks['custom_id'].nunique()} llm={llm['custom_id'].nunique()}"
        )


def main() -> None:
    args = parse_args()
    sample = choose_remaining(args.table2_master, args.completed_firm_metrics)
    codes = set(sample["sec_code"])
    chunks_all = base.read_source_file("ipo_business_technology_chunks.csv")
    sections_all = base.read_source_file("ipo_business_technology_sections.csv")
    llm_all = base.read_source_file(f"ipo_redundancy_chunk_with_llm_{PROMPT_MODE}.csv")

    chunks = chunks_all[chunks_all["sec_code"].isin(codes)].copy()
    sections = sections_all[sections_all["sec_code"].isin(codes)].copy()
    llm = llm_all[llm_all["sec_code"].isin(codes)].copy()
    validate_inputs(codes, chunks, sections, llm)
    order_sample = pd.DataFrame({"code": sample["sec_code"].tolist()})
    base.order_dataframes(order_sample, [chunks, sections, llm])

    selection_rule = (
        "Table2 471 firms excluding completed firm metrics, sorted by first_trade_date and sec_code; take all remaining"
    )
    manifest = write_source_run(
        OUT_DIR,
        sample,
        chunks,
        sections,
        llm,
        "all",
        [p.name for p in base.SOURCE_DIRS],
        selection_rule,
    )

    shard_rows = []
    per_shard = math.ceil(sample.shape[0] / args.shard_n) if args.shard_n else sample.shape[0]
    for i in range(args.shard_n):
        shard_sample = sample.iloc[i * per_shard : (i + 1) * per_shard].copy()
        if shard_sample.empty:
            continue
        shard_codes = set(shard_sample["sec_code"])
        shard_chunks = chunks[chunks["sec_code"].isin(shard_codes)].copy()
        shard_sections = sections[sections["sec_code"].isin(shard_codes)].copy()
        shard_llm = llm[llm["sec_code"].isin(shard_codes)].copy()
        shard_order_sample = pd.DataFrame({"code": shard_sample["sec_code"].tolist()})
        base.order_dataframes(shard_order_sample, [shard_chunks, shard_sections, shard_llm])
        shard_dir = ROOT / f"results/{args.source_stem}_shard{i + 1}_{DATE_TAG}"
        shard_manifest = write_source_run(
            shard_dir,
            shard_sample,
            shard_chunks,
            shard_sections,
            shard_llm,
            f"shard{i + 1}",
            [p.name for p in base.SOURCE_DIRS],
            selection_rule,
        )
        run_name = f"siliconflow_glm4_32b_table2_remaining_to471_shard{i + 1}_{DATE_TAG}"
        command = (
            "python scripts/run_siliconflow_glm4_32b_pilot5_20260707.py "
            f"--source-run-name {shard_dir.name} "
            f"--run-name {run_name} "
            f"--doc-name siliconflow_glm4_32b_table2_remaining_to471_shard{i + 1}_{DATE_TAG}.md "
            f"--doc-label Table2_remaining_to471_shard{i + 1} "
            "--batch-size 2"
        )
        shard_rows.append(
            {
                "shard": i + 1,
                "source_run_name": shard_dir.name,
                "suggested_siliconflow_run_name": run_name,
                "firm_n": shard_manifest["firm_n"],
                "chunk_n": shard_manifest["chunk_n"],
                "first_code": shard_sample["sec_code"].iloc[0],
                "last_code": shard_sample["sec_code"].iloc[-1],
                "command": command,
            }
        )
    shard_plan = pd.DataFrame(shard_rows)
    shard_plan.to_csv(OUT_DIR / f"shard_plan_{DATE_TAG}.csv", index=False, encoding="utf-8-sig")

    doc = [
        "# GLM Remaining-To-471 Table2 Source",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 说明",
        "",
        "- 目的：把 GLM-only X 从当前覆盖推进到 Table2 471 候选全覆盖，用于裁决 BHAR 是否只是样本量/功效问题。",
        f"- completed firm metrics：`{args.completed_firm_metrics}`",
        f"- remaining firm N：`{manifest['firm_n']}`。",
        f"- remaining chunk N：`{manifest['chunk_n']}`。",
        "- 本脚本只生成 SiliconFlow 输入 source run 和分片命令，不直接调用 API。",
        "",
        "## Shards",
        "",
        *base.md_table(
            shard_plan,
            [
                "shard",
                "source_run_name",
                "suggested_siliconflow_run_name",
                "firm_n",
                "chunk_n",
                "first_code",
                "last_code",
            ],
        ),
        "",
        "## Suggested Commands",
        "",
        "```bash",
        "export SILICONFLOW_API_KEY=...",
        *shard_plan["command"].astype(str).tolist(),
        "```",
        "",
        "## 公司清单",
        "",
        *base.md_table(
            sample,
            ["sec_code", "sec_name", "first_trade_date", "listing_year", "chunk_count", "FInvention", "BHAR", "FSales_Growth"],
        ),
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
    print(json.dumps({"doc": str(DOC_OUT), "manifest": manifest, "shards": shard_rows}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
