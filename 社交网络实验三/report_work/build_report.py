"""使用 Codex 文档运行时生成课程实验报告。"""
from pathlib import Path
import json
import hashlib
import sys
from collections import Counter

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.style import WD_STYLE_TYPE
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
WORK = Path(__file__).resolve().parent
OUT = ROOT / '实验三_K-means文本聚类实验报告.docx'
metrics = json.loads((ROOT / 'results/metrics.json').read_text(encoding='utf-8'))
history = json.loads((ROOT / 'results/history.json').read_text(encoding='utf-8'))
clusters = json.loads((ROOT / 'results/clusters.json').read_text(encoding='utf-8'))

# 根据实际日志绘制收敛曲线；不使用示意数据。
im = Image.new('RGB', (1560, 650), 'white')
draw = ImageDraw.Draw(im)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 27)
small = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 23)
left, right, top, bottom = 145, 1490, 65, 540
for v in [20000, 25000, 30000, 35000, 40000]:
    y = bottom - (v - 20000) / 20000 * (bottom - top)
    draw.line((left, y, right, y), fill='#dce1e6', width=2)
    draw.text((35, y - 14), f'{v:,}', font=small, fill='#404040')
points = [(left + (h['iteration'] - 1) / 23 * (right-left),
           bottom - (h['inertia_before_update']-20000)/20000*(bottom-top)) for h in history]
draw.line(points, fill='#245a81', width=5)
for x, y in points:
    draw.ellipse((x-5,y-5,x+5,y+5),fill='#245a81')
draw.line((left,top,left,bottom,right,bottom),fill='#303030',width=2)
for value in [1,5,10,15,20,24]:
    x=left+(value-1)/23*(right-left)
    draw.text((x-10,bottom+18),str(value),font=small,fill='#404040')
draw.text((left,15),'SSE (before center update)',font=font,fill='#202020')
draw.text((720,603),'Iteration',font=font,fill='#202020')
draw.text((points[0][0]+20,points[0][1]),'38,517.31',font=small,fill='#245a81')
draw.text((right-145,bottom-45),'20,445.51',font=small,fill='#245a81')
im.save(WORK/'convergence.png')

doc=Document()
sec=doc.sections[0]
sec.page_width=Inches(8.5)
sec.page_height=Inches(11)
sec.top_margin=sec.bottom_margin=sec.left_margin=sec.right_margin=Inches(1)
sec.header_distance=sec.footer_distance=Inches(.492)

def style(name,size,before,after,line=1.1,bold=False,cjk='宋体',color='000000'):
    s=doc.styles[name] if name in doc.styles else doc.styles.add_style(name,WD_STYLE_TYPE.PARAGRAPH)
    s.font.name='Calibri'
    s.font.size=Pt(size)
    s.font.bold=bold
    s.font.color.rgb=RGBColor.from_string(color)
    s.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),cjk)
    f=s.paragraph_format
    f.space_before=Pt(before)
    f.space_after=Pt(after)
    f.line_spacing=line
    f.widow_control=True
    return s

style('Normal',11,0,6)
style('Title',22,0,10,bold=True,cjk='黑体')
style('Subtitle',12,0,8,cjk='宋体',color='555555')
for n,size,bef,aft in [(1,16,16,8),(2,13,12,6),(3,12,8,4)]:
    s=style(f'Heading {n}',size,bef,aft,bold=True,cjk='黑体')
    s.paragraph_format.keep_with_next=True
style('Caption',9,4,4,color='555555')
style('TableText',10,0,0,line=1.08)
style('Code',9,3,5,line=1.05).font.name='Consolas'
style('Equation',11,4,6,line=1.1)
style('Header',9,0,0,color='666666')
style('Footer',9,0,0,color='666666')
style('Meta',11,0,8,line=1.2)
sec.header.paragraphs[0].text='社交媒体与舆情分析 · 实验三'
footer=sec.footer.paragraphs[0]
footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
footer.add_run('第 ')
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
footer.add_run(' 页')

def p(text,sty=None):
    return doc.add_paragraph(text,sty)

def h(text,level=1):
    return doc.add_heading(text,level)

def page(): doc.add_page_break()

def equation(text):
    paragraph=p(text,'Equation');paragraph.alignment=WD_ALIGN_PARAGRAPH.CENTER

def table(headers,rows,widths):
    t=doc.add_table(rows=1,cols=len(headers))
    t.autofit=False
    pr=t._tbl.tblPr
    width=pr.find(qn('w:tblW'));width.set(qn('w:type'),'dxa');width.set(qn('w:w'),str(sum(widths)))
    ind=OxmlElement('w:tblInd');ind.set(qn('w:w'),'120');ind.set(qn('w:type'),'dxa');pr.append(ind)
    margins=OxmlElement('w:tblCellMar')
    for name,value in [('top',80),('bottom',80),('start',120),('end',120)]:
        el=OxmlElement('w:'+name);el.set(qn('w:w'),str(value));el.set(qn('w:type'),'dxa');margins.append(el)
    pr.append(margins)
    borders=OxmlElement('w:tblBorders')
    for name in ['top','left','bottom','right','insideH','insideV']:
        el=OxmlElement('w:'+name)
        for key,value in [('val','single'),('sz','4'),('color','B7BEC5')]:el.set(qn('w:'+key),value)
        borders.append(el)
    pr.append(borders)
    for grid,w in zip(t._tbl.tblGrid.gridCol_lst,widths):grid.set(qn('w:w'),str(w))
    for _ in rows:t.add_row()
    for ri,row in enumerate([headers]+rows):
        trpr=t.rows[ri]._tr.get_or_add_trPr()
        trpr.append(OxmlElement('w:cantSplit'))
        if ri==0:trpr.append(OxmlElement('w:tblHeader'))
        for ci,text in enumerate(row):
            cell=t.cell(ri,ci)
            cell.width=Inches(widths[ci]/1440)
            cell._tc.get_or_add_tcPr().find(qn('w:tcW')).set(qn('w:w'),str(widths[ci]))
            para=cell.paragraphs[0];para.style=doc.styles['TableText'];para.add_run(str(text))
            if ri==0:
                para.runs[0].bold=True
                shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'F2F4F7');cell._tc.get_or_add_tcPr().append(shade)
    p('').paragraph_format.space_after=Pt(0)
    return t

# 第一页：沿用旧版 DOC 模板的栏目和个人信息项，正文采用可编辑段落。
p('计算机学院', 'Subtitle').alignment=WD_ALIGN_PARAGRAPH.CENTER
p('社交媒体与舆情分析\n课程实验报告', 'Title').alignment=WD_ALIGN_PARAGRAPH.CENTER
p('实验三：基于 K-means 的 Twitter 文本聚类','Subtitle').alignment=WD_ALIGN_PARAGRAPH.CENTER
p('学号：________________    班级：________________','Meta')
p('姓名：________________    日期：________________','Meta')
p('Email：________________________________________','Meta')
h('一、实验方法介绍')
h('1.1 实验目的与任务要求',2)
p('本实验面向 Twitter 短文本聚类任务，将推文转换为数值特征，再利用自行实现的 K-means 将内容相近的文本划分到同一簇。实验旨在掌握文本预处理、词袋表示、迭代聚类及聚类结果解释的完整流程。')
p('按照项目 README 的原始任务要求，逐行读取 JSON 数据，自行完成分词和向量化，并自行实现 K-means。实现中没有调用现成的聚类算法或向量化接口；NumPy、SciPy 仅承担基础数值运算与稀疏矩阵存储。')
h('1.2 数据集与特征选择',2)
p('Twitter_data 共包含 29,846 条记录，每条记录含 userName、clusterNo、text、timeStr、tweetId、errorCode、textCleaned 和 relevance 八个字段。实际数据的标识字段为 tweetId，README 中写作 tweeId。')
p('聚类优先使用 textCleaned；该字段为空时回退到 text。clusterNo 有 220 个不同取值，仅用于聚类结束后的外部评价，不作为文本特征，不参与中心初始化或样本分配。用户名、时间、标识、状态码及 relevance 均未加入特征。')
p('本次设置 K=220，参考数据集已有类别数量确定。该设置是实验参数，不意味着算法能够自动发现最佳类别数，也不意味着聚类编号与真实类别编号一一对应。')

page()
h('1.3 文本预处理与词袋表示',2)
p('首先通过 json.loads() 逐行解析数据，对空白行跳过，对无效 JSON 给出对应行号。然后将文本统一为小写，使用 split() 按空白划分词语。本实现未额外执行停用词过滤或词干提取，已有清洗以数据提供的 textCleaned 为准。')
p('对每篇文本使用 Counter 统计词频，并统计各词出现于多少篇文档。保留文档频率不小于 2 的词，按文档频率降序选取前 5000 个词；同频时按字典序排列。以词表位置作为向量维度，得到词频词袋：')
equation('xᵢ = [count(w₁, dᵢ), …, count(w₅₀₀₀, dᵢ)]')
p('词袋使用 CSR 稀疏矩阵存储，并默认对每个非零向量进行 L2 归一化，以减小推文长度对距离的影响。归一化不引入逆文档频率，因此本实验使用的是归一化词频，而不是 TF-IDF。')
equation('x̂ᵢ = xᵢ / ‖xᵢ‖₂')
p('筛选词表后，13 条文本成为零向量，不参与中心训练和评价；输出 CSV 仍保留这些记录，并将 predicted_cluster 设为 −1。最终参与聚类的文本数为 29,833，保留率约为 99.9564%。')
h('1.4 K-means 原理与实现',2)
p('K-means 以簇内平方误差和最小为目标。设 xᵢ 为归一化后的文本向量，cᵢ 为所属簇，μₖ 为第 k 个中心，则优化目标为：')
equation('J = Σᵢ ‖xᵢ − μcᵢ‖₂²')
p('采用手写 K-means++ 初始化：随机选择第一个样本，再按样本到已选中心的最近距离平方所占比例选取其余中心。随机种子固定为 42，以便复现同一配置的运行结果。')
equation('样本分配：cᵢ = arg minₖ ‖xᵢ − μₖ‖₂²')
equation('中心更新：μₖ = (1 / |Cₖ|) Σxᵢ∈Cₖ xᵢ')
p('交替执行样本分配和中心更新。中心取算术平均后不再归一化，因此属于普通欧氏 K-means，而非球面 K-means。若出现空簇，将其中心重新放在当前误差较大的样本上；本次运行未出现空簇。')
p('当中心矩阵的相对变化 ‖M新−M旧‖F / max(‖M旧‖F, 10⁻¹²) ≤ 10⁻⁴，或达到 50 次迭代时停止。最后再按最终中心分配一次标签，保证导出标签与中心一致。')

page()
h('二、实验过程描述')
h('2.1 实现组织与运行步骤',2)
p('主程序为 twitter_kmeans.py，执行顺序为：读取数据 → 提取文本 → 分词与词袋构建 → 过滤零向量 → 初始化中心 → 迭代聚类 → 评价 → 导出。read_data、tokenize、vectorize 分别完成输入与预处理；initialize_centers、assign_clusters、kmeans 完成聚类；evaluate 和 save_results 完成评价及保存。')
p('运行环境为 Windows、Python 3.10 或更高版本，依赖要求为 NumPy≥1.24、SciPy≥1.10。报告不将未记录的具体软件版本或硬件型号作为实测环境信息。安装及运行命令如下：')
p('python -m pip install -r requirements.txt\npython twitter_kmeans.py\npython -m unittest -v test_twitter_kmeans.py','Code')
h('2.2 参数设置',2)
table(['参数','本次设置','作用'],[
('K / seed','220 / 42','簇数与随机种子'),
('max_iter / tol','50 / 0.0001','迭代上限与停止阈值'),
('min_df','2','最低文档频率'),
('max_features','5000','词表大小上限'),
('batch_size','1024','每批距离计算的样本数'),
('normalize / limit','启用 / 不限制','L2 归一化、读取全部数据'),
],[2450,2150,4760])
h('2.3 距离计算与资源控制',2)
p('利用恒等式 ‖x−μ‖² = ‖x‖² + ‖μ‖² − 2x·μ 计算距离。每批只产生“批大小×K”的距离矩阵，避免构造“样本数×K×词表大小”的三维数组。对浮点误差导致的微小负距离截断为 0。核心计算为：')
p('squared = row_norms[:, None] + center_norms[None, :]\nsquared -= 2 * (block @ centers.T)\nnp.maximum(squared, 0, out=squared)\nnearest = squared.argmin(axis=1)','Code')
p('在 float64 下，一份 1024×220 的距离数组约占 1.72 MiB，220×5000 的中心数组约占 8.39 MiB；这些是单个数组的理论容量，不是程序总内存实测值。中心更新利用稀疏簇归属矩阵求和，再除以各簇样本数。')

page()
h('2.4 实验结果与收敛过程',2)
table(['统计项','实验结果'],[
('读取 / 有效 / 零向量记录','29,846 / 29,833 / 13'),
('词表维度 / 非空簇数','5000 / 220'),
('迭代次数 / 是否收敛','24 / 是'),
('最终 SSE','20445.508069294192'),
('调整兰德指数 ARI','0.3179408470744301'),
('纯度 Purity','0.7348573727080749（73.4857%）'),
('导出前耗时','9.4266364 秒'),
],[4200,5160])
p('上述结果取自本次 results/metrics.json，与提供的运行日志一致。耗时从读取数据前开始，至评价完成、写出文件前结束，包含预处理与聚类，不含结果文件导出；它不是多次运行的平均值。')
doc.add_picture(str(WORK/'convergence.png'),width=Inches(6.5))
p('图 1  各轮更新中心前的 SSE（数据来源：results/history.json）','Caption')
reduction=(history[0]['inertia_before_update']-metrics['inertia'])/history[0]['inertia_before_update']*100
p(f'第 1 轮 SSE 为 38517.3079，第 2 轮降至 21686.6221，之后逐渐趋于稳定；最终相对首轮下降约 {reduction:.2f}%。这表明算法有效降低了给定特征空间中的簇内误差。日志记录的是每轮更新中心前的 SSE，最终指标则按最终中心重新计算。')
p('第 24 轮中心相对变化显示为 0.000000，并满足停止阈值，因此程序提前结束。中间个别轮次中心相对变化增大并不异常，该量不要求单调下降；本次 SSE 持续下降，全部迭代的空簇数均为 0。')

page()
h('三、结论分析')
h('3.1 外部评价的含义',2)
p('ARI 根据真实类别与聚类划分对样本对的同簇关系进行比较，并校正随机一致性。令 nᵢⱼ 为列联表单元计数，aᵢ、bⱼ 为行列边际计数，N 为评价样本数，记：')
equation('A = Σᵢⱼ C(nᵢⱼ, 2)，B = Σᵢ C(aᵢ, 2)，D = Σⱼ C(bⱼ, 2)')
equation('E = BD / C(N, 2)，ARI = (A − E) / [(B + D)/2 − E]')
p('本次 N=29,833，ARI≈0.318，说明聚类与既有类别有一定一致性，但距离完全一致仍有差距。聚类编号可以任意置换，因此不能直接以“预测编号等于 clusterNo”的比例评价结果。')
equation('Purity = (1/N) Σₖ maxⱼ |Cₖ ∩ Tⱼ|')
p('纯度约为 73.49%，表示各簇内数量最多的真实类别样本合计占有效样本的比例。多个簇可以同时以同一真实类别为多数类，因此纯度不能直接称为分类准确率，也不能单独反映类别是否被过度拆分。')
h('3.2 实际簇的内容解释',2)
table(['簇编号','样本数','主要关键词','人工解读'],[
('99','509','iran, deal, nuclear','伊朗核协议相关讨论'),
('119','393','cured, hiv, baby','HIV 与婴幼儿相关报道'),
('5','613','knockknocklive, tomorrow, wait','节目相关讨论'),
('11','475','knockknocklive, special, tuesday','同一节目相关重复表述'),
('1','3056','day, market, everest, yarn','词语分散，主题需进一步检查'),
],[950,1050,3930,3430])
p('关键词来自 clusters.json 中中心权重最高的词，主题名称为人工解释，不是算法输出或对推文事实的核实。簇 99 的代表文本包含“iran nuclear deal”，说明该簇能聚合同一事件的相近表述。')
p('簇 5 与簇 11 均出现 knockknocklive，但被分成不同簇，说明同一宽泛话题可能按用词或重复表述拆分。簇 11 的三个导出代表文本完全相同，提示重复文本会影响中心与结果解释；本实验没有去重。')

page()
h('3.3 局限性与可改进方向',2)
p('本次最小簇有 8 条文本，最大簇有 3056 条，簇规模明显不均衡。最大簇的高权重词较分散，提示仅靠当前词袋距离难以为所有文本形成清晰主题；该判断需要进一步抽样检查，不能仅凭关键词断言簇内全部文本无关。')
p('词袋仅记录词语出现频次，不保留语序，也不能直接识别同义表达。短文本可用信息较少，通用词、重复文本和词表截断都可能影响距离。当前设置丢弃了 13 条零向量，评价指标不覆盖这部分记录。')
p('K 固定为 220，且只记录种子 42 的一次初始化结果。收敛仅表明本次迭代达到停止条件，不保证全局最优。本实验未开展不同 K、词表规模或随机种子的对照实验，因此不能据此宣称当前参数最优。')
p('后续可在保留手写 K-means 的基础上，比较不同词表大小、停用词处理、TF-IDF 权重及多个随机种子的结果，并检查去重对结果的影响。这些属于待验证方案，不是本次已经实现或已经获得提升的结论。')
h('3.4 正确性与输出检查',2)
p('test_twitter_kmeans.py 的 4 项测试全部通过，覆盖词袋计数与归一化、已知两簇样例的中心和 SSE、重复向量造成的空簇与最终标签一致性，以及不受簇编号影响的评价。已知两簇样例的最优 SSE 为 4.0，用于检验中心更新和距离计算。')
p('导出检查确认 assignments.csv 保留 29,846 条记录，标记为 −1 的记录共 13 条；所有簇大小之和为 29,833；centers.npy 形状为 220×5000，且代表文本行号均在数据范围内。测试验证实现的基本正确性，不等于验证主题划分完全正确。')
h('四、结论')
p('本实验完成了 README 要求的数据读取、按空白分词、自行构建词袋及自行实现 K-means 的流程。对 29,833 条有效推文，以 5000 维归一化词频特征进行聚类，经过 24 轮迭代形成 220 个非空簇，最终 SSE 为 20445.51，ARI 为 0.318，纯度为 73.49%。')
p('实验表明，手写 K-means 能够在当前文本表示下完成稳定的迭代优化，并聚合部分用词相近的事件讨论。但仍存在话题拆分、泛化词形成大簇和重复文本影响等问题，需要结合关键词、代表文本及外部评价共同判断效果。')
p('实验材料依据：项目 README.md、twitter_kmeans.py、test_twitter_kmeans.py，以及 results/ 下的 metrics.json、history.json、clusters.json、assignments.csv 和 centers.npy。原始报告模板的“实验方法介绍、实验过程描述、结论分析、结论”栏目已沿用。','Caption')

page()
h('附录：迭代记录与结果文件')
p('表中数值取自 history.json。SSE 为对应轮次更新中心前的值，中心变化为更新前后中心矩阵的相对差异；24 轮的空簇数均为 0。','Caption')
table(['轮次','SSE','中心相对变化','轮次','SSE','中心相对变化'],[
    (str(history[i]['iteration']),f"{history[i]['inertia_before_update']:.4f}",f"{history[i]['relative_center_shift']:.6f}",
     str(history[i+12]['iteration']),f"{history[i+12]['inertia_before_update']:.4f}",f"{history[i+12]['relative_center_shift']:.6f}")
    for i in range(12)
],[660,2280,1740,660,2280,1740])
h('输出文件用途',2)
table(['文件','内容'],[
('assignments.csv','逐条记录的真实标签、聚类编号与文本'),
('clusters.json','各簇大小、10 个关键词和最多 3 条代表文本'),
('metrics.json','参数、最终指标、样本统计与导出前耗时'),
('history.json','迭代 SSE、中心变化及空簇数'),
('vocabulary.json','特征维度对应的词表'),
('centers.npy','220×5000 的聚类中心数组'),
],[2850,6510])
p('默认运行命令：python twitter_kmeans.py。重复使用默认输出目录会覆盖同名结果文件。需要进行对照实验时，可通过 --output 指定独立结果目录；调整参数后应重新评价，不应沿用本报告的指标。')

doc.core_properties.title='实验三：基于 K-means 的 Twitter 文本聚类'
doc.core_properties.subject='社交媒体与舆情分析课程实验报告'
doc.core_properties.author=''
doc.core_properties.keywords='K-means, Twitter, 词袋模型, 文本聚类'
doc.save(OUT)

# 结构核验：表格几何、关键数据、模板原件不变记录。
check=Document(OUT)
assert len(check.tables)==5
assert len(check.inline_shapes)==1
for t in check.tables:
    widths=[int(c.get(qn('w:w'))) for c in t._tbl.tblGrid]
    assert sum(widths)==9360
    assert int(t._tbl.tblPr.find(qn('w:tblW')).get(qn('w:w')))==9360
    for row in t.rows:
        assert [int(c._tc.tcPr.find(qn('w:tcW')).get(qn('w:w'))) for c in row.cells]==widths
text='\n'.join(p.text for p in check.paragraphs)+'\n'+'\n'.join(c.text for t in check.tables for r in t.rows for c in r.cells)
for token in ['实验方法介绍','实验过程描述','结论分析','0.3179408470744301','9.4266364','29,833']:
    assert token in text,token
source=next(ROOT.glob('*.doc'))
(WORK/'artifact.md').write_text(
    '# Report construction notes\n'
    'Source: original binary DOC template, read-only text inspection. Exact visual fidelity is not claimed.\n'
    f'Source SHA256: {hashlib.sha256(source.read_bytes()).hexdigest()}\n'
    'Structure: experiment metadata; methods; process; analysis; conclusion. Appendix added for logs.\n'
    'Preset: standard_business_brief. Letter portrait, 1 inch margins, header/footer .492 inch.\n'
    'Named overrides: Chinese academic typography (SimSun 11 pt body, SimHei black headings); title 22 pt; '
    'TableText 10 pt 1.08 spacing; code 9 pt Consolas; caption 9 pt; no decorative header rule.\n'
    'Tables: width 9360 DXA, indent 120 DXA, cell top/bottom 80 and start/end 120 DXA.\n'
    'Explicit page breaks separate seven content groups; physical pagination requires renderer verification.\n'
    'Personal information fields intentionally blank. Native Word fields supply page numbers.\n'
    'Runtime manifest declares LibreOffice unavailable; render attempt and limitation to be recorded.\n',encoding='utf-8')
print(str(OUT))
print('Structural checks passed; paragraphs:',len(check.paragraphs),'tables:',len(check.tables))
