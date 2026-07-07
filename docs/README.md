# Docs Index

日期：2026-07-07

## 当前优先阅读

当前工作只按下面顺序读，旧 pilot 和早期 handoff 只作溯源：

1. `00_current/candidate566_x_universe_after_first_batch_20260707.md`
2. `00_current/table2_candidate566_ipo_pre_controls_20260707.md`
3. `00_current/sample_and_ready_y_fields_audit_20260706.md`
4. `00_current/first_batch_25firm_measurement_runbook_20260706.md`
5. `00_current/first_batch25_glm4_dewrap_join_measurement_20260706.md`
6. `00_current/text_gap_backfill_probe_20260706.md`
7. `00_current/table2_ipo_pre_controls_rerun_20260706.md`
8. `00_current/y_bhar_fsales_definition_audit_20260706.md`
9. `00_current/table2_data_processing_breakpoints_20260706.md`
10. `00_current/bhar_official_market_return_audit_20260706.md`
11. `00_current/fsales_growth_window_sensitivity_20260706.md`
12. `00_current/table2_listing_year_segment_controls_20260706.md`
13. `00_current/table2_existing_controls_patch_20260706.md`
14. `00_current/descriptive_comparison_vs_original_20260706.md`
15. `00_current/管理世界式_主要变量描述性统计对比_20260706.md`
16. `00_current/table2_glm4_dewrap_full543_audit_20260706.md`
17. `00_current/glm4_dewrap_join_full543_20260705.md`
18. `00_current/当前状态总结与新对话交接_20260705.md`

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

X 的 measurement gate 已经可以锁定：`dewrap_join + GLM tokenizer chunking + cot_v3b_len132_tight + Summary_len_proxy` 在 full543 和补齐首批25家后都通过 Table 1 量级和效度门槛。合并后的 candidate566 为 566 家、9083 个 chunk，企业层 `Redundancy` mean=29.053，原文为 29.074；`lnN_tech` mean=10.967，原文为 10.962。

Table 2 仍是 `NO_PASS_YET`，现在最优先的问题从“单个 Y 怎么调”上移到“样本制度和 Y 精确定义是否对齐”：

- 国泰安 `IPO_Ipobasic` 可重建 2019-2023 科创板首次发行上市 universe：567 家。candidate566 已覆盖其中 566 家，仅缺 `688287`，该样本是转板上市报告书，不是标准 IPO 招股说明书。
- 原文 Table 1 为 552 家；candidate566 相比原文仍多 14 家。当前 chunk N=9083，比原文 8683 多 400 个，与多出的 firm N 基本一致，说明差距主要来自样本筛选制度，不是 tokenizer 或摘要机制。
- 首批 25 家主口径补跑结果已并入 candidate566。单独看首批样本：`Summary_len_proxy` mean=122.417，`Redundancy_chunk_proxy` mean=32.278，`Text_len` mean=3809.610，Panel B Spearman rho=-0.513，低评分组冗余中位数 34.539 高于高评分组 29.459。
- candidate566 重建 Table 2 master 后，完整 2019-2023 下 all 3 Y + ipo-pre controls complete 为 539 家；2019-2022 子样本为 474 家，已经非常接近原文 Table 2 的 471 家。
- candidate566 下控制变量描述统计多数贴近原文：`Size_ipo_pre` mean=20.748 vs 20.741，`Lev_ipo_pre` 0.356 vs 0.356，`ROA_ipo_pre` 0.092 vs 0.094，`Offerfee` 18.324 vs 18.325，`ScopeLen` 5.669 vs 5.671。
- candidate566 Table 2 主规格仍未复刻原文：`FInvention` 保持负向但弱化，full + RD staff 规格 `coef=-0.0368, p=0.094`；`BHAR` 与 `FSales_Growth` 仍为正向且不显著。
- 新下载 IPO 表覆盖足够：`IPO_Ipobasic / IPO_IpoBalance / IPO_IpoIncome / IPO_Iponoem` 覆盖 543 家，`IPO_Ipocsne` 覆盖 541 家。
- `Underwriter_ipo` 仍偏高：candidate566 mean=0.642 vs 原文 0.574；`RD_Staff_ipo` mean=0.280 vs 原文 0.305。
- `NumIndSeg / NumProdSeg / ScopeLen` 的当前替代口径描述统计也接近原文，但 `NumIndSeg / NumProdSeg` 仍是上市当年年报附注替代，不是 strict pre-IPO 口径。
- 旧 543 新 controls 下 `FInvention` 曾恢复为显著负向；并入首批25家并重建 candidate566 后显著性降为边际，说明仍需先确认原文 552/471 样本筛选。
- `BHAR` 仍为弱正，`FSales_Growth` 仍为正；把 `FSales_Growth` 改成招股前收入到上市后收入的窗口也仍为正。
- 20260706 Y 口径核对显示：当前 `BHAR` 不是逐字原文口径，但在近似原文 N 的 2019-2022 子样本中描述统计仍最贴原文；CSMAR 周度市场调整表候选反而离原文更远且回归不转负。
- 新下载 `TRD_Year` 与 `TRD_Cndalym` 后，官方综合日市场收益率仍不能把当前一年买入持有 `BHAR` 拉成负向显著；`listing_year+1` 官方年收益候选转为负向但不显著，且是日历年收益，不等同于“上市一年内”。
- 处理断点审计显示：`BHAR` 的 365 自然日、剔除首日、STAR 等权基准更贴近原文分布，但主回归仍为弱正；`FSales_Growth` 的当前 `L -> L+1` 口径反而最贴原文分布，完整会计年度或上市月份切换不能同时修复分布和回归方向。
- `FSales_Growth` 的窗口问题更明显，`L+1 -> L+2` 可转负但描述统计远离原文且不显著。

## 下一步

不要继续调摘要或 X。下一步应集中审计：

1. 从 candidate566 出发，查明原文 Table 1 的 552 家排除了哪 14 家；重点看转板/特殊上市、同一公司重复发行、金融/未盈利/特殊表决权、缺失完整 Y 或 controls 等制度性筛选。
2. 在 2019-2022 的 474 家接近样本上，继续核对原文 Table 2 的 471 家精确缺口；不要再盲调 X。
3. 定向下载或核对 CSMAR 是否有原文更直接的 `BHAR`/持有期超额收益、成长能力中的营业收入增长率字段；优先用数据库定义对齐，而不是手工再造一版。
4. `BHAR` 暂保留 365 自然日 + 剔除首日 + STAR 等权作为候选；`FSales_Growth` 暂保留当前 `L -> L+1` 作为最贴分布候选。
