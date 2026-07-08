#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
DATE_TAG = "20260708"
TABLE2_MASTER = ROOT / "results/cutoff552_table2_471_probe_20260707/table2_471_candidate_master_20260707.csv"
DEFAULT_FIRM_METRICS = (
    ROOT / "results/glm300_tailmerge_floor_candidates_20260708/proxy_tailmerge1600_floor50_firm_metrics_20260708.csv"
)
RUN_DIR = ROOT / f"results/glm_table2_strict_master_{DATE_TAG}"
DOC_OUT = ROOT / f"docs/00_current/glm_table2_strict_master_{DATE_TAG}.md"

OUTCOMES = ["FInvention", "BHAR", "FSales_Growth"]
ORIGINAL_PANEL_B = {
    "FInvention": {"coef": -0.0316, "t": -1.72, "N": 471, "adj_r2": 0.32},
    "BHAR": {"coef": -0.0188, "t": -2.14, "N": 471, "adj_r2": 0.06},
    "FSales_Growth": {"coef": -0.0373, "t": -2.02, "N": 471, "adj_r2": 0.05},
}
ORIGINAL_PANEL_A = {
    "Redundancy": {"N": 552, "mean": 29.074, "std": 2.630, "median": 28.910},
    "FInvention": {"N": 471, "mean": 2.282, "std": 1.200, "median": 2.197},
    "BHAR": {"N": 471, "mean": -0.036, "std": 0.514, "median": -0.170},
    "FSales_Growth": {"N": 471, "mean": 0.530, "std": 1.522, "median": 0.180},
    "Size": {"N": 552, "mean": 20.741, "std": 0.990, "median": 20.533},
    "Lev": {"N": 552, "mean": 0.356, "std": 0.183, "median": 0.334},
    "ROA": {"N": 552, "mean": 0.094, "std": 0.145, "median": 0.100},
    "Offerfee": {"N": 552, "mean": 18.325, "std": 0.483, "median": 18.270},
    "Underwriter": {"N": 552, "mean": 0.574, "std": 0.495, "median": 1.000},
    "Age": {"N": 552, "mean": 2.601, "std": 0.408, "median": 2.639},
    "NumIndSeg": {"N": 552, "mean": 0.854, "std": 0.361, "median": 0.693},
    "NumProdSeg": {"N": 552, "mean": 1.475, "std": 0.376, "median": 1.609},
    "ScopeLen": {"N": 552, "mean": 5.671, "std": 0.854, "median": 5.762},
    "RD_Staff": {"N": 552, "mean": 0.305, "std": 0.194, "median": 0.240},
}

SPEC_CONTROLS = {
    "paper_exact_current_fin_fe": [
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
    "paper_exact_ipo_pre_fin_fe": [
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
    "rd_staff_extra_current_fin_fe": [
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
    "rd_staff_extra_ipo_pre_fin_fe": [
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
FE_TERMS = " + C(listing_year_fe) + C(industry_fe)"


def z6(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)


def fmt(value: object, digits: int = 4) -> str:
    if pd.isna(value):
        return ""
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return str(value)


def md_table(df: pd.DataFrame, cols: list[str], digits: int = 4, max_rows: int | None = None) -> list[str]:
    view = df if max_rows is None else df.head(max_rows)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, row in view.iterrows():
        vals = []
        for col in cols:
            val = row.get(col, "")
            if isinstance(val, (float, np.floating)):
                vals.append(fmt(val, digits))
            elif isinstance(val, (int, np.integer)):
                vals.append(str(int(val)))
            elif pd.isna(val):
                vals.append("")
            else:
                vals.append(str(val))
        out.append("| " + " | ".join(vals) + " |")
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--table2-master", type=Path, default=TABLE2_MASTER)
    parser.add_argument("--firm-metrics", type=Path, default=DEFAULT_FIRM_METRICS)
    parser.add_argument("--label", default="glm300_proxy_tailmerge1600_floor50")
    parser.add_argument("--doc-out", type=Path, default=DOC_OUT)
    return parser.parse_args()


def load_master(table2_master: Path, firm_metrics: Path, label: str) -> pd.DataFrame:
    master = pd.read_csv(table2_master, dtype={"code": str, "sec_code": str}, encoding="utf-8-sig", low_memory=False)
    master["code"] = z6(master["code"])
    master["sec_code"] = z6(master["sec_code"])
    firm = pd.read_csv(firm_metrics, dtype={"sec_code": str}, encoding="utf-8-sig")
    firm["sec_code"] = z6(firm["sec_code"])
    firm = firm.rename(
        columns={
            "Redundancy": "Redundancy_glm",
            "lnN_tech": "lnN_tech_glm",
            "chunk_n": "chunk_n_glm",
            "text_sum": "text_sum_glm",
            "summary_sum": "summary_sum_glm",
        }
    )
    keep = [
        "sec_code",
        "Redundancy_glm",
        "lnN_tech_glm",
        "chunk_n_glm",
        "text_sum_glm",
        "summary_sum_glm",
    ]
    keep = [c for c in keep if c in firm.columns]
    out = master.merge(firm[keep], on="sec_code", how="inner", validate="one_to_one")
    out["glm_label"] = label
    out["Redundancy_prior_table2"] = pd.to_numeric(out["Redundancy"], errors="coerce")
    out["lnN_tech_prior_table2"] = pd.to_numeric(out["lnN_tech"], errors="coerce")
    out["Redundancy"] = pd.to_numeric(out["Redundancy_glm"], errors="coerce")
    out["lnN_tech"] = pd.to_numeric(out["lnN_tech_glm"], errors="coerce")

    numeric_cols = sorted(
        {
            "Redundancy",
            "lnN_tech",
            *OUTCOMES,
            "Size",
            "Lev",
            "ROA",
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
            "RD_Staff",
        }
        & set(out.columns)
    )
    for col in numeric_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["listing_year_fe"] = out["listing_year_fe"].astype(str).replace({"nan": np.nan, "<NA>": np.nan})
    out["industry_fe"] = out["industry_fe"].astype(str).replace({"nan": np.nan, "<NA>": np.nan})
    return out


def regression_result(spec: str, dep: str, controls: list[str], df: pd.DataFrame) -> dict[str, object]:
    missing = [c for c in [dep, "Redundancy", *controls, "listing_year_fe", "industry_fe"] if c not in df.columns]
    paper = ORIGINAL_PANEL_B[dep]
    if missing:
        return {
            "spec": spec,
            "dep_var": dep,
            "N": 0,
            "coef": np.nan,
            "se_HC1": np.nan,
            "t_HC1": np.nan,
            "p_HC1": np.nan,
            "adj_r2": np.nan,
            "paper_coef": paper["coef"],
            "paper_t": paper["t"],
            "paper_N": paper["N"],
            "sign_match": False,
            "formula": "",
            "error": f"missing columns: {missing}",
        }
    formula = f"{dep} ~ Redundancy + {' + '.join(controls)}{FE_TERMS}"
    try:
        fit = smf.ols(formula, data=df).fit(cov_type="HC1")
        coef = float(fit.params.get("Redundancy", np.nan))
        return {
            "spec": spec,
            "dep_var": dep,
            "N": int(fit.nobs),
            "coef": coef,
            "se_HC1": float(fit.bse.get("Redundancy", np.nan)),
            "t_HC1": float(fit.tvalues.get("Redundancy", np.nan)),
            "p_HC1": float(fit.pvalues.get("Redundancy", np.nan)),
            "adj_r2": float(fit.rsquared_adj),
            "paper_coef": paper["coef"],
            "paper_t": paper["t"],
            "paper_N": paper["N"],
            "sign_match": bool(pd.notna(coef) and ((coef < 0) == (paper["coef"] < 0))),
            "formula": formula,
            "error": "",
        }
    except Exception as exc:
        return {
            "spec": spec,
            "dep_var": dep,
            "N": 0,
            "coef": np.nan,
            "se_HC1": np.nan,
            "t_HC1": np.nan,
            "p_HC1": np.nan,
            "adj_r2": np.nan,
            "paper_coef": paper["coef"],
            "paper_t": paper["t"],
            "paper_N": paper["N"],
            "sign_match": False,
            "formula": formula,
            "error": repr(exc),
        }


def build_regressions(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for spec, controls in SPEC_CONTROLS.items():
        for dep in OUTCOMES:
            rows.append(regression_result(spec, dep, controls, df))
    return pd.DataFrame(rows)


def build_descriptives(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        "Redundancy": "Redundancy",
        "FInvention": "FInvention",
        "BHAR": "BHAR",
        "FSales_Growth": "FSales_Growth",
        "Size": "Size",
        "Lev": "Lev",
        "ROA": "ROA",
        "Size_ipo_pre": "Size",
        "Lev_ipo_pre": "Lev",
        "ROA_ipo_pre": "ROA",
        "Offerfee": "Offerfee",
        "Underwriter_ipo": "Underwriter",
        "Age": "Age",
        "ScopeLen": "ScopeLen",
        "NumIndSeg": "NumIndSeg",
        "NumProdSeg": "NumProdSeg",
        "RD_Staff_ipo": "RD_Staff",
    }
    rows = []
    for col, original_key in mapping.items():
        if col not in df.columns:
            continue
        s = pd.to_numeric(df[col], errors="coerce").dropna()
        if s.empty:
            continue
        orig = ORIGINAL_PANEL_A.get(original_key, {})
        rows.append(
            {
                "variable": col,
                "paper_variable": original_key,
                "N": int(s.shape[0]),
                "mean": float(s.mean()),
                "std": float(s.std(ddof=1)),
                "p25": float(s.quantile(0.25)),
                "median": float(s.median()),
                "p75": float(s.quantile(0.75)),
                "paper_N": orig.get("N", np.nan),
                "paper_mean": orig.get("mean", np.nan),
                "paper_std": orig.get("std", np.nan),
                "paper_median": orig.get("median", np.nan),
            }
        )
    return pd.DataFrame(rows)


def build_sample_audit(df: pd.DataFrame) -> pd.DataFrame:
    rows = [{"step": "glm_table2_intersection", "N": int(df["sec_code"].nunique()), "missing": ""}]
    for spec, controls in SPEC_CONTROLS.items():
        needed = [*OUTCOMES, "Redundancy", *controls, "listing_year_fe", "industry_fe"]
        missing_cols = [c for c in needed if c not in df.columns]
        if missing_cols:
            n = 0
        else:
            n = int(df.dropna(subset=needed)["sec_code"].nunique())
        rows.append({"step": spec, "N": n, "missing": ",".join(missing_cols)})
    return pd.DataFrame(rows)


def write_doc(
    label: str,
    master_out: Path,
    regs: pd.DataFrame,
    desc: pd.DataFrame,
    sample: pd.DataFrame,
    doc_out: Path,
) -> None:
    doc_out.parent.mkdir(parents=True, exist_ok=True)
    main_regs = regs[regs["spec"].isin(["paper_exact_current_fin_fe", "paper_exact_ipo_pre_fin_fe"])].copy()
    extra_regs = regs[regs["spec"].str.startswith("rd_staff_extra")].copy()
    focus = main_regs[main_regs["spec"].eq("paper_exact_ipo_pre_fin_fe")].set_index("dep_var")

    def focus_line(dep: str) -> str:
        if dep not in focus.index:
            return f"`{dep}` not estimated"
        row = focus.loc[dep]
        return f"`{dep}` coef={fmt(row['coef'])}, t={fmt(row['t_HC1'])}, p={fmt(row['p_HC1'])}"

    desc_view = desc[
        desc["variable"].isin(
            [
                "Redundancy",
                "FInvention",
                "BHAR",
                "FSales_Growth",
                "Size",
                "Lev",
                "ROA",
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
        )
    ].copy()
    doc = [
        "# GLM Table 2 Strict Master",
        "",
        "日期：2026-07-08",
        "",
        "## 结论",
        "",
        f"- X label：`{label}`。",
        f"- 当前 GLM 与 Table2 471 候选交集：firm={int(sample.loc[sample['step'].eq('glm_table2_intersection'), 'N'].iloc[0])}。",
        "- `paper_exact_*` 主规格明确不含 `RD_Staff_ipo`；`RD_Staff_ipo` 只进入 `rd_staff_extra_*` 敏感性规格。",
        "- 主规格控制变量：`lnN_tech + Size/Lev/ROA + Offerfee + Underwriter_ipo + Age + ScopeLen + NumIndSeg + NumProdSeg + year FE + industry FE`。",
        f"- `paper_exact_ipo_pre_fin_fe` 下：{focus_line('FInvention')}；{focus_line('BHAR')}；{focus_line('FSales_Growth')}。",
        "- 当前读法：BHAR 已接近原文系数且到 10% 边界附近，FSales_Growth 仍方向错误。",
        "",
        "## Sample Audit",
        "",
        *md_table(sample, ["step", "N", "missing"], digits=0),
        "",
        "## Paper-Exact Regressions",
        "",
        *md_table(
            main_regs,
            ["spec", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2", "paper_coef", "paper_t", "sign_match"],
        ),
        "",
        "## RD Staff Extra Sensitivity",
        "",
        *md_table(
            extra_regs,
            ["spec", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2", "paper_coef", "paper_t", "sign_match"],
        ),
        "",
        "## Descriptives Vs Original",
        "",
        *md_table(
            desc_view,
            ["variable", "paper_variable", "N", "mean", "std", "median", "paper_N", "paper_mean", "paper_std", "paper_median"],
            digits=3,
        ),
        "",
        "## Outputs",
        "",
        f"- strict master：`{master_out}`",
        f"- regressions：`{RUN_DIR / f'{label}_strict_regressions_{DATE_TAG}.csv'}`",
        f"- descriptives：`{RUN_DIR / f'{label}_strict_descriptives_{DATE_TAG}.csv'}`",
        f"- sample audit：`{RUN_DIR / f'{label}_strict_sample_audit_{DATE_TAG}.csv'}`",
        "",
    ]
    doc_out.write_text("\n".join(doc), encoding="utf-8")


def main() -> None:
    args = parse_args()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    df = load_master(args.table2_master, args.firm_metrics, args.label)
    regs = build_regressions(df)
    desc = build_descriptives(df)
    sample = build_sample_audit(df)

    master_out = RUN_DIR / f"{args.label}_strict_master_{DATE_TAG}.csv"
    regs_out = RUN_DIR / f"{args.label}_strict_regressions_{DATE_TAG}.csv"
    desc_out = RUN_DIR / f"{args.label}_strict_descriptives_{DATE_TAG}.csv"
    sample_out = RUN_DIR / f"{args.label}_strict_sample_audit_{DATE_TAG}.csv"
    df.to_csv(master_out, index=False, encoding="utf-8-sig")
    regs.to_csv(regs_out, index=False, encoding="utf-8-sig")
    desc.to_csv(desc_out, index=False, encoding="utf-8-sig")
    sample.to_csv(sample_out, index=False, encoding="utf-8-sig")
    write_doc(args.label, master_out, regs, desc, sample, args.doc_out)
    print(
        json.dumps(
            {
                "doc": str(args.doc_out),
                "master": str(master_out),
                "regressions": str(regs_out),
                "firm_n": int(df["sec_code"].nunique()),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
