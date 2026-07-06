#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import re
from datetime import date
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd


PROJECT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
BASE_SCRIPT = PROJECT / "scripts/run_table2_len132_tight_audit_20260705.py"
MASTER_IN = (
    PROJECT
    / "results/table2_listing_year_segment_controls_20260706/"
    "table2_listing_year_segment_controls_master_20260706.csv"
)
IPO_ROOT = Path("/Users/mac/computerscience/第三方资料/90_临时下载待归档/IPO库")

IPO_BASIC_ZIP = IPO_ROOT / "招股及上市基本情况表173730614(仅供四川大学使用).zip"
IPO_BALANCE_ZIP = IPO_ROOT / "招股前资产负债表173719286(仅供四川大学使用).zip"
IPO_INCOME_ZIP = IPO_ROOT / "招股前利润表173641455(仅供四川大学使用).zip"
IPO_UNDERWRITER_ZIP = IPO_ROOT / "招股承销商表173827384(仅供四川大学使用).zip"
IPO_EMPLOYEE_ZIP = IPO_ROOT / "招股时公司职工人数情况表173739831(仅供四川大学使用).zip"

RUN_DIR = PROJECT / "results/table2_ipo_pre_controls_20260706"
DOC_OUT = PROJECT / "docs/00_current/table2_ipo_pre_controls_rerun_20260706.md"

MASTER_OUT = RUN_DIR / "table2_ipo_pre_controls_master_20260706.csv"
DESC_OUT = RUN_DIR / "table2_ipo_pre_controls_descriptives_20260706.csv"
REG_OUT = RUN_DIR / "table2_ipo_pre_controls_regressions_20260706.csv"
SOURCE_AUDIT_OUT = RUN_DIR / "table2_ipo_pre_controls_source_audit_20260706.csv"
UNDERWRITER_TOP10_OUT = RUN_DIR / "table2_ipo_pre_controls_underwriter_top10_20260706.csv"
EMPLOYEE_ROWS_OUT = RUN_DIR / "table2_ipo_pre_controls_employee_rows_20260706.csv"
FIN_ROWS_OUT = RUN_DIR / "table2_ipo_pre_controls_pre_fin_rows_20260706.csv"


def load_base_module():
    spec = importlib.util.spec_from_file_location("table2_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_base_module()

OUTCOMES = ["FInvention", "BHAR", "FSales_Growth"]
ORIGINAL_PANEL_A = base.ORIGINAL_PANEL_A
FE_VARS = ["listing_year_fe", "industry_fe"]


def z6(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)


def normalize_name(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = re.sub(r"\s+", "", str(value).strip())
    return text or None


def md_table(df: pd.DataFrame, cols: list[str], digits: int = 3) -> list[str]:
    return base.md_table(df, cols, digits=digits)


def stats(series: pd.Series) -> dict:
    s = pd.to_numeric(series, errors="coerce").dropna()
    return {
        "N": int(len(s)),
        "mean": s.mean(),
        "std": s.std(ddof=1),
        "p25": s.quantile(0.25),
        "median": s.median(),
        "p75": s.quantile(0.75),
    }


def winsorize(series: pd.Series, p: float = 0.01) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    nonmiss = s.dropna()
    if nonmiss.empty:
        return s
    lo = nonmiss.quantile(p)
    hi = nonmiss.quantile(1 - p)
    return s.clip(lower=lo, upper=hi)


def read_dta_from_zip(zip_path: Path, member: str, columns: list[str] | None = None) -> pd.DataFrame:
    with ZipFile(zip_path) as zf:
        raw = zf.read(member)
    return pd.read_stata(BytesIO(raw), columns=columns, convert_categoricals=False)


def load_master() -> pd.DataFrame:
    df = pd.read_csv(MASTER_IN, dtype={"sec_code": str, "code": str}, encoding="utf-8-sig")
    df["code"] = z6(df["code"] if "code" in df.columns else df["sec_code"])
    df["sec_code"] = z6(df["sec_code"])
    for col in [
        "Redundancy",
        "lnN_tech",
        *OUTCOMES,
        "Size",
        "Lev",
        "ROA",
        "Offerfee",
        "Underwriter",
        "Age",
        "ScopeLen",
        "NumIndSeg",
        "NumProdSeg",
        "RD_Staff",
        "RD_Asset",
        "revenue_target_year",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["listing_year"] = pd.to_numeric(df["listing_year"], errors="coerce")
    df["listing_year_fe"] = pd.to_numeric(df["listing_year_fe"], errors="coerce").astype("Int64").astype(str)
    df["listing_year_fe"] = df["listing_year_fe"].replace({"<NA>": np.nan, "nan": np.nan})
    df["industry_fe"] = df["industry_fe"].astype(str).replace({"nan": np.nan, "<NA>": np.nan})
    return df


def build_table_coverage(master: pd.DataFrame) -> pd.DataFrame:
    specs = [
        ("IPO_Ipobasic", IPO_BASIC_ZIP, "IPO_Ipobasic.dta", "招股及上市基本情况表"),
        ("IPO_IpoBalance", IPO_BALANCE_ZIP, "IPO_IpoBalance.dta", "招股前资产负债表"),
        ("IPO_IpoIncome", IPO_INCOME_ZIP, "IPO_IpoIncome.dta", "招股前利润表"),
        ("IPO_Ipocsne", IPO_UNDERWRITER_ZIP, "IPO_Ipocsne.dta", "招股承销商表"),
        ("IPO_Iponoem", IPO_EMPLOYEE_ZIP, "IPO_Iponoem.dta", "招股时公司职工人数情况表"),
    ]
    codes = set(master["code"].dropna().astype(str))
    rows = []
    for table, zip_path, member, label in specs:
        df = read_dta_from_zip(zip_path, member, columns=["Stkcd"])
        table_codes = set(z6(df["Stkcd"]).dropna().astype(str))
        rows.append(
            {
                "table": table,
                "label": label,
                "rows": int(len(df)),
                "sample_firm_coverage": int(len(codes & table_codes)),
                "sample_firm_total": int(len(codes)),
                "zip_file": zip_path.name,
            }
        )
    return pd.DataFrame(rows)


def read_ipo_basic() -> pd.DataFrame:
    cols = ["Stkcd", "Listdt", "Subbgdt", "Grsprc", "Fltcst", "Tludwfe", "Sponsfm"]
    df = read_dta_from_zip(IPO_BASIC_ZIP, "IPO_Ipobasic.dta", cols)
    df["code"] = z6(df["Stkcd"])
    df["Listdt"] = pd.to_datetime(df["Listdt"], errors="coerce")
    df["list_year"] = df["Listdt"].dt.year
    df["Sponsfm_clean_new_basic"] = df["Sponsfm"].map(normalize_name)
    for col in ["Grsprc", "Fltcst", "Tludwfe"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def build_ipocsne_underwriter(master: pd.DataFrame, ipo_basic: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    under = read_dta_from_zip(
        IPO_UNDERWRITER_ZIP,
        "IPO_Ipocsne.dta",
        ["Stkcd", "Subbgdt", "Udwnm", "Udwtp", "Pstudw", "Nstudw"],
    )
    under["code"] = z6(under["Stkcd"])
    under["Udwnm_clean"] = under["Udwnm"].map(normalize_name)
    under["Udwtp"] = pd.to_numeric(under["Udwtp"], errors="coerce")
    under["Pstudw"] = pd.to_numeric(under["Pstudw"], errors="coerce")
    under["Nstudw"] = pd.to_numeric(under["Nstudw"], errors="coerce")
    main = under[under["Udwtp"].eq(1.0) & under["Udwnm_clean"].notna()].copy()

    basic_one = ipo_basic.sort_values(["code", "Listdt"]).drop_duplicates("code", keep="last")
    main = main.merge(basic_one[["code", "Listdt", "list_year", "Grsprc"]], on="code", how="left")
    main = main[main["list_year"].between(2019, 2023, inclusive="both")].copy()
    main_count = main.groupby("code")["Udwnm_clean"].transform("count")
    main["equal_weight"] = np.where(main_count.gt(0), 1.0 / main_count, np.nan)
    main["pstudw_weight"] = np.where(main["Pstudw"].notna(), main["Pstudw"] / 100.0, main["equal_weight"])
    main["deal_grsprc_full"] = main["Grsprc"]
    main["deal_grsprc_weighted"] = main["Grsprc"] * main["pstudw_weight"]

    variants = {
        "Underwriter_ipocsne_pool_count": ("pool", "count", None),
        "Underwriter_ipocsne_pool_grsprc_full": ("pool", "sum", "deal_grsprc_full"),
        "Underwriter_ipocsne_pool_grsprc_weighted": ("pool", "sum", "deal_grsprc_weighted"),
        "Underwriter_ipocsne_annual_count": ("annual", "count", None),
        "Underwriter_ipocsne_annual_grsprc_full": ("annual", "sum", "deal_grsprc_full"),
        "Underwriter_ipocsne_annual_grsprc_weighted": ("annual", "sum", "deal_grsprc_weighted"),
    }

    top_sets: dict[str, set[str] | dict[int, set[str]]] = {}
    top_rows: list[dict] = []
    for name, (scope, method, amount_col) in variants.items():
        if scope == "pool":
            if method == "count":
                rank = main.groupby("Udwnm_clean").size().sort_values(ascending=False)
            else:
                rank = main.groupby("Udwnm_clean")[amount_col].sum(min_count=1).sort_values(ascending=False)
            rank = rank.dropna()
            top_sets[name] = set(rank.head(10).index)
            for idx, (firm, value) in enumerate(rank.head(10).items(), 1):
                top_rows.append({"variant": name, "year": "2019-2023", "rank": idx, "firm": firm, "rank_value": value})
        else:
            by_year: dict[int, set[str]] = {}
            for year, sub in main.groupby("list_year"):
                if method == "count":
                    rank = sub.groupby("Udwnm_clean").size().sort_values(ascending=False)
                else:
                    rank = sub.groupby("Udwnm_clean")[amount_col].sum(min_count=1).sort_values(ascending=False)
                rank = rank.dropna()
                by_year[int(year)] = set(rank.head(10).index)
                for idx, (firm, value) in enumerate(rank.head(10).items(), 1):
                    top_rows.append({"variant": name, "year": int(year), "rank": idx, "firm": firm, "rank_value": value})
            top_sets[name] = by_year

    flags = master[["code", "sec_code", "sec_name", "listing_year"]].drop_duplicates("code").copy()
    code_names = main.groupby("code")["Udwnm_clean"].agg(lambda x: ";".join(sorted(set(x)))).reset_index()
    flags = flags.merge(code_names, on="code", how="left")
    main_lookup = main[["code", "Udwnm_clean", "list_year"]].drop_duplicates()
    for name, top in top_sets.items():
        if isinstance(top, dict):
            code_flag = (
                main_lookup.assign(
                    is_top=lambda x: x.apply(
                        lambda row: row["Udwnm_clean"] in top.get(int(row["list_year"]), set())
                        if pd.notna(row["list_year"])
                        else False,
                        axis=1,
                    )
                )
                .groupby("code")["is_top"]
                .max()
                .astype(float)
                .reset_index(name=name)
            )
        else:
            code_flag = (
                main_lookup.assign(is_top=lambda x: x["Udwnm_clean"].isin(top))
                .groupby("code")["is_top"]
                .max()
                .astype(float)
                .reset_index(name=name)
            )
        flags = flags.merge(code_flag, on="code", how="left")

    # Main definition: annual top-10 main underwriter by IPO gross proceeds.
    # Co-main underwriters receive full-deal credit; weighted credit is kept as
    # a sensitivity check because CSMAR's Pstudw is often missing.
    flags["Underwriter_ipo"] = flags["Underwriter_ipocsne_annual_grsprc_full"]
    audit = []
    for name in [*variants.keys(), "Underwriter_ipo"]:
        source = (
            "IPO_Ipocsne main underwriters; annual gross-proceeds Top10, full-deal credit"
            if name == "Underwriter_ipo"
            else "IPO_Ipocsne main underwriters; Top10 variants, full/weighted/count"
        )
        audit.append(
            {
                "variable": name,
                "source": source,
                **stats(flags[name]),
                "original_mean": ORIGINAL_PANEL_A["Underwriter"]["mean"],
                "original_median": ORIGINAL_PANEL_A["Underwriter"]["median"],
            }
        )
    return flags, pd.DataFrame(audit), pd.DataFrame(top_rows)


def build_ipo_rd_staff(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rows = read_dta_from_zip(
        IPO_EMPLOYEE_ZIP,
        "IPO_Iponoem.dta",
        ["Stkcd", "Subbgdt", "Statrange", "Stattype", "Emptype", "Number"],
    )
    rows["code"] = z6(rows["Stkcd"])
    rows["Number"] = pd.to_numeric(rows["Number"], errors="coerce")
    rows["Stattype_str"] = rows["Stattype"].astype(str).str.strip()
    rows["range_priority"] = rows["Statrange"].map({"B": 0, "A": 1}).fillna(9)
    sample_codes = set(master["code"].dropna().astype(str))
    rows = rows[rows["code"].isin(sample_codes)].copy()

    total = (
        rows[rows["Stattype_str"].eq("0")]
        .sort_values(["code", "range_priority", "Number"], ascending=[True, True, False])
        .drop_duplicates("code", keep="first")
        [["code", "Statrange", "Number"]]
        .rename(columns={"Statrange": "employee_total_range", "Number": "employee_total"})
    )
    prof = rows[rows["Stattype_str"].eq("8")].copy()
    prof["is_rd_contains"] = prof["Emptype"].astype(str).str.contains("研发", na=False)
    prof["is_rd_exact_core"] = prof["Emptype"].astype(str).str.fullmatch(r"(研发人员|研发技术人员|技术研发人员|研发及技术人员)", na=False)
    rd_contains = (
        prof[prof["is_rd_contains"]].groupby("code")["Number"].sum(min_count=1).reset_index(name="employee_rd_contains")
    )
    rd_exact = prof[prof["is_rd_exact_core"]].groupby("code")["Number"].sum(min_count=1).reset_index(name="employee_rd_exact_core")
    prof_any = prof.groupby("code").size().reset_index(name="employee_professional_rows")
    out = master[["code", "sec_code", "sec_name"]].drop_duplicates("code").merge(total, on="code", how="left")
    out = out.merge(rd_contains, on="code", how="left").merge(rd_exact, on="code", how="left").merge(prof_any, on="code", how="left")
    out["employee_rd_contains"] = out["employee_rd_contains"].fillna(0)
    out["employee_rd_exact_core"] = out["employee_rd_exact_core"].fillna(0)
    out["RD_Staff_ipo"] = np.where(out["employee_total"].gt(0), out["employee_rd_contains"] / out["employee_total"], np.nan)
    out["RD_Staff_ipo_exact_core"] = np.where(
        out["employee_total"].gt(0), out["employee_rd_exact_core"] / out["employee_total"], np.nan
    )
    audit = pd.DataFrame(
        [
            {
                "variable": "RD_Staff_ipo",
                "source": "IPO_Iponoem, Stattype=8 rows containing 研发 / Stattype=0 total staff",
                **stats(out["RD_Staff_ipo"]),
                "original_mean": ORIGINAL_PANEL_A["RD_Staff"]["mean"],
                "original_median": ORIGINAL_PANEL_A["RD_Staff"]["median"],
            },
            {
                "variable": "RD_Staff_ipo_exact_core",
                "source": "IPO_Iponoem, exact core R&D labels / total staff",
                **stats(out["RD_Staff_ipo_exact_core"]),
                "original_mean": ORIGINAL_PANEL_A["RD_Staff"]["mean"],
                "original_median": ORIGINAL_PANEL_A["RD_Staff"]["median"],
            },
            {
                "variable": "employee_total_available",
                "source": "IPO_Iponoem, Stattype=0",
                "N": int(out["employee_total"].notna().sum()),
                "mean": np.nan,
                "std": np.nan,
                "p25": np.nan,
                "median": np.nan,
                "p75": np.nan,
                "original_mean": np.nan,
                "original_median": np.nan,
            },
        ]
    )
    return out, audit, rows


def annual_state_a(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["code"] = z6(df["Stkcd"])
    df["Accper_dt"] = pd.to_datetime(df["Accper"], errors="coerce")
    df["fin_year"] = df["Accper_dt"].dt.year
    return df[
        df["StateTypeCode"].eq("A")
        & df["Accper_dt"].dt.month.eq(12)
        & df["Accper_dt"].dt.day.eq(31)
        & df["fin_year"].notna()
    ].copy()


def build_ipo_pre_financials(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    bal = read_dta_from_zip(
        IPO_BALANCE_ZIP,
        "IPO_IpoBalance.dta",
        ["Stkcd", "Accper", "StateTypeCode", "A001", "A002", "A001219"],
    )
    inc = read_dta_from_zip(
        IPO_INCOME_ZIP,
        "IPO_IpoIncome.dta",
        ["Stkcd", "Accper", "StateTypeCode", "B001101", "B0011", "B001201", "B002"],
    )
    bal = annual_state_a(bal)
    inc = annual_state_a(inc)
    for col in ["A001", "A002", "A001219"]:
        bal[col] = pd.to_numeric(bal[col], errors="coerce")
    for col in ["B001101", "B0011", "B001201", "B002"]:
        inc[col] = pd.to_numeric(inc[col], errors="coerce")

    fin = bal.merge(
        inc[["code", "fin_year", "B001101", "B0011", "B001201", "B002"]],
        on=["code", "fin_year"],
        how="inner",
        validate="one_to_one",
    )
    keys = master[["code", "sec_code", "sec_name", "listing_year", "revenue_target_year"]].drop_duplicates("code").copy()
    keys["pre_target_year"] = pd.to_numeric(keys["listing_year"], errors="coerce") - 1
    cand = fin.merge(keys, on="code", how="inner")
    cand = cand[cand["fin_year"].le(cand["pre_target_year"])].copy()
    cand["pre_year_gap"] = cand["pre_target_year"] - cand["fin_year"]
    cand["strict_lag1"] = cand["pre_year_gap"].eq(0)
    cand = cand.sort_values(["code", "fin_year"], ascending=[True, False])
    latest = cand.drop_duplicates("code", keep="first").copy()
    strict = cand[cand["strict_lag1"]].drop_duplicates("code", keep="first").copy()

    def attach(prefix: str, frame: pd.DataFrame) -> pd.DataFrame:
        out = keys[["code"]].merge(
            frame[
                [
                    "code",
                    "fin_year",
                    "pre_year_gap",
                    "A001",
                    "A002",
                    "A001219",
                    "B001101",
                    "B0011",
                    "B001201",
                    "B002",
                ]
            ],
            on="code",
            how="left",
        )
        out = out.rename(
            columns={
                "fin_year": f"{prefix}_fin_year",
                "pre_year_gap": f"{prefix}_year_gap",
                "A001": f"{prefix}_asset",
                "A002": f"{prefix}_liability",
                "A001219": f"{prefix}_dev_expenditure",
                "B001101": f"{prefix}_sales",
                "B0011": f"{prefix}_total_sales",
                "B001201": f"{prefix}_sales_cost",
                "B002": f"{prefix}_net_profit",
            }
        )
        asset = pd.to_numeric(out[f"{prefix}_asset"], errors="coerce")
        out[f"Size_{prefix}"] = np.where(asset.gt(0), np.log(asset), np.nan)
        out[f"Lev_{prefix}"] = np.where(asset.gt(0), out[f"{prefix}_liability"] / asset, np.nan)
        out[f"ROA_{prefix}"] = np.where(asset.gt(0), out[f"{prefix}_net_profit"] / asset, np.nan)
        out[f"RD_Asset_{prefix}"] = np.where(asset.gt(0), out[f"{prefix}_dev_expenditure"] / asset, np.nan)
        return out

    latest_out = attach("ipo_pre", latest)
    strict_out = attach("ipo_lag1", strict)
    out = latest_out.merge(strict_out, on="code", how="left", validate="one_to_one")
    out = out.merge(keys[["code", "revenue_target_year"]], on="code", how="left", validate="one_to_one")
    for prefix in ["ipo_pre", "ipo_lag1"]:
        raw_name = f"FSales_Growth_{prefix}_to_Lp1_raw"
        win_name = f"FSales_Growth_{prefix}_to_Lp1_w1p"
        sales = pd.to_numeric(out[f"{prefix}_sales"], errors="coerce")
        target = pd.to_numeric(out["revenue_target_year"], errors="coerce")
        out[raw_name] = np.where(sales.gt(0) & target.notna(), (target - sales) / sales, np.nan)
        out[win_name] = winsorize(out[raw_name])

    audit_rows = []
    original_map = {
        "Size_ipo_pre": "Size",
        "Lev_ipo_pre": "Lev",
        "ROA_ipo_pre": "ROA",
        "RD_Asset_ipo_pre": "RD_Asset",
        "FSales_Growth_ipo_pre_to_Lp1_w1p": "FSales_Growth",
        "Size_ipo_lag1": "Size",
        "Lev_ipo_lag1": "Lev",
        "ROA_ipo_lag1": "ROA",
        "RD_Asset_ipo_lag1": "RD_Asset",
        "FSales_Growth_ipo_lag1_to_Lp1_w1p": "FSales_Growth",
    }
    for var, orig in original_map.items():
        audit_rows.append(
            {
                "variable": var,
                "source": "IPO pre-listing annual StateTypeCode=A; latest <= listing_year-1 or strict lag1",
                **stats(out[var]),
                "original_mean": ORIGINAL_PANEL_A[orig]["mean"],
                "original_median": ORIGINAL_PANEL_A[orig]["median"],
            }
        )
    audit_rows.extend(
        [
            {
                "variable": "ipo_pre_fin_year_available",
                "source": "latest common balance/income annual row <= listing_year-1",
                "N": int(out["ipo_pre_fin_year"].notna().sum()),
                "mean": np.nan,
                "std": np.nan,
                "p25": np.nan,
                "median": np.nan,
                "p75": np.nan,
                "original_mean": np.nan,
                "original_median": np.nan,
            },
            {
                "variable": "ipo_lag1_fin_year_available",
                "source": "strict common balance/income annual row = listing_year-1",
                "N": int(out["ipo_lag1_fin_year"].notna().sum()),
                "mean": np.nan,
                "std": np.nan,
                "p25": np.nan,
                "median": np.nan,
                "p75": np.nan,
                "original_mean": np.nan,
                "original_median": np.nan,
            },
        ]
    )
    return out, pd.DataFrame(audit_rows), cand


def descriptives_key(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    mapping = {
        "lnN_tech": "lnN_tech",
        "Redundancy": "Redundancy",
        "FInvention": "FInvention",
        "BHAR": "BHAR",
        "FSales_Growth": "FSales_Growth",
        "FSales_Growth_ipo_pre_to_Lp1_w1p": "FSales_Growth",
        "FSales_Growth_ipo_lag1_to_Lp1_w1p": "FSales_Growth",
        "Size": "Size",
        "Size_ipo_pre": "Size",
        "Size_ipo_lag1": "Size",
        "Lev": "Lev",
        "Lev_ipo_pre": "Lev",
        "Lev_ipo_lag1": "Lev",
        "ROA": "ROA",
        "ROA_ipo_pre": "ROA",
        "ROA_ipo_lag1": "ROA",
        "RD_Asset": "RD_Asset",
        "RD_Asset_ipo_pre": "RD_Asset",
        "RD_Asset_ipo_lag1": "RD_Asset",
        "Offerfee": "Offerfee",
        "Underwriter": "Underwriter",
        "Underwriter_ipo": "Underwriter",
        "Age": "Age",
        "NumIndSeg": "NumIndSeg",
        "NumProdSeg": "NumProdSeg",
        "ScopeLen": "ScopeLen",
        "RD_Staff": "RD_Staff",
        "RD_Staff_ipo": "RD_Staff",
    }
    for var, orig_var in mapping.items():
        if var not in df.columns:
            continue
        cur = stats(df[var])
        orig = ORIGINAL_PANEL_A[orig_var]
        rows.append(
            {
                "variable": var,
                **{f"current_{k}": v for k, v in cur.items()},
                "original_variable": orig_var,
                "original_N": orig["N"],
                "original_mean": orig["mean"],
                "original_median": orig["median"],
                "mean_diff_current_minus_original": cur["mean"] - orig["mean"],
            }
        )
    return pd.DataFrame(rows)


def regression_grid(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    fe = " + C(listing_year_fe) + C(industry_fe)"
    models = {
        "segment_controls_existing": [
            "lnN_tech",
            "Size",
            "Lev",
            "ROA",
            "Offerfee",
            "Underwriter",
            "Age",
            "ScopeLen",
            "NumIndSeg",
            "NumProdSeg",
        ],
        "segment_ipocsne_underwriter": [
            "lnN_tech",
            "Size",
            "Lev",
            "ROA",
            "Offerfee",
            "Underwriter_ipo",
            "Age",
            "ScopeLen",
            "NumIndSeg",
            "NumProdSeg",
        ],
        "segment_ipocsne_underwriter_rd_staff": [
            "lnN_tech",
            "Size",
            "Lev",
            "ROA",
            "Offerfee",
            "Underwriter_ipo",
            "Age",
            "ScopeLen",
            "NumIndSeg",
            "NumProdSeg",
            "RD_Staff_ipo",
        ],
        "ipo_pre_fin_controls": [
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
        ],
        "ipo_pre_fin_controls_rd_staff": [
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
        ],
        "ipo_lag1_fin_controls": [
            "lnN_tech",
            "Size_ipo_lag1",
            "Lev_ipo_lag1",
            "ROA_ipo_lag1",
            "Offerfee",
            "Underwriter_ipo",
            "Age",
            "ScopeLen",
            "NumIndSeg",
            "NumProdSeg",
        ],
    }
    dep_vars = [*OUTCOMES, "FSales_Growth_ipo_pre_to_Lp1_w1p", "FSales_Growth_ipo_lag1_to_Lp1_w1p"]
    samples = [
        ("full_by_y_available", df),
        ("w2_2019_2022", df[pd.to_numeric(df["listing_year"], errors="coerce").between(2019, 2022)].copy()),
    ]
    for sample, sub in samples:
        for model_name, controls in models.items():
            for dep in dep_vars:
                if dep not in sub.columns:
                    continue
                formula = f"{dep} ~ Redundancy + {' + '.join(controls)}{fe}"
                rows.append(base.regression_result(sample, model_name, dep, formula, sub, "Redundancy"))
    return pd.DataFrame(rows)


def build_doc(
    desc: pd.DataFrame,
    regs: pd.DataFrame,
    source_audit: pd.DataFrame,
    table_coverage: pd.DataFrame,
) -> None:
    desc_view = desc[
        desc["variable"].isin(
            [
                "lnN_tech",
                "Redundancy",
                "FInvention",
                "BHAR",
                "FSales_Growth",
                "FSales_Growth_ipo_pre_to_Lp1_w1p",
                "Size",
                "Size_ipo_pre",
                "Lev",
                "Lev_ipo_pre",
                "ROA",
                "ROA_ipo_pre",
                "Underwriter",
                "Underwriter_ipo",
                "RD_Staff",
                "RD_Staff_ipo",
                "NumIndSeg",
                "NumProdSeg",
                "ScopeLen",
            ]
        )
    ].copy()
    desc_cols = [
        "variable",
        "current_N",
        "current_mean",
        "current_median",
        "original_variable",
        "original_N",
        "original_mean",
        "original_median",
        "mean_diff_current_minus_original",
    ]

    audit_vars = [
        "Underwriter_ipo",
        "Underwriter_ipocsne_annual_grsprc_full",
        "Underwriter_ipocsne_annual_grsprc_weighted",
        "RD_Staff_ipo",
        "RD_Staff_ipo_exact_core",
        "ipo_pre_fin_year_available",
        "ipo_lag1_fin_year_available",
        "Size_ipo_pre",
        "Lev_ipo_pre",
        "ROA_ipo_pre",
        "FSales_Growth_ipo_pre_to_Lp1_w1p",
    ]
    audit_view = source_audit[source_audit["variable"].isin(audit_vars)].copy()
    audit_cols = ["variable", "source", "N", "mean", "median", "p25", "p75", "original_mean", "original_median"]

    main_models = [
        "segment_controls_existing",
        "segment_ipocsne_underwriter",
        "segment_ipocsne_underwriter_rd_staff",
        "ipo_pre_fin_controls",
        "ipo_pre_fin_controls_rd_staff",
    ]
    main = regs[
        regs["sample"].eq("full_by_y_available")
        & regs["model"].isin(main_models)
        & regs["dep_var"].isin(["FInvention", "BHAR", "FSales_Growth"])
    ].copy()
    main_cols = ["model", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"]

    fsales_alt = regs[
        regs["sample"].eq("full_by_y_available")
        & regs["model"].isin(["segment_ipocsne_underwriter", "ipo_pre_fin_controls", "ipo_pre_fin_controls_rd_staff"])
        & regs["dep_var"].isin(["FSales_Growth", "FSales_Growth_ipo_pre_to_Lp1_w1p", "FSales_Growth_ipo_lag1_to_Lp1_w1p"])
    ].copy()
    fsales_cols = ["model", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"]

    w2 = regs[
        regs["sample"].eq("w2_2019_2022")
        & regs["model"].isin(["segment_ipocsne_underwriter", "ipo_pre_fin_controls", "ipo_pre_fin_controls_rd_staff"])
        & regs["dep_var"].isin(["FInvention", "BHAR", "FSales_Growth", "FSales_Growth_ipo_pre_to_Lp1_w1p"])
    ].copy()
    w2_cols = ["model", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"]

    def result_line(model: str, dep: str) -> str:
        row = main[(main["model"].eq(model)) & (main["dep_var"].eq(dep))]
        if row.empty:
            return f"`{dep}` no result"
        r = row.iloc[0]
        return f"`{dep}` coef={r['coef']:.4f}, t={r['t_HC1']:.2f}, p={r['p_HC1']:.3f}, N={int(r['N'])}"

    lines = [
        "# Table 2 新下载 IPO 数据 controls 重跑",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 这次更新了什么",
        "",
        "- 用新下载 `IPO_Ipocsne` 的主承销商表重构 `Underwriter_ipo`：年度主承销商 IPO 募资额 Top10，co-main underwriters 采用 full-deal credit；weighted credit 只保留为敏感性。",
        "- 用新下载 `IPO_Iponoem` 的招股时员工人数表重构 `RD_Staff_ipo`：专业结构中含“研发”的人数 / 总人数。",
        "- 用新下载招股前资产负债表和利润表构造 pre-IPO 财务口径：`Size_ipo_pre`、`Lev_ipo_pre`、`ROA_ipo_pre`、`RD_Asset_ipo_pre`，主口径为 `latest annual <= listing_year - 1`。",
        "- `NumIndSeg / NumProdSeg / ScopeLen` 仍沿用上一轮已补齐的上市当年分部附注和经营范围长度口径。",
        "",
        "## 新下载表覆盖率",
        "",
        *md_table(table_coverage, ["table", "label", "rows", "sample_firm_coverage", "sample_firm_total", "zip_file"], digits=0),
        "",
        "## 关键变量描述性对比",
        "",
        *md_table(desc_view[desc_cols], desc_cols, digits=3),
        "",
        "## 新来源审计",
        "",
        *md_table(audit_view[audit_cols], audit_cols, digits=3),
        "",
        "## Table 2 主回归重跑",
        "",
        *md_table(main[main_cols], main_cols, digits=4),
        "",
        "## FSales_Growth 口径敏感性",
        "",
        *md_table(fsales_alt[fsales_cols], fsales_cols, digits=4),
        "",
        "## 2019-2022 子样本",
        "",
        *md_table(w2[w2_cols], w2_cols, digits=4),
        "",
        "## 直接结论",
        "",
        "- `Underwriter_ipo` 已回到原文量级附近，但仍偏高；这是因为“任一主承销商进年度 Top10 即记 1”的二元规则会天然偏宽。",
        "- `RD_Staff_ipo` 覆盖接近全样本，均值略低于原文和上市公司研发投入表口径，但相关性应比旧缺失口径强。",
        "- pre-IPO 财务 controls 里 `Size / Lev / ROA` 覆盖足够且量级贴近原文，可解释 `listing_year - 1` 在上市公司年报源中覆盖不足的问题；但 `RD_Asset_ipo_pre` 覆盖太低，不能替代机制表的研发资产变量。",
        "- 主回归读法：",
        f"  - `segment_ipocsne_underwriter`：{result_line('segment_ipocsne_underwriter', 'FInvention')}；{result_line('segment_ipocsne_underwriter', 'BHAR')}；{result_line('segment_ipocsne_underwriter', 'FSales_Growth')}",
        f"  - `ipo_pre_fin_controls`：{result_line('ipo_pre_fin_controls', 'FInvention')}；{result_line('ipo_pre_fin_controls', 'BHAR')}；{result_line('ipo_pre_fin_controls', 'FSales_Growth')}",
        "- 判定：`NO_PASS_YET`。新 IPO controls 能改善数据制度一致性，但仍不能把 `BHAR` 和 `FSales_Growth` 拉回原文显著负向；下一步应优先审计 Y 的窗口、行业基准、缩尾和原文样本剔除，而不是继续改 X。",
        "",
        "## 输出",
        "",
        f"- master：`{MASTER_OUT}`",
        f"- descriptives：`{DESC_OUT}`",
        f"- regressions：`{REG_OUT}`",
        f"- source audit：`{SOURCE_AUDIT_OUT}`",
        f"- underwriter top10：`{UNDERWRITER_TOP10_OUT}`",
        f"- employee rows：`{EMPLOYEE_ROWS_OUT}`",
        f"- pre-financial rows：`{FIN_ROWS_OUT}`",
        "",
    ]
    DOC_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    master = load_master()
    table_coverage = build_table_coverage(master)
    ipo_basic = read_ipo_basic()
    under_flags, under_audit, top10 = build_ipocsne_underwriter(master, ipo_basic)
    rd_staff, rd_audit, employee_rows = build_ipo_rd_staff(master)
    pre_fin, pre_fin_audit, fin_rows = build_ipo_pre_financials(master)

    df = master.merge(
        under_flags.drop(columns=["sec_code", "sec_name", "listing_year"], errors="ignore"),
        on="code",
        how="left",
        validate="one_to_one",
    )
    df = df.merge(
        rd_staff.drop(columns=["sec_code", "sec_name"], errors="ignore"),
        on="code",
        how="left",
        validate="one_to_one",
    )
    df = df.merge(pre_fin, on="code", how="left", validate="one_to_one")

    source_audit = pd.concat([under_audit, rd_audit, pre_fin_audit], ignore_index=True)
    desc = descriptives_key(df)
    regs = regression_grid(df)

    df.to_csv(MASTER_OUT, index=False, encoding="utf-8-sig")
    desc.to_csv(DESC_OUT, index=False, encoding="utf-8-sig")
    regs.to_csv(REG_OUT, index=False, encoding="utf-8-sig")
    source_audit.to_csv(SOURCE_AUDIT_OUT, index=False, encoding="utf-8-sig")
    top10.to_csv(UNDERWRITER_TOP10_OUT, index=False, encoding="utf-8-sig")
    employee_rows.to_csv(EMPLOYEE_ROWS_OUT, index=False, encoding="utf-8-sig")
    fin_rows.to_csv(FIN_ROWS_OUT, index=False, encoding="utf-8-sig")
    build_doc(desc, regs, source_audit, table_coverage)

    print(f"master={MASTER_OUT}")
    print(f"descriptives={DESC_OUT}")
    print(f"regressions={REG_OUT}")
    print(f"source_audit={SOURCE_AUDIT_OUT}")
    print(f"doc={DOC_OUT}")
    print(
        regs[
            regs["sample"].eq("full_by_y_available")
            & regs["model"].isin(["segment_ipocsne_underwriter", "ipo_pre_fin_controls", "ipo_pre_fin_controls_rd_staff"])
            & regs["dep_var"].isin(["FInvention", "BHAR", "FSales_Growth"])
        ][["model", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"]].to_string(index=False)
    )


if __name__ == "__main__":
    main()
