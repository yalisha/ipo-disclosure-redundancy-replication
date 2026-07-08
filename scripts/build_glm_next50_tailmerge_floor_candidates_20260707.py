#!/usr/bin/env python3
from __future__ import annotations

import math
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from transformers import AutoTokenizer


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
PROMPT_MODE = "cot_v3b_len132_tight"
TOKENIZER_NAME = "THUDM/glm-4-9b-chat-hf"

SHARD_RUNS = [
    "siliconflow_glm4_32b_table2_next50_shard1_20260707",
    "siliconflow_glm4_32b_table2_next50_shard2_20260707",
    "siliconflow_glm4_32b_table2_next50_shard3_20260707",
]
MERGED_RUN = "siliconflow_glm4_32b_table2_next50_merged_20260707"
RUN_DIR = ROOT / "results" / MERGED_RUN
OUT_DIR = ROOT / "results/glm_next50_tailmerge_floor_candidates_20260707"
DOC = ROOT / "docs/00_current/siliconflow_glm4_32b_table2_next50_20260707.md"
PREV_SUMMARY = ROOT / "results/glm50_tailmerge_floor_candidates_20260707/candidate_summary_20260707.csv"

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
    {"name": "proxy_tailmerge1600_floor50", "unit": "Summary_len_proxy", "process": "merge_tail", "threshold": 1600, "floor": 50},
    {"name": "proxy_tailmerge1700_floor50", "unit": "Summary_len_proxy", "process": "merge_tail", "threshold": 1700, "floor": 50},
    {"name": "proxy_tailmerge2000_floor50", "unit": "Summary_len_proxy", "process": "merge_tail", "threshold": 2000, "floor": 50},
    {"name": "proxy_tailmerge2000_floor60", "unit": "Summary_len_proxy", "process": "merge_tail", "threshold": 2000, "floor": 60},
    {"name": "proxy_tailmerge2000_floor80", "unit": "Summary_len_proxy", "process": "merge_tail", "threshold": 2000, "floor": 80},
    {"name": "proxy_tailmerge2000_floor100", "unit": "Summary_len_proxy", "process": "merge_tail", "threshold": 2000, "floor": 100},
    {"name": "glm4token_tailmerge1500_floor0", "unit": "Summary_len_glm4", "process": "merge_tail", "threshold": 1500, "floor": 0},
    {"name": "glm4token_tailmerge2000_floor0", "unit": "Summary_len_glm4", "process": "merge_tail", "threshold": 2000, "floor": 0},
]


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


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


def md_table(df: pd.DataFrame, cols: list[str], n: int | None = None) -> list[str]:
    data = df if n is None else df.head(n)
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in data.iterrows():
        vals = []
        for col in cols:
            val = r[col]
            if isinstance(val, (float, int, np.floating, np.integer)) and col not in {
                "chunk_n",
                "firm_n",
                "floor_applied_n",
                "threshold",
                "floor",
            }:
                vals.append(fmt(val))
            else:
                vals.append(str(val))
        out.append("| " + " | ".join(vals) + " |")
    return out


def merge_shards() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    file_names = [
        f"ipo_redundancy_chunk_with_llm_{PROMPT_MODE}.csv",
        f"ipo_redundancy_chunk_with_llm_{PROMPT_MODE}_completed_only.csv",
        f"ipo_redundancy_firm_level_{PROMPT_MODE}.csv",
        f"ipo_redundancy_firm_level_{PROMPT_MODE}_completed_only.csv",
        "ipo_business_technology_chunks.csv",
        "ipo_business_technology_sections.csv",
        "summary_comparison_vs_source_20260707.csv",
        "siliconflow_call_log_20260707.csv",
        "siliconflow_call_log_all_20260707.csv",
        "siliconflow_glm4_32b_summary_stats_20260707.csv",
    ]
    for file_name in file_names:
        parts = []
        for shard in SHARD_RUNS:
            path = ROOT / "results" / shard / file_name
            if not path.exists():
                continue
            part = pd.read_csv(path, dtype={"sec_code": str})
            part["source_shard"] = shard
            parts.append(part)
        if parts:
            out = pd.concat(parts, ignore_index=True)
            if "custom_id" in out.columns:
                out = out.drop_duplicates("custom_id", keep="last")
            elif "sec_code" in out.columns:
                out = out.drop_duplicates(["sec_code", "source_shard"], keep="last")
            out.to_csv(RUN_DIR / file_name, index=False, encoding="utf-8-sig")

    jsonl_out = RUN_DIR / f"ipo_redundancy_llm_outputs_{PROMPT_MODE}.jsonl"
    seen: set[str] = set()
    with jsonl_out.open("w", encoding="utf-8") as fout:
        for shard in SHARD_RUNS:
            path = ROOT / "results" / shard / f"ipo_redundancy_llm_outputs_{PROMPT_MODE}.jsonl"
            if not path.exists():
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                custom_id = ""
                try:
                    custom_id = str(json.loads(line).get("custom_id", ""))
                except Exception:
                    pass
                if custom_id and custom_id in seen:
                    continue
                if custom_id:
                    seen.add(custom_id)
                fout.write(line + "\n")


def load_dictionary() -> tuple[dict[str, list[str]], list[str]]:
    terms_df = pd.read_csv(ROOT / "data/dictionaries/cheng2022_innovation_disclosure_keywords.csv")
    excl_df = pd.read_csv(ROOT / "data/dictionaries/cheng2022_innovation_disclosure_exclusions.csv")
    grouped: dict[str, list[str]] = {}
    for category, group in terms_df.groupby("category"):
        terms = sorted(set(str(x) for x in group["term"].dropna() if str(x).strip()), key=len, reverse=True)
        grouped[str(category)] = terms
    exclusions = sorted(set(str(x) for x in excl_df["exclude_term"].dropna() if str(x).strip()), key=len, reverse=True)
    return grouped, exclusions


def count_terms(text: str, terms: list[str], exclusions: list[str]) -> int:
    compact = compact_text(text)
    for term in exclusions:
        compact = compact.replace(term, "")
    return int(sum(compact.count(term) for term in terms))


def add_innovation_rates(df: pd.DataFrame) -> pd.DataFrame:
    grouped, exclusions = load_dictionary()
    all_terms = sorted(set(term for terms in grouped.values() for term in terms), key=len, reverse=True)
    without_target = sorted(
        set(term for category, terms in grouped.items() if category != "innovation_target" for term in terms),
        key=len,
        reverse=True,
    )
    rows = []
    for row in df.to_dict("records"):
        chunk_path = ROOT / str(row["chunk_file"])
        text = chunk_path.read_text(encoding="utf-8", errors="ignore") if chunk_path.exists() else ""
        token = float(row["chunk_glm4_tokens"]) if not pd.isna(row["chunk_glm4_tokens"]) else math.nan
        all_count = count_terms(text, all_terms, exclusions)
        no_target_count = count_terms(text, without_target, exclusions)
        rows.append(
            {
                "custom_id": row["custom_id"],
                "innovation_terms_all_union": all_count,
                "innovation_terms_without_target": no_target_count,
                "innovation_rate_all_union": all_count / token * 1000 if token else math.nan,
                "innovation_rate_without_target": no_target_count / token * 1000 if token else math.nan,
            }
        )
    return df.merge(pd.DataFrame(rows), on="custom_id", how="left")


def build_chunk_metrics() -> pd.DataFrame:
    chunk_path = RUN_DIR / f"ipo_redundancy_chunk_with_llm_{PROMPT_MODE}.csv"
    df = pd.read_csv(chunk_path, dtype={"sec_code": str, "custom_id": str})
    numeric = [
        "chunk_count",
        "chunk_index",
        "chunk_glm4_tokens",
        "Text_len",
        "Chunk_num",
        "chunk_token_proxy",
        "summary_token_proxy",
        "summary_chars",
        "summary_compact_chars",
        "relevant_score",
        "sentence_count",
        "n0",
        "n1",
        "n2",
        "n3",
        "n4",
        "n5",
    ]
    for col in numeric:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME, trust_remote_code=True)
    df["summary_glm4_tokens"] = [
        len(tokenizer.encode(str(text), add_special_tokens=False)) for text in df["summary_text"].fillna("")
    ]
    df["Summary_len_proxy"] = df["summary_token_proxy"]
    df["Summary_len_glm4"] = df["summary_glm4_tokens"]
    df["Text_len"] = df["chunk_glm4_tokens"]
    df["Chunk_num"] = df["chunk_count"]
    df["Redundancy_chunk_proxy"] = df["chunk_glm4_tokens"] / df["summary_token_proxy"].replace({0: np.nan})
    df["Redundancy_chunk_glm4"] = df["chunk_glm4_tokens"] / df["summary_glm4_tokens"].replace({0: np.nan})
    df = add_innovation_rates(df)
    df.to_csv(RUN_DIR / f"chunk_metrics_glm4_{PROMPT_MODE}_20260707.csv", index=False, encoding="utf-8-sig")
    return df


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


def build_candidate(chunks: pd.DataFrame, candidate: dict[str, object]) -> tuple[pd.DataFrame, pd.DataFrame]:
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
    firm["lnN_tech"] = np.log(firm["text_sum"].replace({0: np.nan}))
    firm["Redundancy"] = firm["text_sum"] / firm["summary_sum"].replace({0: np.nan})
    return c, firm


def stat_loss(stats_dict: dict[str, float], target: dict[str, float]) -> float:
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
        "loss_chunk_num": stat_loss(stats_map["Chunk_num"], PAPER_CHUNK["Chunk_num"]),
        "loss_text": stat_loss(stats_map["Text_len"], PAPER_CHUNK["Text_len"]),
        "loss_summary": stat_loss(stats_map["Summary_len"], PAPER_CHUNK["Summary_len"]),
        "loss_red_chunk": stat_loss(stats_map["Redundancy_chunk"], PAPER_CHUNK["Redundancy_chunk"]),
        "loss_lnn": stat_loss(stats_map["lnN_tech"], PAPER_FIRM["lnN_tech"]),
        "loss_red_firm": stat_loss(stats_map["Redundancy"], PAPER_FIRM["Redundancy"]),
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


def firm_list(chunks: pd.DataFrame) -> str:
    firms = chunks[["sec_code", "sec_name"]].drop_duplicates().sort_values("sec_code")
    return "、".join(f"{r.sec_code} {r.sec_name}" for r in firms.itertuples(index=False))


def write_doc(chunks: pd.DataFrame, summary: pd.DataFrame) -> None:
    DOC.parent.mkdir(parents=True, exist_ok=True)
    best = summary.iloc[0].to_dict()
    best_name = str(best["name"])
    prev_best_line = "未读取到上一批 GLM50 summary。"
    if PREV_SUMMARY.exists():
        prev = pd.read_csv(PREV_SUMMARY)
        if not prev.empty:
            p = prev.sort_values("loss_all").iloc[0]
            prev_best_line = (
                f"上一批 GLM50 最佳候选为 `{p['name']}`，"
                f"Summary_len mean={fmt(p['Summary_len_mean'])}，"
                f"Redundancy_chunk mean={fmt(p['Redundancy_chunk_mean'])}，"
                f"PanelB rho={fmt(p['panel_b_rho'])}。"
            )

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
        "panel_c_rho",
        "panel_d_rho",
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

    best_stats_rows = []
    best_row = summary[summary["name"].eq(best_name)].iloc[0]
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

    raw = summary[summary["name"].eq("raw_proxy")].iloc[0]
    doc = [
        "# SiliconFlow GLM-4-32B Table2 next50 测度与候选口径",
        "",
        "日期：2026-07-07",
        "",
        "## 结论",
        "",
        f"- 本轮新增 50 家已跑完并合并：chunk={chunks.shape[0]}，firm={chunks['sec_code'].nunique()}。",
        "- 稳定运行方式是 3 个 source shard 顺序跑、batch-size=1；batch-size=2 会漏返回 custom_id，平行跑会触发 TPM。",
        f"- 原始 GLM 摘要 proxy 均值={fmt(raw['Summary_len_mean'])}，Redundancy_chunk 均值={fmt(raw['Redundancy_chunk_mean'])}。",
        f"- 最接近原文描述性统计的候选是 `{best_name}`；{prev_best_line}",
        "- 这支持“GLM-only + 尾部短 chunk 合并 + 极短摘要下限”这一 measurement 方向，但还没有证明 Table 2 主效应能复刻。",
        "- 下一步应把上一批 GLM50 与本轮 next50 合并成 GLM100，先看描述统计稳定性，再接 Table 2 主效应。",
        "",
        "## 样本",
        "",
        firm_list(chunks),
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
        *md_table(
            pd.DataFrame(best_stats_rows),
            ["metric", "mean", "paper_mean", "std", "paper_std", "median", "paper_median", "p75", "paper_p75"],
            None,
        ),
        "",
        "## 输出文件",
        "",
        f"- merged run：`{RUN_DIR}`",
        f"- chunk metrics：`{RUN_DIR / f'chunk_metrics_glm4_{PROMPT_MODE}_20260707.csv'}`",
        f"- candidates：`{OUT_DIR}`",
        f"- candidate summary：`{OUT_DIR / 'candidate_summary_20260707.csv'}`",
        f"- best chunk：`{OUT_DIR / f'{best_name}_chunk_metrics_20260707.csv'}`",
        f"- best firm：`{OUT_DIR / f'{best_name}_firm_metrics_20260707.csv'}`",
        "",
        "## 备注",
        "",
        "- 本轮没有再调用 API；这里只做 shard 合并、GLM-token 计数、创新词典计数和候选口径评估。",
        "- 旧的 `results/siliconflow_glm4_32b_table2_next50_20260707` 是中途试跑残留，不作为正式结果。",
        "",
    ]
    DOC.write_text("\n".join(doc), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    merge_shards()
    chunks = build_chunk_metrics()

    summary_rows: list[dict[str, object]] = []
    for candidate in CANDIDATES:
        c, f = build_candidate(chunks, candidate)
        c.to_csv(OUT_DIR / f"{candidate['name']}_chunk_metrics_20260707.csv", index=False, encoding="utf-8-sig")
        f.to_csv(OUT_DIR / f"{candidate['name']}_firm_metrics_20260707.csv", index=False, encoding="utf-8-sig")
        summary_rows.append(evaluate_candidate(c, f, candidate))

    summary = pd.DataFrame(summary_rows).sort_values("loss_all")
    summary.to_csv(OUT_DIR / "candidate_summary_20260707.csv", index=False, encoding="utf-8-sig")
    write_doc(chunks, summary)
    print({"doc": str(DOC), "summary": str(OUT_DIR / "candidate_summary_20260707.csv"), "best": str(summary.iloc[0]["name"])})


if __name__ == "__main__":
    main()
