# SiliconFlow GLM-4-32B Table2 next100 after GLM200 测度与候选口径

日期：2026-07-08

## 结论

- 本轮新增第三个 100 家已跑完并合并：chunk=1655，firm=100。
- 原始 GLM proxy：Summary_len mean=123.556，Redundancy_chunk mean=33.525。
- 本批最接近原文 Table 1 的候选是 `proxy_tailmerge1500_floor50`：Summary_len mean=126.927，Redundancy_chunk mean=33.525，企业层 Redundancy mean=30.776。
- GLM200 最佳候选为 `proxy_tailmerge1500_floor50`，Summary_len mean=126.793，Redundancy_chunk mean=33.389。
- QC：5 个 shard 均完成并验收，jsonl=1655/1655，firm=100；其中 `688510_1208870807_glm4_dewrap_join_chunk_0015` 与 `688316_1209353886_glm4_dewrap_join_chunk_0014` 的 GLM 返回空摘要，已做透明兜底摘要以避免 0 分母，评分字段保持 GLM 原值不改。
- 这批单独结果主要服务于 GLM300 合并 gate，不单独定版。

## 候选口径排序

| name | loss_all | chunk_n | floor_applied_n | Chunk_num_mean | Text_len_mean | Text_len_std | Summary_len_mean | Summary_len_std | Redundancy_chunk_mean | Redundancy_chunk_std | Redundancy_mean | Redundancy_std | panel_b_rho | panel_b_p | panel_c_rho | panel_d_rho |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| proxy_tailmerge1500_floor50 | 0.076 | 1613 | 19 | 17.232 | 3884.487 | 333.405 | 126.927 | 53.279 | 33.525 | 10.371 | 30.776 | 2.553 | -0.058 | 0.021 | 0.060 | -0.232 |
| proxy_tailmerge2000_floor50 | 0.076 | 1602 | 19 | 17.125 | 3911.159 | 322.004 | 127.798 | 54.314 | 33.592 | 10.326 | 30.776 | 2.553 | -0.062 | 0.014 | 0.063 | -0.228 |
| proxy_tailmerge1600_floor50 | 0.077 | 1611 | 19 | 17.214 | 3889.309 | 327.953 | 127.084 | 53.448 | 33.537 | 10.359 | 30.776 | 2.553 | -0.058 | 0.021 | 0.061 | -0.232 |
| proxy_tailmerge1700_floor50 | 0.077 | 1611 | 19 | 17.214 | 3889.309 | 327.953 | 127.084 | 53.448 | 33.537 | 10.359 | 30.776 | 2.553 | -0.058 | 0.021 | 0.061 | -0.232 |
| proxy_tailmerge2000_floor60 | 0.078 | 1602 | 35 | 17.125 | 3911.159 | 322.004 | 127.981 | 54.070 | 33.371 | 9.563 | 30.733 | 2.531 | -0.063 | 0.013 | 0.063 | -0.228 |
| proxy_tailmerge2000_floor80 | 0.081 | 1602 | 114 | 17.125 | 3911.159 | 322.004 | 128.889 | 53.109 | 32.701 | 8.016 | 30.524 | 2.447 | -0.068 | 0.007 | 0.062 | -0.229 |
| proxy_tailmerge2000_floor100 | 0.082 | 1602 | 325 | 17.125 | 3911.159 | 322.004 | 131.546 | 51.147 | 31.492 | 6.345 | 29.915 | 2.296 | -0.079 | 0.002 | 0.063 | -0.212 |
| glm4token_tailmerge1500_floor0 | 0.092 | 1613 | 0 | 17.232 | 3884.487 | 333.405 | 146.596 | 65.393 | 29.550 | 12.382 | 26.686 | 2.350 | -0.081 | 0.001 | 0.054 | -0.187 |
| glm4token_tailmerge2000_floor0 | 0.092 | 1602 | 0 | 17.125 | 3911.159 | 322.004 | 147.603 | 66.482 | 29.611 | 12.372 | 26.686 | 2.350 | -0.085 | 0.001 | 0.057 | -0.182 |
| raw_proxy | 0.099 | 1655 | 0 | 17.633 | 3785.908 | 584.891 | 123.556 | 51.464 | 33.525 | 13.828 | 30.814 | 2.583 | -0.045 | 0.068 | 0.062 | -0.234 |

## 最佳候选 vs 原文

| metric | mean | paper_mean | std | paper_std | median | paper_median | p75 | paper_p75 |
|---|---|---|---|---|---|---|---|---|
| Chunk_num | 17.232 | 18.191 | 4.498 | 6.983 | 17.000 | 16.000 | 19.000 | 22.000 |
| Text_len | 3884.487 | 3866.817 | 333.405 | 343.868 | 3970.000 | 3954.000 | 3989.000 | 3985.000 |
| Summary_len | 126.927 | 132.678 | 53.279 | 39.683 | 121.000 | 130.000 | 141.000 | 158.000 |
| Redundancy_chunk | 33.525 | 32.176 | 10.371 | 11.730 | 32.071 | 29.739 | 37.750 | 37.037 |
| lnN_tech | 11.012 | 10.962 | 0.257 | 0.350 | 10.996 | 10.910 | 11.195 | 11.185 |
| Redundancy | 30.776 | 29.074 | 2.553 | 2.630 | 31.152 | 28.910 | 32.681 | 30.795 |

## 输出文件

- merged run：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_after200_merged_20260708`
- chunk metrics：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_after200_merged_20260708/chunk_metrics_glm4_cot_v3b_len132_tight_20260708.csv`
- candidates：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm_next100_after200_tailmerge_floor_candidates_20260708`
- candidate summary：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm_next100_after200_tailmerge_floor_candidates_20260708/candidate_summary_20260708.csv`
- best chunk：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm_next100_after200_tailmerge_floor_candidates_20260708/proxy_tailmerge1500_floor50_chunk_metrics_20260708.csv`
- best firm：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm_next100_after200_tailmerge_floor_candidates_20260708/proxy_tailmerge1500_floor50_firm_metrics_20260708.csv`
