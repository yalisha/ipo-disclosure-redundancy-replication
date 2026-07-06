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
    / "results/table2_glm4_dewrap_full543_audit_20260706/"
    "table2_glm4_dewrap_full543_master_20260706.csv"
)
IPO_BASIC_ZIP = Path(
    "/Users/mac/computerscience/第三方资料/90_临时下载待归档/"
    "招股及上市基本情况表093114533(仅供四川大学使用).zip"
)
FIRM_INFO_XLSX = Path(
    "/Users/mac/computerscience/第三方资料/01_数据资源/国泰安/第三方数据资源/"
    "上市公司财务信息/上市公司基本信息年度表181707814(仅供四川大学使用)/"
    "STK_LISTEDCOINFOANL.xlsx"
)

RUN_DIR = PROJECT / "results/table2_existing_controls_patch_20260706"
DOC_OUT = PROJECT / "docs/00_current/table2_existing_controls_patch_20260706.md"

MASTER_OUT = RUN_DIR / "table2_existing_controls_patch_master_20260706.csv"
DESC_OUT = RUN_DIR / "table2_existing_controls_patch_descriptives_20260706.csv"
REG_OUT = RUN_DIR / "table2_existing_controls_patch_regressions_20260706.csv"
SOURCE_AUDIT_OUT = RUN_DIR / "table2_existing_controls_patch_source_audit_20260706.csv"


def load_base_module():
    spec = importlib.util.spec_from_file_location("table2_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_base_module()

OUTCOMES = base.OUTCOMES
FE_VARS = base.FE_VARS
CURRENT_CONTROL_VARS = base.CURRENT_CONTROL_VARS
ORIGINAL_PANEL_A = base.ORIGINAL_PANEL_A
ORIGINAL_PANEL_B = base.ORIGINAL_PANEL_B


def z6(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)


def normalize_name(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not text or text.lower() == "none":
        return None
    text = re.sub(r"\s+", "", text)
    return text


def clean_scope_text(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value)
    text = re.sub(r"\s+", "", text)
    text = text.replace("经营范围", "")
    return text or None


def read_ipo_basic() -> pd.DataFrame:
    cols = ["Stkcd", "Listdt", "Sponsfm", "Grsprc", "Fltcst", "Tludwfe"]
    with ZipFile(IPO_BASIC_ZIP) as zf:
        raw = zf.read("IPO_Ipobasic.dta")
    df = pd.read_stata(BytesIO(raw), columns=cols, convert_categoricals=False)
    df["code"] = z6(df["Stkcd"])
    df["Listdt"] = pd.to_datetime(df["Listdt"], errors="coerce")
    df["list_year"] = df["Listdt"].dt.year
    df["Sponsfm_clean"] = df["Sponsfm"].map(normalize_name)
    for col in ["Grsprc", "Fltcst", "Tludwfe"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def add_underwriter_variants(master: pd.DataFrame, ipo: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    pool = ipo[ipo["list_year"].between(2019, 2023, inclusive="both") & ipo["Sponsfm_clean"].notna()].copy()
    variant_specs = {
        "Underwriter_sponsfm_pool_count": ("pool", "count", None),
        "Underwriter_sponsfm_pool_grsprc": ("pool", "sum", "Grsprc"),
        "Underwriter_sponsfm_pool_fltcst": ("pool", "sum", "Fltcst"),
        "Underwriter_sponsfm_annual_count": ("annual", "count", None),
        "Underwriter_sponsfm_annual_grsprc": ("annual", "sum", "Grsprc"),
        "Underwriter_sponsfm_annual_fltcst": ("annual", "sum", "Fltcst"),
    }

    top_sets: dict[str, set[str] | dict[int, set[str]]] = {}
    top_rows: list[dict] = []
    for name, (scope, method, amount_col) in variant_specs.items():
        if scope == "pool":
            if method == "count":
                rank = pool.groupby("Sponsfm_clean").size().sort_values(ascending=False)
            else:
                rank = pool.groupby("Sponsfm_clean")[amount_col].sum(min_count=1).sort_values(ascending=False)
            top10 = set(rank.dropna().head(10).index)
            top_sets[name] = top10
            for idx, firm in enumerate(rank.dropna().head(10).index, 1):
                top_rows.append({"variant": name, "year": "2019-2023", "rank": idx, "firm": firm})
        else:
            by_year: dict[int, set[str]] = {}
            for year, sub in pool.groupby("list_year"):
                if method == "count":
                    rank = sub.groupby("Sponsfm_clean").size().sort_values(ascending=False)
                else:
                    rank = sub.groupby("Sponsfm_clean")[amount_col].sum(min_count=1).sort_values(ascending=False)
                top10 = set(rank.dropna().head(10).index)
                by_year[int(year)] = top10
                for idx, firm in enumerate(rank.dropna().head(10).index, 1):
                    top_rows.append({"variant": name, "year": int(year), "rank": idx, "firm": firm})
            top_sets[name] = by_year

    join_cols = ["code", "Listdt", "list_year", "Sponsfm", "Sponsfm_clean"]
    ipo_one = ipo.sort_values(["code", "Listdt"]).drop_duplicates("code", keep="last")[join_cols]
    out = master.merge(ipo_one, on="code", how="left", validate="one_to_one")
    out = out.rename(columns={"Underwriter": "Underwriter_old"})

    for name, top in top_sets.items():
        if isinstance(top, dict):
            out[name] = out.apply(
                lambda row: int(row["Sponsfm_clean"] in top.get(int(row["list_year"]), set()))
                if pd.notna(row["Sponsfm_clean"]) and pd.notna(row["list_year"])
                else np.nan,
                axis=1,
            )
        else:
            out[name] = out["Sponsfm_clean"].map(lambda x: int(x in top) if pd.notna(x) else np.nan)

    # Main repaired definition: top 10 IPO business by same-year IPO gross proceeds.
    out["Underwriter"] = out["Underwriter_sponsfm_annual_grsprc"]

    audit_rows = []
    if "Underwriter_old" in out.columns:
        audit_rows.append(
            {
                "variable": "Underwriter_old",
                "N": int(pd.to_numeric(out["Underwriter_old"], errors="coerce").notna().sum()),
                "mean": pd.to_numeric(out["Underwriter_old"], errors="coerce").mean(),
                "original_mean": ORIGINAL_PANEL_A["Underwriter"]["mean"],
                "source": "previous master field",
            }
        )
    for name in variant_specs:
        s = pd.to_numeric(out[name], errors="coerce")
        audit_rows.append(
            {
                "variable": name,
                "N": int(s.notna().sum()),
                "mean": s.mean(),
                "original_mean": ORIGINAL_PANEL_A["Underwriter"]["mean"],
                "source": "IPO_Ipobasic.Sponsfm",
            }
        )
    top_df = pd.DataFrame(top_rows)
    source_audit = pd.DataFrame(audit_rows)
    source_audit = pd.concat(
        [source_audit, top_df.assign(N=np.nan, mean=np.nan, original_mean=np.nan, source="top10 list")],
        ignore_index=True,
    )
    return out, source_audit


def add_scope_len(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    cols = ["Symbol", "ShortName", "EndDate", "BusinessScope", "MAINBUSSINESS"]
    firm = pd.read_excel(FIRM_INFO_XLSX, usecols=cols, dtype={"Symbol": str})
    firm = firm[firm["Symbol"].astype(str).str.fullmatch(r"\d{6}", na=False)].copy()
    firm["code"] = z6(firm["Symbol"])
    firm["scope_year"] = pd.to_datetime(firm["EndDate"], errors="coerce").dt.year
    firm["BusinessScope_clean"] = firm["BusinessScope"].map(clean_scope_text)
    firm = firm[firm["BusinessScope_clean"].notna()].copy()
    firm["BusinessScope_char_len"] = firm["BusinessScope_clean"].str.len().astype(float)
    firm["BusinessScope_utf8_bytes"] = firm["BusinessScope_clean"].map(lambda x: float(len(x.encode("utf-8"))))
    firm["BusinessScope_gb18030_bytes"] = firm["BusinessScope_clean"].map(
        lambda x: float(len(x.encode("gb18030", errors="ignore")))
    )

    keys = master[["code", "listing_year"]].copy()
    keys["listing_year_num"] = pd.to_numeric(keys["listing_year"], errors="coerce")
    cand = firm.merge(keys, on="code", how="inner")
    cand["distance"] = cand["scope_year"] - cand["listing_year_num"]
    cand["after_listing_penalty"] = (cand["distance"] > 0).astype(int)
    cand["abs_distance"] = cand["distance"].abs()
    chosen = (
        cand.sort_values(["code", "after_listing_penalty", "abs_distance", "scope_year"])
        .drop_duplicates("code", keep="first")
        .copy()
    )
    chosen["ScopeLen_char"] = np.log(chosen["BusinessScope_char_len"])
    chosen["ScopeLen_utf8"] = np.log(chosen["BusinessScope_utf8_bytes"])
    chosen["ScopeLen_gb18030"] = np.log(chosen["BusinessScope_gb18030_bytes"])
    chosen["ScopeLen_log1p_char"] = np.log1p(chosen["BusinessScope_char_len"])
    # Main definition: byte length is closer to how Chinese string length is often
    # recorded in database/Stata-style workflows and matches the paper scale better.
    chosen["ScopeLen"] = chosen["ScopeLen_utf8"]

    out = master.merge(
        chosen[
            [
                "code",
                "scope_year",
                "BusinessScope",
                "MAINBUSSINESS",
                "BusinessScope_char_len",
                "BusinessScope_utf8_bytes",
                "BusinessScope_gb18030_bytes",
                "ScopeLen",
                "ScopeLen_char",
                "ScopeLen_utf8",
                "ScopeLen_gb18030",
                "ScopeLen_log1p_char",
            ]
        ],
        on="code",
        how="left",
        validate="one_to_one",
    )
    audit = pd.DataFrame(
        [
            {
                "variable": "ScopeLen",
                "N": int(out["ScopeLen"].notna().sum()),
                "mean": out["ScopeLen"].mean(),
                "original_mean": ORIGINAL_PANEL_A["ScopeLen"]["mean"],
                "source": "STK_LISTEDCOINFOANL.BusinessScope log(clean UTF-8 bytes)",
            },
            {
                "variable": "ScopeLen_char",
                "N": int(out["ScopeLen_char"].notna().sum()),
                "mean": out["ScopeLen_char"].mean(),
                "original_mean": ORIGINAL_PANEL_A["ScopeLen"]["mean"],
                "source": "STK_LISTEDCOINFOANL.BusinessScope log(clean characters)",
            },
            {
                "variable": "ScopeLen_gb18030",
                "N": int(out["ScopeLen_gb18030"].notna().sum()),
                "mean": out["ScopeLen_gb18030"].mean(),
                "original_mean": ORIGINAL_PANEL_A["ScopeLen"]["mean"],
                "source": "STK_LISTEDCOINFOANL.BusinessScope log(clean GB18030 bytes)",
            },
            {
                "variable": "ScopeLen_log1p_char",
                "N": int(out["ScopeLen_log1p_char"].notna().sum()),
                "mean": out["ScopeLen_log1p_char"].mean(),
                "original_mean": ORIGINAL_PANEL_A["ScopeLen"]["mean"],
                "source": "STK_LISTEDCOINFOANL.BusinessScope log1p(clean characters)",
            },
        ]
    )
    return out, audit


def load_master() -> pd.DataFrame:
    df = pd.read_csv(MASTER_IN, dtype={"sec_code": str, "code": str}, encoding="utf-8-sig")
    if "code" not in df.columns:
        df["code"] = df["sec_code"]
    df["code"] = z6(df["code"])
    df["sec_code"] = z6(df["sec_code"])
    for col in ["Redundancy", *OUTCOMES, *CURRENT_CONTROL_VARS, "RD_Asset", *FE_VARS]:
        if col in df.columns and col not in FE_VARS:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["listing_year"] = pd.to_numeric(df["listing_year"], errors="coerce")
    df["listing_year_fe"] = pd.to_numeric(df["listing_year_fe"], errors="coerce").astype("Int64").astype(str)
    df["listing_year_fe"] = df["listing_year_fe"].replace({"<NA>": np.nan, "nan": np.nan})
    df["industry_fe"] = df["industry_fe"].astype(str).replace({"nan": np.nan, "<NA>": np.nan})
    return df


def regression_grid(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    samples = [
        ("full_by_y_available", df.copy()),
        (
            "common_3y_controls_repaired",
            df.dropna(subset=[*OUTCOMES, "Redundancy", *CURRENT_CONTROL_VARS, *FE_VARS]).copy(),
        ),
        (
            "common_3y_controls_repaired_scope",
            df.dropna(subset=[*OUTCOMES, "Redundancy", *CURRENT_CONTROL_VARS, "ScopeLen", *FE_VARS]).copy(),
        ),
        ("w2_2019_2022_by_y_available", df[pd.to_numeric(df["listing_year"], errors="coerce").between(2019, 2022)].copy()),
    ]
    controls = " + ".join(CURRENT_CONTROL_VARS)
    fe = " + C(listing_year_fe) + C(industry_fe)"
    for sample_name, sub in samples:
        for dep in OUTCOMES:
            rows.append(
                base.regression_result(
                    sample_name,
                    "controls_fe_repaired_underwriter",
                    dep,
                    f"{dep} ~ Redundancy + {controls}{fe}",
                    sub,
                    "Redundancy",
                )
            )
            rows.append(
                base.regression_result(
                    sample_name,
                    "controls_fe_repaired_underwriter_scope",
                    dep,
                    f"{dep} ~ Redundancy + {controls} + ScopeLen{fe}",
                    sub,
                    "Redundancy",
                )
            )

    # Underwriter construction sensitivity on the full sample.
    for uw in [
        "Underwriter_old",
        "Underwriter_sponsfm_pool_count",
        "Underwriter_sponsfm_pool_grsprc",
        "Underwriter_sponsfm_annual_count",
        "Underwriter_sponsfm_annual_grsprc",
    ]:
        if uw not in df.columns:
            continue
        for dep in OUTCOMES:
            variant_controls = ["lnN_tech", "Size", "Lev", "ROA", "Offerfee", uw, "Age"]
            formula = f"{dep} ~ Redundancy + {' + '.join(variant_controls)} + ScopeLen{fe}"
            rows.append(
                base.regression_result(
                    "full_by_y_available",
                    f"underwriter_variant_with_scope::{uw}",
                    dep,
                    formula,
                    df,
                    "Redundancy",
                )
            )
    return pd.DataFrame(rows)


def build_doc(df: pd.DataFrame, desc: pd.DataFrame, regs: pd.DataFrame, source_audit: pd.DataFrame) -> None:
    panel = desc[
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
                "ScopeLen",
                "RD_Staff",
                "NumIndSeg",
                "NumProdSeg",
            ]
        )
    ].copy()
    panel = panel[
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
    main = regs[
        regs["model"].isin(
            ["controls_fe_repaired_underwriter", "controls_fe_repaired_underwriter_scope"]
        )
        & regs["sample"].isin(["full_by_y_available", "common_3y_controls_repaired_scope"])
    ].copy()
    main = main[["sample", "model", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"]]
    sens = regs[regs["model"].str.startswith("underwriter_variant_with_scope::", na=False)].copy()
    sens = sens[["model", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"]]

    uw_summary = source_audit[source_audit["variable"].astype(str).str.startswith("Underwriter")].copy()
    uw_summary = uw_summary[["variable", "N", "mean", "original_mean", "source"]].dropna(subset=["N"])
    scope_summary = source_audit[
        source_audit["variable"].isin(["ScopeLen", "ScopeLen_char", "ScopeLen_gb18030", "ScopeLen_log1p_char"])
    ].copy()
    scope_summary = scope_summary[["variable", "N", "mean", "original_mean", "source"]]

    lines = [
        "# Table 2 existing controls patch 试跑",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 这次做了什么",
        "",
        "- 用已有 `IPO_Ipobasic.Sponsfm` 重构 `Underwriter`，主口径为上市当年 IPO 募资额 Top10。",
        "- 用已有 `STK_LISTEDCOINFOANL.BusinessScope` 构造 `ScopeLen = ln(清洗后经营范围 UTF-8 字节长度)`，同时保留字符数和 GB18030 字节长度审计。",
        "- 没有硬造 `NumIndSeg / NumProdSeg / RD_Staff`，所以仍不是 strict original replication。",
        "",
        "## 新变量描述统计",
        "",
        *base.md_table(panel, list(panel.columns), digits=3),
        "",
        "## Underwriter 来源审计",
        "",
        *base.md_table(uw_summary, ["variable", "N", "mean", "original_mean", "source"], digits=3),
        "",
        "## ScopeLen 来源审计",
        "",
        *base.md_table(scope_summary, ["variable", "N", "mean", "original_mean", "source"], digits=3),
        "",
        "## 主回归结果",
        "",
        *base.md_table(main, ["sample", "model", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"], digits=4),
        "",
        "## Underwriter 变体敏感性",
        "",
        *base.md_table(sens, ["model", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"], digits=4),
        "",
        "## 直接读法",
        "",
        "- `Underwriter_old` 均值约 0.009，确认是错字段；`Sponsfm` 重构后主口径均值约 0.632，已回到原文 0.574 附近。",
        "- `ScopeLen` 覆盖 542 家；字符数口径明显偏低，UTF-8 字节口径更接近原文，说明原文长度更可能是程序/数据库字节长度而非中文字符数。",
        "- 加上这两项后，Table 2 的 `FInvention` 保持负向并达到 10% 边界显著；`BHAR` 转弱正；`FSales_Growth` 仍正。也就是说 controls patch 只救回了 Panel B 的创新列，没有单独救回原文三列。",
        "- 下一步真正卡点是 `NumIndSeg / NumProdSeg / RD_Staff` 和 Y 口径，而不是继续调摘要长度。",
        "",
        "## 输出",
        "",
        f"- master：`{MASTER_OUT}`",
        f"- descriptives：`{DESC_OUT}`",
        f"- regressions：`{REG_OUT}`",
        f"- source audit：`{SOURCE_AUDIT_OUT}`",
        "",
    ]
    DOC_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    df = load_master()
    ipo = read_ipo_basic()
    df, underwriter_audit = add_underwriter_variants(df, ipo)
    df, scope_audit = add_scope_len(df)
    source_audit = pd.concat([underwriter_audit, scope_audit], ignore_index=True)

    df.to_csv(MASTER_OUT, index=False, encoding="utf-8-sig")
    desc = base.descriptives_vs_original(df)
    desc.to_csv(DESC_OUT, index=False, encoding="utf-8-sig")
    regs = regression_grid(df)
    regs.to_csv(REG_OUT, index=False, encoding="utf-8-sig")
    source_audit.to_csv(SOURCE_AUDIT_OUT, index=False, encoding="utf-8-sig")
    build_doc(df, desc, regs, source_audit)

    print(f"master={MASTER_OUT}")
    print(f"descriptives={DESC_OUT}")
    print(f"regressions={REG_OUT}")
    print(f"source_audit={SOURCE_AUDIT_OUT}")
    print(f"doc={DOC_OUT}")
    print(
        regs[
            regs["model"].isin(
                ["controls_fe_repaired_underwriter", "controls_fe_repaired_underwriter_scope"]
            )
            & regs["sample"].eq("full_by_y_available")
        ][["model", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"]].to_string(index=False)
    )


if __name__ == "__main__":
    main()
