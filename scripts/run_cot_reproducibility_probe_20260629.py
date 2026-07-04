#!/usr/bin/env python3
"""Run repeated Codex condensations for one IPO chunk and summarize stability."""

from __future__ import annotations

import argparse
import itertools
import json
import math
import re
import statistics
from collections import Counter
from datetime import datetime
from pathlib import Path

import pandas as pd

from run_ipo_redundancy_codex_cli_20260628 import (
    ROOT,
    build_prompt,
    call_codex,
    extract_json,
    parse_token_usage,
    score_count,
    token_proxy,
)


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def relevant_score(item: dict) -> float:
    counts = [score_count(item, f"n{i}") for i in range(6)]
    total = sum(counts)
    if total == 0:
        return math.nan
    return sum(i * count for i, count in enumerate(counts)) / total


def char_ngrams(text: str, n_min: int = 2, n_max: int = 4) -> Counter[str]:
    compact = compact_text(text)
    grams: Counter[str] = Counter()
    for n in range(n_min, n_max + 1):
        if len(compact) < n:
            continue
        grams.update(compact[i : i + n] for i in range(len(compact) - n + 1))
    return grams


def cosine(a: Counter[str], b: Counter[str]) -> float:
    if not a or not b:
        return math.nan
    common = set(a) & set(b)
    dot = sum(a[key] * b[key] for key in common)
    norm_a = math.sqrt(sum(value * value for value in a.values()))
    norm_b = math.sqrt(sum(value * value for value in b.values()))
    if norm_a == 0 or norm_b == 0:
        return math.nan
    return dot / (norm_a * norm_b)


def describe(values: list[float]) -> dict[str, float]:
    clean = [value for value in values if not math.isnan(value)]
    if not clean:
        return {"mean": math.nan, "sd": math.nan, "min": math.nan, "max": math.nan}
    return {
        "mean": statistics.mean(clean),
        "sd": statistics.stdev(clean) if len(clean) > 1 else 0.0,
        "min": min(clean),
        "max": max(clean),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-name", default="star_token_proxy_20260628")
    parser.add_argument("--prompt-mode", default="cot_v2")
    parser.add_argument("--custom-id", default="688099_1206491566_tok_chunk_0001")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--reasoning-effort", default="low")
    parser.add_argument("--model", default="")
    parser.add_argument("--timeout", type=int, default=1200)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = ROOT / "results" / args.run_name
    chunk_csv = run_dir / "ipo_business_technology_chunks.csv"
    chunks = pd.read_csv(chunk_csv, dtype={"sec_code": str})
    row = chunks.loc[chunks["custom_id"] == args.custom_id]
    if row.empty:
        raise SystemExit(f"custom_id not found: {args.custom_id}")
    base_row = row.iloc[0].to_dict()

    out_dir = run_dir / "reproducibility_probe"
    raw_dir = out_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = f"{args.prompt_mode}_{args.custom_id}_repeat{args.repeats}_{stamp}"
    jsonl_path = out_dir / f"{stem}.jsonl"
    metrics_path = out_dir / f"{stem}_metrics.csv"
    summary_path = out_dir / f"{stem}_summary.md"

    rows: list[dict[str, object]] = []
    usage_rows: list[dict[str, object]] = []
    for rep in range(1, args.repeats + 1):
        rep_row = dict(base_row)
        rep_custom_id = f"{args.custom_id}__rep{rep:02d}"
        rep_row["custom_id"] = rep_custom_id
        prompt_df = pd.DataFrame([rep_row])
        prompt = build_prompt(prompt_df, args.prompt_mode)
        label = f"{args.custom_id} repeat {rep}/{args.repeats}"
        last_message, stdout, stderr = call_codex(prompt, args, label)
        (raw_dir / f"{stem}_rep{rep:02d}_last_message.txt").write_text(
            last_message, encoding="utf-8"
        )
        (raw_dir / f"{stem}_rep{rep:02d}_stdout.txt").write_text(
            stdout, encoding="utf-8"
        )
        if stderr:
            (raw_dir / f"{stem}_rep{rep:02d}_stderr.txt").write_text(
                stderr, encoding="utf-8"
            )
        parsed = extract_json(last_message)
        items = parsed.get("items", [])
        if len(items) != 1:
            raise RuntimeError(f"Expected exactly one item for {label}, got {len(items)}")
        item = items[0]
        summary_text = str(item.get("summary_text", "")).strip()
        counts = {f"n{i}": score_count(item, f"n{i}") for i in range(6)}
        sentence_count = score_count(item, "sentence_count")
        sentence_count_reported = sum(counts.values())
        usage = parse_token_usage(stdout + "\n" + stderr)
        row_out = {
            "repeat": rep,
            "source_custom_id": args.custom_id,
            "custom_id": rep_custom_id,
            "sec_code": base_row.get("sec_code", ""),
            "sec_name": base_row.get("sec_name", ""),
            "chunk_index": base_row.get("chunk_index", ""),
            "chunk_token_proxy": int(base_row.get("chunk_token_proxy", 0)),
            "summary_text": summary_text,
            "summary_compact_chars": len(compact_text(summary_text)),
            "summary_token_proxy": token_proxy(summary_text),
            "summary_sentence_count": score_count(item, "summary_sentence_count"),
            "sentence_count": sentence_count,
            "sentence_count_reported": sentence_count_reported,
            "sentence_count_mismatch": sentence_count - sentence_count_reported,
            **counts,
            "relevant_score": relevant_score(item),
            "high_score_count": counts["n4"] + counts["n5"],
            "high_score_share": (counts["n4"] + counts["n5"]) / sentence_count
            if sentence_count
            else math.nan,
            "total_tokens": usage.get("total_tokens", ""),
            "input_tokens": usage.get("input_tokens", ""),
            "cached_tokens": usage.get("cached_tokens", ""),
            "output_tokens": usage.get("output_tokens", ""),
            "reasoning_tokens": usage.get("reasoning_tokens", ""),
            "token_usage_raw": usage.get("token_usage_raw", ""),
        }
        rows.append(row_out)
        usage_rows.append(usage)
        with jsonl_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row_out, ensure_ascii=False) + "\n")
        print(
            f"[{rep}/{args.repeats}] summary_token_proxy={row_out['summary_token_proxy']} "
            f"relevant_score={row_out['relevant_score']:.3f} "
            f"tokens={row_out['total_tokens']}"
        )

    df = pd.DataFrame(rows)
    summaries = df["summary_text"].astype(str).tolist()
    vectors = [char_ngrams(text) for text in summaries]
    pair_rows: list[dict[str, object]] = []
    sims: list[float] = []
    for (i, vec_i), (j, vec_j) in itertools.combinations(enumerate(vectors, 1), 2):
        sim = cosine(vec_i, vec_j)
        sims.append(sim)
        pair_rows.append({"repeat_a": i, "repeat_b": j, "char_ngram_cosine": sim})
    pair_df = pd.DataFrame(pair_rows)
    pair_path = out_dir / f"{stem}_pairwise_similarity.csv"
    pair_df.to_csv(pair_path, index=False, encoding="utf-8-sig")
    df.to_csv(metrics_path, index=False, encoding="utf-8-sig")

    length_desc = describe(df["summary_token_proxy"].astype(float).tolist())
    compact_desc = describe(df["summary_compact_chars"].astype(float).tolist())
    rel_desc = describe(df["relevant_score"].astype(float).tolist())
    sim_desc = describe(sims)
    token_total = sum(
        int(value) for value in df["total_tokens"].tolist() if str(value).strip()
    )
    lines = [
        "# cot_v2 5次重复凝练可复现性小测试",
        "",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 1. 设置",
        "",
        f"- prompt_mode：`{args.prompt_mode}`",
        f"- custom_id：`{args.custom_id}`",
        f"- 公司：{base_row.get('sec_code', '')} {base_row.get('sec_name', '')}",
        f"- chunk_index：{base_row.get('chunk_index', '')}",
        f"- chunk_token_proxy：{int(base_row.get('chunk_token_proxy', 0))}",
        f"- 重复次数：{args.repeats}",
        "",
        "## 2. 长度稳定性",
        "",
        "| 指标 | 均值 | 标准差 | 最小值 | 最大值 |",
        "|---|---:|---:|---:|---:|",
        f"| summary_token_proxy | {length_desc['mean']:.3f} | {length_desc['sd']:.3f} | {length_desc['min']:.3f} | {length_desc['max']:.3f} |",
        f"| summary_compact_chars | {compact_desc['mean']:.3f} | {compact_desc['sd']:.3f} | {compact_desc['min']:.3f} | {compact_desc['max']:.3f} |",
        f"| Relevant_score | {rel_desc['mean']:.3f} | {rel_desc['sd']:.3f} | {rel_desc['min']:.3f} | {rel_desc['max']:.3f} |",
        "",
        "## 3. 语义相似度代理",
        "",
        "这里先用中文字符 2-4 gram cosine 做低成本代理，不等同于原文的 embedding-3 语义向量。",
        "",
        "| 指标 | 值 |",
        "|---|---:|",
        f"| pairwise cosine mean | {sim_desc['mean']:.3f} |",
        f"| pairwise cosine sd | {sim_desc['sd']:.3f} |",
        f"| pairwise cosine min | {sim_desc['min']:.3f} |",
        f"| pairwise cosine max | {sim_desc['max']:.3f} |",
        "",
        "## 4. token 消耗",
        "",
        f"- total_tokens 合计：{token_total}",
        "",
        "## 5. 输出文件",
        "",
        f"- 明细：`{metrics_path.relative_to(ROOT)}`",
        f"- 两两相似度：`{pair_path.relative_to(ROOT)}`",
        f"- JSONL：`{jsonl_path.relative_to(ROOT)}`",
    ]
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {metrics_path}")
    print(f"Wrote {pair_path}")
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
