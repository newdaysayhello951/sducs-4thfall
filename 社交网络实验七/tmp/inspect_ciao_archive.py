import zipfile,io,hashlib,json,pathlib,numpy as np
from scipy.io import loadmat
p=pathlib.Path('dataset_check/retry/ciao_wayback_zip.zip')
summary={}
with zipfile.ZipFile(p) as z:
 print('ZIP_FILES',z.namelist())
 for f in z.infolist():
  if f.is_dir():continue
  d=z.read(f); print(f.filename,len(d),hashlib.sha256(d).hexdigest())
  if f.filename.endswith('.mat'):
   mats=loadmat(io.BytesIO(d));
   for key,a in mats.items():
    if key.startswith('__'):continue
    print('MATRIX',key,a.shape,'HEAD',a[:3].tolist())
    if a.ndim==2 and a.shape[1]>=4:
     st=dict(rows=len(a),users=len(np.unique(a[:,0])),items=len(np.unique(a[:,1])),rating_values=np.unique(a[:,3],return_counts=True)[0].tolist(),unique_pairs=len(np.unique(a[:,:2],axis=0)))
     print('RATING_STATS',st);summary[f.filename]=st
    elif a.ndim==2:summary[f.filename]=dict(rows=len(a),columns=a.shape[1])
  elif f.filename.lower().endswith('.txt') and len(d)<10000:print(d.decode(errors='replace'))
pathlib.Path('dataset_check/retry/ciao_archive_stats.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
