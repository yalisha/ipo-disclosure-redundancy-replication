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
DEFAULT_MASTER = (
    ROOT
    / "results/glm_table2_strict_master_20260708/"
    "glm300_proxy_tailmerge1600_floor50_strict_master_20260708.csv"
)
RUN_DIR = ROOT / f"results/table2_bhar_fsales_waterfall_{DATE_TAG}"
DOC_OUT = ROOT / f"docs/00_current/table2_bhar_fsales_waterfall_{DATE_TAG}.md"

ORIGINAL_PANEL_B = {
    "BHAR": {"coef": -0.0188, "t": -2.14, "N": 471},
    "FSales_Growth": {"coef": -0.0373, "t": -2.02, "N": 471},
}
Y_VARIANTS = {
    "BHAR": {"winsor": "BHAR", "raw": "excl_first_BHAR_ew"},
    "FSales_Growth": {"winsor": "FSales_Growth", "raw": "FSales_Growth_raw"},
}
WATERFALL_STEPS = [
    ("01_x_only", ["Redundancy"], False),
    ("02_plus_lnn", ["Redundancy", "lnN_tech"], False),
    ("03_plus_year_industry_fe", ["Redundancy", "lnN_tech"], True),
    ("04_plus_fin_controls", ["Redundancy", "lnN_tech", "Size_ipo_pre", "Lev_ipo_pre", "ROA_ipo_pre"], True),
    (
        "05_plus_issue_underwriter_age",
        [
            "Redundancy",
            "lnN_tech",
            "Size_ipo_pre",
            "Lev_ipo_pre",
            "ROA_ipo_pre",
            "Offerfee",
            "Underwriter_ipo",
            "Age",
        ],
        True,
    ),
    (
        "06_plus_scope_segments_paper_exact",
        [
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
        ],
        True,
    ),
    (
        "07_plus_rd_staff_extra_not_main",
        [
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
        ],
        True,
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--master", type=Path, default=DEFAULT_MASTER)
    parser.add_argument("--prefix", default="table2_bhar_fsales")
    parser.add_argument("--doc-out", type=Path, default=DOC_OUT)
    return parser.parse_args()


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


def load_master(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, dtype={"code": str, "sec_code": str}, encoding="utf-8-sig", low_memory=False)
    df["listing_year_fe"] = df["listing_year_fe"].astype(str).replace({"nan": np.nan, "<NA>": np.nan})
    df["industry_fe"] = df["industry_fe"].astype(str).replace({"nan": np.nan, "<NA>": np.nan})
    numeric = {
        "Redundancy",
        "lnN_tech",
        "BHAR",
        "excl_first_BHAR_ew",
        "FSales_Growth",
        "FSales_Growth_raw",
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
    }
    for col in sorted(numeric & set(df.columns)):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def regression_row(outcome: str, y_variant: str, dep_col: str, step_order: int, step: str, rhs_vars: list[str], fe: bool, df: pd.DataFrame) -> dict[str, object]:
    paper = ORIGINAL_PANEL_B[outcome]
    needed = [dep_col, *rhs_vars]
    if fe:
        needed += ["listing_year_fe", "industry_fe"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        return {
            "outcome": outcome,
            "y_variant": y_variant,
            "dep_col": dep_col,
            "step_order": step_order,
            "step": step,
            "N": 0,
            "coef": np.nan,
            "se_HC1": np.nan,
            "t_HC1": np.nan,
            "p_HC1": np.nan,
            "adj_r2": np.nan,
            "paper_coef": paper["coef"],
            "paper_t": paper["t"],
            "paper_N": paper["N"],
            "formula": "",
            "error": f"missing columns: {missing}",
        }
    rhs = " + ".join(rhs_vars)
    if fe:
        rhs += " + C(listing_year_fe) + C(industry_fe)"
    formula = f"{dep_col} ~ {rhs}"
    try:
        fit = smf.ols(formula, data=df).fit(cov_type="HC1")
        coef = float(fit.params.get("Redundancy", np.nan))
        return {
            "outcome": outcome,
            "y_variant": y_variant,
            "dep_col": dep_col,
            "step_order": step_order,
            "step": step,
            "N": int(fit.nobs),
            "coef": coef,
            "se_HC1": float(fit.bse.get("Redundancy", np.nan)),
            "t_HC1": float(fit.tvalues.get("Redundancy", np.nan)),
            "p_HC1": float(fit.pvalues.get("Redundancy", np.nan)),
            "adj_r2": float(fit.rsquared_adj),
            "paper_coef": paper["coef"],
            "paper_t": paper["t"],
            "paper_N": paper["N"],
            "formula": formula,
            "error": "",
        }
    except Exception as exc:
        return {
            "outcome": outcome,
            "y_variant": y_variant,
            "dep_col": dep_col,
            "step_order": step_order,
            "step": step,
            "N": 0,
            "coef": np.nan,
            "se_HC1": np.nan,
            "t_HC1": np.nan,
            "p_HC1": np.nan,
            "adj_r2": np.nan,
            "paper_coef": paper["coef"],
            "paper_t": paper["t"],
            "paper_N": paper["N"],
            "formula": formula,
            "error": repr(exc),
        }


def build_waterfall(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for outcome, variants in Y_VARIANTS.items():
        for y_variant, dep_col in variants.items():
            for i, (step, rhs_vars, fe) in enumerate(WATERFALL_STEPS, start=1):
                rows.append(regression_row(outcome, y_variant, dep_col, i, step, rhs_vars, fe, df))
    return pd.DataFrame(rows)


def build_delta_table(waterfall: pd.DataFrame) -> pd.DataFrame:
    final = waterfall[waterfall["step"].eq("06_plus_scope_segments_paper_exact")].copy()
    wide = final.pivot_table(index="outcome", columns="y_variant", values=["coef", "t_HC1", "p_HC1", "N"], aggfunc="first")
    rows = []
    for outcome in sorted(set(final["outcome"])):
        row = {"outcome": outcome}
        for metric in ["N", "coef", "t_HC1", "p_HC1"]:
            for variant in ["raw", "winsor"]:
                try:
                    row[f"{variant}_{metric}"] = wide.loc[outcome, (metric, variant)]
                except Exception:
                    row[f"{variant}_{metric}"] = np.nan
        row["coef_delta_winsor_minus_raw"] = row.get("winsor_coef", np.nan) - row.get("raw_coef", np.nan)
        rows.append(row)
    return pd.DataFrame(rows)


def write_doc(
    master: Path,
    waterfall: pd.DataFrame,
    delta: pd.DataFrame,
    doc_out: Path,
    prefix: str,
) -> None:
    doc_out.parent.mkdir(parents=True, exist_ok=True)
    main = waterfall[waterfall["y_variant"].eq("winsor") & waterfall["step"].ne("07_plus_rd_staff_extra_not_main")].copy()
    extra = waterfall[waterfall["step"].eq("07_plus_rd_staff_extra_not_main")].copy()
    final = main[main["step"].eq("06_plus_scope_segments_paper_exact")].set_index("outcome")

    def final_line(outcome: str) -> str:
        if outcome not in final.index:
            return f"`{outcome}` not estimated"
        row = final.loc[outcome]
        return f"`{outcome}` paper-exact coef={fmt(row['coef'])}, t={fmt(row['t_HC1'])}, p={fmt(row['p_HC1'])}"

    doc = [
        "# BHAR / FSales_Growth Table 2 Waterfall",
        "",
        "日期：2026-07-08",
        "",
        "## 结论",
        "",
        f"- 输入 master：`{master}`。",
        "- 主瀑布使用 winsorized Y：`BHAR` 与 `FSales_Growth`；同时保留 raw Y 对照来观察缩尾影响。",
        "- `06_plus_scope_segments_paper_exact` 是 strict paper-exact 主规格；`07_plus_rd_staff_extra_not_main` 只是 RD staff 敏感性，不作为主规格。",
        f"- 当前主规格结果：{final_line('BHAR')}；{final_line('FSales_Growth')}。",
        "- 断点读法：BHAR 从单变量到 full controls 一直为负，加入 ScopeLen/segment controls 后更接近原文；FSales_Growth 从单变量起就是正，缩尾只压低极端值但没有修正方向。",
        "",
        "## Winsorized-Y Waterfall",
        "",
        *md_table(
            main,
            ["outcome", "y_variant", "step_order", "step", "N", "coef", "t_HC1", "p_HC1", "adj_r2", "paper_coef", "paper_t"],
        ),
        "",
        "## Raw vs Winsor At Paper-Exact Step",
        "",
        *md_table(
            delta,
            [
                "outcome",
                "raw_N",
                "raw_coef",
                "raw_t_HC1",
                "raw_p_HC1",
                "winsor_N",
                "winsor_coef",
                "winsor_t_HC1",
                "winsor_p_HC1",
                "coef_delta_winsor_minus_raw",
            ],
        ),
        "",
        "## RD Staff Extra Sensitivity",
        "",
        *md_table(
            extra,
            ["outcome", "y_variant", "N", "coef", "t_HC1", "p_HC1", "adj_r2", "paper_coef", "paper_t"],
        ),
        "",
        "## Outputs",
        "",
        f"- waterfall：`{RUN_DIR / f'{prefix}_waterfall_{DATE_TAG}.csv'}`",
        f"- delta：`{RUN_DIR / f'{prefix}_raw_vs_winsor_{DATE_TAG}.csv'}`",
        "",
    ]
    doc_out.write_text("\n".join(doc), encoding="utf-8")


def main() -> None:
    args = parse_args()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    df = load_master(args.master)
    waterfall = build_waterfall(df)
    delta = build_delta_table(waterfall)
    waterfall_out = RUN_DIR / f"{args.prefix}_waterfall_{DATE_TAG}.csv"
    delta_out = RUN_DIR / f"{args.prefix}_raw_vs_winsor_{DATE_TAG}.csv"
    waterfall.to_csv(waterfall_out, index=False, encoding="utf-8-sig")
    delta.to_csv(delta_out, index=False, encoding="utf-8-sig")
    write_doc(args.master, waterfall, delta, args.doc_out, args.prefix)
    print(json.dumps({"doc": str(args.doc_out), "waterfall": str(waterfall_out), "delta": str(delta_out)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
