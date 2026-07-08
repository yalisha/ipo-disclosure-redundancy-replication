# SiliconFlow GLM-4-32B Table2 next100 after GLM200 shard3

日期：2026-07-08

## 结论

- 使用模型：`THUDM/GLM-4-32B-0414`，接口：SiliconFlow OpenAI-compatible chat completions。
- API key 未写入脚本、结果或文档；本目录只保存模型返回文本和聚合指标。
- 样本复用原 `glm4_dewrap_join_glm_next100_after200_table2_shard3_20260708` 的 20 家、364 个 chunk。
- GLM 生成的 `Summary_len_proxy` mean=128.085，source Codex mean=128.629，原文 mean=132.678。
- GLM 生成的 `Redundancy_chunk_proxy` mean=34.099，原文 mean=32.176。
- GLM 的 `Relevant_score` mean=2.096，source Codex mean=2.345。

## 描述统计

| metric | glm_mean | codex_mean | paper_mean | glm_median | codex_median |
| --- | --- | --- | --- | --- | --- |
| Summary_len_proxy | 128.085 | 128.629 | 132.678 | 119.000 | 132.000 |
| Redundancy_chunk_proxy | 34.099 | 31.468 | 32.176 | 31.888 |  |
| Relevant_score | 2.096 | 2.345 |  | 1.803 | 2.364 |

## 企业层

| sec_code | sec_name | original_length_units | summary_length_units | redundancy |
| --- | --- | --- | --- | --- |
| 688316 | 青云科技 | 75099 | 2098 | 35.796 |
| 688689 | 银河微电 | 68391 | 1974 | 34.646 |
| 688680 | 海优新材 | 45606 | 1339 | 34.060 |
| 688083 | 中望软件 | 80901 | 2384 | 33.935 |
| 688669 | 聚石化学 | 60633 | 1814 | 33.425 |
| 688317 | 之江生物 | 100907 | 3038 | 33.215 |
| 688687 | 凯因科技 | 75390 | 2357 | 31.986 |
| 688677 | 海泰新光 | 53443 | 1674 | 31.925 |
| 688059 | 华锐精密 | 42706 | 1349 | 31.658 |
| 688328 | 深科达 | 59532 | 1901 | 31.316 |
| 688183 | 生益电子 | 90286 | 2893 | 31.208 |
| 688696 | 极米科技 | 81182 | 2638 | 30.774 |
| 688607 | 康众医疗 | 56730 | 1915 | 29.624 |
| 688819 | 天能股份 | 42489 | 1470 | 28.904 |
| 688676 | 金盘科技 | 74715 | 2595 | 28.792 |
| 688665 | 四方光电 | 75014 | 2674 | 28.053 |
| 688628 | 优利德 | 104663 | 3827 | 27.349 |
| 688079 | 美迪凯 | 46106 | 1709 | 26.978 |
| 688619 | 罗普特 | 85284 | 3489 | 24.444 |
| 688350 | 富淼科技 | 64830 | 3485 | 18.603 |

## API Calls

- calls：`364`
- total tokens：`1854948`
- prompt tokens：`1771603`
- completion tokens：`83345`

## 输出

- chunk CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_after200_shard3_20260708/ipo_redundancy_chunk_with_llm_cot_v3b_len132_tight.csv`
- firm CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_after200_shard3_20260708/ipo_redundancy_firm_level_cot_v3b_len132_tight.csv`
- comparison：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_after200_shard3_20260708/summary_comparison_vs_source_20260707.csv`
- call log：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_after200_shard3_20260708/siliconflow_call_log_20260707.csv`
