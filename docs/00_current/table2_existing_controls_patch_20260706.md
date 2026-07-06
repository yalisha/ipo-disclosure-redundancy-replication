# Table 2 existing controls patch 试跑

日期：2026-07-06

## 这次做了什么

- 用已有 `IPO_Ipobasic.Sponsfm` 重构 `Underwriter`，主口径为上市当年 IPO 募资额 Top10。
- 用已有 `STK_LISTEDCOINFOANL.BusinessScope` 构造 `ScopeLen = ln(清洗后经营范围 UTF-8 字节长度)`，同时保留字符数和 GB18030 字节长度审计。
- 没有硬造 `NumIndSeg / NumProdSeg / RD_Staff`，所以仍不是 strict original replication。

## 新变量描述统计

| variable | available | current_N | current_mean | original_N | original_mean | mean_diff_current_minus_original | current_median | original_median |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| lnN_tech | True | 543 | 10.966 | 552 | 10.962 | 0.004 | 10.979 | 10.910 |
| Redundancy | True | 543 | 28.944 | 552 | 29.074 | -0.130 | 28.815 | 28.910 |
| FInvention | True | 531 | 2.325 | 471 | 2.282 | 0.043 | 2.197 | 2.197 |
| BHAR | True | 541 | -0.062 | 471 | -0.036 | -0.026 | -0.204 | -0.170 |
| FSales_Growth | True | 538 | 0.409 | 471 | 0.530 | -0.121 | 0.156 | 0.180 |
| RD_Staff | False | 0 |  | 552 | 0.305 |  |  | 0.240 |
| Size | True | 541 | 20.779 | 552 | 20.741 | 0.038 | 20.569 | 20.533 |
| Lev | True | 541 | 0.360 | 552 | 0.356 | 0.004 | 0.337 | 0.334 |
| ROA | True | 541 | 0.091 | 552 | 0.094 | -0.003 | 0.100 | 0.100 |
| Offerfee | True | 542 | 18.327 | 552 | 18.325 | 0.002 | 18.266 | 18.270 |
| Underwriter | True | 538 | 0.632 | 552 | 0.574 | 0.058 | 1.000 | 1.000 |
| Age | True | 541 | 2.612 | 552 | 2.601 | 0.011 | 2.660 | 2.639 |
| NumIndSeg | False | 0 |  | 552 | 0.854 |  |  | 0.693 |
| NumProdSeg | False | 0 |  | 552 | 1.475 |  |  | 1.609 |
| ScopeLen | True | 542 | 5.673 | 552 | 5.671 | 0.002 | 5.756 | 5.762 |

## Underwriter 来源审计

| variable | N | mean | original_mean | source |
| --- | --- | --- | --- | --- |
| Underwriter_old | 543.000 | 0.009 | 0.574 | previous master field |
| Underwriter_sponsfm_pool_count | 539.000 | 0.659 | 0.574 | IPO_Ipobasic.Sponsfm |
| Underwriter_sponsfm_pool_grsprc | 539.000 | 0.668 | 0.574 | IPO_Ipobasic.Sponsfm |
| Underwriter_sponsfm_pool_fltcst | 539.000 | 0.668 | 0.574 | IPO_Ipobasic.Sponsfm |
| Underwriter_sponsfm_annual_count | 538.000 | 0.669 | 0.574 | IPO_Ipobasic.Sponsfm |
| Underwriter_sponsfm_annual_grsprc | 538.000 | 0.632 | 0.574 | IPO_Ipobasic.Sponsfm |
| Underwriter_sponsfm_annual_fltcst | 538.000 | 0.673 | 0.574 | IPO_Ipobasic.Sponsfm |

## ScopeLen 来源审计

| variable | N | mean | original_mean | source |
| --- | --- | --- | --- | --- |
| ScopeLen | 542.000 | 5.673 | 5.671 | STK_LISTEDCOINFOANL.BusinessScope log(clean UTF-8 bytes) |
| ScopeLen_char | 542.000 | 4.617 | 5.671 | STK_LISTEDCOINFOANL.BusinessScope log(clean characters) |
| ScopeLen_gb18030 | 542.000 | 5.279 | 5.671 | STK_LISTEDCOINFOANL.BusinessScope log(clean GB18030 bytes) |
| ScopeLen_log1p_char | 542.000 | 4.632 | 5.671 | STK_LISTEDCOINFOANL.BusinessScope log1p(clean characters) |

## 主回归结果

| sample | model | dep_var | N | coef | t_HC1 | p_HC1 | adj_r2 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| full_by_y_available | controls_fe_repaired_underwriter | FInvention | 527 | -0.0442 | -1.8671 | 0.0619 | 0.3350 |
| full_by_y_available | controls_fe_repaired_underwriter_scope | FInvention | 527 | -0.0447 | -1.8859 | 0.0593 | 0.3352 |
| full_by_y_available | controls_fe_repaired_underwriter | BHAR | 537 | 0.0037 | 0.3540 | 0.7233 | -0.0172 |
| full_by_y_available | controls_fe_repaired_underwriter_scope | BHAR | 537 | 0.0045 | 0.4185 | 0.6756 | -0.0024 |
| full_by_y_available | controls_fe_repaired_underwriter | FSales_Growth | 534 | 0.0181 | 0.4935 | 0.6217 | 0.2036 |
| full_by_y_available | controls_fe_repaired_underwriter_scope | FSales_Growth | 534 | 0.0192 | 0.5266 | 0.5985 | 0.2049 |
| common_3y_controls_repaired_scope | controls_fe_repaired_underwriter | FInvention | 524 | -0.0440 | -1.8619 | 0.0626 | 0.3346 |
| common_3y_controls_repaired_scope | controls_fe_repaired_underwriter_scope | FInvention | 524 | -0.0445 | -1.8831 | 0.0597 | 0.3349 |
| common_3y_controls_repaired_scope | controls_fe_repaired_underwriter | BHAR | 524 | 0.0023 | 0.2177 | 0.8276 | -0.0160 |
| common_3y_controls_repaired_scope | controls_fe_repaired_underwriter_scope | BHAR | 524 | 0.0029 | 0.2711 | 0.7863 | -0.0042 |
| common_3y_controls_repaired_scope | controls_fe_repaired_underwriter | FSales_Growth | 524 | 0.0034 | 0.0999 | 0.9204 | 0.2074 |
| common_3y_controls_repaired_scope | controls_fe_repaired_underwriter_scope | FSales_Growth | 524 | 0.0043 | 0.1277 | 0.8984 | 0.2089 |

## Underwriter 变体敏感性

| model | dep_var | N | coef | t_HC1 | p_HC1 | adj_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| underwriter_variant_with_scope::Underwriter_old | FInvention | 531 | -0.0448 | -1.8979 | 0.0577 | 0.3334 |
| underwriter_variant_with_scope::Underwriter_old | BHAR | 541 | 0.0047 | 0.4395 | 0.6603 | -0.0028 |
| underwriter_variant_with_scope::Underwriter_old | FSales_Growth | 538 | 0.0226 | 0.6178 | 0.5367 | 0.2051 |
| underwriter_variant_with_scope::Underwriter_sponsfm_pool_count | FInvention | 527 | -0.0450 | -1.9023 | 0.0571 | 0.3352 |
| underwriter_variant_with_scope::Underwriter_sponsfm_pool_count | BHAR | 537 | 0.0041 | 0.3809 | 0.7033 | -0.0016 |
| underwriter_variant_with_scope::Underwriter_sponsfm_pool_count | FSales_Growth | 534 | 0.0191 | 0.5230 | 0.6010 | 0.2054 |
| underwriter_variant_with_scope::Underwriter_sponsfm_pool_grsprc | FInvention | 527 | -0.0448 | -1.8876 | 0.0591 | 0.3343 |
| underwriter_variant_with_scope::Underwriter_sponsfm_pool_grsprc | BHAR | 537 | 0.0041 | 0.3910 | 0.6958 | -0.0014 |
| underwriter_variant_with_scope::Underwriter_sponsfm_pool_grsprc | FSales_Growth | 534 | 0.0192 | 0.5275 | 0.5979 | 0.2050 |
| underwriter_variant_with_scope::Underwriter_sponsfm_annual_count | FInvention | 527 | -0.0447 | -1.8809 | 0.0600 | 0.3341 |
| underwriter_variant_with_scope::Underwriter_sponsfm_annual_count | BHAR | 537 | 0.0042 | 0.3977 | 0.6908 | -0.0048 |
| underwriter_variant_with_scope::Underwriter_sponsfm_annual_count | FSales_Growth | 534 | 0.0194 | 0.5312 | 0.5953 | 0.2055 |
| underwriter_variant_with_scope::Underwriter_sponsfm_annual_grsprc | FInvention | 527 | -0.0447 | -1.8859 | 0.0593 | 0.3352 |
| underwriter_variant_with_scope::Underwriter_sponsfm_annual_grsprc | BHAR | 537 | 0.0045 | 0.4185 | 0.6756 | -0.0024 |
| underwriter_variant_with_scope::Underwriter_sponsfm_annual_grsprc | FSales_Growth | 534 | 0.0192 | 0.5266 | 0.5985 | 0.2049 |

## 直接读法

- `Underwriter_old` 均值约 0.009，确认是错字段；`Sponsfm` 重构后主口径均值约 0.632，已回到原文 0.574 附近。
- `ScopeLen` 覆盖 542 家；字符数口径明显偏低，UTF-8 字节口径更接近原文，说明原文长度更可能是程序/数据库字节长度而非中文字符数。
- 加上这两项后，Table 2 的 `FInvention` 保持负向并达到 10% 边界显著；`BHAR` 转弱正；`FSales_Growth` 仍正。也就是说 controls patch 只救回了 Panel B 的创新列，没有单独救回原文三列。
- 下一步真正卡点是 `NumIndSeg / NumProdSeg / RD_Staff` 和 Y 口径，而不是继续调摘要长度。

## 剩余三项控制变量构造方案

原文附录定义很短，但方向清楚：`RD_Staff` 是研发人员占总员工人数比例；`NumIndSeg` 是企业业务分部数量取对数；`NumProdSeg` 是企业产品分部数量取对数。下一步不应从招股书“业务与技术”自然语言 chunk 里硬抽这三项，因为该文本会混合产品、客户、地区、专利、资质、子公司和发展战略，和原文表格式 segment count 口径不是一回事。

### NumIndSeg

- 原文定义：企业业务分部的数量，取对数值。
- 首选数据：国泰安主营业务构成/分行业、业务分部、经营分部或类似表。至少需要证券代码、报告期/会计年度、分类类型、分部名称、主营业务收入或营业收入。
- 时间口径：优先用 IPO/上市前最近一个完整会计年度，默认 `listing_year - 1` 年报口径；若下载表中有招股书最近一期报告期，再保留一个 latest-pre-listing 备选口径。
- 主构造：对每家公司在基准期内的有效业务/行业/经营分部去重计数；剔除 `合计`、`总计`、`其他业务`、`未分配`、空白分部和重复行；优先保留收入为正的分部，收入缺失但分部名称有效的行单独标记审计。
- 变量：`NumIndSeg = ln(有效业务/行业分部数)`。同时生成 `ln(1 + count)` 敏感性口径，不先替换主口径。
- 原文 Panel A 校准目标：N=552、mean=0.854、p25=0.693、median=0.693、p75=1.099。若 `ln(count)` 明显偏离而 `ln(1 + count)` 更贴近这些分位数，再切换并记录原因。

### NumProdSeg

- 原文定义：企业产品分部的数量，取对数值。
- 首选数据：国泰安主营业务构成/分产品、产品/服务构成或类似表。至少需要证券代码、报告期/会计年度、分类类型、产品或服务分部名称、主营业务收入或收入占比。
- 时间口径：与 `NumIndSeg` 保持一致，优先 `listing_year - 1` 年报口径，备选 latest-pre-listing。
- 主构造：对有效产品/服务分部去重计数；剔除 `合计`、`总计`、`其他`、`其他业务`、`未分配`、空白分部；不要把地区、客户、供应商或业务模式行误计为产品分部。
- 变量：`NumProdSeg = ln(有效产品/服务分部数)`。同步生成 `ln(1 + count)` 敏感性口径。
- 原文 Panel A 校准目标：N=552、mean=1.475、p25=1.386、median=1.609、p75=1.609。这个分布暗示多数公司约有 4-5 个产品分部；若下载数据只有粗行业大类，大概率不是原文口径。

### RD_Staff

- 原文定义：企业研发人员占总员工人数的比例。
- 首选数据：国泰安研发创新/研发人员/员工结构类表，直接取研发人员数量或研发人员占比。总员工数若同表没有，可用本地已发现的 `CG_Ybasic.Y0601b` 员工人数作分母。
- 本地可用分母线索：`/Users/mac/computerscience/第三方资料/01_数据资源/国泰安/第三方数据资源/上市公司财务信息/CG_Ybasic.xlsx` 或同名治理综合信息表中的 `Y0601b [员工人数]`。
- 时间口径：优先 IPO/上市前最近一个完整会计年度，默认 `listing_year - 1`；若研发人员表只在上市后年报出现，需要明确标记为替代口径，不能直接冒充原文。
- 主构造：`RD_Staff = 研发人员数量 / 总员工人数`。若数据源直接提供研发人员比例，先采用直接比例，再在同时有分子分母时重算校验。
- 原文 Panel A 校准目标：N=552、mean=0.305、p25=0.157、median=0.240、p75=0.411。该均值较高，说明不能用“研发支出/资产”或“技术人员/员工”替代。

### 下载与验收顺序

1. 先补下载三类表：国泰安主营业务构成-分行业/业务分部、主营业务构成-分产品、研发人员/研发投入人员结构。
2. 先只做 Panel A 描述性校准：三项变量的 N、mean、p25、median、p75 必须接近原文，再进入 Table 2。
3. 若 CSMAR segment 表无法覆盖 IPO 前口径，再考虑从招股书表格中抽取“主营业务收入按产品/行业构成”，但这只能作为 fallback，并且要单独标记来源。
4. 不把缺失的分部数量默认填成 1，除非原始表明确只有一个有效分部或产品。

## 输出

- master：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_existing_controls_patch_20260706/table2_existing_controls_patch_master_20260706.csv`
- descriptives：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_existing_controls_patch_20260706/table2_existing_controls_patch_descriptives_20260706.csv`
- regressions：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_existing_controls_patch_20260706/table2_existing_controls_patch_regressions_20260706.csv`
- source audit：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/table2_existing_controls_patch_20260706/table2_existing_controls_patch_source_audit_20260706.csv`
