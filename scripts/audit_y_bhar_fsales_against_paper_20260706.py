#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import math
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
FSALES_DESC_IN = (
    PROJECT
    / "results/fsales_growth_window_sensitivity_20260706/"
    "fsales_growth_window_descriptives_20260706.csv"
)
FSALES_REG_IN = (
    PROJECT
    / "results/fsales_growth_window_sensitivity_20260706/"
    "fsales_growth_window_regressions_20260706.csv"
)
WEEKLY_ADJ_ZIP = Path(
    "/Users/mac/computerscience/第三方资料/01_数据资源/国泰安/第三方数据资源/"
    "上市公司财务信息/市场调整股票周收益表(年)102503558(仅供沪江大学使用).zip"
)

RUN_DIR = PROJECT / "results/y_bhar_fsales_definition_audit_20260706"
DOC_OUT = PROJECT / "docs/00_current/y_bhar_fsales_definition_audit_20260706.md"

BHAR_WEEKLY_OUT = RUN_DIR / "bhar_csmar_weekly_adjusted_variants_20260706.csv"
WEEKLY_ROWS_OUT = RUN_DIR / "bhar_csmar_weekly_adjusted_raw_rows_20260706.csv"
BHAR_DESC_OUT = RUN_DIR / "bhar_csmar_weekly_adjusted_descriptives_20260706.csv"
BHAR_REG_OUT = RUN_DIR / "bhar_csmar_weekly_adjusted_regressions_20260706.csv"
FSALES_AUDIT_OUT = RUN_DIR / "fsales_growth_key_candidates_20260706.csv"

WEEKLY_MEMBERS = [
    "BF_STOCKADJWR.xlsx",
    "BF_STOCKADJWR1.xlsx",
    "BF_STOCKADJWR2.xlsx",
    "BF_STOCKADJWR3.xlsx",
]

BHAR_COLUMNS = ["Wretwd_Mdeq", "Wretwd_Mdos", "Wretwd_Mdtl", "Wretwd_Cmdeq", "Wretwd_Cmdos", "Wretwd_Cmdtl"]


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
        "FSales_Growth",
        "FInvention",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def to_float(value: object) -> float:
    try:
        if value is None or value == "":
            return np.nan
        return float(value)
    except Exception:
        return np.nan


def load_weekly_adjusted_rows(master: pd.DataFrame) -> pd.DataFrame:
    if WEEKLY_ROWS_OUT.exists():
        cached = pd.read_csv(WEEKLY_ROWS_OUT, dtype={"code": str}, encoding="utf-8-sig")
        cached["code"] = cached["code"].map(z6)
        cached["Opndt"] = pd.to_datetime(cached["Opndt"], errors="coerce")
        cached["Clsdt"] = pd.to_datetime(cached["Clsdt"], errors="coerce")
        return cached

    sample = master[["code", "first_trade_date", "listing_year"]].dropna(subset=["code", "first_trade_date"]).copy()
    codes = set(sample["code"])
    min_date = sample["first_trade_date"].min() - pd.Timedelta(days=7)
    max_date = sample["first_trade_date"].max() + pd.Timedelta(days=390)
    rows: list[dict] = []
    needed = ["Stkcd", "Trdwnt", "Opndt", "Clsdt", "Wretwd", *BHAR_COLUMNS, "MarketType", "Status"]
    with ZipFile(WEEKLY_ADJ_ZIP) as zf:
        for member in WEEKLY_MEMBERS:
            with zf.open(member) as fh:
                raw = pd.read_excel(fh, usecols=needed, dtype=object)
            raw["code"] = raw["Stkcd"].map(z6)
            raw = raw[raw["code"].isin(codes)].copy()
            if raw.empty:
                continue
            raw["Clsdt"] = pd.to_datetime(raw["Clsdt"], errors="coerce")
            raw["Opndt"] = pd.to_datetime(raw["Opndt"], errors="coerce")
            raw = raw[raw["Clsdt"].between(min_date, max_date)].copy()
            if raw.empty:
                continue
            raw["Wretwd"] = pd.to_numeric(raw["Wretwd"], errors="coerce")
            raw["MarketType"] = pd.to_numeric(raw["MarketType"], errors="coerce")
            for col in BHAR_COLUMNS:
                raw[col] = pd.to_numeric(raw[col], errors="coerce")
            raw["source_member"] = member
            rows.extend(raw[["code", "Trdwnt", "Opndt", "Clsdt", "Wretwd", *BHAR_COLUMNS, "MarketType", "Status", "source_member"]].to_dict("records"))
    weekly = pd.DataFrame(rows)
    if weekly.empty:
        return weekly
    weekly = weekly.drop_duplicates(["code", "Trdwnt", "Clsdt"]).sort_values(["code", "Clsdt"])
    weekly.to_csv(WEEKLY_ROWS_OUT, index=False, encoding="utf-8-sig")
    return weekly


def compound_return(series: pd.Series) -> float:
    vals = pd.to_numeric(series, errors="coerce").dropna()
    if vals.empty:
        return np.nan
    vals = vals[vals.gt(-1)]
    if vals.empty:
        return np.nan
    return float(np.exp(np.log1p(vals).sum()) - 1.0)


def build_bhar_weekly_variants(master: pd.DataFrame, weekly: pd.DataFrame) -> pd.DataFrame:
    out_rows: list[dict] = []
    key = master[["code", "sec_name", "listing_year", "first_trade_date", "BHAR", "Redundancy"]].drop_duplicates("code")
    weekly_map = {code: sub.sort_values("Clsdt").copy() for code, sub in weekly.groupby("code", sort=False)}
    for row in key.itertuples(index=False):
        sub = weekly_map.get(row.code, pd.DataFrame())
        rec = {
            "code": row.code,
            "sec_name": row.sec_name,
            "listing_year": row.listing_year,
            "first_trade_date": row.first_trade_date,
            "BHAR_current": row.BHAR,
        }
        if sub.empty or pd.isna(row.first_trade_date):
            out_rows.append(rec)
            continue
        one_year_end = row.first_trade_date + pd.Timedelta(days=365)
        windows = {
            "first52": sub[sub["Clsdt"].ge(row.first_trade_date)].head(52).copy(),
            "within365": sub[sub["Clsdt"].ge(row.first_trade_date) & sub["Clsdt"].le(one_year_end)].copy(),
            "skip_first_first52": sub[sub["Clsdt"].ge(row.first_trade_date)].iloc[1:53].copy(),
        }
        for win_name, win in windows.items():
            rec[f"{win_name}_weeks"] = int(len(win))
            rec[f"{win_name}_start"] = win["Clsdt"].min() if not win.empty else pd.NaT
            rec[f"{win_name}_end"] = win["Clsdt"].max() if not win.empty else pd.NaT
            stock = compound_return(win["Wretwd"]) if len(win) >= 45 else np.nan
            rec[f"BHARwk_{win_name}_stock_bhr"] = stock
            for col in BHAR_COLUMNS:
                # CSMAR adjusted weekly return is stock return minus the corresponding market return.
                # Reconstruct market weekly returns, then compound stock and market separately.
                adjusted = pd.to_numeric(win[col], errors="coerce")
                market_weekly = pd.to_numeric(win["Wretwd"], errors="coerce") - adjusted
                market_bhr = compound_return(market_weekly) if len(win) >= 45 else np.nan
                rec[f"BHARwk_{win_name}_{col}_market_bhr"] = market_bhr
                rec[f"BHARwk_{win_name}_{col}"] = stock - market_bhr if pd.notna(stock) and pd.notna(market_bhr) else np.nan
                rec[f"BHARwk_{win_name}_{col}_sum_adj"] = adjusted.sum(min_count=45)
        out_rows.append(rec)
    return pd.DataFrame(out_rows)


def build_descriptives(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    samples = {
        "full_2019_2023": df.index == df.index,
        "w2_2019_2022": pd.to_numeric(df["listing_year"], errors="coerce").between(2019, 2022),
    }
    columns = ["BHAR_current"] + [
        col
        for col in df.columns
        if col.startswith("BHARwk_") and not col.endswith(("_market_bhr", "_stock_bhr")) and "weeks" not in col
    ]
    for sample, mask in samples.items():
        for col in columns:
            st = stats(df.loc[mask, col])
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
                    "distance_all": sum(
                        abs(st[k] - ORIGINAL_BHAR[k])
                        for k in ["mean", "std", "p25", "median", "p75"]
                        if pd.notna(st[k])
                    ),
                    "distance_q": sum(
                        abs(st[k] - ORIGINAL_BHAR[k])
                        for k in ["p25", "median", "p75"]
                        if pd.notna(st[k])
                    ),
                }
            )
    return pd.DataFrame(rows).sort_values(["sample", "distance_all", "variable"])


def run_bhar_regs(master: pd.DataFrame, bhar_variants: pd.DataFrame, desc: pd.DataFrame) -> pd.DataFrame:
    df = master.merge(bhar_variants.drop(columns=["sec_name", "listing_year", "first_trade_date"], errors="ignore"), on="code")
    controls = [
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
    ]
    fe = " + C(listing_year_fe) + C(industry_fe)"
    candidates = ["BHAR"] + desc[desc["sample"].eq("w2_2019_2022")].head(8)["variable"].tolist()
    candidates = list(dict.fromkeys([c for c in candidates if c in df.columns]))
    rows = []
    for sample_name, sub in [
        ("full_2019_2023", df.copy()),
        ("w2_2019_2022", df[pd.to_numeric(df["listing_year"], errors="coerce").between(2019, 2022)].copy()),
    ]:
        for dep in candidates:
            formula = f"{dep} ~ Redundancy + {' + '.join(controls)}{fe}"
            rows.append(base.regression_result(sample_name, "ipo_pre_controls", dep, formula, sub, "Redundancy"))
    return pd.DataFrame(rows)


def build_fsales_audit() -> pd.DataFrame:
    if not FSALES_DESC_IN.exists():
        return pd.DataFrame()
    desc = pd.read_csv(FSALES_DESC_IN)
    reg = pd.read_csv(FSALES_REG_IN) if FSALES_REG_IN.exists() else pd.DataFrame()
    key = desc[
        desc["sample"].isin(["full_2019_2023", "w2_2019_2022"])
        & desc["source"].eq("combo")
        & desc["window"].isin(["L_to_L1_total", "L1_to_L2_total", "Lm1_to_L1_total", "Lm1_to_L1_cagr"])
        & desc["treatment"].eq("winsor_1_99")
    ].copy()
    if not reg.empty:
        reg_key = reg[
            reg["sample"].isin(["full_2019_2023", "w2_2019_2022"])
            & reg["model"].eq("controls_fe_listing_year_segments")
            & reg["dep_var"].isin(key["variable"])
        ][["sample", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"]].copy()
        key = key.merge(reg_key, left_on=["sample", "variable"], right_on=["sample", "dep_var"], how="left")
    keep = [
        "sample",
        "window",
        "window_label",
        "variable",
        "N_x" if "N_x" in key.columns else "N",
        "mean",
        "std",
        "p25",
        "median",
        "p75",
        "diff_mean",
        "diff_median",
        "coef",
        "t_HC1",
        "p_HC1",
    ]
    keep = [c for c in keep if c in key.columns]
    return key[keep].copy()


def fmt(value: object, digits: int = 3) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (float, np.floating)):
        return f"{float(value):.{digits}f}"
    return str(value)


def md_table(df: pd.DataFrame, cols: list[str], digits: int = 3) -> list[str]:
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(fmt(row[col], digits) for col in cols) + " |")
    return lines


def build_doc(bhar_desc: pd.DataFrame, bhar_regs: pd.DataFrame, fsales: pd.DataFrame) -> None:
    current = bhar_desc[bhar_desc["variable"].eq("BHAR_current")].copy()
    best_w2 = bhar_desc[bhar_desc["sample"].eq("w2_2019_2022")].head(10).copy()
    best_full = bhar_desc[bhar_desc["sample"].eq("full_2019_2023")].head(8).copy()
    reg_view = bhar_regs[
        bhar_regs["sample"].isin(["w2_2019_2022", "full_2019_2023"])
        & bhar_regs["dep_var"].isin(["BHAR", *best_w2.head(5)["variable"].tolist()])
    ].copy()
    reg_cols = ["sample", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"]
    desc_cols = ["sample", "variable", "N", "mean", "std", "p25", "median", "p75", "distance_all"]
    fs_cols = [
        c
        for c in [
            "sample",
            "window",
            "window_label",
            "variable",
            "N_x",
            "N",
            "mean",
            "std",
            "p25",
            "median",
            "p75",
            "mean_gap",
            "median_gap",
            "coef",
            "t_HC1",
            "p_HC1",
        ]
        if c in fsales.columns
    ]
    fsales_lines = (
        md_table(fsales[fs_cols], fs_cols, digits=3)
        if not fsales.empty
        else ["- 未找到 FSales sensitivity 结果。"]
    )
    lines = [
        "# BHAR 与 FSales_Growth 原文口径核对",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 原文可核对定义",
        "",
        "- `BHAR`：科创板企业上市一年内买入并持有股票的超额收益；超额收益等于年度个股收益率减去分市场的综合收益率。",
        "- `FSales_Growth`：科创板企业上市一年后的营业收入增长率。",
        "- 控制变量使用上市前一年 `Size / Lev / ROA`，并控制 `Offerfee / Underwriter / Age / NumIndSeg / NumProdSeg / ScopeLen / lnN_tech`、年份固定效应和行业固定效应。",
        "",
        "## 我们当前代码的偏差",
        "",
        "- 当前 `BHAR` 来自 `scripts/construct_outcome_variables_20260629.py`：用日个股回报 `Dretwd` 复合 252 个交易日，再减去我们自己用科创板股票池算出来的 STAR value-weighted benchmark。这不是原文写的 CSMAR `分市场综合收益率` 口径。",
        "- 当前 `FSales_Growth` 来自上市公司年报利润表：`listing_year -> listing_year+1` 的营业收入增长。原文只写“上市一年后营业收入增长率”，没有说明分母是上市当年、上市前一年，还是招股前最新年度。",
        "",
        "## BHAR 描述统计核对",
        "",
        "当前变量：",
        "",
        *md_table(current[desc_cols], desc_cols, digits=3),
        "",
        "最接近原文的 w2 候选：",
        "",
        *md_table(best_w2[desc_cols], desc_cols, digits=3),
        "",
        "full 样本候选：",
        "",
        *md_table(best_full[desc_cols], desc_cols, digits=3),
        "",
        "## BHAR 回归方向核对",
        "",
        *md_table(reg_view[reg_cols], reg_cols, digits=4),
        "",
        "## FSales_Growth 窗口核对",
        "",
        *fsales_lines,
        "",
        "## 结论",
        "",
        "- `BHAR` 当前实现不是逐字原文口径：原文写的是年度个股收益率减去分市场综合收益率；我们当前用日收益自建 STAR value-weighted benchmark，并且在 market benchmark 中剔除了各股票 IPO 首日。",
        "- 但现有 CSMAR 周度市场调整表不是直接答案：它重构出的 BHAR 分布明显比当前变量更远离原文，而且 Redundancy 系数仍不恢复显著负向。因此现在只能判定为“需定位原文实际市场收益字段”，不能简单判定当前 BHAR 全错。",
        "- `FSales_Growth` 的最大疑点不是字段，而是窗口。`listing_year -> listing_year+1` 描述统计偏低；`listing_year-1 -> listing_year+1` 均值更高但回归仍正；现有证据支持继续核原文收入窗口和样本，而不是继续调 X。",
        "",
        "## 输出",
        "",
        f"- BHAR weekly variants：`{BHAR_WEEKLY_OUT}`",
        f"- BHAR descriptives：`{BHAR_DESC_OUT}`",
        f"- BHAR regressions：`{BHAR_REG_OUT}`",
        f"- FSales key candidates：`{FSALES_AUDIT_OUT}`",
        "",
    ]
    DOC_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    master = load_master()
    weekly = load_weekly_adjusted_rows(master)
    bhar_variants = build_bhar_weekly_variants(master, weekly)
    bhar_desc = build_descriptives(bhar_variants)
    bhar_regs = run_bhar_regs(master, bhar_variants, bhar_desc)
    fsales = build_fsales_audit()

    bhar_variants.to_csv(BHAR_WEEKLY_OUT, index=False, encoding="utf-8-sig")
    bhar_desc.to_csv(BHAR_DESC_OUT, index=False, encoding="utf-8-sig")
    bhar_regs.to_csv(BHAR_REG_OUT, index=False, encoding="utf-8-sig")
    fsales.to_csv(FSALES_AUDIT_OUT, index=False, encoding="utf-8-sig")
    build_doc(bhar_desc, bhar_regs, fsales)

    print(f"doc={DOC_OUT}")
    print(f"weekly_rows={len(weekly):,}")
    print(f"bhar_variants={BHAR_WEEKLY_OUT}")
    print(bhar_desc.head(12).to_string(index=False))
    print(bhar_regs[["sample", "dep_var", "N", "coef", "t_HC1", "p_HC1"]].head(20).to_string(index=False))


if __name__ == "__main__":
    main()
