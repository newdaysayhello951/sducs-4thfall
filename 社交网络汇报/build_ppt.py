# -*- coding: utf-8 -*-
"""黎贤栗2.pptx -- NL => Schedule 汇报（30 页极简版：无备注，每页 2-3 句）"""
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

BASE = r"C:\Users\86134\Desktop\大四上\社交网络汇报"
FIG = os.path.join(BASE, "figs")
OUT = os.path.join(BASE, "_out.pptx")

INK, GRAY, LGRAY = RGBColor(0x1A, 0x23, 0x32), RGBColor(0x5B, 0x65, 0x73), RGBColor(0x8B, 0x95, 0xA3)
ACCENT, ACC_D = RGBColor(0x1F, 0x5A, 0xC0), RGBColor(0x14, 0x3E, 0x8A)
AMBER, SOFT, RULE = RGBColor(0xB8, 0x7A, 0x1E), RGBColor(0xF3, 0xF5, 0xF9), RGBColor(0xD5, 0xDB, 0xE5)
WHITE, GREEN, RED = RGBColor(0xFF, 0xFF, 0xFF), RGBColor(0x1E, 0x7A, 0x4B), RGBColor(0xA8, 0x2C, 0x2C)

FONT, FONT_N = "Microsoft YaHei", "Segoe UI"
prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
L, CW = Inches(0.78), Inches(11.78)


def set_ea(run, font=FONT):
    rPr = run.font._rPr
    for tag in ("a:ea", "a:cs"):
        el = rPr.find(qn(tag))
        if el is None:
            el = rPr.makeelement(qn(tag), {}); rPr.append(el)
        el.set("typeface", font)


def sr(run, size, bold=False, color=INK, font=FONT):
    run.font.size = Pt(size); run.font.bold = bold
    run.font.color.rgb = color; run.font.name = font
    set_ea(run, font); return run


def tb(slide, x, y, w, h, align=PP_ALIGN.LEFT):
    tf = slide.shapes.add_textbox(x, y, w, h).text_frame
    tf.word_wrap = True
    for a in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, a, 0)
    tf.paragraphs[0].alignment = align
    return tf


def put(tf, text, size, bold=False, color=INK, font=FONT, first=False,
        sb=0, line=1.25, align=None):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.space_before = Pt(sb); p.line_spacing = line
    if align is not None:
        p.alignment = align
    sr(p.add_run(), size, bold, color, font).text = text
    return p


def strip_style(sh):
    st = sh._element.find(qn("p:style"))
    if st is not None:
        sh._element.remove(st)
    return sh


def rule(slide, x, y, w, h=Emu(15240), color=ACCENT):
    sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, w, h)
    sh.fill.solid(); sh.fill.fore_color.rgb = color
    sh.line.fill.background(); sh.shadow.inherit = False; strip_style(sh)
    return sh


def card(slide, x, y, w, h, fill=SOFT, line=None):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, y, w, h)
    sh.adjustments[0] = 0.055
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = line; sh.line.width = Pt(1)
    sh.shadow.inherit = False; strip_style(sh)
    return sh


def head(slide, kicker, title):
    put(tb(slide, L, Inches(0.52), CW, Inches(0.3)), kicker, 12, True, ACCENT,
        FONT_N, first=True)
    put(tb(slide, L, Inches(0.86), CW, Inches(0.62)), title, 27, True, INK,
        first=True, line=1.0)
    rule(slide, L, Inches(1.58), Inches(0.72), Emu(22860))


def footer(slide):
    n = len(prs.slides._sldIdLst)
    put(tb(slide, L, Inches(7.06), Inches(7.4), Inches(0.24)),
        "NL ⇒ Schedule  ·  ACL 2026  ·  黎贤栗", 9.5, False, LGRAY, first=True)
    put(tb(slide, Inches(11.2), Inches(7.06), Inches(1.36), Inches(0.24),
           align=PP_ALIGN.RIGHT), f"{n:02d}", 10, True, LGRAY, FONT_N, first=True,
        align=PP_ALIGN.RIGHT)


def ns(kicker, title):
    s = prs.slides.add_slide(BLANK)
    head(s, kicker, title)
    footer(s)
    return s


def table(slide, x, y, w, h, rows, widths, fs=11, first_col_bold=False,
          align_right_from=1, row_heights=None, force_left=()):
    nr, nc = len(rows), len(rows[0])
    t = slide.shapes.add_table(nr, nc, x, y, w, h).table
    t.first_row = True; t.horz_banding = False
    for j, cwd in enumerate(widths):
        t.columns[j].width = cwd
    for i in range(nr):
        t.rows[i].height = row_heights[i] if row_heights else Inches(0.30)
    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            c = t.cell(i, j)
            c.margin_left = c.margin_right = Inches(0.08)
            c.margin_top = c.margin_bottom = Inches(0.02)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.fill.solid()
            c.fill.fore_color.rgb = ACC_D if i == 0 else (WHITE if i % 2 else SOFT)
            c.text_frame.word_wrap = True
            p = c.text_frame.paragraphs[0]
            right = (j >= align_right_from) and (j not in force_left)
            p.alignment = PP_ALIGN.RIGHT if right else PP_ALIGN.LEFT
            sr(p.add_run(), fs, i == 0 or (first_col_bold and j == 0),
               WHITE if i == 0 else INK).text = val
    return t


def pic(slide, name, x, y, w=None, h=None):
    kw = {}
    if w is not None:
        kw["width"] = w
    if h is not None:
        kw["height"] = h
    return slide.shapes.add_picture(os.path.join(FIG, name), x, y, **kw)


def cap(slide, x, y, w, txt):
    put(tb(slide, x, y, w, Inches(0.24)), txt, 9, False, LGRAY, first=True, line=1.1)


def big(slide, x, y, w, num, label, color=ACCENT, ns_=34):
    put(tb(slide, x, y, w, Inches(0.62)), num, ns_, True, color, FONT_N, first=True,
        line=1.0)
    put(tb(slide, x, y + Inches(0.60), w, Inches(0.5)), label, 10.5, False, GRAY,
        first=True, line=1.35)


# =====================================================================
# 01 封面
# =====================================================================
s = prs.slides.add_slide(BLANK)
bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
bg.fill.solid(); bg.fill.fore_color.rgb = WHITE; bg.line.fill.background()
bg.shadow.inherit = False; strip_style(bg)
bd = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(0.30), prs.slide_height)
bd.fill.solid(); bd.fill.fore_color.rgb = ACCENT; bd.line.fill.background()
bd.shadow.inherit = False; strip_style(bd)
put(tb(s, Inches(1.15), Inches(1.66), Inches(10.6), Inches(0.34)),
    "ACL 2026  ·  Long Paper  ·  CCF-A", 13, True, ACCENT, FONT_N, first=True)
put(tb(s, Inches(1.12), Inches(2.16), Inches(10.8), Inches(1.0)),
    "NL  ⇒  Schedule", 50, True, INK, first=True, line=1.0)
tf = tb(s, Inches(1.15), Inches(3.22), Inches(10.6), Inches(1.0))
put(tf, "Evaluate Multitask Scheduling Capability", 20, False, GRAY, first=True, line=1.3)
put(tf, "of Large Language Models", 20, False, GRAY, line=1.3)
rule(s, Inches(1.15), Inches(4.52), Inches(2.1), Emu(28448))
tf = tb(s, Inches(1.15), Inches(4.86), Inches(10.6), Inches(0.9))
put(tf, "廖文瑞 · 杜伟宏 · 李毅 · 梁鸿儒 · 雷文强", 13, False, INK, first=True, line=1.5)
put(tf, "四川大学 计算机学院 / 人工智能学院", 12, False, LGRAY, line=1.5)
put(tb(s, Inches(1.15), Inches(6.30), Inches(10.6), Inches(0.5)),
    "汇报人：黎贤栗        社交网络与舆情分析", 13, True, ACCENT, first=True, line=1.3)

# =====================================================================
# 02 主线
# =====================================================================
s = ns("OVERVIEW", "一条主线：立考题 → 找病因 → 开药")
items = [("01", "立考题", "这个任务是什么？\n现有方法为什么不行？", ACCENT),
         ("02", "找病因", "LLM 做不好，\n究竟错在哪一层？", AMBER),
         ("03", "开药", "MANS：四个 agent\n各修一层错误", GREEN)]
for k, (num, t, d, col) in enumerate(items):
    x = L + (Inches(3.86) + Inches(0.22)) * k
    card(s, x, Inches(2.10), Inches(3.86), Inches(2.90), SOFT)
    rule(s, x, Inches(2.10), Inches(0.055), Inches(2.90), col)
    put(tb(s, x + Inches(0.34), Inches(2.36), Inches(3.2), Inches(0.5)), num, 34, True,
        col, FONT_N, first=True)
    put(tb(s, x + Inches(0.34), Inches(2.98), Inches(3.2), Inches(0.4)), t, 20, True,
        INK, first=True)
    put(tb(s, x + Inches(0.34), Inches(3.52), Inches(3.2), Inches(1.2)), d, 12, False,
        GRAY, first=True, line=1.5)
put(tb(s, L, Inches(5.44), CW, Inches(0.8)),
    "LLM 看得懂、想得远，但落不了地 —— 所以要把“落地”拆成四步。", 17, True, INK,
    first=True, line=1.3)

# =====================================================================
# 03 任务定义
# =====================================================================
s = ns("TASK", "任务定义：从一段人话，推出一个可行方案")
pic(s, "ppt_fig1.png", Inches(5.96), Inches(1.78), w=Inches(6.62))
cap(s, Inches(5.96), Inches(6.54), Inches(6.62),
    "Figure 1 | (a) 自然语言订单 vs 矩阵　(b) 最优调度")
tf = tb(s, L, Inches(1.92), Inches(4.9), Inches(0.4))
put(tf, "输入", 12, True, ACCENT, first=True)
put(tf, "一段自然语言订单", 14, False, INK, sb=4)
tf = tb(s, L, Inches(2.92), Inches(4.9), Inches(0.4))
put(tf, "输出", 12, True, ACCENT, first=True)
put(tf, "一份可行调度方案", 14, False, INK, sb=4)
card(s, L, Inches(3.94), Inches(4.9), Inches(1.02), SOFT)
tf = tb(s, L + Inches(0.24), Inches(4.06), Inches(4.4), Inches(0.8))
put(tf, "要的是 feasible，不是 optimal", 13, True, AMBER, first=True, line=1.3)
put(tf, "合法即可 —— 但最好的模型也只有 32.5%。", 11, False, GRAY, line=1.3, sb=3)
put(tb(s, L, Inches(5.24), Inches(4.9), Inches(1.0)),
    "它不是翻译，是归纳推理：\n理解多目标 · 识别约束 · 多步推理", 14, True, INK,
    first=True, line=1.6)

# =====================================================================
# 04 矩阵解码
# =====================================================================
s = ns("TASK · 细节", "Figure 1 右侧的矩阵，到底在说什么")
pic(s, "ppt_matrix.png", Inches(6.90), Inches(1.86), w=Inches(5.68))
cap(s, Inches(6.90), Inches(4.72), Inches(5.68), "Figure 1(a) 矩阵放大：3 行 × 10 列")
put(tb(s, L, Inches(1.80), Inches(5.9), Inches(0.3)),
    "行 = 一个任务；两两一组 =（机器, 时长）", 12, True, ACCENT, first=True)
rows = [["行", "菜品", "步骤1", "步骤2", "步骤3", "步骤4", "步骤5"],
        ["1", "汉堡", "M0,2", "M1,10", "M0,2", "M2,6", "M0,6"],
        ["2", "寿司卷", "M0,2", "M2,6", "M0,2", "M3,10", "M0,6"],
        ["3", "卷饼", "M0,2", "M3,10", "M0,2", "M1,10", "M0,6"]]
table(s, L, Inches(2.16), Inches(5.9), Inches(1.30), rows,
      [Inches(0.44), Inches(1.10), Inches(0.86), Inches(0.90), Inches(0.86), Inches(0.86), Inches(0.88)],
      fs=10, first_col_bold=True, align_right_from=2, row_heights=[Inches(0.32)] * 4)
mach = [("M0", "机械臂", RED), ("M1", "平底锅", GRAY), ("M2", "砧板", GRAY), ("M3", "灶具", GRAY)]
for k, (m, name, col) in enumerate(mach):
    x = L + Inches(1.50) * k
    card(s, x, Inches(3.70), Inches(1.32), Inches(0.74), SOFT)
    put(tb(s, x + Inches(0.16), Inches(3.80), Inches(1.0), Inches(0.28)), m, 12, True,
        col, FONT_N, first=True)
    put(tb(s, x + Inches(0.16), Inches(4.08), Inches(1.0), Inches(0.28)), name, 10,
        False, GRAY, first=True)
card(s, L, Inches(4.74), Inches(5.9), Inches(1.10), WHITE, line=ACCENT)
tf = tb(s, L + Inches(0.24), Inches(4.88), Inches(5.42), Inches(0.86))
put(tf, "三个任务都反复用 M0（机械臂）—— 它就是瓶颈", 13, True, RED, first=True, line=1.3)
put(tf, "这也解释了 Cooking 的瓶颈负载为什么是 1.00。", 11, False, GRAY, line=1.3, sb=3)
put(tb(s, L, Inches(6.06), Inches(5.9), Inches(0.6)),
    "矩阵里每个数字都是人替模型填好的 —— 这就是 research gap。", 12, True, AMBER,
    first=True, line=1.4)

# =====================================================================
# 05 三个缺口
# =====================================================================
s = ns("MOTIVATION", "现有工作的三个缺口，对应本文的三块贡献")
cards = [("缺口一", "绕过语言", "直接吃矩阵，\n“理解”由人工代劳"),
         ("缺口二", "数据不真实", "随机或规则生成，\n与真实车间不符"),
         ("缺口三", "流水线太脆", "建模 → 代码 → 求解，\n任一环断就全崩")]
for k, (tag, t, d) in enumerate(cards):
    x = L + (Inches(3.86) + Inches(0.22)) * k
    card(s, x, Inches(2.06), Inches(3.86), Inches(1.96), SOFT)
    put(tb(s, x + Inches(0.30), Inches(2.24), Inches(3.2), Inches(0.3)), tag, 11, True,
        LGRAY, first=True)
    put(tb(s, x + Inches(0.30), Inches(2.58), Inches(3.2), Inches(0.4)), t, 17, True,
        INK, first=True)
    put(tb(s, x + Inches(0.30), Inches(3.10), Inches(3.3), Inches(0.8)), d, 11.5, False,
        GRAY, first=True, line=1.5)
qs = [("RQ1", "能不能端到端做好？"), ("RQ2", "错在哪一层？"), ("RQ3", "怎么补？")]
for k, (q, t) in enumerate(qs):
    x = L + Inches(3.95) * k
    tf = tb(s, x, Inches(4.40), Inches(3.8), Inches(0.5))
    p = tf.paragraphs[0]; p.line_spacing = 1.2
    sr(p.add_run(), 15, True, AMBER).text = q + "　"
    sr(p.add_run(), 15, False, INK).text = t
put(tb(s, L, Inches(5.24), CW, Inches(0.9)),
    "三块贡献：任务定义 · 数据集 · MANS 框架。", 16, True, INK, first=True, line=1.4)

# =====================================================================
# 06 造数据总览
# =====================================================================
s = ns("BENCHMARK", "造数据：五步，从公开资料到 240 个实例")
pic(s, "ppt_fig2.png", L, Inches(1.90), w=CW)
cap(s, L, Inches(4.10), CW, "Figure 2 | 数据爬取与形式化 → 调度实例组合 → 问题描述生成")
steps = [("①", "数据来源", "4 书 + 3 站 + 3 游戏", ACCENT),
         ("②", "任务图", "135 个", ACCENT),
         ("③", "Jaccard 聚类", "13 个车间", AMBER),
         ("④", "组合实例", "240 个 + 最优解", AMBER),
         ("⑤", "生成描述", "240 段人话", GREEN)]
sw, sg = Inches(2.244), Inches(0.14)
for k, (num, t, d, col) in enumerate(steps):
    x = L + (sw + sg) * k
    card(s, x, Inches(4.36), sw, Inches(1.06), SOFT)
    rule(s, x, Inches(4.36), sw, Inches(0.04), col)
    put(tb(s, x + Inches(0.20), Inches(4.48), Inches(0.4), Inches(0.28)), num, 12, True,
        col, FONT_N, first=True)
    put(tb(s, x + Inches(0.60), Inches(4.50), sw - Inches(0.72), Inches(0.28)), t, 11,
        True, INK, first=True)
    put(tb(s, x + Inches(0.20), Inches(4.86), sw - Inches(0.34), Inches(0.4)), d, 9.5,
        False, GRAY, first=True)
put(tb(s, L, Inches(5.72), CW, Inches(0.8)),
    "顺序是反的：先有结构化的任务图，后有自然语言 —— 所以它是半合成的。", 16, True,
    INK, first=True, line=1.4)

# =====================================================================
# 07 数据来源
# =====================================================================
s = ns("① 数据来源", "一半是工程手册，一半是电子游戏")
cols = [("4 本专业书", ["Pinedo《Scheduling》", "Singh《Systems Approach》",
                    "Groover《Fundamentals》", "《Automotive Handbook》"], ACCENT),
        ("3 个工业网站", ["SAE 学会", "DMG MORI 机床", "丰田虚拟工厂"], AMBER),
        ("3 款电子游戏", ["Overcooked! 2 → 烹饪", "Big Pharma → 制药",
                    "Construction Simulator → 建筑"], GREEN)]
for k, (t, items_, col) in enumerate(cols):
    x = L + (Inches(3.86) + Inches(0.22)) * k
    card(s, x, Inches(1.94), Inches(3.86), Inches(2.36), SOFT)
    rule(s, x, Inches(1.94), Inches(0.05), Inches(2.36), col)
    put(tb(s, x + Inches(0.28), Inches(2.14), Inches(3.3), Inches(0.34)), t, 14, True,
        INK, first=True)
    tf = tb(s, x + Inches(0.28), Inches(2.60), Inches(3.34), Inches(1.6))
    for i, it in enumerate(items_):
        put(tf, it, 10.5, False, GRAY, first=(i == 0), line=1.4, sb=0 if i == 0 else 10)
put(tb(s, L, Inches(4.62), CW, Inches(0.8)),
    "为什么用游戏？真实排产是商业机密，而模拟游戏把“工序 / 设备 / 耗时”建模得最精确。",
    16, True, INK, first=True, line=1.4)
put(tb(s, L, Inches(5.52), CW, Inches(0.6)),
    "这也说明这个领域的困境：要研究真实世界，但真实世界不给数据。", 13, False, GRAY,
    first=True, line=1.4)

# =====================================================================
# 08 形式化
# =====================================================================
s = ns("② 形式化", "把资料变成图：135 个基础任务图")
put(tb(s, L, Inches(1.86), CW, Inches(0.4)),
    "一个任务 = 一张有向无环图：节点是步骤（机器 + 时长），边是先后约束。", 14, True,
    INK, first=True, line=1.4)
rows = [["场景", "#Task", "#Machine", "#Avg Step"],
        ["Manufacturing 制造", "28", "32", "5.07"],
        ["Construction 建筑", "29", "44", "8.69"],
        ["Pharmaceuticals 制药", "32", "12", "4.12"],
        ["Cooking 烹饪", "46", "20", "7.42"],
        ["合计", "135", "—", "—"]]
table(s, L, Inches(2.58), Inches(7.4), Inches(2.40), rows,
      [Inches(2.98), Inches(1.44), Inches(1.56), Inches(1.42)], fs=12,
      first_col_bold=True, align_right_from=1, row_heights=[Inches(0.40)] * 6)
cap(s, L, Inches(5.08), Inches(7.4), "Table 1 | 28 + 29 + 32 + 46 = 135")
card(s, Inches(8.50), Inches(2.58), Inches(4.06), Inches(2.40), WHITE, line=ACCENT)
tf = tb(s, Inches(8.76), Inches(2.76), Inches(3.56), Inches(2.0))
put(tf, "只收结构化图，不收文本", 13, True, RED, first=True, line=1.25)
put(tf, "公开资料里没有哪份文档会写到“这步用哪台机器、要多久”。", 11.5, False, GRAY,
    line=1.45, sb=6)
put(tf, "所以只能先有图，再反向生成文字。", 11.5, True, INK, line=1.45, sb=6)
put(tb(s, L, Inches(5.62), CW, Inches(0.8)),
    "同一张图的三种写法：图 · 矩阵 · JSON —— 三者等价。", 15, True, INK, first=True,
    line=1.4)

# =====================================================================
# 09 Jaccard + K-Medoids
# =====================================================================
s = ns("③ Jaccard 聚类", "聚成 13 个车间：让任务去抢同一批机器")
put(tb(s, L, Inches(1.84), Inches(6.5), Inches(0.3)),
    "① 把任务图变成“机器向量”", 12, True, ACCENT, first=True)
rows = [["任务", "M0", "M1", "M2", "M3"],
        ["汉堡", "1", "1", "1", "0"],
        ["薯条", "1", "1", "0", "0"],
        ["寿司", "1", "0", "1", "0"]]
table(s, L, Inches(2.16), Inches(4.0), Inches(1.20), rows,
      [Inches(1.30), Inches(0.68), Inches(0.68), Inches(0.68), Inches(0.66)], fs=11,
      first_col_bold=True, align_right_from=1, row_heights=[Inches(0.30)] * 4)
put(tb(s, L, Inches(3.52), Inches(6.5), Inches(0.3)),
    "② 两两算 Jaccard：交集 ÷ 并集", 12, True, ACCENT, first=True)
card(s, L, Inches(3.84), Inches(6.5), Inches(0.62), SOFT)
put(tb(s, L + Inches(0.24), Inches(3.98), Inches(6.0), Inches(0.4)),
    "J = |a∩b| / |a∪b|", 14, True, INK, FONT_N, first=True)
put(tb(s, L, Inches(4.60), Inches(6.5), Inches(0.8)),
    "汉堡 vs 薯条 = 2/3 = 0.67 → 很像，放一起；薯条 vs 寿司只有 1/3。", 11.5, False,
    GRAY, first=True, line=1.4)
put(tb(s, L, Inches(5.34), Inches(6.5), Inches(0.4)),
    "③ 用 K-Medoids 聚成 13 个车间", 12, True, ACCENT, first=True)
put(tb(s, L, Inches(5.66), Inches(6.5), Inches(0.8)),
    "一个簇 = 一个车间：里面的任务都在抢同一批机器。", 11.5, False, GRAY, first=True,
    line=1.4)
put(tb(s, Inches(7.70), Inches(1.84), Inches(4.86), Inches(0.3)),
    "聚类结果", 12, True, ACCENT, first=True)
rows2 = [["场景", "车间数"],
         ["Manufacturing", "7"],
         ["Construction", "4"],
         ["Pharmaceuticals", "1"],
         ["Cooking", "1"],
         ["合计", "13"]]
table(s, Inches(7.70), Inches(2.16), Inches(4.86), Inches(1.56), rows2,
      [Inches(3.30), Inches(1.56)], fs=11.5, first_col_bold=True,
      align_right_from=1, row_heights=[Inches(0.26)] * 6)
card(s, Inches(7.70), Inches(3.94), Inches(4.86), Inches(1.24), SOFT)
tf = tb(s, Inches(7.94), Inches(4.08), Inches(4.4), Inches(1.0))
put(tf, "为什么不用 K-Means？", 11.5, True, AMBER, first=True, line=1.25)
put(tf, "二值向量的平均值是虚构的点；K-Medoids 的中心必须是真实样本。", 11, False,
    GRAY, line=1.45, sb=4)
put(tb(s, L, Inches(6.32), CW, Inches(0.5)),
    "难度不来自“任务多”，而来自“任务之间抢同一批资源”。", 15, True, INK, first=True,
    line=1.3)

# =====================================================================
# 10 组合实例
# =====================================================================
s = ns("④ 组合实例", "4 × 6 × 10 = 240，再用 OR-Tools 打最优解")
card(s, L, Inches(1.90), Inches(6.1), Inches(1.20), SOFT)
tf = tb(s, L + Inches(0.28), Inches(2.06), Inches(5.5), Inches(0.9))
p = tf.paragraphs[0]; p.line_spacing = 1.15
sr(p.add_run(), 18, True, INK).text = "4 场景 × 6 规模 × 10 实例"
p2 = tf.add_paragraph(); p2.line_spacing = 1.15; p2.space_before = Pt(4)
sr(p2.add_run(), 18, True, ACCENT).text = "= 240"
put(tb(s, L, Inches(3.28), Inches(6.1), Inches(0.6)),
    "13 个车间不进这个乘法 —— 它只决定“谁能和谁组合”。", 12.5, False, GRAY, first=True,
    line=1.4)
rows = [["#Task=10 的实例", "份数"],
        ["汉堡 burger", "×3"],
        ["煎饼 pancake", "×4"],
        ["披萨 pizza", "×3"],
        ["合计", "10"]]
table(s, L, Inches(3.96), Inches(6.1), Inches(1.36), rows,
      [Inches(4.60), Inches(1.50)], fs=11, first_col_bold=True,
      align_right_from=1, row_heights=[Inches(0.272)] * 5)
put(tb(s, L, Inches(5.48), Inches(6.1), Inches(0.6)),
    "n 是任务份数，含副本 —— 副本是“难度旋钮”，把资源竞争拉满。", 11.5, False, GRAY,
    first=True, line=1.4)
put(tb(s, Inches(7.34), Inches(1.90), Inches(5.22), Inches(0.3)),
    "最后一步：OR-Tools 打最优解", 12, True, ACCENT, first=True)
card(s, Inches(7.34), Inches(2.22), Inches(5.22), Inches(1.66), WHITE, line=ACCENT)
tf = tb(s, Inches(7.58), Inches(2.40), Inches(4.74), Inches(1.4))
put(tf, "The optimal schedules are annotated by OR-Tools", 11, True, INK, FONT_N,
    first=True, line=1.3)
put(tf, "它给出的解就是评测时的“标准答案”，RMD 拿它当分母。", 11.5, False, GRAY,
    line=1.4, sb=6)
put(tf, "保留：严格说是“时限内最优”。", 10.5, True, AMBER, line=1.4, sb=6)
put(tb(s, Inches(7.34), Inches(4.12), Inches(5.22), Inches(0.3)),
    "一个实例 = 三件套", 12, True, ACCENT, first=True)
for k, (t, col) in enumerate([("问题描述", ACCENT), ("任务图列表", AMBER), ("最优调度", GREEN)]):
    x = Inches(7.34) + Inches(1.78) * k
    card(s, x, Inches(4.46), Inches(1.62), Inches(0.66), SOFT)
    rule(s, x, Inches(4.46), Inches(0.04), Inches(0.66), col)
    put(tb(s, x + Inches(0.18), Inches(4.64), Inches(1.4), Inches(0.32)), t, 11, True,
        INK, first=True)
put(tb(s, L, Inches(6.28), CW, Inches(0.5)),
    "车间平均只有 4–7 个任务图，抽 10 个 unique 不可能 —— 副本正好化解。", 14, True,
    INK, first=True, line=1.3)

# =====================================================================
# 11 模板 + 润色
# =====================================================================
s = ns("⑤ 生成描述", "模板保事实，LLM 保通顺")
put(tb(s, L, Inches(1.90), Inches(5.6), Inches(0.3)), "两步走", 12, True, ACCENT,
    first=True)
st = [("第 1 步　模板填充", "保证信息一条不少、一个字不编", ACCENT),
      ("第 2 步　GPT-4 润色", "只改语言，不改事实", GREEN)]
for k, (t, d, col) in enumerate(st):
    y = Inches(2.22) + Inches(1.10) * k
    card(s, L, y, Inches(5.6), Inches(0.92), SOFT)
    rule(s, L, y, Inches(0.045), Inches(0.92), col)
    put(tb(s, L + Inches(0.26), y + Inches(0.14), Inches(5.1), Inches(0.3)), t, 13, True,
        col, first=True)
    put(tb(s, L + Inches(0.26), y + Inches(0.50), Inches(5.1), Inches(0.3)), d, 11,
        False, GRAY, first=True)
put(tb(s, L, Inches(4.42), Inches(5.6), Inches(0.9)),
    "为什么不直接让 GPT-4 写？\n它会编造或漏掉关键信息。", 13, True, INK, first=True,
    line=1.5)
put(tb(s, Inches(6.78), Inches(1.90), Inches(5.78), Inches(0.3)), "描述的模板从哪来",
    12, True, ACCENT, first=True)
tpl = [("20 个需求模板", "合同与点单对话", ACCENT),
       ("每领域 10 个流程模板", "工艺手册、菜谱（共 40 个）", AMBER)]
for k, (t, d, col) in enumerate(tpl):
    y = Inches(2.22) + Inches(0.90) * k
    card(s, Inches(6.78), y, Inches(5.78), Inches(0.74), SOFT)
    rule(s, Inches(6.78), y, Inches(0.045), Inches(0.74), col)
    put(tb(s, Inches(7.02), y + Inches(0.10), Inches(2.6), Inches(0.3)), t, 11.5, True,
        INK, first=True)
    put(tb(s, Inches(7.02), y + Inches(0.40), Inches(5.3), Inches(0.28)), d, 10.5,
        False, GRAY, first=True)
card(s, Inches(6.78), Inches(4.10), Inches(5.78), Inches(1.24), WHITE, line=RULE)
tf = tb(s, Inches(7.02), Inches(4.24), Inches(5.3), Inches(1.0))
put(tf, "描述是两段式", 11.5, True, ACCENT, first=True, line=1.25)
put(tf, "① 调度需求概述（提供约束与目标）　② 每个任务的流程（提供任务图信息）", 11,
    False, GRAY, line=1.45, sb=4)
put(tb(s, L, Inches(5.66), CW, Inches(0.6)),
    "这个分工有消融为证：拼接版 Accuracy 已 4.20，完整版提升最大的是简洁性。", 14, True,
    INK, first=True, line=1.4)

# =====================================================================
# 12 质量验证
# =====================================================================
s = ns("数据质量", "造出来的数据可信吗？")
pic(s, "ppt_fig67.png", Inches(1.42), Inches(1.80), w=Inches(10.5))
cap(s, Inches(1.42), Inches(4.18), Inches(10.5),
    "Figure 6 | 自动评测（事实保真）　｜　Figure 7 | 人工评测（完整版 vs 只拼接模板）")
for k, (num, lab, col) in enumerate([("0.98", "ESA 动作覆盖", ACCENT),
                                     ("0.94", "FINE 无幻觉", AMBER),
                                     ("≥ 0.75", "专家评分 ICC", GREEN)]):
    x = L + (Inches(3.86) + Inches(0.22)) * k
    big(s, x, Inches(4.60), Inches(3.86), num, lab, col, ns_=30)
put(tb(s, L, Inches(5.94), CW, Inches(0.6)),
    "模板管事实，LLM 管通顺 —— 这是被消融实验证明的。", 15, True, INK, first=True,
    line=1.4)

# =====================================================================
# 13 四种难度
# =====================================================================
s = ns("数据难度", "四个场景 = 四种难度，各测一个方面")
rows = [["场景", "Overlap %", "Max Load", "平均步数", "共享度"],
        ["Manufacturing", "80.49 %", "0.96", "5.05", "5.98"],
        ["Construction", "54.98 %", "0.77", "8.67", "4.02"],
        ["Pharmaceuticals", "64.06 %", "0.93", "4.17", "4.65"],
        ["Cooking", "48.36 %", "1.00", "7.19", "2.98"]]
table(s, L, Inches(1.86), CW, Inches(1.60), rows,
      [Inches(2.70), Inches(2.20), Inches(2.16), Inches(2.28), Inches(2.44)], fs=12,
      first_col_bold=True, align_right_from=1, row_heights=[Inches(0.32)] * 5)
cap(s, L, Inches(3.52), CW, "Table 8 | EmbSim 全局 0.4150，远低于各场景内部 —— 跨领域语言差异极大")
diff = [("Manufacturing", "竞争最激烈", AMBER), ("Construction", "长链依赖", AMBER),
        ("Pharmaceuticals", "高频短任务", AMBER), ("Cooking", "零空闲", GREEN)]
for k, (name, tag, col) in enumerate(diff):
    x = L + (Inches(2.86) + Inches(0.15)) * k
    card(s, x, Inches(4.00), Inches(2.86), Inches(1.10), SOFT)
    rule(s, x, Inches(4.00), Inches(2.86), Inches(0.04), col)
    put(tb(s, x + Inches(0.22), Inches(4.16), Inches(2.5), Inches(0.3)), name, 11, True,
        INK, FONT_N, first=True)
    put(tb(s, x + Inches(0.22), Inches(4.52), Inches(2.5), Inches(0.36)), tag, 15, True,
        col, first=True)
put(tb(s, L, Inches(5.50), CW, Inches(0.6)),
    "四个场景不是凑数，而是刻意覆盖四种难度来源。", 15, True, INK, first=True, line=1.3)

# =====================================================================
# 14 指标设计
# =====================================================================
s = ns("METRICS", "三层指标：为什么是三层")
fun = [(0.00, 5.30, "SER", "步骤执行率", "对的步数 ÷ 总步数", ACCENT),
       (0.38, 4.54, "TCR", "任务完成率", "全对的任务数 ÷ 任务总数", AMBER),
       (0.82, 3.68, "SFR", "方案可行率", "全部任务都对吗？", RED)]
for k, (off, w, tag, name, f, col) in enumerate(fun):
    x = L + Inches(off)
    y = Inches(1.90) + Inches(1.16) * k
    card(s, x, y, Inches(w), Inches(0.98), SOFT)
    rule(s, x, y, Inches(0.05), Inches(0.98), col)
    put(tb(s, x + Inches(0.24), y + Inches(0.12), Inches(1.0), Inches(0.3)), tag, 14,
        True, col, FONT_N, first=True)
    put(tb(s, x + Inches(1.16), y + Inches(0.12), Inches(w) - Inches(1.4), Inches(0.3)),
        name, 12, True, INK, first=True)
    put(tb(s, x + Inches(0.24), y + Inches(0.52), Inches(w) - Inches(0.5), Inches(0.3)),
        f, 11, False, GRAY, first=True)
put(tb(s, Inches(6.60), Inches(1.90), Inches(5.96), Inches(0.3)),
    "手算一个例子", 12, True, ACCENT, first=True)
rows = [["任务", "步数", "做对"],
        ["汉堡", "2", "2"],
        ["寿司", "2", "1"],
        ["合计", "4", "3"]]
table(s, Inches(6.60), Inches(2.22), Inches(3.4), Inches(1.02), rows,
      [Inches(1.50), Inches(0.96), Inches(0.94)], fs=11, first_col_bold=True,
      align_right_from=1, row_heights=[Inches(0.255)] * 4)
res = [("SER", "3/4 = 0.75", ACCENT), ("TCR", "1/2 = 0.50", AMBER), ("SFR", "0", RED)]
for k, (tag, v, col) in enumerate(res):
    x = Inches(6.60) + Inches(2.02) * k
    card(s, x, Inches(3.42), Inches(1.90), Inches(0.76), SOFT)
    put(tb(s, x + Inches(0.18), Inches(3.52), Inches(1.6), Inches(0.26)), tag, 10.5, True,
        col, FONT_N, first=True)
    put(tb(s, x + Inches(0.18), Inches(3.80), Inches(1.7), Inches(0.3)), v, 13, True,
        INK, FONT_N, first=True)
card(s, Inches(6.60), Inches(4.36), Inches(5.96), Inches(0.96), WHITE, line=ACCENT)
put(tb(s, Inches(6.84), Inches(4.48), Inches(5.5), Inches(0.72)),
    "SER 0.75，但 SFR 是 0\n调度是“全对才算交付”。", 13, True, RED, first=True, line=1.45)
put(tb(s, L, Inches(5.60), CW, Inches(0.8)),
    "另两个指标：RMD（可比最优慢多少）· WRT（最坏运行时间）—— 都是越低越好。", 13, False,
    GRAY, first=True, line=1.4)

# =====================================================================
# 15 18 个指标
# =====================================================================
s = ns("METRICS · 全景", "论文其实有 18 个指标，分四类")
rows = [["类别", "用途", "指标"],
        ["① 模型评测", "给模型打分", "SER · TCR · SFR · RMD · WRT"],
        ["② 数据集质量", "证明数据可信", "FINE · ESA · ICC · 人工五维"],
        ["③ 数据集难度", "说明数据多难", "EmbSim · Steps · Workload · Max Load · Overlap %"],
        ["④ 错误归因", "诊断错在哪", "四级匹配率 · 六类错误计数"]]
table(s, L, Inches(1.90), CW, Inches(2.16), rows,
      [Inches(2.40), Inches(2.30), Inches(7.08)], fs=12, first_col_bold=True,
      align_right_from=99, row_heights=[Inches(0.34)] + [Inches(0.455)] * 4)
put(tb(s, L, Inches(4.36), CW, Inches(0.6)),
    "只有第 ① 类用来比模型；其余三类是“验收数据”和“错题分析”。", 15, True, INK,
    first=True, line=1.4)
put(tb(s, L, Inches(5.16), CW, Inches(0.7)),
    "六类错误：步骤缺失 · 机器错配 · 时长不足 · 机器冲突 · 依赖违反 · 前序步骤失败",
    12, False, GRAY, first=True, line=1.4)

# =====================================================================
# 16 RQ1
# =====================================================================
s = ns("RQ1", "九个模型，全都做不出可行方案")
rows = [["模型", "类型", "SER", "TCR", "SFR", "#10 SFR"],
        ["Gemini-2.5-Pro", "推理 · 闭源", "0.634", "0.490", "0.325", "0.175"],
        ["o4-mini", "推理 · 闭源", "0.614", "0.495", "0.325", "0.125"],
        ["DeepSeek-R1", "推理 · 开源", "0.612", "0.455", "0.250", "0.050"],
        ["Gemini-2.5-Flash", "非推理 · 闭源", "0.547", "0.410", "0.200", "0.075"],
        ["GPT-4.1", "非推理 · 闭源", "0.422", "0.315", "0.050", "0.025"],
        ["Qwen3-thinking", "推理 · 开源", "0.279", "0.195", "0.000", "0.000"],
        ["Qwen3-nothinking", "非推理 · 开源", "0.298", "0.215", "0.000", "0.000"]]
table(s, L, Inches(1.84), Inches(7.3), Inches(2.62), rows,
      [Inches(2.02), Inches(1.66), Inches(0.82), Inches(0.82), Inches(0.84), Inches(1.14)],
      fs=11, first_col_bold=True, align_right_from=2, row_heights=[Inches(0.34)] * 8)
cap(s, L, Inches(4.52), Inches(7.3), "Table 2 | #Task=5（左四列）与 #Task=10（右一列）")
for k, (num, lab, col) in enumerate([("≤ 0.325", "最好的可行率", ACCENT),
                                     ("0", "Qwen3 两个模式", RED),
                                     ("31 个点", "SER 与 SFR 的落差", AMBER)]):
    y = Inches(1.84) + Inches(1.30) * k
    big(s, Inches(8.44), y, Inches(4.1), num, lab, col, ns_=26)
put(tb(s, L, Inches(5.34), CW, Inches(0.9)),
    "端到端这条路整体走不通 —— 不是某几个模型不行。", 16, True, INK, first=True,
    line=1.4)

# =====================================================================
# 17 四级错误
# =====================================================================
s = ns("RQ2 · 失败分析", "错在哪一层？")
pic(s, "fig3_zoom.png", Inches(7.30), Inches(1.82), w=Inches(5.28))
cap(s, Inches(7.30), Inches(6.42), Inches(5.28),
    "Figure 3 | 三个模型的错误分布（方案 / 任务 / 步骤 / 约束）")
lv = [("① 方案级", "Qwen3 漏 78.7% 的任务", RED),
      ("② 任务级", "Gemini 仍缺 41.5% 步骤", AMBER),
      ("③ 步骤级", "机器错配 58.9%", AMBER),
      ("④ 约束级", "完美步骤仅 69.8%", GREEN)]
for k, (t, d, col) in enumerate(lv):
    y = Inches(1.90) + Inches(1.14) * k
    card(s, L, y, Inches(6.2), Inches(0.98), SOFT)
    rule(s, L, y, Inches(0.05), Inches(0.98), col)
    put(tb(s, L + Inches(0.26), y + Inches(0.14), Inches(2.2), Inches(0.3)), t, 13, True,
        INK, first=True)
    put(tb(s, L + Inches(0.26), y + Inches(0.52), Inches(5.6), Inches(0.32)), d, 12,
        False, GRAY, first=True)
put(tb(s, L, Inches(6.46), Inches(6.2), Inches(0.5)),
    "弱模型死在第一关，强模型输在细节。", 15, True, INK, first=True, line=1.3)

# =====================================================================
# 18 潜力分析
# =====================================================================
s = ns("RQ2 · 潜力分析", "能交出来的方案，质量其实很高")
pic(s, "ppt_fig4.png", L, Inches(2.06), w=Inches(5.50))
cap(s, L, Inches(5.52), Inches(5.50), "Figure 4 | 相对 makespan 偏差（越低越好）")
big(s, Inches(6.60), Inches(1.90), Inches(5.96), "0.085",
    "只比最优慢 8.5%，与最好的启发式规则持平", ACCENT, ns_=44)
put(tb(s, Inches(6.60), Inches(3.34), Inches(5.96), Inches(0.6)),
    "而最差的规则是 0.32 —— 说明它在动态挑规则，不是死守一条。", 12, False, GRAY,
    first=True, line=1.4)
qs = [("“We note that the RA [Robot Arm] is heavily used.”", "全局规划"),
      ("“This is a conflict! … We must fix this.”", "自我纠错")]
for k, (q, tag) in enumerate(qs):
    y = Inches(4.02) + Inches(1.24) * k
    card(s, Inches(6.60), y, Inches(5.96), Inches(1.06), WHITE, line=RULE)
    put(tb(s, Inches(6.82), y + Inches(0.14), Inches(5.5), Inches(0.42)), q, 10.5, False,
        INK, first=True, line=1.3)
    put(tb(s, Inches(6.82), y + Inches(0.66), Inches(5.5), Inches(0.28)), tag, 11, True,
        AMBER, first=True)
put(tb(s, L, Inches(6.10), Inches(5.50), Inches(0.6)),
    "这两句也印证：M0 就是机械臂。", 13, True, INK, first=True, line=1.3)

# =====================================================================
# 19 Figure 8
# =====================================================================
s = ns("RQ2 · 完整证据", "另外六个模型，同样的层级")
pic(s, "ppt_fig8.png", Inches(1.20), Inches(1.86), h=Inches(4.86))
cap(s, Inches(1.20), Inches(6.78), Inches(3.2), "Figure 8 | 其余六个模型")
put(tb(s, Inches(4.90), Inches(2.10), Inches(7.6), Inches(1.2)),
    "非推理模型输在第一关", 17, True, RED, first=True, line=1.3)
put(tb(s, Inches(4.90), Inches(2.60), Inches(7.6), Inches(0.8)),
    "Llama-4 有 62.9%、DeepSeek-V3 有 49.2% 的方案存在任务遗漏。", 12, False, GRAY,
    first=True, line=1.4)
put(tb(s, Inches(4.90), Inches(3.60), Inches(7.6), Inches(1.2)),
    "微观都卡在机器错配", 17, True, AMBER, first=True, line=1.3)
put(tb(s, Inches(4.90), Inches(4.10), Inches(7.6), Inches(0.8)),
    "Llama-4 68.0%、DeepSeek-V3 63.5%、Gemini-Flash 62.0%。", 12, False, GRAY,
    first=True, line=1.4)
put(tb(s, Inches(4.90), Inches(5.10), Inches(7.6), Inches(0.9)),
    "Figure 3 用三个模型举例，Figure 8 用另外六个复现 —— 不是挑样本。", 14, True, INK,
    first=True, line=1.4)

# =====================================================================
# 20 MANS
# =====================================================================
s = ns("RQ3", "MANS：四个各管一件事的智能体")
pic(s, "ppt_fig5.png", L, Inches(1.86), w=Inches(5.72))
cap(s, L, Inches(5.96), Inches(5.72), "Figure 5 | 四个阶段（a → d）")
put(tb(s, Inches(6.72), Inches(1.86), Inches(5.86), Inches(0.4)),
    "从 LLM-as-Translator 到 LLM-as-Solver", 13, True, ACCENT, first=True)
put(tb(s, Inches(6.72), Inches(2.32), Inches(5.86), Inches(0.8)),
    "旧范式把 LLM 当翻译器，生成的代码一错就全崩；MANS 把算法推理放回模型内部。", 11.5,
    False, GRAY, first=True, line=1.45)
ag = [("Seeker", "只认任务"), ("Weaver", "只拆步骤"),
      ("Verifier", "只做校验"), ("Architect", "只排程")]
for k, (name, w2) in enumerate(ag):
    y = Inches(3.46) + Inches(0.66) * k
    card(s, Inches(6.72), y, Inches(5.86), Inches(0.54), SOFT)
    put(tb(s, Inches(6.96), y + Inches(0.12), Inches(1.7), Inches(0.3)), name, 12, True,
        INK, FONT_N, first=True)
    put(tb(s, Inches(8.72), y + Inches(0.12), Inches(3.6), Inches(0.3)), w2, 11.5, False,
        GRAY, first=True)
put(tb(s, Inches(6.72), Inches(6.28), Inches(5.86), Inches(0.5)),
    "把任务切窄，每个 agent 只想一件事。", 14, True, INK, first=True, line=1.3)

# =====================================================================
# 21 prompt
# =====================================================================
s = ns("RQ3 · 提示词", "提示词里，每个 agent 只做一件事")
rows = [["agent", "提示词原文（节选）"],
        ["Seeker", "“Your sole task is to … identify the complete and accurate set of all tasks.”"],
        ["Weaver", "“… extract its sequence of steps … the specific machine … and its processing duration.”"],
        ["Verifier", "“Verify Attribute Accuracy … Correct any discrepancies.”"],
        ["Architect", "“… create an optimal, conflict-free schedule.”"]]
table(s, L, Inches(1.86), CW, Inches(2.30), rows,
      [Inches(1.60), Inches(10.18)], fs=11, first_col_bold=True,
      align_right_from=99, row_heights=[Inches(0.34)] + [Inches(0.49)] * 4)
put(tb(s, L, Inches(4.44), CW, Inches(0.4)),
    "Architect 的“策略指南” —— 这三条是全文的闭环", 13, True, ACCENT, first=True)
stg = [("Identify Bottlenecks", "先找最拥挤的机器"),
       ("Think Ahead", "别做纯贪心"),
       ("Allow Strategic Idling", "允许策略性空转")]
for k, (t, d) in enumerate(stg):
    x = L + (Inches(3.86) + Inches(0.22)) * k
    card(s, x, Inches(4.86), Inches(3.86), Inches(0.92), SOFT)
    put(tb(s, x + Inches(0.24), Inches(5.00), Inches(3.4), Inches(0.3)), t, 11.5, True,
        INK, FONT_N, first=True)
    put(tb(s, x + Inches(0.24), Inches(5.34), Inches(3.4), Inches(0.3)), d, 11, False,
        GRAY, first=True)
put(tb(s, L, Inches(6.02), CW, Inches(0.6)),
    "它们逐条来自 Figure 4 里模型自己冒出来的推理 —— 观察到策略，写成提示词。", 14, True,
    INK, first=True, line=1.4)

# =====================================================================
# 22 四 agent ↔ 四级错误
# =====================================================================
s = ns("RQ3 · 设计", "四个 agent，正好对着四级错误")
rows = [["错误层级（RQ2）", "对应 agent", "它在修什么"],
        ["① 方案级：任务认全没", "Seeker", "identify the complete set of all tasks"],
        ["② 任务级：步骤全不全", "Weaver", "extract its sequence of steps"],
        ["③ 步骤级：机器对不对", "Verifier", "confirm machine and duration are accurate"],
        ["④ 约束级：抢不抢机器", "Architect", "create an optimal, conflict-free schedule"]]
table(s, L, Inches(1.88), CW, Inches(2.10), rows,
      [Inches(3.40), Inches(1.74), Inches(6.64)], fs=11.5, first_col_bold=True,
      align_right_from=99, row_heights=[Inches(0.34)] + [Inches(0.44)] * 4)
put(tb(s, L, Inches(4.24), CW, Inches(0.9)),
    "所以它不是四个模块，是四个补丁：删掉哪个，对应的那一层错误就复活。", 15, True, INK,
    first=True, line=1.4)
put(tb(s, L, Inches(5.08), CW, Inches(0.9)),
    "删掉 Seeker 最致命 —— 10 任务时可行率从 27.5% 掉到 7.5%。", 15, True, RED,
    first=True, line=1.4)

# =====================================================================
# 23 结果
# =====================================================================
s = ns("RQ3 · 结果", "赢了多数格子，但赢在“更快更稳”")
rows = [["方法", "#5 SER", "#10 SER", "#10 SFR"],
        ["CoE + MOPNR", "0.691", "0.587", "0.225"],
        ["OptiMUS + OR-Tools", "0.602", "0.535", "0.225"],
        ["MANS（本文）", "0.702", "0.682", "0.275"]]
table(s, L, Inches(1.88), Inches(6.4), Inches(1.30), rows,
      [Inches(2.60), Inches(1.28), Inches(1.26), Inches(1.26)], fs=11,
      first_col_bold=True, align_right_from=1, row_heights=[Inches(0.325)] * 4)
cap(s, L, Inches(3.24), Inches(6.4), "Table 3 | 完整性与可行性")
rows2 = [["方法", "WRT 秒", "RMD"],
         ["CoE + OR-Tools", "154.44", "0.023"],
         ["OptiMUS + OR-Tools", "133.70", "0.022"],
         ["MANS（本文）", "79.59", "0.085"]]
table(s, L, Inches(3.56), Inches(6.4), Inches(1.30), rows2,
      [Inches(2.76), Inches(1.86), Inches(1.78)], fs=11, first_col_bold=True,
      align_right_from=1, row_heights=[Inches(0.325)] * 4)
cap(s, L, Inches(4.92), Inches(6.4), "Table 4 | 运行时间与调度质量")
vd = [("赢", "SER 4/6 档、TCR 5/6 档领先", GREEN),
      ("快", "79.59 秒，快 35–48%", ACCENT),
      ("输", "质量 0.085 vs 0.022", RED)]
for k, (tag, txt, col) in enumerate(vd):
    y = Inches(1.88) + Inches(1.34) * k
    card(s, Inches(7.60), y, Inches(4.96), Inches(1.16), SOFT)
    put(tb(s, Inches(7.84), y + Inches(0.24), Inches(0.7), Inches(0.5)), tag, 24, True,
        col, first=True)
    put(tb(s, Inches(8.66), y + Inches(0.38), Inches(3.7), Inches(0.4)), txt, 12, False,
        GRAY, first=True)
put(tb(s, L, Inches(5.62), Inches(6.4), Inches(0.8)),
    "所以作者只说 comparable + more stable，不说 better。", 14, True, INK, first=True,
    line=1.4)

# =====================================================================
# 24 Table 11
# =====================================================================
s = ns("RQ3 · 稳健性", "换个骨干，收益差 5.6 倍")
rows = [["骨干", "#Task=5", "#Task=7", "#Task=10"],
        ["Qwen3-nothinking", "0.346", "0.234", "0.121"],
        ["DeepSeek-V3", "0.597", "0.400", "0.216"],
        ["GPT-4.1", "0.638", "0.596", "0.352"],
        ["Gemini-2.5-Flash", "0.702", "0.608", "0.682"]]
table(s, L, Inches(1.90), Inches(7.6), Inches(1.62), rows,
      [Inches(3.10), Inches(1.52), Inches(1.50), Inches(1.48)], fs=11.5,
      first_col_bold=True, align_right_from=1, row_heights=[Inches(0.325)] * 5)
cap(s, L, Inches(3.60), Inches(7.6), "Table 11 | 同一框架换骨干的 SER")
big(s, Inches(8.80), Inches(1.90), Inches(3.76), "5.6×",
    "Qwen3 0.121 vs Gemini 0.682（#Task=10）", RED, ns_=40)
put(tb(s, L, Inches(4.40), CW, Inches(0.9)),
    "四个 agent 放大的是底模已有的能力，不是凭空创造能力。", 16, True, INK, first=True,
    line=1.4)
put(tb(s, L, Inches(5.24), CW, Inches(0.7)),
    "这也解释了为什么正文只报一个骨干 —— 换骨干的结论会更保守。", 12.5, False, GRAY,
    first=True, line=1.4)

# =====================================================================
# 25 输出格式
# =====================================================================
s = ns("EVAL · 输出格式", "模型交出的是一张“排班表”，5 个字段")
card(s, L, Inches(1.90), Inches(6.6), Inches(1.50), RGBColor(0xF7, 0xF9, 0xFC), line=RULE)
tf = tb(s, L + Inches(0.28), Inches(2.04), Inches(6.1), Inches(1.28))
for i, line in enumerate(['[ {"task_id": 0, "step_id": 1,',
                          '   "machine": "robot_arm",',
                          '   "start_time": 0, "end_time": 2}, … ]']):
    put(tf, line, 11, False, INK, FONT_N, first=(i == 0), line=1.5)
rows = [["字段", "含义"],
        ["task_id / step_id", "第几个任务 / 第几步"],
        ["machine", "机器名（字符串）"],
        ["start_time / end_time", "起止时间点"]]
table(s, L, Inches(3.60), Inches(6.6), Inches(1.28), rows,
      [Inches(2.70), Inches(3.90)], fs=11.5, first_col_bold=True,
      align_right_from=99, row_heights=[Inches(0.32)] * 4)
put(tb(s, L, Inches(5.10), Inches(6.6), Inches(0.7)),
    "模型不给 duration，只给起止时间 —— 时长由评测器算。", 12.5, False, GRAY,
    first=True, line=1.4)
put(tb(s, Inches(7.84), Inches(1.90), Inches(4.72), Inches(0.3)), "判分四步", 12, True,
    ACCENT, first=True)
sp = [("① 对号入座", ACCENT), ("② 逐格判错", AMBER), ("③ 级联标记", RED),
      ("④ 汇总指标", GREEN)]
for k, (t, col) in enumerate(sp):
    y = Inches(2.24) + Inches(0.86) * k
    card(s, Inches(7.84), y, Inches(4.72), Inches(0.70), SOFT)
    rule(s, Inches(7.84), y, Inches(0.045), Inches(0.70), col)
    put(tb(s, Inches(8.08), y + Inches(0.20), Inches(4.3), Inches(0.32)), t, 12.5, True,
        INK, first=True)
put(tb(s, L, Inches(6.02), CW, Inches(0.6)),
    "“输出什么”决定了“指标怎么算”—— 这也是最容易被问的一点。", 14, True, INK,
    first=True, line=1.4)

# =====================================================================
# 26 评测实现
# =====================================================================
s = ns("EVAL · 实现", "读评测代码，发现四处论文没写的细节")
items = [("① SER 是“微平均”", "代码是「总对步数 ÷ 总步数」，论文公式是宏平均。", ACCENT),
         ("② SFR 就是 TCR == 1.0", "所有任务全对才记 1，没有部分分。", AMBER),
         ("③ 一步错 → 后面全记失败", "第六类错误 previous_step_failed。", RED),
         ("④ 对齐靠“时长指纹”", "用匈牙利算法按时长序列配对，一个时长写错可能配错任务。", GREEN)]
for k, (t, d, col) in enumerate(items):
    y = Inches(1.88) + Inches(1.14) * k
    card(s, L, y, CW, Inches(1.00), SOFT)
    rule(s, L, y, Inches(0.05), Inches(1.00), col)
    put(tb(s, L + Inches(0.28), y + Inches(0.18), Inches(4.0), Inches(0.34)), t, 13, True,
        INK, first=True)
    put(tb(s, L + Inches(4.40), y + Inches(0.22), Inches(7.1), Inches(0.62)), d, 11.5,
        False, GRAY, first=True, line=1.4)
put(tb(s, L, Inches(6.48), CW, Inches(0.5)),
    "不影响主要结论，但决定了那些数字的确切含义。", 14, True, INK, first=True, line=1.3)

# =====================================================================
# 27 局限
# =====================================================================
s = ns("LIMITATIONS", "三条局限，恰好对应三块贡献")
rows = [["贡献", "局限"],
        ["① 数据集：240 个实例", "半合成 —— 语言是从任务图反向生成的"],
        ["② 任务定义：NL ⇒ Schedule", "规模偏小 —— 5–10 任务、时长确定、无并行分支"],
        ["③ 评测范式：5 个指标", "未标准化 —— 未覆盖鲁棒性与公平性"]]
table(s, L, Inches(1.90), CW, Inches(1.72), rows,
      [Inches(3.70), Inches(8.08)], fs=12, first_col_bold=True,
      align_right_from=99, row_heights=[Inches(0.34)] + [Inches(0.46)] * 3)
put(tb(s, L, Inches(3.90), CW, Inches(0.9)),
    "另外几处可追问：SER 口径不一致 · 对齐靠时长指纹 · 每格仅 10 个实例 · 两个基线被削弱。",
    13, False, GRAY, first=True, line=1.5)
put(tb(s, L, Inches(4.86), CW, Inches(0.6)),
    "作者对自己每块贡献的天花板都很清楚。", 15, True, INK, first=True, line=1.3)

# =====================================================================
# 28 课程关联
# =====================================================================
s = ns("TAKEAWAY", "它和这门课的关系")
put(tb(s, L, Inches(1.86), Inches(5.8), Inches(0.3)), "方法可以直接迁移", 12, True,
    ACCENT, first=True)
rows = [["MANS 四步", "舆情分析"],
        ["Seeker 认全任务", "抽全议题，不漏"],
        ["Weaver 抽要素", "抽事件要素与阶段"],
        ["Verifier 校验", "事实核查"],
        ["Architect 排程", "出研判报告"]]
table(s, L, Inches(2.18), Inches(5.8), Inches(1.64), rows,
      [Inches(2.76), Inches(3.04)], fs=11, first_col_bold=True,
      align_right_from=99, row_heights=[Inches(0.30)] + [Inches(0.335)] * 4)
put(tb(s, L, Inches(4.10), Inches(5.8), Inches(0.9)),
    "报告 95% 的要素都对，只要有 1 处硬伤，整份就不能用。", 13, True, INK, first=True,
    line=1.4)
put(tb(s, Inches(7.06), Inches(1.86), Inches(5.5), Inches(0.3)),
    "社交网络本身就在做调度", 12, True, ACCENT, first=True)
apps = ["内容审核排班", "爬虫与采集资源分配", "推送与投放排期", "舆情应急响应"]
for k, t in enumerate(apps):
    y = Inches(2.18) + Inches(0.52) * k
    tf = tb(s, Inches(7.06), y, Inches(5.5), Inches(0.4))
    p = tf.paragraphs[0]; p.line_spacing = 1.3
    sr(p.add_run(), 13, False, ACCENT).text = "·  "
    sr(p.add_run(), 13, False, GRAY).text = t
put(tb(s, L, Inches(5.34), CW, Inches(0.9)),
    "模型“看得懂、想得远、落不了地”同样存在于舆情任务 —— 一到“谁、何时、说了什么”，就开始出错。",
    14, True, INK, first=True, line=1.45)
put(tb(s, L, Inches(6.34), CW, Inches(0.5)),
    "所以解法不是换更大的模型，而是把落地拆成可校验的步骤。", 15, True, ACCENT,
    first=True, line=1.3)

# =====================================================================
# 29 结论
# =====================================================================
s = ns("SUMMARY", "它给了什么，又留了什么")
half = [("给了什么", ACCENT, ["新的任务定义与评测框架", "可复现的 240 实例 benchmark", "一个够用的四 agent 解法"]),
        ("留了什么", RED, ["数据半合成、规模偏小", "方法不全面领先", "指标口径有瑕疵"])]
for k, (t, col, lines) in enumerate(half):
    x = L + Inches(6.0) * k
    card(s, x, Inches(1.90), Inches(5.78), Inches(2.30), SOFT)
    rule(s, x, Inches(1.90), Inches(5.78), Inches(0.05), col)
    put(tb(s, x + Inches(0.28), Inches(2.08), Inches(5.2), Inches(0.3)), t, 15, True, col,
        first=True)
    tf = tb(s, x + Inches(0.28), Inches(2.56), Inches(5.2), Inches(1.5))
    for i, line in enumerate(lines):
        put(tf, "·  " + line, 12.5, False, GRAY, first=(i == 0), line=1.6,
            sb=0 if i == 0 else 6)
put(tb(s, L, Inches(4.52), CW, Inches(0.9)),
    "一句话评价：这是一篇“评测框架做得比方法更好”的论文。", 17, True, INK, first=True,
    line=1.4)
put(tb(s, L, Inches(5.36), CW, Inches(0.6)),
    "六个数：135 任务图 · 13 车间 · 240 实例 · 9 个模型 · 6 个基线 · 79.59 秒 / 0.085",
    12.5, False, GRAY, first=True, line=1.4)

# =====================================================================
# 30 备用
# =====================================================================
s = ns("BACKUP", "Table 2 全表：九个模型 × 六种规模的 SFR")
sfr = [["模型", "#5", "#6", "#7", "#8", "#9", "#10"],
       ["Qwen3-nothinking", "0", "0", "0", "0", "0", "0"],
       ["Llama4-Maverick", "0.025", "0", "0", "0", "0", "0.025"],
       ["DeepSeek-V3", "0.050", "0.050", "0.025", "0", "0", "0"],
       ["GPT-4.1", "0.050", "0.225", "0.050", "0.025", "0", "0.025"],
       ["Gemini-2.5-Flash", "0.200", "0.100", "0.100", "0.125", "0.050", "0.075"],
       ["Qwen3-thinking", "0", "0", "0", "0", "0", "0"],
       ["DeepSeek-R1", "0.250", "0.175", "0.125", "0.125", "0.100", "0.050"],
       ["o4-mini", "0.325", "0.250", "0.225", "0.250", "0.200", "0.125"],
       ["Gemini-2.5-Pro", "0.325", "0.275", "0.250", "0.200", "0.200", "0.175"]]
table(s, L, Inches(1.86), Inches(8.4), Inches(3.60), sfr,
      [Inches(2.66), Inches(0.96), Inches(0.96), Inches(0.96), Inches(0.96), Inches(0.95), Inches(0.95)],
      fs=12, first_col_bold=True, align_right_from=1, row_heights=[Inches(0.36)] + [Inches(0.36)] * 9)
cap(s, L, Inches(5.54), Inches(8.4), "Table 2 | 数值为 SFR")
put(tb(s, Inches(9.50), Inches(1.86), Inches(3.06), Inches(3.6)),
    "54 个格子里 39 个低于 0.15\n\nQwen3 两个模式 12 格全为 0\n\n达到 0.3 的只有 2 个",
    12.5, False, GRAY, first=True, line=1.5)

prs.save(OUT)
print("saved:", OUT, "slides:", len(prs.slides._sldIdLst))
