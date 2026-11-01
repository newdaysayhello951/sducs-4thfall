"""Generate real-run tables/figures, with published scores kept separate."""
import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
from scipy.sparse import csr_matrix
from scipy.stats import ttest_rel
from numba import njit
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .data import ROOT, load_dataset, folds_for
from .paper_reference import ORDER, reference, FANG_REPORTED


def write_csv(path, rows):
    if not rows:
        return
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


@njit(cache=True)
def correlations(rp, ri, rv, tp, ti):
    """PCC: own ratings vs mean neighbors' observed ratings on shared items.

    Missing ratings are excluded, not filled with zero. Undefined PCC -> NaN.
    Training is NOT involved in this full-dataset descriptive analysis.
    """
    n = len(rp)-1
    out = np.full(n, np.nan)
    for u in range(n):
        xs, ys = [], []
        for k in range(rp[u], rp[u+1]):
            j, total, count = ri[k], 0., 0
            for t in range(tp[u], tp[u+1]):
                v = ti[t]
                lo, hi = rp[v], rp[v+1]
                while lo < hi:
                    mid = (lo+hi)//2
                    if ri[mid] < j:
                        lo = mid+1
                    else:
                        hi = mid
                if lo < rp[v+1] and ri[lo] == j:
                    total += rv[lo]
                    count += 1
            if count:
                xs.append(rv[k])
                ys.append(total/count)
        if len(xs) >= 2:
            x, y = np.array(xs), np.array(ys)
            x -= x.mean()
            y -= y.mean()
            den = np.sqrt(np.sum(x*x)*np.sum(y*y))
            if den > 0:
                out[u] = min(1.,max(-1.,np.sum(x*y)/den))
    return out


def trust_analysis(dataset, out, allow_mismatch=False):
    data = load_dataset(dataset, allow_mismatch=allow_mismatch)
    # Conflicting FilmTrust duplicate ratings are averaged for this descriptive
    # matrix only; experiment observations themselves remain untouched.
    shape = (data.n_users, data.n_items)
    R = csr_matrix((data.r, (data.u, data.i)), shape=shape)
    C = csr_matrix((np.ones(len(data.r)), (data.u, data.i)), shape=shape)
    R.data /= C.data
    R.sort_indices()
    T = csr_matrix((np.ones(len(data.t)), (data.tu, data.tv)), shape=(data.n_users, data.n_users))
    T.sort_indices()
    count = np.diff(R.indptr)
    degree = np.diff(T.indptr)
    rows = []
    for n in np.unique(count):
        mask = count == n
        rows.append(dict(ratings_count=int(n), users=int(mask.sum()),
                         trusters=int(np.sum(degree[mask] > 0)),
                         trusters_ratio=float(np.mean(degree[mask] > 0))))
    write_csv(out/f'figure1a_{dataset}.csv', rows)
    corr = correlations(R.indptr, R.indices, R.data, T.indptr, T.indices)
    np.savez_compressed(out/f'figure1b_{dataset}.npz', correlation=corr)
    valid = corr[np.isfinite(corr)]
    info = dict(valid_users=len(valid), mean_correlation=float(valid.mean()) if len(valid) else None,
                fraction_ge_05=float(np.mean(valid >= .5)) if len(valid) else None,
                fraction_ge_09=float(np.mean(valid >= .9)) if len(valid) else None)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].plot([r['ratings_count'] for r in rows], [r['trusters_ratio'] for r in rows], '.', ms=3)
    axes[0].set(xlabel='Number of rated items', ylabel='Fraction issuing trust', xlim=(-1, 100), ylim=(0, 1.05))
    axes[1].hist(valid, bins=np.linspace(-1, 1, 21), weights=np.ones(len(valid))/max(1,len(valid)))
    axes[1].set(xlabel='PCC with trusted-neighbor mean', ylabel='Fraction of users')
    fig.suptitle(f'{dataset}: trust analysis (independent reconstruction)')
    fig.tight_layout()
    fig.savefig(out/f'figure1_{dataset}.png', dpi=160)
    fig.savefig(out/f'figure1_{dataset}.svg')
    plt.close(fig)
    return info


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--run', default='gradient_descent')
    p.add_argument('--skip-analysis', action='store_true')
    args = p.parse_args()
    base = ROOT/'results'/args.run
    out = base/'report'
    out.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((base/'manifest.json').read_text(encoding='utf-8'))
    grouped, records, prediction_files = defaultdict(list), [], {}
    for path in base.glob('*/*.json'):
        row = json.loads(path.read_text(encoding='utf-8'))
        if row.get('status') != 'completed':
            continue
        records.append(row)
        grouped[row['dataset'], row['model'], row['dim']].append(row)
        prediction_files[row['dataset'], row['model'], row['dim'], row['fold']] = path.with_suffix('.npz')
    summary, all_folds = [], []
    for (dataset, model, dim), runs in sorted(grouped.items()):
        for view in ('all', 'cold_train_lt5', 'cold_total_lt5'):
            ref = reference(dataset, dim, view, model)
            a = [r[view]['mae'] for r in runs if r[view]['n']]
            b = [r[view]['rmse'] for r in runs if r[view]['n']]
            summary.append(dict(dataset=dataset, model=model, dim=dim, view=view,
                                dataset_matches_paper=manifest['available'][dataset]['matches_paper'],
                                completed_folds=len(runs), expected_folds=5,
                                test_observations=sum(r[view]['n'] for r in runs),
                                mae_mean=float(np.mean(a)) if a else None,
                                mae_std=float(np.std(a, ddof=1)) if len(a)>1 else None,
                                rmse_mean=float(np.mean(b)) if b else None,
                                rmse_std=float(np.std(b, ddof=1)) if len(b)>1 else None,
                                paper_mae=ref['mae'], paper_rmse=ref['rmse'],
                                rmse_difference=float(np.mean(b))-ref['rmse'] if b else None))
            for r in runs:
                all_folds.append(dict(dataset=dataset, model=model, dim=dim, view=view,
                                      fold=r['fold'], **r[view], seconds=r['seconds']))
    write_csv(out/'table2_actual_vs_paper.csv', summary)
    write_csv(out/'fold_metrics.csv', all_folds)
    training_diagnostics=[]
    for r in records:
        for stage in r['training']:
            training_diagnostics.append(dict(dataset=r['dataset'],model=r['model'],dim=r['dim'],fold=r['fold'],
                                             stage=stage['stage'],role=stage['role'],iterations=stage['iterations'],
                                             selected_iterations=stage['selected_iterations'],objective=stage['objective'],
                                             gradient_norm=stage['gradient_norm'],stop_reason=stage['message'],
                                             best_validation_rmse=stage['best_validation_rmse'],seconds=stage['seconds']))
    write_csv(out/'training_diagnostics.csv',training_diagnostics)
    # Diagnose sparse-data failures without changing any predictions or training.
    diagnostics=[]
    fallback_sensitivity=[]
    for dataset in manifest['available']:
        data=load_dataset(dataset, allow_mismatch=dataset in manifest['arguments'].get('allow_mismatch', []))
        folds=folds_for(data,manifest['arguments']['seed'])
        item_counts={f:np.bincount(data.i[folds!=f],minlength=data.n_items) for f in range(5)}
        for (ds,model,dim,fold),path in sorted(prediction_files.items()):
            if ds!=dataset:
                continue
            with np.load(path) as z:
                unseen_item=item_counts[fold][data.i[z['indices']]]==0
                sensitivity_prediction=z['prediction'].copy()
                sensitivity_prediction[unseen_item]=data.r[folds!=fold].mean()
                alternative=sensitivity_prediction-z['truth']
                fallback_sensitivity.append(dict(dataset=dataset,model=model,dim=dim,fold=fold,
                                                 rule='training_global_mean_for_unseen_item_only',
                                                 unseen_items_observations=int(unseen_item.sum()),
                                                 primary_mae=float(np.mean(np.abs(z['prediction']-z['truth']))),
                                                 primary_rmse=float(np.sqrt(np.mean((z['prediction']-z['truth'])**2))),
                                                 sensitivity_mae=float(np.mean(np.abs(alternative))),
                                                 sensitivity_rmse=float(np.sqrt(np.mean(alternative**2)))))
                groups={'item_unseen_in_train':unseen_item,'item_seen_in_train':~unseen_item,
                        'user_unseen_in_train':z['train_rating_count']==0,
                        'user_seen_in_train':z['train_rating_count']>0}
                for group,mask in groups.items():
                    err=z['prediction'][mask]-z['truth'][mask]
                    diagnostics.append(dict(dataset=dataset,model=model,dim=dim,fold=fold,group=group,
                                            observations=int(mask.sum()),fraction=float(mask.mean()),
                                            mae=float(np.mean(np.abs(err))) if len(err) else None,
                                            rmse=float(np.sqrt(np.mean(err**2))) if len(err) else None))
    write_csv(out/'sparsity_diagnostics.csv',diagnostics)
    write_csv(out/'unseen_item_fallback_sensitivity.csv',fallback_sensitivity)
    degree_rows, significance, table3 = [], [], []
    bins = [(1,5), (6,10), (11,20), (21,40), (41,100), (101,500), (501,np.inf)]
    for dataset in manifest['available']:
        for model in ('RSTE','SoRec','SoReg','SocialMF','TrustMF','TrustSVD'):
            fold_metrics = defaultdict(list)
            n_total = defaultdict(int)
            for fold in range(5):
                path = prediction_files.get((dataset, model, 10, fold))
                if path is None:
                    continue
                with np.load(path) as z:
                    for j,(lo,hi) in enumerate(bins):
                        mask = (z['trust_degree'] >= lo)&(z['trust_degree'] <= hi)
                        n_total[j] += int(mask.sum())
                        if mask.any():
                            fold_metrics[j].append(float(np.sqrt(np.mean((z['prediction'][mask]-z['truth'][mask])**2))))
            for j,(lo,hi) in enumerate(bins):
                vals = fold_metrics[j]
                degree_rows.append(dict(dataset=dataset, model=model, trust_bin=f'{lo}-{hi}' if np.isfinite(hi) else '>500',
                                        rmse=float(np.mean(vals)) if vals else None, observations=n_total[j], folds=len(vals)))
        fig, ax = plt.subplots(figsize=(9,4.5))
        for model in ('RSTE','SoRec','SoReg','SocialMF','TrustMF','TrustSVD'):
            rows = [r for r in degree_rows if r['dataset']==dataset and r['model']==model]
            ax.plot(range(7), [np.nan if r['rmse'] is None else r['rmse'] for r in rows], marker='o', label=model)
        ax.set(xticks=range(7), xticklabels=['1-5','6-10','11-20','21-40','41-100','101-500','>500'],
               xlabel='Number of trusted neighbors', ylabel='Mean fold RMSE', title=f'{dataset}, d=10 (actual runs)')
        ax.legend(ncol=3)
        fig.tight_layout()
        fig.savefig(out/f'figure2_{dataset}.png', dpi=160)
        fig.savefig(out/f'figure2_{dataset}.svg')
        plt.close(fig)
        for dim in (5,10):
            actual = next((r for r in summary if r['dataset']==dataset and r['model']=='TrustSVD' and r['dim']==dim and r['view']=='all'), None)
            if actual and (dataset,dim) in FANG_REPORTED:
                fang = FANG_REPORTED[dataset,dim]
                table3.append(dict(dataset=dataset, dim=dim, fang_mae_reported_only=fang[0],
                                   fang_rmse_reported_only=fang[1], trustsvd_actual_mae=actual['mae_mean'],
                                   trustsvd_actual_rmse=actual['rmse_mean'], fang_executed=False))
            main_runs = {r['fold']:r for r in grouped.get((dataset,'TrustSVD',dim),[])}
            for model in ORDER:
                other = {r['fold']:r for r in grouped.get((dataset,model,dim),[])}
                common = sorted(set(main_runs)&set(other))
                if model == 'TrustSVD' or len(common)<2:
                    continue
                x = np.array([main_runs[f]['all']['rmse'] for f in common])
                y = np.array([other[f]['all']['rmse'] for f in common])
                stat = ttest_rel(x,y)
                significance.append(dict(dataset=dataset, dim=dim, baseline=model, paired_unit='outer fold RMSE',
                                         n_pairs=len(common), mean_difference=float(np.mean(x-y)),
                                         t_statistic=float(stat.statistic), p_two_sided=float(stat.pvalue)))
    write_csv(out/'figure2_trust_degree.csv', degree_rows)
    write_csv(out/'table3_actual_vs_reported_fang.csv', table3)
    write_csv(out/'paired_tests.csv', significance)
    analysis = {}
    if not args.skip_analysis:
        for dataset in manifest['available']:
            print('Trust analysis:', dataset, flush=True)
            analysis[dataset] = trust_analysis(dataset, out, allow_mismatch=dataset in manifest['arguments'].get('allow_mismatch', []))
        (out/'trust_analysis.json').write_text(json.dumps(analysis, indent=2), encoding='utf-8')
    text = ['# TrustSVD 独立复现实验报告', '',
            '**状态：独立复现实验。允许的数据版本差异逐项列出，不能视为原文数值的严格复现。**', '',
            '实现来自论文公式的独立推导，未读取或复制已发布模型实现。', '',
            '**这些是独立实现的实际重跑结果，不是逐项数值复现成功；部分基线与原表差距明显。**', '',
            '## 数据与完成范围', '']
    for name, meta in manifest['available'].items():
        n = sum(r['dataset']==name for r in records)
        cfg=manifest['arguments']
        expected=len(cfg['models'])*len(cfg['dims'])*len(cfg['folds'])
        status = '数据四项规模与论文一致' if meta['matches_paper'] else f"使用经用户同意的不同版本，实际规模{meta['counts']}，原文规模{meta['expected']}；原文分数仅供参考，差值不能归因于模型实现"
        text.append(f"- {name}：{status}；完成 {n}/{expected} 个外层训练任务（{len(cfg['models'])}个模型×{len(cfg['dims'])}种维度×{len(cfg['folds'])}折）。")
        if not meta['matches_paper'] and name == 'ciao':
            text.append('- Ciao预处理：作者原始包284,086条评分中排除34条超出1–5评分范围的0分，保留其余284,052条评分和全部111,781条信任边；保留重复观察并按用户-物品对分组划分。来源和校验值见datasets/ciao/preparation.json。')
    for name, reason in manifest['missing'].items():
        text.append(f'- {name}：未运行，原因：{reason}')
    text += ['', '## TrustSVD 实际结果与原文对照', '',
             'MAE表示平均预测差多少分；RMSE对大的预测错误惩罚更重，两者越小越好。5折就是把评分分成5份，每次留1份测试，轮流测试后取平均。', '',
             '`all`包含所有测试评分；`cold_train_lt5`只看训练中评分少于5条的用户；`cold_total_lt5`按全量评分计数。差值为正表示本次误差比原文大。', '',
             '表中为5折均值；只有完成5折的行才是完整交叉验证结果。原文值仅供对照。', '',
             '|数据|维度|视图|折数|实际MAE|实际RMSE|原文RMSE|差值|',
             '|---|---:|---|---:|---:|---:|---:|---:|']
    for r in summary:
        if r['model']=='TrustSVD' and r['rmse_mean'] is not None:
            text.append(f"|{r['dataset']}|{r['dim']}|{r['view']}|{r['completed_folds']}|{r['mae_mean']:.6f}|{r['rmse_mean']:.6f}|{r['paper_rmse']:.3f}|{r['rmse_difference']:+.6f}|")
    comparisons=[]
    for dataset in manifest['available']:
        for dim in (5,10):
            a=next((r for r in summary if r['dataset']==dataset and r['dim']==dim and r['view']=='all' and r['model']=='TrustSVD'),None)
            b=next((r for r in summary if r['dataset']==dataset and r['dim']==dim and r['view']=='all' and r['model']=='SVD++'),None)
            if a and b and a['completed_folds']==5 and b['completed_folds']==5:
                comparisons.append((dataset,dim,a['rmse_mean'],b['rmse_mean']))
    if comparisons:
        wins=sum(a<b for _,_,a,b in comparisons)
        text += ['', '## 是否重现了相对SVD++的优势', '',
                 f'本次完成的{len(comparisons)}组All视图RMSE对比中，TrustSVD优于SVD++的有{wins}组。不能将本次运行称为重现了原论文的整体优势。', '',
                 '|数据|维度|TrustSVD实测RMSE|SVD++实测RMSE|', '|---|---:|---:|---:|']
        for ds,dim,a,b in comparisons:
            text.append(f'|{ds}|{dim}|{a:.6f}|{b:.6f}|')
    text += ['', '## 方法及无法逐项对齐的设置', '',
             '- TrustSVD严格实现原文Eq.(1)的全局目标函数；最后的w_v正则项按所有v求和。所有解析梯度通过中心差分验证。',
             f"- 优化器使用{'独立编写的完整批次梯度下降（Armijo回溯/标量步长）' if manifest['arguments'].get('optimizer')=='gd' else 'L-BFGS-B和完整批次解析梯度'}，非原作者未公开完整设置的训练过程。没有声称数值严格重现。",
             '- 每个外层4折训练集中再留10%作为内部验证，只选择训练迭代数；然后用完整4折重新训练。所有模型与维度使用固定且保存的划分。',
             '- 未用外层测试分数选超参数；正则系数、信任系数及维度按论文设置。初始化、优化上限、停止条件是本实现明确选定的设置。',
             '- FilmTrust有3条额外重复用户-物品记录，保留原始观察并按用户-物品对分组划分，以防同一对进入训练与测试。',
             '- 评分历史只从当前训练集构建；信任图作为已知辅助信息全量使用。测试预测裁剪到原始评分范围，另存未裁剪分数。',
             '- 同时报告按训练评分数<5与全量评分数<5定义的冷启动结果，避免原文表述不明确导致隐藏差异。',
             '- SoReg使用训练集PCC并映射至[0,1]；无共同评分或零方差时权重设为0。',
             '- Figure 1是对论文文字描述的独立重建；邻居聚合和缺失评分处理规则见report.py，原文未提供完整分析脚本。',
             '- Table 3中Fang方法数值仅引用原文已报告结果，没有运行Fang模型；原TrustSVD论文同样复用其已发表结果。',
             '- 配对检验使用5个外层折RMSE作为样本单位；原文没有说明检验样本单位，不能保证其p值一致。',
             '- 对训练中完全未出现的物品，主结果直接使用公式输出并裁剪。原文未说明这种情况的回退规则；对于无偏置的线性模型，这可能显著影响分数。另提供统一回退到训练均值的敏感性分析，未用它更改主表、选参数或声称优于论文。',
             '', '## 输出文件', '',
             '- `table2_actual_vs_paper.csv`：所有已执行模型的All与两种Cold视图、均值、标准差、原文对照。',
             '- `fold_metrics.csv`：逐折指标；每个任务JSON记录训练轨迹、参数、耗时、数据哈希。',
             '- `training_diagnostics.csv`：每个选择/重训阶段的目标值、梯度范数、迭代数和停止原因；达到迭代上限不代表已经收敛。',
             '- `figure1_*.png/svg`、`trust_analysis.json`：信任覆盖与相关性分析。',
             '- `figure2_*.png/svg`、`figure2_trust_degree.csv`：按信任度分组的RMSE。',
             '- `table3_actual_vs_reported_fang.csv`：本次TrustSVD结果和原文引用的Fang结果。',
             '- `paired_tests.csv`：配对检验。每个任务NPZ保存逐条测试预测及样本索引。',
             '- `sparsity_diagnostics.csv`：按训练中是否出现过该用户/物品分组的误差；仅用于诊断，不修改预测。',
             '- `unseen_item_fallback_sensitivity.csv`：训练中未见物品统一回退训练均值时的对照；与主结果分开，不修改原始预测文件。',
             '', '原论文中数值与本次运行数值存放在不同字段，任何原文数值都没有作为实际运行输出写入。']
    (out/'实验报告.md').write_text('\n'.join(text)+'\n', encoding='utf-8')
    print('REPORT', out, 'completed fits', len(records), flush=True)


if __name__ == '__main__':
    main()
