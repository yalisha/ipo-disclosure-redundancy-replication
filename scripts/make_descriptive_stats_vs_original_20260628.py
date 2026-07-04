#!/usr/bin/env python3
"""Build current descriptive-stat tables against the paper's published stats."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RUNS = ["star_20260628", "star_batch002_20260628"]
PROMPT_MODE = "codex_ultra_v2"
OUT_DIR = ROOT / "docs"


ORIGINAL_TABLE1 = {
    "Chunk_num": {"n": 8683, "mean": 18.191, "std": 6.983, "p25": 13.000, "median": 16.000, "p75": 22.000},
    "Text_len": {"n": 8683, "mean": 3866.817, "std": 343.868, "p25": 3888.000, "median": 3954.000, "p75": 3985.000},
    "Summary_len": {"n": 8683, "mean": 132.678, "std": 39.683, "p25": 105.000, "median": 130.000, "p75": 158.000},
    "Redundancy_chunk": {"n": 8683, "mean": 32.176, "std": 11.730, "p25": 24.356, "median": 29.739, "p75": 37.037},
}

ORIGINAL_TABLE2 = {
    "lnN_tech": {"n": 552, "mean": 10.962, "std": 0.350, "p25": 10.714, "median": 10.910, "p75": 11.185},
    "Redundancy": {"n": 552, "mean": 29.074, "std": 2.630, "p25": 27.402, "median": 28.910, "p75": 30.795},
}


def read_current() -> tuple[pd.DataFrame, pd.DataFrame]:
    chunk_frames = []
    firm_frames = []
    for run_name in RUNS:
        run_dir = ROOT / "results" / run_name
        chunk_path = run_dir / f"ipo_redundancy_chunk_with_llm_{PROMPT_MODE}.csv"
        firm_path = run_dir / f"ipo_redundancy_firm_level_{PROMPT_MODE}.csv"
        chunks = pd.read_csv(chunk_path, dtype=str).assign(run_name=run_name)
        firms = pd.read_csv(firm_path, dtype=str).assign(run_name=run_name)
        chunk_frames.append(chunks)
        firm_frames.append(firms)

    chunks = pd.concat(chunk_frames, ignore_index=True)
    firms = pd.concat(firm_frames, ignore_index=True)

    for col in [
        "chunk_index",
        "chunk_count",
        "chunk_chars",
        "chunk_compact_chars",
        "summary_compact_chars",
        "summary_chars",
    ]:
        if col in chunks.columns:
            chunks[col] = pd.to_numeric(chunks[col], errors="coerce")

    for col in [
        "tech_text_compact_chars",
        "chunk_count",
        "chunks",
        "completed_chunks",
        "original_compact_chars",
        "summary_compact_chars",
        "redundancy_partial",
        "redundancy",
    ]:
        if col in firms.columns:
            firms[col] = pd.to_numeric(firms[col], errors="coerce")

    chunks = chunks[chunks["summary_compact_chars"].notna()].copy()
    firms = firms[firms["llm_complete"].astype(str).str.lower().eq("true")].copy()
    return chunks, firms


def stats(series: pd.Series) -> dict[str, float]:
    s = pd.to_numeric(series, errors="coerce").dropna()
    return {
        "n": int(s.shape[0]),
        "mean": float(s.mean()),
        "std": float(s.std(ddof=1)),
        "p25": float(s.quantile(0.25)),
        "median": float(s.quantile(0.50)),
        "p75": float(s.quantile(0.75)),
    }


def format_number(x: object, digits: int = 3) -> str:
    if pd.isna(x):
        return ""
    if isinstance(x, (int,)) or (isinstance(x, float) and x.is_integer() and abs(x) >= 100):
        return f"{int(x)}"
    if isinstance(x, float):
        return f"{x:.{digits}f}"
    return str(x)


def stats_table(current: dict[str, dict[str, float]], original: dict[str, dict[str, float]]) -> pd.DataFrame:
    rows = []
    for name, cur in current.items():
        orig = original.get(name, {})
        row = {"变量": name}
        for key in ["n", "mean", "std", "p25", "median", "p75"]:
            row[f"我们_{key}"] = cur.get(key)
            row[f"原文_{key}"] = orig.get(key)
            if key != "n" and key in cur and key in orig:
                row[f"差值_{key}"] = cur[key] - orig[key]
                row[f"比值_{key}"] = cur[key] / orig[key] if orig[key] else math.nan
        rows.append(row)
    return pd.DataFrame(rows)


def ols_y_on_x(y: pd.Series, x: pd.Series) -> dict[str, float]:
    data = pd.DataFrame({"y": y, "x": x}).dropna()
    n = len(data)
    if n < 3:
        return {"n": n, "alpha": math.nan, "beta": math.nan, "t_beta": math.nan, "adj_r2": math.nan}
    xbar = data["x"].mean()
    ybar = data["y"].mean()
    sxx = ((data["x"] - xbar) ** 2).sum()
    beta = ((data["x"] - xbar) * (data["y"] - ybar)).sum() / sxx
    alpha = ybar - beta * xbar
    resid = data["y"] - alpha - beta * data["x"]
    sse = (resid**2).sum()
    tss = ((data["y"] - ybar) ** 2).sum()
    sigma2 = sse / (n - 2)
    se_beta = math.sqrt(sigma2 / sxx)
    r2 = 1 - sse / tss
    adj_r2 = 1 - (1 - r2) * (n - 1) / (n - 2)
    return {"n": n, "alpha": alpha, "beta": beta, "t_beta": beta / se_beta, "adj_r2": adj_r2}


def markdown_stats_table(df: pd.DataFrame, value_cols: list[str]) -> str:
    headers = ["变量"] + value_cols
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for _, row in df.iterrows():
        cells = [str(row["变量"])] + [format_number(row.get(col), 3) for col in value_cols]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    chunks, firms = read_current()

    chunks["Redundancy_chunk"] = chunks["chunk_compact_chars"] / chunks["summary_compact_chars"]
    chunks["Redundancy_chunk_rawchars"] = chunks["chunk_chars"] / chunks["summary_compact_chars"]
    firms["lnN_tech"] = firms["original_compact_chars"].map(lambda x: math.log(x) if pd.notna(x) and x > 0 else math.nan)
    firms["lnN_tech_half_compact"] = firms["original_compact_chars"].map(
        lambda x: math.log(x / 2) if pd.notna(x) and x > 0 else math.nan
    )
    firms["lnN_tech_raw_from_chunks"] = firms["sec_code"].map(
        chunks.groupby("sec_code")["chunk_chars"].sum().map(lambda x: math.log(x) if x > 0 else math.nan)
    )

    table1_current = {
        "Chunk_num": stats(chunks["chunk_count"]),
        "Text_len": stats(chunks["chunk_compact_chars"]),
        "Summary_len": stats(chunks["summary_compact_chars"]),
        "Redundancy_chunk": stats(chunks["Redundancy_chunk"]),
    }
    table1_raw_current = {
        "Chunk_num": stats(chunks["chunk_count"]),
        "Text_len": stats(chunks["chunk_chars"]),
        "Summary_len": stats(chunks["summary_compact_chars"]),
        "Redundancy_chunk": stats(chunks["Redundancy_chunk_rawchars"]),
    }
    table2_current = {
        "lnN_tech": stats(firms["lnN_tech"]),
        "Redundancy": stats(firms["redundancy"]),
    }
    table2_half_current = {
        "lnN_tech": stats(firms["lnN_tech_half_compact"]),
        "Redundancy": stats(firms["redundancy"]),
    }
    table2_raw_current = {
        "lnN_tech": stats(firms["lnN_tech_raw_from_chunks"]),
        "Redundancy": stats(firms["redundancy"]),
    }

    t1 = stats_table(table1_current, ORIGINAL_TABLE1)
    t1_raw = stats_table(table1_raw_current, ORIGINAL_TABLE1)
    t2 = stats_table(table2_current, ORIGINAL_TABLE2)
    t2_half = stats_table(table2_half_current, ORIGINAL_TABLE2)
    t2_raw = stats_table(table2_raw_current, ORIGINAL_TABLE2)

    t1.to_csv(OUT_DIR / "table1_chunk_descriptive_vs_original_compact_20260628.csv", index=False, encoding="utf-8-sig")
    t1_raw.to_csv(OUT_DIR / "table1_chunk_descriptive_vs_original_rawchars_20260628.csv", index=False, encoding="utf-8-sig")
    t2.to_csv(OUT_DIR / "table2_firm_descriptive_vs_original_compact_20260628.csv", index=False, encoding="utf-8-sig")
    t2_half.to_csv(OUT_DIR / "table2_firm_descriptive_vs_original_half_compact_20260628.csv", index=False, encoding="utf-8-sig")
    t2_raw.to_csv(OUT_DIR / "table2_firm_descriptive_vs_original_rawchars_20260628.csv", index=False, encoding="utf-8-sig")

    panel_c_compact = ols_y_on_x(chunks["Redundancy_chunk"], chunks["chunk_count"])
    panel_c_raw = ols_y_on_x(chunks["Redundancy_chunk_rawchars"], chunks["chunk_count"])
    projected_chunks_half_current = firms["chunk_count"] / 2
    projected_chunks_8000 = (firms["original_compact_chars"] / 8000).map(math.ceil)
    projected_chunk_weighted = float((projected_chunks_8000 * projected_chunks_8000).sum() / projected_chunks_8000.sum())

    md = []
    md.append("# 原文表 1/表 2 描述性统计复刻对照\n")
    md.append("日期：2026-06-28\n")
    md.append("样本：当前 Codex `codex_ultra_v2` 已完成的科创板企业。第一批 50 家完整完成；第二批已完成 39 家；合计企业 89 家、chunk 3241 个。\n")
    md.append("说明：原文的 `Text_len` 更接近带空白/标点的切块长度；我们正式变量计算目前使用紧凑字数，因此下面同时给出“紧凑字数口径”和“原始 chunk 字符口径”。\n")

    md.append("## 表 1 Panel A：文本块层面描述性统计（紧凑字数口径）\n")
    md.append(markdown_stats_table(t1, ["我们_n", "我们_mean", "我们_std", "我们_p25", "我们_median", "我们_p75", "原文_mean", "差值_mean", "比值_mean"]))
    md.append("\n")

    md.append("## 表 1 Panel A：文本块层面描述性统计（原始 chunk 字符口径）\n")
    md.append(markdown_stats_table(t1_raw, ["我们_n", "我们_mean", "我们_std", "我们_p25", "我们_median", "我们_p75", "原文_mean", "差值_mean", "比值_mean"]))
    md.append("\n")

    md.append("## 表 1 Panel C：Chunk_num 与 Redundancy_chunk 的简单相关回归\n")
    md.append("| 口径 | 系数 | t值 | 截距 | 样本量 | 调整R2 | 原文系数 | 原文t值 | 原文调整R2 |")
    md.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    md.append(
        f"| 紧凑字数 | {panel_c_compact['beta']:.4f} | {panel_c_compact['t_beta']:.2f} | "
        f"{panel_c_compact['alpha']:.4f} | {int(panel_c_compact['n'])} | {panel_c_compact['adj_r2']:.3f} | 0.1243 | 6.91 | 0.01 |"
    )
    md.append(
        f"| 原始chunk字符 | {panel_c_raw['beta']:.4f} | {panel_c_raw['t_beta']:.2f} | "
        f"{panel_c_raw['alpha']:.4f} | {int(panel_c_raw['n'])} | {panel_c_raw['adj_r2']:.3f} | 0.1243 | 6.91 | 0.01 |"
    )
    md.append("\n")

    md.append("## 表 2 Panel A：企业层面描述性统计（当前可复刻变量）\n")
    md.append("当前尚未接入 CSMAR/Choice 和专利/行情数据，所以这里只复刻 `lnN_tech` 与 `Redundancy`。`FInvention`、`BHAR`、`FSales_Growth`、`Price_Issue`、`Price_Day5`、控制变量及 Panel B 回归需要后续补数据后再做。\n")
    md.append(markdown_stats_table(t2, ["我们_n", "我们_mean", "我们_std", "我们_p25", "我们_median", "我们_p75", "原文_mean", "差值_mean", "比值_mean"]))
    md.append("\n")

    md.append("## 表 2 Panel A：lnN_tech 的原始 chunk 字符口径敏感性\n")
    md.append(markdown_stats_table(t2_raw, ["我们_n", "我们_mean", "我们_std", "我们_p25", "我们_median", "我们_p75", "原文_mean", "差值_mean", "比值_mean"]))
    md.append("\n")

    md.append("## 表 2 Panel A：lnN_tech 的半字符/近似词元口径敏感性\n")
    md.append("如果把当前紧凑中文字符数除以 2 后再取对数，`lnN_tech` 几乎贴近原文。这提示原文的 `N_tech` 很可能不是中文字符数，而更接近中文分词词数或模型词元数。\n")
    md.append(markdown_stats_table(t2_half, ["我们_n", "我们_mean", "我们_std", "我们_p25", "我们_median", "我们_p75", "原文_mean", "差值_mean", "比值_mean"]))
    md.append("\n")

    md.append("## 长度单位校准线索\n")
    md.append("| 指标 | 当前值 | 原文值 | 含义 |")
    md.append("| --- | ---: | ---: | --- |")
    md.append(f"| `ln(紧凑字符数)` 均值 | {firms['lnN_tech'].mean():.3f} | 10.962 | 当前企业层文本长度比原文高约 `ln(2)` |")
    md.append(f"| `ln(紧凑字符数/2)` 均值 | {firms['lnN_tech_half_compact'].mean():.3f} | 10.962 | 除以 2 后几乎贴近原文 |")
    md.append(f"| 当前企业平均 chunk_count | {firms['chunk_count'].mean():.3f} | {8683/552:.3f} | 当前按 4000 字符切块，企业块数过多 |")
    md.append(f"| 当前 chunk_count/2 均值 | {projected_chunks_half_current.mean():.3f} | {8683/552:.3f} | 若按 4000 词元而非 4000 字符切块，数量大致回落 |")
    md.append(f"| 按约 8000 紧凑字符重切的企业平均块数 | {projected_chunks_8000.mean():.3f} | {8683/552:.3f} | 与原文企业平均块数接近 |")
    md.append(f"| 按约 8000 紧凑字符重切的 chunk 层加权 `Chunk_num` | {projected_chunk_weighted:.3f} | 18.191 | 方向接近，但还需用真实 token/分词重切验证 |")
    md.append("\n")

    md.append("## 目前和原文数据特征的差异\n")
    md.append("1. `Chunk_num` 是最大差异之一。我们当前按 4000 字符切块，chunk 数约为原文 2 倍；如果按约 8000 紧凑字符、或按 4000 词元/分词单位重切，块数会明显贴近原文。")
    md.append("2. 企业层 `lnN_tech` 的差异几乎等于 `ln(2)`；把紧凑字符数除以 2 后，均值从 11.646 变为 10.953，接近原文 10.962。这说明原文长度单位大概率不是字符数，而是词元/词数。")
    md.append("3. `Summary_len` 明显低于原文。原文均值约 132.678，我们当前约 84-85。这是当前 `Redundancy_chunk` 和企业层 `Redundancy` 偏高的直接原因。")
    md.append("4. 企业层 `Redundancy` 原文均值 29.074；我们当前均值 38.797，说明当前 Codex prompt 压缩过强，同时长度单位也尚未与原文统一。")
    md.append("\n")

    md.append("## 逼近原文数据特征的建议\n")
    md.append("1. 先校准长度单位：新增中文分词词数或 GLM/ChatGLM token 数，企业层 `lnN_tech` 目标均值 10.962；目前 `紧凑字符数/2` 已经是一个很好的近似口径。")
    md.append("2. 再校准切块规则：不要按 4000 字符切块，应按 4000 词元/词数切块；临时近似可按 8000 紧凑字符切块。目标是企业平均 chunk 数约 15.73，chunk 层 `Chunk_num` 均值约 18.19。")
    md.append("3. 然后校准摘要口径：把 prompt 的目标摘要长度从 20-180 汉字调到更接近原文的 100-160 字，目标是 `Summary_len` 均值约 130、中位数约 130。")
    md.append("4. 增加原文式重要性输出：要求模型返回 `N0`-`N5`，计算 `Relevant_score`，这样才能复刻表 1 Panel B。")
    md.append("5. 补创新词典：用程新生等（2022）或可审计的创新词典计算 `Innovation_Word_Rate`，再复刻表 1 Panel D。")
    md.append("6. 用小样本做网格校准：抽 20-30 家，分别跑 `4000词元+summary≈130`、`8000字符+summary≈130`、原文式 GLM-4/Kimi/Qwen prompt，比较 `Chunk_num`、`Summary_len`、`Redundancy`、排序相关和高冗余组重合度。")

    out_md = OUT_DIR / "原文表1表2描述性统计复刻对照_20260628.md"
    out_md.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(out_md)
    print(OUT_DIR / "table1_chunk_descriptive_vs_original_compact_20260628.csv")
    print(OUT_DIR / "table2_firm_descriptive_vs_original_compact_20260628.csv")


if __name__ == "__main__":
    main()
