# Docs Index

日期：2026-07-06

## 当前优先阅读

当前工作只看 `00_current/`：

- `00_current/当前状态总结与新对话交接_20260705.md`
- `00_current/glm4_dewrap_join_full543_20260705.md`
- `00_current/glm4_dewrap_join_pilot100_20260705.md`
- `00_current/glm4_dewrap_join_pilot50_20260705.md`
- `00_current/glm4_dewrap_join_pilot5_20260705.md`
- `00_current/当前状态总结与新对话交接_20260703.md`
- `00_current/交给Pro模型_当前复刻情况与问题清单_20260703.md`
- `00_current/prompt_给Pro模型_原文复刻诊断_20260703.md`
- `00_current/Pro模型网页版回复存档与复核_20260703.md`
- `00_current/cot_v3b_len132_50firm_calibration_20260703.md`
- `00_current/cot_v3b_len132_100firm_calibration_20260703.md`
- `00_current/cot_v3b_len132_150firm_calibration_20260703.md`
- `00_current/cot_v3b_len132_200firm_calibration_20260703.md`
- `00_current/cot_v3b_len132_full543_calibration_20260704.md`
- `00_current/descriptive_comparison_vs_original_20260706.md`
- `00_current/管理世界式_主要变量描述性统计对比_20260706.md`
- `00_current/descriptive_comparison_vs_original_20260705.md`
- `00_current/glm4_dewrap_rechunk_trial_20260705.md`
- `00_current/glm4_tokenizer_chunk_audit_20260705.md`
- `00_current/table2_glm4_dewrap_full543_audit_20260706.md`
- `00_current/table2_existing_controls_patch_20260706.md`
- `00_current/table2_listing_year_segment_controls_20260706.md`
- `00_current/table2_len132_tight_audit_20260705.md`
- `00_current/表2降噪对照与543全样本scoregate_20260703.md`
- `00_current/表2窗口切分诊断_20260703.md`

## 目录结构

| 目录 | 内容 |
|---|---|
| `00_current/` | 当前状态、给外部模型的材料、最新表 2 降噪和窗口诊断 |
| `01_measurement_method/` | 冗余变量构造方法、长度单位、tailfix/scoregate 口径 |
| `02_measurement_gates/` | 25/50/100/150/200/250 家 gate 和扩样记录 |
| `03_table1_validation/` | Table 1、Panel C、描述统计和 chunk 层验证 |
| `04_table2_outcomes/` | 结果变量、外部数据、Table 2 经济后果复刻 |
| `05_handoff_archive/` | 旧 handoff、历史交接文档 |
| `06_external_review/` | Claude/老师复核材料 |
| `90_source_evidence/` | 原文官网、CNKI、附录证据快照 |
| `99_early_archive/` | 早期 prompt/QC/token_proxy 试跑归档 |

## 当前判断

当前 `cot_v3b + tailfix_bounded + scoregate` 已经完成 543 家企业层 X；新增 `dewrap_join + GLM-4 tokenizer + cot_v3b_len132_tight` 也已跑完 543 家全样本。固定新 chunking 与摘要 proxy 主口径后，Table 1 measurement gate 已通过；但 strict reproduction 仍是 `NO_PASS_YET`，因为 Table 2 经济后果和原文 controls/data 口径尚未复刻：

- 新全样本 `dewrap_join` 口径覆盖 543 家、8706 个 chunk；`Summary_len_proxy` mean=130.975、`Redundancy_chunk_proxy` mean=30.468、企业层 `Redundancy_proxy` mean=28.944，贴近原文 `132.678 / 32.176 / 29.074`；
- full543 Panel B/C/D 均按预期成立：Panel B Spearman rho=-0.428，低评分组冗余中位数 31.694 > 高评分组 27.274；Panel C cluster coef=0.132，p<0.001；Panel D innovation-rate cluster coef=-0.113，p<0.001；
- 摘要若也用 GLM-4 tokenizer 计数，`Summary_len` mean=158.072、`Redundancy_chunk` mean=25.383，因此 GLM-4 summary token 只保留为敏感性口径，主口径仍用摘要 proxy；
- 旧全 543 家长度校准结果 `Summary_len` mean=128.253、`Redundancy_chunk` mean=30.708、企业层 `Redundancy` mean=29.374，作为历史对照保留；
- 旧口径 Panel B 与 Panel D 仍成立，Table 1 Panel C 方向和量级已恢复；
- 已用 full543 新 X 重跑 Table 2 审计：`FInvention` 明显改善为 `coef=-0.0445, t=-1.88, p=0.0595`，但 `BHAR` 转为弱正，`FSales_Growth` 仍为正，整体结论仍是 `NO_PASS_YET`；
- 20260706 描述性对比显示当前 X/Y 本身没有明显崩：chunk 数 8706 vs 原文 8683，`lnN_tech` 10.966 vs 10.962，`Redundancy` 28.944 vs 29.074；三条 Y 的均值也接近或可解释，真正突出的描述性缺口在 controls；
- `dewrap_join + GLM tokenizer + 4000 token boundary split` 已切出 8706 个 chunk，几乎贴近原文 8683；`lnN_tech` mean=10.966，也贴近原文 10.962；
- 已在 `dewrap_join` chunk base 上完成 5 家 LLM pilot：旧摘要 proxy 口径下 `Summary_len` mean=134.526、`Redundancy_chunk` mean=29.232，贴近原文；但摘要若也用 GLM-4 tokenizer 计数，`Summary_len` mean=162.782、`Redundancy_chunk` mean=24.369，说明摘要长度单位仍需固定；
- 已在 `dewrap_join` chunk base 上完成 50 家、100 家、543 家逐级 gate；full543 结论为 `PASS_FULL543_MEASUREMENT_GATE_PROXY`；
- 主口径已固定为摘要 proxy；全样本 shard plan、merge report 与 diagnostics 均已落盘；
- 已用现有数据修复 `Underwriter` 与 `ScopeLen`：`Underwriter` 主口径为 `IPO_Ipobasic.Sponsfm` 上市当年 IPO 募资额 Top10，mean=0.632 vs 原文 0.574；`ScopeLen` 主口径为 `STK_LISTEDCOINFOANL.BusinessScope` 清洗后 UTF-8 字节长度取对数，mean=5.673 vs 原文 5.671；
- 已用新下载的 `PT_LCRDSPENDING` 构造 `RD_Staff`，主口径为 `listing_year - 1`、合并报表、`Source=IPO` 优先，mean=0.303 vs 原文 0.305，median=0.242 vs 原文 0.240；
- 已用新下载的 `FN_Fn048` 构造上市当年替代口径 `NumIndSeg / NumProdSeg`：主营业务收入分部优先、缺失时用营业收入分部补，均取 `ln(1 + count)`；`NumIndSeg` mean=0.881 vs 原文 0.854，`NumProdSeg` mean=1.503 vs 原文 1.475；
- 但 `NumIndSeg / NumProdSeg` 的 `listing_year - 1` strict pre-IPO 口径仍覆盖太低，不能做主回归；当前 segment controls 是上市当年年报附注替代口径；
- 加入上市当年 segment controls 后，`FInvention` 进一步贴近原文负向并卡在 5% 边界（`coef=-0.0461, p=0.0500`），但 `BHAR` 仍为弱正、`FSales_Growth` 仍为正，因此 Table 2 仍是 `NO_PASS_YET`；
- 下一步可以把 `dewrap_join + cot_v3b_len132_tight + Summary_len_proxy` 作为当前 X measurement 主口径进入外部审阅；但是否用于论文复刻仍要转向原文样本/Y/controls 口径审计，因为 Table 2 经济后果尚未复刻。
