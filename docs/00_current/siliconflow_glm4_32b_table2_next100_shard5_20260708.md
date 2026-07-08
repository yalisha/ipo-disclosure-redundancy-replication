# SiliconFlow GLM-4-32B Table2 next100 shard5

日期：2026-07-08

## 结论

- 使用模型：`THUDM/GLM-4-32B-0414`，接口：SiliconFlow OpenAI-compatible chat completions。
- API key 未写入脚本、结果或文档；本目录只保存模型返回文本和聚合指标。
- 样本复用原 `glm4_dewrap_join_glm_next100_table2_shard5_20260708` 的 20 家、289 个 chunk。
- GLM 生成的 `Summary_len_proxy` mean=120.339，source Codex mean=134.107，原文 mean=132.678。
- GLM 生成的 `Redundancy_chunk_proxy` mean=33.612，原文 mean=32.176。
- GLM 的 `Relevant_score` mean=2.058，source Codex mean=2.318。

## 描述统计

| metric | glm_mean | codex_mean | paper_mean | glm_median | codex_median |
| --- | --- | --- | --- | --- | --- |
| Summary_len_proxy | 120.339 | 134.107 | 132.678 | 117.000 | 135.000 |
| Redundancy_chunk_proxy | 33.612 | 29.689 | 32.176 | 33.017 |  |
| Relevant_score | 2.058 | 2.318 |  | 1.838 | 2.417 |

## 企业层

| sec_code | sec_name | original_length_units | summary_length_units | redundancy |
| --- | --- | --- | --- | --- |
| 688095 | 福昕软件 | 45244 | 1249 | 36.224 |
| 688379 | 华光新材 | 60103 | 1731 | 34.722 |
| 688513 | 苑东生物 | 58206 | 1692 | 34.401 |
| 688390 | 固德威 | 65190 | 1920 | 33.953 |
| 688289 | 圣湘生物 | 70206 | 2069 | 33.932 |
| 688378 | 奥来德 | 48075 | 1438 | 33.432 |
| 688215 | 瑞晟智能 | 50392 | 1515 | 33.262 |
| 688393 | 安必平 | 78687 | 2372 | 33.173 |
| 688408 | 中信博 | 54413 | 1695 | 32.102 |
| 688056 | 莱伯泰科 | 69939 | 2179 | 32.097 |
| 688519 | 南亚新材 | 32993 | 1040 | 31.724 |
| 688550 | 瑞联新材 | 31205 | 987 | 31.616 |
| 688229 | 博睿数据 | 69379 | 2195 | 31.608 |
| 688569 | 铁科轨道 | 65585 | 2181 | 30.071 |
| 688055 | 龙腾光电 | 57274 | 1918 | 29.861 |
| 688356 | 键凯科技 | 54520 | 1828 | 29.825 |
| 688335 | 复洁环保 | 61206 | 2076 | 29.483 |
| 688017 | 绿的谐波 | 39815 | 1396 | 28.521 |
| 688596 | 正帆科技 | 52978 | 1904 | 27.825 |
| 688521 | 芯原股份 | 38138 | 1393 | 27.378 |

## API Calls

- calls：`289`
- total tokens：`1475161`
- prompt tokens：`1411400`
- completion tokens：`63761`

## 输出

- chunk CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_shard5_20260708/ipo_redundancy_chunk_with_llm_cot_v3b_len132_tight.csv`
- firm CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_shard5_20260708/ipo_redundancy_firm_level_cot_v3b_len132_tight.csv`
- comparison：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_shard5_20260708/summary_comparison_vs_source_20260707.csv`
- call log：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_shard5_20260708/siliconflow_call_log_20260707.csv`
