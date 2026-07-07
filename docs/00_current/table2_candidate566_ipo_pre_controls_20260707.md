# Table 2 Candidate566 IPO Pre Controls Rerun

日期：2026-07-07

## 结论

- 判定：`NO_PASS_YET`。
- 这次用 candidate566 X 重建了 Table 2 master，而不是沿用旧 543 master。
- Y 文件本来就覆盖 567 家，因此首批25家的 `FInvention/BHAR/FSales_Growth` 已经可以接入。
- 完整 candidate566 下，X 描述统计继续贴原文；但 Table 2 仍不是 strict pass。
- 2019-2022 子样本 all 3 Y + ipo-pre controls complete 为 474 家，已经接近原文 Panel B 的 471 家；接下来要找 3 家精确缺口和 Table 1 多出的 14 家。

## 样本 Waterfall

| scope | step | N |
| --- | --- | --- |
| candidate566_2019_2023 | X universe | 566 |
| candidate566_2019_2023 | FInvention nonmissing | 556 |
| candidate566_2019_2023 | BHAR nonmissing | 566 |
| candidate566_2019_2023 | FSales_Growth nonmissing | 563 |
| candidate566_2019_2023 | all 3 Y nonmissing | 553 |
| candidate566_2019_2023 | ipo_pre + segment + RD staff controls complete | 549 |
| candidate566_2019_2023 | all 3 Y + ipo_pre controls complete | 539 |
| candidate566_2019_2022 | X universe | 499 |
| candidate566_2019_2022 | FInvention nonmissing | 489 |
| candidate566_2019_2022 | BHAR nonmissing | 499 |
| candidate566_2019_2022 | FSales_Growth nonmissing | 496 |
| candidate566_2019_2022 | all 3 Y nonmissing | 486 |
| candidate566_2019_2022 | ipo_pre + segment + RD staff controls complete | 484 |
| candidate566_2019_2022 | all 3 Y + ipo_pre controls complete | 474 |

## 描述统计对照

| variable | current_N | current_mean | paper_N | paper_mean | mean_gap | current_median | paper_median |
| --- | --- | --- | --- | --- | --- | --- | --- |
| lnN_tech | 566 | 10.967 | 552 | 10.962 | 0.005 | 10.981 | 10.910 |
| Redundancy | 566 | 29.053 | 552 | 29.074 | -0.021 | 28.847 | 28.910 |
| FInvention | 556 | 2.339 | 471 | 2.282 | 0.057 | 2.197 | 2.197 |
| BHAR | 566 | -0.054 | 471 | -0.036 | -0.018 | -0.198 | -0.170 |
| FSales_Growth | 563 | 0.399 | 471 | 0.530 | -0.131 | 0.155 | 0.180 |
| Size_ipo_pre | 566 | 20.748 | 552 | 20.741 | 0.007 | 20.538 | 20.533 |
| Lev_ipo_pre | 566 | 0.356 | 552 | 0.356 | 0.000 | 0.334 | 0.334 |
| ROA_ipo_pre | 566 | 0.092 | 552 | 0.094 | -0.002 | 0.100 | 0.100 |
| Offerfee | 566 | 18.324 | 552 | 18.325 | -0.001 | 18.267 | 18.270 |
| Underwriter_ipo | 564 | 0.642 | 552 | 0.574 | 0.068 | 1.000 | 1.000 |
| Age | 566 | 2.603 | 552 | 2.601 | 0.002 | 2.652 | 2.639 |
| NumIndSeg | 554 | 0.884 | 552 | 0.854 | 0.030 | 0.693 | 0.693 |
| NumProdSeg | 558 | 1.501 | 552 | 1.475 | 0.026 | 1.609 | 1.609 |
| ScopeLen | 566 | 5.669 | 552 | 5.671 | -0.002 | 5.756 | 5.762 |
| RD_Staff_ipo | 565 | 0.280 | 552 | 0.305 | -0.025 | 0.224 | 0.240 |

## 主规格 vs 原文 Panel B

| sample | model | dep_var | N | coef | t_HC1 | p_HC1 | paper_coef | paper_t | paper_N | sign_match |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| candidate566_full | ipo_pre_fin_controls_fe | FInvention | 540 | -0.0354 | -1.5893 | 0.1120 | -0.0316 | -1.7200 | 471 | True |
| candidate566_full | ipo_pre_fin_controls_fe | BHAR | 550 | 0.0082 | 0.8123 | 0.4166 | -0.0188 | -2.1400 | 471 | False |
| candidate566_full | ipo_pre_fin_controls_fe | FSales_Growth | 550 | 0.0252 | 1.0710 | 0.2842 | -0.0373 | -2.0200 | 471 | False |
| candidate566_full | ipo_pre_fin_controls_rd_staff_fe | FInvention | 539 | -0.0368 | -1.6738 | 0.0942 | -0.0316 | -1.7200 | 471 | True |
| candidate566_full | ipo_pre_fin_controls_rd_staff_fe | BHAR | 549 | 0.0079 | 0.7786 | 0.4362 | -0.0188 | -2.1400 | 471 | False |
| candidate566_full | ipo_pre_fin_controls_rd_staff_fe | FSales_Growth | 549 | 0.0248 | 1.0568 | 0.2906 | -0.0373 | -2.0200 | 471 | False |
| candidate566_2019_2022 | ipo_pre_fin_controls_fe | FInvention | 475 | -0.0257 | -1.0184 | 0.3085 | -0.0316 | -1.7200 | 471 | True |
| candidate566_2019_2022 | ipo_pre_fin_controls_fe | BHAR | 485 | 0.0059 | 0.5235 | 0.6006 | -0.0188 | -2.1400 | 471 | False |
| candidate566_2019_2022 | ipo_pre_fin_controls_fe | FSales_Growth | 485 | 0.0311 | 1.1278 | 0.2594 | -0.0373 | -2.0200 | 471 | False |
| candidate566_2019_2022 | ipo_pre_fin_controls_rd_staff_fe | FInvention | 474 | -0.0277 | -1.1071 | 0.2682 | -0.0316 | -1.7200 | 471 | True |
| candidate566_2019_2022 | ipo_pre_fin_controls_rd_staff_fe | BHAR | 484 | 0.0052 | 0.4622 | 0.6439 | -0.0188 | -2.1400 | 471 | False |
| candidate566_2019_2022 | ipo_pre_fin_controls_rd_staff_fe | FSales_Growth | 484 | 0.0304 | 1.1012 | 0.2708 | -0.0373 | -2.0200 | 471 | False |

## 直接读法

- `FInvention` 在加入首批25家后仍保持负向，但显著性和幅度取决于 controls/sample。
- `BHAR` 与 `FSales_Growth` 仍没有稳定恢复原文显著负向。
- 现在最关键的不是 X，而是：原文 Table 1 的 552 样本筛选、Table 2 的 471 样本筛选、以及 BHAR/FSales 的数据库字段定义。
- 在样本和 Y 定义没核清前，不建议继续扩展摘要或替换 prompt。

## 输出

- master：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_candidate566_ipo_pre_controls_20260707/table2_candidate566_ipo_pre_controls_master_20260707.csv`
- descriptives：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_candidate566_ipo_pre_controls_20260707/table2_candidate566_ipo_pre_controls_descriptives_20260707.csv`
- regressions：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_candidate566_ipo_pre_controls_20260707/table2_candidate566_ipo_pre_controls_regressions_20260707.csv`
- waterfall：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_candidate566_ipo_pre_controls_20260707/table2_candidate566_ipo_pre_controls_waterfall_20260707.csv`
- source audit：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_candidate566_ipo_pre_controls_20260707/table2_candidate566_ipo_pre_controls_source_audit_20260707.csv`
