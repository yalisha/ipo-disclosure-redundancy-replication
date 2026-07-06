# BHAR 官方市场收益率口径审计

日期：2026-07-06

## 这次核对的数据

- 新下载 `TRD_Year.dta`：官方年个股回报率文件，核心字段 `Yretwd`。
- 新下载 `TRD_Cndalym.dta`：官方综合日市场回报率文件，核心字段 `Cdretwdeq / Cdretwdos / Cdretwdtl`。
- 目的：检验原文“年度个股收益率减去分市场综合收益率”是否能解释我们 `BHAR` 不显著的问题。

| source | rows | sample_firm_coverage | date_min | date_max | note |
| --- | --- | --- | --- | --- | --- |
| TRD_Year | 2680 | 542 | 2019 | 2025 | official annual individual stock returns; IPO listing-year Yretwd is often missing |
| TRD_Cndalym | 9594 |  | 2019-07-29 | 2026-03-05 | official comprehensive daily market returns by composite market type |

## 构造的 BHAR 候选

- `BHAR_cnd_*`：保留我们当前的一年个股买入持有收益窗口，只把市场基准替换成 CSMAR 官方综合日市场收益率。
- `BHAR_year_L/Lp1/Lp2_*`：使用 `TRD_Year` 官方年个股收益率 `Yretwd`，再减去同日历年窗口内 CSMAR 官方综合日市场收益率。
- 综合市场类型重点测 `33/37/53/63/101/117`；收益字段测等权、流通市值加权、总市值加权。

## 与原文描述统计的距离

原文 `BHAR`：N=471, mean=-0.036, std=0.514, p25=-0.385, median=-0.170, p75=0.162。

当前变量：

| sample | variable | N | mean | std | p25 | median | p75 | distance_all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_2019_2023 | BHAR_current | 541 | -0.062 | 0.489 | -0.387 | -0.204 | 0.073 | 0.176 |
| w2_2019_2022 | BHAR_current | 474 | -0.061 | 0.506 | -0.402 | -0.219 | 0.093 | 0.168 |

2019-2022 子样本最接近原文的候选：

| sample | variable | N | mean | std | p25 | median | p75 | distance_all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| w2_2019_2022 | BHAR_current | 474 | -0.061 | 0.506 | -0.402 | -0.219 | 0.093 | 0.168 |
| w2_2019_2022 | BHAR_year_Lp1_m33_os | 474 | 0.023 | 0.507 | -0.286 | -0.130 | 0.171 | 0.213 |
| w2_2019_2022 | BHAR_year_Lp1_m101_os | 474 | 0.031 | 0.505 | -0.277 | -0.116 | 0.173 | 0.251 |
| w2_2019_2022 | BHAR_year_Lp1_m37_os | 474 | 0.032 | 0.505 | -0.276 | -0.115 | 0.174 | 0.252 |
| w2_2019_2022 | BHAR_year_Lp1_m33_tl | 474 | 0.033 | 0.507 | -0.278 | -0.118 | 0.183 | 0.256 |
| w2_2019_2022 | BHAR_year_Lp1_m63_os | 474 | 0.033 | 0.503 | -0.277 | -0.111 | 0.174 | 0.258 |
| w2_2019_2022 | BHAR_year_Lp1_m53_os | 474 | 0.033 | 0.503 | -0.277 | -0.111 | 0.174 | 0.259 |
| w2_2019_2022 | BHAR_year_Lp1_m117_os | 474 | 0.033 | 0.503 | -0.277 | -0.111 | 0.175 | 0.259 |
| w2_2019_2022 | BHAR_cnd_excl_first_252_m53_tl | 474 | -0.105 | 0.549 | -0.432 | -0.235 | 0.102 | 0.276 |
| w2_2019_2022 | BHAR_cnd_excl_first_252_m117_tl | 474 | -0.105 | 0.549 | -0.432 | -0.234 | 0.102 | 0.276 |
| w2_2019_2022 | BHAR_year_Lp1_m101_tl | 474 | 0.038 | 0.505 | -0.269 | -0.110 | 0.181 | 0.279 |
| w2_2019_2022 | BHAR_year_Lp1_m37_tl | 474 | 0.039 | 0.505 | -0.269 | -0.108 | 0.181 | 0.281 |

full 2019-2023 最接近原文的候选：

| sample | variable | N | mean | std | p25 | median | p75 | distance_all |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_2019_2023 | BHAR_year_Lp1_m33_os | 541 | -0.015 | 0.499 | -0.316 | -0.157 | 0.139 | 0.141 |
| full_2019_2023 | BHAR_year_Lp1_m101_os | 541 | -0.003 | 0.495 | -0.313 | -0.149 | 0.152 | 0.155 |
| full_2019_2023 | BHAR_year_Lp1_m37_os | 541 | -0.003 | 0.495 | -0.313 | -0.149 | 0.152 | 0.155 |
| full_2019_2023 | BHAR_year_Lp1_m33_tl | 541 | -0.004 | 0.498 | -0.307 | -0.148 | 0.149 | 0.161 |
| full_2019_2023 | BHAR_year_Lp1_m117_os | 541 | -0.002 | 0.494 | -0.307 | -0.143 | 0.152 | 0.170 |
| full_2019_2023 | BHAR_year_Lp1_m53_os | 541 | -0.001 | 0.494 | -0.308 | -0.142 | 0.151 | 0.171 |
| full_2019_2023 | BHAR_year_Lp1_m63_os | 541 | -0.002 | 0.494 | -0.308 | -0.142 | 0.151 | 0.171 |
| full_2019_2023 | BHAR_current | 541 | -0.062 | 0.489 | -0.387 | -0.204 | 0.073 | 0.176 |

## 回归方向核对

最接近原文描述统计候选的 w2 主规格：

| sample | model | dep_var | N | coef | t_HC1 | p_HC1 | adj_r2 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| w2_2019_2022 | ipo_pre_fin_controls_rd_staff | BHAR | 459 | 0.0015 | 0.1204 | 0.9042 | 0.0039 |
| w2_2019_2022 | ipo_pre_fin_controls_rd_staff | BHAR_year_Lp1_m33_os | 459 | -0.0151 | -1.1861 | 0.2356 | 0.0308 |
| w2_2019_2022 | ipo_pre_fin_controls_rd_staff | BHAR_year_Lp1_m33_tl | 459 | -0.0151 | -1.1861 | 0.2356 | 0.0290 |
| w2_2019_2022 | ipo_pre_fin_controls_rd_staff | BHAR_year_Lp1_m37_os | 459 | -0.0151 | -1.1862 | 0.2355 | 0.0226 |
| w2_2019_2022 | ipo_pre_fin_controls_rd_staff | BHAR_year_Lp1_m53_os | 459 | -0.0151 | -1.1862 | 0.2355 | 0.0161 |
| w2_2019_2022 | ipo_pre_fin_controls_rd_staff | BHAR_year_Lp1_m63_os | 459 | -0.0151 | -1.1862 | 0.2355 | 0.0161 |
| w2_2019_2022 | ipo_pre_fin_controls_rd_staff | BHAR_year_Lp1_m101_os | 459 | -0.0151 | -1.1862 | 0.2355 | 0.0222 |
| w2_2019_2022 | ipo_pre_fin_controls_rd_staff | BHAR_year_Lp1_m117_os | 459 | -0.0151 | -1.1863 | 0.2355 | 0.0158 |

w2 主规格中系数最负的候选：

| sample | model | dep_var | N | coef | t_HC1 | p_HC1 | adj_r2 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| w2_2019_2022 | ipo_pre_fin_controls_rd_staff | BHAR_year_Lp1_m117_eq | 459 | -0.0151 | -1.1870 | 0.2352 | 0.0567 |
| w2_2019_2022 | ipo_pre_fin_controls_rd_staff | BHAR_year_Lp1_m101_eq | 459 | -0.0151 | -1.1869 | 0.2353 | 0.0359 |
| w2_2019_2022 | ipo_pre_fin_controls_rd_staff | BHAR_year_Lp1_m53_eq | 459 | -0.0151 | -1.1866 | 0.2354 | 0.0567 |
| w2_2019_2022 | ipo_pre_fin_controls_rd_staff | BHAR_year_Lp1_m63_eq | 459 | -0.0151 | -1.1866 | 0.2354 | 0.0557 |
| w2_2019_2022 | ipo_pre_fin_controls_rd_staff | BHAR_year_Lp1_m33_eq | 459 | -0.0151 | -1.1864 | 0.2355 | 0.0567 |
| w2_2019_2022 | ipo_pre_fin_controls_rd_staff | BHAR_year_Lp1_m37_eq | 459 | -0.0151 | -1.1864 | 0.2355 | 0.0401 |
| w2_2019_2022 | ipo_pre_fin_controls_rd_staff | BHAR_year_Lp1_m117_tl | 459 | -0.0151 | -1.1863 | 0.2355 | 0.0143 |
| w2_2019_2022 | ipo_pre_fin_controls_rd_staff | BHAR_year_Lp1_m117_os | 459 | -0.0151 | -1.1863 | 0.2355 | 0.0158 |
| w2_2019_2022 | ipo_pre_fin_controls_rd_staff | BHAR_year_Lp1_m63_os | 459 | -0.0151 | -1.1862 | 0.2355 | 0.0161 |
| w2_2019_2022 | ipo_pre_fin_controls_rd_staff | BHAR_year_Lp1_m53_os | 459 | -0.0151 | -1.1862 | 0.2355 | 0.0161 |
| w2_2019_2022 | ipo_pre_fin_controls_rd_staff | BHAR_year_Lp1_m53_tl | 459 | -0.0151 | -1.1862 | 0.2355 | 0.0148 |
| w2_2019_2022 | ipo_pre_fin_controls_rd_staff | BHAR_year_Lp1_m63_tl | 459 | -0.0151 | -1.1862 | 0.2355 | 0.0145 |

w2 主规格中 10% 水平负向显著候选：

- 无。

## 判断

- 这两个新包确实是我们缺的官方市场收益率数据，应该保留进复现证据链。
- 但不能简单用 `TRD_Year` 替换当前 BHAR：科创板上市首年 `Yretwd` 经常缺失，`listing_year+1` 又变成日历年收益，不等同于“上市一年内买入并持有”。
- 近似原文 N 的 2019-2022 子样本里，当前 `BHAR` 仍是描述统计最贴近原文的变量；full 样本里 `listing_year+1` 年收益更贴近，但它是日历年收益，制度含义不如当前一年买入持有窗口。
- 把当前一年买入持有窗口的 market benchmark 替换成 CSMAR 官方综合日市场收益率，不能恢复负向显著；`TRD_Year` 的 `listing_year+1` 候选虽然转为负向，t 约 -1.19，仍不显著。
- 所以 `BHAR` 的未复刻不能只归因于缺官方市场收益率；更可能还涉及原文样本剔除、上市后一年窗口、年度/日度收益口径或 winsor 口径。

## 输出

- variants：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/bhar_official_market_return_audit_20260706/bhar_official_market_variants_20260706.csv`
- descriptives：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/bhar_official_market_return_audit_20260706/bhar_official_market_descriptives_20260706.csv`
- regressions：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/bhar_official_market_return_audit_20260706/bhar_official_market_regressions_20260706.csv`
- coverage：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/bhar_official_market_return_audit_20260706/bhar_official_market_source_coverage_20260706.csv`
