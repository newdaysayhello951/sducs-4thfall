import urllib.request, concurrent.futures,pathlib,json
urls={
 'trustmf_paper':'https://www.ijcai.org/Proceedings/13/Papers/404.pdf',
 'ciao_readme':'https://raw.githubusercontent.com/mlsys-lab-sogang/Social-Rec-Sys/main/Transformer_modified/dataset/ciao/README.txt',
 'ciao_rating':'https://raw.githubusercontent.com/mlsys-lab-sogang/Social-Rec-Sys/main/Transformer_modified/dataset/ciao/rating.mat',
 'ciao_trust':'https://raw.githubusercontent.com/mlsys-lab-sogang/Social-Rec-Sys/main/Transformer_modified/dataset/ciao/trustnetwork.mat',
}
def f(kv):
 k,u=kv
 try:
  with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as r:
   d=r.read();p=pathlib.Path('dataset_check')/(k+('.pdf' if k.endswith('paper') else '.mat' if k in ['ciao_rating','ciao_trust'] else '.txt'));p.write_bytes(d);return (k,len(d))
 except Exception as e:return(k,str(e))
print(list(concurrent.futures.ThreadPoolExecutor(max_workers=4).map(f,urls.items())))
