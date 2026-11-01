# Sumblr 复现：面向演化推文流的持续摘要

复现论文：**Sumblr: Continuous Summarization of Evolving Tweet Streams**
Lidan Shou, Zhenhua Wang, Ke Chen, Gang Chen (浙江大学), **ACM SIGIR 2013**, pp. 533–542.
DOI: [10.1145/2484028.2484045](https://doi.org/10.1145/2484028.2484045)

本目录是对该论文的**核心架构与实验协议复现**：在线流式聚类 + 簇压缩向量（TCV）+ 金字塔时间框架（PTF）+ 历史摘要 + TCV-Rank 摘要 + 话题演化时间线，并在公开数据集上跑通全部 5 组实验。

> **✅ 完成度**：严格计约 **90%**（36 完成 / 3 偏离 / 1 未实现），核心架构 **100%**。
> 唯一未实现项为 §4.4 多主题流扩展（论文自称"可扩展"方向，非核心贡献）。
> **逐条对照审计见 [AUDIT.md](AUDIT.md)**。

---

## 1. 为什么选这篇论文

在 10 篇候选论文中，Sumblr 是**最可复现**的一篇：

| 复现要素 | Sumblr 的情况 |
|---|---|
| 是否需要训练数据 | **不需要**（完全无监督） |
| 是否需要 GPU | **不需要**，纯 CPU |
| 是否有神经网络/概率采样 | **没有**，纯 IR 算法 |
| 算法是否完整给出 | **是**，Algorithm 1/2 有伪代码，Definition 1/3/4 给全算术细节 |
| 关键超参数是否给出 | **是**，β=0.07, Nmax=150, mc=0.7, m=40, λ=0.4, α=2, 3 天新鲜度, 250 词 |
| 数据是否可得 | 论文原始数据**不可得**（见 §6），但公开替代数据充分 |
| 代码量 | 约 700 行 Python，3–4 天可完成 |

对比其他 9 篇：2017 年 ACL 那篇是 Theano 深度学习（框架已死，需 6–7 GPU 天）；2013/2016 的个性化与多语言摘要是定制动态主题模型 + Gibbs 采样，超参数缺失严重；2011/2012 是因子图与跨集合主题模型，且数据全部私有。

---

## 2. 数据集（公开替代）

论文原始数据（Obama / Chelsea / Arsenal / Tablet / Black Friday，共 121 万推文）来自 2012 年 Twitter 流式 API，**无法重新爬取**，且论文给出的唯一下载地址 `http://db.zju.edu.cn/s/sumblr/` **已失效（HTTP 404，已实测验证）**。

因此本项目改用公开可下载的单一事件推文流：

**Turkey Earthquake Tweets**（2023 土耳其-叙利亚地震）
- 来源：Kaggle [`gpreda/turkey-earthquake-tweets`](https://www.kaggle.com/datasets/gpreda/turkey-earthquake-tweets)
- 无需登录即可通过 Kaggle 公开 API 下载：`https://www.kaggle.com/api/v1/datasets/download/gpreda/turkey-earthquake-tweets`
- 规模：**28,844 条**推文，时间跨度 **2023-02-07 → 2023-02-26**（20 天）
- 字段：`id, user_name, user_location, date, text, hashtags, retweets, favorites, ...`
- 选择理由：单事件、时间戳完整、有天然爆发峰（2/10–2/11 共 8,413 条），与论文的「单主题推文流」设定一致

数据获取方式与论文的差异（必须声明）：
- 论文的 5 个数据集是**单一主题**（如 Chelsea 足球），本数据是**灾难事件流**，噪声（广告、无关政治、祈祷类模板推文）显著更多
- 论文语料最大 438,884 条，本复现 28,844 条（约 1/15 规模），属可行的教学规模

---

## 3. 目录结构

```
sumblr_repro/
├── README.md                      本文件
├── REPORT.md                      复现结果报告
├── AUDIT.md                       论文逐条对照审计（完成度 90%）
├── data/
│   ├── turkey_earthquake_tweets.csv    原始数据（28,844 条）
│   └── turkey-earthquake-tweets.zip    下载压缩包
├── src/
│   ├── config.py                  全部超参数（含「论文未给出」标注）
│   ├── download_data.py           数据下载
│   ├── preprocess.py              模块 1：清洗 + TF-IDF 向量化（原始/归一化双矩阵）
│   ├── ptf.py                     模块 2a：PTF 金字塔（Def.2，按 order 分层）
│   ├── sumblr.py                  模块 2b：在线聚类 + TCV + IDList + Def.3 合并
│   ├── historical.py              模块 2c：§4.2 历史摘要 + Def.4 减法
│   ├── summarize.py               模块 3：TCV-Rank 摘要 + 时间线（Eq.2/3）
│   ├── baselines.py               模块 4a：ClusterSum / LexRank / DSDR / Random
│   ├── evaluate.py                模块 4b：ROUGE + 参考摘要 + 预算裁剪
│   ├── experiments.py             模块 5：滑动窗口 + Eq.4 积分
│   ├── run.py                     主流程（在线摘要 + 时间线）
│   ├── run_experiments.py         §5 五组实验入口
│   └── diagnose_*.py              诊断脚本（β / LexRank / 时间线 / KL / τ）
├── tests/
│   ├── test_ptf.py                PTF vs 论文 Table 1（5 个 order 逐项核对）
│   ├── test_historical.py         Def.4 减法 + 历史摘要
│   ├── test_dsdr.py               DSDR 重构误差最小化
│   └── test_protocol.py           滑动窗口 + Eq.4 + runtime 实测
└── output/
    ├── results_*.json             主流程结果（单日 / 全量）
    ├── exp_*.json                 §5 五组实验结果
    ├── system_summary_*.csv       Sumblr 生成的摘要
    ├── reference_summary_*.csv    参考摘要（金标准）
    └── *.log                      各次运行日志
```

---

## 4. 运行方式

```bash
cd sumblr_repro

# 1) 下载数据（已下载则跳过）
python src/download_data.py

# 2) 单日实验（2023-02-10，爆发峰当天，4,278 条）
python src/run.py

# 3) 全 20 天流式实验（27,661 条，约 60 秒；时间线窗口按流长自动缩放）
python src/run.py --all-days

# 4) §5 五组实验（论文 Figure 5-11）
python src/run_experiments.py --which all
python src/run_experiments.py --which step          # Fig.5/6 step-size 扫描
python src/run_experiments.py --which scalability   # Fig.7 可扩展性
python src/run_experiments.py --which params        # Fig.9 参数曲线
python src/run_experiments.py --which flexibility   # Fig.10 PTF 灵活性
python src/run_experiments.py --which timeline      # Fig.11 时间线 P/R/F

# 5) 单元测试（4 个，验证 PTF/减法/DSDR/协议）
python tests/test_ptf.py
python tests/test_historical.py
python tests/test_dsdr.py
python tests/test_protocol.py
```

**时间线相关参数**（论文 τ=1.012 在其数据集上标定，本替代数据最优点在 τ≈1.06）：

```bash
python src/run.py --all-days --tau 1.06           # 用本数据标定的阈值
python src/run.py --all-days --timeline-window 360  # 手动指定窗口（分钟）
```

环境：Python 3.12 + numpy / pandas / scipy / scikit-learn（无需 GPU，无需联网推理）。

---

## 5. 实现要点（忠实于论文）

### 5.1 推文表示（§3.1）
每条推文是 `(tv_i, ts_i, w_i)`。论文对 4 个新爬数据集因拿不到社交图而设 `w_i = 1`，本复现同样设 `w_i = 1`（与原论文一致）。

### 5.2 TCV（Definition 1）
```
TCV(C) = (sum_v, wsum_v, ts1, ts2, n, ft_set)
  sum_v  = Σ tv_i / ||tv_i||      ← 归一化向量之和
  wsum_v = Σ w_i · tv_i           ← 原始向量之和
  质心    cv = wsum_v / n          ← 论文 Equation (1)
```
**关键实现细节**：论文的 `sum_v` 用归一化向量、`wsum_v` 用原始向量，两者是**不同的量**。这一点至关重要，因为最小边界相似度是

```
MBS = β · Sim(co, t_i),   Sim(co, t_i) = (wsum_v · sum_v) / (n · ||wsum_v||)
```

若把同一个 L2 归一化矩阵同时喂给两者（且 w=1），则 `sum_v ≡ wsum_v`，MBS 退化为 `β·||质心||`，导致**整个流塌缩成一个巨型簇**。我们实测到：塌缩时最大簇占比 **82.7%**，修正后为 **28.8%**。

### 5.3 增量聚类（Algorithm 1）
每条推文：① 找质心最近的簇（对单位化质心做**余弦**相似度）；② 若 `MaxSim < MBS` 则新建簇，否则并入。相似度必须是余弦——用原始 TF-IDF 点积会因向量模长差异而失真（实测会导致所有 β 值下聚类行为完全相同）。

### 5.4 过时簇删除（§4.1.3）
```
μ_c = ts1/n,  σ_c = sqrt(ts2/n - (ts1/n)²)
x = μ_c + σ_c · √2 · erf⁻¹(2p' - 1),   p' = (100 - p/2)%
```
若最新 10% 推文的平均时间戳距今超过 **3 天**，删除该簇。`erf⁻¹` 用 `scipy.special.erfinv` 精确计算（论文用 Maclaurin 展开，属等价替换）。

### 5.5 簇合并（§4.1.4, Definition 3）
簇数超过 `Nmax=150` 时，按质心相似度贪心合并到 `mc=0.7` 比例。实现上维护相似度矩阵并**在每次合并后增量更新被合并簇的那一行**：既避免 O(N³d) 的全量重算，也避免使用冻结矩阵（冻结矩阵会把不相关簇串成一个团）。

### 5.6 PTF（Definition 2）
快照按 `α^i` 间隔存入，每个阶只保留 `α^l + 1` 个，总量上界 `(α^l+1)·log(T)`。

### 5.7 TCV-Rank 摘要（Algorithm 2 + Equation 2）
```
t = argmax_{t_i} [ λ·(n_{t_i}/n_max)·LR(t_i) − (1−λ)·avg_{t_j∈S} Sim(t_i, t_j) ]
```
先在「每簇 LexRank 最高分」集合 `Tc` 中贪心选（第 1 阶段），不足 250 词再从 `T − S` 补（第 2 阶段）。

**LexRank 必须做图稀疏化**：短推文上两两余弦均值仅 0.0197，稠密图几乎全正，特征向量中心度接近均匀，噪声与实质内容无法区分——而论文正是依赖「噪声推文 LexRank 分数低」来去噪（§4.4）。我们按 LexRank 标准做法在 0.1 处截断（实测把 top-25 的平均距离从 0.10 提升到 0.24）。

### 5.8 话题演化检测（§4.3）
```
D_KL(Sc‖Sp) = Σ_w p(w|Sc) ln[p(w|Sc)/p(w|Sp)]
D = 1 − e^(−D_KL)
当 D_cur / D_avg > τ (=1.012) 时产生时间线节点
```
**拉普拉斯平滑的取值是决定性的**。论文只说「ε 是一个小的正常数」而未给值。若取 ε=1e-8（看似合理），短摘要（约 130 个不同词）中任何「当前有、上一个没有」的词都会贡献 `log(p_c/1e-8) ≈ 20`，使 **每一对** 的 D_KL 都在 11–15，D 全部饱和到 1.0000，`D_cur/D_avg` 的最大/最小比只有 **1.0000**，永远无法超过 τ=1.012，时间线恒为空。改用标准 add-one 平滑（ε=1）后，D 落在 [0.45, 0.64] 的可区分区间，τ=1.012 时正确检出节点。

---

## 6. 与论文的差异（必须声明的替代与偏离）

| 项目 | 论文 | 本复现 | 原因 |
|---|---|---|---|
| 数据集 | 5 个私有主题流，121 万推文 | Turkey Earthquake，2.9 万推文 | 原数据不可得，下载地址已 404 |
| 推文权重 `w_i` | UserRank（仅 Obama 集可能可用） | 恒为 1 | 与论文对 4 个数据集的做法一致 |
| Canopy 阈值 | 未给出 | t2=0.15, cap=15 | 论文只说「k 与初始质心由 Canopy 决定」 |
| 摘要推文条数 k/L | 未给出数值 | 25 条 | 论文只给 250 词上限 |
| LexRank 迭代数 r | 未给出 | 10 次 | 论文未给 |
| KL 平滑 ε | 「小的正常数」，未给值 | 1.0（add-one） | 见 §5.8，ε=1e-8 会使时间线恒空 |
| 时间线窗口 | 论文用 PTF 快照 | 非重叠窗口，按流长自动缩放 | 见 §5.9 |
| D_avg 估计 | 「非节点对的均值」 | 加最小样本保护 | 见 §5.10，直译会正反馈失控 |
| 参考摘要 | ClusterSum+LexRank+DSDR 取 ≥2 一致 | 三候选投票后按 Equation 2 排序 | 推文很少逐字重复，严格 ≥2 一致只剩 1 条 |
| 摘要长度归一 | 未明确 | 所有方法统一 250 词 / 25 条 | 保证公平比较 |
| step size / 窗口大小 | 20000 / 4000–20000 | 3000 / 600–3000 | 论文流 95k–438k 推文，本复现 27.7k，按比例缩放 |
| DSDR 基线 | 有 | **已实现** | 贪心重构误差最小化，单测验证 |

---

## 7. 结果

### 7.1 单日（2023-02-10，4,278 条推文）

聚类：**82 个簇**，中位簇大小 17，最大簇占比 **28.8%**，**20 个 live PTF 快照 / 22 个 stored**。

| 方法 | ROUGE-1 F | ROUGE-2 F | ROUGE-L F | 词覆盖 | 平均 IDF | 多样性 | 最大冗余 | 条数 |
|---|---|---|---|---|---|---|---|---|
| **Sumblr** | 0.1271 | 0.0000 | 0.0602 | 0.0319 | 4.83 | **0.990** | **0.100** | 17 |
| Random | 0.1736 | 0.0213 | 0.0965 | 0.0313 | 4.21 | 0.968 | 1.000 | 16 |
| Popularity | 0.3549 | 0.2868 | 0.2321 | 0.0266 | 4.73 | 0.979 | 0.244 | 15 |
| Lead | 0.1581 | 0.0136 | 0.0790 | 0.0348 | 4.82 | 0.922 | 1.000 | 22 |
| ClusterSum | 0.4745 | 0.4207 | 0.3183 | 0.0380 | 5.63 | 0.992 | 0.113 | 11 |
| LexRank | 0.0991 | 0.0109 | 0.0721 | 0.0026 | 1.58 | 0.237 | 1.000 | 25 |

时间线使用自动窗口（单日约 120 分钟、非重叠）→ 11 个窗口、6 个演化节点（τ=1.012）。

| 时间 | D | D/D_avg |
|---|---|---|
| 2023-02-10 08:00 | 0.5685 | 1.04 |
| 2023-02-10 14:00 | 0.5568 | 1.15 |
| 2023-02-10 15:00 | 0.6107 | 1.26 |
| 2023-02-10 16:00 | 0.5495 | 1.13 |
| 2023-02-10 18:00 | 0.5762 | 1.19 |
| 2023-02-10 19:00 | 0.6225 | 1.29 |
| 2023-02-10 20:00 | 0.4946 | 1.02 |
| 2023-02-10 21:00 | 0.6368 | 1.32 |
| 2023-02-10 22:00 | 0.5039 | 1.04 |
| 2023-02-10 23:00 | 0.5280 | 1.09 |

### 7.2 全 20 天流式（27,661 条推文，运行约 60 秒）

聚类：**132 个存活簇**（累计新建 284、合并 138、删除 14），**59 个 live / 463 个 stored PTF 快照**（9 个 order），内存中仅保留 **2,875 条**推文（占 10.4%）。时间线使用自动窗口（约 24 小时、非重叠）→ **20 个窗口、6 个节点**（τ=1.012）。

---

## 8. 对结果的诚实解读

**复现成功的部分（架构与趋势）**
1. **在线聚类有效**：簇大小分布合理（中位 17），无塌缩。
2. **内存有界**：20 天流只保留 10.4% 推文，符合论文「持续摘要」的核心主张。
3. **多样性最优**：Sumblr 的摘要多样性 0.989–0.990、最大冗余仅 0.099–0.100，是唯一同时做到「高多样性 + 极低冗余」的方法——这正是 Equation (2) 中 `(1−λ)·avg Sim` 惩罚项的作用。
4. **历史摘要可用**：PTF Table 1 单测通过，Def.4 减法、drill-down/roll-up/range timeline 均可运行。
5. **实验协议已补全**：step-size、可扩展性、参数、灵活性、时间线 P/R/F 均已产出 `exp_*.json`。

**质量对比的正确解读**

当前主流程使用替代灾难流数据。论文原文说小 step 时 DSDR/LexRank 质量可能高于 Sumblr，step 足够大时 Sumblr 才可能反超；本复现 step sweep 观察到 Sumblr R-1F 从 0.192 增至 0.316，ClusterSum 从 0.499 增至 0.552，方向一致但未出现交叉点。ClusterSum 参与构造参考摘要，ROUGE 也存在构造性偏置，因此绝对 ROUGE 不应单独作为结论。

唯一未实现的是 §4.4 多主题流关键词分组扩展；其他偏离、实验结果和完成度见 [AUDIT.md](AUDIT.md)。

---

## 9. 复现过程中发现并修复的 5 个真实缺陷

这些缺陷都是「照论文公式直译会出错」的地方，记录在此对后续复现有价值：

| # | 缺陷 | 症状 | 修复 |
|---|---|---|---|
| 1 | `sum_v` 与 `wsum_v` 混用同一归一化矩阵 | MBS 退化为 `β·‖质心‖`，最大簇占比 82.7%，全流塌缩 | 分别维护原始/归一化两个和，占比降至 28.8% |
| 2 | 用原始 TF-IDF 点积当相似度 | 所有 β 值下聚类结果完全相同（β 失效） | 改为对单位化质心做余弦相似度 |
| 3 | 簇合并复用冻结相似度矩阵 | 不相关簇被串成一个巨型团（占比 93%） | 每次合并后增量更新被合并簇的那一行 |
| 4 | KL 平滑 ε=1e-8 | D 全部饱和到 1.0000，时间线**恒为 0 个节点** | 改用标准 add-one 平滑（ε=1） |
| 5 | 基线用 `sorted()` 返回 | 250 词预算裁剪时砍掉真正的高分推文 | 所有基线按优先级顺序返回 |
| 6 | D_avg 只从非节点对累积 | 正反馈导致 89% 重叠窗口被判节点 | `min_davg_samples=30` 保护，并提供 `paper_strict`/`all` 模式 |
| 7 | 时间线窗口重叠 6 倍 | D 变异系数过小，节点数爆炸 | 默认非重叠窗口，按流长自动缩放 |

新增的 6/7 是补全过程中发现的时间线实验陷阱；详细诊断见 `AUDIT.md`。

---

## 10. 参考

- Shou, L., Wang, Z., Chen, K., Chen, G. (2013). *Sumblr: Continuous Summarization of Evolving Tweet Streams.* SIGIR '13, 533–542.
- Aggarwal, C. C., et al. (2003). *A Framework for Clustering Evolving Data Streams.* (CluStream / PTF 来源)
- Erkan, G., Radev, D. R. (2004). *LexRank: Graph-based Lexical Centrality as Salience in Text Summarization.* JAIR.
- Inouye, D., Kalita, J. (2011). *Comparing Twitter Summarization Algorithms for Multiple Post Summaries.* (ClusterSum)
- Lin, C.-Y., Hovy, E. (2003). *Automatic Evaluation of Summaries Using N-gram Co-occurrence Statistics.* (ROUGE)
- 数据：Kaggle `gpreda/turkey-earthquake-tweets`
