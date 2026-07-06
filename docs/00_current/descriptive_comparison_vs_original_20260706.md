# 当前 X/Y 描述性统计与原文对比

日期：2026-07-06

## 结论

- X 已经基本回到原文量级：chunk 数 8706 vs 原文 8683，`Summary_len` 130.975 vs 132.678，`Redundancy_chunk` 30.468 vs 32.176。
- 企业层 X 也贴近原文：`lnN_tech` 10.966 vs 10.962，`Redundancy` 28.944 vs 29.074。
- Y 的描述性统计没有明显崩：`FInvention` 均值 2.325 vs 原文 2.282；`BHAR` -0.062 vs -0.036；`FSales_Growth` 0.409 vs 0.530。
- 当前最明显的描述性缺口不在 X/Y 本身，而在 controls：`Underwriter` 0.009 vs 原文 0.574，`NumIndSeg / NumProdSeg / ScopeLen` 仍缺失。

## 关键差距摘要

| scope | variable | current_N | original_N | N_diff | current_mean | original_mean | mean_diff | mean_pct_diff_vs_original | current_median | original_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| table1_chunk | Chunk_num | 8706 | 8683 | 23 | 17.485 | 18.191 | -0.706 | -0.039 | 17.000 | 16.000 |
| table1_chunk | Text_len | 8706 | 8683 | 23 | 3793.173 | 3866.817 | -73.644 | -0.019 | 3967.000 | 3954.000 |
| table1_chunk | Summary_len | 8706 | 8683 | 23 | 130.975 | 132.678 | -1.703 | -0.013 | 132.000 | 130.000 |
| table1_chunk | Redundancy_chunk | 8706 | 8683 | 23 | 30.468 | 32.176 | -1.708 | -0.053 | 29.294 | 29.739 |
| table2_xy | lnN_tech | 543 | 552 | -9 | 10.966 | 10.962 | 0.004 | 0.000 | 10.979 | 10.910 |
| table2_xy | Redundancy | 543 | 552 | -9 | 28.944 | 29.074 | -0.130 | -0.004 | 28.815 | 28.910 |
| table2_xy | FInvention | 531 | 471 | 60 | 2.325 | 2.282 | 0.043 | 0.019 | 2.197 | 2.197 |
| table2_xy | BHAR | 541 | 471 | 70 | -0.062 | -0.036 | -0.026 | -0.716 | -0.204 | -0.170 |
| table2_xy | FSales_Growth | 538 | 471 | 67 | 0.409 | 0.530 | -0.121 | -0.228 | 0.156 | 0.180 |

## X：chunk 层 Table 1 Panel A

| variable | current_N | original_N | N_diff_current_minus_original | current_mean | original_mean | mean_diff_current_minus_original | mean_pct_diff_vs_original | current_std | original_std | current_median | original_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Chunk_num | 8706 | 8683 | 23 | 17.485 | 18.191 | -0.706 | -0.039 | 5.107 | 6.983 | 17.000 | 16.000 |
| Text_len | 8706 | 8683 | 23 | 3793.173 | 3866.817 | -73.644 | -0.019 | 556.384 | 343.868 | 3967.000 | 3954.000 |
| Summary_len | 8706 | 8683 | 23 | 130.975 | 132.678 | -1.703 | -0.013 | 28.800 | 39.683 | 132.000 | 130.000 |
| Redundancy_chunk | 8706 | 8683 | 23 | 30.468 | 32.176 | -1.708 | -0.053 | 9.423 | 11.730 | 29.294 | 29.739 |

读法：`Chunk_num`、`Text_len`、`Summary_len`、`Redundancy_chunk` 都已经和原文接近。这里的 `Summary_len` 和 `Redundancy_chunk` 使用当前主口径，也就是摘要 proxy 分母。

## X/Y：firm 层 Table 2 Panel A

| variable | current_available | current_N | original_N | N_diff_current_minus_original | current_mean | original_mean | mean_diff_current_minus_original | mean_pct_diff_vs_original | current_std | original_std | current_median | original_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lnN_tech | True | 543 | 552 | -9 | 10.966 | 10.962 | 0.004 | 0.000 | 0.329 | 0.350 | 10.979 | 10.910 |
| Redundancy | True | 543 | 552 | -9 | 28.944 | 29.074 | -0.130 | -0.004 | 2.174 | 2.630 | 28.815 | 28.910 |
| FInvention | True | 531 | 471 | 60 | 2.325 | 2.282 | 0.043 | 0.019 | 1.190 | 1.200 | 2.197 | 2.197 |
| BHAR | True | 541 | 471 | 70 | -0.062 | -0.036 | -0.026 | -0.716 | 0.489 | 0.514 | -0.204 | -0.170 |
| FSales_Growth | True | 538 | 471 | 67 | 0.409 | 0.530 | -0.121 | -0.228 | 1.673 | 1.522 | 0.156 | 0.180 |

读法：`lnN_tech` 与 `Redundancy` 已经比旧口径明显更贴近原文；三条 Y 的均值/中位数也不离谱。Table 2 回归没整体复刻，不能优先解释为 X/Y 描述性统计崩坏。

## 参考：关键 controls 描述性缺口

| variable | current_available | current_N | original_N | N_diff_current_minus_original | current_mean | original_mean | mean_diff_current_minus_original | mean_pct_diff_vs_original | current_std | original_std | current_median | original_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Price_Issue | False | 0 | 552 | -552 |  | 0.988 |  |  |  | 1.330 |  | 0.726 |
| Price_Day5 | False | 0 | 552 | -552 |  | 0.949 |  |  |  | 0.957 |  | 0.698 |
| RD_Staff | False | 0 | 552 | -552 |  | 0.305 |  |  |  | 0.194 |  | 0.240 |
| RD_Asset | True | 541 | 552 | -11 | 0.079 | 0.105 | -0.026 | -0.251 | 0.134 | 0.100 | 0.052 | 0.073 |
| Size | True | 541 | 552 | -11 | 20.779 | 20.741 | 0.038 | 0.002 | 0.999 | 0.990 | 20.569 | 20.533 |
| Lev | True | 541 | 552 | -11 | 0.360 | 0.356 | 0.004 | 0.011 | 0.185 | 0.183 | 0.337 | 0.334 |
| ROA | True | 541 | 552 | -11 | 0.091 | 0.094 | -0.003 | -0.037 | 0.189 | 0.145 | 0.100 | 0.100 |
| Offerfee | True | 542 | 552 | -10 | 18.327 | 18.325 | 0.002 | 0.000 | 0.494 | 0.483 | 18.266 | 18.270 |
| Underwriter | True | 543 | 552 | -9 | 0.009 | 0.574 | -0.565 | -0.984 | 0.096 | 0.495 | 0.000 | 1.000 |
| Age | True | 541 | 552 | -11 | 2.612 | 2.601 | 0.011 | 0.004 | 0.413 | 0.408 | 2.660 | 2.639 |
| NumIndSeg | False | 0 | 552 | -552 |  | 0.854 |  |  |  | 0.361 |  | 0.693 |
| NumProdSeg | False | 0 | 552 | -552 |  | 1.475 |  |  |  | 0.376 |  | 1.609 |
| ScopeLen | False | 0 | 552 | -552 |  | 5.671 |  |  |  | 0.854 |  | 5.762 |

读法：controls 里 `Underwriter` 是最大硬伤，三项原文 paper-only controls 仍不可用。这比 X/Y 描述性统计更像当前 Table 2 失败的直接数据缺口。

## 输出文件

- chunk X 对比：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/descriptive_comparison_vs_original_20260706/table1_panel_a_chunk_descriptives_vs_original_20260706.csv`
- firm X/Y 对比：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/descriptive_comparison_vs_original_20260706/table2_xy_descriptives_vs_original_20260706.csv`
- controls 对比：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/descriptive_comparison_vs_original_20260706/table2_controls_descriptives_vs_original_20260706.csv`
- gap summary：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/descriptive_comparison_vs_original_20260706/descriptive_gap_summary_20260706.csv`
