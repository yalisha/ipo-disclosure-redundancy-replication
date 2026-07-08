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
RUN_DIR = PROJECT / "results/cutoff552_table2_471_probe_20260707"
DOC_OUT = PROJECT / "docs/00_current/cutoff552_table2_471_probe_20260707.md"

FIRM_IN = PROJECT / "results/glm4_dewrap_join_candidate566_20260707/firm_metrics_candidate566_20260707.csv"
CHUNK_IN = PROJECT / "results/glm4_dewrap_join_candidate566_20260707/chunk_metrics_candidate566_20260707.csv"
CROSSWALK_IN = PROJECT / "results/glm4_dewrap_join_candidate566_20260707/candidate566_vs_csmar_universe_crosswalk_20260707.csv"
MASTER_IN = PROJECT / "results/table2_candidate566_ipo_pre_controls_20260707/table2_candidate566_ipo_pre_controls_master_20260707.csv"

SAMPLE552_FIRM_OUT = RUN_DIR / "sample552_firm_metrics_cutoff_20260707.csv"
SAMPLE552_CHUNK_OUT = RUN_DIR / "sample552_chunk_metrics_cutoff_20260707.csv"
LATE14_OUT = RUN_DIR / "sample552_late14_excluded_20260707.csv"
TABLE1_DESC_OUT = RUN_DIR / "sample552_table1_descriptives_vs_original_20260707.csv"
PANEL_TESTS_OUT = RUN_DIR / "sample552_panel_tests_20260707.csv"
TABLE2_MASTER471_OUT = RUN_DIR / "table2_471_candidate_master_20260707.csv"
TABLE2_REG_OUT = RUN_DIR / "table2_471_candidate_regressions_20260707.csv"
BHAR_VARIANTS_OUT = RUN_DIR / "table2_471_bhar_variants_20260707.csv"
DROP3_OUT = RUN_DIR / "table2_late2022_drop3_20260707.csv"

LIST_DATE_CUTOFF = pd.Timestamp("2023-08-15")
DROP_LATE_2022 = {"688475", "688496", "688525"}
OUTCOMES = ["FInvention", "BHAR", "FSales_Growth"]
MAIN_CONTROLS = [
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
    "listing_year_fe",
    "industry_fe",
]
RHS = (
    "Redundancy + lnN_tech + Size_ipo_pre + Lev_ipo_pre + ROA_ipo_pre + "
    "Offerfee + Underwriter_ipo + Age + ScopeLen + NumIndSeg + NumProdSeg + "
    "RD_Staff_ipo + C(listing_year_fe) + C(industry_fe)"
)
BHAR_CANDIDATES = [
    "BHAR",
    "excl_first_BHAR_ew",
    "excl_first_BHAR_vw",
    "incl_first_BHAR_ew",
    "incl_first_BHAR_vw",
    "excl_first_BHAR_ew_w1p",
    "excl_first_BHAR_vw_w1p",
    "incl_first_BHAR_ew_w1p",
    "incl_first_BHAR_vw_w1p",
]


def import_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


candidate = import_module("candidate566", PROJECT / "scripts/build_candidate566_x_universe_20260707.py")
table2 = import_module("table2_candidate566", PROJECT / "scripts/run_table2_candidate566_ipo_pre_controls_20260707.py")


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


def md_table(df: pd.DataFrame, cols: list[str], digits: int = 3) -> list[str]:
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df.iterrows():
        vals: list[str] = []
        for col in cols:
            val = row.get(col, "")
            if isinstance(val, (float, np.floating)):
                vals.append("" if pd.isna(val) else f"{float(val):.{digits}f}")
            elif isinstance(val, (int, np.integer)):
                vals.append(str(int(val)))
            elif pd.isna(val):
                vals.append("")
            else:
                vals.append(str(val))
        out.append("| " + " | ".join(vals) + " |")
    return out


def regression_row(sample: str, dep: str, df: pd.DataFrame) -> dict[str, object]:
    try:
        fit = smf.ols(f"{dep} ~ {RHS}", data=df).fit(cov_type="HC1")
        paper = table2.ORIGINAL_PANEL_B[dep]
        return {
            "sample": sample,
            "dep_var": dep,
            "N": int(fit.nobs),
            "coef": float(fit.params.get("Redundancy", np.nan)),
            "se_HC1": float(fit.bse.get("Redundancy", np.nan)),
            "t_HC1": float(fit.tvalues.get("Redundancy", np.nan)),
            "p_HC1": float(fit.pvalues.get("Redundancy", np.nan)),
            "adj_r2": float(fit.rsquared_adj),
            "paper_coef": paper["coef"],
            "paper_t": paper["t"],
            "paper_N": paper["N"],
            "sign_match": bool(pd.notna(fit.params.get("Redundancy", np.nan)) and ((fit.params["Redundancy"] < 0) == (paper["coef"] < 0))),
            "formula": f"{dep} ~ {RHS}",
            "error": "",
        }
    except Exception as exc:
        return {
            "sample": sample,
            "dep_var": dep,
            "N": 0,
            "coef": np.nan,
            "se_HC1": np.nan,
            "t_HC1": np.nan,
            "p_HC1": np.nan,
            "adj_r2": np.nan,
            "paper_coef": table2.ORIGINAL_PANEL_B[dep]["coef"],
            "paper_t": table2.ORIGINAL_PANEL_B[dep]["t"],
            "paper_N": table2.ORIGINAL_PANEL_B[dep]["N"],
            "sign_match": False,
            "formula": f"{dep} ~ {RHS}",
            "error": repr(exc),
        }


def build_sample552() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    firm = pd.read_csv(FIRM_IN, dtype={"sec_code": str}, encoding="utf-8-sig")
    chunk = pd.read_csv(CHUNK_IN, dtype={"sec_code": str}, encoding="utf-8-sig")
    cross = pd.read_csv(CROSSWALK_IN, dtype={"code": str}, encoding="utf-8-sig")
    firm["sec_code"] = z6(firm["sec_code"])
    chunk["sec_code"] = z6(chunk["sec_code"])
    cross["code"] = z6(cross["code"])
    cross["list_date_csmar"] = pd.to_datetime(cross["list_date_csmar"], errors="coerce")
    cross["prospectus_publish_date_csmar"] = pd.to_datetime(cross["prospectus_publish_date_csmar"], errors="coerce")

    late14 = cross[
        cross["candidate_status"].eq("in_candidate_x")
        & cross["list_date_csmar"].ge(LIST_DATE_CUTOFF)
    ].sort_values(["list_date_csmar", "code"]).copy()
    late_codes = set(late14["code"])
    sample_firm = firm[~firm["sec_code"].isin(late_codes)].copy()
    sample_chunk = chunk[~chunk["sec_code"].isin(late_codes)].copy()

    desc = candidate.build_desc(sample_firm, sample_chunk)
    panel = candidate.build_panel_tests(sample_chunk)
    return sample_firm, sample_chunk, late14, desc, panel


def build_table2_471() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    master = pd.read_csv(MASTER_IN, dtype={"code": str}, encoding="utf-8-sig", low_memory=False)
    master["code"] = z6(master["code"])
    master["listing_year"] = pd.to_numeric(master["listing_year"], errors="coerce")
    base474 = master[master["listing_year"].between(2019, 2022)].dropna(subset=OUTCOMES + MAIN_CONTROLS).copy()
    drop3 = base474[base474["code"].isin(DROP_LATE_2022)].copy().sort_values("first_trade_date")
    sample471 = base474[~base474["code"].isin(DROP_LATE_2022)].copy()

    reg_rows = []
    for sample_name, df in [("common474_before_drop3", base474), ("common471_after_drop3", sample471)]:
        for dep in OUTCOMES:
            reg_rows.append(regression_row(sample_name, dep, df))
    regs = pd.DataFrame(reg_rows)

    bhar_rows = []
    for col in BHAR_CANDIDATES:
        if col not in sample471.columns:
            continue
        sub = sample471.dropna(subset=[col]).copy()
        if sub.empty:
            continue
        try:
            fit = smf.ols(f"{col} ~ {RHS}", data=sub).fit(cov_type="HC1")
            coef = float(fit.params.get("Redundancy", np.nan))
            t_val = float(fit.tvalues.get("Redundancy", np.nan))
            p_val = float(fit.pvalues.get("Redundancy", np.nan))
        except Exception:
            coef = math.nan
            t_val = math.nan
            p_val = math.nan
        s = stats(sub[col])
        bhar_rows.append(
            {
                "bhar_candidate": col,
                "N": int(sub.shape[0]),
                "mean": s["mean"],
                "median": s["median"],
                "p25": s["p25"],
                "p75": s["p75"],
                "coef": coef,
                "t_HC1": t_val,
                "p_HC1": p_val,
                "paper_mean": table2.ORIGINAL_PANEL_A["BHAR"]["mean"],
                "paper_median": table2.ORIGINAL_PANEL_A["BHAR"]["median"],
                "paper_coef": table2.ORIGINAL_PANEL_B["BHAR"]["coef"],
                "paper_t": table2.ORIGINAL_PANEL_B["BHAR"]["t"],
            }
        )
    bhar = pd.DataFrame(bhar_rows)
    return master, base474, sample471, drop3, regs, bhar


def write_doc(
    sample_firm: pd.DataFrame,
    sample_chunk: pd.DataFrame,
    late14: pd.DataFrame,
    desc: pd.DataFrame,
    panel: pd.DataFrame,
    base474: pd.DataFrame,
    sample471: pd.DataFrame,
    drop3: pd.DataFrame,
    regs: pd.DataFrame,
    bhar: pd.DataFrame,
) -> None:
    table1_view = desc[
        desc["metric"].isin(
            [
                "Chunk_num",
                "Text_len",
                "Summary_len_proxy",
                "Redundancy_chunk_proxy",
                "lnN_tech",
                "Redundancy_proxy",
                "Redundancy_glm4",
            ]
        )
    ].copy()
    main_regs = regs[regs["sample"].eq("common471_after_drop3")].copy()
    delta = regs.pivot(index="dep_var", columns="sample", values="coef").reset_index()
    if {"common474_before_drop3", "common471_after_drop3"}.issubset(delta.columns):
        delta["coef_move_after_drop3"] = delta["common471_after_drop3"] - delta["common474_before_drop3"]
    else:
        delta["coef_move_after_drop3"] = np.nan

    lines = [
        "# Cutoff552 And Table2 471 Probe",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 结论",
        "",
        "- 判定：`NO_PASS_YET`，但样本制度线索明显增强。",
        "- `2023-08-15` 上市日 cutoff 可以把 candidate566 精确切成原文 Table 1 的 `552` 家。",
        f"- 但 sample552 仍有 `{len(sample_chunk)}` 个 chunk，原文为 8683，仍多 `{len(sample_chunk) - 8683}` 个 chunk；所以 cutoff 解释了 firm N，不足以单独解释 chunk N。",
        "- 2019-2022 complete sample 中删去 `688475`、`688496`、`688525` 可以把 `474` 精确切成原文 Table 2 的 `471` 家。",
        "- 删去这三家后，`BHAR` 和 `FSales_Growth` 仍未恢复原文显著负向；这说明 N 对齐本身不够，Y 的数据库字段/窗口口径仍是主问题。",
        "",
        "## Table 1: 2023-08-15 Cutoff",
        "",
        f"- cutoff 规则：保留 `list_date_csmar < {LIST_DATE_CUTOFF.date().isoformat()}`。",
        f"- firm N：`{sample_firm['sec_code'].nunique()}`。",
        f"- chunk N：`{len(sample_chunk)}`。",
        "",
        *md_table(
            table1_view,
            [
                "scope",
                "metric",
                "current_N",
                "paper_N",
                "N_gap",
                "current_mean",
                "paper_mean",
                "mean_gap",
                "current_median",
                "paper_median",
            ],
            digits=3,
        ),
        "",
        "### Excluded Late-2023 Firms",
        "",
        *md_table(
            late14[["code", "sec_name_csmar", "list_date_csmar", "prospectus_publish_date_csmar"]],
            ["code", "sec_name_csmar", "list_date_csmar", "prospectus_publish_date_csmar"],
            digits=0,
        ),
        "",
        "## Panel B/C/D On Sample552",
        "",
        *md_table(
            panel,
            [
                "measure",
                "B_rho",
                "B_p",
                "low_median_by_score_median",
                "high_median_by_score_median",
                "C_cluster_coef",
                "C_cluster_p",
                "D_cluster_coef",
                "D_cluster_p",
            ],
            digits=4,
        ),
        "",
        "## Table 2: 474 To 471",
        "",
        f"- 2019-2022 common complete sample before drop：`{base474['code'].nunique()}`。",
        f"- drop late-2022 firms 后：`{sample471['code'].nunique()}`。",
        "",
        "### Dropped Late-2022 Firms",
        "",
        *md_table(
            drop3[["code", "sec_name", "first_trade_date", "BHAR", "FSales_Growth", "FInvention"]],
            ["code", "sec_name", "first_trade_date", "BHAR", "FSales_Growth", "FInvention"],
            digits=4,
        ),
        "",
        "### Main Regression On 471",
        "",
        *md_table(
            main_regs,
            ["dep_var", "N", "coef", "t_HC1", "p_HC1", "paper_coef", "paper_t", "paper_N", "sign_match"],
            digits=4,
        ),
        "",
        "### Coefficient Movement After Dropping Three Firms",
        "",
        *md_table(
            delta,
            ["dep_var", "common474_before_drop3", "common471_after_drop3", "coef_move_after_drop3"],
            digits=5,
        ),
        "",
        "## BHAR Variants On 471",
        "",
        *md_table(
            bhar,
            ["bhar_candidate", "N", "mean", "median", "coef", "t_HC1", "p_HC1", "paper_mean", "paper_median", "paper_coef", "paper_t"],
            digits=4,
        ),
        "",
        "## 读法",
        "",
        "1. `2023-08-15` cutoff 是目前最强的 Table 1 firm-level 样本解释，但不能宣称完全复刻 Table 1，因为 chunk N 仍多 223。",
        "2. 2022 年末三家公司确实解释了 Table 2 的 `474 -> 471`，而且它们的 BHAR 很高；但删掉后 BHAR 系数只从约 0.00424 降到 0.00331，仍没有转负。",
        "3. 当前证据支持“样本制度要按 cutoff 写入”，但不支持“样本修正即可复刻 Table 2”。下一步仍应定向找 CSMAR 现成的 BHAR/营业收入增长率字段。",
        "4. 不建议继续扩样、改 prompt 或重做摘要。",
        "",
        "## 输出",
        "",
        f"- sample552 firm：`{SAMPLE552_FIRM_OUT}`",
        f"- sample552 chunk：`{SAMPLE552_CHUNK_OUT}`",
        f"- Table 1 descriptives：`{TABLE1_DESC_OUT}`",
        f"- panel tests：`{PANEL_TESTS_OUT}`",
        f"- table2 471 master：`{TABLE2_MASTER471_OUT}`",
        f"- table2 regressions：`{TABLE2_REG_OUT}`",
        f"- BHAR variants：`{BHAR_VARIANTS_OUT}`",
        "",
    ]
    DOC_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    sample_firm, sample_chunk, late14, desc, panel = build_sample552()
    master, base474, sample471, drop3, regs, bhar = build_table2_471()

    sample_firm.to_csv(SAMPLE552_FIRM_OUT, index=False, encoding="utf-8-sig")
    sample_chunk.to_csv(SAMPLE552_CHUNK_OUT, index=False, encoding="utf-8-sig")
    late14.to_csv(LATE14_OUT, index=False, encoding="utf-8-sig")
    desc.to_csv(TABLE1_DESC_OUT, index=False, encoding="utf-8-sig")
    panel.to_csv(PANEL_TESTS_OUT, index=False, encoding="utf-8-sig")
    sample471.to_csv(TABLE2_MASTER471_OUT, index=False, encoding="utf-8-sig")
    regs.to_csv(TABLE2_REG_OUT, index=False, encoding="utf-8-sig")
    bhar.to_csv(BHAR_VARIANTS_OUT, index=False, encoding="utf-8-sig")
    drop3.to_csv(DROP3_OUT, index=False, encoding="utf-8-sig")

    write_doc(sample_firm, sample_chunk, late14, desc, panel, base474, sample471, drop3, regs, bhar)
    print(f"sample552 firm N={sample_firm['sec_code'].nunique()} chunk N={len(sample_chunk)}")
    print(f"table2 common before={base474['code'].nunique()} after={sample471['code'].nunique()}")
    print(regs.to_string(index=False))
    print(f"doc={DOC_OUT}")


if __name__ == "__main__":
    main()
