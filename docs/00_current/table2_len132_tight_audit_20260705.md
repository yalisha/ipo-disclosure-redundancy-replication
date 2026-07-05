# Table 2 len132_tight 审计试跑

日期：2026-07-05

## 结论

- 判定：`NO_PASS_YET`。
- 这次确认使用的是 `cot_v3b_len132_tight` full543 企业层 X，不是旧 scoregate543。
- 结果没有复刻原文 Table 2：full 口径下 `FInvention` 和 `BHAR` 已回到负号但都很弱，`FSales_Growth` 仍为正号；共同样本和 2019-2022 窗口也没有把三项同时推回原文显著负向。
- 原文完整控制变量仍缺：`NumIndSeg, NumProdSeg, ScopeLen`。因此当前只能称为 current-controls audit，不能称为 strict Table 2 replication。
- 主要差距现在更像是 `Y/controls/sample` 口径问题；X 的均值已接近原文，但 `lnN_tech`、`Underwriter` 和三项 paper-only controls 仍未同口径。

## 输入

- master：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/summary_len_calibration_full_543_20260704/sample_543_firms_20260704.csv`
- len132_tight firm ranking：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/summary_len_calibration_full_543_20260704/firm_ranking_cot_v3b_len132_tight_20260703.csv`
- 输出目录：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_len132_tight_audit_20260705`
- 原文锚点来自本地 PDF `bib/IPO信息披露冗余如何影响新股定价？——基于生成式人工智能技术的经验证据_赵晓阳.pdf` 的表 2。
- 标准误：HC1 robust，与既有脚本保持一致。

## Panel A 对照

| variable | available | current_N | current_mean | original_N | original_mean | mean_diff_current_minus_original | current_median | original_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lnN_tech | True | 543 | 10.745 | 552 | 10.962 | -0.217 | 10.750 | 10.910 |
| Redundancy | True | 543 | 29.374 | 552 | 29.074 | 0.300 | 29.217 | 28.910 |
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
| full_by_y_available | FInvention | 531 | -0.0091 | -0.5809 | 0.5613 | 0.3289 | -0.0316 | -1.7200 | 471 | True |
| full_by_y_available | BHAR | 541 | -0.0051 | -0.6625 | 0.5077 | -0.0176 | -0.0188 | -2.1400 | 471 | True |
| full_by_y_available | FSales_Growth | 538 | 0.0281 | 1.3777 | 0.1683 | 0.2053 | -0.0373 | -2.0200 | 471 | False |
| common_3y_current_controls | FInvention | 528 | -0.0102 | -0.6383 | 0.5233 | 0.3287 | -0.0316 | -1.7200 | 471 | True |
| common_3y_current_controls | BHAR | 528 | -0.0061 | -0.8128 | 0.4164 | -0.0161 | -0.0188 | -2.1400 | 471 | True |
| common_3y_current_controls | FSales_Growth | 528 | 0.0286 | 1.4216 | 0.1551 | 0.2096 | -0.0373 | -2.0200 | 471 | False |
| w2_2019_2022_by_y_available | FInvention | 464 | -0.0062 | -0.3541 | 0.7233 | 0.3215 | -0.0316 | -1.7200 | 471 | True |
| w2_2019_2022_by_y_available | BHAR | 474 | -0.0040 | -0.4462 | 0.6554 | -0.0066 | -0.0188 | -2.1400 | 471 | True |
| w2_2019_2022_by_y_available | FSales_Growth | 471 | 0.0367 | 1.6217 | 0.1049 | 0.1729 | -0.0373 | -2.0200 | 471 | False |
| w2_2019_2022_common_3y_current_controls | FInvention | 461 | -0.0072 | -0.4051 | 0.6854 | 0.3203 | -0.0316 | -1.7200 | 471 | True |
| w2_2019_2022_common_3y_current_controls | BHAR | 461 | -0.0053 | -0.6057 | 0.5447 | -0.0048 | -0.0188 | -2.1400 | 471 | True |
| w2_2019_2022_common_3y_current_controls | FSales_Growth | 461 | 0.0359 | 1.6157 | 0.1062 | 0.1757 | -0.0373 | -2.0200 | 471 | False |

## 缺失原文控制变量

| variable | available_in_master | nonmissing_N | original_mean | note |
| --- | --- | --- | --- | --- |
| NumIndSeg | False | 0 | 0.854 | required by original Table 2 controls |
| NumProdSeg | False | 0 | 1.475 | required by original Table 2 controls |
| ScopeLen | False | 0 | 5.671 | required by original Table 2 controls |

## 直接读法

- `Redundancy` 均值贴得很近：当前约 29.374，原文 29.074。
- `lnN_tech` 当前约 10.745，原文 10.962；使用的是 len132 ranking 中 `original_length_units` 的对数，不再沿用旧 master 的字符长度列。
- `FInvention` 均值约 2.325，接近原文 2.282；len132 后回归系数变为负号，但幅度远小于原文且不显著。
- `BHAR` 均值约 -0.062，原文 -0.036；方向变量本身不离谱，但 Redundancy 系数弱。
- `FSales_Growth` 均值约 0.409，低于原文 0.530；这条 Y 的口径嫌疑仍然较大。
- `Underwriter` 均值约 0.009，原文 0.574；当前来源表的 Sponsor 大多为 `None`，这个 dummy 基本不可用，必须重下或换字段。

## 下一步

1. 补或重构 `NumIndSeg / NumProdSeg / ScopeLen`。
2. 重构 `Underwriter`：原文定义是 IPO 承销业务前十大券商，当前 CSMAR 临时表的 Sponsor 字段严重缺失。
3. 对 `lnN_tech` 做单位审计：字符数、中文字数、token proxy、空白清洗后长度分别算一遍。
4. 对三条 Y 做口径网格，优先 `FInvention` 的申请/授权/窗口和 `BHAR` 的基准收益/首日处理。
5. 做 552 -> 543 -> 541 -> 471 的逐家公司 crosswalk。

## 输出文件

- master copy：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_len132_tight_audit_20260705/table2_len132_tight_master_20260705.csv`
- Panel A：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_len132_tight_audit_20260705/panel_a_descriptives_vs_original_20260705.csv`
- regressions：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_len132_tight_audit_20260705/table2_len132_tight_regressions_20260705.csv`
- waterfall：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_len132_tight_audit_20260705/table2_len132_tight_sample_waterfall_20260705.csv`
- missing controls：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_len132_tight_audit_20260705/table2_len132_tight_missing_paper_controls_20260705.csv`
