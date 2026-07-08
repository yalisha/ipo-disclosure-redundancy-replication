# GLM Table 2 Strict Master

日期：2026-07-08

## 结论

- X label：`glm471_proxy_tailmerge1500_floor50`。
- 当前 GLM 与 Table2 471 候选交集：firm=471。
- `paper_exact_*` 主规格明确不含 `RD_Staff_ipo`；`RD_Staff_ipo` 只进入 `rd_staff_extra_*` 敏感性规格。
- 主规格控制变量：`lnN_tech + Size/Lev/ROA + Offerfee + Underwriter_ipo + Age + ScopeLen + NumIndSeg + NumProdSeg + year FE + industry FE`。
- `paper_exact_ipo_pre_fin_fe` 下：`FInvention` coef=-0.0351, t=-1.8631, p=0.0624；`BHAR` coef=-0.0120, t=-1.2654, p=0.2057；`FSales_Growth` coef=0.0156, t=0.9542, p=0.3400。
- 当前读法：BHAR 已接近原文系数且到 10% 边界附近，FSales_Growth 仍方向错误。

## Sample Audit

| step | N | missing |
|---|---|---|
| glm_table2_intersection | 471 |  |
| paper_exact_current_fin_fe | 471 |  |
| paper_exact_ipo_pre_fin_fe | 471 |  |
| rd_staff_extra_current_fin_fe | 471 |  |
| rd_staff_extra_ipo_pre_fin_fe | 471 |  |

## Paper-Exact Regressions

| spec | dep_var | N | coef | t_HC1 | p_HC1 | adj_r2 | paper_coef | paper_t | sign_match |
|---|---|---|---|---|---|---|---|---|---|
| paper_exact_current_fin_fe | FInvention | 471 | -0.0301 | -1.5982 | 0.1100 | 0.3251 | -0.0316 | -1.7200 | 1 |
| paper_exact_current_fin_fe | BHAR | 471 | -0.0118 | -1.2449 | 0.2132 | 0.0274 | -0.0188 | -2.1400 | 1 |
| paper_exact_current_fin_fe | FSales_Growth | 471 | 0.0144 | 0.9368 | 0.3489 | 0.1179 | -0.0373 | -2.0200 | 0 |
| paper_exact_ipo_pre_fin_fe | FInvention | 471 | -0.0351 | -1.8631 | 0.0624 | 0.3218 | -0.0316 | -1.7200 | 1 |
| paper_exact_ipo_pre_fin_fe | BHAR | 471 | -0.0120 | -1.2654 | 0.2057 | 0.0277 | -0.0188 | -2.1400 | 1 |
| paper_exact_ipo_pre_fin_fe | FSales_Growth | 471 | 0.0156 | 0.9542 | 0.3400 | 0.1270 | -0.0373 | -2.0200 | 0 |

## RD Staff Extra Sensitivity

| spec | dep_var | N | coef | t_HC1 | p_HC1 | adj_r2 | paper_coef | paper_t | sign_match |
|---|---|---|---|---|---|---|---|---|---|
| rd_staff_extra_current_fin_fe | FInvention | 471 | -0.0269 | -1.4263 | 0.1538 | 0.3318 | -0.0316 | -1.7200 | 1 |
| rd_staff_extra_current_fin_fe | BHAR | 471 | -0.0122 | -1.2826 | 0.1996 | 0.0258 | -0.0188 | -2.1400 | 1 |
| rd_staff_extra_current_fin_fe | FSales_Growth | 471 | 0.0168 | 1.0390 | 0.2988 | 0.1216 | -0.0373 | -2.0200 | 0 |
| rd_staff_extra_ipo_pre_fin_fe | FInvention | 471 | -0.0320 | -1.7012 | 0.0889 | 0.3287 | -0.0316 | -1.7200 | 1 |
| rd_staff_extra_ipo_pre_fin_fe | BHAR | 471 | -0.0123 | -1.2978 | 0.1944 | 0.0260 | -0.0188 | -2.1400 | 1 |
| rd_staff_extra_ipo_pre_fin_fe | FSales_Growth | 471 | 0.0177 | 1.0434 | 0.2967 | 0.1298 | -0.0373 | -2.0200 | 0 |

## Descriptives Vs Original

| variable | paper_variable | N | mean | std | median | paper_N | paper_mean | paper_std | paper_median |
|---|---|---|---|---|---|---|---|---|---|
| Redundancy | Redundancy | 471 | 30.530 | 2.546 | 30.599 | 552 | 29.074 | 2.630 | 28.910 |
| FInvention | FInvention | 471 | 2.263 | 1.208 | 2.197 | 471 | 2.282 | 1.200 | 2.197 |
| BHAR | BHAR | 471 | -0.060 | 0.509 | -0.223 | 471 | -0.036 | 0.514 | -0.170 |
| FSales_Growth | FSales_Growth | 471 | 0.315 | 1.107 | 0.169 | 471 | 0.530 | 1.522 | 0.180 |
| Size | Size | 471 | 20.761 | 1.005 | 20.562 | 552 | 20.741 | 0.990 | 20.533 |
| Lev | Lev | 471 | 0.356 | 0.178 | 0.335 | 552 | 0.356 | 0.183 | 0.334 |
| ROA | ROA | 471 | 0.104 | 0.184 | 0.106 | 552 | 0.094 | 0.145 | 0.100 |
| Size_ipo_pre | Size | 471 | 20.717 | 1.001 | 20.521 | 552 | 20.741 | 0.990 | 20.533 |
| Lev_ipo_pre | Lev | 471 | 0.353 | 0.172 | 0.334 | 552 | 0.356 | 0.183 | 0.334 |
| ROA_ipo_pre | ROA | 471 | 0.102 | 0.162 | 0.105 | 552 | 0.094 | 0.145 | 0.100 |
| Offerfee | Offerfee | 471 | 18.285 | 0.483 | 18.226 | 552 | 18.325 | 0.483 | 18.270 |
| Underwriter_ipo | Underwriter | 471 | 0.607 | 0.489 | 1.000 | 552 | 0.574 | 0.495 | 1.000 |
| Age | Age | 471 | 2.609 | 0.401 | 2.668 | 552 | 2.601 | 0.408 | 2.639 |
| ScopeLen | ScopeLen | 471 | 5.718 | 0.812 | 5.823 | 552 | 5.671 | 0.854 | 5.762 |
| NumIndSeg | NumIndSeg | 471 | 0.887 | 0.372 | 0.693 | 552 | 0.854 | 0.361 | 0.693 |
| NumProdSeg | NumProdSeg | 471 | 1.503 | 0.357 | 1.609 | 552 | 1.475 | 0.376 | 1.609 |
| RD_Staff_ipo | RD_Staff | 471 | 0.270 | 0.199 | 0.213 | 552 | 0.305 | 0.194 | 0.240 |

## Outputs

- strict master：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm_table2_strict_master_20260708/glm471_proxy_tailmerge1500_floor50_strict_master_20260708.csv`
- regressions：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm_table2_strict_master_20260708/glm471_proxy_tailmerge1500_floor50_strict_regressions_20260708.csv`
- descriptives：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm_table2_strict_master_20260708/glm471_proxy_tailmerge1500_floor50_strict_descriptives_20260708.csv`
- sample audit：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm_table2_strict_master_20260708/glm471_proxy_tailmerge1500_floor50_strict_sample_audit_20260708.csv`
