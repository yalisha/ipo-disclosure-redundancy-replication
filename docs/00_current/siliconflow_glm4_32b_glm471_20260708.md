# SiliconFlow GLM-4-32B GLM471 合并测度诊断

日期：2026-07-08

## 结论

- 合并测度池：firm=483，chunk=7850。名称 GLM471 指向 Table2 可用样本口径，不等于测度池只含 471 家。
- 原始 GLM proxy：Summary_len mean=124.417，Redundancy_chunk mean=33.556。
- GLM471 最接近原文 Table 1 的候选是 `proxy_tailmerge1500_floor50`：Summary_len mean=127.556，Redundancy_chunk mean=33.142，企业层 Redundancy mean=30.512。
- Panel B：rho=-0.102, p=0.000；低评分组中位数=32.357，高评分组中位数=30.988。
- GLM300 最佳候选为 `proxy_tailmerge1600_floor50`，Summary_len mean=126.963，Redundancy_chunk mean=33.442。

## Source Batch Counts

| source_glm_batch | firm_n |
|---|---|
| glm300 | 300 |
| shard1_20260708 | 31 |
| shard2_20260708 | 31 |
| shard3_20260708 | 31 |
| shard4_20260708 | 31 |
| shard5_20260708 | 31 |
| shard6_20260708 | 28 |

## 候选口径排序

| name | loss_all | chunk_n | firm_n | floor_applied_n | Chunk_num_mean | Text_len_mean | Text_len_std | Summary_len_mean | Summary_len_std | Redundancy_chunk_mean | Redundancy_chunk_std | Redundancy_mean | Redundancy_std | panel_b_rho | panel_b_p | low_score_red_median | high_score_red_median | panel_c_rho | panel_d_rho |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| proxy_tailmerge1500_floor50 | 0.050 | 7671 | 483 | 121 | 17.342 | 3880.512 | 344.583 | 127.556 | 44.101 | 33.142 | 10.370 | 30.512 | 2.571 | -0.102 | 0.000 | 32.357 | 30.988 | 0.054 | -0.258 |
| proxy_tailmerge1600_floor50 | 0.050 | 7666 | 483 | 121 | 17.334 | 3883.043 | 341.850 | 127.639 | 44.187 | 33.148 | 10.364 | 30.512 | 2.571 | -0.103 | 0.000 | 32.366 | 30.976 | 0.054 | -0.259 |
| proxy_tailmerge1700_floor50 | 0.051 | 7650 | 483 | 121 | 17.303 | 3891.164 | 335.940 | 127.906 | 44.482 | 33.166 | 10.348 | 30.512 | 2.571 | -0.105 | 0.000 | 32.379 | 30.969 | 0.053 | -0.259 |
| proxy_tailmerge2000_floor50 | 0.053 | 7598 | 483 | 121 | 17.204 | 3917.795 | 330.046 | 128.782 | 45.864 | 33.233 | 10.310 | 30.512 | 2.571 | -0.111 | 0.000 | 32.404 | 30.969 | 0.054 | -0.255 |
| proxy_tailmerge2000_floor60 | 0.055 | 7598 | 483 | 189 | 17.204 | 3917.795 | 330.046 | 128.989 | 45.530 | 32.981 | 9.427 | 30.465 | 2.536 | -0.111 | 0.000 | 32.404 | 30.969 | 0.054 | -0.255 |
| proxy_tailmerge2000_floor80 | 0.059 | 7598 | 483 | 529 | 17.204 | 3917.795 | 330.046 | 129.870 | 44.398 | 32.331 | 7.879 | 30.267 | 2.417 | -0.114 | 0.000 | 32.396 | 30.965 | 0.052 | -0.252 |
| proxy_tailmerge2000_floor100 | 0.063 | 7598 | 483 | 1455 | 17.204 | 3917.795 | 330.046 | 132.355 | 42.134 | 31.200 | 6.245 | 29.708 | 2.179 | -0.125 | 0.000 | 32.311 | 30.922 | 0.041 | -0.228 |
| glm4token_tailmerge1500_floor0 | 0.092 | 7671 | 483 | 0 | 17.342 | 3880.512 | 344.583 | 146.608 | 53.007 | 29.617 | 18.985 | 26.574 | 2.303 | -0.118 | 0.000 | 28.218 | 26.893 | 0.042 | -0.211 |
| raw_proxy | 0.092 | 7850 | 483 | 0 | 17.682 | 3792.026 | 561.549 | 124.417 | 42.301 | 33.556 | 20.161 | 30.565 | 2.620 | -0.088 | 0.000 | 32.242 | 31.000 | 0.053 | -0.252 |
| glm4token_tailmerge2000_floor0 | 0.096 | 7598 | 483 | 0 | 17.204 | 3917.795 | 330.046 | 148.017 | 54.932 | 29.700 | 19.028 | 26.574 | 2.303 | -0.127 | 0.000 | 28.298 | 26.872 | 0.042 | -0.207 |

## 最佳候选 vs 原文

| metric | mean | paper_mean | std | paper_std | median | paper_median | p75 | paper_p75 |
|---|---|---|---|---|---|---|---|---|
| Chunk_num | 17.342 | 18.191 | 5.044 | 6.983 | 17.000 | 16.000 | 20.000 | 22.000 |
| Text_len | 3880.512 | 3866.817 | 344.583 | 343.868 | 3969.000 | 3954.000 | 3989.000 | 3985.000 |
| Summary_len | 127.556 | 132.678 | 44.101 | 39.683 | 122.000 | 130.000 | 143.000 | 158.000 |
| Redundancy_chunk | 33.142 | 32.176 | 10.370 | 11.730 | 31.744 | 29.739 | 37.028 | 37.037 |
| lnN_tech | 10.980 | 10.962 | 0.328 | 0.350 | 10.996 | 10.910 | 11.187 | 11.185 |
| Redundancy | 30.512 | 29.074 | 2.571 | 2.630 | 30.573 | 28.910 | 32.201 | 30.795 |

## 输出文件

- merged chunk metrics：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_glm471_merged_20260708/chunk_metrics_glm4_cot_v3b_len132_tight_20260708.csv`
- no-summary review CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_glm471_merged_20260708/chunk_metrics_glm4_cot_v3b_len132_tight_no_summary_text_20260708.csv`
- candidate summary：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm471_tailmerge_floor_candidates_20260708/candidate_summary_20260708.csv`
- best chunk：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm471_tailmerge_floor_candidates_20260708/proxy_tailmerge1500_floor50_chunk_metrics_20260708.csv`
- best firm：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm471_tailmerge_floor_candidates_20260708/proxy_tailmerge1500_floor50_firm_metrics_20260708.csv`
