from pathlib import Path
import scipy.io,numpy as np,json,hashlib
source=Path('dataset_check/retry/ciao_original');dest=Path('datasets/ciao');dest.mkdir(exist_ok=True)
a=scipy.io.loadmat(source/'rating.mat')['rating'];t=scipy.io.loadmat(source/'trustnetwork.mat')['trustnetwork'];keep=(a[:,3]>=1)&(a[:,3]<=5)
np.savetxt(dest/'ratings.txt',a[keep][:,[0,1,3]],fmt='%d');np.savetxt(dest/'trust.txt',t,fmt='%d')
meta={'source':'https://web.archive.org/web/20220714012422id_/https://www.cse.msu.edu/~tangjili/datasetcode/ciao.zip','raw_ratings':len(a),'excluded_out_of_range':int((~keep).sum()),'retained_ratings':int(keep.sum()),'trust_edges':len(t),'rule':'Keep ratings within declared range 1..5; retain all duplicates and all observed trust edges. No sampling.','user_authorization':'2026-10-26: use downloaded Ciao; omit Flixster','sha256':{x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in [source/'rating.mat',source/'trustnetwork.mat',dest/'ratings.txt',dest/'trust.txt']}}
(dest/'preparation.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf8')
from trustsvd_repro.data import load_dataset
print(json.dumps(load_dataset('ciao',allow_mismatch=True).metadata,indent=2))
