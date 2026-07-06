#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
from datetime import date
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd


PROJECT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
BASE_SCRIPT = PROJECT / "scripts/run_table2_len132_tight_audit_20260705.py"
MASTER_IN = (
    PROJECT
    / "results/table2_ipo_pre_controls_20260706/"
    "table2_ipo_pre_controls_master_20260706.csv"
)
DAILY_RETURN = Path("/Users/mac/computerscience/0做完了/15会计研究/v1/data_parquet/daily_return.parquet")
INCOME_ANNUAL = Path(
    "/Users/mac/computerscience/23实证选题探索/T16/risk_disclosure_trial/data/"
    "financial_csmar_20260508/income_statement_annual_A_2015_2025.csv"
)
MARKET_ZIP = Path(
    "/Users/mac/computerscience/第三方资料/90_临时下载待归档/股票市场/"
    "综合日市场回报率文件190104355(仅供四川大学使用).zip"
)

RUN_DIR = PROJECT / "results/table2_data_processing_breakpoints_20260706"
DOC_OUT = PROJECT / "docs/00_current/table2_data_processing_breakpoints_20260706.md"
BHAR_VARIANTS_OUT = RUN_DIR / "bhar_daily_window_processing_variants_20260706.csv"
BHAR_DESC_OUT = RUN_DIR / "bhar_daily_window_processing_descriptives_20260706.csv"
BHAR_REG_OUT = RUN_DIR / "bhar_daily_window_processing_regressions_20260706.csv"
FSALES_VARIANTS_OUT = RUN_DIR / "fsales_month_cutoff_processing_variants_20260706.csv"
FSALES_DESC_OUT = RUN_DIR / "fsales_month_cutoff_processing_descriptives_20260706.csv"
FSALES_REG_OUT = RUN_DIR / "fsales_month_cutoff_processing_regressions_20260706.csv"
SAMPLE_AUDIT_OUT = RUN_DIR / "table2_processing_sample_audit_20260706.csv"

CONTROL_VARS = [
    "lnN_tech",
    "Size_ipo_pre",
    "Lev_ipo_pre",
    "ROA_ipo_pre",
    "Offerfee",
    "Underwriter_ipo",
    "Age",
    "ScopeLen",
    "NumIndSeg",
    "NumProdSeg",
    "RD_Staff_ipo",
]
FE = " + C(listing_year_fe) + C(industry_fe)"


def load_base_module():
    spec = importlib.util.spec_from_file_location("table2_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_base_module()
ORIGINAL_BHAR = base.ORIGINAL_PANEL_A["BHAR"]
ORIGINAL_FSALES = base.ORIGINAL_PANEL_A["FSales_Growth"]


def z6(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text.zfill(6) if text.isdigit() else text


def stats(series: pd.Series) -> dict:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return {"N": 0, "mean": np.nan, "std": np.nan, "p25": np.nan, "median": np.nan, "p75": np.nan}
    return {
        "N": int(len(s)),
        "mean": float(s.mean()),
        "std": float(s.std(ddof=1)),
        "p25": float(s.quantile(0.25)),
        "median": float(s.median()),
        "p75": float(s.quantile(0.75)),
    }


def winsorize(series: pd.Series, lower: float = 0.01, upper: float = 0.99) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    ref = s.dropna()
    if ref.empty:
        return s
    return s.clip(ref.quantile(lower), ref.quantile(upper))


def compound_return(series: pd.Series) -> float:
    vals = pd.to_numeric(series, errors="coerce").dropna()
    vals = vals[vals.gt(-1)]
    if vals.empty:
        return np.nan
    return float(np.exp(np.log1p(vals).sum()) - 1.0)


def load_master() -> pd.DataFrame:
    df = pd.read_csv(MASTER_IN, dtype={"code": str, "sec_code": str}, encoding="utf-8-sig")
    df["code"] = df["code"].map(z6)
    df["sec_code"] = df["sec_code"].map(z6)
    df["first_trade_date"] = pd.to_datetime(df["first_trade_date"], errors="coerce")
    df["listing_year"] = pd.to_numeric(df["listing_year"], errors="coerce")
    df["listing_year_fe"] = pd.to_numeric(df["listing_year_fe"], errors="coerce").astype("Int64").astype(str)
    df["listing_year_fe"] = df["listing_year_fe"].replace({"<NA>": np.nan, "nan": np.nan})
    df["industry_fe"] = df["industry_fe"].astype(str).replace({"nan": np.nan, "<NA>": np.nan})
    numeric_cols = [
        "Redundancy",
        "BHAR",
        "FSales_Growth",
        "incl_first_stock_bhr",
        "excl_first_stock_bhr",
        *CONTROL_VARS,
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def load_daily(master: pd.DataFrame) -> pd.DataFrame:
    min_date = master["first_trade_date"].min() - pd.Timedelta(days=10)
    max_date = master["first_trade_date"].max() + pd.Timedelta(days=380)
    daily = pd.read_parquet(
        DAILY_RETURN,
        columns=["Stkcd", "Trddt", "Dretwd", "Dsmvosd", "Markettype"],
    )
    daily["code"] = daily["Stkcd"].map(z6)
    daily["trade_date"] = pd.to_datetime(daily["Trddt"], errors="coerce")
    daily["Dretwd"] = pd.to_numeric(daily["Dretwd"], errors="coerce")
    daily["Dsmvosd"] = pd.to_numeric(daily["Dsmvosd"], errors="coerce")
    daily["Markettype"] = pd.to_numeric(daily["Markettype"], errors="coerce")
    daily = daily[daily["trade_date"].between(min_date, max_date)].copy()
    return daily


def build_star_market(daily: pd.DataFrame, *, exclude_ipo_first_day: bool) -> pd.DataFrame:
    pool = daily[(daily["Markettype"].eq(32)) & daily["code"].str.startswith("688", na=False)].copy()
    pool = pool.dropna(subset=["code", "trade_date", "Dretwd", "Dsmvosd"])
    pool = pool[pool["Dsmvosd"].gt(0)].copy()
    if exclude_ipo_first_day:
        first = pool.groupby("code", sort=False)["trade_date"].min().rename("stock_first_trade_date")
        pool = pool.merge(first, on="code", how="left")
        pool = pool[pool["trade_date"].gt(pool["stock_first_trade_date"])].copy()

    def agg(group: pd.DataFrame) -> pd.Series:
        r = group["Dretwd"].astype(float)
        w = group["Dsmvosd"].astype(float)
        return pd.Series(
            {
                "mkt_star_vw": float(np.average(r, weights=w)) if w.sum() > 0 else np.nan,
                "mkt_star_ew": float(r.mean()),
                "mkt_star_n": int(r.notna().sum()),
            }
        )

    suffix = "exipo" if exclude_ipo_first_day else "all"
    out = pool.groupby("trade_date", sort=True).apply(agg, include_groups=False).reset_index()
    return out.rename(
        columns={
            "mkt_star_vw": f"mkt_star_{suffix}_vw",
            "mkt_star_ew": f"mkt_star_{suffix}_ew",
            "mkt_star_n": f"mkt_star_{suffix}_n",
        }
    )


def read_official_market(master: pd.DataFrame) -> pd.DataFrame:
    with ZipFile(MARKET_ZIP) as zf:
        with tempfile.NamedTemporaryFile(suffix=".dta") as tmp:
            tmp.write(zf.read("TRD_Cndalym.dta"))
            tmp.flush()
            mkt = pd.read_stata(
                tmp.name,
                convert_categoricals=False,
                columns=["Markettype", "Trddt", "Cdretwdos", "Cdretwdtl"],
            )
    min_date = master["first_trade_date"].min() - pd.Timedelta(days=10)
    max_date = master["first_trade_date"].max() + pd.Timedelta(days=380)
    mkt["Markettype"] = pd.to_numeric(mkt["Markettype"], errors="coerce")
    mkt["trade_date"] = pd.to_datetime(mkt["Trddt"], errors="coerce")
    mkt["Cdretwdos"] = pd.to_numeric(mkt["Cdretwdos"], errors="coerce")
    mkt["Cdretwdtl"] = pd.to_numeric(mkt["Cdretwdtl"], errors="coerce")
    mkt = mkt[mkt["Markettype"].isin([33, 53, 117]) & mkt["trade_date"].between(min_date, max_date)].copy()
    pieces = []
    for mt, sub in mkt.groupby("Markettype", sort=True):
        keep = sub[["trade_date", "Cdretwdos", "Cdretwdtl"]].copy()
        keep = keep.rename(
            columns={
                "Cdretwdos": f"mkt_cnd_m{int(mt)}_os",
                "Cdretwdtl": f"mkt_cnd_m{int(mt)}_tl",
            }
        )
        pieces.append(keep)
    out = pieces[0]
    for piece in pieces[1:]:
        out = out.merge(piece, on="trade_date", how="outer")
    return out.sort_values("trade_date")


def build_bhar_processing_variants(master: pd.DataFrame, daily: pd.DataFrame) -> pd.DataFrame:
    codes = set(master["code"].dropna())
    stock = daily[daily["code"].isin(codes)].dropna(subset=["code", "trade_date", "Dretwd"]).copy()
    markets = build_star_market(daily, exclude_ipo_first_day=True)
    markets = markets.merge(build_star_market(daily, exclude_ipo_first_day=False), on="trade_date", how="outer")
    markets = markets.merge(read_official_market(master), on="trade_date", how="outer")
    market_cols = [
        "mkt_star_exipo_vw",
        "mkt_star_exipo_ew",
        "mkt_star_all_vw",
        "mkt_cnd_m33_os",
        "mkt_cnd_m53_tl",
        "mkt_cnd_m117_tl",
    ]
    rows = []
    by_code = {code: sub.sort_values("trade_date") for code, sub in stock.groupby("code", sort=False)}
    for firm in master[["code", "sec_name", "listing_year", "first_trade_date", "BHAR"]].itertuples(index=False):
        sub = by_code.get(firm.code, pd.DataFrame())
        rec = {
            "code": firm.code,
            "sec_name": firm.sec_name,
            "listing_year": firm.listing_year,
            "first_trade_date": firm.first_trade_date,
            "BHAR_current": firm.BHAR,
        }
        if sub.empty or pd.isna(firm.first_trade_date):
            rows.append(rec)
            continue
        windows = {
            "td252_incl": sub[sub["trade_date"].ge(firm.first_trade_date)].head(252),
            "td252_excl": sub[sub["trade_date"].gt(firm.first_trade_date)].head(252),
            "cal365_incl": sub[
                sub["trade_date"].between(firm.first_trade_date, firm.first_trade_date + pd.Timedelta(days=365))
            ],
            "cal365_excl": sub[
                sub["trade_date"].gt(firm.first_trade_date)
                & sub["trade_date"].le(firm.first_trade_date + pd.Timedelta(days=365))
            ],
        }
        for win_name, win in windows.items():
            merged = win[["trade_date", "Dretwd"]].merge(markets, on="trade_date", how="left")
            rec[f"{win_name}_stock_days"] = int(merged["Dretwd"].notna().sum())
            rec[f"{win_name}_start"] = merged["trade_date"].min() if not merged.empty else pd.NaT
            rec[f"{win_name}_end"] = merged["trade_date"].max() if not merged.empty else pd.NaT
            stock_bhr = compound_return(merged["Dretwd"]) if rec[f"{win_name}_stock_days"] >= 180 else np.nan
            rec[f"{win_name}_stock_bhr"] = stock_bhr
            for mcol in market_cols:
                market_bhr = compound_return(merged[mcol]) if rec[f"{win_name}_stock_days"] >= 180 else np.nan
                rec[f"BHAR_{win_name}_{mcol.replace('mkt_', '')}"] = (
                    stock_bhr - market_bhr if pd.notna(stock_bhr) and pd.notna(market_bhr) else np.nan
                )
        rows.append(rec)
    return pd.DataFrame(rows)


def load_income() -> pd.DataFrame:
    cols = ["Stkcd", "Accper", "year", "Typrep", "operating_revenue", "total_operating_revenue"]
    inc = pd.read_csv(INCOME_ANNUAL, usecols=cols, dtype={"Stkcd": str, "Typrep": str})
    inc["code"] = inc["Stkcd"].map(z6)
    inc["Accper"] = pd.to_datetime(inc["Accper"], errors="coerce")
    inc["year"] = pd.to_numeric(inc["year"], errors="coerce").astype("Int64")
    inc = inc[inc["Typrep"].astype(str).eq("A")].copy()
    inc["revenue"] = pd.to_numeric(inc["operating_revenue"], errors="coerce").combine_first(
        pd.to_numeric(inc["total_operating_revenue"], errors="coerce")
    )
    inc = inc.sort_values(["code", "year", "Accper"]).drop_duplicates(["code", "year"], keep="last")
    return inc[["code", "year", "revenue"]]


def revenue_wide(inc: pd.DataFrame) -> pd.DataFrame:
    wide = inc.pivot(index="code", columns="year", values="revenue")
    wide.columns = [int(c) for c in wide.columns]
    return wide


def get_rev(wide: pd.DataFrame, code: str, year: int) -> float:
    if code not in wide.index or year not in wide.columns:
        return np.nan
    return wide.at[code, year]


def build_fsales_processing_variants(master: pd.DataFrame) -> pd.DataFrame:
    wide = revenue_wide(load_income())
    rows = []
    for firm in master[["code", "sec_name", "listing_year", "first_trade_date", "FSales_Growth"]].itertuples(index=False):
        rec = {
            "code": firm.code,
            "sec_name": firm.sec_name,
            "listing_year": firm.listing_year,
            "first_trade_date": firm.first_trade_date,
            "FSales_current": firm.FSales_Growth,
        }
        if pd.isna(firm.listing_year) or pd.isna(firm.first_trade_date):
            rows.append(rec)
            continue
        year = int(firm.listing_year)
        month = int(firm.first_trade_date.month)
        specs = {
            "L_to_L1": (year, year + 1),
            "L1_to_L2": (year + 1, year + 2),
            "Lm1_to_L1": (year - 1, year + 1),
            "month_cutoff_3": (year if month <= 3 else year + 1, year + 1 if month <= 3 else year + 2),
            "month_cutoff_6": (year if month <= 6 else year + 1, year + 1 if month <= 6 else year + 2),
            "month_cutoff_9": (year if month <= 9 else year + 1, year + 1 if month <= 9 else year + 2),
        }
        for name, (start_year, end_year) in specs.items():
            start = get_rev(wide, firm.code, start_year)
            end = get_rev(wide, firm.code, end_year)
            rec[f"FSales_{name}_raw"] = (end - start) / start if pd.notna(start) and pd.notna(end) and start != 0 else np.nan
            rec[f"FSales_{name}_start_year"] = start_year
            rec[f"FSales_{name}_end_year"] = end_year
            rec[f"FSales_{name}_start_revenue"] = start
            rec[f"FSales_{name}_end_revenue"] = end
        rows.append(rec)
    out = pd.DataFrame(rows)
    for col in [c for c in out.columns if c.startswith("FSales_") and c.endswith("_raw")]:
        out[col.replace("_raw", "_w1p")] = winsorize(out[col])
    return out


def distance(st: dict, original: dict) -> float:
    if st["N"] == 0:
        return np.inf
    return sum(abs(st[k] - original[k]) for k in ["mean", "std", "p25", "median", "p75"] if pd.notna(st[k]))


def build_desc(df: pd.DataFrame, original: dict, prefix: str) -> pd.DataFrame:
    rows = []
    samples = {
        "full_2019_2023": df.index == df.index,
        "w2_2019_2022": pd.to_numeric(df["listing_year"], errors="coerce").between(2019, 2022),
    }
    candidates = [c for c in df.columns if c.startswith(prefix)]
    if prefix == "BHAR_":
        candidates = [
            "BHAR_current",
            *[c for c in candidates if c != "BHAR_current" and not c.endswith("_stock_bhr")],
        ]
    elif prefix == "FSales_":
        candidates = ["FSales_current", *[c for c in candidates if c.endswith("_w1p")]]
    for sample, mask in samples.items():
        for col in candidates:
            st = stats(df.loc[mask, col])
            rows.append(
                {
                    "sample": sample,
                    "variable": col,
                    **st,
                    "original_N": original["N"],
                    "original_mean": original["mean"],
                    "original_std": original["std"],
                    "original_p25": original["p25"],
                    "original_median": original["median"],
                    "original_p75": original["p75"],
                    "distance_all": distance(st, original),
                }
            )
    return pd.DataFrame(rows).sort_values(["sample", "distance_all", "variable"])


def run_regs(master: pd.DataFrame, variants: pd.DataFrame, dep_candidates: list[str]) -> pd.DataFrame:
    df = master.merge(
        variants.drop(columns=["sec_name", "listing_year", "first_trade_date"], errors="ignore"),
        on="code",
        how="left",
    )
    rows = []
    samples = [
        ("full_2019_2023", df.copy()),
        ("w2_2019_2022", df[pd.to_numeric(df["listing_year"], errors="coerce").between(2019, 2022)].copy()),
    ]
    rhs = " + ".join(CONTROL_VARS)
    for sample, sub in samples:
        for dep in dep_candidates:
            if dep not in sub.columns:
                continue
            formula = f"{dep} ~ Redundancy + {rhs}{FE}"
            rows.append(base.regression_result(sample, "ipo_pre_fin_controls_rd_staff", dep, formula, sub, "Redundancy"))
    return pd.DataFrame(rows)


def build_sample_audit(master: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for sample_name, mask in [
        ("full_2019_2023", master.index == master.index),
        ("w2_2019_2022", master["listing_year"].between(2019, 2022)),
    ]:
        sub = master[mask].copy()
        checks = [
            ("universe", pd.Series(True, index=sub.index)),
            ("Redundancy nonmissing", sub["Redundancy"].notna()),
            ("BHAR nonmissing", sub["BHAR"].notna()),
            ("FSales_Growth nonmissing", sub["FSales_Growth"].notna()),
            ("all controls nonmissing", sub[CONTROL_VARS].notna().all(axis=1)),
            ("BHAR regression complete", sub[["BHAR", "Redundancy", *CONTROL_VARS, "listing_year_fe", "industry_fe"]].notna().all(axis=1)),
            ("FSales regression complete", sub[["FSales_Growth", "Redundancy", *CONTROL_VARS, "listing_year_fe", "industry_fe"]].notna().all(axis=1)),
        ]
        for label, cond in checks:
            rows.append({"sample": sample_name, "step": label, "N": int(cond.sum())})
    return pd.DataFrame(rows)


def fmt(value: object, digits: int = 3) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.{digits}f}"
    return str(value)


def md_table(df: pd.DataFrame, cols: list[str], digits: int = 3, max_rows: int | None = None) -> list[str]:
    view = df if max_rows is None else df.head(max_rows)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in view.iterrows():
        lines.append("| " + " | ".join(fmt(row.get(col, np.nan), digits) for col in cols) + " |")
    return lines


def build_doc(
    sample_audit: pd.DataFrame,
    bhar_desc: pd.DataFrame,
    bhar_regs: pd.DataFrame,
    fsales_desc: pd.DataFrame,
    fsales_regs: pd.DataFrame,
) -> None:
    desc_cols = ["sample", "variable", "N", "mean", "std", "p25", "median", "p75", "distance_all"]
    reg_cols = ["sample", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"]
    bhar_best_w2 = bhar_desc[bhar_desc["sample"].eq("w2_2019_2022")].head(10)
    fsales_best_w2 = fsales_desc[fsales_desc["sample"].eq("w2_2019_2022")].head(10)
    bhar_reg_key = bhar_regs[
        bhar_regs["sample"].eq("w2_2019_2022")
        & bhar_regs["dep_var"].isin(["BHAR", *bhar_best_w2["variable"].tolist()])
    ].copy()
    fsales_reg_key = fsales_regs[
        fsales_regs["sample"].eq("w2_2019_2022")
        & fsales_regs["dep_var"].isin(["FSales_Growth", *fsales_best_w2["variable"].tolist()])
    ].copy()
    lines = [
        "# Table 2 数据处理断点审计",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 为什么做这个审计",
        "",
        "当前 X 的量级已经贴近原文，`BHAR` 和 `FSales_Growth` 仍不复刻。这里不再调 X，而是把最可能的数据处理断点拆开：",
        "",
        "- `BHAR`：252 交易日 vs 365 自然日；首日纳入/剔除；自建 STAR 市场基准 vs CSMAR 官方综合市场基准。",
        "- `FSales_Growth`：`listing_year -> listing_year+1`、`listing_year+1 -> listing_year+2`、以及按上市月份切换完整会计年度。",
        "- 样本：原文 Table 2 N=471；当前 2019-2022 outcome 样本约 474，但 controls 完整后主规格 N=459。",
        "",
        "## 样本链条",
        "",
        *md_table(sample_audit, ["sample", "step", "N"], digits=0),
        "",
        "## BHAR 处理断点",
        "",
        "2019-2022 描述统计最接近原文的候选：",
        "",
        *md_table(bhar_best_w2[desc_cols], desc_cols, digits=3),
        "",
        "这些候选的主规格回归：",
        "",
        *md_table(bhar_reg_key[reg_cols], reg_cols, digits=4),
        "",
        "## FSales_Growth 处理断点",
        "",
        "2019-2022 描述统计最接近原文的候选：",
        "",
        *md_table(fsales_best_w2[desc_cols], desc_cols, digits=3),
        "",
        "这些候选的主规格回归：",
        "",
        *md_table(fsales_reg_key[reg_cols], reg_cols, digits=4),
        "",
        "## 判断",
        "",
        "- `BHAR` 确实存在窗口/基准处理差异：365 自然日、剔除首日、STAR 等权基准比当前主口径更贴原文分布；但所有可观察日度窗口候选在主规格里仍为正且不显著。",
        "- `FSales_Growth` 的简单窗口切换不能解释差距：当前 `L -> L+1` 反而最贴原文分布；`L+1 -> L+2` 或按上市月份切换会让系数弱负/接近 0，但分布明显远离原文。",
        "- 下一步不建议再扩大网格盲试，应优先核原文作者实际使用的数据字段名、winsor 样本和 471 家样本剔除规则。",
        "",
        "## 输出",
        "",
        f"- BHAR variants：`{BHAR_VARIANTS_OUT}`",
        f"- BHAR descriptives：`{BHAR_DESC_OUT}`",
        f"- BHAR regressions：`{BHAR_REG_OUT}`",
        f"- FSales variants：`{FSALES_VARIANTS_OUT}`",
        f"- FSales descriptives：`{FSALES_DESC_OUT}`",
        f"- FSales regressions：`{FSALES_REG_OUT}`",
        f"- sample audit：`{SAMPLE_AUDIT_OUT}`",
        "",
    ]
    DOC_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    master = load_master()
    sample_audit = build_sample_audit(master)
    daily = load_daily(master)
    bhar_variants = build_bhar_processing_variants(master, daily)
    bhar_desc = build_desc(bhar_variants, ORIGINAL_BHAR, "BHAR_")
    bhar_dep = ["BHAR"] + [
        c for c in bhar_variants.columns if c.startswith("BHAR_") and not c.endswith("_stock_bhr") and c != "BHAR_current"
    ]
    bhar_regs = run_regs(master, bhar_variants, bhar_dep)
    fsales_variants = build_fsales_processing_variants(master)
    fsales_desc = build_desc(fsales_variants, ORIGINAL_FSALES, "FSales_")
    fsales_dep = ["FSales_Growth"] + [c for c in fsales_variants.columns if c.startswith("FSales_") and c.endswith("_w1p")]
    fsales_regs = run_regs(master, fsales_variants, fsales_dep)

    sample_audit.to_csv(SAMPLE_AUDIT_OUT, index=False, encoding="utf-8-sig")
    bhar_variants.to_csv(BHAR_VARIANTS_OUT, index=False, encoding="utf-8-sig")
    bhar_desc.to_csv(BHAR_DESC_OUT, index=False, encoding="utf-8-sig")
    bhar_regs.to_csv(BHAR_REG_OUT, index=False, encoding="utf-8-sig")
    fsales_variants.to_csv(FSALES_VARIANTS_OUT, index=False, encoding="utf-8-sig")
    fsales_desc.to_csv(FSALES_DESC_OUT, index=False, encoding="utf-8-sig")
    fsales_regs.to_csv(FSALES_REG_OUT, index=False, encoding="utf-8-sig")
    build_doc(sample_audit, bhar_desc, bhar_regs, fsales_desc, fsales_regs)

    print(f"doc={DOC_OUT}")
    print("BHAR best w2:")
    print(bhar_desc[bhar_desc["sample"].eq("w2_2019_2022")].head(8).to_string(index=False))
    print("\nFSales best w2:")
    print(fsales_desc[fsales_desc["sample"].eq("w2_2019_2022")].head(8).to_string(index=False))


if __name__ == "__main__":
    main()
