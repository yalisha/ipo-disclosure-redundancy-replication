#!/usr/bin/env python3
"""Prepare and evaluate the 50-firm summary-length calibration pilot."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
RUN_DIR = ROOT / "results" / "star_token_proxy_full_2019_2023_20260702"
MASTER_PATH = (
    ROOT
    / "results"
    / "original_paper_table2_probe_full_2019_2023_csmar_patent_20260702"
    / "original_paper_table2_probe_master_full_2019_2023_csmar_patent_20260702.csv"
)
OUT_DIR = ROOT / "results" / "summary_len_calibration_50_20260703"
DOC_PATH = ROOT / "docs" / "00_current" / "cot_v3b_len132_50firm_calibration_20260703.md"
BASELINE_MODE = "cot_v3b_scoregate_targeted_full_2019_2023"
PILOT_MODE = "cot_v3b_len132_tight"
ATTEMPT_MODES = ["cot_v3b_len132", "cot_v3b_len132_bounded", "cot_v3b_len132_tight"]
QUOTAS = {2019: 5, 2020: 15, 2021: 17, 2022: 13}
ANCHOR_SAMPLE_PATH: Path | None = None


def sample_n() -> int:
    return int(sum(QUOTAS.values()))


def sample_stem() -> str:
    return f"sample_{sample_n()}"


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def describe(s: pd.Series) -> dict[str, float]:
    s = pd.to_numeric(s, errors="coerce").dropna()
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


def reg_y_on_x(df: pd.DataFrame, y: str, x: str, cluster_col: str | None = None) -> dict[str, float]:
    reg = df[[y, x] + ([cluster_col] if cluster_col else [])].dropna().copy()
    if reg.empty or reg[x].nunique() < 2:
        return {"n": int(reg.shape[0]), "coef": math.nan, "t": math.nan, "p": math.nan}
    model = sm.OLS(reg[y].astype(float), sm.add_constant(reg[x].astype(float)))
    if cluster_col:
        fit = model.fit(cov_type="cluster", cov_kwds={"groups": reg[cluster_col].astype(str)})
    else:
        fit = model.fit(cov_type="HC1")
    return {
        "n": int(reg.shape[0]),
        "coef": float(fit.params[x]),
        "t": float(fit.tvalues[x]),
        "p": float(fit.pvalues[x]),
    }


def spearman(df: pd.DataFrame, x: str, y: str) -> dict[str, float]:
    reg = df[[x, y]].dropna().copy()
    if reg.empty or reg[x].nunique() < 2 or reg[y].nunique() < 2:
        return {"n": int(reg.shape[0]), "rho": math.nan, "p": math.nan}
    rho, p = stats.spearmanr(reg[x].astype(float), reg[y].astype(float))
    return {"n": int(reg.shape[0]), "rho": float(rho), "p": float(p)}


def quantile_pick(group: pd.DataFrame, n: int) -> pd.DataFrame:
    group = group.sort_values(["Redundancy", "sec_code"]).reset_index(drop=True)
    if len(group) <= n:
        return group
    positions = np.linspace(0, len(group) - 1, n).round().astype(int)
    positions = sorted(dict.fromkeys(int(x) for x in positions))
    picked = group.iloc[positions].copy()
    if len(picked) < n:
        remaining = group.drop(index=positions).copy()
        need = n - len(picked)
        picked = pd.concat([picked, remaining.iloc[:need]], ignore_index=True)
    return picked.sort_values(["listing_year", "Redundancy", "sec_code"]).reset_index(drop=True)


def prepare_sample() -> pd.DataFrame:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    master = pd.read_csv(MASTER_PATH, dtype={"sec_code": str, "code": str})
    sections = pd.read_csv(RUN_DIR / "ipo_business_technology_sections.csv", dtype={"sec_code": str})
    available = set(sections["sec_code"].astype(str))
    master["listing_year"] = pd.to_numeric(master["listing_year"], errors="coerce")
    master["Redundancy"] = pd.to_numeric(master["Redundancy"], errors="coerce")
    master["chunk_count"] = pd.to_numeric(master["chunk_count"], errors="coerce")
    pool = master[
        master["sec_code"].astype(str).isin(available)
        & master["listing_year"].isin(list(QUOTAS))
        & master["Redundancy"].notna()
    ].copy()

    anchor = pd.DataFrame()
    if ANCHOR_SAMPLE_PATH and ANCHOR_SAMPLE_PATH.exists():
        anchor_codes = pd.read_csv(ANCHOR_SAMPLE_PATH, dtype={"sec_code": str})["sec_code"].astype(str)
        anchor = pool[pool["sec_code"].astype(str).isin(set(anchor_codes))].copy()

    picked_parts = []
    for year, quota in QUOTAS.items():
        year_anchor = anchor[anchor["listing_year"].eq(year)].copy()
        need = max(0, quota - len(year_anchor))
        year_pool = pool[
            pool["listing_year"].eq(year)
            & ~pool["sec_code"].astype(str).isin(set(year_anchor["sec_code"].astype(str)))
        ].copy()
        picked_parts.append(pd.concat([year_anchor, quantile_pick(year_pool, need)], ignore_index=True))
    picked = pd.concat(picked_parts, ignore_index=True)
    picked = picked.sort_values(["listing_year", "Redundancy", "sec_code"]).reset_index(drop=True)
    cols = [
        "sec_code",
        "sec_name",
        "listing_year",
        "announcement_id",
        "Redundancy",
        "chunk_count",
        "FInvention",
        "BHAR",
        "FSales_Growth",
    ]
    sample = picked[[c for c in cols if c in picked.columns]].copy()
    sample.to_csv(OUT_DIR / f"{sample_stem()}_firms_20260703.csv", index=False, encoding="utf-8-sig")
    (OUT_DIR / f"{sample_stem()}_codes_20260703.txt").write_text(
        ",".join(sample["sec_code"].astype(str).tolist()) + "\n",
        encoding="utf-8",
    )
    return sample


def load_mode_chunks(mode: str, sample_codes: set[str]) -> pd.DataFrame | None:
    path = RUN_DIR / f"ipo_redundancy_chunk_with_llm_{mode}_completed_only.csv"
    if not path.exists():
        return None
    df = pd.read_csv(path, dtype={"sec_code": str})
    df = df[df["sec_code"].astype(str).isin(sample_codes)].copy()
    for col in [
        "chunk_token_proxy",
        "summary_token_proxy",
        "chunk_count",
        "relevant_score",
        "summary_compact_chars",
        "summary_chars",
        "summary_sentence_count",
        "high_score_count",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["Redundancy_chunk"] = df["chunk_token_proxy"] / df["summary_token_proxy"].replace({0: np.nan})
    return df


def load_dictionary() -> tuple[dict[str, list[str]], list[str]]:
    terms_df = pd.read_csv(ROOT / "data" / "dictionaries" / "cheng2022_innovation_disclosure_keywords.csv")
    excl_df = pd.read_csv(ROOT / "data" / "dictionaries" / "cheng2022_innovation_disclosure_exclusions.csv")
    grouped: dict[str, list[str]] = {}
    for category, g in terms_df.groupby("category"):
        terms = sorted(set(str(x) for x in g["term"].dropna() if str(x).strip()), key=len, reverse=True)
        grouped[str(category)] = terms
    exclusions = sorted(set(str(x) for x in excl_df["exclude_term"].dropna() if str(x).strip()), key=len, reverse=True)
    return grouped, exclusions


def count_terms(text: str, terms: list[str], exclusions: list[str]) -> int:
    compact = compact_text(text)
    for term in exclusions:
        compact = compact.replace(term, "")
    return int(sum(compact.count(term) for term in terms))


def add_innovation_rates(df: pd.DataFrame, mode: str) -> pd.DataFrame:
    grouped, exclusions = load_dictionary()
    all_terms = sorted(set(term for terms in grouped.values() for term in terms), key=len, reverse=True)
    without_target = sorted(
        set(term for cat, terms in grouped.items() if cat != "innovation_target" for term in terms),
        key=len,
        reverse=True,
    )
    rows = []
    for row in df.to_dict("records"):
        chunk_path = ROOT / str(row["chunk_file"])
        text = chunk_path.read_text(encoding="utf-8", errors="ignore")
        token = float(row.get("chunk_token_proxy") or np.nan)
        all_count = count_terms(text, all_terms, exclusions)
        no_target_count = count_terms(text, without_target, exclusions)
        rows.append(
            {
                "custom_id": row["custom_id"],
                "innovation_terms_all_union": all_count,
                "innovation_terms_without_target": no_target_count,
                "innovation_rate_all_union": all_count / token * 1000 if token else np.nan,
                "innovation_rate_without_target": no_target_count / token * 1000 if token else np.nan,
            }
        )
    out = df.merge(pd.DataFrame(rows), on="custom_id", how="left")
    out.to_csv(OUT_DIR / f"chunk_metrics_{mode}_20260703.csv", index=False, encoding="utf-8-sig")
    return out


def evaluate_mode(mode: str, sample: pd.DataFrame) -> dict[str, object] | None:
    sample_codes = set(sample["sec_code"].astype(str))
    df = load_mode_chunks(mode, sample_codes)
    if df is None or df.empty:
        return None
    df = add_innovation_rates(df, mode)

    median_score = float(df["relevant_score"].median()) if "relevant_score" in df.columns else math.nan
    low = df[df["relevant_score"].le(median_score)] if "relevant_score" in df.columns else pd.DataFrame()
    high = df[df["relevant_score"].gt(median_score)] if "relevant_score" in df.columns else pd.DataFrame()
    rel_low = df[df["relevant_score"].lt(2.0)] if "relevant_score" in df.columns else pd.DataFrame()
    rel_high = df[df["relevant_score"].ge(2.0)] if "relevant_score" in df.columns else pd.DataFrame()
    p99 = float(df["Redundancy_chunk"].quantile(0.99))
    df_drop_p99 = df[df["Redundancy_chunk"].le(p99)].copy()

    firm = (
        df.groupby(["sec_code", "sec_name"], dropna=False)
        .agg(
            chunk_count=("custom_id", "size"),
            original_length_units=("chunk_token_proxy", "sum"),
            summary_length_units=("summary_token_proxy", "sum"),
            relevant_score_mean=("relevant_score", "mean"),
        )
        .reset_index()
    )
    firm["Redundancy"] = firm["original_length_units"] / firm["summary_length_units"].replace({0: np.nan})
    firm = firm.sort_values("Redundancy", ascending=False)
    firm.to_csv(OUT_DIR / f"firm_ranking_{mode}_20260703.csv", index=False, encoding="utf-8-sig")

    metrics: dict[str, object] = {
        "mode": mode,
        "firm_n": int(firm.shape[0]),
        "chunk_n": int(df.shape[0]),
        "text_len": describe(df["chunk_token_proxy"]),
        "summary_len": describe(df["summary_token_proxy"]),
        "redundancy_chunk": describe(df["Redundancy_chunk"]),
        "relevant_score": describe(df["relevant_score"]) if "relevant_score" in df.columns else {},
        "firm_redundancy": describe(firm["Redundancy"]),
        "panel_b_spearman": spearman(df, "relevant_score", "Redundancy_chunk") if "relevant_score" in df.columns else {},
        "panel_b_ols_hc1": reg_y_on_x(df, "Redundancy_chunk", "relevant_score"),
        "panel_b_ols_cluster": reg_y_on_x(df, "Redundancy_chunk", "relevant_score", "sec_code"),
        "panel_b_low_high_by_median": {
            "median_score": median_score,
            "low_median_redundancy": float(low["Redundancy_chunk"].median()) if not low.empty else math.nan,
            "high_median_redundancy": float(high["Redundancy_chunk"].median()) if not high.empty else math.nan,
        },
        "panel_b_low_high_by_2": {
            "low_lt_2_median_redundancy": float(rel_low["Redundancy_chunk"].median()) if not rel_low.empty else math.nan,
            "high_ge_2_median_redundancy": float(rel_high["Redundancy_chunk"].median()) if not rel_high.empty else math.nan,
        },
        "panel_c_raw_hc1": reg_y_on_x(df, "Redundancy_chunk", "chunk_count"),
        "panel_c_raw_cluster": reg_y_on_x(df, "Redundancy_chunk", "chunk_count", "sec_code"),
        "panel_c_drop_p99_cluster": reg_y_on_x(df_drop_p99, "Redundancy_chunk", "chunk_count", "sec_code"),
        "panel_c_spearman": spearman(df, "chunk_count", "Redundancy_chunk"),
        "panel_d_all_union_hc1": reg_y_on_x(df, "Redundancy_chunk", "innovation_rate_all_union"),
        "panel_d_all_union_cluster": reg_y_on_x(df, "Redundancy_chunk", "innovation_rate_all_union", "sec_code"),
        "panel_d_all_union_spearman": spearman(df, "innovation_rate_all_union", "Redundancy_chunk"),
        "panel_d_without_target_hc1": reg_y_on_x(df, "Redundancy_chunk", "innovation_rate_without_target"),
        "panel_d_without_target_cluster": reg_y_on_x(df, "Redundancy_chunk", "innovation_rate_without_target", "sec_code"),
        "panel_d_without_target_spearman": spearman(df, "innovation_rate_without_target", "Redundancy_chunk"),
    }
    (OUT_DIR / f"metrics_{mode}_20260703.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, allow_nan=True),
        encoding="utf-8",
    )
    return metrics


def fmt(value: object, digits: int = 3) -> str:
    if value is None:
        return ""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return str(value)
    if math.isnan(f):
        return ""
    return f"{f:.{digits}f}"


def metric_row(label: str, metric: str, baseline: dict[str, object] | None, pilot: dict[str, object] | None) -> str:
    b = baseline.get(metric, {}) if baseline else {}
    p = pilot.get(metric, {}) if pilot else {}
    if isinstance(b, dict) and "mean" in b:
        return f"| {label} mean | {fmt(b.get('mean'))} | {fmt(p.get('mean') if isinstance(p, dict) else None)} |"
    return f"| {label} |  |  |"


def panel_c_interpretation(pilot: dict[str, object]) -> str:
    raw_hc1_p = float(pilot["panel_c_raw_hc1"]["p"])
    raw_cluster_p = float(pilot["panel_c_raw_cluster"]["p"])
    drop_p99_p = float(pilot["panel_c_drop_p99_cluster"]["p"])
    raw_coef = float(pilot["panel_c_raw_cluster"]["coef"])
    drop_coef = float(pilot["panel_c_drop_p99_cluster"]["coef"])
    if raw_cluster_p < 0.05 or drop_p99_p < 0.05:
        return (
            f"- Panel C 已在 cluster 口径恢复显著正向：raw coef {raw_coef:.3f}, "
            f"cluster p {raw_cluster_p:.4f}; drop p99 coef {drop_coef:.3f}, p {drop_p99_p:.4f}。"
        )
    if raw_cluster_p < 0.10 or drop_p99_p < 0.10:
        return (
            f"- Panel C 已恢复正向且接近 cluster 显著：raw coef {raw_coef:.3f}, "
            f"cluster p {raw_cluster_p:.4f}; drop p99 coef {drop_coef:.3f}, p {drop_p99_p:.4f}；raw HC1 p {raw_hc1_p:.4f}。"
        )
    if raw_hc1_p < 0.05:
        return (
            f"- Panel C 方向和 HC1 已恢复：raw coef {raw_coef:.3f}, HC1 p {raw_hc1_p:.4f}；"
            f"但 cluster 口径仍不显著。"
        )
    return "- 本轮没有恢复 Panel C 显著性，说明长度校准能修 Table 1 量级和保留 B/D 效度，但不能单独解决 chunk_count 关系。"


def attempt_rows(sample_codes: set[str]) -> list[str]:
    lines = [
        "| mode | chunks | firms | Summary_len mean | Summary_len median | note |",
        "|---|---:|---:|---:|---:|---|",
    ]
    notes = {
        "cot_v3b_len132": "too long; stopped after 2 firms",
        "cot_v3b_len132_bounded": "still high; stopped after 2 firms",
        "cot_v3b_len132_tight": "selected pilot mode",
    }
    for mode in ATTEMPT_MODES:
        path = RUN_DIR / f"ipo_redundancy_llm_outputs_{mode}.jsonl"
        if not path.exists():
            continue
        df = pd.read_json(path, lines=True, dtype={"sec_code": str})
        df = df[df["sec_code"].astype(str).isin(sample_codes)].copy()
        if df.empty:
            continue
        df["summary_token_proxy"] = pd.to_numeric(df["summary_token_proxy"], errors="coerce")
        lines.append(
            "| "
            + " | ".join(
                [
                    mode,
                    str(int(df.shape[0])),
                    str(int(df["sec_code"].nunique())),
                    fmt(df["summary_token_proxy"].mean()),
                    fmt(df["summary_token_proxy"].median()),
                    notes.get(mode, ""),
                ]
            )
            + " |"
        )
    return lines


def write_report(sample: pd.DataFrame, baseline: dict[str, object] | None, pilot: dict[str, object] | None) -> None:
    codes = ",".join(sample["sec_code"].astype(str).tolist())
    sample_codes = set(sample["sec_code"].astype(str))
    pilot_complete = pilot is not None and pilot.get("chunk_n", 0) == baseline.get("chunk_n", 0) if baseline else pilot is not None
    verdict = "PENDING_LLM" if pilot is None else ("PASS_CHECK_NEEDED" if pilot_complete else "PARTIAL_LLM")
    if pilot is not None:
        s_mean = float(pilot["summary_len"]["mean"])
        b_rho = float(pilot["panel_b_spearman"]["rho"])
        b_p = float(pilot["panel_b_spearman"]["p"])
        low_med = float(pilot["panel_b_low_high_by_median"]["low_median_redundancy"])
        high_med = float(pilot["panel_b_low_high_by_median"]["high_median_redundancy"])
        panel_d_p = float(pilot["panel_d_all_union_cluster"]["p"])
        if pilot_complete and 125 <= s_mean <= 140 and b_rho < 0 and b_p < 0.01 and low_med > high_med and panel_d_p < 0.05:
            verdict = "PASS_FOR_SUMMARY_LEN_GATE"
        elif pilot_complete:
            verdict = "NO_PASS_YET"

    lines = [
        f"# cot_v3b_len132 {sample_n()} 家摘要长度校准试验",
        "",
        "日期：2026-07-03",
        "",
        "## 结论",
        "",
        f"`{verdict}`",
        "",
        "本试验固定既有 token_proxy chunking，只更换摘要生成 prompt。目标是检查把 `Summary_len` 从当前约 109 拉向原文约 133 后，Panel B/C/D 是否还能成立。",
        "",
        f"注意：这里的 `PASS_FOR_SUMMARY_LEN_GATE` 只表示 {sample_n()} 家摘要长度校准门通过，不表示表 2 经济后果已经复刻。",
        "",
        "## 样本",
        "",
        "- 样本窗口：2019-2022。",
        "- 抽样方式：按上市年配额，并在各年内按当前 full scoregate `Redundancy` 分位点抽取，避免只挑高/低冗余公司。",
        "- 配额：" + "，".join(f"{year} 年 {quota} 家" for year, quota in QUOTAS.items()) + "。",
        "",
        "```text",
        codes,
        "```",
        "",
        "## 输出",
        "",
        f"- 样本清单：`{(OUT_DIR / f'{sample_stem()}_firms_20260703.csv').relative_to(ROOT)}`",
        f"- 样本代码：`{(OUT_DIR / f'{sample_stem()}_codes_20260703.txt').relative_to(ROOT)}`",
        f"- pilot chunk metrics：`{(OUT_DIR / f'chunk_metrics_{PILOT_MODE}_20260703.csv').relative_to(ROOT)}`",
        f"- pilot firm ranking：`{(OUT_DIR / f'firm_ranking_{PILOT_MODE}_20260703.csv').relative_to(ROOT)}`",
        f"- pilot metrics JSON：`{(OUT_DIR / f'metrics_{PILOT_MODE}_20260703.json').relative_to(ROOT)}`",
        "",
        "## 三轮 prompt 校准记录",
        "",
        *attempt_rows(sample_codes),
        "",
        "## 描述统计对照",
        "",
        f"| 指标 | baseline scoregate | {PILOT_MODE} |",
        "|---|---:|---:|",
        metric_row("Text_len", "text_len", baseline, pilot),
        metric_row("Summary_len", "summary_len", baseline, pilot),
        metric_row("Redundancy_chunk", "redundancy_chunk", baseline, pilot),
        metric_row("Firm Redundancy", "firm_redundancy", baseline, pilot),
        "",
    ]
    if pilot is None:
        lines.extend(
            [
                "## 待运行命令",
                "",
                "```bash",
                "python scripts/run_ipo_redundancy_codex_cli_20260628.py \\",
                "  --run-name star_token_proxy_full_2019_2023_20260702 \\",
                f"  --prompt-mode {PILOT_MODE} \\",
                f"  --sec-code {codes} \\",
                "  --max-chunks-per-call 8 \\",
                "  --timeout 1200 \\",
                "  --reasoning-effort low",
                "",
                "python scripts/evaluate_summary_len_calibration_50_20260703.py",
                "```",
                "",
            ]
        )
    else:
        lines.extend(
            [
                "## Panel B",
                "",
                f"| 检验 | baseline | {PILOT_MODE} |",
                "|---|---:|---:|",
                f"| Spearman rho | {fmt(baseline['panel_b_spearman']['rho']) if baseline else ''} | {fmt(pilot['panel_b_spearman']['rho'])} |",
                f"| Spearman p | {fmt(baseline['panel_b_spearman']['p'], 4) if baseline else ''} | {fmt(pilot['panel_b_spearman']['p'], 4)} |",
                f"| low median by score median | {fmt(baseline['panel_b_low_high_by_median']['low_median_redundancy']) if baseline else ''} | {fmt(pilot['panel_b_low_high_by_median']['low_median_redundancy'])} |",
                f"| high median by score median | {fmt(baseline['panel_b_low_high_by_median']['high_median_redundancy']) if baseline else ''} | {fmt(pilot['panel_b_low_high_by_median']['high_median_redundancy'])} |",
                "",
                "## Panel C",
                "",
                f"| 检验 | baseline | {PILOT_MODE} |",
                "|---|---:|---:|",
                f"| raw cluster coef | {fmt(baseline['panel_c_raw_cluster']['coef']) if baseline else ''} | {fmt(pilot['panel_c_raw_cluster']['coef'])} |",
                f"| raw cluster p | {fmt(baseline['panel_c_raw_cluster']['p'], 4) if baseline else ''} | {fmt(pilot['panel_c_raw_cluster']['p'], 4)} |",
                f"| drop p99 cluster coef | {fmt(baseline['panel_c_drop_p99_cluster']['coef']) if baseline else ''} | {fmt(pilot['panel_c_drop_p99_cluster']['coef'])} |",
                f"| drop p99 cluster p | {fmt(baseline['panel_c_drop_p99_cluster']['p'], 4) if baseline else ''} | {fmt(pilot['panel_c_drop_p99_cluster']['p'], 4)} |",
                "",
                "## Panel D",
                "",
                f"| 检验 | baseline | {PILOT_MODE} |",
                "|---|---:|---:|",
                f"| all union cluster coef | {fmt(baseline['panel_d_all_union_cluster']['coef']) if baseline else ''} | {fmt(pilot['panel_d_all_union_cluster']['coef'])} |",
                f"| all union cluster p | {fmt(baseline['panel_d_all_union_cluster']['p'], 4) if baseline else ''} | {fmt(pilot['panel_d_all_union_cluster']['p'], 4)} |",
                f"| without target cluster coef | {fmt(baseline['panel_d_without_target_cluster']['coef']) if baseline else ''} | {fmt(pilot['panel_d_without_target_cluster']['coef'])} |",
                f"| without target cluster p | {fmt(baseline['panel_d_without_target_cluster']['p'], 4) if baseline else ''} | {fmt(pilot['panel_d_without_target_cluster']['p'], 4)} |",
                "",
                "## 初步读法",
                "",
                "- 若 `Summary_len` 进入 125-140 且 Panel B / Panel D 不破，说明当前主要缺口确实在摘要长度校准。",
                "- 若 `Summary_len` 仍明显低于 125，下一步再上调长度区间；若超过 145 且 Panel B 变弱，说明长度校准过度。",
                f"- Panel C 以方向、drop p99/稳健版本为主，不把 {sample_n()} 家样本 raw/cluster 显著性作为唯一硬门槛。",
                panel_c_interpretation(pilot),
                "",
            ]
        )
    DOC_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    sample = prepare_sample()
    baseline = evaluate_mode(BASELINE_MODE, sample)
    pilot = evaluate_mode(PILOT_MODE, sample)
    write_report(sample, baseline, pilot)
    print(f"sample_codes={OUT_DIR / f'{sample_stem()}_codes_20260703.txt'}")
    print(f"report={DOC_PATH}")
    if pilot is None:
        print("pilot_status=PENDING_LLM")
    else:
        print(f"pilot_chunks={pilot['chunk_n']} pilot_summary_mean={pilot['summary_len']['mean']:.3f}")


if __name__ == "__main__":
    main()
