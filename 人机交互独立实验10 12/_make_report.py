# -*- coding: utf-8 -*-
"""生成《人机交互实验课作业3》Word 报告。"""
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

FIG = "figures"
OUT = "人机交互实验课作业3-报告.docx"

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
    """缩进的「推测 / 重新设计」段落。"""
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
                   ("案例二（糟糕）", "Windows 11 文件资源管理器右键菜单")]:
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
      ("作业要求「提供有助于说明观点的截图，如果无法截图请提供草图」。本报告两个案例的界面均随版本更新而变化，"
       "无法为读者复现同一时刻的真实截图。因此统一采用「按公开界面重绘的示意图」代替截图，属于作业允许的草图形式。"
       "示意图用于标注交互结构与控件属性，不作为像素级还原的证据。事实来源见文末「方法与资料来源」。", False)])
rich([("关于案例选择：", True, "微软雅黑"),
      ("本文只评价两个产品各自的一个具体功能，不评价任何产品的整体优劣。支付宝的订单与设置类页面同样有可批评之处，"
       "Windows 11 的窗口管理与资源管理器导航也有相当成熟的改进。把产品当成评价单位，是这类作业最常见的失分点。", False)])

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
h1("案例二（糟糕）：Windows 11 文件资源管理器右键菜单")

h2("1. 这个功能让用户做什么")
para("右键菜单是用户在文件资源管理器里对文件或文件夹发起操作的入口：打开、复制、重命名、删除、压缩、"
     "用第三方程序打开、查看属性等。它的整体用途是「就地给出一组可对当前对象执行的动作」，"
     "因此它本质上是一份短小的命令清单，用户期望的是「一眼看到我要的那一条，然后点掉」。"
     "按这个标准，右键菜单的质量取决于三件事：常用命令是否在第一时间可见、同一动作的名称与位置是否稳定、"
     "以及展开一次菜单要付出多少步数与多少等待。Windows 11 对这一菜单做了重新设计，本报告聚焦其中「精简菜单 + "
     "显示更多选项」这一具体改动，它在上述三点上都留下了明显问题。")

h2("2. 界面示意")
figure("fig3_win11_menu.png", 13.0,
       "图 3  Windows 11 文件资源管理器的新右键菜单（按公开界面重绘）")
figure("fig4_win11_split.png", 16.0,
       "图 4  「显示更多选项」把用户分到了两套完全不同的菜单里（示意图）")

h2("3. 它为什么是糟糕设计：五条理由，附推测与重新设计")

bullet("问题一：把「显示更多选项」放在最底部，让高频命令变成第二步。",
       "新菜单的一级只保留打开、在新选项卡中打开、固定到「快速访问」、压缩为 ZIP 文件，以及一行图标按钮，"
       "其余命令全部收进菜单最底部的「显示更多选项」，点开后弹出的是旧版菜单。"
       "问题在于，被折叠的并不都是罕用命令：解压压缩包、发送到、第三方工具（如用 7-Zip 打开、CRC 校验）"
       "都是高频操作。用户最常做的动作反而需要两次点击，而且两次点击之后菜单还会整体换一套。"
       "按设计原则的说法，这是一次「可见性」上的倒退：减少菜单长度的收益，被高频任务的额外步骤抵消了，"
       "并且这种成本落在每一个使用者、每一次操作上。")
small("推测：为什么会设计成这样。",
      "Win11 的菜单精简是一致性工程的产物——把系统级菜单统一成现代样式、统一图标与间距，"
      "而第三方与旧式命令是通过 shell 扩展注册的，无法直接继承新样式。"
      "最省力的办法就是把它们整体挡在新菜单之外，先保证「新菜单里的一切都是新的」，"
      "把兼容性问题推给用户多点的这一次。这是一个典型的为架构整洁牺牲交互步数的取舍。")
small("重新设计：",
      "让一级菜单按用户实际使用频率排列，而不是按「是不是新式命令」排列：把系统内置命令与第三方常用命令放在同一层，"
      "只有真正低频的管理类命令（属性、脱机可用等）才进二级。若确需保留折叠，则应把折叠入口改成带说明的入口"
      "（例如「显示全部命令」），并支持把用户常用的命令固定到一级。")

bullet("问题二：「显示更多选项」这个名字对第一次使用的人没有意义。",
       "这个标签只回答了「还有东西」，没有回答「还有什么、代价是什么」。对已经形成肌肉记忆的老用户，它只是多一步；"
       "对新用户或很少整理文件的用户，它几乎是一个空标签——他们不知道点开后会得到经典菜单，"
       "也不知道自己日常需要的压缩、发送到命令就藏在里面，于是可能直接放弃，或误以为这个功能不存在。"
       "从认知角度看，标签的作用是帮助用户建立正确的预期与心智模型，而「更多选项」既没有给出内容的类别，"
       "也没有给出与旧菜单的对应关系，属于语义上正确、信息量为零的命名。")
small("推测：为什么会设计成这样。",
      "「显示更多选项」是一个安全的、不承诺任何具体内容的命名：它不会因为内容变化而变得不准确，"
      "在本地化与文案评审中最容易通过。相比之下，「显示经典菜单」这样的名字会暴露新旧两套菜单并存的事实，"
      "等于承认新设计没有覆盖全部场景。命名上的模糊，往往是设计决策有争议时的一种回避。")
small("重新设计：",
      "把标签写成用户能据此决策的话：「显示全部命令（经典菜单）」，并在悬停时给出包含哪些常用命令的提示。"
      "更彻底的做法是取消这个二选一：只留一套菜单，把旧命令作为普通条目混排进去，"
      "让「有两套菜单」这件事本身消失。")

bullet("问题三：图标行只有图标没有文字，可识别性差。",
       "新菜单把剪切、复制、重命名、共享、删除压缩成一行只有图标、没有文字的按钮，文字标签非常小且颜色很浅。"
       "对不常使用这些命令的用户，图标近似程度高（剪切与复制、重命名与删除很容易看错），需要靠位置记忆而不是靠识别；"
       "对视力不佳或在高 DPI 缩放下的用户，实际可读性更差。图标作为辅助是好的，但当图标成为唯一识别依据时，"
       "界面的容错率就下降了——一旦点错，剪切与删除的后果并不对等。"
       "这也违反了「图标应配文字标签」的可用性经验规则。")
small("推测：为什么会设计成这样。",
      "图标行是为了压缩菜单高度、让菜单看起来更轻。在触屏与触控板手势的语境下，图标按钮确实更省空间，"
      "而设计评估通常在熟悉产品的人身上进行，他们不会看错这些图标，"
      "于是「识别成本」这个问题在内部测试中很难暴露出来。")
small("重新设计：",
      "把这五个动作还原为带文字的普通条目，按语义分组（例如「编辑」组含剪切、复制、重命名、删除；「共享」组含共享、发送到）。"
      "如果必须保留图标行，则至少保证文字标签的字号与对比度达到正文水平，"
      "并把破坏性操作（删除）与其余操作在视觉上分开，避免误触。")

bullet("问题四：层级被拉平，不同性质的动作获得同等权重。",
       "新菜单的一级里，「压缩为 ZIP 文件」「复制文件地址」「属性」与「打开」并列，之间只用细线分隔。"
       "在旧菜单里，这些命令通过分组与位置表达了性质差异（打开类在前、编辑类居中、属性收尾），"
       "而新菜单把层级差异压缩成纯粹的纵向排列。结果是扫视失去抓手：用户读的是「一列九行文字」，"
       "而不是「三组不同性质的动作」。按认知要素的角度，分组是降低视觉搜索负担的手段，"
       "取消分组等于把这部分负担转回给用户。")
small("推测：为什么会设计成这样。",
      "统一的间距与统一的分隔线最符合 Fluent 视觉规范，也最容易在多语言、多 DPI 下保持一致；"
      "分组需要设计者判断哪些命令同类、顺序如何，是额外决策。在追求视觉一致性的设计系统里，"
      "「整齐」往往优先于「有结构」，因为前者可以规范，后者需要具体场景判断。")
small("重新设计：",
      "恢复语义分组并写出组名（打开 / 编辑 / 共享与发送 / 工具），组内按使用频率排序；"
      "破坏性操作单独成组并做危险色提示；分隔线只在组之间出现，而不是在每一行之后。"
      "本报告图 5 给出的即是这一形态。")

bullet("问题五：一个动作、两套菜单、两种规则，用户无法形成稳定预期。",
       "折叠之后，同一个文件存在两套右键菜单：新菜单是一套命名与图标，点开「显示更多选项」后的旧菜单是另一套命名与分组，"
       "连「在新选项卡中打开」与「在新窗口中打开」这类同名近义项也在两套菜单里各说各话。"
       "再叠加一层子菜单（打开方式、发送到、CRC SHA），完成一次操作可能需要经过「新菜单 → 显示更多选项 → 子菜单」三层路径。"
       "这违反了内部一致性原则：系统对同一件事给出不同说法与不同位置，用户就无法建立稳定的记忆，"
       "每次都要重新寻找和试错。也正因为如此，公开讨论中长期存在大量「如何恢复经典右键菜单」"
       "「如何让全部选项默认显示」的求助与教程。")
small("推测：为什么会设计成这样。",
      "新菜单与旧菜单由不同的代码路径渲染（一个是 XAML 呈现层，一个是沿用多年的 Win32 菜单），"
      "两者在 Win11 中是并存而非替代关系；为了不破坏海量第三方 shell 扩展的兼容性，"
      "最稳妥的方案就是保留旧菜单、把新菜单叠在前面。这是技术债务在界面上的直接投影，"
      "产品上则表现为「两套都留着，让用户自己选」。")
small("重新设计：",
      "对外只暴露一套菜单：新样式统一渲染全部命令，旧式 shell 扩展通过适配层进入同一套命名与分组规则；"
      "在过渡期，把「显示全部命令」做成一次明确的模式选择（可选、可记忆、可回退），"
      "而不是每次都要用户重新走一遍路径。同时把高频命令固定到一级，"
      "让用户不必为了「解压一个文件」而理解这个系统里存在两套菜单。")

h2("4. 重新设计方案总览")
figure("fig5_win11_redesign.png", 14.0,
       "图 5  重新设计方案：一屏一菜单、分组可见、快捷键可读（示意图）")

table(["原问题", "改造后的做法", "可观察的验证指标"],
      [["高频命令被折叠到第二层",
        "一级菜单按实际使用频率排序，系统命令与第三方命令同层",
        "右键到目标任务的平均点击数；菜单一级各命令的使用率分布"],
       ["「显示更多选项」语义空洞",
        "改名「显示全部命令（经典菜单）」并给出内容提示，最终取消二选一",
        "该入口点击率；改名后展开类操作的成功率"],
       ["图标行无文字、易看错",
        "还原为带文字条目并按语义分组，删除等破坏性操作做危险色",
        "误触删除后的撤销率；图标行点击的纠错次数"],
       ["层级被拉平、扫视困难",
        "引入组名与组间分隔，组内按频率排序",
        "从打开菜单到选中目标的平均停留时间"],
       ["一套动作两套菜单",
        "统一渲染与命名规则，过渡期把经典菜单做成可记忆的模式选择",
        "「如何恢复经典右键菜单」类求助量；跨菜单不一致命名条目数"]],
      [4.0, 6.8, 5.2])

para("需要说明的是，验证指标里刻意保留了「右键到目标任务的平均点击数」这一项，因为它正是本次改动的核心争议点："
     "菜单变短本身是好事，但如果代价是高频任务多一步、并且多出来的那一步通向另一套规则，"
     "那么简洁只在第一眼成立，在长期使用中会被反复的交易成本抵消。", space_before=6)

doc.add_page_break()

# ================= 方法说明 =================
h1("方法与资料来源")
para("1. 图片来源：本报告全部界面图为按公开资料手工重绘的示意图（Pillow 绘制），属于作业允许的草图形式，"
     "不是任何应用或系统的真实截图，也不代表对应产品当前版本的像素级外观。")
para("2. 支付宝「付款码」的功能描述依据其公开的付款码使用说明，以及该界面长期为用户提供的可见交互"
     "（一维码与二维码同屏、付款方式同屏可切换、被扫成功后即时反馈与语音播报、仅用于线下付款的提示）。")
para("3. Windows 11 右键菜单的描述依据其公开界面：一级菜单为打开、在新选项卡中打开、固定到「快速访问」、"
     "压缩为 ZIP 文件与图标行，底部为「显示更多选项」，点开后为沿用旧版布局的完整菜单。"
     "围绕该设计的公开反馈包括大量「如何恢复经典右键菜单」「如何让全部选项默认显示」的求助与教程，"
     "以及「该右键菜单不受欢迎、相关重做工作正在进行」的报道；本文引用的是这些公开可见的结构与反馈，"
     "不针对某一具体系统版本号。")
para("4. 理论出处：本报告引用的设计原则与概念均来自课堂讲授内容与课程阅读材料，包括 Norman 的设计原则"
     "（可见性、反馈、映射、约束、可供性）、执行的鸿沟与评估的鸿沟、行动七阶段框架、"
     "设计姿态的区分（工具 / 媒体）、用户控制与自由、内部一致性、图标应配文字标签等启发式规则，"
     "以及体验设计中实用质量与享乐质量的划分。")
para("5. 关于评价边界：本文只评价上述两个具体功能，不构成对支付宝或 Microsoft 任何产品整体设计水平的判断。")

doc.save(OUT)
print("saved", OUT)
