# SiliconFlow GLM-4-32B Table2_remaining_to471_shard6

日期：2026-07-09

## 结论

- 使用模型：`THUDM/GLM-4-32B-0414`，接口：SiliconFlow OpenAI-compatible chat completions。
- API key 未写入脚本、结果或文档；本目录只保存模型返回文本和聚合指标。
- 样本复用原 `glm4_dewrap_join_glm_remaining_to471_table2_shard6_20260708` 的 28 家、386 个 chunk。
- GLM 生成的 `Summary_len_proxy` mean=127.881，source Codex mean=129.855，原文 mean=132.678。
- GLM 生成的 `Redundancy_chunk_proxy` mean=31.430，原文 mean=32.176。
- GLM 的 `Relevant_score` mean=2.102，source Codex mean=2.296。

## 描述统计

| metric | glm_mean | codex_mean | paper_mean | glm_median | codex_median |
| --- | --- | --- | --- | --- | --- |
| Summary_len_proxy | 127.881 | 129.855 | 132.678 | 124.500 | 130.500 |
| Redundancy_chunk_proxy | 31.430 | 30.619 | 32.176 | 30.502 |  |
| Relevant_score | 2.102 | 2.296 |  | 1.855 | 2.356 |

## 企业层

| sec_code | sec_name | original_length_units | summary_length_units | redundancy |
| --- | --- | --- | --- | --- |
| 688448 | 磁谷科技 | 41047 | 1145 | 35.849 |
| 688275 | 万润新能 | 64482 | 1918 | 33.619 |
| 688498 | 源杰科技 | 42456 | 1267 | 33.509 |
| 688420 | 美腾科技 | 57211 | 1787 | 32.015 |
| 688428 | 诺诚健华 | 76244 | 2423 | 31.467 |
| 688480 | 赛恩斯 | 64531 | 2063 | 31.280 |
| 688244 | 永信至诚 | 68151 | 2214 | 30.782 |
| 688184 | 帕瓦股份 | 30973 | 1016 | 30.485 |
| 688252 | 天德钰 | 38390 | 1274 | 30.133 |
| 688419 | 耐科装备 | 56928 | 1890 | 30.121 |
| 688432 | 有研硅 | 43410 | 1442 | 30.104 |
| 688147 | 微导纳米 | 40385 | 1345 | 30.026 |
| 688387 | 信科移动 | 81935 | 2754 | 29.751 |
| 688362 | 甬矽电子 | 45480 | 1529 | 29.745 |
| 688132 | 邦彦技术 | 53677 | 1810 | 29.656 |
| 688489 | 三未信安 | 44627 | 1510 | 29.554 |
| 688143 | 长盈通 | 66301 | 2286 | 29.003 |
| 688084 | 晶品特装 | 58238 | 2026 | 28.745 |
| 688503 | 聚和材料 | 33329 | 1174 | 28.389 |
| 688372 | 伟测科技 | 40436 | 1427 | 28.336 |
| 688141 | 杰华特 | 38855 | 1383 | 28.095 |
| 688410 | 山外山 | 48710 | 1750 | 27.834 |
| 688426 | 康为世纪 | 57963 | 2087 | 27.773 |
| 688061 | 灿瑞科技 | 44910 | 1631 | 27.535 |
| 688459 | 哈铁科技 | 67445 | 2479 | 27.207 |
| 688152 | 麒麟信安 | 53025 | 1960 | 27.054 |
| 688031 | 星环科技 | 71790 | 2670 | 26.888 |
| 688409 | 富创精密 | 29512 | 1102 | 26.780 |

## API Calls

- calls：`386`
- total tokens：`1959417`
- prompt tokens：`1871505`
- completion tokens：`87912`

## 输出

- chunk CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard6_20260708/ipo_redundancy_chunk_with_llm_cot_v3b_len132_tight.csv`
- firm CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard6_20260708/ipo_redundancy_firm_level_cot_v3b_len132_tight.csv`
- comparison：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard6_20260708/summary_comparison_vs_source_20260707.csv`
- call log：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard6_20260708/siliconflow_call_log_20260707.csv`
