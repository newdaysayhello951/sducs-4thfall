import urllib.request,pathlib,json,concurrent.futures
p=pathlib.Path('dataset_check/retry/third_pass')
urls={'flixster_sfu_binary_archive':'https://web.archive.org/cdx/search/cdx?url=www.sfu.ca/~sja25/datasets/flixster.zip&output=json&filter=statuscode:200&collapse=digest','flixster_cs_binary_archive':'https://web.archive.org/cdx/search/cdx?url=www.cs.sfu.ca/~sja25/datasets/flixster.zip&output=json&filter=statuscode:200&collapse=digest','flixster_ubc_binary_archive':'https://web.archive.org/cdx/search/cdx?url=www.cs.ubc.ca/~jamalim/datasets/flixster.zip&output=json&filter=statuscode:200&collapse=digest'}
def f(kv):
 k,u=kv
 try:
  with urllib.request.urlopen(u,timeout=20) as r:d=r.read(1000000)
  (p/(k+'.json')).write_bytes(d);return {'name':k,'result':d.decode('utf8',errors='replace')[:1500]}
 except Exception as e:return {'name':k,'error':str(e)}
r=list(concurrent.futures.ThreadPoolExecutor(max_workers=3).map(f,urls.items()));(p/'binary_checks.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
