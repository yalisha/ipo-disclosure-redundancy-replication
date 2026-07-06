#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
import shutil
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from transformers import AutoTokenizer


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
SOURCE_RUN = ROOT / "results/star_token_proxy_full_2019_2023_20260702"
OUT_DIR = ROOT / "results/glm4_dewrap_rechunk_trial_20260705"
DOC_OUT = ROOT / "docs/00_current/glm4_dewrap_rechunk_trial_20260705.md"
TOKENIZER_NAME = "THUDM/glm-4-9b-chat-hf"
MAX_TOKENS = 4000

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


def compact(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def drop_page_boilerplate(lines: list[str], sec_name: str) -> list[str]:
    stripped = [line.strip() for line in lines]
    counts = Counter(line for line in stripped if line)
    kept: list[str] = []
    for line in stripped:
        if not line:
            kept.append("")
            continue
        is_page = bool(re.fullmatch(r"(?:\d+|\d+-\d+-\d+|1-1-\d+|第\s*\d+\s*页)", line))
        is_header = (
            counts[line] >= 3
            and ("招股说明书" in line or "首次公开发行" in line or sec_name in line)
            and len(line) < 120
        )
        if not (is_page or is_header):
            kept.append(re.sub(r"[ \t]+", " ", line))
    return kept


def dewrap_join(text: str, sec_name: str) -> str:
    paragraphs: list[str] = []
    current: list[str] = []
    for line in drop_page_boilerplate(text.replace("\r\n", "\n").replace("\r", "\n").split("\n"), sec_name):
        if not line:
            if current:
                paragraphs.append("".join(current))
                current = []
            continue
        current.append(line)
    if current:
        paragraphs.append("".join(current))
    return "\n\n".join(paragraphs)


def dewrap_space(text: str, sec_name: str) -> str:
    paragraphs: list[str] = []
    current: list[str] = []
    for line in drop_page_boilerplate(text.replace("\r\n", "\n").replace("\r", "\n").split("\n"), sec_name):
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(line)
    if current:
        paragraphs.append(" ".join(current))
    return "\n\n".join(paragraphs)


def describe(series: pd.Series) -> dict[str, float]:
    s = pd.to_numeric(series, errors="coerce").dropna()
    return {
        "N": int(len(s)),
        "mean": float(s.mean()),
        "std": float(s.std(ddof=1)),
        "p25": float(s.quantile(0.25)),
        "median": float(s.quantile(0.50)),
        "p75": float(s.quantile(0.75)),
    }


class FastTokenSplitter:
    def __init__(self, tokenizer, max_tokens: int):
        self.tokenizer = tokenizer
        self.max_tokens = max_tokens

    def token_len(self, text: str) -> int:
        return len(self.tokenizer.encode(text, add_special_tokens=False))

    def split(self, text: str) -> list[str]:
        encoded = self.tokenizer(text, add_special_tokens=False, return_offsets_mapping=True)
        token_ids = encoded["input_ids"]
        offsets = encoded["offset_mapping"]
        if len(token_ids) <= self.max_tokens:
            return [text.strip()] if text.strip() else []

        chunks: list[str] = []
        start = 0
        n_tokens = len(token_ids)
        while start < n_tokens:
            hard_end = min(start + self.max_tokens - 1, n_tokens)
            if hard_end == n_tokens:
                end = n_tokens
            else:
                lower = start + min(3000, self.max_tokens - 1)
                end = hard_end
                for candidate in range(hard_end, lower, -1):
                    char_end = offsets[candidate - 1][1]
                    around = text[max(0, char_end - 2) : min(len(text), char_end + 2)]
                    prev_char = text[char_end - 1] if char_end > 0 else ""
                    next_char = text[char_end] if char_end < len(text) else ""
                    if "\n\n" in around or prev_char in "。！？；;" or next_char == "\n":
                        end = candidate
                        break
            chunk = self.tokenizer.decode(token_ids[start:end], skip_special_tokens=True).strip()
            while chunk and self.token_len(chunk) > self.max_tokens and end > start + 1:
                end -= 1
                chunk = self.tokenizer.decode(token_ids[start:end], skip_special_tokens=True).strip()
            if chunk:
                chunks.append(chunk)
            if end <= start:
                end = hard_end
            start = end
        return chunks


def build_variant(name: str, normalizer, sections: pd.DataFrame, splitter: FastTokenSplitter) -> tuple[pd.DataFrame, pd.DataFrame]:
    run_dir = OUT_DIR / name
    if run_dir.exists():
        shutil.rmtree(run_dir)
    section_dir = run_dir / "business_technology_text"
    chunks_dir = run_dir / "chunks"
    section_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)

    section_rows: list[dict[str, object]] = []
    chunk_rows: list[dict[str, object]] = []
    for _, row in sections.iterrows():
        source_path = ROOT / str(row["section_file"])
        raw = source_path.read_text(encoding="utf-8", errors="ignore")
        normalized = normalizer(raw, str(row.get("sec_name") or ""))
        section_tokens = splitter.token_len(normalized)
        chunks = splitter.split(normalized)

        section_path = section_dir / f"{row['sec_code']}_{row['announcement_id']}_business_technology.txt"
        section_path.write_text(normalized, encoding="utf-8")

        base_row = row.to_dict()
        base_row.update(
            {
                "section_file": str(section_path.relative_to(ROOT)),
                "source_section_file": row["section_file"],
                "normalization_mode": name,
                "tokenizer": TOKENIZER_NAME,
                "max_tokens": MAX_TOKENS,
                "tech_text_chars": len(normalized),
                "tech_text_compact_chars": len(compact(normalized)),
                "tech_text_glm4_tokens": section_tokens,
                "lnN_tech_glm4": math.log(section_tokens) if section_tokens > 0 else np.nan,
                "chunk_count": len(chunks),
            }
        )
        section_rows.append(base_row)

        for idx, chunk in enumerate(chunks, start=1):
            custom_id = f"{row['sec_code']}_{row['announcement_id']}_glm4_{name}_chunk_{idx:04d}"
            chunk_path = chunks_dir / f"{custom_id}.txt"
            chunk_path.write_text(chunk, encoding="utf-8")
            token_count = splitter.token_len(chunk)
            chunk_rows.append(
                {
                    "custom_id": custom_id,
                    "sec_code": row["sec_code"],
                    "sec_name": row.get("sec_name", ""),
                    "announcement_id": row.get("announcement_id", ""),
                    "chunk_index": idx,
                    "chunk_count": len(chunks),
                    "chunk_file": str(chunk_path.relative_to(ROOT)),
                    "normalization_mode": name,
                    "tokenizer": TOKENIZER_NAME,
                    "max_tokens": MAX_TOKENS,
                    "chunk_chars": len(chunk),
                    "chunk_compact_chars": len(compact(chunk)),
                    "chunk_glm4_tokens": token_count,
                    "Text_len": token_count,
                    "Chunk_num": len(chunks),
                }
            )
    section_df = pd.DataFrame(section_rows)
    chunk_df = pd.DataFrame(chunk_rows)
    section_df.to_csv(run_dir / "ipo_business_technology_sections.csv", index=False, encoding="utf-8-sig")
    chunk_df.to_csv(run_dir / "ipo_business_technology_chunks.csv", index=False, encoding="utf-8-sig")
    return section_df, chunk_df


def comparison_rows(variant: str, section_df: pd.DataFrame, chunk_df: pd.DataFrame) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    current_metrics = {
        "Chunk_num": describe(chunk_df["Chunk_num"]),
        "Text_len": describe(chunk_df["Text_len"]),
        "lnN_tech": describe(section_df["lnN_tech_glm4"]),
    }
    for var, stats in current_metrics.items():
        paper = PAPER_CHUNK.get(var) or PAPER_FIRM.get(var)
        row = {"variant": variant, "variable": var, **{f"current_{k}": v for k, v in stats.items()}}
        if paper:
            row.update({f"paper_{k}": v for k, v in paper.items()})
            row["mean_gap"] = stats["mean"] - paper["mean"]
            row["mean_gap_pct"] = row["mean_gap"] / paper["mean"]
            row["n_gap"] = stats["N"] - paper["N"]
        rows.append(row)
    return rows


def write_doc(summary: dict[str, object], comparison: pd.DataFrame) -> None:
    def fmt(x: object, digits: int = 3) -> str:
        if x is None or pd.isna(x):
            return ""
        return f"{float(x):.{digits}f}"

    join = summary["variants"]["dewrap_join"]
    space = summary["variants"]["dewrap_space"]
    lines = [
        "# GLM-4 dewrap 重切试验",
        "",
        "日期：2026-07-05",
        "",
        "## 结论",
        "",
        "- 本轮不跑 LLM，只重建 tokenizer 口径 section/chunk base。",
        f"- `dewrap_join` 实际切出 `{join['chunks']}` 个 chunk，原文为 `8683`；`lnN_tech` mean=`{fmt(join['lnN_tech']['mean'])}`，几乎贴原文 `10.962`。",
        f"- `dewrap_space` 实际切出 `{space['chunks']}` 个 chunk，weighted `Chunk_num`=`{fmt(space['chunk_num']['mean'])}`，接近原文 `18.191`，但 `lnN_tech` 偏高。",
        f"- 两个版本最大 chunk token 分别为 `{join['max_chunk_glm4_tokens']}` 和 `{space['max_chunk_glm4_tokens']}`，均满足 `<=4000`。",
        "- 目前最像原文的主口径是 `dewrap_join + GLM tokenizer + 4000 token boundary split`；它把 chunks、Text_len、lnN_tech 同时拉回原文量级。",
        "",
        "## Panel A 对比",
        "",
        "| variant | variable | current N | paper N | current mean | paper mean | mean gap | current p25 | paper p25 | current median | paper median | current p75 | paper p75 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in comparison.itertuples(index=False):
        lines.append(
            f"| {row.variant} | {row.variable} | {int(row.current_N)} | {int(row.paper_N)} | "
            f"{fmt(row.current_mean)} | {fmt(row.paper_mean)} | {fmt(row.mean_gap)} | "
            f"{fmt(row.current_p25)} | {fmt(row.paper_p25)} | {fmt(row.current_median)} | "
            f"{fmt(row.paper_median)} | {fmt(row.current_p75)} | {fmt(row.paper_p75)} |"
        )
    lines.extend(
        [
            "",
            "## 输出",
            "",
            f"- 总目录：`{OUT_DIR}`",
            f"- summary：`{OUT_DIR / 'summary_glm4_dewrap_rechunk_trial_20260705.json'}`",
            f"- 对比表：`{OUT_DIR / 'panel_a_comparison_glm4_dewrap_rechunk_20260705.csv'}`",
            f"- dewrap_join chunks：`{OUT_DIR / 'dewrap_join/ipo_business_technology_chunks.csv'}`",
            f"- dewrap_space chunks：`{OUT_DIR / 'dewrap_space/ipo_business_technology_chunks.csv'}`",
            "",
        ]
    )
    DOC_OUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME, trust_remote_code=True)
    splitter = FastTokenSplitter(tokenizer, MAX_TOKENS)
    sections = pd.read_csv(SOURCE_RUN / "ipo_business_technology_sections.csv", dtype={"sec_code": str}).fillna("")

    outputs: dict[str, dict[str, object]] = {}
    comparison_all: list[dict[str, object]] = []
    for name, normalizer in [("dewrap_join", dewrap_join), ("dewrap_space", dewrap_space)]:
        section_df, chunk_df = build_variant(name, normalizer, sections, splitter)
        outputs[name] = {
            "firms": int(len(section_df)),
            "chunks": int(len(chunk_df)),
            "total_glm4_tokens": float(section_df["tech_text_glm4_tokens"].sum()),
            "max_chunk_glm4_tokens": int(chunk_df["chunk_glm4_tokens"].max()),
            "chunk_text_len": describe(chunk_df["Text_len"]),
            "chunk_num": describe(chunk_df["Chunk_num"]),
            "lnN_tech": describe(section_df["lnN_tech_glm4"]),
        }
        comparison_all.extend(comparison_rows(name, section_df, chunk_df))

    comparison = pd.DataFrame(comparison_all)
    comparison.to_csv(OUT_DIR / "panel_a_comparison_glm4_dewrap_rechunk_20260705.csv", index=False, encoding="utf-8-sig")

    summary = {
        "tokenizer": TOKENIZER_NAME,
        "max_tokens": MAX_TOKENS,
        "paper_chunk": PAPER_CHUNK,
        "paper_firm": PAPER_FIRM,
        "variants": outputs,
    }
    (OUT_DIR / "summary_glm4_dewrap_rechunk_trial_20260705.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_doc(summary, comparison)
    print(DOC_OUT)
    print(comparison[["variant", "variable", "current_N", "paper_N", "current_mean", "paper_mean", "mean_gap"]].to_string(index=False))


if __name__ == "__main__":
    main()
