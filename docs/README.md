# Docs Index

日期：2026-07-04

## 当前优先阅读

当前工作只看 `00_current/`：

- `00_current/当前状态总结与新对话交接_20260703.md`
- `00_current/交给Pro模型_当前复刻情况与问题清单_20260703.md`
- `00_current/prompt_给Pro模型_原文复刻诊断_20260703.md`
- `00_current/Pro模型网页版回复存档与复核_20260703.md`
- `00_current/cot_v3b_len132_50firm_calibration_20260703.md`
- `00_current/cot_v3b_len132_100firm_calibration_20260703.md`
- `00_current/cot_v3b_len132_150firm_calibration_20260703.md`
- `00_current/cot_v3b_len132_200firm_calibration_20260703.md`
- `00_current/表2降噪对照与543全样本scoregate_20260703.md`
- `00_current/表2窗口切分诊断_20260703.md`

## 目录结构

| 目录 | 内容 |
|---|---|
| `00_current/` | 当前状态、给外部模型的材料、最新表 2 降噪和窗口诊断 |
| `01_measurement_method/` | 冗余变量构造方法、长度单位、tailfix/scoregate 口径 |
| `02_measurement_gates/` | 25/50/100/150/200/250 家 gate 和扩样记录 |
| `03_table1_validation/` | Table 1、Panel C、描述统计和 chunk 层验证 |
| `04_table2_outcomes/` | 结果变量、外部数据、Table 2 经济后果复刻 |
| `05_handoff_archive/` | 旧 handoff、历史交接文档 |
| `06_external_review/` | Claude/老师复核材料 |
| `90_source_evidence/` | 原文官网、CNKI、附录证据快照 |
| `99_early_archive/` | 早期 prompt/QC/token_proxy 试跑归档 |

## 当前判断

当前 `cot_v3b + tailfix_bounded + scoregate` 已经完成 543 家企业层 X；新增 50/100/150/200 家 `cot_v3b_len132_tight` 试验显示，固定现有 chunking、只校准摘要长度，可以把 Table 1 量级明显拉近原文，但 strict reproduction 仍是 `NO_PASS_YET`：

- 200 家长度校准后 `Summary_len` mean=126.469、`Redundancy_chunk` mean=31.264、企业层 `Redundancy` mean=29.823，已接近原文量级；
- Panel B 与 Panel D 仍成立，说明长度校准没有破坏核心构念效度；
- Table 1 Panel C 方向和量级已恢复，HC1 显著；200 家 firm cluster raw p=0.0660，drop p99 p=0.0606，已接近但仍未达到 5% 显著；
- Table 2 的三个经济后果没有复刻；
- 下一步不应直接把 `cot_v3b_len132_tight` 锁为全样本生产口径；若继续追 X validation，可再扩到 250 家确认 Panel C 是否稳定越过 5% cluster，否则转向原文样本/Y/controls 口径审计。
