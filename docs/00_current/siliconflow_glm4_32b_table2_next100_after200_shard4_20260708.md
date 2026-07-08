# SiliconFlow GLM-4-32B Table2 next100 after GLM200 shard4

日期：2026-07-08

## 结论

- 使用模型：`THUDM/GLM-4-32B-0414`，接口：SiliconFlow OpenAI-compatible chat completions。
- API key 未写入脚本、结果或文档；本目录只保存模型返回文本和聚合指标。
- 样本复用原 `glm4_dewrap_join_glm_next100_after200_table2_shard4_20260708` 的 20 家、321 个 chunk。
- GLM 生成的 `Summary_len_proxy` mean=121.916，source Codex mean=132.436，原文 mean=132.678。
- GLM 生成的 `Redundancy_chunk_proxy` mean=33.832，原文 mean=32.176。
- GLM 的 `Relevant_score` mean=2.102，source Codex mean=2.329。

## 描述统计

| metric | glm_mean | codex_mean | paper_mean | glm_median | codex_median |
| --- | --- | --- | --- | --- | --- |
| Summary_len_proxy | 121.916 | 132.436 | 132.678 | 119.000 | 132.000 |
| Redundancy_chunk_proxy | 33.832 | 30.430 | 32.176 | 32.512 |  |
| Relevant_score | 2.102 | 2.329 |  | 1.808 | 2.354 |

## 企业层

| sec_code | sec_name | original_length_units | summary_length_units | redundancy |
| --- | --- | --- | --- | --- |
| 688683 | 莱尔科技 | 62313 | 1795 | 34.715 |
| 688636 | 智明达 | 77638 | 2242 | 34.629 |
| 688616 | 西力科技 | 54162 | 1616 | 33.516 |
| 688109 | 品茗股份 | 58262 | 1741 | 33.465 |
| 688659 | 元琛科技 | 58811 | 1772 | 33.189 |
| 688456 | 有研粉材 | 57539 | 1736 | 33.145 |
| 688661 | 和林微纳 | 50397 | 1525 | 33.047 |
| 688092 | 爱科科技 | 63026 | 1920 | 32.826 |
| 688611 | 杭州柯林 | 45545 | 1388 | 32.813 |
| 688191 | 智洋创新 | 67656 | 2126 | 31.823 |
| 688626 | 翔宇医疗 | 78095 | 2505 | 31.176 |
| 688468 | 科美诊断 | 64071 | 2058 | 31.133 |
| 688609 | 九联科技 | 108023 | 3499 | 30.873 |
| 688633 | 星球石墨 | 41495 | 1351 | 30.714 |
| 688195 | 腾景科技 | 50980 | 1674 | 30.454 |
| 688606 | 奥泰生物 | 67984 | 2258 | 30.108 |
| 688260 | 昀冢科技 | 64755 | 2179 | 29.718 |
| 688329 | 艾隆科技 | 33694 | 1155 | 29.172 |
| 688630 | 芯碁微装 | 51686 | 1915 | 26.990 |
| 688662 | 富信科技 | 68972 | 2680 | 25.736 |

## API Calls

- calls：`321`
- total tokens：`1638194`
- prompt tokens：`1567012`
- completion tokens：`71182`

## 输出

- chunk CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_after200_shard4_20260708/ipo_redundancy_chunk_with_llm_cot_v3b_len132_tight.csv`
- firm CSV：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_after200_shard4_20260708/ipo_redundancy_firm_level_cot_v3b_len132_tight.csv`
- comparison：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_after200_shard4_20260708/summary_comparison_vs_source_20260707.csv`
- call log：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/siliconflow_glm4_32b_table2_next100_after200_shard4_20260708/siliconflow_call_log_20260707.csv`
