# SiliconFlow GLM-4-32B Table2 Next50 Shard1

日期：2026-07-07

## 结论

- 使用模型：`THUDM/GLM-4-32B-0414`，接口：SiliconFlow OpenAI-compatible chat completions。
- API key 未写入脚本、结果或文档；本目录只保存模型返回文本和聚合指标。
- 样本复用原 `glm4_dewrap_join_glm_next50_table2_shard1_20260707` 的 17 家、307 个 chunk。
- GLM 生成的 `Summary_len_proxy` mean=124.495，source Codex mean=132.081，原文 mean=132.678。
- GLM 生成的 `Redundancy_chunk_proxy` mean=33.828，原文 mean=32.176。
- GLM 的 `Relevant_score` mean=1.999，source Codex mean=2.298。

## 描述统计

| metric | glm_mean | codex_mean | paper_mean | glm_median | codex_median |
| --- | --- | --- | --- | --- | --- |
| Summary_len_proxy | 124.495 | 132.081 | 132.678 | 121.000 | 133.000 |
| Redundancy_chunk_proxy | 33.828 | 30.460 | 32.176 | 31.902 |  |
| Relevant_score | 1.999 | 2.298 |  | 1.718 | 2.348 |

## 企业层

| sec_code | sec_name | original_length_units | summary_length_units | redundancy |
| --- | --- | --- | --- | --- |
| 688366 | 昊海生科 | 108331 | 3121 | 34.710 |
| 688020 | 方邦股份 | 37061 | 1075 | 34.475 |
| 688388 | 嘉元科技 | 71419 | 2138 | 33.405 |
| 688196 | 卓越新能 | 95907 | 2885 | 33.243 |
| 688058 | 宝兰德 | 83698 | 2588 | 32.341 |
| 688088 | 虹软科技 | 61725 | 1932 | 31.949 |
| 688016 | 心脉医疗 | 56003 | 1775 | 31.551 |
| 688005 | 容百科技 | 47741 | 1531 | 31.183 |
| 688300 | 联瑞新材 | 89199 | 2878 | 30.993 |
| 688008 | 澜起科技 | 37624 | 1219 | 30.865 |
| 688299 | 长阳科技 | 67914 | 2210 | 30.730 |
| 688029 | 南微医学 | 101138 | 3337 | 30.308 |
| 688168 | 安博通 | 41616 | 1413 | 29.452 |
| 688202 | 美迪西 | 57088 | 2001 | 28.530 |
| 688001 | 华兴源创 | 66441 | 2416 | 27.500 |
| 688011 | 新光光电 | 60685 | 2222 | 27.311 |
| 688068 | 热景生物 | 91535 | 3479 | 26.311 |

## API Calls

- calls：`307`
- total tokens：`1570829`
- prompt tokens：`1502081`
- completion tokens：`68748`

## 输出

- chunk CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next50_shard1_20260707/ipo_redundancy_chunk_with_llm_cot_v3b_len132_tight.csv`
- firm CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next50_shard1_20260707/ipo_redundancy_firm_level_cot_v3b_len132_tight.csv`
- comparison：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next50_shard1_20260707/summary_comparison_vs_source_20260707.csv`
- call log：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next50_shard1_20260707/siliconflow_call_log_20260707.csv`
