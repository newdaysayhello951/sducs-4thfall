import urllib.request,urllib.parse,pathlib,json,concurrent.futures,re
out=pathlib.Path('dataset_check/retry')
urls={
'flixster_socialfalcon_https':'https://labs.fme.aegean.gr/ideal/socialfalcon-datasets/',
'flixster_socialfalcon_http':'http://labs.fme.aegean.gr/ideal/socialfalcon-datasets/',
'flixster_socialfalcon_archive':'https://web.archive.org/cdx/search/cdx?'+urllib.parse.urlencode({'url':'labs.fme.aegean.gr/ideal/socialfalcon-datasets/*','output':'json','filter':'statuscode:200','collapse':'urlkey','limit':1000})}
def f(kv):
 k,u=kv
 try:
  with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=20) as r:d=r.read(2000000)
  (out/(k+'.txt')).write_bytes(d)
  return dict(name=k,bytes=len(d),text=d.decode(errors='replace')[:9000])
 except Exception as e:return dict(name=k,error=str(e))
r=list(concurrent.futures.ThreadPoolExecutor(max_workers=3).map(f,urls.items()));(out/'socialfalcon_checks.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r,indent=2))
