# BHAR 与 FSales_Growth 原文口径核对

日期：2026-07-06

## 原文可核对定义

- `BHAR`：科创板企业上市一年内买入并持有股票的超额收益；超额收益等于年度个股收益率减去分市场的综合收益率。
- `FSales_Growth`：科创板企业上市一年后的营业收入增长率。
- 控制变量使用上市前一年 `Size / Lev / ROA`，并控制 `Offerfee / Underwriter / Age / NumIndSeg / NumProdSeg / ScopeLen / lnN_tech`、年份固定效应和行业固定效应。

## 我们当前代码的偏差

- 当前 `BHAR` 来自 `scripts/construct_outcome_variables_20260629.py`：用日个股回报 `Dretwd` 复合 252 个交易日，再减去我们自己用科创板股票池算出来的 STAR value-weighted benchmark。这不是原文写的 CSMAR `分市场综合收益率` 口径。
- 当前 `FSales_Growth` 来自上市公司年报利润表：`listing_year -> listing_year+1` 的营业收入增长。原文只写“上市一年后营业收入增长率”，没有说明分母是上市当年、上市前一年，还是招股前最新年度。

## BHAR 描述统计核对

当前变量：

| sample | variable | N | mean | std | p25 | median | p75 | distance_all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_2019_2023 | BHAR_current | 541 | -0.062 | 0.489 | -0.387 | -0.204 | 0.073 | 0.176 |
| w2_2019_2022 | BHAR_current | 474 | -0.061 | 0.506 | -0.402 | -0.219 | 0.093 | 0.168 |

最接近原文的 w2 候选：

| sample | variable | N | mean | std | p25 | median | p75 | distance_all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| w2_2019_2022 | BHAR_current | 474 | -0.061 | 0.506 | -0.402 | -0.219 | 0.093 | 0.168 |
| w2_2019_2022 | BHARwk_skip_first_first52_Wretwd_Cmdeq | 474 | -0.331 | 0.544 | -0.409 | -0.171 | -0.062 | 0.574 |
| w2_2019_2022 | BHARwk_skip_first_first52_Wretwd_Mdeq | 474 | -0.281 | 0.460 | -0.339 | -0.142 | -0.049 | 0.583 |
| w2_2019_2022 | BHARwk_within365_Wretwd_Mdos | 215 | -0.346 | 0.528 | -0.388 | -0.197 | -0.067 | 0.583 |
| w2_2019_2022 | BHARwk_within365_Wretwd_Mdtl | 215 | -0.346 | 0.534 | -0.379 | -0.203 | -0.069 | 0.600 |
| w2_2019_2022 | BHARwk_first52_Wretwd_Mdeq | 474 | -0.297 | 0.474 | -0.329 | -0.151 | -0.066 | 0.604 |
| w2_2019_2022 | BHARwk_skip_first_first52_Wretwd_Cmdtl | 474 | -0.346 | 0.515 | -0.426 | -0.190 | -0.083 | 0.616 |
| w2_2019_2022 | BHARwk_first52_Wretwd_Mdos | 474 | -0.297 | 0.449 | -0.332 | -0.157 | -0.070 | 0.624 |
| w2_2019_2022 | BHARwk_skip_first_first52_Wretwd_Mdos | 474 | -0.274 | 0.419 | -0.328 | -0.149 | -0.058 | 0.630 |
| w2_2019_2022 | BHARwk_first52_Wretwd_Mdtl | 474 | -0.296 | 0.446 | -0.326 | -0.157 | -0.070 | 0.631 |

full 样本候选：

| sample | variable | N | mean | std | p25 | median | p75 | distance_all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_2019_2023 | BHAR_current | 541 | -0.062 | 0.489 | -0.387 | -0.204 | 0.073 | 0.176 |
| full_2019_2023 | BHARwk_skip_first_first52_Wretwd_Cmdeq | 541 | -0.315 | 0.527 | -0.388 | -0.155 | -0.058 | 0.529 |
| full_2019_2023 | BHARwk_within365_Wretwd_Mdos | 239 | -0.333 | 0.512 | -0.370 | -0.184 | -0.068 | 0.558 |
| full_2019_2023 | BHARwk_within365_Wretwd_Mdtl | 239 | -0.332 | 0.518 | -0.364 | -0.178 | -0.069 | 0.560 |
| full_2019_2023 | BHARwk_skip_first_first52_Wretwd_Cmdtl | 541 | -0.335 | 0.501 | -0.397 | -0.183 | -0.083 | 0.581 |
| full_2019_2023 | BHARwk_first52_Wretwd_Cmdeq | 541 | -0.333 | 0.553 | -0.378 | -0.163 | -0.077 | 0.589 |
| full_2019_2023 | BHARwk_skip_first_first52_Wretwd_Cmdos | 541 | -0.345 | 0.515 | -0.409 | -0.188 | -0.085 | 0.599 |
| full_2019_2023 | BHARwk_skip_first_first52_Wretwd_Mdeq | 541 | -0.269 | 0.450 | -0.316 | -0.130 | -0.049 | 0.617 |

## BHAR 回归方向核对

| sample | dep_var | N | coef | t_HC1 | p_HC1 | adj_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| full_2019_2023 | BHAR | 525 | 0.0046 | 0.4234 | 0.6720 | -0.0055 |
| full_2019_2023 | BHAR_current | 525 | 0.0046 | 0.4234 | 0.6720 | -0.0055 |
| full_2019_2023 | BHARwk_skip_first_first52_Wretwd_Cmdeq | 525 | 0.0033 | 0.2767 | 0.7820 | -0.0035 |
| full_2019_2023 | BHARwk_skip_first_first52_Wretwd_Mdeq | 525 | 0.0093 | 0.8716 | 0.3834 | -0.0109 |
| full_2019_2023 | BHARwk_within365_Wretwd_Mdos | 234 | -0.0027 | -0.1334 | 0.8939 | -0.0647 |
| full_2019_2023 | BHARwk_within365_Wretwd_Mdtl | 234 | -0.0035 | -0.1716 | 0.8637 | -0.0650 |
| w2_2019_2022 | BHAR | 460 | 0.0023 | 0.1841 | 0.8539 | 0.0008 |
| w2_2019_2022 | BHAR_current | 460 | 0.0023 | 0.1841 | 0.8539 | 0.0008 |
| w2_2019_2022 | BHARwk_skip_first_first52_Wretwd_Cmdeq | 460 | 0.0060 | 0.4580 | 0.6470 | -0.0117 |
| w2_2019_2022 | BHARwk_skip_first_first52_Wretwd_Mdeq | 460 | 0.0138 | 1.2072 | 0.2273 | -0.0196 |
| w2_2019_2022 | BHARwk_within365_Wretwd_Mdos | 211 | -0.0066 | -0.2734 | 0.7845 | -0.0893 |
| w2_2019_2022 | BHARwk_within365_Wretwd_Mdtl | 211 | -0.0075 | -0.3112 | 0.7557 | -0.0911 |

## FSales_Growth 窗口核对

| sample | window | window_label | variable | N_x | mean | std | p25 | median | p75 | coef | t_HC1 | p_HC1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_2019_2023 | L_to_L1_total | listing_year -> listing_year+1, current logic | FSales_combo_L_to_L1_total_w1p | 538 | 0.409 | 1.673 | -0.048 | 0.156 | 0.386 | 0.019 | 0.691 | 0.489 |
| w2_2019_2022 | L_to_L1_total | listing_year -> listing_year+1, current logic | FSales_combo_L_to_L1_total_w1p | 471 | 0.408 | 1.601 | -0.034 | 0.165 | 0.404 | 0.030 | 0.914 | 0.361 |
| full_2019_2023 | L1_to_L2_total | first complete listed fiscal year -> next fiscal year | FSales_combo_L1_to_L2_total_w1p | 537 | 0.188 | 0.459 | -0.057 | 0.144 | 0.350 | -0.009 | -0.864 | 0.388 |
| w2_2019_2022 | L1_to_L2_total | first complete listed fiscal year -> next fiscal year | FSales_combo_L1_to_L2_total_w1p | 470 | 0.178 | 0.450 | -0.076 | 0.132 | 0.340 | -0.012 | -1.047 | 0.295 |
| full_2019_2023 | Lm1_to_L1_total | listing_year-1 -> listing_year+1, two-year total growth | FSales_combo_Lm1_to_L1_total_w1p | 82 | 34.031 | 212.061 | 0.013 | 0.350 | 0.857 | -8.550 | -0.805 | 0.421 |
| w2_2019_2022 | Lm1_to_L1_total | listing_year-1 -> listing_year+1, two-year total growth | FSales_combo_Lm1_to_L1_total_w1p | 74 | 37.581 | 223.084 | 0.038 | 0.350 | 0.857 | -9.320 | -0.807 | 0.420 |
| full_2019_2023 | Lm1_to_L1_cagr | listing_year-1 -> listing_year+1, annualized CAGR | FSales_combo_Lm1_to_L1_cagr_w1p | 82 | 1.130 | 5.488 | 0.006 | 0.162 | 0.363 | -0.181 | -0.696 | 0.487 |
| w2_2019_2022 | Lm1_to_L1_cagr | listing_year-1 -> listing_year+1, annualized CAGR | FSales_combo_Lm1_to_L1_cagr_w1p | 74 | 1.214 | 5.772 | 0.019 | 0.162 | 0.363 | -0.203 | -0.710 | 0.478 |

## 结论

- `BHAR` 当前实现不是逐字原文口径：原文写的是年度个股收益率减去分市场综合收益率；我们当前用日收益自建 STAR value-weighted benchmark，并且在 market benchmark 中剔除了各股票 IPO 首日。
- 但现有 CSMAR 周度市场调整表不是直接答案：它重构出的 BHAR 分布明显比当前变量更远离原文，而且 Redundancy 系数仍不恢复显著负向。因此现在只能判定为“需定位原文实际市场收益字段”，不能简单判定当前 BHAR 全错。
- `FSales_Growth` 的最大疑点不是字段，而是窗口。`listing_year -> listing_year+1` 描述统计偏低；`listing_year-1 -> listing_year+1` 均值更高但回归仍正；现有证据支持继续核原文收入窗口和样本，而不是继续调 X。

## 输出

- BHAR weekly variants：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/y_bhar_fsales_definition_audit_20260706/bhar_csmar_weekly_adjusted_variants_20260706.csv`
- BHAR descriptives：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/y_bhar_fsales_definition_audit_20260706/bhar_csmar_weekly_adjusted_descriptives_20260706.csv`
- BHAR regressions：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/y_bhar_fsales_definition_audit_20260706/bhar_csmar_weekly_adjusted_regressions_20260706.csv`
- FSales key candidates：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/y_bhar_fsales_definition_audit_20260706/fsales_growth_key_candidates_20260706.csv`
