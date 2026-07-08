# SiliconFlow GLM-4-32B Table2_remaining_to471_shard3

日期：2026-07-08

## 结论

- 使用模型：`THUDM/GLM-4-32B-0414`，接口：SiliconFlow OpenAI-compatible chat completions。
- API key 未写入脚本、结果或文档；本目录只保存模型返回文本和聚合指标。
- 样本复用原 `glm4_dewrap_join_glm_remaining_to471_table2_shard3_20260708` 的 31 家、492 个 chunk。
- GLM 生成的 `Summary_len_proxy` mean=128.557，source Codex mean=134.096，原文 mean=132.678。
- GLM 生成的 `Redundancy_chunk_proxy` mean=32.066，原文 mean=32.176。
- GLM 的 `Relevant_score` mean=2.121，source Codex mean=2.313。

## 描述统计

| metric | glm_mean | codex_mean | paper_mean | glm_median | codex_median |
| --- | --- | --- | --- | --- | --- |
| Summary_len_proxy | 128.557 | 134.096 | 132.678 | 125.000 | 135.500 |
| Redundancy_chunk_proxy | 32.066 | 29.693 | 32.176 | 30.706 |  |
| Relevant_score | 2.121 | 2.313 |  | 1.837 | 2.395 |

## 企业层

| sec_code | sec_name | original_length_units | summary_length_units | redundancy |
| --- | --- | --- | --- | --- |
| 688190 | 云路股份 | 52923 | 1559 | 33.947 |
| 688232 | 新点软件 | 76119 | 2309 | 32.966 |
| 688049 | 炬芯科技 | 36653 | 1131 | 32.408 |
| 688210 | 统联精密 | 46749 | 1448 | 32.285 |
| 688265 | 南模生物 | 46950 | 1457 | 32.224 |
| 688176 | 亚虹医药 | 72532 | 2251 | 32.222 |
| 688248 | 南网科技 | 73165 | 2289 | 31.964 |
| 688212 | 澳华内镜 | 60309 | 1912 | 31.542 |
| 688075 | 安旭生物 | 71788 | 2287 | 31.390 |
| 688236 | 春立医疗 | 90980 | 2962 | 30.716 |
| 688112 | 鼎阳科技 | 66301 | 2161 | 30.681 |
| 688032 | 禾迈股份 | 51651 | 1688 | 30.599 |
| 688182 | 灿勤科技 | 51840 | 1707 | 30.369 |
| 688235 | 百济神州 | 112973 | 3723 | 30.345 |
| 688246 | 嘉和美康 | 72619 | 2406 | 30.182 |
| 688151 | 华强科技 | 43208 | 1460 | 29.595 |
| 688167 | 炬光科技 | 52066 | 1774 | 29.349 |
| 688227 | 品高股份 | 59848 | 2053 | 29.151 |
| 688230 | 芯导科技 | 41758 | 1435 | 29.100 |
| 688107 | 安路科技 | 36455 | 1277 | 28.547 |
| 688162 | 巨一科技 | 61524 | 2191 | 28.080 |
| 688173 | 希荻微 | 54951 | 1957 | 28.079 |
| 688261 | 东微半导 | 42780 | 1524 | 28.071 |
| 688267 | 中触媒 | 50372 | 1818 | 27.707 |
| 688259 | 创耀科技 | 66976 | 2423 | 27.642 |
| 688223 | 晶科能源 | 60176 | 2222 | 27.082 |
| 688171 | 纬德信息 | 48359 | 1806 | 26.777 |
| 688225 | 亚信安全 | 58337 | 2236 | 26.090 |
| 688262 | 国芯科技 | 77906 | 3055 | 25.501 |
| 688220 | 翱捷科技 | 65842 | 2583 | 25.491 |
| 688082 | 盛美上海 | 51044 | 2146 | 23.786 |

## API Calls

- calls：`492`
- total tokens：`2490752`
- prompt tokens：`2378514`
- completion tokens：`112238`

## 输出

- chunk CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard3_20260708/ipo_redundancy_chunk_with_llm_cot_v3b_len132_tight.csv`
- firm CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard3_20260708/ipo_redundancy_firm_level_cot_v3b_len132_tight.csv`
- comparison：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard3_20260708/summary_comparison_vs_source_20260707.csv`
- call log：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard3_20260708/siliconflow_call_log_20260707.csv`
