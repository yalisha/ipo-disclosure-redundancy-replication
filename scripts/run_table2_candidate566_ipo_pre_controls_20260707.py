#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import math
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


PROJECT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
X_PATH = PROJECT / "results/glm4_dewrap_join_candidate566_20260707/firm_metrics_candidate566_20260707.csv"
OUTCOME_PATH = PROJECT / "results/outcome_variable_probe_csmar_patent_20260702/outcome_variables_star_firm_level_csmar_patent_20260702.csv"
RUN_DIR = PROJECT / "results/table2_candidate566_ipo_pre_controls_20260707"
DOC_OUT = PROJECT / "docs/00_current/table2_candidate566_ipo_pre_controls_20260707.md"

MASTER_OUT = RUN_DIR / "table2_candidate566_ipo_pre_controls_master_20260707.csv"
DESC_OUT = RUN_DIR / "table2_candidate566_ipo_pre_controls_descriptives_20260707.csv"
REG_OUT = RUN_DIR / "table2_candidate566_ipo_pre_controls_regressions_20260707.csv"
WATERFALL_OUT = RUN_DIR / "table2_candidate566_ipo_pre_controls_waterfall_20260707.csv"
SOURCE_AUDIT_OUT = RUN_DIR / "table2_candidate566_ipo_pre_controls_source_audit_20260707.csv"


def import_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = import_module("table2_len132_base", PROJECT / "scripts/run_table2_len132_tight_audit_20260705.py")
ipoctl = import_module("ipo_pre_controls", PROJECT / "scripts/run_table2_ipo_pre_controls_20260706.py")
segctl = import_module("segment_controls", PROJECT / "scripts/run_table2_listing_year_segment_controls_20260706.py")
scopectl = import_module("scope_controls", PROJECT / "scripts/run_existing_controls_patch_20260706.py")
paper2 = import_module("paper2_probe", PROJECT / "scripts/run_original_paper_table2_probe_20260702.py")

OUTCOMES = ["FInvention", "BHAR", "FSales_Growth"]
FE_VARS = ["listing_year_fe", "industry_fe"]
ORIGINAL_PANEL_A = base.ORIGINAL_PANEL_A
ORIGINAL_PANEL_B = base.ORIGINAL_PANEL_B


def z6(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)


def stats(series: pd.Series) -> dict[str, float]:
    s = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if s.empty:
        return {"N": 0, "mean": math.nan, "std": math.nan, "p25": math.nan, "median": math.nan, "p75": math.nan}
    return {
        "N": int(s.shape[0]),
        "mean": float(s.mean()),
        "std": float(s.std(ddof=1)),
        "p25": float(s.quantile(0.25)),
        "median": float(s.median()),
        "p75": float(s.quantile(0.75)),
    }


def winsorize(series: pd.Series, p: float = 0.01) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    nonmiss = s.dropna()
    if nonmiss.empty:
        return s
    return s.clip(nonmiss.quantile(p), nonmiss.quantile(1 - p))


def load_x() -> pd.DataFrame:
    x = pd.read_csv(X_PATH, dtype={"sec_code": str}, encoding="utf-8-sig")
    x["sec_code"] = z6(x["sec_code"])
    x["code"] = x["sec_code"]
    keep = [
        "code",
        "sec_code",
        "sec_name",
        "source_run",
        "chunk_n",
        "chunk_glm4_tokens_sum",
        "summary_proxy_sum",
        "summary_glm4_sum",
        "relevant_score_mean",
        "red_chunk_proxy_mean",
        "red_chunk_glm4_mean",
        "announcement_date",
        "chunk_count",
        "tech_text_glm4_tokens",
        "lnN_tech",
        "Redundancy_proxy",
        "Redundancy_glm4",
    ]
    x = x[keep].copy()
    x["Redundancy"] = pd.to_numeric(x["Redundancy_proxy"], errors="coerce")
    x["lnN_tech"] = pd.to_numeric(x["lnN_tech"], errors="coerce")
    return x


def load_outcomes() -> pd.DataFrame:
    out = pd.read_csv(OUTCOME_PATH, dtype={"code": str}, encoding="utf-8-sig")
    out["code"] = z6(out["code"])
    out["first_trade_date"] = pd.to_datetime(out["first_trade_date"], errors="coerce")
    out["listing_year"] = pd.to_numeric(out["listing_year"], errors="coerce")
    out["FInvention"] = pd.to_numeric(out["FInvention_ln1p_auth"], errors="coerce")
    out["BHAR"] = pd.to_numeric(out["excl_first_BHAR_ew_w1p"], errors="coerce")
    out["FSales_Growth"] = pd.to_numeric(out["FSales_Growth_w1p"], errors="coerce")
    return out


def add_basic_controls(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    codes = set(master["code"].dropna().astype(str))
    listing_years = master[["code", "first_trade_date", "listing_year"]].copy()
    firm_info = paper2.load_firm_info(codes, listing_years)
    fin_current = paper2.load_financial_controls(codes, listing_years)

    master = master.merge(fin_current, on=["code", "listing_year"], how="left")
    master = master.merge(firm_info, on="code", how="left")
    master["industry_fe"] = (
        master["industry_code_patent"].fillna(master.get("IndustryCodeC")).fillna(master.get("IndustryCode"))
    )
    master["industry_fe"] = master["industry_fe"].astype(str).replace({"nan": np.nan, "<NA>": np.nan})
    master["listing_year_fe"] = pd.to_numeric(master["listing_year"], errors="coerce").astype("Int64").astype(str)
    master["listing_year_fe"] = master["listing_year_fe"].replace({"<NA>": np.nan, "nan": np.nan})

    ipo_basic = ipoctl.read_ipo_basic()
    basic_one = ipo_basic.sort_values(["code", "Listdt"]).drop_duplicates("code", keep="last")
    master = master.merge(
        basic_one[["code", "Fltcst", "Tludwfe", "Grsprc", "Listdt"]],
        on="code",
        how="left",
        validate="one_to_one",
    )
    master["Offerfee"] = np.where(pd.to_numeric(master["Fltcst"], errors="coerce").gt(0), np.log(master["Fltcst"] * 10000), np.nan)
    audit = pd.DataFrame(
        [
            {"variable": "Size", "source": "existing parquet financial controls; latest annual before first_trade_date", **stats(master["Size"])},
            {"variable": "Lev", "source": "existing parquet financial controls; latest annual before first_trade_date", **stats(master["Lev"])},
            {"variable": "ROA", "source": "existing parquet financial controls; latest annual before first_trade_date", **stats(master["ROA"])},
            {"variable": "Offerfee", "source": "IPO_Ipobasic.Fltcst", **stats(master["Offerfee"])},
            {"variable": "Age", "source": "firm_info EstablishDate to first_trade_date", **stats(master["Age"])},
        ]
    )
    return master, audit


def build_master() -> tuple[pd.DataFrame, pd.DataFrame]:
    master = load_x().merge(load_outcomes(), on="code", how="left", suffixes=("", "_outcome"), validate="one_to_one")
    master, basic_audit = add_basic_controls(master)

    # ScopeLen from listed-company annual basic info.
    master, scope_audit = scopectl.add_scope_len(master)

    # Segment controls and annual-report RD staff.
    seg_controls, segment_audit, segment_rows = segctl.build_segment_controls(master)
    rd_staff_annual, rd_staff_annual_audit, rd_rows = segctl.build_rd_staff(master)
    master = master.merge(seg_controls, on="code", how="left", validate="one_to_one")
    master = master.merge(rd_staff_annual, on="code", how="left", validate="one_to_one")

    # IPO underwriter, IPO employee R&D, and IPO pre-listing financials.
    ipo_basic = ipoctl.read_ipo_basic()
    underwriter_flags, underwriter_audit, top_rows = ipoctl.build_ipocsne_underwriter(master, ipo_basic)
    ipo_rd, ipo_rd_audit, employee_rows = ipoctl.build_ipo_rd_staff(master)
    ipo_fin, ipo_fin_audit, fin_rows = ipoctl.build_ipo_pre_financials(master)
    master = master.merge(
        underwriter_flags.drop(columns=["sec_code", "sec_name", "listing_year"], errors="ignore"),
        on="code",
        how="left",
        validate="one_to_one",
    )
    master = master.merge(
        ipo_rd.drop(columns=["sec_code", "sec_name"], errors="ignore"),
        on="code",
        how="left",
        validate="one_to_one",
    )
    master = master.merge(ipo_fin, on="code", how="left", validate="one_to_one")

    source_audit = pd.concat(
        [
            basic_audit,
            scope_audit,
            segment_audit,
            rd_staff_annual_audit,
            underwriter_audit,
            ipo_rd_audit,
            ipo_fin_audit,
        ],
        ignore_index=True,
        sort=False,
    )
    source_audit.to_csv(SOURCE_AUDIT_OUT, index=False, encoding="utf-8-sig")
    return master, source_audit


def descriptives(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        "lnN_tech": "lnN_tech",
        "Redundancy": "Redundancy",
        "FInvention": "FInvention",
        "BHAR": "BHAR",
        "FSales_Growth": "FSales_Growth",
        "Size": "Size",
        "Size_ipo_pre": "Size",
        "Lev": "Lev",
        "Lev_ipo_pre": "Lev",
        "ROA": "ROA",
        "ROA_ipo_pre": "ROA",
        "Offerfee": "Offerfee",
        "Underwriter_ipo": "Underwriter",
        "Age": "Age",
        "NumIndSeg": "NumIndSeg",
        "NumProdSeg": "NumProdSeg",
        "ScopeLen": "ScopeLen",
        "RD_Staff": "RD_Staff",
        "RD_Staff_ipo": "RD_Staff",
    }
    rows = []
    for var, paper_var in mapping.items():
        if var not in df.columns:
            continue
        cur = stats(df[var])
        paper = ORIGINAL_PANEL_A[paper_var]
        rows.append(
            {
                "variable": var,
                "paper_variable": paper_var,
                **{f"current_{k}": v for k, v in cur.items()},
                "paper_N": paper["N"],
                "paper_mean": paper["mean"],
                "paper_median": paper["median"],
                "mean_gap": cur["mean"] - paper["mean"],
            }
        )
    return pd.DataFrame(rows)


def regression_result(sample: str, model: str, dep: str, formula: str, df: pd.DataFrame) -> dict[str, object]:
    try:
        fit = smf.ols(formula, data=df).fit(cov_type="HC1")
        return {
            "sample": sample,
            "model": model,
            "dep_var": dep,
            "N": int(fit.nobs),
            "coef": float(fit.params.get("Redundancy", np.nan)),
            "se_HC1": float(fit.bse.get("Redundancy", np.nan)),
            "t_HC1": float(fit.tvalues.get("Redundancy", np.nan)),
            "p_HC1": float(fit.pvalues.get("Redundancy", np.nan)),
            "adj_r2": float(fit.rsquared_adj),
            "formula": formula,
            "error": "",
        }
    except Exception as exc:
        return {
            "sample": sample,
            "model": model,
            "dep_var": dep,
            "N": 0,
            "coef": np.nan,
            "se_HC1": np.nan,
            "t_HC1": np.nan,
            "p_HC1": np.nan,
            "adj_r2": np.nan,
            "formula": formula,
            "error": repr(exc),
        }


def build_regressions(df: pd.DataFrame) -> pd.DataFrame:
    model_specs = {
        "current_controls_fe": ["lnN_tech", "Size", "Lev", "ROA", "Offerfee", "Underwriter_ipo", "Age"],
        "segment_controls_fe": [
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
        "ipo_pre_fin_controls_fe": [
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
        "ipo_pre_fin_controls_rd_staff_fe": [
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
    sample_defs = [
        ("candidate566_full", df.copy()),
        ("candidate566_2019_2022", df[pd.to_numeric(df["listing_year"], errors="coerce").between(2019, 2022)].copy()),
    ]
    rows = []
    for sample_name, sub in sample_defs:
        for model_name, controls in model_specs.items():
            missing = [c for c in controls if c not in sub.columns]
            if missing:
                for dep in OUTCOMES:
                    rows.append(
                        {
                            "sample": sample_name,
                            "model": model_name,
                            "dep_var": dep,
                            "N": 0,
                            "coef": np.nan,
                            "se_HC1": np.nan,
                            "t_HC1": np.nan,
                            "p_HC1": np.nan,
                            "adj_r2": np.nan,
                            "formula": "",
                            "error": f"missing controls: {missing}",
                        }
                    )
                continue
            rhs = "Redundancy + " + " + ".join(controls) + " + C(listing_year_fe) + C(industry_fe)"
            for dep in OUTCOMES:
                rows.append(regression_result(sample_name, model_name, dep, f"{dep} ~ {rhs}", sub))
    return pd.DataFrame(rows)


def build_waterfall(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    controls = [
        "Redundancy",
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
        *FE_VARS,
    ]

    def add(scope: str, sub: pd.DataFrame) -> None:
        rows.extend(
            [
                {"scope": scope, "step": "X universe", "N": int(sub["code"].nunique())},
                {"scope": scope, "step": "FInvention nonmissing", "N": int(sub.dropna(subset=["FInvention"])["code"].nunique())},
                {"scope": scope, "step": "BHAR nonmissing", "N": int(sub.dropna(subset=["BHAR"])["code"].nunique())},
                {"scope": scope, "step": "FSales_Growth nonmissing", "N": int(sub.dropna(subset=["FSales_Growth"])["code"].nunique())},
                {"scope": scope, "step": "all 3 Y nonmissing", "N": int(sub.dropna(subset=OUTCOMES)["code"].nunique())},
                {"scope": scope, "step": "ipo_pre + segment + RD staff controls complete", "N": int(sub.dropna(subset=controls)["code"].nunique())},
                {
                    "scope": scope,
                    "step": "all 3 Y + ipo_pre controls complete",
                    "N": int(sub.dropna(subset=[*OUTCOMES, *controls])["code"].nunique()),
                },
            ]
        )

    add("candidate566_2019_2023", df)
    add("candidate566_2019_2022", df[pd.to_numeric(df["listing_year"], errors="coerce").between(2019, 2022)])
    return pd.DataFrame(rows)


def write_doc(df: pd.DataFrame, desc: pd.DataFrame, regs: pd.DataFrame, waterfall: pd.DataFrame) -> None:
    desc_view = desc[
        desc["variable"].isin(
            [
                "lnN_tech",
                "Redundancy",
                "FInvention",
                "BHAR",
                "FSales_Growth",
                "Size_ipo_pre",
                "Lev_ipo_pre",
                "ROA_ipo_pre",
                "Offerfee",
                "Underwriter_ipo",
                "Age",
                "NumIndSeg",
                "NumProdSeg",
                "ScopeLen",
                "RD_Staff_ipo",
            ]
        )
    ].copy()
    main = regs[
        regs["model"].isin(["ipo_pre_fin_controls_fe", "ipo_pre_fin_controls_rd_staff_fe"])
        & regs["sample"].isin(["candidate566_full", "candidate566_2019_2022"])
    ].copy()
    main = main[["sample", "model", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2", "error"]]
    compare_rows = []
    for _, row in main.iterrows():
        orig = ORIGINAL_PANEL_B[row["dep_var"]]
        compare_rows.append(
            {
                **row.to_dict(),
                "paper_coef": orig["coef"],
                "paper_t": orig["t"],
                "paper_N": orig["N"],
                "sign_match": bool(pd.notna(row["coef"]) and ((row["coef"] < 0) == (orig["coef"] < 0))),
            }
        )
    compare = pd.DataFrame(compare_rows)
    lines = [
        "# Table 2 Candidate566 IPO Pre Controls Rerun",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 结论",
        "",
        "- 这次用 candidate566 X 重建了 Table 2 master，而不是沿用旧 543 master。",
        "- Y 文件本来就覆盖 567 家，因此首批25家的 `FInvention/BHAR/FSales_Growth` 已经可以接入。",
        "- 完整 candidate566 下，X 描述统计继续贴原文；但 Table 2 仍不是 strict pass。",
        "- 2019-2022 子样本更接近原文 Panel B 的 N，但控制变量完整样本仍高于/不同于原文 471，说明还需要找原文额外排除规则。",
        "",
        "## 样本 Waterfall",
        "",
        *base.md_table(waterfall, ["scope", "step", "N"], digits=0),
        "",
        "## 描述统计对照",
        "",
        *base.md_table(
            desc_view,
            ["variable", "current_N", "current_mean", "paper_N", "paper_mean", "mean_gap", "current_median", "paper_median"],
            digits=3,
        ),
        "",
        "## 主规格 vs 原文 Panel B",
        "",
        *base.md_table(
            compare,
            ["sample", "model", "dep_var", "N", "coef", "t_HC1", "p_HC1", "paper_coef", "paper_t", "paper_N", "sign_match"],
            digits=4,
        ),
        "",
        "## 直接读法",
        "",
        "- `FInvention` 在加入首批25家后仍保持负向，但显著性和幅度取决于 controls/sample。",
        "- `BHAR` 与 `FSales_Growth` 仍没有稳定恢复原文显著负向。",
        "- 现在最关键的不是 X，而是：原文 Table 1 的 552 样本筛选、Table 2 的 471 样本筛选、以及 BHAR/FSales 的精确定义。",
        "",
        "## 输出",
        "",
        f"- master：`{MASTER_OUT}`",
        f"- descriptives：`{DESC_OUT}`",
        f"- regressions：`{REG_OUT}`",
        f"- waterfall：`{WATERFALL_OUT}`",
        f"- source audit：`{SOURCE_AUDIT_OUT}`",
        "",
    ]
    DOC_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    master, source_audit = build_master()
    desc = descriptives(master)
    regs = build_regressions(master)
    waterfall = build_waterfall(master)

    master.to_csv(MASTER_OUT, index=False, encoding="utf-8-sig")
    desc.to_csv(DESC_OUT, index=False, encoding="utf-8-sig")
    regs.to_csv(REG_OUT, index=False, encoding="utf-8-sig")
    waterfall.to_csv(WATERFALL_OUT, index=False, encoding="utf-8-sig")
    write_doc(master, desc, regs, waterfall)

    print(f"master={MASTER_OUT}")
    print(f"descriptives={DESC_OUT}")
    print(f"regressions={REG_OUT}")
    print(f"waterfall={WATERFALL_OUT}")
    print(f"doc={DOC_OUT}")
    print(waterfall.to_string(index=False))
    print(
        regs[
            regs["model"].isin(["ipo_pre_fin_controls_fe", "ipo_pre_fin_controls_rd_staff_fe"])
            & regs["sample"].isin(["candidate566_full", "candidate566_2019_2022"])
        ][["sample", "model", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2", "error"]].to_string(index=False)
    )


if __name__ == "__main__":
    main()
