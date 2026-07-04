#!/usr/bin/env python3
"""Use Codex CLI to condense IPO prospectus chunks and compute redundancy.

This is a calibration path for small samples. It avoids third-party LLM API keys,
but it still consumes the user's Codex/ChatGPT model quota.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def compact_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def token_proxy(text: str) -> int:
    return math.ceil(len(compact_text(text)) / 2)


def score_count(item: dict, key: str) -> int:
    value = item.get(key, item.get(key.upper(), 0))
    if value in ("", None):
        return 0
    return int(float(str(value).strip()))


def parse_sec_codes(values: list[str]) -> set[str]:
    codes: set[str] = set()
    for value in values:
        codes.update(part.strip() for part in value.split(",") if part.strip())
    return codes


def parse_custom_ids(values: list[str]) -> set[str]:
    ids: set[str] = set()
    for value in values:
        ids.update(part.strip() for part in value.split(",") if part.strip())
    return ids


def extract_json(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError(f"No JSON object found in Codex output: {text[:300]}")
    payload = cleaned[start : end + 1]
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        # Occasionally the model emits an extra closing brace between array
        # items: {"items":[{...}},{"custom_id":...}]}. The schema has no nested
        # item objects, so this repair is narrowly scoped to item boundaries.
        repaired = re.sub(r'\}\s*\}\s*,\s*\{\s*"custom_id"', r'},{"custom_id"', payload)
        # Occasionally the model closes the items array after the first item and
        # then continues emitting sibling item objects.
        repaired = re.sub(r'\]\s*\}\s*,\s*\{\s*"custom_id"', r',{"custom_id"', repaired)
        repaired = re.sub(r'\]\s*\}\s*\]\s*\}\s*$', r']}', repaired)
        # Occasionally the model spells sentence_count as a bare word, e.g.
        # "sentence_count": ninety. The downstream code can reconstruct this
        # from n0...n5, so preserve the item and mark the field as null.
        repaired = re.sub(
            r'("sentence_count"\s*:\s*)(?![-0-9"{\[])([^,}\n]+)',
            r"\1null",
            repaired,
        )
        return json.loads(repaired)


def parse_token_usage(text: str) -> dict[str, object]:
    usage: dict[str, object] = {
        "total_tokens": "",
        "input_tokens": "",
        "cached_tokens": "",
        "output_tokens": "",
        "reasoning_tokens": "",
        "token_usage_raw": "",
    }
    compact = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", text)
    line_match = re.search(
        r"Token usage:\s*total=([0-9,]+)\s+input=([0-9,]+)"
        r"(?:\s+\(\+\s*([0-9,]+)\s+cached\))?\s+output=([0-9,]+)"
        r"(?:\s+\(reasoning\s+([0-9,]+)\))?",
        compact,
    )
    if line_match:
        usage.update(
            {
                "total_tokens": int(line_match.group(1).replace(",", "")),
                "input_tokens": int(line_match.group(2).replace(",", "")),
                "cached_tokens": int((line_match.group(3) or "0").replace(",", "")),
                "output_tokens": int(line_match.group(4).replace(",", "")),
                "reasoning_tokens": int((line_match.group(5) or "0").replace(",", "")),
                "token_usage_raw": line_match.group(0),
            }
        )
        return usage
    old_match = re.search(r"tokens used\s+([0-9,]+)", compact, re.IGNORECASE)
    if old_match:
        usage.update(
            {
                "total_tokens": int(old_match.group(1).replace(",", "")),
                "token_usage_raw": old_match.group(0),
            }
        )
    return usage


def build_prompt(rows: pd.DataFrame, prompt_mode: str) -> str:
    items: list[str] = []
    for _, row in rows.iterrows():
        chunk_path = ROOT / str(row["chunk_file"])
        text = chunk_path.read_text(encoding="utf-8", errors="ignore")
        items.append(
            "\n".join(
                [
                    f"<chunk custom_id=\"{row['custom_id']}\">",
                    text,
                    "</chunk>",
                ]
            )
        )
    if prompt_mode == "token_proxy_v1":
        return (
            "你是招股说明书“业务与技术”章节的信息凝练员。请分别凝练下面每个 chunk。\n"
            "目标：模拟论文的 IPO 信息披露冗余识别任务，生成每个 chunk 的凝练文本。\n"
            "硬性要求：\n"
            "1. 每个 chunk 必须输出一个 summary_text，不能遗漏 custom_id。\n"
            "2. summary_text 写一段连续中文，通常 220-320 个汉字；如果原文信息密度很低，也至少写 120 个汉字。\n"
            "3. 保留对判断发行人技术实力、核心竞争力、市场地位、产品与研发能力有实质价值的信息。\n"
            "4. 尽量保留主营业务、核心产品、关键技术、研发能力、市场地位、重要客户/供应商、产能或收入等数字事实。\n"
            "5. 压缩或删除页眉页脚、模板话、重复解释、空泛形容、法规合规铺陈和无关背景。\n"
            "6. 不得新增事实，不得评价，不得输出“无”“无。”或空字符串。\n"
            "7. 只输出 JSON 对象，不要 Markdown，不要解释。\n\n"
            "JSON 结构必须是：\n"
            "{\"items\":[{\"custom_id\":\"...\",\"summary_text\":\"...\"}]}\n\n"
            + "\n\n".join(items)
        )
    if prompt_mode == "token_proxy_v2":
        return (
            "你是招股说明书“业务与技术”章节的信息凝练员。请分别凝练下面每个 chunk。\n"
            "目标：模拟论文的 IPO 信息披露冗余识别任务，生成每个 chunk 的短凝练文本。\n"
            "硬性要求：\n"
            "1. 每个 chunk 必须输出一个 summary_text，不能遗漏 custom_id。\n"
            "2. summary_text 写一段连续中文；常规 chunk 控制在 180-260 个汉字，绝对不能超过 280 个汉字。\n"
            "3. 如果原文主要是低密度行业背景、模板介绍、政策法规或重复铺陈，summary_text 控制在 90-180 个汉字。\n"
            "4. 优先保留主营业务、核心产品、关键技术、研发能力、市场地位、重要客户/供应商、产能或收入等数字事实。\n"
            "5. 删除页眉页脚、目录残留、模板话、重复解释、空泛形容、法规合规铺陈和无关背景。\n"
            "6. 不得新增事实，不得评价，不得输出“无”“无。”或空字符串。\n"
            "7. 只输出 JSON 对象，不要 Markdown，不要解释。\n\n"
            "JSON 结构必须是：\n"
            "{\"items\":[{\"custom_id\":\"...\",\"summary_text\":\"...\"}]}\n\n"
            + "\n\n".join(items)
        )
    if prompt_mode == "cot_v1":
        return (
            "你是招股说明书“业务与技术”章节的信息凝练员。请分别处理下面每个 chunk。\n"
            "目标：模拟论文的 IPO 信息披露冗余识别任务。不要做普通定长摘要，而要先按句子/信息单元重要性评分，再依据评分凝练。\n"
            "你只处理给定文本，不使用外部资料，不运行命令。\n\n"
            "对每个 chunk 必须完成以下步骤，但最终只输出 JSON，不输出评分过程或句子列表：\n"
            "1. 将文本块识别为可评分的句子或信息单元。普通正文按句号、问号、叹号、分号等切分；表格行、列表项、项目符号也可作为信息单元。\n"
            "2. 按评估 IPO 发行人价值的重要性给每个信息单元打 0-5 分。标准如下：\n"
            "   0 分：页眉页脚、目录残留、格式噪声、纯模板话、与企业价值判断无关的信息。\n"
            "   1 分：泛泛行业背景、政策铺陈、重复定义、低相关合规性表述。\n"
            "   2 分：一般业务背景、普通产品介绍、较弱的行业或经营事实。\n"
            "   3 分：主营业务、主要产品、市场应用、经营模式、客户/供应商等有用事实。\n"
            "   4 分：核心技术、研发能力、竞争优势、市场地位、收入/产能/客户集中度等重要事实。\n"
            "   5 分：高度体现技术实力、核心竞争力、市场地位或科创属性的关键事实和关键数字。\n"
            "3. 统计不同分数的信息单元数量，字段为 n0、n1、n2、n3、n4、n5；sentence_count 必须等于 n0+n1+n2+n3+n4+n5。\n"
            "4. 根据重要性水平进行文本凝练：尽可能删除低分信息，保留高分信息；不要为了凑长度而保留低分句，也不要为了压缩而删除高分关键事实。\n"
            "5. summary_text 写一段连续中文，不设固定字数上下限；若全是低密度内容，也要保留最必要的行业或业务事实，不得输出空字符串。\n"
            "6. 不得新增事实，不得评价，不得输出 Markdown。\n\n"
            "JSON 结构必须是：\n"
            "{\"items\":[{\"custom_id\":\"...\",\"sentence_count\":0,\"n0\":0,\"n1\":0,\"n2\":0,\"n3\":0,\"n4\":0,\"n5\":0,\"summary_text\":\"...\"}]}\n\n"
            + "\n\n".join(items)
        )
    if prompt_mode == "cot_v2":
        return (
            "你是招股说明书“业务与技术”章节的信息凝练员。请分别处理下面每个 chunk。\n"
            "目标：模拟论文的 IPO 信息披露冗余识别任务。请先按句子/信息单元重要性评分，再依据评分做强凝练。\n"
            "你只处理给定文本，不使用外部资料，不运行命令。\n\n"
            "对每个 chunk 必须完成以下步骤，但最终只输出 JSON，不输出评分过程或句子列表：\n"
            "1. 将文本块识别为可评分的句子或信息单元。普通正文按句号、问号、叹号、分号等切分；表格行、列表项、项目符号也可作为信息单元。\n"
            "2. 按评估 IPO 发行人价值的重要性给每个信息单元打 0-5 分。评分要保守，典型招股书 chunk 中多数信息单元应落在 0-2 分，4-5 分必须稀缺。标准如下：\n"
            "   0 分：页眉页脚、目录残留、格式噪声、纯模板话、与企业价值判断无关的信息。\n"
            "   1 分：泛泛行业背景、政策铺陈、重复定义、低相关合规性表述。\n"
            "   2 分：一般性公司介绍、普通产品介绍、无硬数字或无独特性的能力描述、较弱经营事实。\n"
            "   3 分：有助于识别主营业务、主要产品、经营模式、客户/供应商或应用场景的事实，但缺少强证据或核心性。\n"
            "   4 分：核心事实但证据强度不足一档，例如核心技术、研发能力、竞争优势、市场地位、收入/产能/客户集中度等重要事实，但缺少关键数字、排名、参数、专利或明确占比。\n"
            "   5 分：极少数高度关键事实，必须同时具备“核心性”和“硬证据”，例如主营业务+收入/占比，核心产品+关键参数，关键技术+专利/授权/技术指标，市场地位+份额/排名，重要客户+收入贡献。\n"
            "   自检：多数 chunk 的 n4+n5 应约为 5-10 个信息单元；若 n4+n5 超过 12 或超过全部信息单元的 20%，必须重新审视是否把一般事实打得过高。只有信息密度极高的 chunk 才允许超过该范围。\n"
            "3. 统计不同分数的信息单元数量，字段为 n0、n1、n2、n3、n4、n5；sentence_count 必须等于 n0+n1+n2+n3+n4+n5。\n"
            "4. 凝练规则必须严格按重要性取舍：\n"
            "   - 0、1、2 分信息原则上全部删除。\n"
            "   - 3 分信息只在识别公司业务和上下文必要时极少量合并保留，不逐项复述。\n"
            "   - 4 分信息高度合并保留，只保留最能体现技术、市场、研发、客户、产能、收入的核心事实。\n"
            "   - 5 分信息优先保留，但同类事实必须合并，不能把原文改写成长摘要。\n"
            "5. summary_text 写一段连续中文，目标是形成关键信息骨架，而不是详尽摘要。摘要句数原则上不超过 n4+n5+2；若 n4+n5 很多，必须进一步合并同类事实，不能逐句复述。\n"
            "6. summary_text 不设字数下限，不得为了凑长度扩写；通常不超过 260 个中文字符，信息密度极高时最多不超过 320 个中文字符。\n"
            "7. 输出 summary_sentence_count，表示 summary_text 中的中文句子数；它应与高分信息单元数量保持一致，不能远大于 n4+n5+2。\n"
            "8. 不得新增事实，不得评价，不得输出 Markdown，不得输出空字符串。\n\n"
            "JSON 结构必须是：\n"
            "{\"items\":[{\"custom_id\":\"...\",\"sentence_count\":0,\"n0\":0,\"n1\":0,\"n2\":0,\"n3\":0,\"n4\":0,\"n5\":0,\"summary_sentence_count\":0,\"summary_text\":\"...\"}]}\n\n"
            + "\n\n".join(items)
        )
    if prompt_mode == "cot_v3":
        return (
            "你是招股说明书“业务与技术”章节的信息凝练员。请分别处理下面每个 chunk。\n"
            "目标：复现论文的 IPO 信息披露冗余识别任务。重点不是写摘要，而是先识别重要性，再删除低重要性披露，只保留高重要性事实骨架。\n"
            "你只处理给定文本，不使用外部资料，不运行命令。\n\n"
            "对每个 chunk 必须完成以下步骤，但最终只输出 JSON，不输出评分过程或句子列表：\n"
            "1. 将文本块识别为可评分的句子或信息单元。普通正文按句号、问号、叹号、分号等切分；表格行、列表项、项目符号也可作为信息单元。\n"
            "2. 按评估 IPO 发行人价值的重要性给每个信息单元打 0-5 分。评分必须保守，典型招股书 chunk 中多数信息单元应落在 0-2 分，4-5 分必须稀缺。标准如下：\n"
            "   0 分：页眉页脚、目录残留、格式噪声、纯模板话、无企业价值判断含义的信息。\n"
            "   1 分：泛泛行业背景、政策法规铺陈、重复定义、常识性解释、低相关合规表述。\n"
            "   2 分：一般公司介绍、普通产品介绍、无硬数字或无独特性的能力描述、弱经营事实。\n"
            "   3 分：有助于识别主营业务、主要产品、经营模式、客户/供应商或应用场景的事实，但缺少强证据或核心性。\n"
            "   4 分：核心事实但证据强度不足一档，例如核心技术、研发能力、竞争优势、市场地位、收入/产能/客户集中度等重要事实，但缺少关键数字、排名、参数、专利或明确占比。\n"
            "   5 分：极少数高度关键事实，必须同时具备“核心性”和“硬证据”，例如主营业务+收入/占比，核心产品+关键参数，关键技术+专利/授权/技术指标，市场地位+份额/排名，重要客户+收入贡献。\n"
            "   自检：多数 chunk 的 n4+n5 应约为 4-8 个信息单元；若 n4+n5 超过 10 或超过全部信息单元的 18%，必须重新审视是否把一般事实打得过高。只有信息密度极高的 chunk 才允许超过该范围。\n"
            "3. 统计不同分数的信息单元数量，字段为 n0、n1、n2、n3、n4、n5；sentence_count 必须等于 n0+n1+n2+n3+n4+n5。\n"
            "4. 凝练规则必须严格按重要性取舍：\n"
            "   - 0、1、2 分信息全部删除，不得改写进 summary_text。\n"
            "   - 3 分信息原则上删除；只有在缺少它会导致 4/5 分事实无法识别主体、产品或场景时，才允许合并成半句背景。\n"
            "   - 4 分信息合并保留，不能逐句复述；同一产品、技术、客户、产能、收入或市场地位只写一次。\n"
            "   - 5 分信息优先保留，但也必须合并为事实骨架，不展开解释原因、影响或意义。\n"
            "5. summary_text 写一段连续中文，只输出事实骨架。常规 chunk 写 3-5 个短句；低密度 chunk 写 1-3 个短句；高密度 chunk 也应先合并同类事实再写，不要超过 6 个短句。\n"
            "6. summary_text 不设字数下限，不得为了凑长度扩写。不要照搬原文长句；每句尽量只保留“主体+核心事实+关键数字/证据”。若一个句子超过 45 个中文字符，应优先拆掉修饰语或合并为更短表述，而不是继续展开。\n"
            "7. 输出前自检：summary_text 中不得出现一般性行业铺陈、政策背景、模板话、空泛竞争优势形容、重复定义、未与发行人绑定的泛泛市场描述。\n"
            "8. 输出 summary_sentence_count，表示 summary_text 中的中文句子数；它应显著少于高分信息单元数，除非 n4+n5 本身很少。\n"
            "9. 不得新增事实，不得评价，不得输出 Markdown，不得输出空字符串。\n\n"
            "JSON 结构必须是：\n"
            "{\"items\":[{\"custom_id\":\"...\",\"sentence_count\":0,\"n0\":0,\"n1\":0,\"n2\":0,\"n3\":0,\"n4\":0,\"n5\":0,\"summary_sentence_count\":0,\"summary_text\":\"...\"}]}\n\n"
            + "\n\n".join(items)
        )
    if prompt_mode == "cot_v3b":
        return (
            "你是招股说明书“业务与技术”章节的信息冗余识别员。请分别处理下面每个 chunk。\n"
            "目标：复现论文的 IPO 信息披露冗余识别任务。你的任务不是写完整摘要，而是先用严格标尺识别重要性，再删除低重要性披露，只输出高重要性事实骨架。\n"
            "你只处理给定文本，不使用外部资料，不运行命令。\n\n"
            "对每个 chunk 必须完成以下步骤，但最终只输出 JSON，不输出评分过程或句子列表：\n"
            "1. 将文本块识别为可评分的句子或信息单元。普通正文按句号、问号、叹号、分号等切分；表格行、列表项、项目符号也可作为信息单元。\n"
            "2. 先按严格标尺给每个信息单元打 0-5 分。评分时必须先假定多数招股书披露是低重要性信息，只有发行人绑定、核心性强、证据硬的信息才能进入 4-5 分。\n"
            "   0 分：页眉页脚、目录残留、格式噪声、纯模板话、无企业价值判断含义的信息。\n"
            "   1 分：泛泛行业背景、政策法规铺陈、重复定义、常识性解释、市场空间空泛描述、低相关合规表述。\n"
            "   2 分：一般公司介绍、普通产品介绍、普通应用场景、无硬数字或无独特性的能力描述、弱经营事实。\n"
            "   3 分：发行人绑定的有用事实，例如主营业务、主要产品、经营模式、客户/供应商或应用场景，但缺少收入占比、技术指标、专利、排名、份额、产能等强证据。\n"
            "   4 分：发行人绑定的核心事实，且至少有一种较强证据，例如核心技术、研发能力、竞争优势、市场地位、收入/产能/客户集中度等，并伴随数字、参数、排名、份额、认证、专利或明确占比之一。\n"
            "   5 分：极少数关键事实，必须同时满足三项：直接绑定发行人；高度体现技术实力、核心竞争力、市场地位或科创属性；包含硬证据，例如收入/占比、核心参数、专利/授权/技术指标、份额/排名、重要客户收入贡献。\n"
            "3. 评分复核规则：\n"
            "   - 没有数字、排名、份额、专利、技术指标、认证或收入占比的信息单元，最高只能给 3 分。\n"
            "   - 只讲行业趋势、政策背景、市场空间、技术路线普及、客户需求的一般句子，最高只能给 1 分；若未直接绑定发行人，不能给 3 分及以上。\n"
            "   - 只讲公司“具备优势、水平较高、经验丰富、质量稳定”等空泛表述，最高只能给 2 分。\n"
            "   - 表格中的多行同类数字不能逐行抬高分数；应视为一组证据，只给少数核心行 4-5 分，其余为 2-3 分。\n"
            "   - 多数 chunk 的 n4+n5 应约为 3-8 个信息单元，n5 通常为 0-3 个；若 n4+n5 超过 10 或超过全部信息单元的 15%，必须重新下调一般事实的分数。\n"
            "4. 统计不同分数的信息单元数量，字段为 n0、n1、n2、n3、n4、n5；sentence_count 必须等于 n0+n1+n2+n3+n4+n5。\n"
            "5. 凝练规则必须服从评分结果：\n"
            "   - 0、1、2 分信息全部删除，不得改写进 summary_text。\n"
            "   - 3 分信息原则上删除；只有在缺少它会导致 4/5 分事实无法识别主体、产品或场景时，才允许压缩成半句上下文。\n"
            "   - 4 分信息合并保留；同一产品、技术、客户、产能、收入或市场地位只写一次，不能逐句复述。\n"
            "   - 5 分信息优先保留，但也必须合并为事实骨架，不展开解释原因、影响或意义。\n"
            "6. summary_text 写一段连续中文，只输出事实骨架。低密度 chunk 写 1-3 个短句；常规 chunk 写 3-5 个短句；高密度 chunk 也应先合并同类事实再写，不超过 6 个短句。\n"
            "7. 不设字数下限，不得为了凑长度扩写。不要照搬原文长句；每句只保留“主体+核心事实+关键数字/证据”。若一个句子超过 45 个中文字符，应删除修饰语、背景语和解释语。\n"
            "8. 输出前自检：summary_text 中不得出现一般性行业铺陈、政策背景、模板话、空泛竞争优势形容、重复定义、未与发行人绑定的泛泛市场描述；summary_text 的核心事实应主要来自 4-5 分信息。\n"
            "9. 输出 summary_sentence_count，表示 summary_text 中的中文句子数；它通常应小于 n4+n5，除非 n4+n5 本身很少。\n"
            "10. 不得新增事实，不得评价，不得输出 Markdown，不得输出空字符串。\n\n"
            "JSON 结构必须是：\n"
            "{\"items\":[{\"custom_id\":\"...\",\"sentence_count\":0,\"n0\":0,\"n1\":0,\"n2\":0,\"n3\":0,\"n4\":0,\"n5\":0,\"summary_sentence_count\":0,\"summary_text\":\"...\"}]}\n\n"
            + "\n\n".join(items)
        )
    if prompt_mode == "cot_v3b_len132":
        return (
            "你是招股说明书“业务与技术”章节的信息冗余识别员。请分别处理下面每个 chunk。\n"
            "目标：复现论文的 IPO 信息披露冗余识别任务。请保持 cot_v3b 的严格重要性评分标尺，但把凝练文本长度校准到更接近原文 Summary_len 均值。你不是写完整摘要，而是输出较充分的高重要性事实骨架。\n"
            "你只处理给定文本，不使用外部资料，不运行命令。\n\n"
            "对每个 chunk 必须完成以下步骤，但最终只输出 JSON，不输出评分过程或句子列表：\n"
            "1. 将文本块识别为可评分的句子或信息单元。普通正文按句号、问号、叹号、分号等切分；表格行、列表项、项目符号也可作为信息单元。\n"
            "2. 先按严格标尺给每个信息单元打 0-5 分。评分时必须先假定多数招股书披露是低重要性信息，只有发行人绑定、核心性强、证据硬的信息才能进入 4-5 分。\n"
            "   0 分：页眉页脚、目录残留、格式噪声、纯模板话、无企业价值判断含义的信息。\n"
            "   1 分：泛泛行业背景、政策法规铺陈、重复定义、常识性解释、市场空间空泛描述、低相关合规表述。\n"
            "   2 分：一般公司介绍、普通产品介绍、普通应用场景、无硬数字或无独特性的能力描述、弱经营事实。\n"
            "   3 分：发行人绑定的有用事实，例如主营业务、主要产品、经营模式、客户/供应商或应用场景，但缺少收入占比、技术指标、专利、排名、份额、产能等强证据。\n"
            "   4 分：发行人绑定的核心事实，且至少有一种较强证据，例如核心技术、研发能力、竞争优势、市场地位、收入/产能/客户集中度等，并伴随数字、参数、排名、份额、认证、专利或明确占比之一。\n"
            "   5 分：极少数关键事实，必须同时满足三项：直接绑定发行人；高度体现技术实力、核心竞争力、市场地位或科创属性；包含硬证据，例如收入/占比、核心参数、专利/授权/技术指标、份额/排名、重要客户收入贡献。\n"
            "3. 评分复核规则：\n"
            "   - 没有数字、排名、份额、专利、技术指标、认证或收入占比的信息单元，最高只能给 3 分。\n"
            "   - 只讲行业趋势、政策背景、市场空间、技术路线普及、客户需求的一般句子，最高只能给 1 分；若未直接绑定发行人，不能给 3 分及以上。\n"
            "   - 只讲公司“具备优势、水平较高、经验丰富、质量稳定”等空泛表述，最高只能给 2 分。\n"
            "   - 表格中的多行同类数字不能逐行抬高分数；应视为一组证据，只给少数核心行 4-5 分，其余为 2-3 分。\n"
            "   - 多数 chunk 的 n4+n5 应约为 3-8 个信息单元，n5 通常为 0-3 个；若 n4+n5 超过 10 或超过全部信息单元的 15%，必须重新下调一般事实的分数。\n"
            "4. 统计不同分数的信息单元数量，字段为 n0、n1、n2、n3、n4、n5；sentence_count 必须等于 n0+n1+n2+n3+n4+n5。\n"
            "5. 凝练规则必须服从评分结果：\n"
            "   - 0、1 分信息删除，不得改写进 summary_text。\n"
            "   - 2 分信息原则上删除；只有在缺少它会导致发行人业务、产品或场景无法识别时，才允许压缩成半句上下文。\n"
            "   - 3 分信息只保留直接绑定发行人的主营业务、主要产品、客户/供应商、应用场景、业务板块、产能、研发平台或经营模式，且必须高度合并。\n"
            "   - 4 分信息合并保留；同一产品、技术、客户、产能、收入或市场地位只写一次，不能逐句复述。\n"
            "   - 5 分信息优先保留，但也必须合并为事实骨架，不展开解释原因、影响或意义。\n"
            "6. summary_text 写一段连续中文事实骨架，并按信息密度控制长度：\n"
            "   - 低密度 chunk（n4+n5 不超过 2）写 2-4 个短句，约 120-220 个中文字符；若原 chunk 本身很短，可低于该范围，但不得空泛扩写。\n"
            "   - 常规 chunk（n4+n5 为 3-8）写 4-6 个短句，约 240-320 个中文字符，目标接近 120-160 个 token_proxy 长度单位。\n"
            "   - 高密度 chunk（n4+n5 超过 8）写 5-7 个短句，约 280-380 个中文字符；必须合并同类事实，不得逐条复述表格。\n"
            "7. 这是一轮长度校准，不是放松评分。可以补回发行人绑定的 3 分上下文，但不得补行业背景、政策背景、市场空间空话、模板话、重复定义或未绑定发行人的泛泛描述。\n"
            "8. 输出前自检：summary_text 应覆盖最重要的主营业务、产品/技术、研发/专利、收入/产能/客户/市场地位等事实中的 3-7 个；不得新增事实，不得评价。\n"
            "9. 输出 summary_sentence_count，表示 summary_text 中的中文句子数。\n"
            "10. 不得输出 Markdown，不得输出空字符串。\n\n"
            "JSON 结构必须是：\n"
            "{\"items\":[{\"custom_id\":\"...\",\"sentence_count\":0,\"n0\":0,\"n1\":0,\"n2\":0,\"n3\":0,\"n4\":0,\"n5\":0,\"summary_sentence_count\":0,\"summary_text\":\"...\"}]}\n\n"
            + "\n\n".join(items)
        )
    if prompt_mode == "cot_v3b_len132_bounded":
        return (
            "你是招股说明书“业务与技术”章节的信息冗余识别员。请分别处理下面每个 chunk。\n"
            "目标：复现论文的 IPO 信息披露冗余识别任务。请保持 cot_v3b 的严格重要性评分标尺，同时把 summary_text 的长度硬控制在接近原文 Summary_len 的区间。注意：本项目的 Summary_len 约等于中文紧凑字符数的一半；因此 260 个中文字符约等于 130 个 Summary_len 单位。\n"
            "你只处理给定文本，不使用外部资料，不运行命令。\n\n"
            "对每个 chunk 必须完成以下步骤，但最终只输出 JSON，不输出评分过程或句子列表：\n"
            "1. 将文本块识别为可评分的句子或信息单元。普通正文按句号、问号、叹号、分号等切分；表格行、列表项、项目符号也可作为信息单元。\n"
            "2. 先按严格标尺给每个信息单元打 0-5 分。评分时必须先假定多数招股书披露是低重要性信息，只有发行人绑定、核心性强、证据硬的信息才能进入 4-5 分。\n"
            "   0 分：页眉页脚、目录残留、格式噪声、纯模板话、无企业价值判断含义的信息。\n"
            "   1 分：泛泛行业背景、政策法规铺陈、重复定义、常识性解释、市场空间空泛描述、低相关合规表述。\n"
            "   2 分：一般公司介绍、普通产品介绍、普通应用场景、无硬数字或无独特性的能力描述、弱经营事实。\n"
            "   3 分：发行人绑定的有用事实，例如主营业务、主要产品、经营模式、客户/供应商或应用场景，但缺少收入占比、技术指标、专利、排名、份额、产能等强证据。\n"
            "   4 分：发行人绑定的核心事实，且至少有一种较强证据，例如核心技术、研发能力、竞争优势、市场地位、收入/产能/客户集中度等，并伴随数字、参数、排名、份额、认证、专利或明确占比之一。\n"
            "   5 分：极少数关键事实，必须同时满足三项：直接绑定发行人；高度体现技术实力、核心竞争力、市场地位或科创属性；包含硬证据，例如收入/占比、核心参数、专利/授权/技术指标、份额/排名、重要客户收入贡献。\n"
            "3. 评分复核规则：没有数字、排名、份额、专利、技术指标、认证或收入占比的信息单元，最高只能给 3 分；行业趋势、政策背景、市场空间、技术路线普及、客户需求最高只能给 1 分；空泛优势最高只能给 2 分。多数 chunk 的 n4+n5 应约为 3-8 个信息单元，n5 通常为 0-3 个。\n"
            "4. 统计 n0、n1、n2、n3、n4、n5；sentence_count 必须等于 n0+n1+n2+n3+n4+n5。\n"
            "5. 凝练规则必须服从评分结果：删除 0-1 分信息；2 分原则删除，只在识别发行人业务不可缺时压缩成半句；3 分只保留直接绑定发行人的主营、产品、客户/供应商、应用场景、业务板块、产能、研发平台或经营模式；4-5 分合并保留，不能逐句复述表格。\n"
            "6. summary_text 必须是一段连续中文，且必须严格控制长度：\n"
            "   - 低密度 chunk（n4+n5 不超过 2）：120-180 个中文字符，最多不超过 200 个中文字符。\n"
            "   - 常规 chunk（n4+n5 为 3-8）：220-280 个中文字符，最多不超过 300 个中文字符。\n"
            "   - 高密度 chunk（n4+n5 超过 8）：260-320 个中文字符，最多不超过 340 个中文字符。\n"
            "   - 如果超过对应上限，必须删掉修饰语、原因解释、重复数字、泛背景和同类事实，直到低于上限。\n"
            "7. 这是一轮长度校准，不是放松评分。不得补行业背景、政策背景、市场空间空话、模板话、重复定义或未绑定发行人的泛泛描述。\n"
            "8. 输出前自检：summary_text 应覆盖最重要的主营业务、产品/技术、研发/专利、收入/产能/客户/市场地位等事实中的 3-6 个；不得新增事实，不得评价。\n"
            "9. 输出 summary_sentence_count，表示 summary_text 中的中文句子数。\n"
            "10. 不得输出 Markdown，不得输出空字符串。\n\n"
            "JSON 结构必须是：\n"
            "{\"items\":[{\"custom_id\":\"...\",\"sentence_count\":0,\"n0\":0,\"n1\":0,\"n2\":0,\"n3\":0,\"n4\":0,\"n5\":0,\"summary_sentence_count\":0,\"summary_text\":\"...\"}]}\n\n"
            + "\n\n".join(items)
        )
    if prompt_mode == "cot_v3b_len132_tight":
        return (
            "你是招股说明书“业务与技术”章节的信息冗余识别员。请分别处理下面每个 chunk。\n"
            "目标：复现论文的 IPO 信息披露冗余识别任务。请保持 cot_v3b 的严格重要性评分标尺，同时把 summary_text 的长度校准到原文 Summary_len 附近。注意：本项目的 Summary_len 约等于中文紧凑字符数的一半；因此 260 个中文字符约等于 130 个 Summary_len 单位。\n"
            "你只处理给定文本，不使用外部资料，不运行命令。\n\n"
            "对每个 chunk 必须完成以下步骤，但最终只输出 JSON，不输出评分过程或句子列表：\n"
            "1. 将文本块识别为可评分的句子或信息单元。普通正文按句号、问号、叹号、分号等切分；表格行、列表项、项目符号也可作为信息单元。\n"
            "2. 先按严格标尺给每个信息单元打 0-5 分。评分时必须先假定多数招股书披露是低重要性信息，只有发行人绑定、核心性强、证据硬的信息才能进入 4-5 分。\n"
            "   0 分：页眉页脚、目录残留、格式噪声、纯模板话、无企业价值判断含义的信息。\n"
            "   1 分：泛泛行业背景、政策法规铺陈、重复定义、常识性解释、市场空间空泛描述、低相关合规表述。\n"
            "   2 分：一般公司介绍、普通产品介绍、普通应用场景、无硬数字或无独特性的能力描述、弱经营事实。\n"
            "   3 分：发行人绑定的有用事实，例如主营业务、主要产品、经营模式、客户/供应商或应用场景，但缺少收入占比、技术指标、专利、排名、份额、产能等强证据。\n"
            "   4 分：发行人绑定的核心事实，且至少有一种较强证据，例如核心技术、研发能力、竞争优势、市场地位、收入/产能/客户集中度等，并伴随数字、参数、排名、份额、认证、专利或明确占比之一。\n"
            "   5 分：极少数关键事实，必须同时满足三项：直接绑定发行人；高度体现技术实力、核心竞争力、市场地位或科创属性；包含硬证据，例如收入/占比、核心参数、专利/授权/技术指标、份额/排名、重要客户收入贡献。\n"
            "3. 评分复核规则：没有数字、排名、份额、专利、技术指标、认证或收入占比的信息单元，最高只能给 3 分；行业趋势、政策背景、市场空间、技术路线普及、客户需求最高只能给 1 分；空泛优势最高只能给 2 分。多数 chunk 的 n4+n5 应约为 3-8 个信息单元，n5 通常为 0-3 个。\n"
            "4. 统计 n0、n1、n2、n3、n4、n5；sentence_count 必须等于 n0+n1+n2+n3+n4+n5。\n"
            "5. 凝练规则必须服从评分结果：删除 0-1 分信息；2 分原则删除，只在识别发行人业务不可缺时压缩成半句；3 分只保留直接绑定发行人的主营、产品、客户/供应商、应用场景、业务板块、产能、研发平台或经营模式；4-5 分合并保留，不能逐句复述表格。\n"
            "6. summary_text 必须是一段连续中文，且必须严格控制长度：\n"
            "   - 低密度 chunk（n4+n5 不超过 2）：90-150 个中文字符，最多不超过 170 个中文字符。\n"
            "   - 常规 chunk（n4+n5 为 3-8）：180-240 个中文字符，最多不超过 260 个中文字符。\n"
            "   - 高密度 chunk（n4+n5 超过 8）：220-280 个中文字符，最多不超过 300 个中文字符。\n"
            "   - 如果超过对应上限，必须删掉修饰语、原因解释、重复数字、泛背景和同类事实，直到低于上限。\n"
            "7. 这是一轮长度校准，不是放松评分。不得补行业背景、政策背景、市场空间空话、模板话、重复定义或未绑定发行人的泛泛描述。\n"
            "8. 输出前自检：summary_text 应覆盖最重要的主营业务、产品/技术、研发/专利、收入/产能/客户/市场地位等事实中的 2-6 个；不得新增事实，不得评价。\n"
            "9. 输出 summary_sentence_count，表示 summary_text 中的中文句子数。\n"
            "10. 不得输出 Markdown，不得输出空字符串。\n\n"
            "JSON 结构必须是：\n"
            "{\"items\":[{\"custom_id\":\"...\",\"sentence_count\":0,\"n0\":0,\"n1\":0,\"n2\":0,\"n3\":0,\"n4\":0,\"n5\":0,\"summary_sentence_count\":0,\"summary_text\":\"...\"}]}\n\n"
            + "\n\n".join(items)
        )
    if prompt_mode == "cot_v3c_freelen":
        return (
            "你是招股说明书“业务与技术”章节的信息冗余识别员。请分别处理下面每个 chunk。\n"
            "目标：复现论文的 IPO 信息披露冗余识别任务。你的任务不是写完整摘要，而是先用严格标尺识别重要性，再删除低重要性披露，只输出高重要性事实骨架。\n"
            "你只处理给定文本，不使用外部资料，不运行命令。\n\n"
            "对每个 chunk 必须完成以下步骤，但最终只输出 JSON，不输出评分过程或句子列表：\n"
            "1. 将文本块识别为可评分的句子或信息单元。普通正文按句号、问号、叹号、分号等切分；表格行、列表项、项目符号也可作为信息单元。\n"
            "2. 先按严格标尺给每个信息单元打 0-5 分。评分时必须先假定多数招股书披露是低重要性信息，只有发行人绑定、核心性强、证据硬的信息才能进入 4-5 分。\n"
            "   0 分：页眉页脚、目录残留、格式噪声、纯模板话、无企业价值判断含义的信息。\n"
            "   1 分：泛泛行业背景、政策法规铺陈、重复定义、常识性解释、市场空间空泛描述、低相关合规表述。\n"
            "   2 分：一般公司介绍、普通产品介绍、普通应用场景、无硬数字或无独特性的能力描述、弱经营事实。\n"
            "   3 分：发行人绑定的有用事实，例如主营业务、主要产品、经营模式、客户/供应商或应用场景，但缺少收入占比、技术指标、专利、排名、份额、产能等强证据。\n"
            "   4 分：发行人绑定的核心事实，且至少有一种较强证据，例如核心技术、研发能力、竞争优势、市场地位、收入/产能/客户集中度等，并伴随数字、参数、排名、份额、认证、专利或明确占比之一。\n"
            "   5 分：极少数关键事实，必须同时满足三项：直接绑定发行人；高度体现技术实力、核心竞争力、市场地位或科创属性；包含硬证据，例如收入/占比、核心参数、专利/授权/技术指标、份额/排名、重要客户收入贡献。\n"
            "3. 评分复核规则：\n"
            "   - 没有数字、排名、份额、专利、技术指标、认证或收入占比的信息单元，最高只能给 3 分。\n"
            "   - 只讲行业趋势、政策背景、市场空间、技术路线普及、客户需求的一般句子，最高只能给 1 分；若未直接绑定发行人，不能给 3 分及以上。\n"
            "   - 只讲公司“具备优势、水平较高、经验丰富、质量稳定”等空泛表述，最高只能给 2 分。\n"
            "   - 表格中的多行同类数字不能逐行抬高分数；应视为一组证据，只给少数核心行 4-5 分，其余为 2-3 分。\n"
            "   - 多数 chunk 的 n4+n5 应约为 3-8 个信息单元，n5 通常为 0-3 个；若 n4+n5 超过 10 或超过全部信息单元的 15%，必须重新下调一般事实的分数。\n"
            "4. 统计不同分数的信息单元数量，字段为 n0、n1、n2、n3、n4、n5；sentence_count 必须等于 n0+n1+n2+n3+n4+n5。\n"
            "5. 凝练规则必须服从评分结果：\n"
            "   - 0、1、2 分信息全部删除，不得改写进 summary_text。\n"
            "   - 3 分信息原则上删除；只有在缺少它会导致 4/5 分事实无法识别主体、产品或场景时，才允许压缩成半句上下文。\n"
            "   - 4 分信息合并保留；同一产品、技术、客户、产能、收入或市场地位只写一次，不能逐句复述。\n"
            "   - 5 分信息优先保留，但也必须合并为事实骨架，不展开解释原因、影响或意义。\n"
            "6. summary_text 长度必须由评分结果决定，不设任何下限，也不设按 chunk 的固定句数：\n"
            "   - 只把 4 分和 5 分信息单元写进 summary_text，每个 4-5 分事实合并为一个短句；相同产品/技术/客户/产能/收入只写一次。\n"
            "   - 3 分信息一律不写，除非缺了它会导致某个 4/5 分事实无法识别主体，此时才允许用不超过 6 个字的半句补主语。\n"
            "   - 如果一个 chunk 的 n4+n5 为 0，summary_text 就只写一句（不超过 20 个中文字符）概括该 chunk 属于什么内容，不要为了篇幅扩写。\n"
            "7. 严禁为了达到某个字数而扩写、复述或补充背景。摘要短是低信息 chunk 的正确结果，不是缺陷。\n"
            "8. 不要照搬原文长句；每句只保留“主体+核心事实+关键数字/证据”，超过 45 个中文字符就删修饰语。\n"
            "9. 输出前自检：summary_text 中不得出现一般性行业铺陈、政策背景、模板话、空泛竞争优势形容、重复定义、未与发行人绑定的泛泛市场描述；summary_text 的核心事实应主要来自 4-5 分信息。\n"
            "10. 输出 summary_sentence_count，表示 summary_text 中的中文句子数；它通常应小于 n4+n5，除非 n4+n5 本身很少。\n"
            "11. 不得新增事实，不得评价，不得输出 Markdown，不得输出空字符串。\n\n"
            "JSON 结构必须是：\n"
            "{\"items\":[{\"custom_id\":\"...\",\"sentence_count\":0,\"n0\":0,\"n1\":0,\"n2\":0,\"n3\":0,\"n4\":0,\"n5\":0,\"summary_sentence_count\":0,\"summary_text\":\"...\"}]}\n\n"
            + "\n\n".join(items)
        )
    if prompt_mode == "cot_v3b_tailfix":
        return (
            "你是招股说明书“业务与技术”章节的信息冗余识别员。下面这些 chunk 是上一轮凝练中摘要异常偏短、可能遗漏关键事实的尾部样本。请对每个 chunk 重新评分并修复凝练。\n"
            "目标：保持 cot_v3b 的严格重要性评分，但避免把正常长度 chunk 压成极短摘要。你只处理给定文本，不使用外部资料，不运行命令。\n\n"
            "对每个 chunk 必须完成以下步骤，但最终只输出 JSON，不输出评分过程或句子列表：\n"
            "1. 将文本块识别为可评分的句子或信息单元。普通正文按句号、问号、叹号、分号等切分；表格行、列表项、项目符号也可作为信息单元。\n"
            "2. 使用严格 0-5 分标尺：行业背景、政策法规、常识解释、泛泛市场空间最高 1 分；空泛优势或无硬证据的能力描述最高 2 分；发行人绑定但缺少硬证据的主营、产品、客户、应用场景最高 3 分；只有同时绑定发行人且有数字、排名、份额、专利、技术指标、认证或收入占比等证据的核心事实才能给 4-5 分。\n"
            "3. 统计 n0、n1、n2、n3、n4、n5；sentence_count 必须等于 n0+n1+n2+n3+n4+n5。多数 chunk 的 n4+n5 应约为 3-8 个信息单元，n5 通常为 0-3 个。\n"
            "4. 凝练时仍以 4-5 分事实为骨架，但这是尾部修复任务：\n"
            "   - 0、1 分信息删除。\n"
            "   - 2 分信息原则删除，但若它是理解发行人主营、产品或业务板块的必要背景，可合并成半句。\n"
            "   - 3 分中直接绑定发行人的主营业务、主要产品、客户/供应商、应用场景、业务板块、产能或研发平台，可作为简短上下文保留。\n"
            "   - 4、5 分事实必须保留并合并，不能只写一两句导致关键事实缺失。\n"
            "5. summary_text 写一段连续中文事实骨架。对于正常长度 chunk，通常写 4-7 个短句，约 180-280 个中文字符；低密度但仍有发行人绑定事实的 chunk，也应保留足够上下文，通常不低于 140 个中文字符。不要输出只有 1-2 句的极短摘要，除非原 chunk 本身极短。\n"
            "6. 输出前自检：如果 summary_text 只剩行业背景或政策背景，必须补回发行人绑定的产品、技术、客户、收入、产能、专利、市场地位或业务板块事实；如果只剩 1-2 句，必须确认没有遗漏 3-5 分事实。\n"
            "7. 不得新增事实，不得评价，不得输出 Markdown，不得输出空字符串。\n\n"
            "JSON 结构必须是：\n"
            "{\"items\":[{\"custom_id\":\"...\",\"sentence_count\":0,\"n0\":0,\"n1\":0,\"n2\":0,\"n3\":0,\"n4\":0,\"n5\":0,\"summary_sentence_count\":0,\"summary_text\":\"...\"}]}\n\n"
            + "\n\n".join(items)
        )
    if prompt_mode == "cot_v3b_tailfix_bounded":
        return (
            "你是招股说明书“业务与技术”章节的信息冗余识别员。下面这些 chunk 是上一轮凝练中摘要异常偏短的尾部样本。请只做尾部修复：补回遗漏的发行人绑定关键事实，但不要写成长摘要。\n"
            "你只处理给定文本，不使用外部资料，不运行命令。\n\n"
            "对每个 chunk 必须完成以下步骤，但最终只输出 JSON，不输出评分过程或句子列表：\n"
            "1. 将文本块识别为可评分的句子或信息单元，并按严格 0-5 分标尺评分。行业背景、政策法规、泛泛市场空间最高 1 分；空泛优势或无硬证据能力描述最高 2 分；发行人绑定但缺少硬证据的主营、产品、客户、应用场景最高 3 分；有数字、排名、份额、专利、技术指标、认证或收入占比等证据的核心事实才能给 4-5 分。\n"
            "2. 统计 n0、n1、n2、n3、n4、n5；sentence_count 必须等于 n0+n1+n2+n3+n4+n5。\n"
            "3. summary_text 只写一段连续中文事实骨架，严格控制在 160-220 个中文字符之间。少于 150 个中文字符说明修复不足，超过 230 个中文字符说明过度补写，均视为不合格。\n"
            "4. summary_text 通常写 3-5 个短句。必须覆盖发行人绑定的主营业务、产品/技术/客户/产能/收入/专利/市场地位等核心事实中最重要的 3-6 个；可以保留少量 3 分上下文，但不能展开行业背景、政策背景和原因解释。\n"
            "5. 不得新增事实，不得评价，不得输出 Markdown，不得输出空字符串。\n\n"
            "JSON 结构必须是：\n"
            "{\"items\":[{\"custom_id\":\"...\",\"sentence_count\":0,\"n0\":0,\"n1\":0,\"n2\":0,\"n3\":0,\"n4\":0,\"n5\":0,\"summary_sentence_count\":0,\"summary_text\":\"...\"}]}\n\n"
            + "\n\n".join(items)
        )
    return (
        "你是招股说明书“业务与技术”章节的信息密度筛选器。请分别凝练下面每个 chunk。\n"
        "目标：为 IPO 信息披露冗余变量生成每个 chunk 的凝练文本。\n"
        "硬性要求：\n"
        "1. 每个 chunk 必须输出一个 summary_text，不能遗漏 custom_id。\n"
        "2. summary_text 写一段中文，20-180 个汉字；不得输出“无”“无。”或空字符串。\n"
        "3. 只保留主营业务、核心产品、关键技术、研发能力、市场地位、重要客户/供应商、产能或收入数字等事实。\n"
        "4. 如果 chunk 主要是行业背景，也要用 20-80 个汉字概括其行业事实，不要判空。\n"
        "5. 删除页眉页脚、模板话、重复解释、无数字形容和法规合规铺陈。不得新增事实，不得评价。\n"
        "6. 只输出 JSON 对象，不要 Markdown，不要解释。\n\n"
        "JSON 结构必须是：\n"
        "{\"items\":[{\"custom_id\":\"...\",\"summary_text\":\"...\"}]}\n\n"
        + "\n\n".join(items)
    )


def call_codex(prompt: str, args: argparse.Namespace, label: str) -> tuple[str, str, str]:
    with tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False) as last_msg:
        last_path = Path(last_msg.name)
    cmd = [
        "codex",
        "exec",
        "--ephemeral",
        "--ignore-user-config",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "-c",
        f"model_reasoning_effort=\"{args.reasoning_effort}\"",
        "--output-last-message",
        str(last_path),
        "-",
    ]
    if args.model:
        cmd[2:2] = ["--model", args.model]
    proc = subprocess.run(
        cmd,
        input=prompt,
        text=True,
        cwd=ROOT,
        capture_output=True,
        timeout=args.timeout,
    )
    try:
        last_message = last_path.read_text(encoding="utf-8", errors="replace")
    finally:
        last_path.unlink(missing_ok=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Codex failed for {label}: {proc.stderr[-2000:]}")
    return last_message, proc.stdout, proc.stderr


def load_existing(out_path: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    if not out_path.exists():
        return pd.DataFrame()
    with out_path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return pd.DataFrame(rows)


def append_call_log(path: Path, row: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    pd.DataFrame(rows).to_csv(path.with_suffix(".csv"), index=False, encoding="utf-8-sig")


def write_rows(out_path: Path, rows: list[dict[str, object]], replace_ids: set[str]) -> None:
    existing = load_existing(out_path)
    if not existing.empty and "custom_id" in existing.columns:
        existing = existing[~existing["custom_id"].astype(str).isin(replace_ids)]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        if not existing.empty:
            for row in existing.to_dict("records"):
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def aggregate(run_dir: Path, prompt_mode: str) -> None:
    outputs_path = run_dir / f"ipo_redundancy_llm_outputs_{prompt_mode}.jsonl"
    chunks_path = run_dir / "ipo_business_technology_chunks.csv"
    sections_path = run_dir / "ipo_business_technology_sections.csv"
    chunks = pd.read_csv(chunks_path, dtype=str)
    sections = pd.read_csv(sections_path, dtype=str)
    out_df = load_existing(outputs_path)
    if out_df.empty:
        raise SystemExit("No Codex outputs to aggregate.")

    chunks["chunk_compact_chars"] = pd.to_numeric(chunks["chunk_compact_chars"], errors="coerce")
    if "chunk_token_proxy" in chunks.columns:
        chunks["chunk_token_proxy"] = pd.to_numeric(chunks["chunk_token_proxy"], errors="coerce")
    out_df = out_df.drop_duplicates(subset=["custom_id"], keep="last").copy()
    out_df["summary_compact_chars"] = pd.to_numeric(out_df["summary_compact_chars"], errors="coerce")
    if "summary_token_proxy" in out_df.columns:
        out_df["summary_token_proxy"] = pd.to_numeric(out_df["summary_token_proxy"], errors="coerce")
    extra_cols = [
        "sentence_count",
        "sentence_count_reported",
        "sentence_count_mismatch",
        "n0",
        "n1",
        "n2",
        "n3",
        "n4",
        "n5",
        "high_score_count",
        "high_score_share",
        "summary_sentence_count",
        "summary_high_score_gap",
        "relevant_score",
        "relevant_score_model",
    ]
    for col in extra_cols:
        if col in out_df.columns:
            out_df[col] = pd.to_numeric(out_df[col], errors="coerce")

    merge_cols = ["custom_id", "summary_compact_chars", "summary_chars", "summary_text"]
    if "summary_token_proxy" in out_df.columns:
        merge_cols.append("summary_token_proxy")
    merge_cols.extend([col for col in extra_cols if col in out_df.columns])
    merged = chunks.merge(out_df[merge_cols], on="custom_id", how="left")
    merged.to_csv(run_dir / f"ipo_redundancy_chunk_with_llm_{prompt_mode}.csv", index=False, encoding="utf-8-sig")
    completed_chunks = merged[merged["summary_compact_chars"].notna()].copy()
    completed_chunks.to_csv(
        run_dir / f"ipo_redundancy_chunk_with_llm_{prompt_mode}_completed_only.csv",
        index=False,
        encoding="utf-8-sig",
    )

    if "chunk_token_proxy" in merged.columns and "summary_token_proxy" in merged.columns:
        original_length_col = "chunk_token_proxy"
        summary_length_col = "summary_token_proxy"
        length_mode = "token_proxy"
    else:
        original_length_col = "chunk_compact_chars"
        summary_length_col = "summary_compact_chars"
        length_mode = "compact_chars"

    agg_spec = {
        "chunks": ("custom_id", "size"),
        "completed_chunks": (summary_length_col, "count"),
        "original_compact_chars": ("chunk_compact_chars", "sum"),
        "summary_compact_chars": ("summary_compact_chars", "sum"),
        "original_length_units": (original_length_col, "sum"),
        "summary_length_units": (summary_length_col, "sum"),
    }
    if "sentence_count" in merged.columns:
        agg_spec["sentence_count_sum"] = ("sentence_count", "sum")
    if "summary_sentence_count" in merged.columns:
        agg_spec["summary_sentence_count_sum"] = ("summary_sentence_count", "sum")
    if "high_score_count" in merged.columns:
        agg_spec["high_score_count_sum"] = ("high_score_count", "sum")
    if "high_score_share" in merged.columns:
        agg_spec["high_score_share_mean"] = ("high_score_share", "mean")
    if "summary_high_score_gap" in merged.columns:
        agg_spec["summary_high_score_gap_mean"] = ("summary_high_score_gap", "mean")
    if "relevant_score" in merged.columns:
        agg_spec["relevant_score_mean"] = ("relevant_score", "mean")
    for col in ["n0", "n1", "n2", "n3", "n4", "n5"]:
        if col in merged.columns:
            agg_spec[f"{col}_sum"] = (col, "sum")

    agg = merged.groupby(["sec_code", "announcement_id"], dropna=False).agg(**agg_spec).reset_index()
    agg["llm_complete"] = agg["chunks"].eq(agg["completed_chunks"])
    agg["length_mode"] = length_mode
    agg["redundancy_partial"] = agg["original_length_units"] / agg["summary_length_units"].replace({0: pd.NA})
    agg["redundancy"] = agg["redundancy_partial"].where(agg["llm_complete"])
    keep_cols = [
        "sec_code",
        "sec_name",
        "announcement_id",
        "announcement_title",
        "announcement_date",
        "doc_type",
        "section_status",
        "tech_text_compact_chars",
        "chunk_count",
    ]
    firm = sections[[c for c in keep_cols if c in sections.columns]].merge(agg, on=["sec_code", "announcement_id"], how="left")
    firm.to_csv(run_dir / f"ipo_redundancy_firm_level_{prompt_mode}.csv", index=False, encoding="utf-8-sig")
    firm[firm["llm_complete"].fillna(False)].to_csv(
        run_dir / f"ipo_redundancy_firm_level_{prompt_mode}_completed_only.csv",
        index=False,
        encoding="utf-8-sig",
    )
    print(f"[aggregate] rows={len(firm)} out={run_dir / f'ipo_redundancy_firm_level_{prompt_mode}.csv'}", flush=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-name", default="star_codex_test_20260628")
    parser.add_argument("--sec-code", action="append", default=[], help="One or more sec_code values, comma-separated allowed.")
    parser.add_argument("--custom-id", action="append", default=[], help="One or more custom_id values, comma-separated allowed.")
    parser.add_argument("--prompt-mode", default="codex_ultra_v2")
    parser.add_argument("--max-chunks-per-call", type=int, default=50)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--sleep", type=float, default=0.5)
    parser.add_argument("--reasoning-effort", default="low")
    parser.add_argument("--model", default="")
    parser.add_argument("--aggregate-only", action="store_true")
    parser.add_argument("--rerun-existing", action="store_true", help="Rerun chunks even if they already have outputs.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = ROOT / "results" / args.run_name
    chunks_path = run_dir / "ipo_business_technology_chunks.csv"
    if not chunks_path.exists():
        raise SystemExit(f"Missing chunk file: {chunks_path}")

    if not args.aggregate_only:
        chunks = pd.read_csv(chunks_path, dtype=str).fillna("")
        sec_codes = parse_sec_codes(args.sec_code)
        if sec_codes:
            chunks = chunks[chunks["sec_code"].isin(sec_codes)].copy()
        custom_ids = parse_custom_ids(args.custom_id)
        if custom_ids:
            chunks = chunks[chunks["custom_id"].isin(custom_ids)].copy()
        if chunks.empty:
            raise SystemExit("No chunks selected.")

        out_path = run_dir / f"ipo_redundancy_llm_outputs_{args.prompt_mode}.jsonl"
        if out_path.exists() and not args.rerun_existing:
            existing = load_existing(out_path)
            if not existing.empty and "custom_id" in existing.columns:
                done_ids = set(existing["custom_id"].astype(str))
                before = len(chunks)
                chunks = chunks[~chunks["custom_id"].astype(str).isin(done_ids)].copy()
                print(f"[resume] skipping_existing_chunks={before - len(chunks)} remaining_chunks={len(chunks)}", flush=True)
        if chunks.empty:
            print("[resume] all selected chunks already have outputs; aggregating only.", flush=True)
            aggregate(run_dir, args.prompt_mode)
            return
        raw_dir = run_dir / "codex_cli_raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        token_log_path = run_dir / f"codex_cli_token_usage_{args.prompt_mode}.jsonl"
        all_rows: list[dict[str, object]] = []
        replace_ids: set[str] = set()

        for sec_code, firm_chunks in chunks.groupby("sec_code", sort=False):
            firm_chunks = firm_chunks.sort_values("chunk_index", key=lambda s: pd.to_numeric(s, errors="coerce"))
            batches = [firm_chunks.iloc[i : i + args.max_chunks_per_call].copy() for i in range(0, len(firm_chunks), args.max_chunks_per_call)]
            for part, batch in enumerate(batches, start=1):
                first_idx = int(pd.to_numeric(batch["chunk_index"], errors="coerce").min())
                last_idx = int(pd.to_numeric(batch["chunk_index"], errors="coerce").max())
                label = f"{sec_code}_chunks_{first_idx:04d}_{last_idx:04d}"
                print(f"[codex] {label} chunks={len(batch)}", flush=True)
                prompt = build_prompt(batch, args.prompt_mode)
                last_message, stdout, stderr = call_codex(prompt, args, label)
                token_usage = parse_token_usage(stdout + "\n" + stderr)
                (raw_dir / f"{args.prompt_mode}_{label}_last_message.txt").write_text(last_message, encoding="utf-8")
                (raw_dir / f"{args.prompt_mode}_{label}_stdout_tail.txt").write_text(stdout[-6000:], encoding="utf-8")
                (raw_dir / f"{args.prompt_mode}_{label}_stderr_tail.txt").write_text(stderr[-6000:], encoding="utf-8")

                parsed = extract_json(last_message)
                items = parsed.get("items", [])
                expected = set(batch["custom_id"].astype(str))
                got = {str(item.get("custom_id", "")) for item in items}
                missing = sorted(expected - got)
                extra = sorted(got - expected)
                if missing or extra:
                    raise RuntimeError(f"Codex JSON id mismatch for {label}: missing={missing[:5]} extra={extra[:5]}")
                call_log = {
                    "ts": datetime.now().isoformat(timespec="seconds"),
                    "run_name": args.run_name,
                    "prompt_mode": args.prompt_mode,
                    "label": label,
                    "sec_code": sec_code,
                    "sec_name": str(batch["sec_name"].iloc[0]) if "sec_name" in batch.columns and len(batch) else "",
                    "announcement_id": str(batch["announcement_id"].iloc[0]) if len(batch) else "",
                    "chunks": len(batch),
                    "first_chunk_index": first_idx,
                    "last_chunk_index": last_idx,
                    "chunk_chars": int(pd.to_numeric(batch["chunk_chars"], errors="coerce").fillna(0).sum()),
                    "chunk_compact_chars": int(pd.to_numeric(batch["chunk_compact_chars"], errors="coerce").fillna(0).sum()),
                    "prompt_chars": len(prompt),
                    "items_returned": len(items),
                    "model": args.model or "codex-cli-default",
                    "reasoning_effort": args.reasoning_effort,
                    **token_usage,
                }
                append_call_log(token_log_path, call_log)
                for item in items:
                    summary = str(item.get("summary_text", "")).strip()
                    cid = str(item.get("custom_id", "")).strip()
                    cot_fields: dict[str, object] = {}
                    if args.prompt_mode.startswith("cot_"):
                        counts = {f"n{i}": score_count(item, f"n{i}") for i in range(6)}
                        count_sum = sum(counts.values())
                        sentence_reported_raw = item.get("sentence_count", item.get("Sentence_count", count_sum))
                        sentence_reported = int(float(str(sentence_reported_raw).strip())) if sentence_reported_raw not in ("", None) else count_sum
                        if count_sum <= 0:
                            raise RuntimeError(f"{args.prompt_mode} returned nonpositive sentence counts for {cid}: {item}")
                        relevant_score = sum(i * counts[f"n{i}"] for i in range(6)) / count_sum
                        high_score_count = counts["n4"] + counts["n5"]
                        high_score_share = high_score_count / count_sum if count_sum else ""
                        summary_sentence_raw = item.get("summary_sentence_count", item.get("Summary_sentence_count", ""))
                        summary_sentence_count = (
                            int(float(str(summary_sentence_raw).strip()))
                            if summary_sentence_raw not in ("", None)
                            else ""
                        )
                        summary_high_score_gap = (
                            summary_sentence_count - high_score_count
                            if summary_sentence_count != ""
                            else ""
                        )
                        cot_fields = {
                            "sentence_count": count_sum,
                            "sentence_count_reported": sentence_reported,
                            "sentence_count_mismatch": int(sentence_reported != count_sum),
                            **counts,
                            "high_score_count": high_score_count,
                            "high_score_share": high_score_share,
                            "summary_sentence_count": summary_sentence_count,
                            "summary_high_score_gap": summary_high_score_gap,
                            "relevant_score": relevant_score,
                            "relevant_score_model": item.get("relevant_score", item.get("Relevant_score", "")),
                        }
                    row = {
                        "custom_id": cid,
                        "sec_code": str(batch.loc[batch["custom_id"].eq(cid), "sec_code"].iloc[0]),
                        "announcement_id": str(batch.loc[batch["custom_id"].eq(cid), "announcement_id"].iloc[0]),
                        "model": args.model or "codex-cli-default",
                        "temperature": "",
                        "prompt_mode": args.prompt_mode,
                        "summary_text": summary,
                        "summary_chars": len(summary),
                        "summary_compact_chars": len(compact_text(summary)),
                        "summary_token_proxy": token_proxy(summary),
                        "batch_label": label,
                        "batch_total_tokens": token_usage.get("total_tokens", ""),
                        "batch_input_tokens": token_usage.get("input_tokens", ""),
                        "batch_cached_tokens": token_usage.get("cached_tokens", ""),
                        "batch_output_tokens": token_usage.get("output_tokens", ""),
                        "batch_reasoning_tokens": token_usage.get("reasoning_tokens", ""),
                        **cot_fields,
                    }
                    all_rows.append(row)
                    replace_ids.add(cid)
                write_rows(out_path, all_rows, replace_ids)
                print(
                    f"[codex] {label} ok items={len(items)} total_tokens={token_usage.get('total_tokens', '')}",
                    flush=True,
                )
                if args.sleep:
                    time.sleep(args.sleep)
    aggregate(run_dir, args.prompt_mode)


if __name__ == "__main__":
    main()
