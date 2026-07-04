#!/usr/bin/env python3
"""Compute embedding cosine similarity for repeated IPO summaries.

The default configuration matches the paper's reproducibility check as closely
as possible: ZhipuAI embedding-3, 2048 dimensions, pairwise cosine similarity.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any

import requests


ROOT = Path(__file__).resolve().parents[1]


def find_api_key(explicit_env: str | None) -> tuple[str, str]:
    candidates = []
    if explicit_env:
        candidates.append(explicit_env)
    candidates.extend(["ZHIPUAI_API_KEY", "ZAI_API_KEY", "BIGMODEL_API_KEY", "SILICONFLOW_API_KEY"])
    for name in candidates:
        value = os.environ.get(name)
        if value:
            return name, value
    raise SystemExit(
        "No embedding API key found. Set one of: ZHIPUAI_API_KEY, ZAI_API_KEY, "
        "BIGMODEL_API_KEY, SILICONFLOW_API_KEY"
    )


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
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


def load_texts(path: Path, id_column: str, text_column: str) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    items = []
    for idx, row in enumerate(rows, 1):
        text = (row.get(text_column) or "").strip()
        if not text:
            continue
        item_id = (row.get(id_column) or str(idx)).strip()
        items.append({"id": item_id, "text": text})
    if len(items) < 2:
        raise SystemExit("Need at least two non-empty texts to compute pairwise similarity.")
    return items


def post_embeddings(
    texts: list[str],
    api_key: str,
    base_url: str,
    model: str,
    dimensions: int,
    timeout: int,
) -> tuple[list[list[float]], dict[str, Any]]:
    url = base_url.rstrip("/") + "/embeddings"
    payload: dict[str, Any] = {"model": model, "input": texts}
    if dimensions:
        payload["dimensions"] = dimensions
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=timeout,
    )
    try:
        data = response.json()
    except Exception:
        data = {"raw_text": response.text}
    if response.status_code >= 400:
        raise SystemExit(
            f"Embedding API failed with HTTP {response.status_code}: "
            f"{json.dumps(data, ensure_ascii=False)[:1000]}"
        )
    vectors = data.get("data", [])
    if not isinstance(vectors, list) or not vectors:
        raise SystemExit(f"No embedding data returned: {json.dumps(data, ensure_ascii=False)[:1000]}")
    vectors = sorted(vectors, key=lambda item: item.get("index", 0))
    embeddings = [item["embedding"] for item in vectors]
    return embeddings, data.get("usage", {})


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def safe_stem(text: str) -> str:
    return "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "_" for ch in text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    default_base_url = os.environ.get(
        "EMBEDDING_BASE_URL",
        os.environ.get("SILICONFLOW_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
    )
    parser.add_argument(
        "--metrics-csv",
        default=(
            "results/star_token_proxy_20260628/reproducibility_probe/"
            "cot_v2_688099_1206491566_tok_chunk_0001_repeat5_20260629_161940_metrics.csv"
        ),
    )
    parser.add_argument("--id-column", default="repeat")
    parser.add_argument("--text-column", default="summary_text")
    parser.add_argument("--base-url", default=default_base_url)
    parser.add_argument("--model", default="embedding-3")
    parser.add_argument("--dimensions", type=int, default=2048)
    parser.add_argument("--api-key-env", default="")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--out-dir", default="")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    metrics_csv = Path(args.metrics_csv)
    if not metrics_csv.is_absolute():
        metrics_csv = ROOT / metrics_csv
    items = load_texts(metrics_csv, args.id_column, args.text_column)
    key_name, api_key = find_api_key(args.api_key_env or None)
    embeddings, usage = post_embeddings(
        [item["text"] for item in items],
        api_key,
        args.base_url,
        args.model,
        args.dimensions,
        args.timeout,
    )
    if len(embeddings) != len(items):
        raise SystemExit(f"Expected {len(items)} embeddings, got {len(embeddings)}")
    dims = {len(vec) for vec in embeddings}
    if len(dims) != 1:
        raise SystemExit(f"Returned embedding dimensions differ: {sorted(dims)}")

    out_dir = Path(args.out_dir) if args.out_dir else metrics_csv.parent
    if not out_dir.is_absolute():
        out_dir = ROOT / out_dir
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    stem = f"{metrics_csv.stem}_{safe_stem(args.model)}_dim{args.dimensions}_{stamp}"

    embedding_path = out_dir / f"{stem}_embeddings.jsonl"
    with embedding_path.open("w", encoding="utf-8") as f:
        for item, vector in zip(items, embeddings):
            f.write(
                json.dumps(
                    {"id": item["id"], "text": item["text"], "embedding": vector},
                    ensure_ascii=False,
                )
                + "\n"
            )

    pair_rows: list[dict[str, Any]] = []
    sims: list[float] = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            sim = cosine(embeddings[i], embeddings[j])
            sims.append(sim)
            pair_rows.append(
                {
                    "id_a": items[i]["id"],
                    "id_b": items[j]["id"],
                    "embedding_cosine": sim,
                }
            )
    pair_path = out_dir / f"{stem}_pairwise_similarity.csv"
    write_csv(pair_path, pair_rows)

    desc = describe(sims)
    summary_path = out_dir / f"{stem}_summary.md"
    lines = [
        "# Embedding 语义相似度复刻",
        "",
        f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 1. 设置",
        "",
        f"- metrics_csv：`{metrics_csv.relative_to(ROOT)}`",
        f"- model：`{args.model}`",
        f"- dimensions：`{next(iter(dims))}`",
        f"- base_url：`{args.base_url}`",
        f"- api_key_env：`{key_name}`",
        f"- 文本数量：{len(items)}",
        "",
        "## 2. 两两 cosine",
        "",
        "| 指标 | 值 |",
        "|---|---:|",
        f"| mean | {desc['mean']:.6f} |",
        f"| sd | {desc['sd']:.6f} |",
        f"| min | {desc['min']:.6f} |",
        f"| max | {desc['max']:.6f} |",
        "",
        "## 3. usage",
        "",
        "```json",
        json.dumps(usage, ensure_ascii=False, indent=2),
        "```",
        "",
        "## 4. 输出文件",
        "",
        f"- embeddings：`{embedding_path.relative_to(ROOT)}`",
        f"- pairwise_similarity：`{pair_path.relative_to(ROOT)}`",
    ]
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Embedding cosine mean={desc['mean']:.6f}, sd={desc['sd']:.6f}")
    print(f"Wrote {summary_path}")
    print(f"Wrote {pair_path}")
    print(f"Wrote {embedding_path}")


if __name__ == "__main__":
    main()
