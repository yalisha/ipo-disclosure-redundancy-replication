#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from datetime import date
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd


PROJECT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
EXISTING_PATCH_SCRIPT = PROJECT / "scripts/run_existing_controls_patch_20260706.py"

SEGMENT_ZIPS = [
    Path(
        "/Users/mac/computerscience/第三方资料/90_临时下载待归档/"
        "营业收入、营业成本103046576(仅供四川大学使用).zip"
    ),
    Path(
        "/Users/mac/computerscience/第三方资料/90_临时下载待归档/"
        "营业收入、营业成本105043738(仅供四川大学使用).zip"
    ),
]
RD_ZIP = Path(
    "/Users/mac/computerscience/第三方资料/90_临时下载待归档/"
    "研发投入情况表104054450(仅供四川大学使用).zip"
)

RUN_DIR = PROJECT / "results/table2_listing_year_segment_controls_20260706"
DOC_OUT = PROJECT / "docs/00_current/table2_listing_year_segment_controls_20260706.md"

MASTER_OUT = RUN_DIR / "table2_listing_year_segment_controls_master_20260706.csv"
DESC_OUT = RUN_DIR / "table2_listing_year_segment_controls_descriptives_20260706.csv"
REG_OUT = RUN_DIR / "table2_listing_year_segment_controls_regressions_20260706.csv"
SOURCE_AUDIT_OUT = RUN_DIR / "table2_listing_year_segment_controls_source_audit_20260706.csv"
SEGMENT_COUNTS_OUT = RUN_DIR / "table2_listing_year_segment_counts_20260706.csv"
RD_ROWS_OUT = RUN_DIR / "table2_rd_staff_rows_20260706.csv"


def load_existing_patch_module():
    spec = importlib.util.spec_from_file_location("existing_controls_patch", EXISTING_PATCH_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {EXISTING_PATCH_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


patch = load_existing_patch_module()
base = patch.base

OUTCOMES = patch.OUTCOMES
FE_VARS = patch.FE_VARS
CURRENT_CONTROL_VARS = patch.CURRENT_CONTROL_VARS
ORIGINAL_PANEL_A = patch.ORIGINAL_PANEL_A


def z6(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)


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


def valid_segment_item(series: pd.Series) -> pd.Series:
    item = series.astype(str).str.strip()
    invalid = {"", "nan", "None", "合计", "总计", "小计", "总额"}
    return ~item.isin(invalid)


def read_segment_rows(keys: pd.DataFrame) -> pd.DataFrame:
    codes = set(keys["code"].dropna().astype(str))
    target_years = set(pd.to_numeric(keys["segment_target_year"], errors="coerce").dropna().astype(int))
    parts: list[pd.DataFrame] = []
    for zip_path in SEGMENT_ZIPS:
        with ZipFile(zip_path) as zf:
            for member in ["FN_Fn048.dta", "FN_Fn0481.dta"]:
                if member not in zf.namelist():
                    continue
                with zf.open(member) as f:
                    for chunk in pd.read_stata(f, chunksize=450_000, convert_categoricals=False):
                        chunk["code"] = z6(chunk["Stkcd"])
                        chunk["Accper"] = pd.to_datetime(chunk["Accper"], errors="coerce")
                        chunk["segment_year"] = chunk["Accper"].dt.year
                        sub = chunk[
                            chunk["code"].isin(codes)
                            & chunk["segment_year"].isin(target_years)
                            & chunk["Typrep"].eq(1.0)
                            & chunk["Sgnyea"].eq(1.0)
                            & chunk["fn04814"].isin([1.0, 3.0])
                            & chunk["Fn04801"].isin([1.0, 3.0])
                        ].copy()
                        if sub.empty:
                            continue
                        sub["source_zip"] = zip_path.name
                        sub["source_member"] = member
                        parts.append(sub)
    if not parts:
        return pd.DataFrame()

    rows = pd.concat(parts, ignore_index=True)
    rows["segment_item"] = rows["Fn04802"].astype(str).str.strip()
    rows["segment_amount"] = pd.to_numeric(rows["Fn04804"], errors="coerce")
    rows = rows[valid_segment_item(rows["segment_item"])].copy()
    rows = rows[rows["segment_amount"].isna() | rows["segment_amount"].gt(0)].copy()
    rows = rows.drop_duplicates(
        ["code", "Accper", "Typrep", "Sgnyea", "fn04814", "Fn04801", "segment_item", "Fn04804"]
    )
    return rows


def build_segment_controls(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    keys = master[["code", "sec_code", "sec_name", "listing_year"]].drop_duplicates("code").copy()
    keys["segment_target_year"] = pd.to_numeric(keys["listing_year"], errors="coerce").astype("Int64")
    rows = read_segment_rows(keys)
    out = keys[["code", "segment_target_year"]].copy()
    audit_rows: list[dict] = []

    if rows.empty:
        for name in ["NumIndSeg", "NumProdSeg"]:
            out[name] = np.nan
        return out, pd.DataFrame(audit_rows), rows

    labels = {1.0: "NumIndSeg", 3.0: "NumProdSeg"}
    source_labels = {1.0: "main_business_revenue", 3.0: "operating_revenue_fallback"}
    for seg_type, variable in labels.items():
        counts = (
            rows[rows["Fn04801"].eq(seg_type)]
            .groupby(["code", "segment_year", "fn04814"])["segment_item"]
            .nunique()
            .reset_index(name="count")
        )
        main = counts[counts["fn04814"].eq(1.0)][["code", "segment_year", "count"]].rename(
            columns={"count": f"{variable}_count_main"}
        )
        operating = counts[counts["fn04814"].eq(3.0)][["code", "segment_year", "count"]].rename(
            columns={"count": f"{variable}_count_operating"}
        )
        merged = main.merge(operating, on=["code", "segment_year"], how="outer")
        merged[f"{variable}_count"] = merged[f"{variable}_count_main"].combine_first(
            merged[f"{variable}_count_operating"]
        )
        merged[f"{variable}_source"] = pd.Series(pd.NA, index=merged.index, dtype="object")
        merged.loc[merged[f"{variable}_count_operating"].notna(), f"{variable}_source"] = source_labels[3.0]
        merged.loc[merged[f"{variable}_count_main"].notna(), f"{variable}_source"] = source_labels[1.0]
        merged[f"{variable}"] = np.log1p(merged[f"{variable}_count"])
        merged[f"{variable}_ln_count"] = np.log(merged[f"{variable}_count"])
        out = out.merge(
            merged[
                [
                    "code",
                    "segment_year",
                    f"{variable}_count",
                    f"{variable}_count_main",
                    f"{variable}_count_operating",
                    f"{variable}_source",
                    f"{variable}",
                    f"{variable}_ln_count",
                ]
            ],
            left_on=["code", "segment_target_year"],
            right_on=["code", "segment_year"],
            how="left",
        ).drop(columns=["segment_year"])

        for rule, col in [("main_else_operating_ln1p", variable), ("main_only_ln1p", f"{variable}_count_main")]:
            series = out[col] if col == variable else np.log1p(out[col])
            audit_rows.append(
                {
                    "variable": variable,
                    "source": rule,
                    **stats(pd.Series(series)),
                    "original_mean": ORIGINAL_PANEL_A[variable]["mean"],
                    "original_median": ORIGINAL_PANEL_A[variable]["median"],
                }
            )

    audit_rows.extend(
        [
            {
                "variable": "segment_rows_valid",
                "source": "FN_Fn048 listing_year rows after filters",
                "N": int(len(rows)),
                "mean": np.nan,
                "std": np.nan,
                "p25": np.nan,
                "median": np.nan,
                "p75": np.nan,
                "original_mean": np.nan,
                "original_median": np.nan,
            },
            {
                "variable": "segment_firms_any",
                "source": "FN_Fn048 listing_year rows after filters",
                "N": int(rows["code"].nunique()),
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
    return out, pd.DataFrame(audit_rows), rows


def build_rd_staff(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    keys = master[["code", "sec_code", "sec_name", "listing_year"]].drop_duplicates("code").copy()
    keys["rd_target_year"] = (pd.to_numeric(keys["listing_year"], errors="coerce") - 1).astype("Int64")
    codes = set(keys["code"].dropna().astype(str))
    target_years = set(pd.to_numeric(keys["rd_target_year"], errors="coerce").dropna().astype(int))
    parts: list[pd.DataFrame] = []
    with ZipFile(RD_ZIP) as zf:
        with zf.open("PT_LCRDSPENDING.dta") as f:
            for chunk in pd.read_stata(f, chunksize=220_000, convert_categoricals=False):
                chunk["code"] = z6(chunk["Symbol"])
                chunk["EndDate"] = pd.to_datetime(chunk["EndDate"], errors="coerce")
                chunk["rd_year"] = chunk["EndDate"].dt.year
                sub = chunk[
                    chunk["code"].isin(codes)
                    & chunk["rd_year"].isin(target_years)
                    & chunk["StateTypeCode"].eq(1.0)
                ].copy()
                if not sub.empty:
                    parts.append(sub)

    out = keys[["code", "rd_target_year"]].copy()
    if not parts:
        out["RD_Staff"] = np.nan
        return out, pd.DataFrame(), pd.DataFrame()

    rows = pd.concat(parts, ignore_index=True)
    rows["RD_Staff"] = pd.to_numeric(rows["RDPersonRatio"], errors="coerce") / 100.0
    rows["rd_source_priority"] = rows["Source"].map({1.0: 0, 0.0: 1}).fillna(9)
    rows = rows.merge(keys[["code", "rd_target_year"]], left_on=["code", "rd_year"], right_on=["code", "rd_target_year"])
    chosen = (
        rows.sort_values(["code", "rd_year", "rd_source_priority", "Source"])
        .drop_duplicates(["code", "rd_year"], keep="first")
        .copy()
    )
    out = out.merge(
        chosen[["code", "rd_year", "Source", "RDPerson", "RDPersonRatio", "RD_Staff"]],
        left_on=["code", "rd_target_year"],
        right_on=["code", "rd_year"],
        how="left",
    ).drop(columns=["rd_year"])

    audit = pd.DataFrame(
        [
            {
                "variable": "RD_Staff",
                "source": "PT_LCRDSPENDING listing_year-1, StateTypeCode=1, Source=IPO preferred",
                **stats(out["RD_Staff"]),
                "original_mean": ORIGINAL_PANEL_A["RD_Staff"]["mean"],
                "original_median": ORIGINAL_PANEL_A["RD_Staff"]["median"],
            }
        ]
    )
    return out, audit, rows


def regression_grid(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    current_controls = " + ".join(CURRENT_CONTROL_VARS)
    segment_controls = " + ".join([*CURRENT_CONTROL_VARS, "ScopeLen", "NumIndSeg", "NumProdSeg"])
    rd_controls = f"{segment_controls} + RD_Staff"
    fe = " + C(listing_year_fe) + C(industry_fe)"
    sample_specs = [
        ("full_by_y_available", df.copy()),
        (
            "common_3y_segment_controls",
            df.dropna(subset=[*OUTCOMES, "Redundancy", *CURRENT_CONTROL_VARS, "ScopeLen", "NumIndSeg", "NumProdSeg", *FE_VARS]).copy(),
        ),
        (
            "common_3y_segment_controls_rd_staff",
            df.dropna(
                subset=[
                    *OUTCOMES,
                    "Redundancy",
                    *CURRENT_CONTROL_VARS,
                    "ScopeLen",
                    "NumIndSeg",
                    "NumProdSeg",
                    "RD_Staff",
                    *FE_VARS,
                ]
            ).copy(),
        ),
    ]
    for sample_name, sub in sample_specs:
        for dep in OUTCOMES:
            rows.append(
                base.regression_result(
                    sample_name,
                    "controls_fe_repaired_underwriter_scope",
                    dep,
                    f"{dep} ~ Redundancy + {current_controls} + ScopeLen{fe}",
                    sub,
                    "Redundancy",
                )
            )
            rows.append(
                base.regression_result(
                    sample_name,
                    "controls_fe_listing_year_segments",
                    dep,
                    f"{dep} ~ Redundancy + {segment_controls}{fe}",
                    sub,
                    "Redundancy",
                )
            )
            rows.append(
                base.regression_result(
                    sample_name,
                    "controls_fe_listing_year_segments_rd_staff",
                    dep,
                    f"{dep} ~ Redundancy + {rd_controls}{fe}",
                    sub,
                    "Redundancy",
                )
            )
    return pd.DataFrame(rows)


def build_doc(df: pd.DataFrame, desc: pd.DataFrame, regs: pd.DataFrame, source_audit: pd.DataFrame) -> None:
    panel_vars = [
        "lnN_tech",
        "Redundancy",
        "FInvention",
        "BHAR",
        "FSales_Growth",
        "RD_Staff",
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
    panel = desc[desc["variable"].isin(panel_vars)].copy()
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
        regs["sample"].eq("full_by_y_available")
        & regs["model"].isin(
            [
                "controls_fe_repaired_underwriter_scope",
                "controls_fe_listing_year_segments",
                "controls_fe_listing_year_segments_rd_staff",
            ]
        )
    ].copy()
    main = main[["model", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"]]
    common = regs[
        regs["sample"].isin(["common_3y_segment_controls", "common_3y_segment_controls_rd_staff"])
        & regs["model"].isin(["controls_fe_listing_year_segments", "controls_fe_listing_year_segments_rd_staff"])
    ].copy()
    common = common[["sample", "model", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"]]
    audit_view = source_audit[
        source_audit["variable"].isin(["RD_Staff", "NumIndSeg", "NumProdSeg", "segment_firms_any"])
    ].copy()
    audit_view = audit_view[["variable", "source", "N", "mean", "median", "p25", "p75", "original_mean", "original_median"]]

    main_model = main[main["model"].eq("controls_fe_listing_year_segments")]
    rd_model = main[main["model"].eq("controls_fe_listing_year_segments_rd_staff")]

    def result_line(frame: pd.DataFrame, dep: str) -> str:
        row = frame[frame["dep_var"].eq(dep)]
        if row.empty:
            return f"`{dep}`：no result"
        r = row.iloc[0]
        return f"`{dep}`：coef={r['coef']:.4f}, t={r['t_HC1']:.2f}, p={r['p_HC1']:.3f}, N={int(r['N'])}"

    lines = [
        "# Table 2 listing_year segment controls 试跑",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 这次做了什么",
        "",
        "- `Underwriter` 与 `ScopeLen` 继承 existing controls patch 口径。",
        "- `RD_Staff` 使用 `PT_LCRDSPENDING`，`listing_year - 1`，合并报表，`Source=IPO` 优先，`RDPersonRatio / 100`。",
        "- `NumIndSeg / NumProdSeg` 使用 `FN_Fn048` 上市当年年报附注：`fn04814=1` 主营业务收入优先；若公司当年缺主营业务收入分部，则用 `fn04814=3` 营业收入补；`Fn04801=1` 为业务/行业分部，`Fn04801=3` 为产品分部，均取 `ln(1 + count)`。",
        "",
        "## 描述统计对照",
        "",
        *base.md_table(panel, list(panel.columns), digits=3),
        "",
        "## 新变量来源审计",
        "",
        *base.md_table(audit_view, list(audit_view.columns), digits=3),
        "",
        "## 主回归结果",
        "",
        *base.md_table(main, ["model", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"], digits=4),
        "",
        "## 共同样本结果",
        "",
        *base.md_table(common, ["sample", "model", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"], digits=4),
        "",
        "## 直接读法",
        "",
        "- Segment controls 的覆盖率和量级已经可用：`NumIndSeg` N=529、`NumProdSeg` N=533，均值接近原文，但这是上市当年年报附注替代口径，不是 strict pre-IPO 口径。",
        "- `RD_Staff` 几乎贴住原文描述统计，但不属于原文 Table 2 的核心 P0 controls；加不加它主要作为敏感性。",
        "- 加入上市当年 segment controls 后，主结果为：",
        f"  - {result_line(main_model, 'FInvention')}",
        f"  - {result_line(main_model, 'BHAR')}",
        f"  - {result_line(main_model, 'FSales_Growth')}",
        "- 若再加入 `RD_Staff`，结果为：",
        f"  - {result_line(rd_model, 'FInvention')}",
        f"  - {result_line(rd_model, 'BHAR')}",
        f"  - {result_line(rd_model, 'FSales_Growth')}",
        "- 结论：这一步补齐了可观测 controls，但 Table 2 仍未 strict pass；`FInvention` 卡在 5%-10% 边界，`BHAR` 和 `FSales_Growth` 仍没有恢复原文显著负向。",
        "",
        "## 输出",
        "",
        f"- master：`{MASTER_OUT}`",
        f"- descriptives：`{DESC_OUT}`",
        f"- regressions：`{REG_OUT}`",
        f"- source audit：`{SOURCE_AUDIT_OUT}`",
        f"- segment counts：`{SEGMENT_COUNTS_OUT}`",
        f"- RD rows：`{RD_ROWS_OUT}`",
        "",
    ]
    DOC_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    df = patch.load_master()
    ipo = patch.read_ipo_basic()
    df, underwriter_audit = patch.add_underwriter_variants(df, ipo)
    df, scope_audit = patch.add_scope_len(df)
    seg_controls, segment_audit, segment_rows = build_segment_controls(df)
    rd_controls, rd_audit, rd_rows = build_rd_staff(df)

    df = df.merge(seg_controls, on="code", how="left", validate="one_to_one")
    df = df.merge(rd_controls, on="code", how="left", validate="one_to_one")

    source_audit = pd.concat([underwriter_audit, scope_audit, segment_audit, rd_audit], ignore_index=True)
    desc = base.descriptives_vs_original(df)
    regs = regression_grid(df)

    df.to_csv(MASTER_OUT, index=False, encoding="utf-8-sig")
    desc.to_csv(DESC_OUT, index=False, encoding="utf-8-sig")
    regs.to_csv(REG_OUT, index=False, encoding="utf-8-sig")
    source_audit.to_csv(SOURCE_AUDIT_OUT, index=False, encoding="utf-8-sig")
    seg_controls.to_csv(SEGMENT_COUNTS_OUT, index=False, encoding="utf-8-sig")
    rd_rows.to_csv(RD_ROWS_OUT, index=False, encoding="utf-8-sig")
    build_doc(df, desc, regs, source_audit)

    print(f"master={MASTER_OUT}")
    print(f"descriptives={DESC_OUT}")
    print(f"regressions={REG_OUT}")
    print(f"source_audit={SOURCE_AUDIT_OUT}")
    print(f"doc={DOC_OUT}")
    print(
        regs[
            regs["sample"].eq("full_by_y_available")
            & regs["model"].isin(["controls_fe_listing_year_segments", "controls_fe_listing_year_segments_rd_staff"])
        ][["model", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"]].to_string(index=False)
    )


if __name__ == "__main__":
    main()
