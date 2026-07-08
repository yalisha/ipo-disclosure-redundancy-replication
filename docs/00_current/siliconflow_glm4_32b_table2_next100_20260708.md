# SiliconFlow GLM-4-32B Table2 next100 测度与候选口径

日期：2026-07-08

## 结论

- 本轮新增 100 家已跑完并合并：chunk=1756，firm=100。
- 原始 GLM proxy：Summary_len mean=123.664，Redundancy_chunk mean=33.853。
- next100 最接近原文 Table 1 的候选是 `proxy_tailmerge1700_floor50`：Summary_len mean=126.881，Redundancy_chunk mean=33.452，企业层 Redundancy mean=30.776。
- GLM100 最佳候选为 `proxy_tailmerge1700_floor50`，Summary_len mean=127.615，Redundancy_chunk mean=33.392。
- 这批 next100 的主要用途不是单独定版，而是和 GLM100 合成 GLM200 后看口径稳定性与 Table 2 方向。

## 候选口径排序

| name | loss_all | chunk_n | floor_applied_n | Chunk_num_mean | Text_len_mean | Text_len_std | Summary_len_mean | Summary_len_std | Redundancy_chunk_mean | Redundancy_chunk_std | Redundancy_mean | Redundancy_std | panel_b_rho | panel_b_p | panel_c_rho | panel_d_rho |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| proxy_tailmerge1700_floor50 | 0.060 | 1715 | 31 | 18.467 | 3888.071 | 335.065 | 126.881 | 42.962 | 33.452 | 10.494 | 30.776 | 2.483 | -0.093 | 0.000 | 0.035 | -0.254 |
| proxy_tailmerge1500_floor50 | 0.060 | 1720 | 31 | 18.521 | 3876.768 | 344.050 | 126.512 | 42.537 | 33.424 | 10.515 | 30.776 | 2.483 | -0.088 | 0.000 | 0.036 | -0.253 |
| proxy_tailmerge1600_floor50 | 0.061 | 1719 | 31 | 18.513 | 3879.023 | 341.378 | 126.586 | 42.617 | 33.429 | 10.508 | 30.776 | 2.483 | -0.090 | 0.000 | 0.036 | -0.254 |
| proxy_tailmerge2000_floor50 | 0.062 | 1702 | 31 | 18.360 | 3917.768 | 327.888 | 127.850 | 44.267 | 33.517 | 10.460 | 30.776 | 2.483 | -0.097 | 0.000 | 0.038 | -0.248 |
| proxy_tailmerge2000_floor60 | 0.065 | 1702 | 50 | 18.360 | 3917.768 | 327.888 | 128.086 | 43.879 | 33.231 | 9.476 | 30.720 | 2.443 | -0.097 | 0.000 | 0.038 | -0.248 |
| proxy_tailmerge2000_floor80 | 0.067 | 1702 | 139 | 18.360 | 3917.768 | 327.888 | 129.071 | 42.582 | 32.511 | 7.810 | 30.496 | 2.335 | -0.102 | 0.000 | 0.036 | -0.243 |
| proxy_tailmerge2000_floor100 | 0.071 | 1702 | 339 | 18.360 | 3917.768 | 327.888 | 131.659 | 40.151 | 31.337 | 6.159 | 29.909 | 2.100 | -0.121 | 0.000 | 0.021 | -0.203 |
| glm4token_tailmerge1500_floor0 | 0.081 | 1720 | 0 | 18.521 | 3876.768 | 344.050 | 145.396 | 50.203 | 29.803 | 13.863 | 26.817 | 2.189 | -0.101 | 0.000 | 0.008 | -0.206 |
| glm4token_tailmerge2000_floor0 | 0.084 | 1702 | 0 | 18.360 | 3917.768 | 327.888 | 146.934 | 52.082 | 29.886 | 13.867 | 26.817 | 2.189 | -0.110 | 0.000 | 0.010 | -0.201 |
| raw_proxy | 0.089 | 1756 | 0 | 18.858 | 3797.290 | 536.289 | 123.664 | 41.025 | 33.853 | 15.833 | 30.837 | 2.525 | -0.075 | 0.002 | 0.036 | -0.257 |

## 最佳候选 vs 原文

| metric | mean | paper_mean | std | paper_std | median | paper_median | p75 | paper_p75 |
|---|---|---|---|---|---|---|---|---|
| Chunk_num | 18.467 | 18.191 | 4.733 | 6.983 | 18.000 | 16.000 | 22.000 | 22.000 |
| Text_len | 3888.071 | 3866.817 | 335.065 | 343.868 | 3969.000 | 3954.000 | 3988.000 | 3985.000 |
| Summary_len | 126.881 | 132.678 | 42.962 | 39.683 | 122.000 | 130.000 | 142.000 | 158.000 |
| Redundancy_chunk | 33.452 | 32.176 | 10.494 | 11.730 | 32.081 | 29.739 | 37.037 | 37.037 |
| lnN_tech | 11.068 | 10.962 | 0.290 | 0.350 | 11.078 | 10.910 | 11.282 | 11.185 |
| Redundancy | 30.776 | 29.074 | 2.483 | 2.630 | 30.694 | 28.910 | 32.113 | 30.795 |

## 输出文件

- merged run：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_merged_20260708`
- chunk metrics：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_merged_20260708/chunk_metrics_glm4_cot_v3b_len132_tight_20260708.csv`
- candidates：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm_next100_tailmerge_floor_candidates_20260708`
- candidate summary：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm_next100_tailmerge_floor_candidates_20260708/candidate_summary_20260708.csv`
- best chunk：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm_next100_tailmerge_floor_candidates_20260708/proxy_tailmerge1700_floor50_chunk_metrics_20260708.csv`
- best firm：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm_next100_tailmerge_floor_candidates_20260708/proxy_tailmerge1700_floor50_firm_metrics_20260708.csv`
