# FSales_Growth window sensitivity 20260706

## Purpose

This run only changes the sales-growth outcome definition. The X measurement, controls, fixed effects, and HC1 standard errors are kept aligned with the latest Table 2 audit.

Original paper benchmark for `FSales_Growth`: N=471, mean=0.530, std=1.522, p25=-0.008, median=0.180, p75=0.523; Table 2 coefficient=-0.0373, t=-2.02.

## Current Definition Check

| sample | source | window | N | mean | std | p25 | median | p75 | mean_gap | median_gap |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| w2_2019_2022 | combo | L_to_L1_total | 471 | 0.408 | 1.601 | -0.034 | 0.165 | 0.404 | -0.122 | -0.015 |

## Best Descriptive Matches

Ranked on the 2019-2022 sample, winsorized at 1/99, against the original paper's `FSales_Growth` descriptive distribution.

| source | window | N | mean | std | p25 | median | p75 | desc_distance | reg_coef | reg_t_HC1 | reg_p_HC1 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| combo | L1_to_L2_total | 470 | 0.178 | 0.450 | -0.076 | 0.132 | 0.340 | 0.888 | -0.012 | -1.047 | 0.295 |
| operating | L1_to_L2_total | 470 | 0.178 | 0.450 | -0.076 | 0.132 | 0.340 | 0.888 | -0.012 | -1.047 | 0.295 |
| total | L1_to_L2_total | 470 | 0.178 | 0.450 | -0.076 | 0.132 | 0.340 | 0.888 | -0.012 | -1.047 | 0.295 |
| combo | Lm1_to_L2_cagr | 73 | 0.447 | 1.728 | 0.036 | 0.121 | 0.279 | 1.255 | -0.078 | -0.803 | 0.422 |
| operating | Lm1_to_L2_cagr | 73 | 0.447 | 1.728 | 0.036 | 0.121 | 0.279 | 1.255 | -0.078 | -0.803 | 0.422 |
| total | Lm1_to_L2_cagr | 73 | 0.447 | 1.728 | 0.036 | 0.121 | 0.279 | 1.255 | -0.078 | -0.803 | 0.422 |
| combo | Lm1_to_L1_cagr | 74 | 1.214 | 5.772 | 0.019 | 0.162 | 0.363 | 2.733 | -0.203 | -0.710 | 0.478 |
| operating | Lm1_to_L1_cagr | 74 | 1.214 | 5.772 | 0.019 | 0.162 | 0.363 | 2.733 | -0.203 | -0.710 | 0.478 |
| total | Lm1_to_L1_cagr | 74 | 1.214 | 5.772 | 0.019 | 0.162 | 0.363 | 2.733 | -0.203 | -0.710 | 0.478 |
| combo | Lm1_to_L1_total | 74 | 37.581 | 223.084 | 0.038 | 0.350 | 0.857 | 93.763 | -9.320 | -0.807 | 0.420 |
| operating | Lm1_to_L1_total | 74 | 37.581 | 223.084 | 0.038 | 0.350 | 0.857 | 93.763 | -9.320 | -0.807 | 0.420 |
| total | Lm1_to_L1_total | 74 | 37.581 | 223.084 | 0.038 | 0.350 | 0.857 | 93.763 | -9.320 | -0.807 | 0.420 |

## Main Regression Sensitivity

Combo revenue means `operating_revenue` first, then `total_operating_revenue` fallback. Sample is 2019-2022 to match the paper's 471 outcome observations as closely as possible.

| window | model | N | coef | t_HC1 | p_HC1 | adj_r2 |
| --- | --- | --- | --- | --- | --- | --- |
| L1_to_L2_total | controls_fe_current | 466 | -0.008 | -0.741 | 0.459 | 0.054 |
| L1_to_L2_total | controls_fe_listing_year_segments | 456 | -0.012 | -1.047 | 0.295 | 0.044 |
| L1_to_L2_total | fe_text | 470 | -0.006 | -0.483 | 0.629 | 0.045 |
| L1_to_L2_total | simple | 470 | -0.009 | -0.886 | 0.376 | -0.000 |
| L_to_L1_total | controls_fe_current | 467 | 0.017 | 0.403 | 0.687 | 0.168 |
| L_to_L1_total | controls_fe_listing_year_segments | 458 | 0.030 | 0.914 | 0.361 | 0.121 |
| L_to_L1_total | fe_text | 471 | 0.028 | 0.626 | 0.531 | 0.097 |
| L_to_L1_total | simple | 471 | 0.061 | 1.493 | 0.136 | 0.004 |
| L_to_L2_cagr | controls_fe_current | 467 | -0.003 | -0.176 | 0.860 | 0.171 |
| L_to_L2_cagr | controls_fe_listing_year_segments | 456 | 0.003 | 0.226 | 0.821 | 0.122 |
| L_to_L2_cagr | fe_text | 471 | 0.004 | 0.258 | 0.796 | 0.100 |
| L_to_L2_cagr | simple | 471 | 0.012 | 0.836 | 0.403 | -0.000 |
| L_to_L2_total | controls_fe_current | 467 | -0.012 | -0.127 | 0.899 | 0.123 |
| L_to_L2_total | controls_fe_listing_year_segments | 456 | 0.016 | 0.219 | 0.827 | 0.075 |
| L_to_L2_total | fe_text | 471 | 0.019 | 0.202 | 0.840 | 0.076 |
| L_to_L2_total | simple | 471 | 0.091 | 1.066 | 0.286 | 0.001 |
| Lm1_to_L1_cagr | controls_fe_current | 74 | -0.117 | -0.474 | 0.636 | 0.095 |
| Lm1_to_L1_cagr | controls_fe_listing_year_segments | 73 | -0.203 | -0.710 | 0.478 | 0.160 |
| Lm1_to_L1_cagr | fe_text | 74 | 0.095 | 0.422 | 0.673 | -0.030 |
| Lm1_to_L1_cagr | simple | 74 | 0.168 | 0.840 | 0.401 | -0.011 |
| Lm1_to_L1_total | controls_fe_current | 74 | -5.520 | -0.565 | 0.572 | 0.076 |
| Lm1_to_L1_total | controls_fe_listing_year_segments | 73 | -9.320 | -0.807 | 0.420 | 0.154 |
| Lm1_to_L1_total | fe_text | 74 | 2.767 | 0.327 | 0.743 | -0.065 |
| Lm1_to_L1_total | simple | 74 | 5.236 | 0.734 | 0.463 | -0.012 |

## Reading

- If a window matches the descriptive distribution but keeps a positive or insignificant `Redundancy` coefficient, the issue is not just the sales-growth window.
- `L1_to_L2_total` is the strictest interpretation of a complete post-listing fiscal-year growth outcome.
- `Lm1_to_L1_total` and `Lm1_to_L1_cagr` test whether the paper may be using pre-IPO-to-post-IPO growth around listing.
- This run does not change winsorization except the standard 1/99 treatment used in the existing outcome construction.

## Outputs

- variants: `/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/fsales_growth_window_sensitivity_20260706/fsales_growth_window_variants_20260706.csv`
- descriptives: `/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/fsales_growth_window_sensitivity_20260706/fsales_growth_window_descriptives_20260706.csv`
- regressions: `/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/fsales_growth_window_sensitivity_20260706/fsales_growth_window_regressions_20260706.csv`
- ranked candidates: `/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/fsales_growth_window_sensitivity_20260706/fsales_growth_window_ranked_candidates_20260706.csv`
