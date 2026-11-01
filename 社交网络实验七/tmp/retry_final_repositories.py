import urllib.request,urllib.parse,pathlib,json,concurrent.futures
out=pathlib.Path('dataset_check/retry')
urls={
'flixter_rating_file':'https://labs.fme.aegean.gr/ideal/wp-content/uploads/datasets/flixter/Flixter_ratings.csv.bz2',
'flixter_trust_file':'http://labs.fme.aegean.gr/ideal/wp-content/uploads/datasets/flixter/Flixter_trust.csv.bz2',
'zenodo_flixster':'https://zenodo.org/api/records?'+urllib.parse.urlencode({'q':'flixster','size':10}),
'dataverse_flixster':'https://dataverse.harvard.edu/api/search?'+urllib.parse.urlencode({'q':'flixster','type':'dataset','per_page':20})}
def f(kv):
 k,u=kv
 try:
  with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as r:d=r.read(60000000)
  (out/(k+('.bz2' if d[:3]==b'BZh' else '.json'))).write_bytes(d)
  info=dict(name=k,bytes=len(d))
  if k=='zenodo_flixster':info['records']=[dict(id=x['id'],title=x['metadata']['title'],files=[{'name':v['key'],'size':v['size'],'url':v['links']['self']} for v in x.get('files',[])]) for x in json.loads(d).get('hits',{}).get('hits',[])]
  elif k=='dataverse_flixster':info['records']=json.loads(d).get('data',{}).get('items',[])
  return info
 except Exception as e:return dict(name=k,error=str(e))
r=list(concurrent.futures.ThreadPoolExecutor(max_workers=4).map(f,urls.items()));(out/'additional_repository_checks.json').write_text(json.dumps(r,indent=2),encoding='utf-8');print(json.dumps(r,indent=2))
