# Docs Index

日期：2026-07-08

## 当前优先阅读

当前工作只按下面顺序读，旧 pilot 和早期 handoff 只作溯源：

1. `00_current/glm300_table2_gate_20260708.md`
2. `00_current/siliconflow_glm4_32b_glm300_20260708.md`
3. `00_current/siliconflow_glm4_32b_table2_next100_after200_20260708.md`
4. `00_current/glm_next100_after200_table2_source_20260708.md`
5. `00_current/glm200_table2_gate_20260708.md`
6. `00_current/siliconflow_glm4_32b_glm200_20260708.md`
7. `00_current/siliconflow_glm4_32b_table2_next100_20260708.md`
8. `00_current/glm_next100_table2_source_20260708.md`
9. `00_current/siliconflow_glm4_32b_glm100_20260707.md`
10. `00_current/siliconflow_glm4_32b_table2_next50_20260707.md`
11. `00_current/glm_next50_table2_source_20260707.md`
12. `00_current/glm_only_replication_hypothesis_20260707.md`
13. `00_current/summary_diagnostic_x_table2_20260707.md`
14. `00_current/summary_denominator_right_tail_repair_probe_20260707.md`
15. `00_current/sample552_tailmerge_threshold_probe_20260707.md`
16. `00_current/glm50_tailmerge_floor_candidate_gate_20260707.md`
17. `00_current/glm50_processing_descriptive_sweep_20260707.md`
18. `00_current/siliconflow_glm4_32b_pilot50_measurement_20260707.md`
19. `00_current/siliconflow_glm4_32b_pilot50_20260707.md`
20. `00_current/siliconflow_glm4_32b_pilot5_measurement_20260707.md`
21. `00_current/siliconflow_glm4_32b_pilot5_20260707.md`
22. `00_current/cutoff552_table2_471_probe_20260707.md`
23. `00_current/candidate566_x_universe_after_first_batch_20260707.md`
24. `00_current/table2_candidate566_ipo_pre_controls_20260707.md`
25. `00_current/sample_and_ready_y_fields_audit_20260706.md`
26. `00_current/first_batch_25firm_measurement_runbook_20260706.md`
27. `00_current/first_batch25_glm4_dewrap_join_measurement_20260706.md`
28. `00_current/text_gap_backfill_probe_20260706.md`
29. `00_current/table2_ipo_pre_controls_rerun_20260706.md`
30. `00_current/y_bhar_fsales_definition_audit_20260706.md`
31. `00_current/table2_data_processing_breakpoints_20260706.md`
32. `00_current/bhar_official_market_return_audit_20260706.md`
33. `00_current/fsales_growth_window_sensitivity_20260706.md`
34. `00_current/table2_listing_year_segment_controls_20260706.md`
35. `00_current/table2_existing_controls_patch_20260706.md`
36. `00_current/descriptive_comparison_vs_original_20260706.md`
37. `00_current/管理世界式_主要变量描述性统计对比_20260706.md`
38. `00_current/table2_glm4_dewrap_full543_audit_20260706.md`
39. `00_current/glm4_dewrap_join_full543_20260705.md`
40. `00_current/当前状态总结与新对话交接_20260705.md`

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

### 2026-07-08 追加：strict Table 2 与 GLM471 补跑脚本

- 新增 strict Table 2 master：`00_current/glm_table2_strict_master_20260708.md`。主规格 `paper_exact_*` 明确不含 `RD_Staff_ipo`，`RD_Staff_ipo` 只作为 `rd_staff_extra_*` 敏感性。
- 新增 GLM remaining-to-471 source：`00_current/glm_remaining_to471_table2_source_20260708.md`。当前 GLM300 与 Table2 471 候选交集为 288 家，剩余 183 家、2733 个 chunk，已分 6 个 source shards。
- 新增 BHAR/FSales 断点瀑布：`00_current/table2_bhar_fsales_waterfall_20260708.md`。当前读法：BHAR 从单变量到 full controls 一直为负，paper-exact 下约为 `-0.021`、接近原文；FSales_Growth 从单变量起就是正，优先怀疑 Y 字段/窗口。

X measurement 已经从“明显不对”推进到“Table 1 量级基本可用的候选口径”，但还不能视为完整复刻：`GLM-4-32B + dewrap_join/GLM tokenizer chunking + cot_v3b_len132_tight + Summary_len_proxy + tail_merge + summary_floor=50` 在 GLM300 上仍能稳定贴近原文 Table 1，且 Panel B 正向判据成立；但 Table 2 经济后果只恢复了 `FInvention` 显著负向，`BHAR` 仍负向不显著，`FSales_Growth` 仍正向不显著。因此当前结论是 `MEASUREMENT_GATE_PASS_WEAK / TABLE2_NO_PASS_YET`。项目不能结题，下一步不能只靠继续扩样，要同时核对原文样本制度和 Y 精确定义。

Table 2 仍是 `NO_PASS_YET`，现在最优先的问题从“单个 Y 怎么调”上移到“样本制度和 Y 精确定义是否对齐”：

- 国泰安 `IPO_Ipobasic` 可重建 2019-2023 科创板首次发行上市 universe：567 家。candidate566 已覆盖其中 566 家，仅缺 `688287`，该样本是转板上市报告书，不是标准 IPO 招股说明书。
- 原文 Table 1 为 552 家；candidate566 相比原文仍多 14 家。当前 chunk N=9083，比原文 8683 多 400 个，与多出的 firm N 基本一致，说明差距主要来自样本筛选制度，不是 tokenizer 或摘要机制。
- 首批 25 家主口径补跑结果已并入 candidate566。单独看首批样本：`Summary_len_proxy` mean=122.417，`Redundancy_chunk_proxy` mean=32.278，`Text_len` mean=3809.610，Panel B Spearman rho=-0.513，低评分组冗余中位数 34.539 高于高评分组 29.459。
- candidate566 重建 Table 2 master 后，完整 2019-2023 下 all 3 Y + ipo-pre controls complete 为 539 家；2019-2022 子样本为 474 家，已经非常接近原文 Table 2 的 471 家。
- `2023-08-15` 上市日 cutoff 可以把 candidate566 精确切成原文 Table 1 的 552 家；但 chunk N 仍为 8906，高于原文 8683，说明 cutoff 解释 firm N 但不能完全解释 chunk 层数量。
- 552 家 cutoff 上做 tail-merge 阈值扫描：`tail_merge<threshold=1700` 后 chunk N=8679，只比原文 8683 少 4 个；`threshold=1600` 后 chunk N=8699，比原文多 16 个。tail-merge 能修复 chunk N 和 Text_len std，但 `Redundancy_chunk` mean/std 仍低于原文，说明当前摘要右尾仍不够像原文。
- 进一步做 summary denominator diagnostic X：`tail_merge<1700 + Relevant_score<1.8 cap80` 和 `tail_merge<1700 + high_score_share<=10% cap80` 确实能把右尾描述统计推近原文；其中 `score18 cap80` 后 `Redundancy_chunk` mean/std/p75=32.943/10.776/36.907。但接回 471 家 Table 2 后，`BHAR` 仍为正，`FSales_Growth` 仍为正，只能说明右尾机制可修，不能说明 X 修完即可复刻主效应。
- 2019-2022 complete sample 中删去 `688475`、`688496`、`688525` 可以把 474 精确切成原文 Table 2 的 471 家；但重跑后 `BHAR` 仍为正且不显著，`FSales_Growth` 仍为正且不显著。
- SiliconFlow `THUDM/GLM-4-32B-0414` 50 家 pilot 已完成：proxy 口径下 `Summary_len` mean=124.325，低于原文 132.678；`Redundancy_chunk` mean=35.731，高于原文 32.176；GLM-token 摘要口径下 `Redundancy_chunk` mean=31.362，反而更贴原文。Panel B 方向成立但强度很弱：rho=-0.093, p=0.0083，低评分组冗余中位数 32.765 高于高评分组 31.091；cluster 回归不显著，且 13 个 chunk 缺失评分。50 家自身仍是 `NO_PASS_YET`，但在 Codex 主口径和 Codex 机械修复都不能恢复 Table 2 后，GLM 不应再只作为旁证，而应进入 471 家 Table 2 样本验证。
- GLM 50 家描述性统计反推扫描显示：最接近原文 Table 1 的处理不是直接改用 GLM-token，而是 `proxy + merge_short_tail(threshold=2000) + summary_floor=50`。该规则下 `Text_len` std=336.975 vs 原文 343.868，`Summary_len` mean=128.946 vs 132.678，`Redundancy_chunk` mean=33.629 vs 32.176，std=11.068 vs 11.730，企业层 `Redundancy` mean=30.215 vs 29.074。解释是原文可能没有保留极短尾 chunk，也不会允许 3-20 字的极短摘要直接进入分母。
- SiliconFlow GLM Table2 next50 已完成：新增 50 家、885 个 chunk，三段 shard 顺序跑完，合并目录为 `results/siliconflow_glm4_32b_table2_next50_merged_20260707`。next50 原始 proxy `Summary_len` mean=124.595，`Redundancy_chunk` mean=33.633；最佳候选为 `proxy_tailmerge1500_floor50`，`Text_len` mean/std=3885.223/340.943，`Summary_len` mean/std=126.842/37.980，`Redundancy_chunk` mean/std=33.204/10.450。
- GLM100 合并诊断已完成：旧 GLM50 与 next50 无公司或 custom_id 重叠，合并后为 100 家、1706 个 chunk。GLM100 最接近原文 Table 1 的候选为 `proxy_tailmerge1700_floor50`，与 `proxy_tailmerge2000_floor50` 几乎并列；最佳候选下 `Text_len` mean/std=3897.920/333.374，`Summary_len` mean/std=127.615/41.842，`Redundancy_chunk` mean/std=33.392/10.738，企业层 `Redundancy` mean/std=30.418/2.710。Panel B 方向成立但弱：rho=-0.114, p<0.001。
- GLM100 的新信息是：GLM-only 不是 5 家或 50 家偶然现象，Table 1 量级贴近度在 100 家上仍稳定；但 Panel B 仍弱，且尚未接 Table 2 主效应，因此仍不能宣称 X measurement 复刻完成。
- GLM next100 已完成：新增 100 家、1756 个 chunk，五段 shard 顺序跑完，合并目录为 `results/siliconflow_glm4_32b_table2_next100_merged_20260708`。next100 最佳候选为 `proxy_tailmerge1700_floor50`，`Summary_len` mean=126.881，`Redundancy_chunk` mean=33.452，Panel B rho=-0.093, p<0.001。
- GLM200 合并诊断已完成：GLM100 与 next100 合并后为 200 家、3462 个原始 chunk。最接近原文 Table 1 的候选变为 `proxy_tailmerge1500_floor50`：chunk=3395，`Text_len` mean/std=3879.167/345.151，`Summary_len` mean/std=126.793/41.845，`Redundancy_chunk` mean/std=33.389/10.643，企业层 `Redundancy` mean/std=30.597/2.599。原文对应均值分别为 `Text_len=3866.817`、`Summary_len=132.678`、`Redundancy_chunk=32.176`、`Redundancy=29.074`。
- GLM200 Panel B 方向成立但仍弱：主候选下 rho=-0.100, p<0.001；低评分组 `Redundancy_chunk` 中位数 32.549 高于高评分组 31.190，满足正向判据。Panel C rho=0.057, p<0.001；Panel D rho=-0.256, p<0.001。
- GLM200 接当前 Table2 master 后，与 Table2 471 候选交集为 188 家；current-controls FE 下 `FInvention` 已恢复显著负向：coef=-0.0755, t=-2.339, p=0.019。`BHAR` 为负但不显著：coef=-0.0267, t=-1.515, p=0.130。`FSales_Growth` 仍为正且不显著：coef=0.0068, p=0.705。这说明 GLM-only measurement 明显优于 Codex 机械修复，但还没有通过 Table 2 经济后果 gate。
- GLM next100 after GLM200 已完成：新增 100 家、1655 个 chunk，五段 shard 跑完并验收通过；其中 2 个 GLM 空摘要 chunk 做了透明兜底摘要，以避免 0 分母，评分不改。合并目录为 `results/siliconflow_glm4_32b_table2_next100_after200_merged_20260708`。
- GLM300 合并诊断已完成：合并后为 300 家、5117 个原始 chunk。最接近原文 Table 1 的候选为 `proxy_tailmerge1600_floor50`：chunk=5003，`Text_len` mean/std=3884.759/337.136，`Summary_len` mean/std=126.963/45.966，`Redundancy_chunk` mean/std=33.442/10.546，企业层 `Redundancy` mean/std=30.657/2.581。原文对应均值分别为 `Text_len=3866.817`、`Summary_len=132.678`、`Redundancy_chunk=32.176`、`Redundancy=29.074`。
- GLM300 Panel B 方向成立但仍弱：主候选下 rho=-0.087, p<0.001；低评分组 `Redundancy_chunk` 中位数 32.523 高于高评分组 31.291，满足正向判据。Panel C rho=0.055, p<0.001；Panel D rho=-0.250, p<0.001。
- GLM300 接当前 Table2 master 后，与 Table2 471 候选交集为 288 家；current-controls FE 下 `FInvention` 仍显著负向：coef=-0.0575, t=-2.476, p=0.013。`BHAR` 为负但不显著：coef=-0.0154, t=-1.222, p=0.222。`FSales_Growth` 仍为正且不显著：coef=0.0148, p=0.477。扩样到 300 家没有修复 Table 2 主效应，只说明 X measurement 量级更稳。
- GLM 50 家与现有 552 家给出的处理规则不同：GLM 需要 `summary_floor=50` 来处理极短摘要；现有 Codex 552 家几乎不需要 floor，关键是 `tail_merge` 阈值约 1600-1700。二者共同指向“尾部 chunk 处理”是当前最像原文口径的缺口，但不能直接证明主效应会恢复。
- SiliconFlow 5 家 pilot 的乐观量级不再作为主要证据，只保留为早期模型行为记录。
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

不要把机械 cap 版 X 定为正式变量，也不要继续围绕 Codex 摘要分母反复贴表。GLM300 后，扩样本身已经不能解释 `BHAR / FSales_Growth` 不复刻；下一步应把 GLM 继续补到 Table2 471 家候选作为最后的 measurement falsification，同时并行核对 Y 和样本制度：

1. 固定 GLM 流程候选：`THUDM/GLM-4-32B-0414 + dewrap_join/GLM tokenizer chunk + proxy 中文长度 + tail_merge<1600 + summary_floor=50`；主口径暂用 GLM300 最佳候选 `proxy_tailmerge1600_floor50`，保留 `1500/1700` 作为敏感性。
2. 把 GLM 跑到原文 Table 2 471 家候选样本作为最后的 X measurement 裁决；若 `BHAR / FSales_Growth` 在 471 家仍不能至少转负，应停止把问题继续归咎于摘要模型。
3. 若 GLM 471 家 Table 2 继续改善，再补 552 家 Table 1 cutoff 样本，检查描述统计、Panel B/C/D 和企业层排序。
4. 同时将 `list_date_csmar < 2023-08-15` 作为候选 Table 1 firm-level cutoff 写入样本制度，并保留 `688475`、`688496`、`688525` 作为 Table 2 年末窗口排除候选。
5. 继续核对 CSMAR 是否有原文更直接的 `BHAR`/持有期超额收益、成长能力中的营业收入增长率字段；但不要再用 Codex 机械调参替代这一步。
