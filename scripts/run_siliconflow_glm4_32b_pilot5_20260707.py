#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

import pandas as pd


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
SOURCE_RUN = ROOT / "results/glm4_dewrap_join_pilot5_20260705"
RUN_NAME = "siliconflow_glm4_32b_pilot5_20260707"
RUN_DIR = ROOT / f"results/{RUN_NAME}"
RAW_DIR = RUN_DIR / "siliconflow_raw"
PROMPT_MODE = "cot_v3b_len132_tight"
MODEL = "THUDM/GLM-4-32B-0414"
BASE_URL = "https://api.siliconflow.cn/v1/chat/completions"


def import_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


runner = import_module("ipo_runner", ROOT / "scripts/run_ipo_redundancy_codex_cli_20260628.py")


def copy_inputs() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    for name in ["ipo_business_technology_chunks.csv", "ipo_business_technology_sections.csv"]:
        shutil.copy2(SOURCE_RUN / name, RUN_DIR / name)


def load_existing(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return pd.DataFrame(rows)


def append_jsonl(path: Path, rows: list[dict[str, object]], replace_ids: set[str]) -> None:
    existing = load_existing(path)
    if not existing.empty and "custom_id" in existing.columns:
        existing = existing[~existing["custom_id"].astype(str).isin(replace_ids)]
    with path.open("w", encoding="utf-8") as f:
        if not existing.empty:
            for row in existing.to_dict("records"):
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def post_chat(prompt: str, api_key: str, args: argparse.Namespace) -> dict[str, object]:
    payload = {
        "model": args.model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": args.temperature,
        "max_tokens": args.max_tokens,
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        args.base_url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"SiliconFlow HTTP {exc.code}: {body[:1200]}") from exc


def parse_usage(payload: dict[str, object]) -> dict[str, object]:
    usage = payload.get("usage") if isinstance(payload, dict) else {}
    if not isinstance(usage, dict):
        usage = {}
    return {
        "batch_input_tokens": usage.get("prompt_tokens", ""),
        "batch_output_tokens": usage.get("completion_tokens", ""),
        "batch_total_tokens": usage.get("total_tokens", ""),
    }


def parse_model_json(content: str) -> dict[str, object]:
    try:
        return runner.extract_json(content)
    except Exception:
        pass
    cleaned = content.strip()
    if cleaned.startswith("```"):
        import re

        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    def repair_json_closers(text: str) -> str:
        out: list[str] = []
        stack: list[str] = []
        in_string = False
        escaped = False
        close_for = {"{": "}", "[": "]"}
        open_for = {"}": "{", "]": "["}
        for ch in text:
            if in_string:
                out.append(ch)
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
                continue
            if ch == '"':
                in_string = True
                out.append(ch)
            elif ch in close_for:
                stack.append(ch)
                out.append(ch)
            elif ch in open_for:
                while stack and stack[-1] != open_for[ch]:
                    out.append(close_for[stack.pop()])
                if stack and stack[-1] == open_for[ch]:
                    stack.pop()
                    out.append(ch)
                else:
                    out.append(ch)
            else:
                out.append(ch)
        while stack:
            out.append(close_for[stack.pop()])
        return "".join(out)

    cleaned = repair_json_closers(cleaned)
    decoder = json.JSONDecoder()
    idx = 0
    items: list[dict[str, object]] = []
    while idx < len(cleaned):
        while idx < len(cleaned) and cleaned[idx] in " \t\r\n,":
            idx += 1
        if idx >= len(cleaned):
            break
        obj, end = decoder.raw_decode(cleaned, idx)
        if isinstance(obj, dict) and isinstance(obj.get("items"), list):
            items.extend(obj["items"])
        else:
            raise ValueError(f"Unexpected JSON object at char {idx}: {str(obj)[:120]}")
        idx = end
    if not items:
        raise ValueError(f"No items parsed from model content: {content[:300]}")
    return {"items": items}


def item_to_row(item: dict[str, object], batch: pd.DataFrame, call_meta: dict[str, object], args: argparse.Namespace) -> dict[str, object]:
    cid = str(item.get("custom_id", "")).strip()
    summary = str(item.get("summary_text", "")).strip()
    matched = batch[batch["custom_id"].astype(str).eq(cid)]
    if matched.empty:
        raise RuntimeError(f"Unknown custom_id returned: {cid}")
    counts = {f"n{i}": runner.score_count(item, f"n{i}") for i in range(6)}
    count_sum = sum(counts.values())
    sentence_reported_raw = item.get("sentence_count", item.get("Sentence_count", count_sum))
    sentence_reported = int(float(str(sentence_reported_raw).strip())) if sentence_reported_raw not in ("", None) else count_sum
    score_parse_error = int(count_sum <= 0)
    if count_sum <= 0:
        count_sum = sentence_reported if sentence_reported > 0 else 0
    high_score_count = counts["n4"] + counts["n5"]
    summary_sentence_raw = item.get("summary_sentence_count", item.get("Summary_sentence_count", ""))
    summary_sentence_count = int(float(str(summary_sentence_raw).strip())) if summary_sentence_raw not in ("", None) else ""
    relevant_score = sum(i * counts[f"n{i}"] for i in range(6)) / count_sum if count_sum and not score_parse_error else ""
    row = matched.iloc[0]
    return {
        "custom_id": cid,
        "sec_code": str(row["sec_code"]),
        "announcement_id": str(row["announcement_id"]),
        "model": args.model,
        "temperature": args.temperature,
        "prompt_mode": args.prompt_mode,
        "summary_text": summary,
        "summary_chars": len(summary),
        "summary_compact_chars": len(runner.compact_text(summary)),
        "summary_token_proxy": runner.token_proxy(summary),
        "batch_label": call_meta["label"],
        **call_meta["usage"],
        "sentence_count": count_sum,
        "sentence_count_reported": sentence_reported,
        "sentence_count_mismatch": int(sentence_reported != count_sum),
        "score_parse_error": score_parse_error,
        **counts,
        "high_score_count": high_score_count,
        "high_score_share": high_score_count / count_sum if count_sum else "",
        "summary_sentence_count": summary_sentence_count,
        "summary_high_score_gap": summary_sentence_count - high_score_count if summary_sentence_count != "" else "",
        "relevant_score": relevant_score,
        "relevant_score_model": item.get("relevant_score", item.get("Relevant_score", "")),
    }


def write_call_log(path: Path, rows: list[dict[str, object]]) -> None:
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def write_doc(args: argparse.Namespace, call_rows: list[dict[str, object]]) -> None:
    chunk_csv = RUN_DIR / f"ipo_redundancy_chunk_with_llm_{args.prompt_mode}.csv"
    firm_csv = RUN_DIR / f"ipo_redundancy_firm_level_{args.prompt_mode}.csv"
    df = pd.read_csv(chunk_csv, dtype={"sec_code": str})
    firm = pd.read_csv(firm_csv, dtype={"sec_code": str})
    for col in ["summary_token_proxy", "chunk_token_proxy", "relevant_score"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["redundancy_chunk"] = df["chunk_token_proxy"] / df["summary_token_proxy"].replace({0: pd.NA})

    old_path = SOURCE_RUN / f"ipo_redundancy_chunk_with_llm_{args.prompt_mode}.csv"
    old = pd.read_csv(old_path, dtype={"custom_id": str})[
        ["custom_id", "summary_token_proxy", "relevant_score", "summary_text"]
    ].rename(
        columns={
            "summary_token_proxy": "old_summary_token_proxy",
            "relevant_score": "old_relevant_score",
            "summary_text": "old_summary_text",
        }
    )
    cmp = df[["custom_id", "sec_code", "sec_name", "chunk_index", "summary_token_proxy", "relevant_score", "summary_text"]].merge(
        old, on="custom_id", how="left"
    )
    cmp["summary_token_proxy_delta"] = pd.to_numeric(cmp["summary_token_proxy"], errors="coerce") - pd.to_numeric(
        cmp["old_summary_token_proxy"], errors="coerce"
    )
    cmp["relevant_score_delta"] = pd.to_numeric(cmp["relevant_score"], errors="coerce") - pd.to_numeric(
        cmp["old_relevant_score"], errors="coerce"
    )
    cmp_path = RUN_DIR / "summary_comparison_vs_source_20260707.csv"
    cmp.to_csv(cmp_path, index=False, encoding="utf-8-sig")

    def fmt(x: object, digits: int = 3) -> str:
        try:
            return f"{float(x):.{digits}f}"
        except Exception:
            return ""

    desc = pd.DataFrame(
        [
            {
                "metric": "Summary_len_proxy",
                "glm_mean": df["summary_token_proxy"].mean(),
                "codex_mean": old["old_summary_token_proxy"].mean(),
                "paper_mean": 132.678,
                "glm_median": df["summary_token_proxy"].median(),
                "codex_median": old["old_summary_token_proxy"].median(),
            },
            {
                "metric": "Redundancy_chunk_proxy",
                "glm_mean": df["redundancy_chunk"].mean(),
                "codex_mean": (
                    pd.to_numeric(df["chunk_token_proxy"], errors="coerce")
                    / pd.to_numeric(old["old_summary_token_proxy"], errors="coerce").replace({0: pd.NA})
                ).mean(),
                "paper_mean": 32.176,
                "glm_median": df["redundancy_chunk"].median(),
                "codex_median": "",
            },
            {
                "metric": "Relevant_score",
                "glm_mean": df["relevant_score"].mean(),
                "codex_mean": old["old_relevant_score"].mean(),
                "paper_mean": "",
                "glm_median": df["relevant_score"].median(),
                "codex_median": old["old_relevant_score"].median(),
            },
        ]
    )
    desc_path = RUN_DIR / "siliconflow_glm4_32b_summary_stats_20260707.csv"
    desc.to_csv(desc_path, index=False, encoding="utf-8-sig")
    firm_view = firm[["sec_code", "sec_name", "original_length_units", "summary_length_units", "redundancy"]].copy()
    firm_view = firm_view.sort_values("redundancy", ascending=False)

    def table(data: pd.DataFrame, cols: list[str], digits: int = 3) -> list[str]:
        out = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
        for _, r in data.iterrows():
            vals = []
            for c in cols:
                v = r.get(c, "")
                if isinstance(v, float):
                    vals.append(fmt(v, digits))
                else:
                    vals.append(str(v))
            out.append("| " + " | ".join(vals) + " |")
        return out

    raw_call_rows: list[dict[str, object]] = []
    for raw_json in sorted(RAW_DIR.glob("*.json")):
        try:
            payload = json.loads(raw_json.read_text(encoding="utf-8"))
        except Exception:
            continue
        usage = payload.get("usage", {}) if isinstance(payload, dict) else {}
        choice0 = payload.get("choices", [{}])[0] if isinstance(payload.get("choices"), list) else {}
        raw_call_rows.append(
            {
                "label": raw_json.stem,
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
                "finish_reason": choice0.get("finish_reason", ""),
                "model": payload.get("model", args.model),
            }
        )
    call_df = pd.DataFrame(raw_call_rows or call_rows)
    if not call_df.empty:
        call_df.to_csv(RUN_DIR / "siliconflow_call_log_all_20260707.csv", index=False, encoding="utf-8-sig")
    doc = [
        f"# SiliconFlow GLM-4-32B {args.doc_label}",
        "",
        f"日期：{datetime.now().date().isoformat()}",
        "",
        "## 结论",
        "",
        f"- 使用模型：`{args.model}`，接口：SiliconFlow OpenAI-compatible chat completions。",
        "- API key 未写入脚本、结果或文档；本目录只保存模型返回文本和聚合指标。",
        f"- 样本复用原 `{args.source_run_name}` 的 {df['sec_code'].nunique()} 家、{len(df)} 个 chunk。",
        f"- GLM 生成的 `Summary_len_proxy` mean={fmt(df['summary_token_proxy'].mean())}，source Codex mean={fmt(old['old_summary_token_proxy'].mean())}，原文 mean=132.678。",
        f"- GLM 生成的 `Redundancy_chunk_proxy` mean={fmt(df['redundancy_chunk'].mean())}，原文 mean=32.176。",
        f"- GLM 的 `Relevant_score` mean={fmt(df['relevant_score'].mean())}，source Codex mean={fmt(old['old_relevant_score'].mean())}。",
        "",
        "## 描述统计",
        "",
        *table(desc, ["metric", "glm_mean", "codex_mean", "paper_mean", "glm_median", "codex_median"]),
        "",
        "## 企业层",
        "",
        *table(firm_view, ["sec_code", "sec_name", "original_length_units", "summary_length_units", "redundancy"]),
        "",
        "## API Calls",
        "",
        f"- calls：`{len(call_df)}`",
        f"- total tokens：`{int(pd.to_numeric(call_df.get('total_tokens', pd.Series(dtype=float)), errors='coerce').fillna(0).sum())}`",
        f"- prompt tokens：`{int(pd.to_numeric(call_df.get('prompt_tokens', pd.Series(dtype=float)), errors='coerce').fillna(0).sum())}`",
        f"- completion tokens：`{int(pd.to_numeric(call_df.get('completion_tokens', pd.Series(dtype=float)), errors='coerce').fillna(0).sum())}`",
        "",
        "## 输出",
        "",
        f"- chunk CSV：`{chunk_csv}`",
        f"- firm CSV：`{firm_csv}`",
        f"- comparison：`{cmp_path}`",
        f"- call log：`{RUN_DIR / 'siliconflow_call_log_20260707.csv'}`",
        "",
    ]
    (ROOT / f"docs/00_current/{args.doc_name}").write_text("\n".join(doc), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-run-name", default=SOURCE_RUN.name)
    parser.add_argument("--run-name", default=RUN_NAME)
    parser.add_argument("--doc-name", default="siliconflow_glm4_32b_pilot5_20260707.md")
    parser.add_argument("--doc-label", default="Pilot5")
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--prompt-mode", default=PROMPT_MODE)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--sleep", type=float, default=0.8)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--rate-limit-sleep", type=float, default=65.0)
    parser.add_argument("--rerun-existing", action="store_true")
    return parser.parse_args()


def main() -> None:
    global SOURCE_RUN, RUN_NAME, RUN_DIR, RAW_DIR
    args = parse_args()
    SOURCE_RUN = ROOT / f"results/{args.source_run_name}"
    RUN_NAME = args.run_name
    RUN_DIR = ROOT / f"results/{args.run_name}"
    RAW_DIR = RUN_DIR / "siliconflow_raw"
    copy_inputs()
    chunks = pd.read_csv(RUN_DIR / "ipo_business_technology_chunks.csv", dtype=str).fillna("")
    out_path = RUN_DIR / f"ipo_redundancy_llm_outputs_{args.prompt_mode}.jsonl"
    if out_path.exists() and not args.rerun_existing:
        existing = load_existing(out_path)
        done = set(existing["custom_id"].astype(str)) if not existing.empty and "custom_id" in existing.columns else set()
        chunks = chunks[~chunks["custom_id"].astype(str).isin(done)].copy()
        print(f"[resume] done={len(done)} remaining={len(chunks)}", flush=True)

    api_key = os.environ.get("SILICONFLOW_API_KEY")
    if not chunks.empty and not api_key:
        raise SystemExit("Missing SILICONFLOW_API_KEY")

    all_rows: list[dict[str, object]] = []
    replace_ids: set[str] = set()
    call_rows: list[dict[str, object]] = []
    for sec_code, firm_chunks in chunks.groupby("sec_code", sort=False):
        firm_chunks = firm_chunks.sort_values("chunk_index", key=lambda s: pd.to_numeric(s, errors="coerce"))
        for start in range(0, len(firm_chunks), args.batch_size):
            batch = firm_chunks.iloc[start : start + args.batch_size].copy()
            first_idx = int(pd.to_numeric(batch["chunk_index"], errors="coerce").min())
            last_idx = int(pd.to_numeric(batch["chunk_index"], errors="coerce").max())
            label = f"{sec_code}_chunks_{first_idx:04d}_{last_idx:04d}"
            prompt = runner.build_prompt(batch, args.prompt_mode)
            print(f"[siliconflow] {label} chunks={len(batch)} prompt_chars={len(prompt)}", flush=True)
            expected = set(batch["custom_id"].astype(str))
            payload: dict[str, object] | None = None
            items: list[dict[str, object]] = []
            for attempt in range(args.retries + 1):
                try:
                    payload = post_chat(prompt, api_key, args)
                    content = str(payload.get("choices", [{}])[0].get("message", {}).get("content", ""))
                    (RAW_DIR / f"{label}.json").write_text(
                        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
                    )
                    (RAW_DIR / f"{label}.txt").write_text(content, encoding="utf-8")
                    parsed = parse_model_json(content)
                    items = parsed.get("items", [])
                    got = {str(item.get("custom_id", "")) for item in items}
                    if expected != got:
                        raise RuntimeError(
                            f"id mismatch for {label}: missing={sorted(expected-got)} extra={sorted(got-expected)}"
                        )
                    break
                except Exception as exc:
                    if attempt >= args.retries:
                        raise
                    print(f"[retry] {label} attempt={attempt + 1} error={exc}", flush=True)
                    retry_sleep = args.rate_limit_sleep if "TPM limit reached" in str(exc) else min(5 * (attempt + 1), 20)
                    time.sleep(retry_sleep)
            assert payload is not None
            usage = parse_usage(payload)
            call_meta = {"label": label, "usage": usage}
            for item in items:
                row = item_to_row(item, batch, call_meta, args)
                all_rows.append(row)
                replace_ids.add(str(row["custom_id"]))
            call_rows.append(
                {
                    "ts": datetime.now().isoformat(timespec="seconds"),
                    "label": label,
                    "sec_code": sec_code,
                    "chunks": len(batch),
                    "prompt_chars": len(prompt),
                    "items_returned": len(items),
                    "prompt_tokens": usage.get("batch_input_tokens", ""),
                    "completion_tokens": usage.get("batch_output_tokens", ""),
                    "total_tokens": usage.get("batch_total_tokens", ""),
                    "model": args.model,
                }
            )
            append_jsonl(out_path, all_rows, replace_ids)
            write_call_log(RUN_DIR / "siliconflow_call_log_20260707.csv", call_rows)
            if args.sleep:
                time.sleep(args.sleep)

    runner.aggregate(RUN_DIR, args.prompt_mode)
    write_doc(args, call_rows)
    print(json.dumps({"run_dir": str(RUN_DIR), "chunks": len(load_existing(out_path))}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
