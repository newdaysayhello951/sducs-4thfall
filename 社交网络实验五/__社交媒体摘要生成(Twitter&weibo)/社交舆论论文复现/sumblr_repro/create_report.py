"""Create the full Chinese Word report for Sumblr reproduction."""
import json, os, sys, math
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.style import WD_STYLE_TYPE

ROOT = Path(r"C:\Users\86134\Desktop\大四上\社交网络实验五\__社交媒体摘要生成(Twitter&weibo)\社交舆论论文复现\sumblr_repro")
OUT = ROOT / "Sumblr论文复现实验报告.docx"
ASSET = ROOT / "report_assets"


def set_cell_shading(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr(); shd = tcPr.find(qn('w:shd'))
    if shd is None: shd = OxmlElement('w:shd'); tcPr.append(shd)
    shd.set(qn('w:fill'), fill)

def set_cell_text(cell, text, bold=False, color=None, size=9):
    cell.text = ""
    p = cell.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(str(text)); r.bold=bold; r.font.size=Pt(size); r.font.name="Microsoft YaHei"; r._element.rPr.rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei')
    if color: r.font.color.rgb = RGBColor(*color)
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

def set_repeat_table_header(row):
    trPr = row._tr.get_or_add_trPr(); tblHeader = OxmlElement('w:tblHeader'); tblHeader.set(qn('w:val'), 'true'); trPr.append(tblHeader)

def add_table(doc, headers, rows, widths=None, font_size=8.5):
    table = doc.add_table(rows=1, cols=len(headers)); table.style='Table Grid'; table.alignment=WD_TABLE_ALIGNMENT.CENTER
    hdr=table.rows[0]; set_repeat_table_header(hdr)
    for i,h in enumerate(headers): set_cell_text(hdr.cells[i],h,True,(255,255,255),font_size); set_cell_shading(hdr.cells[i],'1F4E79')
    for row in rows:
        cells=table.add_row().cells
        for i,v in enumerate(row): set_cell_text(cells[i],v,False,None,font_size)
    if widths:
        for row in table.rows:
            for i,w in enumerate(widths): row.cells[i].width=Cm(w)
    doc.add_paragraph().paragraph_format.space_after=Pt(2)
    return table

def add_caption(doc, text):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=p.add_run(text); r.italic=True; r.font.size=Pt(9); r.font.color.rgb=RGBColor(89,89,89)

def add_img(doc, name, caption, width=16.5):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run().add_picture(str(ASSET/name), width=Cm(width)); add_caption(doc, caption)

def add_code(doc, text):
    p=doc.add_paragraph(style='CodeBlock'); r=p.add_run(text); r.font.name='Consolas'; r._element.rPr.rFonts.set(qn('w:eastAsia'),'Consolas'); r.font.size=Pt(8)

def add_formula(doc, text):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=p.add_run(text); r.font.name='Cambria Math'; r.font.size=Pt(11); r.italic=True

def set_doc_defaults(doc):
    sec=doc.sections[0]; sec.top_margin=Cm(2.2); sec.bottom_margin=Cm(2.2); sec.left_margin=Cm(2.5); sec.right_margin=Cm(2.5)
    styles=doc.styles
    normal=styles['Normal']; normal.font.name='Microsoft YaHei'; normal._element.rPr.rFonts.set(qn('w:eastAsia'),'Microsoft YaHei'); normal.font.size=Pt(10.5); normal.paragraph_format.line_spacing=1.35; normal.paragraph_format.space_after=Pt(6)
    for name,size,color in [('Title',24,(31,78,121)),('Heading 1',16,(31,78,121)),('Heading 2',13,(47,84,150)),('Heading 3',11,(68,114,160))]:
        st=styles[name]; st.font.name='Microsoft YaHei'; st._element.rPr.rFonts.set(qn('w:eastAsia'),'Microsoft YaHei'); st.font.size=Pt(size); st.font.bold=True; st.font.color.rgb=RGBColor(*color)
    if 'CodeBlock' not in styles:
        st=styles.add_style('CodeBlock', WD_STYLE_TYPE.PARAGRAPH); st.font.name='Consolas'; st.font.size=Pt(8); st._element.rPr.rFonts.set(qn('w:eastAsia'),'Consolas'); st.paragraph_format.left_indent=Cm(0.5); st.paragraph_format.space_before=Pt(3); st.paragraph_format.space_after=Pt(3)

def heading(doc,text,level=1): doc.add_heading(text,level=level)
def para(doc,text,bold_prefix=None):
    p=doc.add_paragraph()
    if bold_prefix and text.startswith(bold_prefix): p.add_run(bold_prefix).bold=True; p.add_run(text[len(bold_prefix):])
    else: p.add_run(text)
    return p

def bullet(doc,text,level=0): doc.add_paragraph(text, style='List Bullet' if level==0 else 'List Bullet 2')

# Load current results
with open(ROOT/'output'/'results_alldays.json',encoding='utf-8') as f: full=json.load(f)
with open(ROOT/'output'/'results_2023-02-10.json',encoding='utf-8') as f: day=json.load(f)
with open(ROOT/'output'/'exp_step_sweep_w3000.json',encoding='utf-8') as f: step=json.load(f)
with open(ROOT/'output'/'exp_scalability.json',encoding='utf-8') as f: scale=json.load(f)
with open(ROOT/'output'/'exp_params.json',encoding='utf-8') as f: params=json.load(f)
with open(ROOT/'output'/'exp_flexibility.json',encoding='utf-8') as f: flex=json.load(f)
with open(ROOT/'output'/'exp_timeline.json',encoding='utf-8') as f: timeline=json.load(f)

D=Document(); set_doc_defaults(D)
# Header/footer
for sec in D.sections:
    hp=sec.header.paragraphs[0]; hp.text='社交媒体摘要生成（Twitter & Weibo）实验报告'; hp.alignment=WD_ALIGN_PARAGRAPH.RIGHT; hp.runs[0].font.size=Pt(8); hp.runs[0].font.color.rgb=RGBColor(120,120,120)
    fp=sec.footer.paragraphs[0]; fp.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=fp.add_run('Sumblr 复现 · 2026'); r.font.size=Pt(8); r.font.color.rgb=RGBColor(120,120,120)

# Cover
p=D.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_before=Pt(60); r=p.add_run('社交媒体摘要生成实验报告'); r.bold=True; r.font.size=Pt(26); r.font.color.rgb=RGBColor(31,78,121)
p=D.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=p.add_run('—— Sumblr: Continuous Summarization of Evolving Tweet Streams 复现'); r.font.size=Pt(16); r.font.color.rgb=RGBColor(68,114,160)
D.add_paragraph('')
for t in ['课程：社交网络实验五','论文：Sumblr: Continuous Summarization of Evolving Tweet Streams','作者：Lidan Shou, Zhenhua Wang, Ke Chen, Gang Chen','会议：ACM SIGIR 2013','复现数据：Turkey Earthquake Tweets（Kaggle）','报告类型：算法复现与实验分析报告']:
    p=D.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run(t).font.size=Pt(12)
D.add_paragraph(''); p=D.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.add_run('2026 年').font.size=Pt(12)
D.add_page_break()

# Abstract
heading(D,'摘要',1)
para(D,'本文对 Shou 等人在 SIGIR 2013 提出的 Sumblr（SUMmarization By stream cLusTeRing）进行复现。Sumblr 面向动态、快速到达、大规模的推文流，使用在线聚类压缩推文内容，通过 Tweet Cluster Vector（TCV）保存簇级统计量，并结合 Pyramidal Time Frame（PTF）支持任意时间区间的历史摘要；在此基础上，TCV-Rank 使用 LexRank 中心性、簇规模覆盖和冗余惩罚选择摘要推文，同时利用摘要间 KL 距离检测话题演化。')
para(D,'本复现采用公开的 Turkey Earthquake Tweets 数据集替代论文原始的 2012 年 Twitter 数据，完整实现了 TCV、在线聚类、PTF 金字塔、IDList、Definition 4 减法、历史摘要、DSDR 基线、滑动窗口、Eq. (4) 评估、参数扫描、PTF 灵活性与时间线 P/R/F 评测。实验结果表明：全量 27,661 条去重推文经过流式处理后，live cluster membership 统计覆盖约 10.4% 推文；这不是完整内存字节占用，而是当前活动簇中仍关联的推文数量。DSDR 的运行时间随窗口规模增长显著快于 Sumblr；step-size 扫描呈现 Sumblr 随 step 增大而改善的趋势。')
para(D,'关键词：持续摘要；推文流；在线聚类；Tweet Cluster Vector；Pyramidal Time Frame；时间线生成')

# TOC placeholder
heading(D,'目录',1)
para(D,'本报告按“问题定义—论文方法—代码实现—实验设计—结果分析—复现局限”的顺序组织。Word 打开后可通过“引用→目录”更新自动目录。')
for s in ['1 绪论','2 论文方法原理','3 复现环境与数据集','4 系统实现与代码对应关系','5 实验设计','6 实验结果与分析','7 复现问题、偏差与改进','8 结论','参考文献']:
    bullet(D,s)
D.add_page_break()

# 1
heading(D,'1 绪论',1)
heading(D,'1.1 研究背景',2)
para(D,'微博客平台中的短文本具有实时性强、数量巨大、噪声和冗余显著等特点。传统文档摘要通常假设输入规模有限且相对静态，难以直接处理持续到达的推文流。论文将问题概括为三个要求：效率（单遍或近似单遍处理）、灵活性（支持任意时间区间）以及话题演化检测（发现子话题变化时刻）。')
heading(D,'1.2 论文贡献',2)
for t in ['提出持续推文摘要框架 Sumblr；','提出 Tweet Cluster Vector 与 Pyramidal Time Frame 两种数据结构，分别压缩当前簇状态并保存不同时间粒度的历史快照；','提出 TCV-Rank 摘要算法，通过覆盖与新颖性共同选择推文；','提出基于连续摘要变化的时间线生成方法。']:
    bullet(D,t)
heading(D,'1.3 本复现目标',2)
para(D,'本实验不将“逐数字复现论文原始表格”作为唯一目标，因为论文原始 Twitter 数据来自历史 API，且论文提供的下载地址已经失效。本实验的目标是：准确实现论文公式和伪代码；验证 PTF 与 Definition 4 的正确性；在可下载替代数据上复现完整工程流程；通过 step-size、运行时间、参数和时间线实验检验论文提出的方向性结论。对于主流程的参考摘要，代码实际使用 ClusterSum、LexRank 和 Popularity 三者投票；窗口化第 5 章实验则使用论文指定的 ClusterSum、LexRank 和 DSDR 三候选。

# 2
heading(D,'2 论文方法原理',1)
heading(D,'2.1 推文表示与 TCV',2)
para(D,'论文将每条推文表示为三元组：文本向量、时间戳和作者影响力权重。本文在没有用户社交网络的替代数据上将权重统一设置为 1，与论文对其四个新爬数据集的处理一致。')
add_formula(D,'tᵢ = (tvᵢ, tsᵢ, wᵢ)')
para(D,'对包含 n 条推文的簇 C，论文定义 TCV：')
add_formula(D,'TCV(C) = (sum_v, wsum_v, ts1, ts2, n, ft_set)')
for t in ['sum_v = Σᵢ tvᵢ / ||tvᵢ||：归一化文本向量之和；','wsum_v = Σᵢ wᵢ·tvᵢ：加权原始文本向量之和；','ts1 = Σᵢ tsᵢ，ts2 = Σᵢ(tsᵢ)²：时间统计量；','n：簇内推文数；','ft_set：距离簇中心最近的 m 条焦点推文。']:
    bullet(D,t)
add_formula(D,'cv = wsum_v / n')
para(D,'实现中必须区分 sum_v 与 wsum_v。若错误地将同一归一化矩阵同时用于两者，在 wᵢ=1 时 MBS 会退化，造成簇塌缩。')
heading(D,'2.2 在线聚类',2)
para(D,'新推文到达后，首先计算其与所有活动簇中心的余弦相似度，找到最大相似度 MaxSim 的簇。论文使用最小边界相似度（Minimum Bounding Similarity, MBS）判断是否吸收：')
add_formula(D,'MBS = β · Sim(co, tᵢ)')
add_formula(D,'Sim(co,tᵢ) = (wsum_v · sum_v) / (n · ||wsum_v||)')
para(D,'当 MaxSim < MBS 时新建簇，否则更新最近簇。簇数超过 Nmax 后按中心相似度贪心合并，直到剩余 mc 比例的簇。过时簇删除使用时间均值、标准差和正态分布分位点估计最近 10% 推文的平均到达时间，超过三天则删除。')
heading(D,'2.3 PTF 金字塔与历史摘要',2)
para(D,'PTF 按快照时间粒度分层。第 i 阶快照的时间间隔为 αⁱ，每阶最多保留 αˡ+1 个快照，并将同一时刻快照放到最高可用阶，以避免重复。论文 Table 1 的 α=3、l=2、T=86 示例在本实验中逐项测试通过。')
para(D,'对于结束时间 tse、时长 H，论文检索不晚于 tse 与 tse−H 的两个快照，记为 S(ts1) 和 S(ts2)，将真实区间近似为 [ts2, ts1]。随后按照 IDList 找到同一原始簇在早期快照的对应项，执行 Definition 4：')
add_formula(D,'TCV(C₁−C₂) = (sum_v₁−sum_v₂, wsum_v₁−wsum_v₂, ts1₁−ts1₂, ts2₁−ts2₂, n₁−n₂, ft_set₁−ft_set₂)')
para(D,'减法后的簇集用于历史摘要，从而支持 range summary、drill-down 和 roll-up。')
heading(D,'2.4 TCV-Rank 摘要',2)
para(D,'算法首先收集所有簇的 ft_set，建立余弦相似度图并计算 LexRank。随后先从每个簇中 LexRank 最高的推文组成候选集合 Tc，再使用覆盖—新颖性目标选择推文：')
add_formula(D,'score(tᵢ) = λ·(nₜᵢ/nmax)·LR(tᵢ) − (1−λ)·avg_{tⱼ∈S} Sim(tᵢ,tⱼ)')
para(D,'第一项鼓励选择大簇中的中心推文，第二项抑制摘要内部冗余；当 250 词预算尚未达到时，再从全部候选 T−S 中补充。')
heading(D,'2.5 话题演化检测',2)
para(D,'对相邻摘要计算词分布的 KL 距离，并归一化为 [0,1) 区间：')
add_formula(D,'D_KL(S_c||S_p) = Σ_w p(w|S_c) ln[p(w|S_c)/p(w|S_p)]')
add_formula(D,'D = 1 − exp(−D_KL)')
para(D,'若 Dcur/Davg > τ，则将当前时刻判定为话题演化节点。复现中发现，严格照字面实现“只用非节点对估计 Davg”会产生正反馈，因此增加最小样本保护，并将窗口设置为非重叠时间段；这保证时间线节点数量具有解释性。')

# 3
heading(D,'3 复现环境与数据集',1)
heading(D,'3.1 软件环境',2)
add_table(D,['组件','版本/说明'],[['Python','3.12'],['NumPy / pandas','数值计算与数据处理'],['SciPy','erfinv、稀疏矩阵'],['scikit-learn','TF-IDF、K-means'],['设备','纯 CPU，不需要 GPU']], [5,11])
heading(D,'3.2 数据集',2)
para(D,'论文原始数据包含 Obama、Chelsea、Arsenal Arsene Wenger、Tablet Smartphone Cellphone 和 Black Friday 五个 Twitter 流，共约 121 万条推文。论文唯一的 Sumblr 数据页面现已返回 HTTP 404，且 2012 年 Twitter Streaming API 无法重建，因此本实验采用 Kaggle 公开数据集 Turkey Earthquake Tweets。')
add_table(D,['项目','值'],[['CSV 原始行数','28,844 条'],['全量主流程输入（按 text 去重）','27,661 条'],['2023-02-10 原始行数','4,289 条'],['2023-02-10 主流程输入（去重后）','4,278 条'],['时间范围','2023-02-07 至 2023-02-26'],['主题','2023 土耳其—叙利亚地震'],['主要字段','id、date、text、retweets、favorites、hashtags'],['下载来源','Kaggle: gpreda/turkey-earthquake-tweets']], [5,11])
add_img(D,'fig01_daily_volume.png','图 1  土耳其地震推文流的日分布。数据在 2 月 10—11 日达到高峰。',16.5)
para(D,'该数据与论文相比存在三项差异：规模较小、主题是灾害事件而非足球/政治等主题、噪声和模板化推文较多。因此本文将结果解释为方法复现与替代数据验证。数据处理分为三层：原始 CSV 有 28,844 行；load_tweets 按 text 去重并解析时间后得到 27,661 条全量推文，2023-02-10 子流为 4,278 条；实验表中的 ROUGE 又会对候选摘要执行 250 raw-word / 25-tweet 预算裁剪。因此 JSON 中的 summary_stats 是未裁剪 TCV 候选统计，而 metrics 是裁剪后的评测统计；metrics.summary_words 还是清洗、分词后的 token 数，二者不能混为同一词数。')

# 4
heading(D,'4 系统实现与代码对应关系',1)
add_img(D,'fig02_pipeline.png','图 2  复现系统总体流程图。',17.5)
add_table(D,['论文模块','实现文件','主要内容'],[
['预处理','preprocess.py','清洗、分词、原始/归一化 TF-IDF 双矩阵'],
['TCV 与在线聚类','sumblr.py','TCV、Canopy+K-means、MBS、删除、合并、IDList'],
['PTF','ptf.py','order 分层、快照容量、检索、Table 1 验证'],
['历史摘要','historical.py','快照差集、Definition 4、区间摘要'],
['TCV-Rank','summarize.py','LexRank、Eq. (2)、摘要选择'],
['基线','baselines.py','ClusterSum、LexRank、DSDR、Random'],
['实验协议','experiments.py','滑动窗口、Eq. (4)、同窗口对比'],
['实验入口','run_experiments.py','step、scalability、params、flexibility、timeline']], [4,4.5,7.5])
heading(D,'4.1 关键代码逻辑',2)
add_code(D,'# TCV 的核心更新（对应 Definition 1）\nself.sum_v += normalized_tv\nself.wsum_v += weight * raw_tv\nself.ts1 += timestamp\nself.ts2 += timestamp ** 2\nself.n += 1\n\n# 历史摘要（对应 Definition 4）\nwindow_tcv = end_snapshot_tcv.subtract(start_snapshot_tcv)\nsummary = tcv_rank(window_tcv_clusters)')
para(D,'代码中增加了四个单元测试：test_ptf.py 验证 PTF Table 1；test_historical.py 验证减法的六项算术；test_dsdr.py 验证重构误差单调下降且优于随机子集；test_protocol.py 验证窗口、Eq. (4) 和 runtime 统计。')

# 5
heading(D,'5 实验设计',1)
heading(D,'5.1 主流程实验',2)
para(D,'单日实验用于观察爆发时段的聚类和摘要行为；全量实验用于验证持续流式处理、PTF 存储和过时簇删除。主流程结果保存为 results_2023-02-10.json 和 results_alldays.json。')
heading(D,'5.2 Step-size 实验',2)
para(D,'按照论文 Figure 5/6，固定窗口大小 3000 条，取 step/window=0.2、0.4、0.6、0.8、1.0。每个方法在相同窗口和相同参考摘要上评估 ROUGE-1/2 F1，同时记录累计运行时间。由于 DSDR 的复杂度较高，每个 step 取最多 6 个均匀窗口。')
heading(D,'5.3 可扩展性实验',2)
para(D,'固定摘要长度，改变窗口大小 500、1000、2000、4000、8000，分别测量 Sumblr、ClusterSum、LexRank 和 DSDR 的运行时间，绘制对数纵轴。')
heading(D,'5.4 参数与灵活性实验',2)
para(D,'参数实验扫描 β、Nmax、mc、m、λ。灵活性实验按照论文 Eq. (5) 对 1—10 天区间求平均分数，并比较 l=3、5、8 时的快照数量和摘要质量。')
heading(D,'5.5 时间线实验',2)
para(D,'由于替代数据不是 Arsenal/Chelsea，本文使用 2023 地震的 10 个公开事件里程碑作为近似参考时间线，12 小时内匹配判定 TP，计算 Precision、Recall 和 F1。该结果只用于验证指标流程和 τ 的趋势，不能与论文 Table 3 直接等价。')

# 6
heading(D,'6 实验结果与分析',1)
heading(D,'6.1 数据分布与系统结构',2)
para(D,'全量流实验处理 27,661 条去重推文，最终保留 132 个活动簇，累计创建 284 个簇、合并 138 次、删除 14 个过时簇。PTF 中有 59 个 live snapshots、463 个 stored snapshots，使用 9 个 order；内存簇统计只覆盖 2,875 条推文，占全流 10.4%。这说明 TCV 与过时删除有效压缩了长期流。')
add_img(D,'fig03_step_quality.png','图 3  不同步长下各方法 ROUGE-1 F1。Sumblr 随 step 增大而改善。',16.5)
add_img(D,'fig04_step_runtime.png','图 4  不同步长下运行时间。DSDR 明显慢于 Sumblr。',16.5)
add_img(D,'fig05_scalability.png','图 5  窗口规模与运行时间的关系。纵轴采用对数尺度。',16.5)
heading(D,'6.2 参数和 PTF 灵活性',2)
add_img(D,'fig06_beta.png','图 6  β 对平均 IDF 的影响。',8.0)
add_img(D,'fig06_n_max.png','图 7  Nmax 对平均 IDF 的影响。',8.0)
add_img(D,'fig06_lam.png','图 8  λ 对平均 IDF 的影响。λ=1 过度强调覆盖。',8.0)
add_img(D,'fig07_ptf_flexibility.png','图 9  PTF 深度 l 对 Eq. (5) 分数和快照数量的影响。',16.5)
heading(D,'6.3 时间线结果',2)
add_img(D,'fig08_timeline_tau.png','图 10  τ 对时间线 Precision、Recall 与 F1 的影响。',16.5)
para(D,'在本替代数据上，τ≈1.06 的 F1 最高（0.421），高于论文原始数据上报告的 τ=1.012。这不是实现错误，而是数据分布差异：本灾害事件流相邻摘要的 D 距离更加集中，较小 τ 会产生过多节点。')

# 7
heading(D,'7 复现问题、偏差与改进',1)
heading(D,'7.1 数据不可得造成的边界',2)
para(D,'原始 2012 Twitter 数据、作者人工参考摘要及体育新闻时间线均无法获取，因此本报告不声称复现论文原始绝对数值。替代数据实验用于验证算法流程、复杂度趋势和参数行为。')
heading(D,'7.2 复现中发现的实现陷阱',2)
add_table(D,['问题','现象','修复'],[
['sum_v 与 wsum_v 混用','MBS 退化，最大簇占比 82.7%','原始/归一化矩阵分开维护'],
['点积代替余弦','β 扫描失效','单位化质心余弦相似度'],
['冻结合并矩阵','不相关簇串成大簇','合并后增量更新相似度'],
['KL ε 过小','D 饱和 1.0，时间线为空','add-one 平滑'],
['D_avg 正反馈','大量窗口被判节点','最小样本保护'],
['窗口重叠过度','D 方差过小，节点爆炸','默认非重叠窗口']], [4,8,4.5])
heading(D,'7.3 进一步改进方向',2)
for t in ['实现论文 §4.4 的多主题关键词分组，使多个主题共享一套流式框架；','获取规模更接近论文的公开事件流，检验 Sumblr 与基线的质量交叉点；','将推文单元切分为句子或信息片段，降低灾害流中短标签推文对 TCV-Rank 的干扰；','在相同公开数据上构建人工参考摘要，进一步降低基线构造参考带来的偏置。']:
    bullet(D,t)

# 8
heading(D,'8 结论',1)
para(D,'本实验完成了 Sumblr 论文核心方法和第 5 章实验协议的工程复现。PTF 与论文 Table 1 精确匹配，历史摘要的 Definition 4 减法通过单元测试，DSDR、滑动窗口、Eq. (4)、参数、灵活性和时间线实验均已运行。全量流结果表明，Sumblr 能在纯 CPU 上以有界内存处理 20 天推文流，并在摘要多样性和冗余控制方面表现稳定。')
para(D,'同时，原始数据不可得、参考摘要存在基线偏置、替代数据规模与主题不同，决定了本实验应被定义为“方法复现 + 替代数据验证”，而不是原论文表格的逐数字复制。除多主题流扩展外，论文中要求的主要算法、公式、实验模块和测试均已完成。')

# references
heading(D,'参考文献',1)
refs=[
'[1] Shou, L., Wang, Z., Chen, K., & Chen, G. Sumblr: Continuous Summarization of Evolving Tweet Streams. SIGIR, 2013, pp. 533–542.',
'[2] Aggarwal, C. C., et al. A Framework for Clustering Evolving Data Streams. KDD, 2003.',
'[3] Erkan, G., & Radev, D. R. LexRank: Graph-based Lexical Centrality as Salience in Text Summarization. JAIR, 2004.',
'[4] Inouye, D., & Kalita, J. Comparing Twitter Summarization Algorithms for Multiple Post Summaries. SocialCom, 2011.',
'[5] He, T., et al. DSDR: Document Summarization with Diversity and Structural Reconstruction. AAAI, 2012.',
'[6] Lin, C.-Y., & Hovy, E. Automatic Evaluation of Summaries Using N-gram Co-occurrence Statistics. NAACL, 2003.',
'[7] Kaggle. Turkey Earthquake Tweets. Dataset: gpreda/turkey-earthquake-tweets.'
]
for r in refs: D.add_paragraph(r)

D.save(OUT)
print(OUT)
