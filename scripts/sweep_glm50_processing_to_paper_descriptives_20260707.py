#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
RUN_DIR = ROOT / "results/siliconflow_glm4_32b_pilot50_20260707"
OUT_DIR = ROOT / "results/glm50_processing_descriptive_sweep_20260707"
DOC = ROOT / "docs/00_current/glm50_processing_descriptive_sweep_20260707.md"

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


def describe(s: pd.Series) -> dict[str, float]:
    s = pd.to_numeric(s, errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
    if s.empty:
        return {k: math.nan for k in ["mean", "std", "p25", "median", "p75", "min", "max"]}
    return {
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


def prepare_rows(
    chunks: pd.DataFrame,
    unit: str,
    process: str,
    threshold: int,
    summary_floor: int,
    red_winsor: str,
    firm_len_mode: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = chunks.copy()
    df["summary_len"] = df[unit].astype(float)
    rows: list[dict[str, object]] = []
    for _, g in df.groupby("sec_code", sort=False):
        g = g.sort_values("chunk_index").copy()
        proc: list[dict[str, object]] = []
        for row in g.to_dict("records"):
            item = {
                "sec_code": row["sec_code"],
                "sec_name": row["sec_name"],
                "text_len": float(row["chunk_glm4_tokens"]),
                "summary_len": float(row["summary_len"]),
                "source_chunks": 1,
            }
            proc.append(item)
        if process == "drop_short_tail":
            while len(proc) > 1 and proc[-1]["text_len"] < threshold:
                proc.pop()
        elif process == "merge_short_tail":
            while len(proc) > 1 and proc[-1]["text_len"] < threshold:
                tail = proc.pop()
                proc[-1]["text_len"] += tail["text_len"]
                proc[-1]["summary_len"] += tail["summary_len"]
                proc[-1]["source_chunks"] += tail["source_chunks"]
        elif process == "drop_any_short":
            proc = [x for x in proc if x["text_len"] >= threshold]
            if not proc:
                proc = [
                    {
                        "sec_code": g.iloc[-1]["sec_code"],
                        "sec_name": g.iloc[-1]["sec_name"],
                        "text_len": float(g.iloc[-1]["chunk_glm4_tokens"]),
                        "summary_len": float(g.iloc[-1]["summary_len"]),
                        "source_chunks": 1,
                    }
                ]
        elif process != "keep":
            raise ValueError(process)
        chunk_n = len(proc)
        for i, item in enumerate(proc, start=1):
            item["processed_chunk_index"] = i
            item["Chunk_num"] = chunk_n
            rows.append(item)
    c = pd.DataFrame(rows)
    c["Summary_len"] = c["summary_len"].clip(lower=summary_floor) if summary_floor else c["summary_len"]
    c["Text_len"] = c["text_len"]
    c["Redundancy_chunk_raw"] = c["text_len"] / c["Summary_len"].replace({0: np.nan})
    if red_winsor == "none":
        c["Redundancy_chunk"] = c["Redundancy_chunk_raw"]
    else:
        q = float(red_winsor)
        hi = c["Redundancy_chunk_raw"].quantile(q)
        c["Redundancy_chunk"] = c["Redundancy_chunk_raw"].clip(upper=hi)

    f = (
        c.groupby(["sec_code", "sec_name"], as_index=False)
        .agg(
            text_sum=("text_len", "sum"),
            summary_sum=("Summary_len", "sum"),
            chunk_n=("processed_chunk_index", "size"),
        )
    )
    sections = pd.read_csv(RUN_DIR / "ipo_business_technology_sections.csv", dtype={"sec_code": str})
    sections["tech_text_glm4_tokens"] = pd.to_numeric(sections["tech_text_glm4_tokens"], errors="coerce")
    f = f.merge(sections[["sec_code", "tech_text_glm4_tokens"]], on="sec_code", how="left")
    numerator = f["tech_text_glm4_tokens"] if firm_len_mode == "original_section" else f["text_sum"]
    f["lnN_tech"] = np.log(numerator.replace({0: np.nan}))
    f["Redundancy"] = numerator / f["summary_sum"].replace({0: np.nan})
    return c, f


def evaluate(c: pd.DataFrame, f: pd.DataFrame) -> tuple[dict[str, object], dict[str, float]]:
    stats: dict[str, dict[str, float]] = {
        "Chunk_num": describe(c["Chunk_num"]),
        "Text_len": describe(c["Text_len"]),
        "Summary_len": describe(c["Summary_len"]),
        "Redundancy_chunk": describe(c["Redundancy_chunk"]),
        "lnN_tech": describe(f["lnN_tech"]),
        "Redundancy": describe(f["Redundancy"]),
    }
    loss_parts: dict[str, float] = {}
    total = 0.0
    count = 0
    for metric, target in PAPER_CHUNK.items():
        loss = 0.0
        n = 0
        for stat, tval in target.items():
            err = rel_error(stats[metric][stat], tval)
            loss += err
            total += err
            n += 1
            count += 1
        loss_parts[f"chunk_{metric}"] = loss / n
    for metric, target in PAPER_FIRM.items():
        loss = 0.0
        n = 0
        for stat, tval in target.items():
            err = rel_error(stats[metric][stat], tval)
            loss += err
            total += err
            n += 1
            count += 1
        loss_parts[f"firm_{metric}"] = loss / n
    return {
        "chunk_n": int(c.shape[0]),
        "firm_n": int(f.shape[0]),
        "loss_all": total / count,
        **loss_parts,
        **{f"{m}_{s}": v for m, d in stats.items() for s, v in d.items()},
    }, stats


def fmt(x: object, digits: int = 3) -> str:
    try:
        f = float(x)
    except Exception:
        return ""
    if math.isnan(f):
        return ""
    return f"{f:.{digits}f}"


def md_table(df: pd.DataFrame, cols: list[str], n: int = 20) -> list[str]:
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.head(n).iterrows():
        vals = []
        for c in cols:
            v = r[c]
            vals.append(fmt(v) if isinstance(v, (float, int, np.floating, np.integer)) and c not in {"chunk_n", "firm_n", "threshold"} else str(v))
        out.append("| " + " | ".join(vals) + " |")
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    chunks = pd.read_csv(RUN_DIR / "chunk_metrics_glm4_cot_v3b_len132_tight_20260705.csv", dtype={"sec_code": str})
    for col in ["chunk_index", "chunk_glm4_tokens", "Summary_len_proxy", "Summary_len_glm4"]:
        chunks[col] = pd.to_numeric(chunks[col], errors="coerce")

    units = {"proxy": "Summary_len_proxy", "glm4_token": "Summary_len_glm4"}
    processes = ["keep", "merge_short_tail", "drop_short_tail", "drop_any_short"]
    thresholds = [0, 500, 1000, 1500, 2000, 2500, 3000, 3500]
    red_winsors = ["none", "0.99", "0.975", "0.95"]
    summary_floors = [0, 30, 50, 60, 80, 100, 120]
    firm_modes = ["original_section", "processed_text_sum"]
    records: list[dict[str, object]] = []
    detail: dict[str, tuple[pd.DataFrame, pd.DataFrame]] = {}
    for unit_name, unit_col in units.items():
        for process in processes:
            for threshold in thresholds:
                if process == "keep" and threshold != 0:
                    continue
                for red_winsor in red_winsors:
                    for summary_floor in summary_floors:
                        for firm_mode in firm_modes:
                            c, f = prepare_rows(
                                chunks, unit_col, process, threshold, summary_floor, red_winsor, firm_mode
                            )
                            row, _ = evaluate(c, f)
                            key = f"{unit_name}|{process}|{threshold}|floor{summary_floor}|{red_winsor}|{firm_mode}"
                            row.update(
                                {
                                    "key": key,
                                    "unit": unit_name,
                                    "process": process,
                                    "threshold": threshold,
                                    "summary_floor": summary_floor,
                                    "red_winsor": red_winsor,
                                    "firm_len_mode": firm_mode,
                                }
                            )
                            records.append(row)
                            detail[key] = (c, f)
    res = pd.DataFrame(records).sort_values("loss_all")
    res.to_csv(OUT_DIR / "glm50_processing_sweep_ranked_20260707.csv", index=False, encoding="utf-8-sig")

    # Save detailed stats for the best few interpretable rules.
    selected_keys = list(res.head(10)["key"])
    long_rows: list[dict[str, object]] = []
    for key in selected_keys:
        c, f = detail[key]
        _, stats = evaluate(c, f)
        for metric, d in stats.items():
            target = PAPER_CHUNK.get(metric) or PAPER_FIRM.get(metric) or {}
            for stat in ["mean", "std", "p25", "median", "p75"]:
                long_rows.append(
                    {
                        "key": key,
                        "metric": metric,
                        "stat": stat,
                        "value": d.get(stat),
                        "paper": target.get(stat),
                        "diff": d.get(stat) - target.get(stat) if stat in target else np.nan,
                    }
                )
    pd.DataFrame(long_rows).to_csv(OUT_DIR / "glm50_processing_top10_stats_long_20260707.csv", index=False, encoding="utf-8-sig")

    top_cols = [
        "unit",
        "process",
        "threshold",
        "summary_floor",
        "red_winsor",
        "firm_len_mode",
        "loss_all",
        "chunk_n",
        "Chunk_num_mean",
        "Text_len_mean",
        "Summary_len_mean",
        "Redundancy_chunk_mean",
        "Redundancy_chunk_std",
        "lnN_tech_mean",
        "Redundancy_mean",
        "Redundancy_std",
    ]
    legitimate = res[(res["red_winsor"] == "none") & (res["process"].isin(["keep", "merge_short_tail", "drop_short_tail"]))]
    no_drop = res[(res["process"].isin(["keep", "merge_short_tail"])) & (res["red_winsor"] == "none")]
    no_floor_no_winsor = res[(res["summary_floor"] == 0) & (res["red_winsor"] == "none")]

    doc = [
        "# GLM 50 家描述性统计贴近原文的切割/处理扫描",
        "",
        "日期：2026-07-07",
        "",
        "## 结论",
        "",
        "- 这是一轮反推诊断，不是正式测度选择。目标是看 GLM 50 家在什么切割/处理规则下最像原文 Table 1 的描述性统计。",
        "- 最重要的发现：`GLM-token` 摘要长度单位能让 chunk 层 `Redundancy_chunk` 均值更接近原文，但会让企业层 `Redundancy` 均值偏低。",
        "- `proxy` 口径在企业层更接近原文，但 chunk 层 `Summary_len` 偏短、`Redundancy_chunk` 偏高。",
        "- 短尾 chunk 的处理很关键：原文 `Text_len` 的 std=343.868，GLM 50 原始 std=545.233；说明我们当前切割保留了更多短尾 chunk。",
        "- 极短摘要也很关键：GLM 会返回 `无重要信息` 一类 3-20 个 proxy 单位的摘要，直接把 `Redundancy_chunk` std 撑爆；`summary_floor=50` 可视为对这类异常的 bounded repair 近似。",
        "- 仅靠切割/处理无法同时让 chunk 层和企业层全部贴原文；要么像 chunk 层，要么像企业层。这支持“原文长度单位/切割规则仍未完全对齐”的判断。",
        "",
        "## 原文目标",
        "",
        "| 层级 | 指标 | mean | std | p25 | median | p75 |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for metric, d in PAPER_CHUNK.items():
        doc.append(f"| chunk | {metric} | {d['mean']:.3f} | {d['std']:.3f} | {d['p25']:.3f} | {d['median']:.3f} | {d['p75']:.3f} |")
    for metric, d in PAPER_FIRM.items():
        doc.append(f"| firm | {metric} | {d['mean']:.3f} | {d['std']:.3f} | {d['p25']:.3f} | {d['median']:.3f} | {d['p75']:.3f} |")
    doc.extend(
        [
            "",
            "## Overall Top 15",
            "",
            *md_table(res[top_cols], top_cols, 15),
            "",
            "## 不做 winsor 的可解释规则 Top 15",
            "",
            *md_table(legitimate[top_cols], top_cols, 15),
            "",
            "## 不做 winsor 且不设 summary floor 的规则 Top 15",
            "",
            *md_table(no_floor_no_winsor[top_cols], top_cols, 15),
            "",
            "## 不丢正文的规则 Top 15",
            "",
            *md_table(no_drop[top_cols], top_cols, 15),
            "",
            "## 输出文件",
            "",
            f"- ranked sweep：`{OUT_DIR / 'glm50_processing_sweep_ranked_20260707.csv'}`",
            f"- top10 stats long：`{OUT_DIR / 'glm50_processing_top10_stats_long_20260707.csv'}`",
            "",
        ]
    )
    DOC.write_text("\n".join(doc), encoding="utf-8")
    print(
        {
            "ranked": str(OUT_DIR / "glm50_processing_sweep_ranked_20260707.csv"),
            "doc": str(DOC),
            "best": res.head(1).to_dict("records")[0],
        }
    )


if __name__ == "__main__":
    main()
