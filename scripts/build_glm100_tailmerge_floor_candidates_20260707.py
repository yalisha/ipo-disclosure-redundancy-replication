#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
HELPER = ROOT / "scripts/build_glm_next50_tailmerge_floor_candidates_20260707.py"
OUT_RUN = ROOT / "results/siliconflow_glm4_32b_glm100_merged_20260707"
OUT_DIR = ROOT / "results/glm100_tailmerge_floor_candidates_20260707"
DOC = ROOT / "docs/00_current/siliconflow_glm4_32b_glm100_20260707.md"

SOURCES = [
    (
        "pilot50",
        ROOT / "results/siliconflow_glm4_32b_pilot50_20260707/chunk_metrics_glm4_cot_v3b_len132_tight_20260705.csv",
    ),
    (
        "table2_next50",
        ROOT / "results/siliconflow_glm4_32b_table2_next50_merged_20260707/chunk_metrics_glm4_cot_v3b_len132_tight_20260707.csv",
    ),
]


def load_helper():
    spec = importlib.util.spec_from_file_location("glm_next50_helper", HELPER)
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
    chunks = pd.concat(parts, ignore_index=True)
    chunks = chunks.drop_duplicates("custom_id", keep="last")
    OUT_RUN.mkdir(parents=True, exist_ok=True)
    chunks.to_csv(OUT_RUN / "chunk_metrics_glm4_cot_v3b_len132_tight_20260707.csv", index=False, encoding="utf-8-sig")
    chunks[[c for c in chunks.columns if c != "summary_text"]].to_csv(
        OUT_RUN / "chunk_metrics_glm4_cot_v3b_len132_tight_no_summary_text_20260707.csv",
        index=False,
        encoding="utf-8-sig",
    )
    return chunks


def md_best_vs_paper(helper, row: pd.Series) -> list[str]:
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
    top = summary.head(8)
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
    firms = (
        chunks[["sec_code", "sec_name", "source_glm_batch"]]
        .drop_duplicates()
        .sort_values(["source_glm_batch", "sec_code"])
    )
    batch_counts = firms.groupby("source_glm_batch")["sec_code"].nunique().to_dict()
    doc = [
        "# SiliconFlow GLM-4-32B GLM100 合并测度诊断",
        "",
        "日期：2026-07-07",
        "",
        "## 结论",
        "",
        f"- 合并样本：firm={chunks['sec_code'].nunique()}，chunk={chunks.shape[0]}，pilot50={batch_counts.get('pilot50', 0)}，table2_next50={batch_counts.get('table2_next50', 0)}。",
        f"- 原始 GLM proxy 口径：Summary_len mean={helper.fmt(raw['Summary_len_mean'])}，Redundancy_chunk mean={helper.fmt(raw['Redundancy_chunk_mean'])}。",
        f"- GLM100 最接近原文 Table 1 的候选是 `{best_name}`：Summary_len mean={helper.fmt(best['Summary_len_mean'])}，Redundancy_chunk mean={helper.fmt(best['Redundancy_chunk_mean'])}，企业层 Redundancy mean={helper.fmt(best['Redundancy_mean'])}。",
        f"- Panel B 方向仍成立但很弱：rho={helper.fmt(best['panel_b_rho'])}, p={helper.fmt(best['panel_b_p'])}；这不是效度最终通过，只说明低相关评分与高冗余的机械关系未消失。",
        "- 因此目前最清楚的判断是：GLM 摘要显著改善 Table 1 描述统计贴近度，但必须接 Table 2 才能裁决能否复刻论文主效应。",
        "",
        "## 候选口径排序",
        "",
        *helper.md_table(top[compare_cols], compare_cols, None),
        "",
        "## 最佳候选 vs 原文",
        "",
        *md_best_vs_paper(helper, best),
        "",
        "## 输出文件",
        "",
        f"- merged chunk metrics：`{OUT_RUN / 'chunk_metrics_glm4_cot_v3b_len132_tight_20260707.csv'}`",
        f"- no-summary review CSV：`{OUT_RUN / 'chunk_metrics_glm4_cot_v3b_len132_tight_no_summary_text_20260707.csv'}`",
        f"- candidate summary：`{OUT_DIR / 'candidate_summary_20260707.csv'}`",
        f"- best chunk：`{OUT_DIR / f'{best_name}_chunk_metrics_20260707.csv'}`",
        f"- best firm：`{OUT_DIR / f'{best_name}_firm_metrics_20260707.csv'}`",
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
        c.to_csv(OUT_DIR / f"{candidate['name']}_chunk_metrics_20260707.csv", index=False, encoding="utf-8-sig")
        f.to_csv(OUT_DIR / f"{candidate['name']}_firm_metrics_20260707.csv", index=False, encoding="utf-8-sig")
        rows.append(helper.evaluate_candidate(c, f, candidate))
    summary = pd.DataFrame(rows).sort_values("loss_all")
    summary.to_csv(OUT_DIR / "candidate_summary_20260707.csv", index=False, encoding="utf-8-sig")
    write_doc(helper, chunks, summary)
    print({"doc": str(DOC), "summary": str(OUT_DIR / "candidate_summary_20260707.csv"), "best": str(summary.iloc[0]["name"])})


if __name__ == "__main__":
    main()
