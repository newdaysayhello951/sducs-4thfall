import urllib.request,concurrent.futures,pathlib
urls={
'ciao_author_archive':'https://guoguibing.github.io/librec/datasets/ciao.zip',
'ciao_librec_data':'https://raw.githubusercontent.com/guoguibing/librec/1.3/data/ciao/ratings.txt',
'ciao_sreps_data':'https://raw.githubusercontent.com/WSPTTH/SREPS/master/dataset/ciao/ratings.txt',
'ciao_msu_file':'https://www.cse.msu.edu/~tangjili/datasetcode/ciao/rating.mat',
'flixster_author_archive':'https://guoguibing.github.io/librec/datasets/flixster.zip',
'flixster_cornac_archive':'https://static.preferred.ai/cornac/datasets/flixster/flixster.zip',
}
def f(kv):
 k,u=kv
 try:
  with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=15) as r:
   d=r.read(15000000);p=pathlib.Path('dataset_check/'+k+'.bin');p.write_bytes(d);return (k,r.status,len(d),d[:20])
 except Exception as e:return (k,str(e))
print(list(concurrent.futures.ThreadPoolExecutor(max_workers=6).map(f,urls.items())))
