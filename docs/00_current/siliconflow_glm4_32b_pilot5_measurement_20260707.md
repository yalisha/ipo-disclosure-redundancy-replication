# GLM4 dewrap_join 5 家 LLM measurement gate

日期：2026-07-07

## 结论

`PASS_SMALL_PILOT_FOR_SCALE_ONLY`

这轮只是在新的 `dewrap_join + GLM-4 tokenizer + 4000 token boundary split` chunk base 上试跑 5 家，检验量级是否能回到原文附近；它不是正式 gate。

核心读法：

- 5 家 78 个 chunk 已全部跑完 `cot_v3b_len132_tight`。
- 若沿用原项目此前的摘要长度 proxy，`Summary_len` mean=131.731，`Redundancy_chunk` mean=30.745，分别贴近原文 132.678 和 32.176。
- 若摘要也改用 GLM-4 tokenizer 计数，`Summary_len` mean=150.154，`Redundancy_chunk` mean=26.976，冗余度会明显低于原文。
- Panel B 在 5 家样本里方向为负：proxy 口径 rho=-0.159, p=0.1674；低评分组冗余中位数 31.122 高于高评分组 29.827，硬方向成立。
- Panel C / D 在 5 家样本里仍需谨慎解读；这里只看方向和是否出现明显异常。

## 样本

| sec_code | sec_name | date | chunks | glm4_tokens | Red_proxy | Red_glm4 |
|---|---|---|---|---|---|---|
| 688123 | 聚辰股份 | 2019-12-18 | 19 | 72696 | 27.925 | 25.328 |
| 688311 | 盟升电子 | 2020-07-28 | 17 | 63244 | 28.758 | 25.065 |
| 688038 | 中科通达 | 2021-07-07 | 16 | 61026 | 29.281 | 26.799 |
| 688172 | 燕东微 | 2022-12-13 | 13 | 50646 | 28.198 | 24.104 |
| 688693 | 锴威特 | 2023-08-14 | 13 | 50357 | 31.608 | 25.941 |

## 输出文件

- chunk metrics：`results/siliconflow_glm4_32b_pilot5_20260707/chunk_metrics_glm4_cot_v3b_len132_tight_20260705.csv`
- firm metrics：`results/siliconflow_glm4_32b_pilot5_20260707/firm_metrics_glm4_cot_v3b_len132_tight_20260705.csv`
- diagnostics：`results/siliconflow_glm4_32b_pilot5_20260707/diagnostics_glm4_cot_v3b_len132_tight_20260705.json`
- LLM chunk CSV：`results/siliconflow_glm4_32b_pilot5_20260707/ipo_redundancy_chunk_with_llm_cot_v3b_len132_tight.csv`

## 描述统计对照

| scope | metric | N | mean | paper_mean | diff | std | median | paper_median | p25 | p75 |
|---|---|---|---|---|---|---|---|---|---|---|
| chunk | Chunk_num | 78 | 15.949 | 18.191 | -2.242 | 2.340 | 16.000 | 16.000 | 13.000 | 17.000 |
| chunk | Text_len | 78 | 3819.795 | 3866.817 | -47.022 | 530.402 | 3963.000 | 3954.000 | 3896.750 | 3988.000 |
| chunk | Summary_len_proxy | 78 | 131.731 | 132.678 | -0.947 | 44.010 | 127.500 | 130.000 | 105.000 | 145.750 |
| chunk | Redundancy_chunk_proxy | 78 | 30.745 | 32.176 | -1.431 | 8.127 | 30.658 | 29.739 | 26.661 | 36.415 |
| chunk | Summary_len_glm4 | 78 | 150.154 | 132.678 | 17.476 | 50.767 | 141.000 | 130.000 | 122.250 | 162.000 |
| chunk | Redundancy_chunk_glm4 | 78 | 26.976 | 32.176 | -5.200 | 7.042 | 27.199 | 29.739 | 22.888 | 31.643 |
| firm | lnN_tech | 5 | 10.985 | 10.962 | 0.023 | 0.156 | 11.019 | 10.910 | 10.833 | 11.055 |
| firm | Redundancy_proxy | 5 | 29.154 | 29.074 | 0.080 | 1.468 | 28.758 | 28.910 | 28.198 | 29.281 |
| firm | Redundancy_glm4 | 5 | 25.447 | 29.074 | -3.627 | 1.004 | 25.328 | 28.910 | 25.065 | 25.941 |

## Panel B/C/D 快速检验

| measure | B rho | B p | low med | high med | <2 med | >=2 med | C rho | D rho all | D p all |
|---|---|---|---|---|---|---|---|---|---|
| proxy denominator | -0.159 | 0.1674 | 31.122 | 29.827 | 30.281 | 30.708 | -0.029 | -0.204 | 0.0736 |
| GLM4 denominator | -0.184 | 0.1097 | 28.405 | 26.427 | 27.282 | 26.437 | 0.071 | -0.205 | 0.0724 |

## 企业层排序

| rank | sec_code | sec_name | chunks | Red_proxy | Red_glm4 | score_mean |
|---|---|---|---|---|---|---|
| 1 | 688693 | 锴威特 | 13 | 31.608 | 25.941 | 1.882 |
| 2 | 688038 | 中科通达 | 16 | 29.281 | 26.799 | 2.121 |
| 3 | 688311 | 盟升电子 | 17 | 28.758 | 25.065 | 2.197 |
| 4 | 688172 | 燕东微 | 13 | 28.198 | 24.104 | 2.132 |
| 5 | 688123 | 聚辰股份 | 19 | 27.925 | 25.328 | 2.060 |

## 判断

1. `dewrap_join` 新 chunk base 的分块数量和正文长度已经非常接近原文；这一步值得继续。
2. 摘要长度单位需要固定：如果原文 `Summary_len` 本质更接近中文摘要字符 proxy，当前 prompt 已经接近；如果原文也用 GLM tokenizer 计摘要，当前摘要过长，需要把 prompt 缩短。
3. 5 家样本下 Panel B 主要看方向、显著性和低/高评分中位数关系；Panel C/D 用 firm-cluster 与 Spearman 同时核对。
4. 下一步不建议立刻全样本，建议做 50 家分层 pilot：固定 `dewrap_join`，同时输出 proxy 与 GLM4 两套摘要长度，正式看 Panel B/C/D。
