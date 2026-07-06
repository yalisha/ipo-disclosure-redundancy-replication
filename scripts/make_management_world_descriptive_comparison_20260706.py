#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
MASTER_IN = (
    PROJECT
    / "results/table2_listing_year_segment_controls_20260706/"
    "table2_listing_year_segment_controls_master_20260706.csv"
)
RUN_DIR = PROJECT / "results/descriptive_stats_management_world_20260706"
DOC_OUT = PROJECT / "docs/00_current/管理世界式_主要变量描述性统计对比_20260706.md"
CSV_OUT = RUN_DIR / "management_world_descriptive_comparison_20260706.csv"
JSON_OUT = RUN_DIR / "management_world_descriptive_comparison_20260706.json"
ORIGINAL_PANEL_A = {
    "lnN_tech": {"N": 552, "mean": 10.962, "std": 0.350, "p25": 10.714, "median": 10.910, "p75": 11.185},
    "Redundancy": {"N": 552, "mean": 29.074, "std": 2.630, "p25": 27.402, "median": 28.910, "p75": 30.795},
    "FInvention": {"N": 471, "mean": 2.282, "std": 1.200, "p25": 1.386, "median": 2.197, "p75": 2.890},
    "BHAR": {"N": 471, "mean": -0.036, "std": 0.514, "p25": -0.385, "median": -0.170, "p75": 0.162},
    "FSales_Growth": {"N": 471, "mean": 0.530, "std": 1.522, "p25": -0.008, "median": 0.180, "p75": 0.523},
    "RD_Staff": {"N": 552, "mean": 0.305, "std": 0.194, "p25": 0.157, "median": 0.240, "p75": 0.411},
    "RD_Asset": {"N": 552, "mean": 0.105, "std": 0.100, "p25": 0.046, "median": 0.073, "p75": 0.125},
    "Size": {"N": 552, "mean": 20.741, "std": 0.990, "p25": 20.064, "median": 20.533, "p75": 21.189},
    "Lev": {"N": 552, "mean": 0.356, "std": 0.183, "p25": 0.207, "median": 0.334, "p75": 0.476},
    "ROA": {"N": 552, "mean": 0.094, "std": 0.145, "p25": 0.058, "median": 0.100, "p75": 0.157},
    "Offerfee": {"N": 552, "mean": 18.325, "std": 0.483, "p25": 17.965, "median": 18.270, "p75": 18.618},
    "Underwriter": {"N": 552, "mean": 0.574, "std": 0.495, "p25": 0.000, "median": 1.000, "p75": 1.000},
    "Age": {"N": 552, "mean": 2.601, "std": 0.408, "p25": 2.350, "median": 2.639, "p75": 2.890},
    "NumIndSeg": {"N": 552, "mean": 0.854, "std": 0.361, "p25": 0.693, "median": 0.693, "p75": 1.099},
    "NumProdSeg": {"N": 552, "mean": 1.475, "std": 0.376, "p25": 1.386, "median": 1.609, "p75": 1.609},
    "ScopeLen": {"N": 552, "mean": 5.671, "std": 0.854, "p25": 5.159, "median": 5.762, "p75": 6.276},
}


PANELS = [
    (
        "Panel A 因变量",
        [
            ("FInvention", "未来发明专利", "上市后创新产出，按当前 master 口径"),
            ("BHAR", "买入持有异常收益", "上市后市场表现，按当前 master 口径"),
            ("FSales_Growth", "未来销售增长", "上市后经营增长，按当前 master 口径"),
        ],
    ),
    (
        "Panel B 核心自变量",
        [
            ("Redundancy", "信息披露冗余度", "dewrap_join + cot_v3b_len132_tight + Summary_len_proxy 主口径"),
        ],
    ),
    (
        "Panel C 控制变量",
        [
            ("lnN_tech", "技术文本长度", "业务与技术文本长度取对数"),
            ("RD_Staff", "研发人员占比", "PT_LCRDSPENDING，listing_year-1，Source=IPO 优先"),
            ("RD_Asset", "研发资产强度", "当前 master 既有 CSMAR 口径"),
            ("Size", "公司规模", "上市前一年总资产取对数"),
            ("Lev", "资产负债率", "上市前一年总负债/总资产"),
            ("ROA", "资产收益率", "上市前一年净利润/总资产"),
            ("Offerfee", "发行费用", "IPO 发行费用取对数"),
            ("Underwriter", "承销商声誉", "IPO_Ipobasic.Sponsfm，同年 IPO 募资额 Top10"),
            ("Age", "公司年龄", "上市时公司年龄取对数"),
            ("NumIndSeg", "业务/行业分部数", "FN_Fn048，listing_year，主营业务收入优先、营业收入补缺，ln(1+count)"),
            ("NumProdSeg", "产品分部数", "FN_Fn048，listing_year，主营业务收入优先、营业收入补缺，ln(1+count)"),
            ("ScopeLen", "经营范围长度", "STK_LISTEDCOINFOANL.BusinessScope 清洗后 UTF-8 字节长度取对数"),
        ],
    ),
]


def fmt(x: object, digits: int = 3) -> str:
    if x is None or pd.isna(x):
        return ""
    return f"{float(x):.{digits}f}"


def describe(series: pd.Series) -> dict:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return {
            "current_N": 0,
            "current_mean": np.nan,
            "current_std": np.nan,
            "current_p25": np.nan,
            "current_median": np.nan,
            "current_p75": np.nan,
        }
    return {
        "current_N": int(len(s)),
        "current_mean": float(s.mean()),
        "current_std": float(s.std(ddof=1)),
        "current_p25": float(s.quantile(0.25)),
        "current_median": float(s.median()),
        "current_p75": float(s.quantile(0.75)),
    }


def build_table(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for panel, items in PANELS:
        for var, label, note in items:
            cur = describe(df[var]) if var in df.columns else describe(pd.Series(dtype=float))
            orig = ORIGINAL_PANEL_A.get(var, {})
            rows.append(
                {
                    "panel": panel,
                    "variable": var,
                    "label": label,
                    "current_N": cur["current_N"],
                    "current_mean": cur["current_mean"],
                    "current_std": cur["current_std"],
                    "current_p25": cur["current_p25"],
                    "current_median": cur["current_median"],
                    "current_p75": cur["current_p75"],
                    "original_N": orig.get("N", np.nan),
                    "original_mean": orig.get("mean", np.nan),
                    "original_std": orig.get("std", np.nan),
                    "original_p25": orig.get("p25", np.nan),
                    "original_median": orig.get("median", np.nan),
                    "original_p75": orig.get("p75", np.nan),
                    "mean_diff": cur["current_mean"] - orig.get("mean", np.nan)
                    if cur["current_N"] and orig
                    else np.nan,
                    "note": note,
                }
            )
    return pd.DataFrame(rows)


def md_table(rows: pd.DataFrame) -> list[str]:
    cols = [
        ("变量", "variable"),
        ("变量含义", "label"),
        ("N", "current_N"),
        ("均值", "current_mean"),
        ("标准差", "current_std"),
        ("P25", "current_p25"),
        ("中位数", "current_median"),
        ("P75", "current_p75"),
        ("原文N", "original_N"),
        ("原文均值", "original_mean"),
        ("原文中位数", "original_median"),
        ("均值差", "mean_diff"),
    ]
    lines = ["| " + " | ".join(c[0] for c in cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in rows.iterrows():
        vals = []
        for _, key in cols:
            val = row[key]
            if key in {"variable", "label"}:
                vals.append(str(val))
            elif key in {"current_N", "original_N"}:
                vals.append("" if pd.isna(val) else str(int(val)))
            else:
                vals.append(fmt(val))
        lines.append("| " + " | ".join(vals) + " |")
    return lines


def write_markdown(table: pd.DataFrame) -> None:
    lines: list[str] = [
        "# 主要变量描述性统计对比",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "表 1 报告当前复现样本与原文样本的主要变量描述性统计。为便于与中文管理学期刊常见呈现方式保持一致，表内按因变量、核心自变量和控制变量分为三个 Panel，并报告样本量、均值、标准差、四分位数和原文均值/中位数。",
        "",
    ]
    for panel, _ in PANELS:
        sub = table[table["panel"].eq(panel)].copy()
        lines.extend([f"## {panel}", "", *md_table(sub), ""])
    lines.extend(
        [
            "注：当前样本使用 `dewrap_join + cot_v3b_len132_tight + Summary_len_proxy` 作为冗余度主口径；`NumIndSeg` 与 `NumProdSeg` 为上市当年 `FN_Fn048` 年报附注替代口径，主营业务收入分部优先，缺失时以营业收入分部补缺，并取 `ln(1+count)`；`RD_Staff` 使用 IPO 来源优先的 `PT_LCRDSPENDING` 上市前一年口径。原文统计值来自原文 Panel A/附录口径；均值差为当前均值减原文均值。",
            "",
        ]
    )
    DOC_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(MASTER_IN, dtype={"sec_code": str, "code": str}, encoding="utf-8-sig")
    table = build_table(df)
    table.to_csv(CSV_OUT, index=False, encoding="utf-8-sig")
    JSON_OUT.write_text(json.dumps(table.to_dict(orient="records"), ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(table)
    print(f"csv={CSV_OUT}")
    print(f"json={JSON_OUT}")
    print(f"doc={DOC_OUT}")
    print(table[["panel", "variable", "current_N", "current_mean", "original_mean", "mean_diff"]].to_string(index=False))


if __name__ == "__main__":
    main()
