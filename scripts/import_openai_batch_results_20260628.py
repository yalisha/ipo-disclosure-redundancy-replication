#!/usr/bin/env python3
"""Import OpenAI Batch output JSONL into IPO redundancy tables."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def load_batch_output(path: Path, prompt_mode: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            cid = str(item.get("custom_id", ""))
            error = item.get("error") or {}
            response = item.get("response") or {}
            body = response.get("body") or {}
            content = ""
            model = body.get("model", "")
            if not error:
                try:
                    content = body["choices"][0]["message"]["content"]
                except Exception:
                    error = {"message": "missing choices[0].message.content"}
            rows.append(
                {
                    "custom_id": cid,
                    "model": model,
                    "temperature": "",
                    "prompt_mode": prompt_mode,
                    "summary_text": str(content or "").strip(),
                    "summary_chars": len(str(content or "").strip()),
                    "summary_compact_chars": len(compact_text(str(content or ""))),
                    "error": json.dumps(error, ensure_ascii=False) if error else "",
                }
            )
    return pd.DataFrame(rows)


def aggregate(run_dir: Path, prompt_mode: str) -> None:
    outputs_path = run_dir / f"ipo_redundancy_llm_outputs_{prompt_mode}.jsonl"
    chunks = pd.read_csv(run_dir / "ipo_business_technology_chunks.csv", dtype=str)
    sections = pd.read_csv(run_dir / "ipo_business_technology_sections.csv", dtype=str)
    outs = []
    with outputs_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                outs.append(json.loads(line))
    out_df = pd.DataFrame(outs)
    out_df = out_df[out_df.get("error", "").fillna("").eq("")].copy() if "error" in out_df.columns else out_df
    out_df = out_df.drop_duplicates(subset=["custom_id"], keep="last")
    out_df["summary_compact_chars"] = pd.to_numeric(out_df["summary_compact_chars"], errors="coerce")
    chunks["chunk_compact_chars"] = pd.to_numeric(chunks["chunk_compact_chars"], errors="coerce")
    merged = chunks.merge(out_df[["custom_id", "summary_compact_chars", "summary_chars", "summary_text"]], on="custom_id", how="left")
    merged.to_csv(run_dir / f"ipo_redundancy_chunk_with_llm_{prompt_mode}.csv", index=False, encoding="utf-8-sig")
    agg = (
        merged.groupby(["sec_code", "announcement_id"], dropna=False)
        .agg(
            chunks=("custom_id", "size"),
            completed_chunks=("summary_compact_chars", "count"),
            original_compact_chars=("chunk_compact_chars", "sum"),
            summary_compact_chars=("summary_compact_chars", "sum"),
        )
        .reset_index()
    )
    agg["llm_complete"] = agg["chunks"].eq(agg["completed_chunks"])
    agg["redundancy_partial"] = agg["original_compact_chars"] / agg["summary_compact_chars"].replace({0: pd.NA})
    agg["redundancy"] = agg["redundancy_partial"].where(agg["llm_complete"])
    keep_cols = [
        "sec_code",
        "sec_name",
        "announcement_id",
        "announcement_title",
        "announcement_date",
        "doc_type",
        "section_status",
        "tech_text_compact_chars",
        "chunk_count",
    ]
    firm = sections[[c for c in keep_cols if c in sections.columns]].merge(agg, on=["sec_code", "announcement_id"], how="left")
    firm.to_csv(run_dir / f"ipo_redundancy_firm_level_{prompt_mode}.csv", index=False, encoding="utf-8-sig")
    print(f"[aggregate] rows={len(firm)} out={run_dir / f'ipo_redundancy_firm_level_{prompt_mode}.csv'}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-name", default="star_codex_test_20260628")
    parser.add_argument("--batch-output-jsonl", required=True)
    parser.add_argument("--prompt-mode", default="openai_batch_ultra_v2")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = ROOT / "results" / args.run_name
    out_df = load_batch_output(Path(args.batch_output_jsonl), args.prompt_mode)
    out_path = run_dir / f"ipo_redundancy_llm_outputs_{args.prompt_mode}.jsonl"
    with out_path.open("w", encoding="utf-8") as f:
        for row in out_df.to_dict("records"):
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"[import] rows={len(out_df)} out={out_path}", flush=True)
    aggregate(run_dir, args.prompt_mode)


if __name__ == "__main__":
    main()
