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

YEAR_ZIP = Path(
    "/Users/mac/computerscience/第三方资料/90_临时下载待归档/股票市场/"
    "年个股回报率文件190542267(仅供四川大学使用).zip"
)
MARKET_ZIP = Path(
    "/Users/mac/computerscience/第三方资料/90_临时下载待归档/股票市场/"
    "综合日市场回报率文件190104355(仅供四川大学使用).zip"
)

RUN_DIR = PROJECT / "results/bhar_official_market_return_audit_20260706"
DOC_OUT = PROJECT / "docs/00_current/bhar_official_market_return_audit_20260706.md"
VARIANTS_OUT = RUN_DIR / "bhar_official_market_variants_20260706.csv"
DESC_OUT = RUN_DIR / "bhar_official_market_descriptives_20260706.csv"
REG_OUT = RUN_DIR / "bhar_official_market_regressions_20260706.csv"
COVERAGE_OUT = RUN_DIR / "bhar_official_market_source_coverage_20260706.csv"

MARKET_TYPES = [33, 37, 53, 63, 101, 117]
MARKET_FIELDS = ["Cdretwdeq", "Cdretwdos", "Cdretwdtl"]
WINDOWS = [
    ("incl_first_252", "incl_first_window_start", "incl_first_window_end", "incl_first_stock_bhr"),
    ("excl_first_252", "excl_first_window_start", "excl_first_window_end", "excl_first_stock_bhr"),
]
YEAR_OFFSETS = [0, 1, 2]


def load_base_module():
    spec = importlib.util.spec_from_file_location("table2_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_base_module()
ORIGINAL_BHAR = base.ORIGINAL_PANEL_A["BHAR"]


def z6(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text.zfill(6) if text.isdigit() else text


def read_zipped_dta(zip_path: Path, member: str, columns: list[str] | None = None) -> pd.DataFrame:
    with ZipFile(zip_path) as zf:
        with tempfile.NamedTemporaryFile(suffix=".dta") as tmp:
            tmp.write(zf.read(member))
            tmp.flush()
            return pd.read_stata(tmp.name, convert_categoricals=False, columns=columns)


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
        "lnN_tech",
        "Size",
        "Lev",
        "ROA",
        "Size_ipo_pre",
        "Lev_ipo_pre",
        "ROA_ipo_pre",
        "Offerfee",
        "Underwriter",
        "Underwriter_ipo",
        "Age",
        "ScopeLen",
        "NumIndSeg",
        "NumProdSeg",
        "RD_Staff_ipo",
        "BHAR",
        "incl_first_stock_bhr",
        "excl_first_stock_bhr",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in [
        "incl_first_window_start",
        "incl_first_window_end",
        "excl_first_window_start",
        "excl_first_window_end",
    ]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def load_market(master: pd.DataFrame) -> pd.DataFrame:
    cols = ["Markettype", "Trddt", *MARKET_FIELDS, "Cdnstkcal"]
    mkt = read_zipped_dta(MARKET_ZIP, "TRD_Cndalym.dta", columns=cols)
    mkt["Markettype"] = pd.to_numeric(mkt["Markettype"], errors="coerce").astype("Int64")
    mkt["Trddt"] = pd.to_datetime(mkt["Trddt"], errors="coerce")
    for col in MARKET_FIELDS:
        mkt[col] = pd.to_numeric(mkt[col], errors="coerce")
    min_date = master["first_trade_date"].min() - pd.Timedelta(days=10)
    max_date = master["first_trade_date"].max() + pd.Timedelta(days=820)
    mkt = mkt[mkt["Markettype"].isin(MARKET_TYPES) & mkt["Trddt"].between(min_date, max_date)].copy()
    return mkt.sort_values(["Markettype", "Trddt"])


def load_year(master: pd.DataFrame) -> pd.DataFrame:
    cols = ["Stkcd", "Trdynt", "Opndt", "Clsdt", "Ndaytrd", "Yretwd", "Yretnd", "Yarkettype"]
    yr = read_zipped_dta(YEAR_ZIP, "TRD_Year.dta", columns=cols)
    yr["code"] = yr["Stkcd"].map(z6)
    yr["year"] = pd.to_numeric(yr["Trdynt"], errors="coerce").astype("Int64")
    yr["Yretwd"] = pd.to_numeric(yr["Yretwd"], errors="coerce")
    yr["Ndaytrd"] = pd.to_numeric(yr["Ndaytrd"], errors="coerce")
    codes = set(master["code"].dropna())
    min_year = int(master["listing_year"].min())
    max_year = int(master["listing_year"].max()) + max(YEAR_OFFSETS)
    yr = yr[yr["code"].isin(codes) & yr["year"].between(min_year, max_year)].copy()

    def make_date(row: pd.Series, col: str) -> pd.Timestamp:
        value = str(row[col]).strip()
        if not value or value == "DD" or "-" not in value or pd.isna(row["year"]):
            return pd.NaT
        return pd.to_datetime(f"{int(row['year'])}-{value}", errors="coerce")

    yr["year_open_date"] = yr.apply(lambda r: make_date(r, "Opndt"), axis=1)
    yr["year_close_date"] = yr.apply(lambda r: make_date(r, "Clsdt"), axis=1)
    return yr.sort_values(["code", "year"])


def market_compound(market_by_type: dict[int, pd.DataFrame], market_type: int, field: str, start: pd.Timestamp, end: pd.Timestamp) -> tuple[float, int]:
    if pd.isna(start) or pd.isna(end):
        return np.nan, 0
    sub = market_by_type.get(market_type)
    if sub is None or sub.empty:
        return np.nan, 0
    win = sub[sub["Trddt"].between(start, end)]
    if win.empty:
        return np.nan, 0
    return compound_return(win[field]), int(win[field].notna().sum())


def build_variants(master: pd.DataFrame, market: pd.DataFrame, year_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    market_by_type = {int(k): v.copy() for k, v in market.groupby("Markettype", sort=False)}
    year_by_key = {(r.code, int(r.year)): r for r in year_df.itertuples(index=False) if pd.notna(r.year)}
    rows: list[dict] = []
    coverage_rows: list[dict] = []

    for row in master.itertuples(index=False):
        rec = {
            "code": row.code,
            "sec_name": getattr(row, "sec_name", np.nan),
            "listing_year": row.listing_year,
            "first_trade_date": row.first_trade_date,
            "BHAR_current": row.BHAR,
        }
        for win_name, start_col, end_col, stock_col in WINDOWS:
            start = getattr(row, start_col)
            end = getattr(row, end_col)
            stock_bhr = getattr(row, stock_col)
            rec[f"{win_name}_stock_bhr"] = stock_bhr
            for market_type in MARKET_TYPES:
                for field in MARKET_FIELDS:
                    mkt_bhr, n_days = market_compound(market_by_type, market_type, field, start, end)
                    suffix = f"m{market_type}_{field.replace('Cdretwd', '')}"
                    rec[f"BHAR_cnd_{win_name}_{suffix}"] = stock_bhr - mkt_bhr if pd.notna(stock_bhr) and pd.notna(mkt_bhr) else np.nan
                    rec[f"mkt_cnd_{win_name}_{suffix}_days"] = n_days

        listing_year = int(row.listing_year) if pd.notna(row.listing_year) else None
        if listing_year is not None:
            for offset in YEAR_OFFSETS:
                year = listing_year + offset
                label = "L" if offset == 0 else f"Lp{offset}"
                yr = year_by_key.get((row.code, year))
                if yr is None:
                    continue
                rec[f"Yretwd_{label}"] = yr.Yretwd
                rec[f"Ndaytrd_{label}"] = yr.Ndaytrd
                rec[f"year_open_{label}"] = yr.year_open_date
                rec[f"year_close_{label}"] = yr.year_close_date
                for market_type in MARKET_TYPES:
                    for field in MARKET_FIELDS:
                        mkt_bhr, n_days = market_compound(
                            market_by_type,
                            market_type,
                            field,
                            yr.year_open_date,
                            yr.year_close_date,
                        )
                        suffix = f"m{market_type}_{field.replace('Cdretwd', '')}"
                        rec[f"BHAR_year_{label}_{suffix}"] = yr.Yretwd - mkt_bhr if pd.notna(yr.Yretwd) and pd.notna(mkt_bhr) else np.nan
                        rec[f"mkt_year_{label}_{suffix}_days"] = n_days
        rows.append(rec)

    variants = pd.DataFrame(rows)
    coverage_rows.extend(
        [
            {
                "source": "TRD_Year",
                "rows": len(year_df),
                "sample_firm_coverage": year_df["code"].nunique(),
                "date_min": str(year_df["year"].min()),
                "date_max": str(year_df["year"].max()),
                "note": "official annual individual stock returns; IPO listing-year Yretwd is often missing",
            },
            {
                "source": "TRD_Cndalym",
                "rows": len(market),
                "sample_firm_coverage": np.nan,
                "date_min": str(market["Trddt"].min().date()) if not market.empty else "",
                "date_max": str(market["Trddt"].max().date()) if not market.empty else "",
                "note": "official comprehensive daily market returns by composite market type",
            },
        ]
    )
    return variants, pd.DataFrame(coverage_rows)


def build_descriptives(variants: pd.DataFrame) -> pd.DataFrame:
    cols = ["BHAR_current"] + [
        c
        for c in variants.columns
        if c.startswith("BHAR_") and not c.endswith("_stock_bhr") and c != "BHAR_current"
    ]
    rows: list[dict] = []
    samples = {
        "full_2019_2023": variants.index == variants.index,
        "w2_2019_2022": pd.to_numeric(variants["listing_year"], errors="coerce").between(2019, 2022),
    }
    for sample, mask in samples.items():
        for col in cols:
            st = stats(variants.loc[mask, col])
            distance_all = (
                np.inf
                if st["N"] == 0
                else sum(
                    abs(st[k] - ORIGINAL_BHAR[k])
                    for k in ["mean", "std", "p25", "median", "p75"]
                    if pd.notna(st[k])
                )
            )
            distance_q = (
                np.inf
                if st["N"] == 0
                else sum(
                    abs(st[k] - ORIGINAL_BHAR[k])
                    for k in ["p25", "median", "p75"]
                    if pd.notna(st[k])
                )
            )
            rows.append(
                {
                    "sample": sample,
                    "variable": col,
                    **st,
                    "original_N": ORIGINAL_BHAR["N"],
                    "original_mean": ORIGINAL_BHAR["mean"],
                    "original_std": ORIGINAL_BHAR["std"],
                    "original_p25": ORIGINAL_BHAR["p25"],
                    "original_median": ORIGINAL_BHAR["median"],
                    "original_p75": ORIGINAL_BHAR["p75"],
                    "distance_all": distance_all,
                    "distance_q": distance_q,
                }
            )
    return pd.DataFrame(rows).sort_values(["sample", "distance_all", "variable"])


def run_regressions(master: pd.DataFrame, variants: pd.DataFrame) -> pd.DataFrame:
    df = master.merge(
        variants.drop(columns=["sec_name", "listing_year", "first_trade_date"], errors="ignore"),
        on="code",
        how="left",
    )
    controls_by_model = {
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
    }
    candidates = ["BHAR"] + [
        c
        for c in variants.columns
        if c.startswith("BHAR_") and c != "BHAR_current"
    ]
    rows: list[dict] = []
    fe = " + C(listing_year_fe) + C(industry_fe)"
    samples = [
        ("full_2019_2023", df.copy()),
        ("w2_2019_2022", df[pd.to_numeric(df["listing_year"], errors="coerce").between(2019, 2022)].copy()),
    ]
    for sample, sub in samples:
        for model, controls in controls_by_model.items():
            rhs = " + ".join(controls)
            for dep in candidates:
                if dep not in sub.columns:
                    continue
                formula = f"{dep} ~ Redundancy + {rhs}{fe}"
                rows.append(base.regression_result(sample, model, dep, formula, sub, "Redundancy"))
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


def build_doc(coverage: pd.DataFrame, desc: pd.DataFrame, regs: pd.DataFrame) -> None:
    desc_cols = ["sample", "variable", "N", "mean", "std", "p25", "median", "p75", "distance_all"]
    reg_cols = ["sample", "model", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"]
    best_w2 = desc[desc["sample"].eq("w2_2019_2022")].copy()
    best_full = desc[desc["sample"].eq("full_2019_2023")].copy()
    current = desc[desc["variable"].eq("BHAR_current")].copy()
    key_desc_vars = list(dict.fromkeys(["BHAR_current", *best_w2.head(8)["variable"].tolist()]))
    key_regs = regs[
        regs["sample"].eq("w2_2019_2022")
        & regs["model"].eq("ipo_pre_fin_controls_rd_staff")
        & regs["dep_var"].isin(["BHAR", *key_desc_vars])
    ].copy()
    strongest_negative = regs[
        regs["sample"].eq("w2_2019_2022")
        & regs["model"].eq("ipo_pre_fin_controls_rd_staff")
        & regs["coef"].notna()
    ].sort_values(["coef", "p_HC1"]).head(12)
    significant_negative = regs[
        regs["sample"].eq("w2_2019_2022")
        & regs["model"].eq("ipo_pre_fin_controls_rd_staff")
        & regs["coef"].lt(0)
        & regs["p_HC1"].lt(0.1)
    ].sort_values(["p_HC1", "coef"])

    lines = [
        "# BHAR 官方市场收益率口径审计",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 这次核对的数据",
        "",
        "- 新下载 `TRD_Year.dta`：官方年个股回报率文件，核心字段 `Yretwd`。",
        "- 新下载 `TRD_Cndalym.dta`：官方综合日市场回报率文件，核心字段 `Cdretwdeq / Cdretwdos / Cdretwdtl`。",
        "- 目的：检验原文“年度个股收益率减去分市场综合收益率”是否能解释我们 `BHAR` 不显著的问题。",
        "",
        *md_table(coverage, ["source", "rows", "sample_firm_coverage", "date_min", "date_max", "note"], digits=0),
        "",
        "## 构造的 BHAR 候选",
        "",
        "- `BHAR_cnd_*`：保留我们当前的一年个股买入持有收益窗口，只把市场基准替换成 CSMAR 官方综合日市场收益率。",
        "- `BHAR_year_L/Lp1/Lp2_*`：使用 `TRD_Year` 官方年个股收益率 `Yretwd`，再减去同日历年窗口内 CSMAR 官方综合日市场收益率。",
        "- 综合市场类型重点测 `33/37/53/63/101/117`；收益字段测等权、流通市值加权、总市值加权。",
        "",
        "## 与原文描述统计的距离",
        "",
        "原文 `BHAR`：N=471, mean=-0.036, std=0.514, p25=-0.385, median=-0.170, p75=0.162。",
        "",
        "当前变量：",
        "",
        *md_table(current[desc_cols], desc_cols, digits=3),
        "",
        "2019-2022 子样本最接近原文的候选：",
        "",
        *md_table(best_w2[desc_cols], desc_cols, digits=3, max_rows=12),
        "",
        "full 2019-2023 最接近原文的候选：",
        "",
        *md_table(best_full[desc_cols], desc_cols, digits=3, max_rows=8),
        "",
        "## 回归方向核对",
        "",
        "最接近原文描述统计候选的 w2 主规格：",
        "",
        *md_table(key_regs[reg_cols], reg_cols, digits=4),
        "",
        "w2 主规格中系数最负的候选：",
        "",
        *md_table(strongest_negative[reg_cols], reg_cols, digits=4),
        "",
        "w2 主规格中 10% 水平负向显著候选：",
        "",
        *(
            md_table(significant_negative[reg_cols], reg_cols, digits=4, max_rows=20)
            if not significant_negative.empty
            else ["- 无。"]
        ),
        "",
        "## 判断",
        "",
        "- 这两个新包确实是我们缺的官方市场收益率数据，应该保留进复现证据链。",
        "- 但不能简单用 `TRD_Year` 替换当前 BHAR：科创板上市首年 `Yretwd` 经常缺失，`listing_year+1` 又变成日历年收益，不等同于“上市一年内买入并持有”。",
        "- 近似原文 N 的 2019-2022 子样本里，当前 `BHAR` 仍是描述统计最贴近原文的变量；full 样本里 `listing_year+1` 年收益更贴近，但它是日历年收益，制度含义不如当前一年买入持有窗口。",
        "- 把当前一年买入持有窗口的 market benchmark 替换成 CSMAR 官方综合日市场收益率，不能恢复负向显著；`TRD_Year` 的 `listing_year+1` 候选虽然转为负向，t 约 -1.19，仍不显著。",
        "- 所以 `BHAR` 的未复刻不能只归因于缺官方市场收益率；更可能还涉及原文样本剔除、上市后一年窗口、年度/日度收益口径或 winsor 口径。",
        "",
        "## 输出",
        "",
        f"- variants：`{VARIANTS_OUT}`",
        f"- descriptives：`{DESC_OUT}`",
        f"- regressions：`{REG_OUT}`",
        f"- coverage：`{COVERAGE_OUT}`",
        "",
    ]
    DOC_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    master = load_master()
    market = load_market(master)
    year_df = load_year(master)
    variants, coverage = build_variants(master, market, year_df)
    desc = build_descriptives(variants)
    regs = run_regressions(master, variants)

    variants.to_csv(VARIANTS_OUT, index=False, encoding="utf-8-sig")
    desc.to_csv(DESC_OUT, index=False, encoding="utf-8-sig")
    regs.to_csv(REG_OUT, index=False, encoding="utf-8-sig")
    coverage.to_csv(COVERAGE_OUT, index=False, encoding="utf-8-sig")
    build_doc(coverage, desc, regs)

    print(f"doc={DOC_OUT}")
    print(f"variants={VARIANTS_OUT}")
    print(desc[desc['sample'].eq('w2_2019_2022')].head(12).to_string(index=False))
    print(
        regs[
            regs["sample"].eq("w2_2019_2022")
            & regs["model"].eq("ipo_pre_fin_controls_rd_staff")
        ][["dep_var", "N", "coef", "t_HC1", "p_HC1"]]
        .sort_values(["coef", "p_HC1"])
        .head(20)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
