#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
DATE_TAG = "20260708"
TABLE2_MASTER = ROOT / "results/cutoff552_table2_471_probe_20260707/table2_471_candidate_master_20260707.csv"
SPECS = [
    ("primary_best", "proxy_tailmerge1500_floor50"),
    ("glm100_legacy", "proxy_tailmerge1700_floor50"),
]
RUN_DIR = ROOT / f"results/glm200_table2_gate_{DATE_TAG}"
DOC = ROOT / f"docs/00_current/glm200_table2_gate_{DATE_TAG}.md"
PATCH_SCRIPT = ROOT / "scripts/run_existing_controls_patch_20260706.py"


def load_patch():
    spec = importlib.util.spec_from_file_location("existing_controls_patch", PATCH_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {PATCH_SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fmt(value: object, digits: int = 4) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return ""


def md_table(df: pd.DataFrame, cols: list[str]) -> list[str]:
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, row in df.iterrows():
        vals = []
        for col in cols:
            val = row.get(col, "")
            if isinstance(val, float):
                vals.append(fmt(val))
            else:
                vals.append(str(val))
        out.append("| " + " | ".join(vals) + " |")
    return out


def main() -> None:
    patch = load_patch()
    base = patch.base
    outcomes = patch.OUTCOMES
    control_vars = patch.CURRENT_CONTROL_VARS
    fe_vars = patch.FE_VARS
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    controls = " + ".join(control_vars)
    fe = " + C(listing_year_fe) + C(industry_fe)"
    rows = []
    desc_rows = []
    sample_rows = []
    for spec_label, spec_name in SPECS:
        firm_metrics = ROOT / f"results/glm200_tailmerge_floor_candidates_{DATE_TAG}/{spec_name}_firm_metrics_{DATE_TAG}.csv"
        master = pd.read_csv(TABLE2_MASTER, dtype={"code": str, "sec_code": str}, low_memory=False)
        firm = pd.read_csv(firm_metrics, dtype={"sec_code": str})
        firm = firm.rename(columns={"Redundancy": "Redundancy_glm200", "lnN_tech": "lnN_tech_glm200"})
        df = master.merge(
            firm[["sec_code", "Redundancy_glm200", "lnN_tech_glm200", "chunk_n"]],
            on="sec_code",
            how="inner",
        )
        df["spec_label"] = spec_label
        df["spec_name"] = spec_name
        df["Redundancy_prior"] = pd.to_numeric(df["Redundancy"], errors="coerce")
        df["lnN_tech_prior"] = pd.to_numeric(df["lnN_tech"], errors="coerce")
        df["Redundancy"] = pd.to_numeric(df["Redundancy_glm200"], errors="coerce")
        df["lnN_tech"] = pd.to_numeric(df["lnN_tech_glm200"], errors="coerce")
        if "Underwriter" not in df.columns and "Underwriter_ipo" in df.columns:
            df["Underwriter"] = pd.to_numeric(df["Underwriter_ipo"], errors="coerce")

        numeric_cols = ["Redundancy", "lnN_tech", *outcomes, *control_vars]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        sample_rows.append({"spec_label": spec_label, "spec_name": spec_name, "firm_n": df["sec_code"].nunique()})
        for dep in outcomes:
            row = base.regression_result(
                spec_label,
                "current_controls_fe",
                dep,
                f"{dep} ~ Redundancy + {controls}{fe}",
                df,
                "Redundancy",
            )
            row["spec_label"] = spec_label
            row["spec_name"] = spec_name
            rows.append(row)

        desc_vars = ["Redundancy", "lnN_tech", *outcomes, *control_vars]
        for col in desc_vars:
            if col not in df.columns:
                continue
            s = pd.to_numeric(df[col], errors="coerce").dropna()
            desc_rows.append(
                {
                    "spec_label": spec_label,
                    "spec_name": spec_name,
                    "variable": col,
                    "N": int(s.shape[0]),
                    "mean": s.mean(),
                    "std": s.std(ddof=1),
                    "p25": s.quantile(0.25),
                    "median": s.median(),
                    "p75": s.quantile(0.75),
                }
            )
        df.to_csv(
            RUN_DIR / f"glm200_table2_master_{spec_name}_{DATE_TAG}.csv",
            index=False,
            encoding="utf-8-sig",
        )

    regs = pd.DataFrame(rows)
    desc = pd.DataFrame(desc_rows)
    samples = pd.DataFrame(sample_rows)

    regs.to_csv(RUN_DIR / f"glm200_table2_regressions_{DATE_TAG}.csv", index=False, encoding="utf-8-sig")
    desc.to_csv(RUN_DIR / f"glm200_table2_descriptives_{DATE_TAG}.csv", index=False, encoding="utf-8-sig")
    samples.to_csv(RUN_DIR / f"glm200_table2_samples_{DATE_TAG}.csv", index=False, encoding="utf-8-sig")

    result_lines = []
    for spec_label, spec_name in SPECS:
        for dep in outcomes:
            row = regs[regs["spec_label"].eq(spec_label) & regs["dep_var"].eq(dep)].iloc[0]
            result_lines.append(
                {
                    "spec": spec_label,
                    "outcome": dep,
                    "N": int(row["N"]),
                    "coef": fmt(row["coef"]),
                    "t": fmt(row["t_HC1"]),
                    "p": fmt(row["p_HC1"]),
                    "adj_r2": fmt(row["adj_r2"]),
                }
            )
    primary_desc = desc[desc["spec_label"].eq("primary_best")].copy()
    DOC.write_text(
        "\n".join(
            [
                "# GLM200 Table 2 Gate",
                "",
                "日期：2026-07-08",
                "",
                "## 结论",
                "",
                f"- 样本：GLM200 与 Table2 471 交集 firm={int(samples.loc[samples['spec_label'].eq('primary_best'), 'firm_n'].iloc[0])}。",
                "- X 主口径：使用 GLM200 最贴 Table 1 的 `proxy_tailmerge1500_floor50` 企业层 Redundancy，并同步替换 `lnN_tech`。",
                "- X 对照口径：保留 GLM100 阶段旧主口径 `proxy_tailmerge1700_floor50` 作为敏感性检查。",
                "- 控制变量：沿用当前 current-controls FE 规格：`lnN_tech + Size + Lev + ROA + Offerfee + Underwriter + Age + year FE + industry FE`。",
                "- 这是 GLM-only 是否值得继续扩到 471 家的中途 gate，不是 strict 原文复刻。",
                "- Gate 判定：`NO_PASS_YET`。`FInvention` 已显著负向，`BHAR` 为负但不显著，`FSales_Growth` 仍为正且不显著。",
                "- 含义：GLM-only measurement 已明显优于 Codex 机械修复，但还不能结束复刻；下一步应跑到更接近原文 Table 2 的 471 家候选样本，并继续核对 `BHAR` 与 `FSales_Growth` 的原文口径。",
                "",
                "## 回归结果",
                "",
                *md_table(pd.DataFrame(result_lines), ["spec", "outcome", "N", "coef", "t", "p", "adj_r2"]),
                "",
                "## 主口径描述统计",
                "",
                *md_table(primary_desc, ["variable", "N", "mean", "std", "p25", "median", "p75"]),
                "",
                "## 输出",
                "",
                f"- samples：`{RUN_DIR / f'glm200_table2_samples_{DATE_TAG}.csv'}`",
                f"- regressions：`{RUN_DIR / f'glm200_table2_regressions_{DATE_TAG}.csv'}`",
                f"- descriptives：`{RUN_DIR / f'glm200_table2_descriptives_{DATE_TAG}.csv'}`",
                f"- primary master：`{RUN_DIR / f'glm200_table2_master_proxy_tailmerge1500_floor50_{DATE_TAG}.csv'}`",
                f"- legacy master：`{RUN_DIR / f'glm200_table2_master_proxy_tailmerge1700_floor50_{DATE_TAG}.csv'}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print({"doc": str(DOC), "regressions": str(RUN_DIR / f"glm200_table2_regressions_{DATE_TAG}.csv")})


if __name__ == "__main__":
    main()
