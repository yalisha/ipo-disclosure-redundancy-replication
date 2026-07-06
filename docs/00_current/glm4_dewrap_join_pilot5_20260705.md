# GLM4 dewrap_join 5 家 LLM pilot

日期：2026-07-05

## 结论

`PASS_SMALL_PILOT_FOR_SCALE_ONLY`

这轮只是在新的 `dewrap_join + GLM-4 tokenizer + 4000 token boundary split` chunk base 上试跑 5 家，检验量级是否能回到原文附近；它不是正式 gate。

核心读法：

- 5 家 78 个 chunk 已全部跑完 `cot_v3b_len132_tight`。
- 若沿用原项目此前的摘要长度 proxy，`Summary_len` mean=134.526，`Redundancy_chunk` mean=29.232，分别贴近原文 132.678 和 32.176。
- 若摘要也改用 GLM-4 tokenizer 计数，`Summary_len` mean=162.782，`Redundancy_chunk` mean=24.369，冗余度会明显低于原文。
- Panel B 在 5 家小样本里方向为负但不显著：proxy 口径 rho=-0.160, p=0.1625；低评分组冗余中位数 29.375 高于高评分组 27.596，硬方向没坏。
- Panel C / D 在 5 家小样本里不应作为成败判据；这里只看方向和是否出现明显异常。

## 样本

| sec_code | sec_name | date | chunks | glm4_tokens | Red_proxy | Red_glm4 |
|---|---|---|---|---|---|---|
| 688123 | 聚辰股份 | 2019-12-18 | 19 | 72696 | 28.539 | 23.532 |
| 688311 | 盟升电子 | 2020-07-28 | 17 | 63244 | 30.128 | 24.897 |
| 688038 | 中科通达 | 2021-07-07 | 16 | 61026 | 27.352 | 23.570 |
| 688172 | 燕东微 | 2022-12-13 | 13 | 50646 | 30.109 | 24.383 |
| 688693 | 锴威特 | 2023-08-14 | 13 | 50357 | 26.035 | 20.962 |

## 输出文件

- chunk metrics：`results/glm4_dewrap_join_pilot5_20260705/chunk_metrics_glm4_cot_v3b_len132_tight_20260705.csv`
- firm metrics：`results/glm4_dewrap_join_pilot5_20260705/firm_metrics_glm4_cot_v3b_len132_tight_20260705.csv`
- diagnostics：`results/glm4_dewrap_join_pilot5_20260705/diagnostics_glm4_cot_v3b_len132_tight_20260705.json`
- LLM chunk CSV：`results/glm4_dewrap_join_pilot5_20260705/ipo_redundancy_chunk_with_llm_cot_v3b_len132_tight.csv`

## 描述统计对照

| scope | metric | N | mean | paper_mean | diff | std | median | paper_median | p25 | p75 |
|---|---|---|---|---|---|---|---|---|---|---|
| chunk | Chunk_num | 78 | 15.949 | 18.191 | -2.242 | 2.340 | 16.000 | 16.000 | 13.000 | 17.000 |
| chunk | Text_len | 78 | 3819.795 | 3866.817 | -47.022 | 530.402 | 3963.000 | 3954.000 | 3896.750 | 3988.000 |
| chunk | Summary_len_proxy | 78 | 134.526 | 132.678 | 1.848 | 24.693 | 133.000 | 130.000 | 117.250 | 155.000 |
| chunk | Redundancy_chunk_proxy | 78 | 29.232 | 32.176 | -2.944 | 6.884 | 28.519 | 29.739 | 25.542 | 33.452 |
| chunk | Summary_len_glm4 | 78 | 162.782 | 132.678 | 30.104 | 33.094 | 158.000 | 130.000 | 138.000 | 189.500 |
| chunk | Redundancy_chunk_glm4 | 78 | 24.369 | 32.176 | -7.807 | 6.260 | 24.013 | 29.739 | 20.827 | 28.398 |
| firm | lnN_tech | 5 | 10.985 | 10.962 | 0.023 | 0.156 | 11.019 | 10.910 | 10.833 | 11.055 |
| firm | Redundancy_proxy | 5 | 28.432 | 29.074 | -0.642 | 1.776 | 28.539 | 28.910 | 27.352 | 30.109 |
| firm | Redundancy_glm4 | 5 | 23.469 | 29.074 | -5.605 | 1.514 | 23.570 | 28.910 | 23.532 | 24.383 |

## Panel B/C/D 快速检验

| measure | B rho | B p | low med | high med | <2 med | >=2 med | C rho | D rho all | D p all |
|---|---|---|---|---|---|---|---|---|---|
| proxy denominator | -0.160 | 0.1625 | 29.375 | 27.596 | 32.161 | 27.517 | 0.086 | -0.313 | 0.0053 |
| GLM4 denominator | -0.176 | 0.1228 | 24.272 | 23.871 | 27.384 | 23.116 | 0.135 | -0.324 | 0.0038 |

## 企业层排序

| rank | sec_code | sec_name | chunks | Red_proxy | Red_glm4 | score_mean |
|---|---|---|---|---|---|---|
| 1 | 688311 | 盟升电子 | 17 | 30.128 | 24.897 | 2.395 |
| 2 | 688172 | 燕东微 | 13 | 30.109 | 24.383 | 2.216 |
| 3 | 688123 | 聚辰股份 | 19 | 28.539 | 23.532 | 2.340 |
| 4 | 688038 | 中科通达 | 16 | 27.352 | 23.570 | 2.616 |
| 5 | 688693 | 锴威特 | 13 | 26.035 | 20.962 | 2.360 |

## 判断

1. `dewrap_join` 新 chunk base 的分块数量和正文长度已经非常接近原文；这一步值得继续。
2. 摘要长度单位需要固定：如果原文 `Summary_len` 本质更接近中文摘要字符 proxy，当前 prompt 已经接近；如果原文也用 GLM tokenizer 计摘要，当前摘要过长，需要把 prompt 缩短。
3. 5 家样本下 Panel B 只保住方向和低/高评分中位数关系，rho 绝对值不够；这可能是样本太小，也可能说明新 chunk base 后评分-冗余关系需要重新校准。
4. 下一步不建议立刻全样本，建议做 50 家分层 pilot：固定 `dewrap_join`，同时输出 proxy 与 GLM4 两套摘要长度，正式看 Panel B/C/D。
