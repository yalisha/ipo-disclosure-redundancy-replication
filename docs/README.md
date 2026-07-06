# Docs Index

日期：2026-07-06

## 当前优先阅读

当前工作只按下面顺序读，旧 pilot 和早期 handoff 只作溯源：

1. `00_current/sample_and_ready_y_fields_audit_20260706.md`
2. `00_current/first_batch_25firm_measurement_runbook_20260706.md`
3. `00_current/text_gap_backfill_probe_20260706.md`
4. `00_current/table2_ipo_pre_controls_rerun_20260706.md`
5. `00_current/y_bhar_fsales_definition_audit_20260706.md`
6. `00_current/table2_data_processing_breakpoints_20260706.md`
7. `00_current/bhar_official_market_return_audit_20260706.md`
8. `00_current/fsales_growth_window_sensitivity_20260706.md`
9. `00_current/table2_listing_year_segment_controls_20260706.md`
10. `00_current/table2_existing_controls_patch_20260706.md`
11. `00_current/descriptive_comparison_vs_original_20260706.md`
12. `00_current/管理世界式_主要变量描述性统计对比_20260706.md`
13. `00_current/table2_glm4_dewrap_full543_audit_20260706.md`
14. `00_current/glm4_dewrap_join_full543_20260705.md`
15. `00_current/当前状态总结与新对话交接_20260705.md`

## 目录结构

| 目录 | 内容 |
|---|---|
| `00_current/` | 当前状态、最新 Table 2/描述统计/给外部模型材料 |
| `01_measurement_method/` | 冗余变量构造方法、长度单位、tailfix/scoregate 口径 |
| `02_measurement_gates/` | 25/50/100/150/200/250 家 gate 和扩样记录 |
| `03_table1_validation/` | Table 1、Panel C、chunk 层验证 |
| `04_table2_outcomes/` | 结果变量、外部数据、Table 2 经济后果复刻 |
| `05_handoff_archive/` | 旧 handoff、历史交接文档 |
| `06_external_review/` | Claude/Pro/老师复核材料 |
| `90_source_evidence/` | 原文官网、CNKI、附录证据快照 |
| `99_early_archive/` | 早期 prompt/QC/token_proxy 试跑归档 |

## 当前判断

X 的 measurement gate 已经可以锁定：`dewrap_join + GLM tokenizer chunking + cot_v3b_len132_tight + Summary_len_proxy` 在 543 家全样本上通过 Table 1 量级和效度门槛。企业层 `Redundancy` mean=28.944，原文为 29.074；`lnN_tech` mean=10.966，原文为 10.962。

Table 2 仍是 `NO_PASS_YET`，现在最优先的问题从“单个 Y 怎么调”上移到“样本制度是否对齐”：

- 国泰安 `IPO_Ipobasic` 可重建 2019-2023 科创板首次发行上市 universe：567 家。当前 X master 为 543 家，其中只有 541 家与该 universe 重合，缺 26 家，另有 `688688`、`688717` 两家不属于 2019-2023 已上市 universe。
- 26 家缺口中 25 家是 2019-07-22 首批科创板公司，另 1 家是 `688287`。这说明当前 543 并不是原文 552 的合法近似，必须先补齐/判定这些公司。
- 补抓验证显示：25 家首批科创板公司此前被旧抓取窗口漏掉，现已成功下载并抽取“业务与技术”，合计 772 个 chunk；`688287` 是科创板转板上市报告书，应优先排除或单独说明。
- 原文 Table 2 的 471 家，和当前 2019-2022 `FSales_Growth` 非缺失数正好一致；但加入当前 controls 后主规格只剩 459 家，说明 controls 缺失处理也没完全对齐原文。
- 新下载 IPO 表覆盖足够：`IPO_Ipobasic / IPO_IpoBalance / IPO_IpoIncome / IPO_Iponoem` 覆盖 543 家，`IPO_Ipocsne` 覆盖 541 家。
- `Size_ipo_pre / Lev_ipo_pre / ROA_ipo_pre` 与原文描述统计基本贴合；`Underwriter_ipo` mean=0.649 vs 原文 0.574；`RD_Staff_ipo` mean=0.280 vs 原文 0.305。
- `NumIndSeg / NumProdSeg / ScopeLen` 的当前替代口径描述统计也接近原文，但 `NumIndSeg / NumProdSeg` 仍是上市当年年报附注替代，不是 strict pre-IPO 口径。
- 新 controls 下，`FInvention` 已经恢复为显著负向：`ipo_pre_fin_controls_rd_staff` 中 `coef=-0.0465, t=-2.01, p=0.0447`。
- `BHAR` 仍为弱正，`FSales_Growth` 仍为正；把 `FSales_Growth` 改成招股前收入到上市后收入的窗口也仍为正。
- 20260706 Y 口径核对显示：当前 `BHAR` 不是逐字原文口径，但在近似原文 N 的 2019-2022 子样本中描述统计仍最贴原文；CSMAR 周度市场调整表候选反而离原文更远且回归不转负。
- 新下载 `TRD_Year` 与 `TRD_Cndalym` 后，官方综合日市场收益率仍不能把当前一年买入持有 `BHAR` 拉成负向显著；`listing_year+1` 官方年收益候选转为负向但不显著，且是日历年收益，不等同于“上市一年内”。
- 处理断点审计显示：`BHAR` 的 365 自然日、剔除首日、STAR 等权基准更贴近原文分布，但主回归仍为弱正；`FSales_Growth` 的当前 `L -> L+1` 口径反而最贴原文分布，完整会计年度或上市月份切换不能同时修复分布和回归方向。
- `FSales_Growth` 的窗口问题更明显，`L+1 -> L+2` 可转负但描述统计远离原文且不显著。

## 下一步

不要继续调摘要或 X。下一步应集中审计：

1. 对首批 25 家补跑 `cot_v3b_len132_tight`，再与 full543 合并成候选 X universe；这一步约 772 个 chunk，会消耗较多 LLM 配额。
2. 候选 universe 中剔除 `688688`、`688717`，并优先排除或单独标注 `688287` 转板样本。
3. 用补齐后的 universe 重新计算 X，再判断如何从 565/566 对齐到原文 552。
4. 定向下载 CSMAR 成长能力/财务指标分析中的营业收入增长率，以及市场调整年个股回报率或持有期超额收益字段。
5. `BHAR` 保留 365 自然日 + 剔除首日 + STAR 等权作为候选；`FSales_Growth` 暂保留当前 `L -> L+1` 作为最贴分布候选，不继续盲目扩窗口。
