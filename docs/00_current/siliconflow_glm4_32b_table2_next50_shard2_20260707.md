# SiliconFlow GLM-4-32B Table2 Next50 Shard2

日期：2026-07-07

## 结论

- 使用模型：`THUDM/GLM-4-32B-0414`，接口：SiliconFlow OpenAI-compatible chat completions。
- API key 未写入脚本、结果或文档；本目录只保存模型返回文本和聚合指标。
- 样本复用原 `glm4_dewrap_join_glm_next50_table2_shard2_20260707` 的 17 家、297 个 chunk。
- GLM 生成的 `Summary_len_proxy` mean=124.401，source Codex mean=121.279，原文 mean=132.678。
- GLM 生成的 `Redundancy_chunk_proxy` mean=33.750，原文 mean=32.176。
- GLM 的 `Relevant_score` mean=2.068，source Codex mean=2.411。

## 描述统计

| metric | glm_mean | codex_mean | paper_mean | glm_median | codex_median |
| --- | --- | --- | --- | --- | --- |
| Summary_len_proxy | 124.401 | 121.279 | 132.678 | 122.000 | 120.000 |
| Redundancy_chunk_proxy | 33.750 | 32.771 | 32.176 | 31.065 |  |
| Relevant_score | 2.068 | 2.411 |  | 1.793 | 2.474 |

## 企业层

| sec_code | sec_name | original_length_units | summary_length_units | redundancy |
| --- | --- | --- | --- | --- |
| 688310 | 迈得医疗 | 41283 | 1192 | 34.633 |
| 688111 | 金山办公 | 85327 | 2509 | 34.008 |
| 688188 | 柏楚电子 | 69869 | 2081 | 33.575 |
| 688006 | 杭可科技 | 51366 | 1584 | 32.428 |
| 688025 | 杰普特 | 73532 | 2282 | 32.223 |
| 688009 | 中国通号 | 100149 | 3110 | 32.202 |
| 688139 | 海尔生物 | 46766 | 1499 | 31.198 |
| 688033 | 天宜上佳 | 104701 | 3360 | 31.161 |
| 688363 | 华熙生物 | 92253 | 2978 | 30.978 |
| 688022 | 瀚川智能 | 68761 | 2247 | 30.601 |
| 688116 | 天奈科技 | 53625 | 1758 | 30.503 |
| 688389 | 普门科技 | 67824 | 2349 | 28.874 |
| 688023 | 安恒信息 | 75560 | 2632 | 28.708 |
| 688018 | 乐鑫科技 | 43794 | 1529 | 28.642 |
| 688002 | 睿创微纳 | 56427 | 2049 | 27.539 |
| 688122 | 西部超导 | 63240 | 2321 | 27.247 |
| 688012 | 中微公司 | 32325 | 1467 | 22.035 |

## API Calls

- calls：`297`
- total tokens：`1509280`
- prompt tokens：`1443095`
- completion tokens：`66185`

## 输出

- chunk CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next50_shard2_20260707/ipo_redundancy_chunk_with_llm_cot_v3b_len132_tight.csv`
- firm CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next50_shard2_20260707/ipo_redundancy_firm_level_cot_v3b_len132_tight.csv`
- comparison：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next50_shard2_20260707/summary_comparison_vs_source_20260707.csv`
- call log：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next50_shard2_20260707/siliconflow_call_log_20260707.csv`
