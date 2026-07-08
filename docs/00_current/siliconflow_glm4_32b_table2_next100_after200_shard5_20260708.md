# SiliconFlow GLM-4-32B Table2 next100 after GLM200 shard5

日期：2026-07-08

## 结论

- 使用模型：`THUDM/GLM-4-32B-0414`，接口：SiliconFlow OpenAI-compatible chat completions。
- API key 未写入脚本、结果或文档；本目录只保存模型返回文本和聚合指标。
- 样本复用原 `glm4_dewrap_join_glm_next100_after200_table2_shard5_20260708` 的 20 家、319 个 chunk。
- GLM 生成的 `Summary_len_proxy` mean=122.508，source Codex mean=125.661，原文 mean=132.678。
- GLM 生成的 `Redundancy_chunk_proxy` mean=33.001，原文 mean=32.176。
- GLM 的 `Relevant_score` mean=2.109，source Codex mean=2.358。

## 描述统计

| metric | glm_mean | codex_mean | paper_mean | glm_median | codex_median |
| --- | --- | --- | --- | --- | --- |
| Summary_len_proxy | 122.508 | 125.661 | 132.678 | 121.000 | 128.000 |
| Redundancy_chunk_proxy | 33.001 | 31.287 | 32.176 | 31.754 |  |
| Relevant_score | 2.109 | 2.358 |  | 1.849 | 2.361 |

## 企业层

| sec_code | sec_name | original_length_units | summary_length_units | redundancy |
| --- | --- | --- | --- | --- |
| 688217 | 睿昂基因 | 59619 | 1745 | 34.166 |
| 688201 | 信安世纪 | 61578 | 1853 | 33.232 |
| 688682 | 霍莱沃 | 43902 | 1322 | 33.209 |
| 688395 | 正弦电气 | 38993 | 1187 | 32.850 |
| 688575 | 亚辉龙 | 97319 | 2967 | 32.800 |
| 688655 | 迅捷兴 | 65133 | 2025 | 32.164 |
| 688613 | 奥精医疗 | 61488 | 1915 | 32.109 |
| 688533 | 上声电子 | 45072 | 1408 | 32.011 |
| 688097 | 博众精工 | 76433 | 2401 | 31.834 |
| 688355 | 明志科技 | 68013 | 2146 | 31.693 |
| 688076 | 诺泰生物 | 102800 | 3273 | 31.408 |
| 688639 | 华恒生物 | 51084 | 1686 | 30.299 |
| 688565 | 力源科技 | 51715 | 1725 | 29.980 |
| 688663 | 新风光 | 50330 | 1701 | 29.588 |
| 688359 | 三孚新科 | 55970 | 1901 | 29.442 |
| 688383 | 新益昌 | 56674 | 1933 | 29.319 |
| 688660 | 电气风电 | 80215 | 2746 | 29.212 |
| 688314 | 康拓医疗 | 45003 | 1603 | 28.074 |
| 688113 | 联测科技 | 57477 | 2148 | 26.758 |
| 688323 | 瑞华泰 | 36121 | 1395 | 25.893 |

## API Calls

- calls：`319`
- total tokens：`1616113`
- prompt tokens：`1544691`
- completion tokens：`71422`

## 输出

- chunk CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_after200_shard5_20260708/ipo_redundancy_chunk_with_llm_cot_v3b_len132_tight.csv`
- firm CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_after200_shard5_20260708/ipo_redundancy_firm_level_cot_v3b_len132_tight.csv`
- comparison：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_after200_shard5_20260708/summary_comparison_vs_source_20260707.csv`
- call log：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_after200_shard5_20260708/siliconflow_call_log_20260707.csv`
