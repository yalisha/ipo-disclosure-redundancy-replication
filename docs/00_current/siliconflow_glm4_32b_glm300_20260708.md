# SiliconFlow GLM-4-32B GLM300 合并测度诊断

日期：2026-07-08

## 结论

- 合并样本：firm=300，chunk=5117，glm200=200，table2_next100_after200=100。
- 原始 GLM proxy：Summary_len mean=123.896，Redundancy_chunk mean=34.010。
- GLM300 最接近原文 Table 1 的候选是 `proxy_tailmerge1600_floor50`：Summary_len mean=126.963，Redundancy_chunk mean=33.442，企业层 Redundancy mean=30.657。
- Panel B：rho=-0.087, p=0.000；低评分组中位数=32.523，高评分组中位数=31.291。
- QC：GLM300 合并前第三批 100 家已完成 1655/1655 chunk 验收，空摘要和 0 分母均清零；2 个 GLM 空摘要 chunk 使用透明兜底摘要，评分字段保留原值。
- GLM300 的用途是继续裁决 GLM-only 是否值得扩到 Table2 471。

## 候选口径排序

| name | loss_all | chunk_n | floor_applied_n | Chunk_num_mean | Text_len_mean | Text_len_std | Summary_len_mean | Summary_len_std | Redundancy_chunk_mean | Redundancy_chunk_std | Redundancy_mean | Redundancy_std | panel_b_rho | panel_b_p | low_score_red_median | high_score_red_median | panel_c_rho | panel_d_rho |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| proxy_tailmerge1600_floor50 | 0.051 | 5003 | 77 | 18.221 | 3884.759 | 337.136 | 126.963 | 45.966 | 33.442 | 10.546 | 30.657 | 2.581 | -0.087 | 0.000 | 32.523 | 31.291 | 0.055 | -0.250 |
| proxy_tailmerge2000_floor50 | 0.051 | 4959 | 77 | 18.091 | 3919.227 | 325.843 | 128.090 | 47.542 | 33.528 | 10.497 | 30.657 | 2.581 | -0.093 | 0.000 | 32.574 | 31.287 | 0.055 | -0.245 |
| proxy_tailmerge1700_floor50 | 0.051 | 4994 | 77 | 18.191 | 3891.760 | 332.182 | 127.192 | 46.253 | 33.459 | 10.531 | 30.657 | 2.581 | -0.088 | 0.000 | 32.529 | 31.291 | 0.054 | -0.250 |
| proxy_tailmerge1500_floor50 | 0.053 | 5008 | 77 | 18.233 | 3880.880 | 341.388 | 126.836 | 45.835 | 33.433 | 10.555 | 30.657 | 2.581 | -0.086 | 0.000 | 32.516 | 31.323 | 0.055 | -0.248 |
| proxy_tailmerge2000_floor60 | 0.053 | 4959 | 129 | 18.091 | 3919.227 | 325.843 | 128.304 | 47.211 | 33.265 | 9.588 | 30.609 | 2.550 | -0.094 | 0.000 | 32.574 | 31.287 | 0.055 | -0.245 |
| proxy_tailmerge2000_floor80 | 0.056 | 4959 | 376 | 18.091 | 3919.227 | 325.843 | 129.244 | 46.062 | 32.571 | 7.972 | 30.399 | 2.441 | -0.097 | 0.000 | 32.574 | 31.283 | 0.053 | -0.242 |
| proxy_tailmerge2000_floor100 | 0.059 | 4959 | 1001 | 18.091 | 3919.227 | 325.843 | 131.877 | 43.782 | 31.371 | 6.282 | 29.805 | 2.231 | -0.109 | 0.000 | 32.495 | 31.197 | 0.044 | -0.216 |
| glm4token_tailmerge2000_floor0 | 0.096 | 4959 | 0 | 18.091 | 3919.227 | 325.843 | 147.227 | 57.056 | 30.094 | 21.892 | 26.700 | 2.336 | -0.108 | 0.000 | 28.444 | 27.298 | 0.044 | -0.198 |
| glm4token_tailmerge1500_floor0 | 0.097 | 5008 | 0 | 18.233 | 3880.880 | 341.388 | 145.787 | 55.220 | 30.006 | 21.828 | 26.700 | 2.336 | -0.100 | 0.000 | 28.336 | 27.301 | 0.044 | -0.202 |
| raw_proxy | 0.102 | 5117 | 0 | 18.581 | 3798.211 | 547.494 | 123.896 | 44.274 | 34.010 | 22.878 | 30.710 | 2.624 | -0.073 | 0.000 | 32.407 | 31.339 | 0.056 | -0.247 |

## 最佳候选 vs 原文

| metric | mean | paper_mean | std | paper_std | median | paper_median | p75 | paper_p75 |
|---|---|---|---|---|---|---|---|---|
| Chunk_num | 18.221 | 18.191 | 5.271 | 6.983 | 18.000 | 16.000 | 22.000 | 22.000 |
| Text_len | 3884.759 | 3866.817 | 337.136 | 343.868 | 3969.000 | 3954.000 | 3989.000 | 3985.000 |
| Summary_len | 126.963 | 132.678 | 45.966 | 39.683 | 121.000 | 130.000 | 142.000 | 158.000 |
| Redundancy_chunk | 33.442 | 32.176 | 10.546 | 11.730 | 31.992 | 29.739 | 37.346 | 37.037 |
| lnN_tech | 11.028 | 10.962 | 0.340 | 0.350 | 11.033 | 10.910 | 11.231 | 11.185 |
| Redundancy | 30.657 | 29.074 | 2.581 | 2.630 | 30.897 | 28.910 | 32.281 | 30.795 |

## 输出文件

- merged chunk metrics：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_glm300_merged_20260708/chunk_metrics_glm4_cot_v3b_len132_tight_20260708.csv`
- no-summary review CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_glm300_merged_20260708/chunk_metrics_glm4_cot_v3b_len132_tight_no_summary_text_20260708.csv`
- candidate summary：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm300_tailmerge_floor_candidates_20260708/candidate_summary_20260708.csv`
- best chunk：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm300_tailmerge_floor_candidates_20260708/proxy_tailmerge1600_floor50_chunk_metrics_20260708.csv`
- best firm：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm300_tailmerge_floor_candidates_20260708/proxy_tailmerge1600_floor50_firm_metrics_20260708.csv`
