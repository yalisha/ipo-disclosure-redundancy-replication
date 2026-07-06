#!/usr/bin/env python3
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path("/Users/mac/computerscience/文章复现/IPO 信息披露冗余")
OUT_DIR = ROOT / "output/pdf"
TMP_DIR = ROOT / "tmp/pdfs"
PDF_OUT = OUT_DIR / "IPO信息披露冗余复刻审计报告_20260705.pdf"

TABLE1_CSV = (
    ROOT
    / "results/descriptive_comparison_vs_original_20260705/"
    "table1_panel_a_chunk_descriptives_vs_original_20260705.csv"
)
TABLE2_CSV = (
    ROOT
    / "results/descriptive_comparison_vs_original_20260705/"
    "table2_panel_a_firm_descriptives_vs_original_20260705.csv"
)
REG_CSV = (
    ROOT
    / "results/table2_len132_tight_audit_20260705/"
    "table2_len132_tight_regressions_20260705.csv"
)


def register_fonts() -> tuple[str, str]:
    song = "/System/Library/Fonts/Supplemental/Songti.ttc"
    hei = "/System/Library/Fonts/STHeiti Medium.ttc"
    pdfmetrics.registerFont(TTFont("Songti", song))
    pdfmetrics.registerFont(TTFont("Heiti", hei))
    return "Songti", "Heiti"


def fmt(x: object, digits: int = 3) -> str:
    if pd.isna(x):
        return ""
    try:
        return f"{float(x):.{digits}f}"
    except Exception:
        return str(x)


def pct(x: object) -> str:
    if pd.isna(x):
        return ""
    return f"{float(x) * 100:.1f}%"


class TopRule(Flowable):
    def __init__(self, width: float = 480, color=colors.black, thickness: float = 1.0):
        super().__init__()
        self.width = width
        self.height = 4
        self.color = color
        self.thickness = thickness

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, 2, self.width, 2)


def make_styles(song: str, hei: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    styles: dict[str, ParagraphStyle] = {}
    styles["title"] = ParagraphStyle(
        "title",
        parent=base["Title"],
        fontName=hei,
        fontSize=21,
        leading=28,
        alignment=TA_CENTER,
        spaceAfter=8,
        wordWrap="CJK",
    )
    styles["subtitle"] = ParagraphStyle(
        "subtitle",
        parent=base["Normal"],
        fontName=song,
        fontSize=10.5,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#444444"),
        spaceAfter=12,
        wordWrap="CJK",
    )
    styles["abstract_title"] = ParagraphStyle(
        "abstract_title",
        parent=base["Normal"],
        fontName=hei,
        fontSize=10.5,
        leading=15,
        alignment=TA_LEFT,
        spaceBefore=4,
        spaceAfter=3,
        wordWrap="CJK",
    )
    styles["body"] = ParagraphStyle(
        "body",
        parent=base["BodyText"],
        fontName=song,
        fontSize=10,
        leading=16,
        firstLineIndent=20,
        alignment=TA_JUSTIFY,
        spaceAfter=6,
        wordWrap="CJK",
    )
    styles["body_noindent"] = ParagraphStyle(
        "body_noindent",
        parent=styles["body"],
        firstLineIndent=0,
        alignment=TA_LEFT,
    )
    styles["heading1"] = ParagraphStyle(
        "heading1",
        parent=base["Heading1"],
        fontName=hei,
        fontSize=14,
        leading=19,
        spaceBefore=12,
        spaceAfter=7,
        wordWrap="CJK",
    )
    styles["heading2"] = ParagraphStyle(
        "heading2",
        parent=base["Heading2"],
        fontName=hei,
        fontSize=11.5,
        leading=16,
        spaceBefore=8,
        spaceAfter=5,
        wordWrap="CJK",
    )
    styles["table_title"] = ParagraphStyle(
        "table_title",
        parent=base["Normal"],
        fontName=hei,
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        spaceBefore=8,
        spaceAfter=4,
        wordWrap="CJK",
    )
    styles["table_cell"] = ParagraphStyle(
        "table_cell",
        parent=base["Normal"],
        fontName=song,
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        wordWrap="CJK",
    )
    styles["table_head"] = ParagraphStyle(
        "table_head",
        parent=styles["table_cell"],
        fontName=hei,
        fontSize=8,
        leading=10,
    )
    styles["note"] = ParagraphStyle(
        "note",
        parent=base["Normal"],
        fontName=song,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#555555"),
        spaceBefore=3,
        spaceAfter=6,
        wordWrap="CJK",
    )
    styles["verdict"] = ParagraphStyle(
        "verdict",
        parent=base["Normal"],
        fontName=hei,
        fontSize=11,
        leading=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#7A1F1F"),
        wordWrap="CJK",
    )
    return styles


def p(text: str, styles: dict[str, ParagraphStyle], style: str = "body") -> Paragraph:
    return Paragraph(text, styles[style])


def cell(text: object, styles: dict[str, ParagraphStyle], head: bool = False) -> Paragraph:
    return Paragraph(str(text), styles["table_head" if head else "table_cell"])


def academic_table(
    title: str,
    headers: list[str],
    rows: list[list[object]],
    widths: list[float],
    styles: dict[str, ParagraphStyle],
    note: str | None = None,
    highlight_rows: set[int] | None = None,
) -> list[Flowable]:
    highlight_rows = highlight_rows or set()
    data = [[cell(h, styles, True) for h in headers]]
    for row in rows:
        data.append([cell(x, styles) for x in row])
    tbl = Table(data, colWidths=widths, repeatRows=1, hAlign="CENTER")
    ts = TableStyle(
        [
            ("FONTNAME", (0, 0), (-1, -1), "Songti"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
            ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.black),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F3F4")),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]
    )
    for i, _ in enumerate(rows, start=1):
        if i % 2 == 0:
            ts.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FAFAFA"))
    for i in highlight_rows:
        ts.add("BACKGROUND", (0, i + 1), (-1, i + 1), colors.HexColor("#FFF3E0"))
    tbl.setStyle(ts)
    flows: list[Flowable] = [Paragraph(title, styles["table_title"]), tbl]
    if note:
        flows.append(Paragraph(f"注：{note}", styles["note"]))
    return flows


def read_tables():
    t1 = pd.read_csv(TABLE1_CSV)
    t2 = pd.read_csv(TABLE2_CSV)
    regs = pd.read_csv(REG_CSV)
    return t1, t2, regs


def build_story(styles: dict[str, ParagraphStyle]) -> list[Flowable]:
    t1, t2, regs = read_tables()
    story: list[Flowable] = []
    w = A4[0] - 42 * mm

    story.append(TopRule(w, colors.black, 1.2))
    story.append(Spacer(1, 10))
    story.append(p("IPO 信息披露冗余复刻审计报告", styles, "title"))
    story.append(p("基于 cot_v3b_len132_tight 全 543 家样本与原文表 1/表 2 的描述性对比", styles, "subtitle"))
    story.append(p("日期：2026-07-05　　项目：IPO 信息披露冗余如何影响新股定价复刻", styles, "subtitle"))
    story.append(TopRule(w, colors.black, 0.8))
    story.append(Spacer(1, 8))

    story.append(p("摘要", styles, "abstract_title"))
    story.append(
        p(
            "本文档对当前本地复刻结果与原文描述性统计及 Table 2 经济后果回归进行审计。结论是："
            "cot_v3b_len132_tight 已经可以作为当前主 X 口径进入下一阶段审计；企业层 Redundancy 均值为 29.374，"
            "与原文 29.074 接近，chunk 层 Summary_len 与 Redundancy_chunk 也已贴近原文。但 Table 2 strict replication 仍为 NO_PASS_YET。"
            "主要缺口已经从 prompt 或摘要长度转向 empirical layer，包括 Underwriter 构造错误、NumIndSeg/NumProdSeg/ScopeLen 缺失、"
            "FSales_Growth 口径偏差、lnN_tech 长度单位与 552 到 471 样本链条未对齐。",
            styles,
            "body",
        )
    )
    story.append(
        p(
            "关键词：IPO 信息披露冗余；生成式人工智能；描述性统计复刻；Table 2；控制变量审计",
            styles,
            "body_noindent",
        )
    )
    story.append(Spacer(1, 6))
    story.append(p("当前判定", styles, "abstract_title"))
    story.append(p("X 变量维度：LOCK_X_MEASUREMENT_FOR_NEXT_EMPIRICAL_AUDIT　　Table 2 strict replication：NO_PASS_YET", styles, "verdict"))

    story.append(p("一、审计背景与 major correction", styles, "heading1"))
    story.append(
        p(
            "本轮审计首先修正了一个关键口径错误：旧 master 中的大写 Redundancy 并不是 cot_v3b_len132_tight 的企业层 X。"
            "若直接使用该列运行 Table 2，会把旧 scoregate 口径误认为 len132_tight。现已显式合并 "
            "firm_ranking_cot_v3b_len132_tight_20260703.csv，并将其作为唯一 X 来源。这个修正使 FInvention 与 BHAR 的系数回到原文方向，"
            "但幅度和显著性仍不足，FSales_Growth 仍为反号。",
            styles,
        )
    )
    story.append(
        p(
            "因此，当前结论不是 X prompt 崩坏，而是 X 测度已经足够进入下一阶段，真正瓶颈在 Y、controls、样本 waterfall 与数据库字段。"
            "后续文件必须保留 x_source、x_file、x_merge_key、x_N 与 x_mean，以避免再次发生 X provenance 混淆。",
            styles,
        )
    )

    story.append(p("二、文本块层面描述性统计对比", styles, "heading1"))
    table1_rows = []
    for _, r in t1.iterrows():
        table1_rows.append(
            [
                r["variable"],
                int(r["current_N"]),
                int(r["original_N"]),
                fmt(r["current_mean"]),
                fmt(r["original_mean"]),
                fmt(r["mean_diff_current_minus_original"]),
                pct(r["mean_pct_diff_vs_original"]),
                fmt(r["current_median"]),
                fmt(r["original_median"]),
            ]
        )
    story.extend(
        academic_table(
            "表 1　文本块层面描述性统计：当前口径 vs 原文",
            ["变量", "当前N", "原文N", "当前均值", "原文均值", "差值", "差异率", "当前中位数", "原文中位数"],
            table1_rows,
            [55, 42, 42, 55, 55, 48, 45, 55, 55],
            styles,
            "当前口径为 cot_v3b_len132_tight 全 543 家；原文为 552 家、8683 个文本块。差异率按均值差值除以原文均值计算。",
            highlight_rows={0},
        )
    )
    story.append(
        p(
            "表 1 显示，Summary_len 当前均值 128.253，原文 132.678；Redundancy_chunk 当前均值 30.708，原文 32.176。"
            "这说明摘要长度校准已经基本成功。更值得注意的是 Chunk_num 当前 14.054，原文 18.191，且当前 chunk 总数为 7028，"
            "比原文少 1655 个。这个差距更可能来自样本企业缺失、章节抽取边界或切块规则，而不是模型摘要长度本身。",
            styles,
        )
    )

    story.append(p("三、企业层描述性统计对比", styles, "heading1"))
    key_vars = [
        "lnN_tech",
        "Redundancy",
        "FInvention",
        "BHAR",
        "FSales_Growth",
        "RD_Asset",
        "Size",
        "Lev",
        "ROA",
        "Offerfee",
        "Underwriter",
        "Age",
        "NumIndSeg",
        "NumProdSeg",
        "ScopeLen",
    ]
    t2_key = t2[t2["variable"].isin(key_vars)].copy()
    t2_key["order"] = t2_key["variable"].map({v: i for i, v in enumerate(key_vars)})
    t2_key = t2_key.sort_values("order")
    table2_rows = []
    highlight = set()
    for idx, (_, r) in enumerate(t2_key.iterrows()):
        available = "是" if bool(r["current_available"]) else "否"
        table2_rows.append(
            [
                r["variable"],
                available,
                "" if pd.isna(r["current_N"]) else int(r["current_N"]),
                int(r["original_N"]),
                fmt(r["current_mean"]),
                fmt(r["original_mean"]),
                fmt(r["mean_diff_current_minus_original"]),
                pct(r["mean_pct_diff_vs_original"]),
            ]
        )
        if r["variable"] in {"Underwriter", "NumIndSeg", "NumProdSeg", "ScopeLen"}:
            highlight.add(idx)
    story.extend(
        academic_table(
            "表 2　企业层主要变量描述性统计：当前口径 vs 原文",
            ["变量", "当前可得", "当前N", "原文N", "当前均值", "原文均值", "差值", "差异率"],
            table2_rows,
            [68, 45, 42, 42, 55, 55, 50, 45],
            styles,
            "空白表示当前 master 未构造该变量。Underwriter 当前均值仅 0.009，源于临时 CSMAR 表 Sponsor 字段大多为 None。",
            highlight_rows=highlight,
        )
    )
    story.append(
        p(
            "企业层 X 的均值已经贴近原文：Redundancy 当前 29.374，原文 29.074。但 lnN_tech 当前 10.745，低于原文 10.962；"
            "换算后当前原始长度约为原文口径的 80.5%。这说明文本长度单位或业务与技术章节抽取边界仍需审计。"
            "Controls 方面，Underwriter 与 NumIndSeg、NumProdSeg、ScopeLen 是最大缺口，当前回归不能称为原文 Table 2 的 strict replication。",
            styles,
        )
    )

    story.append(PageBreak())
    story.append(p("四、Table 2 接入审计结果", styles, "heading1"))
    current = regs[(regs["sample"] == "full_by_y_available") & (regs["model"] == "controls_fe_current")].copy()
    paper_coef = {"FInvention": -0.0316, "BHAR": -0.0188, "FSales_Growth": -0.0373}
    paper_t = {"FInvention": -1.72, "BHAR": -2.14, "FSales_Growth": -2.02}
    reg_rows = []
    for _, r in current.iterrows():
        dep = r["dep_var"]
        reg_rows.append(
            [
                dep,
                int(r["N"]),
                fmt(r["coef"], 4),
                fmt(r["t_HC1"], 2),
                fmt(r["p_HC1"], 3),
                fmt(paper_coef[dep], 4),
                fmt(paper_t[dep], 2),
                "同号" if math.copysign(1, r["coef"]) == math.copysign(1, paper_coef[dep]) else "反号",
            ]
        )
    story.extend(
        academic_table(
            "表 3　Table 2 Panel B 主规格回归对比",
            ["被解释变量", "当前N", "当前coef", "当前t", "当前p", "原文coef", "原文t", "方向"],
            reg_rows,
            [80, 45, 58, 50, 50, 58, 50, 45],
            styles,
            "当前规格为 Outcome ~ Redundancy + lnN_tech + Size + Lev + ROA + Offerfee + Underwriter + Age + Year FE + Industry FE，HC1 robust 标准误。",
            highlight_rows={2},
        )
    )
    story.append(
        p(
            "接入真正的 len132_tight X 后，FInvention 与 BHAR 回到负号，但系数约只有原文的三分之一左右且不显著；"
            "FSales_Growth 仍为正号。共同样本与 2019-2022 窗口也不能把三项同时推回原文结果。"
            "这说明 Table 2 失败不应优先反推 X 测度失败，而应优先检查 outcome 与 controls 口径。",
            styles,
        )
    )

    story.append(p("五、当前 replication gap 的优先级", styles, "heading1"))
    priority_rows = [
        ["1", "Underwriter", "当前均值 0.009，原文 0.574；Sponsor 字段几乎全空", "从 Choice 或可替代 IPO 承销数据库重构主承销商/保荐机构 top10 dummy"],
        ["2", "NumIndSeg / NumProdSeg / ScopeLen", "原文明确控制，当前完全缺失", "补齐业务分部、产品分部、经营范围长度；先复现 Panel A 均值"],
        ["3", "FSales_Growth", "当前均值 0.409，原文 0.530；回归仍反号", "做 t+1/t、完整会计年度、字段来源、winsor、471 样本网格"],
        ["4", "lnN_tech", "当前 10.745，原文 10.962；原始长度约为原文的 80.5%", "并行比较原始字符、去空白字符、中文字数、token proxy"],
        ["5", "552 -> 471 crosswalk", "当前 543/541/528，与原文 552/471 未对齐", "逐家公司列出 X、上市年、三个 Y、controls 和最终样本进入情况"],
    ]
    story.extend(
        academic_table(
            "表 4　下一阶段审计任务优先级",
            ["顺序", "对象", "当前问题", "建议动作"],
            priority_rows,
            [35, 85, 160, 190],
            styles,
            "这些任务应先于任何新的 prompt 调参或 LLM 重跑。",
        )
    )

    story.append(p("六、结论", styles, "heading1"))
    story.append(
        p(
            "当前最稳妥的研究状态表述是：cot_v3b_len132_tight 已锁定为下一阶段 empirical audit 的主 X 口径，"
            "暂停 prompt、tailfix 与 summary length 调参。Table 2 strict replication 仍未通过，不能宣称复刻原文经济后果。"
            "下一阶段主战场是 Choice/CSMAR 字段、原文 controls、Y 变量口径与样本 waterfall。",
            styles,
        )
    )
    story.append(
        p(
            "若后续 Underwriter 与三项 paper-only controls 补齐后，FInvention 与 BHAR 仍保持负号但较弱，而 FSales_Growth 仍反号，"
            "则应优先重查 FSales_Growth 的会计年度口径与 winsor 处理，而不是回头重建 X。",
            styles,
        )
    )

    story.append(Spacer(1, 8))
    story.append(TopRule(w, colors.HexColor("#888888"), 0.5))
    story.append(p("数据来源与输出文件", styles, "heading2"))
    story.append(
        p(
            "主要输入：descriptive_comparison_vs_original_20260705、table2_len132_tight_audit_20260705、"
            "summary_len_calibration_full_543_20260704。原文锚点来自本地 PDF 的表 1 与表 2。",
            styles,
            "note",
        )
    )
    return story


def draw_page(canvas, doc):
    canvas.saveState()
    canvas.setFont("Songti", 8)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(22 * mm, 12 * mm, "IPO 信息披露冗余复刻审计报告")
    canvas.drawRightString(A4[0] - 22 * mm, 12 * mm, f"{doc.page}")
    canvas.setStrokeColor(colors.HexColor("#CCCCCC"))
    canvas.setLineWidth(0.4)
    canvas.line(22 * mm, 17 * mm, A4[0] - 22 * mm, 17 * mm)
    canvas.restoreState()


def build_pdf() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    song, hei = register_fonts()
    styles = make_styles(song, hei)
    doc = SimpleDocTemplate(
        str(PDF_OUT),
        pagesize=A4,
        leftMargin=21 * mm,
        rightMargin=21 * mm,
        topMargin=22 * mm,
        bottomMargin=22 * mm,
        title="IPO 信息披露冗余复刻审计报告",
        author="Codex",
    )
    story = build_story(styles)
    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    print(PDF_OUT)


if __name__ == "__main__":
    build_pdf()
