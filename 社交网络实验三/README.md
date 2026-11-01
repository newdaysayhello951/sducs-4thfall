### Task-3

This Experiment is for social network and opinion analysis course.

The Task is Clustering using **K-means**.

Hope you will enjoy it.

### Data Format

​	First, you need to download the dataset(Twitter_data) in [link](https://www.weiyun.com/disk/sharedir/ea51ad8c0a0c0133a882654baf779852).

​	And you can open the file with note book.

​	This file contains 29846 data,and each of them has 8 items("userName":用户名;"clusterNo":类别；"text":Twitter内容；"timeStr":时间戳；"tweeId":用户Id；"errorCode":状态码；"textCleaned":去除链接等特殊符号只保留文本的处理；"relevance":)

### Preprocessing

#### File Read

```python
import json
# 将数据读取成dict格式便于后续的操作
Twitter_data=[]
with open("Twitter_data")as f:
    for line in f:
        # print(line)
        Twitter_data.append(json.loads(line))

```

#### Tokenize

```python
#可以直接按空格进行分词
#implement by yourself
```

#### Vectoring

```python
#建议使用词袋模型
#implement by yourself
```

### k-Means

```python
#不允许调库，数据集中有200左右个类别
#implement by yourself
```

### 已实现的代码与运行方式

`twitter_kmeans.py` 实现完整流程：逐行读取 JSON → 空白分词 → 手写词袋向量化 → 手写 K-means++ 初始化 → 手写 Lloyd K-means → 导出结果与评价。

需要 Python 3.10 或更高版本，在项目目录运行：

```powershell
python -m pip install -r requirements.txt
python twitter_kmeans.py
```

默认使用已有的 `Twitter_data` 文件、全部样本和 220 个簇。实际数据中 `clusterNo` 有 220 个不同值，但代码不会读取标签来构建特征、选择中心或分配样本。标签仅在聚类结束后用于评价。

NumPy 和 SciPy 仅用于基础数值运算和稀疏矩阵存储；没有调用 sklearn、现成的 K-means 或词袋向量化工具。分词、词表构建、词频统计、中心初始化、距离计算、样本分配、中心更新和评价公式均由代码实现。README 的“不允许调库”按禁止直接使用现成聚类算法理解；若课程另有禁止基础数值库的规定，需要按教师要求调整。

#### 实现细节

- 优先读取 `textCleaned`，为空时回退到 `text`，转小写后按空白分词。
- 默认保留至少出现在 2 篇文本中的词，按文档频率选取前 5000 个词；同频时按字典序排序，便于复现。
- 使用词频词袋，默认进行 L2 归一化，减小文本长度对距离的影响；不是 TF-IDF。使用 `--no-normalize` 可改为原始词频。
- 使用平方欧氏距离，按簇内样本算术平均值更新中心；中心不再归一化，因此实现的是普通 K-means，而非球面 K-means。
- 默认随机种子为 42，最多迭代 50 次。中心整体的相对变化不超过 `1e-4` 时停止；达到迭代上限也会输出结果，并在指标中记录是否收敛。
- 空簇重新初始化为当前距离所属中心最远的样本。若不同向量的数量少于 K，最终非空簇数可能小于 K。
- 筛词后变成全零向量的文本不参与聚类和评价，但保留在输出 CSV 中，簇编号为 `-1`。统计中单独记录这些样本数量。
- 分批计算距离，并用稀疏矩阵存储词袋，避免分配三维距离数组。

#### 可选运行参数

快速试运行（只读前 2000 条，分为 20 簇）：

```powershell
python twitter_kmeans.py --limit 2000 --k 20 --max-iter 15 --output results_smoke
```

自定义词表规模和迭代次数：

```powershell
python twitter_kmeans.py --k 220 --max-features 10000 --min-df 2 --max-iter 100 --output results_large
```

用原始词频运行：

```powershell
python twitter_kmeans.py --no-normalize --output results_counts
```

完整参数说明：`python twitter_kmeans.py --help`。

#### 输出文件

默认写入 `results/`；重复使用同一输出目录会覆盖同名结果文件。

| 文件 | 内容 |
| --- | --- |
| `assignments.csv` | 每条记录的原始行序号（从 0 开始）、tweetId、真实标签、预测簇编号、实际使用的文本 |
| `clusters.json` | 各簇大小、权重最高的 10 个词、距离中心最近的最多 3 条代表文本 |
| `metrics.json` | 参数、有效样本数、零向量数、迭代次数、收敛状态、SSE、ARI、纯度、导出前耗时 |
| `history.json` | 各轮更新中心前的 SSE、中心相对变化、空簇数 |
| `vocabulary.json` | 词表，列表索引对应向量维度 |
| `centers.npy` | K × 词表大小的聚类中心数组，可用 `numpy.load()` 读取 |

簇编号只是算法产生的编号，不是话题名称，也不与 `clusterNo` 直接对应。关键词可以辅助人工解释簇的主题。

SSE 是样本到其中心的平方距离之和，在相同特征与 K 设置下越小越好；不同预处理配置下不宜直接比较。ARI 衡量聚类与已有标签的一致性，不受簇编号置换影响，1 表示完全一致，接近 0 表示与随机划分相近，也可能为负。纯度统计每簇中最多的真实类别所占比例；它容易随 K 增大而提高，不能单独作为好坏依据。外部评价仅覆盖具有真实标签的非零向量样本。

#### 验证

```powershell
python -m unittest -v test_twitter_kmeans.py
```

测试覆盖词频和归一化、已知两簇样例的中心与 SSE、重复向量造成的空簇、输出标签与最终中心的一致性，以及不受簇编号影响的评价指标。
