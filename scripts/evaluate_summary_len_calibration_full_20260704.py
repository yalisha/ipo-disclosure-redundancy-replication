#!/usr/bin/env python3
"""Evaluate cot_v3b_len132_tight on the full 543-firm run."""

from __future__ import annotations

import math

import pandas as pd

import evaluate_summary_len_calibration_50_20260703 as base


base.OUT_DIR = base.ROOT / "results" / "summary_len_calibration_full_543_20260704"
base.DOC_PATH = base.ROOT / "docs" / "00_current" / "cot_v3b_len132_full543_calibration_20260704.md"


def prepare_full_sample() -> pd.DataFrame:
    base.OUT_DIR.mkdir(parents=True, exist_ok=True)
    sections = pd.read_csv(base.RUN_DIR / "ipo_business_technology_sections.csv", dtype={"sec_code": str})
    master = pd.read_csv(base.MASTER_PATH, dtype={"sec_code": str, "code": str})
    sample = sections[["sec_code", "sec_name", "announcement_id", "chunk_count"]].merge(
        master.drop(columns=[c for c in ["sec_name", "announcement_id", "chunk_count"] if c in master.columns]),
        on="sec_code",
        how="left",
    )
    sample["listing_year"] = pd.to_numeric(sample.get("listing_year"), errors="coerce")
    sample = sample.sort_values(["listing_year", "sec_code"], na_position="last").reset_index(drop=True)
    sample.to_csv(base.OUT_DIR / "sample_543_firms_20260704.csv", index=False, encoding="utf-8-sig")
    (base.OUT_DIR / "sample_543_codes_20260704.txt").write_text(
        ",".join(sample["sec_code"].astype(str).tolist()) + "\n",
        encoding="utf-8",
    )
    return sample


def fmt(value: object, digits: int = 3) -> str:
    return base.fmt(value, digits)


def metric_row(label: str, metric: str, baseline: dict[str, object] | None, pilot: dict[str, object] | None) -> str:
    return base.metric_row(label, metric, baseline, pilot)


def verdict_for(baseline: dict[str, object] | None, pilot: dict[str, object] | None) -> str:
    if pilot is None:
        return "PENDING_LLM"
    pilot_complete = pilot is not None and (baseline is None or pilot.get("chunk_n", 0) == baseline.get("chunk_n", 0))
    if not pilot_complete:
        return "PARTIAL_LLM"
    s_mean = float(pilot["summary_len"]["mean"])
    b_rho = float(pilot["panel_b_spearman"]["rho"])
    b_p = float(pilot["panel_b_spearman"]["p"])
    low_med = float(pilot["panel_b_low_high_by_median"]["low_median_redundancy"])
    high_med = float(pilot["panel_b_low_high_by_median"]["high_median_redundancy"])
    panel_d_p = float(pilot["panel_d_all_union_cluster"]["p"])
    if 125 <= s_mean <= 140 and b_rho < 0 and b_p < 0.01 and low_med > high_med and panel_d_p < 0.05:
        return "PASS_FOR_SUMMARY_LEN_GATE"
    return "NO_PASS_YET"


def write_report(sample: pd.DataFrame, baseline: dict[str, object] | None, pilot: dict[str, object] | None) -> None:
    codes = ",".join(sample["sec_code"].astype(str).tolist())
    year_counts = sample["listing_year"].value_counts(dropna=False).sort_index()
    year_text = []
    for year, count in year_counts.items():
        if pd.isna(year):
            year_text.append(f"上市年缺失 {int(count)} 家")
        else:
            year_text.append(f"{int(year)} 年 {int(count)} 家")
    verdict = verdict_for(baseline, pilot)

    lines = [
        "# cot_v3b_len132 全 543 家摘要长度校准",
        "",
        "日期：2026-07-04",
        "",
        "## 结论",
        "",
        f"`{verdict}`",
        "",
        "本报告固定既有 token_proxy chunking，只更换摘要生成 prompt 为 `cot_v3b_len132_tight`。目标是检查全 543 家后，Table 1 量级和 Panel B/C/D 构念效度是否稳定。",
        "",
        "注意：这里的 `PASS_FOR_SUMMARY_LEN_GATE` 只表示摘要长度校准门通过，不表示表 2 经济后果已经复刻。",
        "",
        "## 样本",
        "",
        "- 样本来源：`results/star_token_proxy_full_2019_2023_20260702/ipo_business_technology_sections.csv` 中全部 543 家。",
        "- 上市年分布：" + "，".join(year_text) + "。",
        "",
        "```text",
        codes,
        "```",
        "",
        "## 输出",
        "",
        "- 样本清单：`results/summary_len_calibration_full_543_20260704/sample_543_firms_20260704.csv`",
        "- 样本代码：`results/summary_len_calibration_full_543_20260704/sample_543_codes_20260704.txt`",
        f"- pilot chunk metrics：`results/summary_len_calibration_full_543_20260704/chunk_metrics_{base.PILOT_MODE}_20260703.csv`",
        f"- pilot firm ranking：`results/summary_len_calibration_full_543_20260704/firm_ranking_{base.PILOT_MODE}_20260703.csv`",
        f"- pilot metrics JSON：`results/summary_len_calibration_full_543_20260704/metrics_{base.PILOT_MODE}_20260703.json`",
        "",
        "## 描述统计对照",
        "",
        f"| 指标 | baseline scoregate | {base.PILOT_MODE} |",
        "|---|---:|---:|",
        metric_row("Text_len", "text_len", baseline, pilot),
        metric_row("Summary_len", "summary_len", baseline, pilot),
        metric_row("Redundancy_chunk", "redundancy_chunk", baseline, pilot),
        metric_row("Firm Redundancy", "firm_redundancy", baseline, pilot),
        "",
    ]
    if pilot is not None:
        lines.extend(
            [
                "## Panel B",
                "",
                f"| 检验 | baseline | {base.PILOT_MODE} |",
                "|---|---:|---:|",
                f"| Spearman rho | {fmt(baseline['panel_b_spearman']['rho']) if baseline else ''} | {fmt(pilot['panel_b_spearman']['rho'])} |",
                f"| Spearman p | {fmt(baseline['panel_b_spearman']['p'], 4) if baseline else ''} | {fmt(pilot['panel_b_spearman']['p'], 4)} |",
                f"| low median by score median | {fmt(baseline['panel_b_low_high_by_median']['low_median_redundancy']) if baseline else ''} | {fmt(pilot['panel_b_low_high_by_median']['low_median_redundancy'])} |",
                f"| high median by score median | {fmt(baseline['panel_b_low_high_by_median']['high_median_redundancy']) if baseline else ''} | {fmt(pilot['panel_b_low_high_by_median']['high_median_redundancy'])} |",
                "",
                "## Panel C",
                "",
                f"| 检验 | baseline | {base.PILOT_MODE} |",
                "|---|---:|---:|",
                f"| raw cluster coef | {fmt(baseline['panel_c_raw_cluster']['coef']) if baseline else ''} | {fmt(pilot['panel_c_raw_cluster']['coef'])} |",
                f"| raw cluster p | {fmt(baseline['panel_c_raw_cluster']['p'], 4) if baseline else ''} | {fmt(pilot['panel_c_raw_cluster']['p'], 4)} |",
                f"| drop p99 cluster coef | {fmt(baseline['panel_c_drop_p99_cluster']['coef']) if baseline else ''} | {fmt(pilot['panel_c_drop_p99_cluster']['coef'])} |",
                f"| drop p99 cluster p | {fmt(baseline['panel_c_drop_p99_cluster']['p'], 4) if baseline else ''} | {fmt(pilot['panel_c_drop_p99_cluster']['p'], 4)} |",
                "",
                "## Panel D",
                "",
                f"| 检验 | baseline | {base.PILOT_MODE} |",
                "|---|---:|---:|",
                f"| all union cluster coef | {fmt(baseline['panel_d_all_union_cluster']['coef']) if baseline else ''} | {fmt(pilot['panel_d_all_union_cluster']['coef'])} |",
                f"| all union cluster p | {fmt(baseline['panel_d_all_union_cluster']['p'], 4) if baseline else ''} | {fmt(pilot['panel_d_all_union_cluster']['p'], 4)} |",
                f"| without target cluster coef | {fmt(baseline['panel_d_without_target_cluster']['coef']) if baseline else ''} | {fmt(pilot['panel_d_without_target_cluster']['coef'])} |",
                f"| without target cluster p | {fmt(baseline['panel_d_without_target_cluster']['p'], 4) if baseline else ''} | {fmt(pilot['panel_d_without_target_cluster']['p'], 4)} |",
                "",
                "## 初步读法",
                "",
                "- 全样本后若 `Summary_len` 仍在 125-140，说明摘要长度校准稳定。",
                "- Panel B 低评分组冗余中位数必须高于高评分组，这是构念效度硬条件。",
                "- Panel C 继续观察 firm-cluster 和 drop-p99 口径；若仍只在 10% 附近，说明摘要长度不是唯一差距。",
                "- Table 2 经济后果复刻仍需单独判断，不能由本报告替代。",
                base.panel_c_interpretation(pilot),
                "",
            ]
        )
    base.DOC_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    sample = prepare_full_sample()
    baseline = base.evaluate_mode(base.BASELINE_MODE, sample)
    pilot = base.evaluate_mode(base.PILOT_MODE, sample)
    write_report(sample, baseline, pilot)
    print(f"sample_codes={base.OUT_DIR / 'sample_543_codes_20260704.txt'}")
    print(f"report={base.DOC_PATH}")
    if pilot is None:
        print("pilot_status=PENDING_LLM")
    else:
        print(f"pilot_chunks={pilot['chunk_n']} pilot_summary_mean={pilot['summary_len']['mean']:.3f}")


if __name__ == "__main__":
    main()
