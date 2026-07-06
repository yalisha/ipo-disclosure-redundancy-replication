#!/usr/bin/env python3
from __future__ import annotations

from datetime import date
from pathlib import Path
import textwrap

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


PROJECT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
OUT_DIR = PROJECT / "output/pdf"
RESULT_DIR = PROJECT / "results/controls_data_needs_20260706"
PDF_OUT = OUT_DIR / "ipo_controls_data_needs_20260706.pdf"
NEEDS_CSV = RESULT_DIR / "controls_data_needs_20260706.csv"

DESC_SUMMARY = PROJECT / "results/descriptive_comparison_vs_original_20260706/descriptive_gap_summary_20260706.csv"
XY_CSV = PROJECT / "results/descriptive_comparison_vs_original_20260706/table2_xy_descriptives_vs_original_20260706.csv"
CONTROLS_CSV = PROJECT / "results/descriptive_comparison_vs_original_20260706/table2_controls_descriptives_vs_original_20260706.csv"
REG_CSV = PROJECT / "results/table2_glm4_dewrap_full543_audit_20260706/table2_glm4_dewrap_full543_regressions_20260706.csv"


def register_fonts() -> tuple[str, str]:
    candidates = [
        Path("/Library/Fonts/Arial Unicode.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
        Path("/System/Library/Fonts/STHeiti Medium.ttc"),
    ]
    for path in candidates:
        if path.exists():
            pdfmetrics.registerFont(TTFont("CJK", str(path)))
            pdfmetrics.registerFont(TTFont("CJKBold", str(path)))
            return "CJK", "CJKBold"
    return "Helvetica", "Helvetica-Bold"


FONT, FONT_BOLD = register_fonts()


def p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(str(text), style)


def fmt(x: object, digits: int = 3) -> str:
    if pd.isna(x):
        return ""
    try:
        return f"{float(x):.{digits}f}"
    except Exception:
        return str(x)


def wrap(text: object, width: int = 34) -> str:
    if pd.isna(text):
        return ""
    s = str(text)
    return "<br/>".join(textwrap.wrap(s, width=width, break_long_words=False, replace_whitespace=False)) or s


def page_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont(FONT, 8)
    canvas.setFillColor(colors.HexColor("#6B7280"))
    canvas.drawString(18 * mm, 10 * mm, "IPO disclosure redundancy replication - controls data needs")
    canvas.drawRightString(192 * mm, 10 * mm, f"Page {doc.page}")
    canvas.restoreState()


def make_table(rows: list[list[object]], col_widths: list[float], header: bool = True, font_size: int = 8) -> Table:
    table = Table(rows, colWidths=col_widths, repeatRows=1 if header else 0, hAlign="LEFT")
    style = TableStyle(
        [
            ("FONTNAME", (0, 0), (-1, -1), FONT),
            ("FONTSIZE", (0, 0), (-1, -1), font_size),
            ("LEADING", (0, 0), (-1, -1), font_size + 2),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D1D5DB")),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )
    if header:
        style.add("FONTNAME", (0, 0), (-1, 0), FONT_BOLD)
        style.add("TEXTCOLOR", (0, 0), (-1, 0), colors.white)
        style.add("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2937"))
    for idx in range(1 if header else 0, len(rows)):
        if idx % 2 == 0:
            style.add("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#F9FAFB"))
    table.setStyle(style)
    return table


def paragraph_table(raw_rows: list[list[object]], col_widths: list[float], styles: dict[str, ParagraphStyle], wrap_cols: set[int] | None = None, font_size: int = 8) -> Table:
    wrap_cols = wrap_cols or set()
    rows: list[list[object]] = []
    for r_i, row in enumerate(raw_rows):
        out = []
        for c_i, value in enumerate(row):
            if r_i == 0:
                out.append(p(value, styles["table_header"]))
            elif c_i in wrap_cols:
                out.append(p(wrap(value, 25), styles["table_cell"]))
            else:
                out.append(p(value, styles["table_cell"]))
        rows.append(out)
    return make_table(rows, col_widths, header=True, font_size=font_size)


def controls_data_needs() -> pd.DataFrame:
    rows = [
        {
            "priority": "P0",
            "variable": "Underwriter",
            "role": "Table 2/3/4 control",
            "current_status": "Current dummy almost unusable: mean 0.009 vs original 0.574.",
            "needed_data": "IPO sponsor / lead underwriter / main underwriter identities, plus IPO underwriting business ranking.",
            "preferred_source": "Choice, because original states issuance institution and issue-fee data are from Choice. CSMAR IPO underwriting detail can be fallback.",
            "fields_to_download": "stock code, listing date, issue date, sponsor, lead underwriter, main underwriter, underwriter name, underwriting amount or IPO count.",
            "construction": "Top-10 IPO underwriters = 1, else 0. Need confirm whether top 10 is market-wide IPO business over 2019-2023 or annual ranking.",
        },
        {
            "priority": "P0",
            "variable": "NumIndSeg",
            "role": "Original Table 2 control",
            "current_status": "Missing.",
            "needed_data": "Business / industry segment table near IPO or listing pre-year.",
            "preferred_source": "CSMAR segment information or business composition by industry; prospectus segment table if CSMAR lacks IPO-year coverage.",
            "fields_to_download": "stock code, report date/year, segment type, industry/business segment name, segment revenue.",
            "construction": "Count distinct business/industry segments, then log-transform. Original stats suggest checking ln(1 + count).",
        },
        {
            "priority": "P0",
            "variable": "NumProdSeg",
            "role": "Original Table 2 control",
            "current_status": "Missing.",
            "needed_data": "Product segment / main product composition table near IPO or listing pre-year.",
            "preferred_source": "CSMAR business composition by product; prospectus main product revenue table as fallback.",
            "fields_to_download": "stock code, report date/year, product segment name, product revenue, revenue share.",
            "construction": "Count distinct product segments, then log-transform. Original median 1.609 implies careful check of ln(count) vs ln(1 + count).",
        },
        {
            "priority": "P0",
            "variable": "ScopeLen",
            "role": "Original Table 2 control",
            "current_status": "Missing.",
            "needed_data": "Business scope text from company registration/basic information at IPO.",
            "preferred_source": "CSMAR listed-company basic information / company registration info; Tianyancha/Qichacha as fallback if CSMAR has no scope text.",
            "fields_to_download": "stock code, company name, registration date/update date, business scope full text.",
            "construction": "Clean whitespace and count Chinese characters, then log length. Original mean 5.671 implies about 290 characters.",
        },
        {
            "priority": "P1",
            "variable": "RD_Staff",
            "role": "Table 3/4 RD_Low construction and Panel A variable",
            "current_status": "Missing in current master.",
            "needed_data": "R&D staff count and total employee count in the pre-IPO reporting period.",
            "preferred_source": "CSMAR R&D innovation / employee structure table; prospectus employee table fallback.",
            "fields_to_download": "stock code, report year, R&D staff count, total staff count.",
            "construction": "RD_Staff = R&D staff / total staff. Use pre-listing year or prospectus latest reporting period.",
        },
        {
            "priority": "P1",
            "variable": "RD_Asset",
            "role": "Table 3/4 RD_Low construction",
            "current_status": "Available but mean 0.079 vs original 0.105; needs source audit.",
            "needed_data": "R&D expenditure or total R&D investment, and beginning total assets.",
            "preferred_source": "CSMAR R&D innovation table plus financial statements.",
            "fields_to_download": "stock code, report year, R&D expenditure / R&D investment, beginning total assets, fiscal period type.",
            "construction": "RD_Asset = R&D expenditure / beginning total assets. Verify whether original used expense only or total R&D input.",
        },
        {
            "priority": "P1",
            "variable": "Price_Issue / Price_Day5",
            "role": "Table 4 outcomes, Panel A descriptive",
            "current_status": "Available in current master, but exact Choice/industry-adjusted口径 needs audit.",
            "needed_data": "Issue price, fifth trading day close, NAV per share, industry benchmark mean.",
            "preferred_source": "Choice issuance/basic data plus CSMAR daily trading and firm fundamentals; CSMAR IPO first-day performance as cross-check.",
            "fields_to_download": "stock code, issue price, listing date, daily close, fifth trading day, NAV per share, industry code.",
            "construction": "Price / NAV per share, then divide by industry mean. Confirm industry level and whether day 5 counts listing day as day 1.",
        },
        {
            "priority": "P2",
            "variable": "Offerfee",
            "role": "Table 2/3/4 control",
            "current_status": "Available and close to original: 18.327 vs 18.325.",
            "needed_data": "Issue expenses from Choice, because original states issue institution and issue-fee data are from Choice.",
            "preferred_source": "Choice IPO issuance expenses; current CSMAR IPO basic can be retained as fallback.",
            "fields_to_download": "stock code, issue expenses / total issuance cost, issue date, listing date.",
            "construction": "Offerfee = ln(issue expenses). Keep current if Choice matches.",
        },
        {
            "priority": "P2",
            "variable": "Size / Lev / ROA / Age / industry FE",
            "role": "Current controls",
            "current_status": "Available and close to original.",
            "needed_data": "No urgent new data; only audit timing and industry classification.",
            "preferred_source": "Current CSMAR financial statements and firm_info parquet are acceptable for now.",
            "fields_to_download": "If re-downloading: balance sheet, income statement, establishment date, CSRC industry code.",
            "construction": "Use pre-listing year consolidated statements; Age = ln(years from establishment to IPO).",
        },
    ]
    df = pd.DataFrame(rows)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(NEEDS_CSV, index=False, encoding="utf-8-sig")
    return df


def build_pdf() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    needs = controls_data_needs()
    summary = pd.read_csv(DESC_SUMMARY)
    xy = pd.read_csv(XY_CSV)
    controls_df = pd.read_csv(CONTROLS_CSV)
    regs = pd.read_csv(REG_CSV)

    styles_base = getSampleStyleSheet()
    styles = {
        "title": ParagraphStyle(
            "title",
            parent=styles_base["Title"],
            fontName=FONT_BOLD,
            fontSize=20,
            leading=26,
            textColor=colors.HexColor("#111827"),
            alignment=TA_LEFT,
            spaceAfter=10,
        ),
        "h1": ParagraphStyle(
            "h1",
            parent=styles_base["Heading1"],
            fontName=FONT_BOLD,
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#111827"),
            spaceBefore=8,
            spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=styles_base["Heading2"],
            fontName=FONT_BOLD,
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#374151"),
            spaceBefore=6,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            parent=styles_base["BodyText"],
            fontName=FONT,
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#111827"),
            spaceAfter=5,
        ),
        "small": ParagraphStyle(
            "small",
            parent=styles_base["BodyText"],
            fontName=FONT,
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#4B5563"),
        ),
        "table_header": ParagraphStyle(
            "table_header",
            fontName=FONT_BOLD,
            fontSize=7.5,
            leading=9,
            textColor=colors.white,
        ),
        "table_cell": ParagraphStyle(
            "table_cell",
            fontName=FONT,
            fontSize=7.2,
            leading=9,
            textColor=colors.HexColor("#111827"),
        ),
    }

    story = []
    story.append(p("IPO 信息披露冗余复刻：X/Y 描述性统计与 Controls 数据需求", styles["title"]))
    story.append(p(f"日期：{date.today().isoformat()}；口径：full543 dewrap_join + GLM-4 tokenizer + cot_v3b_len132_tight + Summary_len_proxy", styles["small"]))
    story.append(Spacer(1, 5 * mm))

    bullets = [
        "X measurement 已基本回到原文量级：chunk 数 8706 vs 8683，企业层 Redundancy 28.944 vs 29.074。",
        "Y 描述性统计没有明显崩坏：FInvention 接近原文，BHAR 略更负，FSales_Growth 偏低但仍在可解释范围。",
        "Table 2 回归仍 NO_PASS_YET：FInvention 已接近原文负向，BHAR 和 FSales_Growth 未恢复。",
        "下一步不是继续调 X，而是补齐 controls，尤其 Underwriter、NumIndSeg、NumProdSeg、ScopeLen。",
    ]
    story.append(
        ListFlowable(
            [ListItem(p(item, styles["body"])) for item in bullets],
            bulletType="bullet",
            start="circle",
            leftIndent=12,
        )
    )

    story.append(p("1. 当前 X/Y 与原文描述性对比", styles["h1"]))
    key = summary[summary["variable"].isin(["Chunk_num", "Summary_len", "Redundancy_chunk", "lnN_tech", "Redundancy", "FInvention", "BHAR", "FSales_Growth"])].copy()
    key_rows = [["scope", "variable", "N", "paper N", "mean", "paper mean", "median", "paper median"]]
    for _, r in key.iterrows():
        key_rows.append(
            [
                r["scope"],
                r["variable"],
                int(r["current_N"]),
                int(r["original_N"]),
                fmt(r["current_mean"]),
                fmt(r["original_mean"]),
                fmt(r["current_median"]),
                fmt(r["original_median"]),
            ]
        )
    story.append(paragraph_table(key_rows, [24 * mm, 31 * mm, 15 * mm, 18 * mm, 21 * mm, 24 * mm, 21 * mm, 24 * mm], styles, wrap_cols={0, 1}, font_size=7))
    story.append(Spacer(1, 4 * mm))

    story.append(p("Table 2 主规格重跑", styles["h2"]))
    main_reg = regs[(regs["sample"].eq("full_by_y_available")) & (regs["model"].eq("controls_fe_current"))].copy()
    reg_rows = [["Y", "N", "coef", "t", "p", "paper coef", "paper t", "read"]]
    paper = {
        "FInvention": (-0.0316, -1.72),
        "BHAR": (-0.0188, -2.14),
        "FSales_Growth": (-0.0373, -2.02),
    }
    for _, r in main_reg.iterrows():
        dep = r["dep_var"]
        read = "接近原文负向" if dep == "FInvention" else "未恢复原文方向"
        reg_rows.append([dep, int(r["N"]), fmt(r["coef"], 4), fmt(r["t_HC1"], 2), fmt(r["p_HC1"], 3), fmt(paper[dep][0], 4), fmt(paper[dep][1], 2), read])
    story.append(paragraph_table(reg_rows, [28 * mm, 16 * mm, 22 * mm, 18 * mm, 18 * mm, 24 * mm, 18 * mm, 42 * mm], styles, wrap_cols={7}, font_size=7))

    story.append(PageBreak())
    story.append(p("2. Controls 缺口定位", styles["h1"]))
    important = controls_df[controls_df["variable"].isin(["RD_Staff", "RD_Asset", "Size", "Lev", "ROA", "Offerfee", "Underwriter", "Age", "NumIndSeg", "NumProdSeg", "ScopeLen"])].copy()
    control_rows = [["variable", "available", "N", "paper N", "mean", "paper mean", "median", "paper median", "status"]]
    status_map = {
        "Underwriter": "严重错口径",
        "NumIndSeg": "缺失",
        "NumProdSeg": "缺失",
        "ScopeLen": "缺失",
        "RD_Staff": "缺失",
        "RD_Asset": "有但偏低",
        "Size": "基本可用",
        "Lev": "基本可用",
        "ROA": "基本可用",
        "Offerfee": "基本可用但需 Choice 复核",
        "Age": "基本可用",
    }
    for _, r in important.iterrows():
        control_rows.append(
            [
                r["variable"],
                str(r["current_available"]),
                "" if pd.isna(r["current_N"]) else int(r["current_N"]),
                int(r["original_N"]),
                fmt(r["current_mean"]),
                fmt(r["original_mean"]),
                fmt(r["current_median"]),
                fmt(r["original_median"]),
                status_map.get(r["variable"], ""),
            ]
        )
    story.append(paragraph_table(control_rows, [24 * mm, 18 * mm, 14 * mm, 18 * mm, 18 * mm, 22 * mm, 19 * mm, 22 * mm, 31 * mm], styles, wrap_cols={0, 8}, font_size=6.8))
    story.append(Spacer(1, 4 * mm))
    story.append(p("关键判断", styles["h2"]))
    story.append(p("原文附录定义显示，模型控制变量包括 Size、Lev、ROA、Offerfee、Underwriter、Age、NumIndSeg、NumProdSeg、ScopeLen，并额外控制 lnN_tech。当前 Size/Lev/ROA/Offerfee/Age/lnN_tech 基本可用；真正会阻断 strict replication 的是 Underwriter 和三个分部/经营范围变量。机制和定价表还需要 RD_Staff，并复核 RD_Asset 与 Price_Issue/Price_Day5。", styles["body"]))

    story.append(PageBreak())
    story.append(p("3. 需要补的数据清单", styles["h1"]))
    story.append(p("P0 是复刻 Table 2 必须补齐的数据；P1 是复刻动机/定价机制表必须补齐或复核的数据；P2 是已有但最好用原文来源复核的数据。", styles["body"]))
    need_rows = [["prio", "variable", "needed data", "preferred source", "fields / construction"]]
    for _, r in needs.iterrows():
        need_rows.append(
            [
                r["priority"],
                r["variable"],
                r["needed_data"],
                r["preferred_source"],
                f"{r['fields_to_download']} Construction: {r['construction']}",
            ]
        )
    story.append(paragraph_table(need_rows, [12 * mm, 24 * mm, 45 * mm, 48 * mm, 58 * mm], styles, wrap_cols={1, 2, 3, 4}, font_size=6.5))
    story.append(Spacer(1, 5 * mm))
    story.append(p("最小下一步", styles["h2"]))
    story.append(p("先下载或构造 P0 四项：Underwriter、NumIndSeg、NumProdSeg、ScopeLen。若这四项补齐后 Table 2 仍不动，再进入 Y 口径网格和机制表变量重构。", styles["body"]))
    story.append(p(f"Companion CSV: {NEEDS_CSV}", styles["small"]))

    doc = SimpleDocTemplate(
        str(PDF_OUT),
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="IPO controls data needs",
        author="Codex",
    )
    doc.build(story, onFirstPage=page_footer, onLaterPages=page_footer)


if __name__ == "__main__":
    build_pdf()
    print(f"pdf={PDF_OUT}")
    print(f"needs_csv={NEEDS_CSV}")
