#!/usr/bin/env python3
"""Prepare a two-firm sample for Codex/OpenAI batch extraction tests."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[0]
sys.path.insert(0, str(SCRIPT_DIR))

from build_ipo_redundancy_base_20260628 import (  # noqa: E402
    RUN_TAG_DEFAULT,
    download_extract,
    make_chunks_and_tasks,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-run", default=f"star_{RUN_TAG_DEFAULT}")
    parser.add_argument("--out-run", default="star_codex_test_20260628")
    parser.add_argument("--existing-sec-code", default="688099")
    parser.add_argument("--new-sec-code", default="688030")
    parser.add_argument("--max-chars", type=int, default=4000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source_dir = ROOT / "results" / args.source_run
    out_dir = ROOT / "results" / args.out_run
    selected_path = source_dir / "ipo_prospectus_selected_primary.csv"
    if not selected_path.exists():
        raise SystemExit(f"Missing selected primary file: {selected_path}")

    selected = pd.read_csv(selected_path, dtype=str).fillna("")
    wanted = [args.existing_sec_code, args.new_sec_code]
    sample = selected[selected["sec_code"].isin(wanted)].copy()
    missing = [code for code in wanted if code not in set(sample["sec_code"])]
    if missing:
        raise SystemExit(f"Selected primary docs missing sec_code(s): {', '.join(missing)}")
    sample["_order"] = sample["sec_code"].map({code: i for i, code in enumerate(wanted)})
    sample = sample.sort_values("_order").drop(columns=["_order"])

    raw_base = ROOT / "data" / "raw" / "cninfo_ipo_prospectus_star_20260628"
    pdf_dir = raw_base / "raw_pdf"
    text_dir = raw_base / "text"
    out_dir.mkdir(parents=True, exist_ok=True)

    download_rows: list[dict[str, object]] = []
    for i, (_, row) in enumerate(sample.iterrows(), start=1):
        print(f"[download] {i}/{len(sample)} {row.get('sec_code')} {row.get('sec_name')}", flush=True)
        status = download_extract(row, pdf_dir, text_dir)
        download_rows.append({**row.to_dict(), **status})
        time.sleep(0.08)

    downloaded = pd.DataFrame(download_rows)
    downloaded.to_csv(out_dir / "ipo_prospectus_downloaded.csv", index=False, encoding="utf-8-sig")
    sample.to_csv(out_dir / "sample_selected_primary.csv", index=False, encoding="utf-8-sig")

    section_df, chunk_df = make_chunks_and_tasks(downloaded, out_dir, args.max_chars)
    section_df.to_csv(out_dir / "ipo_business_technology_sections.csv", index=False, encoding="utf-8-sig")
    chunk_df.to_csv(out_dir / "ipo_business_technology_chunks.csv", index=False, encoding="utf-8-sig")

    print(f"[done] out={out_dir}", flush=True)
    print(f"[done] firms={len(section_df)} chunks={len(chunk_df)}", flush=True)
    if not section_df.empty:
        print(section_df[["sec_code", "sec_name", "section_status", "tech_text_compact_chars", "chunk_count"]].to_string(index=False), flush=True)


if __name__ == "__main__":
    main()
