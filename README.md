# IPO Disclosure Redundancy Replication

This repository is a lightweight review package for the IPO disclosure redundancy replication project.

The current task is not to claim a finished paper replication. It is to audit whether our constructed redundancy variable is close enough to the original paper's measurement system to justify moving forward.

## Current Bottom Line

As of 2026-07-04:

- The original `cot_v3b + tailfix_bounded + scoregate` path has produced a 543-firm enterprise-level redundancy variable.
- The newer `cot_v3b_len132_tight` path now covers the full 543-firm sample and calibrates summary length while keeping the existing chunking fixed.
- On the full 543-firm sample, the measurement scale is close to the original paper:
  - `Summary_len` mean = 128.253
  - `Redundancy_chunk` mean = 30.708
  - firm-level `Redundancy` mean = 29.374
- Construct-validity checks now pass on the X-measurement side:
  - Panel B score-redundancy relation is strongly negative.
  - Panel D innovation-word-rate relation remains strongly negative.
  - Panel C is positive and significant under firm-clustered standard errors.
- Strict reproduction status remains `NO_PASS_YET`, mainly because the downstream Table 2 economic-outcome regressions are not reproduced.

## Suggested Review Order

Read these first:

1. `docs/README.md`
2. `docs/00_current/当前状态总结与新对话交接_20260703.md`
3. `docs/00_current/交给Pro模型_当前复刻情况与问题清单_20260703.md`
4. `docs/00_current/cot_v3b_len132_200firm_calibration_20260703.md`
5. `docs/00_current/cot_v3b_len132_full543_calibration_20260704.md`
6. `docs/00_current/表2降噪对照与543全样本scoregate_20260703.md`
7. `docs/00_current/表2窗口切分诊断_20260703.md`
8. `docs/00_current/prompt_给Pro模型_原文复刻诊断_20260703.md`

## Key Outputs Included

- `results/summary_len_calibration_50_20260703/`
- `results/summary_len_calibration_100_20260703/`
- `results/summary_len_calibration_150_20260703/`
- `results/summary_len_calibration_200_20260703/`
- `results/summary_len_calibration_full_543_20260704/`
- selected Table 2 regression and descriptive outputs
- current scripts needed to inspect the measurement and diagnostics
- `data/dictionaries/` innovation-disclosure dictionary files used in Panel D-style checks

## What Is Intentionally Excluded

This repository intentionally excludes heavy or sensitive artifacts:

- raw prospectus PDFs and extracted full text
- full LLM raw logs
- complete third-party database downloads
- temporary working folders
- large intermediate result directories

The excluded files remain on the local machine. This GitHub repo is meant for methodological review, not as a full raw-data archive.
