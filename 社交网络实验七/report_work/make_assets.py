"""Scientific analysis of saved experimental outputs; never retrains models."""
from pathlib import Path
import json, csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'report_work'/'assets'
OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'Microsoft YaHei','axes.unicode_minus':False,
                     'font.size':10,'axes.spines.top':False,'axes.spines.right':False,
                     'figure.facecolor':'white','savefig.facecolor':'white'})
BLUE, ORANGE, GRAY = '#25628A','#C76C36','#73808B'
DS=['filmtrust','epinions','ciao'];LABEL={'filmtrust':'FilmTrust','epinions':'Epinions','ciao':'Ciao'}
MODELS=['UserAvg','ItemAvg','PMF','RSTE','SoRec','SoReg','SocialMF','TrustMF','SVD++','TrustSVD']
def read(path):
    with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
runs={'filmtrust':'gradient_descent','epinions':'gradient_descent','ciao':'ciao_original_gd'}
summary=read(ROOT/'results/combined_report/three_datasets.csv')
def row(ds,m,d=10,v='all'):
    return next(x for x in summary if x['dataset']==ds and x['model']==m and int(x['dim'])==d and x['view']==v)
def save(fig,name):
    fig.savefig(OUT/(name+'.png'),dpi=220,bbox_inches='tight');plt.close(fig)

# Full-model comparison, identical model order across three datasets.
fig,axs=plt.subplots(1,3,figsize=(10.4,5.0),sharey=True)
for ax,ds in zip(axs,DS):
    vals=[float(row(ds,m)['rmse_mean']) for m in MODELS]
    std=[float(row(ds,m)['rmse_std']) for m in MODELS]
    ax.barh(np.arange(10),vals,xerr=std,color=[ORANGE if m=='TrustSVD' else BLUE if m=='SVD++' else '#AAB8C3' for m in MODELS],capsize=2)
    ax.set_yticks(np.arange(10),MODELS);ax.invert_yaxis();ax.set_xlim(0,max(vals)*1.15)
    ax.set_title(LABEL[ds]);ax.set_xlabel('五折平均 RMSE  越小越好');ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
fig.suptitle('全部模型在 d＝10 时的实际误差',fontsize=14)
fig.tight_layout(rect=(0,0,1,.94));save(fig,'all_models')

fig,axs=plt.subplots(1,3,figsize=(10.4,3.6))
for ax,ds in zip(axs,DS):
    x=np.arange(2);w=.24
    for j,(label,key,c) in enumerate([('TrustSVD 实测','TrustSVD',ORANGE),('SVD++ 实测','SVD++',BLUE),('TrustSVD 原文','paper',GRAY)]):
        vals=[float(row(ds,'TrustSVD',d)['paper_rmse'] if key=='paper' else row(ds,key,d)['rmse_mean']) for d in [5,10]]
        ax.bar(x+(j-1)*w,vals,w,label=label,color=c)
        for k,v in enumerate(vals):ax.text(x[k]+(j-1)*w,v+.018,f'{v:.3f}',ha='center',fontsize=8)
    ax.set_xticks(x,['d＝5','d＝10']);ax.set_ylim(0,1.3);ax.set_title(LABEL[ds]);ax.set_ylabel('RMSE');ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
handles,labels=axs[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower center',ncol=3,frameon=False)
fig.tight_layout(rect=(0,.1,1,1));save(fig,'paper_comparison')

fig,axs=plt.subplots(1,3,figsize=(10.4,3.7),sharey=True)
views=['all','cold_train_lt5','cold_total_lt5']
for ax,ds in zip(axs,DS):
    x=np.arange(3)
    for k,(m,c) in enumerate([('SVD++',BLUE),('TrustSVD',ORANGE)]):
        vals=[float(row(ds,m,10,v)['rmse_mean']) for v in views]
        ax.bar(x+(k-.5)*.32,vals,.32,label=m,color=c)
        for j,v in enumerate(vals):ax.text(x[j]+(k-.5)*.32,v+.025,f'{v:.3f}',ha='center',fontsize=8)
    ax.set_xticks(x,['全部','训练少于5条','全量少于5条'],rotation=15);ax.set_title(LABEL[ds]);ax.set_ylim(0,1.5);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
axs[0].set_ylabel('五折平均 RMSE');fig.legend(*axs[0].get_legend_handles_labels(),loc='lower center',ncol=2,frameon=False)
fig.tight_layout(rect=(0,.09,1,1));save(fig,'cold_start')

fig,axs=plt.subplots(1,3,figsize=(10.4,3.7));correlations={}
for ax,ds in zip(axs,DS):
    p=ROOT/'results'/runs[ds]/'report'
    with np.load(p/f'figure1b_{ds}.npz') as z:a=z['correlation'];a=a[np.isfinite(a)]
    ax.hist(a,bins=np.linspace(-1,1,21),weights=np.ones(len(a))/len(a),color=BLUE,edgecolor='white')
    ax.axvline(a.mean(),color=ORANGE,lw=1.8,label=f'均值 {a.mean():.3f}')
    ax.set(title=f'{LABEL[ds]}  有效用户 {len(a):,}',xlabel='与可信邻居平均评分的 PCC',ylabel='有效用户占比',xlim=(-1,1));ax.legend(frameon=False,fontsize=9)
    correlations[ds]={'n':len(a),'mean':float(a.mean()),'ge05':float(np.mean(a>=.5))}
fig.tight_layout();save(fig,'correlations')

fig,axs=plt.subplots(3,1,figsize=(9,9));degree_data=[]
for ax,ds in zip(axs,DS):
    rows=read(ROOT/'results'/runs[ds]/'report/figure2_trust_degree.csv');degree_data+=rows
    for m,c in [('RSTE','#91A3AF'),('SoRec','#B9ADB0'),('SoReg','#8CA282'),('SocialMF','#7A7C9D'),('TrustMF','#967551'),('TrustSVD',ORANGE)]:
        v=[r for r in rows if r['dataset']==ds and r['model']==m]
        ax.plot(range(7),[float(r['rmse']) if r['rmse'] else np.nan for r in v],marker='o',markersize=4,label=m,color=c,lw=2 if m=='TrustSVD' else 1)
    ax.set(title=LABEL[ds],xticks=range(7),xticklabels=['1–5','6–10','11–20','21–40','41–100','101–500','>500'],ylabel='五折平均 RMSE');ax.grid(alpha=.15)
axs[-1].set_xlabel('用户给出的信任边数');fig.legend(*axs[0].get_legend_handles_labels(),loc='lower center',ncol=6,frameon=False,fontsize=9)
fig.tight_layout(rect=(0,.04,1,1));save(fig,'trust_degree')

# A real optimization trace from the recorded selection and refit stages.
fig,axs=plt.subplots(1,2,figsize=(10.4,3.8));trace_info={}
for ds,c in zip(DS,[BLUE,'#738C53',ORANGE]):
    p=ROOT/'results'/runs[ds]/ds/'TrustSVD_d10_fold0.json';r=json.loads(p.read_text(encoding='utf8'))
    for stage in r['training']:
        t=stage['trace']
        if stage['stage']=='refit':axs[0].plot([x['iteration'] for x in t],[x['objective'] for x in t],label=LABEL[ds],color=c)
        else:axs[1].plot([x['iteration'] for x in t],[x['validation_rmse'] for x in t],label=LABEL[ds],color=c)
    trace_info[ds]={'selected':next(x['selected_iterations'] for x in r['training'] if x['stage']=='selection'),'seconds':r['seconds']}
axs[0].set(xlabel='重训迭代次数',ylabel='按训练评分数归一化后的目标值',title='训练目标');axs[0].set_yscale('log')
axs[1].set(xlabel='内部验证阶段迭代次数',ylabel='内部验证 RMSE',title='内部验证误差')
for ax in axs:ax.grid(alpha=.15);ax.legend(frameon=False)
fig.tight_layout();save(fig,'training_trace')

# Illustration of actual model/data flow, not fabricated experimental data.
fig,ax=plt.subplots(figsize=(10,3.8));ax.axis('off');ax.set(xlim=(0,10),ylim=(0,3.8))
boxes=[(.1,2.25,2.1,.9,'评分数据\n显式分数与评价历史'),(.1,.6,2.1,.9,'信任数据\n用户信任哪些人'),(3.1,2.25,2.1,.9,'评分与历史表示\n用户 P  物品 Q 与 Y'),(3.1,.6,2.1,.9,'信任表示\n受信任用户 W'),(6.1,1.45,1.8,1,'组合用户表示\nH＝P＋NY＋SW'),(8.6,1.45,1.3,1,'评分预测\n与 Q 匹配')]
for x,y,w,h,t in boxes:
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=.04',facecolor='#EDF3F6',edgecolor=BLUE,lw=1));ax.text(x+w/2,y+h/2,t,ha='center',va='center',fontsize=11)
for a,b in [((2.25,2.7),(3.02,2.7)),((2.25,1.05),(3.02,1.05)),((5.25,2.7),(6.05,2.13)),((5.25,1.05),(6.05,1.73)),((7.96,1.95),(8.52,1.95))]:ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=14,color=BLUE,lw=1.4))
ax.text(5,3.5,'评分误差与信任重建误差联合训练',ha='center',fontsize=13,fontweight='bold')
ax.text(5,.12,'图中 N 和 S 分别表示按邻域大小归一化的评分历史与信任邻接矩阵',ha='center',fontsize=10,color=GRAY)
save(fig,'model_flow')

stats={'correlations':correlations,'trace_info':trace_info,'datasets':{},'paired':[],'sparsity':{},'stopping':{}}
for ds in DS:
    base=ROOT/'results'/runs[ds];man=json.loads((base/'manifest.json').read_text(encoding='utf8'))
    stats['datasets'][ds]=man['available'][ds]
    paired=read(base/'report/paired_tests.csv');stats['paired'] += [r for r in paired if r['dataset']==ds and r['baseline']=='SVD++']
    diag=read(base/'report/sparsity_diagnostics.csv')
    rr=[r for r in diag if r['dataset']==ds and r['model']=='TrustSVD' and r['dim']=='10' and r['group']=='item_unseen_in_train']
    stats['sparsity'][ds]={'unseen_item_test_n':sum(int(r['observations']) for r in rr),'test_n':int(row(ds,'TrustSVD')['test_observations'])}
    fits=[json.loads(p.read_text(encoding='utf8')) for p in (base/ds).glob('*.json')]
    refits=[t for f in fits for t in f['training'] if t['stage']=='refit']
    stats['stopping'][ds]={'fits':len(fits),'refits':len(refits),'hit_selected_budget':sum(t['message']=='maximum iterations reached' for t in refits),'seconds_sum':sum(f['seconds'] for f in fits)}
(OUT/'stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf8')
fig,axs=plt.subplots(1,3,figsize=(10.4,3.4),sharey=True)
for ax,ds in zip(axs,DS):
    rr=read(ROOT/'results'/runs[ds]/'report'/f'figure1a_{ds}.csv')
    ax.scatter([int(x['ratings_count']) for x in rr],[float(x['trusters_ratio']) for x in rr],s=7,color=BLUE)
    ax.set(xlim=(-1,100),ylim=(0,1.05),title=LABEL[ds],xlabel='用户评价过的不同物品数');ax.grid(alpha=.15)
axs[0].set_ylabel('发起过信任的用户比例');fig.tight_layout();save(fig,'coverage')
equations={
 'prediction':r'$\hat r_{uj}=\mu+b_u+b_j+q_j^{\mathsf{T}}\left(p_u+\frac{1}{\sqrt{|I_u|}}\sum_{i\in I_u}y_i+\frac{1}{\sqrt{|T_u|}}\sum_{v\in T_u}w_v\right)$',
 'objective':r'$L=\frac{1}{2}\sum_{(u,j)\in\Omega_R}(\hat r_{uj}-r_{uj})^2+\frac{\lambda_t}{2}\sum_{(u,v)\in\Omega_T}(p_u^{\mathsf{T}}w_v-t_{uv})^2+\frac{1}{2}\sum_{\theta}d_{\theta}\Vert\theta\Vert^2$',
 'gradient':r'$H=P+NY+SW,\quad G=EQ,\quad \nabla_Y L=N^{\mathsf{T}}G+D_Y Y$',
 'gradient_w':r'$\nabla_W L=S^{\mathsf{T}}G+\lambda_t F^{\mathsf{T}}P+D_W W$',
 'metrics':r'$\mathrm{MAE}=\frac{1}{n}\sum_{k=1}^{n}|\hat r_k-r_k|,\qquad\mathrm{RMSE}=\sqrt{\frac{1}{n}\sum_{k=1}^{n}(\hat r_k-r_k)^2}$'
}
for name,formula in equations.items():
    fig=plt.figure(figsize=(11,1.0));fig.text(.5,.5,formula,ha='center',va='center',fontsize=18);save(fig,'eq_'+name)
print('Generated',len(list(OUT.glob('*.png'))),'figures')
