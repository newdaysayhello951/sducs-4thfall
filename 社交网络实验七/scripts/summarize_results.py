"""Combine audited independent runs without copying predictions or retraining."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    runs = ['gradient_descent', 'ciao_original_gd']
    rows, datasets, total = [], set(), 0
    for run in runs:
        folder = ROOT / 'results' / run
        audit = json.loads((folder / 'audit.json').read_text(encoding='utf-8'))
        if audit['errors'] or not audit['complete_for_available']:
            raise ValueError(f'{run}: incomplete or failed audit')
        manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
        if datasets.intersection(manifest['available']):
            raise ValueError('Duplicate datasets across runs')
        datasets.update(manifest['available'])
        total += audit['checked_fits']
        with (folder / 'report' / 'table2_actual_vs_paper.csv').open(encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                if int(row['completed_folds']) != 5:
                    raise ValueError('Incomplete cross validation')
                row['run'] = run
                row['dataset_matches_paper'] = manifest['available'][row['dataset']]['matches_paper']
                rows.append(row)
    out = ROOT / 'results' / 'combined_report'
    out.mkdir(exist_ok=True)
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with (out / 'three_datasets.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    text = ['# 三个数据集实验汇总', '',
            f'共完成并复核 {total} 组评估：3个数据集 × 10个模型 × 2种维度 × 5折。Flixster按用户要求不再运行。', '',
            'FilmTrust、Epinions的四项数据规模与论文一致。Ciao使用用户同意的可获得版本：剔除34条0分后保留284,052条评分、7,375用户、105,096物品、111,781条信任边，与论文规模不同。', '',
            '所有分数均为独立实现的实际输出。数据版本、划分、初始化和训练设置存在差异，不能称为原文数值的严格复现。', '',
            '## TrustSVD 五折均值（全部测试评分）', '',
            '|数据|维度|实际MAE|实际RMSE|SVD++实际RMSE|数据规模与论文一致|',
            '|---|---:|---:|---:|---:|---|']
    for row in rows:
        if row['model'] != 'TrustSVD' or row['view'] != 'all':
            continue
        other = next(r for r in rows if r['dataset'] == row['dataset'] and r['dim'] == row['dim'] and r['model'] == 'SVD++' and r['view'] == 'all')
        text.append(f"|{row['dataset']}|{row['dim']}|{float(row['mae_mean']):.6f}|{float(row['rmse_mean']):.6f}|{float(other['rmse_mean']):.6f}|{'是' if row['dataset_matches_paper'] else '否'}|")
    text += ['', '## 详细结果', '',
             '- 全部模型、All/两种Cold Start视图、均值与标准差见 three_datasets.csv。',
             '- FilmTrust、Epinions：../gradient_descent/report/实验报告.md。',
             '- Ciao：../ciao_original_gd/report/实验报告.md。',
             '- 每个运行目录的audit.json保存逐条预测重算、划分泄漏与模型重载检查结果。',
             '- Ciao数据转换来源和哈希见datasets/ciao/preparation.json；重跑入口为run_ciao.ps1。']
    (out / '三数据集实验汇总.md').write_text('\n'.join(text) + '\n', encoding='utf-8')
    print(out)


if __name__ == '__main__':
    main()
