import urllib.request,urllib.parse,concurrent.futures,pathlib,json,re
out=pathlib.Path('dataset_check/retry')
urls={
'figshare_metadata':'https://api.figshare.com/v2/articles/5677741',
'librec_dataset_listing':'https://github.com/guoguibing/librec/tree/master/librec/demo/Datasets',
'flixster_snapshot':'https://web.archive.org/web/20110415084158id_/http://www.cs.sfu.ca:80/~sja25/personal/datasets/',
'ciao_asu_archive':'https://web.archive.org/cdx/search/cdx?'+urllib.parse.urlencode({'url':'www.public.asu.edu/~jtang20/datasetcode/*','output':'json','filter':['statuscode:200','original:.*[cC]iao.*'],'collapse':'urlkey'},doseq=True),
'ciao_msu_archive':'https://web.archive.org/cdx/search/cdx?'+urllib.parse.urlencode({'url':'cse.msu.edu/~tangjili/datasetcode/*','output':'json','filter':['statuscode:200','original:.*[cC]iao.*'],'collapse':'urlkey'},doseq=True),
}
def f(kv):
 k,u=kv
 try:
  with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as r:
   d=r.read(5000000);(out/(k+'.txt')).write_bytes(d);info={'name':k,'url':u,'bytes':len(d),'status':r.status}
   if k=='figshare_metadata':
    info['files']=json.loads(d).get('files',[])
   elif k=='librec_dataset_listing': info['paths']=sorted(set(re.findall(r'[^"<>\\ ]*(?:[cC]iao|[fF]lixster)[^"<>\\ ]*',d.decode(errors='replace'))))[:30]
   else: info['content']=d.decode(errors='replace')[:6000]
   return info
 except Exception as e:return {'name':k,'error':str(e)}
r=list(concurrent.futures.ThreadPoolExecutor(max_workers=5).map(f,urls.items()));(out/'new_sources.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(r,ensure_ascii=False,indent=2))
