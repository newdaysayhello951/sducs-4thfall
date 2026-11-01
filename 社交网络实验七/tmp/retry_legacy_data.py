import urllib.request,urllib.parse,concurrent.futures,pathlib,json,re,hashlib,zipfile
out=pathlib.Path('dataset_check/retry')
urls={
'flixster_sfu_zip':'https://www.cs.sfu.ca/~sja25/personal/datasets/flixster.zip',
'flixster_ubc_zip':'https://www.cs.ubc.ca/~jamalim/datasets/flixster.zip',
'old_asu_all_archive':'https://web.archive.org/cdx/search/cdx?'+urllib.parse.urlencode({'url':'www.public.asu.edu/~jtang20/datasetcode/*','output':'json','collapse':'urlkey','limit':1000}),
'old_ciao_zip_history':'https://web.archive.org/cdx/search/cdx?'+urllib.parse.urlencode({'url':'www.cse.msu.edu/~tangjili/datasetcode/ciao.zip','output':'json','filter':'statuscode:200','collapse':'digest'}),
}
def f(kv):
 k,u=kv
 try:
  with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as r:
   d=r.read(100000000);ext='.zip' if d[:2]==b'PK' else '.txt';(out/(k+ext)).write_bytes(d);info=dict(name=k,status=r.status,bytes=len(d),url=r.url)
   if ext=='.txt':info['text']=d.decode(errors='replace')[:10000]
   else:
    with zipfile.ZipFile(out/(k+ext)) as z:info['files']=[dict(name=x.filename,size=x.file_size) for x in z.infolist()]
   return info
 except Exception as e:return dict(name=k,error=str(e))
r=list(concurrent.futures.ThreadPoolExecutor(max_workers=4).map(f,urls.items()));(out/'legacy_sources.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r,indent=2))
with zipfile.ZipFile(out/'ciao_wayback_zip.zip') as z:
 for n,old in [('ciao/rating.mat','dataset_check/ciao_rating.mat'),('ciao/trustnetwork.mat','dataset_check/ciao_trust.mat')]:print('ORIGINAL_MIRROR_IDENTICAL',n,z.read(n)==pathlib.Path(old).read_bytes())
