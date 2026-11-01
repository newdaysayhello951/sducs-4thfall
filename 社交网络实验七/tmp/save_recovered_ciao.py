from pathlib import Path
from scipy.io import loadmat
import zipfile,numpy as np,json,hashlib
out=Path('dataset_check/retry')
with zipfile.ZipFile(out/'ciao_wayback_zip.zip') as z:
 for n in ['ciao/rating.mat','ciao/trustnetwork.mat']:
  p=out/'ciao_original'/Path(n).name;p.parent.mkdir(exist_ok=True);p.write_bytes(z.read(n))
a=loadmat(out/'ciao_original/rating.mat')['rating'];t=loadmat(out/'ciao_original/trustnetwork.mat')['trustnetwork']
stats={'raw_rows':len(a),'raw_users':len(np.unique(a[:,0])),'raw_items':len(np.unique(a[:,1])),'trust_edges':len(t),
       'zero_ratings':int(sum(a[:,3]==0)),'positive_rows':int(sum(a[:,3]>0)),
       'positive_unique_pairs':len(np.unique(a[a[:,3]>0,:2],axis=0)),
       'raw_duplicate_extra_rows':len(a)-len(np.unique(a[:,:2],axis=0)),
       'sha256_zip':hashlib.sha256((out/'ciao_wayback_zip.zip').read_bytes()).hexdigest(),
       'paper_counts':{'users':7375,'items':99746,'ratings':280391,'trust_edges':111781}}
(out/'ciao_recovered_verification.json').write_text(json.dumps(stats,indent=2),encoding='utf-8');print(json.dumps(stats,indent=2))
