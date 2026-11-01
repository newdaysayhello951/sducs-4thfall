from pathlib import Path
p=Path('README.md');s=p.read_text(encoding='utf8');s=s.replace('## 当前范围','''## Ciao 补充实验（用户已同意采用可获得版本）

2026-10-26：使用找回的 Ciao 作者原始包，排除超出声明评分范围的34条0分记录，保留其余284,052条评分（7,375用户、105,096物品）和111,781条信任边。保留重复观察，按用户-物品对分组划分以避免泄漏。该版本不等同于论文280,391条评分、99,746物品的输入。

预处理来源、规则和原始/输出校验值见 `datasets/ciao/preparation.json`。补充实验单独保存于 `results/ciao_original_gd/`，日志为 `results/ciao_original_training.log`。Flixster 按用户要求不再查找和运行。

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
D:\\anaconda\\python.exe -u -m trustsvd_repro.experiment --datasets ciao --allow-mismatch ciao --run ciao_original_gd --optimizer gd --maxiter 200 --jobs 2
D:\\anaconda\\python.exe -m trustsvd_repro.report --run ciao_original_gd
D:\\anaconda\\python.exe -m trustsvd_repro.audit --run ciao_original_gd
```

以下为此前仅完成两个匹配数据集时的记录。

## 当前范围''',1);p.write_text(s,encoding='utf8')
p=Path('datasets/SOURCES.md');s=p.read_text(encoding='utf8');s+='''

## 用户同意的 Ciao 补充输入

2026-10-26：用户同意直接使用已下载的 Ciao，并放弃 Flixster。`datasets/ciao/` 使用上述作者原始包：评分取原始矩阵的用户、物品、评分列，剔除34条0分，保留其余284052条评分、7375用户、105096物品及全部111781条信任边。不做抽样、不为匹配论文数字删行；重复对按组划分。完整来源及哈希见 preparation.json。必须显式使用 --allow-mismatch ciao，实验结果保留 matches_paper=false。
''';p.write_text(s,encoding='utf8')
