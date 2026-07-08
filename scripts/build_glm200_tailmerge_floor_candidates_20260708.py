#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
HELPER = ROOT / "scripts/build_glm_next50_tailmerge_floor_candidates_20260707.py"
DATE_TAG = "20260708"
OUT_RUN = ROOT / f"results/siliconflow_glm4_32b_glm200_merged_{DATE_TAG}"
OUT_DIR = ROOT / f"results/glm200_tailmerge_floor_candidates_{DATE_TAG}"
DOC = ROOT / f"docs/00_current/siliconflow_glm4_32b_glm200_{DATE_TAG}.md"

SOURCES = [
    (
        "glm100",
        ROOT / "results/siliconflow_glm4_32b_glm100_merged_20260707/chunk_metrics_glm4_cot_v3b_len132_tight_20260707.csv",
    ),
    (
        "table2_next100",
        ROOT / f"results/siliconflow_glm4_32b_table2_next100_merged_{DATE_TAG}/chunk_metrics_glm4_cot_v3b_len132_tight_{DATE_TAG}.csv",
    ),
]


def load_helper():
    spec = importlib.util.spec_from_file_location("glm_helper", HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {HELPER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_chunks() -> pd.DataFrame:
    parts = []
    for label, path in SOURCES:
        df = pd.read_csv(path, dtype={"sec_code": str, "custom_id": str})
        df["source_glm_batch"] = label
        parts.append(df)
    chunks = pd.concat(parts, ignore_index=True).drop_duplicates("custom_id", keep="last")
    OUT_RUN.mkdir(parents=True, exist_ok=True)
    chunks.to_csv(OUT_RUN / f"chunk_metrics_glm4_cot_v3b_len132_tight_{DATE_TAG}.csv", index=False, encoding="utf-8-sig")
    chunks[[c for c in chunks.columns if c != "summary_text"]].to_csv(
        OUT_RUN / f"chunk_metrics_glm4_cot_v3b_len132_tight_no_summary_text_{DATE_TAG}.csv",
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
    batch_counts = chunks[["sec_code", "source_glm_batch"]].drop_duplicates().groupby("source_glm_batch")["sec_code"].nunique().to_dict()
    doc = [
        "# SiliconFlow GLM-4-32B GLM200 合并测度诊断",
        "",
        "日期：2026-07-08",
        "",
        "## 结论",
        "",
        f"- 合并样本：firm={chunks['sec_code'].nunique()}，chunk={chunks.shape[0]}，glm100={batch_counts.get('glm100', 0)}，table2_next100={batch_counts.get('table2_next100', 0)}。",
        f"- 原始 GLM proxy：Summary_len mean={helper.fmt(raw['Summary_len_mean'])}，Redundancy_chunk mean={helper.fmt(raw['Redundancy_chunk_mean'])}。",
        f"- GLM200 最接近原文 Table 1 的候选是 `{best_name}`：Summary_len mean={helper.fmt(best['Summary_len_mean'])}，Redundancy_chunk mean={helper.fmt(best['Redundancy_chunk_mean'])}，企业层 Redundancy mean={helper.fmt(best['Redundancy_mean'])}。",
        f"- Panel B：rho={helper.fmt(best['panel_b_rho'])}, p={helper.fmt(best['panel_b_p'])}；低评分组中位数={helper.fmt(best['low_score_red_median'])}，高评分组中位数={helper.fmt(best['high_score_red_median'])}。",
        "- GLM200 的用途是决定是否继续扩到 Table2 471。若接 Table2 后 BHAR/FSales_Growth 仍不转负，应停止把问题继续归咎于摘要模型。",
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
        f"- merged chunk metrics：`{OUT_RUN / f'chunk_metrics_glm4_cot_v3b_len132_tight_{DATE_TAG}.csv'}`",
        f"- no-summary review CSV：`{OUT_RUN / f'chunk_metrics_glm4_cot_v3b_len132_tight_no_summary_text_{DATE_TAG}.csv'}`",
        f"- candidate summary：`{OUT_DIR / f'candidate_summary_{DATE_TAG}.csv'}`",
        f"- best chunk：`{OUT_DIR / f'{best_name}_chunk_metrics_{DATE_TAG}.csv'}`",
        f"- best firm：`{OUT_DIR / f'{best_name}_firm_metrics_{DATE_TAG}.csv'}`",
        "",
    ]
    DOC.write_text("\n".join(doc), encoding="utf-8")


def main() -> None:
    helper = load_helper()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    chunks = load_chunks()
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
