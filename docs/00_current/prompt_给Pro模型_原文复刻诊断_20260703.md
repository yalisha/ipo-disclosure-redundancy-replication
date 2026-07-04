# Prompt：请 Pro 模型诊断 IPO 信息披露冗余复刻方案

请你扮演一名同时熟悉会计/金融实证、IPO 信息披露、文本分析、LLM 测量复现的 senior replication reviewer。

我会同时提供：

1. 原文全文或原文 PDF；
2. 我们当前复刻情况说明：`交给Pro模型_当前复刻情况与问题清单_20260703.md`。

请不要泛泛而谈。请基于原文和我们当前结果，判断下一步如何最大概率完成 strict reproduction。

## 背景

我们正在复刻一篇关于 IPO 信息披露冗余的文章。

原文核心变量：

```text
Redundancy = 原始“业务与技术”文本长度 / LLM 凝练后摘要长度
```

原文检验包括：

- Table 1 Panel A：chunk 层描述性统计；
- Table 1 Panel B：`Relevant_score -> Redundancy_chunk` 显著负；
- Table 1 Panel C：`Chunk_num -> Redundancy_chunk` 显著正；
- Table 1 Panel D：`Innovation_Word_Rate -> Redundancy_chunk` 显著负；
- Table 2 Panel A：企业层 X/Y 描述性统计；
- Table 2 Panel B：`Redundancy` 负向预测 `FInvention`、`BHAR`、`FSales_Growth`。

我们目前已经构造出一个 `cot_v3b + tailfix_bounded + scoregate` 版本的 Redundancy。它有一定构念效度，但 Table 2 没有复刻出来，且 Panel C 本身也没有复现。

## 关键事实

原文 Table 2 Panel A：

| 变量 | 原文 N | 原文 mean | 原文 std | 原文 p25 | 原文 median | 原文 p75 |
|---|---:|---:|---:|---:|---:|---:|
| lnN_tech | 552 | 10.962 | 0.350 | 10.714 | 10.910 | 11.185 |
| Redundancy | 552 | 29.074 | 2.630 | 27.402 | 28.910 | 30.795 |
| FInvention | 471 | 2.282 | 1.200 | 1.386 | 2.197 | 2.890 |
| BHAR | 471 | -0.036 | 0.514 | -0.385 | -0.170 | 0.162 |
| FSales_Growth | 471 | 0.530 | 1.522 | -0.008 | 0.180 | 0.523 |

我们当前 full scoregate 2019-2023：

| 变量 | 当前 N | 当前 mean | 当前 std | 当前 p25 | 当前 median | 当前 p75 | 与原文 mean 差 |
|---|---:|---:|---:|---:|---:|---:|---:|
| lnN_tech | 541 | 11.437 | 0.322 | 11.252 | 11.443 | 11.653 | +0.475 |
| Redundancy | 541 | 34.733 | 4.450 | 31.781 | 34.288 | 37.356 | +5.659 |
| FInvention | 531 | 2.325 | 1.190 | 1.609 | 2.197 | 2.996 | +0.043 |
| BHAR | 541 | -0.062 | 0.489 | -0.387 | -0.204 | 0.073 | -0.026 |
| FSales_Growth | 538 | 0.409 | 1.673 | -0.048 | 0.156 | 0.386 | -0.121 |

2019-2022 窗口 W2：

| 变量 | W2 N | W2 mean | W2 std | W2 median | W2 p75 | 与原文 mean 差 |
|---|---:|---:|---:|---:|---:|---:|
| lnN_tech | 474 | 11.459 | 0.312 | 11.470 | 11.667 | +0.497 |
| Redundancy | 474 | 34.650 | 4.363 | 34.359 | 37.283 | +5.576 |
| FInvention | 464 | 2.254 | 1.197 | 2.197 | 2.890 | -0.028 |
| BHAR | 474 | -0.061 | 0.506 | -0.219 | 0.093 | -0.025 |
| FSales_Growth | 471 | 0.408 | 1.601 | 0.165 | 0.404 | -0.122 |

原文 Panel B：

| Y | 原文 coef | 原文 t | 原文 N |
|---|---:|---:|---:|
| FInvention | -0.0316 | -1.72 | 471 |
| BHAR | -0.0188 | -2.14 | 471 |
| FSales_Growth | -0.0373 | -2.02 | 471 |

当前 full scoregate controls_fe：

| Y | 当前 N | 当前 coef | 当前 t | 当前 p |
|---|---:|---:|---:|---:|
| FInvention | 531 | 0.0029 | 0.27 | 0.786 |
| BHAR | 541 | -0.0041 | -0.79 | 0.431 |
| FSales_Growth | 538 | 0.0016 | 0.10 | 0.920 |

W2 = 2019-2022 controls_fe：

| Y | W2 N | W2 coef | W2 t | W2 p |
|---|---:|---:|---:|---:|
| FInvention | 464 | 0.0100 | 0.84 | 0.402 |
| BHAR | 474 | -0.0062 | -1.04 | 0.299 |
| FSales_Growth | 471 | 0.0122 | 0.65 | 0.513 |

## 请你完成的任务

### Task 1：从原文中抽取 exact reproduction spec

请从原文中抽取并整理：

1. `Redundancy` 的精确定义；
2. 原文如何切分 chunk；
3. `Text_len`、`Summary_len`、`lnN_tech` 的长度单位最可能是什么；
4. 原文使用的 LLM、prompt、temperature、是否有附录稳健性；
5. `Relevant_score` 如何计算；
6. `Innovation_Word_Rate` 如何计算；
7. Table 2 的样本筛选口径；
8. `FInvention`、`BHAR`、`FSales_Growth` 的定义；
9. controls、FE、winsor、标准误口径。

请用表格输出：`原文依据 / 原文口径 / 我们当前口径 / 差异风险 / 下一步修复动作`。

### Task 2：判断当前 X 是否已经能算原文 Redundancy

请重点判断：

1. 当前 `Redundancy` mean/std 明显高于原文，最可能原因是什么？
2. 当前 `lnN_tech` 高于原文约 0.48，说明长度单位/文本范围/切分哪里不一致？
3. 当前 `Summary_len` 仍低于原文，是否足以解释 Redundancy 偏高？
4. Panel C 不显著是否应该被视为“当前 X 不是原文 X”的硬证据？
5. scoregate 是否会让变量更合理但更不像原文？

请明确给出判断：

```text
当前 X = strict reproduction / approximate proxy / own constructed proxy
```

### Task 3：判断 Table 2 不复刻的主因

请在以下候选中排序，并说明证据：

1. X 测量机制仍不像原文；
2. Y 构造口径不一致；
3. controls / FE / winsor 不一致；
4. 样本筛选不一致；
5. 原文结果依赖特定模型或 prompt；
6. 我们当前样本扩展到了不同经济环境；
7. 原文本身效应弱，复刻不稳定。

### Task 4：给出最小成本复刻路线

请设计一个最小成本、可执行的复刻路线。

约束：

- 不要建议直接全样本重跑 LLM；
- 优先用 50 家或 100 家小样本做 grid；
- 目标是先复刻 Table 1，再回 Table 2；
- 不要为了表 2 显著而改变量；
- 不要把 2023 样本直接定义为错误样本。

请输出一个分阶段计划：

1. 不烧 LLM 的诊断；
2. 小样本 LLM grid；
3. Table 1 gate criteria；
4. 通过后如何扩到 W2；
5. 最终是否值得继续 strict reproduction。

### Task 5：请区分 Redundancy 与 Specificity

我们担心“冗余”与“披露具体性”混在一起。

请判断：

1. 原文 Redundancy 是否实际上混合了“低具体性”和“高冗余”？
2. 如果要做新研究，是否应同时构造 `Specificity`？
3. 若构造两个变量，怎样定义：
   - `Redundancy`
   - `Specificity`
   - `Net_Redundancy = Redundancy residualized on Specificity`
4. 这会不会偏离原文 replication？

## 输出格式

请按以下结构输出：

```text
1. Executive judgment
2. Exact original spec extracted from the paper
3. Current replication gap diagnosis
4. Why Panel C matters
5. X vs Y vs controls: likely source of failure
6. Minimum-cost next plan
7. Whether to pursue strict reproduction or pivot to own variable
8. Concrete commands / data checks we should run next
```

请务必直接、具体、可执行。不要只说“需要进一步检查”。

