from pathlib import Path
from collections import Counter
import json, csv, re, statistics, hashlib
import openpyxl
from docx import Document

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'outputs'/'问卷分析'
OUT.mkdir(parents=True,exist_ok=True)
src=ROOT/'SmartCampus_P3_问卷原始数据.xlsx'
w=openpyxl.load_workbook(src,data_only=True)
rows=list(w.worksheets[0].values)
headers=list(rows[0][:31])
records=[dict(zip(headers,r[:31])) for r in rows[1:] if r[0]]
definitions={r[0]:{'type':r[1],'title':r[2],'options':r[3].split('\n')} for r in list(w.worksheets[1].values)[1:] if r[0] and re.fullmatch(r'Q\d+',r[0])}
qcols=[k for k in headers if re.match('Q',k)]
assert len(records)==11
assert len({r['编号'] for r in records})==len(records)
assert all(r['答卷性质']=='real' and r['符合目标用户'] is True and r['同意参与'] is True for r in records)
assert len({tuple(r[k] for k in qcols) for r in records})==len(records)
issues=[]
for r in records:
 assert sorted(r[f'Q11_{i}'] for i in range(1,6))==[1,2,3,4,5]
 for q in definitions:
  if q in ['Q11','Q22']: continue
  val=r[q]
  if val is None: continue
  parts=val.split('；') if definitions[q]['type']=='多选题' else [val]
  assert len(parts)==len(set(parts))
  assert all(p in definitions[q]['options'] for p in parts),(r['编号'],q,parts)
  if q=='Q21': assert len(parts)<=3
  if q=='Q20' and '如果控制机制充分，我愿意共享以上全部信息' in parts: assert len(parts)==1

# Compare every questionnaire response to the original Word tables, by participant ID.
doc=Document(ROOT/'SmartCampus_P3_作业四_修订版.docx')
mapping={2:['Q1','Q2','Q3','Q4'],3:['Q5','Q6','Q7'],4:['Q8','Q9'],5:['Q10'],6:[f'Q11_{i}' for i in range(1,6)],7:['Q12','Q13','Q14'],8:['Q15','Q16'],9:['Q17'],10:['Q18','Q19'],11:['Q20'],12:['Q21'],13:['Q22']}
byid={r['编号']:r for r in records}
diffs=[]; compared=0
for tableidx,fields in mapping.items():
 for row in doc.tables[tableidx].rows[1:]:
  rid=row.cells[0].text.strip()
  for j,k in enumerate(fields,1):
   a=row.cells[j].text.strip().replace('\r\n','\n')
   v=byid[rid][k]
   b='未作答' if v is None else str(v).strip().replace('\r\n','\n')
   compared+=1
   if a!=b: diffs.append([rid,k,a,b])

stats=[]
for q,d in definitions.items():
 if q in ['Q11','Q22']: continue
 vals=[r[q] for r in records if r[q] is not None]
 cnt=Counter(p for v in vals for p in (v.split('；') if d['type']=='多选题' else [v]))
 for option in d['options']:
  stats.append({'q':q,'option':option,'count':cnt[option],'valid':len(vals),'pct':cnt[option]/len(vals),'missing':len(records)-len(vals),'type':d['type']})
rank=[]
for i in range(1,6):
 label=definitions['Q11']['options'][i-1].split('：',1)[1].split('，')[0]
 v=[r[f'Q11_{i}'] for r in records]
 rank.append({'field':f'Q11_{i}','label':label,'n':len(v),'score':sum(5-a for a in v),'mean':statistics.mean(v),'median':statistics.median(v),'first':v.count(1),'last':v.count(5),'dist':[v.count(j) for j in range(1,6)]})
rank.sort(key=lambda x:-x['score'])
assert sum(x['score'] for x in rank)==110
assert sum(x['first'] for x in rank)==11
assert sum(x['last'] for x in rank)==11
assert not diffs, diffs
missing={q:[r['编号'] for r in records if r[q] is None] for q in qcols if any(r[q] is None for r in records)}
payload={'headers':headers,'records':records,'definitions':definitions,'stats':stats,'rank':rank,'audit':{'n':len(records),'compared':compared,'diffs':diffs,'missing':missing,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest()},'source':src.name}
(Path(__file__).parent/'analysis.json').write_text(json.dumps(payload,ensure_ascii=False,default=str,indent=2),encoding='utf-8')
print(json.dumps({'n':len(records),'compared_answers':compared,'differences':diffs,'missing':missing,'rank':rank},ensure_ascii=False,indent=2))
