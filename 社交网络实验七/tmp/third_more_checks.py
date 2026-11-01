import urllib.request,pathlib,re,json,concurrent.futures
p=pathlib.Path('dataset_check/retry/third_pass')
urls={'dtmf_tree':'https://github.com/EnnengYang/DTMF/tree/master/Dataset','recq_tree':'https://github.com/Coder-Yu/RecQ/tree/master/dataset','flixster_archive':'https://web.archive.org/cdx/search/cdx?url=www.cs.ubc.ca/~jamalim/datasets/*&output=json&filter=statuscode:200&collapse=urlkey','tang_new':'https://www.cse.msu.edu/~tangjili/trust.html'}
def f(kv):
 k,u=kv
 try:
  with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as r:d=r.read(5000000)
  (p/(k+'.txt')).write_bytes(d);s=d.decode('utf8',errors='replace');return {'name':k,'bytes':len(d),'paths':sorted(set(re.findall(r'"path":"([^"\n]+)"',s))),'links':re.findall(r'href=[\"\x27]([^\"\x27]+)',s) if k=='tang_new' else s[:1000] if k=='flixster_archive' else []}
 except Exception as e:return {'name':k,'error':str(e)}
r=list(concurrent.futures.ThreadPoolExecutor(max_workers=4).map(f,urls.items()));(p/'more_checks.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
