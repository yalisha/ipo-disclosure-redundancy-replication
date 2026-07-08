# SiliconFlow GLM-4-32B Table2_remaining_to471_shard2

日期：2026-07-08

## 结论

- 使用模型：`THUDM/GLM-4-32B-0414`，接口：SiliconFlow OpenAI-compatible chat completions。
- API key 未写入脚本、结果或文档；本目录只保存模型返回文本和聚合指标。
- 样本复用原 `glm4_dewrap_join_glm_remaining_to471_table2_shard2_20260708` 的 31 家、511 个 chunk。
- GLM 生成的 `Summary_len_proxy` mean=123.143，source Codex mean=129.217，原文 mean=132.678。
- GLM 生成的 `Redundancy_chunk_proxy` mean=33.169，原文 mean=32.176。
- GLM 的 `Relevant_score` mean=2.099，source Codex mean=2.315。

## 描述统计

| metric | glm_mean | codex_mean | paper_mean | glm_median | codex_median |
| --- | --- | --- | --- | --- | --- |
| Summary_len_proxy | 123.143 | 129.217 | 132.678 | 121.000 | 130.000 |
| Redundancy_chunk_proxy | 33.169 | 30.716 | 32.176 | 31.563 |  |
| Relevant_score | 2.099 | 2.315 |  | 1.800 | 2.375 |

## 企业层

| sec_code | sec_name | original_length_units | summary_length_units | redundancy |
| --- | --- | --- | --- | --- |
| 688778 | 厦钨新能 | 60066 | 1653 | 36.338 |
| 688772 | 珠海冠宇 | 60577 | 1693 | 35.781 |
| 688733 | 壹石通 | 51941 | 1478 | 35.143 |
| 688280 | 精进电动 | 77977 | 2264 | 34.442 |
| 688121 | 卓然股份 | 61344 | 1822 | 33.668 |
| 688553 | 汇宇制药 | 68144 | 2024 | 33.668 |
| 688670 | 金迪克 | 51656 | 1571 | 32.881 |
| 688722 | 同益中 | 41559 | 1272 | 32.672 |
| 688779 | 长远锂科 | 63447 | 1952 | 32.504 |
| 688255 | 凯尔达 | 69224 | 2147 | 32.242 |
| 688739 | 成大生物 | 57085 | 1780 | 32.070 |
| 688511 | 天微电子 | 61599 | 1944 | 31.687 |
| 688071 | 华依科技 | 66704 | 2118 | 31.494 |
| 688776 | 国光电气 | 43503 | 1387 | 31.365 |
| 688737 | 中自科技 | 56941 | 1846 | 30.846 |
| 688697 | 纽威数控 | 54312 | 1784 | 30.444 |
| 688728 | 格科微 | 58918 | 1939 | 30.386 |
| 688187 | 时代电气 | 69863 | 2305 | 30.309 |
| 688148 | 芳源股份 | 48440 | 1606 | 30.162 |
| 688767 | 博拓生物 | 75845 | 2542 | 29.837 |
| 688707 | 振华新材 | 64084 | 2178 | 29.423 |
| 688272 | 富吉瑞 | 80806 | 2767 | 29.203 |
| 688257 | 新锐股份 | 56006 | 1921 | 29.155 |
| 688787 | 海天瑞声 | 93323 | 3206 | 29.109 |
| 688622 | 禾信仪器 | 70999 | 2449 | 28.991 |
| 688701 | 卓锦股份 | 69477 | 2426 | 28.638 |
| 688711 | 宏微科技 | 56734 | 1982 | 28.625 |
| 688103 | 国力股份 | 64270 | 2282 | 28.164 |
| 688385 | 复旦微电 | 74043 | 2726 | 27.162 |
| 688798 | 艾为电子 | 45997 | 1718 | 26.774 |
| 688766 | 普冉股份 | 56399 | 2144 | 26.306 |

## API Calls

- calls：`511`
- total tokens：`2589568`
- prompt tokens：`2475297`
- completion tokens：`114271`

## 输出

- chunk CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard2_20260708/ipo_redundancy_chunk_with_llm_cot_v3b_len132_tight.csv`
- firm CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard2_20260708/ipo_redundancy_firm_level_cot_v3b_len132_tight.csv`
- comparison：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard2_20260708/summary_comparison_vs_source_20260707.csv`
- call log：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard2_20260708/siliconflow_call_log_20260707.csv`
