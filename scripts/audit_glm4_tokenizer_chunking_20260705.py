#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import numpy as np
import pandas as pd
from transformers import AutoTokenizer


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
RUN_DIR = ROOT / "results/star_token_proxy_full_2019_2023_20260702"
OUT_DIR = ROOT / "results/glm4_tokenizer_chunk_audit_20260705"
DOC_OUT = ROOT / "docs/00_current/glm4_tokenizer_chunk_audit_20260705.md"

TOKENIZER_NAME = "THUDM/glm-4-9b-chat-hf"
TOKENIZER_SOURCE_URL = "https://huggingface.co/zai-org/glm-4-9b-chat-hf"

PAPER = {
    "firms": 552,
    "chunks": 8683,
    "text_len_mean": 3866.817,
    "chunk_num_mean": 18.191,
    "lnN_tech_mean": 10.962,
}


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def load_tokenizer():
    return AutoTokenizer.from_pretrained(TOKENIZER_NAME, trust_remote_code=True)


def glm_len(tokenizer, text: str) -> int:
    return len(tokenizer.encode(text, add_special_tokens=False))


def count_sections(tokenizer) -> pd.DataFrame:
    sections = pd.read_csv(RUN_DIR / "ipo_business_technology_sections.csv", dtype={"sec_code": str}).fillna("")
    rows = []
    for _, row in sections.iterrows():
        path = ROOT / str(row.get("section_file", ""))
        text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        compact_chars = len(compact_text(text))
        rows.append(
            {
                "sec_code": row["sec_code"],
                "sec_name": row.get("sec_name", ""),
                "section_file": str(path.relative_to(ROOT)) if path.exists() else "",
                "compact_chars": compact_chars,
                "char2_proxy": math.ceil(compact_chars / 2),
                "glm4_tokens": glm_len(tokenizer, text),
                "current_chunk_count": int(float(row.get("chunk_count") or 0)),
            }
        )
    return pd.DataFrame(rows)


def count_chunks(tokenizer) -> pd.DataFrame:
    chunks = pd.read_csv(RUN_DIR / "ipo_business_technology_chunks.csv", dtype={"sec_code": str}).fillna("")
    rows = []
    for _, row in chunks.iterrows():
        path = ROOT / str(row.get("chunk_file", ""))
        text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
        rows.append(
            {
                "custom_id": row["custom_id"],
                "sec_code": row["sec_code"],
                "chunk_index": int(float(row["chunk_index"])),
                "chunk_count": int(float(row["chunk_count"])),
                "chunk_token_proxy": float(row["chunk_token_proxy"]),
                "glm4_tokens": glm_len(tokenizer, text),
                "compact_chars": len(compact_text(text)),
            }
        )
    return pd.DataFrame(rows)


def budget_grid(section_counts: pd.DataFrame) -> pd.DataFrame:
    rows = []
    tokens = pd.to_numeric(section_counts["glm4_tokens"], errors="coerce")
    for budget in [4000, 4200, 4300, 4400, 4500, 4600, 4800, 5000]:
        counts = np.ceil(tokens / budget).astype(int)
        chunks = int(counts.sum())
        rows.append(
            {
                "budget": budget,
                "approx_chunks": chunks,
                "gap_chunks_vs_paper": chunks - PAPER["chunks"],
                "chunks_per_firm": chunks / len(section_counts),
                "weighted_chunk_num": float((counts * counts).sum() / counts.sum()),
                "total_glm_tokens_per_chunk": float(tokens.sum() / chunks),
                "gap_avg_tokens_vs_paper_textlen": float(tokens.sum() / chunks - PAPER["text_len_mean"]),
            }
        )
    return pd.DataFrame(rows)


def describe(series: pd.Series) -> dict[str, float]:
    s = pd.to_numeric(series, errors="coerce").dropna()
    return {
        "n": int(len(s)),
        "mean": float(s.mean()),
        "std": float(s.std(ddof=1)),
        "p25": float(s.quantile(0.25)),
        "median": float(s.quantile(0.50)),
        "p75": float(s.quantile(0.75)),
        "p95": float(s.quantile(0.95)),
        "max": float(s.max()),
    }


def write_doc(section_counts: pd.DataFrame, chunk_counts: pd.DataFrame, grid: pd.DataFrame, summary: dict) -> None:
    def fmt(x: object, digits: int = 3) -> str:
        if pd.isna(x):
            return ""
        return f"{float(x):.{digits}f}"

    grid_rows = [
        f"| {int(r.budget)} | {int(r.approx_chunks)} | {int(r.gap_chunks_vs_paper)} | {fmt(r.chunks_per_firm)} | {fmt(r.weighted_chunk_num)} | {fmt(r.total_glm_tokens_per_chunk)} |"
        for r in grid.itertuples()
    ]
    lines = [
        "# GLM-4 tokenizer 与 chunk 口径审计",
        "",
        "日期：2026-07-05",
        "",
        "## 结论",
        "",
        "- 主人的质疑成立：当前 `char2 token_proxy = ceil(去空白字符数 / 2)` 不是 GLM-4 tokenizer。",
        "- 使用开放 tokenizer `THUDM/glm-4-9b-chat-hf` 计数后，现有 chunk 的平均 GLM-4 tokens 为 `5297.880`，而当前 proxy 均值为 `3758.194`。",
        "- 因此，若原文“4000 词元”指 GLM-4 tokenizer，我们当前 chunk 实际切得过大，不是过小。",
        "- 当前 543 家业务与技术全文 GLM-4 token 总量为 `37,584,029`，高于原文 `8683 * 3866.817 ≈ 33,575,572` 的 implied token 总量。",
        "- 用 GLM-4 tokens 按 4000 上限粗略重切，当前文本会得到约 `9666` 个 chunk，反而高于原文 `8683`。要接近原文 chunk 数，预算大约在 `4400-4500` GLM tokens。",
        "",
        "## Tokenizer 来源",
        "",
        f"- 本次用 `transformers.AutoTokenizer.from_pretrained(\"{TOKENIZER_NAME}\", trust_remote_code=True)` 加载 tokenizer。",
        f"- Hugging Face 模型页：`{TOKENIZER_SOURCE_URL}`。",
        f"- tokenizer class：`{summary['tokenizer_class']}`；vocab size：`{summary['tokenizer_vocab_size']}`。",
        "- 注意：这是开源 GLM-4-9B-Chat tokenizer，未必与商业 GLM-4 服务端内部 tokenizer 完全一致，但已经足以说明旧 `char2` proxy 不是同一长度单位。",
        "",
        "## 关键统计",
        "",
        "| 指标 | 当前 proxy | GLM-4 tokenizer |",
        "|---|---:|---:|",
        f"| chunk 均值 | {fmt(chunk_counts['chunk_token_proxy'].mean())} | {fmt(chunk_counts['glm4_tokens'].mean())} |",
        f"| chunk 中位数 | {fmt(chunk_counts['chunk_token_proxy'].median())} | {fmt(chunk_counts['glm4_tokens'].median())} |",
        f"| section 总量 | {fmt(section_counts['char2_proxy'].sum(), 0)} | {fmt(section_counts['glm4_tokens'].sum(), 0)} |",
        f"| GLM/proxy 比例均值 |  | {fmt(summary['chunk_glm_proxy_ratio_mean'])} |",
        "",
        "## GLM-4 预算近似网格",
        "",
        "| budget | approx chunks | vs 原文差 | chunks/firm | weighted Chunk_num | total_glm/chunk |",
        "|---:|---:|---:|---:|---:|---:|",
        *grid_rows,
        "",
        "## 解释",
        "",
        "之前说“不能靠多切解决”是基于旧 proxy 的总量算术；在真正 GLM-4 tokenizer 下，这个判断要修正。现在的问题不是文本总量不足，而是 tokenizer 口径错了：现有 chunk 按 proxy 看贴近 4000，但按 GLM-4 看普遍超过 5000。",
        "",
        "下一步应当先重建一个 `glm4_tokenizer_chunk_base`，不跑 LLM，只生成 section/chunk 表并对照原文 Table 1。若 chunk 数、Text_len、lnN_tech 同时接近，再决定是否小样本重跑摘要。",
        "",
        "## 输出",
        "",
        f"- section counts：`{OUT_DIR / 'section_glm4_token_counts_20260705.csv'}`",
        f"- chunk counts：`{OUT_DIR / 'chunk_glm4_token_counts_20260705.csv'}`",
        f"- budget grid：`{OUT_DIR / 'glm4_budget_grid_20260705.csv'}`",
        f"- summary：`{OUT_DIR / 'summary_glm4_tokenizer_chunk_audit_20260705.json'}`",
        "",
    ]
    DOC_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tokenizer = load_tokenizer()
    section_counts = count_sections(tokenizer)
    chunk_counts = count_chunks(tokenizer)
    grid = budget_grid(section_counts)

    summary = {
        "tokenizer": TOKENIZER_NAME,
        "tokenizer_source_url": TOKENIZER_SOURCE_URL,
        "tokenizer_class": type(tokenizer).__name__,
        "tokenizer_vocab_size": int(getattr(tokenizer, "vocab_size", 0) or 0),
        "section_n": int(len(section_counts)),
        "chunk_n": int(len(chunk_counts)),
        "section_glm_total": float(section_counts["glm4_tokens"].sum()),
        "section_proxy_total": float(section_counts["char2_proxy"].sum()),
        "chunk_glm_mean": float(chunk_counts["glm4_tokens"].mean()),
        "chunk_proxy_mean": float(chunk_counts["chunk_token_proxy"].mean()),
        "section_glm_proxy_ratio_mean": float((section_counts["glm4_tokens"] / section_counts["char2_proxy"]).mean()),
        "chunk_glm_proxy_ratio_mean": float((chunk_counts["glm4_tokens"] / chunk_counts["chunk_token_proxy"]).mean()),
    }

    section_counts.to_csv(OUT_DIR / "section_glm4_token_counts_20260705.csv", index=False, encoding="utf-8-sig")
    chunk_counts.to_csv(OUT_DIR / "chunk_glm4_token_counts_20260705.csv", index=False, encoding="utf-8-sig")
    grid.to_csv(OUT_DIR / "glm4_budget_grid_20260705.csv", index=False, encoding="utf-8-sig")
    (OUT_DIR / "summary_glm4_tokenizer_chunk_audit_20260705.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_doc(section_counts, chunk_counts, grid, summary)
    print(DOC_OUT)
    print(grid.to_string(index=False))


if __name__ == "__main__":
    main()
