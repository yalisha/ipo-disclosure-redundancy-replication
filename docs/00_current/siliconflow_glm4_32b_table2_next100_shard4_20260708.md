# SiliconFlow GLM-4-32B Table2 next100 shard4

日期：2026-07-08

## 结论

- 使用模型：`THUDM/GLM-4-32B-0414`，接口：SiliconFlow OpenAI-compatible chat completions。
- API key 未写入脚本、结果或文档；本目录只保存模型返回文本和聚合指标。
- 样本复用原 `glm4_dewrap_join_glm_next100_table2_shard4_20260708` 的 20 家、320 个 chunk。
- GLM 生成的 `Summary_len_proxy` mean=125.372，source Codex mean=127.156，原文 mean=132.678。
- GLM 生成的 `Redundancy_chunk_proxy` mean=33.446，原文 mean=32.176。
- GLM 的 `Relevant_score` mean=2.098，source Codex mean=2.243。

## 描述统计

| metric | glm_mean | codex_mean | paper_mean | glm_median | codex_median |
| --- | --- | --- | --- | --- | --- |
| Summary_len_proxy | 125.372 | 127.156 | 132.678 | 122.000 | 128.000 |
| Redundancy_chunk_proxy | 33.446 | 31.027 | 32.176 | 31.398 |  |
| Relevant_score | 2.098 | 2.243 |  | 1.824 | 2.296 |

## 企业层

| sec_code | sec_name | original_length_units | summary_length_units | redundancy |
| --- | --- | --- | --- | --- |
| 688567 | 孚能科技 | 79835 | 2371 | 33.671 |
| 688065 | 凯赛生物 | 51415 | 1542 | 33.343 |
| 688050 | 爱博医疗 | 84393 | 2537 | 33.265 |
| 688077 | 大地熊 | 47357 | 1429 | 33.140 |
| 688069 | 德林海 | 75234 | 2291 | 32.839 |
| 688338 | 赛科希德 | 67794 | 2196 | 30.872 |
| 688981 | 中芯国际 | 30954 | 1015 | 30.497 |
| 688488 | 艾迪药业 | 63783 | 2099 | 30.387 |
| 688556 | 高测股份 | 71243 | 2369 | 30.073 |
| 688561 | 奇安信 | 93942 | 3132 | 29.994 |
| 688580 | 伟思医疗 | 55934 | 1901 | 29.423 |
| 688286 | 敏芯股份 | 44794 | 1534 | 29.201 |
| 688155 | 先惠技术 | 58023 | 1990 | 29.157 |
| 688508 | 芯朋微 | 45947 | 1586 | 28.970 |
| 688586 | 江航装备 | 40540 | 1402 | 28.916 |
| 688589 | 力合微 | 47664 | 1682 | 28.338 |
| 688418 | 震有科技 | 70296 | 2498 | 28.141 |
| 688256 | 寒武纪 | 44986 | 1637 | 27.481 |
| 688579 | 山大地纬 | 55072 | 2024 | 27.209 |
| 688339 | 亿华通 | 74275 | 2884 | 25.754 |

## API Calls

- calls：`320`
- total tokens：`1616757`
- prompt tokens：`1544358`
- completion tokens：`72399`

## 输出

- chunk CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_shard4_20260708/ipo_redundancy_chunk_with_llm_cot_v3b_len132_tight.csv`
- firm CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_shard4_20260708/ipo_redundancy_firm_level_cot_v3b_len132_tight.csv`
- comparison：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_shard4_20260708/summary_comparison_vs_source_20260707.csv`
- call log：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_shard4_20260708/siliconflow_call_log_20260707.csv`
