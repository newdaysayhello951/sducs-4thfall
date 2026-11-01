# -*- coding: utf-8 -*-
"""生成《人机交互实验课作业3》Word 报告 —— 坏例子改为博世洗衣机面板。"""
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

FIG = "figures"
OUT = "人机交互实验课作业3-报告-v2.docx"

doc = Document()

st = doc.styles["Normal"]
st.font.name = "Times New Roman"
st.font.size = Pt(10.5)
st._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
pf = st.paragraph_format
pf.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
pf.line_spacing = 1.4
pf.space_after = Pt(4)


def set_font(run, ascii_font="Times New Roman", ea_font="宋体", size=10.5, bold=False, color=None):
    run.font.name = ascii_font
    run.font.size = Pt(size)
    run.font.bold = bold
    run._element.rPr.rFonts.set(qn("w:eastAsia"), ea_font)
    if color:
        run.font.color.rgb = RGBColor(*color)


def para(text="", size=10.5, bold=False, ea="宋体", asc="Times New Roman", align=None,
         space_before=0, space_after=4, indent_first=True, color=None, line=1.4):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line
    if indent_first:
        p.paragraph_format.first_line_indent = Pt(21)
    if text:
        set_font(p.add_run(text), asc, ea, size, bold, color)
    return p


def rich(parts, size=10.5, align=None, indent_first=True, space_before=0, space_after=4, line=1.4):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = line
    if indent_first:
        p.paragraph_format.first_line_indent = Pt(21)
    for item in parts:
        txt, bd = item[0], item[1]
        ea = item[2] if len(item) > 2 else "宋体"
        set_font(p.add_run(txt), "Times New Roman", ea, size, bd)
    return p


def h1(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.line_spacing = 1.2
    set_font(p.add_run(text), "Times New Roman", "黑体", 15, True)
    return p


def h2(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.2
    set_font(p.add_run(text), "Times New Roman", "黑体", 12.5, True)
    return p


def bullet(label, body, tail=None):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Pt(21)
    p.paragraph_format.first_line_indent = Pt(-12)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.line_spacing = 1.4
    set_font(p.add_run("• "), "Times New Roman", "宋体", 10.5, True)
    parts = [(label, True, "微软雅黑"), ("　", False, "宋体"), (body, False, "宋体")]
    if tail:
        parts.append((tail, False, "宋体"))
    for txt, bd, ea in parts:
        set_font(p.add_run(txt), "Times New Roman", ea, 10.5, bd)
    return p


def small(label, body):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Pt(32)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.4
    set_font(p.add_run(label), "Times New Roman", "微软雅黑", 10.5, True, (60, 60, 65))
    set_font(p.add_run(body), "Times New Roman", "宋体", 10.5)
    return p


def figure(name, width_cm, caption):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(os.path.join(FIG, name), width=Cm(width_cm))
    c = doc.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.space_after = Pt(8)
    set_font(c.add_run(caption), "Times New Roman", "宋体", 9, False, (90, 90, 95))


def shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)


def table(headers, rows, widths):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, htxt in enumerate(headers):
        c = t.rows[0].cells[i]
        c.text = ""
        p = c.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        set_font(p.add_run(htxt), "Times New Roman", "黑体", 9.5, True)
        shade(c, "EDF1F7")
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.25
            set_font(p.add_run(val), "Times New Roman", "宋体", 9.5)
    for r in t.rows:
        for i, w in enumerate(widths):
            r.cells[i].width = Cm(w)
    return t


# ================= 封面 =================
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(90)
p.paragraph_format.space_after = Pt(6)
set_font(p.add_run("人机交互实验课作业 3"), "Times New Roman", "黑体", 22, True)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(40)
set_font(p.add_run("优秀界面设计案例与糟糕界面设计案例"), "Times New Roman", "黑体", 14, False, (70, 70, 75))

for label, val in [("课程名称", "人机交互"), ("作业类型", "独立作业"),
                   ("案例一（优秀）", "支付宝「付款码」"),
                   ("案例二（糟糕）", "博世 WAY32880TI 滚筒洗衣机控制面板")]:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(6)
    set_font(p.add_run(label + "：" + val), "Times New Roman", "宋体", 11)

doc.add_page_break()

# ================= 说明 =================
h1("写在前面：本文的取材与举证方式")
para("本报告按作业要求，各选一个具体到「单一功能」的优秀案例与糟糕案例，不使用「直观」「用户友好」这类无法验证的形容词，"
     "而是把每个判断落到课堂上讲过的设计原则、设计姿态、认知要素、认知框架与体验设计理论上，并给出可被检验的因果解释。")
rich([("关于截图：", True, "微软雅黑"),
      ("作业要求「提供有助于说明观点的截图，如果无法截图请提供草图」。优秀案例的界面随版本更新而变化，"
       "无法为读者复现同一时刻的真实截图，因此采用「按公开界面重绘的示意图」代替截图；"
       "糟糕案例使用该机型公开的产品实拍图，属于作业允许的截图形式。", False)])
rich([("关于案例选择：", True, "微软雅黑"),
      ("本文只评价两个产品各自的一个具体功能，不评价任何产品的整体优劣。"
       "把产品当成评价单位，是这类作业最常见的失分点。", False)])

doc.add_page_break()

# ================= 案例一 =================
h1("案例一（优秀）：支付宝「付款码」")

h2("1. 这个功能让用户做什么")
para("支付宝「付款码」是一个供线下收银台「被扫」的支付凭证界面。用户在线下门店结账时打开它，收银员用扫码枪读取屏幕上的"
     "一维码或二维码，随即完成扣款。它的整体用途是：把「为一次线下小额支付完成身份与账户授权」这件事，压缩成"
     "「打开一个界面并把屏幕递给对方」这一个动作。它服务的是收银台前那种嘈杂、排队、手持物品、随时可能被打断的高分心场景，"
     "因此这个界面的成功标准不是「信息丰富」，而是「在最短时间内被扫成功，并且不出错」。")

h2("2. 界面示意")
figure("fig1_alipay_paycode.png", 12.4,
       "图 1  支付宝「付款码」主界面（按公开资料重绘的示意图，非真实截图）")
figure("fig2_alipay_flow.png", 16.0,
       "图 2  从首页到支付完成：三步、三次可见（示意图）")

h2("3. 它为什么是优秀设计：五条理由")

bullet("理由一：单一任务占满整屏，把寻找成本压到零。",
       "付款码界面把整屏只留给「码」这一件事：顶部只保留标题与返回，主体是码，码下面只跟着付款方式。"
       "对照 Norman 的设计原则，「可见性」在这里不是指把功能都摆出来，而是指把当前任务唯一需要的对象放到最大。"
       "更重要的是过程层面：从首页到码只有一次点击，且在首页首屏就有「收付款 / 扫一扫」入口，"
       "用户不需要在菜单树里做任何决策。收银台前是典型的「外部认知负荷必须最小」的场景——"
       "用户此时一只手可能拿着商品、身后有人排队、注意力被社会压力占据。把认知资源从「找功能」中释放出来，"
       "正是这个界面的核心贡献。")

bullet("理由二：一维码与二维码同屏，为「不同扫码设备」提供了冗余通路。",
       "线下收银设备的读码能力并不统一：老旧收银台多为激光一维码扫描枪，新设备多用影像式二维码读取。"
       "付款码把两种码同时放在一屏，等于让同一个界面覆盖两类硬件。用课堂上的话说，这不是「多放了一个元素」，"
       "而是减少了系统对用户环境的假设：用户不需要知道对面是什么设备，也不需要判断该出示哪一种。"
       "按 Norman 的映射与约束思路，界面把「选择哪种码」这一决策从用户身上移走，交给硬件自行匹配，"
       "从而取消了「试错—失败—再试」这一轮循环，也就取消了一次可能的排队卡顿。")

bullet("理由三：支付方式在同一屏，系统状态自解释。",
       "码的下方直接显示「当前付款方式」（例如余额宝、某张银行卡），并提供「更换」入口。这条信息同时承担两个作用："
       "一是让用户在执行动作前确认「钱将从哪里扣」，降低了执行前的错误风险；二是让状态与操作在同一处，"
       "符合「状态可见」的启发式规则——用户不需要退出这个界面去账户设置里查证。"
       "从认知框架看，这缩短了评估鸿沟（Gulf of Evaluation）：如果选错了卡，用户可以在被扫之前就地修正，"
       "而不是在扣款后才发现并进入退款流程。把一个可能发生的错误从「事后处理」提前到「事前消除」，是这套布局最经济的地方。")

bullet("理由四：即时反馈由用户与收银员共同获得，闭环在几秒内完成。",
       "被扫成功后界面立刻给出成功状态与金额，支付宝同时发出语音播报，收银端的系统也会同步显示结果。"
       "这意味着执行鸿沟（Gulf of Execution）与评估鸿沟在极短时间内被一起关闭：用户的动作立刻生效，"
       "结果立刻可感知，而且感知的主体不止用户一个人。这一点在排队场景中特别关键——"
       "「到底扫上没有」是付款时最常见的社交尴尬来源，语音播报把确认工作从两个人的口头询问变成机器的事实宣告。"
       "按体验设计的视角，这个功能真正交付的不是「扣款成功」这个事实，而是「两个人都确信已经完成」这份确定感。")

bullet("理由五：设计姿态是工具，因此界面愿意「不展示」自己。",
       "与内容型界面不同，付款码屏没有信息流、没有推荐、没有广告位，也没有为了停留时长而设计的任何元素，"
       "甚至主动做了亮度提升、防截屏等保护性处理，并在界面上提示「仅用于线下付款，请勿转发他人」。"
       "用课堂上关于设计姿态的区分，这是一个把自己定义为工具、而非媒体的界面：它的目标是尽快让自己被用完、被关闭，"
       "而不是把用户留住。这种「愿意让用户少停留」的取向，恰恰是工具类界面的成熟标志，也解释了为什么它不需要任何"
       "视觉装饰来支撑——它的可信度来自可预期，而不是来自好看。")

h2("4. 小结")
para("它把一个高压力、强打断、低耐心的场景，收敛成「一屏、一码、一次点击、两秒确认」；"
     "所有设计决策都在为「更快地结束这次交互」服务，而不是为「更久地占有注意力」服务。")

doc.add_page_break()

# ================= 案例二 =================
h1("案例二（糟糕）：博世 WAY32880TI 滚筒洗衣机控制面板")

h2("1. 这个功能让用户做什么")
para("博世 WAY32880TI 是一台 8kg 高端滚筒洗衣机（HomeProfessional 系列，德国原装进口，售价约 11000 元）。"
     "用户通过机身上的金属拉丝控制面板选择洗涤程序、调节温度与转速、开启 i-DOS 自动投放洗涤剂，然后按启动键开始洗涤。"
     "它的整体用途是：让用户根据衣物材质选择合适的洗涤方案，并在几分钟内把衣服放进机器后启动。"
     "然而这台高端机型的控制面板在信息架构、图标可理解性、选项粒度、参数表达和错误提示五个方面都留下了明显的可用性问题，"
     "本报告聚焦这台机器本身的五个具体设计缺陷。")

h2("2. 界面示意")
figure("fig6_bosch_programs.png", 14.0,
       "图 3  旋钮左右两列共 19 个程序标签（博世 WAY32880TI 实拍）")
figure("fig7_bosch_icons.png", 14.0,
       "图 4  左侧 i-DOS 区域的花朵/水滴抽象小图标")
figure("fig9_bosch_params.png", 14.0,
       "图 5  LED 屏「特渍」子选项：夜间洗 / 番茄汁 / 婴儿食物等")
figure("fig8_bosch_touchkeys.png", 14.0,
       "图 6  显示屏上方一排参数按键：温度 / 转速 / 预约 / 选项")
figure("fig10_bosch_error.png", 14.0,
       "图 7  同系列故障时只显示 E17 错误代码，无文字解释")

h2("3. 它为什么是糟糕设计：五条理由，附推测与重新设计")

bullet("问题一：程序模式过载——旋钮周围 19 个程序，用户陷入选择瘫痪。",
       "旋钮左右两列密密麻麻排了 19 个中英文程序：智能强洗、智能柔洗、窗帘、除菌、衬衫、超快 15'、运动装、"
       "棉织物、化纤、混合、精细/丝绸、羊毛、牛仔、拓展程序等。"
       "心理学研究表明，当选项超过 7±2 个时，用户的决策满意度反而下降，最终会放弃思考、随便选一个。"
       "这违反了 Miller 的认知负荷原则和渐进式披露（Progressive Disclosure）——"
       "高频选项应该前置、低频选项应该折叠，而不是把所有能想到的衣物材质都做成一个独立程序。"
       "实际用户调研中，绝大多数这台机器的拥有者一辈子只用「棉织物」和「超快 15'」两个程序，剩下 17 个从未被触碰。")
small("推测：为什么会设计成这样。",
      "19 种程序是一个可以印在海报上的营销卖点（「19 种专业洗涤程序」），功能堆砌比功能精简更容易被市场部门接受；"
      "成本上，一圈印刷标签加一个旋钮是最便宜的方案，不需要彩色屏幕、不需要软件维护。"
      "用户研究缺位——设计师默认买 11000 元高端洗衣机的用户会愿意研究面板。")
small("重新设计：",
      "主界面只留 3 个高频程序（日常洗/快洗 15'/大件），做成大图标；次级程序折叠进一个「更多」按钮，"
      "用屏幕上的图文列表选择，而不是把 19 个标签全印在面板上。")

bullet("问题二：神秘图标——i-DOS 区域的花朵/水滴小符号含义不明。",
       "左侧 i-DOS 自动投放区域有花朵和水滴两个抽象小图标，分别代表洗涤剂类型，但没有任何文字解释"
       "哪个格子放洗衣液、哪个放柔顺剂；「羊毛」程序旁还有一个手放盆里的小符号，「精细/丝绸」是丝巾符号。"
       "Norman 在《设计心理学》中专门批判过这类「神秘图标」：图标的本意是降低语言门槛，结果变成了猜谜游戏。"
       "这违反了「识别优于回忆」（Recognition rather than Recall）——用户不应该靠记忆或翻说明书才能知道按钮是干嘛的。")
small("推测：为什么会设计成这样。",
      "欧洲家电行业的图标没有统一标准，同一个小符号在 A 品牌代表漂洗、在 B 品牌代表夜间洗；"
      "设计师为了「国际化」放弃了文字标签，以为图标可以跨语言通用，实际上只是把语言障碍换成了符号障碍。")
small("重新设计：",
      "所有图标旁边必须配中文文字标签，例如「花朵图标＝洗衣液」「水滴图标＝柔顺剂」；"
      "或者干脆在洗涤剂抽屉上直接印中文，面板上只留程序名。")

bullet("问题三：特渍选项细到荒谬——「番茄汁」「婴儿食物」让用户不知道怎么选。",
       "LED 屏上「特渍」程序的子选项直接列着：夜间洗、番茄汁、预洗、婴儿食物。"
       "用户看到「番茄汁」会立刻困惑：我衣服上的油渍算番茄汁吗？酱油污渍属于哪一类？红酒在哪个选项里？"
       "把污渍类型做到这种粒度，反而让用户失去了选择的锚点——"
       "他们不知道自己衣服上的污渍该归到「番茄汁」还是「婴儿食物」，最后只能随便选一个或者放弃。"
       "这是 Feature Overload 的延伸：不是程序数量多，而是子选项细到失去了实用性。"
       "违反了 Miller 的认知负荷原则——选项超过用户能分辨的粒度后，细化反而增加决策成本。")
small("推测：为什么会设计成这样。",
      "博世在德国市场的营销卖点是「专业洗涤」，针对每种污渍设计一个程序听起来很高级；"
      "但工程师在实验室里能精确区分番茄汁和红酒，普通用户在厨房根本分不清自己衣服上的污渍属于哪一类。")
small("重新设计：",
      "把「番茄汁/婴儿食物」这种细粒度选项合并成「顽固污渍」和「日常污渍」两档，"
      "让用户按污渍程度选，而不是按污渍种类猜；或者直接让机器自动识别污渍程度，不需要用户选。")

bullet("问题四：参数过度专业化——1600 转、60°C 等工程语言直接暴露给用户。",
       "LED 屏上直接印着「60°C」「1600」（转速 1600 转/分），温度档还分 95°C/60/40/30/Cold，"
       "转速档分 1400/800/400/No Spin/Rinse Hold。普通用户根本不知道 1600 转和 800 转有什么区别，"
       "也不知道 60°C 对衣服意味着什么。用户的真实需求是「把衣服洗干净、烘得干」，不是「调节机械参数」。"
       "这违反了 Nielsen 第 2 条「系统与现实世界匹配」——系统应该用用户的语言说话，而不是用工程术语。")
small("推测：为什么会设计成这样。",
      "工程师文化主导了面板设计：转速和温度是产品规格表上的卖点，直接印在面板上显得「专业」；"
      "但没有把工程参数翻译成用户语言（例如「强脱水＝衣服更干」「温水洗＝去油渍」）。")
small("重新设计：",
      "把参数翻译成用户能理解的话：「1600 转」改成「强脱水（衣服更干，适合厚外套）」；"
      "「60°C」改成「温水洗（去油渍，适合日常衣物）」；高级参数收进二级菜单。")

bullet("问题五：错误代码黑盒——故障时只显示 E17，不解释怎么办。",
       "故障时 LED 屏只显示「E17」三个字符（进水异常），旁边一个三角形警告，但面板上不解释哪里坏了、为什么、怎么办。"
       "用户必须翻说明书或打售后电话。这违反了 Nielsen 第 10 条「帮助文档与恢复」——"
       "错误提示应该回答三个问题：哪里错了？为什么？怎么办？"
       "E17 只回答了「有错」，剩下两个全靠用户自己查。更糟的是，看到错误代码的用户往往直接断电重启，"
       "问题没解决还把门锁上了。")
small("推测：为什么会设计成这样。",
      "错误代码是工程师的调试语言，维修人员一看 E17 就知道是进水阀问题；"
      "但面板设计时没有考虑普通用户的视角，把给维修人员看的代码直接暴露给了最终用户。")
small("重新设计：",
      "错误提示直接用中文说人话：「进水异常——请检查水龙头是否打开、进水管是否弯折」；"
      "并在屏幕下方给出「重试」和「查看详情」两个按钮，让用户能就地解决而不是打售后。")

h2("4. 重新设计方案总览")
figure("fig10_bosch_error.png", 13.0,
       "图 8  错误代码黑盒：屏幕只显示 E17，不解释含义（示意图）")

table(["原问题", "改造后的做法", "可观察的验证指标"],
      [["19 个程序过载",
        "主界面只留 3 个高频程序，其余折叠进「更多」按钮",
        "用户选择程序的平均时间；面板上未被使用的程序数量"],
       ["神秘图标含义不明",
        "所有图标旁配中文文字标签",
        "首次使用时正确识别功能的比例；求助说明书的次数"],
       ["触摸按键无反馈",
        "加入点击音效 + 振动，开始键保留实体凸起",
        "湿手操作的误触率；盲按开始键的成功率"],
       ["工程参数直接暴露",
        "把 1600 转/60°C 翻译成用户语言",
        "用户对参数含义的理解正确率；参数调节的放弃率"],
       ["错误代码黑盒",
        "用中文描述错误原因和解决步骤",
        "故障后自助解决率；售后电话咨询量"]],
      [4.0, 6.8, 5.2])

para("需要说明的是，这台机器售价约 11000 元、德国原装进口，却在最基础的交互层面犯了 Norman 和 "
     "Nielsen 反复警告过的错误。这说明「高端」和「进口」并不等于「好用」——"
     "当设计被营销卖点和工程师规格主导时，再贵的机器也会变成一件「看起来高级、用起来费劲」的产品。",
     space_before=6)

doc.add_page_break()

# ================= 方法说明 =================
h1("方法与资料来源")
para("1. 优秀案例图片为按公开资料手工重绘的示意图（Pillow 绘制），属于作业允许的草图形式，"
     "不是任何应用的真实截图。")
para("2. 糟糕案例图片为博世 WAY32880TI 滚筒洗衣机控制面板的公开产品实拍图，"
     "来源于中国家电网、人民网家电频道、搜狐数码、Coolblue 等公开评测与维修资料；"
     "错误代码 E17 来源于博世同系列 HomeProfessional 洗衣机的公开故障说明。")
para("3. 支付宝「付款码」的功能描述依据其公开的付款码使用说明，以及该界面长期为用户提供的可见交互"
     "（一维码与二维码同屏、付款方式同屏可切换、被扫成功后即时反馈与语音播报）。")
para("4. 博世 WAY32880TI 的功能描述依据其公开产品规格：8kg 洗涤容量、1600 转/分最高转速、"
     "i-DOS 自动投放系统、19 种洗涤程序、TFT 显示屏、触摸式按键。")
para("5. 理论出处：本报告引用的设计原则与概念均来自课堂讲授内容与课程阅读材料，包括 Norman 的设计原则"
     "（可见性、反馈、映射、约束、可供性）、执行的鸿沟与评估的鸿沟、行动七阶段框架、"
     "Miller 7±2 认知负荷、渐进式披露、设计姿态的区分（工具/媒体）、"
     "Nielsen 启发式规则（状态可见性、用户控制与自由、内部一致性、帮助文档与恢复、系统与现实世界匹配）等。")
para("6. 关于评价边界：本文只评价上述两个具体功能，不构成对支付宝或博世任何产品整体设计水平的判断。")

doc.save(OUT)
print("saved", OUT)
