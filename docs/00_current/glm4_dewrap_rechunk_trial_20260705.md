# GLM-4 dewrap 重切试验

日期：2026-07-05

## 结论

- 本轮不跑 LLM，只重建 tokenizer 口径 section/chunk base。
- `dewrap_join` 实际切出 `8706` 个 chunk，原文为 `8683`；`lnN_tech` mean=`10.966`，几乎贴原文 `10.962`。
- `dewrap_space` 实际切出 `9266` 个 chunk，weighted `Chunk_num`=`18.615`，接近原文 `18.191`，但 `lnN_tech` 偏高。
- 两个版本最大 chunk token 分别为 `3999` 和 `4000`，均满足 `<=4000`。
- 目前最像原文的主口径是 `dewrap_join + GLM tokenizer + 4000 token boundary split`；它把 chunks、Text_len、lnN_tech 同时拉回原文量级。

## Panel A 对比

| variant | variable | current N | paper N | current mean | paper mean | mean gap | current p25 | paper p25 | current median | paper median | current p75 | paper p75 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| dewrap_join | Chunk_num | 8706 | 8683 | 17.485 | 18.191 | -0.706 | 14.000 | 13.000 | 17.000 | 16.000 | 20.000 | 22.000 |
| dewrap_join | Text_len | 8706 | 8683 | 3793.173 | 3866.817 | -73.644 | 3883.000 | 3888.000 | 3967.000 | 3954.000 | 3987.000 | 3985.000 |
| dewrap_join | lnN_tech | 543 | 552 | 10.966 | 10.962 | 0.004 | 10.775 | 10.714 | 10.979 | 10.910 | 11.175 | 11.185 |
| dewrap_space | Chunk_num | 9266 | 8683 | 18.615 | 18.191 | 0.424 | 15.000 | 13.000 | 18.000 | 16.000 | 22.000 | 22.000 |
| dewrap_space | Text_len | 9266 | 8683 | 3790.443 | 3866.817 | -76.374 | 3885.000 | 3888.000 | 3965.000 | 3954.000 | 3986.000 | 3985.000 |
| dewrap_space | lnN_tech | 543 | 552 | 11.028 | 10.962 | 0.066 | 10.840 | 10.714 | 11.044 | 10.910 | 11.239 | 11.185 |

## 输出

- 总目录：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm4_dewrap_rechunk_trial_20260705`
- summary：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm4_dewrap_rechunk_trial_20260705/summary_glm4_dewrap_rechunk_trial_20260705.json`
- 对比表：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm4_dewrap_rechunk_trial_20260705/panel_a_comparison_glm4_dewrap_rechunk_20260705.csv`
- dewrap_join chunks：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm4_dewrap_rechunk_trial_20260705/dewrap_join/ipo_business_technology_chunks.csv`
- dewrap_space chunks：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm4_dewrap_rechunk_trial_20260705/dewrap_space/ipo_business_technology_chunks.csv`
