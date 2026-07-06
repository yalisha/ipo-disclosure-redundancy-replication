# 样本链条与现成 Y 字段审计

日期：2026-07-06

## 直接结论

- 国泰安 `IPO_Ipobasic` 可重建 2019-2023 科创板首次发行上市 universe：567 家。
- 当前 X master 有 543 家，其中与 CSMAR 2019-2023 STAR IPO universe 有 541 家重合；缺 CSMAR universe 内 26 家，另有 2 家不属于该 universe。
- 原文 Table 1 的 552 家不是当前 543 家。现在最大风险是 X 样本没有进入原文样本制度，尤其缺 2019-07-22 首批科创板公司。
- 原文 Table 2 的 471 家，和当前 2019-2022 `FSales_Growth` 非缺失数正好一致；但加入我们当前 controls 后只剩 459 家，说明 controls 口径/缺失处理也没有完全对齐原文。
- 本地尚未发现可直接替代的“成长能力营业收入增长率”或“市场调整年个股/持有期超额收益”现成表；下一步需要定向下载，而不是继续盲试已有表。

## CSMAR 2019-2023 STAR IPO Universe

| list_year_csmar | csmar_star_ipo_universe | current_valid_x_overlap | x_missing_from_universe |
| --- | --- | --- | --- |
| 2019 | 70 | 45 | 25 |
| 2020 | 144 | 144 | 0 |
| 2021 | 162 | 162 | 0 |
| 2022 | 124 | 123 | 1 |
| 2023 | 67 | 67 | 0 |

## 当前 X 缺失的 CSMAR Universe 公司

| code | sec_name_csmar | list_date_csmar | prospectus_publish_date_csmar | sponsor |
| --- | --- | --- | --- | --- |
| 688001 | 华兴源创 | 2019-07-22 00:00:00 | 2019-07-03 | 华泰联合证券有限责任公司 |
| 688002 | 睿创微纳 | 2019-07-22 00:00:00 | 2019-07-08 | 中信证券股份有限公司 |
| 688003 | 天准科技 | 2019-07-22 00:00:00 | 2019-07-08 | 海通证券股份有限公司 |
| 688005 | 容百科技 | 2019-07-22 00:00:00 | 2019-07-16 | 中信证券股份有限公司 |
| 688006 | 杭可科技 | 2019-07-22 00:00:00 | 2019-07-09 | 国信证券股份有限公司 |
| 688007 | 光峰科技 | 2019-07-22 00:00:00 | 2019-07-16 | 华泰联合证券有限责任公司 |
| 688008 | 澜起科技 | 2019-07-22 00:00:00 | 2019-07-12 | 中信证券股份有限公司 |
| 688009 | 中国通号 | 2019-07-22 00:00:00 | 2019-07-16 | 中国国际金融股份有限公司 |
| 688010 | 福光股份 | 2019-07-22 00:00:00 | 2019-07-16 | 兴业证券股份有限公司 |
| 688011 | 新光光电 | 2019-07-22 00:00:00 | 2019-07-16 | 中信建投证券股份有限公司 |
| 688012 | 中微公司 | 2019-07-22 00:00:00 | 2019-07-16 | 海通证券股份有限公司 |
| 688015 | 交控科技 | 2019-07-22 00:00:00 | 2019-07-18 | 中国国际金融股份有限公司 |
| 688016 | 心脉医疗 | 2019-07-22 00:00:00 | 2019-07-17 | 国泰君安证券股份有限公司,华菁证券有限公司 |
| 688018 | 乐鑫科技 | 2019-07-22 00:00:00 | 2019-07-16 | 招商证券股份有限公司 |
| 688019 | 安集科技 | 2019-07-22 00:00:00 | 2019-07-16 | 申万宏源证券承销保荐有限责任公司 |
| 688020 | 方邦股份 | 2019-07-22 00:00:00 | 2019-07-18 | 华泰联合证券有限责任公司 |
| 688022 | 瀚川智能 | 2019-07-22 00:00:00 | 2019-07-18 | 安信证券股份有限公司 |
| 688028 | 沃尔德 | 2019-07-22 00:00:00 | 2019-07-18 | 中信建投证券股份有限公司 |
| 688029 | 南微医学 | 2019-07-22 00:00:00 | 2019-07-17 | 南京证券股份有限公司 |
| 688033 | 天宜上佳 | 2019-07-22 00:00:00 | 2019-07-18 | 中信建投证券股份有限公司 |
| 688066 | 航天宏图 | 2019-07-22 00:00:00 | 2019-07-18 | 国信证券股份有限公司 |
| 688088 | 虹软科技 | 2019-07-22 00:00:00 | 2019-07-17 | 中信建投证券股份有限公司,华泰联合证券有限责任公司 |
| 688122 | 西部超导 | 2019-07-22 00:00:00 | 2019-07-17 | 中信建投证券股份有限公司 |
| 688333 | 铂力特 | 2019-07-22 00:00:00 | 2019-07-16 | 中信建投证券股份有限公司 |
| 688388 | 嘉元科技 | 2019-07-22 00:00:00 | 2019-07-18 | 东兴证券股份有限公司 |
| 688287 | 观典防务 | 2022-05-25 00:00:00 | 2022-05-24 | 中信证券股份有限公司 |

## 当前 X 中不属于 CSMAR 2019-2023 STAR IPO Universe 的公司

| code | sec_name | listing_year | first_trade_date |
| --- | --- | --- | --- |
| 688688 | 蚂蚁集团 |  |  |
| 688717 | 艾罗能源 |  |  |

## Table 2 样本 Waterfall

| sample | step | N |
| --- | --- | --- |
| full_2019_2023_current_master | universe | 543 |
| full_2019_2023_current_master | Redundancy nonmissing | 543 |
| full_2019_2023_current_master | FInvention nonmissing | 531 |
| full_2019_2023_current_master | BHAR nonmissing | 541 |
| full_2019_2023_current_master | FSales_Growth nonmissing | 538 |
| full_2019_2023_current_master | all three outcomes nonmissing | 528 |
| full_2019_2023_current_master | all controls nonmissing | 524 |
| full_2019_2023_current_master | FInvention regression complete | 514 |
| full_2019_2023_current_master | BHAR regression complete | 524 |
| full_2019_2023_current_master | FSales regression complete | 524 |
| w2_2019_2022_current_master | universe | 474 |
| w2_2019_2022_current_master | Redundancy nonmissing | 474 |
| w2_2019_2022_current_master | FInvention nonmissing | 464 |
| w2_2019_2022_current_master | BHAR nonmissing | 474 |
| w2_2019_2022_current_master | FSales_Growth nonmissing | 471 |
| w2_2019_2022_current_master | all three outcomes nonmissing | 461 |
| w2_2019_2022_current_master | all controls nonmissing | 459 |
| w2_2019_2022_current_master | FInvention regression complete | 449 |
| w2_2019_2022_current_master | BHAR regression complete | 459 |
| w2_2019_2022_current_master | FSales regression complete | 459 |

## 2019-2022 Controls 缺失模式

| missing_controls | firm_count |
| --- | --- |
| NumIndSeg | 6 |
| NumIndSeg,NumProdSeg | 5 |
| Underwriter_ipo | 2 |
| NumProdSeg | 1 |
| RD_Staff_ipo | 1 |

## 现成 Y 字段库存

| source | status | usable_for | fields | note |
| --- | --- | --- | --- | --- |
| TRD_Year 年个股回报率文件 | downloaded_tested | BHAR calendar-year candidate | Yretwd, Yretnd, Ndaytrd, Yarkettype | calendar-year annual stock return; listing-year Yretwd often missing for IPO year, not direct holding-period return |
| TRD_Cndalym 综合日市场回报率文件 | downloaded_tested | market benchmark | Cdretwdeq, Cdretwdos, Cdretwdtl | official composite daily market returns; benchmark replacement did not recover BHAR significance |
| 市场调整股票周收益表 | downloaded_tested | BHAR weekly adjusted candidate | Wretwd_Mdeq/Mdos/Mdtl, Wretwd_Cmdeq/Cmdos/Cmdtl | weekly adjusted candidates were farther from paper distribution |
| 上市公司利润表 annual A | downloaded_tested | FSales_Growth hand-built | operating_revenue, total_operating_revenue | current L to L+1 distribution is closest among tested accounting-year windows |
| IPO_IpoFinancialIndex 招股前财务指标表 | downloaded_inspected | pre-IPO controls, not FSales outcome | DebtToAssetratio, ROE, AssetTurnover, etc. | does not contain post-listing sales growth; useful for controls only |
| FN_Fn048 营业收入、营业成本 | downloaded_inspected | segment controls | Fn04804 revenue by segment, Fn04806 cost by segment | segment table, not firm total post-listing sales growth variable |
| 成长能力/财务指标分析营业收入增长率 | missing_download | FSales_Growth ready-made candidate | 营业收入增长率 / operating revenue growth rate | recommended next download; may match paper better than hand-built income statement growth |
| 市场调整年个股回报率或持有期超额收益 | missing_download | BHAR ready-made candidate | annual market-adjusted return or holding-period excess return | recommended next download if available; current local annual return is not market-adjusted holding-period return |

## 下一步

1. 先补齐/判定 26 家 CSMAR universe 内但当前 X 缺失的招股书文本，尤其 2019-07-22 首批科创板公司；同时剔除 `688688`、`688717` 这类不在 2019-2023 已上市 universe 内的记录。
2. 用补齐后的 universe 重新计算 X；再按原文 552 逻辑判断哪些公司应被排除。没有这一步，Table 2 的系数不可解释。
3. 定向下载 CSMAR 成长能力/财务指标分析中的营业收入增长率字段，以及市场调整年个股回报率或持有期超额收益字段。
4. 如果现成字段仍不能恢复 `BHAR/FSales_Growth`，再考虑联系作者或把文章复现结论写成“X 可复刻、Y/样本制度不可完全复刻”。

## 输出

- universe：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/sample_and_ready_y_fields_audit_20260706/csmar_star_ipo_universe_2019_2023_20260706.csv`
- sample compare：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/sample_and_ready_y_fields_audit_20260706/sample_543_vs_csmar_universe_compare_20260706.csv`
- missing from X：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/sample_and_ready_y_fields_audit_20260706/sample_missing_from_x_20260706.csv`
- extra X：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/sample_and_ready_y_fields_audit_20260706/sample_extra_not_in_csmar_2019_2023_20260706.csv`
- Table 2 waterfall：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/sample_and_ready_y_fields_audit_20260706/table2_471_waterfall_20260706.csv`
- control missing：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/sample_and_ready_y_fields_audit_20260706/table2_control_missing_2019_2022_20260706.csv`
- ready field inventory：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/sample_and_ready_y_fields_audit_20260706/ready_y_field_inventory_20260706.csv`
