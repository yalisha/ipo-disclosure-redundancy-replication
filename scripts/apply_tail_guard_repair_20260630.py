#!/usr/bin/env python3
"""Merge tail-repair Codex outputs into a base prompt-mode output file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def parse_values(values: list[str]) -> set[str]:
    parsed: set[str] = set()
    for value in values:
        parsed.update(part.strip() for part in value.split(",") if part.strip())
    return parsed


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        raise SystemExit(f"Missing JSONL: {path}")
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-name", default="star_token_proxy_20260628")
    parser.add_argument("--base-mode", default="cot_v3b")
    parser.add_argument("--repair-mode", default="cot_v3b_tailfix")
    parser.add_argument("--output-mode", default="cot_v3b_tailguard")
    parser.add_argument("--sec-code", action="append", default=[])
    parser.add_argument("--min-summary-token", type=float, default=80)
    parser.add_argument("--max-redun", type=float, default=50)
    parser.add_argument("--min-chunk-token", type=float, default=1000)
    parser.add_argument("--min-relevant-score", type=float, default=None)
    parser.add_argument("--preserve-base-scores", action="store_true")
    args = parser.parse_args()

    run_dir = ROOT / "results" / args.run_name
    chunk_path = run_dir / f"ipo_redundancy_chunk_with_llm_{args.base_mode}.csv"
    if not chunk_path.exists():
        raise SystemExit(f"Missing chunk diagnostics: {chunk_path}")

    chunks = pd.read_csv(chunk_path, dtype={"sec_code": str})
    for col in ["chunk_token_proxy", "summary_token_proxy"]:
        chunks[col] = pd.to_numeric(chunks[col], errors="coerce")
    chunks["redundancy_chunk"] = chunks["chunk_token_proxy"] / chunks["summary_token_proxy"]
    chunks = chunks[chunks["summary_token_proxy"].notna()].copy()

    sec_codes = parse_values(args.sec_code)
    if sec_codes:
        chunks = chunks[chunks["sec_code"].isin(sec_codes)].copy()

    tail_mask = (
        chunks["chunk_token_proxy"].ge(args.min_chunk_token)
        & (
            chunks["summary_token_proxy"].lt(args.min_summary_token)
            | chunks["redundancy_chunk"].gt(args.max_redun)
        )
    )
    if args.min_relevant_score is not None:
        if "relevant_score" not in chunks.columns:
            raise SystemExit("--min-relevant-score requires relevant_score in chunk diagnostics.")
        chunks["relevant_score"] = pd.to_numeric(chunks["relevant_score"], errors="coerce")
        tail_mask = tail_mask & chunks["relevant_score"].ge(args.min_relevant_score)
    tail_ids = set(chunks.loc[tail_mask, "custom_id"].astype(str))
    if not tail_ids:
        raise SystemExit("No tail chunks selected.")

    base_path = run_dir / f"ipo_redundancy_llm_outputs_{args.base_mode}.jsonl"
    repair_path = run_dir / f"ipo_redundancy_llm_outputs_{args.repair_mode}.jsonl"
    output_path = run_dir / f"ipo_redundancy_llm_outputs_{args.output_mode}.jsonl"

    base_rows = load_jsonl(base_path)
    repair_rows = load_jsonl(repair_path)
    repair_by_id = {str(row.get("custom_id")): row for row in repair_rows}
    missing = sorted(tail_ids - set(repair_by_id))
    if missing:
        raise SystemExit(f"Missing repair rows for {len(missing)} tail chunks: {missing[:10]}")

    merged_rows: list[dict] = []
    replaced = 0
    for row in base_rows:
        cid = str(row.get("custom_id"))
        if cid in tail_ids:
            repaired_source = dict(repair_by_id[cid])
            if args.preserve_base_scores:
                repaired = dict(row)
                for key in [
                    "summary_text",
                    "summary_chars",
                    "summary_compact_chars",
                    "summary_token_proxy",
                    "summary_sentence_count",
                ]:
                    repaired[key] = repaired_source.get(key, repaired.get(key))
                repaired["tail_repair_prompt_mode"] = repaired_source.get("prompt_mode", args.repair_mode)
                repaired["tail_repair_batch_label"] = repaired_source.get("batch_label", "")
                repaired["tail_repair_batch_total_tokens"] = repaired_source.get("batch_total_tokens", "")
            else:
                repaired = repaired_source
            repaired["prompt_mode"] = args.output_mode
            repaired["tail_repaired_from"] = args.base_mode
            merged_rows.append(repaired)
            replaced += 1
        else:
            kept = dict(row)
            kept["prompt_mode"] = args.output_mode
            merged_rows.append(kept)

    write_jsonl(output_path, merged_rows)
    tail_report = chunks.loc[
        tail_mask,
        ["custom_id", "sec_code", "sec_name", "chunk_token_proxy", "summary_token_proxy", "redundancy_chunk"],
    ].copy()
    tail_report.to_csv(run_dir / f"{args.output_mode}_tail_ids.csv", index=False, encoding="utf-8-sig")
    print(f"[tailguard] tail_ids={len(tail_ids)} replaced={replaced} out={output_path}")


if __name__ == "__main__":
    main()
