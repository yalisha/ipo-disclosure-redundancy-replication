# SiliconFlow GLM-4-32B Table2 next100 after GLM200 shard2 repaired

日期：2026-07-08

## 结论

- 使用模型：`THUDM/GLM-4-32B-0414`，接口：SiliconFlow OpenAI-compatible chat completions。
- API key 未写入脚本、结果或文档；本目录只保存模型返回文本和聚合指标。
- 样本复用原 `glm4_dewrap_join_glm_next100_after200_table2_shard2_20260708` 的 20 家、310 个 chunk。
- GLM 生成的 `Summary_len_proxy` mean=120.955，source Codex mean=130.568，原文 mean=132.678。
- GLM 生成的 `Redundancy_chunk_proxy` mean=32.982，原文 mean=32.176。
- GLM 的 `Relevant_score` mean=2.048，source Codex mean=2.255。

## 描述统计

| metric | glm_mean | codex_mean | paper_mean | glm_median | codex_median |
| --- | --- | --- | --- | --- | --- |
| Summary_len_proxy | 120.955 | 130.568 | 132.678 | 118.000 | 130.000 |
| Redundancy_chunk_proxy | 32.982 | 30.011 | 32.176 | 32.320 |  |
| Relevant_score | 2.048 | 2.255 |  | 1.762 | 2.292 |

## 企业层

| sec_code | sec_name | original_length_units | summary_length_units | redundancy |
| --- | --- | --- | --- | --- |
| 688557 | 兰剑智能 | 72675 | 2137 | 34.008 |
| 688656 | 浩欧博 | 56562 | 1666 | 33.951 |
| 688136 | 科兴制药 | 68097 | 2017 | 33.762 |
| 688679 | 通源环境 | 41614 | 1244 | 33.452 |
| 688578 | 艾力斯 | 74571 | 2238 | 33.320 |
| 688617 | 惠泰医疗 | 92315 | 2874 | 32.121 |
| 688658 | 悦康药业 | 78874 | 2459 | 32.076 |
| 688618 | 三旺通信 | 58303 | 1848 | 31.549 |
| 688571 | 杭华股份 | 59019 | 1897 | 31.112 |
| 688510 | 航亚科技 | 54402 | 1749 | 31.105 |
| 688308 | 欧科亿 | 51879 | 1679 | 30.899 |
| 688560 | 明冠新材 | 50493 | 1635 | 30.883 |
| 688699 | 明微电子 | 51549 | 1673 | 30.812 |
| 688590 | 新致软件 | 45524 | 1536 | 29.638 |
| 688063 | 派能科技 | 57212 | 1937 | 29.536 |
| 688777 | 中控技术 | 54352 | 1864 | 29.159 |
| 688608 | 恒玄科技 | 37323 | 1296 | 28.799 |
| 688698 | 伟创电气 | 59609 | 2164 | 27.546 |
| 688668 | 鼎通科技 | 43579 | 1605 | 27.152 |
| 688686 | 奥普特 | 51153 | 1978 | 25.861 |

## API Calls

- calls：`310`
- total tokens：`1558087`
- prompt tokens：`1489261`
- completion tokens：`68826`

## 输出

- chunk CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_after200_shard2_20260708/ipo_redundancy_chunk_with_llm_cot_v3b_len132_tight.csv`
- firm CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_after200_shard2_20260708/ipo_redundancy_firm_level_cot_v3b_len132_tight.csv`
- comparison：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_after200_shard2_20260708/summary_comparison_vs_source_20260707.csv`
- call log：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_after200_shard2_20260708/siliconflow_call_log_20260707.csv`
