#!/usr/bin/env python3
"""Extract Cheng et al. (2022) innovation disclosure keyword dictionary.

The source PDF is text-based CNKI output.  Table 1 spans three pages and
contains four groups: innovation endowment, target, process, and result.
This script keeps the extraction reproducible and records footnote-based
exclusion phrases separately from included terms.
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "bib" / "企业研发投入波动与信息披露_投资者创新包容视角_程新生.pdf"
OUT_DIR = ROOT / "data" / "dictionaries"
TMP_TXT = ROOT / "tmp" / "pdfs" / "cheng2022" / "cheng2022_layout.txt"


def ensure_layout_text() -> list[str]:
    TMP_TXT.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["pdftotext", "-layout", str(PDF), str(TMP_TXT)],
        check=True,
    )
    return TMP_TXT.read_text(encoding="utf-8").splitlines()


def clean_join(block: list[str]) -> str:
    parts: list[str] = []
    for line in block:
        line = re.sub(r"^\s*(创新|禀赋|目标|进展|成果)\s+", "", line)
        line = line.strip()
        if line:
            parts.append(line)
    text = "".join(parts)
    text = re.sub(r"[①②③④⑤⑥⑦⑧⑨]", "", text)
    text = re.sub(r"\s+", " ", text)
    # Footnote markers such as "攻关 1 0、重构" should not become terms.
    text = re.sub(r"\s+\d+(?:\s+\d+)?(?=、)", "", text)
    text = re.sub(r"\s+\d+(?:\s+\d+)?(?=，)", "", text)
    text = text.replace("（ ", "（").replace(" ）", "）")
    text = text.replace("( ", "(").replace(" )", ")")
    return text


def split_terms(text: str) -> list[str]:
    terms: list[str] = []
    for raw in text.split("、"):
        term = raw.strip(" ，。；;:：\t\n")
        term = re.sub(r"\s+", "", term)
        if term:
            terms.append(term)
    return terms


def expand_variants(term: str) -> list[str]:
    variants = [term]
    replacements = [
        ("Ⅰ（一）", ["Ⅰ", "一"]),
        ("Ⅱ（二）", ["Ⅱ", "二"]),
        ("Ⅲ（三）", ["Ⅲ", "三"]),
        ("Ⅳ（四）", ["Ⅳ", "四"]),
        ("（的）", ["", "的"]),
        ("(的)", ["", "的"]),
    ]
    for old, news in replacements:
        expanded: list[str] = []
        for variant in variants:
            if old in variant:
                expanded.extend(variant.replace(old, new) for new in news)
            else:
                expanded.append(variant)
        variants = expanded
    return list(dict.fromkeys(variants))


def locate(lines: list[str], needle: str) -> int:
    for i, line in enumerate(lines):
        if needle in line:
            return i
    raise RuntimeError(f"Cannot find marker: {needle}")


def extract_terms(lines: list[str]) -> list[dict[str, str]]:
    table = locate(lines, "创新信息披露关键词量表")
    dev_footnote = locate(lines, "剔除以下含开发")
    process_start = locate(lines, "试制、打样、送样")
    process_footnote = locate(lines, "删除可能出现的测试中心")
    result_start = locate(lines, "开发成功、成功开发")
    result_footnote = locate(lines, "该关键词涵盖上文中的成果转化中心")
    result_cont = locate(lines, "奖、艾普兰智能科技奖")
    end_marker = locate(lines, "本文利用 Python 提取创新类关键词")

    blocks = {
        "innovation_endowment": split_terms(clean_join(lines[table + 3 : dev_footnote])),
        "innovation_target": ["创新", "技术", "研发", "研究", "开发", "发明", "专利", "研制", "科研", "科技"],
        "innovation_process": split_terms(clean_join(lines[process_start : process_footnote])),
        "innovation_result": split_terms(clean_join(lines[result_start : result_footnote] + lines[result_cont : end_marker])),
    }

    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for category, raw_terms in blocks.items():
        for raw_term in raw_terms:
            for term in expand_variants(raw_term):
                key = (category, term)
                if key in seen:
                    continue
                seen.add(key)
                rows.append(
                    {
                        "category": category,
                        "term": term,
                        "raw_term": raw_term,
                        "source": "Cheng_Xinsheng_et_al_2022_Table_1",
                    }
                )
    return rows


def exclusion_rules() -> list[dict[str, str]]:
    rules = {
        "innovation_target": [
            "开发商",
            "房地产开发",
            "住宅开发",
            "地产项目开发",
            "公开发",
            "开发投资",
            "开发有限",
            "开发科技股份",
            "开发股份",
            "开发主体",
            "开发建设",
            "开发融资",
            "开发权益",
            "园区开发",
            "开发期",
            "开发行业",
            "开发区资源开发",
            "市场开发",
            "开发市场",
        ],
        "innovation_process": [
            "测试中心",
            "测试平台",
            "测试设备",
            "测试机构",
            "检验中心",
            "检验平台",
            "检验设备",
            "检验机构",
            "检验公司",
            "检验有限公司",
            "检测中心",
            "检测平台",
            "检测设备",
            "检测机构",
            "检测公司",
            "检测有限公司",
            "试验基地",
            "试验室",
            "试验中心",
            "试验装置",
            "试验设备",
            "试验仪器",
            "试验站",
            "试验合同",
        ],
        "innovation_result": [
            "企业认证",
            "资质认证",
            "机构认证",
            "体系认证",
            "品牌证书",
            "企业证书",
            "资质证书",
            "机构证书",
            "体系证书",
            "发布会",
            "发布报道",
            "发布报告",
            "发布通知",
            "发布通告",
            "发布消息",
            "发布新闻",
            "新闻发布",
            "数据发布",
            "标准发布",
            "发布实施",
            "首发报道",
            "报道首发",
            "媒体首发",
        ],
    }
    rows: list[dict[str, str]] = []
    for category, terms in rules.items():
        for term in terms:
            rows.append(
                {
                    "category": category,
                    "exclude_term": term,
                    "source": "Cheng_Xinsheng_et_al_2022_Table_1_footnotes",
                }
            )
    return rows


def write_outputs(rows: list[dict[str, str]], exclusions: list[dict[str, str]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "cheng2022_innovation_disclosure_keywords.csv"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["category", "term", "raw_term", "source"])
        writer.writeheader()
        writer.writerows(rows)

    exclusions_path = OUT_DIR / "cheng2022_innovation_disclosure_exclusions.csv"
    with exclusions_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["category", "exclude_term", "source"])
        writer.writeheader()
        writer.writerows(exclusions)

    json_path = OUT_DIR / "cheng2022_innovation_disclosure_dictionary.json"
    grouped: dict[str, list[str]] = {}
    for row in rows:
        grouped.setdefault(row["category"], []).append(row["term"])
    json_path.write_text(
        json.dumps(
            {
                "source_pdf": str(PDF.relative_to(ROOT)),
                "source_table": "Table 1 创新信息披露关键词量表",
                "terms": grouped,
                "exclusions": exclusions,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def main() -> None:
    lines = ensure_layout_text()
    rows = extract_terms(lines)
    exclusions = exclusion_rules()
    write_outputs(rows, exclusions)

    by_cat: dict[str, int] = {}
    for row in rows:
        by_cat[row["category"]] = by_cat.get(row["category"], 0) + 1
    print("Extracted terms:", len(rows))
    for key in sorted(by_cat):
        print(f"{key}: {by_cat[key]}")
    print("Exclusion rules:", len(exclusions))
    print("Output dir:", OUT_DIR)


if __name__ == "__main__":
    main()
