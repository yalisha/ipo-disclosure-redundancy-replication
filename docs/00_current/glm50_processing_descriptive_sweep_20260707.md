# GLM 50 家描述性统计贴近原文的切割/处理扫描

日期：2026-07-07

## 结论

- 这是一轮反推诊断，不是正式测度选择。目标是看 GLM 50 家在什么切割/处理规则下最像原文 Table 1 的描述性统计。
- 最重要的发现：`GLM-token` 摘要长度单位能让 chunk 层 `Redundancy_chunk` 均值更接近原文，但会让企业层 `Redundancy` 均值偏低。
- `proxy` 口径在企业层更接近原文，但 chunk 层 `Summary_len` 偏短、`Redundancy_chunk` 偏高。
- 短尾 chunk 的处理很关键：原文 `Text_len` 的 std=343.868，GLM 50 原始 std=545.233；说明我们当前切割保留了更多短尾 chunk。
- 极短摘要也很关键：GLM 会返回 `无重要信息` 一类 3-20 个 proxy 单位的摘要，直接把 `Redundancy_chunk` std 撑爆；`summary_floor=50` 可视为对这类异常的 bounded repair 近似。
- 仅靠切割/处理无法同时让 chunk 层和企业层全部贴原文；要么像 chunk 层，要么像企业层。这支持“原文长度单位/切割规则仍未完全对齐”的判断。

## 原文目标

| 层级 | 指标 | mean | std | p25 | median | p75 |
|---|---|---:|---:|---:|---:|---:|
| chunk | Chunk_num | 18.191 | 6.983 | 13.000 | 16.000 | 22.000 |
| chunk | Text_len | 3866.817 | 343.868 | 3888.000 | 3954.000 | 3985.000 |
| chunk | Summary_len | 132.678 | 39.683 | 105.000 | 130.000 | 158.000 |
| chunk | Redundancy_chunk | 32.176 | 11.730 | 24.356 | 29.739 | 37.037 |
| firm | lnN_tech | 10.962 | 0.350 | 10.714 | 10.910 | 11.185 |
| firm | Redundancy | 29.074 | 2.630 | 27.402 | 28.910 | 30.795 |

## Overall Top 15

| unit | process | threshold | summary_floor | red_winsor | firm_len_mode | loss_all | chunk_n | Chunk_num_mean | Text_len_mean | Summary_len_mean | Redundancy_chunk_mean | Redundancy_chunk_std | lnN_tech_mean | Redundancy_mean | Redundancy_std |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| proxy | merge_short_tail | 2000 | 50.000 | none | processed_text_sum | 0.060 | 794 | 18.877 | 3926.576 | 128.946 | 33.629 | 11.068 | 10.927 | 30.215 | 2.974 |
| proxy | merge_short_tail | 2000 | 50.000 | none | original_section | 0.060 | 794 | 18.877 | 3926.576 | 128.946 | 33.629 | 11.068 | 10.927 | 30.218 | 2.975 |
| proxy | merge_short_tail | 2000 | 50.000 | 0.99 | processed_text_sum | 0.061 | 794 | 18.877 | 3926.576 | 128.946 | 33.595 | 10.932 | 10.927 | 30.215 | 2.974 |
| proxy | merge_short_tail | 2000 | 50.000 | 0.99 | original_section | 0.061 | 794 | 18.877 | 3926.576 | 128.946 | 33.595 | 10.932 | 10.927 | 30.218 | 2.975 |
| proxy | drop_any_short | 1500 | 50.000 | none | original_section | 0.061 | 804 | 18.988 | 3861.004 | 125.514 | 33.696 | 11.054 | 10.927 | 30.731 | 2.736 |
| proxy | drop_short_tail | 1500 | 50.000 | none | original_section | 0.061 | 804 | 18.988 | 3861.004 | 125.514 | 33.696 | 11.054 | 10.927 | 30.731 | 2.736 |
| proxy | merge_short_tail | 1500 | 50.000 | none | processed_text_sum | 0.061 | 804 | 18.988 | 3877.738 | 127.342 | 33.518 | 11.121 | 10.927 | 30.215 | 2.974 |
| proxy | merge_short_tail | 1500 | 50.000 | none | original_section | 0.061 | 804 | 18.988 | 3877.738 | 127.342 | 33.518 | 11.121 | 10.927 | 30.218 | 2.975 |
| proxy | drop_any_short | 1500 | 50.000 | 0.99 | original_section | 0.061 | 804 | 18.988 | 3861.004 | 125.514 | 33.661 | 10.913 | 10.927 | 30.731 | 2.736 |
| proxy | drop_short_tail | 1500 | 50.000 | 0.99 | original_section | 0.061 | 804 | 18.988 | 3861.004 | 125.514 | 33.661 | 10.913 | 10.927 | 30.731 | 2.736 |
| proxy | merge_short_tail | 1500 | 50.000 | 0.99 | processed_text_sum | 0.061 | 804 | 18.988 | 3877.738 | 127.342 | 33.482 | 10.981 | 10.927 | 30.215 | 2.974 |
| proxy | merge_short_tail | 1500 | 50.000 | 0.99 | original_section | 0.061 | 804 | 18.988 | 3877.738 | 127.342 | 33.482 | 10.981 | 10.927 | 30.218 | 2.975 |
| proxy | merge_short_tail | 2000 | 80.000 | none | processed_text_sum | 0.062 | 794 | 18.877 | 3926.576 | 130.242 | 32.532 | 8.220 | 10.927 | 29.955 | 2.762 |
| proxy | merge_short_tail | 2000 | 80.000 | 0.99 | processed_text_sum | 0.062 | 794 | 18.877 | 3926.576 | 130.242 | 32.530 | 8.216 | 10.927 | 29.955 | 2.762 |
| proxy | merge_short_tail | 2000 | 80.000 | none | original_section | 0.062 | 794 | 18.877 | 3926.576 | 130.242 | 32.532 | 8.220 | 10.927 | 29.958 | 2.763 |

## 不做 winsor 的可解释规则 Top 15

| unit | process | threshold | summary_floor | red_winsor | firm_len_mode | loss_all | chunk_n | Chunk_num_mean | Text_len_mean | Summary_len_mean | Redundancy_chunk_mean | Redundancy_chunk_std | lnN_tech_mean | Redundancy_mean | Redundancy_std |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| proxy | merge_short_tail | 2000 | 50.000 | none | processed_text_sum | 0.060 | 794 | 18.877 | 3926.576 | 128.946 | 33.629 | 11.068 | 10.927 | 30.215 | 2.974 |
| proxy | merge_short_tail | 2000 | 50.000 | none | original_section | 0.060 | 794 | 18.877 | 3926.576 | 128.946 | 33.629 | 11.068 | 10.927 | 30.218 | 2.975 |
| proxy | drop_short_tail | 1500 | 50.000 | none | original_section | 0.061 | 804 | 18.988 | 3861.004 | 125.514 | 33.696 | 11.054 | 10.927 | 30.731 | 2.736 |
| proxy | merge_short_tail | 1500 | 50.000 | none | processed_text_sum | 0.061 | 804 | 18.988 | 3877.738 | 127.342 | 33.518 | 11.121 | 10.927 | 30.215 | 2.974 |
| proxy | merge_short_tail | 1500 | 50.000 | none | original_section | 0.061 | 804 | 18.988 | 3877.738 | 127.342 | 33.518 | 11.121 | 10.927 | 30.218 | 2.975 |
| proxy | merge_short_tail | 2000 | 80.000 | none | processed_text_sum | 0.062 | 794 | 18.877 | 3926.576 | 130.242 | 32.532 | 8.220 | 10.927 | 29.955 | 2.762 |
| proxy | merge_short_tail | 2000 | 80.000 | none | original_section | 0.062 | 794 | 18.877 | 3926.576 | 130.242 | 32.532 | 8.220 | 10.927 | 29.958 | 2.763 |
| proxy | drop_short_tail | 1500 | 50.000 | none | processed_text_sum | 0.062 | 804 | 18.988 | 3861.004 | 125.514 | 33.696 | 11.054 | 10.920 | 30.528 | 2.800 |
| proxy | merge_short_tail | 2000 | 60.000 | none | processed_text_sum | 0.062 | 794 | 18.877 | 3926.576 | 129.213 | 33.302 | 9.984 | 10.927 | 30.165 | 2.933 |
| proxy | merge_short_tail | 2000 | 60.000 | none | original_section | 0.062 | 794 | 18.877 | 3926.576 | 129.213 | 33.302 | 9.984 | 10.927 | 30.168 | 2.933 |
| proxy | merge_short_tail | 1500 | 80.000 | none | processed_text_sum | 0.062 | 804 | 18.988 | 3877.738 | 128.622 | 32.434 | 8.319 | 10.927 | 29.955 | 2.762 |
| proxy | merge_short_tail | 1500 | 80.000 | none | original_section | 0.062 | 804 | 18.988 | 3877.738 | 128.622 | 32.434 | 8.319 | 10.927 | 29.958 | 2.763 |
| proxy | drop_short_tail | 1500 | 60.000 | none | original_section | 0.062 | 804 | 18.988 | 3861.004 | 125.777 | 33.373 | 9.985 | 10.927 | 30.679 | 2.691 |
| proxy | merge_short_tail | 2000 | 100.000 | none | processed_text_sum | 0.063 | 794 | 18.877 | 3926.576 | 133.016 | 31.264 | 6.461 | 10.927 | 29.384 | 2.476 |
| proxy | merge_short_tail | 2000 | 100.000 | none | original_section | 0.063 | 794 | 18.877 | 3926.576 | 133.016 | 31.264 | 6.461 | 10.927 | 29.387 | 2.476 |

## 不做 winsor 且不设 summary floor 的规则 Top 15

| unit | process | threshold | summary_floor | red_winsor | firm_len_mode | loss_all | chunk_n | Chunk_num_mean | Text_len_mean | Summary_len_mean | Redundancy_chunk_mean | Redundancy_chunk_std | lnN_tech_mean | Redundancy_mean | Redundancy_std |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| proxy | merge_short_tail | 1500 | 0.000 | none | processed_text_sum | 0.162 | 804 | 18.988 | 3877.738 | 126.954 | 36.096 | 46.253 | 10.927 | 30.289 | 3.051 |
| proxy | merge_short_tail | 1500 | 0.000 | none | original_section | 0.162 | 804 | 18.988 | 3877.738 | 126.954 | 36.096 | 46.253 | 10.927 | 30.291 | 3.051 |
| proxy | drop_short_tail | 1500 | 0.000 | none | original_section | 0.162 | 804 | 18.988 | 3861.004 | 125.126 | 36.274 | 46.226 | 10.927 | 30.807 | 2.821 |
| proxy | drop_any_short | 1500 | 0.000 | none | original_section | 0.162 | 804 | 18.988 | 3861.004 | 125.126 | 36.274 | 46.226 | 10.927 | 30.807 | 2.821 |
| proxy | merge_short_tail | 2000 | 0.000 | none | processed_text_sum | 0.162 | 794 | 18.877 | 3926.576 | 128.553 | 36.240 | 46.507 | 10.927 | 30.289 | 3.051 |
| proxy | merge_short_tail | 2000 | 0.000 | none | original_section | 0.162 | 794 | 18.877 | 3926.576 | 128.553 | 36.240 | 46.507 | 10.927 | 30.291 | 3.051 |
| proxy | drop_any_short | 1500 | 0.000 | none | processed_text_sum | 0.163 | 804 | 18.988 | 3861.004 | 125.126 | 36.274 | 46.226 | 10.920 | 30.604 | 2.884 |
| proxy | drop_short_tail | 1500 | 0.000 | none | processed_text_sum | 0.163 | 804 | 18.988 | 3861.004 | 125.126 | 36.274 | 46.226 | 10.920 | 30.604 | 2.884 |
| glm4_token | drop_any_short | 1500 | 0.000 | none | original_section | 0.164 | 804 | 18.988 | 3861.004 | 144.067 | 31.829 | 45.492 | 10.927 | 26.811 | 2.569 |
| glm4_token | drop_short_tail | 1500 | 0.000 | none | original_section | 0.164 | 804 | 18.988 | 3861.004 | 144.067 | 31.829 | 45.492 | 10.927 | 26.811 | 2.569 |
| proxy | merge_short_tail | 2500 | 0.000 | none | processed_text_sum | 0.165 | 788 | 18.817 | 3956.473 | 129.532 | 36.315 | 46.668 | 10.927 | 30.289 | 3.051 |
| proxy | merge_short_tail | 2500 | 0.000 | none | original_section | 0.165 | 788 | 18.817 | 3956.473 | 129.532 | 36.315 | 46.668 | 10.927 | 30.291 | 3.051 |
| glm4_token | drop_any_short | 1500 | 0.000 | none | processed_text_sum | 0.165 | 804 | 18.988 | 3861.004 | 144.067 | 31.829 | 45.492 | 10.920 | 26.631 | 2.593 |
| glm4_token | drop_short_tail | 1500 | 0.000 | none | processed_text_sum | 0.165 | 804 | 18.988 | 3861.004 | 144.067 | 31.829 | 45.492 | 10.920 | 26.631 | 2.593 |
| proxy | merge_short_tail | 1000 | 0.000 | none | processed_text_sum | 0.167 | 810 | 19.052 | 3849.014 | 126.014 | 35.958 | 46.117 | 10.927 | 30.289 | 3.051 |

## 不丢正文的规则 Top 15

| unit | process | threshold | summary_floor | red_winsor | firm_len_mode | loss_all | chunk_n | Chunk_num_mean | Text_len_mean | Summary_len_mean | Redundancy_chunk_mean | Redundancy_chunk_std | lnN_tech_mean | Redundancy_mean | Redundancy_std |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| proxy | merge_short_tail | 2000 | 50.000 | none | processed_text_sum | 0.060 | 794 | 18.877 | 3926.576 | 128.946 | 33.629 | 11.068 | 10.927 | 30.215 | 2.974 |
| proxy | merge_short_tail | 2000 | 50.000 | none | original_section | 0.060 | 794 | 18.877 | 3926.576 | 128.946 | 33.629 | 11.068 | 10.927 | 30.218 | 2.975 |
| proxy | merge_short_tail | 1500 | 50.000 | none | processed_text_sum | 0.061 | 804 | 18.988 | 3877.738 | 127.342 | 33.518 | 11.121 | 10.927 | 30.215 | 2.974 |
| proxy | merge_short_tail | 1500 | 50.000 | none | original_section | 0.061 | 804 | 18.988 | 3877.738 | 127.342 | 33.518 | 11.121 | 10.927 | 30.218 | 2.975 |
| proxy | merge_short_tail | 2000 | 80.000 | none | processed_text_sum | 0.062 | 794 | 18.877 | 3926.576 | 130.242 | 32.532 | 8.220 | 10.927 | 29.955 | 2.762 |
| proxy | merge_short_tail | 2000 | 80.000 | none | original_section | 0.062 | 794 | 18.877 | 3926.576 | 130.242 | 32.532 | 8.220 | 10.927 | 29.958 | 2.763 |
| proxy | merge_short_tail | 2000 | 60.000 | none | processed_text_sum | 0.062 | 794 | 18.877 | 3926.576 | 129.213 | 33.302 | 9.984 | 10.927 | 30.165 | 2.933 |
| proxy | merge_short_tail | 2000 | 60.000 | none | original_section | 0.062 | 794 | 18.877 | 3926.576 | 129.213 | 33.302 | 9.984 | 10.927 | 30.168 | 2.933 |
| proxy | merge_short_tail | 1500 | 80.000 | none | processed_text_sum | 0.062 | 804 | 18.988 | 3877.738 | 128.622 | 32.434 | 8.319 | 10.927 | 29.955 | 2.762 |
| proxy | merge_short_tail | 1500 | 80.000 | none | original_section | 0.062 | 804 | 18.988 | 3877.738 | 128.622 | 32.434 | 8.319 | 10.927 | 29.958 | 2.763 |
| proxy | merge_short_tail | 2000 | 100.000 | none | processed_text_sum | 0.063 | 794 | 18.877 | 3926.576 | 133.016 | 31.264 | 6.461 | 10.927 | 29.384 | 2.476 |
| proxy | merge_short_tail | 2000 | 100.000 | none | original_section | 0.063 | 794 | 18.877 | 3926.576 | 133.016 | 31.264 | 6.461 | 10.927 | 29.387 | 2.476 |
| proxy | merge_short_tail | 1500 | 60.000 | none | processed_text_sum | 0.063 | 804 | 18.988 | 3877.738 | 127.606 | 33.194 | 10.054 | 10.927 | 30.165 | 2.933 |
| proxy | merge_short_tail | 1500 | 60.000 | none | original_section | 0.063 | 804 | 18.988 | 3877.738 | 127.606 | 33.194 | 10.054 | 10.927 | 30.168 | 2.933 |
| proxy | merge_short_tail | 2500 | 50.000 | none | processed_text_sum | 0.063 | 788 | 18.817 | 3956.473 | 129.928 | 33.684 | 11.059 | 10.927 | 30.215 | 2.974 |

## 输出文件

- ranked sweep：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm50_processing_descriptive_sweep_20260707/glm50_processing_sweep_ranked_20260707.csv`
- top10 stats long：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm50_processing_descriptive_sweep_20260707/glm50_processing_top10_stats_long_20260707.csv`
