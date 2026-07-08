# SiliconFlow GLM-4-32B Table2 next100 shard2

日期：2026-07-08

## 结论

- 使用模型：`THUDM/GLM-4-32B-0414`，接口：SiliconFlow OpenAI-compatible chat completions。
- API key 未写入脚本、结果或文档；本目录只保存模型返回文本和聚合指标。
- 样本复用原 `glm4_dewrap_join_glm_next100_table2_shard2_20260708` 的 20 家、373 个 chunk。
- GLM 生成的 `Summary_len_proxy` mean=122.169，source Codex mean=131.094，原文 mean=132.678。
- GLM 生成的 `Redundancy_chunk_proxy` mean=34.873，原文 mean=32.176。
- GLM 的 `Relevant_score` mean=1.983，source Codex mean=2.300。

## 描述统计

| metric | glm_mean | codex_mean | paper_mean | glm_median | codex_median |
| --- | --- | --- | --- | --- | --- |
| Summary_len_proxy | 122.169 | 131.094 | 132.678 | 122.000 | 131.000 |
| Redundancy_chunk_proxy | 34.873 | 30.665 | 32.176 | 31.904 |  |
| Relevant_score | 1.983 | 2.300 |  | 1.759 | 2.346 |

## 企业层

| sec_code | sec_name | original_length_units | summary_length_units | redundancy |
| --- | --- | --- | --- | --- |
| 688365 | 光云科技 | 49213 | 1277 | 38.538 |
| 688516 | 奥特维 | 103988 | 2962 | 35.107 |
| 688051 | 佳华科技 | 75270 | 2303 | 32.683 |
| 688228 | 开普云 | 91280 | 2839 | 32.152 |
| 688566 | 吉贝尔 | 97249 | 3032 | 32.074 |
| 688169 | 石头科技 | 67275 | 2105 | 31.960 |
| 688085 | 三友医疗 | 91293 | 2857 | 31.954 |
| 688096 | 京源环保 | 75301 | 2362 | 31.880 |
| 688598 | 金博股份 | 44369 | 1406 | 31.557 |
| 688222 | 成都先导 | 55842 | 1772 | 31.514 |
| 688189 | 南新制药 | 90334 | 2871 | 31.464 |
| 688177 | 百奥泰 | 91507 | 2909 | 31.457 |
| 688233 | 神工股份 | 33064 | 1076 | 30.729 |
| 688318 | 财富趋势 | 61702 | 2041 | 30.231 |
| 688466 | 金科环境 | 58052 | 1945 | 29.847 |
| 688090 | 瑞松科技 | 90269 | 3084 | 29.270 |
| 688126 | 沪硅产业 | 46090 | 1593 | 28.933 |
| 688396 | 华润微 | 54270 | 1915 | 28.339 |
| 688086 | 紫晶存储 | 99312 | 3523 | 28.190 |
| 688200 | 华峰测控 | 46571 | 1697 | 27.443 |

## API Calls

- calls：`373`
- total tokens：`1902069`
- prompt tokens：`1819378`
- completion tokens：`82691`

## 输出

- chunk CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_shard2_20260708/ipo_redundancy_chunk_with_llm_cot_v3b_len132_tight.csv`
- firm CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_shard2_20260708/ipo_redundancy_firm_level_cot_v3b_len132_tight.csv`
- comparison：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_shard2_20260708/summary_comparison_vs_source_20260707.csv`
- call log：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_shard2_20260708/siliconflow_call_log_20260707.csv`
