#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pandas as pd


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
SOURCE = ROOT / "results/glm4_dewrap_rechunk_trial_20260705/dewrap_join"
ANCHOR = ROOT / "results/glm4_dewrap_join_pilot100_20260705"
OUT = ROOT / "results/glm4_dewrap_join_full543_20260705"
PLAN_DIR = ROOT / "results/glm4_dewrap_join_full543_20260705_shards"
MODE = "cot_v3b_len132_tight"
SHARD_N = 4


def seed_anchor_outputs(chunks: pd.DataFrame) -> int:
    src = ANCHOR / f"ipo_redundancy_llm_outputs_{MODE}.jsonl"
    dst = OUT / f"ipo_redundancy_llm_outputs_{MODE}.jsonl"
    expected_ids = set(chunks["custom_id"].astype(str))
    rows = []
    with src.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if str(row.get("custom_id", "")) in expected_ids:
                rows.append(row)
    with dst.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(rows)


def assign_shards(sections: pd.DataFrame, chunks: pd.DataFrame, seeded_ids: set[str]) -> pd.DataFrame:
    remaining = chunks[~chunks["custom_id"].astype(str).isin(seeded_ids)].copy()
    firm_counts = (
        remaining.groupby(["sec_code", "sec_name"], dropna=False)
        .size()
        .reset_index(name="chunk_n")
        .sort_values(["chunk_n", "sec_code"], ascending=[False, True])
    )
    shard_loads = {i: 0 for i in range(1, SHARD_N + 1)}
    assignments = []
    for row in firm_counts.to_dict("records"):
        shard = min(shard_loads, key=lambda k: (shard_loads[k], k))
        shard_loads[shard] += int(row["chunk_n"])
        assignments.append({**row, "shard": shard})
    plan = pd.DataFrame(assignments).sort_values(["shard", "sec_code"]).reset_index(drop=True)
    year_map = sections.set_index("sec_code")["year"].to_dict()
    plan["year"] = plan["sec_code"].map(year_map)
    return plan


def write_shard_runs(sections: pd.DataFrame, chunks: pd.DataFrame, plan: pd.DataFrame) -> None:
    for shard in range(1, SHARD_N + 1):
        run_name = f"glm4_dewrap_join_full543_20260705_shard{shard:02d}"
        shard_dir = ROOT / "results" / run_name
        if shard_dir.exists():
            shutil.rmtree(shard_dir)
        shard_dir.mkdir(parents=True)
        codes = plan.loc[plan["shard"].eq(shard), "sec_code"].astype(str).tolist()
        shard_sections = sections[sections["sec_code"].astype(str).isin(codes)].copy()
        shard_chunks = chunks[chunks["sec_code"].astype(str).isin(codes)].copy()
        shard_sections.to_csv(shard_dir / "ipo_business_technology_sections.csv", index=False, encoding="utf-8-sig")
        shard_chunks.to_csv(shard_dir / "ipo_business_technology_chunks.csv", index=False, encoding="utf-8-sig")
        (PLAN_DIR / f"shard{shard:02d}_codes.txt").write_text(",".join(codes), encoding="utf-8")
        (PLAN_DIR / f"shard{shard:02d}_run_name.txt").write_text(run_name, encoding="utf-8")


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    if PLAN_DIR.exists():
        shutil.rmtree(PLAN_DIR)
    OUT.mkdir(parents=True)
    PLAN_DIR.mkdir(parents=True)

    sections = pd.read_csv(SOURCE / "ipo_business_technology_sections.csv", dtype={"sec_code": str}).fillna("")
    chunks = pd.read_csv(SOURCE / "ipo_business_technology_chunks.csv", dtype={"sec_code": str}).fillna("")
    sections["year"] = sections["announcement_date"].astype(str).str[:4]

    for df in [sections, chunks]:
        if "chunk_glm4_tokens" in df.columns:
            df["chunk_token_proxy"] = pd.to_numeric(df["chunk_glm4_tokens"], errors="coerce")
        if "tech_text_glm4_tokens" in df.columns:
            df["tech_text_token_proxy"] = pd.to_numeric(df["tech_text_glm4_tokens"], errors="coerce")
            df["token_mode"] = "glm4_dewrap_join"

    sections.to_csv(OUT / "ipo_business_technology_sections.csv", index=False, encoding="utf-8-sig")
    chunks.to_csv(OUT / "ipo_business_technology_chunks.csv", index=False, encoding="utf-8-sig")
    sections[["sec_code", "sec_name", "announcement_date", "chunk_count", "tech_text_glm4_tokens"]].to_csv(
        OUT / "sample_firms_20260705.csv", index=False, encoding="utf-8-sig"
    )
    (OUT / "sample_codes_20260705.txt").write_text(",".join(sections["sec_code"].astype(str)), encoding="utf-8")

    seeded_chunks = seed_anchor_outputs(chunks)
    seeded_df = pd.read_json(OUT / f"ipo_redundancy_llm_outputs_{MODE}.jsonl", lines=True, dtype={"sec_code": str})
    seeded_ids = set(seeded_df["custom_id"].astype(str))
    plan = assign_shards(sections, chunks, seeded_ids)
    write_shard_runs(sections, chunks, plan)

    plan.to_csv(PLAN_DIR / f"shard_plan_{MODE}_20260705.csv", index=False, encoding="utf-8-sig")
    shard_summary = (
        plan.groupby("shard")
        .agg(firm_n=("sec_code", "nunique"), chunk_n=("chunk_n", "sum"), codes=("sec_code", lambda x: ",".join(x.astype(str))))
        .reset_index()
    )
    shard_summary.to_csv(PLAN_DIR / f"shard_summary_{MODE}_20260705.csv", index=False, encoding="utf-8-sig")

    manifest = {
        "source": str(SOURCE.relative_to(ROOT)),
        "anchor": str(ANCHOR.relative_to(ROOT)),
        "out": str(OUT.relative_to(ROOT)),
        "plan_dir": str(PLAN_DIR.relative_to(ROOT)),
        "shard_n": SHARD_N,
        "firms": int(sections["sec_code"].nunique()),
        "chunks": int(len(chunks)),
        "seeded_chunks_from_pilot100": int(seeded_chunks),
        "remaining_chunks_for_llm": int(len(chunks) - seeded_chunks),
        "chunk_glm4_tokens_mean": float(pd.to_numeric(chunks["chunk_glm4_tokens"], errors="coerce").mean()),
        "shards": shard_summary.to_dict("records"),
    }
    (OUT / "manifest_20260705.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    (PLAN_DIR / "manifest_20260705.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print(shard_summary.to_string(index=False))


if __name__ == "__main__":
    main()
