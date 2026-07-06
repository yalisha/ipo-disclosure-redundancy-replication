# Table 2 新下载 IPO 数据 controls 重跑

日期：2026-07-06

## 这次更新了什么

- 用新下载 `IPO_Ipocsne` 的主承销商表重构 `Underwriter_ipo`：年度主承销商 IPO 募资额 Top10，co-main underwriters 采用 full-deal credit；weighted credit 只保留为敏感性。
- 用新下载 `IPO_Iponoem` 的招股时员工人数表重构 `RD_Staff_ipo`：专业结构中含“研发”的人数 / 总人数。
- 用新下载招股前资产负债表和利润表构造 pre-IPO 财务口径：`Size_ipo_pre`、`Lev_ipo_pre`、`ROA_ipo_pre`、`RD_Asset_ipo_pre`，主口径为 `latest annual <= listing_year - 1`。
- `NumIndSeg / NumProdSeg / ScopeLen` 仍沿用上一轮已补齐的上市当年分部附注和经营范围长度口径。

## 新下载表覆盖率

| table | label | rows | sample_firm_coverage | sample_firm_total | zip_file |
| --- | --- | --- | --- | --- | --- |
| IPO_Ipobasic | 招股及上市基本情况表 | 4558 | 543 | 543 | 招股及上市基本情况表173730614(仅供四川大学使用).zip |
| IPO_IpoBalance | 招股前资产负债表 | 35625 | 543 | 543 | 招股前资产负债表173719286(仅供四川大学使用).zip |
| IPO_IpoIncome | 招股前利润表 | 39848 | 543 | 543 | 招股前利润表173641455(仅供四川大学使用).zip |
| IPO_Ipocsne | 招股承销商表 | 6240 | 541 | 543 | 招股承销商表173827384(仅供四川大学使用).zip |
| IPO_Iponoem | 招股时公司职工人数情况表 | 57234 | 543 | 543 | 招股时公司职工人数情况表173739831(仅供四川大学使用).zip |

## 关键变量描述性对比

| variable | current_N | current_mean | current_median | original_variable | original_N | original_mean | original_median | mean_diff_current_minus_original |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lnN_tech | 543 | 10.966 | 10.979 | lnN_tech | 552 | 10.962 | 10.910 | 0.004 |
| Redundancy | 543 | 28.944 | 28.815 | Redundancy | 552 | 29.074 | 28.910 | -0.130 |
| FInvention | 531 | 2.325 | 2.197 | FInvention | 471 | 2.282 | 2.197 | 0.043 |
| BHAR | 541 | -0.062 | -0.204 | BHAR | 471 | -0.036 | -0.170 | -0.026 |
| FSales_Growth | 538 | 0.409 | 0.156 | FSales_Growth | 471 | 0.530 | 0.180 | -0.121 |
| FSales_Growth_ipo_pre_to_Lp1_w1p | 535 | 1.025 | 0.362 | FSales_Growth | 471 | 0.530 | 0.180 | 0.495 |
| Size | 541 | 20.779 | 20.569 | Size | 552 | 20.741 | 20.533 | 0.038 |
| Size_ipo_pre | 541 | 20.738 | 20.525 | Size | 552 | 20.741 | 20.533 | -0.003 |
| Lev | 541 | 0.360 | 0.337 | Lev | 552 | 0.356 | 0.334 | 0.004 |
| Lev_ipo_pre | 541 | 0.357 | 0.335 | Lev | 552 | 0.356 | 0.334 | 0.001 |
| ROA | 541 | 0.091 | 0.100 | ROA | 552 | 0.094 | 0.100 | -0.003 |
| ROA_ipo_pre | 541 | 0.090 | 0.097 | ROA | 552 | 0.094 | 0.100 | -0.004 |
| Underwriter | 538 | 0.632 | 1.000 | Underwriter | 552 | 0.574 | 1.000 | 0.058 |
| Underwriter_ipo | 539 | 0.649 | 1.000 | Underwriter | 552 | 0.574 | 1.000 | 0.075 |
| NumIndSeg | 529 | 0.881 | 0.693 | NumIndSeg | 552 | 0.854 | 0.693 | 0.027 |
| NumProdSeg | 533 | 1.503 | 1.609 | NumProdSeg | 552 | 1.475 | 1.609 | 0.028 |
| ScopeLen | 542 | 5.673 | 5.756 | ScopeLen | 552 | 5.671 | 5.762 | 0.002 |
| RD_Staff | 456 | 0.303 | 0.242 | RD_Staff | 552 | 0.305 | 0.240 | -0.002 |
| RD_Staff_ipo | 542 | 0.280 | 0.224 | RD_Staff | 552 | 0.305 | 0.240 | -0.025 |

## 新来源审计

| variable | source | N | mean | median | p25 | p75 | original_mean | original_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Underwriter_ipocsne_annual_grsprc_full | IPO_Ipocsne main underwriters; Top10 variants, full/weighted/count | 539 | 0.649 | 1.000 | 0.000 | 1.000 | 0.574 | 1.000 |
| Underwriter_ipocsne_annual_grsprc_weighted | IPO_Ipocsne main underwriters; Top10 variants, full/weighted/count | 539 | 0.718 | 1.000 | 0.000 | 1.000 | 0.574 | 1.000 |
| Underwriter_ipo | IPO_Ipocsne main underwriters; annual gross-proceeds Top10, full-deal credit | 539 | 0.649 | 1.000 | 0.000 | 1.000 | 0.574 | 1.000 |
| RD_Staff_ipo | IPO_Iponoem, Stattype=8 rows containing 研发 / Stattype=0 total staff | 542 | 0.280 | 0.224 | 0.140 | 0.387 | 0.305 | 0.240 |
| RD_Staff_ipo_exact_core | IPO_Iponoem, exact core R&D labels / total staff | 542 | 0.251 | 0.201 | 0.116 | 0.362 | 0.305 | 0.240 |
| Size_ipo_pre | IPO pre-listing annual StateTypeCode=A; latest <= listing_year-1 or strict lag1 | 541 | 20.738 | 20.525 | 20.073 | 21.174 | 20.741 | 20.533 |
| Lev_ipo_pre | IPO pre-listing annual StateTypeCode=A; latest <= listing_year-1 or strict lag1 | 541 | 0.357 | 0.335 | 0.212 | 0.473 | 0.356 | 0.334 |
| ROA_ipo_pre | IPO pre-listing annual StateTypeCode=A; latest <= listing_year-1 or strict lag1 | 541 | 0.090 | 0.097 | 0.058 | 0.152 | 0.094 | 0.100 |
| FSales_Growth_ipo_pre_to_Lp1_w1p | IPO pre-listing annual StateTypeCode=A; latest <= listing_year-1 or strict lag1 | 535 | 1.025 | 0.362 | 0.072 | 0.786 | 0.530 | 0.180 |
| ipo_pre_fin_year_available | latest common balance/income annual row <= listing_year-1 | 541 |  |  |  |  |  |  |
| ipo_lag1_fin_year_available | strict common balance/income annual row = listing_year-1 | 458 |  |  |  |  |  |  |

## Table 2 主回归重跑

| model | dep_var | N | coef | t_HC1 | p_HC1 | adj_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| segment_controls_existing | FInvention | 513 | -0.0461 | -1.9600 | 0.0500 | 0.3360 |
| segment_controls_existing | BHAR | 523 | 0.0042 | 0.3847 | 0.7004 | -0.0058 |
| segment_controls_existing | FSales_Growth | 523 | 0.0188 | 0.6914 | 0.4893 | 0.1340 |
| segment_ipocsne_underwriter | FInvention | 515 | -0.0454 | -1.9311 | 0.0535 | 0.3366 |
| segment_ipocsne_underwriter | BHAR | 525 | 0.0041 | 0.3776 | 0.7057 | -0.0067 |
| segment_ipocsne_underwriter | FSales_Growth | 525 | 0.0205 | 0.7434 | 0.4572 | 0.1389 |
| segment_ipocsne_underwriter_rd_staff | FInvention | 514 | -0.0450 | -1.9356 | 0.0529 | 0.3495 |
| segment_ipocsne_underwriter_rd_staff | BHAR | 524 | 0.0037 | 0.3374 | 0.7358 | -0.0053 |
| segment_ipocsne_underwriter_rd_staff | FSales_Growth | 524 | 0.0213 | 0.7849 | 0.4325 | 0.1420 |
| ipo_pre_fin_controls | FInvention | 515 | -0.0466 | -1.9865 | 0.0470 | 0.3293 |
| ipo_pre_fin_controls | BHAR | 525 | 0.0046 | 0.4234 | 0.6720 | -0.0055 |
| ipo_pre_fin_controls | FSales_Growth | 525 | 0.0260 | 0.9485 | 0.3429 | 0.1461 |
| ipo_pre_fin_controls_rd_staff | FInvention | 514 | -0.0465 | -2.0073 | 0.0447 | 0.3431 |
| ipo_pre_fin_controls_rd_staff | BHAR | 524 | 0.0042 | 0.3864 | 0.6992 | -0.0041 |
| ipo_pre_fin_controls_rd_staff | FSales_Growth | 524 | 0.0266 | 0.9766 | 0.3288 | 0.1485 |

## FSales_Growth 口径敏感性

| model | dep_var | N | coef | t_HC1 | p_HC1 | adj_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| segment_ipocsne_underwriter | FSales_Growth | 525 | 0.0205 | 0.7434 | 0.4572 | 0.1389 |
| segment_ipocsne_underwriter | FSales_Growth_ipo_pre_to_Lp1_w1p | 522 | 0.0514 | 1.0674 | 0.2858 | 0.1334 |
| segment_ipocsne_underwriter | FSales_Growth_ipo_lag1_to_Lp1_w1p | 443 | 0.0555 | 1.2435 | 0.2137 | 0.1537 |
| ipo_pre_fin_controls | FSales_Growth | 525 | 0.0260 | 0.9485 | 0.3429 | 0.1461 |
| ipo_pre_fin_controls | FSales_Growth_ipo_pre_to_Lp1_w1p | 522 | 0.0588 | 1.1975 | 0.2311 | 0.1479 |
| ipo_pre_fin_controls | FSales_Growth_ipo_lag1_to_Lp1_w1p | 443 | 0.0558 | 1.2478 | 0.2121 | 0.1537 |
| ipo_pre_fin_controls_rd_staff | FSales_Growth | 524 | 0.0266 | 0.9766 | 0.3288 | 0.1485 |
| ipo_pre_fin_controls_rd_staff | FSales_Growth_ipo_pre_to_Lp1_w1p | 521 | 0.0586 | 1.1943 | 0.2324 | 0.1460 |
| ipo_pre_fin_controls_rd_staff | FSales_Growth_ipo_lag1_to_Lp1_w1p | 442 | 0.0558 | 1.2483 | 0.2119 | 0.1528 |

## 2019-2022 子样本

| model | dep_var | N | coef | t_HC1 | p_HC1 | adj_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| segment_ipocsne_underwriter | FInvention | 450 | -0.0348 | -1.2760 | 0.2020 | 0.3313 |
| segment_ipocsne_underwriter | BHAR | 460 | 0.0019 | 0.1513 | 0.8797 | 0.0006 |
| segment_ipocsne_underwriter | FSales_Growth | 460 | 0.0306 | 0.9289 | 0.3529 | 0.1249 |
| segment_ipocsne_underwriter | FSales_Growth_ipo_pre_to_Lp1_w1p | 457 | 0.0701 | 1.1676 | 0.2430 | 0.1174 |
| ipo_pre_fin_controls | FInvention | 450 | -0.0364 | -1.3346 | 0.1820 | 0.3277 |
| ipo_pre_fin_controls | BHAR | 460 | 0.0023 | 0.1841 | 0.8539 | 0.0008 |
| ipo_pre_fin_controls | FSales_Growth | 460 | 0.0365 | 1.1061 | 0.2687 | 0.1329 |
| ipo_pre_fin_controls | FSales_Growth_ipo_pre_to_Lp1_w1p | 457 | 0.0793 | 1.2865 | 0.1983 | 0.1327 |
| ipo_pre_fin_controls_rd_staff | FInvention | 449 | -0.0374 | -1.3760 | 0.1688 | 0.3364 |
| ipo_pre_fin_controls_rd_staff | BHAR | 459 | 0.0015 | 0.1204 | 0.9042 | 0.0039 |
| ipo_pre_fin_controls_rd_staff | FSales_Growth | 459 | 0.0368 | 1.1207 | 0.2624 | 0.1360 |
| ipo_pre_fin_controls_rd_staff | FSales_Growth_ipo_pre_to_Lp1_w1p | 456 | 0.0791 | 1.2815 | 0.2000 | 0.1305 |

## 直接结论

- `Underwriter_ipo` 已回到原文量级附近，但仍偏高；这是因为“任一主承销商进年度 Top10 即记 1”的二元规则会天然偏宽。
- `RD_Staff_ipo` 覆盖接近全样本，均值略低于原文和上市公司研发投入表口径，但相关性应比旧缺失口径强。
- pre-IPO 财务 controls 里 `Size / Lev / ROA` 覆盖足够且量级贴近原文，可解释 `listing_year - 1` 在上市公司年报源中覆盖不足的问题；但 `RD_Asset_ipo_pre` 覆盖太低，不能替代机制表的研发资产变量。
- 主回归读法：
  - `segment_ipocsne_underwriter`：`FInvention` coef=-0.0454, t=-1.93, p=0.053, N=515；`BHAR` coef=0.0041, t=0.38, p=0.706, N=525；`FSales_Growth` coef=0.0205, t=0.74, p=0.457, N=525
  - `ipo_pre_fin_controls`：`FInvention` coef=-0.0466, t=-1.99, p=0.047, N=515；`BHAR` coef=0.0046, t=0.42, p=0.672, N=525；`FSales_Growth` coef=0.0260, t=0.95, p=0.343, N=525
- 判定：`NO_PASS_YET`。新 IPO controls 能改善数据制度一致性，但仍不能把 `BHAR` 和 `FSales_Growth` 拉回原文显著负向；下一步应优先审计 Y 的窗口、行业基准、缩尾和原文样本剔除，而不是继续改 X。

## 输出

- master：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_ipo_pre_controls_20260706/table2_ipo_pre_controls_master_20260706.csv`
- descriptives：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_ipo_pre_controls_20260706/table2_ipo_pre_controls_descriptives_20260706.csv`
- regressions：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_ipo_pre_controls_20260706/table2_ipo_pre_controls_regressions_20260706.csv`
- source audit：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_ipo_pre_controls_20260706/table2_ipo_pre_controls_source_audit_20260706.csv`
- underwriter top10：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_ipo_pre_controls_20260706/table2_ipo_pre_controls_underwriter_top10_20260706.csv`
- employee rows：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_ipo_pre_controls_20260706/table2_ipo_pre_controls_employee_rows_20260706.csv`
- pre-financial rows：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_ipo_pre_controls_20260706/table2_ipo_pre_controls_pre_fin_rows_20260706.csv`
