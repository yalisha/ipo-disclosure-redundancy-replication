#!/usr/bin/env python3
"""Submit or inspect an OpenAI Batch job for IPO redundancy.

Requires:
  pip install openai
  export OPENAI_API_KEY=...
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def get_client():
    try:
        from openai import OpenAI
    except Exception as exc:
        raise SystemExit("Missing OpenAI SDK. Install it with: python -m pip install openai") from exc
    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Missing OPENAI_API_KEY.")
    return OpenAI()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    submit = sub.add_parser("submit")
    submit.add_argument("--run-name", default="star_codex_test_20260628")
    submit.add_argument("--request-file", default="openai_batch_requests_openai_batch_ultra_v2.jsonl")
    submit.add_argument("--completion-window", default="24h")
    submit.add_argument("--metadata", default='{"project":"ipo_redundancy"}')

    status = sub.add_parser("status")
    status.add_argument("--batch-id", required=True)

    download = sub.add_parser("download")
    download.add_argument("--batch-id", required=True)
    download.add_argument("--out", required=True)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = get_client()
    if args.cmd == "submit":
        request_path = ROOT / "results" / args.run_name / args.request_file
        if not request_path.exists():
            raise SystemExit(f"Missing request file: {request_path}")
        uploaded = client.files.create(file=request_path.open("rb"), purpose="batch")
        metadata = json.loads(args.metadata)
        batch = client.batches.create(
            input_file_id=uploaded.id,
            endpoint="/v1/chat/completions",
            completion_window=args.completion_window,
            metadata=metadata,
        )
        print(json.dumps(batch.model_dump(), ensure_ascii=False, indent=2))
    elif args.cmd == "status":
        batch = client.batches.retrieve(args.batch_id)
        print(json.dumps(batch.model_dump(), ensure_ascii=False, indent=2))
    elif args.cmd == "download":
        batch = client.batches.retrieve(args.batch_id)
        if not batch.output_file_id:
            raise SystemExit(f"Batch has no output_file_id yet. status={batch.status}")
        content = client.files.content(batch.output_file_id)
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(content.read())
        print(f"[download] {out_path}")


if __name__ == "__main__":
    main()
