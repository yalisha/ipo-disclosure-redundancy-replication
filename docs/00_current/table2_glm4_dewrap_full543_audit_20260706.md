# Table 2 GLM4 dewrap_join full543 审计试跑

日期：2026-07-06

## 结论

- 判定：`NO_PASS_YET`。
- 这次使用的是 full543 新 X：`dewrap_join + GLM-4 tokenizer + cot_v3b_len132_tight + Summary_len_proxy`。
- 相比旧 len132_tight X，`Redundancy` 均值从约 29.374 降到 28.944，`lnN_tech` 从约 10.745 回到 10.966，已经贴近原文 Table 2 的 29.074 和 10.962。
- 但 Table 2 仍没有整体复刻原文：full 口径下 `FInvention` 已接近原文负向并达到 10% 边界显著，`BHAR` 转为弱正，`FSales_Growth` 仍为正；2019-2022 窗口也没有让三项同时显著为负。
- 原文完整控制变量仍缺：`NumIndSeg, NumProdSeg, ScopeLen`。当前只能称为 current-controls audit，不能称为 strict Table 2 replication。

## 输入

- base master：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_len132_tight_audit_20260705/table2_len132_tight_master_20260705.csv`
- full543 firm X：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm4_dewrap_join_full543_20260705/firm_metrics_glm4_cot_v3b_len132_tight_20260705.csv`
- 输出目录：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_glm4_dewrap_full543_audit_20260706`
- 标准误：HC1 robust，与既有 Table 2 审计脚本保持一致。

## X 替换前后

| metric | N | mean | median |
| --- | --- | --- | --- |
| Redundancy prior len132_tight | 543 | 29.374 | 29.217 |
| Redundancy full543 dewrap proxy | 543 | 28.944 | 28.815 |
| Redundancy full543 summary-token sensitivity | 543 | 24.025 | 23.967 |
| lnN_tech prior len132_tight | 543 | 10.745 | 10.750 |
| lnN_tech full543 GLM tokens | 543 | 10.966 | 10.979 |

## Panel A 对照

| variable | available | current_N | current_mean | original_N | original_mean | mean_diff_current_minus_original | current_median | original_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lnN_tech | True | 543 | 10.966 | 552 | 10.962 | 0.004 | 10.979 | 10.910 |
| Redundancy | True | 543 | 28.944 | 552 | 29.074 | -0.130 | 28.815 | 28.910 |
| FInvention | True | 531 | 2.325 | 471 | 2.282 | 0.043 | 2.197 | 2.197 |
| BHAR | True | 541 | -0.062 | 471 | -0.036 | -0.026 | -0.204 | -0.170 |
| FSales_Growth | True | 538 | 0.409 | 471 | 0.530 | -0.121 | 0.156 | 0.180 |
| Size | True | 541 | 20.779 | 552 | 20.741 | 0.038 | 20.569 | 20.533 |
| Lev | True | 541 | 0.360 | 552 | 0.356 | 0.004 | 0.337 | 0.334 |
| ROA | True | 541 | 0.091 | 552 | 0.094 | -0.003 | 0.100 | 0.100 |
| Offerfee | True | 542 | 18.327 | 552 | 18.325 | 0.002 | 18.266 | 18.270 |
| Underwriter | True | 543 | 0.009 | 552 | 0.574 | -0.565 | 0.000 | 1.000 |
| Age | True | 541 | 2.612 | 552 | 2.601 | 0.011 | 2.660 | 2.639 |
| NumIndSeg | False | 0 |  | 552 | 0.854 |  |  | 0.693 |
| NumProdSeg | False | 0 |  | 552 | 1.475 |  |  | 1.609 |
| ScopeLen | False | 0 |  | 552 | 5.671 |  |  | 5.762 |

## 样本 waterfall

| scope | step | N |
| --- | --- | --- |
| full_2019_2023 | 2019-2023: firms with len132_tight X | 543 |
| full_2019_2023 | with listing_year | 541 |
| full_2019_2023 | FInvention nonmissing | 531 |
| full_2019_2023 | BHAR nonmissing | 541 |
| full_2019_2023 | FSales_Growth nonmissing | 538 |
| full_2019_2023 | current controls complete | 541 |
| full_2019_2023 | all 3 Y + current controls complete | 528 |
| full_2019_2023 | all 3 Y + original paper controls complete | 0 |
| w2_2019_2022 | 2019-2022: firms with len132_tight X | 474 |
| w2_2019_2022 | with listing_year | 474 |
| w2_2019_2022 | FInvention nonmissing | 464 |
| w2_2019_2022 | BHAR nonmissing | 474 |
| w2_2019_2022 | FSales_Growth nonmissing | 471 |
| w2_2019_2022 | current controls complete | 474 |
| w2_2019_2022 | all 3 Y + current controls complete | 461 |
| w2_2019_2022 | all 3 Y + original paper controls complete | 0 |

## 当前 controls 主规格 vs 原文 Panel B

单元格使用 `Outcome ~ Redundancy + lnN_tech + Size + Lev + ROA + Offerfee + Underwriter + Age + Year FE + Industry FE`。

| sample | Y | N | coef | t | p | adj_r2 | paper_coef | paper_t | paper_N | sign_match |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_by_y_available | FInvention | 531 | -0.0445 | -1.8843 | 0.0595 | 0.3336 | -0.0316 | -1.7200 | 471 | True |
| full_by_y_available | BHAR | 541 | 0.0041 | 0.3864 | 0.6992 | -0.0175 | -0.0188 | -2.1400 | 471 | False |
| full_by_y_available | FSales_Growth | 538 | 0.0216 | 0.5884 | 0.5562 | 0.2036 | -0.0373 | -2.0200 | 471 | False |
| common_3y_current_controls | FInvention | 528 | -0.0443 | -1.8814 | 0.0599 | 0.3333 | -0.0316 | -1.7200 | 471 | True |
| common_3y_current_controls | BHAR | 528 | 0.0028 | 0.2623 | 0.7931 | -0.0164 | -0.0188 | -2.1400 | 471 | False |
| common_3y_current_controls | FSales_Growth | 528 | 0.0067 | 0.1979 | 0.8431 | 0.2072 | -0.0373 | -2.0200 | 471 | False |
| w2_2019_2022_by_y_available | FInvention | 464 | -0.0387 | -1.4260 | 0.1539 | 0.3246 | -0.0316 | -1.7200 | 471 | True |
| w2_2019_2022_by_y_available | BHAR | 474 | 0.0025 | 0.2109 | 0.8329 | -0.0061 | -0.0188 | -2.1400 | 471 | False |
| w2_2019_2022_by_y_available | FSales_Growth | 471 | 0.0200 | 0.4656 | 0.6415 | 0.1692 | -0.0373 | -2.0200 | 471 | False |
| w2_2019_2022_common_3y_current_controls | FInvention | 461 | -0.0385 | -1.4235 | 0.1546 | 0.3234 | -0.0316 | -1.7200 | 471 | True |
| w2_2019_2022_common_3y_current_controls | BHAR | 461 | 0.0010 | 0.0848 | 0.9324 | -0.0045 | -0.0188 | -2.1400 | 471 | False |
| w2_2019_2022_common_3y_current_controls | FSales_Growth | 461 | 0.0022 | 0.0568 | 0.9547 | 0.1714 | -0.0373 | -2.0200 | 471 | False |

## GLM-4 摘要 token 分母敏感性

| sample | dep_var | N | coef | t_HC1 | p_HC1 | adj_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| full_by_y_available | FInvention | 531 | -0.0234 | -0.9152 | 0.3601 | 0.3293 |
| full_by_y_available | BHAR | 541 | 0.0073 | 0.5838 | 0.5593 | -0.0171 |
| full_by_y_available | FSales_Growth | 538 | -0.0042 | -0.1229 | 0.9022 | 0.2029 |
| w2_2019_2022_by_y_available | FInvention | 464 | -0.0158 | -0.5317 | 0.5949 | 0.3213 |
| w2_2019_2022_by_y_available | BHAR | 474 | 0.0035 | 0.2487 | 0.8036 | -0.0060 |
| w2_2019_2022_by_y_available | FSales_Growth | 471 | -0.0153 | -0.3833 | 0.7015 | 0.1689 |

## 缺失原文控制变量

| variable | available_in_master | nonmissing_N | original_mean | note |
| --- | --- | --- | --- | --- |
| NumIndSeg | False | 0 | 0.854 | required by original Table 2 controls |
| NumProdSeg | False | 0 | 1.475 | required by original Table 2 controls |
| ScopeLen | False | 0 | 5.671 | required by original Table 2 controls |

## 直接读法

- X measurement 的 Table 1 问题基本已解：`Redundancy` 和 `lnN_tech` 都贴近原文。
- 只替换成 full543 新 X 后，`FInvention` 这一列明显改善，但 `BHAR` 和 `FSales_Growth` 没有恢复原文负向；这说明当前主要差距已经转向 Y/controls/sample 口径。
- `Underwriter` 仍是最大硬伤：当前均值约 0.009，原文 0.574，不能视为同一变量。
- `NumIndSeg / NumProdSeg / ScopeLen` 仍缺失，严格原文控制变量组无法运行。

## 输出文件

- master copy：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_glm4_dewrap_full543_audit_20260706/table2_glm4_dewrap_full543_master_20260706.csv`
- Panel A：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_glm4_dewrap_full543_audit_20260706/panel_a_descriptives_vs_original_20260706.csv`
- regressions：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_glm4_dewrap_full543_audit_20260706/table2_glm4_dewrap_full543_regressions_20260706.csv`
- waterfall：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_glm4_dewrap_full543_audit_20260706/table2_glm4_dewrap_full543_sample_waterfall_20260706.csv`
- missing controls：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_glm4_dewrap_full543_audit_20260706/table2_glm4_dewrap_full543_missing_paper_controls_20260706.csv`
