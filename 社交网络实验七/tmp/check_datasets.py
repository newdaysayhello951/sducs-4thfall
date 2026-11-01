import urllib.request, concurrent.futures, json, pathlib
urls={
'filmtrust_author':'https://guoguibing.github.io/librec/datasets/filmtrust.zip',
'filmtrust_librec':'https://www.librec.net/datasets/filmtrust.zip',
'filmtrust_cornac':'https://static.preferred.ai/cornac/datasets/filmtrust/filmtrust.zip',
'librec_datasets':'https://guoguibing.github.io/librec/datasets.html',
'epinions_trustlet':'https://www.trustlet.org/downloaded_epinions.html',
'epinions_alchemy':'https://alchemy.cs.washington.edu/data/epinions/',
'ciao_author':'https://www.cse.msu.edu/~tangjili/datasetcode/truststudy.htm',
'flixster_old':'https://www.cs.sfu.ca/~sja25/personal/datasets/',
'flixster_author':'https://sites.google.com/view/mohsenjamali/home'
}
out=pathlib.Path('dataset_check');out.mkdir(exist_ok=True)
def check(pair):
 k,u=pair
 try:
  req=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req,timeout=18) as r:
   data=r.read(4000000); info={'name':k,'url':u,'final_url':r.url,'status':r.status,'bytes':len(data),'type':r.headers.get('Content-Type')}
   (out/(k+('.zip' if data[:2]==b'PK' else '.html'))).write_bytes(data)
   return info
 except Exception as e:return {'name':k,'url':u,'error':str(e)}
results=list(concurrent.futures.ThreadPoolExecutor(max_workers=9).map(check,urls.items()))
(out/'url_checks.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(results,ensure_ascii=False,indent=2))
