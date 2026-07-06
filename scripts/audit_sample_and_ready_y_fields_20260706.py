#!/usr/bin/env python3
from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd


PROJECT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
THIRD_PARTY = Path("/Users/mac/computerscience/第三方资料")
IPO_DIR = THIRD_PARTY / "90_临时下载待归档/IPO库"
MASTER_IN = (
    PROJECT
    / "results/table2_ipo_pre_controls_20260706/"
    "table2_ipo_pre_controls_master_20260706.csv"
)
SAMPLE_543_IN = (
    PROJECT
    / "results/summary_len_calibration_full_543_20260704/"
    "sample_543_firms_20260704.csv"
)

RUN_DIR = PROJECT / "results/sample_and_ready_y_fields_audit_20260706"
DOC_OUT = PROJECT / "docs/00_current/sample_and_ready_y_fields_audit_20260706.md"

UNIVERSE_OUT = RUN_DIR / "csmar_star_ipo_universe_2019_2023_20260706.csv"
SAMPLE_COMPARE_OUT = RUN_DIR / "sample_543_vs_csmar_universe_compare_20260706.csv"
MISSING_UNIVERSE_OUT = RUN_DIR / "sample_missing_from_x_20260706.csv"
EXTRA_X_OUT = RUN_DIR / "sample_extra_not_in_csmar_2019_2023_20260706.csv"
TABLE2_WATERFALL_OUT = RUN_DIR / "table2_471_waterfall_20260706.csv"
CONTROL_MISSING_OUT = RUN_DIR / "table2_control_missing_2019_2022_20260706.csv"
READY_FIELDS_OUT = RUN_DIR / "ready_y_field_inventory_20260706.csv"

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


def z6(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text.zfill(6) if text.isdigit() else text


def read_zipped_dta(zip_path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    with ZipFile(zip_path) as zf:
        member = [n for n in zf.namelist() if n.lower().endswith(".dta")][0]
        with tempfile.NamedTemporaryFile(suffix=".dta") as tmp:
            tmp.write(zf.read(member))
            tmp.flush()
            return pd.read_stata(tmp.name, convert_categoricals=False, columns=columns)


def load_ipobasic_universe() -> pd.DataFrame:
    ipobasic = read_zipped_dta(
        IPO_DIR / "招股及上市基本情况表173730614(仅供四川大学使用).zip",
        columns=["Stkcd", "T1", "Listdt", "Ipostpbdt", "Ipostsbdt", "Aiprc", "Grsprc", "Fltcst", "Sponsfm"],
    )
    cobasic = read_zipped_dta(
        IPO_DIR / "公司基本情况表173730945(仅供四川大学使用).zip",
        columns=["Stkcd", "Stknme", "Conme", "Listdt", "Listexg", "Nindcd", "Nindnme", "IndustryCodeC", "IndustryNameC"],
    )
    for df in (ipobasic, cobasic):
        df["code"] = df["Stkcd"].map(z6)
        df["Listdt_dt"] = pd.to_datetime(df["Listdt"], errors="coerce")
    ipobasic = ipobasic[
        ipobasic["code"].str.startswith("688", na=False)
        & ipobasic["T1"].eq("A")
        & ipobasic["Listdt_dt"].between("2019-01-01", "2023-12-31")
    ].copy()
    cobasic = cobasic[["code", "Stknme", "Conme", "Listexg", "Nindcd", "Nindnme", "IndustryCodeC", "IndustryNameC"]].drop_duplicates("code")
    out = ipobasic.merge(cobasic, on="code", how="left")
    out = out.rename(
        columns={
            "Stknme": "sec_name_csmar",
            "Conme": "company_name_csmar",
            "Listdt_dt": "list_date_csmar",
            "Ipostpbdt": "prospectus_publish_date_csmar",
            "Ipostsbdt": "prospectus_sign_date_csmar",
            "Aiprc": "issue_price",
            "Grsprc": "gross_proceeds",
            "Fltcst": "issue_fee",
            "Sponsfm": "sponsor",
        }
    )
    out["list_year_csmar"] = out["list_date_csmar"].dt.year
    keep = [
        "code",
        "sec_name_csmar",
        "company_name_csmar",
        "list_date_csmar",
        "list_year_csmar",
        "prospectus_publish_date_csmar",
        "prospectus_sign_date_csmar",
        "issue_price",
        "gross_proceeds",
        "issue_fee",
        "sponsor",
        "Listexg",
        "Nindcd",
        "Nindnme",
        "IndustryCodeC",
        "IndustryNameC",
    ]
    return out[keep].sort_values(["list_date_csmar", "code"]).drop_duplicates("code")


def load_master() -> pd.DataFrame:
    df = pd.read_csv(MASTER_IN, dtype={"code": str, "sec_code": str}, encoding="utf-8-sig")
    df["code"] = df["code"].map(z6)
    df["sec_code"] = df["sec_code"].map(z6)
    df["first_trade_date"] = pd.to_datetime(df["first_trade_date"], errors="coerce")
    df["listing_year"] = pd.to_numeric(df["listing_year"], errors="coerce")
    for col in ["Redundancy", "FInvention", "BHAR", "FSales_Growth", *CONTROL_VARS]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def build_sample_compare(universe: pd.DataFrame, master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    x = master[["code", "sec_name", "first_trade_date", "listing_year", "Redundancy", "BHAR", "FSales_Growth", "FInvention"]].drop_duplicates("code")
    compare = universe.merge(x, on="code", how="outer", indicator=True)
    compare["in_csmar_star_ipo_2019_2023"] = compare["_merge"].isin(["both", "left_only"])
    compare["in_current_x_master"] = compare["_merge"].isin(["both", "right_only"])
    compare["valid_overlap"] = compare["_merge"].eq("both")
    compare["list_year_compare"] = compare["list_year_csmar"].combine_first(compare["listing_year"])
    compare = compare.sort_values(["list_year_compare", "list_date_csmar", "code"], na_position="last")
    missing = compare[compare["_merge"].eq("left_only")].copy()
    extra = compare[compare["_merge"].eq("right_only")].copy()
    return compare, missing, extra


def build_waterfall(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    control_missing_rows = []
    samples = {
        "full_2019_2023_current_master": master.index == master.index,
        "w2_2019_2022_current_master": master["listing_year"].between(2019, 2022),
    }
    steps = [
        ("universe", []),
        ("Redundancy nonmissing", ["Redundancy"]),
        ("FInvention nonmissing", ["FInvention"]),
        ("BHAR nonmissing", ["BHAR"]),
        ("FSales_Growth nonmissing", ["FSales_Growth"]),
        ("all three outcomes nonmissing", ["FInvention", "BHAR", "FSales_Growth"]),
        ("all controls nonmissing", CONTROL_VARS),
        ("FInvention regression complete", ["FInvention", "Redundancy", *CONTROL_VARS]),
        ("BHAR regression complete", ["BHAR", "Redundancy", *CONTROL_VARS]),
        ("FSales regression complete", ["FSales_Growth", "Redundancy", *CONTROL_VARS]),
    ]
    for sample, mask in samples.items():
        sub = master[mask].copy()
        for step, cols in steps:
            n = len(sub) if not cols else int(sub[cols].notna().all(axis=1).sum())
            rows.append({"sample": sample, "step": step, "N": n})
        control_missing = sub[sub[CONTROL_VARS].isna().any(axis=1)].copy()
        for firm in control_missing.itertuples(index=False):
            missing_controls = [c for c in CONTROL_VARS if pd.isna(getattr(firm, c))]
            control_missing_rows.append(
                {
                    "sample": sample,
                    "code": firm.code,
                    "sec_name": firm.sec_name,
                    "listing_year": firm.listing_year,
                    "missing_control_count": len(missing_controls),
                    "missing_controls": ",".join(missing_controls),
                }
            )
    return pd.DataFrame(rows), pd.DataFrame(control_missing_rows)


def field_inventory() -> pd.DataFrame:
    rows = []
    def add(source: str, path: Path, status: str, usable_for: str, fields: str, note: str) -> None:
        rows.append(
            {
                "source": source,
                "path": str(path),
                "status": status,
                "usable_for": usable_for,
                "fields": fields,
                "note": note,
            }
        )

    add(
        "TRD_Year 年个股回报率文件",
        THIRD_PARTY / "90_临时下载待归档/股票市场/年个股回报率文件190542267(仅供四川大学使用).zip",
        "downloaded_tested",
        "BHAR calendar-year candidate",
        "Yretwd, Yretnd, Ndaytrd, Yarkettype",
        "calendar-year annual stock return; listing-year Yretwd often missing for IPO year, not direct holding-period return",
    )
    add(
        "TRD_Cndalym 综合日市场回报率文件",
        THIRD_PARTY / "90_临时下载待归档/股票市场/综合日市场回报率文件190104355(仅供四川大学使用).zip",
        "downloaded_tested",
        "market benchmark",
        "Cdretwdeq, Cdretwdos, Cdretwdtl",
        "official composite daily market returns; benchmark replacement did not recover BHAR significance",
    )
    add(
        "市场调整股票周收益表",
        THIRD_PARTY
        / "01_数据资源/国泰安/第三方数据资源/上市公司财务信息/市场调整股票周收益表(年)102503558(仅供沪江大学使用).zip",
        "downloaded_tested",
        "BHAR weekly adjusted candidate",
        "Wretwd_Mdeq/Mdos/Mdtl, Wretwd_Cmdeq/Cmdos/Cmdtl",
        "weekly adjusted candidates were farther from paper distribution",
    )
    add(
        "上市公司利润表 annual A",
        Path("/Users/mac/computerscience/23实证选题探索/T16/risk_disclosure_trial/data/financial_csmar_20260508/income_statement_annual_A_2015_2025.csv"),
        "downloaded_tested",
        "FSales_Growth hand-built",
        "operating_revenue, total_operating_revenue",
        "current L to L+1 distribution is closest among tested accounting-year windows",
    )
    add(
        "IPO_IpoFinancialIndex 招股前财务指标表",
        IPO_DIR / "招股前财务指标表173712900(仅供四川大学使用).zip",
        "downloaded_inspected",
        "pre-IPO controls, not FSales outcome",
        "DebtToAssetratio, ROE, AssetTurnover, etc.",
        "does not contain post-listing sales growth; useful for controls only",
    )
    add(
        "FN_Fn048 营业收入、营业成本",
        THIRD_PARTY / "90_临时下载待归档/营业收入、营业成本105043738(仅供四川大学使用).zip",
        "downloaded_inspected",
        "segment controls",
        "Fn04804 revenue by segment, Fn04806 cost by segment",
        "segment table, not firm total post-listing sales growth variable",
    )
    add(
        "成长能力/财务指标分析营业收入增长率",
        Path("CSMAR not found locally"),
        "missing_download",
        "FSales_Growth ready-made candidate",
        "营业收入增长率 / operating revenue growth rate",
        "recommended next download; may match paper better than hand-built income statement growth",
    )
    add(
        "市场调整年个股回报率或持有期超额收益",
        Path("CSMAR not found locally"),
        "missing_download",
        "BHAR ready-made candidate",
        "annual market-adjusted return or holding-period excess return",
        "recommended next download if available; current local annual return is not market-adjusted holding-period return",
    )
    return pd.DataFrame(rows)


def md_table(df: pd.DataFrame, cols: list[str], max_rows: int | None = None) -> list[str]:
    view = df if max_rows is None else df.head(max_rows)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in view.iterrows():
        vals = []
        for col in cols:
            val = row.get(col, "")
            if pd.isna(val):
                vals.append("")
            elif isinstance(val, (float, np.floating)):
                vals.append(f"{float(val):.3f}")
            else:
                vals.append(str(val))
        lines.append("| " + " | ".join(vals) + " |")
    return lines


def build_doc(
    universe: pd.DataFrame,
    compare: pd.DataFrame,
    missing: pd.DataFrame,
    extra: pd.DataFrame,
    waterfall: pd.DataFrame,
    control_missing: pd.DataFrame,
    inventory: pd.DataFrame,
) -> None:
    by_year = (
        universe.groupby("list_year_csmar")["code"].nunique().reset_index(name="csmar_star_ipo_universe")
        .merge(
            compare[compare["in_current_x_master"] & compare["valid_overlap"]]
            .groupby("list_year_csmar")["code"]
            .nunique()
            .reset_index(name="current_valid_x_overlap"),
            on="list_year_csmar",
            how="left",
        )
        .fillna({"current_valid_x_overlap": 0})
    )
    by_year["x_missing_from_universe"] = by_year["csmar_star_ipo_universe"] - by_year["current_valid_x_overlap"]
    missing_preview = missing[
        ["code", "sec_name_csmar", "list_date_csmar", "prospectus_publish_date_csmar", "sponsor"]
    ].copy()
    extra_preview = extra[["code", "sec_name", "listing_year", "first_trade_date"]].copy()
    control_missing_summary = (
        control_missing[control_missing["sample"].eq("w2_2019_2022_current_master")]
        .groupby("missing_controls")
        .size()
        .reset_index(name="firm_count")
        .sort_values(["firm_count", "missing_controls"], ascending=[False, True])
    )
    lines = [
        "# 样本链条与现成 Y 字段审计",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 直接结论",
        "",
        "- 国泰安 `IPO_Ipobasic` 可重建 2019-2023 科创板首次发行上市 universe：567 家。",
        f"- 当前 X master 有 {compare['in_current_x_master'].sum()} 家，其中与 CSMAR 2019-2023 STAR IPO universe 有 {compare['valid_overlap'].sum()} 家重合；缺 CSMAR universe 内 {len(missing)} 家，另有 {len(extra)} 家不属于该 universe。",
        "- 原文 Table 1 的 552 家不是当前 543 家。现在最大风险是 X 样本没有进入原文样本制度，尤其缺 2019-07-22 首批科创板公司。",
        "- 原文 Table 2 的 471 家，和当前 2019-2022 `FSales_Growth` 非缺失数正好一致；但加入我们当前 controls 后只剩 459 家，说明 controls 口径/缺失处理也没有完全对齐原文。",
        "- 本地尚未发现可直接替代的“成长能力营业收入增长率”或“市场调整年个股/持有期超额收益”现成表；下一步需要定向下载，而不是继续盲试已有表。",
        "",
        "## CSMAR 2019-2023 STAR IPO Universe",
        "",
        *md_table(by_year, ["list_year_csmar", "csmar_star_ipo_universe", "current_valid_x_overlap", "x_missing_from_universe"]),
        "",
        "## 当前 X 缺失的 CSMAR Universe 公司",
        "",
        *md_table(missing_preview, ["code", "sec_name_csmar", "list_date_csmar", "prospectus_publish_date_csmar", "sponsor"], max_rows=40),
        "",
        "## 当前 X 中不属于 CSMAR 2019-2023 STAR IPO Universe 的公司",
        "",
        *md_table(extra_preview, ["code", "sec_name", "listing_year", "first_trade_date"], max_rows=20),
        "",
        "## Table 2 样本 Waterfall",
        "",
        *md_table(waterfall, ["sample", "step", "N"]),
        "",
        "## 2019-2022 Controls 缺失模式",
        "",
        *(
            md_table(control_missing_summary, ["missing_controls", "firm_count"], max_rows=30)
            if not control_missing_summary.empty
            else ["- 无 controls 缺失。"]
        ),
        "",
        "## 现成 Y 字段库存",
        "",
        *md_table(inventory, ["source", "status", "usable_for", "fields", "note"], max_rows=20),
        "",
        "## 下一步",
        "",
        "1. 先补齐/判定 26 家 CSMAR universe 内但当前 X 缺失的招股书文本，尤其 2019-07-22 首批科创板公司；同时剔除 `688688`、`688717` 这类不在 2019-2023 已上市 universe 内的记录。",
        "2. 用补齐后的 universe 重新计算 X；再按原文 552 逻辑判断哪些公司应被排除。没有这一步，Table 2 的系数不可解释。",
        "3. 定向下载 CSMAR 成长能力/财务指标分析中的营业收入增长率字段，以及市场调整年个股回报率或持有期超额收益字段。",
        "4. 如果现成字段仍不能恢复 `BHAR/FSales_Growth`，再考虑联系作者或把文章复现结论写成“X 可复刻、Y/样本制度不可完全复刻”。",
        "",
        "## 输出",
        "",
        f"- universe：`{UNIVERSE_OUT}`",
        f"- sample compare：`{SAMPLE_COMPARE_OUT}`",
        f"- missing from X：`{MISSING_UNIVERSE_OUT}`",
        f"- extra X：`{EXTRA_X_OUT}`",
        f"- Table 2 waterfall：`{TABLE2_WATERFALL_OUT}`",
        f"- control missing：`{CONTROL_MISSING_OUT}`",
        f"- ready field inventory：`{READY_FIELDS_OUT}`",
        "",
    ]
    DOC_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    universe = load_ipobasic_universe()
    master = load_master()
    compare, missing, extra = build_sample_compare(universe, master)
    waterfall, control_missing = build_waterfall(master)
    inventory = field_inventory()

    universe.to_csv(UNIVERSE_OUT, index=False, encoding="utf-8-sig")
    compare.to_csv(SAMPLE_COMPARE_OUT, index=False, encoding="utf-8-sig")
    missing.to_csv(MISSING_UNIVERSE_OUT, index=False, encoding="utf-8-sig")
    extra.to_csv(EXTRA_X_OUT, index=False, encoding="utf-8-sig")
    waterfall.to_csv(TABLE2_WATERFALL_OUT, index=False, encoding="utf-8-sig")
    control_missing.to_csv(CONTROL_MISSING_OUT, index=False, encoding="utf-8-sig")
    inventory.to_csv(READY_FIELDS_OUT, index=False, encoding="utf-8-sig")
    build_doc(universe, compare, missing, extra, waterfall, control_missing, inventory)

    print(f"doc={DOC_OUT}")
    print(f"universe={len(universe)} current_x={compare['in_current_x_master'].sum()} overlap={compare['valid_overlap'].sum()} missing={len(missing)} extra={len(extra)}")
    print("missing by year:")
    print(missing.groupby("list_year_csmar")["code"].nunique().to_string())
    print("waterfall:")
    print(waterfall.to_string(index=False))


if __name__ == "__main__":
    main()
