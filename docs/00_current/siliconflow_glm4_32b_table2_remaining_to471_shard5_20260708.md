# SiliconFlow GLM-4-32B Table2_remaining_to471_shard5

日期：2026-07-09

## 结论

- 使用模型：`THUDM/GLM-4-32B-0414`，接口：SiliconFlow OpenAI-compatible chat completions。
- API key 未写入脚本、结果或文档；本目录只保存模型返回文本和聚合指标。
- 样本复用原 `glm4_dewrap_join_glm_remaining_to471_table2_shard5_20260708` 的 31 家、400 个 chunk。
- GLM 生成的 `Summary_len_proxy` mean=122.550，source Codex mean=130.025，原文 mean=132.678。
- GLM 生成的 `Redundancy_chunk_proxy` mean=32.638，原文 mean=32.176。
- GLM 的 `Relevant_score` mean=2.118，source Codex mean=2.267。

## 描述统计

| metric | glm_mean | codex_mean | paper_mean | glm_median | codex_median |
| --- | --- | --- | --- | --- | --- |
| Summary_len_proxy | 122.550 | 130.025 | 132.678 | 121.000 | 132.500 |
| Redundancy_chunk_proxy | 32.638 | 30.281 | 32.176 | 31.634 |  |
| Relevant_score | 2.118 | 2.267 |  | 1.815 | 2.350 |

## 企业层

| sec_code | sec_name | original_length_units | summary_length_units | redundancy |
| --- | --- | --- | --- | --- |
| 688373 | 盟科药业 | 63158 | 1718 | 36.763 |
| 688332 | 中科蓝讯 | 46125 | 1256 | 36.724 |
| 688203 | 海正生材 | 77986 | 2244 | 34.753 |
| 688370 | 丛麟科技 | 65835 | 1904 | 34.577 |
| 688371 | 菲沃泰 | 52124 | 1514 | 34.428 |
| 688403 | 汇成股份 | 38785 | 1135 | 34.172 |
| 688247 | 宣泰医药 | 71388 | 2118 | 33.705 |
| 688231 | 隆达股份 | 63146 | 1949 | 32.399 |
| 688035 | 德邦科技 | 46065 | 1433 | 32.146 |
| 688322 | 奥比中光 | 12238 | 381 | 32.121 |
| 688114 | 华大智造 | 35941 | 1133 | 31.722 |
| 688381 | 帝奥微 | 48043 | 1561 | 30.777 |
| 688416 | 恒烁股份 | 53838 | 1753 | 30.712 |
| 688439 | 振华风光 | 31418 | 1029 | 30.533 |
| 688348 | 昱能科技 | 44479 | 1465 | 30.361 |
| 688041 | 海光信息 | 34614 | 1144 | 30.257 |
| 688353 | 华盛锂电 | 42979 | 1426 | 30.140 |
| 688053 | 思科瑞 | 55179 | 1837 | 30.038 |
| 688351 | 微电生理 | 49254 | 1667 | 29.546 |
| 688297 | 中无人机 | 45890 | 1558 | 29.454 |
| 688271 | 联影医疗 | 81111 | 2773 | 29.250 |
| 688130 | 晶华微 | 35975 | 1232 | 29.200 |
| 688391 | 钜泉科技 | 63337 | 2181 | 29.040 |
| 688237 | 超卓航科 | 38402 | 1350 | 28.446 |
| 688380 | 中微半导 | 34489 | 1216 | 28.363 |
| 688292 | 浩瀚深度 | 54668 | 1959 | 27.906 |
| 688401 | 路维光电 | 47375 | 1705 | 27.786 |
| 688047 | 龙芯中科 | 31169 | 1127 | 27.657 |
| 688400 | 凌云光 | 62854 | 2277 | 27.604 |
| 688205 | 德科立 | 45659 | 1668 | 27.374 |
| 688273 | 麦澜德 | 33753 | 1307 | 25.825 |

## API Calls

- calls：`400`
- total tokens：`2022780`
- prompt tokens：`1933253`
- completion tokens：`89527`

## 输出

- chunk CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard5_20260708/ipo_redundancy_chunk_with_llm_cot_v3b_len132_tight.csv`
- firm CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard5_20260708/ipo_redundancy_firm_level_cot_v3b_len132_tight.csv`
- comparison：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard5_20260708/summary_comparison_vs_source_20260707.csv`
- call log：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_remaining_to471_shard5_20260708/siliconflow_call_log_20260707.csv`
