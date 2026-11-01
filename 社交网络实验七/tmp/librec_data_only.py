import urllib.request,concurrent.futures,pathlib
base='https://raw.githubusercontent.com/guoguibing/librec/master/'
paths=['librec/demo/Datasets/Ciao/ratings.txt','librec/demo/Datasets/Ciao/trust.txt','librec/demo/Datasets/Flixster/ratings.txt','librec/demo/Datasets/Flixster/trust.txt','librec/demo/Datasets/Ciao/README.txt','librec/demo/Datasets/FilmTrust/ratings.txt']
def f(p):
 try:
  with urllib.request.urlopen(urllib.request.Request(base+p,headers={'User-Agent':'Mozilla/5.0'}),timeout=15) as r:
   d=r.read(15000000);name=p.replace('/','_');pathlib.Path('dataset_check/'+name).write_bytes(d);return p,len(d)
 except Exception as e:return p,str(e)
print(list(concurrent.futures.ThreadPoolExecutor(max_workers=6).map(f,paths)))
