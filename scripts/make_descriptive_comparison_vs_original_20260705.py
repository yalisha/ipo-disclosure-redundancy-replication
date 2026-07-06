#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
OUT_DIR = PROJECT / "results/descriptive_comparison_vs_original_20260705"
DOC_OUT = PROJECT / "docs/00_current/descriptive_comparison_vs_original_20260705.md"

METRICS_JSON = (
    PROJECT
    / "results/summary_len_calibration_full_543_20260704/"
    "metrics_cot_v3b_len132_tight_20260703.json"
)
CHUNK_CSV = (
    PROJECT
    / "results/summary_len_calibration_full_543_20260704/"
    "chunk_metrics_cot_v3b_len132_tight_20260703.csv"
)
TABLE2_PANEL_A_CSV = (
    PROJECT
    / "results/table2_len132_tight_audit_20260705/"
    "panel_a_descriptives_vs_original_20260705.csv"
)

TABLE1_OUT = OUT_DIR / "table1_panel_a_chunk_descriptives_vs_original_20260705.csv"
TABLE2_OUT = OUT_DIR / "table2_panel_a_firm_descriptives_vs_original_20260705.csv"
SUMMARY_OUT = OUT_DIR / "descriptive_gap_summary_20260705.csv"


ORIGINAL_TABLE1_PANEL_A = {
    "Chunk_num": {"N": 8683, "mean": 18.191, "std": 6.983, "p25": 13.000, "median": 16.000, "p75": 22.000},
    "Text_len": {"N": 8683, "mean": 3866.817, "std": 343.868, "p25": 3888.000, "median": 3954.000, "p75": 3985.000},
    "Summary_len": {"N": 8683, "mean": 132.678, "std": 39.683, "p25": 105.000, "median": 130.000, "p75": 158.000},
    "Redundancy_chunk": {"N": 8683, "mean": 32.176, "std": 11.730, "p25": 24.356, "median": 29.739, "p75": 37.037},
}

TABLE2_DISPLAY_ORDER = [
    "lnN_tech",
    "Redundancy",
    "FInvention",
    "BHAR",
    "FSales_Growth",
    "Price_Issue",
    "Price_Day5",
    "RD_Staff",
    "RD_Asset",
    "Size",
    "Lev",
    "ROA",
    "Offerfee",
    "Underwriter",
    "Age",
    "NumIndSeg",
    "NumProdSeg",
    "ScopeLen",
]


def fmt(x: object, digits: int = 3) -> str:
    if pd.isna(x):
        return ""
    return f"{float(x):.{digits}f}"


def md_table(df: pd.DataFrame, cols: list[str], digits: int = 3) -> list[str]:
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df.iterrows():
        vals: list[str] = []
        for col in cols:
            val = row[col]
            if isinstance(val, (float, np.floating)):
                vals.append(fmt(val, digits))
            elif pd.isna(val):
                vals.append("")
            else:
                vals.append(str(val))
        lines.append("| " + " | ".join(vals) + " |")
    return lines


def add_gap_cols(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["N_diff_current_minus_original"] = out["current_N"] - out["original_N"]
    out["mean_diff_current_minus_original"] = out["current_mean"] - out["original_mean"]
    out["mean_pct_diff_vs_original"] = out["mean_diff_current_minus_original"] / out["original_mean"].abs()
    out.loc[out["original_mean"].eq(0), "mean_pct_diff_vs_original"] = np.nan
    out["median_diff_current_minus_original"] = out["current_median"] - out["original_median"]
    return out


def describe_series(s: pd.Series) -> dict[str, float | int]:
    x = pd.to_numeric(s, errors="coerce").dropna()
    return {
        "current_N": int(len(x)),
        "current_mean": x.mean(),
        "current_std": x.std(ddof=1),
        "current_p25": x.quantile(0.25),
        "current_median": x.quantile(0.50),
        "current_p75": x.quantile(0.75),
    }


def make_table1() -> pd.DataFrame:
    metrics = json.loads(METRICS_JSON.read_text(encoding="utf-8"))
    chunks = pd.read_csv(CHUNK_CSV, usecols=["chunk_count"], encoding="utf-8-sig")

    current = {
        "Chunk_num": describe_series(chunks["chunk_count"]),
        "Text_len": {
            "current_N": int(metrics["text_len"]["n"]),
            "current_mean": metrics["text_len"]["mean"],
            "current_std": metrics["text_len"]["std"],
            "current_p25": metrics["text_len"]["p25"],
            "current_median": metrics["text_len"]["median"],
            "current_p75": metrics["text_len"]["p75"],
        },
        "Summary_len": {
            "current_N": int(metrics["summary_len"]["n"]),
            "current_mean": metrics["summary_len"]["mean"],
            "current_std": metrics["summary_len"]["std"],
            "current_p25": metrics["summary_len"]["p25"],
            "current_median": metrics["summary_len"]["median"],
            "current_p75": metrics["summary_len"]["p75"],
        },
        "Redundancy_chunk": {
            "current_N": int(metrics["redundancy_chunk"]["n"]),
            "current_mean": metrics["redundancy_chunk"]["mean"],
            "current_std": metrics["redundancy_chunk"]["std"],
            "current_p25": metrics["redundancy_chunk"]["p25"],
            "current_median": metrics["redundancy_chunk"]["median"],
            "current_p75": metrics["redundancy_chunk"]["p75"],
        },
    }

    rows = []
    for var, orig in ORIGINAL_TABLE1_PANEL_A.items():
        rows.append(
            {
                "variable": var,
                **current[var],
                "original_N": orig["N"],
                "original_mean": orig["mean"],
                "original_std": orig["std"],
                "original_p25": orig["p25"],
                "original_median": orig["median"],
                "original_p75": orig["p75"],
            }
        )
    return add_gap_cols(pd.DataFrame(rows))


def make_table2() -> pd.DataFrame:
    df = pd.read_csv(TABLE2_PANEL_A_CSV, encoding="utf-8-sig")
    out = df.rename(
        columns={
            "available": "current_available",
        }
    )
    out["variable"] = pd.Categorical(out["variable"], TABLE2_DISPLAY_ORDER, ordered=True)
    out = out.sort_values("variable").reset_index(drop=True)
    out["variable"] = out["variable"].astype(str)
    if "N_diff_current_minus_original" not in out.columns:
        out = add_gap_cols(out)
    return out


def gap_summary(table1: pd.DataFrame, table2: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for scope, df, variables in [
        ("table1_chunk", table1, ["Chunk_num", "Text_len", "Summary_len", "Redundancy_chunk"]),
        (
            "table2_firm",
            table2,
            ["lnN_tech", "Redundancy", "FInvention", "BHAR", "FSales_Growth", "RD_Asset", "Underwriter"],
        ),
    ]:
        for var in variables:
            row = df[df["variable"].eq(var)]
            if row.empty:
                continue
            r = row.iloc[0]
            rows.append(
                {
                    "scope": scope,
                    "variable": var,
                    "current_N": r.get("current_N"),
                    "original_N": r.get("original_N"),
                    "N_diff": r.get("N_diff_current_minus_original"),
                    "current_mean": r.get("current_mean"),
                    "original_mean": r.get("original_mean"),
                    "mean_diff": r.get("mean_diff_current_minus_original"),
                    "mean_pct_diff_vs_original": r.get("mean_pct_diff_vs_original"),
                    "current_median": r.get("current_median"),
                    "original_median": r.get("original_median"),
                    "median_diff": r.get("median_diff_current_minus_original"),
                }
            )
    return pd.DataFrame(rows)


def write_doc(table1: pd.DataFrame, table2: pd.DataFrame, summary: pd.DataFrame) -> None:
    table1_view = table1[
        [
            "variable",
            "current_N",
            "original_N",
            "N_diff_current_minus_original",
            "current_mean",
            "original_mean",
            "mean_diff_current_minus_original",
            "mean_pct_diff_vs_original",
            "current_std",
            "original_std",
            "current_median",
            "original_median",
        ]
    ].copy()
    table2_view = table2[
        [
            "variable",
            "current_available",
            "current_N",
            "original_N",
            "N_diff_current_minus_original",
            "current_mean",
            "original_mean",
            "mean_diff_current_minus_original",
            "mean_pct_diff_vs_original",
            "current_median",
            "original_median",
        ]
    ].copy()

    key_summary = summary[
        summary["variable"].isin(
            [
                "Text_len",
                "Summary_len",
                "Redundancy_chunk",
                "lnN_tech",
                "Redundancy",
                "FInvention",
                "BHAR",
                "FSales_Growth",
                "Underwriter",
            ]
        )
    ].copy()

    lines = [
        "# 与原文描述性统计对比",
        "",
        "日期：2026-07-05",
        "",
        "## 结论",
        "",
        "- X 的核心量级已经接近原文：企业层 `Redundancy` 当前均值 29.374，原文 29.074；chunk 层 `Summary_len` 当前 128.253，原文 132.678；chunk 层 `Redundancy_chunk` 当前 30.708，原文 32.176。",
        "- 样本和切块数量仍不同：原文 552 家、8683 个 chunk；当前 543 家、7028 个 chunk。chunk 层加权的 `Chunk_num` 当前 14.054，原文 18.191，说明切块/文本范围仍不是完全同口径。",
        "- `lnN_tech` 当前均值 10.745，原文 10.962，低约 0.217；这比 Redundancy 的差距更值得查，指向原始文本长度单位或章节抽取边界。",
        "- 三个 outcome 的均值没有严重崩：`FInvention` 接近原文，`BHAR` 略更低，`FSales_Growth` 当前 0.409 低于原文 0.530。",
        "- controls 的差距最大：`Underwriter` 当前 0.009，原文 0.574；`NumIndSeg`、`NumProdSeg`、`ScopeLen` 当前缺失。因此 Table 2 复刻失败不能优先归咎于 X。",
        "",
        "## 关键差距摘要",
        "",
        *md_table(
            key_summary,
            [
                "scope",
                "variable",
                "current_N",
                "original_N",
                "N_diff",
                "current_mean",
                "original_mean",
                "mean_diff",
                "mean_pct_diff_vs_original",
                "current_median",
                "original_median",
            ],
            digits=3,
        ),
        "",
        "## Table 1 Panel A：chunk 层描述性统计",
        "",
        *md_table(table1_view, list(table1_view.columns), digits=3),
        "",
        "读法：`Summary_len` 与 `Redundancy_chunk` 已贴近原文，但 `Chunk_num` 明显偏低；这意味着我们的摘要长度校准成功了，剩下的 X 差异更多来自样本/章节抽取/切块边界，而不是 prompt 长度本身。",
        "",
        "## Table 2 Panel A：firm 层描述性统计",
        "",
        *md_table(table2_view, list(table2_view.columns), digits=3),
        "",
        "读法：`Redundancy`、`Size`、`Lev`、`ROA`、`Offerfee`、`Age` 都比较接近；`Underwriter` 和 paper-only controls 是最明显的数据缺口。`RD_Asset` 当前低于原文，`FSales_Growth` 也偏低，后续机制/经济后果回归需要先校对这些变量。",
        "",
        "## 输出文件",
        "",
        f"- Table 1 chunk 对比：`{TABLE1_OUT}`",
        f"- Table 2 firm 对比：`{TABLE2_OUT}`",
        f"- gap summary：`{SUMMARY_OUT}`",
        "",
    ]
    DOC_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    table1 = make_table1()
    table2 = make_table2()
    summary = gap_summary(table1, table2)

    table1.to_csv(TABLE1_OUT, index=False, encoding="utf-8-sig")
    table2.to_csv(TABLE2_OUT, index=False, encoding="utf-8-sig")
    summary.to_csv(SUMMARY_OUT, index=False, encoding="utf-8-sig")
    write_doc(table1, table2, summary)

    print(f"table1={TABLE1_OUT}")
    print(f"table2={TABLE2_OUT}")
    print(f"summary={SUMMARY_OUT}")
    print(f"doc={DOC_OUT}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
