# SiliconFlow GLM-4-32B Table2_remaining_to471_shard1

日期：2026-07-08

## 结论

- 使用模型：`THUDM/GLM-4-32B-0414`，接口：SiliconFlow OpenAI-compatible chat completions。
- API key 未写入脚本、结果或文档；本目录只保存模型返回文本和聚合指标。
- 样本复用原 `glm4_dewrap_join_glm_remaining_to471_table2_shard1_20260708` 的 31 家、525 个 chunk。
- GLM 生成的 `Summary_len_proxy` mean=121.981，source Codex mean=128.790，原文 mean=132.678。
- GLM 生成的 `Redundancy_chunk_proxy` mean=34.688，原文 mean=32.176。
- GLM 的 `Relevant_score` mean=2.127，source Codex mean=2.359。

## 描述统计

| metric | glm_mean | codex_mean | paper_mean | glm_median | codex_median |
| --- | --- | --- | --- | --- | --- |
| Summary_len_proxy | 121.981 | 128.790 | 132.678 | 122.000 | 129.000 |
| Redundancy_chunk_proxy | 34.688 | 31.115 | 32.176 | 31.503 |  |
| Relevant_score | 2.127 | 2.359 |  | 1.800 | 2.367 |

## 企业层

| sec_code | sec_name | original_length_units | summary_length_units | redundancy |
| --- | --- | --- | --- | --- |
| 688161 | 威高骨科 | 81726 | 2116 | 38.623 |
| 688226 | 威腾电气 | 86582 | 2456 | 35.253 |
| 688087 | 英科再生 | 54919 | 1567 | 35.047 |
| 688793 | 倍轻松 | 69819 | 2026 | 34.462 |
| 688305 | 科德数控 | 76467 | 2260 | 33.835 |
| 688319 | 欧林生物 | 77022 | 2299 | 33.502 |
| 688768 | 容知日新 | 58620 | 1763 | 33.250 |
| 688303 | 大全能源 | 57755 | 1738 | 33.231 |
| 688067 | 爱威科技 | 64096 | 1947 | 32.920 |
| 688276 | 百克生物 | 52795 | 1622 | 32.549 |
| 688296 | 和达科技 | 62807 | 1961 | 32.028 |
| 688501 | 青达环保 | 66829 | 2092 | 31.945 |
| 688789 | 宏华数科 | 49924 | 1605 | 31.105 |
| 688269 | 凯立新材 | 68522 | 2207 | 31.048 |
| 688601 | 力芯微 | 34914 | 1129 | 30.925 |
| 688718 | 唯赛勃 | 65063 | 2105 | 30.909 |
| 688681 | 科汇股份 | 54974 | 1802 | 30.507 |
| 688131 | 皓元医药 | 97034 | 3201 | 30.314 |
| 688367 | 工大高科 | 60168 | 1987 | 30.281 |
| 688625 | 呈和科技 | 48955 | 1619 | 30.238 |
| 688345 | 博力威 | 64869 | 2146 | 30.228 |
| 688117 | 圣诺生物 | 75919 | 2523 | 30.091 |
| 688700 | 东威科技 | 36453 | 1216 | 29.978 |
| 688690 | 纳微科技 | 41697 | 1413 | 29.510 |
| 688597 | 煜邦电力 | 73302 | 2495 | 29.380 |
| 688239 | 航宇科技 | 73297 | 2534 | 28.925 |
| 688499 | 利元亨 | 48963 | 1715 | 28.550 |
| 688800 | 瑞可达 | 56345 | 1989 | 28.328 |
| 688517 | 金冠电气 | 63427 | 2250 | 28.190 |
| 688425 | 铁建重工 | 99614 | 3540 | 28.140 |
| 688538 | 和辉光电 | 74445 | 2717 | 27.400 |

## API Calls

- calls：`526`
- total tokens：`2682401`
- prompt tokens：`2565377`
- completion tokens：`117024`

## 输出

- chunk CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard1_20260708/ipo_redundancy_chunk_with_llm_cot_v3b_len132_tight.csv`
- firm CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard1_20260708/ipo_redundancy_firm_level_cot_v3b_len132_tight.csv`
- comparison：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard1_20260708/summary_comparison_vs_source_20260707.csv`
- call log：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard1_20260708/siliconflow_call_log_20260707.csv`
