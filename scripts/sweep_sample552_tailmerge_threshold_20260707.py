#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
IN = ROOT / "results/cutoff552_table2_471_probe_20260707/sample552_chunk_metrics_cutoff_20260707.csv"
OUT_DIR = ROOT / "results/sample552_tailmerge_threshold_probe_20260707"
DOC = ROOT / "docs/00_current/sample552_tailmerge_threshold_probe_20260707.md"

PAPER = {
    "chunk_n": 8683,
    "Chunk_num_mean": 18.191,
    "Text_len_mean": 3866.817,
    "Text_len_std": 343.868,
    "Summary_len_mean": 132.678,
    "Summary_len_std": 39.683,
    "Red_mean": 32.176,
    "Red_std": 11.730,
    "FirmRed_mean": 29.074,
    "FirmRed_std": 2.630,
}


def fmt(x: object) -> str:
    try:
        return f"{float(x):.3f}"
    except Exception:
        return ""


def process(df: pd.DataFrame, threshold: int, floor: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows: list[dict[str, object]] = []
    for _, g in df.groupby("sec_code", sort=False):
        arr = []
        for r in g.sort_values("chunk_index").to_dict("records"):
            arr.append(
                {
                    "sec_code": r["sec_code"],
                    "sec_name": r["sec_name"],
                    "text": float(r["chunk_glm4_tokens"]),
                    "summary_raw": float(r["Summary_len_proxy"]),
                    "source_custom_ids": str(r["custom_id"]),
                }
            )
        while len(arr) > 1 and arr[-1]["text"] < threshold:
            tail = arr.pop()
            arr[-1]["text"] += tail["text"]
            arr[-1]["summary_raw"] += tail["summary_raw"]
            arr[-1]["source_custom_ids"] += ";" + tail["source_custom_ids"]
        chunk_n = len(arr)
        for i, item in enumerate(arr, start=1):
            item["processed_chunk_index"] = i
            item["Chunk_num"] = chunk_n
            item["Summary_len"] = max(item["summary_raw"], floor)
            item["floor_applied"] = int(item["summary_raw"] < floor)
            item["Red"] = item["text"] / item["Summary_len"] if item["Summary_len"] else np.nan
            rows.append(item)
    c = pd.DataFrame(rows)
    f = c.groupby(["sec_code", "sec_name"], as_index=False).agg(text=("text", "sum"), summary=("Summary_len", "sum"))
    f["Redundancy"] = f["text"] / f["summary"].replace({0: np.nan})
    return c, f


def summarize(c: pd.DataFrame, f: pd.DataFrame, threshold: int, floor: int, raw_n: int) -> dict[str, object]:
    row = {
        "threshold": threshold,
        "summary_floor": floor,
        "chunk_n": int(c.shape[0]),
        "merge_n": int(raw_n - c.shape[0]),
        "floor_applied_n": int(c["floor_applied"].sum()),
        "Chunk_num_mean": c["Chunk_num"].mean(),
        "Text_len_mean": c["text"].mean(),
        "Text_len_std": c["text"].std(ddof=1),
        "Summary_len_mean": c["Summary_len"].mean(),
        "Summary_len_std": c["Summary_len"].std(ddof=1),
        "Red_mean": c["Red"].mean(),
        "Red_std": c["Red"].std(ddof=1),
        "FirmRed_mean": f["Redundancy"].mean(),
        "FirmRed_std": f["Redundancy"].std(ddof=1),
    }
    errs = []
    for key, target in PAPER.items():
        errs.append(abs(float(row[key]) - target) / abs(target))
    row["loss"] = float(np.mean(errs))
    row["chunk_n_diff"] = int(row["chunk_n"] - PAPER["chunk_n"])
    return row


def md_table(df: pd.DataFrame, cols: list[str], n: int) -> list[str]:
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.head(n).iterrows():
        vals = []
        for c in cols:
            v = r[c]
            vals.append(str(int(v)) if c in {"threshold", "summary_floor", "chunk_n", "merge_n", "floor_applied_n", "chunk_n_diff"} else fmt(v))
        out.append("| " + " | ".join(vals) + " |")
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(IN, dtype={"sec_code": str})
    for col in ["chunk_index", "chunk_glm4_tokens", "Summary_len_proxy", "summary_token_proxy"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "Summary_len_proxy" not in df.columns:
        df["Summary_len_proxy"] = df["summary_token_proxy"]

    rows = []
    raw_n = int(df.shape[0])
    for threshold in range(500, 2501, 100):
        for floor in [0, 30, 50, 60, 70, 80, 90, 100]:
            c, f = process(df, threshold, floor)
            rows.append(summarize(c, f, threshold, floor, raw_n))
    res = pd.DataFrame(rows).sort_values("loss")
    res.to_csv(OUT_DIR / "sample552_tailmerge_threshold_ranked_20260707.csv", index=False, encoding="utf-8-sig")
    close = res.assign(chunk_abs=res["chunk_n_diff"].abs()).sort_values(["chunk_abs", "loss"])
    close.to_csv(OUT_DIR / "sample552_tailmerge_threshold_closest_chunkn_20260707.csv", index=False, encoding="utf-8-sig")

    raw = df.copy()
    raw["Red"] = raw["chunk_glm4_tokens"] / raw["Summary_len_proxy"].replace({0: np.nan})
    raw_row = {
        "chunk_n": int(raw.shape[0]),
        "Text_len_mean": raw["chunk_glm4_tokens"].mean(),
        "Text_len_std": raw["chunk_glm4_tokens"].std(ddof=1),
        "Summary_len_mean": raw["Summary_len_proxy"].mean(),
        "Summary_len_std": raw["Summary_len_proxy"].std(ddof=1),
        "Red_mean": raw["Red"].mean(),
        "Red_std": raw["Red"].std(ddof=1),
    }
    cols = [
        "threshold",
        "summary_floor",
        "chunk_n",
        "chunk_n_diff",
        "merge_n",
        "floor_applied_n",
        "loss",
        "Text_len_mean",
        "Text_len_std",
        "Summary_len_mean",
        "Summary_len_std",
        "Red_mean",
        "Red_std",
        "FirmRed_mean",
        "FirmRed_std",
    ]
    doc = [
        "# 552 家 cutoff 样本 tail-merge 阈值扫描",
        "",
        "日期：2026-07-07",
        "",
        "## 结论",
        "",
        "- 在 552 家 cutoff 样本上，原始 chunk N=8906，高于原文 8683。",
        "- 若只追 chunk N，`tail_merge<threshold=1700` 后 chunk N=8679，只比原文少 4 个。",
        "- 若看整体描述统计 loss，`threshold=2300` 最优，但 chunk N=8584，低于原文 99 个；因此更像贴表，不适合优先采用。",
        "- 和 GLM 50 家不同，当前 552 家 Codex 输出几乎不需要 summary floor；`floor=50` 对整体影响很小。",
        "- 关键问题：tail-merge 能修复 chunk N 和 Text_len std，但 `Redundancy_chunk` 均值与 std 仍低于原文，说明当前摘要/尾部右尾仍不够像原文。",
        "",
        "## 原始 552 样本",
        "",
        f"- chunk_n：`{raw_row['chunk_n']}`，原文 `8683`",
        f"- Text_len mean/std：`{raw_row['Text_len_mean']:.3f}` / `{raw_row['Text_len_std']:.3f}`，原文 `3866.817` / `343.868`",
        f"- Summary_len mean/std：`{raw_row['Summary_len_mean']:.3f}` / `{raw_row['Summary_len_std']:.3f}`，原文 `132.678` / `39.683`",
        f"- Redundancy_chunk mean/std：`{raw_row['Red_mean']:.3f}` / `{raw_row['Red_std']:.3f}`，原文 `32.176` / `11.730`",
        "",
        "## Overall loss Top 15",
        "",
        *md_table(res, cols, 15),
        "",
        "## Chunk N 最接近原文 Top 15",
        "",
        *md_table(close, cols, 15),
        "",
        "## 输出文件",
        "",
        f"- ranked：`{OUT_DIR / 'sample552_tailmerge_threshold_ranked_20260707.csv'}`",
        f"- closest chunk N：`{OUT_DIR / 'sample552_tailmerge_threshold_closest_chunkn_20260707.csv'}`",
        "",
    ]
    DOC.write_text("\n".join(doc), encoding="utf-8")
    print({"doc": str(DOC), "ranked": str(OUT_DIR / "sample552_tailmerge_threshold_ranked_20260707.csv")})


if __name__ == "__main__":
    main()
