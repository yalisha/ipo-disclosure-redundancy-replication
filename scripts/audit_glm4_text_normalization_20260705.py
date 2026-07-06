#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from transformers import AutoTokenizer


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
AUDIT_DIR = ROOT / "results/glm4_tokenizer_chunk_audit_20260705"
SECTION_COUNTS = AUDIT_DIR / "section_glm4_token_counts_20260705.csv"
META = ROOT / "results/star_token_proxy_full_2019_2023_20260702/ipo_business_technology_sections.csv"
TOKENIZER_NAME = "THUDM/glm-4-9b-chat-hf"


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
        is_header = counts[line] >= 3 and (
            "招股说明书" in line or "首次公开发行" in line or sec_name in line
        ) and len(line) < 120
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


def summarize(series: pd.Series) -> dict[str, float]:
    counts = np.ceil(series / 4000).astype(int)
    return {
        "total_tokens": float(series.sum()),
        "mean_tokens": float(series.mean()),
        "mean_ln_tokens": float(np.log(series).mean()),
        "approx_chunks_4000": int(counts.sum()),
        "firm_avg_chunks_4000": float(counts.mean()),
        "weighted_chunk_num_4000": float((counts * counts).sum() / counts.sum()),
        "avg_tokens_per_chunk_4000": float(series.sum() / counts.sum()),
    }


def main() -> None:
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME, trust_remote_code=True)
    sections = pd.read_csv(SECTION_COUNTS, dtype={"sec_code": str})
    meta = pd.read_csv(META, dtype={"sec_code": str}).fillna("")
    sections = sections.merge(meta[["sec_code", "announcement_date"]], on="sec_code", how="left")

    rows: list[dict[str, object]] = []
    for _, row in sections.iterrows():
        path = ROOT / str(row["section_file"])
        text = path.read_text(encoding="utf-8", errors="ignore")
        joined = dewrap_join(text, str(row.get("sec_name") or ""))
        spaced = dewrap_space(text, str(row.get("sec_name") or ""))
        compacted = compact(text)
        rows.append(
            {
                "sec_code": row["sec_code"],
                "sec_name": row.get("sec_name", ""),
                "year": str(row.get("announcement_date", ""))[:4],
                "raw_glm4_tokens": int(row["glm4_tokens"]),
                "dewrap_join_glm4_tokens": len(tokenizer.encode(joined, add_special_tokens=False)),
                "dewrap_space_glm4_tokens": len(tokenizer.encode(spaced, add_special_tokens=False)),
                "compact_glm4_tokens": len(tokenizer.encode(compacted, add_special_tokens=False)),
                "dewrap_join_compact_chars": len(compact(joined)),
            }
        )

    out = pd.DataFrame(rows)
    out_path = AUDIT_DIR / "section_glm4_normalization_counts_20260705.csv"
    out.to_csv(out_path, index=False, encoding="utf-8-sig")

    summary = {
        "paper": {
            "firms": 552,
            "chunks": 8683,
            "text_len_mean": 3866.817,
            "chunk_num_mean": 18.191,
            "lnN_tech_mean": 10.962,
        },
        "raw_layout": summarize(out["raw_glm4_tokens"]),
        "dewrap_join": summarize(out["dewrap_join_glm4_tokens"]),
        "dewrap_space": summarize(out["dewrap_space_glm4_tokens"]),
        "compact": summarize(out["compact_glm4_tokens"]),
    }
    (AUDIT_DIR / "summary_glm4_text_normalization_20260705.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(out_path)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
