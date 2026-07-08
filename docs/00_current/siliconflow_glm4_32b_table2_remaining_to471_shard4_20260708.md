# SiliconFlow GLM-4-32B Table2_remaining_to471_shard4

日期：2026-07-08

## 结论

- 使用模型：`THUDM/GLM-4-32B-0414`，接口：SiliconFlow OpenAI-compatible chat completions。
- API key 未写入脚本、结果或文档；本目录只保存模型返回文本和聚合指标。
- 样本复用原 `glm4_dewrap_join_glm_remaining_to471_table2_shard4_20260708` 的 31 家、419 个 chunk。
- GLM 生成的 `Summary_len_proxy` mean=129.107，source Codex mean=135.041，原文 mean=132.678。
- GLM 生成的 `Redundancy_chunk_proxy` mean=31.639，原文 mean=32.176。
- GLM 的 `Relevant_score` mean=2.053，source Codex mean=2.248。

## 描述统计

| metric | glm_mean | codex_mean | paper_mean | glm_median | codex_median |
| --- | --- | --- | --- | --- | --- |
| Summary_len_proxy | 129.107 | 135.041 | 132.678 | 126.000 | 135.000 |
| Redundancy_chunk_proxy | 31.639 | 29.177 | 32.176 | 30.807 |  |
| Relevant_score | 2.053 | 2.248 |  | 1.815 | 2.291 |

## 企业层

| sec_code | sec_name | original_length_units | summary_length_units | redundancy |
| --- | --- | --- | --- | --- |
| 688046 | 药康生物 | 51765 | 1449 | 35.725 |
| 688238 | 和元生物 | 46164 | 1405 | 32.857 |
| 688052 | 纳芯微 | 50264 | 1533 | 32.788 |
| 688306 | 均普智能 | 59081 | 1817 | 32.516 |
| 688320 | 禾川科技 | 52115 | 1603 | 32.511 |
| 688072 | 拓荆科技 | 29076 | 916 | 31.742 |
| 688207 | 格灵深瞳 | 34328 | 1082 | 31.726 |
| 688279 | 峰岹科技 | 33947 | 1070 | 31.726 |
| 688209 | 英集芯 | 49026 | 1554 | 31.548 |
| 688153 | 唯捷创芯 | 28640 | 917 | 31.232 |
| 688102 | 斯瑞新材 | 60634 | 1955 | 31.015 |
| 688290 | 景业智能 | 50362 | 1631 | 30.878 |
| 688295 | 中复神鹰 | 52750 | 1748 | 30.177 |
| 688115 | 思林杰 | 51374 | 1706 | 30.114 |
| 688120 | 华海清科 | 47362 | 1578 | 30.014 |
| 688325 | 赛微微电 | 30886 | 1032 | 29.928 |
| 688327 | 云从科技 | 69829 | 2343 | 29.803 |
| 688282 | 理工导航 | 51753 | 1745 | 29.658 |
| 688193 | 仁度生物 | 70104 | 2437 | 28.767 |
| 688337 | 普源精电 | 55704 | 1945 | 28.640 |
| 688045 | 必易微 | 39304 | 1373 | 28.626 |
| 688251 | 井松智能 | 38913 | 1375 | 28.300 |
| 688125 | 安达智能 | 50295 | 1789 | 28.113 |
| 688175 | 高凌信息 | 71707 | 2614 | 27.432 |
| 688326 | 经纬恒润 | 48913 | 1796 | 27.234 |
| 688281 | 华秦科技 | 48249 | 1778 | 27.137 |
| 688197 | 首药控股 | 48909 | 1818 | 26.903 |
| 688213 | 思特威 | 40319 | 1503 | 26.826 |
| 688119 | 中钢洛耐 | 63072 | 2353 | 26.805 |
| 688331 | 荣昌生物 | 96078 | 3729 | 25.765 |
| 688170 | 德龙激光 | 59557 | 2502 | 23.804 |

## API Calls

- calls：`419`
- total tokens：`2122802`
- prompt tokens：`2026525`
- completion tokens：`96277`

## 输出

- chunk CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard4_20260708/ipo_redundancy_chunk_with_llm_cot_v3b_len132_tight.csv`
- firm CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard4_20260708/ipo_redundancy_firm_level_cot_v3b_len132_tight.csv`
- comparison：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard4_20260708/summary_comparison_vs_source_20260707.csv`
- call log：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard4_20260708/siliconflow_call_log_20260707.csv`
