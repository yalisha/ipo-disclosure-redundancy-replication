# Cutoff552 And Table2 471 Probe

日期：2026-07-07

## 结论

- 判定：`NO_PASS_YET`，但样本制度线索明显增强。
- `2023-08-15` 上市日 cutoff 可以把 candidate566 精确切成原文 Table 1 的 `552` 家。
- 但 sample552 仍有 `8906` 个 chunk，原文为 8683，仍多 `223` 个 chunk；所以 cutoff 解释了 firm N，不足以单独解释 chunk N。
- 2019-2022 complete sample 中删去 `688475`、`688496`、`688525` 可以把 `474` 精确切成原文 Table 2 的 `471` 家。
- 删去这三家后，`BHAR` 和 `FSales_Growth` 仍未恢复原文显著负向；这说明 N 对齐本身不够，Y 的数据库字段/窗口口径仍是主问题。

## Table 1: 2023-08-15 Cutoff

- cutoff 规则：保留 `list_date_csmar < 2023-08-15`。
- firm N：`552`。
- chunk N：`8906`。

| scope | metric | current_N | paper_N | N_gap | current_mean | paper_mean | mean_gap | current_median | paper_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| chunk | Chunk_num | 8906 | 8683 | 223 | 17.592 | 18.191 | -0.599 | 17.000 | 16.000 |
| chunk | Text_len | 8906 | 8683 | 223 | 3793.364 | 3866.817 | -73.453 | 3967.000 | 3954.000 |
| chunk | Summary_len_proxy | 8906 | 8683 | 223 | 130.415 | 132.678 | -2.263 | 131.000 | 130.000 |
| chunk | Redundancy_chunk_proxy | 8906 | 8683 | 223 | 30.587 | 32.176 | -1.589 | 29.411 | 29.739 |
| firm | lnN_tech | 552 | 552 | 0 | 10.972 | 10.962 | 0.010 | 10.987 | 10.910 |
| firm | Redundancy_proxy | 552 | 552 | 0 | 29.090 | 29.074 | 0.016 | 28.875 | 28.910 |
| firm | Redundancy_glm4 | 552 | 552 | 0 | 24.157 | 29.074 | -4.917 | 24.030 | 28.910 |

### Excluded Late-2023 Firms

| code | sec_name_csmar | list_date_csmar | prospectus_publish_date_csmar |
| --- | --- | --- | --- |
| 688548 | 广钢气体 | 2023-08-15 00:00:00 | 2023-08-10 00:00:00 |
| 688592 | 司南导航 | 2023-08-16 00:00:00 | 2023-08-09 00:00:00 |
| 688573 | 信宇人 | 2023-08-17 00:00:00 | 2023-08-11 00:00:00 |
| 688693 | 锴威特 | 2023-08-18 00:00:00 | 2023-08-14 00:00:00 |
| 688591 | 泰凌微 | 2023-08-25 00:00:00 | 2023-08-22 00:00:00 |
| 688549 | 中巨芯 | 2023-09-08 00:00:00 | 2023-09-01 00:00:00 |
| 688702 | 盛科通信 | 2023-09-14 00:00:00 | 2023-09-08 00:00:00 |
| 688716 | 中研股份 | 2023-09-20 00:00:00 | 2023-09-15 00:00:00 |
| 688719 | 爱科赛博 | 2023-09-28 00:00:00 | 2023-09-22 00:00:00 |
| 688657 | 浩辰软件 | 2023-10-10 00:00:00 | 2023-09-27 00:00:00 |
| 688648 | 中邮科技 | 2023-11-13 00:00:00 | 2023-11-08 00:00:00 |
| 688653 | 康希通信 | 2023-11-17 00:00:00 | 2023-11-14 00:00:00 |
| 688652 | 京仪装备 | 2023-11-29 00:00:00 | 2023-11-24 00:00:00 |
| 688720 | 艾森股份 | 2023-12-06 00:00:00 | 2023-12-01 00:00:00 |

## Panel B/C/D On Sample552

| measure | B_rho | B_p | low_median_by_score_median | high_median_by_score_median | C_cluster_coef | C_cluster_p | D_cluster_coef | D_cluster_p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| proxy denominator | -0.4257 | 0.0000 | 31.7581 | 27.4345 | 0.1270 | 0.0000 | -0.1116 | 0.0000 |
| GLM4 denominator | -0.4329 | 0.0000 | 26.4000 | 22.6534 | 0.0857 | 0.0001 | -0.0876 | 0.0000 |

## Table 2: 474 To 471

- 2019-2022 common complete sample before drop：`474`。
- drop late-2022 firms 后：`471`。

### Dropped Late-2022 Firms

| code | sec_name | first_trade_date | BHAR | FSales_Growth | FInvention |
| --- | --- | --- | --- | --- | --- |
| 688475 | 萤石网络 | 2022-12-28 | 0.6514 | 0.1239 | 4.5109 |
| 688496 | 清越科技 | 2022-12-28 | 0.9969 | -0.3669 | 2.8332 |
| 688525 | 佰维存储 | 2022-12-30 | 1.5546 | 0.2027 | 4.0431 |

### Main Regression On 471

| dep_var | N | coef | t_HC1 | p_HC1 | paper_coef | paper_t | paper_N | sign_match |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FInvention | 471 | -0.0291 | -1.1562 | 0.2476 | -0.0316 | -1.7200 | 471 | 1 |
| BHAR | 471 | 0.0033 | 0.2960 | 0.7673 | -0.0188 | -2.1400 | 471 | 0 |
| FSales_Growth | 471 | 0.0141 | 0.6247 | 0.5321 | -0.0373 | -2.0200 | 471 | 0 |

### Coefficient Movement After Dropping Three Firms

| dep_var | common474_before_drop3 | common471_after_drop3 | coef_move_after_drop3 |
| --- | --- | --- | --- |
| BHAR | 0.00424 | 0.00331 | -0.00094 |
| FInvention | -0.02774 | -0.02909 | -0.00135 |
| FSales_Growth | 0.01473 | 0.01412 | -0.00061 |

## BHAR Variants On 471

| bhar_candidate | N | mean | median | coef | t_HC1 | p_HC1 | paper_mean | paper_median | paper_coef | paper_t |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BHAR | 471 | -0.0600 | -0.2226 | 0.0033 | 0.2960 | 0.7673 | -0.0360 | -0.1700 | -0.0188 | -2.1400 |
| excl_first_BHAR_ew | 471 | -0.0569 | -0.2226 | 0.0048 | 0.4176 | 0.6762 | -0.0360 | -0.1700 | -0.0188 | -2.1400 |
| excl_first_BHAR_vw | 471 | -0.3816 | -0.4702 | 0.0079 | 0.6838 | 0.4941 | -0.0360 | -0.1700 | -0.0188 | -2.1400 |
| incl_first_BHAR_ew | 471 | 1.0932 | 0.5599 | 0.0450 | 1.4278 | 0.1534 | -0.0360 | -0.1700 | -0.0188 | -2.1400 |
| incl_first_BHAR_vw | 471 | 0.7680 | 0.2391 | 0.0474 | 1.5008 | 0.1334 | -0.0360 | -0.1700 | -0.0188 | -2.1400 |
| excl_first_BHAR_ew_w1p | 471 | -0.0600 | -0.2226 | 0.0033 | 0.2960 | 0.7673 | -0.0360 | -0.1700 | -0.0188 | -2.1400 |
| excl_first_BHAR_vw_w1p | 471 | -0.3854 | -0.4702 | 0.0058 | 0.5296 | 0.5964 | -0.0360 | -0.1700 | -0.0188 | -2.1400 |
| incl_first_BHAR_ew_w1p | 471 | 1.0796 | 0.5599 | 0.0462 | 1.4936 | 0.1353 | -0.0360 | -0.1700 | -0.0188 | -2.1400 |
| incl_first_BHAR_vw_w1p | 471 | 0.7521 | 0.2391 | 0.0479 | 1.5540 | 0.1202 | -0.0360 | -0.1700 | -0.0188 | -2.1400 |

## 读法

1. `2023-08-15` cutoff 是目前最强的 Table 1 firm-level 样本解释，但不能宣称完全复刻 Table 1，因为 chunk N 仍多 223。
2. 2022 年末三家公司确实解释了 Table 2 的 `474 -> 471`，而且它们的 BHAR 很高；但删掉后 BHAR 系数只从约 0.00424 降到 0.00331，仍没有转负。
3. 当前证据支持“样本制度要按 cutoff 写入”，但不支持“样本修正即可复刻 Table 2”。下一步仍应定向找 CSMAR 现成的 BHAR/营业收入增长率字段。
4. 不建议继续扩样、改 prompt 或重做摘要。

## 输出

- sample552 firm：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/cutoff552_table2_471_probe_20260707/sample552_firm_metrics_cutoff_20260707.csv`
- sample552 chunk：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/cutoff552_table2_471_probe_20260707/sample552_chunk_metrics_cutoff_20260707.csv`
- Table 1 descriptives：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/cutoff552_table2_471_probe_20260707/sample552_table1_descriptives_vs_original_20260707.csv`
- panel tests：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/cutoff552_table2_471_probe_20260707/sample552_panel_tests_20260707.csv`
- table2 471 master：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/cutoff552_table2_471_probe_20260707/table2_471_candidate_master_20260707.csv`
- table2 regressions：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/cutoff552_table2_471_probe_20260707/table2_471_candidate_regressions_20260707.csv`
- BHAR variants：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/cutoff552_table2_471_probe_20260707/table2_471_bhar_variants_20260707.csv`
