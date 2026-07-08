# GLM Table 2 Strict Master

日期：2026-07-08

## 结论

- X label：`glm300_proxy_tailmerge1600_floor50`。
- 当前 GLM 与 Table2 471 候选交集：firm=288。
- `paper_exact_*` 主规格明确不含 `RD_Staff_ipo`；`RD_Staff_ipo` 只进入 `rd_staff_extra_*` 敏感性规格。
- 主规格控制变量：`lnN_tech + Size/Lev/ROA + Offerfee + Underwriter_ipo + Age + ScopeLen + NumIndSeg + NumProdSeg + year FE + industry FE`。
- `paper_exact_ipo_pre_fin_fe` 下：`FInvention` coef=-0.0609, t=-2.6079, p=0.0091；`BHAR` coef=-0.0213, t=-1.6421, p=0.1006；`FSales_Growth` coef=0.0153, t=0.6833, p=0.4944。
- 当前读法：BHAR 已接近原文系数且到 10% 边界附近，FSales_Growth 仍方向错误。

## Sample Audit

| step | N | missing |
|---|---|---|
| glm_table2_intersection | 288 |  |
| paper_exact_current_fin_fe | 288 |  |
| paper_exact_ipo_pre_fin_fe | 288 |  |
| rd_staff_extra_current_fin_fe | 288 |  |
| rd_staff_extra_ipo_pre_fin_fe | 288 |  |

## Paper-Exact Regressions

| spec | dep_var | N | coef | t_HC1 | p_HC1 | adj_r2 | paper_coef | paper_t | sign_match |
|---|---|---|---|---|---|---|---|---|---|
| paper_exact_current_fin_fe | FInvention | 288 | -0.0564 | -2.4160 | 0.0157 | 0.3187 | -0.0316 | -1.7200 | 1 |
| paper_exact_current_fin_fe | BHAR | 288 | -0.0216 | -1.6670 | 0.0955 | 0.1107 | -0.0188 | -2.1400 | 1 |
| paper_exact_current_fin_fe | FSales_Growth | 288 | 0.0163 | 0.7285 | 0.4663 | 0.1916 | -0.0373 | -2.0200 | 0 |
| paper_exact_ipo_pre_fin_fe | FInvention | 288 | -0.0609 | -2.6079 | 0.0091 | 0.3106 | -0.0316 | -1.7200 | 1 |
| paper_exact_ipo_pre_fin_fe | BHAR | 288 | -0.0213 | -1.6421 | 0.1006 | 0.1126 | -0.0188 | -2.1400 | 1 |
| paper_exact_ipo_pre_fin_fe | FSales_Growth | 288 | 0.0153 | 0.6833 | 0.4944 | 0.1991 | -0.0373 | -2.0200 | 0 |

## RD Staff Extra Sensitivity

| spec | dep_var | N | coef | t_HC1 | p_HC1 | adj_r2 | paper_coef | paper_t | sign_match |
|---|---|---|---|---|---|---|---|---|---|
| rd_staff_extra_current_fin_fe | FInvention | 288 | -0.0543 | -2.3870 | 0.0170 | 0.3246 | -0.0316 | -1.7200 | 1 |
| rd_staff_extra_current_fin_fe | BHAR | 288 | -0.0224 | -1.7269 | 0.0842 | 0.1129 | -0.0188 | -2.1400 | 1 |
| rd_staff_extra_current_fin_fe | FSales_Growth | 288 | 0.0165 | 0.7386 | 0.4602 | 0.1886 | -0.0373 | -2.0200 | 0 |
| rd_staff_extra_ipo_pre_fin_fe | FInvention | 288 | -0.0585 | -2.5821 | 0.0098 | 0.3176 | -0.0316 | -1.7200 | 1 |
| rd_staff_extra_ipo_pre_fin_fe | BHAR | 288 | -0.0221 | -1.7048 | 0.0882 | 0.1146 | -0.0188 | -2.1400 | 1 |
| rd_staff_extra_ipo_pre_fin_fe | FSales_Growth | 288 | 0.0158 | 0.7017 | 0.4828 | 0.1964 | -0.0373 | -2.0200 | 0 |

## Descriptives Vs Original

| variable | paper_variable | N | mean | std | median | paper_N | paper_mean | paper_std | paper_median |
|---|---|---|---|---|---|---|---|---|---|
| Redundancy | Redundancy | 288 | 30.693 | 2.537 | 30.912 | 552 | 29.074 | 2.630 | 28.910 |
| FInvention | FInvention | 288 | 2.129 | 1.134 | 2.079 | 471 | 2.282 | 1.200 | 2.197 |
| BHAR | BHAR | 288 | -0.062 | 0.554 | -0.247 | 471 | -0.036 | 0.514 | -0.170 |
| FSales_Growth | FSales_Growth | 288 | 0.372 | 1.060 | 0.215 | 471 | 0.530 | 1.522 | 0.180 |
| Size | Size | 288 | 20.666 | 0.976 | 20.507 | 552 | 20.741 | 0.990 | 20.533 |
| Lev | Lev | 288 | 0.342 | 0.168 | 0.328 | 552 | 0.356 | 0.183 | 0.334 |
| ROA | ROA | 288 | 0.110 | 0.147 | 0.110 | 552 | 0.094 | 0.145 | 0.100 |
| Size_ipo_pre | Size | 288 | 20.613 | 0.979 | 20.443 | 552 | 20.741 | 0.990 | 20.533 |
| Lev_ipo_pre | Lev | 288 | 0.342 | 0.166 | 0.328 | 552 | 0.356 | 0.183 | 0.334 |
| ROA_ipo_pre | ROA | 288 | 0.110 | 0.119 | 0.110 | 552 | 0.094 | 0.145 | 0.100 |
| Offerfee | Offerfee | 288 | 18.181 | 0.433 | 18.141 | 552 | 18.325 | 0.483 | 18.270 |
| Underwriter_ipo | Underwriter | 288 | 0.542 | 0.499 | 1.000 | 552 | 0.574 | 0.495 | 1.000 |
| Age | Age | 288 | 2.619 | 0.371 | 2.670 | 552 | 2.601 | 0.408 | 2.639 |
| ScopeLen | ScopeLen | 288 | 5.699 | 0.810 | 5.832 | 552 | 5.671 | 0.854 | 5.762 |
| NumIndSeg | NumIndSeg | 288 | 0.922 | 0.405 | 0.693 | 552 | 0.854 | 0.361 | 0.693 |
| NumProdSeg | NumProdSeg | 288 | 1.528 | 0.356 | 1.609 | 552 | 1.475 | 0.376 | 1.609 |
| RD_Staff_ipo | RD_Staff | 288 | 0.246 | 0.186 | 0.201 | 552 | 0.305 | 0.194 | 0.240 |

## Outputs

- strict master：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm_table2_strict_master_20260708/glm300_proxy_tailmerge1600_floor50_strict_master_20260708.csv`
- regressions：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm_table2_strict_master_20260708/glm300_proxy_tailmerge1600_floor50_strict_regressions_20260708.csv`
- descriptives：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm_table2_strict_master_20260708/glm300_proxy_tailmerge1600_floor50_strict_descriptives_20260708.csv`
- sample audit：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm_table2_strict_master_20260708/glm300_proxy_tailmerge1600_floor50_strict_sample_audit_20260708.csv`
