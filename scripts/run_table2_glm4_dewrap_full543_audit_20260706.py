#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
BASE_AUDIT_SCRIPT = PROJECT / "scripts/run_table2_len132_tight_audit_20260705.py"
BASE_MASTER_IN = (
    PROJECT
    / "results/table2_len132_tight_audit_20260705/table2_len132_tight_master_20260705.csv"
)
FIRM_X_IN = (
    PROJECT
    / "results/glm4_dewrap_join_full543_20260705/firm_metrics_glm4_cot_v3b_len132_tight_20260705.csv"
)
RUN_DIR = PROJECT / "results/table2_glm4_dewrap_full543_audit_20260706"
DOC_OUT = PROJECT / "docs/00_current/table2_glm4_dewrap_full543_audit_20260706.md"

MASTER_OUT = RUN_DIR / "table2_glm4_dewrap_full543_master_20260706.csv"
DESC_OUT = RUN_DIR / "panel_a_descriptives_vs_original_20260706.csv"
REG_OUT = RUN_DIR / "table2_glm4_dewrap_full543_regressions_20260706.csv"
WATERFALL_OUT = RUN_DIR / "table2_glm4_dewrap_full543_sample_waterfall_20260706.csv"
MISSING_CONTROLS_OUT = RUN_DIR / "table2_glm4_dewrap_full543_missing_paper_controls_20260706.csv"


def load_base_module():
    spec = importlib.util.spec_from_file_location("table2_len132_base", BASE_AUDIT_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {BASE_AUDIT_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_base_module()

ORIGINAL_PANEL_A = base.ORIGINAL_PANEL_A
ORIGINAL_PANEL_B = base.ORIGINAL_PANEL_B
OUTCOMES = base.OUTCOMES
CURRENT_CONTROL_VARS = base.CURRENT_CONTROL_VARS
PAPER_ONLY_CONTROL_VARS = base.PAPER_ONLY_CONTROL_VARS
FE_VARS = base.FE_VARS


def z6(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)


def load_master() -> pd.DataFrame:
    df = pd.read_csv(BASE_MASTER_IN, dtype={"sec_code": str, "code": str}, encoding="utf-8-sig")
    df["sec_code"] = z6(df["sec_code"])
    df["code"] = z6(df["code"])

    # Preserve the previous len132_tight X for direct comparison.
    rename_map = {}
    if "Redundancy" in df.columns:
        rename_map["Redundancy"] = "Redundancy_prior_len132_tight"
    if "lnN_tech" in df.columns:
        rename_map["lnN_tech"] = "lnN_tech_prior_len132_tight"
    df = df.rename(columns=rename_map)

    x = pd.read_csv(FIRM_X_IN, dtype={"sec_code": str}, encoding="utf-8-sig")
    x["sec_code"] = z6(x["sec_code"])
    keep = [
        "sec_code",
        "chunk_n",
        "tech_text_glm4_tokens",
        "summary_proxy_sum",
        "summary_glm4_sum",
        "relevant_score_mean",
        "red_chunk_proxy_mean",
        "red_chunk_glm4_mean",
        "lnN_tech",
        "Redundancy_proxy",
        "Redundancy_glm4",
    ]
    x = x[keep].rename(
        columns={
            "chunk_n": "chunk_count_glm4_dewrap",
            "tech_text_glm4_tokens": "tech_text_glm4_tokens_full543",
            "summary_proxy_sum": "summary_proxy_sum_full543",
            "summary_glm4_sum": "summary_glm4_sum_full543",
            "relevant_score_mean": "relevant_score_mean_glm4_dewrap",
            "red_chunk_proxy_mean": "red_chunk_proxy_mean_full543",
            "red_chunk_glm4_mean": "red_chunk_glm4_mean_full543",
            "lnN_tech": "lnN_tech_glm4_dewrap",
            "Redundancy_proxy": "Redundancy_glm4_dewrap_proxy",
            "Redundancy_glm4": "Redundancy_glm4_dewrap_summarytoken",
        }
    )
    df = df.merge(x, on="sec_code", how="left", validate="one_to_one")
    df["Redundancy"] = pd.to_numeric(df["Redundancy_glm4_dewrap_proxy"], errors="coerce")
    df["lnN_tech"] = pd.to_numeric(df["lnN_tech_glm4_dewrap"], errors="coerce")

    numeric_cols = [
        "Redundancy",
        "lnN_tech",
        "Redundancy_prior_len132_tight",
        "lnN_tech_prior_len132_tight",
        "Redundancy_glm4_dewrap_summarytoken",
        *OUTCOMES,
        *CURRENT_CONTROL_VARS,
        "RD_Asset",
        "Price_Issue_pb_indadj",
        "Price_Day5_pb_indadj",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["listing_year"] = pd.to_numeric(df["listing_year"], errors="coerce")
    df["listing_year_fe"] = pd.to_numeric(df["listing_year_fe"], errors="coerce").astype("Int64").astype(str)
    df["listing_year_fe"] = df["listing_year_fe"].replace({"<NA>": np.nan, "nan": np.nan})
    df["industry_fe"] = df["industry_fe"].astype(str).replace({"nan": np.nan, "<NA>": np.nan})
    return df


def build_sensitivity_regressions(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    if "Redundancy_glm4_dewrap_summarytoken" not in df.columns:
        return pd.DataFrame(rows)
    current_controls = " + ".join(CURRENT_CONTROL_VARS)
    current_fe = " + C(listing_year_fe) + C(industry_fe)"
    sample_defs = [
        ("full_by_y_available", df.copy()),
        (
            "common_3y_current_controls",
            df.dropna(subset=[*OUTCOMES, "Redundancy_glm4_dewrap_summarytoken", *CURRENT_CONTROL_VARS, *FE_VARS]).copy(),
        ),
        ("w2_2019_2022_by_y_available", df[pd.to_numeric(df["listing_year"], errors="coerce").between(2019, 2022)].copy()),
        (
            "w2_2019_2022_common_3y_current_controls",
            df[pd.to_numeric(df["listing_year"], errors="coerce").between(2019, 2022)]
            .dropna(subset=[*OUTCOMES, "Redundancy_glm4_dewrap_summarytoken", *CURRENT_CONTROL_VARS, *FE_VARS])
            .copy(),
        ),
    ]
    for sample_name, sub in sample_defs:
        for dep in OUTCOMES:
            rows.append(
                base.regression_result(
                    sample_name,
                    "controls_fe_current_summarytoken_sensitivity",
                    dep,
                    f"{dep} ~ Redundancy_glm4_dewrap_summarytoken + {current_controls}{current_fe}",
                    sub,
                    "Redundancy_glm4_dewrap_summarytoken",
                )
            )
    return pd.DataFrame(rows)


def pick_row(regs: pd.DataFrame, sample: str, dep: str, model: str = "controls_fe_current") -> pd.Series:
    row = regs[(regs["sample"].eq(sample)) & (regs["dep_var"].eq(dep)) & (regs["model"].eq(model))]
    if row.empty:
        return pd.Series(dtype=object)
    return row.iloc[0]


def build_main_view(regs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sample in [
        "full_by_y_available",
        "common_3y_current_controls",
        "w2_2019_2022_by_y_available",
        "w2_2019_2022_common_3y_current_controls",
    ]:
        for dep in OUTCOMES:
            r = pick_row(regs, sample, dep)
            orig = ORIGINAL_PANEL_B[dep]
            rows.append(
                {
                    "sample": sample,
                    "Y": dep,
                    "N": int(r.get("N", 0)),
                    "coef": r.get("coef", np.nan),
                    "t": r.get("t_HC1", np.nan),
                    "p": r.get("p_HC1", np.nan),
                    "adj_r2": r.get("adj_r2", np.nan),
                    "paper_coef": orig["coef"],
                    "paper_t": orig["t"],
                    "paper_N": orig["N"],
                    "sign_match": (r.get("coef", np.nan) < 0) == (orig["coef"] < 0)
                    if pd.notna(r.get("coef", np.nan))
                    else False,
                }
            )
    return pd.DataFrame(rows)


def write_doc(df: pd.DataFrame, desc: pd.DataFrame, regs: pd.DataFrame, sens: pd.DataFrame, waterfall: pd.DataFrame, miss: pd.DataFrame) -> None:
    panel_a_vars = [
        "lnN_tech",
        "Redundancy",
        "FInvention",
        "BHAR",
        "FSales_Growth",
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
    panel_a_view = desc[desc["variable"].isin(panel_a_vars)].copy()
    panel_a_view = panel_a_view[
        [
            "variable",
            "available",
            "current_N",
            "current_mean",
            "original_N",
            "original_mean",
            "mean_diff_current_minus_original",
            "current_median",
            "original_median",
        ]
    ]

    main = build_main_view(regs)
    full_main = main[main["sample"].eq("full_by_y_available")].copy()
    sign_matches = int(full_main["sign_match"].sum())
    if sign_matches == 3 and (full_main["p"] < 0.1).all():
        verdict = "PASS_LIKE_ORIGINAL"
    elif sign_matches >= 1:
        verdict = "NO_PASS_YET"
    else:
        verdict = "NO_PASS_YET_STRONG_GAP"

    sens_view = sens[
        sens["sample"].isin(["full_by_y_available", "w2_2019_2022_by_y_available"])
        & sens["model"].eq("controls_fe_current_summarytoken_sensitivity")
    ].copy()
    sens_view = sens_view[["sample", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"]]

    x_compare = pd.DataFrame(
        [
            {
                "metric": "Redundancy prior len132_tight",
                "N": int(df["Redundancy_prior_len132_tight"].notna().sum()),
                "mean": df["Redundancy_prior_len132_tight"].mean(),
                "median": df["Redundancy_prior_len132_tight"].median(),
            },
            {
                "metric": "Redundancy full543 dewrap proxy",
                "N": int(df["Redundancy"].notna().sum()),
                "mean": df["Redundancy"].mean(),
                "median": df["Redundancy"].median(),
            },
            {
                "metric": "Redundancy full543 summary-token sensitivity",
                "N": int(df["Redundancy_glm4_dewrap_summarytoken"].notna().sum()),
                "mean": df["Redundancy_glm4_dewrap_summarytoken"].mean(),
                "median": df["Redundancy_glm4_dewrap_summarytoken"].median(),
            },
            {
                "metric": "lnN_tech prior len132_tight",
                "N": int(df["lnN_tech_prior_len132_tight"].notna().sum()),
                "mean": df["lnN_tech_prior_len132_tight"].mean(),
                "median": df["lnN_tech_prior_len132_tight"].median(),
            },
            {
                "metric": "lnN_tech full543 GLM tokens",
                "N": int(df["lnN_tech"].notna().sum()),
                "mean": df["lnN_tech"].mean(),
                "median": df["lnN_tech"].median(),
            },
        ]
    )

    missing_controls = ", ".join(miss.loc[~miss["available_in_master"], "variable"].astype(str).tolist())
    lines = [
        "# Table 2 GLM4 dewrap_join full543 审计试跑",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 结论",
        "",
        f"- 判定：`{verdict}`。",
        "- 这次使用的是 full543 新 X：`dewrap_join + GLM-4 tokenizer + cot_v3b_len132_tight + Summary_len_proxy`。",
        "- 相比旧 len132_tight X，`Redundancy` 均值从约 29.374 降到 28.944，`lnN_tech` 从约 10.745 回到 10.966，已经贴近原文 Table 2 的 29.074 和 10.962。",
        "- 但 Table 2 仍没有整体复刻原文：full 口径下 `FInvention` 已接近原文负向并达到 10% 边界显著，`BHAR` 转为弱正，`FSales_Growth` 仍为正；2019-2022 窗口也没有让三项同时显著为负。",
        f"- 原文完整控制变量仍缺：`{missing_controls}`。当前只能称为 current-controls audit，不能称为 strict Table 2 replication。",
        "",
        "## 输入",
        "",
        f"- base master：`{BASE_MASTER_IN}`",
        f"- full543 firm X：`{FIRM_X_IN}`",
        f"- 输出目录：`{RUN_DIR}`",
        "- 标准误：HC1 robust，与既有 Table 2 审计脚本保持一致。",
        "",
        "## X 替换前后",
        "",
        *base.md_table(x_compare, ["metric", "N", "mean", "median"], digits=3),
        "",
        "## Panel A 对照",
        "",
        *base.md_table(panel_a_view, list(panel_a_view.columns), digits=3),
        "",
        "## 样本 waterfall",
        "",
        *base.md_table(waterfall, ["scope", "step", "N"], digits=0),
        "",
        "## 当前 controls 主规格 vs 原文 Panel B",
        "",
        "单元格使用 `Outcome ~ Redundancy + lnN_tech + Size + Lev + ROA + Offerfee + Underwriter + Age + Year FE + Industry FE`。",
        "",
        *base.md_table(main, ["sample", "Y", "N", "coef", "t", "p", "adj_r2", "paper_coef", "paper_t", "paper_N", "sign_match"], digits=4),
        "",
        "## GLM-4 摘要 token 分母敏感性",
        "",
        *base.md_table(sens_view, ["sample", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"], digits=4),
        "",
        "## 缺失原文控制变量",
        "",
        *base.md_table(miss, ["variable", "available_in_master", "nonmissing_N", "original_mean", "note"], digits=3),
        "",
        "## 直接读法",
        "",
        "- X measurement 的 Table 1 问题基本已解：`Redundancy` 和 `lnN_tech` 都贴近原文。",
        "- 只替换成 full543 新 X 后，`FInvention` 这一列明显改善，但 `BHAR` 和 `FSales_Growth` 没有恢复原文负向；这说明当前主要差距已经转向 Y/controls/sample 口径。",
        "- `Underwriter` 仍是最大硬伤：当前均值约 0.009，原文 0.574，不能视为同一变量。",
        "- `NumIndSeg / NumProdSeg / ScopeLen` 仍缺失，严格原文控制变量组无法运行。",
        "",
        "## 输出文件",
        "",
        f"- master copy：`{MASTER_OUT}`",
        f"- Panel A：`{DESC_OUT}`",
        f"- regressions：`{REG_OUT}`",
        f"- waterfall：`{WATERFALL_OUT}`",
        f"- missing controls：`{MISSING_CONTROLS_OUT}`",
        "",
    ]
    DOC_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    df = load_master()
    df.to_csv(MASTER_OUT, index=False, encoding="utf-8-sig")

    desc = base.descriptives_vs_original(df)
    desc.to_csv(DESC_OUT, index=False, encoding="utf-8-sig")

    regs = base.build_regressions(df)
    sens = build_sensitivity_regressions(df)
    regs_all = pd.concat([regs, sens], ignore_index=True)
    regs_all.to_csv(REG_OUT, index=False, encoding="utf-8-sig")

    waterfall = base.build_waterfall(df)
    waterfall.to_csv(WATERFALL_OUT, index=False, encoding="utf-8-sig")

    miss = base.missing_paper_controls(df)
    miss.to_csv(MISSING_CONTROLS_OUT, index=False, encoding="utf-8-sig")

    write_doc(df, desc, regs, sens, waterfall, miss)

    print(f"master={MASTER_OUT}")
    print(f"panel_a={DESC_OUT}")
    print(f"regressions={REG_OUT}")
    print(f"waterfall={WATERFALL_OUT}")
    print(f"missing_controls={MISSING_CONTROLS_OUT}")
    print(f"doc={DOC_OUT}")
    print(
        regs[
            regs["model"].eq("controls_fe_current")
            & regs["sample"].isin(
                [
                    "full_by_y_available",
                    "common_3y_current_controls",
                    "w2_2019_2022_by_y_available",
                    "w2_2019_2022_common_3y_current_controls",
                ]
            )
        ][["sample", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"]].to_string(index=False)
    )


if __name__ == "__main__":
    main()
