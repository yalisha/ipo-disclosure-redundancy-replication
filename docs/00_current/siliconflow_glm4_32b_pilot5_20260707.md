# SiliconFlow GLM-4-32B Pilot5

日期：2026-07-07

## 结论

- 使用模型：`THUDM/GLM-4-32B-0414`，接口：SiliconFlow OpenAI-compatible chat completions。
- API key 未写入脚本、结果或文档；本目录只保存模型返回文本和聚合指标。
- 样本复用原 `glm4_dewrap_join_pilot5_20260705` 的 5 家、78 个 chunk。
- GLM 生成的 `Summary_len_proxy` mean=131.731，原 Codex pilot5 mean=134.526，原文 mean=132.678。
- GLM 生成的 `Redundancy_chunk_proxy` mean=30.745，原文 mean=32.176。
- GLM 的 `Relevant_score` mean=2.085，原 Codex pilot5 mean=2.391。

## 描述统计

| metric | glm_mean | codex_mean | paper_mean | glm_median | codex_median |
| --- | --- | --- | --- | --- | --- |
| Summary_len_proxy | 131.731 | 134.526 | 132.678 | 127.500 | 133.000 |
| Redundancy_chunk_proxy | 30.745 | 29.232 | 32.176 | 30.658 |  |
| Relevant_score | 2.085 | 2.391 |  | 1.788 | 2.457 |

## 企业层

| sec_code | sec_name | original_length_units | summary_length_units | redundancy |
| --- | --- | --- | --- | --- |
| 688693 | 锴威特 | 50351 | 1593 | 31.608 |
| 688038 | 中科通达 | 61022 | 2084 | 29.281 |
| 688311 | 盟升电子 | 63238 | 2199 | 28.758 |
| 688172 | 燕东微 | 50643 | 1796 | 28.198 |
| 688123 | 聚辰股份 | 72690 | 2603 | 27.925 |

## API Calls

- calls：`78`
- total tokens：`407328`
- prompt tokens：`389061`
- completion tokens：`18267`

## 输出

- chunk CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_pilot5_20260707/ipo_redundancy_chunk_with_llm_cot_v3b_len132_tight.csv`
- firm CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_pilot5_20260707/ipo_redundancy_firm_level_cot_v3b_len132_tight.csv`
- comparison：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_pilot5_20260707/summary_comparison_vs_codex_pilot5_20260707.csv`
- call log：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_pilot5_20260707/siliconflow_call_log_20260707.csv`
