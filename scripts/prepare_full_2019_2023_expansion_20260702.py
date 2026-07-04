#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd


PROJECT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
sys.path.insert(0, str(PROJECT / "scripts"))

from build_ipo_redundancy_base_20260628 import (  # noqa: E402
    ROOT,
    compact_text,
    download_extract,
    extract_business_technology,
)


BASE_SELECTED = PROJECT / "results/star_20260628/ipo_prospectus_selected_primary.csv"
BASE_COMPLETED_RUN = PROJECT / "results/star_token_proxy_250_late50_20260702"
BASE_COMPLETED_MODE = "cot_v3b_scoregate_targeted_300_late50"
REMAINING_RUN = PROJECT / "results/star_remaining_251_543_20260702"
FULL_RUN = PROJECT / "results/star_token_proxy_full_2019_2023_20260702"
OUTCOME = PROJECT / "results/outcome_variable_probe_csmar_patent_20260702/outcome_variables_star_firm_level_csmar_patent_20260702.csv"
MAX_UNITS = 4000


def token_proxy(text: str) -> int:
    return math.ceil(len(compact_text(text)) / 2)


def normalize_for_section(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def split_by_budget(text: str, max_units: int = MAX_UNITS) -> list[str]:
    clean = normalize_for_section(text).strip()
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", clean) if p.strip()]
    chunks: list[str] = []
    current = ""

    def flush() -> None:
        nonlocal current
        if current.strip():
            chunks.append(current.strip())
            current = ""

    def append_piece(piece: str) -> None:
        nonlocal current
        piece = piece.strip()
        if not piece:
            return
        sep = "\n\n" if "\n" in piece else "\n"
        candidate = f"{current}{sep if current else ''}{piece}"
        if current and token_proxy(candidate) > max_units:
            flush()
            candidate = piece
        if token_proxy(candidate) <= max_units:
            current = candidate
            return

        start = 0
        while start < len(piece):
            lo, hi = start + 1, len(piece)
            best = lo
            while lo <= hi:
                mid = (lo + hi) // 2
                part = piece[start:mid]
                if token_proxy(part) <= max_units:
                    best = mid
                    lo = mid + 1
                else:
                    hi = mid - 1
            part = piece[start:best].strip()
            if part:
                if current:
                    flush()
                chunks.append(part)
            start = max(best, start + 1)

    for para in paragraphs:
        if token_proxy(para) > max_units:
            for sentence in [s.strip() for s in re.split(r"(?<=[。！？；;])", para) if s.strip()]:
                append_piece(sentence)
        else:
            append_piece(para)
    flush()
    return chunks


def z6(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text.zfill(6) if text.isdigit() else text


def read_completed_codes() -> set[str]:
    firm = pd.read_csv(
        BASE_COMPLETED_RUN / f"ipo_redundancy_firm_level_{BASE_COMPLETED_MODE}.csv",
        dtype={"sec_code": str},
    )
    complete = firm["llm_complete"].astype(str).str.lower().isin(["true", "1"])
    return set(firm.loc[complete, "sec_code"].map(z6))


def year_counts(df: pd.DataFrame, year_col: str = "listing_year") -> dict[str, int]:
    counts = df.groupby(year_col)["code"].nunique().dropna()
    return {str(int(k)): int(v) for k, v in counts.items()}


def copy_completed_run() -> None:
    FULL_RUN.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(BASE_COMPLETED_RUN, FULL_RUN, dirs_exist_ok=True)


def load_base_numbers(completed_codes: set[str]) -> dict[str, object]:
    base = pd.read_csv(BASE_SELECTED, dtype=str)
    base["code"] = base["sec_code"].map(z6)
    base["announcement_year"] = pd.to_datetime(base["announcement_date"], errors="coerce").dt.year
    outcome = pd.read_csv(OUTCOME, dtype={"code": str})
    outcome["code"] = outcome["code"].map(z6)
    outcome["listing_year"] = pd.to_numeric(outcome["listing_year"], errors="coerce").astype("Int64")
    merged = base.merge(
        outcome[["code", "first_trade_date", "listing_year", "FInvention_ln1p_auth"]],
        on="code",
        how="left",
    )
    merged["llm_complete_current"] = merged["code"].isin(completed_codes)
    missing = merged[~merged["llm_complete_current"]].copy()
    return {
        "base_rows": int(len(merged)),
        "base_codes": int(merged["code"].nunique()),
        "base_by_listing_year": year_counts(merged),
        "completed_codes": int(len(completed_codes)),
        "completed_by_listing_year": year_counts(merged[merged["llm_complete_current"]]),
        "missing_codes": int(missing["code"].nunique()),
        "missing_by_listing_year": year_counts(missing),
        "base_finvention_nonmissing": int(merged["FInvention_ln1p_auth"].notna().sum()),
        "completed_finvention_nonmissing": int(
            merged.loc[merged["llm_complete_current"], "FInvention_ln1p_auth"].notna().sum()
        ),
        "missing_finvention_nonmissing": int(missing["FInvention_ln1p_auth"].notna().sum()),
    }


def download_one(row: dict[str, object], pdf_dir: Path, text_dir: Path) -> dict[str, object]:
    status = download_extract(pd.Series(row), pdf_dir, text_dir)
    return {**row, **status}


def build_downloads(selected_missing: pd.DataFrame, workers: int) -> pd.DataFrame:
    raw_base = PROJECT / "data/raw/cninfo_ipo_prospectus_star_remaining_251_543_20260702"
    pdf_dir = raw_base / "raw_pdf"
    text_dir = raw_base / "text"
    rows = selected_missing.to_dict("records")
    out: list[dict[str, object]] = []
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(download_one, row, pdf_dir, text_dir): row for row in rows}
        for i, future in enumerate(as_completed(futures), start=1):
            row = futures[future]
            try:
                item = future.result()
            except Exception as exc:
                item = {**row, "download_status": f"error_{type(exc).__name__}", "download_error": str(exc)[:500]}
            out.append(item)
            print(
                f"[download] {i}/{len(rows)} {item.get('sec_code')} {item.get('download_status')}",
                flush=True,
            )
            time.sleep(0.02)
    df = pd.DataFrame(out)
    df = df.sort_values(["announcement_date", "sec_code", "announcement_id"])
    REMAINING_RUN.mkdir(parents=True, exist_ok=True)
    df.to_csv(REMAINING_RUN / "ipo_prospectus_downloaded.csv", index=False, encoding="utf-8-sig")
    return df


def append_missing_token_base(downloaded: pd.DataFrame, existing_codes: set[str]) -> dict[str, object]:
    section_dir = FULL_RUN / "business_technology_text"
    chunks_dir = FULL_RUN / "chunks"
    section_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)

    existing_sections = pd.read_csv(FULL_RUN / "ipo_business_technology_sections.csv", dtype=str).fillna("")
    existing_chunks = pd.read_csv(FULL_RUN / "ipo_business_technology_chunks.csv", dtype=str).fillna("")
    existing_chunk_ids = set(existing_chunks["custom_id"].astype(str))

    section_rows: list[dict[str, object]] = []
    chunk_rows: list[dict[str, object]] = []
    for _, row in downloaded.iterrows():
        code = z6(row.get("sec_code"))
        if code in existing_codes:
            continue
        text = ""
        txt_file = str(row.get("txt_file") or "")
        if txt_file:
            path = ROOT / txt_file
            if path.exists():
                text = path.read_text(encoding="utf-8", errors="ignore")
        section, status, start, end = extract_business_technology(text) if text else ("", "no_text", -1, -1)
        section_path = section_dir / f"{code}_{row.get('announcement_id')}_business_technology.txt"
        chunks: list[str] = []
        if section and status == "ok":
            section_path.write_text(section, encoding="utf-8")
            chunks = split_by_budget(section, MAX_UNITS)

        section_rows.append(
            {
                **{
                    k: row.get(k, "")
                    for k in [
                        "sec_code",
                        "sec_name",
                        "announcement_id",
                        "announcement_title",
                        "announcement_date",
                        "doc_type",
                        "pdf_url",
                        "download_status",
                        "pdf_file",
                        "txt_file",
                    ]
                },
                "source_run_name": "star_remaining_251_543_20260702",
                "section_status": status,
                "section_file": str(section_path.relative_to(ROOT)) if section else "",
                "section_start_char": start,
                "section_end_char": end,
                "full_text_chars": row.get("full_text_chars", 0),
                "tech_text_chars": len(section),
                "tech_text_compact_chars": len(compact_text(section)),
                "token_mode": "char2_proxy",
                "max_units": MAX_UNITS,
                "tech_text_token_proxy": token_proxy(section) if section else 0,
                "chunk_count": len(chunks),
                "chunk_count_token_proxy": len(chunks),
            }
        )

        for idx, chunk in enumerate(chunks, start=1):
            custom_id = f"{code}_{row.get('announcement_id')}_tok_chunk_{idx:04d}"
            if custom_id in existing_chunk_ids:
                continue
            chunk_path = chunks_dir / f"{custom_id}.txt"
            chunk_path.write_text(chunk, encoding="utf-8")
            chunk_rows.append(
                {
                    "custom_id": custom_id,
                    "sec_code": code,
                    "sec_name": row.get("sec_name", ""),
                    "announcement_id": row.get("announcement_id", ""),
                    "source_run_name": "star_remaining_251_543_20260702",
                    "chunk_index": idx,
                    "chunk_count": len(chunks),
                    "chunk_file": str(chunk_path.relative_to(ROOT)),
                    "chunk_token_proxy": token_proxy(chunk),
                    "chunk_chars": len(chunk),
                    "chunk_compact_chars": len(compact_text(chunk)),
                }
            )

    new_sections = pd.DataFrame(section_rows)
    new_chunks = pd.DataFrame(chunk_rows)
    combined_sections = pd.concat([existing_sections, new_sections], ignore_index=True)
    combined_sections["sec_code"] = combined_sections["sec_code"].map(z6)
    combined_sections = combined_sections.drop_duplicates(["sec_code", "announcement_id"], keep="first")
    combined_chunks = pd.concat([existing_chunks, new_chunks], ignore_index=True)
    combined_chunks["sec_code"] = combined_chunks["sec_code"].map(z6)
    combined_chunks = combined_chunks.drop_duplicates("custom_id", keep="first")
    combined_sections.to_csv(FULL_RUN / "ipo_business_technology_sections.csv", index=False, encoding="utf-8-sig")
    combined_chunks.to_csv(FULL_RUN / "ipo_business_technology_chunks.csv", index=False, encoding="utf-8-sig")
    combined_sections.to_csv(
        FULL_RUN / "ipo_business_technology_sections_token_proxy.csv", index=False, encoding="utf-8-sig"
    )
    combined_chunks.to_csv(
        FULL_RUN / "ipo_business_technology_chunks_token_proxy.csv", index=False, encoding="utf-8-sig"
    )
    new_sections.to_csv(REMAINING_RUN / "ipo_business_technology_sections_token_proxy_missing.csv", index=False, encoding="utf-8-sig")
    new_chunks.to_csv(REMAINING_RUN / "ipo_business_technology_chunks_token_proxy_missing.csv", index=False, encoding="utf-8-sig")

    return {
        "new_section_rows": int(len(new_sections)),
        "new_section_ok": int(new_sections["section_status"].eq("ok").sum()) if not new_sections.empty else 0,
        "new_chunk_rows": int(len(new_chunks)),
        "full_section_rows": int(len(combined_sections)),
        "full_section_codes": int(combined_sections["sec_code"].nunique()),
        "full_chunk_rows": int(len(combined_chunks)),
        "full_chunk_codes": int(combined_chunks["sec_code"].nunique()),
    }


def main() -> None:
    completed_codes = read_completed_codes()
    copy_completed_run()

    selected = pd.read_csv(BASE_SELECTED, dtype=str).fillna("")
    selected["sec_code"] = selected["sec_code"].map(z6)
    selected_missing = selected[~selected["sec_code"].isin(completed_codes)].copy()
    selected_missing = selected_missing.sort_values(["announcement_date", "sec_code", "announcement_id"])
    selected_missing.to_csv(REMAINING_RUN / "selected_missing_after_300.csv", index=False, encoding="utf-8-sig")

    a1 = load_base_numbers(completed_codes)
    downloaded = build_downloads(selected_missing, workers=8)
    prep = append_missing_token_base(downloaded, completed_codes)

    manifest = {
        "run_name": FULL_RUN.name,
        "base_completed_run": BASE_COMPLETED_RUN.name,
        "base_completed_mode": BASE_COMPLETED_MODE,
        "remaining_run": REMAINING_RUN.name,
        "completed_codes_before_append": len(completed_codes),
        "selected_missing_after_300": int(len(selected_missing)),
        **a1,
        **prep,
    }
    (FULL_RUN / "build_manifest_full_2019_2023.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (REMAINING_RUN / "prepare_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
