import urllib.request,pathlib,concurrent.futures,json,re
out=pathlib.Path('dataset_check/retry/third_pass')
urls={
'ciao_timestamp.txt':'https://media.githubusercontent.com/media/ljf012/GNN-DSR/master/datasets/Ciao/rating_with_timestamp.txt',
'ciao_raw_tree.html':'https://github.com/INFORMSJoC/2024.0682/tree/main/data/raw/Ciao',
'ciao_rest_tree.html':'https://github.com/DMIRLAB-Group/REST/tree/main/datasets/Ciao',
'flixster_ubc_archive.json':'https://web.archive.org/cdx/search/cdx?url=www.cs.ubc.ca/~jamalim/datasets/*&output=json&filter=statuscode:200&collapse=urlkey'}
def f(kv):
 k,u=kv
 try:
  with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=30) as r:d=r.read(25000000)
  (out/k).write_bytes(d)
  if k.endswith('.html'):return {'file':k,'paths':sorted(set(re.findall(r'"path":"([^"\n]+)"',d.decode('utf8'))))}
  return {'file':k,'bytes':len(d),'head':d[:200].decode('utf8',errors='replace')}
 except Exception as e:return {'file':k,'error':str(e)}
r=list(concurrent.futures.ThreadPoolExecutor(max_workers=4).map(f,urls.items()));(out/'checks.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
