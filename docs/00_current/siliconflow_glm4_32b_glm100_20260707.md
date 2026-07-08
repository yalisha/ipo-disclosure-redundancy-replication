# SiliconFlow GLM-4-32B GLM100 合并测度诊断

日期：2026-07-07

## 结论

- 合并样本：firm=100，chunk=1706，pilot50=50，table2_next50=50。
- 原始 GLM proxy 口径：Summary_len mean=124.465，Redundancy_chunk mean=34.643。
- GLM100 最接近原文 Table 1 的候选是 `proxy_tailmerge1700_floor50`：Summary_len mean=127.615，Redundancy_chunk mean=33.392，企业层 Redundancy mean=30.418。
- Panel B 方向仍成立但很弱：rho=-0.114, p=0.000；这不是效度最终通过，只说明低相关评分与高冗余的机械关系未消失。
- 因此目前最清楚的判断是：GLM 摘要显著改善 Table 1 描述统计贴近度，但必须接 Table 2 才能裁决能否复刻论文主效应。

## 候选口径排序

| name | loss_all | chunk_n | floor_applied_n | Chunk_num_mean | Text_len_mean | Text_len_std | Summary_len_mean | Summary_len_std | Redundancy_chunk_mean | Redundancy_chunk_std | Redundancy_mean | Redundancy_std | panel_b_rho | panel_b_p | panel_c_rho | panel_d_rho |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| proxy_tailmerge1700_floor50 | 0.051 | 1668 | 27 | 18.851 | 3897.920 | 333.374 | 127.615 | 41.842 | 33.392 | 10.738 | 30.418 | 2.710 | -0.114 | 0.000 | 0.075 | -0.262 |
| proxy_tailmerge2000_floor50 | 0.051 | 1655 | 27 | 18.750 | 3928.538 | 327.387 | 128.618 | 43.635 | 33.478 | 10.703 | 30.418 | 2.710 | -0.121 | 0.000 | 0.073 | -0.259 |
| proxy_tailmerge1500_floor50 | 0.052 | 1675 | 27 | 18.901 | 3881.630 | 346.363 | 127.082 | 41.133 | 33.354 | 10.775 | 30.418 | 2.710 | -0.112 | 0.000 | 0.076 | -0.259 |
| proxy_tailmerge1600_floor50 | 0.052 | 1673 | 27 | 18.892 | 3886.270 | 341.561 | 127.234 | 41.275 | 33.366 | 10.767 | 30.418 | 2.710 | -0.114 | 0.000 | 0.076 | -0.262 |
| proxy_tailmerge2000_floor60 | 0.053 | 1655 | 44 | 18.750 | 3928.538 | 327.387 | 128.843 | 43.254 | 33.198 | 9.730 | 30.375 | 2.679 | -0.122 | 0.000 | 0.073 | -0.259 |
| proxy_tailmerge2000_floor80 | 0.055 | 1655 | 123 | 18.750 | 3928.538 | 327.387 | 129.766 | 42.008 | 32.508 | 8.095 | 30.176 | 2.547 | -0.123 | 0.000 | 0.070 | -0.255 |
| proxy_tailmerge2000_floor100 | 0.059 | 1655 | 337 | 18.750 | 3928.538 | 327.387 | 132.422 | 39.439 | 31.289 | 6.349 | 29.591 | 2.300 | -0.128 | 0.000 | 0.058 | -0.231 |
| glm4token_tailmerge1500_floor0 | 0.127 | 1675 | 0 | 18.901 | 3881.630 | 346.363 | 145.409 | 49.129 | 30.655 | 32.856 | 26.598 | 2.479 | -0.120 | 0.000 | 0.071 | -0.212 |

## 最佳候选 vs 原文

| metric | mean | paper_mean | std | paper_std | median | paper_median | p75 | paper_p75 |
|---|---|---|---|---|---|---|---|---|
| Chunk_num | 18.851 | 18.191 | 6.253 | 6.983 | 18.000 | 16.000 | 23.000 | 22.000 |
| Text_len | 3897.920 | 3866.817 | 333.374 | 343.868 | 3971.000 | 3954.000 | 3989.250 | 3985.000 |
| Summary_len | 127.615 | 132.678 | 41.842 | 39.683 | 122.000 | 130.000 | 144.000 | 158.000 |
| Redundancy_chunk | 33.392 | 32.176 | 10.738 | 11.730 | 31.916 | 29.739 | 37.299 | 37.037 |
| lnN_tech | 11.004 | 10.962 | 0.443 | 0.350 | 11.043 | 10.910 | 11.233 | 11.185 |
| Redundancy | 30.418 | 29.074 | 2.710 | 2.630 | 30.888 | 28.910 | 32.274 | 30.795 |

## 输出文件

- merged chunk metrics：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_glm100_merged_20260707/chunk_metrics_glm4_cot_v3b_len132_tight_20260707.csv`
- no-summary review CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_glm100_merged_20260707/chunk_metrics_glm4_cot_v3b_len132_tight_no_summary_text_20260707.csv`
- candidate summary：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm100_tailmerge_floor_candidates_20260707/candidate_summary_20260707.csv`
- best chunk：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm100_tailmerge_floor_candidates_20260707/proxy_tailmerge1700_floor50_chunk_metrics_20260707.csv`
- best firm：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm100_tailmerge_floor_candidates_20260707/proxy_tailmerge1700_floor50_firm_metrics_20260707.csv`
