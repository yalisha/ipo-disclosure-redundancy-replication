# SiliconFlow GLM-4-32B Table2 next100 shard1

日期：2026-07-08

## 结论

- 使用模型：`THUDM/GLM-4-32B-0414`，接口：SiliconFlow OpenAI-compatible chat completions。
- API key 未写入脚本、结果或文档；本目录只保存模型返回文本和聚合指标。
- 样本复用原 `glm4_dewrap_join_glm_next100_table2_shard1_20260708` 的 20 家、376 个 chunk。
- GLM 生成的 `Summary_len_proxy` mean=121.074，source Codex mean=132.444，原文 mean=132.678。
- GLM 生成的 `Redundancy_chunk_proxy` mean=34.480，原文 mean=32.176。
- GLM 的 `Relevant_score` mean=2.048，source Codex mean=2.372。

## 描述统计

| metric | glm_mean | codex_mean | paper_mean | glm_median | codex_median |
| --- | --- | --- | --- | --- | --- |
| Summary_len_proxy | 121.074 | 132.444 | 132.678 | 119.000 | 133.000 |
| Redundancy_chunk_proxy | 34.480 | 30.141 | 32.176 | 32.407 |  |
| Relevant_score | 2.048 | 2.372 |  | 1.746 | 2.409 |

## 企业层

| sec_code | sec_name | original_length_units | summary_length_units | redundancy |
| --- | --- | --- | --- | --- |
| 688186 | 广大特材 | 81237 | 2266 | 35.850 |
| 688268 | 华特气体 | 77316 | 2218 | 34.858 |
| 688399 | 硕世生物 | 87768 | 2554 | 34.365 |
| 688258 | 卓易信息 | 68451 | 1994 | 34.328 |
| 688357 | 建龙微纳 | 65810 | 1987 | 33.120 |
| 688100 | 威胜信息 | 87624 | 2683 | 32.659 |
| 688358 | 祥生医疗 | 61669 | 1937 | 31.837 |
| 688181 | 八亿时空 | 64297 | 2031 | 31.658 |
| 688089 | 嘉必优 | 62300 | 1998 | 31.181 |
| 688037 | 芯源微 | 47650 | 1534 | 31.063 |
| 688298 | 东方生物 | 88345 | 2855 | 30.944 |
| 688266 | 泽璟制药 | 99033 | 3222 | 30.736 |
| 688208 | 道通科技 | 52763 | 1735 | 30.411 |
| 688026 | 洁特生物 | 93604 | 3121 | 29.992 |
| 688398 | 赛特新材 | 58370 | 1952 | 29.903 |
| 688178 | 万德斯 | 57295 | 1920 | 29.841 |
| 688198 | 佰仁医疗 | 79244 | 2705 | 29.295 |
| 688039 | 当虹科技 | 56459 | 1951 | 28.938 |
| 688080 | 映翰通 | 56895 | 1977 | 28.778 |
| 688158 | 优刻得 | 81983 | 2884 | 28.427 |

## API Calls

- calls：`376`
- total tokens：`1911945`
- prompt tokens：`1828524`
- completion tokens：`83421`

## 输出

- chunk CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_shard1_20260708/ipo_redundancy_chunk_with_llm_cot_v3b_len132_tight.csv`
- firm CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_shard1_20260708/ipo_redundancy_firm_level_cot_v3b_len132_tight.csv`
- comparison：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_shard1_20260708/summary_comparison_vs_source_20260707.csv`
- call log：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_shard1_20260708/siliconflow_call_log_20260707.csv`
