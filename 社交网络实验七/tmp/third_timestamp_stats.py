import numpy as np,json,pathlib,urllib.request,concurrent.futures,scipy.io,hashlib
out=pathlib.Path('dataset_check/retry/third_pass')
a=np.loadtxt(out/'ciao_timestamp.txt');print('timestamp_txt',a.shape,'users',len(np.unique(a[:,0])),'items',len(np.unique(a[:,1])))
urls={
'ciao_informs.mat':'https://raw.githubusercontent.com/INFORMSJoC/2024.0682/main/data/raw/Ciao/rating_with_timestamp.mat',
'ciao_rest.mat':'https://raw.githubusercontent.com/DMIRLAB-Group/REST/main/datasets/Ciao/rating_with_timestamp.mat',
'ciao_informs_trust.mat':'https://raw.githubusercontent.com/INFORMSJoC/2024.0682/main/data/raw/Ciao/trust.mat'}
def f(kv):
 k,u=kv
 try:
  with urllib.request.urlopen(u,timeout=25) as r:d=r.read(25000000)
  (out/k).write_bytes(d);m=scipy.io.loadmat(out/k);v={n:{'shape':list(x.shape),'users':len(np.unique(x[:,0])),'items':len(np.unique(x[:,1]))} for n,x in m.items() if not n.startswith('__')};return dict(file=k,sha256=hashlib.sha256(d).hexdigest(),arrays=v)
 except Exception as e:return dict(file=k,error=str(e))
r=list(concurrent.futures.ThreadPoolExecutor(max_workers=3).map(f,urls.items()));(out/'timestamp_stats.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
