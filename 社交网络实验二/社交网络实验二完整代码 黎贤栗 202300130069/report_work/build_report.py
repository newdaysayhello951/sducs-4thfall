"""根据实际实验产物生成可编辑 Word 报告。使用 Codex 文档运行时运行。"""
import csv
import json
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Twips
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '新闻自动摘要实验报告.docx'
rows = list(csv.DictReader((ROOT/'results/metrics.csv').open(encoding='utf-8-sig')))
config = json.loads((ROOT/'results/config.json').read_text(encoding='utf-8'))
stats = json.loads((ROOT/'results/dataset_stats.json').read_text(encoding='utf-8'))
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Inches(8.5), Inches(11)
sec.top_margin = sec.bottom_margin = sec.left_margin = sec.right_margin = Inches(1)
sec.header_distance = sec.footer_distance = Inches(.492)
# Preset: standard_business_brief. Named overrides: Chinese fonts (宋体/黑体),
# formula/table styles 10pt, editorial_cover compact title 22pt, explicit page chapters.
def style(name, size, before=0, after=6, color='222222', bold=False, east='宋体', line=1.10):
    s = doc.styles[name] if name in doc.styles else doc.styles.add_style(name, 1)
    s.font.name = 'Calibri'
    s.font.size = Pt(size)
    s.font.bold = bold
    s.font.color.rgb = RGBColor.from_string(color)
    s.element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), east)
    s.paragraph_format.space_before = Pt(before)
    s.paragraph_format.space_after = Pt(after)
    s.paragraph_format.line_spacing = line
    return s
style('Normal',11)
style('Title',22,0,12,'17365D',True,'黑体')
style('Subtitle',11,0,10,'666666')
for name,size,before,after,color in [('Heading 1',16,16,8,'2E74B5'),('Heading 2',13,12,6,'2E74B5'),('Heading 3',12,8,4,'1F4D78')]:
    style(name,size,before,after,color,True,'黑体').paragraph_format.keep_with_next=True
style('TableText',10,0,4,line=1.10)
style('Caption',9,4,4,'666666')
style('Formula',10,4,6,'17365D',line=1.15)
style('Code',9,0,4,'333333',line=1.10).font.name='Consolas'
style('Header',9,0,0,'777777')
style('Footer',9,0,0,'777777')
sec.header.paragraphs[0].text='社交网络实验二  |  新闻自动摘要'
foot=sec.footer.paragraphs[0]
foot.alignment=WD_ALIGN_PARAGRAPH.RIGHT
foot.add_run('第 ')
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');foot._p.append(field)
foot.add_run(' 页')

def p(text, sty=None):
    return doc.add_paragraph(text, sty)
def h(text, level=1):
    return doc.add_heading(text,level)
def page(title):
    doc.add_page_break(); h(title)
def formula(text):
    p(text,'Formula')
def table(headers, data, widths):
    assert sum(widths)==9360
    t=doc.add_table(rows=1, cols=len(headers));t.autofit=False
    pr=t._tbl.tblPr
    w=pr.find(qn('w:tblW'));w.set(qn('w:w'),'9360');w.set(qn('w:type'),'dxa')
    ind=OxmlElement('w:tblInd');ind.set(qn('w:w'),'120');ind.set(qn('w:type'),'dxa');pr.append(ind)
    margins=OxmlElement('w:tblCellMar')
    for tag,value in [('top',80),('bottom',80),('start',120),('end',120)]:
        el=OxmlElement('w:'+tag);el.set(qn('w:w'),str(value));el.set(qn('w:type'),'dxa');margins.append(el)
    pr.append(margins)
    borders=OxmlElement('w:tblBorders')
    for side in ['top','left','bottom','right','insideH','insideV']:
        el=OxmlElement('w:'+side);el.set(qn('w:val'),'single');el.set(qn('w:sz'),'4');el.set(qn('w:color'),'CDD4DC');borders.append(el)
    pr.append(borders)
    for col,width in zip(t.columns,widths):col.width=Twips(width)
    for record in [headers]+list(data):
        row=t.rows[0] if record is headers else t.add_row()
        for cell,text,width in zip(row.cells,record,widths):
            cell.width=Twips(width)
            cell.text=str(text)
            for para in cell.paragraphs:para.style=doc.styles['TableText']
        trpr=row._tr.get_or_add_trPr();no=OxmlElement('w:cantSplit');trpr.append(no)
    repeat=OxmlElement('w:tblHeader');t.rows[0]._tr.get_or_add_trPr().append(repeat)
    for c in t.rows[0].cells:
        shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'F2F4F7');c._tc.get_or_add_tcPr().append(shade)
        for run in c.paragraphs[0].runs:run.bold=True
    p('','Caption')
    return t

title=p('基于 TextRank 的新闻自动摘要\n实验报告','Title');title.alignment=WD_ALIGN_PARAGRAPH.CENTER
p('CNN News Story Dataset · 抽取式摘要与基线对比','Subtitle').alignment=WD_ALIGN_PARAGRAPH.CENTER
p('姓名：____________    学号：____________    班级：____________')
p('实验日期：____________')
h('一、实验目的与任务')
p('本实验给定一篇英文新闻正文，自动选取重要句子组成摘要，并与数据集提供的人工摘要进行比较。实验重点是手写 TextRank 的句子相似度计算、图构建、PageRank 迭代和选句过程，理解图中节点的重要性如何用于文本处理。')
p('采用 Lead-3 作为基线，同时实现词重叠和 TF-IDF 余弦相似度两种图排序方案。以 ROUGE-1、ROUGE-2、ROUGE-L 的 F1 值及 BLEU-4 评价效果，并分析摘要长度、执行效率和收敛情况。生成式 Encoder–Decoder 仅作原理了解，不训练模型。')
h('二、数据与实验环境')
table(['项目','实际配置'],[
('数据来源','项目内 CNN News Story Dataset，已分词的 .story 文件'),
('样本数量',f"原始 {config['files_found']} 篇；有效 {config['evaluated']} 篇；跳过 {len(config['skipped_ids'])} 篇无效样本"),
('文本规模',f"正文平均 {stats['mean_story_words']:.2f} 词；人工摘要平均 {stats['mean_reference_words']:.2f} 词"),
('运行环境',f"Windows / PowerShell；Python {config['python']}；NumPy {config['numpy']}"),
('默认设置','每篇最多选 3 句；阻尼系数 0.85；误差阈值 10⁻⁶；最多 200 次迭代'),
('结果来源','用户本次全量运行输出，以及 results 中对应的 CSV、JSON 和逐篇预测文件')
],[1900,7460])
p('文件按名称排序读取，以 @highlight 分离正文和参考要点。同篇新闻的所有 highlights 合并成一个完整参考摘要。正文或参考摘要无法提取有效词元的文件跳过，文件 ID 记录在 config.json 中。算法生成摘要时仅使用正文，参考摘要只参与评分。')

page('三、算法原理与执行流程')
h('3.1 总体流程',2)
formula('读取新闻 → 分离正文与参考 → 正文分句、分词 → 构建句子图\n→ PageRank 迭代 → 选取高分句并恢复原文顺序 → 评测与导出')
p('summarize() 串联全部摘要步骤。split_sentences() 将新闻拆成句子；tokenize() 提取小写英文和数字词元。分句前恢复 -LRB-、-RRB- 等括号标记，并临时保护 Dr. 等常见缩写，避免直接把缩写中的句点当成句末。用于排名的词元过滤固定停用词表；最终输出保留处理后的原句。')
h('3.2 句子相似度与图构建',2)
p('每个句子是一个节点，两个句子的相似度是连边权重。设 Uᵢ 为句子 i 的不同有效词集合，Lᵢ 为过滤停用词后的词数。默认词重叠相似度为：')
formula('Wᵢⱼ = |Uᵢ ∩ Uⱼ| / [ln(1 + Lᵢ) + ln(1 + Lⱼ)]，i ≠ j')
p('共同词种类越多，句子越相关；分母对句长进行调整，加 1 避免短句产生零分母。若分母为零则相似度记为零。权重矩阵对称，Wᵢⱼ = Wⱼᵢ；对角线为零，不设置自环。这是本代码采用的词重叠变体。')
p('TF-IDF 对照在单篇新闻内把句子视作“文档”，根据一个词出现于多少句子中计算 IDF，再将两个句子的加权词频向量做余弦比较：')
formula('IDF(w) = ln[(1 + N)/(1 + df(w))] + 1\nvᵢ(w) = TFᵢ(w) × IDF(w)\nWᵢⱼ = (vᵢ · vⱼ) / (||vᵢ|| × ||vⱼ||)')
p('N 是该篇新闻的句子数，df(w) 是包含词 w 的句子数，TF 是词频。零向量的相似度记为零。该对照属于 LexRank 风格的句子相似度选择，后续排名与词重叠方案一致。')
h('3.3 PageRank 迭代与摘要输出',2)
p('每行权重除以行和，得到转移概率矩阵 M；没有有效连边的行改为均匀分配 1/N。初始句子得分均为 1/N，使用列向量按下式更新：')
formula('p⁽ᵗ⁺¹⁾ = [(1 − d)/N]·1 + d·Mᵀp⁽ᵗ⁾，d = 0.85\n停止条件：Σᵢ |pᵢ⁽ᵗ⁺¹⁾ − pᵢ⁽ᵗ⁾| < 10⁻⁶，或达到 200 次')
p('可将其理解为句子按照相似度互相“投票”，得分高的句子传出的票更有分量。选取得分最高的 3 句，同分优先选择原文靠前的句子；随后按原文顺序拼接，减少叙述顺序混乱。Lead-3 则直接取前三句，不构图也不迭代。')

page('四、评价指标与计算口径')
p('评价时统一转成小写英文/数字词元，不去停用词、不做词干化。以下分数均在 0～1 之间，不等同于事实正确率。本实验自实现指标，没有调用 sumeval，不宣称与其默认设置逐值一致；未计算 ROUGE-BE。')
h('4.1 ROUGE-1 F1 与 ROUGE-2 F1',2)
p('ROUGE-1 比较单个词，ROUGE-2 比较相邻的两个词。对每个词或词组 g，匹配次数取程序摘要与参考摘要出现次数的较小值，防止重复输出刷高匹配数。设候选摘要为 C、参考为 R，则：')
formula('Aₙ = Σg min[countC(g), countR(g)]\nPₙ = Aₙ / 候选 n 元组总数；Rₙ = Aₙ / 参考 n 元组总数\nF1ₙ = 2PₙRₙ / (Pₙ + Rₙ)，n = 1 或 2')
p('精确率 P 衡量输出中有多少内容匹配参考；召回率 R 衡量参考中有多少内容被覆盖。分母为零时相应分数置零。F1 同时考虑精确率与召回率。')
h('4.2 ROUGE-L F1',2)
p('计算两份摘要的最长公共子序列长度 L：单词顺序必须一致，但允许中间跳过词。代码 lcs_length() 使用动态规划，并仅保留当前行与上一行。')
formula('Pᴸ = L / 候选词数；Rᴸ = L / 参考词数\nF1ᴸ = 2PᴸRᴸ / (Pᴸ + Rᴸ)')
p('本实现对完整摘要计算最长公共子序列，不是按句汇总的 ROUGE-Lsum。例如参考为“the cat ate fish”，候选为“the cat ate fresh fish”，L = 4。')
h('4.3 语料级 BLEU-4',2)
p('分别计算 1～4 元组的截断匹配比例 pₙ。每篇文章只与自己的参考匹配，再把所有文章的匹配数和候选元组总数相加计算比例，不在不同文章之间形成词组。设 c、r 为全部候选与参考的总词数：')
formula('pₙ = 全部文章第 n 阶匹配数之和 / 候选第 n 阶元组数之和\nBP = 1（c ≥ r）；BP = exp(1 − r/c)（0 < c < r）\nBLEU-4 = BP × exp[(ln p₁ + ln p₂ + ln p₃ + ln p₄)/4]')
p('长度惩罚 BP 限制过短摘要。本实现固定四阶、无平滑；候选总长度为零，或任何一阶没有匹配/候选元组时，BLEU-4 返回零。因此短句或换词表达可能得分很低，即使含义相近。')
h('4.4 汇总方式',2)
p('三种 ROUGE 均先逐篇计算 P、R、F1，再分别取算术平均。主结果表使用“逐篇 F1 的平均值”，不是用平均 P、R 再计算 F1。BLEU-4 使用语料累计计数计算一次，不是逐篇 BLEU 的平均值。四项指标分别报告，不合成为总分。')

page('五、实验结果')
p('执行 python run_experiment.py，对全部 4996 篇有效新闻运行三种方法。以下表格来自本次保存结果，与用户提供的终端输出一致；为便于阅读，指标保留四位小数。')
names={'lead-3':'Lead-3','textrank-overlap':'TextRank（词重叠）','textrank-tfidf':'TF-IDF 图排序'}
p('表 1  摘要质量对比（ROUGE 为宏平均 F1）','Caption')
table(['方法','ROUGE-1','ROUGE-2','ROUGE-L','BLEU-4'],[[names[r['method']]]+[f"{float(r[k]):.4f}" for k in ['rouge1_f1','rouge2_f1','rougeL_f1','bleu4']] for r in rows],[2800,1640,1640,1640,1640])
p('Lead-3 在四项主指标上均最高。TF-IDF 图排序的四项主指标均高于词重叠 TextRank，但两种图排序方法均未超过 Lead-3。该结论只针对本数据与当前固定配置，不代表所有摘要任务的普遍优劣。')
p('表 2  ROUGE-1 精确率、召回率与摘要长度','Caption')
table(['方法','精确率 P','召回率 R','平均摘要词数'],[[names[r['method']],f"{float(r['rouge1_precision']):.4f}",f"{float(r['rouge1_recall']):.4f}",f"{float(r['mean_words']):.2f}"] for r in rows],[3000,1800,1800,2760])
p('词重叠 TextRank 的 ROUGE-1 召回率最高，为 0.4386；但其平均摘要长度为 92.49 词，比 Lead-3 的 72.31 词多约 20.19 词。较长输出覆盖了更多参考词汇，也带入更多额外内容，其精确率只有 0.2122，因此综合 F1 较低。')
p('表 3  执行效率与收敛情况','Caption')
table(['方法','平均耗时/ms','平均迭代次数','未收敛篇数'],[[names[r['method']],f"{1000*float(r['mean_seconds']):.3f}",f"{float(r['mean_iterations']):.2f}",r['nonconverged']] for r in rows],[3000,2200,2200,1960])
p('耗时只统计摘要生成过程，不包含读取文件、指标计算和导出。Lead-3 无需构图和迭代，因此最快。两种 TextRank 的未收敛篇数均为 0，说明本次运行均达到设定的收敛阈值。平均耗时受硬件和进程负载影响，不作为跨设备性能结论。')
p('有效样本正文平均 677.61 词，人工摘要平均 43.52 词。三种方法的摘要都比参考更长；相同“3 句”限制并非相同词数预算，比较结果时应同时参考表 2。')

page('六、结果分析与案例讨论')
h('6.1 方法差异与合理解释',2)
p('Lead-3 的优势可能与新闻开头集中交代主要事件有关；图排序主要衡量词汇联系，较多背景描述也可能形成强连接，重要但只出现一次的细节却可能排名不高。这是结合算法与结果提出的解释，不能仅凭总体分数证明因果关系。')
p('TF-IDF 在当前结果中优于词重叠方案，说明词权重和向量长度归一化可能改善句子关系的区分能力。不过其平均摘要也更短，因此不能把全部差异都归因于相似度公式。实验未进行显著性检验，报告中的差异属于描述性比较。')
h('6.2 固定新闻案例',2)
p('案例选用排序后第一篇新闻，文件 ID 为 0001d1afc246a7964130f43ae940af6bc6c57f01，主题为奥巴马寻求国会支持对叙利亚采取军事行动。以下内容是对实际英文输出的中文概述，不是重新生成的实验摘要。')
p('人工摘要包含：叙利亚官员的评论、奥巴马致信参众两院领导、寻求国会批准军事行动，以及联合国调查目标是确认是否使用化学武器而非认定使用者。')
table(['方法','选中句子序号*','ROUGE-1 F1'],[
('Lead-3','1、2、3','0.4054'),('TextRank（词重叠）','1、16、64','0.3158'),('TF-IDF 图排序','1、30、76','0.2692')],[4000,3000,2360])
p('* 此处按 1 开始计数；逐篇 JSON 中的 indices 按 0 开始。','Caption')
p('Lead-3 保留了“寻求议员意见”“致信两院领导”和“拟议授权目的”，与参考中的部分核心信息一致，但没有覆盖联合国调查目标等后文内容。')
p('词重叠 TextRank 选入联合国调查人员离境及叙利亚电视评论，覆盖了其他话题，但没有选入致信两院领导的句子，且评论段较长。TF-IDF 选入有限军事行动和伊朗警告的内容，后者不在这份参考摘要的主要要点中。')
p('该案例中词重叠方案的 ROUGE-1 F1 高于 TF-IDF，与全量平均排序不同。这说明不同新闻上的算法表现会变化，单个案例不能替代总体评价。')
h('6.3 局限与改进方向',2)
p('当前算法依赖词面重合，缺少同义词和否定语义理解；规则分句可能误切特殊缩写或标题。选取前三个高分句没有专门去重，可能包含重复信息或失去前文指代。可进一步尝试固定词数预算、句子位置先验和冗余惩罚，并进行受控对比。若依据结果调参，应先划分开发集和独立测试集，避免用同一批数据选参数又报告最优测试结果。')

page('七、代码实现、复现与实验结论')
h('7.1 代码结构与验证',2)
table(['文件','职责'],[
('load_data.py','读取 .story 文件，按 @highlight 分离正文和参考要点'),
('textrank.py','手写分词、相似度矩阵、PageRank 迭代和选句'),
('metrics.py','计算 ROUGE-1/2/L 与语料级 BLEU-4'),
('run_experiment.py','批量运行三种方法，导出指标、逐篇结果和运行配置'),
('test_experiment.py','验证数据解析、已知排名分布、孤立节点、选句与指标边界')
],[3100,6260])
p('此前已完成 4 项单元测试并全部通过，包括解析异常、已知稳态分布与孤立节点、空文本及原文顺序、指标匹配与边界情况。全量结果文件的篇数与汇总表一致。手写要求由 textrank.py 完成，未调用现成摘要器或 PageRank 实现；NumPy 仅用于基础数组运算。')
h('7.2 复现方法',2)
p('在项目文件夹打开 PowerShell，执行以下命令：')
p('python -m pip install -r requirements.txt','Code')
p('python -m unittest -v test_experiment','Code')
p('python run_experiment.py','Code')
p('结果位于 results：metrics.csv 保存详细指标，predictions.jsonl 保存逐篇摘要、参考与评分，config.json 保存配置和异常文件 ID，dataset_stats.json 保存数据统计。report.md 是简要结果。重复运行会覆盖同名结果，若需保留旧结果，可使用 --output 指定其他目录。')
h('7.3 生成式方法理解',2)
p('Encoder–Decoder 将新闻编码为内部表示，再由解码器从开始标记逐步生成词语，直到结束标记。相比直接抽取原句，它可以重组语言，但需要学习生成能力，也可能引入原文没有的信息。依照 README 的“了解”要求，本实验仅解释其原理，没有训练或评测生成式模型。')
h('7.4 实验结论',2)
p('本实验完成了从新闻读取、句子图构建、手写迭代排序到摘要评测的完整流程。4996 篇有效新闻的结果表明，Lead-3 在四项主指标上优于两种图排序方法；TF-IDF 对照整体优于词重叠 TextRank。词重叠方法虽取得更高的 ROUGE-1 召回率，但输出更长、精确率更低。算法复杂度增加并不保证摘要质量提高，需要结合数据特点、长度控制与真实案例进行解释。')
p('资料依据：项目 README.md、assets/text_rank.png、assets/encoder-decoder.png；本项目算法与指标源代码；用户本次全量运行日志及 results 中保存的实验产物。本文主结论仅使用全量固定配置实验，不混入此前 100 篇探索性参数扫描的结果。','Caption')
doc.core_properties.title='基于 TextRank 的新闻自动摘要实验报告'
doc.core_properties.subject='CNN 新闻摘要、算法流程、指标和实验结果分析'
doc.core_properties.author=''
doc.core_properties.keywords='TextRank, ROUGE, BLEU, CNN, 实验报告'
doc.save(OUT)
# Structural audit: geometry, all cells, data coverage, section/page count intent.
assert len(doc.tables)==6
assert all(sum(int(c.get(qn('w:w'))) for c in t._tbl.tblGrid)==9360 for t in doc.tables)
assert all(int(s.page_width.twips)==12240 for s in doc.sections)
print(str(OUT))
print('Structural audit passed; tables:',len(doc.tables))
