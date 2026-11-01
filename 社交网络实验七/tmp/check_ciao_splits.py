import json,numpy as np
from trustsvd_repro.data import load_dataset,folds_for
from pathlib import Path
d=load_dataset('ciao',allow_mismatch=True);f=folds_for(d);pairs=d.u*d.n_items+d.i
rows=[]
for k in range(5):
 train=f!=k;test=~train;leak=len(np.intersect1d(pairs[train],pairs[test]));assert leak==0
 counts=np.bincount(d.u[train],minlength=d.n_users);rows.append({'fold':k,'train':int(train.sum()),'test':int(test.sum()),'overlapping_user_item_pairs':leak,'cold_test_observations':int((counts[d.u[test]]<5).sum())})
p=Path('results/ciao_original_gd/input_split_checks.json');p.write_text(json.dumps({'folds':rows,'data':d.metadata},indent=2));print(json.dumps(rows,indent=2))
