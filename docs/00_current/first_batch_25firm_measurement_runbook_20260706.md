# 首批 25 家科创板缺口补跑 Runbook

日期：2026-07-06

## 一句话结论

当前最该补的不是继续调 `BHAR` 或 `FSales_Growth`，而是先把 X 的样本制度拉回原文附近。国泰安 2019-2023 科创板 IPO universe 显示，当前 X master 漏了 26 家 universe 内公司，其中 25 家是 2019-07-22 首批科创板公司。它们不是文本不可得，而是旧 CNINFO 抓取窗口从 2019-07-22 开始，漏掉了 2019-07-03 至 2019-07-18 公告的招股说明书。

本轮执行顺序固定为：

```text
先归档当前审计文档并 push
再对首批 25 家运行 cot_v3b_len132_tight
跑完后再合并进入候选 X universe
```

## 为什么要补这 25 家

- CSMAR `IPO_Ipobasic` + `IPO_Cobasic` 可重建 2019-2023 科创板首次发行上市 universe：567 家。
- 当前 X master 有 543 家，其中只有 541 家属于该 universe。
- 当前 X 缺 CSMAR universe 内 26 家；其中 25 家是 2019-07-22 首批科创板公司，另 1 家是 `688287` 观典防务。
- 当前 X 还多出 `688688` 蚂蚁集团、`688717` 艾罗能源，两家不属于 2019-2023 科创板已上市 IPO universe。
- 原文 Table 1 是 552 家；如果不先解决 25 家首批缺口，后续 Table 2 的 Y/controls 调参都可能是在错误样本上打转。

## 本轮纳入测度的 25 家

```text
688001,688002,688003,688005,688006,
688007,688008,688009,688010,688011,
688012,688015,688016,688018,688019,
688020,688022,688028,688029,688033,
688066,688088,688122,688333,688388
```

这些公司已经完成文本补抓和“业务与技术”抽取：

```text
run: results/star_first_batch_missing_20260706
selected_docs: 27
downloaded: 27
all_download_status: ok
all_section_status: ok
target_25_chunk_count: 772
```

同一窗口额外选到 `688099`、`688188` 两家招股意向书。它们不是缺失清单成员，后续合并时不能重复计入。

## 每家公司 chunk 数

| sec_code | chunk_count |
| --- | ---: |
| 688001 | 34 |
| 688002 | 26 |
| 688003 | 33 |
| 688005 | 23 |
| 688006 | 26 |
| 688007 | 31 |
| 688008 | 20 |
| 688009 | 50 |
| 688010 | 25 |
| 688011 | 29 |
| 688012 | 16 |
| 688015 | 29 |
| 688016 | 26 |
| 688018 | 23 |
| 688019 | 23 |
| 688020 | 18 |
| 688022 | 35 |
| 688028 | 29 |
| 688029 | 52 |
| 688033 | 50 |
| 688066 | 32 |
| 688088 | 34 |
| 688122 | 30 |
| 688333 | 45 |
| 688388 | 33 |

## 不直接并入的样本

### 688287 观典防务

CNINFO 可找到的文本是：

```text
2022-05-24  688287  观典防务  观典防务科创板转板上市报告书
```

该文本可以抽取“业务与技术”，但它不是标准 IPO 招股说明书。当前判定是：`688287` 应优先从 IPO 招股书样本中排除，或作为转板样本单独说明。

### 688688 与 688717

这两家公司在当前 X master 中出现，但不在 CSMAR 2019-2023 科创板已上市 IPO universe 中。后续候选 universe 合并时应剔除。

## 补跑命令

本轮只跑 25 家首批缺口，不重跑 full543：

```bash
python scripts/run_ipo_redundancy_codex_cli_20260628.py \
  --run-name star_first_batch_missing_20260706 \
  --prompt-mode cot_v3b_len132_tight \
  --sec-code 688001,688002,688003,688005,688006,688007,688008,688009,688010,688011,688012,688015,688016,688018,688019,688020,688022,688028,688029,688033,688066,688088,688122,688333,688388
```

跑完后聚合：

```bash
python scripts/run_ipo_redundancy_codex_cli_20260628.py \
  --run-name star_first_batch_missing_20260706 \
  --prompt-mode cot_v3b_len132_tight \
  --aggregate-only
```

## 跑完后的合并原则

1. 从当前 full543 中剔除 `688688`、`688717`。
2. 把首批 25 家 `cot_v3b_len132_tight` 结果并入。
3. `688287` 暂不作为标准 IPO X 合并；若为了解释 CSMAR universe 差异，可单列转板样本。
4. 合并后候选标准 IPO X 样本预期约为 565 家，再继续查明为什么原文 Table 1 是 552 家。
5. 只有在补齐 X 样本后，才重新跑 Table 1 描述统计与 Table 2 的 `FInvention/BHAR/FSales_Growth`。

## Gate 读数

这轮不是新的测度 prompt gate，而是样本制度 gate。跑完后只回答三件事：

- 首批 25 家的 `Redundancy`、`Summary_len_proxy`、`lnN_tech` 是否和 full543 的量级一致；
- 合并后 X 描述统计是否仍贴近原文 Table 1；
- Table 2 的方向问题是否因首批样本缺口而明显改变。

## 当前 source of truth

- 样本链条审计：`docs/00_current/sample_and_ready_y_fields_audit_20260706.md`
- 文本缺口补抓：`docs/00_current/text_gap_backfill_probe_20260706.md`
- Table 2 当前重跑：`docs/00_current/table2_ipo_pre_controls_rerun_20260706.md`
- Y 处理断点：`docs/00_current/table2_data_processing_breakpoints_20260706.md`
