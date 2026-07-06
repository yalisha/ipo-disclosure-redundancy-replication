# GLM-4 tokenizer 与 chunk 口径审计

日期：2026-07-05

## 结论

- 主人的质疑成立：当前 `char2 token_proxy = ceil(去空白字符数 / 2)` 不是 GLM-4 tokenizer。
- 使用开放 tokenizer `THUDM/glm-4-9b-chat-hf` 计数后，现有 chunk 的平均 GLM-4 tokens 为 `5297.880`，而当前 proxy 均值为 `3758.194`。
- 因此，若原文“4000 词元”指 GLM-4 tokenizer，我们当前 chunk 实际切得过大，不是过小。
- 当前 543 家业务与技术全文 GLM-4 token 总量为 `37,584,029`，高于原文 `8683 * 3866.817 ≈ 33,575,572` 的 implied token 总量。
- 用 GLM-4 tokens 按 4000 上限粗略重切，当前文本会得到约 `9666` 个 chunk，反而高于原文 `8683`。要接近原文 chunk 数，预算大约在 `4400-4500` GLM tokens。

## Tokenizer 来源

- 本次用 `transformers.AutoTokenizer.from_pretrained("THUDM/glm-4-9b-chat-hf", trust_remote_code=True)` 加载 tokenizer。
- Hugging Face 模型页：`https://huggingface.co/zai-org/glm-4-9b-chat-hf`。
- tokenizer class：`PreTrainedTokenizerFast`；vocab size：`151329`。
- 注意：这是开源 GLM-4-9B-Chat tokenizer，未必与商业 GLM-4 服务端内部 tokenizer 完全一致，但已经足以说明旧 `char2` proxy 不是同一长度单位。

## 关键统计

| 指标 | 当前 proxy | GLM-4 tokenizer |
|---|---:|---:|
| chunk 均值 | 3758.194 | 5297.880 |
| chunk 中位数 | 3940.000 | 5380.000 |
| section 总量 | 26410967 | 37584029 |
| GLM/proxy 比例均值 |  | 1.407 |

## GLM-4 预算近似网格

| budget | approx chunks | vs 原文差 | chunks/firm | weighted Chunk_num | total_glm/chunk |
|---:|---:|---:|---:|---:|---:|
| 4000 | 9666 | 983 | 17.801 | 19.402 | 3888.271 |
| 4200 | 9222 | 539 | 16.983 | 18.520 | 4075.475 |
| 4300 | 9015 | 332 | 16.602 | 18.086 | 4169.055 |
| 4400 | 8823 | 140 | 16.249 | 17.711 | 4259.779 |
| 4500 | 8619 | -64 | 15.873 | 17.294 | 4360.602 |
| 4600 | 8446 | -237 | 15.554 | 16.945 | 4449.921 |
| 4800 | 8102 | -581 | 14.921 | 16.261 | 4638.858 |
| 5000 | 7793 | -890 | 14.352 | 15.634 | 4822.793 |

## 解释

之前说“不能靠多切解决”是基于旧 proxy 的总量算术；在真正 GLM-4 tokenizer 下，这个判断要修正。现在的问题不是文本总量不足，而是 tokenizer 口径错了：现有 chunk 按 proxy 看贴近 4000，但按 GLM-4 看普遍超过 5000。

但 `9666` 仍比原文 `8683` 多约 `983` 个 chunk。进一步检查后，这个残差主要不是章节范围多抽了 12%，而是 `pdftotext -layout` 的物理断行、页码、页眉页脚直接进入 tokenizer，导致 raw layout 字符串 token 数被抬高。

## 文本规范化敏感性

同一批 543 家 section，使用 GLM-4 tokenizer 计数：

| 口径 | total tokens | mean lnN | approx chunks@4000 | firm avg chunks | weighted Chunk_num | avg tokens/chunk | 和原文关系 |
|---|---:|---:|---:|---:|---:|---:|---|
| raw layout | 37,584,029 | 11.095 | 9,666 | 17.801 | 19.402 | 3,888.271 | chunk 数明显偏高 |
| dewrap join | 33,026,541 | 10.966 | 8,534 | 15.716 | 17.122 | 3,869.995 | `lnN_tech` 与企业平均 chunk 几乎贴原文 |
| dewrap space | 35,126,365 | 11.028 | 9,058 | 16.681 | 18.165 | 3,877.938 | weighted `Chunk_num` 几乎贴原文 |
| compact | 30,820,566 | 10.898 | 7,977 | 14.691 | 15.979 | 3,863.679 | 完全去空白后偏低 |

原文关键值为：`chunks=8683`、`Text_len=3866.817`、`Chunk_num=18.191`、`lnN_tech=10.962`。因此，原文口径很可能不是 raw `pdftotext -layout`，而是介于 `dewrap join` 与 `dewrap space` 之间的正文规范化：去掉页眉页码，并合并 PDF 物理换行，但在表格/英文/数字位置是否保留空格会影响 token 数。

这也解释了“同一文本为什么 token 会变”：语义内容相同，但传给 tokenizer 的字符串不同。GLM tokenizer 会计入换行和空白；PDF layout 中大量人为断行不是原文语义内容，却会增加 token。

下一步应当先重建一个 `glm4_tokenizer_chunk_base`，不跑 LLM，只生成 section/chunk 表并对照原文 Table 1。若 chunk 数、Text_len、lnN_tech 同时接近，再决定是否小样本重跑摘要。

## 输出

- section counts：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm4_tokenizer_chunk_audit_20260705/section_glm4_token_counts_20260705.csv`
- chunk counts：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm4_tokenizer_chunk_audit_20260705/chunk_glm4_token_counts_20260705.csv`
- budget grid：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm4_tokenizer_chunk_audit_20260705/glm4_budget_grid_20260705.csv`
- normalization counts：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm4_tokenizer_chunk_audit_20260705/section_glm4_dewrap_counts_20260705.csv`
- normalization summary：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm4_tokenizer_chunk_audit_20260705/summary_glm4_text_normalization_20260705.json`
- summary：`/Users/mac/computerscience/文章复现/IPO 信息披露冗余/results/glm4_tokenizer_chunk_audit_20260705/summary_glm4_tokenizer_chunk_audit_20260705.json`
