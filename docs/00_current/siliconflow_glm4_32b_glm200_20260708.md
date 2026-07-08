# SiliconFlow GLM-4-32B GLM200 合并测度诊断

日期：2026-07-08

## 结论

- 合并样本：firm=200，chunk=3462，glm100=100，table2_next100=100。
- 原始 GLM proxy：Summary_len mean=124.059，Redundancy_chunk mean=34.242。
- GLM200 最接近原文 Table 1 的候选是 `proxy_tailmerge1500_floor50`：Summary_len mean=126.793，Redundancy_chunk mean=33.389，企业层 Redundancy mean=30.597。
- Panel B：rho=-0.100, p=0.000；低评分组中位数=32.549，高评分组中位数=31.190。
- GLM200 的用途是决定是否继续扩到 Table2 471。若接 Table2 后 BHAR/FSales_Growth 仍不转负，应停止把问题继续归咎于摘要模型。

## 候选口径排序

| name | loss_all | chunk_n | floor_applied_n | Chunk_num_mean | Text_len_mean | Text_len_std | Summary_len_mean | Summary_len_std | Redundancy_chunk_mean | Redundancy_chunk_std | Redundancy_mean | Redundancy_std | panel_b_rho | panel_b_p | low_score_red_median | high_score_red_median | panel_c_rho | panel_d_rho |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| proxy_tailmerge1500_floor50 | 0.050 | 3395 | 58 | 18.708 | 3879.167 | 345.151 | 126.793 | 41.845 | 33.389 | 10.643 | 30.597 | 2.599 | -0.100 | 0.000 | 32.549 | 31.190 | 0.057 | -0.256 |
| proxy_tailmerge1600_floor50 | 0.050 | 3392 | 58 | 18.700 | 3882.598 | 341.437 | 126.905 | 41.956 | 33.398 | 10.635 | 30.597 | 2.599 | -0.102 | 0.000 | 32.574 | 31.178 | 0.057 | -0.258 |
| proxy_tailmerge2000_floor50 | 0.051 | 3357 | 58 | 18.552 | 3923.077 | 327.637 | 128.228 | 43.951 | 33.498 | 10.579 | 30.597 | 2.599 | -0.109 | 0.000 | 32.612 | 31.189 | 0.056 | -0.253 |
| proxy_tailmerge1700_floor50 | 0.051 | 3383 | 58 | 18.657 | 3892.927 | 334.219 | 127.243 | 42.409 | 33.423 | 10.614 | 30.597 | 2.599 | -0.103 | 0.000 | 32.574 | 31.178 | 0.056 | -0.258 |
| proxy_tailmerge2000_floor60 | 0.053 | 3357 | 94 | 18.552 | 3923.077 | 327.637 | 128.459 | 43.567 | 33.215 | 9.601 | 30.547 | 2.563 | -0.109 | 0.000 | 32.612 | 31.189 | 0.056 | -0.253 |
| proxy_tailmerge2000_floor80 | 0.057 | 3357 | 262 | 18.552 | 3923.077 | 327.637 | 129.413 | 42.295 | 32.509 | 7.951 | 30.336 | 2.442 | -0.112 | 0.000 | 32.612 | 31.189 | 0.054 | -0.249 |
| proxy_tailmerge2000_floor100 | 0.060 | 3357 | 676 | 18.552 | 3923.077 | 327.637 | 132.035 | 39.797 | 31.314 | 6.253 | 29.750 | 2.202 | -0.124 | 0.000 | 32.517 | 31.148 | 0.040 | -0.217 |
| glm4token_tailmerge1500_floor0 | 0.104 | 3395 | 0 | 18.708 | 3879.167 | 345.151 | 145.402 | 49.669 | 30.223 | 25.099 | 26.707 | 2.335 | -0.110 | 0.000 | 28.410 | 27.213 | 0.041 | -0.208 |
| glm4token_tailmerge2000_floor0 | 0.106 | 3357 | 0 | 18.552 | 3923.077 | 327.637 | 147.048 | 51.969 | 30.325 | 25.197 | 26.707 | 2.335 | -0.120 | 0.000 | 28.450 | 27.212 | 0.040 | -0.205 |
| raw_proxy | 0.108 | 3462 | 0 | 19.034 | 3804.093 | 528.670 | 124.059 | 40.395 | 34.242 | 26.118 | 30.659 | 2.649 | -0.087 | 0.000 | 32.431 | 31.283 | 0.057 | -0.252 |

## 最佳候选 vs 原文

| metric | mean | paper_mean | std | paper_std | median | paper_median | p75 | paper_p75 |
|---|---|---|---|---|---|---|---|---|
| Chunk_num | 18.708 | 18.191 | 5.526 | 6.983 | 18.000 | 16.000 | 23.000 | 22.000 |
| Text_len | 3879.167 | 3866.817 | 345.151 | 343.868 | 3969.000 | 3954.000 | 3989.000 | 3985.000 |
| Summary_len | 126.793 | 132.678 | 41.845 | 39.683 | 122.000 | 130.000 | 142.000 | 158.000 |
| Redundancy_chunk | 33.389 | 32.176 | 10.643 | 11.730 | 31.968 | 29.739 | 37.187 | 37.037 |
| lnN_tech | 11.036 | 10.962 | 0.375 | 0.350 | 11.055 | 10.910 | 11.268 | 11.185 |
| Redundancy | 30.597 | 29.074 | 2.599 | 2.630 | 30.801 | 28.910 | 32.230 | 30.795 |

## 输出文件

- merged chunk metrics：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_glm200_merged_20260708/chunk_metrics_glm4_cot_v3b_len132_tight_20260708.csv`
- no-summary review CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_glm200_merged_20260708/chunk_metrics_glm4_cot_v3b_len132_tight_no_summary_text_20260708.csv`
- candidate summary：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm200_tailmerge_floor_candidates_20260708/candidate_summary_20260708.csv`
- best chunk：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm200_tailmerge_floor_candidates_20260708/proxy_tailmerge1500_floor50_chunk_metrics_20260708.csv`
- best firm：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm200_tailmerge_floor_candidates_20260708/proxy_tailmerge1500_floor50_firm_metrics_20260708.csv`
