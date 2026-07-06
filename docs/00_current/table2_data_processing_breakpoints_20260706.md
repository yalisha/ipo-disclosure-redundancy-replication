# Table 2 数据处理断点审计

日期：2026-07-06

## 为什么做这个审计

当前 X 的量级已经贴近原文，`BHAR` 和 `FSales_Growth` 仍不复刻。这里不再调 X，而是把最可能的数据处理断点拆开：

- `BHAR`：252 交易日 vs 365 自然日；首日纳入/剔除；自建 STAR 市场基准 vs CSMAR 官方综合市场基准。
- `FSales_Growth`：`listing_year -> listing_year+1`、`listing_year+1 -> listing_year+2`、以及按上市月份切换完整会计年度。
- 样本：原文 Table 2 N=471；当前 2019-2022 outcome 样本约 474，但 controls 完整后主规格 N=459。

## 样本链条

| sample | step | N |
| --- | --- | --- |
| full_2019_2023 | universe | 543 |
| full_2019_2023 | Redundancy nonmissing | 543 |
| full_2019_2023 | BHAR nonmissing | 541 |
| full_2019_2023 | FSales_Growth nonmissing | 538 |
| full_2019_2023 | all controls nonmissing | 524 |
| full_2019_2023 | BHAR regression complete | 524 |
| full_2019_2023 | FSales regression complete | 524 |
| w2_2019_2022 | universe | 474 |
| w2_2019_2022 | Redundancy nonmissing | 474 |
| w2_2019_2022 | BHAR nonmissing | 474 |
| w2_2019_2022 | FSales_Growth nonmissing | 471 |
| w2_2019_2022 | all controls nonmissing | 459 |
| w2_2019_2022 | BHAR regression complete | 459 |
| w2_2019_2022 | FSales regression complete | 459 |

## BHAR 处理断点

2019-2022 描述统计最接近原文的候选：

| sample | variable | N | mean | std | p25 | median | p75 | distance_all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| w2_2019_2022 | BHAR_cal365_excl_star_exipo_ew | 474 | -0.058 | 0.523 | -0.388 | -0.212 | 0.118 | 0.120 |
| w2_2019_2022 | BHAR_td252_excl_star_exipo_ew | 474 | -0.058 | 0.522 | -0.402 | -0.219 | 0.093 | 0.164 |
| w2_2019_2022 | BHAR_current | 474 | -0.061 | 0.506 | -0.402 | -0.219 | 0.093 | 0.168 |
| w2_2019_2022 | BHAR_td252_excl_cnd_m53_tl | 474 | -0.105 | 0.549 | -0.432 | -0.239 | 0.102 | 0.280 |
| w2_2019_2022 | BHAR_td252_excl_cnd_m117_tl | 474 | -0.105 | 0.549 | -0.432 | -0.239 | 0.102 | 0.281 |
| w2_2019_2022 | BHAR_cal365_excl_cnd_m53_tl | 474 | -0.102 | 0.559 | -0.436 | -0.230 | 0.097 | 0.285 |
| w2_2019_2022 | BHAR_cal365_excl_cnd_m117_tl | 474 | -0.102 | 0.559 | -0.437 | -0.230 | 0.097 | 0.287 |
| w2_2019_2022 | BHAR_cal365_excl_cnd_m33_os | 474 | -0.115 | 0.559 | -0.442 | -0.252 | 0.083 | 0.342 |
| w2_2019_2022 | BHAR_td252_excl_cnd_m33_os | 474 | -0.120 | 0.547 | -0.460 | -0.256 | 0.078 | 0.362 |
| w2_2019_2022 | BHAR_cal365_excl_star_exipo_vw | 474 | -0.363 | 0.555 | -0.762 | -0.443 | -0.131 | 1.310 |

这些候选的主规格回归：

| sample | dep_var | N | coef | t_HC1 | p_HC1 | adj_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| w2_2019_2022 | BHAR | 459 | 0.0015 | 0.1204 | 0.9042 | 0.0039 |
| w2_2019_2022 | BHAR_td252_excl_star_exipo_ew | 459 | 0.0035 | 0.2685 | 0.7883 | 0.0037 |
| w2_2019_2022 | BHAR_td252_excl_cnd_m33_os | 459 | 0.0041 | 0.3030 | 0.7619 | 0.0483 |
| w2_2019_2022 | BHAR_td252_excl_cnd_m53_tl | 459 | 0.0045 | 0.3332 | 0.7390 | 0.0520 |
| w2_2019_2022 | BHAR_td252_excl_cnd_m117_tl | 459 | 0.0045 | 0.3321 | 0.7398 | 0.0524 |
| w2_2019_2022 | BHAR_cal365_excl_star_exipo_vw | 459 | 0.0054 | 0.4181 | 0.6759 | 0.1133 |
| w2_2019_2022 | BHAR_cal365_excl_star_exipo_ew | 459 | 0.0061 | 0.4674 | 0.6402 | 0.0025 |
| w2_2019_2022 | BHAR_cal365_excl_cnd_m33_os | 459 | 0.0046 | 0.3380 | 0.7353 | 0.0560 |
| w2_2019_2022 | BHAR_cal365_excl_cnd_m53_tl | 459 | 0.0052 | 0.3816 | 0.7028 | 0.0572 |
| w2_2019_2022 | BHAR_cal365_excl_cnd_m117_tl | 459 | 0.0052 | 0.3801 | 0.7039 | 0.0576 |

## FSales_Growth 处理断点

2019-2022 描述统计最接近原文的候选：

| sample | variable | N | mean | std | p25 | median | p75 | distance_all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| w2_2019_2022 | FSales_current | 471 | 0.408 | 1.601 | -0.034 | 0.165 | 0.404 | 0.361 |
| w2_2019_2022 | FSales_L_to_L1_w1p | 471 | 0.448 | 1.964 | -0.034 | 0.165 | 0.404 | 0.684 |
| w2_2019_2022 | FSales_month_cutoff_9_w1p | 471 | 0.317 | 0.912 | -0.031 | 0.165 | 0.404 | 0.979 |
| w2_2019_2022 | FSales_month_cutoff_6_w1p | 472 | 0.247 | 0.656 | -0.048 | 0.153 | 0.372 | 1.367 |
| w2_2019_2022 | FSales_month_cutoff_3_w1p | 471 | 0.231 | 0.651 | -0.068 | 0.147 | 0.364 | 1.421 |
| w2_2019_2022 | FSales_L1_to_L2_w1p | 470 | 0.179 | 0.453 | -0.076 | 0.132 | 0.340 | 1.720 |
| w2_2019_2022 | FSales_Lm1_to_L1_w1p | 74 | 37.826 | 224.737 | 0.038 | 0.350 | 0.857 | 261.061 |

这些候选的主规格回归：

| sample | dep_var | N | coef | t_HC1 | p_HC1 | adj_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| w2_2019_2022 | FSales_Growth | 459 | 0.0368 | 1.1207 | 0.2624 | 0.1360 |
| w2_2019_2022 | FSales_L_to_L1_w1p | 459 | 0.0428 | 1.0558 | 0.2911 | 0.1166 |
| w2_2019_2022 | FSales_L1_to_L2_w1p | 457 | -0.0094 | -0.8110 | 0.4174 | 0.0385 |
| w2_2019_2022 | FSales_Lm1_to_L1_w1p | 73 | -4.3355 | -0.4484 | 0.6539 | 0.0981 |
| w2_2019_2022 | FSales_month_cutoff_3_w1p | 458 | -0.0004 | -0.0260 | 0.9792 | 0.1505 |
| w2_2019_2022 | FSales_month_cutoff_6_w1p | 459 | 0.0083 | 0.6023 | 0.5470 | 0.1523 |
| w2_2019_2022 | FSales_month_cutoff_9_w1p | 459 | 0.0163 | 0.9244 | 0.3553 | 0.1784 |

## 判断

- `BHAR` 确实存在窗口/基准处理差异：365 自然日、剔除首日、STAR 等权基准比当前主口径更贴原文分布；但所有可观察日度窗口候选在主规格里仍为正且不显著。
- `FSales_Growth` 的简单窗口切换不能解释差距：当前 `L -> L+1` 反而最贴原文分布；`L+1 -> L+2` 或按上市月份切换会让系数弱负/接近 0，但分布明显远离原文。
- 下一步不建议再扩大网格盲试，应优先核原文作者实际使用的数据字段名、winsor 样本和 471 家样本剔除规则。

## 输出

- BHAR variants：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_data_processing_breakpoints_20260706/bhar_daily_window_processing_variants_20260706.csv`
- BHAR descriptives：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_data_processing_breakpoints_20260706/bhar_daily_window_processing_descriptives_20260706.csv`
- BHAR regressions：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_data_processing_breakpoints_20260706/bhar_daily_window_processing_regressions_20260706.csv`
- FSales variants：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_data_processing_breakpoints_20260706/fsales_month_cutoff_processing_variants_20260706.csv`
- FSales descriptives：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_data_processing_breakpoints_20260706/fsales_month_cutoff_processing_descriptives_20260706.csv`
- FSales regressions：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_data_processing_breakpoints_20260706/fsales_month_cutoff_processing_regressions_20260706.csv`
- sample audit：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_data_processing_breakpoints_20260706/table2_processing_sample_audit_20260706.csv`
