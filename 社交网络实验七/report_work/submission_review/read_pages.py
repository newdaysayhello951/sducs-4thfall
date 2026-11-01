from pypdf import PdfReader
import json
from pathlib import Path
r=PdfReader('report_work/submission_review/submission.pdf');a=[]
for k,p in enumerate(r.pages):
 t=p.extract_text() or '';a.append({'page':k+1,'chars':len(t),'start':t[:130],'end':t[-180:]})
print(json.dumps(a,ensure_ascii=False,indent=2));Path('report_work/submission_review/page_text.json').write_text(json.dumps(a,ensure_ascii=False,indent=2),encoding='utf8')
