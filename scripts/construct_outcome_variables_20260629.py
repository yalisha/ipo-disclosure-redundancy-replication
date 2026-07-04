#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
OUT_DIR = PROJECT / "results" / "outcome_variable_probe_20260629"

PATENT_ANNUAL = Path(
    "/Users/mac/computerscience/第三方资料/01_数据资源/国泰安/第三方数据资源/"
    "上市公司创新/企业创新韧性数据_20260621/上市公司创新韧性数据（2000-2024年）/"
    "原始数据/上市公司专利数据.xlsx"
)
INCOME_ANNUAL = Path(
    "/Users/mac/computerscience/23实证选题探索/T16/risk_disclosure_trial/data/"
    "financial_csmar_20260508/income_statement_annual_A_2015_2025.csv"
)
DAILY_RETURN = Path(
    "/Users/mac/computerscience/0做完了/15会计研究/v1/data_parquet/daily_return.parquet"
)

ORIGINAL = {
    "FInvention": {"N": 471, "mean": 2.282, "std": 1.200, "p25": 1.386, "median": 2.197, "p75": 2.890},
    "BHAR": {"N": 471, "mean": -0.036, "std": 0.514, "p25": -0.385, "median": -0.170, "p75": 0.162},
    "FSales_Growth": {"N": 471, "mean": 0.530, "std": 1.522, "p25": -0.008, "median": 0.180, "p75": 0.523},
}


def z6(value) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text.zfill(6) if text.isdigit() else text


def desc(series: pd.Series) -> dict:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        return {"N": 0, "mean": np.nan, "std": np.nan, "p25": np.nan, "median": np.nan, "p75": np.nan}
    return {
        "N": int(len(s)),
        "mean": float(s.mean()),
        "std": float(s.std(ddof=1)) if len(s) > 1 else np.nan,
        "p25": float(s.quantile(0.25)),
        "median": float(s.quantile(0.50)),
        "p75": float(s.quantile(0.75)),
    }


def winsorize(series: pd.Series, lower: float = 0.01, upper: float = 0.99) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    nonmissing = s.dropna()
    if nonmissing.empty:
        return s
    lo = nonmissing.quantile(lower)
    hi = nonmissing.quantile(upper)
    return s.clip(lo, hi)


def cumulative_return(returns: pd.Series) -> float:
    r = pd.to_numeric(returns, errors="coerce").dropna()
    if r.empty:
        return np.nan
    return float(np.prod(1.0 + r.to_numpy()) - 1.0)


def build_daily_and_universe() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    print("Loading daily returns...")
    daily = pd.read_parquet(
        DAILY_RETURN,
        columns=["Stkcd", "Trddt", "Dretwd", "Dretnd", "Dsmvosd", "Markettype"],
    )
    daily["code"] = daily["Stkcd"].map(z6)
    daily["trade_date"] = pd.to_datetime(daily["Trddt"], errors="coerce")
    daily["Dretwd"] = pd.to_numeric(daily["Dretwd"], errors="coerce")
    daily["Dretnd"] = pd.to_numeric(daily["Dretnd"], errors="coerce")
    daily["Dsmvosd"] = pd.to_numeric(daily["Dsmvosd"], errors="coerce")
    daily["Markettype"] = pd.to_numeric(daily["Markettype"], errors="coerce")

    star_daily = daily[(daily["Markettype"] == 32) & daily["code"].str.startswith("688", na=False)].copy()
    star_daily = star_daily.dropna(subset=["code", "trade_date"])

    universe = (
        star_daily.groupby("code")
        .agg(
            first_trade_date=("trade_date", "min"),
            last_trade_date=("trade_date", "max"),
            daily_obs=("Dretwd", "count"),
        )
        .reset_index()
    )
    start = pd.Timestamp("2019-07-22")
    end = pd.Timestamp("2023-12-31")
    universe = universe[(universe["first_trade_date"] >= start) & (universe["first_trade_date"] <= end)].copy()
    universe["listing_year"] = universe["first_trade_date"].dt.year
    universe["target_year"] = universe["listing_year"] + 1

    print(f"STAR daily pool rows: {len(star_daily):,}; IPO universe: {len(universe):,}")
    return daily, star_daily, universe


def build_market_returns(star_daily: pd.DataFrame) -> pd.DataFrame:
    print("Building STAR market benchmark returns...")
    pool = star_daily.dropna(subset=["trade_date", "Dretwd"]).copy()
    pool = pool[pool["Dsmvosd"].notna() & (pool["Dsmvosd"] > 0)]
    first_trade = pool.groupby("code", sort=False)["trade_date"].min().rename("stock_first_trade_date")
    pool = pool.merge(first_trade, on="code", how="left")
    # Exclude each stock's IPO first trading day from the market benchmark. Otherwise the
    # STAR benchmark mechanically absorbs every IPO underpricing jump in the sample period.
    before = len(pool)
    pool = pool[pool["trade_date"] > pool["stock_first_trade_date"]].copy()
    print(f"Market benchmark rows after excluding IPO first days: {len(pool):,} / {before:,}")

    def agg(group: pd.DataFrame) -> pd.Series:
        r = group["Dretwd"].astype(float)
        w = group["Dsmvosd"].astype(float)
        return pd.Series(
            {
                "mkt_ret_vw": float(np.average(r, weights=w)) if w.sum() > 0 else np.nan,
                "mkt_ret_ew": float(r.mean()),
                "mkt_n": int(r.notna().sum()),
                "mkt_weight_sum": float(w.sum()),
            }
        )

    market = pool.groupby("trade_date", sort=True).apply(agg, include_groups=False).reset_index()
    return market


def build_patent_variables(universe: pd.DataFrame) -> pd.DataFrame:
    print("Building patent variables...")
    pat = pd.read_excel(PATENT_ANNUAL, dtype={"股票代码": str})
    pat["code"] = pat["股票代码"].map(z6)
    pat["year"] = pd.to_numeric(pat["年份"], errors="coerce").astype("Int64")
    pat = pat.rename(
        columns={
            "股票简称": "short_name_patent",
            "首次上市年份": "listing_year_patent",
            "行业代码": "industry_code_patent",
            "行业名称": "industry_name_patent",
            "企业发明专利授权量": "invention_grant_count",
            "企业专利申请总量": "patent_application_total",
            "企业专利授权总量": "patent_grant_total",
        }
    )
    pat["listing_year_patent"] = pd.to_numeric(pat["listing_year_patent"], errors="coerce")
    for col in ["invention_grant_count", "patent_application_total", "patent_grant_total"]:
        pat[col] = pd.to_numeric(pat[col], errors="coerce")

    target = universe[["code", "target_year"]].rename(columns={"target_year": "year"})
    out = target.merge(
        pat[
            [
                "code",
                "year",
                "short_name_patent",
                "listing_year_patent",
                "industry_code_patent",
                "industry_name_patent",
                "invention_grant_count",
                "patent_application_total",
                "patent_grant_total",
            ]
        ],
        on=["code", "year"],
        how="left",
    ).drop_duplicates("code")
    out["FInvention_ln1p_auth"] = np.log1p(out["invention_grant_count"])
    out["FInvention_ln_auth"] = np.log(out["invention_grant_count"].where(out["invention_grant_count"] > 0))
    out["FInvention_ln1p_total_app"] = np.log1p(out["patent_application_total"])
    return out.drop(columns=["year"])


def build_sales_variables(universe: pd.DataFrame) -> pd.DataFrame:
    print("Building sales-growth variables...")
    inc = pd.read_csv(INCOME_ANNUAL, dtype={"Stkcd": str})
    inc["code"] = inc["Stkcd"].map(z6)
    inc["year"] = pd.to_numeric(inc["year"], errors="coerce").astype("Int64")
    inc["operating_revenue"] = pd.to_numeric(inc.get("operating_revenue"), errors="coerce")
    inc["total_operating_revenue"] = pd.to_numeric(inc.get("total_operating_revenue"), errors="coerce")
    inc["rev"] = inc["operating_revenue"].fillna(inc["total_operating_revenue"])
    inc = inc[inc["Typrep"].astype(str).eq("A")].copy()

    base = universe[["code", "listing_year", "target_year"]].copy()
    rev0 = inc[["code", "year", "rev", "operating_revenue", "total_operating_revenue"]].rename(
        columns={
            "year": "listing_year",
            "rev": "revenue_listing_year",
            "operating_revenue": "operating_revenue_listing_year",
            "total_operating_revenue": "total_operating_revenue_listing_year",
        }
    )
    rev1 = inc[["code", "year", "rev", "operating_revenue", "total_operating_revenue"]].rename(
        columns={
            "year": "target_year",
            "rev": "revenue_target_year",
            "operating_revenue": "operating_revenue_target_year",
            "total_operating_revenue": "total_operating_revenue_target_year",
        }
    )
    out = base.merge(rev0, on=["code", "listing_year"], how="left").merge(
        rev1, on=["code", "target_year"], how="left"
    )
    out["FSales_Growth_raw"] = np.where(
        out["revenue_listing_year"].notna()
        & out["revenue_target_year"].notna()
        & (out["revenue_listing_year"] != 0),
        (out["revenue_target_year"] - out["revenue_listing_year"]) / out["revenue_listing_year"],
        np.nan,
    )
    return out.drop(columns=["listing_year", "target_year"])


def bhar_one_window(
    firm_rows: pd.DataFrame,
    market: pd.DataFrame,
    *,
    skip_first: bool,
    window_days: int = 252,
) -> dict:
    rows = firm_rows.sort_values("trade_date").dropna(subset=["Dretwd"]).copy()
    if skip_first:
        rows = rows.iloc[1 : window_days + 1]
    else:
        rows = rows.iloc[:window_days]
    if len(rows) < window_days:
        return {
            "n_stock_days": int(len(rows)),
            "n_market_days": 0,
            "window_start": pd.NaT,
            "window_end": pd.NaT,
            "stock_bhr": np.nan,
            "market_bhr_vw": np.nan,
            "market_bhr_ew": np.nan,
            "BHAR_vw": np.nan,
            "BHAR_ew": np.nan,
        }
    merged = rows[["trade_date", "Dretwd"]].merge(market, on="trade_date", how="left")
    stock_bhr = cumulative_return(merged["Dretwd"])
    market_bhr_vw = cumulative_return(merged["mkt_ret_vw"])
    market_bhr_ew = cumulative_return(merged["mkt_ret_ew"])
    return {
        "n_stock_days": int(len(rows)),
        "n_market_days": int(merged["mkt_ret_vw"].notna().sum()),
        "window_start": rows["trade_date"].min(),
        "window_end": rows["trade_date"].max(),
        "stock_bhr": stock_bhr,
        "market_bhr_vw": market_bhr_vw,
        "market_bhr_ew": market_bhr_ew,
        "BHAR_vw": stock_bhr - market_bhr_vw if pd.notna(market_bhr_vw) else np.nan,
        "BHAR_ew": stock_bhr - market_bhr_ew if pd.notna(market_bhr_ew) else np.nan,
    }


def build_bhar_variables(star_daily: pd.DataFrame, universe: pd.DataFrame, market: pd.DataFrame) -> pd.DataFrame:
    print("Building BHAR variables...")
    code_set = set(universe["code"])
    rows = star_daily[star_daily["code"].isin(code_set)].copy()
    results = []
    for code, group in rows.groupby("code", sort=True):
        include = bhar_one_window(group, market, skip_first=False)
        exclude = bhar_one_window(group, market, skip_first=True)
        record = {"code": code}
        for prefix, payload in [("incl_first", include), ("excl_first", exclude)]:
            for key, value in payload.items():
                record[f"{prefix}_{key}"] = value
        results.append(record)
    return pd.DataFrame(results)


def build_descriptive_tables(firm: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    firm["FSales_Growth_w1p"] = winsorize(firm["FSales_Growth_raw"])
    for col in [
        "incl_first_BHAR_vw",
        "excl_first_BHAR_vw",
        "incl_first_BHAR_ew",
        "excl_first_BHAR_ew",
    ]:
        firm[f"{col}_w1p"] = winsorize(firm[col])

    variables = [
        ("FInvention", "FInvention_ln1p_auth", "ln(1+ invention grants)"),
        ("FInvention", "FInvention_ln_auth", "ln(invention grants), positive only"),
        ("FInvention", "FInvention_ln1p_total_app", "ln(1+ total patent applications), check only"),
        ("FSales_Growth", "FSales_Growth_raw", "raw"),
        ("FSales_Growth", "FSales_Growth_w1p", "winsor 1/99"),
        ("BHAR", "incl_first_BHAR_vw", "include first day, STAR value-weighted benchmark"),
        ("BHAR", "incl_first_BHAR_vw_w1p", "include first day, winsor 1/99"),
        ("BHAR", "excl_first_BHAR_vw", "exclude first day, STAR value-weighted benchmark"),
        ("BHAR", "excl_first_BHAR_vw_w1p", "exclude first day, winsor 1/99"),
        ("BHAR", "incl_first_BHAR_ew", "include first day, STAR equal-weighted benchmark"),
        ("BHAR", "incl_first_BHAR_ew_w1p", "include first day, STAR equal-weighted benchmark, winsor 1/99"),
        ("BHAR", "excl_first_BHAR_ew", "exclude first day, STAR equal-weighted benchmark"),
        ("BHAR", "excl_first_BHAR_ew_w1p", "exclude first day, STAR equal-weighted benchmark, winsor 1/99"),
    ]
    samples = [
        ("DAILY_STAR_2019_2023", firm["listing_year"].between(2019, 2023)),
        ("DAILY_STAR_2019_2022", firm["listing_year"].between(2019, 2022)),
        ("PATENT_STAR_2019_2023", firm["listing_year_patent"].between(2019, 2023)),
        ("PATENT_STAR_2019_2022", firm["listing_year_patent"].between(2019, 2022)),
        (
            "common_daily_2019_2023_excl_first",
            firm["listing_year"].between(2019, 2023)
            & firm["FInvention_ln1p_auth"].notna()
            & firm["FSales_Growth_raw"].notna()
            & firm["excl_first_BHAR_vw"].notna(),
        ),
        (
            "common_daily_2019_2022_excl_first",
            firm["listing_year"].between(2019, 2022)
            & firm["FInvention_ln1p_auth"].notna()
            & firm["FSales_Growth_raw"].notna()
            & firm["excl_first_BHAR_vw"].notna(),
        ),
        (
            "common_patent_2019_2023_excl_first",
            firm["listing_year_patent"].between(2019, 2023)
            & firm["FInvention_ln1p_auth"].notna()
            & firm["FSales_Growth_raw"].notna()
            & firm["excl_first_BHAR_vw"].notna(),
        ),
        (
            "common_patent_2019_2022_excl_first",
            firm["listing_year_patent"].between(2019, 2022)
            & firm["FInvention_ln1p_auth"].notna()
            & firm["FSales_Growth_raw"].notna()
            & firm["excl_first_BHAR_vw"].notna(),
        ),
    ]

    records = []
    for sample_name, mask in samples:
        subset = firm[mask].copy()
        for original_name, col, variant in variables:
            d = desc(subset[col])
            orig = ORIGINAL[original_name]
            rec = {
                "sample": sample_name,
                "variable": original_name,
                "column": col,
                "variant": variant,
                **d,
                "orig_N": orig["N"],
                "orig_mean": orig["mean"],
                "orig_std": orig["std"],
                "orig_p25": orig["p25"],
                "orig_median": orig["median"],
                "orig_p75": orig["p75"],
            }
            for key in ["mean", "std", "p25", "median", "p75"]:
                rec[f"diff_{key}"] = rec[key] - orig[key] if pd.notna(rec[key]) else np.nan
            rec["distance_quantiles"] = sum(abs(rec[f"diff_{k}"]) for k in ["p25", "median", "p75"] if pd.notna(rec[f"diff_{k}"]))
            rec["distance_all"] = sum(abs(rec[f"diff_{k}"]) for k in ["mean", "std", "p25", "median", "p75"] if pd.notna(rec[f"diff_{k}"]))
            records.append(rec)
    descriptive = pd.DataFrame(records)

    loss_records = []
    for sample_name, mask in [
        ("DAILY_STAR_2019_2023", firm["listing_year"].between(2019, 2023)),
        ("DAILY_STAR_2019_2022", firm["listing_year"].between(2019, 2022)),
        ("PATENT_STAR_2019_2023", firm["listing_year_patent"].between(2019, 2023)),
        ("PATENT_STAR_2019_2022", firm["listing_year_patent"].between(2019, 2022)),
    ]:
        subset = firm[mask].copy()
        steps = [
            ("universe", len(subset)),
            ("patent_target_year_present", int(subset["invention_grant_count"].notna().sum())),
            ("patent_positive_for_ln", int((subset["invention_grant_count"].fillna(0) > 0).sum())),
            ("sales_growth_available", int(subset["FSales_Growth_raw"].notna().sum())),
            ("bhar_include_first_available", int(subset["incl_first_BHAR_vw"].notna().sum())),
            ("bhar_exclude_first_available", int(subset["excl_first_BHAR_vw"].notna().sum())),
            (
                "common_ln1p_auth_sales_bhar_excl_first",
                int(
                    (
                        subset["FInvention_ln1p_auth"].notna()
                        & subset["FSales_Growth_raw"].notna()
                        & subset["excl_first_BHAR_vw"].notna()
                    ).sum()
                ),
            ),
            (
                "common_ln_auth_sales_bhar_excl_first",
                int(
                    (
                        subset["FInvention_ln_auth"].notna()
                        & subset["FSales_Growth_raw"].notna()
                        & subset["excl_first_BHAR_vw"].notna()
                    ).sum()
                ),
            ),
        ]
        for step, n in steps:
            loss_records.append({"sample": sample_name, "step": step, "N": n})
    loss = pd.DataFrame(loss_records)
    return descriptive, loss


def build_sales_winsor_sensitivity(firm: pd.DataFrame) -> pd.DataFrame:
    samples = [
        ("PATENT_STAR_2019_2023", firm["listing_year_patent"].between(2019, 2023)),
        ("PATENT_STAR_2019_2022", firm["listing_year_patent"].between(2019, 2022)),
        (
            "common_patent_2019_2023_excl_first",
            firm["listing_year_patent"].between(2019, 2023)
            & firm["FInvention_ln1p_auth"].notna()
            & firm["FSales_Growth_raw"].notna()
            & firm["excl_first_BHAR_ew"].notna(),
        ),
        (
            "common_patent_2019_2022_excl_first",
            firm["listing_year_patent"].between(2019, 2022)
            & firm["FInvention_ln1p_auth"].notna()
            & firm["FSales_Growth_raw"].notna()
            & firm["excl_first_BHAR_ew"].notna(),
        ),
    ]
    winsor_specs = [
        ("raw", None, None),
        ("0.5/99.5", 0.005, 0.995),
        ("1/99", 0.01, 0.99),
        ("2.5/97.5", 0.025, 0.975),
        ("5/95", 0.05, 0.95),
    ]

    rows = []
    orig = ORIGINAL["FSales_Growth"]
    for sample_name, mask in samples:
        series = pd.to_numeric(firm.loc[mask, "FSales_Growth_raw"], errors="coerce")
        for label, lower, upper in winsor_specs:
            adjusted = series if lower is None else winsorize(series, lower, upper)
            rec = {"sample": sample_name, "winsor": label, **desc(adjusted)}
            for key in ["mean", "std", "p25", "median", "p75"]:
                rec[f"diff_{key}"] = rec[key] - orig[key] if pd.notna(rec[key]) else np.nan
            rec["distance_all"] = sum(
                abs(rec[f"diff_{key}"])
                for key in ["mean", "std", "p25", "median", "p75"]
                if pd.notna(rec[f"diff_{key}"])
            )
            rows.append(rec)
    return pd.DataFrame(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    _, star_daily, universe = build_daily_and_universe()
    market = build_market_returns(star_daily)
    patent = build_patent_variables(universe)
    sales = build_sales_variables(universe)
    bhar = build_bhar_variables(star_daily, universe, market)

    firm = universe.merge(patent, on="code", how="left").merge(sales, on="code", how="left").merge(
        bhar, on="code", how="left"
    )
    firm = firm.sort_values(["listing_year", "first_trade_date", "code"])

    descriptive, loss = build_descriptive_tables(firm)
    sales_winsor_sensitivity = build_sales_winsor_sensitivity(firm)

    firm.to_csv(OUT_DIR / "outcome_variables_star_firm_level_20260629.csv", index=False)
    market.to_csv(OUT_DIR / "star_market_returns_constructed_20260629.csv", index=False)
    descriptive.to_csv(OUT_DIR / "outcome_descriptive_vs_original_20260629.csv", index=False)
    loss.to_csv(OUT_DIR / "outcome_sample_loss_20260629.csv", index=False)
    sales_winsor_sensitivity.to_csv(OUT_DIR / "sales_growth_winsor_sensitivity_20260629.csv", index=False)

    print("\nSaved outputs:")
    for name in [
        "outcome_variables_star_firm_level_20260629.csv",
        "star_market_returns_constructed_20260629.csv",
        "outcome_descriptive_vs_original_20260629.csv",
        "outcome_sample_loss_20260629.csv",
        "sales_growth_winsor_sensitivity_20260629.csv",
    ]:
        print(OUT_DIR / name)

    print("\nSample loss:")
    print(loss.to_string(index=False))
    print("\nClosest rows by variable/sample:")
    view = descriptive.sort_values(["variable", "sample", "distance_all"])
    cols = ["sample", "variable", "variant", "N", "mean", "std", "p25", "median", "p75", "distance_all"]
    print(view[cols].head(30).to_string(index=False))


if __name__ == "__main__":
    main()
