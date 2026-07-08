#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import math
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats as scipy_stats


PROJECT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
RUN_DIR = PROJECT / "results/summary_diagnostic_x_table2_20260707"
DOC_OUT = PROJECT / "docs/00_current/summary_diagnostic_x_table2_20260707.md"

CHUNK_IN = PROJECT / "results/cutoff552_table2_471_probe_20260707/sample552_chunk_metrics_cutoff_20260707.csv"
MASTER_IN = PROJECT / "results/cutoff552_table2_471_probe_20260707/table2_471_candidate_master_20260707.csv"

MASTER_OUT = RUN_DIR / "table2_471_diagnostic_x_master_20260707.csv"
REG_OUT = RUN_DIR / "table2_471_diagnostic_x_regressions_20260707.csv"
DESC_OUT = RUN_DIR / "diagnostic_x_descriptives_vs_original_20260707.csv"
PANEL_OUT = RUN_DIR / "diagnostic_x_panel_tests_20260707.csv"

TAIL_THRESHOLD = 1700
SUMMARY_CAP = 80

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

PAPER = {
    "chunk_n": 8683,
    "Chunk_num_mean": 18.191,
    "Text_len_mean": 3866.817,
    "Text_len_std": 343.868,
    "Summary_len_mean": 132.678,
    "Summary_len_std": 39.683,
    "Red_mean": 32.176,
    "Red_std": 11.730,
    "Red_p75": 37.037,
    "FirmRed_mean": 29.074,
    "FirmRed_std": 2.630,
    "FirmRed_p75": 30.795,
}


def import_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


table2 = import_module("table2_candidate566", PROJECT / "scripts/run_table2_candidate566_ipo_pre_controls_20260707.py")


def z6(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)


def to_num(df: pd.DataFrame, cols: list[str]) -> None:
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")


def desc(series: pd.Series) -> dict[str, float]:
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


def merged_chunks(raw: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    n_cols = [f"n{i}" for i in range(6)]
    for _, g in raw.groupby("sec_code", sort=False):
        arr: list[dict[str, object]] = []
        for r in g.sort_values("chunk_index").to_dict("records"):
            item = {
                "sec_code": r["sec_code"],
                "sec_name": r.get("sec_name", ""),
                "text_len": float(r["chunk_glm4_tokens"]),
                "summary_raw": float(r["Summary_len_proxy"]),
                "source_custom_ids": str(r["custom_id"]),
                "source_chunk_count": 1,
            }
            for col in n_cols:
                item[col] = float(r.get(col, 0) if pd.notna(r.get(col, 0)) else 0)
            arr.append(item)

        while len(arr) > 1 and float(arr[-1]["text_len"]) < TAIL_THRESHOLD:
            tail = arr.pop()
            arr[-1]["text_len"] = float(arr[-1]["text_len"]) + float(tail["text_len"])
            arr[-1]["summary_raw"] = float(arr[-1]["summary_raw"]) + float(tail["summary_raw"])
            arr[-1]["source_custom_ids"] = str(arr[-1]["source_custom_ids"]) + ";" + str(tail["source_custom_ids"])
            arr[-1]["source_chunk_count"] = int(arr[-1]["source_chunk_count"]) + int(tail["source_chunk_count"])
            for col in n_cols:
                arr[-1][col] = float(arr[-1][col]) + float(tail[col])

        chunk_n = len(arr)
        for idx, item in enumerate(arr, start=1):
            sentence_count = sum(float(item[col]) for col in n_cols)
            high_score_count = float(item["n4"]) + float(item["n5"])
            weighted_score = sum(i * float(item[f"n{i}"]) for i in range(6))
            relevant_score = weighted_score / sentence_count if sentence_count else np.nan
            high_share = high_score_count / sentence_count if sentence_count else np.nan
            item.update(
                {
                    "processed_chunk_index": idx,
                    "processed_chunk_n": chunk_n,
                    "sentence_count": sentence_count,
                    "high_score_count": high_score_count,
                    "relevant_score_merged": relevant_score,
                    "high_score_share_merged": high_share,
                }
            )
            rows.append(item)

    return pd.DataFrame(rows)


def apply_candidate(processed: pd.DataFrame, label: str, rule: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    c = processed.copy()
    if rule == "score18":
        mask = pd.to_numeric(c["relevant_score_merged"], errors="coerce").lt(1.8)
        rule_desc = "Relevant_score < 1.8"
    elif rule == "highshare10":
        mask = pd.to_numeric(c["high_score_share_merged"], errors="coerce").le(0.10)
        rule_desc = "high_score_share <= 10%"
    else:
        mask = pd.Series(False, index=c.index)
        rule_desc = "no repair"

    c["candidate"] = label
    c["low_relevance_rule"] = rule_desc
    c["cap_applied"] = mask.astype(int)
    c["summary_diag"] = np.where(mask, np.minimum(c["summary_raw"].astype(float), SUMMARY_CAP), c["summary_raw"].astype(float))
    c["Redundancy_chunk_diag"] = c["text_len"].astype(float) / c["summary_diag"].replace({0: np.nan})
    c["Text_len"] = c["text_len"]
    c["Summary_len"] = c["summary_diag"]
    c["Chunk_num"] = c["processed_chunk_n"]

    f = (
        c.groupby(["sec_code", "sec_name"], as_index=False)
        .agg(
            chunk_n=("processed_chunk_index", "count"),
            text_sum=("text_len", "sum"),
            summary_sum=("summary_diag", "sum"),
            relevant_score_mean=("relevant_score_merged", "mean"),
            cap_applied_n=("cap_applied", "sum"),
            red_chunk_mean=("Redundancy_chunk_diag", "mean"),
        )
        .copy()
    )
    f["candidate"] = label
    f["Redundancy_diag"] = f["text_sum"] / f["summary_sum"].replace({0: np.nan})
    f["lnN_tech_diag"] = np.log(f["text_sum"].replace({0: np.nan}))
    return c, f


def build_descriptives(chunk_map: dict[str, pd.DataFrame], firm_map: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for label, c in chunk_map.items():
        f = firm_map[label]
        rows.append(
            {
                "candidate": label,
                "chunk_n": int(c.shape[0]),
                "chunk_n_gap": int(c.shape[0] - PAPER["chunk_n"]),
                "cap_applied_n": int(c["cap_applied"].sum()),
                "Chunk_num_mean": float(c["Chunk_num"].mean()),
                "Text_len_mean": float(c["Text_len"].mean()),
                "Text_len_std": float(c["Text_len"].std(ddof=1)),
                "Summary_len_mean": float(c["Summary_len"].mean()),
                "Summary_len_std": float(c["Summary_len"].std(ddof=1)),
                "Red_mean": float(c["Redundancy_chunk_diag"].mean()),
                "Red_std": float(c["Redundancy_chunk_diag"].std(ddof=1)),
                "Red_p75": float(c["Redundancy_chunk_diag"].quantile(0.75)),
                "FirmRed_mean": float(f["Redundancy_diag"].mean()),
                "FirmRed_std": float(f["Redundancy_diag"].std(ddof=1)),
                "FirmRed_p75": float(f["Redundancy_diag"].quantile(0.75)),
            }
        )
    out = pd.DataFrame(rows)
    for key, target in PAPER.items():
        if key in out.columns:
            out[f"paper_{key}"] = target
            out[f"gap_{key}"] = out[key] - target
    return out


def panel_tests(chunk_map: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for label, c in chunk_map.items():
        reg = c[["relevant_score_merged", "Redundancy_chunk_diag", "sec_code"]].replace([np.inf, -np.inf], np.nan).dropna()
        if reg["relevant_score_merged"].nunique() > 1 and reg["Redundancy_chunk_diag"].nunique() > 1:
            rho, p_val = scipy_stats.spearmanr(reg["relevant_score_merged"], reg["Redundancy_chunk_diag"])
        else:
            rho, p_val = np.nan, np.nan
        med = reg["relevant_score_merged"].median()
        low = reg[reg["relevant_score_merged"].le(med)]
        high = reg[reg["relevant_score_merged"].gt(med)]
        low2 = reg[reg["relevant_score_merged"].lt(2.0)]
        high2 = reg[reg["relevant_score_merged"].ge(2.0)]
        rows.append(
            {
                "candidate": label,
                "N": int(reg.shape[0]),
                "spearman_rho": float(rho) if pd.notna(rho) else np.nan,
                "spearman_p": float(p_val) if pd.notna(p_val) else np.nan,
                "low_median_by_score_median": float(low["Redundancy_chunk_diag"].median()),
                "high_median_by_score_median": float(high["Redundancy_chunk_diag"].median()),
                "low_lt2_median": float(low2["Redundancy_chunk_diag"].median()),
                "high_ge2_median": float(high2["Redundancy_chunk_diag"].median()),
            }
        )
    return pd.DataFrame(rows)


def regression_row(candidate: str, dep: str, df: pd.DataFrame) -> dict[str, object]:
    sample = df.dropna(subset=[dep, *MAIN_CONTROLS]).copy()
    try:
        fit = smf.ols(f"{dep} ~ {RHS}", data=sample).fit(cov_type="HC1")
        paper = table2.ORIGINAL_PANEL_B[dep]
        return {
            "candidate": candidate,
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
            "error": "",
        }
    except Exception as exc:
        return {
            "candidate": candidate,
            "dep_var": dep,
            "N": int(sample.shape[0]),
            "coef": np.nan,
            "se_HC1": np.nan,
            "t_HC1": np.nan,
            "p_HC1": np.nan,
            "adj_r2": np.nan,
            "paper_coef": table2.ORIGINAL_PANEL_B[dep]["coef"],
            "paper_t": table2.ORIGINAL_PANEL_B[dep]["t"],
            "paper_N": table2.ORIGINAL_PANEL_B[dep]["N"],
            "sign_match": False,
            "error": repr(exc),
        }


def build_table2(master: pd.DataFrame, firm_map: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    base = master.copy()
    base["code"] = z6(base["code"])
    wide = base.copy()
    rows = []

    candidates = {"baseline_original_x": None, **firm_map}
    for label, firm in candidates.items():
        sub = base.copy()
        if firm is not None:
            f = firm[["sec_code", "Redundancy_diag", "cap_applied_n", "summary_sum"]].copy()
            f["code"] = z6(f["sec_code"])
            sub = sub.merge(
                f[["code", "Redundancy_diag", "cap_applied_n", "summary_sum"]],
                on="code",
                how="left",
                validate="one_to_one",
            )
            sub["Redundancy"] = pd.to_numeric(sub["Redundancy_diag"], errors="coerce")
            wide[f"Redundancy_{label}"] = sub["Redundancy"].values
            wide[f"cap_applied_n_{label}"] = sub["cap_applied_n"].values
            wide[f"summary_sum_{label}"] = sub["summary_sum"].values
        else:
            wide[f"Redundancy_{label}"] = sub["Redundancy"].values

        for dep in OUTCOMES:
            rows.append(regression_row(label, dep, sub))

    regs = pd.DataFrame(rows)
    baseline = regs[regs["candidate"].eq("baseline_original_x")][["dep_var", "coef", "t_HC1", "p_HC1"]].rename(
        columns={"coef": "baseline_coef", "t_HC1": "baseline_t", "p_HC1": "baseline_p"}
    )
    regs = regs.merge(baseline, on="dep_var", how="left")
    regs["coef_delta_vs_baseline"] = regs["coef"] - regs["baseline_coef"]
    regs["abs_gap_to_paper_coef"] = (regs["coef"] - regs["paper_coef"]).abs()
    regs["abs_gap_baseline_to_paper_coef"] = (regs["baseline_coef"] - regs["paper_coef"]).abs()
    regs["gap_improved_vs_baseline"] = regs["abs_gap_to_paper_coef"] < regs["abs_gap_baseline_to_paper_coef"]
    return wide, regs


def write_doc(desc_df: pd.DataFrame, panel_df: pd.DataFrame, regs: pd.DataFrame) -> None:
    main_desc = desc_df[
        [
            "candidate",
            "chunk_n",
            "chunk_n_gap",
            "cap_applied_n",
            "Summary_len_mean",
            "Summary_len_std",
            "Red_mean",
            "Red_std",
            "Red_p75",
            "FirmRed_mean",
            "FirmRed_std",
        ]
    ].copy()
    reg_view = regs[
        [
            "candidate",
            "dep_var",
            "N",
            "coef",
            "t_HC1",
            "p_HC1",
            "paper_coef",
            "paper_t",
            "coef_delta_vs_baseline",
            "gap_improved_vs_baseline",
            "sign_match",
        ]
    ].copy()
    lines = [
        "# Summary Denominator Diagnostic X And Table 2",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 结论",
        "",
        "- 本轮只做第一步 diagnostic X：不重跑 LLM，不把机械 cap 当正式测度。",
        f"- 处理口径固定为 `tail_merge<{TAIL_THRESHOLD}`，然后对低相关 processed chunk 执行 `Summary_len=min(Summary_len,{SUMMARY_CAP})`。",
        "- 两个候选分别是 `tailmerge1700_score18_cap80` 与 `tailmerge1700_highshare10_cap80`。",
        "- 结果显示：描述统计确实更接近原文右尾；但 Table 2 的 `BHAR` 和 `FSales_Growth` 仍没有恢复原文显著负向。",
        "- 因此这一步支持“摘要分母右尾机制可以修”，但不支持“修 X 就能复刻主效应”。",
        "",
        "## Diagnostic X 描述统计",
        "",
        f"原文参照：chunk N=`{PAPER['chunk_n']}`，Summary mean/std=`{PAPER['Summary_len_mean']}`/`{PAPER['Summary_len_std']}`，Red mean/std/p75=`{PAPER['Red_mean']}`/`{PAPER['Red_std']}`/`{PAPER['Red_p75']}`，Firm Red mean/std=`{PAPER['FirmRed_mean']}`/`{PAPER['FirmRed_std']}`。",
        "",
        *md_table(main_desc, main_desc.columns.tolist(), digits=3),
        "",
        "## Panel B 方向性检查",
        "",
        *md_table(
            panel_df,
            [
                "candidate",
                "N",
                "spearman_rho",
                "spearman_p",
                "low_median_by_score_median",
                "high_median_by_score_median",
                "low_lt2_median",
                "high_ge2_median",
            ],
            digits=4,
        ),
        "",
        "## Table 2 471 家主回归",
        "",
        *md_table(reg_view, reg_view.columns.tolist(), digits=4),
        "",
        "## 读法",
        "",
        "1. `score18 cap80` 对右尾修复更强，`Redundancy_chunk` 的 p75 与 std 更接近原文，但企业层 Redundancy 均值被推高到 30 以上。",
        "2. `highshare10 cap80` 更温和，且让 `FSales_Growth` 系数从 0.0141 降到 0.0079，但仍没有转负。",
        "3. `FInvention` 仍是负向但不显著；`BHAR` 仍为正，甚至在 `score18 cap80` 下更偏离原文。",
        "4. 下一步若继续修 X，应只把它作为真实 LLM 低相关短摘 repair 的候选，不应直接用机械 cap 定版。",
        "5. 若目标是复刻论文主效应，优先级仍应回到 `BHAR/FSales_Growth` 的原文数据库字段与窗口口径。",
        "",
        "## 输出",
        "",
        f"- master：`{MASTER_OUT}`",
        f"- regressions：`{REG_OUT}`",
        f"- descriptives：`{DESC_OUT}`",
        f"- panel tests：`{PANEL_OUT}`",
        "",
    ]
    DOC_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(CHUNK_IN, dtype={"sec_code": str}, encoding="utf-8-sig")
    raw["sec_code"] = z6(raw["sec_code"])
    to_num(raw, ["chunk_index", "chunk_glm4_tokens", "Summary_len_proxy", *[f"n{i}" for i in range(6)]])
    master = pd.read_csv(MASTER_IN, dtype={"code": str, "sec_code": str}, encoding="utf-8-sig", low_memory=False)
    master["code"] = z6(master["code"])
    master["sec_code"] = z6(master["sec_code"])

    processed = merged_chunks(raw)
    chunk_map: dict[str, pd.DataFrame] = {}
    firm_map: dict[str, pd.DataFrame] = {}
    for label, rule in [
        ("tailmerge1700_score18_cap80", "score18"),
        ("tailmerge1700_highshare10_cap80", "highshare10"),
    ]:
        c, f = apply_candidate(processed, label, rule)
        chunk_map[label] = c
        firm_map[label] = f
        c.to_csv(RUN_DIR / f"{label}_chunk_metrics_20260707.csv", index=False, encoding="utf-8-sig")
        f.to_csv(RUN_DIR / f"{label}_firm_metrics_20260707.csv", index=False, encoding="utf-8-sig")

    desc_df = build_descriptives(chunk_map, firm_map)
    panel_df = panel_tests(chunk_map)
    wide, regs = build_table2(master, firm_map)

    desc_df.to_csv(DESC_OUT, index=False, encoding="utf-8-sig")
    panel_df.to_csv(PANEL_OUT, index=False, encoding="utf-8-sig")
    wide.to_csv(MASTER_OUT, index=False, encoding="utf-8-sig")
    regs.to_csv(REG_OUT, index=False, encoding="utf-8-sig")
    write_doc(desc_df, panel_df, regs)

    print(f"doc={DOC_OUT}")
    print(f"master={MASTER_OUT}")
    print(f"regressions={REG_OUT}")
    print(desc_df.to_string(index=False))
    print(regs[["candidate", "dep_var", "N", "coef", "t_HC1", "p_HC1", "paper_coef", "paper_t", "coef_delta_vs_baseline", "gap_improved_vs_baseline", "sign_match"]].to_string(index=False))


if __name__ == "__main__":
    main()
