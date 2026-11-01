import urllib.request,concurrent.futures,pathlib,re,json,tarfile
urls={
'epinions_headers':'https://alchemy.cs.washington.edu/data/epinions/epinions.tgz',
'flixster_drive':'https://drive.google.com/embeddedfolderview?id=0B2B7102TE1nbdjBTaGFCUkNtU3M',
'ciao_cornac':'https://raw.githubusercontent.com/PreferredAI/cornac/master/cornac/datasets/ciao.py',
'epinions_cornac':'https://raw.githubusercontent.com/PreferredAI/cornac/master/cornac/datasets/epinions.py'
}
def f(kv):
 k,u=kv
 try:
  req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'},method='HEAD' if k=='epinions_headers' else 'GET')
  with urllib.request.urlopen(req,timeout=20) as r:
   d=r.read();pathlib.Path('dataset_check/'+k+'.txt').write_bytes(d)
   return {'name':k,'status':r.status,'size':len(d),'length':r.headers.get('Content-Length'),'text':d.decode(errors='replace')[:6000] if 'cornac' in k else re.findall(r'href="([^"]+)"',d.decode(errors='replace'))}
 except Exception as e:return {'name':k,'error':str(e)}
print(json.dumps(list(concurrent.futures.ThreadPoolExecutor(max_workers=4).map(f,urls.items())),ensure_ascii=False,indent=2))
try:
 with tarfile.open('dataset_check/epinions_alchemy_archive.tgz','r:gz') as t:
  for n in t:
   print('TAR',n.name,n.size)
except Exception as e:print('TARERROR',str(e))
