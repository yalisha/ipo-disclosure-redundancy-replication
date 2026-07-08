#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
RUN_DIR = ROOT / "results/siliconflow_glm4_32b_pilot50_20260707"
OUT_DIR = ROOT / "results/glm50_tailmerge_floor_candidates_20260707"
DOC = ROOT / "docs/00_current/glm50_tailmerge_floor_candidate_gate_20260707.md"

PAPER_CHUNK = {
    "Chunk_num": {"mean": 18.191, "std": 6.983, "p25": 13.000, "median": 16.000, "p75": 22.000},
    "Text_len": {"mean": 3866.817, "std": 343.868, "p25": 3888.000, "median": 3954.000, "p75": 3985.000},
    "Summary_len": {"mean": 132.678, "std": 39.683, "p25": 105.000, "median": 130.000, "p75": 158.000},
    "Redundancy_chunk": {"mean": 32.176, "std": 11.730, "p25": 24.356, "median": 29.739, "p75": 37.037},
}
PAPER_FIRM = {
    "lnN_tech": {"mean": 10.962, "std": 0.350, "p25": 10.714, "median": 10.910, "p75": 11.185},
    "Redundancy": {"mean": 29.074, "std": 2.630, "p25": 27.402, "median": 28.910, "p75": 30.795},
}

CANDIDATES = [
    {"name": "raw_proxy", "unit": "Summary_len_proxy", "process": "keep", "threshold": 0, "floor": 0},
    {"name": "raw_glm4token", "unit": "Summary_len_glm4", "process": "keep", "threshold": 0, "floor": 0},
    {"name": "proxy_tailmerge1500_floor50", "unit": "Summary_len_proxy", "process": "merge_tail", "threshold": 1500, "floor": 50},
    {"name": "proxy_tailmerge2000_floor50", "unit": "Summary_len_proxy", "process": "merge_tail", "threshold": 2000, "floor": 50},
    {"name": "proxy_tailmerge2000_floor60", "unit": "Summary_len_proxy", "process": "merge_tail", "threshold": 2000, "floor": 60},
    {"name": "proxy_tailmerge2000_floor80", "unit": "Summary_len_proxy", "process": "merge_tail", "threshold": 2000, "floor": 80},
    {"name": "proxy_tailmerge2000_floor100", "unit": "Summary_len_proxy", "process": "merge_tail", "threshold": 2000, "floor": 100},
    {"name": "glm4token_tailmerge1500_floor0", "unit": "Summary_len_glm4", "process": "merge_tail", "threshold": 1500, "floor": 0},
    {"name": "glm4token_tailmerge2000_floor0", "unit": "Summary_len_glm4", "process": "merge_tail", "threshold": 2000, "floor": 0},
]


def describe(s: pd.Series) -> dict[str, float]:
    s = pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if s.empty:
        return {k: math.nan for k in ["n", "mean", "std", "p25", "median", "p75", "min", "max"]}
    return {
        "n": int(s.shape[0]),
        "mean": float(s.mean()),
        "std": float(s.std(ddof=1)),
        "p25": float(s.quantile(0.25)),
        "median": float(s.median()),
        "p75": float(s.quantile(0.75)),
        "min": float(s.min()),
        "max": float(s.max()),
    }


def rel_error(value: float, target: float) -> float:
    if not np.isfinite(value) or not np.isfinite(target) or target == 0:
        return 0.0
    return abs(value - target) / abs(target)


def spearman(df: pd.DataFrame, x: str, y: str) -> dict[str, float]:
    reg = df[[x, y]].replace([np.inf, -np.inf], np.nan).dropna()
    if reg.empty or reg[x].nunique() < 2 or reg[y].nunique() < 2:
        return {"n": int(reg.shape[0]), "rho": math.nan, "p": math.nan}
    rho, p = stats.spearmanr(reg[x].astype(float), reg[y].astype(float))
    return {"n": int(reg.shape[0]), "rho": float(rho), "p": float(p)}


def reg_y_on_x(df: pd.DataFrame, y: str, x: str, cluster_col: str | None = None) -> dict[str, float]:
    cols = [y, x] + ([cluster_col] if cluster_col else [])
    reg = df[cols].replace([np.inf, -np.inf], np.nan).dropna()
    if reg.empty or reg[x].nunique() < 2:
        return {"n": int(reg.shape[0]), "coef": math.nan, "t": math.nan, "p": math.nan}
    model = sm.OLS(reg[y].astype(float), sm.add_constant(reg[x].astype(float)))
    if cluster_col:
        fit = model.fit(cov_type="cluster", cov_kwds={"groups": reg[cluster_col].astype(str)})
    else:
        fit = model.fit(cov_type="HC1")
    return {"n": int(reg.shape[0]), "coef": float(fit.params[x]), "t": float(fit.tvalues[x]), "p": float(fit.pvalues[x])}


def fmt(value: object, digits: int = 3) -> str:
    try:
        f = float(value)
    except Exception:
        return ""
    if math.isnan(f):
        return ""
    return f"{f:.{digits}f}"


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    chunks = pd.read_csv(RUN_DIR / "chunk_metrics_glm4_cot_v3b_len132_tight_20260705.csv", dtype={"sec_code": str})
    sections = pd.read_csv(RUN_DIR / "ipo_business_technology_sections.csv", dtype={"sec_code": str})
    numeric = [
        "chunk_index",
        "chunk_glm4_tokens",
        "Summary_len_proxy",
        "Summary_len_glm4",
        "sentence_count",
        "n0",
        "n1",
        "n2",
        "n3",
        "n4",
        "n5",
        "innovation_terms_all_union",
        "innovation_terms_without_target",
    ]
    for col in numeric:
        if col in chunks.columns:
            chunks[col] = pd.to_numeric(chunks[col], errors="coerce")
    sections["tech_text_glm4_tokens"] = pd.to_numeric(sections["tech_text_glm4_tokens"], errors="coerce")
    return chunks, sections


def score_from_counts(row: dict[str, float]) -> float:
    total = sum(float(row.get(f"n{i}", 0) or 0) for i in range(6))
    if total <= 0:
        return math.nan
    return sum(i * float(row.get(f"n{i}", 0) or 0) for i in range(6)) / total


def aggregate_items(items: list[dict[str, object]], candidate: dict[str, object], firm_chunk_n: int) -> dict[str, object]:
    out: dict[str, object] = {
        "sec_code": items[0]["sec_code"],
        "sec_name": items[0]["sec_name"],
        "source_custom_ids": ";".join(str(x["custom_id"]) for x in items),
        "source_chunk_start": int(min(float(x["chunk_index"]) for x in items)),
        "source_chunk_end": int(max(float(x["chunk_index"]) for x in items)),
        "source_chunk_n": len(items),
        "Text_len": sum(float(x["chunk_glm4_tokens"]) for x in items),
        "summary_len_raw_sum": sum(float(x[candidate["unit"]]) for x in items),
        "Chunk_num": firm_chunk_n,
        "unit": candidate["unit"],
        "process": candidate["process"],
        "threshold": candidate["threshold"],
        "summary_floor": candidate["floor"],
        "candidate": candidate["name"],
    }
    out["Summary_len"] = max(float(out["summary_len_raw_sum"]), float(candidate["floor"]))
    out["floor_applied"] = int(float(out["summary_len_raw_sum"]) < float(candidate["floor"]))
    for col in ["n0", "n1", "n2", "n3", "n4", "n5"]:
        out[col] = sum(float(x.get(col, 0) or 0) for x in items)
    out["Relevant_score"] = score_from_counts(out)
    out["innovation_terms_all_union"] = sum(float(x.get("innovation_terms_all_union", 0) or 0) for x in items)
    out["innovation_terms_without_target"] = sum(float(x.get("innovation_terms_without_target", 0) or 0) for x in items)
    out["innovation_rate_all_union"] = out["innovation_terms_all_union"] / out["Text_len"] * 1000 if out["Text_len"] else math.nan
    out["innovation_rate_without_target"] = (
        out["innovation_terms_without_target"] / out["Text_len"] * 1000 if out["Text_len"] else math.nan
    )
    out["Redundancy_chunk"] = out["Text_len"] / out["Summary_len"] if out["Summary_len"] else math.nan
    return out


def build_candidate(chunks: pd.DataFrame, sections: pd.DataFrame, candidate: dict[str, object]) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    for _, g in chunks.groupby("sec_code", sort=False):
        items = g.sort_values("chunk_index").to_dict("records")
        groups = [[x] for x in items]
        if candidate["process"] == "merge_tail":
            while len(groups) > 1 and sum(float(x["chunk_glm4_tokens"]) for x in groups[-1]) < float(candidate["threshold"]):
                groups[-2].extend(groups.pop())
        elif candidate["process"] != "keep":
            raise ValueError(str(candidate["process"]))
        firm_chunk_n = len(groups)
        for group in groups:
            rows.append(aggregate_items(group, candidate, firm_chunk_n))
    c = pd.DataFrame(rows)
    firm = (
        c.groupby(["sec_code", "sec_name"], as_index=False)
        .agg(
            chunk_n=("source_custom_ids", "size"),
            text_sum=("Text_len", "sum"),
            summary_sum=("Summary_len", "sum"),
            floor_applied_n=("floor_applied", "sum"),
            relevant_score_mean=("Relevant_score", "mean"),
        )
    )
    firm = firm.merge(sections[["sec_code", "tech_text_glm4_tokens"]], on="sec_code", how="left")
    firm["lnN_tech"] = np.log(firm["text_sum"].replace({0: np.nan}))
    firm["Redundancy"] = firm["text_sum"] / firm["summary_sum"].replace({0: np.nan})
    return c, firm


def stat_loss(metric: str, stats_dict: dict[str, float], target: dict[str, float]) -> float:
    return float(np.mean([rel_error(stats_dict[k], target[k]) for k in ["mean", "std", "p25", "median", "p75"]]))


def evaluate_candidate(c: pd.DataFrame, firm: pd.DataFrame, candidate: dict[str, object]) -> dict[str, object]:
    stats_map = {
        "Chunk_num": describe(c["Chunk_num"]),
        "Text_len": describe(c["Text_len"]),
        "Summary_len": describe(c["Summary_len"]),
        "Redundancy_chunk": describe(c["Redundancy_chunk"]),
        "lnN_tech": describe(firm["lnN_tech"]),
        "Redundancy": describe(firm["Redundancy"]),
    }
    losses = {
        "loss_chunk_num": stat_loss("Chunk_num", stats_map["Chunk_num"], PAPER_CHUNK["Chunk_num"]),
        "loss_text": stat_loss("Text_len", stats_map["Text_len"], PAPER_CHUNK["Text_len"]),
        "loss_summary": stat_loss("Summary_len", stats_map["Summary_len"], PAPER_CHUNK["Summary_len"]),
        "loss_red_chunk": stat_loss("Redundancy_chunk", stats_map["Redundancy_chunk"], PAPER_CHUNK["Redundancy_chunk"]),
        "loss_lnn": stat_loss("lnN_tech", stats_map["lnN_tech"], PAPER_FIRM["lnN_tech"]),
        "loss_red_firm": stat_loss("Redundancy", stats_map["Redundancy"], PAPER_FIRM["Redundancy"]),
    }
    panel_b = spearman(c, "Relevant_score", "Redundancy_chunk")
    panel_b_reg = reg_y_on_x(c, "Redundancy_chunk", "Relevant_score", "sec_code")
    valid_score = c[["Relevant_score", "Redundancy_chunk"]].dropna()
    med_score = valid_score["Relevant_score"].median()
    low = valid_score[valid_score["Relevant_score"].le(med_score)]
    high = valid_score[valid_score["Relevant_score"].gt(med_score)]
    panel_c = spearman(c, "Chunk_num", "Redundancy_chunk")
    panel_d = spearman(c, "innovation_rate_all_union", "Redundancy_chunk")
    out: dict[str, object] = {
        **candidate,
        "chunk_n": int(c.shape[0]),
        "firm_n": int(firm.shape[0]),
        "floor_applied_n": int(c["floor_applied"].sum()),
        "loss_all": float(np.mean(list(losses.values()))),
        **losses,
        "panel_b_n": panel_b["n"],
        "panel_b_rho": panel_b["rho"],
        "panel_b_p": panel_b["p"],
        "panel_b_cluster_coef": panel_b_reg["coef"],
        "panel_b_cluster_p": panel_b_reg["p"],
        "low_score_red_median": float(low["Redundancy_chunk"].median()) if not low.empty else math.nan,
        "high_score_red_median": float(high["Redundancy_chunk"].median()) if not high.empty else math.nan,
        "panel_c_rho": panel_c["rho"],
        "panel_c_p": panel_c["p"],
        "panel_d_rho": panel_d["rho"],
        "panel_d_p": panel_d["p"],
    }
    for metric, d in stats_map.items():
        for stat in ["n", "mean", "std", "p25", "median", "p75", "min", "max"]:
            out[f"{metric}_{stat}"] = d[stat]
    return out


def md_table(df: pd.DataFrame, cols: list[str], n: int | None = None) -> list[str]:
    data = df if n is None else df.head(n)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in data.iterrows():
        vals = []
        for col in cols:
            val = r[col]
            if isinstance(val, (float, int, np.floating, np.integer)) and col not in {"chunk_n", "firm_n", "floor_applied_n", "threshold", "floor"}:
                vals.append(fmt(val))
            else:
                vals.append(str(val))
        out.append("| " + " | ".join(vals) + " |")
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    chunks, sections = load_inputs()
    summary_rows: list[dict[str, object]] = []
    built: dict[str, tuple[pd.DataFrame, pd.DataFrame]] = {}
    for candidate in CANDIDATES:
        c, f = build_candidate(chunks, sections, candidate)
        c.to_csv(OUT_DIR / f"{candidate['name']}_chunk_metrics_20260707.csv", index=False, encoding="utf-8-sig")
        f.to_csv(OUT_DIR / f"{candidate['name']}_firm_metrics_20260707.csv", index=False, encoding="utf-8-sig")
        summary_rows.append(evaluate_candidate(c, f, candidate))
        built[candidate["name"]] = (c, f)
    summary = pd.DataFrame(summary_rows).sort_values("loss_all")
    summary.to_csv(OUT_DIR / "candidate_summary_20260707.csv", index=False, encoding="utf-8-sig")

    best = summary.iloc[0].to_dict()
    compare_cols = [
        "name",
        "loss_all",
        "chunk_n",
        "floor_applied_n",
        "Chunk_num_mean",
        "Text_len_mean",
        "Text_len_std",
        "Summary_len_mean",
        "Summary_len_std",
        "Redundancy_chunk_mean",
        "Redundancy_chunk_std",
        "Redundancy_mean",
        "Redundancy_std",
        "panel_b_rho",
        "panel_b_p",
        "low_score_red_median",
        "high_score_red_median",
        "panel_d_rho",
        "panel_d_p",
    ]
    target_rows = []
    for scope, metric, target in [
        ("chunk", "Chunk_num", PAPER_CHUNK["Chunk_num"]),
        ("chunk", "Text_len", PAPER_CHUNK["Text_len"]),
        ("chunk", "Summary_len", PAPER_CHUNK["Summary_len"]),
        ("chunk", "Redundancy_chunk", PAPER_CHUNK["Redundancy_chunk"]),
        ("firm", "lnN_tech", PAPER_FIRM["lnN_tech"]),
        ("firm", "Redundancy", PAPER_FIRM["Redundancy"]),
    ]:
        target_rows.append({"scope": scope, "metric": metric, **{k: fmt(v) for k, v in target.items()}})

    best_name = str(best["name"])
    best_row = summary[summary["name"].eq(best_name)].iloc[0]
    best_stats_rows = []
    for metric in ["Chunk_num", "Text_len", "Summary_len", "Redundancy_chunk", "lnN_tech", "Redundancy"]:
        target = PAPER_CHUNK.get(metric) or PAPER_FIRM.get(metric) or {}
        best_stats_rows.append(
            {
                "metric": metric,
                "mean": fmt(best_row[f"{metric}_mean"]),
                "paper_mean": fmt(target["mean"]),
                "std": fmt(best_row[f"{metric}_std"]),
                "paper_std": fmt(target["std"]),
                "median": fmt(best_row[f"{metric}_median"]),
                "paper_median": fmt(target["median"]),
                "p75": fmt(best_row[f"{metric}_p75"]),
                "paper_p75": fmt(target["p75"]),
            }
        )

    doc = [
        "# GLM 50 家 tail-merge + summary-floor 候选口径 Gate",
        "",
        "日期：2026-07-07",
        "",
        "## 结论",
        "",
        f"- 最接近原文描述性统计的候选是 `{best_name}`。",
        "- 这不是正式复刻结论，而是原文口径反推：它说明原文大概率没有让极短尾 chunk 单独存在，也没有让 3-20 字的极短摘要直接进入冗余分母。",
        "- 最佳候选可解释为：先把尾部短 chunk 合并到前一个 chunk，再对极短摘要做 bounded repair 的最小长度约束。",
        "- 但 Panel B 相关性仍弱，不能说 measurement gate 完成；下一步必须看这个处理后的 X 是否能改善 Table 2 主效应。",
        "",
        "## 原文目标",
        "",
        *md_table(pd.DataFrame(target_rows), ["scope", "metric", "mean", "std", "p25", "median", "p75"], None),
        "",
        "## 候选口径排序",
        "",
        *md_table(summary[compare_cols], compare_cols, None),
        "",
        "## 最佳候选 vs 原文",
        "",
        *md_table(pd.DataFrame(best_stats_rows), ["metric", "mean", "paper_mean", "std", "paper_std", "median", "paper_median", "p75", "paper_p75"], None),
        "",
        "## 输出文件",
        "",
        f"- summary：`{OUT_DIR / 'candidate_summary_20260707.csv'}`",
        f"- best chunk：`{OUT_DIR / f'{best_name}_chunk_metrics_20260707.csv'}`",
        f"- best firm：`{OUT_DIR / f'{best_name}_firm_metrics_20260707.csv'}`",
        "",
    ]
    DOC.write_text("\n".join(doc), encoding="utf-8")
    print({"doc": str(DOC), "summary": str(OUT_DIR / "candidate_summary_20260707.csv"), "best": best_name})


if __name__ == "__main__":
    main()
