from pathlib import Path
import json
from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs'/'实验报告';OUT.mkdir(parents=True,exist_ok=True)
DATA=json.loads((ROOT/'tmp/survey_build/analysis.json').read_text(encoding='utf-8'))
AFF=json.loads((ROOT/'outputs/亲和图/亲和图数据.json').read_text(encoding='utf-8'))
CARDS={c['id']:c for c in AFF['cards']}
FIG=ROOT/'outputs/问卷分析/图表'
d=Document()
s=d.sections[0]
s.page_width=Inches(8.5);s.page_height=Inches(11)
s.top_margin=Cm(2.0);s.bottom_margin=Cm(2.0);s.left_margin=Cm(2.3);s.right_margin=Cm(2.3)
s.header_distance=Cm(.7);s.footer_distance=Cm(.8)
for name in ['Normal','Title','Subtitle','Heading 1','Heading 2','Heading 3','Caption']:
 st=d.styles[name];st.font.name='Times New Roman';st.font.color.rgb=RGBColor(0,0,0)
 st.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'宋体')
 st.font.size=Pt(12);st.paragraph_format.line_spacing=1.5;st.paragraph_format.space_after=Pt(6)
 st.font.italic=False
 st.paragraph_format.widow_control=True
 for border in list(st.element.iter(qn('w:pBdr'))):border.getparent().remove(border)
d.styles['Title'].font.size=Pt(20);d.styles['Title'].paragraph_format.space_after=Pt(12)
for name,size in [('Heading 1',15),('Heading 2',13),('Heading 3',12)]:
 d.styles[name].font.size=Pt(size);d.styles[name].font.bold=True
 d.styles[name].paragraph_format.space_before=Pt(10);d.styles[name].paragraph_format.keep_with_next=True
d.styles['Caption'].font.size=Pt(10);d.styles['Caption'].font.italic=False
d.styles['Caption'].paragraph_format.space_after=Pt(7)
# Source report requirements: 12pt Latin Times New Roman, Chinese Song, 1.5 spacing.
def p(text='',style=None,bold=None):
 x=d.add_paragraph(style=style)
 r=x.add_run(text)
 if bold is not None:r.bold=bold
 return x
def h(text,level=1):return p(text,'Heading '+str(level))
def br():d.add_page_break()
def pending(text):
 x=p('【待补充】'+text)
 for r in x.runs:r.font.highlight_color=7
 return x
def shade(cell,fill):
 pr=cell._tc.get_or_add_tcPr();e=OxmlElement('w:shd');e.set(qn('w:fill'),fill);pr.append(e)
def set_cell(cell,text,header=False,center=False):
 cell.text='';pr=cell.paragraphs[0];pr.paragraph_format.space_after=Pt(0);pr.paragraph_format.space_before=Pt(0)
 pr.paragraph_format.line_spacing=1.5
 pr.alignment=WD_ALIGN_PARAGRAPH.CENTER if center else WD_ALIGN_PARAGRAPH.LEFT
 r=pr.add_run(str(text));r.font.size=Pt(12);r.font.name='Times New Roman';r._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'宋体');r.bold=header
 if header:r.font.color.rgb=RGBColor(0,0,0)
 cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
 return pr
def table(rows,widths,center_cols=(),keep=False):
 t=d.add_table(rows=1,cols=len(rows[0]));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
 for c,w in zip(t.columns,widths):c.width=Cm(w)
 pr=t._tbl.tblPr
 borders=OxmlElement('w:tblBorders')
 for side in ['top','left','bottom','right','insideH','insideV']:
  e=OxmlElement('w:'+side);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
 pr.append(borders)
 margins=OxmlElement('w:tblCellMar')
 for side in ['top','left','bottom','right']:
  e=OxmlElement('w:'+side);e.set(qn('w:w'),'85');e.set(qn('w:type'),'dxa');margins.append(e)
 pr.append(margins)
 for i,row in enumerate(rows):
  cells=t.rows[0].cells if i==0 else t.add_row().cells
  for j,(cell,val) in enumerate(zip(cells,row)):
   cell.width=Cm(widths[j]);set_cell(cell,val,i==0,j in center_cols)
   if i==0:shade(cell,'E7EDF4')
  if i==0:
   repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
  no=OxmlElement('w:cantSplit');t.rows[i]._tr.get_or_add_trPr().append(no)
 spacer=p();spacer.paragraph_format.line_spacing=Pt(1);spacer.paragraph_format.space_after=Pt(5)
 for run in spacer.runs:run.font.size=Pt(1)
 return t
def chart(stem,note,width=16.5):
 x=p();x.paragraph_format.space_after=Pt(0);x.paragraph_format.keep_with_next=True
 x.alignment=WD_ALIGN_PARAGRAPH.CENTER
 x.add_run().add_picture(str(FIG/(stem+'.png')),width=Cm(width))
 p(note,'Caption')
def qrows(q):return [r for r in DATA['stats'] if r['q']==q]
def link(par,url,text=None):
 e=OxmlElement('w:hyperlink');e.set(qn('r:id'),par.part.relate_to(url,RT.HYPERLINK,is_external=True))
 r=OxmlElement('w:r');rp=OxmlElement('w:rPr');f=OxmlElement('w:rFonts');f.set(qn('w:ascii'),'Times New Roman');f.set(qn('w:hAnsi'),'Times New Roman');rp.append(f)
 c=OxmlElement('w:color');c.set(qn('w:val'),'0563C1');rp.append(c);r.append(rp);t=OxmlElement('w:t');t.text=text or url;r.append(t);e.append(r);par._p.append(e)

p('人机交互实验课作业5','Title')
p('SmartCampus 校园助手数据分析实验报告','Subtitle')
p('团队名称：SmartCampus+ 小组')
p('团队成员：黎贤栗 202300130069；孔令桐 202300130186；马云龙 202300130106；卢泽同 202300130184。')
url='https://smartcampus-plus-p3-hci-2026.active-rook-1294.chatgpt.site'
x=p('项目网站：');link(x,url)
h('1 项目介绍与研究方法')
p('SmartCampus+ 是面向大学生的情境感知型校园助手，拟整合课程表、校园导航、食堂信息、自习空间状态、校园交通和个性化通知。本阶段基于前期收集的问卷与访谈，分析学生如何安排校园活动、哪些信息影响决策，以及他们在什么条件下愿意接受推荐和共享数据。')
p('我们分析了11份问卷和4位用户的半结构化访谈。问卷采用描述性统计呈现样本背景、行为与偏好；访谈从26轮问答中提取44条数据便利贴，形成6个上层主题和18个子主题的初步亲和图。结果支持先验证自习空间与食堂信息，并保留用户对通知、推荐和数据使用的控制。')
h('1 1 数据来源与处理口径',2)
p('问卷编号为R01至R11，访谈编号为I01至I04，两套编号相互独立。问卷均自报符合目标用户条件并同意参与；按编号及完整回答核对后，没有重复编号或完整重复答卷。已将Excel与前期Word报告中的286项问卷回答逐项核对，内容一致。')
p('Q5有10份有效回答，Q22仅2人作答，其余各题均为11人。缺失值原样保留，不补成零分或中立分。单选与量表题展示人数及比例；多选题按选择该项的人数统计，比例之和可超过100%。排序题每项按5减名次计分，第一名4分、第五名0分，每项总分最高44分。')
p('亲和图目前为基于原始访谈的分析草案。实体归类讨论、过程照片以及本次作业的实际成员贡献，留在相应位置由小组补充确认。')

br();h('2 问卷数据分析');h('2 1 样本背景',2)
table([['指标','人数与比例'],['本科一年级','1/11（9.1%）'],['本科二年级','1/11（9.1%）'],['本科三年级','4/11（36.4%）'],['本科四年级及以上','4/11（36.4%）'],['研究生','1/11（9.1%）'],['校内住宿','10/11（90.9%）'],['校外步行或骑行到校','1/11（9.1%）'],['每周到校6至7天','10/11（90.9%）'],['每周到校5天','1/11（9.1%）'],['主要使用智能手机','8/11（72.7%）'],['主要使用笔记本电脑','3/11（27.3%）']],[10.4,6.5],center_cols=(1,))
chart('01_学习阶段','Q1有效n=11。图中为人数及占有效回答的比例。',15.8)
p('样本以高年级本科生和住校学生为主：本科三年级和四年级及以上合计8人，10人住校。结果主要反映这一小规模便利样本的情况，不能代表全校学生或所有校外通勤者。')

h('2 2 当前信息查询习惯',2)
chart('02_查询频率','Q5有效n=10，Q7与Q8有效n=11。三题使用同一频率选项，色块数字为人数。')
p('出发前查看课表或日程方面，9/10人选择经常或总是。就餐前查看食堂拥挤、排队或供应信息方面，10/11人选择经常或总是。前往学习空间前查看空位或使用情况方面，9/11人选择经常或总是。这些结果显示相关信息与本样本的日常决策有关，但题目没有测量现有信息是否准确或容易获取。')
chart('03_导航频率','Q6有效n=11。该题使用实际使用频率选项，与Q5、Q7、Q8的量表不同，因此单独呈现。')
p('4人从不使用校内地图，3人每月少于一次，合计7/11（63.6%）。后文Q14中所有人又认可结合日程的路线建议有帮助，说明当前导航频率和对未来方案的态度需要分别理解。')

h('2 3 时间负担与校园服务使用',2)
table([['Q9 每周估计浪费时间','人数','比例'],*[[r['option'],r['count'],f'{r["pct"]:.1%}'] for r in qrows('Q9')]],[10.4,2.7,3.8],center_cols=(1,2))
p('2人估计每周浪费超过2小时，另有2人不确定。Q9是区间题，包含开放上界和“不确定”，因此不计算平均浪费时长。结果为受访者自报估计，不等同于独立计时。')
chart('04_每周服务','Q10有效n=11，多选题。图示为非零选项，“其他”为0人；各项比例之和可以超过100%。')
p('教学楼和食堂或咖啡店均为11/11人选择，图书馆和自习空间均为10/11人选择。学习与就餐是本样本常见的每周活动，可以作为后续原型测试的场景；选择人数不能用于推断使用时长或满意度。')

h('2 4 功能相对优先级',2)
chart('05_功能排序','Q11完整排序n=11。每项总分为所有参与者的“5减名次”之和；得分越高，表示样本中的相对优先级越高。')
table([['功能','排序总分','平均名次','第一名人数','第五名人数'],*[[r['label'],r['score'],f'{r["mean"]:.2f}',r['first'],r['last']] for r in DATA['rank']]],[7.7,2.1,2.1,2.5,2.5],center_cols=(1,2,3,4))
p('自习空间空位情况获得34分、5人排第一；食堂拥挤情况获得30分、3人排第一，在本样本中位居前两位。路线建议18分、校园交通17分、统一通知11分。该计分用于描述相对排序，不用于预测真实使用量。')
p('平均或总分之外还存在个人差异：路线建议被2人排第一、5人排第五，统一通知被1人排第一、6人排第五。因此不能仅依赖总分，将某项功能解释为所有用户都需要或都不需要。')

h('2 5 功能态度与意外发现',2)
chart('06_功能态度','Q12至Q14各有11份有效回答。横轴为有效回答比例，色块数字为人数。')
table([['问题','同意或非常同意','中立'],['Q12 整合助手减少切换精力','8/11（72.7%）','3/11（27.3%）'],['Q13 实时占用影响设施选择','11/11（100%）','0'],['Q14 结合日程的路线有帮助','11/11（100%）','0']],[8.9,4.5,3.5],center_cols=(1,2))
p('实时占用信息得到一致的态度认可，与空间及食堂功能在排序中的领先相呼应，为后续验证提供了方向。但问卷没有测量实际使用或节省时间，不能据此声称系统已改善效率。')
p('一个值得继续研究的发现是：11人都认为情境路线建议有帮助，但其中5人仍将其排在五项功能的最后。Q14评价潜在帮助，Q11要求相对取舍，两题衡量内容不同。功能被认可，并不意味着应该优先开发或一定会被高频使用。')
p('本样本只有1位研究生和1位校外居住者，本科一年级、二年级也各只有1人，因此不据此推断年级或居住方式导致的差异。本次以描述性统计和跨题对照为主。')

h('2 6 通知偏好与推荐控制',2)
chart('07_通知方式','Q15有效n=11，题目针对非紧急信息。')
chart('08_通知上限','Q16有效n=11。7/11（63.6%）最多接受每日5条非紧急主动通知。')
p('主动打开查看和少量汇总各3人，立即推送2人，自选时间摘要1人，不希望主动通知2人。接收方式较分散，支持将提醒的方式、数量和时机作为可调设置。')
table([['Q17 推荐控制偏好','人数','比例'],*[[r['option'],r['count'],f'{r["pct"]:.1%}'] for r in qrows('Q17')]],[11.2,2.2,3.5],center_cols=(1,2))
p('R09、R10在Q15选择不希望主动通知，却在Q16给出非零容忍上限。两题分别问偏好和最大接受量，不能仅据此判定填写错误；保留原回答，并在后续具体任务中确认其含义。')

h('2 7 数据权限与接受条件',2)
chart('09_权限接受度','Q18、Q19各有11份有效回答。定位题限定为仅在App使用期间获取位置；课表题限定为情境提醒与路线用途。')
p('8/11（72.7%）接受或非常接受仅使用时获取位置，3人中立；11/11人接受或非常接受连接课程表。这是对题目具体用途的态度，不代表所有情境下的无条件授权。')
chart('10_不愿共享的信息','Q20有效n=11，多选题。“控制充分时愿共享全部”为条件性选项，应与具体不愿共享的信息分别解释。')
p('8/11（72.7%）选择控制充分时愿共享全部，其余3人对部分数据保留限制。R10在Q19接受连接课表，但Q20又选择不希望共享课表。该差异可能与用途、题意理解或未澄清原因有关，原样保留。')
p('设计上应逐项说明用途，提供独立权限开关、撤销入口和必要的用户确认。实际产品中的授权仍需在具体使用情境下进行，研究中的开放意愿不能代替实际授权。')

h('2 8 信任因素与开放回答',2)
chart('11_信任因素','Q21有效n=11，每人最多选择三项。多选比例之和可超过100%。')
p('10/11（90.9%）选择长期推荐准确性，8/11（72.7%）选择学校官方验证或支持，4/11（36.4%）选择解释推荐原因。该题反映最多三项的相对优先选择，未选择某项不等于不重视或反对该项。')
table([['Q22 编号','开放回答原文'],['R01',DATA['records'][0]['Q22']],['R05',DATA['records'][4]['Q22']]],[2.7,14.2])
p('Q22仅2/11人作答，本题作答率18.2%。两条回答分别提及食堂排队和自习空位，与封闭题的优先场景相呼应。由于开放回答少，不能把有效回答中各占一半解释为全体学生的需求比例。')
h('2 9 问卷分析总结',2)
p('本次11份问卷中，学习空间和食堂信息在功能相对排序中领先，且所有填写者均认可实时占用会影响去向。出乎预期的是，路线建议虽获一致的潜在价值认可，仍有5人将其排在最后。通知与推荐控制偏好也较分散。我们据此建议先验证学习与就餐场景，并提供可调的通知和权限设置，同时用真实任务检验方案是否有效。')

h('3 访谈数据分析与亲和图');h('3 1 访谈样本与便利贴提取',2)
table([['编号','背景','问答轮次','提取数据卡'],['I01','大四，住校',8,14],['I02','大一，住校北区',6,11],['I03','本科大二，校外租房，电动车通勤',7,11],['I04','研究生一年级，住校北区，电动车通勤',5,8]],[1.5,9.8,2.8,2.8],center_cols=(0,2,3))
p('从访谈的具体经历、日常行为、困难、应对方式和个人偏好中提取44条独立信息，每条保留便利贴编号和问答出处。便利贴是对回答的概括，不作为逐字引语。I01、I02、I03、I04分别以黄色、蓝色、绿色和紫色区分来源，主题卡另计。')
p('对证据性质分别标注：N13为假设情境回答，N19为条件性偏好，N42为一般情境举例；其余仍以受访者自报为基础，不写成现场观察。I03的返校路线已由I03-03澄清；I01食堂楼层等未澄清表述不用于精确归纳。')
br();h('3 2 亲和图主题结构草案',2)
table([['上层主题','子主题','数据卡数量'],*[[t['id']+' '+t['title'],'\n'.join(g[0]+' '+g[1] for g in t['groups']),sum(len(g[2]) for g in t['groups'])] for t in AFF['themes']]],[5.3,9.6,2.0],center_cols=(2,))
p('A和B关注地点与服务状态，C和D关注活动衔接及出行条件，E和F关注信息接收、信任和自主控制。各组共同回答学生如何在具体情境中形成可执行的校园安排。附录A以可编辑的层级表格呈现全部主题、子主题和44张数据卡。')

br();h('3 3 制作过程记录',2)
p('以下为实际制作过程的记录位置。应在小组完成对应步骤后，插入真实照片并按实际情况填写说明；目前不将待进行的实体分组写成已完成。')
table([['阶段','照片位置','过程说明'],['原始数据提取','待插入原始便利贴照片','待记录：如何从访谈提取单条信息、如何标注来源。'],['初次分组','待插入初次分组照片','待记录：哪些卡片因相似经历、需求或条件被归为一组。'],['讨论与调整','待插入调整过程照片','待记录：实际发生的移动、拆分、合并或主题改名及理由。'],['最终实体图','待插入最终布局照片','待记录：最终上层主题、子主题和卡片数量；核对数字版本。']],[3.2,5.0,8.7])
pending('补入以上照片和实际说明后，按最终分组更新附录A及数字亲和图。')
h('3 4 主题发现与分析',2)
findings=[
 ('学习空间的实际适用条件','N20至N22显示，课表占用与实际活动占用需要区分。I01关心空调、插座、人数、安静程度和距离；I03在拥挤或偏好位置被占时会换地点。I04已有固定工位，不需要公共自习空间。设计应呈现适用条件，并保留用户需求差异。'),
 ('就餐信息影响选择与感受','I02需要到窗口比较当日菜品，文字菜单不易判断具体菜品；I03和I04会因队伍过长而改选。I03强调没吃到想吃的饭菜带来的郁闷，说明影响不只有时间。信息展示可以支持比较，但不能声称能够改善菜品口味。'),
 ('活动安排包含准备与往返动机','I01的延误包括打水、小程序卡顿及等电梯，不能把十五分钟全部当成纯步行耗时。I03回出租屋是为了午休和充电，I04在冬天往返骑车不便。安排支持应考虑准备、休息、交通方式及天气，也要保留现有课表已经有效的顺利经验。'),
 ('交通选择兼顾可靠性与自由','I03雨夜等巴士的总等候约十几至二十分钟，相对排班晚到十几分钟，两者不能相加作为总延误。I04从未乘坐巴士，更看重电动车的时间自由，不能作为巴士实际延误的第二个案例。'),
 ('通知价值取决于相关性','I01希望课前约半小时提醒，I03希望紧急调课和课前任务提醒；I02对通知集中持保留意见，I04基本没有漏看或无关消息打扰。统一入口应保留选择性，不能将所有人的需求概括为更多推送。'),
 ('共享意愿以信任和控制为条件','I01信任官方课表，但面对过期空间信息仍只能到场核实。I02愿贡献状态并希望署名可选，I03与I04强调自主控制。应分别说明信息来源、时效和数据用途，并允许用户调整共享范围。'),
]
for title,text in findings:
 h(title,3);p(text)
h('3 5 访谈分析总结',2)
p('初步归类显示，用户关心信息能否反映实际可用状态、是否符合当下活动，以及是否能自主选择接收和共享方式。值得注意的是，现有课表与提前通知对部分用户已经有效，公共自习空间和通知集中也并非所有人的共同需求。后续方案应围绕具体场景验证空间与食堂信息，同时保留准备缓冲、个性化提醒和权限控制。本段结论需在小组实际归类后，与最终主题结构保持一致。')

br();h('4 综合发现与后续设计')
table([['设计方向','对应证据','下一步验证'],['优先验证学习空间与食堂信息','Q11、Q13；I01的空间偏好及I02至I04的就餐经历','能否找到适合的空间，能否在就餐前比较菜品与排队。'],['路线建议结合准备与后续活动','Q6低频导航与Q14态度认可并存；I01准备延误','仅路线与加入准备缓冲、活动衔接的信息有何实际差别。'],['通知与推荐保留可选控制','Q15至Q17偏好分散；访谈中消息负担不同','自主查看、汇总、推送及确认机制是否符合具体任务。'],['明确数据用途和信息可靠性','Q18至Q21；I01信任依据及I02至I04控制条件','用户能否理解权限、来源、更新时间及纠错方式。']],[4.0,6.4,6.5])
p('问卷与访谈用于相互解释，不进行未经确认的参与者关联。例如，问卷提示自习空间优先，访谈说明“无课”之外还要考虑实际占用与环境；问卷显示通知偏好分散，访谈解释了个人关注方式和圈子差异。两种方法形成的共同方向仍需通过原型和真实任务检验。')
h('5 研究限制')
p('问卷只有11人，访谈只有4人，均为便利招募。问卷高年级本科生与住校学生占比较高，不能代表全校或所有通勤学生。缺少邀请总人数，无法计算整体问卷回收率，Q22的18.2%仅为本题作答率。')
p('问卷为自报行为和态度，访谈时间为回忆估计；一般习惯、假设回答和具体事件已经区分，但仍缺少现场观察和实际产品使用记录。因此不主张因果关系，不把功能偏好解释为使用预测，也不把研究开放意愿解释为实际授权。Q5、Q22缺失与跨题差异原样保留。')

br();h('6 成员贡献')
p('团队成员为黎贤栗、孔令桐、马云龙、卢泽同。下表按本次作业的实际撰写、修改和审阅填写，前一阶段的分工不直接作为本次贡献记录。')
table([['部分','初稿或整理负责人','修改与审阅负责人'],['问卷核对与统计','待填写','待填写'],['问卷图表与结果解释','待填写','待填写'],['访谈便利贴与主题归纳','待填写','待填写'],['实体分组与过程照片','待填写','待填写'],['数字亲和图与报告整合','待填写','待填写']],[7.0,4.95,4.95])
h('7 资料来源')
p('1. SmartCampus_P3_问卷原始数据.xlsx：问卷原始数据、题目与字段说明。')
p('2. SmartCampus_P3_作业四_修订版.docx：四位受访者逐字稿、研究背景与前期问卷记录。')
p('3. slide9_DataAnalysis.pdf：亲和图方法与问卷描述性统计、可视化及解释的课程内容。')
p('4. 人机交互实验课作业5要求PDF：分析内容、提交格式和评分标准。')

counts=[]
for ti,t in enumerate(AFF['themes']):
 br()
 if ti==0:h('附录A 数字亲和图与数据便利贴')
 h(t['id']+' '+t['title'],2)
 p('层级关系：上层主题 '+t['id']+' → 子主题 → 数据便利贴。以下短句及出处均可直接编辑。','Caption')
 tab=table([['编号','数据便利贴内容','问答出处']],[1.6,12.4,2.9],center_cols=(0,2))
 # Remove the trailing blank paragraph temporarily, so the table remains the sole container.
 for gid,gtitle,ids in t['groups']:
  row=tab.add_row();merged=row.cells[0].merge(row.cells[-1]);set_cell(merged,gid+' '+gtitle,True);shade(merged,'E7EDF4')
  for num in ids:
   c=CARDS['N'+num];row=tab.add_row()
   for j,val in enumerate([c['id'],c['text'],c['source']]):set_cell(row.cells[j],val,False,j in [0,2])
   shade(row.cells[0],{'I01':'FFF1AF','I02':'DCECFB','I03':'DDEEDB','I04':'EEDFF4'}[c['participant']])
   no=OxmlElement('w:cantSplit');row._tr.get_or_add_trPr().append(no)
   counts.append(c['id'])
 p('证据性质：'+'；'.join(c['id']+'为'+c['type'] for num in [v for _,_,arr in t['groups'] for v in arr] if (c:=CARDS['N'+num])['type'] in ['假设情境回答','条件性偏好','一般情境举例']) if any(CARDS['N'+v]['type'] in ['假设情境回答','条件性偏好','一般情境举例'] for _,_,arr in t['groups'] for v in arr) else '本组信息为受访者自报经历、习惯或偏好；出处可回查原始访谈。','Caption')

# Page numbering without decorative headers.
f=s.footer.paragraphs[0];f.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=f.add_run();r.font.size=Pt(10)
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');r._r.addnext(field)
d.core_properties.title='SmartCampus 校园助手数据分析实验报告'
d.core_properties.subject='人机交互实验课作业5 数据分析'
d.core_properties.author='SmartCampus+ 小组'
d.save(OUT/'SmartCampus_作业5_数据分析实验报告_可编辑版.docx')
assert len(counts)==44 and len(set(counts))==44
print('Saved:',OUT/'SmartCampus_作业5_数据分析实验报告_可编辑版.docx')
print('Paragraphs:',len(d.paragraphs),'Tables:',len(d.tables),'Images:',len(d.inline_shapes),'Cards:',len(counts))
