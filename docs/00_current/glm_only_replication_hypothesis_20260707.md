# GLM-only 复刻假说

日期：2026-07-07

## 结论

当前应把 `GLM-only` 从“模型差异诊断”提升为一个需要正式验证的主假说：

```text
只有用 GLM 类模型直接生成摘要与评分，
再配合短尾 chunk 合并和极短摘要 bounded repair，
才可能同时贴近原文 Table 1 描述统计和后续 Table 2 主效应。
```

这不是已经通过的结论。它的含义是：继续在 Codex 摘要上做机械 cap、floor、winsor 或摘要分母贴表，边际价值已经很低；下一步若还要救 X，应验证 GLM 全流程，而不是继续调 Codex 产物。

## 为什么这个假说现在变强

### 1. Codex 主口径贴近 Table 1，但 Table 2 不动

当前主口径是：

```text
dewrap_join + GLM tokenizer chunking + Codex cot_v3b_len132_tight
+ Summary_len_proxy
```

它能让企业层 `Redundancy` 量级接近原文，但 Table 2 主效应仍是 `NO_PASS`：

| Y | 当前 471 家 baseline coef | 原文 coef | 判断 |
|---|---:|---:|---|
| FInvention | -0.0291 | -0.0316 | 方向接近但不显著 |
| BHAR | 0.0033 | -0.0188 | 方向相反 |
| FSales_Growth | 0.0141 | -0.0373 | 方向相反 |

### 2. 对 Codex 产物修摘要右尾，仍不能恢复主效应

`tail_merge<1700 + low relevance cap80` 能把右尾描述统计推近原文：

| 口径 | Red_chunk mean | Red_chunk std | Red_chunk p75 |
|---|---:|---:|---:|
| 原文 | 32.176 | 11.730 | 37.037 |
| score18 cap80 | 32.943 | 10.776 | 36.907 |
| highshare10 cap80 | 32.701 | 10.619 | 36.236 |

但接回 471 家 Table 2 后：

| 口径 | FInvention | BHAR | FSales_Growth |
|---|---:|---:|---:|
| baseline | -0.0291 | 0.0033 | 0.0141 |
| score18 cap80 | -0.0231 | 0.0133 | 0.0116 |
| highshare10 cap80 | -0.0281 | 0.0062 | 0.0079 |

这说明：如果主效应来自摘要模型对“冗余”的语义压缩方式，而不是单纯来自长度分布，那么机械修右尾不会复刻论文。

### 3. GLM 50 家在描述统计上更像原文机制

SiliconFlow `THUDM/GLM-4-32B-0414` 的 50 家 pilot 显示，GLM 原始摘要行为和 Codex 不同。经过处理后，最接近原文 Table 1 的候选是：

```text
GLM 摘要
+ proxy 中文长度计数
+ tail_merge<2000
+ summary_floor=50
```

最佳候选 `proxy_tailmerge2000_floor50`：

| 指标 | GLM 50 处理后 | 原文 |
|---|---:|---:|
| Chunk_num mean | 18.877 | 18.191 |
| Text_len mean | 3926.576 | 3866.817 |
| Text_len std | 336.975 | 343.868 |
| Summary_len mean | 128.946 | 132.678 |
| Summary_len std | 46.064 | 39.683 |
| Redundancy_chunk mean | 33.629 | 32.176 |
| Redundancy_chunk std | 11.068 | 11.730 |
| Firm Redundancy mean | 30.215 | 29.074 |
| Firm Redundancy std | 2.974 | 2.630 |

它不是完美贴表，但比 Codex 产物的机械修复更像“模型自身产生的摘要分母机制”。

## 关键解释

原文的 X 不只是一个长度比值。它实际由三层机制共同决定：

```text
chunk 切割机制
+ 模型摘要压缩机制
+ 摘要长度计数机制
```

我们已经基本确认：

- GLM tokenizer 切 chunk 比早期 proxy 切 chunk 更合理；
- `tail_merge` 能解释大量短尾 chunk 差异；
- Codex 产物可以被机械调到贴近 Table 1，但 Table 2 不恢复；
- GLM 摘要经过 `tail_merge + floor` 后，Table 1 描述统计自然接近原文。

因此，现在最有价值的问题不是“怎么继续调 Codex 的 Summary_len”，而是：

```text
原文的摘要模型是否本来就是 GLM 类模型，
并且主效应依赖 GLM 对低信息密度文本的语义压缩方式？
```

## 不能过度解读

目前不能说“只有 GLM 能复刻”，因为：

- GLM 只有 50 家 pilot，还没有覆盖原文 552 家或 Table 2 的 471 家；
- 50 家 pilot 的 Panel B 方向成立但强度弱，`rho=-0.093, p=0.0083`；
- GLM 50 家尚未接入完整 Table 2 主回归；
- 当前 Table 2 的 `BHAR / FSales_Growth` 口径仍可能没有对齐原文。

所以准确说法是：

```text
GLM-only 是当前最值得验证的 X 机制假说；
Codex 主口径和 Codex 机械修复已经不足以解释主效应缺失。
```

## 下一步验证计划

### Step 1. 固定 GLM 流程

固定不再调 prompt：

```text
model = THUDM/GLM-4-32B-0414
chunk source = dewrap_join + GLM tokenizer chunk
length unit = proxy 中文长度
postprocess = tail_merge<2000 + summary_floor=50
```

`summary_floor=50` 只作为 bounded repair，用于处理 `无重要信息` 一类极短摘要，不直接 winsor `Redundancy_chunk`。

### Step 2. 先跑 Table 2 471 家所需样本

不要一上来全 552 家。优先覆盖已经对齐的 471 家 Table 2 样本，目标是直接检验主效应：

```text
FInvention
BHAR
FSales_Growth
```

如果 GLM X 仍不能让 `BHAR / FSales_Growth` 转为负向，基本可以判定主问题不在 X 模型。

### Step 3. 再补 552 家 Table 1 样本

如果 471 家 Table 2 有改善，再补齐 `list_date_csmar < 2023-08-15` 的 552 家 Table 1 样本，检查：

- chunk N 是否接近 8683；
- `Text_len / Summary_len / Redundancy_chunk` 是否稳定贴原文；
- 企业层 `Redundancy` 是否保持在原文量级；
- Panel B/C/D 是否比 Codex 更接近原文。

### Step 4. Gate Criteria

GLM-only 假说至少要通过：

- Table 1 描述统计不明显差于当前最佳候选；
- Panel B 低评分组 Redundancy 中位数高于高评分组；
- `FInvention` 负向且不弱于当前 Codex；
- `BHAR` 和 `FSales_Growth` 至少方向转负；
- 若 `BHAR / FSales_Growth` 仍为正，停止继续扩 GLM。

## 当前判断

`GLM-only` 值得试，但必须用 Table 2 主效应来裁决。

如果 GLM 471 家通过，说明原文 X 很可能依赖 GLM 类摘要模型本身，不能用 Codex 近似替代。

如果 GLM 471 家不通过，说明复刻失败的主因大概率在：

- `BHAR` 原文字段或窗口；
- `FSales_Growth` 原文字段或窗口；
- Table 2 样本筛选制度；
- 或原文其他未披露的数据处理细节。

届时应停止继续调 X。

## 相关文件

- GLM 50 家测度记录：`docs/00_current/siliconflow_glm4_32b_pilot50_measurement_20260707.md`
- GLM 50 家处理扫描：`docs/00_current/glm50_processing_descriptive_sweep_20260707.md`
- GLM 50 家最佳候选：`docs/00_current/glm50_tailmerge_floor_candidate_gate_20260707.md`
- Codex 摘要分母探针：`docs/00_current/summary_diagnostic_x_table2_20260707.md`
- GLM 50 结果目录：`results/glm50_tailmerge_floor_candidates_20260707/`
