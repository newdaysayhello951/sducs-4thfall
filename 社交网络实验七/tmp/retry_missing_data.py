import urllib.request,concurrent.futures,pathlib,json
out=pathlib.Path('dataset_check/retry');out.mkdir(parents=True,exist_ok=True)
urls={
'ciao_original':'https://www.cse.msu.edu/~tangjili/datasetcode/ciao.zip',
'ciao_timestamp':'https://cse.msu.edu/~tangjili/datasetcode/ciao_with_rating_timestamp_txt.zip',
'ciao_archive':'https://web.archive.org/cdx/search/cdx?url=www.cse.msu.edu/~tangjili/datasetcode/ciao*.zip&output=json&filter=statuscode:200&collapse=urlkey',
'flixster_archive':'https://web.archive.org/cdx/search/cdx?url=www.cs.sfu.ca/~sja25/personal/datasets/*&output=json&filter=statuscode:200&collapse=urlkey',
'hf_flixster':'https://huggingface.co/api/datasets?search=flixster',
'hf_ciao':'https://huggingface.co/api/datasets?search=ciao',
'github_data_tree':'https://api.github.com/repos/guoguibing/librec/git/trees/master?recursive=1'
}
def f(kv):
 k,u=kv
 try:
  with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as r:
   d=r.read(15000000);ext='.zip' if d[:2]==b'PK' else '.json';(out/(k+ext)).write_bytes(d)
   info=dict(name=k,url=u,status=r.status,bytes=len(d))
   if k=='github_data_tree': info['data_paths']=[x['path'] for x in json.loads(d).get('tree',[]) if any(s in x['path'].lower() for s in ['ciao','flixster']) and not x['path'].endswith(('.java','.py'))]
   elif k.startswith('hf_'):info['datasets']=[x['id'] for x in json.loads(d)]
   elif ext=='.json':info['preview']=d.decode(errors='replace')[:1500]
   return info
 except Exception as e:return dict(name=k,error=str(e))
r=list(concurrent.futures.ThreadPoolExecutor(max_workers=7).map(f,urls.items()));(out/'checks.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(r,ensure_ascii=False,indent=2))
