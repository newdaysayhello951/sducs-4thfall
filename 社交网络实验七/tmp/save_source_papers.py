from pathlib import Path
import urllib.request,concurrent.futures,shutil
out=Path('references');out.mkdir(exist_ok=True)
urls={
'2007_pmf.pdf':'https://papers.nips.cc/paper/2007/file/d7322ed717dedf1eb4e6e52a37ea7bcd-Paper.pdf',
'2008_svdpp.pdf':'https://people.engr.tamu.edu/huangrh/Spring16/papers_course/matrix_factorization.pdf'}
def f(kv):
 n,u=kv
 try:
  with urllib.request.urlopen(u,timeout=20) as r:d=r.read()
  assert d[:4]==b'%PDF';(out/n).write_bytes(d);return n,len(d)
 except Exception as e:return n,str(e)
print(list(concurrent.futures.ThreadPoolExecutor(max_workers=2).map(f,urls.items())))
shutil.copyfile('dataset_check/trustmf_paper.pdf',out/'2013_trustmf.pdf')
