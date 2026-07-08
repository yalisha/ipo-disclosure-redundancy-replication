# SiliconFlow GLM-4-32B Table2 next100 shard3

日期：2026-07-08

## 结论

- 使用模型：`THUDM/GLM-4-32B-0414`，接口：SiliconFlow OpenAI-compatible chat completions。
- API key 未写入脚本、结果或文档；本目录只保存模型返回文本和聚合指标。
- 样本复用原 `glm4_dewrap_join_glm_next100_table2_shard3_20260708` 的 20 家、398 个 chunk。
- GLM 生成的 `Summary_len_proxy` mean=128.553，source Codex mean=133.219，原文 mean=132.678。
- GLM 生成的 `Redundancy_chunk_proxy` mean=32.807，原文 mean=32.176。
- GLM 的 `Relevant_score` mean=2.089，source Codex mean=2.381。

## 描述统计

| metric | glm_mean | codex_mean | paper_mean | glm_median | codex_median |
| --- | --- | --- | --- | --- | --- |
| Summary_len_proxy | 128.553 | 133.219 | 132.678 | 123.000 | 133.000 |
| Redundancy_chunk_proxy | 32.807 | 29.808 | 32.176 | 31.133 |  |
| Relevant_score | 2.089 | 2.381 |  | 1.815 | 2.373 |

## 企业层

| sec_code | sec_name | original_length_units | summary_length_units | redundancy |
| --- | --- | --- | --- | --- |
| 688558 | 国盛智科 | 82662 | 2542 | 32.518 |
| 688500 | 慧辰资讯 | 61305 | 1902 | 32.232 |
| 688309 | 恒誉环保 | 99301 | 3089 | 32.147 |
| 688277 | 天智航 | 59593 | 1859 | 32.056 |
| 688528 | 秦川物联 | 101425 | 3199 | 31.705 |
| 688027 | 国盾量子 | 78084 | 2468 | 31.639 |
| 688180 | 君实生物 | 89313 | 2850 | 31.338 |
| 688555 | 泽达易盛 | 75616 | 2435 | 31.054 |
| 688599 | 天合光能 | 107849 | 3557 | 30.320 |
| 688518 | 联赢激光 | 96809 | 3195 | 30.300 |
| 688060 | 云涌科技 | 45219 | 1497 | 30.206 |
| 688505 | 复旦张江 | 69881 | 2330 | 29.992 |
| 688360 | 德马科技 | 85035 | 2871 | 29.619 |
| 688165 | 埃夫特 | 60303 | 2040 | 29.560 |
| 688312 | 燕麦科技 | 44998 | 1546 | 29.106 |
| 688377 | 迪威尔 | 79213 | 2832 | 27.971 |
| 688004 | 博汇科技 | 68717 | 2473 | 27.787 |
| 688106 | 金宏气体 | 68111 | 2464 | 27.642 |
| 688600 | 皖仪科技 | 63297 | 2344 | 27.004 |
| 688568 | 中科星图 | 73917 | 3671 | 20.135 |

## API Calls

- calls：`398`
- total tokens：`2025280`
- prompt tokens：`1934559`
- completion tokens：`90721`

## 输出

- chunk CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_shard3_20260708/ipo_redundancy_chunk_with_llm_cot_v3b_len132_tight.csv`
- firm CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_shard3_20260708/ipo_redundancy_firm_level_cot_v3b_len132_tight.csv`
- comparison：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_shard3_20260708/summary_comparison_vs_source_20260707.csv`
- call log：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_shard3_20260708/siliconflow_call_log_20260707.csv`
