#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


PROJECT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
MASTER_IN = (
    PROJECT
    / "results/summary_len_calibration_full_543_20260704/"
    "sample_543_firms_20260704.csv"
)
RANK_IN = (
    PROJECT
    / "results/summary_len_calibration_full_543_20260704/"
    "firm_ranking_cot_v3b_len132_tight_20260703.csv"
)
RUN_DIR = PROJECT / "results/table2_len132_tight_audit_20260705"
DOC_OUT = PROJECT / "docs/00_current/table2_len132_tight_audit_20260705.md"

MASTER_OUT = RUN_DIR / "table2_len132_tight_master_20260705.csv"
DESC_OUT = RUN_DIR / "panel_a_descriptives_vs_original_20260705.csv"
REG_OUT = RUN_DIR / "table2_len132_tight_regressions_20260705.csv"
WATERFALL_OUT = RUN_DIR / "table2_len132_tight_sample_waterfall_20260705.csv"
MISSING_CONTROLS_OUT = RUN_DIR / "table2_len132_tight_missing_paper_controls_20260705.csv"


ORIGINAL_PANEL_A = {
    "lnN_tech": {"N": 552, "mean": 10.962, "std": 0.350, "p25": 10.714, "median": 10.910, "p75": 11.185},
    "Redundancy": {"N": 552, "mean": 29.074, "std": 2.630, "p25": 27.402, "median": 28.910, "p75": 30.795},
    "FInvention": {"N": 471, "mean": 2.282, "std": 1.200, "p25": 1.386, "median": 2.197, "p75": 2.890},
    "BHAR": {"N": 471, "mean": -0.036, "std": 0.514, "p25": -0.385, "median": -0.170, "p75": 0.162},
    "FSales_Growth": {"N": 471, "mean": 0.530, "std": 1.522, "p25": -0.008, "median": 0.180, "p75": 0.523},
    "Price_Issue": {"N": 552, "mean": 0.988, "std": 1.330, "p25": 0.462, "median": 0.726, "p75": 1.163},
    "Price_Day5": {"N": 552, "mean": 0.949, "std": 0.957, "p25": 0.419, "median": 0.698, "p75": 1.125},
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

ORIGINAL_PANEL_B = {
    "FInvention": {"coef": -0.0316, "t": -1.72, "N": 471, "adj_r2": 0.32},
    "BHAR": {"coef": -0.0188, "t": -2.14, "N": 471, "adj_r2": 0.06},
    "FSales_Growth": {"coef": -0.0373, "t": -2.02, "N": 471, "adj_r2": 0.05},
}

OUTCOMES = ["FInvention", "BHAR", "FSales_Growth"]
CURRENT_CONTROL_VARS = ["lnN_tech", "Size", "Lev", "ROA", "Offerfee", "Underwriter", "Age"]
PAPER_ONLY_CONTROL_VARS = ["NumIndSeg", "NumProdSeg", "ScopeLen"]
FE_VARS = ["listing_year_fe", "industry_fe"]


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


def load_master() -> pd.DataFrame:
    df = pd.read_csv(MASTER_IN, dtype={"sec_code": str, "code": str}, encoding="utf-8-sig")
    if "code" not in df.columns:
        df["code"] = df["sec_code"]
    df["code"] = df["code"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)
    if "sec_code" in df.columns:
        df["sec_code"] = df["sec_code"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)

    rank = pd.read_csv(RANK_IN, dtype={"sec_code": str}, encoding="utf-8-sig")
    rank["sec_code"] = rank["sec_code"].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)
    rank = rank.rename(
        columns={
            "Redundancy": "Redundancy_len132_tight",
            "original_length_units": "original_length_units_len132_tight",
            "summary_length_units": "summary_length_units_len132_tight",
            "relevant_score_mean": "relevant_score_mean_len132_tight",
            "chunk_count": "chunk_count_len132_tight",
        }
    )
    df = df.rename(
        columns={
            "Redundancy": "Redundancy_prior_master",
            "redundancy": "redundancy_prior_master",
            "lnN_tech": "lnN_tech_prior_master",
        }
    )
    keep_rank = [
        "sec_code",
        "Redundancy_len132_tight",
        "original_length_units_len132_tight",
        "summary_length_units_len132_tight",
        "relevant_score_mean_len132_tight",
        "chunk_count_len132_tight",
    ]
    df = df.merge(rank[keep_rank], on="sec_code", how="left", validate="one_to_one")
    df["Redundancy"] = pd.to_numeric(df["Redundancy_len132_tight"], errors="coerce")
    df["lnN_tech"] = np.log(pd.to_numeric(df["original_length_units_len132_tight"], errors="coerce"))

    for col in ORIGINAL_PANEL_A:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["Redundancy", *OUTCOMES, *CURRENT_CONTROL_VARS, "RD_Asset", "Price_Issue_pb_indadj", "Price_Day5_pb_indadj"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["listing_year"] = pd.to_numeric(df["listing_year"], errors="coerce")
    df["listing_year_fe"] = pd.to_numeric(df["listing_year_fe"], errors="coerce").astype("Int64").astype(str)
    df["listing_year_fe"] = df["listing_year_fe"].replace({"<NA>": np.nan, "nan": np.nan})
    df["industry_fe"] = df["industry_fe"].astype(str).replace({"nan": np.nan, "<NA>": np.nan})
    return df


def descriptives_vs_original(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for var, orig in ORIGINAL_PANEL_A.items():
        if var in df.columns:
            s = pd.to_numeric(df[var], errors="coerce").dropna()
            cur = {
                "current_N": int(len(s)),
                "current_mean": s.mean(),
                "current_std": s.std(ddof=1),
                "current_p25": s.quantile(0.25),
                "current_median": s.quantile(0.5),
                "current_p75": s.quantile(0.75),
            }
            available = True
        else:
            cur = {
                "current_N": 0,
                "current_mean": np.nan,
                "current_std": np.nan,
                "current_p25": np.nan,
                "current_median": np.nan,
                "current_p75": np.nan,
            }
            available = False
        rows.append(
            {
                "variable": var,
                "available": available,
                **cur,
                "original_N": orig["N"],
                "original_mean": orig["mean"],
                "original_std": orig["std"],
                "original_p25": orig["p25"],
                "original_median": orig["median"],
                "original_p75": orig["p75"],
                "mean_diff_current_minus_original": cur["current_mean"] - orig["mean"]
                if available
                else np.nan,
            }
        )
    return pd.DataFrame(rows)


def regression_result(sample: str, model_name: str, dep: str, formula: str, df: pd.DataFrame, target: str) -> dict:
    try:
        res = smf.ols(formula, data=df).fit(cov_type="HC1")
    except Exception as exc:
        return {
            "sample": sample,
            "model": model_name,
            "dep_var": dep,
            "target_var": target,
            "N": 0,
            "coef": np.nan,
            "se_HC1": np.nan,
            "t_HC1": np.nan,
            "p_HC1": np.nan,
            "adj_r2": np.nan,
            "formula": formula,
            "error": repr(exc),
        }
    return {
        "sample": sample,
        "model": model_name,
        "dep_var": dep,
        "target_var": target,
        "N": int(res.nobs),
        "coef": float(res.params.get(target, np.nan)),
        "se_HC1": float(res.bse.get(target, np.nan)),
        "t_HC1": float(res.tvalues.get(target, np.nan)),
        "p_HC1": float(res.pvalues.get(target, np.nan)),
        "adj_r2": float(res.rsquared_adj),
        "formula": formula,
        "error": "",
    }


def run_regressions_for_sample(sample: str, df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    current_controls = " + ".join(CURRENT_CONTROL_VARS)
    current_fe = " + C(listing_year_fe) + C(industry_fe)"
    for dep in OUTCOMES:
        rows.append(regression_result(sample, "simple", dep, f"{dep} ~ Redundancy", df, "Redundancy"))
        rows.append(
            regression_result(
                sample,
                "fe_text",
                dep,
                f"{dep} ~ Redundancy + lnN_tech{current_fe}",
                df,
                "Redundancy",
            )
        )
        rows.append(
            regression_result(
                sample,
                "controls_fe_current",
                dep,
                f"{dep} ~ Redundancy + {current_controls}{current_fe}",
                df,
                "Redundancy",
            )
        )

        if all(col in df.columns for col in PAPER_ONLY_CONTROL_VARS):
            paper_controls = " + ".join([*CURRENT_CONTROL_VARS, *PAPER_ONLY_CONTROL_VARS])
            rows.append(
                regression_result(
                    sample,
                    "controls_fe_paper_full",
                    dep,
                    f"{dep} ~ Redundancy + {paper_controls}{current_fe}",
                    df,
                    "Redundancy",
                )
            )
        else:
            rows.append(
                {
                    "sample": sample,
                    "model": "controls_fe_paper_full",
                    "dep_var": dep,
                    "target_var": "Redundancy",
                    "N": 0,
                    "coef": np.nan,
                    "se_HC1": np.nan,
                    "t_HC1": np.nan,
                    "p_HC1": np.nan,
                    "adj_r2": np.nan,
                    "formula": "missing NumIndSeg + NumProdSeg + ScopeLen",
                    "error": "missing_paper_controls",
                }
            )
    return pd.DataFrame(rows)


def build_regressions(df: pd.DataFrame) -> pd.DataFrame:
    samples: list[tuple[str, pd.DataFrame]] = []
    samples.append(("full_by_y_available", df.copy()))

    current_common_cols = [*OUTCOMES, "Redundancy", *CURRENT_CONTROL_VARS, *FE_VARS]
    common = df.dropna(subset=current_common_cols).copy()
    samples.append(("common_3y_current_controls", common))

    w2 = df[pd.to_numeric(df["listing_year"], errors="coerce").between(2019, 2022)].copy()
    samples.append(("w2_2019_2022_by_y_available", w2))
    samples.append(("w2_2019_2022_common_3y_current_controls", w2.dropna(subset=current_common_cols).copy()))

    return pd.concat([run_regressions_for_sample(name, sub) for name, sub in samples], ignore_index=True)


def build_waterfall(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []

    def add(scope: str, label: str, sub: pd.DataFrame) -> None:
        base_controls = ["Redundancy", *CURRENT_CONTROL_VARS, *FE_VARS]
        rows.extend(
            [
                {"scope": scope, "step": f"{label}: firms with len132_tight X", "N": int(sub["code"].nunique())},
                {"scope": scope, "step": "with listing_year", "N": int(sub.dropna(subset=["listing_year"])["code"].nunique())},
                {"scope": scope, "step": "FInvention nonmissing", "N": int(sub.dropna(subset=["FInvention"])["code"].nunique())},
                {"scope": scope, "step": "BHAR nonmissing", "N": int(sub.dropna(subset=["BHAR"])["code"].nunique())},
                {"scope": scope, "step": "FSales_Growth nonmissing", "N": int(sub.dropna(subset=["FSales_Growth"])["code"].nunique())},
                {"scope": scope, "step": "current controls complete", "N": int(sub.dropna(subset=base_controls)["code"].nunique())},
                {
                    "scope": scope,
                    "step": "all 3 Y + current controls complete",
                    "N": int(sub.dropna(subset=[*OUTCOMES, *base_controls])["code"].nunique()),
                },
                {
                    "scope": scope,
                    "step": "all 3 Y + original paper controls complete",
                    "N": 0
                    if not all(col in sub.columns for col in PAPER_ONLY_CONTROL_VARS)
                    else int(sub.dropna(subset=[*OUTCOMES, *base_controls, *PAPER_ONLY_CONTROL_VARS])["code"].nunique()),
                },
            ]
        )

    add("full_2019_2023", "2019-2023", df)
    add("w2_2019_2022", "2019-2022", df[pd.to_numeric(df["listing_year"], errors="coerce").between(2019, 2022)])
    return pd.DataFrame(rows)


def missing_paper_controls(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in PAPER_ONLY_CONTROL_VARS:
        rows.append(
            {
                "variable": col,
                "available_in_master": col in df.columns,
                "nonmissing_N": int(pd.to_numeric(df[col], errors="coerce").notna().sum()) if col in df.columns else 0,
                "original_mean": ORIGINAL_PANEL_A[col]["mean"],
                "note": "required by original Table 2 controls",
            }
        )
    return pd.DataFrame(rows)


def pick_row(regs: pd.DataFrame, sample: str, dep: str, model: str = "controls_fe_current") -> pd.Series:
    row = regs[(regs["sample"].eq(sample)) & (regs["dep_var"].eq(dep)) & (regs["model"].eq(model))]
    if row.empty:
        return pd.Series(dtype=object)
    return row.iloc[0]


def write_doc(df: pd.DataFrame, desc: pd.DataFrame, regs: pd.DataFrame, waterfall: pd.DataFrame, miss: pd.DataFrame) -> None:
    panel_a_view = desc[
        desc["variable"].isin(
            [
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
        )
    ].copy()
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

    main_rows = []
    for sample in [
        "full_by_y_available",
        "common_3y_current_controls",
        "w2_2019_2022_by_y_available",
        "w2_2019_2022_common_3y_current_controls",
    ]:
        for dep in OUTCOMES:
            r = pick_row(regs, sample, dep)
            orig = ORIGINAL_PANEL_B[dep]
            main_rows.append(
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
    main = pd.DataFrame(main_rows)

    missing_controls = ", ".join(miss.loc[~miss["available_in_master"], "variable"].astype(str).tolist())
    full_main = main[main["sample"].eq("full_by_y_available")].copy()
    sign_matches = int(full_main["sign_match"].sum())
    if sign_matches == 3 and (full_main["p"] < 0.1).all():
        verdict = "PASS_LIKE_ORIGINAL"
    elif sign_matches >= 1:
        verdict = "NO_PASS_YET"
    else:
        verdict = "NO_PASS_YET_STRONG_GAP"

    lines = [
        "# Table 2 len132_tight 审计试跑",
        "",
        "日期：2026-07-05",
        "",
        "## 结论",
        "",
        f"- 判定：`{verdict}`。",
        "- 这次确认使用的是 `cot_v3b_len132_tight` full543 企业层 X，不是旧 scoregate543。",
        "- 结果没有复刻原文 Table 2：full 口径下 `FInvention` 和 `BHAR` 已回到负号但都很弱，`FSales_Growth` 仍为正号；共同样本和 2019-2022 窗口也没有把三项同时推回原文显著负向。",
        f"- 原文完整控制变量仍缺：`{missing_controls}`。因此当前只能称为 current-controls audit，不能称为 strict Table 2 replication。",
        "- 主要差距现在更像是 `Y/controls/sample` 口径问题；X 的均值已接近原文，但 `lnN_tech`、`Underwriter` 和三项 paper-only controls 仍未同口径。",
        "",
        "## 输入",
        "",
        f"- master：`{MASTER_IN}`",
        f"- len132_tight firm ranking：`{RANK_IN}`",
        f"- 输出目录：`{RUN_DIR}`",
        "- 原文锚点来自本地 PDF `bib/IPO信息披露冗余如何影响新股定价？——基于生成式人工智能技术的经验证据_赵晓阳.pdf` 的表 2。",
        "- 标准误：HC1 robust，与既有脚本保持一致。",
        "",
        "## Panel A 对照",
        "",
        *md_table(panel_a_view, list(panel_a_view.columns), digits=3),
        "",
        "## 样本 waterfall",
        "",
        *md_table(waterfall, ["scope", "step", "N"], digits=0),
        "",
        "## 当前 controls 主规格 vs 原文 Panel B",
        "",
        "单元格使用 `Outcome ~ Redundancy + lnN_tech + Size + Lev + ROA + Offerfee + Underwriter + Age + Year FE + Industry FE`。",
        "",
        *md_table(main, ["sample", "Y", "N", "coef", "t", "p", "adj_r2", "paper_coef", "paper_t", "paper_N", "sign_match"], digits=4),
        "",
        "## 缺失原文控制变量",
        "",
        *md_table(miss, ["variable", "available_in_master", "nonmissing_N", "original_mean", "note"], digits=3),
        "",
        "## 直接读法",
        "",
        "- `Redundancy` 均值贴得很近：当前约 29.374，原文 29.074。",
        "- `lnN_tech` 当前约 10.745，原文 10.962；使用的是 len132 ranking 中 `original_length_units` 的对数，不再沿用旧 master 的字符长度列。",
        "- `FInvention` 均值约 2.325，接近原文 2.282；len132 后回归系数变为负号，但幅度远小于原文且不显著。",
        "- `BHAR` 均值约 -0.062，原文 -0.036；方向变量本身不离谱，但 Redundancy 系数弱。",
        "- `FSales_Growth` 均值约 0.409，低于原文 0.530；这条 Y 的口径嫌疑仍然较大。",
        "- `Underwriter` 均值约 0.009，原文 0.574；当前来源表的 Sponsor 大多为 `None`，这个 dummy 基本不可用，必须重下或换字段。",
        "",
        "## 下一步",
        "",
        "1. 补或重构 `NumIndSeg / NumProdSeg / ScopeLen`。",
        "2. 重构 `Underwriter`：原文定义是 IPO 承销业务前十大券商，当前 CSMAR 临时表的 Sponsor 字段严重缺失。",
        "3. 对 `lnN_tech` 做单位审计：字符数、中文字数、token proxy、空白清洗后长度分别算一遍。",
        "4. 对三条 Y 做口径网格，优先 `FInvention` 的申请/授权/窗口和 `BHAR` 的基准收益/首日处理。",
        "5. 做 552 -> 543 -> 541 -> 471 的逐家公司 crosswalk。",
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

    desc = descriptives_vs_original(df)
    desc.to_csv(DESC_OUT, index=False, encoding="utf-8-sig")

    regs = build_regressions(df)
    regs.to_csv(REG_OUT, index=False, encoding="utf-8-sig")

    waterfall = build_waterfall(df)
    waterfall.to_csv(WATERFALL_OUT, index=False, encoding="utf-8-sig")

    miss = missing_paper_controls(df)
    miss.to_csv(MISSING_CONTROLS_OUT, index=False, encoding="utf-8-sig")

    write_doc(df, desc, regs, waterfall, miss)

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
