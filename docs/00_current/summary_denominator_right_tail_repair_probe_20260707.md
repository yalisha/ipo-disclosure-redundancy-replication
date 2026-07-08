# 摘要分母与右尾机制修复模拟

日期：2026-07-07

## 问题

在 552 cutoff 样本上，`tail_merge<1600/1700` 可以把 chunk N 与 `Text_len` 分布推近原文，但 `Redundancy_chunk` 右尾仍不足：

| 口径 | chunk N | Red mean | Red std | Red median | Red p75 |
|---|---:|---:|---:|---:|---:|
| 原文 | 8683 | 32.176 | 11.730 | 29.739 | 37.037 |
| merge<1600 | 8699 | 30.970 | 8.954 | 29.548 | 34.155 |
| merge<1700 | 8679 | 30.994 | 8.933 | 29.560 | 34.162 |

结论：tail merge 修的是分子切割；右尾不足来自摘要分母机制。当前低相关 chunk 的摘要仍偏长，导致高冗余右尾不够。

## 模拟方法

不重新调用 LLM，只在 `tail_merge<1600/1700` 后模拟：

```text
若 chunk 满足低相关条件，则 Summary_len = min(Summary_len, cap)
```

这不是正式测度，只是判断“如果低相关摘要更短，描述统计能否接近原文”。

## 关键结果

### threshold=1700

| 规则 | cap chunks | Summary mean | Summary std | Red mean | Red std | Red p75 | Firm Red mean | loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| score<1.8, cap80 | 1564 | 129.006 | 38.515 | 32.943 | 10.776 | 36.907 | 30.210 | 0.043 |
| n4+n5 share<=10%, cap80 | 1541 | 129.685 | 38.214 | 32.701 | 10.619 | 36.236 | 30.050 | 0.047 |
| score<1.5, cap60 | 977 | 130.007 | 39.616 | 33.390 | 13.304 | 34.911 | 30.010 | 0.050 |
| no repair | 0 | 133.826 | 34.725 | 30.994 | 8.933 | 34.162 | 29.090 | 0.089 |

### threshold=1600

| 规则 | cap chunks | Summary mean | Summary std | Red mean | Red std | Red p75 | Firm Red mean | loss |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| score<1.8, cap80 | 1564 | 128.710 | 37.854 | 32.915 | 10.794 | 36.852 | 30.210 | 0.046 |
| n4+n5 share<=10%, cap80 | 1543 | 129.380 | 37.560 | 32.674 | 10.635 | 36.220 | 30.052 | 0.049 |
| score<1.5, cap60 | 977 | 129.708 | 38.979 | 33.360 | 13.314 | 34.890 | 30.010 | 0.053 |
| no repair | 0 | 133.519 | 34.042 | 30.970 | 8.954 | 34.155 | 29.090 | 0.091 |

## 判断

最有解释力的候选不是全局 cap，也不是 winsor，而是：

```text
tail_merge<1700
+ low-relevance short-summary repair
+ low-relevance rule: Relevant_score < 1.8 或 high-score share <= 10%
+ target summary cap: 80 proxy units
```

这个机制能同时改善：

- `Summary_len` mean/std；
- `Redundancy_chunk` mean/std/p75；
- 低相关 chunk 的高冗余右尾；
- 不需要直接 winsor `Redundancy_chunk`。

但它会把企业层 `Redundancy` mean 从约 29.09 推到约 30.05-30.21，略高于原文 29.074。因此它只能作为候选机制，必须继续看 Table 2 主效应。

## 下一步

1. 先用现有结果构造两个 diagnostic X：
   - `tail_merge1700_score18_cap80`
   - `tail_merge1700_highshare10_cap80`
2. 用这两个 X 重跑 Table 2，看 `FInvention / BHAR / FSales_Growth` 是否向原文移动。
3. 若 Table 2 有改善，再考虑真实 LLM repair：只对低相关 chunk 重摘短摘要，而不是用机械 cap。
4. 若 Table 2 仍无改善，停止在摘要分母上继续调，回到 Y 与样本制度。
