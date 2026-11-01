from pathlib import Path
import json, math, html
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, KeepTogether
from reportlab.graphics.shapes import Drawing, Rect, Line, String
from reportlab.graphics import renderSVG

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT/'outputs'/'问卷分析'
FIG=OUT/'图表';FIG.mkdir(exist_ok=True)
D=json.loads((HERE/'analysis.json').read_text(encoding='utf-8'))
pdfmetrics.registerFont(TTFont('CN','C:/Windows/Fonts/simsun.ttc',subfontIndex=0))
pdfmetrics.registerFont(TTFont('CNHead','C:/Windows/Fonts/simhei.ttf'))
pdfmetrics.registerFont(TTFont('TimesLocal','C:/Windows/Fonts/times.ttf'))
INK=colors.HexColor('#20344C');BLUE=colors.HexColor('#35679B');MID=colors.HexColor('#69788A');LIGHT=colors.HexColor('#E7EDF4')
PAL=[colors.HexColor(x) for x in ['#AF503F','#D58C6D','#C9CDD4','#7EACCA','#35679B']]
WIDTH=475
styles={
 'title':ParagraphStyle('title',fontName='CNHead',fontSize=22,leading=31,textColor=INK,spaceAfter=14),
 'head':ParagraphStyle('head',fontName='CNHead',fontSize=16,leading=24,textColor=INK,spaceAfter=12),
 'sub':ParagraphStyle('sub',fontName='CNHead',fontSize=12,leading=18,textColor=INK,spaceBefore=7,spaceAfter=6),
 'body':ParagraphStyle('body',fontName='CN',fontSize=12,leading=18,wordWrap='CJK',spaceAfter=9),
 'small':ParagraphStyle('small',fontName='CN',fontSize=9,leading=13,wordWrap='CJK',spaceAfter=6,textColor=MID),
 'cell':ParagraphStyle('cell',fontName='CN',fontSize=10,leading=14,wordWrap='CJK'),
 'th':ParagraphStyle('th',fontName='CNHead',fontSize=10,leading=14,textColor=colors.white,wordWrap='CJK'),
}
story=[];md=['# SmartCampus+ 问卷分析\n']
def p(s,kind='body'):
 story.append(Paragraph(html.escape(s).replace('\n','<br/>'),styles[kind]));md.append(s+'\n')
def heading(s):p(s,'head');md.append('')
def page():story.append(PageBreak())
def table(rows,widths):
 vals=[[Paragraph(html.escape(str(x)).replace('\n','<br/>'),styles['th' if i==0 else 'cell']) for x in r] for i,r in enumerate(rows)]
 t=Table(vals,colWidths=widths,repeatRows=1,hAlign='LEFT')
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),INK),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),0.6,INK),('LINEBELOW',(0,1),(-1,-1),0.35,LIGHT)]))
 story.extend([t,Spacer(1,10)])
 md.append('| '+' | '.join(map(str,rows[0]))+' |\n|'+'|'.join(['---']*len(rows[0]))+'|')
 md.extend('| '+' | '.join(map(str,r))+' |' for r in rows[1:]);md.append('')
def qs(q):return [x for x in D['stats'] if x['q']==q]
def count(q,option):return next(x['count'] for x in qs(q) if x['option']==option)
def txt(d,x,y,text,size=9,fill=INK,anchor='start',font='CN'):
 d.add(String(x,y,text,fontName=font,fontSize=size,fillColor=fill,textAnchor=anchor))
def bar(q,title,short=None,nonzero=False,rowh=22,save=None):
 rows=qs(q)
 if nonzero:rows=[x for x in rows if x['count']]
 return bars(title,[short.get(x['option'],x['option']) if short else x['option'] for x in rows],[x['count'] for x in rows],rows[0]['valid'],rowh=rowh,save=save,caption=f'{q} 有效 n={rows[0]["valid"]}；人数（百分比）'+('；多选，比例之和可超过100%' if rows[0]['type']=='多选题' else ''))
def bars(title,labels,values,n,rowh=22,save=None,caption=None,score=False):
 labelw=min(258,max(110,max(pdfmetrics.stringWidth(t,'CN',9) for t in labels)+12))
 axisx=labelw;barw=WIDTH-axisx-72;maxv=math.ceil(max(values)/5)*5 if score else n
 h=54+len(labels)*rowh
 d=Drawing(WIDTH,h)
 txt(d,0,h-13,title,11,font='CNHead')
 top=h-37
 ticks=[0,maxv/2,maxv] if score else [0,math.floor(n/2),n]
 for t in ticks:
  x=axisx+t/maxv*barw
  d.add(Line(x,22,x,top+10,strokeColor=LIGHT,strokeWidth=0.5))
  txt(d,x,8,f'{t:g}',8,MID,'middle')
 for i,(label,v) in enumerate(zip(labels,values)):
  y=top-i*rowh
  txt(d,axisx-8,y-2,label,9,anchor='end')
  d.add(Rect(axisx,y-4,v/maxv*barw,12,fillColor=BLUE,strokeColor=None))
  t=f'{v}分' if score else f'{v}（{v/n:.1%}）'
  txt(d,axisx+v/maxv*barw+5,y-2,t,9)
 return addchart(d,save,caption)
def stacked(qs_,title,labels,save=None,accept=False):
 h=78+len(qs_)*35;d=Drawing(WIDTH,h)
 txt(d,0,h-13,title,11,font='CNHead')
 axisx=130;barw=300
 for i,q in enumerate(qs_):
  rows=qs(q);y=h-44-i*35
  txt(d,axisx-8,y+3,labels[i]+f' n={rows[0]["valid"]}',9,anchor='end')
  start=axisx
  for j,x in enumerate(rows):
   w=x['pct']*barw
   if w:
    d.add(Rect(start,y,w,17,fillColor=PAL[j],strokeColor=colors.white,strokeWidth=0.5))
    txt(d,start+w/2,y+4,str(x['count']),9,colors.white if j in [0,4] else INK,'middle')
   start+=w
 opts=['非常不接受','不接受','中立','接受','非常接受'] if accept else ['非常不同意','不同意','中立','同意','非常同意']
 for j,label in enumerate(opts):
  x=j*95;d.add(Rect(x,9,9,9,fillColor=PAL[j],strokeColor=None));txt(d,x+12,9,label,8)
 return addchart(d,save,'横轴为各题有效回答比例（0%-100%），色块数字为人数。')
def addchart(d,name,caption):
 story.append(d)
 if caption:p(caption,'small')
 if name:
  svg=renderSVG.drawToString(d).replace('font-family: CNHead','font-family: SimHei').replace('font-family: CN','font-family: SimSun')
  (FIG/(name+'.svg')).write_text(svg,encoding='utf-8')
 return d

# Page 1
p('SmartCampus+ 问卷分析','title')
p('样本背景、功能偏好与使用条件','sub')
p('本次分析覆盖11份有效问卷。结果支持优先验证自习空间和食堂信息两个场景，并为通知方式、推荐控制及数据权限提供可选设置。结论仅描述本次样本的自报行为与偏好。')
heading('一 样本与分析口径')
p('11位填写者均自报符合目标用户条件并同意参与。按匿名编号核对后，没有重复编号或完整重复答卷。问卷22题覆盖背景、行为、功能价值、通知、隐私与信任。')
table([['指标','结果','解释'],['样本量','11人','便利样本'],['本科三年级及以上本科生','8/11（72.7%）','高年级本科生较多'],['校内住宿','10/11（90.9%）','校外生活背景覆盖不足'],['每周到校6-7天','10/11（90.9%）','以高频校园使用者为主'],['主要使用智能手机','8/11（72.7%）','另有3人主要使用笔记本电脑']],[155,125,195])
bar('Q1','图1 学习阶段',nonzero=True,save='01_学习阶段')
p('统计比例以各题有效回答人数为分母：Q5为10人，Q22为2人，其余题目为11人。缺失回答保持为空白，不填零或中立分；多选题按选择该项的人数统计。比例保留一位小数，四舍五入后合计可能不等于100%。','small')

# Page 2
page();heading('二 当前行为与时间负担')
# Same frequency scale for Q5, Q7, Q8. Do not combine the different Q6 scale.
h=170;d=Drawing(WIDTH,h);txt(d,0,h-13,'图2 常规信息查询频率',11,font='CNHead')
for i,(q,label) in enumerate([('Q5','出发前查课表'),('Q7','就餐前查信息'),('Q8','出发前查空间')]):
 rows=qs(q);y=123-i*34;txt(d,119,y+3,label+f' n={rows[0]["valid"]}',9,anchor='end');start=130
 for j,x in enumerate(rows):
  w=x['pct']*300
  if w:d.add(Rect(start,y,w,17,fillColor=PAL[j],strokeColor=colors.white,strokeWidth=.5));txt(d,start+w/2,y+4,str(x['count']),9,colors.white if j in [0,4] else INK,'middle')
  start+=w
for j,t in enumerate(['从不','很少','有时','经常','总是']):
 d.add(Rect(j*95,9,9,9,fillColor=PAL[j],strokeColor=None));txt(d,j*95+12,9,t,8)
addchart(d,'02_查询频率','Q5、Q7、Q8使用同一频率选项。横轴为比例，色块数字为人数。')
p('Q5中9/10人经常或总是查看课表；Q7中10/11人经常或总是查询食堂拥挤、排队或供应信息；Q8中9/11人经常或总是查询空间使用情况。这表明这些信息与本样本当前的日常决策有关，但没有测量现有信息是否准确、是否容易获得。')
bar('Q6','图3 校内地图或导航使用频率',rowh=21,save='03_导航频率')
p('Q6中4人从不使用校内地图，3人每月少于一次，合计7/11（63.6%）。这与后文对情境路线建议的认可并存，值得在真实任务中进一步验证。')
table([['Q9 每周估计浪费时间','人数','比例'],*[[x['option'],x['count'],f'{x["pct"]:.1%}'] for x in qs('Q9')]],[285,85,105])
p('2人估计每周浪费超过2小时，另有2人不确定。Q9为时间区间且包含开放上界和“不确定”，不据此计算平均浪费时长。','small')

# Page 3
page();heading('三 校园服务与功能优先级')
bar('Q10','图4 每周至少使用一次的服务或地点',short={'自习室 / 自习空间':'自习空间','食堂 / 咖啡店':'食堂或咖啡店','校园班车 / 校内交通':'校园班车或校内交通','打印 / 行政服务':'打印或行政服务','快递 / 取件点':'快递或取件点'},nonzero=True,rowh=18,save='04_每周服务')
p('教学楼和食堂均为11/11人选择，图书馆和自习空间均为10/11人选择。这些是自报的每周使用情况，支持将学习和就餐作为后续任务测试场景；不能据此判断使用时长或满意度。')
bars('图5 功能相对排序得分',[x['label'] for x in D['rank']],[x['score'] for x in D['rank']],11,rowh=20,score=True,save='05_功能排序',caption='Q11完整排序 n=11；每人每项得分=5-名次，第一名4分、第五名0分；每项满分44分。')
table([['功能','平均名次','第一名人数','第五名人数'],*[[x['label'],f'{x["mean"]:.2f}',x['first'],x['last']] for x in D['rank']]],[238,79,79,79])
p('自习空间34分、食堂信息30分，在本样本中位居前两位。路线建议18分，2人将其排第一、5人排第五；统一通知11分，1人排第一、6人排第五。总分用于描述相对次序，同时应保留个人偏好差异。')

# Page 4
page();heading('四 功能态度与需要继续验证的差异')
stacked(['Q12','Q13','Q14'],'图6 对整合、占用信息和情境路线的态度',['减少平台切换','占用影响去向','日程路线有帮助'],save='06_功能态度')
table([['问题','同意或非常同意','中立'],['Q12 整合助手减少切换精力','8/11（72.7%）','3/11（27.3%）'],['Q13 实时占用影响设施选择','11/11（100%）','0'],['Q14 结合下一项日程的路线有帮助','11/11（100%）','0']],[255,130,90])
p('实时占用信息得到一致的态度认可，且与空间和食堂功能在排序中的领先相呼应。这为下一步验证这些场景提供方向，但目前没有实际行为或节省时间的测量。')
p('路线建议在Q14获得11人认可，却在Q11仅排第三，并有5人将其放在最后。Q14询问“是否有帮助”，Q11要求在五项功能间进行相对取舍，两者衡量的内容不同。结果支持进一步区分功能的潜在价值和相对优先级。')
p('对导航低频使用的7人，Q14仍全部为同意或非常同意。这一现象说明当前导航频率不能直接替代对情境路线方案的评价；也不能据此认定方案上线后一定会被高频使用。')
p('下一步建议','sub')
p('采用具体任务验证路线建议的价值：例如下一节课前从宿舍出发，比较仅给路线、加入准备缓冲、关联后续活动三种信息组合。任务评价应记录实际操作和结果，并与当前态度问卷区分。')
p('分组比较的边界','sub')
p('样本仅有1位研究生、1位校外居住者，每个低年级各1人，因此本次不根据这些分组推断年级或居住方式导致的差异，也不进行缺乏样本支持的显著性检验。')

# Page 5
page();heading('五 通知方式与推荐控制')
bar('Q15','图7 非紧急信息接收方式',short={'需要时由我主动打开仪表盘查看':'主动打开查看','每天接收少量汇总通知':'少量汇总通知','在我选择的时间接收每日摘要':'自选时间摘要','不希望收到主动通知':'不希望主动通知'},rowh=21,save='07_通知方式')
bar('Q16','图8 每日最多接受的非紧急主动通知',short={'只要信息相关，超过 10 条也可以':'相关时可超过10条'},rowh=20,save='08_通知上限')
p('接收方式分散：主动打开与少量汇总各3人，立即推送2人，自选时间摘要1人，不希望主动通知2人。Q16中7/11（63.6%）最多接受每日5条，提示非紧急提醒需要数量与方式控制。')
table([['Q17 推荐控制偏好','人数','比例'],*[[x['option'],x['count'],f'{x["pct"]:.1%}'] for x in qs('Q17')]],[330,65,80])
p('R09、R10在Q15选择不希望主动通知，却在Q16给出非零容忍上限。两题分别询问偏好与最大接受量，现有数据不能判定为填错；保留原回答，并建议在测试时确认具体情境。','small')

# Page 6
page();heading('六 数据权限与接受条件')
stacked(['Q18','Q19'],'图9 位置与课程表连接的接受度',['仅使用时定位','连接课程表'],save='09_权限接受度',accept=True)
p('Q18中8/11（72.7%）接受或非常接受仅在使用时获取位置，3人中立。Q19中11/11人接受或非常接受连接课表；这一结果针对题目所描述的提醒和路线用途，不代表所有情境下的无条件授权。')
bar('Q20','图10 不希望共享的信息与条件性共享意愿',short={'如果控制机制充分，我愿意共享以上全部信息':'控制充分时愿共享全部','通知点击或交互记录':'通知交互记录'},rowh=22,save='10_不愿共享的信息')
p('Q20中8/11（72.7%）选择“控制机制充分时愿共享全部”。其余3人分别保留对位置、课表、常访地点、搜索、通知交互或无障碍偏好的限制。图中“愿共享全部”为条件性选项，应与不愿共享的具体信息分开解释。')
p('R10在Q19选择接受连接课表，同时在Q20选择不希望共享课表。该跨题差异可能与使用目的、题意理解或其他未澄清原因有关；不擅自统一，也不在缺少追问时选择一种解释作为事实。')
p('设计建议是逐项说明数据用途，提供独立开关、撤销入口和用户确认。支持这些控制的证据包括Q20的条件性表述及访谈中的控制偏好，而非仅以Q21的选择人数作为唯一依据。')

# Page 7
page();heading('七 信任因素与开放回答')
bar('Q21','图11 最能增强信任的因素',short={'清楚解释为什么会给出某条推荐':'解释推荐原因','能够分别开启或关闭不同数据来源':'各数据源独立开关','实时信息显示明确的更新时间和来源':'明确更新时间与来源','能够方便地纠正错误信息':'方便纠正错误','由学校官方验证或支持':'学校官方验证或支持','尽量减少个人数据保存时间':'减少数据保存时间','透明且易理解的隐私政策':'易理解的隐私政策','长期保持较高的推荐准确性':'长期推荐准确性'},rowh=23,save='11_信任因素')
p('10/11（90.9%）选择长期推荐准确性，8/11（72.7%）选择学校官方验证或支持，4/11（36.4%）选择解释推荐原因。Q21最多选择三项，因此结果表示该题设下的相对优先因素；某项未被选择不等于用户不重视或反对该项。')
table([['Q22 编号','开放回答原文'],['R01','查询食堂排队情况'],['R05','自习空间空位情况说明\n对自习室、图书馆空位要求频繁，且考试周高峰期难以寻找']],[80,395])
p('Q22仅2/11人作答，回答率18.2%。两条回答分别提及食堂排队与自习空位，和封闭题的优先场景相呼应。有效回答中各占1/2，不将其表述为全体11人或全校学生各有一半的需求。')
p('与访谈对照','sub')
p('I01优先考虑找自习空间，I02、I03、I04更优先考虑食堂菜单或排队信息；I04有固定工位，缺乏寻找公共自习空间的需求。两种方法共同提示先验证学习与就餐场景，并保留不同用户的实际差异。访谈编号与问卷编号独立，不进行未经确认的一对一关联。')

# Page 8
page();heading('八 综合结论与研究限制')
p('可用于报告的问卷总结','sub')
p('本次11份问卷中，自习空间空位与食堂拥挤信息分别获得34分和30分，位居五项功能排序的前两位。所有填写者均认可实时占用信息会影响校园设施选择。一个值得继续研究的发现是：11人都认为结合日程的路线建议有帮助，但5人仍将其排在五项功能的最后。这提示功能的潜在价值与相对优先级需要分别评价。通知接收方式和推荐控制偏好较分散，支持提供自主查看、汇总与推送等可选方式。数据连接的接受度较高，但共享意愿带有用途和控制条件，推荐准确性及学校官方支持是主要的信任优先因素。这些结果支持先围绕学习与就餐场景开展原型验证，并检验通知设置、空间状态含义和信息可靠性。')
p('建议进入下一阶段的验证','sub')
table([['建议','证据与待验证内容'],['学习空间与食堂信息优先验证','Q11、Q13与访谈共同支持；测试能否帮助用户找到适合的空间、比较就餐选择。'],['路线建议结合具体任务验证','Q6低频使用与Q14认可并存；测试日程衔接和准备缓冲的实际价值。'],['通知与推荐提供控制','Q15—Q17偏好分散；测试关注范围、接收方式、提醒时机与确认流程。'],['明确数据用途和信息来源','Q18—Q21显示条件性开放及准确性优先；测试授权理解、更新时间和错误纠正。']],[145,330])
p('研究限制','sub')
p('样本量为11，且采用便利招募，高年级本科生和住校学生占比较高，不能代表全校或所有通勤学生。仅调查自报行为、偏好和假设方案的态度，未观察实际产品使用，不能证明改善效果或因果关系。缺少邀请总人数，无法计算整体问卷回收率；Q22的18.2%仅为本题作答率。Q5和Q22存在缺失，Q19与Q20等存在未澄清的跨题差异，均已保留。')
p('资料与统计复核','sub')
p('原始问卷：SmartCampus_P3_问卷原始数据.xlsx，工作表“问卷原始数据”和“题目与字段说明”。访谈对照：SmartCampus_P3_作业四_修订版.docx，I01—I04。方法参考：slide9_DataAnalysis.pdf，第58—62页。已逐项比对Word中的286个问卷回答，无内容差异。全部113项选项统计及5项排序由两种计算方式复核；排序得分按5减名次，与原报告保持一致。','small')

def footer(c,doc):
 c.saveState();c.setFont('CN',8);c.setFillColor(MID);c.drawString(60,30,'SmartCampus+  问卷分析');c.drawRightString(535,30,str(doc.page));c.restoreState()
doc=SimpleDocTemplate(str(OUT/'SmartCampus_问卷分析报告.pdf'),pagesize=(595.28,841.89),leftMargin=60,rightMargin=60,topMargin=48,bottomMargin=48,title='SmartCampus+ 问卷分析',author='SmartCampus+ 项目组')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
(OUT/'SmartCampus_问卷分析文字.md').write_text('\n'.join(md),encoding='utf-8')
print('PDF created; charts:',len(list(FIG.glob('*.svg'))))
