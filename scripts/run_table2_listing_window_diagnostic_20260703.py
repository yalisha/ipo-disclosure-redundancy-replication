#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import run_original_paper_table2_probe_20260702 as base


PROJECT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
DEFAULT_MASTER = (
    PROJECT
    / "results/original_paper_table2_probe_full_2019_2023_csmar_patent_20260702/"
    "original_paper_table2_probe_master_full_2019_2023_csmar_patent_20260702.csv"
)
DEFAULT_RUN_DIR = PROJECT / "results/table2_listing_window_diagnostic_20260703"
DEFAULT_DOC = PROJECT / "docs/表2窗口切分诊断_20260703.md"


WINDOWS = [
    ("W1_2019_2021", 2019, 2021, "W1(19-21)"),
    ("W2_2019_2022", 2019, 2022, "W2(19-22)"),
    ("W3_2019_2023", 2019, 2023, "W3(19-23)"),
]


def fmt(x: object, digits: int = 4) -> str:
    if pd.isna(x):
        return ""
    return f"{float(x):.{digits}f}"


def coef_cell(row: pd.Series) -> str:
    return f"{fmt(row['coef'], 4)} / {fmt(row['t_HC1'], 2)} / {fmt(row['p_HC1'], 3)} / {int(row['N'])}"


def md_table(df: pd.DataFrame, cols: list[str]) -> str:
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df.iterrows():
        vals: list[str] = []
        for col in cols:
            val = row[col]
            if isinstance(val, float):
                vals.append(fmt(val, 3))
            else:
                vals.append(str(val))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def run_window_regs(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    all_regs: list[pd.DataFrame] = []
    sample_rows: list[dict] = []
    for key, lo, hi, label in WINDOWS:
        sub = master[pd.to_numeric(master["listing_year"], errors="coerce").between(lo, hi)].copy()
        regs = base.run_regressions(sub)
        regs.insert(0, "window", key)
        regs.insert(1, "window_label", label)
        regs.insert(2, "listing_year_min", lo)
        regs.insert(3, "listing_year_max", hi)
        all_regs.append(regs)
        sample_rows.append(
            {
                "window": key,
                "window_label": label,
                "firm_N": int(sub["code"].nunique()),
                "FInvention_nonmissing": int(sub["FInvention"].notna().sum()),
                "BHAR_nonmissing": int(sub["BHAR"].notna().sum()),
                "FSales_Growth_nonmissing": int(sub["FSales_Growth"].notna().sum()),
                "Redundancy_mean": pd.to_numeric(sub["Redundancy"], errors="coerce").mean(),
                "Redundancy_std": pd.to_numeric(sub["Redundancy"], errors="coerce").std(ddof=1),
                "FInvention_mean": pd.to_numeric(sub["FInvention"], errors="coerce").mean(),
            }
        )
    return pd.concat(all_regs, ignore_index=True), pd.DataFrame(sample_rows)


def pivot_reg_table(regs: pd.DataFrame, models: list[str]) -> pd.DataFrame:
    keep_deps = ["FInvention", "BHAR", "FSales_Growth"]
    rows: list[dict] = []
    for dep in keep_deps:
        for model in models:
            row = {"Y": dep, "规格": model}
            for _, _, _, label in WINDOWS:
                sub = regs[(regs["window_label"].eq(label)) & (regs["dep_var"].eq(dep)) & (regs["model"].eq(model))]
                row[label] = coef_cell(sub.iloc[0]) if not sub.empty else ""
            orig = base.ORIGINAL_PANEL_B[dep]
            row["原文 coef/t/N"] = f"{orig['coef']:.4f} / {orig['t']:.2f} / {orig['N']}"
            rows.append(row)
    return pd.DataFrame(rows)


def monotonic_note(regs: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for dep, orig in base.ORIGINAL_PANEL_B.items():
        vals: list[float] = []
        ts: list[float] = []
        for _, _, _, label in WINDOWS:
            r = regs[
                (regs["window_label"].eq(label))
                & (regs["dep_var"].eq(dep))
                & (regs["model"].eq("controls_fe"))
            ].iloc[0]
            vals.append(float(r["coef"]))
            ts.append(float(r["t_HC1"]))
        paper = orig["coef"]
        dist_w2 = abs(vals[1] - paper)
        dist_w3 = abs(vals[2] - paper)
        rows.append(
            {
                "Y": dep,
                "W1_coef": vals[0],
                "W2_coef": vals[1],
                "W3_coef": vals[2],
                "W1_t": ts[0],
                "W2_t": ts[1],
                "W3_t": ts[2],
                "W2_closer_than_W3": dist_w2 < dist_w3,
                "W2_sign_matches_paper": (vals[1] < 0) == (paper < 0),
                "dilution_pattern_W2_to_W3": abs(vals[2]) < abs(vals[1]),
            }
        )
    return pd.DataFrame(rows)


def write_doc(master: pd.DataFrame, regs: pd.DataFrame, samples: pd.DataFrame, doc_out: Path) -> None:
    controls = pivot_reg_table(regs, ["controls_fe"])
    all_specs = pivot_reg_table(regs, ["simple", "fe_text", "controls_fe"])
    trend = monotonic_note(regs)
    year_counts = (
        master.groupby("listing_year")["code"]
        .nunique()
        .rename("N")
        .reset_index()
        .sort_values("listing_year")
    )
    listing_year_numeric = pd.to_numeric(master["listing_year"], errors="coerce")
    missing_year = master[listing_year_numeric.isna()].copy()
    missing_year_note = ""
    if not missing_year.empty:
        missing_items = "；".join(
            f"`{str(r.code).zfill(6)} {getattr(r, 'sec_name', '')}`" for r in missing_year.itertuples()
        )
        listing_year_n = int(master.loc[listing_year_numeric.notna(), "code"].nunique())
        missing_year_note = (
            f"- 注意：full scoregate X 文件为 {int(master['code'].nunique())} 家，但现成 master 中可按 "
            f"`listing_year` 切分的是 {listing_year_n} 家；{missing_items} 缺 "
            "`first_trade_date/listing_year`，且三个 Y 均缺失，不进入表 2 回归。"
        )

    w2_better_count = int(trend["W2_closer_than_W3"].sum())
    w2_sign_count = int(trend["W2_sign_matches_paper"].sum())
    dilution_count = int(trend["dilution_pattern_W2_to_W3"].sum())
    if w2_better_count >= 2 and w2_sign_count >= 2 and dilution_count >= 2:
        verdict = "WINDOW_LIKELY"
        conclusion = "W2 相比 W3 明显更接近原文，窗口不一致是强候选解释。"
    elif w2_better_count >= 2:
        verdict = "WINDOW_PARTIAL"
        conclusion = "W2 有部分变量更接近原文，但符号/显著性或稀释趋势不够稳定，只能算部分支持。"
    else:
        verdict = "NO_PASS_YET"
        conclusion = "W2 没有系统性优于 W3，窗口不一致暂时不能解释表 2 复不出来。"

    lines = [
        "# 表 2 按上市年窗口切分诊断",
        "",
        "日期：2026-07-03",
        "",
        "## 结论先行",
        "",
        f"- 诊断结论：`{verdict}`。",
        f"- {conclusion}",
        "- 本轮只读现成 full scoregate master，不重建 master、不重跑 LLM、不改控制变量/FE 设定。",
        *([missing_year_note] if missing_year_note else []),
        "",
        "## 输入",
        "",
        f"- master：`{DEFAULT_MASTER}`",
        "- 回归公式：复用 `scripts/run_original_paper_table2_probe_20260702.py` 的 `run_regressions()`。",
        "- 单元格格式：`coef / HC1 t / p / N`。",
        "",
        "## 上市年分布",
        "",
        "| 上市年 | N |",
        "|---:|---:|",
        *[f"| {int(r.listing_year)} | {int(r.N)} |" for r in year_counts.itertuples()],
        "",
        "## 窗口样本",
        "",
        md_table(samples, ["window_label", "firm_N", "FInvention_nonmissing", "BHAR_nonmissing", "FSales_Growth_nonmissing", "Redundancy_mean", "Redundancy_std", "FInvention_mean"]),
        "",
        "## 主规格 controls_fe 对照",
        "",
        md_table(controls, ["Y", "规格", "W1(19-21)", "W2(19-22)", "W3(19-23)", "原文 coef/t/N"]),
        "",
        "## 趋势判定",
        "",
        md_table(trend, ["Y", "W1_coef", "W2_coef", "W3_coef", "W1_t", "W2_t", "W3_t", "W2_closer_than_W3", "W2_sign_matches_paper", "dilution_pattern_W2_to_W3"]),
        "",
        "读法：W2→W3 的确呈现加入 2023 后绝对值变小的稀释形态，但主规格里只有 `BHAR` 与原文同号；`FInvention` 和 `FSales_Growth` 在 W2 仍为正号。因此，窗口差异最多解释 BHAR 的一部分弱化，不能解释原文三个 Y 同时显著为负。",
        "",
        "## 全规格附表",
        "",
        md_table(all_specs, ["Y", "规格", "W1(19-21)", "W2(19-22)", "W3(19-23)", "原文 coef/t/N"]),
        "",
        "## 判断",
        "",
        "- W2 的 firm_N 应为 474，本轮实际为 `" + str(int(samples.loc[samples["window_label"].eq("W2(19-22)"), "firm_N"].iloc[0])) + "`。",
        "- W3 的 firm_N 为 `" + str(int(samples.loc[samples["window_label"].eq("W3(19-23)"), "firm_N"].iloc[0])) + "`，不是 X 文件的 " + str(int(master["code"].nunique())) + "；差异来自缺上市年且 Y 全缺的企业，不影响本轮窗口诊断。",
        "- 若只看主规格，W2 是否更接近原文要同时看符号、t 值和 W2→W3 是否被 2023 稀释。",
        "- 本轮输出只用于诊断窗口假说；不能直接把 2023 样本视为错误样本。",
        "",
        "## 输出文件",
        "",
        f"- window regressions：`{DEFAULT_RUN_DIR / 'table2_listing_window_regressions_20260703.csv'}`",
        f"- window samples：`{DEFAULT_RUN_DIR / 'table2_listing_window_samples_20260703.csv'}`",
        "",
    ]
    doc_out.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--master-path", type=Path, default=DEFAULT_MASTER)
    parser.add_argument("--run-dir", type=Path, default=DEFAULT_RUN_DIR)
    parser.add_argument("--doc-out", type=Path, default=DEFAULT_DOC)
    args = parser.parse_args()

    master = pd.read_csv(args.master_path, dtype={"code": str, "sec_code": str}, encoding="utf-8-sig")
    args.run_dir.mkdir(parents=True, exist_ok=True)

    regs, samples = run_window_regs(master)
    reg_out = args.run_dir / "table2_listing_window_regressions_20260703.csv"
    sample_out = args.run_dir / "table2_listing_window_samples_20260703.csv"
    regs.to_csv(reg_out, index=False, encoding="utf-8-sig")
    samples.to_csv(sample_out, index=False, encoding="utf-8-sig")
    write_doc(master, regs, samples, args.doc_out)

    print(f"regressions={reg_out}")
    print(f"samples={sample_out}")
    print(f"doc={args.doc_out}")
    print(
        regs[
            regs["dep_var"].isin(["FInvention", "BHAR", "FSales_Growth"])
            & regs["model"].eq("controls_fe")
        ][["window_label", "dep_var", "N", "coef", "t_HC1", "p_HC1", "adj_r2"]].to_string(index=False)
    )


if __name__ == "__main__":
    main()
