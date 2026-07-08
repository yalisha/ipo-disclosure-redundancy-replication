# BHAR / FSales_Growth Table 2 Waterfall

日期：2026-07-08

## 结论

- 输入 master：`results/glm_table2_strict_master_20260708/glm471_proxy_tailmerge1500_floor50_strict_master_20260708.csv`。
- 主瀑布使用 winsorized Y：`BHAR` 与 `FSales_Growth`；同时保留 raw Y 对照来观察缩尾影响。
- `06_plus_scope_segments_paper_exact` 是 strict paper-exact 主规格；`07_plus_rd_staff_extra_not_main` 只是 RD staff 敏感性，不作为主规格。
- 当前主规格结果：`BHAR` paper-exact coef=-0.0120, t=-1.2654, p=0.2057；`FSales_Growth` paper-exact coef=0.0156, t=0.9542, p=0.3400。
- 断点读法：BHAR 从单变量到 full controls 一直为负，加入 ScopeLen/segment controls 后更接近原文；FSales_Growth 从单变量起就是正，缩尾只压低极端值但没有修正方向。

## Winsorized-Y Waterfall

| outcome | y_variant | step_order | step | N | coef | t_HC1 | p_HC1 | adj_r2 | paper_coef | paper_t |
|---|---|---|---|---|---|---|---|---|---|---|
| BHAR | winsor | 1 | 01_x_only | 471 | -0.0103 | -1.1565 | 0.2475 | 0.0005 | -0.0188 | -2.1400 |
| BHAR | winsor | 2 | 02_plus_lnn | 471 | -0.0069 | -0.7950 | 0.4266 | 0.0091 | -0.0188 | -2.1400 |
| BHAR | winsor | 3 | 03_plus_year_industry_fe | 471 | -0.0097 | -1.0801 | 0.2801 | 0.0289 | -0.0188 | -2.1400 |
| BHAR | winsor | 4 | 04_plus_fin_controls | 471 | -0.0097 | -1.0677 | 0.2856 | 0.0224 | -0.0188 | -2.1400 |
| BHAR | winsor | 5 | 05_plus_issue_underwriter_age | 471 | -0.0105 | -1.1449 | 0.2522 | 0.0193 | -0.0188 | -2.1400 |
| BHAR | winsor | 6 | 06_plus_scope_segments_paper_exact | 471 | -0.0120 | -1.2654 | 0.2057 | 0.0277 | -0.0188 | -2.1400 |
| FSales_Growth | winsor | 1 | 01_x_only | 471 | 0.0311 | 1.7223 | 0.0850 | 0.0030 | -0.0373 | -2.0200 |
| FSales_Growth | winsor | 2 | 02_plus_lnn | 471 | 0.0272 | 1.6308 | 0.1029 | 0.0041 | -0.0373 | -2.0200 |
| FSales_Growth | winsor | 3 | 03_plus_year_industry_fe | 471 | 0.0087 | 0.6296 | 0.5289 | 0.0558 | -0.0373 | -2.0200 |
| FSales_Growth | winsor | 4 | 04_plus_fin_controls | 471 | 0.0166 | 1.0512 | 0.2932 | 0.1218 | -0.0373 | -2.0200 |
| FSales_Growth | winsor | 5 | 05_plus_issue_underwriter_age | 471 | 0.0167 | 1.0149 | 0.3102 | 0.1186 | -0.0373 | -2.0200 |
| FSales_Growth | winsor | 6 | 06_plus_scope_segments_paper_exact | 471 | 0.0156 | 0.9542 | 0.3400 | 0.1270 | -0.0373 | -2.0200 |

## Raw vs Winsor At Paper-Exact Step

| outcome | raw_N | raw_coef | raw_t_HC1 | raw_p_HC1 | winsor_N | winsor_coef | winsor_t_HC1 | winsor_p_HC1 | coef_delta_winsor_minus_raw |
|---|---|---|---|---|---|---|---|---|---|
| BHAR | 471 | -0.0107 | -1.0791 | 0.2806 | 471 | -0.0120 | -1.2654 | 0.2057 | -0.0014 |
| FSales_Growth | 471 | 1.0390 | 1.2299 | 0.2187 | 471 | 0.0156 | 0.9542 | 0.3400 | -1.0234 |

## RD Staff Extra Sensitivity

| outcome | y_variant | N | coef | t_HC1 | p_HC1 | adj_r2 | paper_coef | paper_t |
|---|---|---|---|---|---|---|---|---|
| BHAR | winsor | 471 | -0.0123 | -1.2978 | 0.1944 | 0.0260 | -0.0188 | -2.1400 |
| BHAR | raw | 471 | -0.0109 | -1.1003 | 0.2712 | 0.0243 | -0.0188 | -2.1400 |
| FSales_Growth | winsor | 471 | 0.0177 | 1.0434 | 0.2967 | 0.1298 | -0.0373 | -2.0200 |
| FSales_Growth | raw | 471 | 1.0925 | 1.2741 | 0.2026 | 0.0038 | -0.0373 | -2.0200 |

## Outputs

- waterfall：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_bhar_fsales_waterfall_20260708/glm471_table2_bhar_fsales_waterfall_20260708.csv`
- delta：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_bhar_fsales_waterfall_20260708/glm471_table2_bhar_fsales_raw_vs_winsor_20260708.csv`
