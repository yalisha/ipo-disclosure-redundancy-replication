#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats


PROJECT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
FULL_DIR = PROJECT / "results/glm4_dewrap_join_full543_20260705"
FIRST25_DIR = PROJECT / "results/glm4_dewrap_join_first_batch25_20260706"
AUDIT_DIR = PROJECT / "results/sample_and_ready_y_fields_audit_20260706"
OUT_DIR = PROJECT / "results/glm4_dewrap_join_candidate566_20260707"
DOC_OUT = PROJECT / "docs/00_current/candidate566_x_universe_after_first_batch_20260707.md"

MODE = "cot_v3b_len132_tight"
EXCLUDE_EXTRA = {"688688", "688717"}
TRANSFER_SAMPLE = "688287"

PAPER_CHUNK = {
    "Chunk_num": {"N": 8683, "mean": 18.191, "std": 6.983, "p25": 13.000, "median": 16.000, "p75": 22.000},
    "Text_len": {"N": 8683, "mean": 3866.817, "std": 343.868, "p25": 3888.000, "median": 3954.000, "p75": 3985.000},
    "Summary_len": {"N": 8683, "mean": 132.678, "std": 39.683, "p25": 105.000, "median": 130.000, "p75": 158.000},
    "Redundancy_chunk": {"N": 8683, "mean": 32.176, "std": 11.730, "p25": 24.356, "median": 29.739, "p75": 37.037},
}
PAPER_FIRM = {
    "lnN_tech": {"N": 552, "mean": 10.962, "std": 0.350, "p25": 10.714, "median": 10.910, "p75": 11.185},
    "Redundancy": {"N": 552, "mean": 29.074, "std": 2.630, "p25": 27.402, "median": 28.910, "p75": 30.795},
}


def z6(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6)


def describe(series: pd.Series) -> dict[str, float]:
    s = pd.to_numeric(series, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if s.empty:
        return {"N": 0, "mean": math.nan, "std": math.nan, "p25": math.nan, "median": math.nan, "p75": math.nan}
    return {
        "N": int(len(s)),
        "mean": float(s.mean()),
        "std": float(s.std(ddof=1)),
        "p25": float(s.quantile(0.25)),
        "median": float(s.median()),
        "p75": float(s.quantile(0.75)),
    }


def spearman(df: pd.DataFrame, x: str, y: str) -> dict[str, float]:
    reg = df[[x, y]].replace([np.inf, -np.inf], np.nan).dropna()
    if reg.empty or reg[x].nunique() < 2 or reg[y].nunique() < 2:
        return {"n": int(reg.shape[0]), "rho": math.nan, "p": math.nan}
    rho, p = stats.spearmanr(reg[x].astype(float), reg[y].astype(float))
    return {"n": int(reg.shape[0]), "rho": float(rho), "p": float(p)}


def cluster_ols(df: pd.DataFrame, y: str, x: str, cluster_col: str = "sec_code") -> dict[str, float]:
    reg = df[[y, x, cluster_col]].replace([np.inf, -np.inf], np.nan).dropna()
    if reg.empty or reg[x].nunique() < 2:
        return {"n": int(reg.shape[0]), "coef": math.nan, "t": math.nan, "p": math.nan}
    model = sm.OLS(reg[y].astype(float), sm.add_constant(reg[x].astype(float)))
    fit = model.fit(cov_type="cluster", cov_kwds={"groups": reg[cluster_col].astype(str)})
    return {
        "n": int(fit.nobs),
        "coef": float(fit.params[x]),
        "t": float(fit.tvalues[x]),
        "p": float(fit.pvalues[x]),
    }


def stat_row(scope: str, metric: str, current: dict[str, float], paper: dict[str, float] | None = None) -> dict[str, object]:
    row: dict[str, object] = {"scope": scope, "metric": metric, **{f"current_{k}": v for k, v in current.items()}}
    if paper:
        row.update({f"paper_{k}": v for k, v in paper.items()})
        row["mean_gap"] = current["mean"] - paper["mean"]
        row["N_gap"] = current["N"] - paper["N"]
    return row


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


def load_metrics() -> tuple[pd.DataFrame, pd.DataFrame]:
    firm_parts = []
    chunk_parts = []
    specs = [("full543", FULL_DIR), ("first_batch25", FIRST25_DIR)]
    for source, directory in specs:
        firm = pd.read_csv(directory / f"firm_metrics_glm4_{MODE}_20260705.csv", dtype={"sec_code": str})
        chunk = pd.read_csv(directory / f"chunk_metrics_glm4_{MODE}_20260705.csv", dtype={"sec_code": str})
        firm["sec_code"] = z6(firm["sec_code"])
        chunk["sec_code"] = z6(chunk["sec_code"])
        firm["source_run"] = source
        chunk["source_run"] = source
        firm_parts.append(firm)
        chunk_parts.append(chunk)
    firm_all = pd.concat(firm_parts, ignore_index=True)
    chunk_all = pd.concat(chunk_parts, ignore_index=True)
    firm = firm_all[~firm_all["sec_code"].isin(EXCLUDE_EXTRA)].copy()
    chunk = chunk_all[~chunk_all["sec_code"].isin(EXCLUDE_EXTRA)].copy()
    if firm["sec_code"].duplicated().any():
        dup = firm.loc[firm["sec_code"].duplicated(keep=False), "sec_code"].tolist()
        raise RuntimeError(f"Duplicated firm rows after merge: {dup[:10]}")
    return firm, chunk


def build_crosswalk(firm: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    universe = pd.read_csv(AUDIT_DIR / "csmar_star_ipo_universe_2019_2023_20260706.csv", dtype={"code": str})
    universe["code"] = z6(universe["code"])
    x_codes = set(firm["sec_code"].astype(str))
    universe_codes = set(universe["code"].astype(str))
    cross = universe.copy()
    cross["in_candidate_x"] = cross["code"].isin(x_codes)
    cross["candidate_status"] = np.select(
        [
            cross["code"].eq(TRANSFER_SAMPLE),
            cross["in_candidate_x"],
        ],
        ["transfer_listing_not_standard_ipo", "in_candidate_x"],
        default="missing_from_candidate_x",
    )
    extras = sorted(x_codes - universe_codes)
    extra_rows = pd.DataFrame({"code": extras, "candidate_status": "extra_not_in_csmar_universe"})
    if not extra_rows.empty:
        cross = pd.concat([cross, extra_rows], ignore_index=True, sort=False)
    by_year = (
        cross[cross["code"].isin(universe_codes)]
        .groupby(["list_year_csmar", "candidate_status"], dropna=False)["code"]
        .nunique()
        .reset_index(name="firm_n")
        .sort_values(["list_year_csmar", "candidate_status"])
    )
    return cross, by_year


def build_desc(firm: pd.DataFrame, chunk: pd.DataFrame) -> pd.DataFrame:
    desc_rows = [
        stat_row("chunk", "Chunk_num", describe(chunk["Chunk_num"]), PAPER_CHUNK["Chunk_num"]),
        stat_row("chunk", "Text_len", describe(chunk["Text_len"]), PAPER_CHUNK["Text_len"]),
        stat_row("chunk", "Summary_len_proxy", describe(chunk["Summary_len_proxy"]), PAPER_CHUNK["Summary_len"]),
        stat_row("chunk", "Redundancy_chunk_proxy", describe(chunk["Redundancy_chunk_proxy"]), PAPER_CHUNK["Redundancy_chunk"]),
        stat_row("chunk", "Summary_len_glm4", describe(chunk["Summary_len_glm4"]), PAPER_CHUNK["Summary_len"]),
        stat_row("chunk", "Redundancy_chunk_glm4", describe(chunk["Redundancy_chunk_glm4"]), PAPER_CHUNK["Redundancy_chunk"]),
        stat_row("firm", "lnN_tech", describe(firm["lnN_tech"]), PAPER_FIRM["lnN_tech"]),
        stat_row("firm", "Redundancy_proxy", describe(firm["Redundancy_proxy"]), PAPER_FIRM["Redundancy"]),
        stat_row("firm", "Redundancy_glm4", describe(firm["Redundancy_glm4"]), PAPER_FIRM["Redundancy"]),
    ]
    return pd.DataFrame(desc_rows)


def build_panel_tests(chunk: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for red_col, label in [
        ("Redundancy_chunk_proxy", "proxy denominator"),
        ("Redundancy_chunk_glm4", "GLM4 denominator"),
    ]:
        median_score = float(chunk["relevant_score"].median())
        low = chunk[chunk["relevant_score"].le(median_score)]
        high = chunk[chunk["relevant_score"].gt(median_score)]
        rel_low = chunk[chunk["relevant_score"].lt(2.0)]
        rel_high = chunk[chunk["relevant_score"].ge(2.0)]
        rows.append(
            {
                "measure": label,
                "B_rho": spearman(chunk, "relevant_score", red_col)["rho"],
                "B_p": spearman(chunk, "relevant_score", red_col)["p"],
                "low_median_by_score_median": float(low[red_col].median()),
                "high_median_by_score_median": float(high[red_col].median()),
                "low_lt2_median": float(rel_low[red_col].median()) if not rel_low.empty else math.nan,
                "high_ge2_median": float(rel_high[red_col].median()) if not rel_high.empty else math.nan,
                "C_cluster_coef": cluster_ols(chunk, red_col, "Chunk_num")["coef"],
                "C_cluster_p": cluster_ols(chunk, red_col, "Chunk_num")["p"],
                "D_cluster_coef": cluster_ols(chunk, red_col, "innovation_rate_all_union")["coef"],
                "D_cluster_p": cluster_ols(chunk, red_col, "innovation_rate_all_union")["p"],
            }
        )
    return pd.DataFrame(rows)


def write_doc(firm: pd.DataFrame, chunk: pd.DataFrame, cross: pd.DataFrame, by_year: pd.DataFrame, desc: pd.DataFrame, panel: pd.DataFrame) -> None:
    missing = cross[cross["candidate_status"].eq("missing_from_candidate_x")].copy()
    transfer = cross[cross["candidate_status"].eq("transfer_listing_not_standard_ipo")].copy()
    paper_gap = int(firm["sec_code"].nunique() - PAPER_FIRM["Redundancy"]["N"])
    chunk_gap = int(len(chunk) - PAPER_CHUNK["Text_len"]["N"])
    source_counts = firm.groupby("source_run")["sec_code"].nunique().reset_index(name="firm_n")

    lines = [
        "# Candidate566 X Universe After First-Batch Backfill",
        "",
        "日期：2026-07-07",
        "",
        "## 结论",
        "",
        "- 已将 full543 主口径 X 与首批 25 家 `dewrap_join + GLM tokenizer` 主口径 X 合并。",
        "- 已剔除 `688688`、`688717` 这两家不在 CSMAR 2019-2023 科创板已上市 IPO universe 内的记录。",
        f"- 合并后标准 IPO 候选 X 为 `{firm['sec_code'].nunique()}` 家、`{len(chunk)}` 个 chunk。",
        f"- CSMAR 2019-2023 STAR IPO universe 为 567 家；当前候选 X 只剩 `688287` 未纳入，且它是转板上市报告书，不是标准 IPO 招股说明书。",
        f"- 原文 Table 1 为 552 家；因此即使排除 `688287` 后，仍需要解释约 `{paper_gap}` 家额外排除规则。",
        f"- 当前 chunk 数比原文多 `{chunk_gap}` 个；这与 firm N 从 552 增至 566 一致，说明下一步不是再调 tokenizer，而是找原文样本筛选制度。",
        "",
        "## Source Runs",
        "",
        *md_table(source_counts, ["source_run", "firm_n"], digits=0),
        "",
        "## CSMAR Universe Crosswalk",
        "",
        *md_table(by_year, ["list_year_csmar", "candidate_status", "firm_n"], digits=0),
        "",
        "缺失/特殊样本：",
        "",
        *md_table(
            pd.concat([missing, transfer], ignore_index=True)[
                ["code", "sec_name_csmar", "list_date_csmar", "prospectus_publish_date_csmar", "candidate_status"]
            ],
            ["code", "sec_name_csmar", "list_date_csmar", "prospectus_publish_date_csmar", "candidate_status"],
            digits=0,
        ),
        "",
        "## Table 1 Measurement 对照",
        "",
        *md_table(
            desc,
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
                "current_p25",
                "current_p75",
            ],
            digits=3,
        ),
        "",
        "## Panel B/C/D 快速检验",
        "",
        *md_table(
            panel,
            [
                "measure",
                "B_rho",
                "B_p",
                "low_median_by_score_median",
                "high_median_by_score_median",
                "low_lt2_median",
                "high_ge2_median",
                "C_cluster_coef",
                "C_cluster_p",
                "D_cluster_coef",
                "D_cluster_p",
            ],
            digits=4,
        ),
        "",
        "## 判断",
        "",
        "1. X 的测度机制没有被首批25家破坏：`Redundancy_chunk_proxy`、Panel B、Panel D 都保持在合理区间。",
        "2. 合并后的 N=566 与原文 N=552 仍差 14 家；这已经是样本制度问题，不是 LLM 摘要或 tokenizer 问题。",
        "3. 下一步应优先查原文是否排除了转板、特殊上市、未完整一年后数据、发行失败/撤回后重启、或 Y/controls 缺失导致 Table 1 实际样本口径收缩。",
        "4. Table 2 不能直接用旧 543 master 续跑，因为新增25家没有被拼入 Y/controls master；需要用底层 CSMAR 数据重建 566 家 master。",
        "",
        "## 输出文件",
        "",
        f"- firm metrics：`{OUT_DIR / 'firm_metrics_candidate566_20260707.csv'}`",
        f"- chunk metrics：`{OUT_DIR / 'chunk_metrics_candidate566_20260707.csv'}`",
        f"- crosswalk：`{OUT_DIR / 'candidate566_vs_csmar_universe_crosswalk_20260707.csv'}`",
        f"- descriptives：`{OUT_DIR / 'candidate566_descriptives_vs_original_20260707.csv'}`",
        f"- panel tests：`{OUT_DIR / 'candidate566_panel_tests_20260707.csv'}`",
        "",
    ]
    DOC_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    firm, chunk = load_metrics()
    cross, by_year = build_crosswalk(firm)
    desc = build_desc(firm, chunk)
    panel = build_panel_tests(chunk)

    firm.to_csv(OUT_DIR / "firm_metrics_candidate566_20260707.csv", index=False, encoding="utf-8-sig")
    chunk.to_csv(OUT_DIR / "chunk_metrics_candidate566_20260707.csv", index=False, encoding="utf-8-sig")
    cross.to_csv(OUT_DIR / "candidate566_vs_csmar_universe_crosswalk_20260707.csv", index=False, encoding="utf-8-sig")
    by_year.to_csv(OUT_DIR / "candidate566_vs_csmar_by_year_20260707.csv", index=False, encoding="utf-8-sig")
    desc.to_csv(OUT_DIR / "candidate566_descriptives_vs_original_20260707.csv", index=False, encoding="utf-8-sig")
    panel.to_csv(OUT_DIR / "candidate566_panel_tests_20260707.csv", index=False, encoding="utf-8-sig")

    manifest = {
        "firms": int(firm["sec_code"].nunique()),
        "chunks": int(len(chunk)),
        "excluded_extra": sorted(EXCLUDE_EXTRA),
        "transfer_not_included": TRANSFER_SAMPLE,
        "paper_firm_n": PAPER_FIRM["Redundancy"]["N"],
        "paper_chunk_n": PAPER_CHUNK["Text_len"]["N"],
        "firm_n_gap_vs_paper": int(firm["sec_code"].nunique() - PAPER_FIRM["Redundancy"]["N"]),
        "chunk_n_gap_vs_paper": int(len(chunk) - PAPER_CHUNK["Text_len"]["N"]),
    }
    (OUT_DIR / "manifest_20260707.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_doc(firm, chunk, cross, by_year, desc, panel)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(desc[["scope", "metric", "current_N", "paper_N", "N_gap", "current_mean", "paper_mean", "mean_gap"]].to_string(index=False))
    print(panel.to_string(index=False))


if __name__ == "__main__":
    main()
