from pathlib import Path
import re, json, csv, html, math
from collections import Counter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,PageBreak,KeepTogether
from reportlab.graphics.shapes import Drawing,Rect,Line,String
from reportlab.graphics import renderSVG,renderPDF

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs'/'亲和图';OUT.mkdir(parents=True,exist_ok=True)
source=(ROOT/'tmp/read/SmartCampus_P3_作业四_修订版.txt').read_text(encoding='utf-8')
answers={m.group(1):m.group(2).strip() for m in re.finditer(r'(?m)^(I0[1-4]-\d{2}) (?:提问|追问)\n问 .*?\n答 (.*?)(?=\nI0[1-4]-|\n（访谈结束）)',source,re.S)}
assert len(answers)==26,len(answers)
# Every note is a paraphrase. The final string is an exact excerpt checked against its answer.
data=[
('01','I01-02','自报事件','我预留10分钟去实验楼，结果比计划晚到5分钟。','计划4.10到，我是4.00出发，然后迟到了，4.15到达'),
('02','I01-04','自报习惯','我预估的10分钟，没有包括打水、小程序卡顿和等电梯。','平时估算十分钟是没有考虑到打水、卡顿和等电梯'),
('03','I01-04','自报习惯','找空教室有时要花约10分钟；找不到时，我会继续找。','找空教室的时间可能会花十分钟左右'),
('04','I01-07','空间偏好','我可以和其他人一起自习，只要人数不多、环境不吵。','里面有自习的人我是可以接受的，只要人不太多，然后不是特别吵就行'),
('05','I01-07','自报习惯','期末周图书馆座位紧张时，我会改找教学楼自习室。','期末周的时候图书馆的位置非常紧张，所以就有的时候就会去找教学楼的自习室'),
('06','I01-07','空间偏好','我选择自习室时，会考虑空调、插座和电源。','自习室里边有基本的这个空调，然后自习室里面还有插座、电源这样的设备'),
('07','I01-07','空间偏好','选择自习教室时，没有课程是我的首要条件。','没有课肯定是第一位的'),
('08','I01-07','地点偏好','教学楼离宿舍区较近，去那里自习对我更方便。','教学楼相对来说离我们宿舍区比较近，非常方便'),
('09','I01-05','信息渠道','我主要通过本科学院网站和小程序获取课表与课程通知。','一般都是通过这两个渠道'),
('10','I01-07','提醒偏好','我希望在上课前约半小时收到主动提醒。','课程开始前的半个小时左右提醒我'),
('11','I01-06','自报体验','百度地图有时会向我推送与我无关的信息。','有的时候百度地图会提醒我这个一些跟我无关的信息'),
('12','I01-08','信任依据','平时课表稳定，让我信任学校官方的课程信息。','平时课表很稳定，我信任我们学校官方的信息'),
('13','I01-08','假设情境回答','面对两小时前更新的空教室信息，我会去现场看，因为没有其他判断依据。','我会先过去看一下吧，因为我没有其他的判断依据'),
('14','I01-06','应对方式','打水小程序卡住时，我会先等，等久了再重新扫码。','我一般是先等，然后等的时间比较长之后，然后再会重新扫码'),
('15','I02-01','自报习惯','我根据课表决定出发时间：步行提前约20分钟，骑车约10分钟。','走路的话，可能要提前20分钟'),
('16','I02-02','顺利经验','我通过课表APP确认教室，认为信息准确，没有报告这次上课延误。','信息还是很准确的'),
('17','I02-03','就餐行为','菜谱不固定，我会到食堂窗口看当天有什么菜，再按口味和心情选择。','看看是不是符合自己当时的口味，当时的心情'),
('18','I02-03','信息困难','窗口文字菜单不能让我充分判断具体菜品是什么样。','不太能分辨出来它具体是什么样子的菜'),
('19','I02-03','条件性偏好','如果提前知道某个菜的队伍很长，我可能就不选它。','如果排队人数很多的话，我可能就不选这个菜了'),
('20','I02-04','现有工具经验','现有APP能查教室课程占用，我到场时课表占用信息与实际一致。','到场后，确实显示一致'),
('21','I02-04','信息困难','我能知道教室是否在上课，但很难查询其他活动的预约信息。','相关教室预约信息就基本上很难看到'),
('22','I02-06','自报经历','我偶尔遇到教室被其他活动使用，遇到后会换一间教室。','遇到过，但比较少，很少。但是遇到后确实会换教室'),
('23','I02-06','通知偏好','通知集中未必更好，我会关注重要消息，选择性忽略其他消息。','通知集中我感觉未必是好事'),
('24','I02-05','贡献意愿','我愿意提供课表，也愿意上报教室自习或活动占用情况。','遇到哪个空教室里面有活动，我也会上传到这个APP里面'),
('25','I02-06','署名偏好','上传教室状态时，我希望可以选择匿名或实名。','你可以匿名上传，也可以实名上传'),
('26','I03-02','通勤负担','中午回出租屋、下午返校，两段路各约15分钟，反复骑车让我觉得麻烦。','两段路应该都是十五分钟左右'),
('27','I03-02','行为动机','我中午回出租屋，是为了在自己的床上午休，并给手机、电脑充电。','回宿住屋的床上休息一段时间，然后给手机给电脑充电'),
('28','I03-04','顺利经验','老师一般提前半天通知调课，我通常在出发前就知道安排变化。','一般老师都会提前半天左右通知，所以都是在出发前就已经知道换了安排'),
('29','I03-04','通知困扰','群里很多与我无关的信息，会让我觉得被打扰。','很多跟我无关的无效信息，我会觉得会有点打扰'),
('30','I03-05','提醒偏好','我愿意接收紧急调课和上课前需要完成任务的提醒。','课程有什么任务要我们上课之前完成'),
('31','I03-05','信息缺口','去食堂之前，我无法提前知道当天窗口的人数和排队情况。','不能提前知道人数或者排队情况'),
('32','I03-05','自报事件','想吃的窗口队伍太长，我换了别的饭菜；没吃到想吃的让我郁闷。','想吃的东西，最后没有吃到，觉得比较郁闷'),
('33','I03-04','自报习惯','常去自习室人太多或喜欢的位置被占时，我会换自习地点。','你原来一直喜欢的位置被别人占了，你不得不换一个这个自习室坐'),
('34','I03-07','自报事件','我依据学校排班表等巴士，但实际到达比排班晚了十几分钟。','最后他实际到达慢了十几分钟'),
('35','I03-07','情境与选择','雨夜天气恶劣，我仍选择等巴士，等候约十几至二十分钟。','当时天气确实很恶劣，不得不坐校园巴士'),
('36','I03-06','条件性授权','我愿意开放课表、课程通知和位置，但希望自己决定开关与限制。','希望有自己能够决定的开关和限制'),
('37','I04-02','通勤负担','北区到教学楼或科研地点约10至15分钟，冬天骑车往返不方便。','冬天比较冷，然后非常不方便'),
('38','I04-03','交通选择','我从未坐过校园巴士，更看重自己骑电动车来去的时间自由。','没有自己骑电动车来去那么方便'),
('39','I04-03','需求差异','我有固定实验室工位，不需要另外寻找自习空间。','因为我有自己的工位，所以我不需要自习的地方'),
('40','I04-04','自报习惯','喜欢的食堂窗口排队太长时，我会换一家，也会有点不高兴。','食堂当口排队非常多，我就会换一家'),
('41','I04-04','顺利经验','研究生圈子较小，我基本没有漏看通知或被无关消息打扰的经历。','基本上没有什么漏看或者说无关信息打扰，因为研究生的圈子比较小'),
('42','I04-05','一般情境举例','课程或组会改时间后，我会用空出来的时间做自己的事，或改变去向。','那这段时间我就可以做我自己的事情'),
('43','I04-05','条件性授权','在能控制开放权限的前提下，我愿意提供广泛信息来换取便利。','如果是我能控制开放权限的话，我愿意提供基本上所有的信息'),
('44','I04-05','个人优先项','我最希望先获得食堂排队与菜单信息。','我最希望提供食堂排队与菜单信息'),
]
cards={i:{'id':'N'+i,'source':src,'participant':src[:3],'type':typ,'text':text,'excerpt':quote} for i,src,typ,text,quote in data}
for c in cards.values():assert c['excerpt'] in answers[c['source']],c
themes=[
 {'id':'A','title':'找到真正适合的学习空间','groups':[
  ('A1','课程空闲仍需核对实际活动',['20','21','22']),
  ('A2','设施与环境决定是否适合',['04','06','07']),
  ('A3','拥挤与距离促使更换地点',['05','08','33']),
  ('A4','寻找负担与固定工位需求不同',['03','39'])]},
 {'id':'B','title':'就餐选择需要及时且具体的信息','groups':[
  ('B1','到场比较菜品存在信息成本',['17','18','31']),
  ('B2','排队会改变选择及用餐感受',['19','32','40']),
  ('B3','食堂信息是个人优先项',['44'])]},
 {'id':'C','title':'日常安排受准备与往返条件影响','groups':[
  ('C1','路程预估未必包含出门准备',['01','02','14']),
  ('C2','交通方式与休息需求影响往返',['15','26','27','37']),
  ('C3','现有课表与提前通知也能奏效',['16','28'])]},
 {'id':'D','title':'交通选择同时考虑可靠性与自由','groups':[
  ('D1','排班与实际到达存在差距',['34']),
  ('D2','天气与时间自由影响交通取舍',['35','38'])]},
 {'id':'E','title':'通知价值取决于相关性与个人情境','groups':[
  ('E1','现有渠道承载课程信息',['09']),
  ('E2','消息负担与集中需求因人而异',['11','23','29','41']),
  ('E3','提醒需支持具体时间与行动',['10','30','42'])]},
 {'id':'F','title':'信息使用依赖信任与自主控制','groups':[
  ('F1','官方信任与时效判断条件不同',['12','13']),
  ('F2','共享及署名需要选择权',['25','36','43']),
  ('F3','用户愿意贡献空间状态信息',['24'])]},
]
assigned=[]
for t in themes:
 for gid,gname,ids in t['groups']:
  for i in ids:cards[i].update(theme=t['title'],theme_id=t['id'],subtheme=gname,subtheme_id=gid);assigned.append(i)
assert sorted(assigned)==sorted(cards)
assert len(cards)==44
with (OUT/'便利贴清单与出处.csv').open('w',encoding='utf-8-sig',newline='') as f:
 writer=csv.writer(f);writer.writerow(['便利贴编号','受访者','问答出处','证据性质','抄写内容','原回答摘录','上层主题草案','子主题草案'])
 for c in cards.values():writer.writerow([c[k] for k in ['id','participant','source','type','text','excerpt','theme','subtheme']])
(OUT/'亲和图数据.json').write_text(json.dumps({'status':'初步分析草案，待小组讨论及真实过程照片确认','cards':list(cards.values()),'themes':themes},ensure_ascii=False,indent=2),encoding='utf-8')

pdfmetrics.registerFont(TTFont('CN','C:/Windows/Fonts/simsun.ttc',subfontIndex=0))
pdfmetrics.registerFont(TTFont('CNHead','C:/Windows/Fonts/simhei.ttf'))
INK=colors.HexColor('#20344C');GREY=colors.HexColor('#64748B')
PC={'I01':colors.HexColor('#FFF1AF'),'I02':colors.HexColor('#DCECFB'),'I03':colors.HexColor('#DDEEDB'),'I04':colors.HexColor('#EEDFF4')}
styles={
 'title':ParagraphStyle('title',fontName='CNHead',fontSize=20,leading=28,textColor=INK,spaceAfter=12),
 'head':ParagraphStyle('head',fontName='CNHead',fontSize=15,leading=23,textColor=INK,spaceAfter=10),
 'sub':ParagraphStyle('sub',fontName='CNHead',fontSize=11,leading=17,textColor=INK,spaceBefore=7,spaceAfter=7),
 'body':ParagraphStyle('body',fontName='CN',fontSize=11,leading=17,wordWrap='CJK',spaceAfter=8),
 'small':ParagraphStyle('small',fontName='CN',fontSize=9,leading=14,wordWrap='CJK',spaceAfter=5,textColor=GREY),
 'card':ParagraphStyle('card',fontName='CN',fontSize=11,leading=17,wordWrap='CJK',spaceAfter=5),
}
story=[]
def P(t,style='body'):return Paragraph(html.escape(t).replace('\n','<br/>'),styles[style])
def add(t,style='body'):story.append(P(t,style))
add('SmartCampus+ 亲和图制作材料','title')
add('44张数据便利贴及分组草案','head')
add('本材料从4位用户的26轮访谈问答中提取44条独立信息，提供可直接抄写的短句、原回答摘录与出处。便利贴短句是忠实概括，不是逐字引语。6个上层主题和18个子主题为当前分析草案，供小组实际归类、讨论和调整。')
add('抄写与拍照顺序','sub')
for t in [
 '1. 先抄写N01至N44。每张只写编号、短句和出处，例如“N01 / 我预留10分钟去实验楼，结果比计划晚到5分钟。/ I01-02”。原回答摘录用于核对，不必全部抄写。',
 '2. 不同受访者使用不同颜色：I01黄色、I02蓝色、I03绿色、I04紫色。若颜色不足，保留受访者编号即可。颜色表示来源，不表示主题。',
 '3. 先将数据便利贴铺开、阅读并拍照，再依据内容联系进行初步分组。记录真实讨论中的调整；如果小组认可本草案，也请实际核对每组依据。',
 '4. 分组后写子主题卡，再归纳上层主题卡。44张是数据便利贴数量，主题卡另计。图顶端写分析问题，并拍摄最终实体图。',
 '5. 按实际发生的阶段保留照片：原始数据卡片、初次分组、调整过程和最终布局。每张照片说明当时做了什么；尚未发生的过程不写成已经完成。',
 '6. 将最终实体分组与数字版对齐。若小组移动或修改卡片，更新数字图后再纳入提交报告。'
]:add(t)
add('分析问题','sub');add('学生在安排上课、就餐、自习和校园出行时，依靠什么信息做决定，遇到哪些困难，以及在什么条件下愿意接受助手支持？')
add('来源与解释边界','sub');add('来源为SmartCampus_P3_作业四_修订版.docx第二部分访谈逐字稿。时间均为受访者回忆或习惯估计。N13是对假设情境的回答，N19是条件性偏好，N42是一般情境举例；不能把这些卡片都写成现场观察到的事件。N26的返校路线已由I03-03澄清。','small')

insights={
 'A':'“无课”与“当前适合自习”包含不同条件：活动占用、设施、人数、安静程度和距离都影响选择。I04已有固定工位，说明公共自习空间不是每个人的共同需求。',
 'B':'食堂选择同时受菜品可理解性、排队和个人心情影响。信息可帮助比较，但无法据此声称改善菜品口味。N19是假设提前知道排队后的条件性选择，应与N32的具体事件区分。',
 'C':'路线耗时之外还有出门准备和往返动机。I01的延误不能全部算为纯步行时间；I03的午休和充电需求也不能仅靠更短路线消除。I02和I03的顺利经验应一并保留。',
 'D':'N34描述相对排班的晚到时间，N35描述总等候及天气约束，两者不可相加作为总延误。I04从未乘坐校园巴士，其偏好不能作为实际巴士延误的第二个案例。',
 'E':'用户在消息负担、关注方式和提醒时机上存在差异。I02对集中通知持保留意见，I04未报告消息干扰，不能把统一推送作为所有人的共同需求。',
 'F':'信任官方课表与能判断空间实时状态是两回事。共享意愿带有权限、署名和用途条件，不能解释为无条件开放个人信息。N13中到现场查看源于缺乏判断依据。'
}
for t in themes:
 story.append(PageBreak());add(t['id']+' '+t['title'],'head')
 for gid,gname,ids in t['groups']:
  add(gid+' '+gname,'sub')
  for i in ids:
   c=cards[i]
   block=[P(c['id']+'  '+c['text'],'card'),P(c['source']+'  |  '+c['type']+'  |  原回答：“'+c['excerpt']+'”','small')]
   story.append(KeepTogether(block))
 add('本组分析','sub');add(insights[t['id']])

story.append(PageBreak());add('分组核对与分析总结','head')
for t in themes:
 ids=[i for _,_,arr in t['groups'] for i in arr]
 add(t['id']+' '+t['title']+'（'+str(len(ids))+'张）：'+ '、'.join(cards[i]['id'] for i in ids),'body')
add('主题之间的关系','sub')
add('A和B关注地点与服务状态。C和D关注活动衔接及出行约束。E和F关注信息接收、信任和控制。六组主题共同回答：如何在具体情境中作出可执行的校园安排？')
add('可用于报告的访谈分析总结','sub')
add('对四位受访者的访谈进行提取与初步归类后，可以看到学习空间、就餐选择、出行安排、通知和数据使用之间的联系。用户关心的不只是是否有信息，还包括信息能否反映实际可用状态、是否符合当下任务，以及自己能否选择接收和共享方式。出乎预期的是，现有课表和提前通知对部分用户已经有效，有固定工位的研究生也没有找公共自习空间的需求；通知集中同样未得到一致认可。因而后续方案应围绕具体情境验证空间与食堂信息，并保留准备缓冲、个人提醒和数据控制。以上为当前草案的分析，最终提交时需与小组实际确认后的分组一致。')
add('待补齐的提交材料','sub');add('实体制作与讨论的真实照片、照片对应的过程说明、按最终布局更新的数字图，以及本次分析各部分的实际撰写和审阅贡献。当前材料未声称已完成小组讨论或照片记录。')

def footer(c,doc):
 c.setFont('CN',8);c.setFillColor(GREY);c.drawString(50,28,'SmartCampus+  亲和图制作材料');c.drawRightString(545,28,str(doc.page))
SimpleDocTemplate(str(OUT/'亲和图_便利贴清单与制作指南.pdf'),pagesize=(595.28,841.89),leftMargin=50,rightMargin=50,topMargin=44,bottomMargin=45,title='SmartCampus+ 亲和图便利贴清单与制作指南').build(story,onFirstPage=footer,onLaterPages=footer)

# A scalable, code-native hierarchy. The diagram is explicitly a proposed grouping.
W=1860;PANEL=590;GAP=25;M=20
def wrap(t,font,size,width):
 lines=[];cur=''
 for ch in t:
  if pdfmetrics.stringWidth(cur+ch,font,size)>width and cur:
   if ch in '，。；：！？、）》】”’%':cur+=ch
   else:lines.append(cur);cur=ch
  else:cur+=ch
 if cur:lines.append(cur)
 return lines
def panelheight(t):
 h=56
 for gid,gname,ids in t['groups']:
  h+=34
  for i in range(0,len(ids),2):h+=max(88,max(22+len(wrap(cards[j]['text'],'CN',12,256))*18+23 for j in ids[i:i+2]))+12
 return h+16
# Three columns, two rows; each row uses its tallest panel.
heights=[panelheight(t) for t in themes];rh=[max(heights[:3]),max(heights[3:])]
H=180+rh[0]+rh[1]+35
d=Drawing(W,H)
d.add(Rect(0,0,W,H,fillColor=colors.white,strokeColor=None))
def text(x,y,t,size=12,font='CN',fill=INK):d.add(String(x,y,t,fontName=font,fontSize=size,fillColor=fill))
text(M,H-32,'SmartCampus+ 访谈亲和图',24,'CNHead')
text(M,H-58,'初步分组草案  |  44张数据卡片  |  6个上层主题  |  18个子主题  |  待小组实际讨论与照片确认',12)
text(M,H-81,'问题：学生如何利用信息安排上课、就餐、自习和出行，遇到什么困难，并在什么条件下接受助手支持？',12)
for k,pid in enumerate(PC):
 x=M+k*170;d.add(Rect(x,H-112,14,14,fillColor=PC[pid],strokeColor=colors.HexColor('#CFD6DF'),strokeWidth=.5));text(x+20,H-110,pid+' 访谈来源',11)
for k,t in enumerate(themes):
 row=k//3;col=k%3;x=M+col*(PANEL+GAP);top=H-145-(rh[0]+25 if row else 0);height=heights[k]
 d.add(Rect(x,top-height,PANEL,height,fillColor=colors.HexColor('#F8FAFC'),strokeColor=colors.HexColor('#CFD8E3'),strokeWidth=1))
 d.add(Rect(x,top-42,PANEL,42,fillColor=INK,strokeColor=None));text(x+14,top-27,t['id']+' '+t['title'],17,'CNHead',colors.white)
 y=top-56
 for gid,gname,ids in t['groups']:
  text(x+14,y-15,gid+' '+gname,13,'CNHead');y-=34
  for z in range(0,len(ids),2):
   pair=ids[z:z+2];ch=max(88,max(22+len(wrap(cards[j]['text'],'CN',12,256))*18+23 for j in pair))
   for ci,j in enumerate(pair):
    c=cards[j];cx=x+14+ci*284;d.add(Rect(cx,y-ch,274,ch,rx=3,ry=3,fillColor=PC[c['participant']],strokeColor=colors.HexColor('#CDD5DF'),strokeWidth=.5))
    text(cx+9,y-17,c['id']+'  '+c['source'],10,'CNHead')
    for li,line in enumerate(wrap(c['text'],'CN',12,256)):text(cx+9,y-37-li*18,line,12)
    text(cx+9,y-ch+9,c['type'],9,fill=GREY)
   y-=ch+12
text(M,16,'短句为访谈概括，逐字摘录见配套清单。颜色表示受访者来源；主题关系与卡片位置为分析草案。',11)
svg=renderSVG.drawToString(d).replace('font-family: CNHead','font-family: SimHei').replace('font-family: CN','font-family: SimSun')
(OUT/'亲和图_数字分组草案.svg').write_text(svg,encoding='utf-8')
renderPDF.drawToFile(d,str(OUT/'亲和图_数字分组草案.pdf'))
print(json.dumps({'cards':len(cards),'sources':dict(Counter(c['participant'] for c in cards.values())),'subthemes':sum(len(t['groups']) for t in themes),'svg_size':[W,H]},ensure_ascii=False))
