#!/usr/bin/env python3
from __future__ import annotations

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
OUT_DIR = PROJECT / "results/descriptive_comparison_vs_original_20260706"
DOC_OUT = PROJECT / "docs/00_current/descriptive_comparison_vs_original_20260706.md"

CHUNK_METRICS = (
    PROJECT
    / "results/glm4_dewrap_join_full543_20260705/"
    "chunk_metrics_glm4_cot_v3b_len132_tight_20260705.csv"
)
TABLE2_PANEL_A = (
    PROJECT
    / "results/table2_glm4_dewrap_full543_audit_20260706/"
    "panel_a_descriptives_vs_original_20260706.csv"
)

TABLE1_OUT = OUT_DIR / "table1_panel_a_chunk_descriptives_vs_original_20260706.csv"
TABLE2_XY_OUT = OUT_DIR / "table2_xy_descriptives_vs_original_20260706.csv"
TABLE2_CONTROLS_OUT = OUT_DIR / "table2_controls_descriptives_vs_original_20260706.csv"
SUMMARY_OUT = OUT_DIR / "descriptive_gap_summary_20260706.csv"


ORIGINAL_TABLE1_PANEL_A = {
    "Chunk_num": {"N": 8683, "mean": 18.191, "std": 6.983, "p25": 13.000, "median": 16.000, "p75": 22.000},
    "Text_len": {"N": 8683, "mean": 3866.817, "std": 343.868, "p25": 3888.000, "median": 3954.000, "p75": 3985.000},
    "Summary_len": {"N": 8683, "mean": 132.678, "std": 39.683, "p25": 105.000, "median": 130.000, "p75": 158.000},
    "Redundancy_chunk": {"N": 8683, "mean": 32.176, "std": 11.730, "p25": 24.356, "median": 29.739, "p75": 37.037},
}

TABLE2_XY_ORDER = ["lnN_tech", "Redundancy", "FInvention", "BHAR", "FSales_Growth"]
TABLE2_CONTROL_ORDER = [
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


def describe(s: pd.Series) -> dict[str, float | int]:
    x = pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    return {
        "current_N": int(len(x)),
        "current_mean": float(x.mean()) if len(x) else np.nan,
        "current_std": float(x.std(ddof=1)) if len(x) > 1 else np.nan,
        "current_p25": float(x.quantile(0.25)) if len(x) else np.nan,
        "current_median": float(x.median()) if len(x) else np.nan,
        "current_p75": float(x.quantile(0.75)) if len(x) else np.nan,
    }


def add_gap_cols(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["N_diff_current_minus_original"] = out["current_N"] - out["original_N"]
    out["mean_diff_current_minus_original"] = out["current_mean"] - out["original_mean"]
    out["mean_pct_diff_vs_original"] = out["mean_diff_current_minus_original"] / out["original_mean"].abs()
    out.loc[pd.to_numeric(out["original_mean"], errors="coerce").eq(0), "mean_pct_diff_vs_original"] = np.nan
    out["median_diff_current_minus_original"] = out["current_median"] - out["original_median"]
    return out


def make_table1() -> pd.DataFrame:
    chunks = pd.read_csv(CHUNK_METRICS, encoding="utf-8-sig")
    current = {
        "Chunk_num": describe(chunks["Chunk_num"]),
        "Text_len": describe(chunks["Text_len"]),
        "Summary_len": describe(chunks["Summary_len_proxy"]),
        "Redundancy_chunk": describe(chunks["Redundancy_chunk_proxy"]),
    }
    rows: list[dict[str, object]] = []
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


def load_table2_panel_a() -> pd.DataFrame:
    df = pd.read_csv(TABLE2_PANEL_A, encoding="utf-8-sig")
    df = df.rename(columns={"available": "current_available"})
    if "N_diff_current_minus_original" not in df.columns:
        df = add_gap_cols(df)
    return df


def ordered_subset(df: pd.DataFrame, order: list[str]) -> pd.DataFrame:
    out = df[df["variable"].isin(order)].copy()
    out["variable"] = pd.Categorical(out["variable"], order, ordered=True)
    out = out.sort_values("variable").reset_index(drop=True)
    out["variable"] = out["variable"].astype(str)
    return out


def make_summary(table1: pd.DataFrame, table2_xy: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for scope, df, variables in [
        ("table1_chunk", table1, ["Chunk_num", "Text_len", "Summary_len", "Redundancy_chunk"]),
        ("table2_xy", table2_xy, ["lnN_tech", "Redundancy", "FInvention", "BHAR", "FSales_Growth"]),
    ]:
        for var in variables:
            r = df[df["variable"].eq(var)].iloc[0]
            rows.append(
                {
                    "scope": scope,
                    "variable": var,
                    "current_N": r["current_N"],
                    "original_N": r["original_N"],
                    "N_diff": r["N_diff_current_minus_original"],
                    "current_mean": r["current_mean"],
                    "original_mean": r["original_mean"],
                    "mean_diff": r["mean_diff_current_minus_original"],
                    "mean_pct_diff_vs_original": r["mean_pct_diff_vs_original"],
                    "current_median": r["current_median"],
                    "original_median": r["original_median"],
                    "median_diff": r["median_diff_current_minus_original"],
                }
            )
    return pd.DataFrame(rows)


def compact_view(df: pd.DataFrame, include_available: bool) -> pd.DataFrame:
    cols = [
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
    if include_available:
        cols.insert(1, "current_available")
    return df[cols].copy()


def write_doc(table1: pd.DataFrame, table2_xy: pd.DataFrame, table2_controls: pd.DataFrame, summary: pd.DataFrame) -> None:
    table1_view = compact_view(table1, include_available=False)
    xy_view = compact_view(table2_xy, include_available=True)
    controls_view = compact_view(table2_controls, include_available=True)
    key_view = summary.copy()

    lines = [
        "# 当前 X/Y 描述性统计与原文对比",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 结论",
        "",
        "- X 已经基本回到原文量级：chunk 数 8706 vs 原文 8683，`Summary_len` 130.975 vs 132.678，`Redundancy_chunk` 30.468 vs 32.176。",
        "- 企业层 X 也贴近原文：`lnN_tech` 10.966 vs 10.962，`Redundancy` 28.944 vs 29.074。",
        "- Y 的描述性统计没有明显崩：`FInvention` 均值 2.325 vs 原文 2.282；`BHAR` -0.062 vs -0.036；`FSales_Growth` 0.409 vs 0.530。",
        "- 当前最明显的描述性缺口不在 X/Y 本身，而在 controls：`Underwriter` 0.009 vs 原文 0.574，`NumIndSeg / NumProdSeg / ScopeLen` 仍缺失。",
        "",
        "## 关键差距摘要",
        "",
        *md_table(
            key_view,
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
        "## X：chunk 层 Table 1 Panel A",
        "",
        *md_table(table1_view, list(table1_view.columns), digits=3),
        "",
        "读法：`Chunk_num`、`Text_len`、`Summary_len`、`Redundancy_chunk` 都已经和原文接近。这里的 `Summary_len` 和 `Redundancy_chunk` 使用当前主口径，也就是摘要 proxy 分母。",
        "",
        "## X/Y：firm 层 Table 2 Panel A",
        "",
        *md_table(xy_view, list(xy_view.columns), digits=3),
        "",
        "读法：`lnN_tech` 与 `Redundancy` 已经比旧口径明显更贴近原文；三条 Y 的均值/中位数也不离谱。Table 2 回归没整体复刻，不能优先解释为 X/Y 描述性统计崩坏。",
        "",
        "## 参考：关键 controls 描述性缺口",
        "",
        *md_table(controls_view, list(controls_view.columns), digits=3),
        "",
        "读法：controls 里 `Underwriter` 是最大硬伤，三项原文 paper-only controls 仍不可用。这比 X/Y 描述性统计更像当前 Table 2 失败的直接数据缺口。",
        "",
        "## 输出文件",
        "",
        f"- chunk X 对比：`{TABLE1_OUT}`",
        f"- firm X/Y 对比：`{TABLE2_XY_OUT}`",
        f"- controls 对比：`{TABLE2_CONTROLS_OUT}`",
        f"- gap summary：`{SUMMARY_OUT}`",
        "",
    ]
    DOC_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    table1 = make_table1()
    table2 = load_table2_panel_a()
    table2_xy = ordered_subset(table2, TABLE2_XY_ORDER)
    table2_controls = ordered_subset(table2, TABLE2_CONTROL_ORDER)
    summary = make_summary(table1, table2_xy)

    table1.to_csv(TABLE1_OUT, index=False, encoding="utf-8-sig")
    table2_xy.to_csv(TABLE2_XY_OUT, index=False, encoding="utf-8-sig")
    table2_controls.to_csv(TABLE2_CONTROLS_OUT, index=False, encoding="utf-8-sig")
    summary.to_csv(SUMMARY_OUT, index=False, encoding="utf-8-sig")
    write_doc(table1, table2_xy, table2_controls, summary)

    print(f"doc={DOC_OUT}")
    print(f"table1={TABLE1_OUT}")
    print(f"table2_xy={TABLE2_XY_OUT}")
    print(f"controls={TABLE2_CONTROLS_OUT}")
    print(f"summary={SUMMARY_OUT}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
