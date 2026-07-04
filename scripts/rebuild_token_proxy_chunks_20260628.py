#!/usr/bin/env python3
"""Rebuild IPO redundancy chunks with token-like budgets.

The paper says chunks are no more than 4000 "词元". Our first run used
4000 characters, which roughly doubled chunk counts. This script tests several
token proxies and writes a primary char/2 proxy chunk base for later LLM runs.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Callable

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RUNS = ["star_20260628", "star_batch002_20260628"]
OUT_RUN = "star_token_proxy_20260628"
MAX_UNITS = 4000

ORIGINAL = {
    "chunks_total": 8683,
    "firms": 552,
    "firm_chunk_mean": 8683 / 552,
    "chunk_num_mean": 18.191,
    "text_len_mean": 3866.817,
    "lnN_tech_mean": 10.962,
}


def normalize_for_section(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def char2_units(text: str) -> int:
    return math.ceil(len(compact_text(text)) / 2)


def load_tokenizers() -> dict[str, Callable[[str], int]]:
    counters: dict[str, Callable[[str], int]] = {"char2_proxy": char2_units}

    try:
        import jieba  # type: ignore

        def jieba_units(text: str) -> int:
            return len(jieba.lcut(compact_text(text), HMM=False))

        counters["jieba_words"] = jieba_units
    except Exception:
        pass

    try:
        import tiktoken  # type: ignore

        for enc_name in ["o200k_base", "cl100k_base"]:
            try:
                enc = tiktoken.get_encoding(enc_name)

                def make_counter(encoding):
                    return lambda text: len(encoding.encode(compact_text(text), disallowed_special=()))

                counters[f"tiktoken_{enc_name}"] = make_counter(enc)
            except Exception:
                continue
    except Exception:
        pass

    return counters


def split_by_budget(text: str, unit_count: Callable[[str], int], max_units: int = MAX_UNITS) -> list[str]:
    clean = normalize_for_section(text).strip()
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", clean) if p.strip()]
    chunks: list[str] = []
    current = ""

    def flush() -> None:
        nonlocal current
        if current.strip():
            chunks.append(current.strip())
            current = ""

    def append_piece(piece: str) -> None:
        nonlocal current
        piece = piece.strip()
        if not piece:
            return
        sep = "\n\n" if "\n" in piece else "\n"
        candidate = f"{current}{sep if current else ''}{piece}"
        if current and unit_count(candidate) > max_units:
            flush()
            candidate = piece
        if unit_count(candidate) <= max_units:
            current = candidate
            return

        # Fallback for very long sentences or tables: binary-search character slices
        # using compact length as the slicing axis, while preserving original order.
        start = 0
        while start < len(piece):
            lo, hi = start + 1, len(piece)
            best = lo
            while lo <= hi:
                mid = (lo + hi) // 2
                part = piece[start:mid]
                if unit_count(part) <= max_units:
                    best = mid
                    lo = mid + 1
                else:
                    hi = mid - 1
            part = piece[start:best].strip()
            if part:
                if current:
                    flush()
                chunks.append(part)
            start = max(best, start + 1)

    for para in paragraphs:
        if unit_count(para) > max_units:
            for sentence in [s.strip() for s in re.split(r"(?<=[。！？；;])", para) if s.strip()]:
                append_piece(sentence)
        else:
            append_piece(para)
    flush()
    return chunks


def load_sections() -> pd.DataFrame:
    frames = []
    for run_name in RUNS:
        path = ROOT / "results" / run_name / "ipo_business_technology_sections.csv"
        df = pd.read_csv(path, dtype=str).fillna("")
        df["source_run_name"] = run_name
        frames.append(df)
    sections = pd.concat(frames, ignore_index=True)
    sections = sections[sections["section_status"].eq("ok")].copy()
    return sections.sort_values(["announcement_date", "sec_code", "announcement_id"]).reset_index(drop=True)


def describe(series: pd.Series) -> dict[str, float]:
    s = pd.to_numeric(series, errors="coerce").dropna()
    return {
        "n": int(len(s)),
        "mean": float(s.mean()),
        "std": float(s.std(ddof=1)),
        "p25": float(s.quantile(0.25)),
        "median": float(s.quantile(0.50)),
        "p75": float(s.quantile(0.75)),
    }


def task_prompt_token_calibrated(text: str) -> str:
    return (
        "你是招股说明书“业务与技术”章节的信息凝练员。请模拟论文中的冗余识别任务："
        "保留对判断发行人技术实力、核心竞争力、市场地位、产品与研发能力有实质价值的信息，"
        "压缩或删除重复、模板化、合规铺陈、空泛形容、无关背景和低信息密度表述。\n\n"
        "输出要求：\n"
        "1. 只基于原文，不新增事实，不评论。\n"
        "2. 输出一段连续中文正文，不要项目符号，不要解释。\n"
        "3. 通常写 220-320 个汉字；若原文信息密度很低，也至少写 120 个汉字概括其行业或业务事实。\n"
        "4. 尽量保留关键产品、技术、研发、市场、客户、供应商、产能、收入等数字事实。\n\n"
        f"待凝练文本：\n{text}"
    )


def write_primary_base(sections: pd.DataFrame, unit_count: Callable[[str], int]) -> tuple[pd.DataFrame, pd.DataFrame]:
    run_dir = ROOT / "results" / OUT_RUN
    section_dir = run_dir / "business_technology_text"
    chunks_dir = run_dir / "chunks"
    section_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)

    section_rows = []
    chunk_rows = []
    task_path = run_dir / "ipo_redundancy_llm_tasks_token_proxy.jsonl"
    with task_path.open("w", encoding="utf-8") as task_f:
        for _, row in sections.iterrows():
            section_path = ROOT / row["section_file"]
            section = section_path.read_text(encoding="utf-8", errors="ignore")
            chunks = split_by_budget(section, unit_count, MAX_UNITS)
            new_section_path = section_dir / f"{row['sec_code']}_{row['announcement_id']}_business_technology.txt"
            new_section_path.write_text(section, encoding="utf-8")

            section_row = row.to_dict()
            section_row.update(
                {
                    "source_chunk_count": row.get("chunk_count", ""),
                    "token_mode": "char2_proxy",
                    "max_units": MAX_UNITS,
                    "section_file": str(new_section_path.relative_to(ROOT)),
                    "tech_text_token_proxy": unit_count(section),
                    "tech_text_chars": len(section),
                    "tech_text_compact_chars": len(compact_text(section)),
                    "chunk_count": len(chunks),
                    "chunk_count_token_proxy": len(chunks),
                }
            )
            section_rows.append(section_row)

            for idx, chunk in enumerate(chunks, start=1):
                custom_id = f"{row['sec_code']}_{row['announcement_id']}_tok_chunk_{idx:04d}"
                chunk_file = chunks_dir / f"{custom_id}.txt"
                chunk_file.write_text(chunk, encoding="utf-8")
                chunk_row = {
                    "custom_id": custom_id,
                    "sec_code": row["sec_code"],
                    "sec_name": row["sec_name"],
                    "announcement_id": row["announcement_id"],
                    "source_run_name": row["source_run_name"],
                    "chunk_index": idx,
                    "chunk_count": len(chunks),
                    "chunk_file": str(chunk_file.relative_to(ROOT)),
                    "chunk_token_proxy": unit_count(chunk),
                    "chunk_chars": len(chunk),
                    "chunk_compact_chars": len(compact_text(chunk)),
                }
                chunk_rows.append(chunk_row)
                task_f.write(
                    json.dumps(
                        {
                            "custom_id": custom_id,
                            "sec_code": row["sec_code"],
                            "announcement_id": row["announcement_id"],
                            "token_mode": "char2_proxy",
                            "messages": [
                                {"role": "system", "content": "你只做忠实文本凝练，不新增事实。"},
                                {"role": "user", "content": task_prompt_token_calibrated(chunk)},
                            ],
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

    section_df = pd.DataFrame(section_rows)
    chunk_df = pd.DataFrame(chunk_rows)
    section_df.to_csv(run_dir / "ipo_business_technology_sections_token_proxy.csv", index=False, encoding="utf-8-sig")
    chunk_df.to_csv(run_dir / "ipo_business_technology_chunks_token_proxy.csv", index=False, encoding="utf-8-sig")
    section_df.to_csv(run_dir / "ipo_business_technology_sections.csv", index=False, encoding="utf-8-sig")
    chunk_df.to_csv(run_dir / "ipo_business_technology_chunks.csv", index=False, encoding="utf-8-sig")
    return section_df, chunk_df


def diagnostics(sections: pd.DataFrame, counters: dict[str, Callable[[str], int]]) -> pd.DataFrame:
    rows = []
    texts = []
    for _, row in sections.iterrows():
        section = (ROOT / row["section_file"]).read_text(encoding="utf-8", errors="ignore")
        texts.append((row, section))

    for mode, counter in counters.items():
        firm_rows = []
        chunk_rows = []
        for row, section in texts:
            total_units = counter(section)
            if mode == "char2_proxy":
                chunks = split_by_budget(section, counter, MAX_UNITS)
                chunk_units = [counter(chunk) for chunk in chunks]
                chunk_chars = [len(chunk) for chunk in chunks]
                chunk_compact_chars = [len(compact_text(chunk)) for chunk in chunks]
            else:
                # Heavy tokenizers are expensive if repeatedly applied during
                # paragraph-boundary search. For diagnostics, approximate a
                # packed 4000-token split from the one-time section token count.
                k = max(1, math.ceil(total_units / MAX_UNITS))
                chunk_units = [MAX_UNITS] * (k - 1) + [total_units - MAX_UNITS * (k - 1)]
                compact_len = len(compact_text(section))
                chars_per_unit = compact_len / total_units if total_units else math.nan
                chunk_compact_chars = [
                    int(round(u * chars_per_unit)) if pd.notna(chars_per_unit) else 0 for u in chunk_units
                ]
                chunk_chars = chunk_compact_chars
                chunks = [""] * k
            firm_rows.append(
                {
                    "sec_code": row["sec_code"],
                    "units": total_units,
                    "ln_units": math.log(total_units) if total_units > 0 else math.nan,
                    "chunks": len(chunks),
                }
            )
            for u, c, cc in zip(chunk_units, chunk_chars, chunk_compact_chars):
                chunk_rows.append(
                    {
                        "sec_code": row["sec_code"],
                        "chunk_count": len(chunks),
                        "text_len_units": u,
                        "chunk_chars": c,
                        "chunk_compact_chars": cc,
                    }
                )
        firm_df = pd.DataFrame(firm_rows)
        chunk_df = pd.DataFrame(chunk_rows)
        d_chunk_num = describe(chunk_df["chunk_count"])
        d_text = describe(chunk_df["text_len_units"])
        d_ln = describe(firm_df["ln_units"])
        rows.append(
            {
                "mode": mode,
                "firms": len(firm_df),
                "chunks_total": len(chunk_df),
                "firm_chunk_mean": firm_df["chunks"].mean(),
                "firm_chunk_median": firm_df["chunks"].median(),
                "chunk_level_chunk_num_mean": d_chunk_num["mean"],
                "text_len_units_mean": d_text["mean"],
                "text_len_units_median": d_text["median"],
                "ln_units_mean": d_ln["mean"],
                "ln_units_median": d_ln["median"],
                "chars_per_unit_mean": chunk_df["chunk_compact_chars"].sum() / chunk_df["text_len_units"].sum(),
                "diff_firm_chunk_mean_vs_original": firm_df["chunks"].mean() - ORIGINAL["firm_chunk_mean"],
                "diff_chunk_num_mean_vs_original": d_chunk_num["mean"] - ORIGINAL["chunk_num_mean"],
                "diff_text_len_mean_vs_original": d_text["mean"] - ORIGINAL["text_len_mean"],
                "diff_lnN_mean_vs_original": d_ln["mean"] - ORIGINAL["lnN_tech_mean"],
            }
        )
    return pd.DataFrame(rows).sort_values("diff_lnN_mean_vs_original", key=lambda s: s.abs())


def markdown_table(df: pd.DataFrame, cols: list[str]) -> str:
    labels = {
        "mode": "口径",
        "firms": "企业数",
        "chunks_total": "chunk数",
        "firm_chunk_mean": "企业平均chunk",
        "chunk_level_chunk_num_mean": "chunk层Chunk_num均值",
        "text_len_units_mean": "Text_len均值",
        "ln_units_mean": "lnN均值",
        "chars_per_unit_mean": "紧凑字符/单位",
        "diff_lnN_mean_vs_original": "lnN差值",
    }
    out = ["| " + " | ".join(labels.get(c, c) for c in cols) + " |"]
    out.append("| " + " | ".join(["---"] * len(cols)) + " |")
    for _, row in df.iterrows():
        vals = []
        for col in cols:
            value = row[col]
            if isinstance(value, float):
                vals.append(f"{value:.3f}")
            else:
                vals.append(str(value))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


def main() -> None:
    sections = load_sections()
    counters = load_tokenizers()
    section_df, chunk_df = write_primary_base(sections, counters["char2_proxy"])
    diag = diagnostics(sections, counters)

    docs_dir = ROOT / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    diag_path = docs_dir / "token_rechunk_diagnostics_20260628.csv"
    diag.to_csv(diag_path, index=False, encoding="utf-8-sig")

    run_dir = ROOT / "results" / OUT_RUN
    md = [
        "# Token 口径重构诊断",
        "",
        "日期：2026-06-28",
        "",
        f"样本：已抽取“业务与技术”章节的 100 家科创板 IPO 企业。主输出目录：`{run_dir}`。",
        "",
        "## 原文锚点",
        "",
        "| 指标 | 原文值 |",
        "| --- | ---: |",
        f"| 企业数 | {ORIGINAL['firms']} |",
        f"| chunk 总数 | {ORIGINAL['chunks_total']} |",
        f"| 企业平均 chunk 数 | {ORIGINAL['firm_chunk_mean']:.3f} |",
        f"| chunk 层 Chunk_num 均值 | {ORIGINAL['chunk_num_mean']:.3f} |",
        f"| Text_len 均值 | {ORIGINAL['text_len_mean']:.3f} |",
        f"| 企业层 lnN_tech 均值 | {ORIGINAL['lnN_tech_mean']:.3f} |",
        "",
        "## 不同 token 口径重切结果",
        "",
        markdown_table(
            diag,
            [
                "mode",
                "firms",
                "chunks_total",
                "firm_chunk_mean",
                "chunk_level_chunk_num_mean",
                "text_len_units_mean",
                "ln_units_mean",
                "chars_per_unit_mean",
                "diff_lnN_mean_vs_original",
            ],
        ),
        "",
        "## 当前主重构口径",
        "",
        "`char2_proxy` 定义为：",
        "",
        "```text",
        "token_proxy = ceil(去空白后的紧凑字符数 / 2)",
        "每个 chunk 不超过 4000 token_proxy",
        "```",
        "",
        "这个口径不是正式 tokenizer，但它能解释两个同时出现的事实：第一，原文企业层 `lnN_tech` 约等于我们 `ln(紧凑字符数/2)`；第二，原文 chunk 数约等于我们 4000 字符切块数的一半。",
        "",
        "## 已写出的文件",
        "",
        f"- sections：`{run_dir / 'ipo_business_technology_sections_token_proxy.csv'}`",
        f"- chunks：`{run_dir / 'ipo_business_technology_chunks_token_proxy.csv'}`",
        f"- tasks：`{run_dir / 'ipo_redundancy_llm_tasks_token_proxy.jsonl'}`",
        f"- diagnostics：`{diag_path}`",
        "",
        "同时已写出 runner 可直接读取的标准文件名：",
        "",
        f"- `{run_dir / 'ipo_business_technology_sections.csv'}`",
        f"- `{run_dir / 'ipo_business_technology_chunks.csv'}`",
        "",
        "## 下一步",
        "",
        "如果要继续逼近原文，建议先用这个 token_proxy chunk base 抽 5-10 家试跑新的凝练 prompt。新的 prompt 已把单块摘要目标调到约 220-320 个汉字，因为如果原文 `Summary_len=132` 也是 token/词元数，那么对应中文字符长度大约在 260 字左右，而不是我们旧 prompt 的 20-180 字。",
    ]
    md_path = docs_dir / "token_rechunk_diagnostics_20260628.md"
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    print(md_path)
    print(diag_path)
    print(run_dir / "ipo_business_technology_chunks_token_proxy.csv")
    print(f"primary_chunks={len(chunk_df)} primary_firms={len(section_df)}")


if __name__ == "__main__":
    main()
