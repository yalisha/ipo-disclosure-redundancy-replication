# SiliconFlow GLM-4-32B Table2 Next50 Shard3

日期：2026-07-07

## 结论

- 使用模型：`THUDM/GLM-4-32B-0414`，接口：SiliconFlow OpenAI-compatible chat completions。
- API key 未写入脚本、结果或文档；本目录只保存模型返回文本和聚合指标。
- 样本复用原 `glm4_dewrap_join_glm_next50_table2_shard3_20260707` 的 16 家、281 个 chunk。
- GLM 生成的 `Summary_len_proxy` mean=124.911，source Codex mean=132.107，原文 mean=132.678。
- GLM 生成的 `Redundancy_chunk_proxy` mean=33.297，原文 mean=32.176。
- GLM 的 `Relevant_score` mean=1.927，source Codex mean=2.315。

## 描述统计

| metric | glm_mean | codex_mean | paper_mean | glm_median | codex_median |
| --- | --- | --- | --- | --- | --- |
| Summary_len_proxy | 124.911 | 132.107 | 132.678 | 121.000 | 131.000 |
| Redundancy_chunk_proxy | 33.297 | 30.388 | 32.176 | 32.066 |  |
| Relevant_score | 1.927 | 2.315 |  | 1.744 | 2.346 |

## 企业层

| sec_code | sec_name | original_length_units | summary_length_units | redundancy |
| --- | --- | --- | --- | --- |
| 688321 | 微芯生物 | 74712 | 2260 | 33.058 |
| 688030 | 山石网科 | 84483 | 2573 | 32.834 |
| 688007 | 光峰科技 | 63227 | 1935 | 32.675 |
| 688199 | 久日新材 | 88867 | 2746 | 32.362 |
| 688028 | 沃尔德 | 63160 | 1956 | 32.290 |
| 688333 | 铂力特 | 93830 | 2943 | 31.882 |
| 688138 | 清溢光电 | 50045 | 1574 | 31.795 |
| 688369 | 致远互联 | 54337 | 1731 | 31.391 |
| 688101 | 三达膜 | 73296 | 2365 | 30.992 |
| 688021 | 奥福环保 | 74095 | 2397 | 30.912 |
| 688003 | 天准科技 | 67095 | 2268 | 29.583 |
| 688066 | 航天宏图 | 60358 | 2072 | 29.130 |
| 688019 | 安集科技 | 44881 | 1541 | 29.125 |
| 688108 | 赛诺医疗 | 80927 | 2795 | 28.954 |
| 688010 | 福光股份 | 51938 | 1869 | 27.789 |
| 688015 | 交控科技 | 56851 | 2075 | 27.398 |

## API Calls

- calls：`281`
- total tokens：`1444546`
- prompt tokens：`1381296`
- completion tokens：`63250`

## 输出

- chunk CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next50_shard3_20260707/ipo_redundancy_chunk_with_llm_cot_v3b_len132_tight.csv`
- firm CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next50_shard3_20260707/ipo_redundancy_firm_level_cot_v3b_len132_tight.csv`
- comparison：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next50_shard3_20260707/summary_comparison_vs_source_20260707.csv`
- call log：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next50_shard3_20260707/siliconflow_call_log_20260707.csv`
