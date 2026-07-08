#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
HELPER = ROOT / "scripts/build_glm_next50_tailmerge_floor_candidates_20260707.py"
RUNNER = ROOT / "scripts/run_ipo_redundancy_codex_cli_20260628.py"
DATE_TAG = "20260708"
PROMPT_MODE = "cot_v3b_len132_tight"
GLM300_CHUNK = (
    ROOT
    / f"results/siliconflow_glm4_32b_glm300_merged_{DATE_TAG}/"
    f"chunk_metrics_glm4_{PROMPT_MODE}_{DATE_TAG}.csv"
)
SHARD_RUNS = [f"siliconflow_glm4_32b_table2_remaining_to471_shard{i}_{DATE_TAG}" for i in range(1, 7)]
RUN_DIR = ROOT / f"results/siliconflow_glm4_32b_glm471_merged_{DATE_TAG}"
OUT_DIR = ROOT / f"results/glm471_tailmerge_floor_candidates_{DATE_TAG}"
DOC = ROOT / f"docs/00_current/siliconflow_glm4_32b_glm471_{DATE_TAG}.md"
PREV_SUMMARY = ROOT / f"results/glm300_tailmerge_floor_candidates_{DATE_TAG}/candidate_summary_{DATE_TAG}.csv"


def import_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_helper():
    return import_module("glm_helper", HELPER)


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def ensure_shard_metrics(helper, run_name: str) -> Path:
    run_dir = ROOT / "results" / run_name
    source_csv = run_dir / "ipo_business_technology_chunks.csv"
    jsonl = run_dir / f"ipo_redundancy_llm_outputs_{PROMPT_MODE}.jsonl"
    chunk_csv = run_dir / f"ipo_redundancy_chunk_with_llm_{PROMPT_MODE}.csv"
    if not source_csv.exists():
        raise FileNotFoundError(f"Missing source chunks for {run_name}: {source_csv}")
    total = max(sum(1 for _ in source_csv.open("r", encoding="utf-8-sig")) - 1, 0)
    done = count_jsonl(jsonl)
    if done != total:
        raise RuntimeError(f"{run_name} is incomplete: jsonl rows={done}, source chunks={total}")
    if not chunk_csv.exists():
        runner = import_module("ipo_runner", RUNNER)
        runner.aggregate(run_dir, PROMPT_MODE)

    dated = run_dir / f"chunk_metrics_glm4_{PROMPT_MODE}_{DATE_TAG}.csv"
    legacy = run_dir / f"chunk_metrics_glm4_{PROMPT_MODE}_20260707.csv"
    if not dated.exists():
        old_run_dir = helper.RUN_DIR
        try:
            helper.RUN_DIR = run_dir
            helper.build_chunk_metrics()
        finally:
            helper.RUN_DIR = old_run_dir
        if legacy.exists() and not dated.exists():
            legacy.rename(dated)
    if not dated.exists():
        raise FileNotFoundError(f"Missing built chunk metrics for {run_name}: {dated}")
    return dated


def load_chunks(helper) -> pd.DataFrame:
    if not GLM300_CHUNK.exists():
        raise FileNotFoundError(f"Missing GLM300 chunk metrics: {GLM300_CHUNK}")
    parts = []
    base = pd.read_csv(GLM300_CHUNK, dtype={"sec_code": str, "custom_id": str})
    base["source_glm_batch"] = "glm300"
    parts.append(base)
    for run_name in SHARD_RUNS:
        path = ensure_shard_metrics(helper, run_name)
        df = pd.read_csv(path, dtype={"sec_code": str, "custom_id": str})
        df["source_glm_batch"] = run_name.replace(f"siliconflow_glm4_32b_table2_remaining_to471_", "")
        parts.append(df)

    chunks = pd.concat(parts, ignore_index=True)
    duplicated = chunks["custom_id"].duplicated(keep=False)
    if duplicated.any():
        dup_count = int(duplicated.sum())
        chunks = chunks.drop_duplicates("custom_id", keep="last")
        print(f"[dedupe] duplicate custom_id rows={dup_count}; kept last occurrence")
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    chunks.to_csv(RUN_DIR / f"chunk_metrics_glm4_{PROMPT_MODE}_{DATE_TAG}.csv", index=False, encoding="utf-8-sig")
    chunks[[c for c in chunks.columns if c != "summary_text"]].to_csv(
        RUN_DIR / f"chunk_metrics_glm4_{PROMPT_MODE}_no_summary_text_{DATE_TAG}.csv",
        index=False,
        encoding="utf-8-sig",
    )
    return chunks


def best_vs_paper(helper, row: pd.Series) -> list[str]:
    rows = []
    for metric in ["Chunk_num", "Text_len", "Summary_len", "Redundancy_chunk", "lnN_tech", "Redundancy"]:
        target = helper.PAPER_CHUNK.get(metric) or helper.PAPER_FIRM.get(metric) or {}
        rows.append(
            {
                "metric": metric,
                "mean": helper.fmt(row[f"{metric}_mean"]),
                "paper_mean": helper.fmt(target["mean"]),
                "std": helper.fmt(row[f"{metric}_std"]),
                "paper_std": helper.fmt(target["std"]),
                "median": helper.fmt(row[f"{metric}_median"]),
                "paper_median": helper.fmt(target["median"]),
                "p75": helper.fmt(row[f"{metric}_p75"]),
                "paper_p75": helper.fmt(target["p75"]),
            }
        )
    return helper.md_table(
        pd.DataFrame(rows),
        ["metric", "mean", "paper_mean", "std", "paper_std", "median", "paper_median", "p75", "paper_p75"],
        None,
    )


def write_doc(helper, chunks: pd.DataFrame, summary: pd.DataFrame) -> None:
    DOC.parent.mkdir(parents=True, exist_ok=True)
    best = summary.iloc[0]
    best_name = str(best["name"])
    raw = summary[summary["name"].eq("raw_proxy")].iloc[0]
    top = summary.head(10)
    compare_cols = [
        "name",
        "loss_all",
        "chunk_n",
        "firm_n",
        "floor_applied_n",
        "Chunk_num_mean",
        "Text_len_mean",
        "Text_len_std",
        "Summary_len_mean",
        "Summary_len_std",
        "Redundancy_chunk_mean",
        "Redundancy_chunk_std",
        "Redundancy_mean",
        "Redundancy_std",
        "panel_b_rho",
        "panel_b_p",
        "low_score_red_median",
        "high_score_red_median",
        "panel_c_rho",
        "panel_d_rho",
    ]
    batch_counts = (
        chunks[["sec_code", "source_glm_batch"]]
        .drop_duplicates()
        .groupby("source_glm_batch")["sec_code"]
        .nunique()
        .reset_index(name="firm_n")
        .sort_values("source_glm_batch")
    )
    prev_line = "未读取到 GLM300 候选 summary。"
    if PREV_SUMMARY.exists():
        prev = pd.read_csv(PREV_SUMMARY).sort_values("loss_all").iloc[0]
        prev_line = (
            f"GLM300 最佳候选为 `{prev['name']}`，"
            f"Summary_len mean={helper.fmt(prev['Summary_len_mean'])}，"
            f"Redundancy_chunk mean={helper.fmt(prev['Redundancy_chunk_mean'])}。"
        )

    doc = [
        "# SiliconFlow GLM-4-32B GLM471 合并测度诊断",
        "",
        "日期：2026-07-08",
        "",
        "## 结论",
        "",
        f"- 合并测度池：firm={chunks['sec_code'].nunique()}，chunk={chunks.shape[0]}。名称 GLM471 指向 Table2 可用样本口径，不等于测度池只含 471 家。",
        f"- 原始 GLM proxy：Summary_len mean={helper.fmt(raw['Summary_len_mean'])}，Redundancy_chunk mean={helper.fmt(raw['Redundancy_chunk_mean'])}。",
        f"- GLM471 最接近原文 Table 1 的候选是 `{best_name}`：Summary_len mean={helper.fmt(best['Summary_len_mean'])}，Redundancy_chunk mean={helper.fmt(best['Redundancy_chunk_mean'])}，企业层 Redundancy mean={helper.fmt(best['Redundancy_mean'])}。",
        f"- Panel B：rho={helper.fmt(best['panel_b_rho'])}, p={helper.fmt(best['panel_b_p'])}；低评分组中位数={helper.fmt(best['low_score_red_median'])}，高评分组中位数={helper.fmt(best['high_score_red_median'])}。",
        f"- {prev_line}",
        "",
        "## Source Batch Counts",
        "",
        *helper.md_table(batch_counts, ["source_glm_batch", "firm_n"], None),
        "",
        "## 候选口径排序",
        "",
        *helper.md_table(top[compare_cols], compare_cols, None),
        "",
        "## 最佳候选 vs 原文",
        "",
        *best_vs_paper(helper, best),
        "",
        "## 输出文件",
        "",
        f"- merged chunk metrics：`{RUN_DIR / f'chunk_metrics_glm4_{PROMPT_MODE}_{DATE_TAG}.csv'}`",
        f"- no-summary review CSV：`{RUN_DIR / f'chunk_metrics_glm4_{PROMPT_MODE}_no_summary_text_{DATE_TAG}.csv'}`",
        f"- candidate summary：`{OUT_DIR / f'candidate_summary_{DATE_TAG}.csv'}`",
        f"- best chunk：`{OUT_DIR / f'{best_name}_chunk_metrics_{DATE_TAG}.csv'}`",
        f"- best firm：`{OUT_DIR / f'{best_name}_firm_metrics_{DATE_TAG}.csv'}`",
        "",
    ]
    DOC.write_text("\n".join(doc), encoding="utf-8")


def main() -> None:
    helper = load_helper()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    chunks = load_chunks(helper)
    rows = []
    for candidate in helper.CANDIDATES:
        c, f = helper.build_candidate(chunks, candidate)
        c.to_csv(OUT_DIR / f"{candidate['name']}_chunk_metrics_{DATE_TAG}.csv", index=False, encoding="utf-8-sig")
        f.to_csv(OUT_DIR / f"{candidate['name']}_firm_metrics_{DATE_TAG}.csv", index=False, encoding="utf-8-sig")
        rows.append(helper.evaluate_candidate(c, f, candidate))
    summary = pd.DataFrame(rows).sort_values("loss_all")
    summary.to_csv(OUT_DIR / f"candidate_summary_{DATE_TAG}.csv", index=False, encoding="utf-8-sig")
    write_doc(helper, chunks, summary)
    print(json.dumps({"doc": str(DOC), "summary": str(OUT_DIR / f"candidate_summary_{DATE_TAG}.csv"), "best": str(summary.iloc[0]["name"])}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
