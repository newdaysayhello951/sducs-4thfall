import sys
from docx import Document
path = r'C:\Users\86134\Desktop\大四上\人机交互独立实验10 12\人机交互实验课作业3-报告.docx'
doc = Document(path)
sys.stdout.reconfigure(encoding='utf-8')
for i, p in enumerate(doc.paragraphs):
    t = p.text.strip()
    if t:
        print(f'{i}|{p.style.name}|{t}')
print('\n=== TABLES ===')
for ti, tbl in enumerate(doc.tables):
    print(f'TABLE {ti}: rows={len(tbl.rows)} cols={len(tbl.columns)}')
