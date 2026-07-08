#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
HELPER = ROOT / "scripts/build_glm_next50_tailmerge_floor_candidates_20260707.py"
DATE_TAG = "20260708"
PROMPT_MODE = "cot_v3b_len132_tight"
SHARD_RUNS = [f"siliconflow_glm4_32b_table2_next100_after200_shard{i}_{DATE_TAG}" for i in range(1, 6)]
RUN_DIR = ROOT / f"results/siliconflow_glm4_32b_table2_next100_after200_merged_{DATE_TAG}"
OUT_DIR = ROOT / f"results/glm_next100_after200_tailmerge_floor_candidates_{DATE_TAG}"
DOC = ROOT / f"docs/00_current/siliconflow_glm4_32b_table2_next100_after200_{DATE_TAG}.md"
PREV_SUMMARY = ROOT / f"results/glm200_tailmerge_floor_candidates_{DATE_TAG}/candidate_summary_{DATE_TAG}.csv"


def load_helper():
    spec = importlib.util.spec_from_file_location("glm_helper", HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {HELPER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.SHARD_RUNS = SHARD_RUNS
    module.RUN_DIR = RUN_DIR
    module.OUT_DIR = OUT_DIR
    module.DOC = DOC
    module.PREV_SUMMARY = PREV_SUMMARY
    return module


def write_doc(helper, chunks: pd.DataFrame, summary: pd.DataFrame) -> None:
    DOC.parent.mkdir(parents=True, exist_ok=True)
    best = summary.iloc[0]
    best_name = str(best["name"])
    raw = summary[summary["name"].eq("raw_proxy")].iloc[0]
    compare_cols = [
        "name",
        "loss_all",
        "chunk_n",
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
        "panel_c_rho",
        "panel_d_rho",
    ]
    prev_line = "未读取到 GLM200 候选 summary。"
    if PREV_SUMMARY.exists():
        prev = pd.read_csv(PREV_SUMMARY).sort_values("loss_all").iloc[0]
        prev_line = (
            f"GLM200 最佳候选为 `{prev['name']}`，"
            f"Summary_len mean={helper.fmt(prev['Summary_len_mean'])}，"
            f"Redundancy_chunk mean={helper.fmt(prev['Redundancy_chunk_mean'])}。"
        )

    rows = []
    for metric in ["Chunk_num", "Text_len", "Summary_len", "Redundancy_chunk", "lnN_tech", "Redundancy"]:
        target = helper.PAPER_CHUNK.get(metric) or helper.PAPER_FIRM.get(metric) or {}
        rows.append(
            {
                "metric": metric,
                "mean": helper.fmt(best[f"{metric}_mean"]),
                "paper_mean": helper.fmt(target["mean"]),
                "std": helper.fmt(best[f"{metric}_std"]),
                "paper_std": helper.fmt(target["std"]),
                "median": helper.fmt(best[f"{metric}_median"]),
                "paper_median": helper.fmt(target["median"]),
                "p75": helper.fmt(best[f"{metric}_p75"]),
                "paper_p75": helper.fmt(target["p75"]),
            }
        )

    doc = [
        "# SiliconFlow GLM-4-32B Table2 next100 after GLM200 测度与候选口径",
        "",
        "日期：2026-07-08",
        "",
        "## 结论",
        "",
        f"- 本轮新增第三个 100 家已跑完并合并：chunk={chunks.shape[0]}，firm={chunks['sec_code'].nunique()}。",
        f"- 原始 GLM proxy：Summary_len mean={helper.fmt(raw['Summary_len_mean'])}，Redundancy_chunk mean={helper.fmt(raw['Redundancy_chunk_mean'])}。",
        f"- 本批最接近原文 Table 1 的候选是 `{best_name}`：Summary_len mean={helper.fmt(best['Summary_len_mean'])}，Redundancy_chunk mean={helper.fmt(best['Redundancy_chunk_mean'])}，企业层 Redundancy mean={helper.fmt(best['Redundancy_mean'])}。",
        f"- {prev_line}",
        "- 这批单独结果主要服务于 GLM300 合并 gate，不单独定版。",
        "",
        "## 候选口径排序",
        "",
        *helper.md_table(summary[compare_cols].head(10), compare_cols, None),
        "",
        "## 最佳候选 vs 原文",
        "",
        *helper.md_table(
            pd.DataFrame(rows),
            ["metric", "mean", "paper_mean", "std", "paper_std", "median", "paper_median", "p75", "paper_p75"],
            None,
        ),
        "",
        "## 输出文件",
        "",
        f"- merged run：`{RUN_DIR}`",
        f"- chunk metrics：`{RUN_DIR / f'chunk_metrics_glm4_{PROMPT_MODE}_{DATE_TAG}.csv'}`",
        f"- candidates：`{OUT_DIR}`",
        f"- candidate summary：`{OUT_DIR / f'candidate_summary_{DATE_TAG}.csv'}`",
        f"- best chunk：`{OUT_DIR / f'{best_name}_chunk_metrics_{DATE_TAG}.csv'}`",
        f"- best firm：`{OUT_DIR / f'{best_name}_firm_metrics_{DATE_TAG}.csv'}`",
        "",
    ]
    DOC.write_text("\n".join(doc), encoding="utf-8")


def main() -> None:
    helper = load_helper()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    helper.merge_shards()
    helper.build_chunk_metrics()
    chunk_metrics = RUN_DIR / f"chunk_metrics_glm4_{PROMPT_MODE}_20260707.csv"
    if chunk_metrics.exists():
        chunk_metrics.rename(RUN_DIR / f"chunk_metrics_glm4_{PROMPT_MODE}_{DATE_TAG}.csv")
    chunks = pd.read_csv(RUN_DIR / f"chunk_metrics_glm4_{PROMPT_MODE}_{DATE_TAG}.csv", dtype={"sec_code": str, "custom_id": str})
    rows = []
    for candidate in helper.CANDIDATES:
        c, f = helper.build_candidate(chunks, candidate)
        c.to_csv(OUT_DIR / f"{candidate['name']}_chunk_metrics_{DATE_TAG}.csv", index=False, encoding="utf-8-sig")
        f.to_csv(OUT_DIR / f"{candidate['name']}_firm_metrics_{DATE_TAG}.csv", index=False, encoding="utf-8-sig")
        rows.append(helper.evaluate_candidate(c, f, candidate))
    summary = pd.DataFrame(rows).sort_values("loss_all")
    summary.to_csv(OUT_DIR / f"candidate_summary_{DATE_TAG}.csv", index=False, encoding="utf-8-sig")
    write_doc(helper, chunks, summary)
    print({"doc": str(DOC), "summary": str(OUT_DIR / f"candidate_summary_{DATE_TAG}.csv"), "best": str(summary.iloc[0]["name"])})


if __name__ == "__main__":
    main()
