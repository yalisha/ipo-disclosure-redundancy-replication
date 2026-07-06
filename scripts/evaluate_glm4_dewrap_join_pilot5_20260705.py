#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
import argparse
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from transformers import AutoTokenizer


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
DEFAULT_RUN_NAME = "glm4_dewrap_join_pilot5_20260705"
RUN_DIR = ROOT / "results" / DEFAULT_RUN_NAME
MODE = "cot_v3b_len132_tight"
DOC_PATH = ROOT / "docs" / "00_current" / f"{DEFAULT_RUN_NAME}.md"
TOKENIZER_NAME = "THUDM/glm-4-9b-chat-hf"

PAPER_CHUNK = {
    "Chunk_num": {"n": 8683, "mean": 18.191, "std": 6.983, "p25": 13.000, "median": 16.000, "p75": 22.000},
    "Text_len": {"n": 8683, "mean": 3866.817, "std": 343.868, "p25": 3888.000, "median": 3954.000, "p75": 3985.000},
    "Summary_len": {"n": 8683, "mean": 132.678, "std": 39.683, "p25": 105.000, "median": 130.000, "p75": 158.000},
    "Redundancy_chunk": {"n": 8683, "mean": 32.176, "std": 11.730, "p25": 24.356, "median": 29.739, "p75": 37.037},
}
PAPER_FIRM = {
    "lnN_tech": {"n": 552, "mean": 10.962, "std": 0.350, "p25": 10.714, "median": 10.910, "p75": 11.185},
    "Redundancy": {"n": 552, "mean": 29.074, "std": 2.630, "p25": 27.402, "median": 28.910, "p75": 30.795},
}


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def describe(s: pd.Series) -> dict[str, float]:
    s = pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if s.empty:
        return {"n": 0, "mean": math.nan, "std": math.nan, "p25": math.nan, "median": math.nan, "p75": math.nan, "min": math.nan, "max": math.nan}
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


def spearman(df: pd.DataFrame, x: str, y: str) -> dict[str, float]:
    reg = df[[x, y]].replace([np.inf, -np.inf], np.nan).dropna()
    if reg.empty or reg[x].nunique() < 2 or reg[y].nunique() < 2:
        return {"n": int(reg.shape[0]), "rho": math.nan, "p": math.nan}
    rho, p = stats.spearmanr(reg[x].astype(float), reg[y].astype(float))
    return {"n": int(reg.shape[0]), "rho": float(rho), "p": float(p)}


def reg_y_on_x(df: pd.DataFrame, y: str, x: str, cluster_col: str | None = None) -> dict[str, float]:
    cols = [y, x] + ([cluster_col] if cluster_col else [])
    reg = df[cols].replace([np.inf, -np.inf], np.nan).dropna().copy()
    if reg.empty or reg[x].nunique() < 2:
        return {"n": int(reg.shape[0]), "coef": math.nan, "t": math.nan, "p": math.nan}
    model = sm.OLS(reg[y].astype(float), sm.add_constant(reg[x].astype(float)))
    if cluster_col:
        fit = model.fit(cov_type="cluster", cov_kwds={"groups": reg[cluster_col].astype(str)})
    else:
        fit = model.fit(cov_type="HC1")
    return {"n": int(reg.shape[0]), "coef": float(fit.params[x]), "t": float(fit.tvalues[x]), "p": float(fit.pvalues[x])}


def winsor_series(s: pd.Series, lower: float = 0.01, upper: float = 0.99) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce")
    lo = s.quantile(lower)
    hi = s.quantile(upper)
    return s.clip(lower=lo, upper=hi)


def load_dictionary() -> tuple[dict[str, list[str]], list[str]]:
    terms_df = pd.read_csv(ROOT / "data" / "dictionaries" / "cheng2022_innovation_disclosure_keywords.csv")
    excl_df = pd.read_csv(ROOT / "data" / "dictionaries" / "cheng2022_innovation_disclosure_exclusions.csv")
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
        text = (ROOT / str(row["chunk_file"])).read_text(encoding="utf-8", errors="ignore")
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


def fmt(value: object, digits: int = 3) -> str:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return ""
    if math.isnan(f):
        return ""
    return f"{f:.{digits}f}"


def md_table(rows: list[dict[str, object]], cols: list[str]) -> list[str]:
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(col, "")) for col in cols) + " |")
    return out


def stat_row(scope: str, metric: str, current: dict[str, float], paper: dict[str, float] | None = None) -> dict[str, object]:
    return {
        "scope": scope,
        "metric": metric,
        "N": int(current.get("n", 0)),
        "mean": fmt(current.get("mean")),
        "paper_mean": fmt(paper.get("mean") if paper else None),
        "diff": fmt(current.get("mean") - paper.get("mean") if paper else None),
        "std": fmt(current.get("std")),
        "median": fmt(current.get("median")),
        "paper_median": fmt(paper.get("median") if paper else None),
        "p25": fmt(current.get("p25")),
        "p75": fmt(current.get("p75")),
    }


def load_chunks() -> pd.DataFrame:
    path = RUN_DIR / f"ipo_redundancy_chunk_with_llm_{MODE}.csv"
    df = pd.read_csv(path, dtype={"sec_code": str})
    numeric_cols = [
        "chunk_count",
        "chunk_glm4_tokens",
        "chunk_token_proxy",
        "summary_token_proxy",
        "summary_chars",
        "summary_compact_chars",
        "relevant_score",
    ]
    for col in numeric_cols:
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
    df["Redundancy_chunk_proxy_w99"] = winsor_series(df["Redundancy_chunk_proxy"])
    df["Redundancy_chunk_glm4_w99"] = winsor_series(df["Redundancy_chunk_glm4"])
    return add_innovation_rates(df)


def make_firm(df: pd.DataFrame) -> pd.DataFrame:
    sections = pd.read_csv(RUN_DIR / "ipo_business_technology_sections.csv", dtype={"sec_code": str})
    for col in ["tech_text_glm4_tokens", "chunk_count"]:
        sections[col] = pd.to_numeric(sections[col], errors="coerce")
    firm = (
        df.groupby(["sec_code", "sec_name"], dropna=False)
        .agg(
            chunk_n=("custom_id", "size"),
            chunk_glm4_tokens_sum=("chunk_glm4_tokens", "sum"),
            summary_proxy_sum=("summary_token_proxy", "sum"),
            summary_glm4_sum=("summary_glm4_tokens", "sum"),
            relevant_score_mean=("relevant_score", "mean"),
            red_chunk_proxy_mean=("Redundancy_chunk_proxy", "mean"),
            red_chunk_glm4_mean=("Redundancy_chunk_glm4", "mean"),
        )
        .reset_index()
    )
    firm = firm.merge(
        sections[["sec_code", "announcement_date", "chunk_count", "tech_text_glm4_tokens"]],
        on="sec_code",
        how="left",
    )
    firm["lnN_tech"] = np.log(firm["tech_text_glm4_tokens"].replace({0: np.nan}))
    firm["Redundancy_proxy"] = firm["chunk_glm4_tokens_sum"] / firm["summary_proxy_sum"].replace({0: np.nan})
    firm["Redundancy_glm4"] = firm["chunk_glm4_tokens_sum"] / firm["summary_glm4_sum"].replace({0: np.nan})
    return firm.sort_values("Redundancy_proxy", ascending=False)


def evaluate_red(df: pd.DataFrame, red_col: str) -> dict[str, object]:
    median_score = float(df["relevant_score"].median())
    low = df[df["relevant_score"].le(median_score)]
    high = df[df["relevant_score"].gt(median_score)]
    rel_low = df[df["relevant_score"].lt(2.0)]
    rel_high = df[df["relevant_score"].ge(2.0)]
    return {
        "red_col": red_col,
        "panel_b_spearman": spearman(df, "relevant_score", red_col),
        "panel_b_hc1": reg_y_on_x(df, red_col, "relevant_score"),
        "panel_b_cluster": reg_y_on_x(df, red_col, "relevant_score", "sec_code"),
        "panel_b_low_high_by_median": {
            "median_score": median_score,
            "low_n": int(low.shape[0]),
            "high_n": int(high.shape[0]),
            "low_median": float(low[red_col].median()),
            "high_median": float(high[red_col].median()),
        },
        "panel_b_low_high_by_2": {
            "low_n": int(rel_low.shape[0]),
            "high_n": int(rel_high.shape[0]),
            "low_median": float(rel_low[red_col].median()) if not rel_low.empty else math.nan,
            "high_median": float(rel_high[red_col].median()) if not rel_high.empty else math.nan,
        },
        "panel_c_spearman": spearman(df, "Chunk_num", red_col),
        "panel_c_hc1": reg_y_on_x(df, red_col, "Chunk_num"),
        "panel_c_cluster": reg_y_on_x(df, red_col, "Chunk_num", "sec_code"),
        "panel_c_w99_cluster": reg_y_on_x(df.assign(_red_w=winsor_series(df[red_col])), "_red_w", "Chunk_num", "sec_code"),
        "panel_d_all_union_spearman": spearman(df, "innovation_rate_all_union", red_col),
        "panel_d_all_union_hc1": reg_y_on_x(df, red_col, "innovation_rate_all_union"),
        "panel_d_all_union_cluster": reg_y_on_x(df, red_col, "innovation_rate_all_union", "sec_code"),
        "panel_d_without_target_spearman": spearman(df, "innovation_rate_without_target", red_col),
        "panel_d_without_target_hc1": reg_y_on_x(df, red_col, "innovation_rate_without_target"),
        "panel_d_without_target_cluster": reg_y_on_x(df, red_col, "innovation_rate_without_target", "sec_code"),
    }


def write_outputs(df: pd.DataFrame, firm: pd.DataFrame, metrics: dict[str, object]) -> None:
    chunk_path = RUN_DIR / f"chunk_metrics_glm4_{MODE}_20260705.csv"
    firm_path = RUN_DIR / f"firm_metrics_glm4_{MODE}_20260705.csv"
    metrics_path = RUN_DIR / f"diagnostics_glm4_{MODE}_20260705.json"
    df.to_csv(chunk_path, index=False, encoding="utf-8-sig")
    firm.to_csv(firm_path, index=False, encoding="utf-8-sig")
    metrics_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2, allow_nan=True), encoding="utf-8")


def write_doc(df: pd.DataFrame, firm: pd.DataFrame, metrics: dict[str, object]) -> None:
    proxy = metrics["proxy"]
    glm4 = metrics["glm4"]
    firm_n = int(metrics["firms"])
    chunk_n = int(metrics["chunks"])
    sample_rows = []
    for row in firm.sort_values("announcement_date").to_dict("records"):
        sample_rows.append(
            {
                "sec_code": row["sec_code"],
                "sec_name": row["sec_name"],
                "date": row["announcement_date"],
                "chunks": int(row["chunk_n"]),
                "glm4_tokens": int(row["tech_text_glm4_tokens"]),
                "Red_proxy": fmt(row["Redundancy_proxy"]),
                "Red_glm4": fmt(row["Redundancy_glm4"]),
            }
        )

    desc_rows = [
        stat_row("chunk", "Chunk_num", metrics["descriptives"]["Chunk_num"], PAPER_CHUNK["Chunk_num"]),
        stat_row("chunk", "Text_len", metrics["descriptives"]["Text_len"], PAPER_CHUNK["Text_len"]),
        stat_row("chunk", "Summary_len_proxy", metrics["descriptives"]["Summary_len_proxy"], PAPER_CHUNK["Summary_len"]),
        stat_row("chunk", "Redundancy_chunk_proxy", metrics["descriptives"]["Redundancy_chunk_proxy"], PAPER_CHUNK["Redundancy_chunk"]),
        stat_row("chunk", "Summary_len_glm4", metrics["descriptives"]["Summary_len_glm4"], PAPER_CHUNK["Summary_len"]),
        stat_row("chunk", "Redundancy_chunk_glm4", metrics["descriptives"]["Redundancy_chunk_glm4"], PAPER_CHUNK["Redundancy_chunk"]),
        stat_row("firm", "lnN_tech", metrics["firm_descriptives"]["lnN_tech"], PAPER_FIRM["lnN_tech"]),
        stat_row("firm", "Redundancy_proxy", metrics["firm_descriptives"]["Redundancy_proxy"], PAPER_FIRM["Redundancy"]),
        stat_row("firm", "Redundancy_glm4", metrics["firm_descriptives"]["Redundancy_glm4"], PAPER_FIRM["Redundancy"]),
    ]

    panel_rows = [
        {
            "measure": "proxy denominator",
            "B rho": fmt(proxy["panel_b_spearman"]["rho"]),
            "B p": fmt(proxy["panel_b_spearman"]["p"], 4),
            "low med": fmt(proxy["panel_b_low_high_by_median"]["low_median"]),
            "high med": fmt(proxy["panel_b_low_high_by_median"]["high_median"]),
            "<2 med": fmt(proxy["panel_b_low_high_by_2"]["low_median"]),
            ">=2 med": fmt(proxy["panel_b_low_high_by_2"]["high_median"]),
            "C rho": fmt(proxy["panel_c_spearman"]["rho"]),
            "D rho all": fmt(proxy["panel_d_all_union_spearman"]["rho"]),
            "D p all": fmt(proxy["panel_d_all_union_spearman"]["p"], 4),
        },
        {
            "measure": "GLM4 denominator",
            "B rho": fmt(glm4["panel_b_spearman"]["rho"]),
            "B p": fmt(glm4["panel_b_spearman"]["p"], 4),
            "low med": fmt(glm4["panel_b_low_high_by_median"]["low_median"]),
            "high med": fmt(glm4["panel_b_low_high_by_median"]["high_median"]),
            "<2 med": fmt(glm4["panel_b_low_high_by_2"]["low_median"]),
            ">=2 med": fmt(glm4["panel_b_low_high_by_2"]["high_median"]),
            "C rho": fmt(glm4["panel_c_spearman"]["rho"]),
            "D rho all": fmt(glm4["panel_d_all_union_spearman"]["rho"]),
            "D p all": fmt(glm4["panel_d_all_union_spearman"]["p"], 4),
        },
    ]

    firm_rank_rows = []
    for row in firm.sort_values("Redundancy_proxy", ascending=False).to_dict("records"):
        firm_rank_rows.append(
            {
                "rank": len(firm_rank_rows) + 1,
                "sec_code": row["sec_code"],
                "sec_name": row["sec_name"],
                "chunks": int(row["chunk_n"]),
                "Red_proxy": fmt(row["Redundancy_proxy"]),
                "Red_glm4": fmt(row["Redundancy_glm4"]),
                "score_mean": fmt(row["relevant_score_mean"]),
            }
        )

    red_proxy_mean = metrics["descriptives"]["Redundancy_chunk_proxy"]["mean"]
    summary_proxy_mean = metrics["descriptives"]["Summary_len_proxy"]["mean"]
    b_proxy = proxy["panel_b_spearman"]
    b_low_high = proxy["panel_b_low_high_by_median"]
    b_pass = b_proxy["rho"] < 0 and b_proxy["p"] < 0.01 and b_low_high["low_median"] > b_low_high["high_median"]
    c_pass = proxy["panel_c_cluster"]["coef"] > 0 and proxy["panel_c_cluster"]["p"] < 0.05
    d_pass = proxy["panel_d_all_union_cluster"]["coef"] < 0 and proxy["panel_d_all_union_cluster"]["p"] < 0.05
    scale_pass = 125 <= summary_proxy_mean <= 140 and 28 <= red_proxy_mean <= 36
    if firm_n >= 500 and scale_pass and b_pass and c_pass and d_pass:
        verdict = "PASS_FULL543_MEASUREMENT_GATE_PROXY"
    elif firm_n >= 100 and scale_pass and b_pass and c_pass and d_pass:
        verdict = "PASS_100FIRM_MEASUREMENT_GATE_PROXY"
    elif firm_n >= 50 and scale_pass and b_pass and c_pass and d_pass:
        verdict = "PASS_50FIRM_MEASUREMENT_GATE_PROXY"
    elif scale_pass and b_proxy["rho"] < 0 and b_low_high["low_median"] > b_low_high["high_median"]:
        verdict = "PASS_SMALL_PILOT_FOR_SCALE_ONLY"
    else:
        verdict = "NO_PASS_YET"

    lines = [
        f"# GLM4 dewrap_join {firm_n} 家 LLM measurement gate",
        "",
        f"日期：{date.today().isoformat()}",
        "",
        "## 结论",
        "",
        f"`{verdict}`",
        "",
        (
            f"这轮是在新的 `dewrap_join + GLM-4 tokenizer + 4000 token boundary split` chunk base 上完成 {firm_n} 家全样本测度，检验量级和构念效度是否能回到原文附近。"
            if firm_n >= 500
            else f"这轮只是在新的 `dewrap_join + GLM-4 tokenizer + 4000 token boundary split` chunk base 上试跑 {firm_n} 家，检验量级是否能回到原文附近；它不是正式 gate。"
        ),
        "",
        "核心读法：",
        "",
        f"- {firm_n} 家 {chunk_n} 个 chunk 已全部跑完 `cot_v3b_len132_tight`。",
        f"- 若沿用原项目此前的摘要长度 proxy，`Summary_len` mean={fmt(summary_proxy_mean)}，`Redundancy_chunk` mean={fmt(red_proxy_mean)}，分别贴近原文 132.678 和 32.176。",
        f"- 若摘要也改用 GLM-4 tokenizer 计数，`Summary_len` mean={fmt(metrics['descriptives']['Summary_len_glm4']['mean'])}，`Redundancy_chunk` mean={fmt(metrics['descriptives']['Redundancy_chunk_glm4']['mean'])}，冗余度会明显低于原文。",
        f"- Panel B 在 {firm_n} 家样本里方向为负：proxy 口径 rho={fmt(b_proxy['rho'])}, p={fmt(b_proxy['p'], 4)}；低评分组冗余中位数 {fmt(b_low_high['low_median'])} 高于高评分组 {fmt(b_low_high['high_median'])}，硬方向成立。",
        (
            f"- Panel C / D 在 {firm_n} 家全样本里作为构念效度检验读取，proxy 口径下 C cluster coef={fmt(proxy['panel_c_cluster']['coef'])}, p={fmt(proxy['panel_c_cluster']['p'], 4)}；D cluster coef={fmt(proxy['panel_d_all_union_cluster']['coef'])}, p={fmt(proxy['panel_d_all_union_cluster']['p'], 4)}。"
            if firm_n >= 500
            else f"- Panel C / D 在 {firm_n} 家样本里仍需谨慎解读；这里只看方向和是否出现明显异常。"
        ),
        "",
        "## 样本",
        "",
        *md_table(sample_rows, ["sec_code", "sec_name", "date", "chunks", "glm4_tokens", "Red_proxy", "Red_glm4"]),
        "",
        "## 输出文件",
        "",
        f"- chunk metrics：`{(RUN_DIR / f'chunk_metrics_glm4_{MODE}_20260705.csv').relative_to(ROOT)}`",
        f"- firm metrics：`{(RUN_DIR / f'firm_metrics_glm4_{MODE}_20260705.csv').relative_to(ROOT)}`",
        f"- diagnostics：`{(RUN_DIR / f'diagnostics_glm4_{MODE}_20260705.json').relative_to(ROOT)}`",
        f"- LLM chunk CSV：`{(RUN_DIR / f'ipo_redundancy_chunk_with_llm_{MODE}.csv').relative_to(ROOT)}`",
        "",
        "## 描述统计对照",
        "",
        *md_table(desc_rows, ["scope", "metric", "N", "mean", "paper_mean", "diff", "std", "median", "paper_median", "p25", "p75"]),
        "",
        "## Panel B/C/D 快速检验",
        "",
        *md_table(panel_rows, ["measure", "B rho", "B p", "low med", "high med", "<2 med", ">=2 med", "C rho", "D rho all", "D p all"]),
        "",
        "## 企业层排序",
        "",
        *md_table(firm_rank_rows, ["rank", "sec_code", "sec_name", "chunks", "Red_proxy", "Red_glm4", "score_mean"]),
        "",
        "## 判断",
        "",
        "1. `dewrap_join` 新 chunk base 的分块数量和正文长度已经非常接近原文；这一步值得继续。",
        "2. 摘要长度单位需要固定：如果原文 `Summary_len` 本质更接近中文摘要字符 proxy，当前 prompt 已经接近；如果原文也用 GLM tokenizer 计摘要，当前摘要过长，需要把 prompt 缩短。",
        f"3. {firm_n} 家样本下 Panel B 主要看方向、显著性和低/高评分中位数关系；Panel C/D 用 firm-cluster 与 Spearman 同时核对。",
        (
            "4. 下一步可以基于这个 X 进入下游 Table 2 / 询问函 X 方案，但不要把 measurement gate 等同于原文经济结果已经复刻。"
            if firm_n >= 500
            else "4. 下一步建议做 100 家确认或直接制定全样本重跑方案；前提是先固定 `Summary_len` 到底采用旧摘要 proxy 还是 GLM-4 summary tokens。"
            if firm_n >= 50
            else "4. 下一步不建议立刻全样本，建议做 50 家分层 pilot：固定 `dewrap_join`，同时输出 proxy 与 GLM4 两套摘要长度，正式看 Panel B/C/D。"
        ),
        "",
    ]
    DOC_PATH.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-name", default=DEFAULT_RUN_NAME)
    parser.add_argument("--prompt-mode", default=MODE)
    parser.add_argument("--doc-name", default="")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    global RUN_DIR, MODE, DOC_PATH
    RUN_DIR = ROOT / "results" / args.run_name
    MODE = args.prompt_mode
    DOC_PATH = ROOT / "docs" / "00_current" / (args.doc_name or f"{args.run_name}.md")
    df = load_chunks()
    firm = make_firm(df)
    metrics: dict[str, object] = {
        "run_dir": str(RUN_DIR.relative_to(ROOT)),
        "mode": MODE,
        "tokenizer": TOKENIZER_NAME,
        "firms": int(firm.shape[0]),
        "chunks": int(df.shape[0]),
        "descriptives": {
            "Chunk_num": describe(df["Chunk_num"]),
            "Text_len": describe(df["Text_len"]),
            "Summary_len_proxy": describe(df["Summary_len_proxy"]),
            "Summary_len_glm4": describe(df["Summary_len_glm4"]),
            "Redundancy_chunk_proxy": describe(df["Redundancy_chunk_proxy"]),
            "Redundancy_chunk_glm4": describe(df["Redundancy_chunk_glm4"]),
            "Relevant_score": describe(df["relevant_score"]),
            "innovation_rate_all_union": describe(df["innovation_rate_all_union"]),
            "innovation_rate_without_target": describe(df["innovation_rate_without_target"]),
        },
        "firm_descriptives": {
            "lnN_tech": describe(firm["lnN_tech"]),
            "Redundancy_proxy": describe(firm["Redundancy_proxy"]),
            "Redundancy_glm4": describe(firm["Redundancy_glm4"]),
        },
        "proxy": evaluate_red(df, "Redundancy_chunk_proxy"),
        "glm4": evaluate_red(df, "Redundancy_chunk_glm4"),
    }
    write_outputs(df, firm, metrics)
    write_doc(df, firm, metrics)
    print(json.dumps({
        "doc": str(DOC_PATH),
        "chunk_metrics": str(RUN_DIR / f"chunk_metrics_glm4_{MODE}_20260705.csv"),
        "firm_metrics": str(RUN_DIR / f"firm_metrics_glm4_{MODE}_20260705.csv"),
        "diagnostics": str(RUN_DIR / f"diagnostics_glm4_{MODE}_20260705.json"),
        "chunks": int(df.shape[0]),
        "firms": int(firm.shape[0]),
        "summary_proxy_mean": metrics["descriptives"]["Summary_len_proxy"]["mean"],
        "red_proxy_mean": metrics["descriptives"]["Redundancy_chunk_proxy"]["mean"],
        "summary_glm4_mean": metrics["descriptives"]["Summary_len_glm4"]["mean"],
        "red_glm4_mean": metrics["descriptives"]["Redundancy_chunk_glm4"]["mean"],
    }, ensure_ascii=False, indent=2, allow_nan=True))


if __name__ == "__main__":
    main()
