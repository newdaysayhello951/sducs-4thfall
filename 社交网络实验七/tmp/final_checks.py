import urllib.request,concurrent.futures,pathlib,json,zipfile,re
urls={
'epinions_ratings':'https://static.preferred.ai/cornac/datasets/epinions/ratings_data.zip',
'epinions_trust':'https://static.preferred.ai/cornac/datasets/epinions/trust_data.zip',
'ciao_msu_nowww':'https://cse.msu.edu/~tangjili/datasetcode/truststudy.htm',
'ciao_msu_new':'https://www.cse.msu.edu/~tangjili/trust.html',
'graphrec_tree':'https://api.github.com/repos/wenqifan03/GraphRec-WWW19/git/trees/master?recursive=1'
}
def f(kv):
 k,u=kv
 try:
  with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=20) as r:
   d=r.read(15000000);p=pathlib.Path('dataset_check')/(k+('.zip' if d[:2]==b'PK' else '.txt'));p.write_bytes(d)
   info={'name':k,'status':r.status,'bytes':len(d),'final_url':r.url}
   if d[:2]==b'PK':
    with zipfile.ZipFile(p) as z:
     info['files']=[{'name':n,'rows':len(z.read(n).splitlines())} for n in z.namelist() if not n.endswith('/')]
     for n in z.namelist():
      if n.endswith('.txt'):
       target=pathlib.Path('datasets/epinions_665k')/pathlib.Path(n).name;target.parent.mkdir(exist_ok=True,parents=True);target.write_bytes(z.read(n))
   elif k=='graphrec_tree':info['data_paths']=[x['path'] for x in json.loads(d).get('tree',[]) if any(y in x['path'].lower() for y in ['ciao','epinions','readme'])]
   else:info['links']=[h for h in re.findall(r'href=[\"\x27]([^\"\x27]+)',d.decode(errors='replace')) if any(y in h for y in ['zip','mat','trust','ciao','epinion'])]
   return info
 except Exception as e:return {'name':k,'error':str(e)}
r=list(concurrent.futures.ThreadPoolExecutor(max_workers=5).map(f,urls.items()));pathlib.Path('dataset_check/final_checks.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(r,ensure_ascii=False,indent=2))
