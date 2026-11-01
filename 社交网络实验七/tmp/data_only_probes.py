import urllib.request, concurrent.futures,pathlib
# Data-only paths and a source publication; never fetch any model implementation.
urls={
'ciao_msu_zip':'https://www.cse.msu.edu/~tangjili/datasetcode/ciao.zip',
'ciao_cornac_zip':'https://static.preferred.ai/cornac/datasets/ciao/ciao.zip',
'ciao_libbrec_mat':'https://raw.githubusercontent.com/guoguibing/librec/master/data/ciao/rating.mat',
'flixster_librec_rating':'https://raw.githubusercontent.com/guoguibing/librec/master/data/flixster/ratings.txt',
'ciao_sreps':'https://raw.githubusercontent.com/WSPTTH/SREPS/master/data/ciao/ratings.txt',
'ciao_msc_rating':'https://raw.githubusercontent.com/mlsys-lab-sogang/Social-Rec-Sys/master/Transformer_modified/dataset/ciao/rating.mat',
}
def f(kv):
 k,u=kv
 try:
  with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=15) as r:
   d=r.read(20000000)
   if not d.startswith(b'<'):
    pathlib.Path('dataset_check/'+k+'.bin').write_bytes(d)
   return(k,r.status,len(d),d[:20])
 except Exception as e:return(k,str(e))
print(list(concurrent.futures.ThreadPoolExecutor(max_workers=6).map(f,urls.items())))
