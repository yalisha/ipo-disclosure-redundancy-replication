# 文本样本缺口补抓验证

日期：2026-07-06

## 结论

- 当前 543 家 X 样本缺失的 26 家 CSMAR 科创板 universe 公司，并不是都不可得。
- 其中 25 家 2019-07-22 首批科创板公司已经通过 CNINFO 成功补抓，`download_status=ok`，`section_status=ok`。
- 这 25 家此前缺失的直接原因很明确：旧抓取脚本默认 `--start-date 2019-07-22`，而这些公司的招股说明书公告日期集中在 `2019-07-03` 到 `2019-07-18`，被时间窗漏掉。
- `688287 观典防务` 不是标准 IPO 招股说明书口径；CNINFO 对应文本是 `观典防务科创板转板上市报告书`，可以抽出“业务与技术”，但应作为转板样本单独判定，不能直接并入 IPO 招股说明书样本。

## 已执行补抓

首批科创板窗口：

```bash
python scripts/build_ipo_redundancy_base_20260628.py \
  --universe star \
  --run-name star_first_batch_missing_20260706 \
  --start-date 2019-07-01 \
  --end-date 2019-07-21 \
  --full-download \
  --page-size 50 \
  --max-chars 4000
```

输出：

```text
selected_docs=27
downloaded=27
chunks=825
```

其中属于缺失清单的 25 家：

```text
688001, 688002, 688003, 688005, 688006,
688007, 688008, 688009, 688010, 688011,
688012, 688015, 688016, 688018, 688019,
688020, 688022, 688028, 688029, 688033,
688066, 688088, 688122, 688333, 688388
```

这 25 家的 chunk 数合计：

```text
772
```

同一窗口还额外选到 2 家招股意向书：

```text
688099, 688188
```

这两家不是缺失清单成员，后续合并时不要重复计入。

## 688287 单独核查

公司名/转板关键词查询显示：

```text
2022-05-24  688287  观典防务  观典防务科创板转板上市报告书
```

已抽取验证：

```text
run: results/star_688287_transfer_20260706
download_status: ok
section_status: ok
tech_text_compact_chars: 59793
chunk_count: 19
```

判定：

```text
688287 应优先从 IPO 招股书样本中排除，或作为转板样本单独说明。
```

## 对复现路线的影响

- 现在不能再把当前 `543` 当成原文 `552` 的近似样本。
- 下一步应将首批 25 家纳入 X 测度补跑，同时剔除 `688688`、`688717` 这两个不在 CSMAR 2019-2023 科创板已上市 universe 内的记录。
- 若纳入首批 25 家并剔除 2 家额外记录，当前可进入标准 IPO universe 的 X 样本会从 `541` 变为 `566`；再排除 `688287` 转板样本后为 `565`。
- 原文 Table 1 为 `552`，说明还存在约 13 家额外样本筛选差异，需要在补跑后继续对齐。

## 下一步命令草案

先不要直接全量跑 LLM。建议先对 25 家首批样本跑 `cot_v3b_len132_tight`，再与 full543 合并成一个候选 X universe：

```bash
python scripts/run_ipo_redundancy_codex_cli_20260628.py \
  --run-name star_first_batch_missing_20260706 \
  --prompt-mode cot_v3b_len132_tight \
  --sec-code 688001,688002,688003,688005,688006,688007,688008,688009,688010,688011,688012,688015,688016,688018,688019,688020,688022,688028,688029,688033,688066,688088,688122,688333,688388
```

注意：这一步约 772 个 chunk，会消耗较多 Codex/LLM 配额，建议单独确认后再跑。

## 关键输出路径

- 首批补抓 base：`results/star_first_batch_missing_20260706/`
- 首批 sections：`results/star_first_batch_missing_20260706/ipo_business_technology_sections.csv`
- 首批 chunks：`results/star_first_batch_missing_20260706/ipo_business_technology_chunks.csv`
- 观典防务转板验证：`results/star_688287_transfer_20260706/`
