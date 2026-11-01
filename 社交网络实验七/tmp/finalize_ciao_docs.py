from pathlib import Path
import json
p=Path('results/ciao_original_gd/audit.json');a=json.loads(p.read_text(encoding='utf8'));print({k:a[k] for k in ['checked_fits','errors','missing_tasks','complete_for_available','complete_for_entire_paper']})
p=Path('README.md');s=p.read_text(encoding='utf8');needle='以下为此前仅完成两个匹配数据集时的记录。';s=s.replace(needle,'Ciao补充实验已完成100/100组，0失败，100组结果复核通过。连同此前两个数据集共完成300组评估；汇总见 [三数据集实验汇总](results/combined_report/三数据集实验汇总.md)，Ciao详细报告见 [Ciao实验报告](results/ciao_original_gd/report/实验报告.md)。Ciao的TrustSVD All RMSE为0.965598（d=5）、0.966041（d=10），本次未优于SVD++。\n\n'+needle);p.write_text(s,encoding='utf8')
