# Candidate566 X Universe After First-Batch Backfill

日期：2026-07-07

## 结论

- 已将 full543 主口径 X 与首批 25 家 `dewrap_join + GLM tokenizer` 主口径 X 合并。
- 已剔除 `688688`、`688717` 这两家不在 CSMAR 2019-2023 科创板已上市 IPO universe 内的记录。
- 合并后标准 IPO 候选 X 为 `566` 家、`9083` 个 chunk。
- CSMAR 2019-2023 STAR IPO universe 为 567 家；当前候选 X 只剩 `688287` 未纳入，且它是转板上市报告书，不是标准 IPO 招股说明书。
- 原文 Table 1 为 552 家；因此即使排除 `688287` 后，仍需要解释约 `14` 家额外排除规则。
- 当前 chunk 数比原文多 `400` 个；这与 firm N 从 552 增至 566 一致，说明下一步不是再调 tokenizer，而是找原文样本筛选制度。

## Source Runs

| source_run | firm_n |
| --- | --- |
| first_batch25 | 25 |
| full543 | 541 |

## CSMAR Universe Crosswalk

| list_year_csmar | candidate_status | firm_n |
| --- | --- | --- |
| 2019 | in_candidate_x | 70 |
| 2020 | in_candidate_x | 144 |
| 2021 | in_candidate_x | 162 |
| 2022 | in_candidate_x | 123 |
| 2022 | transfer_listing_not_standard_ipo | 1 |
| 2023 | in_candidate_x | 67 |

缺失/特殊样本：

| code | sec_name_csmar | list_date_csmar | prospectus_publish_date_csmar | candidate_status |
| --- | --- | --- | --- | --- |
| 688287 | 观典防务 | 2022-05-25 | 2022-05-24 | transfer_listing_not_standard_ipo |

## Table 1 Measurement 对照

| scope | metric | current_N | paper_N | N_gap | current_mean | paper_mean | mean_gap | current_median | paper_median | current_p25 | current_p75 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chunk | Chunk_num | 9083 | 8683 | 400 | 17.504 | 18.191 | -0.687 | 17.000 | 16.000 | 14.000 | 20.000 |
| chunk | Text_len | 9083 | 8683 | 400 | 3794.009 | 3866.817 | -72.808 | 3967.000 | 3954.000 | 3885.000 | 3987.000 |
| chunk | Summary_len_proxy | 9083 | 8683 | 400 | 130.580 | 132.678 | -2.098 | 131.000 | 130.000 | 113.000 | 149.000 |
| chunk | Redundancy_chunk_proxy | 9083 | 8683 | 400 | 30.551 | 32.176 | -1.625 | 29.390 | 29.739 | 25.609 | 34.053 |
| chunk | Summary_len_glm4 | 9083 | 8683 | 400 | 157.550 | 132.678 | 24.872 | 158.000 | 130.000 | 136.000 | 181.000 |
| chunk | Redundancy_chunk_glm4 | 9083 | 8683 | 400 | 25.462 | 32.176 | -6.714 | 24.366 | 29.739 | 21.056 | 28.436 |
| firm | lnN_tech | 566 | 552 | 14 | 10.967 | 10.962 | 0.005 | 10.981 | 10.910 | 10.775 | 11.173 |
| firm | Redundancy_proxy | 566 | 552 | 14 | 29.053 | 29.074 | -0.021 | 28.847 | 28.910 | 27.607 | 30.604 |
| firm | Redundancy_glm4 | 566 | 552 | 14 | 24.123 | 29.074 | -4.951 | 24.009 | 28.910 | 22.775 | 25.339 |

## Panel B/C/D 快速检验

| measure | B_rho | B_p | low_median_by_score_median | high_median_by_score_median | low_lt2_median | high_ge2_median | C_cluster_coef | C_cluster_p | D_cluster_coef | D_cluster_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| proxy denominator | -0.4258 | 0.0000 | 31.7381 | 27.4214 | 35.3363 | 28.0352 | 0.1319 | 0.0000 | -0.1118 | 0.0000 |
| GLM4 denominator | -0.4332 | 0.0000 | 26.3754 | 22.6433 | 29.6791 | 23.1395 | 0.0905 | 0.0000 | -0.0878 | 0.0000 |

## 判断

1. X 的测度机制没有被首批25家破坏：`Redundancy_chunk_proxy`、Panel B、Panel D 都保持在合理区间。
2. 合并后的 N=566 与原文 N=552 仍差 14 家；这已经是样本制度问题，不是 LLM 摘要或 tokenizer 问题。
3. 下一步应优先查原文是否排除了转板、特殊上市、未完整一年后数据、发行失败/撤回后重启、或 Y/controls 缺失导致 Table 1 实际样本口径收缩。
4. Table 2 不能直接用旧 543 master 续跑，因为新增25家没有被拼入 Y/controls master；需要用底层 CSMAR 数据重建 566 家 master。

## 输出文件

- firm metrics：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm4_dewrap_join_candidate566_20260707/firm_metrics_candidate566_20260707.csv`
- chunk metrics：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm4_dewrap_join_candidate566_20260707/chunk_metrics_candidate566_20260707.csv`
- crosswalk：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm4_dewrap_join_candidate566_20260707/candidate566_vs_csmar_universe_crosswalk_20260707.csv`
- descriptives：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm4_dewrap_join_candidate566_20260707/candidate566_descriptives_vs_original_20260707.csv`
- panel tests：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm4_dewrap_join_candidate566_20260707/candidate566_panel_tests_20260707.csv`
