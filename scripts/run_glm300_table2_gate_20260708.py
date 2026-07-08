#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path

import pandas as pd


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
DATE_TAG = "20260708"
TABLE2_MASTER = ROOT / "results/cutoff552_table2_471_probe_20260707/table2_471_candidate_master_20260707.csv"
CANDIDATE_SUMMARY = ROOT / f"results/glm300_tailmerge_floor_candidates_{DATE_TAG}/candidate_summary_{DATE_TAG}.csv"
RUN_DIR = ROOT / f"results/glm300_table2_gate_{DATE_TAG}"
DOC = ROOT / f"docs/00_current/glm300_table2_gate_{DATE_TAG}.md"
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


def choose_specs() -> list[tuple[str, str]]:
    summary = pd.read_csv(CANDIDATE_SUMMARY).sort_values("loss_all")
    names: list[tuple[str, str]] = [("primary_best", str(summary.iloc[0]["name"]))]
    for label, name in [("glm200_primary", "proxy_tailmerge1500_floor50"), ("glm100_legacy", "proxy_tailmerge1700_floor50")]:
        if name not in [n for _, n in names]:
            names.append((label, name))
    return names


def gate_label(regs: pd.DataFrame) -> str:
    primary = regs[regs["spec_label"].eq("primary_best")]
    vals = {r["dep_var"]: r for _, r in primary.iterrows()}
    finv = vals.get("FInvention")
    bhar = vals.get("BHAR")
    fsales = vals.get("FSales_Growth")
    if finv is not None and bhar is not None and fsales is not None:
        if finv["coef"] < 0 and finv["p_HC1"] < 0.05 and bhar["coef"] < 0 and fsales["coef"] < 0:
            return "PASS_DIRECTIONAL"
        if finv["coef"] < 0 and finv["p_HC1"] < 0.05:
            return "NO_PASS_YET"
    return "STOP_OR_RECHECK"


def main() -> None:
    patch = load_patch()
    base = patch.base
    outcomes = patch.OUTCOMES
    control_vars = patch.CURRENT_CONTROL_VARS
    RUN_DIR.mkdir(parents=True, exist_ok=True)

    specs = choose_specs()
    controls = " + ".join(control_vars)
    fe = " + C(listing_year_fe) + C(industry_fe)"
    rows = []
    desc_rows = []
    sample_rows = []
    for spec_label, spec_name in specs:
        firm_metrics = ROOT / f"results/glm300_tailmerge_floor_candidates_{DATE_TAG}/{spec_name}_firm_metrics_{DATE_TAG}.csv"
        master = pd.read_csv(TABLE2_MASTER, dtype={"code": str, "sec_code": str}, low_memory=False)
        firm = pd.read_csv(firm_metrics, dtype={"sec_code": str})
        firm = firm.rename(columns={"Redundancy": "Redundancy_glm300", "lnN_tech": "lnN_tech_glm300"})
        df = master.merge(
            firm[["sec_code", "Redundancy_glm300", "lnN_tech_glm300", "chunk_n"]],
            on="sec_code",
            how="inner",
        )
        df["spec_label"] = spec_label
        df["spec_name"] = spec_name
        df["Redundancy_prior"] = pd.to_numeric(df["Redundancy"], errors="coerce")
        df["lnN_tech_prior"] = pd.to_numeric(df["lnN_tech"], errors="coerce")
        df["Redundancy"] = pd.to_numeric(df["Redundancy_glm300"], errors="coerce")
        df["lnN_tech"] = pd.to_numeric(df["lnN_tech_glm300"], errors="coerce")
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

        for col in ["Redundancy", "lnN_tech", *outcomes, *control_vars]:
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
            RUN_DIR / f"glm300_table2_master_{spec_name}_{DATE_TAG}.csv",
            index=False,
            encoding="utf-8-sig",
        )

    regs = pd.DataFrame(rows)
    desc = pd.DataFrame(desc_rows)
    samples = pd.DataFrame(sample_rows)
    label = gate_label(regs)

    regs.to_csv(RUN_DIR / f"glm300_table2_regressions_{DATE_TAG}.csv", index=False, encoding="utf-8-sig")
    desc.to_csv(RUN_DIR / f"glm300_table2_descriptives_{DATE_TAG}.csv", index=False, encoding="utf-8-sig")
    samples.to_csv(RUN_DIR / f"glm300_table2_samples_{DATE_TAG}.csv", index=False, encoding="utf-8-sig")

    result_lines = []
    for spec_label, spec_name in specs:
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
                "# GLM300 Table 2 Gate",
                "",
                "日期：2026-07-08",
                "",
                "## 结论",
                "",
                f"- 样本：GLM300 与 Table2 471 交集 firm={int(samples.loc[samples['spec_label'].eq('primary_best'), 'firm_n'].iloc[0])}。",
                f"- X 主口径：使用 GLM300 最贴 Table 1 的 `{specs[0][1]}` 企业层 Redundancy，并同步替换 `lnN_tech`。",
                "- 控制变量：沿用 current-controls FE 规格：`lnN_tech + Size + Lev + ROA + Offerfee + Underwriter + Age + year FE + industry FE`。",
                f"- Gate 判定：`{label}`。",
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
                f"- samples：`{RUN_DIR / f'glm300_table2_samples_{DATE_TAG}.csv'}`",
                f"- regressions：`{RUN_DIR / f'glm300_table2_regressions_{DATE_TAG}.csv'}`",
                f"- descriptives：`{RUN_DIR / f'glm300_table2_descriptives_{DATE_TAG}.csv'}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print({"doc": str(DOC), "regressions": str(RUN_DIR / f"glm300_table2_regressions_{DATE_TAG}.csv"), "gate": label})


if __name__ == "__main__":
    main()
