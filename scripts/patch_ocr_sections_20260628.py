#!/usr/bin/env python3
"""Patch garbled prospectus text with OCR page-range extraction.

Use this only for PDFs where pdftotext returns unusable custom-font text.
The script updates the section/chunk/task files for a run while preserving an
extraction-method flag for audit.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

import pandas as pd

from build_ipo_redundancy_base_20260628 import compact_text, split_into_chunks, task_prompt


ROOT = Path(__file__).resolve().parents[1]


DEFAULT_PAGE_RANGES = {
    "star_batch002_20260628": {
        # PDF physical page ranges, inclusive. Confirmed by OCR probe.
        "688208": (97, 220),
        "688189": (110, 304),
    }
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--dpi", type=int, default=150)
    parser.add_argument("--max-chars", type=int, default=4000)
    parser.add_argument(
        "--page-range",
        action="append",
        default=[],
        help="Override or add OCR range as sec_code:start:end, PDF physical pages inclusive.",
    )
    return parser.parse_args()


def page_ranges(args: argparse.Namespace) -> dict[str, tuple[int, int]]:
    ranges = dict(DEFAULT_PAGE_RANGES.get(args.run_name, {}))
    for value in args.page_range:
        code, start, end = value.split(":")
        ranges[code.strip()] = (int(start), int(end))
    return ranges


def run_cmd(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{proc.stderr[-1000:]}")


def ocr_pdf_range(pdf_path: Path, out_dir: Path, start_page: int, end_page: int, dpi: int) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = out_dir / "page"
    run_cmd(["pdftoppm", "-r", str(dpi), "-f", str(start_page), "-l", str(end_page), "-png", str(pdf_path), str(prefix)])
    texts: list[str] = []
    for image in sorted(out_dir.glob("page-*.png")):
        txt_path = image.with_suffix("")
        run_cmd(["tesseract", str(image), str(txt_path), "-l", "chi_sim+eng", "--psm", "6", "quiet"])
        page_text_path = image.with_suffix(".txt")
        text = page_text_path.read_text(encoding="utf-8", errors="ignore").strip()
        texts.append(f"\n\n[OCR_PAGE {image.stem.split('-')[-1]}]\n{text}")
    return "\n".join(texts).strip()


def rebuild_tasks(chunk_df: pd.DataFrame, task_path: Path) -> None:
    with task_path.open("w", encoding="utf-8") as task_f:
        for _, row in chunk_df.iterrows():
            chunk_path = ROOT / str(row["chunk_file"])
            chunk = chunk_path.read_text(encoding="utf-8", errors="ignore")
            task_f.write(
                json.dumps(
                    {
                        "custom_id": row["custom_id"],
                        "sec_code": row.get("sec_code", ""),
                        "announcement_id": row.get("announcement_id", ""),
                        "messages": [
                            {"role": "system", "content": "你只做忠实文本凝练，不新增事实。"},
                            {"role": "user", "content": task_prompt(chunk)},
                        ],
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )


def main() -> None:
    args = parse_args()
    ranges = page_ranges(args)
    if not ranges:
        raise SystemExit("No page ranges configured.")

    run_dir = ROOT / "results" / args.run_name
    downloaded_path = run_dir / "ipo_prospectus_downloaded.csv"
    sections_path = run_dir / "ipo_business_technology_sections.csv"
    chunks_path = run_dir / "ipo_business_technology_chunks.csv"
    if not downloaded_path.exists() or not sections_path.exists() or not chunks_path.exists():
        raise SystemExit(f"Missing run files under {run_dir}")

    downloaded = pd.read_csv(downloaded_path, dtype=str).fillna("")
    sections = pd.read_csv(sections_path, dtype=str).fillna("")
    chunks = pd.read_csv(chunks_path, dtype=str).fillna("")
    if "section_extraction_method" not in sections.columns:
        sections["section_extraction_method"] = sections["section_status"].map(lambda x: "pdftotext_regex" if x == "ok" else "")
    for col in ["ocr_pdf_start_page", "ocr_pdf_end_page", "ocr_dpi"]:
        if col not in sections.columns:
            sections[col] = ""

    section_dir = run_dir / "business_technology_text"
    chunks_dir = run_dir / "chunks"
    ocr_root = run_dir / "ocr_pages"
    section_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)
    ocr_root.mkdir(parents=True, exist_ok=True)

    patched_chunk_rows: list[dict[str, object]] = []
    patched_codes = set(ranges)
    for code, (start_page, end_page) in ranges.items():
        match = downloaded[downloaded["sec_code"].eq(code)]
        if match.empty:
            raise SystemExit(f"Missing downloaded row for {code}")
        row = match.iloc[0]
        pdf_path = ROOT / str(row["pdf_file"])
        if not pdf_path.exists():
            raise SystemExit(f"Missing PDF for {code}: {pdf_path}")
        ocr_dir = ocr_root / f"{code}_{start_page}_{end_page}"
        if ocr_dir.exists():
            shutil.rmtree(ocr_dir)
        print(f"[ocr] {code} pages={start_page}-{end_page} pdf={pdf_path.name}", flush=True)
        section = ocr_pdf_range(pdf_path, ocr_dir, start_page, end_page, args.dpi)
        announcement_id = str(row["announcement_id"])
        section_path = section_dir / f"{code}_{announcement_id}_business_technology.txt"
        section_path.write_text(section, encoding="utf-8")
        code_chunks = split_into_chunks(section, max_chars=args.max_chars)
        print(f"[patch] {code} chars={len(section)} compact={len(compact_text(section))} chunks={len(code_chunks)}", flush=True)

        mask = sections["sec_code"].eq(code) & sections["announcement_id"].eq(announcement_id)
        if not mask.any():
            raise SystemExit(f"Missing section row for {code}/{announcement_id}")
        sections.loc[mask, "section_status"] = "ok"
        sections.loc[mask, "section_file"] = str(section_path.relative_to(ROOT))
        sections.loc[mask, "section_start_char"] = ""
        sections.loc[mask, "section_end_char"] = ""
        sections.loc[mask, "tech_text_chars"] = len(section)
        sections.loc[mask, "tech_text_compact_chars"] = len(compact_text(section))
        sections.loc[mask, "chunk_count"] = len(code_chunks)
        sections.loc[mask, "section_extraction_method"] = "ocr_page_range"
        sections.loc[mask, "ocr_pdf_start_page"] = start_page
        sections.loc[mask, "ocr_pdf_end_page"] = end_page
        sections.loc[mask, "ocr_dpi"] = args.dpi

        for idx, chunk in enumerate(code_chunks, start=1):
            custom_id = f"{code}_{announcement_id}_chunk_{idx:04d}"
            chunk_file = chunks_dir / f"{custom_id}.txt"
            chunk_file.write_text(chunk, encoding="utf-8")
            patched_chunk_rows.append(
                {
                    "custom_id": custom_id,
                    "sec_code": code,
                    "sec_name": row.get("sec_name", ""),
                    "announcement_id": announcement_id,
                    "chunk_index": idx,
                    "chunk_count": len(code_chunks),
                    "chunk_file": str(chunk_file.relative_to(ROOT)),
                    "chunk_chars": len(chunk),
                    "chunk_compact_chars": len(compact_text(chunk)),
                }
            )

    chunks = chunks[~chunks["sec_code"].isin(patched_codes)].copy()
    chunks = pd.concat([chunks, pd.DataFrame(patched_chunk_rows)], ignore_index=True)
    order = sections[["sec_code", "announcement_id"]].reset_index().rename(columns={"index": "_firm_order"})
    chunks = chunks.merge(order, on=["sec_code", "announcement_id"], how="left")
    chunks["chunk_index_num"] = pd.to_numeric(chunks["chunk_index"], errors="coerce")
    chunks = chunks.sort_values(["_firm_order", "chunk_index_num"]).drop(columns=["_firm_order", "chunk_index_num"])

    sections.to_csv(sections_path, index=False, encoding="utf-8-sig")
    chunks.to_csv(chunks_path, index=False, encoding="utf-8-sig")
    rebuild_tasks(chunks, run_dir / "ipo_redundancy_llm_tasks.jsonl")
    print(f"[done] sections={len(sections)} chunks={len(chunks)} patched={','.join(sorted(patched_codes))}", flush=True)


if __name__ == "__main__":
    main()
