# cot_v3b_len132 150 家摘要长度校准试验

日期：2026-07-03

## 结论

`PASS_FOR_SUMMARY_LEN_GATE`

本试验固定既有 token_proxy chunking，只更换摘要生成 prompt。目标是检查把 `Summary_len` 从当前约 109 拉向原文约 133 后，Panel B/C/D 是否还能成立。

注意：这里的 `PASS_FOR_SUMMARY_LEN_GATE` 只表示 150 家摘要长度校准门通过，不表示表 2 经济后果已经复刻。

## 样本

- 样本窗口：2019-2022。
- 抽样方式：按上市年配额，并在各年内按当前 full scoregate `Redundancy` 分位点抽取，避免只挑高/低冗余公司。
- 配额：2019 年 14 家，2020 年 46 家，2021 年 51 家，2022 年 39 家。

```text
688357,688168,688078,688021,688108,688366,688116,688139,688399,688218,688039,688288,688300,688111,688135,688529,688126,688521,688686,688318,688580,688668,688060,688398,688200,688233,688159,688086,688221,688311,688027,688155,688555,688526,688278,688567,688520,688339,688298,688065,688569,688133,688356,688222,688330,688093,688050,688360,688085,688051,688289,688500,688777,688338,688100,688558,688096,688177,688561,688256,688367,688075,688663,688183,688655,688167,688038,688819,688676,688779,688683,688212,688103,688117,688606,688622,688553,688195,688328,688617,688689,688121,688626,688682,688456,688272,688314,688187,688182,688211,688092,688192,688232,688611,688316,688076,688768,688355,688565,688739,688285,688667,688501,688350,688625,688105,688767,688317,688071,688280,688793,688475,688376,688115,688322,688238,688416,688172,688381,688380,688459,688141,688410,688035,688271,688403,688290,688489,688052,688503,688351,688053,688045,688496,688176,688331,688281,688119,688031,688102,688234,688073,688370,688231,688327,688448,688261,688062,688302,688375
```

## 输出

- 样本清单：`results/summary_len_calibration_150_20260703/sample_150_firms_20260703.csv`
- 样本代码：`results/summary_len_calibration_150_20260703/sample_150_codes_20260703.txt`
- pilot chunk metrics：`results/summary_len_calibration_150_20260703/chunk_metrics_cot_v3b_len132_tight_20260703.csv`
- pilot firm ranking：`results/summary_len_calibration_150_20260703/firm_ranking_cot_v3b_len132_tight_20260703.csv`
- pilot metrics JSON：`results/summary_len_calibration_150_20260703/metrics_cot_v3b_len132_tight_20260703.json`

## 三轮 prompt 校准记录

| mode | chunks | firms | Summary_len mean | Summary_len median | note |
|---|---:|---:|---:|---:|---|
| cot_v3b_len132 | 32 | 2 | 246.125 | 251.000 | too long; stopped after 2 firms |
| cot_v3b_len132_bounded | 32 | 2 | 150.625 | 146.000 | still high; stopped after 2 firms |
| cot_v3b_len132_tight | 2030 | 150 | 126.370 | 126.000 | selected pilot mode |

## 描述统计对照

| 指标 | baseline scoregate | cot_v3b_len132_tight |
|---|---:|---:|
| Text_len mean | 3761.814 | 3761.814 |
| Summary_len mean | 108.952 | 126.370 |
| Redundancy_chunk mean | 41.538 | 31.326 |
| Firm Redundancy mean | 34.882 | 29.812 |

## Panel B

| 检验 | baseline | cot_v3b_len132_tight |
|---|---:|---:|
| Spearman rho | -0.609 | -0.520 |
| Spearman p | 0.0000 | 0.0000 |
| low median by score median | 39.545 | 33.429 |
| high median by score median | 30.235 | 28.016 |

## Panel C

| 检验 | baseline | cot_v3b_len132_tight |
|---|---:|---:|
| raw cluster coef | 0.281 | 0.164 |
| raw cluster p | 0.3062 | 0.0769 |
| drop p99 cluster coef | 0.317 | 0.167 |
| drop p99 cluster p | 0.0291 | 0.0545 |

## Panel D

| 检验 | baseline | cot_v3b_len132_tight |
|---|---:|---:|
| all union cluster coef | -0.197 | -0.107 |
| all union cluster p | 0.0000 | 0.0000 |
| without target cluster coef | -0.281 | -0.154 |
| without target cluster p | 0.0000 | 0.0000 |

## 初步读法

- 若 `Summary_len` 进入 125-140 且 Panel B / Panel D 不破，说明当前主要缺口确实在摘要长度校准。
- 若 `Summary_len` 仍明显低于 125，下一步再上调长度区间；若超过 145 且 Panel B 变弱，说明长度校准过度。
- Panel C 以方向、drop p99/稳健版本为主，不把 150 家样本 raw/cluster 显著性作为唯一硬门槛。
- Panel C 已恢复正向且接近 cluster 显著：raw coef 0.164, cluster p 0.0769; drop p99 coef 0.167, p 0.0545；raw HC1 p 0.0039。
