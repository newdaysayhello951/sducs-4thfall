# 数据来源及版本

核验日期：2026-10-26。这里只保存实际核验过的正式输入；不同版本不混入。

## FilmTrust

- 作者原包：https://guoguibing.github.io/librec/datasets/filmtrust.zip
- 镜像：https://static.preferred.ai/cornac/datasets/filmtrust/filmtrust.zip
- 两份ZIP的压缩方式不同，但三个解压文件逐文件SHA256相同。
- 原始评分35,497条；不同用户1,508、不同物品2,071；信任边1,853条。
- 原始数据中同一个用户-物品对有3条额外观察，保留并分组交叉验证，不让同一对跨训练/测试。

## Epinions 665K

- 来源说明：https://raw.githubusercontent.com/PreferredAI/cornac/master/cornac/datasets/epinions.py
- 数据包：https://static.preferred.ai/cornac/datasets/epinions/ratings_data.zip
- 原始评分664,824条；评分用户40,163、物品139,738；信任边487,183条。
- 这是TrustSVD使用的665K版，不是TrustWalker/Circle-based使用的Alchemy版本。

上述文件的SHA256写在 `scripts/download_verified.py` 和每个实验JSON中。运行该下载脚本不会下载任何模型源码。

## 缺失版本

- Ciao：第二轮已从MSU原站的2022年网页存档恢复作者公开压缩包，位于 `dataset_check/retry/ciao_wayback_zip.zip`。原包与此前镜像逐字节一致，有284,086条评分、105,114个不同物品，且含0分和重复对；与论文的280,391条评分、99,746个物品仍存在未解释差异，未用作匹配论文版本的正式实验输入。
- Flixster：作者新页 https://sites.google.com/view/mohsenjamali/flixter-data-set 仍存在，嵌入的旧Google Drive文件夹返回404。即便拿到完整爬取数据，也不能自行抽样后声称是论文所用的409,803条评分子集。

未通过删除记录或人工拼凑使不同数据集“匹配”论文统计。

第二轮新恢复的Ciao原包、Flixster存档及逐项检查详见 `dataset_check/retry/第二轮核查结果.md`。Flixster的Figshare包经实际检查只包含社交图，没有电影评分。


## 用户同意的 Ciao 补充输入

2026-10-26：用户同意直接使用已下载的 Ciao，并放弃 Flixster。`datasets/ciao/` 使用上述作者原始包：评分取原始矩阵的用户、物品、评分列，剔除34条0分，保留其余284052条评分、7375用户、105096物品及全部111781条信任边。不做抽样、不为匹配论文数字删行；重复对按组划分。完整来源及哈希见 preparation.json。必须显式使用 --allow-mismatch ciao，实验结果保留 matches_paper=false。
