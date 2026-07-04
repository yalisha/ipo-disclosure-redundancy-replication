#!/usr/bin/env python3
"""Build OpenAI Batch API JSONL requests for IPO redundancy chunk condensation."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def parse_sec_codes(values: list[str]) -> set[str]:
    codes: set[str] = set()
    for value in values:
        codes.update(part.strip() for part in value.split(",") if part.strip())
    return codes


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def ultra_v2_messages(text: str) -> list[dict[str, str]]:
    prompt = (
        "你是招股说明书“业务与技术”章节的信息密度筛选器。请从原文中抽取最核心事实，用于衡量文本冗余度。\n"
        "硬性要求：输出一段中文，20-180个汉字；不要标题、编号、解释、评价、换行；不得输出“无”“无。”或空字符串。\n"
        "只保留主营业务、核心产品、关键技术、研发能力、市场地位、重要客户/供应商、产能或收入数字等事实。\n"
        "如果原文主要是行业背景，也要用20-80个汉字概括其行业事实，不要判空。\n"
        "删除页眉页脚、政策空话、行业常识、模板话、重复描述、无数字形容和法规合规铺陈。不得新增事实。\n\n"
        f"原文：\n{text}"
    )
    return [
        {"role": "system", "content": "你只输出一段20-180个汉字的忠实事实凝练。"},
        {"role": "user", "content": prompt},
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-name", default="star_codex_test_20260628")
    parser.add_argument("--sec-code", action="append", default=[], help="One or more sec_code values, comma-separated allowed.")
    parser.add_argument("--model", default="gpt-4.1-mini")
    parser.add_argument("--temperature", type=float, default=0)
    parser.add_argument("--max-completion-tokens", type=int, default=220)
    parser.add_argument("--prompt-mode", default="openai_batch_ultra_v2")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = ROOT / "results" / args.run_name
    chunks_path = run_dir / "ipo_business_technology_chunks.csv"
    if not chunks_path.exists():
        raise SystemExit(f"Missing chunk file: {chunks_path}")
    chunks = pd.read_csv(chunks_path, dtype=str).fillna("")
    sec_codes = parse_sec_codes(args.sec_code)
    if sec_codes:
        chunks = chunks[chunks["sec_code"].isin(sec_codes)].copy()
    if chunks.empty:
        raise SystemExit("No chunks selected.")

    out_path = run_dir / f"openai_batch_requests_{args.prompt_mode}.jsonl"
    rows = []
    total_input_chars = 0
    with out_path.open("w", encoding="utf-8") as f:
        for _, row in chunks.iterrows():
            chunk_path = ROOT / str(row["chunk_file"])
            text = chunk_path.read_text(encoding="utf-8", errors="ignore")
            total_input_chars += len(text)
            request = {
                "custom_id": str(row["custom_id"]),
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": args.model,
                    "messages": ultra_v2_messages(text),
                    "temperature": args.temperature,
                    "max_completion_tokens": args.max_completion_tokens,
                },
            }
            f.write(json.dumps(request, ensure_ascii=False) + "\n")
            rows.append(
                {
                    "custom_id": row["custom_id"],
                    "sec_code": row["sec_code"],
                    "sec_name": row["sec_name"],
                    "chunk_compact_chars": row["chunk_compact_chars"],
                }
            )

    manifest = {
        "run_name": args.run_name,
        "prompt_mode": args.prompt_mode,
        "model": args.model,
        "temperature": args.temperature,
        "max_completion_tokens": args.max_completion_tokens,
        "requests": len(rows),
        "firms": sorted(set(r["sec_code"] for r in rows)),
        "total_input_chars": total_input_chars,
        "jsonl_file": str(out_path.relative_to(ROOT)),
        "submit_note": [
            "Install the OpenAI Python SDK if needed: python -m pip install openai",
            "Set OPENAI_API_KEY, then upload with purpose='batch' and create a batch for endpoint '/v1/chat/completions'.",
        ],
    }
    manifest_path = run_dir / f"openai_batch_manifest_{args.prompt_mode}.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame(rows).to_csv(run_dir / f"openai_batch_manifest_{args.prompt_mode}.csv", index=False, encoding="utf-8-sig")
    print(f"[done] requests={len(rows)} out={out_path}", flush=True)
    print(f"[done] manifest={manifest_path}", flush=True)


if __name__ == "__main__":
    main()
