# BHAR / FSales_Growth Table 2 Waterfall

日期：2026-07-08

## 结论

- 输入 master：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm_table2_strict_master_20260708/glm300_proxy_tailmerge1600_floor50_strict_master_20260708.csv`。
- 主瀑布使用 winsorized Y：`BHAR` 与 `FSales_Growth`；同时保留 raw Y 对照来观察缩尾影响。
- `06_plus_scope_segments_paper_exact` 是 strict paper-exact 主规格；`07_plus_rd_staff_extra_not_main` 只是 RD staff 敏感性，不作为主规格。
- 当前主规格结果：`BHAR` paper-exact coef=-0.0213, t=-1.6421, p=0.1006；`FSales_Growth` paper-exact coef=0.0153, t=0.6833, p=0.4944。
- 断点读法：BHAR 从单变量到 full controls 一直为负，加入 ScopeLen/segment controls 后更接近原文；FSales_Growth 从单变量起就是正，缩尾只压低极端值但没有修正方向。

## Winsorized-Y Waterfall

| outcome | y_variant | step_order | step | N | coef | t_HC1 | p_HC1 | adj_r2 | paper_coef | paper_t |
|---|---|---|---|---|---|---|---|---|---|---|
| BHAR | winsor | 1 | 01_x_only | 288 | -0.0163 | -1.2347 | 0.2170 | 0.0021 | -0.0188 | -2.1400 |
| BHAR | winsor | 2 | 02_plus_lnn | 288 | -0.0103 | -0.8084 | 0.4189 | 0.0171 | -0.0188 | -2.1400 |
| BHAR | winsor | 3 | 03_plus_year_industry_fe | 288 | -0.0127 | -1.0326 | 0.3018 | 0.0536 | -0.0188 | -2.1400 |
| BHAR | winsor | 4 | 04_plus_fin_controls | 288 | -0.0138 | -1.1124 | 0.2660 | 0.0469 | -0.0188 | -2.1400 |
| BHAR | winsor | 5 | 05_plus_issue_underwriter_age | 288 | -0.0152 | -1.2016 | 0.2295 | 0.0633 | -0.0188 | -2.1400 |
| BHAR | winsor | 6 | 06_plus_scope_segments_paper_exact | 288 | -0.0213 | -1.6421 | 0.1006 | 0.1126 | -0.0188 | -2.1400 |
| FSales_Growth | winsor | 1 | 01_x_only | 288 | 0.0259 | 1.0788 | 0.2807 | 0.0004 | -0.0373 | -2.0200 |
| FSales_Growth | winsor | 2 | 02_plus_lnn | 288 | 0.0234 | 1.0254 | 0.3052 | -0.0022 | -0.0373 | -2.0200 |
| FSales_Growth | winsor | 3 | 03_plus_year_industry_fe | 288 | 0.0085 | 0.4667 | 0.6407 | 0.0559 | -0.0373 | -2.0200 |
| FSales_Growth | winsor | 4 | 04_plus_fin_controls | 288 | 0.0159 | 0.7513 | 0.4525 | 0.1912 | -0.0373 | -2.0200 |
| FSales_Growth | winsor | 5 | 05_plus_issue_underwriter_age | 288 | 0.0136 | 0.6500 | 0.5157 | 0.1914 | -0.0373 | -2.0200 |
| FSales_Growth | winsor | 6 | 06_plus_scope_segments_paper_exact | 288 | 0.0153 | 0.6833 | 0.4944 | 0.1991 | -0.0373 | -2.0200 |

## Raw vs Winsor At Paper-Exact Step

| outcome | raw_N | raw_coef | raw_t_HC1 | raw_p_HC1 | winsor_N | winsor_coef | winsor_t_HC1 | winsor_p_HC1 | coef_delta_winsor_minus_raw |
|---|---|---|---|---|---|---|---|---|---|
| BHAR | 288 | -0.0211 | -1.6238 | 0.1044 | 288 | -0.0213 | -1.6421 | 0.1006 | -0.0002 |
| FSales_Growth | 288 | 1.2803 | 0.9884 | 0.3230 | 288 | 0.0153 | 0.6833 | 0.4944 | -1.2650 |

## RD Staff Extra Sensitivity

| outcome | y_variant | N | coef | t_HC1 | p_HC1 | adj_r2 | paper_coef | paper_t |
|---|---|---|---|---|---|---|---|---|
| BHAR | winsor | 288 | -0.0221 | -1.7048 | 0.0882 | 0.1146 | -0.0188 | -2.1400 |
| BHAR | raw | 288 | -0.0220 | -1.6870 | 0.0916 | 0.1149 | -0.0188 | -2.1400 |
| FSales_Growth | winsor | 288 | 0.0158 | 0.7017 | 0.4828 | 0.1964 | -0.0373 | -2.0200 |
| FSales_Growth | raw | 288 | 1.2836 | 0.9869 | 0.3237 | -0.0256 | -0.0373 | -2.0200 |

## Outputs

- waterfall：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_bhar_fsales_waterfall_20260708/table2_bhar_fsales_waterfall_20260708.csv`
- delta：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_bhar_fsales_waterfall_20260708/table2_bhar_fsales_raw_vs_winsor_20260708.csv`
