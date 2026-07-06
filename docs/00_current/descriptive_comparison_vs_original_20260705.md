# 与原文描述性统计对比

日期：2026-07-05

## 结论

- X 的核心量级已经接近原文：企业层 `Redundancy` 当前均值 29.374，原文 29.074；chunk 层 `Summary_len` 当前 128.253，原文 132.678；chunk 层 `Redundancy_chunk` 当前 30.708，原文 32.176。
- 样本和切块数量仍不同：原文 552 家、8683 个 chunk；当前 543 家、7028 个 chunk。chunk 层加权的 `Chunk_num` 当前 14.054，原文 18.191，说明切块/文本范围仍不是完全同口径。
- `lnN_tech` 当前均值 10.745，原文 10.962，低约 0.217；这比 Redundancy 的差距更值得查，指向原始文本长度单位或章节抽取边界。
- 三个 outcome 的均值没有严重崩：`FInvention` 接近原文，`BHAR` 略更低，`FSales_Growth` 当前 0.409 低于原文 0.530。
- controls 的差距最大：`Underwriter` 当前 0.009，原文 0.574；`NumIndSeg`、`NumProdSeg`、`ScopeLen` 当前缺失。因此 Table 2 复刻失败不能优先归咎于 X。

## 关键差距摘要

| scope | variable | current_N | original_N | N_diff | current_mean | original_mean | mean_diff | mean_pct_diff_vs_original | current_median | original_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| table1_chunk | Text_len | 7028 | 8683 | -1655 | 3758.194 | 3866.817 | -108.623 | -0.028 | 3940.000 | 3954.000 |
| table1_chunk | Summary_len | 7028 | 8683 | -1655 | 128.253 | 132.678 | -4.425 | -0.033 | 128.000 | 130.000 |
| table1_chunk | Redundancy_chunk | 7028 | 8683 | -1655 | 30.708 | 32.176 | -1.468 | -0.046 | 29.955 | 29.739 |
| table2_firm | lnN_tech | 543 | 552 | -9 | 10.745 | 10.962 | -0.217 | -0.020 | 10.750 | 10.910 |
| table2_firm | Redundancy | 543 | 552 | -9 | 29.374 | 29.074 | 0.300 | 0.010 | 29.217 | 28.910 |
| table2_firm | FInvention | 531 | 471 | 60 | 2.325 | 2.282 | 0.043 | 0.019 | 2.197 | 2.197 |
| table2_firm | BHAR | 541 | 471 | 70 | -0.062 | -0.036 | -0.026 | -0.716 | -0.204 | -0.170 |
| table2_firm | FSales_Growth | 538 | 471 | 67 | 0.409 | 0.530 | -0.121 | -0.228 | 0.156 | 0.180 |
| table2_firm | Underwriter | 543 | 552 | -9 | 0.009 | 0.574 | -0.565 | -0.984 | 0.000 | 1.000 |

## Table 1 Panel A：chunk 层描述性统计

| variable | current_N | original_N | N_diff_current_minus_original | current_mean | original_mean | mean_diff_current_minus_original | mean_pct_diff_vs_original | current_std | original_std | current_median | original_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Chunk_num | 7028 | 8683 | -1655 | 14.054 | 18.191 | -4.137 | -0.227 | 3.985 | 6.983 | 14.000 | 16.000 |
| Text_len | 7028 | 8683 | -1655 | 3758.194 | 3866.817 | -108.623 | -0.028 | 588.750 | 343.868 | 3940.000 | 3954.000 |
| Summary_len | 7028 | 8683 | -1655 | 128.253 | 132.678 | -4.425 | -0.033 | 26.957 | 39.683 | 128.000 | 130.000 |
| Redundancy_chunk | 7028 | 8683 | -1655 | 30.708 | 32.176 | -1.468 | -0.046 | 9.221 | 11.730 | 29.955 | 29.739 |

读法：`Summary_len` 与 `Redundancy_chunk` 已贴近原文，但 `Chunk_num` 明显偏低；这意味着我们的摘要长度校准成功了，剩下的 X 差异更多来自样本/章节抽取/切块边界，而不是 prompt 长度本身。

## Table 2 Panel A：firm 层描述性统计

| variable | current_available | current_N | original_N | N_diff_current_minus_original | current_mean | original_mean | mean_diff_current_minus_original | mean_pct_diff_vs_original | current_median | original_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lnN_tech | True | 543 | 552 | -9 | 10.745 | 10.962 | -0.217 | -0.020 | 10.750 | 10.910 |
| Redundancy | True | 543 | 552 | -9 | 29.374 | 29.074 | 0.300 | 0.010 | 29.217 | 28.910 |
| FInvention | True | 531 | 471 | 60 | 2.325 | 2.282 | 0.043 | 0.019 | 2.197 | 2.197 |
| BHAR | True | 541 | 471 | 70 | -0.062 | -0.036 | -0.026 | -0.716 | -0.204 | -0.170 |
| FSales_Growth | True | 538 | 471 | 67 | 0.409 | 0.530 | -0.121 | -0.228 | 0.156 | 0.180 |
| Price_Issue | False | 0 | 552 | -552 |  | 0.988 |  |  |  | 0.726 |
| Price_Day5 | False | 0 | 552 | -552 |  | 0.949 |  |  |  | 0.698 |
| RD_Staff | False | 0 | 552 | -552 |  | 0.305 |  |  |  | 0.240 |
| RD_Asset | True | 541 | 552 | -11 | 0.079 | 0.105 | -0.026 | -0.251 | 0.052 | 0.073 |
| Size | True | 541 | 552 | -11 | 20.779 | 20.741 | 0.038 | 0.002 | 20.569 | 20.533 |
| Lev | True | 541 | 552 | -11 | 0.360 | 0.356 | 0.004 | 0.011 | 0.337 | 0.334 |
| ROA | True | 541 | 552 | -11 | 0.091 | 0.094 | -0.003 | -0.037 | 0.100 | 0.100 |
| Offerfee | True | 542 | 552 | -10 | 18.327 | 18.325 | 0.002 | 0.000 | 18.266 | 18.270 |
| Underwriter | True | 543 | 552 | -9 | 0.009 | 0.574 | -0.565 | -0.984 | 0.000 | 1.000 |
| Age | True | 541 | 552 | -11 | 2.612 | 2.601 | 0.011 | 0.004 | 2.660 | 2.639 |
| NumIndSeg | False | 0 | 552 | -552 |  | 0.854 |  |  |  | 0.693 |
| NumProdSeg | False | 0 | 552 | -552 |  | 1.475 |  |  |  | 1.609 |
| ScopeLen | False | 0 | 552 | -552 |  | 5.671 |  |  |  | 5.762 |

读法：`Redundancy`、`Size`、`Lev`、`ROA`、`Offerfee`、`Age` 都比较接近；`Underwriter` 和 paper-only controls 是最明显的数据缺口。`RD_Asset` 当前低于原文，`FSales_Growth` 也偏低，后续机制/经济后果回归需要先校对这些变量。

## 输出文件

- Table 1 chunk 对比：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/descriptive_comparison_vs_original_20260705/table1_panel_a_chunk_descriptives_vs_original_20260705.csv`
- Table 2 firm 对比：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/descriptive_comparison_vs_original_20260705/table2_panel_a_firm_descriptives_vs_original_20260705.csv`
- gap summary：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/descriptive_comparison_vs_original_20260705/descriptive_gap_summary_20260705.csv`
