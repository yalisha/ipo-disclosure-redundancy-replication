#!/usr/bin/env python3
"""Prepare and evaluate the 150-firm summary-length calibration pilot."""

from __future__ import annotations

import evaluate_summary_len_calibration_50_20260703 as base


base.OUT_DIR = base.ROOT / "results" / "summary_len_calibration_150_20260703"
base.DOC_PATH = base.ROOT / "docs" / "00_current" / "cot_v3b_len132_150firm_calibration_20260703.md"
base.QUOTAS = {2019: 14, 2020: 46, 2021: 51, 2022: 39}
base.ANCHOR_SAMPLE_PATH = (
    base.ROOT / "results" / "summary_len_calibration_100_20260703" / "sample_100_firms_20260703.csv"
)


if __name__ == "__main__":
    base.main()
