#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf


PROJECT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
BASE_SCRIPT = PROJECT / "scripts/run_table2_len132_tight_audit_20260705.py"
MASTER_IN = (
    PROJECT
    / "results/table2_listing_year_segment_controls_20260706/"
    "table2_listing_year_segment_controls_master_20260706.csv"
)
OUTCOME_UNIVERSE = (
    PROJECT
    / "results/outcome_variable_probe_20260629/"
    "outcome_variables_star_firm_level_20260629.csv"
)
INCOME_ANNUAL = Path(
    "/Users/mac/computerscience/23实证选题探索/T16/risk_disclosure_trial/data/"
    "financial_csmar_20260508/income_statement_annual_A_2015_2025.csv"
)

RUN_DIR = PROJECT / "results/fsales_growth_window_sensitivity_20260706"
DOC_OUT = PROJECT / "docs/00_current/fsales_growth_window_sensitivity_20260706.md"

VARIANT_OUT = RUN_DIR / "fsales_growth_window_variants_20260706.csv"
DESC_OUT = RUN_DIR / "fsales_growth_window_descriptives_20260706.csv"
REG_OUT = RUN_DIR / "fsales_growth_window_regressions_20260706.csv"
RANK_OUT = RUN_DIR / "fsales_growth_window_ranked_candidates_20260706.csv"


def load_base_module():
    spec = importlib.util.spec_from_file_location("table2_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {BASE_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_base_module()

ORIGINAL = base.ORIGINAL_PANEL_A["FSales_Growth"]
ORIGINAL_REG = base.ORIGINAL_PANEL_B["FSales_Growth"]
CURRENT_CONTROL_VARS = base.CURRENT_CONTROL_VARS
FE_VARS = base.FE_VARS

REVENUE_SOURCES = {
    "combo": "operating_revenue first, total_operating_revenue fallback",
    "operating": "operating_revenue only",
    "total": "total_operating_revenue only",
}

WINDOWS = [
    ("L_to_L1_total", "listing_year -> listing_year+1, current logic", 0, 1, "total"),
    ("L1_to_L2_total", "first complete listed fiscal year -> next fiscal year", 1, 2, "total"),
    ("Lm1_to_L1_total", "listing_year-1 -> listing_year+1, two-year total growth", -1, 1, "total"),
    ("Lm1_to_L1_cagr", "listing_year-1 -> listing_year+1, annualized CAGR", -1, 1, "cagr"),
    ("L_to_L2_total", "listing_year -> listing_year+2, two-year total growth", 0, 2, "total"),
    ("L_to_L2_cagr", "listing_year -> listing_year+2, annualized CAGR", 0, 2, "cagr"),
    ("Lm1_to_L_total", "listing_year-1 -> listing_year, IPO-year growth", -1, 0, "total"),
    ("Lm2_to_L_total", "listing_year-2 -> listing_year, pre-IPO two-year total growth", -2, 0, "total"),
    ("Lm2_to_L_cagr", "listing_year-2 -> listing_year, pre-IPO annualized CAGR", -2, 0, "cagr"),
    ("Lm1_to_L2_total", "listing_year-1 -> listing_year+2, three-year total growth", -1, 2, "total"),
    ("Lm1_to_L2_cagr", "listing_year-1 -> listing_year+2, annualized CAGR", -1, 2, "cagr"),
]


def z6(value: object) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text.zfill(6) if text.isdigit() else text


def winsorize(series: pd.Series, lower: float = 0.01, upper: float = 0.99) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    nonmissing = s.dropna()
    if nonmissing.empty:
        return s
    return s.clip(nonmissing.quantile(lower), nonmissing.quantile(upper))


def winsorize_like(series: pd.Series, reference: pd.Series, lower: float = 0.01, upper: float = 0.99) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    ref = pd.to_numeric(reference, errors="coerce").dropna()
    if ref.empty:
        return s
    return s.clip(ref.quantile(lower), ref.quantile(upper))


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


def load_master() -> pd.DataFrame:
    df = pd.read_csv(MASTER_IN, dtype={"sec_code": str, "code": str}, encoding="utf-8-sig")
    df["sec_code"] = df["sec_code"].map(z6)
    df["code"] = df["code"].map(z6)
    for col in [
        "listing_year",
        "Redundancy",
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
        "RD_Staff",
        "FInvention",
        "BHAR",
        "FSales_Growth",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["listing_year_fe"] = pd.to_numeric(df["listing_year_fe"], errors="coerce").astype("Int64").astype(str)
    df["listing_year_fe"] = df["listing_year_fe"].replace({"<NA>": np.nan, "nan": np.nan})
    df["industry_fe"] = df["industry_fe"].astype(str).replace({"nan": np.nan, "<NA>": np.nan})
    return df


def load_income() -> pd.DataFrame:
    cols = ["Stkcd", "ShortName", "Accper", "year", "Typrep", "operating_revenue", "total_operating_revenue"]
    inc = pd.read_csv(INCOME_ANNUAL, usecols=cols, dtype={"Stkcd": str, "Typrep": str})
    inc["code"] = inc["Stkcd"].map(z6)
    inc["Accper"] = pd.to_datetime(inc["Accper"], errors="coerce")
    inc["year"] = pd.to_numeric(inc["year"], errors="coerce").astype("Int64")
    inc = inc[inc["Typrep"].astype(str).eq("A")].copy()
    inc["operating"] = pd.to_numeric(inc["operating_revenue"], errors="coerce")
    inc["total"] = pd.to_numeric(inc["total_operating_revenue"], errors="coerce")
    inc["combo"] = inc["operating"].combine_first(inc["total"])
    inc = inc.sort_values(["code", "year", "Accper"]).drop_duplicates(["code", "year"], keep="last")
    return inc[["code", "year", "ShortName", "operating", "total", "combo"]].copy()


def load_winsor_universe() -> pd.DataFrame:
    cols = ["code", "listing_year"]
    universe = pd.read_csv(OUTCOME_UNIVERSE, usecols=cols, dtype={"code": str}, encoding="utf-8-sig")
    universe["code"] = universe["code"].map(z6)
    universe["listing_year"] = pd.to_numeric(universe["listing_year"], errors="coerce")
    return universe.drop_duplicates("code").copy()


def revenue_lookup(inc: pd.DataFrame, source: str) -> pd.DataFrame:
    wide = inc.pivot(index="code", columns="year", values=source)
    wide.columns = [int(c) for c in wide.columns]
    return wide


def window_growth(
    wide: pd.DataFrame, codes: pd.Series, listing_years: pd.Series, start_offset: int, end_offset: int, kind: str
) -> tuple[pd.Series, pd.Series, pd.Series]:
    starts = []
    ends = []
    values = []
    period = end_offset - start_offset
    for code, listing_year in zip(codes, listing_years):
        if pd.isna(code) or pd.isna(listing_year):
            starts.append(np.nan)
            ends.append(np.nan)
            values.append(np.nan)
            continue
        start_year = int(listing_year) + start_offset
        end_year = int(listing_year) + end_offset
        start_value = wide.at[code, start_year] if code in wide.index and start_year in wide.columns else np.nan
        end_value = wide.at[code, end_year] if code in wide.index and end_year in wide.columns else np.nan
        starts.append(start_value)
        ends.append(end_value)
        if pd.isna(start_value) or pd.isna(end_value) or start_value == 0:
            values.append(np.nan)
        elif kind == "cagr":
            if start_value > 0 and end_value > 0 and period > 0:
                values.append((end_value / start_value) ** (1.0 / period) - 1.0)
            else:
                values.append(np.nan)
        else:
            values.append((end_value - start_value) / start_value)
    return pd.Series(values, index=codes.index), pd.Series(starts, index=codes.index), pd.Series(ends, index=codes.index)


def build_variants(master: pd.DataFrame, inc: pd.DataFrame, winsor_universe: pd.DataFrame) -> pd.DataFrame:
    out = master.copy()
    for source in REVENUE_SOURCES:
        wide = revenue_lookup(inc, source)
        for window_id, label, start_offset, end_offset, kind in WINDOWS:
            raw_col = f"FSales_{source}_{window_id}_raw"
            win_col = f"FSales_{source}_{window_id}_w1p"
            start_col = f"{raw_col}_start_revenue"
            end_col = f"{raw_col}_end_revenue"
            growth, start_revenue, end_revenue = window_growth(
                wide,
                out["code"],
                out["listing_year"],
                start_offset,
                end_offset,
                kind,
            )
            reference_growth, _, _ = window_growth(
                wide,
                winsor_universe["code"],
                winsor_universe["listing_year"],
                start_offset,
                end_offset,
                kind,
            )
            out[raw_col] = growth
            out[win_col] = winsorize_like(growth, reference_growth)
            out[start_col] = start_revenue
            out[end_col] = end_revenue
    return out


def build_descriptives(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    samples = {
        "full_2019_2023": df.index == df.index,
        "w2_2019_2022": pd.to_numeric(df["listing_year"], errors="coerce").between(2019, 2022),
    }
    for source, source_label in REVENUE_SOURCES.items():
        for window_id, window_label, start_offset, end_offset, kind in WINDOWS:
            raw_col = f"FSales_{source}_{window_id}_raw"
            win_col = f"FSales_{source}_{window_id}_w1p"
            for sample_name, mask in samples.items():
                for treatment, col in [("raw", raw_col), ("winsor_1_99", win_col)]:
                    rec = {
                        "sample": sample_name,
                        "source": source,
                        "source_label": source_label,
                        "window": window_id,
                        "window_label": window_label,
                        "start_offset": start_offset,
                        "end_offset": end_offset,
                        "growth_kind": kind,
                        "treatment": treatment,
                        "variable": col,
                        **stats(df.loc[mask, col]),
                    }
                    rec["original_N"] = ORIGINAL["N"]
                    rec["original_mean"] = ORIGINAL["mean"]
                    rec["original_std"] = ORIGINAL["std"]
                    rec["original_p25"] = ORIGINAL["p25"]
                    rec["original_median"] = ORIGINAL["median"]
                    rec["original_p75"] = ORIGINAL["p75"]
                    rec["mean_gap"] = rec["mean"] - ORIGINAL["mean"]
                    rec["std_gap"] = rec["std"] - ORIGINAL["std"]
                    rec["p25_gap"] = rec["p25"] - ORIGINAL["p25"]
                    rec["median_gap"] = rec["median"] - ORIGINAL["median"]
                    rec["p75_gap"] = rec["p75"] - ORIGINAL["p75"]
                    rec["N_gap"] = rec["N"] - ORIGINAL["N"]
                    rec["desc_distance"] = (
                        abs(rec["mean_gap"])
                        + abs(rec["median_gap"])
                        + abs(rec["p75_gap"])
                        + 0.5 * abs(rec["p25_gap"])
                        + 0.25 * abs(rec["std_gap"])
                        + 0.002 * abs(rec["N_gap"])
                    )
                    rows.append(rec)
    return pd.DataFrame(rows)


def regression_result(sample: str, model: str, dep: str, formula: str, df: pd.DataFrame) -> dict:
    try:
        res = smf.ols(formula, data=df).fit(cov_type="HC1")
    except Exception as exc:
        return {
            "sample": sample,
            "model": model,
            "dep_var": dep,
            "target_var": "Redundancy",
            "N": 0,
            "coef": np.nan,
            "se_HC1": np.nan,
            "t_HC1": np.nan,
            "p_HC1": np.nan,
            "adj_r2": np.nan,
            "formula": formula,
            "error": repr(exc),
        }
    return {
        "sample": sample,
        "model": model,
        "dep_var": dep,
        "target_var": "Redundancy",
        "N": int(res.nobs),
        "coef": float(res.params.get("Redundancy", np.nan)),
        "se_HC1": float(res.bse.get("Redundancy", np.nan)),
        "t_HC1": float(res.tvalues.get("Redundancy", np.nan)),
        "p_HC1": float(res.pvalues.get("Redundancy", np.nan)),
        "adj_r2": float(res.rsquared_adj),
        "formula": formula,
        "error": "",
    }


def build_regressions(df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    controls = " + ".join(CURRENT_CONTROL_VARS)
    segment_controls = " + ".join([*CURRENT_CONTROL_VARS, "ScopeLen", "NumIndSeg", "NumProdSeg"])
    rd_controls = f"{segment_controls} + RD_Staff"
    fe = " + C(listing_year_fe) + C(industry_fe)"
    samples = {
        "full_2019_2023": df,
        "w2_2019_2022": df[pd.to_numeric(df["listing_year"], errors="coerce").between(2019, 2022)].copy(),
    }
    for source in REVENUE_SOURCES:
        for window_id, window_label, start_offset, end_offset, kind in WINDOWS:
            dep = f"FSales_{source}_{window_id}_w1p"
            for sample_name, sub in samples.items():
                models = [
                    ("simple", f"{dep} ~ Redundancy"),
                    ("fe_text", f"{dep} ~ Redundancy + lnN_tech{fe}"),
                    ("controls_fe_current", f"{dep} ~ Redundancy + {controls}{fe}"),
                    ("controls_fe_listing_year_segments", f"{dep} ~ Redundancy + {segment_controls}{fe}"),
                    ("controls_fe_listing_year_segments_rd_staff", f"{dep} ~ Redundancy + {rd_controls}{fe}"),
                ]
                for model_name, formula in models:
                    rec = regression_result(sample_name, model_name, dep, formula, sub)
                    rec.update(
                        {
                            "source": source,
                            "window": window_id,
                            "window_label": window_label,
                            "start_offset": start_offset,
                            "end_offset": end_offset,
                            "growth_kind": kind,
                            "treatment": "winsor_1_99",
                            "paper_coef": ORIGINAL_REG["coef"],
                            "paper_t": ORIGINAL_REG["t"],
                            "paper_N": ORIGINAL_REG["N"],
                        }
                    )
                    rows.append(rec)
    return pd.DataFrame(rows)


def build_ranked_candidates(desc: pd.DataFrame, regs: pd.DataFrame) -> pd.DataFrame:
    d = desc[(desc["sample"].eq("w2_2019_2022")) & (desc["treatment"].eq("winsor_1_99"))].copy()
    r = regs[
        regs["sample"].eq("w2_2019_2022")
        & regs["model"].eq("controls_fe_listing_year_segments")
    ].copy()
    keep_reg = r[
        [
            "source",
            "window",
            "N",
            "coef",
            "t_HC1",
            "p_HC1",
            "adj_r2",
        ]
    ].rename(
        columns={
            "N": "reg_N",
            "coef": "reg_coef",
            "t_HC1": "reg_t_HC1",
            "p_HC1": "reg_p_HC1",
            "adj_r2": "reg_adj_r2",
        }
    )
    out = d.merge(keep_reg, on=["source", "window"], how="left")
    out["coef_gap_vs_paper"] = out["reg_coef"] - ORIGINAL_REG["coef"]
    out["wrong_sign"] = out["reg_coef"].ge(0).astype(int)
    out["combined_rank_score"] = out["desc_distance"] + 2.0 * out["wrong_sign"] + 5.0 * out["reg_p_HC1"].fillna(1)
    return out.sort_values(["wrong_sign", "desc_distance", "reg_p_HC1"], ascending=[True, True, True])


def build_doc(desc: pd.DataFrame, regs: pd.DataFrame, ranked: pd.DataFrame) -> None:
    current = desc[
        desc["sample"].eq("w2_2019_2022")
        & desc["source"].eq("combo")
        & desc["window"].eq("L_to_L1_total")
        & desc["treatment"].eq("winsor_1_99")
    ].copy()
    desc_top = ranked.head(12).copy()
    reg_main = regs[
        regs["sample"].eq("w2_2019_2022")
        & regs["source"].eq("combo")
        & regs["model"].isin(["simple", "fe_text", "controls_fe_current", "controls_fe_listing_year_segments"])
        & regs["window"].isin(["L_to_L1_total", "L1_to_L2_total", "Lm1_to_L1_total", "Lm1_to_L1_cagr", "L_to_L2_total", "L_to_L2_cagr"])
    ].copy()
    reg_main = reg_main.sort_values(["window", "model"])

    lines: list[str] = [
        "# FSales_Growth window sensitivity 20260706",
        "",
        "## Purpose",
        "",
        "This run only changes the sales-growth outcome definition. The X measurement, controls, fixed effects, and HC1 standard errors are kept aligned with the latest Table 2 audit.",
        "",
        "Original paper benchmark for `FSales_Growth`: N=471, mean=0.530, std=1.522, p25=-0.008, median=0.180, p75=0.523; Table 2 coefficient=-0.0373, t=-2.02.",
        "",
        "## Current Definition Check",
        "",
    ]
    lines.extend(
        md_table(
            current,
            ["sample", "source", "window", "N", "mean", "std", "p25", "median", "p75", "mean_gap", "median_gap"],
        )
    )
    lines.extend(
        [
            "",
            "## Best Descriptive Matches",
            "",
            "Ranked on the 2019-2022 sample, winsorized at 1/99, against the original paper's `FSales_Growth` descriptive distribution.",
            "",
        ]
    )
    lines.extend(
        md_table(
            desc_top,
            [
                "source",
                "window",
                "N",
                "mean",
                "std",
                "p25",
                "median",
                "p75",
                "desc_distance",
                "reg_coef",
                "reg_t_HC1",
                "reg_p_HC1",
            ],
        )
    )
    lines.extend(
        [
            "",
            "## Main Regression Sensitivity",
            "",
            "Combo revenue means `operating_revenue` first, then `total_operating_revenue` fallback. Sample is 2019-2022 to match the paper's 471 outcome observations as closely as possible.",
            "",
        ]
    )
    lines.extend(
        md_table(
            reg_main,
            ["window", "model", "N", "coef", "t_HC1", "p_HC1", "adj_r2"],
        )
    )
    lines.extend(
        [
            "",
            "## Reading",
            "",
            "- If a window matches the descriptive distribution but keeps a positive or insignificant `Redundancy` coefficient, the issue is not just the sales-growth window.",
            "- `L1_to_L2_total` is the strictest interpretation of a complete post-listing fiscal-year growth outcome.",
            "- `Lm1_to_L1_total` and `Lm1_to_L1_cagr` test whether the paper may be using pre-IPO-to-post-IPO growth around listing.",
            "- This run does not change winsorization except the standard 1/99 treatment used in the existing outcome construction.",
            "",
            "## Outputs",
            "",
            f"- variants: `{VARIANT_OUT}`",
            f"- descriptives: `{DESC_OUT}`",
            f"- regressions: `{REG_OUT}`",
            f"- ranked candidates: `{RANK_OUT}`",
            "",
        ]
    )
    DOC_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    master = load_master()
    inc = load_income()
    winsor_universe = load_winsor_universe()
    variants = build_variants(master, inc, winsor_universe)
    desc = build_descriptives(variants)
    regs = build_regressions(variants)
    ranked = build_ranked_candidates(desc, regs)

    variant_cols = [
        "sec_code",
        "sec_name",
        "code",
        "listing_year",
        "Redundancy",
        "lnN_tech",
        "FInvention",
        "BHAR",
        "FSales_Growth",
    ]
    variant_cols.extend([c for c in variants.columns if c.startswith("FSales_")])
    variants[variant_cols].to_csv(VARIANT_OUT, index=False, encoding="utf-8-sig")
    desc.to_csv(DESC_OUT, index=False, encoding="utf-8-sig")
    regs.to_csv(REG_OUT, index=False, encoding="utf-8-sig")
    ranked.to_csv(RANK_OUT, index=False, encoding="utf-8-sig")
    build_doc(desc, regs, ranked)

    top = ranked.head(8)[
        ["source", "window", "N", "mean", "median", "p75", "desc_distance", "reg_coef", "reg_t_HC1", "reg_p_HC1"]
    ]
    print("Top ranked candidates:")
    print(top.to_string(index=False))
    print(f"doc={DOC_OUT}")
    print(f"desc={DESC_OUT}")
    print(f"reg={REG_OUT}")


if __name__ == "__main__":
    main()
