"""Author the report with the bundled python-docx runtime."""
from pathlib import Path
import csv,json
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[1];ASSET=ROOT/'report_work/assets'
OUT=ROOT/'TrustSVD论文复现实验报告.docx'
stats=json.loads((ASSET/'stats.json').read_text(encoding='utf8'))
def read(p):
    with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
rows=read(ROOT/'results/combined_report/three_datasets.csv')
DS=['filmtrust','epinions','ciao'];NAMES={'filmtrust':'FilmTrust','epinions':'Epinions','ciao':'Ciao'}
MODELS=['UserAvg','ItemAvg','PMF','RSTE','SoRec','SoReg','SocialMF','TrustMF','SVD++','TrustSVD']
def result(ds,m='TrustSVD',d=10,v='all'):
    return next(r for r in rows if r['dataset']==ds and r['model']==m and int(r['dim'])==d and r['view']==v)
def f(x,n=4):return f'{float(x):.{n}f}'

doc=Document();sec=doc.sections[0]
sec.page_width=Cm(21);sec.page_height=Cm(29.7)
sec.top_margin=Cm(2.0);sec.bottom_margin=Cm(1.9);sec.left_margin=Cm(2.25);sec.right_margin=Cm(2.25)
sec.footer_distance=Cm(.8)
def font(style,name,size,bold=False):
    s=doc.styles[style];s.font.name=name;s.font.size=Pt(size);s.font.bold=bold;s.font.color.rgb=RGBColor(0,0,0)
    s.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),name)
    s.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:ascii'),'Calibri')
    s.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:hAnsi'),'Calibri')
    return s
n=font('Normal','宋体',10.5);n.paragraph_format.line_spacing=1.32;n.paragraph_format.space_after=Pt(6);n.paragraph_format.first_line_indent=Pt(21)
t=font('Title','黑体',24,True);t.paragraph_format.space_after=Pt(13);t.paragraph_format.first_line_indent=Pt(0)
font('Subtitle','宋体',13).font.italic=False
for style in doc.styles:
    if style.type == 1:
        pp=style.element.find(qn('w:pPr'))
        if pp is not None:
            for border in list(pp.findall(qn('w:pBdr'))):pp.remove(border)
for sty,size in [('Heading 1',17),('Heading 2',13)]:
    s=font(sty,'黑体',size,True);s.paragraph_format.space_before=Pt(11);s.paragraph_format.space_after=Pt(9);s.paragraph_format.first_line_indent=Pt(0)
    # Explicitly disable inherited heading numbering.
    pp=s.element.get_or_add_pPr();np=OxmlElement('w:numPr');ni=OxmlElement('w:numId');ni.set(qn('w:val'),'0');np.append(ni);pp.append(np)
cap=font('Caption','宋体',9);cap.paragraph_format.first_line_indent=Pt(0);cap.paragraph_format.space_before=Pt(3);cap.paragraph_format.space_after=Pt(8)
footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER;footer.paragraph_format.first_line_indent=Pt(0)
r=footer.add_run();fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');r._r.addnext(fld)
doc.core_properties.title='TrustSVD 论文复现实验报告';doc.core_properties.subject='独立实现与三个数据集实验分析';doc.core_properties.author='';doc.core_properties.keywords='TrustSVD 社交推荐 论文复现'
def para(text,bold=False):
    p=doc.add_paragraph();p.add_run(text).bold=bold;return p
def heading(s):return doc.add_heading(s,1)
def sub(s):return doc.add_heading(s,2)
def page(title):
    p=heading(title);p.paragraph_format.page_break_before=True
def caption(s):
    p=doc.add_paragraph(s,'Caption');p.alignment=WD_ALIGN_PARAGRAPH.CENTER;return p
def pic(name,width=16.2,caption_text=None):
    p=doc.add_paragraph();p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.space_after=Pt(1)
    p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    shape=p.add_run().add_picture(str(ASSET/(name+'.png')),width=Cm(width))
    shape._inline.docPr.set('descr',caption_text or name)
    if caption_text:p.paragraph_format.keep_with_next=True;caption(caption_text)
def table(headers,data,widths=None,size=9.3,highlight=None):
    tb=doc.add_table(rows=1,cols=len(headers));tb.alignment=WD_TABLE_ALIGNMENT.CENTER;tb.autofit=False
    widths=widths or [16.2/len(headers)]*len(headers)
    for c,w in zip(tb.columns,widths):c.width=Cm(w)
    pr=tb._tbl.tblPr
    borders=OxmlElement('w:tblBorders')
    for side in ['top','left','bottom','right','insideH','insideV']:
        e=OxmlElement('w:'+side);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
    pr.append(borders)
    for i,values in enumerate([headers]+data):
        row=tb.rows[0] if i==0 else tb.add_row()
        if i==0:
            repeat=OxmlElement('w:tblHeader');repeat.set(qn('w:val'),'true');row._tr.get_or_add_trPr().append(repeat)
        cant=OxmlElement('w:cantSplit');row._tr.get_or_add_trPr().append(cant)
        for j,(cell,val,w) in enumerate(zip(row.cells,values,widths)):
            cell.width=Cm(w);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cp=cell._tc.get_or_add_tcPr();sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'DFEAF0' if i==0 else 'F3F6F8' if i%2==0 else 'FFFFFF');cp.append(sh)
            mar=OxmlElement('w:tcMar')
            for side in ['top','left','bottom','right']:
                e=OxmlElement('w:'+side);e.set(qn('w:w'),'80');e.set(qn('w:type'),'dxa');mar.append(e)
            cp.append(mar)
            p=cell.paragraphs[0];p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.space_before=Pt(1);p.paragraph_format.space_after=Pt(1);p.paragraph_format.line_spacing=1.13
            p.alignment=WD_ALIGN_PARAGRAPH.LEFT if j==0 else WD_ALIGN_PARAGRAPH.CENTER
            r=p.add_run(str(val));r.font.size=Pt(size);r.bold=i==0 or (highlight is not None and i>0 and values[0] in highlight)
    spacer=doc.add_paragraph();spacer.paragraph_format.line_spacing=Pt(2);spacer.paragraph_format.space_after=Pt(4);spacer.paragraph_format.first_line_indent=Pt(0)
    return tb
def code(lines):
    p=doc.add_paragraph();p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.line_spacing=1.1;p.paragraph_format.space_before=Pt(4);p.paragraph_format.space_after=Pt(8)
    r=p.add_run(lines);r.font.name='Consolas';r.font.size=Pt(8.5)
    return p

# Opening page: evidence and scope, no decorative cover or numbered headings.
p=doc.add_paragraph('TrustSVD 论文复现实验报告','Title')
p=doc.add_paragraph('评分与社会信任联合建模','Subtitle');p.paragraph_format.first_line_indent=Pt(0)
for r in p.runs:r.font.color.rgb=RGBColor(0,0,0);r.font.size=Pt(13)
p=doc.add_paragraph('实验日期  2026年10月26日');p.paragraph_format.first_line_indent=Pt(0)
heading('摘要')
para('本实验复现 Guo、Zhang 与 Yorke-Smith 在 AAAI 2015 发表的 TrustSVD。该方法在矩阵分解中同时使用用户给出的分数、评价过哪些物品，以及信任哪些用户，尝试改善数据稀疏和冷启动条件下的评分预测。实现依据论文公式独立编写，未读取或复制作者及其他现成模型的实现代码。')
para('实验在 FilmTrust、Epinions 和 Ciao 上完成 10 个模型、两种隐向量维度和五折交叉验证，共得到 300 组真实评估结果。18 项数学与隔离测试通过，300 组结果文件的指标重算、划分检查和相应模型重载检查通过。下表列出 TrustSVD 在全部测试评分上的五折均值。')
table(['数据集','维度','MAE','RMSE'],[[NAMES[ds],str(d),f(result(ds,d=d)['mae_mean'],6),f(result(ds,d=d)['rmse_mean'],6)] for ds in DS for d in [5,10]],[4.4,2.3,4.7,4.8],size=10)
para('本次六组 All 视图比较中，TrustSVD 的平均 RMSE 均略高于 SVD++，因此没有重现论文所报告的整体领先结论。FilmTrust 与 Epinions 的四项输入规模与论文一致；Ciao 使用可获得的原始版本，经过评分范围检查后有 284,052 条评分，与论文的数据规模不同。Flixster 未纳入本次实验。')
para('本报告依次说明模型原理、公式与代码的对应关系、数据处理和实验设置，并结合真实图表分析结果。实验完成意味着实现和运行过程可核查，不等于已经逐项重现原论文的数值与结论。')

page('研究问题与模型思路')
para('传统协同过滤从已有评分推断用户口味，再预测用户尚未评价的物品。问题在于，大多数用户只评价很少的物品，用户与物品之间缺乏足够的共同观察。社会信任提供另一条线索：即使一个用户评价不多，也可能指定一些可信用户，其行为能够补充这个用户的偏好信息。')
para('TrustSVD 将“给了几分”视为显式反馈，将“评价过什么”和“信任了谁”视为隐式反馈。隐式反馈表达关联关系，本身不保证用户喜欢该物品，也不等于把朋友的评分简单取平均。模型将这些关系映射为可学习的向量，并与目标物品向量匹配。')
pic('model_flow',16.2,'TrustSVD 的信息流与联合训练关系  根据论文预测式和本项目实现绘制')
table(['符号','含义','在模型中的作用'],[
 ['P 与 pᵤ','用户的显式偏好向量','描述用户口味并参与信任重建'],
 ['Q 与 qⱼ','目标物品向量','与用户综合表示进行内积'],
 ['Y 与 yᵢ','物品历史的隐式因子','汇总用户评价过的物品'],
 ['W 与 wᵥ','受信任用户因子','汇总可信邻居并解释信任边'],
 ['μ 与 bᵤ 和 bⱼ','训练均值及用户物品偏置','解释整体水平与打分习惯'],
 ['Iᵤ 与 Tᵤ','训练评分历史与出向信任邻域','确定隐式聚合范围和归一化系数']],[2.8,5.4,8.0])
para('与 SVD++ 相比，TrustSVD 增加了信任邻域的隐式影响，以及对观察到的信任边的重建约束。两者共享用户因子和受信任用户因子，使评分预测和信任重建相互影响。论文的核心假设是：这种额外信息能够补足评分稀疏造成的不足。')

page('论文公式与计算实现')
para('设 μ 为当前训练集评分均值，bᵤ 与 bⱼ 分别为用户、物品偏置。TrustSVD 的评分预测由基础偏好、评价历史和可信邻居三部分构成，公式如下。Iᵤ 仅包含当前训练集中的不同物品，Tᵤ 表示用户发起的信任关系。')
pic('eq_prediction',16.2)
para('两个隐式求和项分别除以邻域大小的平方根，降低历史长度和信任度不同带来的尺度差异。空邻域的贡献定义为零。信任边的预测为 pᵤ 与 wᵥ 的内积，只对已经观察到的评分和正信任边计算误差，不把缺失关系当作零分或不信任。')
pic('eq_objective',16.2)
para('ΩR 和 ΩT 分别为观察评分和信任边集合。λₜ 控制显式信任重建项，dθ 表示按实体频次加权的正则系数。对用户因子 P 的权重为 λ/√|Iᵤ| 加 λₜ/√|Tᵤ|；Q、Y 与物品被评价人数的逆平方根相关，W 与受信任入度的逆平方根相关。用户和物品偏置也进行加权正则。')
para('实现遵循原文 Eq. (1) 的全局加权正则：每个参数的惩罚在完整目标中累加一次。论文末尾 W 的正则项排版未显式写出求和，本实现对所有受信任用户求和，与原文梯度式的解释一致。整个目标及梯度统一除以训练评分条数，该缩放不改变目标的最优点。')
sub('使用稀疏聚合计算梯度')
para('定义 N 和 S 为归一化评分历史矩阵、信任邻接矩阵，则用户综合表示为 H。令 E 为按用户物品位置累积的评分残差，F 为信任残差，G 是传回用户综合表示的梯度。以下关系把逐条评分的邻域求和写成稀疏矩阵乘法。')
pic('eq_gradient',15.6)
pic('eq_gradient_w',12.2)
para('objectives.py 中的 effective 构造 H，rating_loss_grad 计算评分残差及梯度，edge_loss_grad 计算信任误差，value_grad 汇合梯度与正则。重复用户物品观察在损失中逐条计数，在回传时累积残差；不能先把评分相加再平方。该聚合方式减少重复遍历，单次目标与梯度计算约随“评分数加信任边数”乘维度线性增长。')

page('数据来源与预处理')
para('FilmTrust 来自论文作者维护的数据页面，Epinions 使用公开镜像保存的 665K 版本。Ciao 从作者原站的历史压缩包恢复。三个输入均包含评分与正信任边，信任有方向；用户映射使用评分和信任两部分出现的用户并集，因此模型中的用户总数可能大于有评分的用户数。')
table(['数据集','评分用户','物品','评分记录','信任边'],[[NAMES[ds]]+[f'{v:,}' for v in stats['datasets'][ds]['counts']] for ds in DS],[3.2,3.0,3.0,3.5,3.5],size=9.7)
table(['数据集','评分范围','用户并集','与论文四项规模一致'],[[NAMES[ds],'.5–4.0' if ds=='filmtrust' else '1–5',f"{stats['datasets'][ds]['user_union']:,}",'是' if stats['datasets'][ds]['matches_paper'] else '否'] for ds in DS],[3.2,3.1,4.3,5.6],size=9.7)
sub('Ciao 数据版本说明')
para('恢复的 Ciao 原始包含 284,086 条评分、7,375 名评分用户、105,114 个物品和 111,781 条信任边。原始评分中有 34 条零分，超出所声明的 1–5 分范围。剔除这些记录后，实际实验保留 284,052 条评分、105,096 个物品，全部信任边保留。没有为了凑出论文规模而抽样或删去其他评分。')
table(['版本','评分数','不同物品数','信任边数'],[
 ['论文 Table 1','280,391','99,746','111,781'],['原始公开包','284,086','105,114','111,781'],['本次有效输入','284,052','105,096','111,781']],[5.2,3.6,3.7,3.7])
para('Ciao 的版本差异意味着与论文对照的分差同时受数据和实现设置影响，不能直接解释为模型准确度提高或下降。FilmTrust 和 Epinions 的规模核对一致，也不等于已恢复论文当年的原始随机划分。')
sub('重复观察与划分边界')
para('FilmTrust 存在 3 条额外重复用户物品观察，Ciao 有 1,433 条。实验保留这些有效观察，但以用户物品对为组分配折号，使同一对的全部记录只落入同一折。这样避免模型在训练中已经见过同一对评分，却又在测试中预测该对的泄漏。隐式历史按不同物品去重，统计分析中对重复评分取平均。')
para('所有输入文件均保存 SHA256。Ciao 原始文件、转换规则和转换后校验值保存在 datasets/ciao/preparation.json；每组实验 JSON 同时记录评分与信任文件的哈希，保证后续核对使用的是同一份输入。')

page('复现代码结构与正确性验证')
para('项目使用 NumPy、SciPy 的数组与稀疏矩阵功能，以及 Numba 加速自行编写的循环。主实验的优化器由本项目独立实现，没有导入推荐算法库中的模型。已发布数值单独存放在 paper_reference.py，仅供报告对照；训练模块不读取该文件。')
table(['文件','主要职责','对应的复现要点'],[
 ['data.py','读取映射 规模核对 分组五折','记录数据版本与校验值'],
 ['objectives.py','模型前向 目标函数 解析梯度','实现论文预测式和联合损失'],
 ['optimizers.py','全批次梯度下降与步长搜索','Armijo 回溯和 BB 标量步长'],
 ['experiment.py','内部验证 完整训练 外层测试','只用验证集选择迭代数'],
 ['report.py','表格 图形 冷启动与分组分析','分开保存原文与实际结果'],
 ['audit.py','逐条预测重算与模型重载','检查划分 指标及预测一致性'],
 ['tests/test_math.py','数学与隔离测试','梯度 前向 损失及泄漏检查']],[3.3,6.0,6.9],size=9.1)
sub('从代码理解隐式影响')
para('以下语句摘自 effective 和 value_grad。Hr 与 Ht 分别对应前文 N 与 S；h 是用户最终用于预测的表示。评分误差的梯度通过转置矩阵回到 Y 和 W，而 W 还会收到信任重建任务的梯度。')
code("h = z['p'].copy()\nh += self.Hr @ z['y']\nh += self.Ht @ z['w']\ng['y'] = self.Hr.T @ gh\ng['w'] = self.Ht.T @ gh")
para('测试集中的评分不会进入训练均值、隐式历史、目标函数或梯度。测试通过改变被留出评分的数值，验证训练损失与梯度保持不变；另用直接遍历邻域的计算对照稀疏聚合结果。')
para('18 项测试包括八种可训练模型的中心差分梯度检查、TrustMF 反向角色梯度、TrustSVD 完整目标逐项对照、空邻域处理、冷用户信任梯度、重复对分组与指标计算。差分检查使用小型可控数据，验证公式与代码的局部一致性；它不能证明训练设置已经与原作者完全相同。')

page('实验设置与评估方法')
para('每个数据集执行五折交叉验证，四折训练、一折测试，轮流得到五次结果。所有模型共享相同外层折。外层训练数据再划出 10% 作为内部验证，每 5 次迭代检查验证 RMSE，连续 5 次检查无改善时停止选择；随后从相同初始化在完整四折上重训所选迭代次数。测试集不参与选择。')
pic('eq_metrics',14.8)
para('MAE 表示平均偏差多少分，RMSE 对较大的预测错误惩罚更重，均为越低越好。报告采用五个外层折的算术平均，并保存折间样本标准差。All 包含全部测试评分；Cold Start 主定义为训练评分条数少于 5，同时报告按全量评分条数少于 5 的另一口径。两种口径的样本不同，不能混为一列。')
table(['数据集','TrustSVD λ','TrustSVD λₜ','SVD++ λ'],[['FilmTrust','1.2','0.9','0.1'],['Epinions','0.9','0.5','0.35'],['Ciao','0.5','1.0','0.1']],[4.2,4,4,4],size=10)
para('维度取 5 和 10，主种子为 20261026；向量按均值 0、标准差 0.05 的正态分布初始化，偏置为零。主训练使用独立编写的全批次梯度下降，最多 200 次迭代，Armijo 回溯保证接受步下降，BB 标量步长提供下一次搜索起点。全部预测裁剪到合法评分范围，并另存未裁剪值。')
sub('对比方法与实现约定')
table(['方法','用于比较的主要机制'],[
 ['UserAvg 与 ItemAvg','用户均分或物品均分 无观察时退回训练均值'],
 ['PMF','概率矩阵分解 实验采用 sigmoid 并映射评分范围'],
 ['RSTE 与 SoRec','分别使用社会信任集成与评分信任联合分解'],
 ['SoReg 与 SocialMF','分别约束相连用户偏好与可信邻居平均偏好'],
 ['TrustMF','分别训练信任者与受信任者模型 再组合向量'],
 ['SVD++ 与 TrustSVD','分别利用评价历史 以及评价历史与社会信任']],[4.3,11.9],size=9.3)
para('SoReg 的相似度只由训练评分计算，PCC 映射至 [0,1]；无共同评分或零方差时置零。SVD++ 使用按观察频次累计的标准 L2 正则，TrustSVD 使用原文全局逆平方根正则。实验在 CPU 上运行，不依赖 GPU、PyTorch 或 CUDA。实际版本为 Python 3.12.7、NumPy 1.26.4、SciPy 1.13.1、Numba 0.60.0、Matplotlib 3.9.2。')

page('所有模型的评分预测结果')
para('下表为 All 视图的五折平均结果，每格依次为 MAE 和 RMSE。所有数值来自保存的实际预测，保留四位小数。SVD++ 与 TrustSVD 加粗便于对照；表中不填入论文分数。Ciao 为本次可获得版本。')
for d,title in [(5,'五维隐向量'),(10,'十维隐向量')]:
    sub(title)
    table(['模型','FilmTrust\nMAE / RMSE','Epinions\nMAE / RMSE','Ciao\nMAE / RMSE'],[[m]+[f"{f(result(ds,m,d)['mae_mean'])} / {f(result(ds,m,d)['rmse_mean'])}" for ds in DS] for m in MODELS],[3,4.4,4.4,4.4],size=9.1,highlight={'SVD++','TrustSVD'})

page('整体性能与论文结果对照')
pic('all_models',16.2,'十维实验的五折平均 RMSE  误差线为折间样本标准差  各面板横轴范围不同')
para('三个数据集上，SVD++ 和 TrustSVD 的误差均明显低于本次多数其他可训练基线。部分社会模型的误差较大；这反映的是当前实现与训练流程的实测表现，不能据此否定这些方法在原论文条件下的有效性。尤其 Ciao 有较多测试物品未在训练中出现，后文给出诊断。')
pic('paper_comparison',16.2,'TrustSVD 与 SVD++ 实测结果及 TrustSVD 原文结果  Ciao 的数据版本不同')
para('FilmTrust 的 TrustSVD RMSE 为 0.802401 与 0.807112，原文为 0.789 与 0.787；Epinions 为 1.054978 与 1.055690，原文为 1.043 与 1.044；Ciao 为 0.965598 与 0.966041，原文为 0.955 与 0.956。六组实测值均高于相应原文值。')
para('在相同数据与划分内，TrustSVD 相对 SVD++ 的平均 RMSE 差为正：FilmTrust 分别约 0.000280、0.006752，Epinions 约 0.006360、0.007413，Ciao 约 0.009231、0.012793。当前结果没有重现“TrustSVD 整体优于 SVD++”这一核心实验结论。')

page('冷启动用户的预测表现')
para('冷启动分析关注训练反馈较少的用户。按训练评分数筛选，符合真实预测时只知道训练历史的使用条件；按全量评分数筛选，则更接近对原始用户活跃度进行分层。原文未明确计数发生在划分前还是划分后，因此保留两种口径，避免选择更有利的定义。')
pic('cold_start',16.2,'十维实验的全部用户与两种冷启动口径  柱高为五折平均 RMSE')
data=[]
for ds in DS:
    for v,name in [('cold_train_lt5','训练少于5条'),('cold_total_lt5','全量少于5条')]:
        a=result(ds,'TrustSVD',10,v);b=result(ds,'SVD++',10,v)
        data.append([NAMES[ds],name,f"{int(a['test_observations']):,}",f(a['rmse_mean']),f(b['rmse_mean'])])
table(['数据集','筛选口径','测试观察数','TrustSVD RMSE','SVD++ RMSE'],data,[2.5,3.7,3.1,3.5,3.4],size=9.2)
para('表中的测试观察数是五折合计的评分条数，不是冷启动用户人数，也不是训练条数。对某个测试样本，用户是否冷启动取决于对应折的训练集，因此两种口径产生不同的样本集合。Ciao 按全量口径仅有 8 条测试评分，结果对个别样本高度敏感，不宜据此作稳定的性能排序。')
para('冷启动分数需要在相同口径内比较。某一冷启动子集上的 RMSE 低于 All 并不矛盾，可能与被筛选样本的评分分布和难度有关，不能解释为冷启动问题天然更容易。对本次结果的合理结论，应以表中各数据集的实测比较为准，不直接套用原文的领先结论。')

page('信任信息与评分偏好的关系')
para('论文先分析社会信任是否能够补充评分。本实验在完整输入上重建这项描述性分析：对每个用户，将其评分与可信邻居在相同物品上的平均评分配对，再计算 Pearson 相关系数。只使用邻居实际评价过的共同物品；样本不足或方差为零时记为无效，不用零分填补缺失。该分析不参与参数选择。')
pic('correlations',16.2,'用户评分与可信邻居平均评分的相关性分布  仅统计能够定义 PCC 的用户')
table(['数据集','有效用户数','实测平均 PCC','论文平均 PCC'],[[NAMES[ds],f"{stats['correlations'][ds]['n']:,}",f(stats['correlations'][ds]['mean'],6),{'filmtrust':'0.183','epinions':'0.446','ciao':'0.322'}[ds]] for ds in DS],[4.1,4.0,4.0,4.1],size=9.8)
para('FilmTrust 的实测均值 0.182785、Epinions 的 0.446293 与论文给出的三位小数一致，说明这一描述性现象得到较好重建。Ciao 为 0.323948，与论文 0.322 接近，但输入版本不同。相关性为正说明存在可利用的统计关联，不代表加入信任项必然降低测试误差。')
pic('coverage',16.2,'不同评分历史长度下发起过信任的用户比例  展示历史长度不超过100的区间')
para('信任覆盖图说明评分历史长度与是否提供社会关系之间存在结构差异。每个点对应同一历史长度的一组用户；样本很少的组可能产生较大波动，因此不能把散点直接解释为严格的单调关系或因果效应。')

page('不同信任度用户的分组结果')
para('按论文的七档区间，将用户发起的信任边数划分为 1–5、6–10、11–20、21–40、41–100、101–500 和大于 500，比较 d＝10 时的测试 RMSE。每档先在各折内计算误差，再对有样本的折取平均。没有出向信任边的用户不在这七档中，但已包含在 All 结果中。')
pic('trust_degree',15.5,'不同信任度的实际评分误差  三个面板纵轴范围不同  来源为逐条测试预测')
para('图中比较 RSTE、SoRec、SoReg、SocialMF、TrustMF 和 TrustSVD，与原文图示的模型范围一致。当前 TrustSVD 曲线通常低于这些社会模型，但该图没有 SVD++，因此它不能证明 TrustSVD 优于 SVD++。All 视图中两者的对照已在前文单独报告。')
para('信任度较高也未必持续降低误差。分档改变了用户组成、评分历史和测试样本量，末端区间的样本更少；某档中观察到的下降只能视为该子集上的现象。完整档位观察数与有效折数保存在 figure2_trust_degree.csv，便于进一步检查。')

page('训练过程与结果复核')
para('下面展示各数据集 d＝10、外层第一个折的 TrustSVD 实际轨迹。左图为完整外层训练集上的重训目标，右图为迭代选择阶段的内部验证 RMSE。两图属于不同训练阶段，不能将它们拼成一次连续训练，也不能把左图目标值与右图 RMSE 直接比较。')
pic('training_trace',16.2,'TrustSVD 保存的真实训练轨迹  左图纵轴为对数刻度  不同数据集目标值不可直接排名')
table(['数据集','示例所选迭代数','该任务耗时 秒'],[[NAMES[ds],str(stats['trace_info'][ds]['selected']),f(stats['trace_info'][ds]['seconds'],1)] for ds in DS],[5.2,5.5,5.5],size=10)
para('Armijo 回溯检查每个接受步的目标值下降；保存的检查点也通过非递增检查。目标下降只说明求解器在降低当前目标，不能保证找到全局最优，也不能保证测试指标提升。重训到所选迭代预算的停止记录，不应直接等同于“已经收敛”或“训练失败”。')
table(['复核内容','核对方式','结果'],[
 ['外层划分','核对测试索引及同一用户物品对是否跨折','通过'],
 ['内部验证隔离','核对训练验证并集及其与测试的交集','通过'],
 ['指标重算','从逐条预测重算 MAE RMSE 与冷启动分数','通过'],
 ['预测合法性','检查有限值与合法评分范围','通过'],
 ['TrustSVD 模型重载','重建目标并从保存参数还原测试预测','通过'],
 ['任务完整性','核对数据集 模型 维度 折号的笛卡尔积','300组齐全']],[3.4,10.0,2.8],size=9.2)
para('FilmTrust、Epinions 的 200 组任务与 Ciao 的 100 组任务分别保存独立 manifest 和 audit。所有检查均无错误、无缺失任务。这个结果证明保存产物与本项目约定一致，仍不能代替与作者原始数据划分和训练设置的逐项对齐。')

page('差异分析与实验结论')
para('当前最明确的差异来自数据版本、训练细节和未见实体处理。原文给出了模型、维度及主要正则系数，但没有提供可直接复用的折文件、随机种子、完整初始化和停止设置。本次采用内部验证与全批次步长搜索，是可记录、可重跑的实现选择，并非已恢复作者当年的训练轨迹。')
table(['数据集','训练未见物品的测试评分','占全部测试评分'],[[NAMES[ds],f"{stats['sparsity'][ds]['unseen_item_test_n']:,}",f"{100*stats['sparsity'][ds]['unseen_item_test_n']/stats['sparsity'][ds]['test_n']:.2f}%"] for ds in DS],[4.2,7.0,5.0],size=10)
para('表中“训练未见物品”按每个测试样本所属折判断。它们占 Epinions 的约 13.32%，占 Ciao 的约 26.40%，因此相关边界处理可能明显影响误差。主表统一按各模型公式输出后裁剪；另外保存“对训练未见物品回退训练均值”的敏感性分析，但未用该分析替换主表、选择参数或声称达到论文结果。')
sub('与 SVD++ 的配对比较')
table(['数据集','维度','RMSE 平均差','双侧 p 值'],[[NAMES[r['dataset']],r['dim'],f(r['mean_difference'],6),f(r['p_two_sided'],6)] for r in stats['paired']],[4.2,2.5,5.0,4.5],size=9.5)
para('差值定义为 TrustSVD 减 SVD++，正值表示 TrustSVD 误差更大。检验以五个外层折 RMSE 为配对单位，p 值未经多重比较校正；交叉验证各折训练数据重叠，不能将其视为完全独立的重复实验。这里将检验作为描述性辅助证据，不恢复原文未说明的检验单位，也不把不显著解释为等效。')
sub('结论与可继续开展的工作')
para('本实验完成了 TrustSVD 及主要对比模型的独立实现，在三个数据集上得到可重算的 300 组结果，并较好重建了 FilmTrust、Epinions 中用户评分与可信邻居平均评分的相关性。当前模型准确度与论文仍有差距，TrustSVD 相对 SVD++ 的整体优势未被重现。Ciao 的数据版本差异也限制了原文数值比较。')
para('后续工作可在固定外层测试集的前提下，补充只使用训练内部验证的步长和初始化敏感性实验，检查部分基线的训练表现，并分别讨论未见用户与未见物品的预测策略。只有这些差异得到控制，才适合进一步判断模型结论能否稳定重现；不应为了得到论文分数反复查看测试结果来调参。')

page('复跑入口与资料来源')
para('项目以 requirements-lock.txt 固定实际库版本，模型不需要 GPU。主结果目录 results/gradient_descent 保存 FilmTrust 与 Epinions；results/ciao_original_gd 保存本次 Ciao 实验。results/combined_report/three_datasets.csv 汇合三个数据集的模型、视图、均值、标准差及论文对照字段。')
para('在项目根目录运行以下命令，可重新生成 Ciao 输入并续跑已有任务、重建图表和复核结果。改变数据、参数或算法时，应改用新的运行目录，避免把不同设置的输出混在一起。')
code(".\\run_ciao.ps1\nD:\\anaconda\\python.exe -m trustsvd_repro.report --run gradient_descent\nD:\\anaconda\\python.exe scripts/summarize_results.py")
para('每组任务 JSON 记录参数、数据哈希、训练轨迹与停止原因；NPZ 保存测试索引、真实评分和预测。TrustSVD 另存模型参数。原文数值集中在 paper_reference.py，实际预测集中在各任务 NPZ 和 JSON，两者有清晰的数据来源边界。Fang 方法只保留原文转引的表格对照，没有将其已发表分数当作本项目训练结果。')
sub('论文与方法资料')
refs=[
 'Guo G, Zhang J, Yorke-Smith N. TrustSVD: Collaborative Filtering with Both the Explicit and Implicit Influence of User Trust and of Item Ratings. AAAI, 2015, 123–129. 主要依据为预测式、Eq. (1) 与 Eq. (2)、Table 1–3、Figure 1–2。',
 'Koren Y. Factorization Meets the Neighborhood: A Multifaceted Collaborative Filtering Model. KDD, 2008, 426–434. SVD++ 方法依据。',
 'Salakhutdinov R, Mnih A. Probabilistic Matrix Factorization. Advances in Neural Information Processing Systems 20, 2008, 1257–1264. PMF 依据。',
 'Ma H 等. SoRec. CIKM, 2008；Learning to Recommend with Social Trust Ensemble. SIGIR, 2009；Recommender Systems with Social Regularization. WSDM, 2011。',
 'Jamali M, Ester M. A Matrix Factorization Technique with Trust Propagation for Recommendation in Social Networks. RecSys, 2010, 135–142。',
 'Yang B, Lei Y, Liu D, Liu J. Social Collaborative Filtering by Trust. IJCAI, 2013, 2747–2753。'
]
for ref in refs:
    p=para(ref);p.paragraph_format.first_line_indent=Pt(0);p.paragraph_format.space_after=Pt(6)
sub('数据与结果依据')
for text in [
 'FilmTrust 作者页面  https://guoguibing.github.io/librec/datasets.html',
 'Epinions 公开镜像  https://static.preferred.ai/cornac/datasets/epinions/ratings_data.zip',
 'Ciao 作者原始包存档  2022年7月14日 MSU 数据页面存档；原始文件保存在 dataset_check/retry/ciao_original，来源链接与哈希见 datasets/ciao/preparation.json。',
 '本项目资料  METHOD.md、trustsvd_repro 源代码、tests/test_math.py、两个主运行目录中的 manifest.json 与 audit.json。所有图均由实际运行输出重新绘制，模型信息流图根据论文与实现绘制。'
]:
    p=para(text);p.paragraph_format.first_line_indent=Pt(0)

# Remove theme colors and title borders to keep the requested plain academic style.
for p in doc.paragraphs:
    if p.style.name in ['Title','Subtitle','Heading 1','Heading 2']:
        pp=p._p.get_or_add_pPr()
        for b in list(pp.findall(qn('w:pBdr'))):pp.remove(b)
        for r in p.runs:r.font.color.rgb=RGBColor(0,0,0)
doc.save(OUT)
print(OUT)
print('Paragraphs',len(doc.paragraphs),'tables',len(doc.tables),'images',len(doc.inline_shapes))
