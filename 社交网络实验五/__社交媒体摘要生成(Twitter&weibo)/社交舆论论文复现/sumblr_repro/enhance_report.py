"""Enhance the generated Sumblr report with appendices, full result tables, and run log."""
import json, os
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

ROOT=Path(r"C:\Users\86134\Desktop\大四上\社交网络实验五\__社交媒体摘要生成(Twitter&weibo)\社交舆论论文复现\sumblr_repro")
DOC=ROOT/"Sumblr论文复现实验报告.docx"

def shade(cell, fill):
    tcPr=cell._tc.get_or_add_tcPr(); el=tcPr.find(qn('w:shd'))
    if el is None: el=OxmlElement('w:shd'); tcPr.append(el)
    el.set(qn('w:fill'),fill)

def table(doc, headers, rows, size=8.2):
    t=doc.add_table(rows=1, cols=len(headers)); t.style='Table Grid'; t.alignment=WD_TABLE_ALIGNMENT.CENTER
    hr=t.rows[0]
    trPr=hr._tr.get_or_add_trPr(); th=OxmlElement('w:tblHeader'); th.set(qn('w:val'),'true'); trPr.append(th)
    for i,h in enumerate(headers):
        c=hr.cells[i]; c.text=''; p=c.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=p.add_run(str(h)); r.bold=True; r.font.size=Pt(size); r.font.name='Microsoft YaHei'; r._element.rPr.rFonts.set(qn('w:eastAsia'),'Microsoft YaHei'); r.font.color.rgb=RGBColor(255,255,255); shade(c,'1F4E79'); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
    for row in rows:
        cells=t.add_row().cells
        for i,v in enumerate(row):
            c=cells[i]; c.text=''; p=c.paragraphs[0]; p.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=p.add_run(str(v)); r.font.size=Pt(size); r.font.name='Microsoft YaHei'; r._element.rPr.rFonts.set(qn('w:eastAsia'),'Microsoft YaHei'); c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
    doc.add_paragraph().paragraph_format.space_after=Pt(1)
    return t

def h(doc,text,level=1): doc.add_heading(text,level=level)
def p(doc,text): doc.add_paragraph(text)
def code(doc,text):
    q=doc.add_paragraph(style='CodeBlock'); r=q.add_run(text); r.font.name='Consolas'; r.font.size=Pt(8); r._element.rPr.rFonts.set(qn('w:eastAsia'),'Consolas')

def img(doc,path,caption,width=15.5):
    q=doc.add_paragraph(); q.alignment=WD_ALIGN_PARAGRAPH.CENTER; q.add_run().add_picture(str(ROOT/'report_assets'/path),width=Cm(width)); c=doc.add_paragraph(); c.alignment=WD_ALIGN_PARAGRAPH.CENTER; r=c.add_run(caption); r.italic=True; r.font.size=Pt(9); r.font.color.rgb=RGBColor(89,89,89)

D=Document(DOC)
D.add_page_break()
h(D,'附录 A 复现配置、依赖与目录',1)
p(D,'本附录记录本实验最终使用的工程配置、目录和运行命令，便于第三方复现。报告中的原始数据、源代码、JSON 实验结果和图表均保存在 sumblr_repro 目录中。')
table(D,['项目','最终设置'],[
['数据文件','data/turkey_earthquake_tweets.csv；原始 28,844 条，去重后 27,661 条'],
['核心参数','β=0.07；Nmax=150；mc=0.7；m=40；λ=0.4；α=2；l=3；freshness=3 days；p=10'],
['摘要预算','250 raw words；最多 25 条推文'],
['时间线','KL add-one smoothing；τ=1.012（论文可比值）；窗口按流长自动缩放；默认非重叠'],
['依赖','Python 3.12；numpy；pandas；scipy；scikit-learn；python-docx；Pillow'],
['随机性','K-means / 随机基线使用 seed=42'],
['单测','tests/test_ptf.py；test_historical.py；test_dsdr.py；test_protocol.py'],
])
h(D,'附录 B 核心算法伪代码',1)
code(D,'''Algorithm 1: Online Sumblr clustering\nInput: tweet stream, TCV set C, parameters β, Nmax, mc\nfor each tweet t=(tv, ts, w) in stream:\n    compute cosine(MaxSim) between t and each cluster centroid\n    C_p ← nearest cluster\n    MBS ← β · average_similarity(C_p)\n    if MaxSim(C_p,t) < MBS:\n        create new cluster with a new cid and IDList={cid}\n    else:\n        update C_p.sum_v, C_p.wsum_v, C_p.ts1, C_p.ts2, C_p.n, ft_set\n    delete clusters whose estimated newest 10% is older than 3 days\n    if |C| > Nmax:\n        greedily merge most similar clusters until mc fraction remains\n    store a PTF snapshot at the current α-order tick''')
code(D,'''Algorithm 2: Historical summary and TCV-Rank\nInput: end time tse, duration H\nS_end ← latest PTF snapshot at or before tse\nS_start ← latest PTF snapshot at or before tse-H\nfor each cluster C in S_end:\n    use C.IDList to find matching old clusters in S_start\n    C_window ← Definition4_Subtract(C, matching_old_clusters)\nT ← union of all C_window.ft_set\ncompute LexRank scores over cosine similarity graph on T\nfirst select highest-LexRank tweet from each cluster\nwhile summary budget not reached:\n    select argmax [ λ(n_t/n_max)LR(t) − (1−λ)avgSim(t,S) ]\nreturn extractive summary''')
h(D,'附录 C 完整实验结果索引',1)
p(D,'以下 JSON 文件为报告图表和表格的机器可读来源。')
table(D,['结果文件','对应实验','主要内容'],[
['exp_step_sweep_w3000.json','Figure 5/6','step-size 与 ROUGE/runtime'],
['exp_scalability.json','Figure 7','window size 与 runtime'],
['exp_params.json','Figure 9','β、Nmax、mc、m、λ 扫描'],
['exp_flexibility.json','Figure 10','l 与 Eq.(5) 灵活性得分'],
['exp_timeline.json','Figure 11','τ 与时间线 P/R/F1'],
['results_alldays.json','主流程','全量聚类、PTF、摘要、主指标'],
])
p(D,'图表说明：本报告中的图 1—图 10 均由 report_assets 目录中的 Pillow 脚本自动生成。图 3—图 5对应论文 Figure 5—7；图 6—图 9对应参数和 PTF 灵活性；图 10对应时间线阈值实验。')
h(D,'附录 D 复现日志与验收结果',1)
code(D,'''# 主流程\npython src/download_data.py\npython src/run.py\npython src/run.py --all-days\n\n# 完整实验\npython src/run_experiments.py --which all\n\n# 单元测试\npython tests/test_ptf.py\npython tests/test_historical.py\npython tests/test_dsdr.py\npython tests/test_protocol.py''')
table(D,['验收项','结果'],[
['PTF Table 1 验证','PASS：order 0/1/2/3/4 全部匹配论文示例'],
['Definition 4 单元测试','PASS：sum_v、wsum_v、ts1、ts2、n、ft_set 全部验证'],
['DSDR 单元测试','PASS：重构误差单调下降、优于随机子集、结果确定'],
['实验协议测试','PASS：窗口步进、采样间隔、Eq.4、runtime、250 词预算'],
['单日主流程','PASS：4,278 条推文；82 簇；ROUGE 和时间线正常'],
['全量主流程','PASS：27,661 条；132 簇；2,875 条内存簇推文；约 60 秒'],
])
p(D,'可复现性声明：由于论文原始 Twitter 数据来自历史 API 且下载页面已经失效，本报告不宣称原始实验的逐数字重现。所有偏差、替代数据、参考摘要构造方式和时间线人工参考替代均已在正文和 AUDIT.md 中明确记录。')
h(D,'附录 E 图表清单',1)
for name,desc in [('fig01_daily_volume.png','数据集日分布'),('fig02_pipeline.png','系统流水线'),('fig03_step_quality.png','step-size 与 ROUGE-1 F1'),('fig04_step_runtime.png','step-size 与 runtime'),('fig05_scalability.png','窗口规模与 runtime'),('fig06_beta.png','β 参数曲线'),('fig06_n_max.png','Nmax 参数曲线'),('fig06_mc.png','mc 参数曲线'),('fig06_m.png','m 参数曲线'),('fig06_lam.png','λ 参数曲线'),('fig07_ptf_flexibility.png','PTF 灵活性'),('fig08_timeline_tau.png','时间线 τ 扫描')]:
    if (ROOT/'report_assets'/name).exists():
        p(D,f'{name}：{desc}')
D.save(DOC)
print(DOC)
