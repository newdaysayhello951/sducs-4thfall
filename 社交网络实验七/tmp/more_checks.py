import urllib.request,concurrent.futures,pathlib,json,re
urls={
'epinions_alchemy_archive':'https://alchemy.cs.washington.edu/data/epinions/epinions.tgz',
'flixster_new':'https://sites.google.com/view/mohsenjamali/flixter-data-set',
'douban_author':'https://www.cse.cuhk.edu.hk/irwin.king.new/pub/data/douban',
'ciao_asu':'https://www.public.asu.edu/~jtang20/datasetcode/truststudy.htm',
'ciao_msu_http':'http://www.cse.msu.edu/~tangjili/datasetcode/truststudy.htm',
'epinions_trustlet_http':'http://www.trustlet.org/downloaded_epinions.html'
}
def f(kv):
 k,u=kv
 try:
  with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=20) as r:
   d=r.read(30000000);p=pathlib.Path('dataset_check')/(k+('.tgz' if d[:2]==b'\x1f\x8b' else '.html'));p.write_bytes(d)
   return dict(name=k,url=u,final_url=r.url,status=r.status,bytes=len(d),file=str(p))
 except Exception as e:return dict(name=k,url=u,error=str(e))
r=list(concurrent.futures.ThreadPoolExecutor(max_workers=6).map(f,urls.items()));pathlib.Path('dataset_check/more_checks.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(r,ensure_ascii=False,indent=2))
for k in ['flixster_new','douban_author','ciao_asu','ciao_msu_http','epinions_trustlet_http']:
 p=pathlib.Path('dataset_check')/(k+'.html')
 if p.exists():
  print('\nLINKS',k)
  for h,l in re.findall(r'<a[^>]+href=[\"\x27]([^\"\x27]+)[\"\x27][^>]*>(.*?)</a>',p.read_text(encoding='utf-8',errors='replace'),re.S):
   if any(x in (h+l).lower() for x in ['download','drive.google','dropbox','zip','tar','dataset','rating','trust','douban','flixster']):print(h,re.sub('<[^>]+>','',l)[:140])
