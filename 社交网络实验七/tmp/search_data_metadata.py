import urllib.request,urllib.parse,concurrent.futures,json,pathlib
queries=['Flixter_ratings.csv','409803','280391']
def f(q):
 try:
  u='https://grep.app/api/search?'+urllib.parse.urlencode({'q':q})
  with urllib.request.urlopen(u,timeout=20) as r:d=json.load(r)
  # Display metadata only; never display model implementation snippets.
  return dict(query=q,total=d.get('hits',{}).get('total'),paths=[{'repo':x['repo'],'path':x['path']} for x in d.get('hits',{}).get('hits',[])])
 except Exception as e:return dict(query=q,error=str(e))
r=list(concurrent.futures.ThreadPoolExecutor(max_workers=3).map(f,queries));p=pathlib.Path('dataset_check/retry/third_pass');p.mkdir(exist_ok=True);(p/'code_index_metadata.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r,indent=2))
