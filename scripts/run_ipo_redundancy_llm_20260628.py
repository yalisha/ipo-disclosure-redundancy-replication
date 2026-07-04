#!/usr/bin/env python3
"""Run LLM condensation for IPO redundancy chunks and aggregate redundancy.

Required environment:
- IPO_LLM_API_KEY

Optional:
- IPO_LLM_BASE_URL, default https://api.openai.com/v1/chat/completions
- IPO_LLM_MODEL, default gpt-4.1-mini
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from urllib.request import Request, urlopen

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RUN_TAG_DEFAULT = "20260628"


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def strong_condense_messages(text: str) -> list[dict[str, str]]:
    prompt = (
        "你是招股说明书“业务与技术”章节的信息冗余识别员。任务不是写摘要，而是最大限度删除冗余文本。\n"
        "请只保留对判断发行人技术实力、核心产品、关键技术、研发能力、市场地位、客户/供应商、产能和竞争格局有直接价值的事实。\n"
        "删除：目录/页眉页脚、套话、政策背景、行业常识、重复解释、无数字支撑的形容、低信息密度段落、法规合规铺陈。\n"
        "输出必须极度精炼，目标长度约为原文的 2%-5%；如果原文有效信息很少，可以更短。\n"
        "不得新增事实，不得评价，不得说明删减过程，不得使用标题或项目符号。\n\n"
        f"原文：\n{text}"
    )
    return [
        {"role": "system", "content": "你只做忠实、极短的事实凝练，不新增事实。"},
        {"role": "user", "content": prompt},
    ]


def ultra_condense_messages(text: str) -> list[dict[str, str]]:
    prompt = (
        "你是招股说明书“业务与技术”章节的信息密度筛选器。请从原文中抽取最核心事实，用于衡量文本冗余度。\n"
        "硬性要求：输出不超过180个汉字；只写一段；不要标题、编号、解释、评价、换行。\n"
        "只保留最关键的3-6个事实：主营业务/核心产品/关键技术/研发能力/市场地位/重要客户或供应商/产能或收入数字。\n"
        "删除所有政策背景、行业常识、模板话、重复描述、无数字形容、页眉页脚和法规合规铺陈。\n"
        "如果原文缺少关键经营技术事实，输出更短。不得新增事实。\n\n"
        f"原文：\n{text}"
    )
    return [
        {"role": "system", "content": "你只输出不超过180个汉字的忠实事实凝练。"},
        {"role": "user", "content": prompt},
    ]


def load_tasks(run_dir: Path, prompt_mode: str) -> list[dict[str, object]]:
    if prompt_mode == "stored":
        task_path = run_dir / "ipo_redundancy_llm_tasks.jsonl"
        if not task_path.exists():
            raise SystemExit(f"Task file not found: {task_path}")
        tasks: list[dict[str, object]] = []
        with task_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    tasks.append(json.loads(line))
        return tasks
    if prompt_mode in {"strong", "ultra"}:
        chunks_path = run_dir / "ipo_business_technology_chunks.csv"
        if not chunks_path.exists():
            raise SystemExit(f"Chunk file not found: {chunks_path}")
        chunks = pd.read_csv(chunks_path, dtype=str)
        tasks = []
        for _, row in chunks.iterrows():
            chunk_path = ROOT / str(row["chunk_file"])
            text = chunk_path.read_text(encoding="utf-8", errors="ignore")
            tasks.append(
                {
                    "custom_id": row["custom_id"],
                    "sec_code": row["sec_code"],
                    "announcement_id": row["announcement_id"],
                    "messages": strong_condense_messages(text) if prompt_mode == "strong" else ultra_condense_messages(text),
                }
            )
        return tasks
    raise ValueError(f"Unknown prompt mode: {prompt_mode}")


def call_chat_completion(base_url: str, api_key: str, model: str, messages: list[dict[str, str]], temperature: float) -> tuple[str, dict[str, object]]:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    last_exc: Exception | None = None
    for attempt in range(5):
        try:
            req = Request(base_url, data=data, headers=headers, method="POST")
            with urlopen(req, timeout=120) as resp:
                raw = resp.read()
            parsed = json.loads(raw.decode("utf-8", errors="replace"))
            return parsed["choices"][0]["message"]["content"], parsed.get("usage") or {}
        except Exception as exc:
            last_exc = exc
            time.sleep(1.5 + attempt)
    raise RuntimeError(f"LLM call failed after retries: {last_exc}")


def load_existing(path: Path) -> set[str]:
    done: set[str] = set()
    if not path.exists():
        return done
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                done.add(json.loads(line)["custom_id"])
            except Exception:
                continue
    return done


def parse_custom_ids(values: list[str]) -> set[str]:
    ids: set[str] = set()
    for value in values:
        ids.update(part.strip() for part in value.split(",") if part.strip())
    return ids


def drop_existing_outputs(path: Path, custom_ids: set[str]) -> None:
    if not custom_ids or not path.exists():
        return
    kept: list[str] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except Exception:
                kept.append(line)
                continue
            if str(row.get("custom_id", "")) not in custom_ids:
                kept.append(line)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        f.writelines(kept)
    tmp_path.replace(path)


def run_llm(args: argparse.Namespace) -> Path:
    run_dir = ROOT / "results" / f"{args.universe}_{args.run_tag}"
    out_path = run_dir / f"ipo_redundancy_llm_outputs_{args.prompt_mode}.jsonl"
    api_key = os.environ.get("IPO_LLM_API_KEY", "")
    if not api_key:
        raise SystemExit("Missing IPO_LLM_API_KEY. Set it before running the LLM condensation step.")
    base_url = os.environ.get("IPO_LLM_BASE_URL", "https://api.openai.com/v1/chat/completions")
    model = os.environ.get("IPO_LLM_MODEL", "gpt-4.1-mini")
    tasks = load_tasks(run_dir, args.prompt_mode)
    requested_ids = parse_custom_ids(args.custom_id)
    if requested_ids:
        task_ids = {str(task["custom_id"]) for task in tasks}
        missing = sorted(requested_ids - task_ids)
        if missing:
            raise SystemExit(f"Requested custom_id not found: {', '.join(missing)}")
        tasks = [task for task in tasks if str(task["custom_id"]) in requested_ids]
        drop_existing_outputs(out_path, requested_ids)

    done = load_existing(out_path)
    pending = [task for task in tasks if str(task["custom_id"]) not in done]
    if args.limit:
        pending = pending[: args.limit]
    write_lock = Lock()
    completed = 0

    def one(task: dict[str, object]) -> dict[str, object]:
        content, usage = call_chat_completion(base_url, api_key, model, task["messages"], args.temperature)
        completion_details = usage.get("completion_tokens_details") or {}
        prompt_details = usage.get("prompt_tokens_details") or {}
        return {
            "custom_id": task["custom_id"],
            "sec_code": task.get("sec_code", ""),
            "announcement_id": task.get("announcement_id", ""),
            "model": model,
            "temperature": args.temperature,
            "prompt_mode": args.prompt_mode,
            "summary_text": content,
            "summary_chars": len(content),
            "summary_compact_chars": len(compact_text(content)),
            "prompt_tokens": usage.get("prompt_tokens", ""),
            "completion_tokens": usage.get("completion_tokens", ""),
            "total_tokens": usage.get("total_tokens", ""),
            "reasoning_tokens": completion_details.get("reasoning_tokens", ""),
            "cached_tokens": prompt_details.get("cached_tokens", ""),
            "usage_json": json.dumps(usage, ensure_ascii=False) if usage else "",
        }

    with out_path.open("a", encoding="utf-8") as out_f:
        with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
            futures = {pool.submit(one, task): str(task["custom_id"]) for task in pending}
            for future in as_completed(futures):
                cid = futures[future]
                try:
                    row = future.result()
                except Exception as exc:
                    row = {
                        "custom_id": cid,
                        "model": model,
                        "temperature": args.temperature,
                        "prompt_mode": args.prompt_mode,
                        "error": f"{type(exc).__name__}: {str(exc)[:500]}",
                        "summary_text": "",
                        "summary_chars": 0,
                        "summary_compact_chars": 0,
                    }
                with write_lock:
                    out_f.write(json.dumps(row, ensure_ascii=False) + "\n")
                    out_f.flush()
                completed += 1
                print(f"[llm] {completed}/{len(pending)} {cid} summary_chars={row.get('summary_chars', 0)}", flush=True)
                if args.sleep:
                    time.sleep(args.sleep)
    return out_path


def aggregate(args: argparse.Namespace) -> None:
    run_dir = ROOT / "results" / f"{args.universe}_{args.run_tag}"
    outputs_path = run_dir / f"ipo_redundancy_llm_outputs_{args.prompt_mode}.jsonl"
    chunks_path = run_dir / "ipo_business_technology_chunks.csv"
    sections_path = run_dir / "ipo_business_technology_sections.csv"
    if not outputs_path.exists():
        raise SystemExit(f"LLM output file not found: {outputs_path}")
    chunks = pd.read_csv(chunks_path, dtype=str)
    sections = pd.read_csv(sections_path, dtype=str)
    outs = []
    with outputs_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                outs.append(json.loads(line))
    out_df = pd.DataFrame(outs)
    if out_df.empty:
        raise SystemExit("No LLM outputs to aggregate.")
    chunks["chunk_compact_chars"] = pd.to_numeric(chunks["chunk_compact_chars"], errors="coerce")
    out_df = out_df[out_df.get("error", "").fillna("").eq("")].copy() if "error" in out_df.columns else out_df
    out_df = out_df.drop_duplicates(subset=["custom_id"], keep="last")
    out_df["summary_compact_chars"] = pd.to_numeric(out_df["summary_compact_chars"], errors="coerce")
    merged = chunks.merge(out_df[["custom_id", "summary_compact_chars", "summary_chars"]], on="custom_id", how="left")
    merged.to_csv(run_dir / f"ipo_redundancy_chunk_with_llm_{args.prompt_mode}.csv", index=False, encoding="utf-8-sig")

    agg = (
        merged.groupby(["sec_code", "announcement_id"], dropna=False)
        .agg(
            chunks=("custom_id", "size"),
            completed_chunks=("summary_compact_chars", "count"),
            original_compact_chars=("chunk_compact_chars", "sum"),
            summary_compact_chars=("summary_compact_chars", "sum"),
        )
        .reset_index()
    )
    agg["llm_complete"] = agg["chunks"].eq(agg["completed_chunks"])
    agg["redundancy_partial"] = agg["original_compact_chars"] / agg["summary_compact_chars"].replace({0: pd.NA})
    agg["redundancy"] = agg["redundancy_partial"].where(agg["llm_complete"])
    keep_cols = [
        "sec_code",
        "sec_name",
        "announcement_id",
        "announcement_title",
        "announcement_date",
        "doc_type",
        "section_status",
        "tech_text_compact_chars",
        "chunk_count",
    ]
    firm = sections[[c for c in keep_cols if c in sections.columns]].merge(agg, on=["sec_code", "announcement_id"], how="left")
    firm.to_csv(run_dir / f"ipo_redundancy_firm_level_{args.prompt_mode}.csv", index=False, encoding="utf-8-sig")
    print(f"[aggregate] rows={len(firm)} out={run_dir / f'ipo_redundancy_firm_level_{args.prompt_mode}.csv'}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--universe", choices=["star", "a_share"], default="star", help="star=科创板; a_share=全A股IPO.")
    parser.add_argument("--run-tag", default=RUN_TAG_DEFAULT)
    parser.add_argument("--limit", type=int, default=0, help="Maximum new chunks to run; 0 means all remaining.")
    parser.add_argument("--temperature", type=float, default=0.5)
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--prompt-mode", choices=["stored", "strong", "ultra"], default="ultra")
    parser.add_argument("--aggregate-only", action="store_true")
    parser.add_argument("--custom-id", action="append", default=[], help="Rerun one or more comma-separated custom_id values.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.aggregate_only:
        run_llm(args)
    aggregate(args)


if __name__ == "__main__":
    main()
