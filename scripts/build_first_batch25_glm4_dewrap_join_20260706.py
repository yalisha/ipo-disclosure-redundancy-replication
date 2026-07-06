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
SOURCE_RUN = ROOT / "results/star_first_batch_missing_20260706"
OUT_DIR = ROOT / "results/glm4_dewrap_join_first_batch25_20260706"
TOKENIZER_NAME = "THUDM/glm-4-9b-chat-hf"
MAX_TOKENS = 4000

TARGET_CODES = {
    "688001", "688002", "688003", "688005", "688006",
    "688007", "688008", "688009", "688010", "688011",
    "688012", "688015", "688016", "688018", "688019",
    "688020", "688022", "688028", "688029", "688033",
    "688066", "688088", "688122", "688333", "688388",
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
    normalized_lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    for line in drop_page_boilerplate(normalized_lines, sec_name):
        if not line:
            if current:
                paragraphs.append("".join(current))
                current = []
            continue
        current.append(line)
    if current:
        paragraphs.append("".join(current))
    return "\n\n".join(paragraphs)


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


def main() -> None:
    sections_path = SOURCE_RUN / "ipo_business_technology_sections.csv"
    if not sections_path.exists():
        raise SystemExit(f"Missing sections file: {sections_path}")

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    section_dir = OUT_DIR / "business_technology_text"
    chunks_dir = OUT_DIR / "chunks"
    section_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_NAME, trust_remote_code=True)
    splitter = FastTokenSplitter(tokenizer, MAX_TOKENS)
    sections = pd.read_csv(sections_path, dtype={"sec_code": str}).fillna("")
    sections = sections[sections["sec_code"].isin(TARGET_CODES)].copy()
    sections = sections.sort_values(["announcement_date", "sec_code"]).reset_index(drop=True)

    section_rows: list[dict[str, object]] = []
    chunk_rows: list[dict[str, object]] = []
    for row in sections.to_dict("records"):
        source_path = ROOT / str(row["section_file"])
        raw = source_path.read_text(encoding="utf-8", errors="ignore")
        normalized = dewrap_join(raw, str(row.get("sec_name") or ""))
        section_tokens = splitter.token_len(normalized)
        chunks = splitter.split(normalized)

        section_path = section_dir / f"{row['sec_code']}_{row['announcement_id']}_business_technology.txt"
        section_path.write_text(normalized, encoding="utf-8")

        section_row = dict(row)
        section_row.update(
            {
                "section_file": str(section_path.relative_to(ROOT)),
                "source_section_file": row["section_file"],
                "normalization_mode": "dewrap_join",
                "tokenizer": TOKENIZER_NAME,
                "max_tokens": MAX_TOKENS,
                "tech_text_chars": len(normalized),
                "tech_text_compact_chars": len(compact(normalized)),
                "tech_text_glm4_tokens": section_tokens,
                "tech_text_token_proxy": section_tokens,
                "lnN_tech_glm4": math.log(section_tokens) if section_tokens > 0 else np.nan,
                "chunk_count": len(chunks),
                "token_mode": "glm4_dewrap_join",
            }
        )
        section_rows.append(section_row)

        for idx, chunk in enumerate(chunks, start=1):
            custom_id = f"{row['sec_code']}_{row['announcement_id']}_glm4_dewrap_join_chunk_{idx:04d}"
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
                    "normalization_mode": "dewrap_join",
                    "tokenizer": TOKENIZER_NAME,
                    "max_tokens": MAX_TOKENS,
                    "chunk_chars": len(chunk),
                    "chunk_compact_chars": len(compact(chunk)),
                    "chunk_glm4_tokens": token_count,
                    "Text_len": token_count,
                    "Chunk_num": len(chunks),
                    "chunk_token_proxy": token_count,
                }
            )

    section_df = pd.DataFrame(section_rows)
    chunk_df = pd.DataFrame(chunk_rows)
    section_df.to_csv(OUT_DIR / "ipo_business_technology_sections.csv", index=False, encoding="utf-8-sig")
    chunk_df.to_csv(OUT_DIR / "ipo_business_technology_chunks.csv", index=False, encoding="utf-8-sig")
    section_df[["sec_code", "sec_name", "announcement_date", "chunk_count", "tech_text_glm4_tokens"]].to_csv(
        OUT_DIR / "sample_firms_20260706.csv", index=False, encoding="utf-8-sig"
    )
    (OUT_DIR / "sample_codes_20260706.txt").write_text(",".join(section_df["sec_code"].astype(str)), encoding="utf-8")

    manifest = {
        "source_run": str(SOURCE_RUN.relative_to(ROOT)),
        "out_dir": str(OUT_DIR.relative_to(ROOT)),
        "normalization_mode": "dewrap_join",
        "tokenizer": TOKENIZER_NAME,
        "max_tokens": MAX_TOKENS,
        "firms": int(section_df["sec_code"].nunique()),
        "chunks": int(len(chunk_df)),
        "chunk_glm4_tokens_mean": float(pd.to_numeric(chunk_df["chunk_glm4_tokens"], errors="coerce").mean()),
        "tech_text_glm4_tokens_mean": float(pd.to_numeric(section_df["tech_text_glm4_tokens"], errors="coerce").mean()),
        "excluded_extra_codes": ["688099", "688188"],
    }
    (OUT_DIR / "manifest_20260706.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
