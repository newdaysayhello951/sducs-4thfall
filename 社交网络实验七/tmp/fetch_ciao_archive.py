import urllib.request,pathlib,ssl,json,concurrent.futures
out=pathlib.Path('dataset_check/retry')
def get(name,url,context=None):
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'}),context=context,timeout=30) as r:
   d=r.read(20000000);ext='.zip' if d[:2]==b'PK' else '.html';(out/(name+ext)).write_bytes(d)
   return dict(name=name,status=r.status,bytes=len(d),url=r.url,preview=None if ext=='.zip' else d.decode(errors='replace')[:4000])
 except urllib.error.HTTPError as e:return dict(name=name,error=str(e),retry_after=e.headers.get('Retry-After'))
 except Exception as e:return dict(name=name,error=str(e))
ctx=ssl.create_default_context();ctx.maximum_version=ssl.TLSVersion.TLSv1_2
jobs=[('ciao_wayback_zip','https://web.archive.org/web/20220714012422id_/https://www.cse.msu.edu/~tangjili/datasetcode/ciao.zip',None),('ciao_tls12','https://www.cse.msu.edu/~tangjili/datasetcode/ciao.zip',ctx)]
r=list(concurrent.futures.ThreadPoolExecutor(max_workers=2).map(lambda x:get(*x),jobs));(out/'archive_download_checks.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r,indent=2))
