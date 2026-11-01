from pathlib import Path
from docx import Document
from pypdf import PdfReader
import hashlib,json,re
root=Path.cwd();doc=Document(root/'TrustSVD论文复现实验报告.docx');pdf=PdfReader(root/'report_work/qa/final-report.pdf')
headings=[p.text for p in doc.paragraphs if p.style.name.startswith('Heading')]
assert not any(re.match(r'^\s*(?:\d+[.、]|[一二三四五六七八九十]+[、．])',h) for h in headings)
assert len(pdf.pages)==14
assert all(len(p.extract_text() or '')>100 for p in pdf.pages)
assert len(doc.inline_shapes)==13 and len(doc.tables)==16
for t in doc.tables:assert t.rows[0]._tr.xpath('./w:trPr/w:tblHeader')
changed=[]
for i in range(1,15):
 a=root/f'report_work/qa/final-page-{i:02d}.png';b=root/f'report_work/qa/verified-page-{i:02d}.png'
 if hashlib.sha256(a.read_bytes()).digest()!=hashlib.sha256(b.read_bytes()).digest():changed.append(i)
r={'pages':len(pdf.pages),'tables':len(doc.tables),'images':len(doc.inline_shapes),'heading_numbering':False,'headings':headings,'changed_pages_since_last_visual_review':changed,'renderer':'WPS COM ExportAsFixedFormat followed by bundled Poppler; packaged render_docx.py failed due Windows temporary directory permissions and unavailable LibreOffice','docx_sha256':hashlib.sha256((root/'TrustSVD论文复现实验报告.docx').read_bytes()).hexdigest()}
(root/'report_work/qa/verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(r,ensure_ascii=False,indent=2))
