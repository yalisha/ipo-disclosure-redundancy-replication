# cot_v3b_len132 100 家摘要长度校准试验

日期：2026-07-03

## 结论

`PASS_FOR_SUMMARY_LEN_GATE`

本试验固定既有 token_proxy chunking，只更换摘要生成 prompt。目标是检查把 `Summary_len` 从当前约 109 拉向原文约 133 后，Panel B/C/D 是否还能成立。

注意：这里的 `PASS_FOR_SUMMARY_LEN_GATE` 只表示 100 家摘要长度校准门通过，不表示表 2 经济后果已经复刻。

## 样本

- 样本窗口：2019-2022。
- 抽样方式：按上市年配额，并在各年内按当前 full scoregate `Redundancy` 分位点抽取，避免只挑高/低冗余公司。
- 配额：2019 年 10 家，2020 年 30 家，2021 年 34 家，2022 年 26 家。

```text
688357,688168,688021,688108,688116,688139,688218,688039,688300,688111,688135,688529,688521,688686,688668,688060,688200,688233,688086,688221,688027,688155,688526,688278,688520,688339,688065,688569,688356,688222,688093,688050,688085,688051,688500,688777,688558,688096,688561,688256,688367,688075,688183,688655,688038,688819,688779,688683,688103,688117,688622,688553,688328,688617,688121,688626,688456,688272,688182,688211,688192,688232,688316,688076,688355,688565,688285,688667,688350,688625,688767,688317,688280,688793,688475,688376,688322,688238,688172,688381,688459,688141,688035,688271,688290,688489,688503,688351,688496,688176,688281,688119,688102,688234,688370,688231,688448,688261,688302,688375
```

## 输出

- 样本清单：`results/summary_len_calibration_100_20260703/sample_100_firms_20260703.csv`
- 样本代码：`results/summary_len_calibration_100_20260703/sample_100_codes_20260703.txt`
- pilot chunk metrics：`results/summary_len_calibration_100_20260703/chunk_metrics_cot_v3b_len132_tight_20260703.csv`
- pilot firm ranking：`results/summary_len_calibration_100_20260703/firm_ranking_cot_v3b_len132_tight_20260703.csv`
- pilot metrics JSON：`results/summary_len_calibration_100_20260703/metrics_cot_v3b_len132_tight_20260703.json`

## 三轮 prompt 校准记录

| mode | chunks | firms | Summary_len mean | Summary_len median | note |
|---|---:|---:|---:|---:|---|
| cot_v3b_len132 | 32 | 2 | 246.125 | 251.000 | too long; stopped after 2 firms |
| cot_v3b_len132_bounded | 32 | 2 | 150.625 | 146.000 | still high; stopped after 2 firms |
| cot_v3b_len132_tight | 1328 | 100 | 126.581 | 126.000 | selected pilot mode |

## 描述统计对照

| 指标 | baseline scoregate | cot_v3b_len132_tight |
|---|---:|---:|
| Text_len mean | 3769.910 | 3769.910 |
| Summary_len mean | 109.016 | 126.581 |
| Redundancy_chunk mean | 41.961 | 31.392 |
| Firm Redundancy mean | 34.993 | 29.823 |

## Panel B

| 检验 | baseline | cot_v3b_len132_tight |
|---|---:|---:|
| Spearman rho | -0.620 | -0.535 |
| Spearman p | 0.0000 | 0.0000 |
| low median by score median | 39.880 | 33.246 |
| high median by score median | 30.023 | 28.065 |

## Panel C

| 检验 | baseline | cot_v3b_len132_tight |
|---|---:|---:|
| raw cluster coef | 0.232 | 0.128 |
| raw cluster p | 0.4989 | 0.2582 |
| drop p99 cluster coef | 0.301 | 0.137 |
| drop p99 cluster p | 0.0950 | 0.1968 |

## Panel D

| 检验 | baseline | cot_v3b_len132_tight |
|---|---:|---:|
| all union cluster coef | -0.218 | -0.116 |
| all union cluster p | 0.0000 | 0.0000 |
| without target cluster coef | -0.347 | -0.199 |
| without target cluster p | 0.0000 | 0.0000 |

## 初步读法

- 若 `Summary_len` 进入 125-140 且 Panel B / Panel D 不破，说明当前主要缺口确实在摘要长度校准。
- 若 `Summary_len` 仍明显低于 125，下一步再上调长度区间；若超过 145 且 Panel B 变弱，说明长度校准过度。
- Panel C 以方向、drop p99/稳健版本为主，不把 100 家样本 raw/cluster 显著性作为唯一硬门槛。
- 本轮没有恢复 Panel C 显著性，说明长度校准能修 Table 1 量级和保留 B/D 效度，但不能单独解决 chunk_count 关系。
