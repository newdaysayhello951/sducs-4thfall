from pathlib import Path
p=Path('dataset_check/retry/第三轮核查结果.md')
p.write_text('''# 第三轮数据集核查（2026-10-26）

本轮只检查论文、仓库说明、数据目录和数据文件，没有读取第三方模型实现。

## Ciao

新取回两个公开仓库保存的 `rating_with_timestamp.mat`：

- https://raw.githubusercontent.com/INFORMSJoC/2024.0682/main/data/raw/Ciao/rating_with_timestamp.mat
- https://raw.githubusercontent.com/DMIRLAB-Group/REST/main/datasets/Ciao/rating_with_timestamp.mat

两个文件 SHA256 相同：488e9aa5f60e6a52a972795b6402f922fc0d9d273152f4d124a5c5bdefb86a71。读取后的数组均为 284086 × 6，7375 个评分用户，105114 个实际商品，含 34 条零评分；所有时间戳均为正。与论文所列 280391 条评分、99746 个商品仍不一致。新增时间戳副本与此前原始包的前五列逐行并不完全相同，尚不能据此推断具体清洗规则。

INFORMS 仓库的 trust.mat 实际只有 57544 条信任关系，2190 个信任发起者、2325 个接收者；不能代替论文所用 111781 条信任数据。该仓库同时保存 CiaoDVD 文件，因此不能仅凭目录名确认版本。

另取回 GNN-DSR 仓库的 `rating_with_timestamp.txt`，只有 36065 条评分、2248 个用户、16861 个商品，也是子集，不能当作完整基准。

数据与逐次核查 JSON 位于 `dataset_check/retry/third_pass/`，详细统计见 timestamp_stats.json、timestamp_comparison.json。

## Flixster

继续检查 Jamali 数据压缩包在 www.sfu.ca/~sja25/datasets/、www.cs.sfu.ca/~sja25/datasets/、www.cs.ubc.ca/~jamalim/datasets/ 下的公开历史存档，三个精确 ZIP 地址查询均返回空列表。UBC 目录通配查询遇到服务错误/超时；这些结果不能证明所有历史副本均不存在。

SREPS 仓库说明再次确认所需文件为 ratings.txt 与 links.txt，但只指回 Jamali 原始数据，没有提供新下载副本。DTMF 仓库的数据目录只有 Epinions；RecQ 当前数据目录没有 Ciao/Flixster。

本轮仍未取得 TrustSVD 所用的 Flixster 409803 条评分子集，未修改正式实验输入或结果。之前取得的 Figshare Flixster 包只有社交关系，不能用于电影评分预测。

## 当前结论

Ciao 已有可读取的原始数据和带时间戳版本，但尚未确认 TrustSVD 使用的确切输入；Flixster 缺少所需评分文件及确切子集。不能将这些副本标记为“与论文一致”，也没有为了凑规模而裁剪数据。
''',encoding='utf8')
print(p.resolve())
