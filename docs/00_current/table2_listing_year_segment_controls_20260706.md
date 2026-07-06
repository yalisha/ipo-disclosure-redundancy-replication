# Table 2 listing_year segment controls 试跑

日期：2026-07-06

## 这次做了什么

- `Underwriter` 与 `ScopeLen` 继承 existing controls patch 口径。
- `RD_Staff` 使用 `PT_LCRDSPENDING`，`listing_year - 1`，合并报表，`Source=IPO` 优先，`RDPersonRatio / 100`。
- `NumIndSeg / NumProdSeg` 使用 `FN_Fn048` 上市当年年报附注：`fn04814=1` 主营业务收入优先；若公司当年缺主营业务收入分部，则用 `fn04814=3` 营业收入补；`Fn04801=1` 为业务/行业分部，`Fn04801=3` 为产品分部，均取 `ln(1 + count)`。

## 描述统计对照

| variable | available | current_N | current_mean | original_N | original_mean | mean_diff_current_minus_original | current_median | original_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lnN_tech | True | 543 | 10.966 | 552 | 10.962 | 0.004 | 10.979 | 10.910 |
| Redundancy | True | 543 | 28.944 | 552 | 29.074 | -0.130 | 28.815 | 28.910 |
| FInvention | True | 531 | 2.325 | 471 | 2.282 | 0.043 | 2.197 | 2.197 |
| BHAR | True | 541 | -0.062 | 471 | -0.036 | -0.026 | -0.204 | -0.170 |
| FSales_Growth | True | 538 | 0.409 | 471 | 0.530 | -0.121 | 0.156 | 0.180 |
| RD_Staff | True | 456 | 0.303 | 552 | 0.305 | -0.002 | 0.242 | 0.240 |
| Size | True | 541 | 20.779 | 552 | 20.741 | 0.038 | 20.569 | 20.533 |
| Lev | True | 541 | 0.360 | 552 | 0.356 | 0.004 | 0.337 | 0.334 |
| ROA | True | 541 | 0.091 | 552 | 0.094 | -0.003 | 0.100 | 0.100 |
| Offerfee | True | 542 | 18.327 | 552 | 18.325 | 0.002 | 18.266 | 18.270 |
| Underwriter | True | 538 | 0.632 | 552 | 0.574 | 0.058 | 1.000 | 1.000 |
| Age | True | 541 | 2.612 | 552 | 2.601 | 0.011 | 2.660 | 2.639 |
| NumIndSeg | True | 529 | 0.881 | 552 | 0.854 | 0.027 | 0.693 | 0.693 |
| NumProdSeg | True | 533 | 1.503 | 552 | 1.475 | 0.028 | 1.609 | 1.609 |
| ScopeLen | True | 542 | 5.673 | 552 | 5.671 | 0.002 | 5.756 | 5.762 |

## 新变量来源审计

| variable | source | N | mean | median | p25 | p75 | original_mean | original_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NumIndSeg | main_else_operating_ln1p | 529.000 | 0.881 | 0.693 | 0.693 | 1.099 | 0.854 | 0.693 |
| NumIndSeg | main_only_ln1p | 436.000 | 0.888 | 0.693 | 0.693 | 1.099 | 0.854 | 0.693 |
| NumProdSeg | main_else_operating_ln1p | 533.000 | 1.503 | 1.609 | 1.386 | 1.792 | 1.475 | 1.609 |
| NumProdSeg | main_only_ln1p | 436.000 | 1.518 | 1.609 | 1.386 | 1.792 | 1.475 | 1.609 |
| segment_firms_any | FN_Fn048 listing_year rows after filters | 540.000 |  |  |  |  |  |  |
| RD_Staff | PT_LCRDSPENDING listing_year-1, StateTypeCode=1, Source=IPO preferred | 456.000 | 0.303 | 0.242 | 0.157 | 0.408 | 0.305 | 0.240 |

## 主回归结果

| model | dep_var | N | coef | t_HC1 | p_HC1 | adj_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| controls_fe_repaired_underwriter_scope | FInvention | 527 | -0.0447 | -1.8859 | 0.0593 | 0.3352 |
| controls_fe_listing_year_segments | FInvention | 513 | -0.0461 | -1.9600 | 0.0500 | 0.3360 |
| controls_fe_listing_year_segments_rd_staff | FInvention | 430 | -0.0468 | -1.8556 | 0.0635 | 0.3675 |
| controls_fe_repaired_underwriter_scope | BHAR | 537 | 0.0045 | 0.4185 | 0.6756 | -0.0024 |
| controls_fe_listing_year_segments | BHAR | 523 | 0.0042 | 0.3847 | 0.7004 | -0.0058 |
| controls_fe_listing_year_segments_rd_staff | BHAR | 438 | 0.0006 | 0.0496 | 0.9605 | 0.0116 |
| controls_fe_repaired_underwriter_scope | FSales_Growth | 534 | 0.0192 | 0.5266 | 0.5985 | 0.2049 |
| controls_fe_listing_year_segments | FSales_Growth | 523 | 0.0188 | 0.6914 | 0.4893 | 0.1340 |
| controls_fe_listing_year_segments_rd_staff | FSales_Growth | 438 | -0.0011 | -0.0415 | 0.9669 | 0.1351 |

## 共同样本结果

| sample | model | dep_var | N | coef | t_HC1 | p_HC1 | adj_r2 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| common_3y_segment_controls | controls_fe_listing_year_segments | FInvention | 513 | -0.0461 | -1.9600 | 0.0500 | 0.3360 |
| common_3y_segment_controls | controls_fe_listing_year_segments_rd_staff | FInvention | 430 | -0.0468 | -1.8556 | 0.0635 | 0.3675 |
| common_3y_segment_controls | controls_fe_listing_year_segments | BHAR | 513 | 0.0031 | 0.2858 | 0.7751 | -0.0070 |
| common_3y_segment_controls | controls_fe_listing_year_segments_rd_staff | BHAR | 430 | -0.0014 | -0.1209 | 0.9038 | 0.0126 |
| common_3y_segment_controls | controls_fe_listing_year_segments | FSales_Growth | 513 | 0.0056 | 0.2405 | 0.8099 | 0.1274 |
| common_3y_segment_controls | controls_fe_listing_year_segments_rd_staff | FSales_Growth | 430 | -0.0178 | -0.8989 | 0.3687 | 0.1329 |
| common_3y_segment_controls_rd_staff | controls_fe_listing_year_segments | FInvention | 430 | -0.0525 | -2.0004 | 0.0455 | 0.3388 |
| common_3y_segment_controls_rd_staff | controls_fe_listing_year_segments_rd_staff | FInvention | 430 | -0.0468 | -1.8556 | 0.0635 | 0.3675 |
| common_3y_segment_controls_rd_staff | controls_fe_listing_year_segments | BHAR | 430 | -0.0017 | -0.1518 | 0.8793 | 0.0144 |
| common_3y_segment_controls_rd_staff | controls_fe_listing_year_segments_rd_staff | BHAR | 430 | -0.0014 | -0.1209 | 0.9038 | 0.0126 |
| common_3y_segment_controls_rd_staff | controls_fe_listing_year_segments | FSales_Growth | 430 | -0.0203 | -0.9501 | 0.3421 | 0.1262 |
| common_3y_segment_controls_rd_staff | controls_fe_listing_year_segments_rd_staff | FSales_Growth | 430 | -0.0178 | -0.8989 | 0.3687 | 0.1329 |

## 直接读法

- Segment controls 的覆盖率和量级已经可用：`NumIndSeg` N=529、`NumProdSeg` N=533，均值接近原文，但这是上市当年年报附注替代口径，不是 strict pre-IPO 口径。
- `RD_Staff` 几乎贴住原文描述统计，但不属于原文 Table 2 的核心 P0 controls；加不加它主要作为敏感性。
- 加入上市当年 segment controls 后，主结果为：
  - `FInvention`：coef=-0.0461, t=-1.96, p=0.050, N=513
  - `BHAR`：coef=0.0042, t=0.38, p=0.700, N=523
  - `FSales_Growth`：coef=0.0188, t=0.69, p=0.489, N=523
- 若再加入 `RD_Staff`，结果为：
  - `FInvention`：coef=-0.0468, t=-1.86, p=0.064, N=430
  - `BHAR`：coef=0.0006, t=0.05, p=0.960, N=438
  - `FSales_Growth`：coef=-0.0011, t=-0.04, p=0.967, N=438
- 结论：这一步补齐了可观测 controls，但 Table 2 仍未 strict pass；`FInvention` 卡在 5%-10% 边界，`BHAR` 和 `FSales_Growth` 仍没有恢复原文显著负向。

## 输出

- master：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_listing_year_segment_controls_20260706/table2_listing_year_segment_controls_master_20260706.csv`
- descriptives：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_listing_year_segment_controls_20260706/table2_listing_year_segment_controls_descriptives_20260706.csv`
- regressions：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_listing_year_segment_controls_20260706/table2_listing_year_segment_controls_regressions_20260706.csv`
- source audit：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_listing_year_segment_controls_20260706/table2_listing_year_segment_controls_source_audit_20260706.csv`
- segment counts：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_listing_year_segment_controls_20260706/table2_listing_year_segment_counts_20260706.csv`
- RD rows：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_listing_year_segment_controls_20260706/table2_rd_staff_rows_20260706.csv`
