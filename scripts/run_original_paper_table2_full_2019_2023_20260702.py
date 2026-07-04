#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import run_original_paper_table2_probe_20260702 as base


PROJECT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
DEFAULT_REDUNDANCY = (
    PROJECT
    / "results/star_token_proxy_full_2019_2023_20260702/"
    "ipo_redundancy_firm_level_cot_v3b_scoregate_targeted_full_2019_2023.csv"
)
DEFAULT_OUTCOME = (
    PROJECT
    / "results/outcome_variable_probe_csmar_patent_20260702/"
    "outcome_variables_star_firm_level_csmar_patent_20260702.csv"
)
DEFAULT_RUN_DIR = PROJECT / "results/original_paper_table2_probe_full_2019_2023_csmar_patent_20260702"
DEFAULT_DOC = PROJECT / "docs/表2扩样至2019-2023结果_20260702.md"


def fmt(x: object, digits: int = 4) -> str:
    if pd.isna(x):
        return ""
    return f"{float(x):.{digits}f}"


def write_full_doc(master: pd.DataFrame, regs: pd.DataFrame, desc: pd.DataFrame, doc_out: Path, red_path: Path) -> None:
    by_year = (
        master.groupby("listing_year")["code"]
        .nunique()
        .dropna()
        .rename("N")
        .reset_index()
        .sort_values("listing_year")
    )
    by_year_rows = [f"| {int(r.listing_year)} | {int(r.N)} |" for r in by_year.itertuples()]

    desc_rows = []
    for var in ["Redundancy", "FInvention", "BHAR", "FSales_Growth", "RD_Asset", "Size", "Lev", "ROA", "Offerfee", "Age"]:
        row = desc[desc["variable"].eq(var)]
        if row.empty:
            continue
        r = row.iloc[0]
        desc_rows.append(
            f"| {var} | {int(r['N'])} | {fmt(r['mean'], 3)} | {fmt(r['std'], 3)} | "
            f"{fmt(r['p25'], 3)} | {fmt(r['median'], 3)} | {fmt(r['p75'], 3)} |"
        )

    reg_rows = []
    for dep in ["FInvention", "BHAR", "FSales_Growth"]:
        for model in ["simple", "fe_text", "controls_fe"]:
            row = regs[(regs["dep_var"].eq(dep)) & (regs["model"].eq(model))]
            if row.empty:
                continue
            r = row.iloc[0]
            reg_rows.append(
                f"| {dep} | {model} | {int(r['N'])} | {fmt(r['coef'])} | "
                f"{fmt(r['t_HC1'], 2)} | {fmt(r['p_HC1'], 3)} | {fmt(r['adj_r2'], 3)} |"
            )

    original_rows = []
    for dep, orig in base.ORIGINAL_PANEL_B.items():
        row = regs[(regs["dep_var"].eq(dep)) & (regs["model"].eq("controls_fe"))]
        if row.empty:
            continue
        r = row.iloc[0]
        original_rows.append(
            f"| {dep} | {int(r['N'])} | {fmt(r['coef'])} | {fmt(r['t_HC1'], 2)} | "
            f"{fmt(r['p_HC1'], 3)} | {orig['coef']:.4f} | {orig['t']:.2f} | {orig['N']} |"
        )

    pricing_rows = []
    for dep in ["Price_Issue_pb_indadj", "Price_Day5_pb_indadj"]:
        row = regs[(regs["dep_var"].eq(dep)) & (regs["target_var"].eq("RD_Low_x_Redundancy_High"))]
        if row.empty:
            continue
        r = row.iloc[0]
        pricing_rows.append(
            f"| {dep} | {int(r['N'])} | {fmt(r['coef'])} | {fmt(r['t_HC1'], 2)} | "
            f"{fmt(r['p_HC1'], 3)} | {fmt(r['adj_r2'], 3)} |"
        )

    sample_loss = [
        ("Redundancy firms", len(master)),
        ("FInvention nonmissing", int(master["FInvention"].notna().sum())),
        ("BHAR nonmissing", int(master["BHAR"].notna().sum())),
        ("FSales_Growth nonmissing", int(master["FSales_Growth"].notna().sum())),
        (
            "complete controls for FInvention main spec",
            int(
                master[
                    [
                        "FInvention",
                        "Redundancy",
                        "lnN_tech",
                        "Size",
                        "Lev",
                        "ROA",
                        "Offerfee",
                        "Underwriter",
                        "Age",
                        "industry_fe",
                        "listing_year_fe",
                    ]
                ]
                .dropna()
                .shape[0]
            ),
        ),
    ]

    lines = [
        "# 表 2 扩样至 2019-2023 结果",
        "",
        "日期：2026-07-02",
        "",
        "## 口径",
        "",
        f"- Redundancy：`{red_path}`",
        f"- Outcome：`{DEFAULT_OUTCOME}`",
        "- FInvention：CSMAR `PT_LCDOMFORAPPLY`，`StateTypeCode=1`，`ApplyTypeCode=S5202`，国内外合计，`ln(1 + Invention_{listing_year+1})`。",
        "- 标准误：HC1 robust。",
        "",
        "## 样本",
        "",
        "| 步骤 | N |",
        "|---|---:|",
        *[f"| {k} | {v} |" for k, v in sample_loss],
        "",
        "按上市年分布：",
        "",
        "| 年份 | N |",
        "|---:|---:|",
        *by_year_rows,
        "",
        "## 描述统计",
        "",
        "| 变量 | N | 均值 | 标准差 | p25 | 中位数 | p75 |",
        "|---|---:|---:|---:|---:|---:|---:|",
        *desc_rows,
        "",
        "## 原文表 2 Panel B 对照",
        "",
        "| 被解释变量 | N | 当前 coef | 当前 t | 当前 p | 原文 coef | 原文 t | 原文 N |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
        *original_rows,
        "",
        "## 三规格结果",
        "",
        "| 被解释变量 | 规格 | N | coef | t | p | Adj.R2 |",
        "|---|---|---:|---:|---:|---:|---:|",
        *reg_rows,
        "",
        "## 定价交互 smoke test",
        "",
        "| 被解释变量 | N | RD_Low_x_Redundancy_High coef | t | p | Adj.R2 |",
        "|---|---:|---:|---:|---:|---:|",
        *pricing_rows,
        "",
        "## 输出文件",
        "",
        f"- master：`{base.MASTER_OUT}`",
        f"- regressions：`{base.REG_OUT}`",
        f"- descriptives：`{base.DESC_OUT}`",
        "",
    ]
    doc_out.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--redun-path", type=Path, default=DEFAULT_REDUNDANCY)
    parser.add_argument("--outcome-path", type=Path, default=DEFAULT_OUTCOME)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--doc-out", type=Path, default=DEFAULT_DOC)
    args = parser.parse_args()

    if not args.redun_path.exists():
        raise SystemExit(f"Missing final redundancy file: {args.redun_path}")
    if not args.outcome_path.exists():
        raise SystemExit(f"Missing outcome file: {args.outcome_path}")

    args.run_dir.mkdir(parents=True, exist_ok=True)
    base.RUN_DIR = args.run_dir
    base.REDUNDANCY_PATH = args.redun_path
    base.OUTCOME_PATH = args.outcome_path
    base.MASTER_OUT = args.run_dir / "original_paper_table2_probe_master_full_2019_2023_csmar_patent_20260702.csv"
    base.REG_OUT = args.run_dir / "original_paper_table2_probe_regressions_full_2019_2023_csmar_patent_20260702.csv"
    base.DESC_OUT = args.run_dir / "original_paper_table2_probe_descriptives_full_2019_2023_csmar_patent_20260702.csv"

    master = base.build_master()
    master["RD_Asset_w1p"] = base.winsorize(master["RD_Asset"])
    master.to_csv(base.MASTER_OUT, index=False)

    desc = base.descriptives(master)
    desc.to_csv(base.DESC_OUT, index=False)

    regs = base.run_regressions(master)
    regs.to_csv(base.REG_OUT, index=False)

    write_full_doc(master, regs, desc, args.doc_out, args.redun_path)
    print(f"master={base.MASTER_OUT}")
    print(f"regressions={base.REG_OUT}")
    print(f"descriptives={base.DESC_OUT}")
    print(f"doc={args.doc_out}")
    print(regs[["model", "dep_var", "target_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"]].to_string(index=False))


if __name__ == "__main__":
    main()
