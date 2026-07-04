# cot_v3b_len132 50 家摘要长度校准试验

日期：2026-07-03

## 结论

`PASS_FOR_SUMMARY_LEN_GATE`

本试验固定既有 token_proxy chunking，只更换摘要生成 prompt。目标是检查把 `Summary_len` 从当前约 109 拉向原文约 133 后，Panel B/C/D 是否还能成立。

注意：这里的 `PASS_FOR_SUMMARY_LEN_GATE` 只表示 50 家摘要长度校准门通过，不表示表 2 经济后果已经复刻。

## 样本

- 样本窗口：2019-2022。
- 抽样方式：按上市年配额，并在各年内按当前 full scoregate `Redundancy` 分位点抽取，避免只挑高/低冗余公司。
- 配额：2019 年 5 家，2020 年 15 家，2021 年 17 家，2022 年 13 家。

```text
688357,688021,688116,688039,688111,688135,688521,688668,688233,688086,688027,688526,688339,688569,688222,688050,688085,688777,688096,688256,688367,688183,688038,688779,688103,688622,688328,688121,688456,688211,688232,688076,688565,688667,688625,688317,688793,688475,688322,688172,688459,688271,688489,688351,688496,688281,688234,688231,688261,688375
```

## 输出

- 样本清单：`results/summary_len_calibration_50_20260703/sample_50_firms_20260703.csv`
- 样本代码：`results/summary_len_calibration_50_20260703/sample_50_codes_20260703.txt`
- pilot chunk metrics：`results/summary_len_calibration_50_20260703/chunk_metrics_cot_v3b_len132_tight_20260703.csv`
- pilot firm ranking：`results/summary_len_calibration_50_20260703/firm_ranking_cot_v3b_len132_tight_20260703.csv`
- pilot metrics JSON：`results/summary_len_calibration_50_20260703/metrics_cot_v3b_len132_tight_20260703.json`

## 三轮 prompt 校准记录

| mode | chunks | firms | Summary_len mean | Summary_len median | note |
|---|---:|---:|---:|---:|---|
| cot_v3b_len132 | 32 | 2 | 246.125 | 251.000 | too long; stopped after 2 firms |
| cot_v3b_len132_bounded | 32 | 2 | 150.625 | 146.000 | still high; stopped after 2 firms |
| cot_v3b_len132_tight | 654 | 50 | 126.531 | 127.000 | selected pilot mode |

## 描述统计对照

| 指标 | baseline scoregate | cot_v3b_len132_tight |
|---|---:|---:|
| Text_len mean | 3768.138 | 3768.138 |
| Summary_len mean | 109.436 | 126.531 |
| Redundancy_chunk mean | 41.921 | 31.431 |
| Firm Redundancy mean | 35.098 | 29.933 |

## Panel B

| 检验 | baseline | cot_v3b_len132_tight |
|---|---:|---:|
| Spearman rho | -0.609 | -0.548 |
| Spearman p | 0.0000 | 0.0000 |
| low median by score median | 39.340 | 33.145 |
| high median by score median | 29.617 | 28.056 |

## Panel C

| 检验 | baseline | cot_v3b_len132_tight |
|---|---:|---:|
| raw cluster coef | -0.127 | 0.052 |
| raw cluster p | 0.8066 | 0.6670 |
| drop p99 cluster coef | 0.196 | 0.049 |
| drop p99 cluster p | 0.3640 | 0.6611 |

## Panel D

| 检验 | baseline | cot_v3b_len132_tight |
|---|---:|---:|
| all union cluster coef | -0.232 | -0.124 |
| all union cluster p | 0.0000 | 0.0000 |
| without target cluster coef | -0.395 | -0.222 |
| without target cluster p | 0.0005 | 0.0000 |

## 初步读法

- 若 `Summary_len` 进入 125-140 且 Panel B / Panel D 不破，说明当前主要缺口确实在摘要长度校准。
- 若 `Summary_len` 仍明显低于 125，下一步再上调长度区间；若超过 145 且 Panel B 变弱，说明长度校准过度。
- Panel C 以方向、drop p99/稳健版本为主，不把 50 家小样本 raw cluster 显著性作为硬门槛。
- 本轮没有恢复 Panel C 显著性，说明长度校准能修 Table 1 量级和保留 B/D 效度，但不能单独解决 chunk_count 关系。
