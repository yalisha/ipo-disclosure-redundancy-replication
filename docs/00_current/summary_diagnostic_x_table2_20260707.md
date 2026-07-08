# Summary Denominator Diagnostic X And Table 2

日期：2026-07-07

## 结论

- 本轮只做第一步 diagnostic X：不重跑 LLM，不把机械 cap 当正式测度。
- 处理口径固定为 `tail_merge<1700`，然后对低相关 processed chunk 执行 `Summary_len=min(Summary_len,80)`。
- 两个候选分别是 `tailmerge1700_score18_cap80` 与 `tailmerge1700_highshare10_cap80`。
- 结果显示：描述统计确实更接近原文右尾；但 Table 2 的 `BHAR` 和 `FSales_Growth` 仍没有恢复原文显著负向。
- 因此这一步支持“摘要分母右尾机制可以修”，但不支持“修 X 就能复刻主效应”。

## Diagnostic X 描述统计

原文参照：chunk N=`8683`，Summary mean/std=`132.678`/`39.683`，Red mean/std/p75=`32.176`/`11.73`/`37.037`，Firm Red mean/std=`29.074`/`2.63`。

| candidate | chunk_n | chunk_n_gap | cap_applied_n | Summary_len_mean | Summary_len_std | Red_mean | Red_std | Red_p75 | FirmRed_mean | FirmRed_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tailmerge1700_score18_cap80 | 8679 | -4 | 1564 | 129.006 | 38.515 | 32.943 | 10.776 | 36.907 | 30.210 | 2.373 |
| tailmerge1700_highshare10_cap80 | 8679 | -4 | 1541 | 129.685 | 38.214 | 32.701 | 10.619 | 36.236 | 30.050 | 2.364 |

## Panel B 方向性检查

| candidate | N | spearman_rho | spearman_p | low_median_by_score_median | high_median_by_score_median | low_lt2_median | high_ge2_median |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tailmerge1700_score18_cap80 | 8679 | -0.5618 | 0.0000 | 34.1538 | 27.4122 | 49.6500 | 28.1056 |
| tailmerge1700_highshare10_cap80 | 8679 | -0.5308 | 0.0000 | 33.4874 | 27.4122 | 49.4875 | 28.1434 |

## Table 2 471 家主回归

| candidate | dep_var | N | coef | t_HC1 | p_HC1 | paper_coef | paper_t | coef_delta_vs_baseline | gap_improved_vs_baseline | sign_match |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_original_x | FInvention | 471 | -0.0291 | -1.1562 | 0.2476 | -0.0316 | -1.7200 | 0.0000 | 0 | 1 |
| baseline_original_x | BHAR | 471 | 0.0033 | 0.2960 | 0.7673 | -0.0188 | -2.1400 | 0.0000 | 0 | 0 |
| baseline_original_x | FSales_Growth | 471 | 0.0141 | 0.6247 | 0.5321 | -0.0373 | -2.0200 | 0.0000 | 0 | 0 |
| tailmerge1700_score18_cap80 | FInvention | 471 | -0.0231 | -0.9895 | 0.3224 | -0.0316 | -1.7200 | 0.0060 | 0 | 1 |
| tailmerge1700_score18_cap80 | BHAR | 471 | 0.0133 | 1.2981 | 0.1943 | -0.0188 | -2.1400 | 0.0100 | 0 | 0 |
| tailmerge1700_score18_cap80 | FSales_Growth | 471 | 0.0116 | 0.6499 | 0.5157 | -0.0373 | -2.0200 | -0.0025 | 1 | 0 |
| tailmerge1700_highshare10_cap80 | FInvention | 471 | -0.0281 | -1.2163 | 0.2239 | -0.0316 | -1.7200 | 0.0010 | 0 | 1 |
| tailmerge1700_highshare10_cap80 | BHAR | 471 | 0.0062 | 0.6183 | 0.5364 | -0.0188 | -2.1400 | 0.0029 | 0 | 0 |
| tailmerge1700_highshare10_cap80 | FSales_Growth | 471 | 0.0079 | 0.4860 | 0.6270 | -0.0373 | -2.0200 | -0.0062 | 1 | 0 |

## 读法

1. `score18 cap80` 对右尾修复更强，`Redundancy_chunk` 的 p75 与 std 更接近原文，但企业层 Redundancy 均值被推高到 30 以上。
2. `highshare10 cap80` 更温和，且让 `FSales_Growth` 系数从 0.0141 降到 0.0079，但仍没有转负。
3. `FInvention` 仍是负向但不显著；`BHAR` 仍为正，甚至在 `score18 cap80` 下更偏离原文。
4. 下一步若继续修 X，应只把它作为真实 LLM 低相关短摘 repair 的候选，不应直接用机械 cap 定版。
5. 若目标是复刻论文主效应，优先级仍应回到 `BHAR/FSales_Growth` 的原文数据库字段与窗口口径。

## 输出

- master：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/summary_diagnostic_x_table2_20260707/table2_471_diagnostic_x_master_20260707.csv`
- regressions：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/summary_diagnostic_x_table2_20260707/table2_471_diagnostic_x_regressions_20260707.csv`
- descriptives：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/summary_diagnostic_x_table2_20260707/diagnostic_x_descriptives_vs_original_20260707.csv`
- panel tests：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/summary_diagnostic_x_table2_20260707/diagnostic_x_panel_tests_20260707.csv`
