from pypdf import PdfReader
from pathlib import Path
r=PdfReader('report_work/qa/report.pdf')
for k,p in enumerate(r.pages):
 t=p.extract_text() or '';print(k+1,len(t),t[:48].replace('\n',' / '),'TAIL',t[-70:].replace('\n',' / '))
from docx import Document
from lxml import etree
x=Document('TrustSVD论文复现实验报告.docx')
for n in ['Title','Subtitle','Normal']:
 print(n,x.styles[n].element.xml[:2200])
