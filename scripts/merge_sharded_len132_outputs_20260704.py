#!/usr/bin/env python3
"""Merge sharded cot_v3b_len132_tight JSONL outputs back into canonical run."""

from __future__ import annotations

import argparse
import json
import shutil
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANONICAL_RUN = "star_token_proxy_full_2019_2023_20260702"
DEFAULT_PROMPT_MODE = "cot_v3b_len132_tight"


def jsonl_path(run_dir: Path, prompt_mode: str) -> Path:
    return run_dir / f"ipo_redundancy_llm_outputs_{prompt_mode}.jsonl"


def read_jsonl(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Bad JSONL at {path}:{line_no}: {exc}") from exc
            cid = str(row.get("custom_id", "")).strip()
            if not cid:
                raise ValueError(f"Missing custom_id at {path}:{line_no}")
            rows.append(row)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-run", default=DEFAULT_CANONICAL_RUN)
    parser.add_argument("--prompt-mode", default=DEFAULT_PROMPT_MODE)
    parser.add_argument(
        "--shard-prefix",
        default=f"{DEFAULT_CANONICAL_RUN}_shard",
        help="Shard run-name prefix under results/; all matching directories are merged.",
    )
    parser.add_argument("--apply", action="store_true", help="Replace canonical JSONL after validation.")
    parser.add_argument(
        "--prefer",
        choices=["canonical", "last"],
        default="canonical",
        help="How to resolve duplicate custom_id rows.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    results_dir = ROOT / "results"
    canonical_dir = results_dir / args.canonical_run
    canonical_path = jsonl_path(canonical_dir, args.prompt_mode)
    if not canonical_path.exists():
        raise SystemExit(f"Missing canonical JSONL: {canonical_path}")

    shard_dirs = sorted(p for p in results_dir.glob(f"{args.shard_prefix}*") if p.is_dir())
    if not shard_dirs:
        raise SystemExit(f"No shard dirs found for prefix: {args.shard_prefix}")

    rows_by_id: OrderedDict[str, dict[str, object]] = OrderedDict()
    duplicate_rows: list[dict[str, object]] = []
    source_counts: dict[str, int] = {}

    sources = [canonical_dir, *shard_dirs]
    for source in sources:
        rows = read_jsonl(jsonl_path(source, args.prompt_mode))
        source_counts[source.name] = len(rows)
        for row in rows:
            cid = str(row["custom_id"]).strip()
            if cid in rows_by_id:
                duplicate_rows.append({"custom_id": cid, "source": source.name})
                if args.prefer == "last":
                    rows_by_id[cid] = row
                continue
            rows_by_id[cid] = row

    chunks = pd.read_csv(canonical_dir / "ipo_business_technology_chunks.csv", dtype=str).fillna("")
    expected_ids = set(chunks["custom_id"].astype(str))
    merged_ids = set(rows_by_id)
    missing_ids = sorted(expected_ids - merged_ids)
    extra_ids = sorted(merged_ids - expected_ids)

    report = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "canonical_run": args.canonical_run,
        "prompt_mode": args.prompt_mode,
        "prefer": args.prefer,
        "sources": source_counts,
        "merged_rows": len(rows_by_id),
        "expected_chunks": len(expected_ids),
        "missing_count": len(missing_ids),
        "extra_count": len(extra_ids),
        "duplicate_count": len(duplicate_rows),
        "missing_ids_sample": missing_ids[:50],
        "extra_ids_sample": extra_ids[:50],
        "duplicates_sample": duplicate_rows[:50],
    }

    plan_dir = results_dir / f"{args.canonical_run}_shards"
    plan_dir.mkdir(parents=True, exist_ok=True)
    report_path = plan_dir / f"merge_report_{args.prompt_mode}_20260704.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    merged_path = canonical_path.with_suffix(".merged.tmp.jsonl")
    write_jsonl(merged_path, list(rows_by_id.values()))

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"merged_tmp={merged_path}")
    print(f"report={report_path}")

    if missing_ids or extra_ids:
        raise SystemExit("Coverage validation failed; canonical JSONL was not replaced.")

    if args.apply:
        backup_path = canonical_path.with_name(
            f"{canonical_path.name}.pre_shard_merge_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
        )
        shutil.copy2(canonical_path, backup_path)
        merged_path.replace(canonical_path)
        print(f"backup={backup_path}")
        print(f"replaced={canonical_path}")
    else:
        print("dry_run=true; pass --apply to replace canonical JSONL")


if __name__ == "__main__":
    main()
