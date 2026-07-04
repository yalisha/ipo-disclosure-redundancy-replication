#!/usr/bin/env python3
from __future__ import annotations

import re
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


PROJECT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
RUN_DIR = PROJECT / "results" / "original_paper_table2_probe_20260702"
RUN_DIR.mkdir(parents=True, exist_ok=True)

REDUNDANCY_PATH = (
    PROJECT
    / "results/star_token_proxy_200_20260701/ipo_redundancy_firm_level_cot_v3b_scoregate_targeted_200.csv"
)
OUTCOME_PATH = (
    PROJECT / "results/outcome_variable_probe_20260629/outcome_variables_star_firm_level_20260629.csv"
)
IPO_BASIC_ZIP = Path(
    "/Users/mac/computerscience/第三方资料/90_临时下载待归档/招股及上市基本情况表093114533(仅供四川大学使用).zip"
)
PARQUET_DIR = Path("/Users/mac/computerscience/0做完了/15会计研究/v1/data_parquet")

MASTER_OUT = RUN_DIR / "original_paper_table2_probe_master_20260702.csv"
REG_OUT = RUN_DIR / "original_paper_table2_probe_regressions_20260702.csv"
DESC_OUT = RUN_DIR / "original_paper_table2_probe_descriptives_20260702.csv"
DOC_OUT = PROJECT / "docs" / "原文表2经济后果试跑_20260702.md"


ORIGINAL_PANEL_B = {
    "FInvention": {"coef": -0.0316, "t": -1.72, "N": 471, "adj_r2": 0.32},
    "BHAR": {"coef": -0.0188, "t": -2.14, "N": 471, "adj_r2": 0.06},
    "FSales_Growth": {"coef": -0.0373, "t": -2.02, "N": 471, "adj_r2": 0.05},
}


def z6(value) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text.zfill(6) if text.isdigit() else text


def winsorize(series: pd.Series, lower: float = 0.01, upper: float = 0.99) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    nonmissing = s.dropna()
    if nonmissing.empty:
        return s
    return s.clip(nonmissing.quantile(lower), nonmissing.quantile(upper))


def split_sponsors(value: object) -> list[str]:
    if pd.isna(value):
        return []
    text = str(value).strip()
    if not text or text.lower() == "none":
        return []
    parts = re.split(r"[,，;；、]", text)
    return [p.strip() for p in parts if p.strip() and p.strip().lower() != "none"]


def read_ipo_basic() -> pd.DataFrame:
    cols = [
        "Stkcd",
        "Listdt",
        "Ipoiteddt",
        "Ipostsbdt",
        "Ipostpbdt",
        "Aiprc",
        "Fltcst",
        "Sponsor",
        "Nshripo",
        "Grserc",
        "Neterc",
        "NAV2",
        "PB",
        "Pedlt",
    ]
    with ZipFile(IPO_BASIC_ZIP) as zf:
        dta = [n for n in zf.namelist() if n.endswith(".dta")][0]
        with zf.open(dta) as fh:
            df = pd.read_stata(fh, columns=cols)
    df["code"] = df["Stkcd"].map(z6)
    df["ipo_list_date_raw"] = df["Listdt"].astype(str)
    df["ipo_list_date"] = pd.to_datetime(df["Listdt"], errors="coerce")
    for col in ["Aiprc", "Fltcst", "Nshripo", "Grserc", "Neterc", "NAV2", "PB", "Pedlt"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Offerfee"] = np.log(df["Fltcst"] * 10000)
    return df.drop_duplicates("code")


def build_underwriter_dummy(ipo_basic: pd.DataFrame) -> pd.DataFrame:
    star = ipo_basic[ipo_basic["code"].str.startswith("688", na=False)].copy()
    star["ipo_year"] = pd.to_datetime(star["ipo_list_date"], errors="coerce").dt.year
    star = star[star["ipo_year"].between(2019, 2023, inclusive="both")]
    counts: dict[str, int] = {}
    for sponsors in star["Sponsor"].map(split_sponsors):
        for sponsor in sponsors:
            counts[sponsor] = counts.get(sponsor, 0) + 1
    top10 = {name for name, _ in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:10]}
    out = ipo_basic[["code", "Sponsor"]].copy()
    out["Underwriter"] = out["Sponsor"].map(lambda x: int(bool(set(split_sponsors(x)) & top10)))
    return out[["code", "Underwriter"]]


def load_financial_controls(codes: set[str], listing_years: pd.DataFrame) -> pd.DataFrame:
    bal = pd.read_parquet(
        PARQUET_DIR / "balance_sheet.parquet",
        columns=["Stkcd", "Accper", "Typrep", "A001000000", "A002000000", "A001219000"],
    )
    inc = pd.read_parquet(
        PARQUET_DIR / "income_stmt.parquet",
        columns=["Stkcd", "Accper", "Typrep", "B001101000", "B001100000", "B002000000", "B001216000"],
    )
    for df in [bal, inc]:
        df["code"] = df["Stkcd"].map(z6)
        df["Accper"] = pd.to_datetime(df["Accper"], errors="coerce")
        df["year"] = df["Accper"].dt.year
        df["Typrep"] = df["Typrep"].astype(str)
    bal = bal[(bal["code"].isin(codes)) & bal["Typrep"].eq("A")].copy()
    inc = inc[(inc["code"].isin(codes)) & inc["Typrep"].eq("A")].copy()
    annual_like = lambda df: df[
        ((df["Accper"].dt.month == 12) & (df["Accper"].dt.day == 31))
        | ((df["Accper"].dt.month == 1) & (df["Accper"].dt.day == 1))
    ].copy()
    bal = annual_like(bal)
    inc = annual_like(inc)

    key = listing_years[["code", "listing_year", "first_trade_date"]].copy()

    bal_pre = key.merge(
        bal[["code", "Accper", "A001000000", "A002000000", "A001219000"]],
        on="code",
        how="left",
    )
    bal_pre = bal_pre[bal_pre["Accper"].le(bal_pre["first_trade_date"])].copy()
    bal_pre = bal_pre.sort_values(["code", "Accper"]).drop_duplicates("code", keep="last")

    inc_pre = key.merge(
        inc[["code", "Accper", "B001101000", "B001100000", "B002000000", "B001216000"]],
        on="code",
        how="left",
    )
    inc_pre = inc_pre[inc_pre["Accper"].le(inc_pre["first_trade_date"])].copy()
    inc_pre = inc_pre.sort_values(["code", "Accper"]).drop_duplicates("code", keep="last")

    out = key[["code", "listing_year"]].merge(
        bal_pre[["code", "Accper", "A001000000", "A002000000", "A001219000"]].rename(
            columns={"Accper": "balance_accper"}
        ),
        on="code",
        how="left",
    )
    out = out.merge(
        inc_pre[["code", "Accper", "B001101000", "B001100000", "B002000000", "B001216000"]].rename(
            columns={"Accper": "income_accper"}
        ),
        on="code",
        how="left",
    )
    for col in ["A001000000", "A002000000", "A001219000", "B001101000", "B001100000", "B002000000", "B001216000"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["Size"] = np.log(out["A001000000"])
    out["Lev"] = out["A002000000"] / out["A001000000"]
    out["ROA"] = out["B002000000"] / out["A001000000"]
    out["RD_Asset"] = out["B001216000"] / out["A001000000"]
    out["Dev_Asset"] = out["A001219000"] / out["A001000000"]
    return out


def load_firm_info(codes: set[str], listing_years: pd.DataFrame) -> pd.DataFrame:
    fi = pd.read_parquet(
        PARQUET_DIR / "firm_info.parquet",
        columns=[
            "Symbol",
            "EndDate",
            "IndustryCode",
            "IndustryCodeC",
            "IndustryCodeD",
            "EstablishDate",
            "LISTINGDATE",
            "PROVINCE",
            "CITY",
        ],
    )
    fi["code"] = fi["Symbol"].map(z6)
    fi = fi[fi["code"].isin(codes)].copy()
    fi["EndDate"] = pd.to_datetime(fi["EndDate"], errors="coerce")
    fi = fi.sort_values(["code", "EndDate"]).drop_duplicates("code", keep="first")
    fi["EstablishDate"] = pd.to_datetime(fi["EstablishDate"], errors="coerce")
    out = listing_years[["code", "first_trade_date"]].merge(
        fi[["code", "IndustryCode", "IndustryCodeC", "IndustryCodeD", "EstablishDate", "PROVINCE", "CITY"]],
        on="code",
        how="left",
    )
    age_years = (out["first_trade_date"] - out["EstablishDate"]).dt.days / 365.25
    out["Age"] = np.log(age_years.where(age_years > 0))
    return out.drop(columns=["first_trade_date"])


def load_day5_price(codes: set[str]) -> pd.DataFrame:
    ret = pd.read_parquet(
        PARQUET_DIR / "daily_return.parquet",
        columns=["Stkcd", "Trddt", "Clsprc", "Dretwd", "Markettype"],
    )
    ret["code"] = ret["Stkcd"].map(z6)
    ret = ret[ret["code"].isin(codes)].copy()
    ret["Trddt"] = pd.to_datetime(ret["Trddt"], errors="coerce")
    ret["Clsprc"] = pd.to_numeric(ret["Clsprc"], errors="coerce")
    ret = ret.sort_values(["code", "Trddt"])
    ret["trading_day_rank"] = ret.groupby("code").cumcount() + 1
    d5 = ret[ret["trading_day_rank"].eq(5)][["code", "Trddt", "Clsprc"]].copy()
    d5 = d5.rename(columns={"Trddt": "day5_date", "Clsprc": "day5_close"})
    return d5


def build_master() -> pd.DataFrame:
    red = pd.read_csv(REDUNDANCY_PATH, dtype={"sec_code": str})
    red["code"] = red["sec_code"].map(z6)
    red["Redundancy"] = pd.to_numeric(red["redundancy"], errors="coerce")
    red["lnN_tech"] = np.log(pd.to_numeric(red["tech_text_compact_chars"], errors="coerce"))
    red["chunk_count"] = pd.to_numeric(red["chunk_count"], errors="coerce")

    outcomes = pd.read_csv(OUTCOME_PATH, dtype={"code": str})
    outcomes["code"] = outcomes["code"].map(z6)
    outcomes["first_trade_date"] = pd.to_datetime(outcomes["first_trade_date"], errors="coerce")
    outcomes["listing_year"] = pd.to_numeric(outcomes["listing_year"], errors="coerce").astype("Int64")
    outcomes["FInvention"] = outcomes["FInvention_ln1p_auth"]
    outcomes["BHAR"] = outcomes["excl_first_BHAR_ew_w1p"]
    outcomes["FSales_Growth"] = outcomes["FSales_Growth_w1p"]

    master = red.merge(outcomes, on="code", how="left", suffixes=("", "_outcome"))
    codes = set(master["code"].dropna())
    listing_years = master[["code", "first_trade_date", "listing_year"]].copy()
    listing_years["listing_year"] = pd.to_numeric(listing_years["listing_year"], errors="coerce")

    ipo = read_ipo_basic()
    underwriter = build_underwriter_dummy(ipo)
    fin = load_financial_controls(codes, listing_years)
    fi = load_firm_info(codes, listing_years)
    d5 = load_day5_price(codes)

    master = master.merge(
        ipo[["code", "Aiprc", "Fltcst", "Offerfee", "NAV2", "PB", "Pedlt", "ipo_list_date_raw", "ipo_list_date"]],
        on="code",
        how="left",
    )
    master = master.merge(underwriter, on="code", how="left")
    master = master.merge(fin, on=["code", "listing_year"], how="left")
    master = master.merge(fi, on="code", how="left")
    master = master.merge(d5, on="code", how="left")

    master["industry_fe"] = master["industry_code_patent"].fillna(master["IndustryCodeC"]).fillna(master["IndustryCode"])
    master["industry_fe"] = master["industry_fe"].astype(str).replace({"nan": np.nan, "<NA>": np.nan})
    master["Price_Issue_pb"] = master["PB"].fillna(master["Aiprc"] / master["NAV2"])
    master["Price_Day5_pb"] = master["day5_close"] / master["NAV2"]
    for col in ["Price_Issue_pb", "Price_Day5_pb"]:
        mean_by_ind = master.groupby("industry_fe")[col].transform("mean")
        master[col + "_indadj"] = master[col] / mean_by_ind

    master["RD_Low"] = (master["RD_Asset"] <= master["RD_Asset"].quantile(0.25)).astype(float)
    master.loc[master["RD_Asset"].isna(), "RD_Low"] = np.nan
    master["Redundancy_High"] = (master["Redundancy"] >= master["Redundancy"].quantile(0.75)).astype(float)
    master["RD_Low_x_Redundancy_High"] = master["RD_Low"] * master["Redundancy_High"]
    master["listing_year_fe"] = pd.to_numeric(master["listing_year"], errors="coerce").astype("float").astype("Int64").astype(str)
    master["listing_year_fe"] = master["listing_year_fe"].replace({"<NA>": np.nan})

    return master


def regression_result(model_name: str, dep: str, formula: str, df: pd.DataFrame, target_var: str) -> dict:
    model_df = df.copy()
    res = smf.ols(formula, data=model_df).fit(cov_type="HC1")
    if target_var not in res.params.index:
        coef = se = t = p = np.nan
    else:
        coef = float(res.params[target_var])
        se = float(res.bse[target_var])
        t = float(res.tvalues[target_var])
        p = float(res.pvalues[target_var])
    return {
        "model": model_name,
        "dep_var": dep,
        "target_var": target_var,
        "N": int(res.nobs),
        "coef": coef,
        "se_HC1": se,
        "t_HC1": t,
        "p_HC1": p,
        "adj_r2": float(res.rsquared_adj),
        "formula": formula,
    }


def run_regressions(master: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    outcomes = {
        "FInvention": "FInvention",
        "BHAR": "BHAR",
        "FSales_Growth": "FSales_Growth",
    }
    for label, dep in outcomes.items():
        rows.append(regression_result("simple", label, f"{dep} ~ Redundancy", master, "Redundancy"))
        rows.append(
            regression_result(
                "fe_text",
                label,
                f"{dep} ~ Redundancy + lnN_tech + C(listing_year_fe) + C(industry_fe)",
                master,
                "Redundancy",
            )
        )
        rows.append(
            regression_result(
                "controls_fe",
                label,
                (
                    f"{dep} ~ Redundancy + lnN_tech + Size + Lev + ROA + Offerfee + "
                    "Underwriter + Age + C(listing_year_fe) + C(industry_fe)"
                ),
                master,
                "Redundancy",
            )
        )

    for dep in ["Price_Issue_pb_indadj", "Price_Day5_pb_indadj"]:
        rows.append(
            regression_result(
                "pricing_rd_asset_controls_fe",
                dep,
                (
                    f"{dep} ~ RD_Low_x_Redundancy_High + RD_Low + Redundancy_High + "
                    "lnN_tech + Size + Lev + ROA + Offerfee + Underwriter + Age + "
                    "C(listing_year_fe) + C(industry_fe)"
                ),
                master,
                "RD_Low_x_Redundancy_High",
            )
        )
    return pd.DataFrame(rows)


def descriptives(master: pd.DataFrame) -> pd.DataFrame:
    rows = []
    vars_ = [
        "Redundancy",
        "lnN_tech",
        "FInvention",
        "BHAR",
        "FSales_Growth",
        "Price_Issue_pb_indadj",
        "Price_Day5_pb_indadj",
        "RD_Asset",
        "Size",
        "Lev",
        "ROA",
        "Offerfee",
        "Underwriter",
        "Age",
    ]
    for var in vars_:
        s = pd.to_numeric(master[var], errors="coerce").dropna()
        rows.append(
            {
                "variable": var,
                "N": int(len(s)),
                "mean": s.mean(),
                "std": s.std(ddof=1),
                "p25": s.quantile(0.25),
                "median": s.quantile(0.5),
                "p75": s.quantile(0.75),
            }
        )
    return pd.DataFrame(rows)


def fmt_num(x: object, digits: int = 3) -> str:
    if pd.isna(x):
        return ""
    return f"{float(x):.{digits}f}"


def write_doc(master: pd.DataFrame, regs: pd.DataFrame, desc: pd.DataFrame) -> None:
    sample_loss = [
        ("200 家 Redundancy 样本", len(master)),
        ("可匹配上市后结果变量", int(master["FInvention"].notna().sum())),
        ("BHAR 可得", int(master["BHAR"].notna().sum())),
        ("FSales_Growth 可得", int(master["FSales_Growth"].notna().sum())),
        ("完整控制变量共同样本", int(master[["FInvention", "BHAR", "FSales_Growth", "Size", "Lev", "ROA", "Offerfee", "Underwriter", "Age", "lnN_tech", "industry_fe"]].dropna().shape[0])),
    ]
    panel_rows = []
    for dep in ["FInvention", "BHAR", "FSales_Growth"]:
        r = regs[(regs["model"].eq("controls_fe")) & (regs["dep_var"].eq(dep))].iloc[0]
        orig = ORIGINAL_PANEL_B[dep]
        panel_rows.append(
            f"| {dep} | {int(r['N'])} | {fmt_num(r['coef'], 4)} | {fmt_num(r['t_HC1'], 2)} | "
            f"{fmt_num(r['p_HC1'], 3)} | {fmt_num(r['adj_r2'], 3)} | {orig['coef']:.4f} | {orig['t']:.2f} |"
        )

    simple_rows = []
    for dep in ["FInvention", "BHAR", "FSales_Growth"]:
        for model in ["simple", "fe_text", "controls_fe"]:
            r = regs[(regs["model"].eq(model)) & (regs["dep_var"].eq(dep))].iloc[0]
            simple_rows.append(
                f"| {dep} | {model} | {int(r['N'])} | {fmt_num(r['coef'], 4)} | "
                f"{fmt_num(r['t_HC1'], 2)} | {fmt_num(r['p_HC1'], 3)} | {fmt_num(r['adj_r2'], 3)} |"
            )

    pricing_rows = []
    for dep in ["Price_Issue_pb_indadj", "Price_Day5_pb_indadj"]:
        r = regs[(regs["model"].eq("pricing_rd_asset_controls_fe")) & (regs["dep_var"].eq(dep))].iloc[0]
        pricing_rows.append(
            f"| {dep} | {int(r['N'])} | {fmt_num(r['coef'], 4)} | {fmt_num(r['t_HC1'], 2)} | "
            f"{fmt_num(r['p_HC1'], 3)} | {fmt_num(r['adj_r2'], 3)} |"
        )

    desc_rows = []
    for var in ["Redundancy", "FInvention", "BHAR", "FSales_Growth", "RD_Asset", "Size", "Lev", "ROA", "Offerfee", "Age"]:
        r = desc[desc["variable"].eq(var)].iloc[0]
        desc_rows.append(
            f"| {var} | {int(r['N'])} | {fmt_num(r['mean'])} | {fmt_num(r['std'])} | "
            f"{fmt_num(r['p25'])} | {fmt_num(r['median'])} | {fmt_num(r['p75'])} |"
        )

    lines = [
        "# 原文表 2 经济后果试跑",
        "",
        "日期：2026-07-02",
        "",
        "## 结论",
        "",
        "这是一版探索性复刻，不是最终复刻。它使用当前 200 家文本冗余样本与已构造的上市后结果变量、基础控制变量合并，检验原文表 2 Panel B 的方向是否先跑得动。",
        "",
        "当前结果：",
        "",
        "- `FInvention` 主规格方向与原文相反，且不显著。",
        "- `BHAR` 简单回归为负，但加入文本长度、控制变量、年度 FE、行业 FE 后基本归零，未复现原文显著负向。",
        "- `FSales_Growth` 主规格方向与原文一致，但不显著；简单回归反而为正。",
        "- 定价机制的 `RD_Low × Redundancy_High` 用 `RD_Asset` 近似后，对 `Price_Issue` 和 `Price_Day5` 均未跑出原文预期的显著正向。",
        "",
        "因此，当前 200 家样本还不能说已经复刻原文经济后果结果。最可能的原因不是结果变量无法构造，而是文本 Redundancy 只覆盖 199 家已上市企业，且集中在 2019-2021 年；原文表 2 使用约 471 家企业，覆盖 2019-2023 年。",
        "",
        "## 口径",
        "",
        "- `Redundancy`：当前 `cot_v3b_scoregate_targeted_200` 企业层冗余度。",
        "- `FInvention`：`ln(1 + 上市后一年发明专利授权量)`。",
        "- `BHAR`：剔除上市首日后 252 个交易日买入持有超额收益，市场基准为科创板等权收益，1%/99% 缩尾。",
        "- `FSales_Growth`：上市后一年度营业收入增长率，1%/99% 缩尾。",
        "- 控制变量：`lnN_tech`、上市日前最近一期 1月1日/12月31日合并报表构造的 `Size`、`Lev`、`ROA`、发行费用 `Offerfee`、承销商声誉近似 `Underwriter`、上市年龄 `Age`，并加入上市年份 FE 与行业 FE。",
        "- 定价试跑：`Price_Issue` 和 `Price_Day5` 按每股净资产调整后，再除以样本行业均值；`RD_Low` 用 `RD_Asset` 样本底部 25% 近似。",
        "",
        "## 样本损失",
        "",
        "| 步骤 | N |",
        "|---|---:|",
        *[f"| {name} | {n} |" for name, n in sample_loss],
        "",
        "注：`688688` 蚂蚁集团没有真实上市交易，经济后果回归自动剔除。",
        "",
        "## 描述统计",
        "",
        "| 变量 | N | 均值 | 标准差 | p25 | 中位数 | p75 |",
        "|---|---:|---:|---:|---:|---:|---:|",
        *desc_rows,
        "",
        "## 表 2 Panel B 试跑：主规格",
        "",
        "主规格为 `Outcome ~ Redundancy + Controls + Year FE + Industry FE`，标准误为 HC1 robust。",
        "",
        "| 被解释变量 | N | 当前 coef | 当前 t | 当前 p | 当前 Adj.R2 | 原文 coef | 原文 t |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
        *panel_rows,
        "",
        "## 分规格结果",
        "",
        "| 被解释变量 | 规格 | N | coef | t | p | Adj.R2 |",
        "|---|---|---:|---:|---:|---:|---:|",
        *simple_rows,
        "",
        "## 定价机制试跑",
        "",
        "这一部分只用 `RD_Asset` 近似 `RD_Low`，因为当前尚未取得原文 `RD_Staff`。因此只能作为 smoke test。",
        "",
        "| 被解释变量 | N | 交互项 coef | t | p | Adj.R2 |",
        "|---|---:|---:|---:|---:|---:|",
        *pricing_rows,
        "",
        "## 文件",
        "",
        f"- master dataset：`{MASTER_OUT}`",
        f"- 回归结果：`{REG_OUT}`",
        f"- 描述统计：`{DESC_OUT}`",
        "",
        "## 下一步",
        "",
        "若只为了判断这篇文章能否复刻，下一步应优先把 Redundancy 扩到 2019-2023 年约 552 家，而不是继续在 200 家上调规格。当前结果最多说明：数据链路能跑通，但经济后果结果尚未在小样本中复现。",
        "",
    ]
    DOC_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    master = build_master()
    # Preserve raw values and add a few safety winsorized controls for inspection; the main
    # outcome variables already follow the prior variable-QC decision.
    master["RD_Asset_w1p"] = winsorize(master["RD_Asset"])
    master.to_csv(MASTER_OUT, index=False)

    desc = descriptives(master)
    desc.to_csv(DESC_OUT, index=False)

    regs = run_regressions(master)
    regs.to_csv(REG_OUT, index=False)

    write_doc(master, regs, desc)
    print(f"master={MASTER_OUT}")
    print(f"regressions={REG_OUT}")
    print(f"descriptives={DESC_OUT}")
    print(f"doc={DOC_OUT}")
    print(regs[["model", "dep_var", "target_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"]].to_string(index=False))


if __name__ == "__main__":
    main()
