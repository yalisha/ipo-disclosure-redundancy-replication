# SiliconFlow GLM-4-32B Table2 next100 after GLM200 shard1

日期：2026-07-08

## 结论

- 使用模型：`THUDM/GLM-4-32B-0414`，接口：SiliconFlow OpenAI-compatible chat completions。
- API key 未写入脚本、结果或文档；本目录只保存模型返回文本和聚合指标。
- 样本复用原 `glm4_dewrap_join_glm_next100_after200_table2_shard1_20260708` 的 20 家、341 个 chunk。
- GLM 生成的 `Summary_len_proxy` mean=123.551，source Codex mean=130.938，原文 mean=132.678。
- GLM 生成的 `Redundancy_chunk_proxy` mean=33.006，原文 mean=32.176。
- GLM 的 `Relevant_score` mean=2.078，source Codex mean=2.329。

## 描述统计

| metric | glm_mean | codex_mean | paper_mean | glm_median | codex_median |
| --- | --- | --- | --- | --- | --- |
| Summary_len_proxy | 123.551 | 130.938 | 132.678 | 122.000 | 132.000 |
| Redundancy_chunk_proxy | 33.006 | 30.103 | 32.176 | 31.417 |  |
| Relevant_score | 2.078 | 2.329 |  | 1.790 | 2.386 |

## 企业层

| sec_code | sec_name | original_length_units | summary_length_units | redundancy |
| --- | --- | --- | --- | --- |
| 688330 | 宏力达 | 69208 | 2082 | 33.241 |
| 688529 | 豪森股份 | 73051 | 2253 | 32.424 |
| 688526 | 科前生物 | 91267 | 2822 | 32.341 |
| 688386 | 泛亚微透 | 58122 | 1802 | 32.254 |
| 688160 | 步科股份 | 45475 | 1442 | 31.536 |
| 688577 | 浙海德曼 | 60667 | 1926 | 31.499 |
| 688559 | 海目星 | 68180 | 2171 | 31.405 |
| 688179 | 阿拉丁 | 75995 | 2425 | 31.338 |
| 688093 | 世华科技 | 63993 | 2046 | 31.277 |
| 688127 | 蓝特光学 | 53417 | 1716 | 31.129 |
| 688057 | 金达莱 | 108549 | 3578 | 30.338 |
| 688013 | 天臣医疗 | 66732 | 2201 | 30.319 |
| 688551 | 科威尔 | 63258 | 2103 | 30.080 |
| 688156 | 路德环境 | 64978 | 2167 | 29.985 |
| 688129 | 东来技术 | 55446 | 1861 | 29.794 |
| 688788 | 科思科技 | 64473 | 2178 | 29.602 |
| 688536 | 思瑞浦 | 35871 | 1216 | 29.499 |
| 688135 | 利扬芯片 | 48241 | 1685 | 28.630 |
| 688585 | 上纬新材 | 75201 | 2649 | 28.388 |
| 688219 | 会通股份 | 50498 | 1808 | 27.930 |

## API Calls

- calls：`341`
- total tokens：`1732323`
- prompt tokens：`1655776`
- completion tokens：`76547`

## 输出

- chunk CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_after200_shard1_20260708/ipo_redundancy_chunk_with_llm_cot_v3b_len132_tight.csv`
- firm CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_after200_shard1_20260708/ipo_redundancy_firm_level_cot_v3b_len132_tight.csv`
- comparison：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_after200_shard1_20260708/summary_comparison_vs_source_20260707.csv`
- call log：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_after200_shard1_20260708/siliconflow_call_log_20260707.csv`
