#!/usr/bin/env python3
"""Build the IPO disclosure redundancy text base from CNINFO.

This script does not call an LLM. It creates an auditable base:
- CNINFO query metadata
- selected IPO prospectus candidates
- downloaded PDFs and extracted full text
- extracted "Business and Technology" chapter text
- chunk-level LLM task JSONL
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import math
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RUN_TAG_DEFAULT = "20260628"

QUERY_URL = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
STATIC_BASE = "https://static.cninfo.com.cn/"
SEARCH_PAGE = "http://www.cninfo.com.cn/new/commonUrl/pageOfSearch?url=disclosure/list/search"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Referer": SEARCH_PAGE,
    "Origin": "http://www.cninfo.com.cn",
}

MARKET_SCOPES = [
    {"scope": "sse", "column": "sse", "plate": "sh"},
    {"scope": "szse", "column": "szse", "plate": "sz"},
    {"scope": "bse", "column": "third", "plate": "bj"},
]
STAR_TERMS = [
    "科创板上市招股说明书",
    "招股说明书 科创板",
    "首次公开发行股票并在科创板上市招股说明书",
    "科创板 招股意向书",
    "首次公开发行股票并在科创板上市招股意向书",
]
A_SHARE_TERMS = [
    "招股说明书",
    "招股意向书",
]

EXCLUDE_TITLE_PAT = re.compile(
    r"提示性公告|附录|摘要|上市公告书|发行公告|发行结果|网下发行|网上发行|申购情况|"
    r"中签|配售|保荐|法律意见|专项核查|问询|回复|财务报表及审计报告|审计报告"
)
FINAL_PROSPECTUS_PAT = re.compile(r"招股说明书")
INTENTION_PROSPECTUS_PAT = re.compile(r"招股意向书")
STAR_BOARD_PAT = re.compile(r"科创板")
SIX_DIGIT_CODE_PAT = re.compile(r"^\d{6}$")
A_SHARE_CODE_PAT = re.compile(r"^(?:(?:000|001|002|003|300|301|600|601|603|605|688)\d{3}|[489]\d{5})$")
ALLOWED_PAGE_COLUMNS = {"SZZB", "SZCY", "SHZB", "SHKCB", "BJS"}

SECTION_START_PAT = re.compile(
    r"(?:^|\n)\s*第\s*[一二三四五六七八九十]+\s*[章节]\s*业务\s*(?:与|和)\s*技术\s*(?:\n|$)"
)
SECTION_HEADING_PAT = re.compile(r"\n\s*第\s*[一二三四五六七八九十]+\s*[章节]\s*[^\n]{0,50}\n")
COMMON_NEXT_SECTION_PAT = re.compile(
    r"\n\s*第\s*[一二三四五六七八九十]+\s*[章节]\s*(?:公司治理|同业竞争|关联交易|财务会计|"
    r"管理层分析|募集资金|投资者保护|风险因素|发行人基本情况|发行基本情况|其他重要事项)"
)


def strip_tags(text: object) -> str:
    value = html.unescape(str(text or ""))
    value = re.sub(r"<[^>]+>", "", value)
    return re.sub(r"\s+", " ", value).strip()


def safe_name(text: str, limit: int = 180) -> str:
    value = re.sub(r"[\\/:*?\"<>|]", "_", str(text))
    value = re.sub(r"\s+", "_", value)
    return value[:limit].strip("_")


def ts_to_date(ms: object) -> str:
    try:
        return datetime.fromtimestamp(int(ms) / 1000).strftime("%Y-%m-%d")
    except Exception:
        return ""


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def http_post_json(url: str, data: dict[str, object], timeout: int = 30) -> dict:
    payload = urlencode(data).encode("utf-8")
    headers = {
        **HEADERS,
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }
    last_exc: Exception | None = None
    for attempt in range(5):
        try:
            req = Request(url, data=payload, headers=headers, method="POST")
            with urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
            return json.loads(raw.decode("utf-8", errors="replace"))
        except Exception as exc:
            last_exc = exc
            time.sleep(0.8 + attempt * 0.5)
    raise RuntimeError(f"CNINFO POST failed after retries: {last_exc}")


def http_get_bytes(url: str, timeout: int = 60) -> tuple[int, bytes]:
    last_exc: Exception | None = None
    for attempt in range(5):
        try:
            req = Request(url, headers={"User-Agent": HEADERS["User-Agent"]}, method="GET")
            with urlopen(req, timeout=timeout) as resp:
                return int(getattr(resp, "status", 200)), resp.read()
        except Exception as exc:
            last_exc = exc
            time.sleep(0.8 + attempt * 0.5)
    raise RuntimeError(f"GET failed after retries: {last_exc}")


def terms_for_universe(universe: str) -> list[str]:
    if universe == "star":
        return STAR_TERMS
    if universe == "a_share":
        return A_SHARE_TERMS
    raise ValueError(f"Unknown universe: {universe}")


def scopes_for_universe(universe: str) -> list[dict[str, str]]:
    if universe == "star":
        return [MARKET_SCOPES[0]]
    if universe == "a_share":
        return MARKET_SCOPES
    raise ValueError(f"Unknown universe: {universe}")


def query_cninfo(scope: dict[str, str], term: str, start_date: str, end_date: str, page_num: int, page_size: int) -> dict:
    data = {
        "pageNum": page_num,
        "pageSize": page_size,
        "column": scope["column"],
        "tabName": "fulltext",
        "plate": scope["plate"],
        "stock": "",
        "searchkey": term,
        "secid": "",
        "category": "",
        "trade": "",
        "seDate": f"{start_date}~{end_date}",
        "sortName": "",
        "sortType": "",
        "isHLtitle": "true",
    }
    return http_post_json(QUERY_URL, data)


def normalize_announcement(row: dict, scope: dict[str, str], term: str) -> dict[str, object]:
    adjunct = row.get("adjunctUrl") or ""
    sec_code_raw = str(row.get("secCode") or "")
    sec_code = sec_code_raw.zfill(6) if sec_code_raw else ""
    return {
        "query_scope": scope["scope"],
        "query_terms": term,
        "sec_code_raw": sec_code_raw,
        "sec_code": sec_code,
        "sec_name": strip_tags(row.get("secName") or ""),
        "org_id": row.get("orgId") or "",
        "announcement_id": str(row.get("announcementId") or ""),
        "announcement_title": strip_tags(row.get("announcementTitle") or ""),
        "announcement_date": ts_to_date(row.get("announcementTime")),
        "announcement_time_ms": str(row.get("announcementTime") or ""),
        "adjunct_url": adjunct,
        "pdf_url": urljoin(STATIC_BASE, adjunct) if adjunct else "",
        "adjunct_size": str(row.get("adjunctSize") or ""),
        "adjunct_type": row.get("adjunctType") or "",
        "page_column": row.get("pageColumn") or "",
        "column_id": row.get("columnId") or "",
    }


def query_all(scopes: list[dict[str, str]], terms: list[str], start_date: str, end_date: str, page_size: int, raw_json_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    raw_json_dir.mkdir(parents=True, exist_ok=True)
    rows: dict[str, dict[str, object]] = {}
    counts: list[dict[str, object]] = []
    for scope in scopes:
        for term in terms:
            first = query_cninfo(scope, term, start_date, end_date, 1, page_size)
            total = int(first.get("totalRecordNum") or 0)
            pages = math.ceil(total / page_size) if total else 0
            counts.append({"query_scope": scope["scope"], "query_term": term, "total": total, "pages": pages})
            print(f"[query] {scope['scope']} {term}: total={total}, pages={pages}", flush=True)
            payloads = [(1, first)] if pages else []
            for page in range(2, pages + 1):
                time.sleep(0.08)
                payloads.append((page, query_cninfo(scope, term, start_date, end_date, page, page_size)))
            for page, payload in payloads:
                raw_path = raw_json_dir / f"{scope['scope']}_{safe_name(term, 80)}_page_{page:04d}.json"
                raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                for ann in payload.get("announcements") or []:
                    item = normalize_announcement(ann, scope, term)
                    aid = str(item.get("announcement_id") or "")
                    if not aid:
                        continue
                    if aid not in rows:
                        rows[aid] = item
                    else:
                        old_terms = set(str(rows[aid].get("query_terms") or "").split(";"))
                        old_scopes = set(str(rows[aid].get("query_scope") or "").split(";"))
                        old_terms.add(term)
                        old_scopes.add(scope["scope"])
                        rows[aid]["query_terms"] = ";".join(sorted(t for t in old_terms if t))
                        rows[aid]["query_scope"] = ";".join(sorted(s for s in old_scopes if s))
    raw = pd.DataFrame(sorted(rows.values(), key=lambda r: (str(r.get("announcement_date")), str(r.get("sec_code")), str(r.get("announcement_id")))))
    return raw, pd.DataFrame(counts)


def add_filters(raw: pd.DataFrame, universe: str) -> pd.DataFrame:
    out = raw.copy()
    title = out["announcement_title"].astype(str)
    out["is_star_board"] = out["page_column"].eq("SHKCB") | title.map(lambda x: bool(STAR_BOARD_PAT.search(x)))
    out["is_688_code"] = out["sec_code"].astype(str).str.match(r"^688\d{3}$")
    out["is_six_digit_code"] = out["sec_code"].astype(str).map(lambda x: bool(SIX_DIGIT_CODE_PAT.match(x)))
    out["is_a_share_code_shape"] = out["sec_code"].astype(str).map(lambda x: bool(A_SHARE_CODE_PAT.match(x)))
    out["is_allowed_page_column"] = out["page_column"].isin(ALLOWED_PAGE_COLUMNS)
    out["title_has_final_prospectus"] = title.map(lambda x: bool(FINAL_PROSPECTUS_PAT.search(x)))
    out["title_has_intention_prospectus"] = title.map(lambda x: bool(INTENTION_PROSPECTUS_PAT.search(x)))
    out["title_excluded"] = title.map(lambda x: bool(EXCLUDE_TITLE_PAT.search(x)))
    out["has_pdf_url"] = out["pdf_url"].astype(str).str.len().gt(0)
    out["doc_type"] = ""
    out.loc[out["title_has_final_prospectus"], "doc_type"] = "final_prospectus"
    out.loc[out["title_has_intention_prospectus"], "doc_type"] = "intention_prospectus"
    if universe == "star":
        universe_gate = out["is_star_board"] & out["is_688_code"]
    elif universe == "a_share":
        universe_gate = out["is_allowed_page_column"] & out["is_a_share_code_shape"]
    else:
        raise ValueError(f"Unknown universe: {universe}")
    out["eligible_doc"] = universe_gate & out["has_pdf_url"] & ~out["title_excluded"] & out["doc_type"].isin(["final_prospectus", "intention_prospectus"])
    return out


def select_primary_docs(filtered: pd.DataFrame) -> pd.DataFrame:
    keep = filtered[filtered["eligible_doc"]].copy()
    if keep.empty:
        return keep
    keep["doc_rank"] = keep["doc_type"].map({"final_prospectus": 0, "intention_prospectus": 1}).fillna(9)
    keep["announcement_date_sort"] = pd.to_datetime(keep["announcement_date"], errors="coerce")
    selected = (
        keep.sort_values(["sec_code", "doc_rank", "announcement_date_sort", "announcement_id"], ascending=[True, True, False, False])
        .drop_duplicates(["sec_code"], keep="first")
        .sort_values(["announcement_date_sort", "sec_code"])
    )
    return selected


def local_paths(row: pd.Series, pdf_dir: Path, text_dir: Path) -> tuple[Path, Path]:
    name = safe_name(
        f"{row.get('announcement_date','')}_{row.get('sec_code','')}_{row.get('sec_name','')}_"
        f"{row.get('announcement_id','')}_{row.get('announcement_title','')}"
    )
    return pdf_dir / f"{name}.pdf", text_dir / f"{name}.txt"


def download_extract(row: pd.Series, pdf_dir: Path, text_dir: Path) -> dict[str, object]:
    pdf_dir.mkdir(parents=True, exist_ok=True)
    text_dir.mkdir(parents=True, exist_ok=True)
    pdf_path, txt_path = local_paths(row, pdf_dir, text_dir)
    out = {
        "download_status": "",
        "pdf_file": "",
        "txt_file": "",
        "pdf_bytes": 0,
        "full_text_chars": 0,
        "download_error": "",
    }
    try:
        if not pdf_path.exists():
            status, content = http_get_bytes(str(row.get("pdf_url") or ""))
            if status != 200:
                out["download_status"] = f"download_failed_{status}"
                return out
            if b"%PDF" not in content[:4096]:
                out["download_status"] = "download_failed_not_pdf"
                out["download_error"] = content[:120].decode("utf-8", errors="replace")
                return out
            pdf_path.write_bytes(content)
        if not txt_path.exists() or txt_path.stat().st_size == 0:
            proc = subprocess.run(
                ["pdftotext", "-layout", str(pdf_path), str(txt_path)],
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                out["download_status"] = "pdftotext_failed"
                out["download_error"] = (proc.stderr or proc.stdout or "")[:500]
                out["pdf_file"] = str(pdf_path.relative_to(ROOT))
                out["pdf_bytes"] = pdf_path.stat().st_size if pdf_path.exists() else 0
                return out
        text = txt_path.read_text(encoding="utf-8", errors="ignore")
        out.update(
            {
                "download_status": "ok",
                "pdf_file": str(pdf_path.relative_to(ROOT)),
                "txt_file": str(txt_path.relative_to(ROOT)),
                "pdf_bytes": pdf_path.stat().st_size,
                "full_text_chars": len(text),
            }
        )
        return out
    except Exception as exc:
        out["download_status"] = f"error_{type(exc).__name__}"
        out["download_error"] = str(exc)[:500]
        return out


def normalize_for_section(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def extract_business_technology(text: str) -> tuple[str, str, int, int]:
    norm = normalize_for_section(text)
    starts = list(SECTION_START_PAT.finditer(norm))
    if not starts:
        return "", "start_not_found", -1, -1
    for match in starts:
        line_end = norm.find("\n", match.start() + 1)
        line_end = line_end if line_end != -1 else min(len(norm), match.start() + 200)
        line = norm[match.start() : line_end]
        # Skip table-of-contents entries such as "第六节 业务与技术 ........ 118".
        if "." in line or "…" in line:
            continue
        start = match.start()
        after = norm[match.end() :]
        end_rel = None
        for next_heading in SECTION_HEADING_PAT.finditer(after):
            if next_heading.start() > 10000:
                end_rel = next_heading.start()
                break
        if end_rel is None:
            next_common = COMMON_NEXT_SECTION_PAT.search(after)
            if next_common and next_common.start() > 10000:
                end_rel = next_common.start()
        if end_rel:
            section = norm[start : match.end() + end_rel].strip()
            if len(compact_text(section)) >= 3000:
                return section, "ok", start, match.end() + end_rel
    match = starts[-1]
    start = match.start()
    section = norm[start:].strip()
    return section, "end_not_found", start, len(norm)


def split_into_chunks(text: str, max_chars: int = 4000) -> list[str]:
    clean = normalize_for_section(text).strip()
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", clean) if p.strip()]
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if len(para) > max_chars:
            sentences = re.split(r"(?<=[。！？；;])", para)
            for sentence in [s.strip() for s in sentences if s.strip()]:
                if current and len(current) + len(sentence) + 1 > max_chars:
                    chunks.append(current.strip())
                    current = ""
                current += ("\n" if current else "") + sentence
            continue
        if current and len(current) + len(para) + 2 > max_chars:
            chunks.append(current.strip())
            current = ""
        current += ("\n\n" if current else "") + para
    if current.strip():
        chunks.append(current.strip())
    return chunks


def task_prompt(text: str) -> str:
    return (
        "你是资本市场招股说明书文本凝练员。请只基于给定文本，保留对判断发行人技术实力、"
        "核心竞争力、市场地位、产品与研发能力有实质价值的信息，删除重复、模板化、合规铺陈、"
        "空泛形容、无关背景和低信息密度表述。不要新增事实，不要评论。\n\n"
        "输出要求：只输出凝练后的中文正文，不要项目符号说明，不要解释。\n\n"
        f"待凝练文本：\n{text}"
    )


def make_chunks_and_tasks(downloaded: pd.DataFrame, run_dir: Path, max_chars: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    section_dir = run_dir / "business_technology_text"
    chunks_dir = run_dir / "chunks"
    section_dir.mkdir(parents=True, exist_ok=True)
    chunks_dir.mkdir(parents=True, exist_ok=True)
    section_rows: list[dict[str, object]] = []
    chunk_rows: list[dict[str, object]] = []
    task_path = run_dir / "ipo_redundancy_llm_tasks.jsonl"
    with task_path.open("w", encoding="utf-8") as task_f:
        for _, row in downloaded.iterrows():
            text = ""
            txt_file = str(row.get("txt_file") or "")
            if txt_file:
                path = ROOT / txt_file
                if path.exists():
                    text = path.read_text(encoding="utf-8", errors="ignore")
            section, status, start, end = extract_business_technology(text) if text else ("", "no_text", -1, -1)
            section_name = f"{row.get('sec_code')}_{row.get('announcement_id')}_business_technology.txt"
            section_path = section_dir / section_name
            if section:
                section_path.write_text(section, encoding="utf-8")
            chunks = split_into_chunks(section, max_chars=max_chars) if section else []
            section_rows.append(
                {
                    **{k: row.get(k, "") for k in ["sec_code", "sec_name", "announcement_id", "announcement_title", "announcement_date", "doc_type", "pdf_url", "download_status", "pdf_file", "txt_file"]},
                    "section_status": status,
                    "section_file": str(section_path.relative_to(ROOT)) if section else "",
                    "section_start_char": start,
                    "section_end_char": end,
                    "full_text_chars": row.get("full_text_chars", 0),
                    "tech_text_chars": len(section),
                    "tech_text_compact_chars": len(compact_text(section)),
                    "chunk_count": len(chunks),
                }
            )
            for idx, chunk in enumerate(chunks, start=1):
                custom_id = f"{row.get('sec_code')}_{row.get('announcement_id')}_chunk_{idx:04d}"
                chunk_file = chunks_dir / f"{custom_id}.txt"
                chunk_file.write_text(chunk, encoding="utf-8")
                chunk_row = {
                    "custom_id": custom_id,
                    "sec_code": row.get("sec_code", ""),
                    "sec_name": row.get("sec_name", ""),
                    "announcement_id": row.get("announcement_id", ""),
                    "chunk_index": idx,
                    "chunk_count": len(chunks),
                    "chunk_file": str(chunk_file.relative_to(ROOT)),
                    "chunk_chars": len(chunk),
                    "chunk_compact_chars": len(compact_text(chunk)),
                }
                chunk_rows.append(chunk_row)
                task_f.write(
                    json.dumps(
                        {
                            "custom_id": custom_id,
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
    return pd.DataFrame(section_rows), pd.DataFrame(chunk_rows)


def write_report(path: Path, args: argparse.Namespace, counts: pd.DataFrame, raw: pd.DataFrame, filtered: pd.DataFrame, selected: pd.DataFrame, section_df: pd.DataFrame, chunk_df: pd.DataFrame) -> None:
    def md_table(df: pd.DataFrame) -> str:
        if df.empty:
            return "(empty)"
        cols = list(df.columns)
        rows = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
        for _, row in df.iterrows():
            rows.append("| " + " | ".join(str(row.get(c, "")) for c in cols) + " |")
        return "\n".join(rows)

    status_table = pd.DataFrame()
    if not section_df.empty and "section_status" in section_df.columns:
        status_table = section_df["section_status"].value_counts(dropna=False).rename_axis("section_status").reset_index(name="rows")
    run_name = getattr(args, "effective_run_name", f"{args.universe}_{args.run_tag}")
    lines = [
        "# IPO Redundancy Base Run",
        "",
        f"- universe: `{args.universe}`",
        f"- run_tag: `{args.run_tag}`",
        f"- run_name: `{run_name}`",
        f"- start_index: `{args.start_index}`",
        f"- download_limit: `{args.download_limit}`",
        f"- source: CNINFO `hisAnnouncement/query`",
        f"- date window: `{args.start_date}` to `{args.end_date}`",
        f"- raw announcements: `{len(raw)}`",
        f"- eligible docs: `{int(filtered['eligible_doc'].sum()) if not filtered.empty else 0}`",
        f"- selected primary docs by firm: `{len(selected)}`",
        f"- downloaded docs in this run: `{len(section_df)}`",
        f"- sections ok: `{int(section_df['section_status'].eq('ok').sum()) if not section_df.empty else 0}`",
        f"- chunks: `{len(chunk_df)}`",
        "",
        "## Query Counts",
        "",
        md_table(counts),
        "",
        "## Section Status",
        "",
        md_table(status_table),
        "",
        "## Outputs",
        "",
        f"- `results/{run_name}/cninfo_raw_hits.csv`",
        f"- `results/{run_name}/ipo_prospectus_selected_primary.csv`",
        f"- `results/{run_name}/ipo_business_technology_sections.csv`",
        f"- `results/{run_name}/ipo_business_technology_chunks.csv`",
        f"- `results/{run_name}/ipo_redundancy_llm_tasks.jsonl`",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", choices=["star", "a_share"], default="star", help="star=科创板; a_share=全A股IPO.")
    parser.add_argument("--run-tag", default=RUN_TAG_DEFAULT)
    parser.add_argument("--run-name", default="", help="Override output run directory name under results/ and data/raw/.")
    parser.add_argument("--start-date", default="2019-07-22")
    parser.add_argument("--end-date", default="2023-12-31")
    parser.add_argument("--page-size", type=int, default=30)
    parser.add_argument("--start-index", type=int, default=1, help="1-based start row in selected primary docs.")
    parser.add_argument("--download-limit", type=int, default=20)
    parser.add_argument("--full-download", action="store_true")
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--max-chars", type=int, default=4000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.start_index < 1:
        raise SystemExit("--start-index must be >= 1")
    run_name = args.run_name or f"{args.universe}_{args.run_tag}"
    args.effective_run_name = run_name
    run_dir = ROOT / "results" / run_name
    raw_base = ROOT / "data" / "raw" / f"cninfo_ipo_prospectus_{run_name}"
    raw_json_dir = raw_base / "raw_json"
    pdf_dir = raw_base / "raw_pdf"
    text_dir = raw_base / "text"
    run_dir.mkdir(parents=True, exist_ok=True)

    raw, counts = query_all(scopes_for_universe(args.universe), terms_for_universe(args.universe), args.start_date, args.end_date, args.page_size, raw_json_dir)
    filtered = add_filters(raw, args.universe) if not raw.empty else raw
    selected = select_primary_docs(filtered) if not filtered.empty else filtered

    raw.to_csv(run_dir / "cninfo_raw_hits.csv", index=False, encoding="utf-8-sig")
    counts.to_csv(run_dir / "cninfo_query_counts.csv", index=False, encoding="utf-8-sig")
    filtered.to_csv(run_dir / "cninfo_filtered_hits.csv", index=False, encoding="utf-8-sig")
    selected.to_csv(run_dir / "ipo_prospectus_selected_primary.csv", index=False, encoding="utf-8-sig")

    selected_from_start = selected.iloc[args.start_index - 1 :].copy() if not selected.empty else selected
    if args.skip_download:
        to_download = selected.head(0).copy()
    elif args.full_download:
        to_download = selected_from_start.copy()
    else:
        to_download = selected_from_start.head(args.download_limit).copy()

    download_rows: list[dict[str, object]] = []
    for i, (_, row) in enumerate(to_download.iterrows(), start=1):
        print(f"[download] {i}/{len(to_download)} {row.get('sec_code')} {row.get('announcement_title')}", flush=True)
        status = download_extract(row, pdf_dir, text_dir)
        download_rows.append({**row.to_dict(), **status})
        time.sleep(0.08)
    downloaded = pd.DataFrame(download_rows)
    downloaded.to_csv(run_dir / "ipo_prospectus_downloaded.csv", index=False, encoding="utf-8-sig")

    section_df, chunk_df = make_chunks_and_tasks(downloaded, run_dir, args.max_chars) if not downloaded.empty else (pd.DataFrame(), pd.DataFrame())
    section_df.to_csv(run_dir / "ipo_business_technology_sections.csv", index=False, encoding="utf-8-sig")
    chunk_df.to_csv(run_dir / "ipo_business_technology_chunks.csv", index=False, encoding="utf-8-sig")
    write_report(run_dir / "run_report.md", args, counts, raw, filtered, selected, section_df, chunk_df)

    print(f"[done] selected_docs={len(selected)} downloaded={len(downloaded)} chunks={len(chunk_df)}", flush=True)
    print(f"[out] {run_dir}", flush=True)


if __name__ == "__main__":
    main()
