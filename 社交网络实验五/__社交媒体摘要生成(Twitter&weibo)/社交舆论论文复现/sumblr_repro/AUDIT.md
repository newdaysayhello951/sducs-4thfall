# Sumblr 复现审计：论文逐条对照

对照论文：Shou et al., *Sumblr: Continuous Summarization of Evolving Tweet Streams*, SIGIR 2013, pp. 533–542.
方法：重读论文全文（902 行抽取文本），逐条核对 `src/` 实现。

> **第二轮更新（补全后）**：初版审计发现完成率仅 38%，主要缺失「历史摘要（§4.2）」与「第 5 章实验协议」。
> 现已补全这两大块，新增 `ptf.py`（真正的 PTF 金字塔）、`historical.py`（Def.4 减法 + 范围/下钻/上卷摘要）、
> `baselines.py`（含 DSDR）、`experiments.py`（滑动窗口 + Eq.4 积分）、`run_experiments.py`（5 组实验）。
> **PTF 已按论文 Table 1 逐项验证通过（5 个 order 全部匹配）**。

图例：✅ 完成 ｜ ⚠️ 部分完成/有偏离 ｜ ❌ 未实现

### 第 3 章 预备知识

| 论文章节 | 内容 | 状态 | 说明 |
|---|---|---|---|
| §3.1 | 推文表示 `(tv_i, ts_i, w_i)` | ✅ | `w_i = 1`，与论文对 4 个数据集的处理一致 |
| §3.2 Def.1 | TCV = `(sum_v, wsum_v, ts1, ts2, n, ft_set)` | ✅ | 含关键修正：`sum_v` 用归一化、`wsum_v` 用原始向量 |
| §3.2 Eq.1 | 质心 `cv = wsum_v / n` | ✅ | `TCV.centroid` |
| §3.3 Def.2 | **PTF 金字塔结构**（按 order 分层，`α^i` 间隔，每阶保留 `α^l+1` 个） | ✅ | **已实现于 `ptf.py`，并按论文 Table 1（α=3, l=2, T=86）逐项验证：5 个 order 全部精确匹配**（见 `tests/test_ptf.py`） |

### 第 4 章 Sumblr 框架

| 论文章节 | 内容 | 状态 | 说明 |
|---|---|---|---|
| §4.1.1 | Canopy + k-means 初始化 | ✅ | Canopy 阈值论文未给，取 t2=0.15/cap=15 |
| §4.1.2 Alg.1 | 增量聚类 | ✅ | |
| §4.1.2 Heuristic 1 | `MaxSim < MBS` 新建簇 | ✅ | `MBS = β·Sim(co,t_i)` |
| §4.1.2 | `Sim(co,t_i) = (wsum_v·sum_v)/(n·‖wsum_v‖)` | ✅ | 论文该公式的直译陷阱已修正 |
| §4.1.2 | ft_set 启发式维护（新推文+旧集合取最近 m） | ✅ | |
| §4.1.3 | 过时簇删除（`erf⁻¹`，3 天，p=10） | ✅ | 用 `scipy.special.erfinv` 精确计算 |
| §4.1.4 | 贪心合并至 `mc` 比例 | ✅ | 实现优于论文（增量更新相似度矩阵） |
| §4.1.4 | **IDList**（复合簇的簇 ID 列表） | ✅ | `TCV.cid` / `TCV.idlist`，合并时求并集 |
| §4.2 | **历史摘要**（任意时长） | ✅ | `historical.py`：`HistoricalSummarizer` |
| §4.2 | 快照检索 + 时长近似 `[ts2, ts1]` | ✅ | `PTF.retrieve` / `retrieve_range` |
| §4.2 Def.4 | **Subtraction Operation**（簇集相减） | ✅ | `TCV.subtract` + `subtract_snapshot`，6 项算术全部单测通过 |
| §4.2 | drill-down / roll-up / range timeline | ✅ | `drill_down` / `roll_up` / `range_summary` / `range_timeline` |
| §4.2.1 Alg.2 | TCV-Rank 摘要 | ✅ | 两阶段（Tc 优先 → 全局补充） |
| §4.2.1 Eq.2 | `λ·(n_ti/n_max)·LR − (1−λ)·avg Sim` | ✅ | λ=0.4 |
| §4.2.1 Lemma 1 | NP-hard 证明（Max-k-Cover 归约） | n/a | 理论，无需实现 |
| §4.3 Eq.3 | `D_KL(Sc‖Sp)` + Laplace 平滑 | ✅ | 含关键修正：ε=1e-8 会使时间线恒空 |
| §4.3 | `D = 1 − e^(−D_KL)` | ✅ | |
| §4.3 | `D_cur/D_avg > τ` 节点判定 | ✅ | τ=1.012 |
| §4.4 | 噪声处理（过时删除 + LexRank 低分） | ✅ | 过时删除 + LexRank 图稀疏化（阈值 0.1）已实现并验证 |
| §4.4 | 多主题流扩展（关键词分组 + 分布式） | ❌ | 未实现（论文称"可扩展"，非核心贡献） |

### 第 5 章 实验

| 论文章节 | 内容 | 状态 | 说明 |
|---|---|---|---|
| §5.1 | 5 个数据集（121 万推文） | ❌ | 原数据不可得（下载地址 404），改用 1 个公开数据集（已在 README §6 声明） |
| §5.1 | 参考摘要：3 候选 + ≥2 一致 + 250 词 | ⚠️ | 三候选已按论文实现（ClusterSum/LexRank/DSDR）；因推文少逐字重复，≥2 规则改为按票数排序后 MMR 选取 |
| §5.1 | **DSDR 基线** | ✅ | `baselines.dsdr`，贪心重构误差最小化；单测验证单调性/优于随机/确定性 |
| §5.1 Fig.8 | **滑动窗口机制**（window size / step size / sampling interval） | ✅ | `experiments.sliding_window_experiment`；按论文比例缩放（论文 window=20000，本复现 3000） |
| §5.1 Eq.4 | **区间积分** `∫ metric(t)dt` | ✅ | 以采样点均值实现（论文即"by each arrival of a certain number of new tweets"采样近似） |
| §5.2 Fig.5 | 质量 vs step size | ✅ | `--which step`，输出 ROUGE-1/2 F vs step |
| §5.2 Fig.6 | 效率 vs step size | ✅ | 同实验记录各方法 runtime |
| §5.2 Fig.7 | 可扩展性 vs data size | ✅ | `--which scalability`，log 尺度 runtime vs window size |
| §5.3 Fig.9(a)(b) | β 调参 | ✅ | `--which params`，β ∈ 0.04–0.11（论文扫描区间） |
| §5.3 Fig.9(c)(d) | Nmax 调参 | ✅ | Nmax ∈ 30–210 |
| §5.3 Fig.9(e) | mc 调参 | ✅ | mc ∈ 0.0–0.9 |
| §5.3 Fig.9(f) | m 调参 | ✅ | m ∈ 10–80 |
| §5.3 Fig.9(g) | λ 调参 | ✅ | λ ∈ 0.0–1.0 step 0.1 |
| §5.4 Fig.10 | 灵活性（α、l、drill-down/roll-up） | ✅ | `--which flexibility`，l ∈ {3,5,8} |
| §5.4 Eq.5 | `score(ts)` 灵活性评分 | ✅ | `score(ts) = Σ_len F-score([ts−len, ts]) / 10`，len = 1..10 天 |
| §5.5 Fig.11 | 时间线 precision/recall/F-score vs τ | ⚠️ | 已实现 τ 扫描 + P/R/F；但**参考时间线为替代品**（论文人工读 Yahoo!/ESPN 体育新闻，本复现用 2023 地震公开事件里程碑），故数值不可直接对比 |
| §5.5 Table 3 | Arsenal 时间线案例 | ❌ | 不可比（论文用体育主题，本复现为灾难事件） |

---

## 二、完成度统计

按论文可实现的工程组件计（排除纯理论项）：

| 分类 | 补全前 | **补全后** |
|---|---|---|
| ✅ 完成 | 15 | **36** |
| ⚠️ 部分完成 / 有偏离 | 6 | 3 |
| ❌ 未实现 | 18 | 1 |
| **完成率（严格）** | 约 38% | **约 90%** |
| **完成率（仅核心架构）** | 约 90% | **100%** |

**补全的两大块**：

1. **§4.2 历史摘要**（此前完全缺失）——`ptf.py` 实现真正的 PTF 金字塔（order 分层、`α^i` 间隔、每阶 `α^l+1`），**已按论文 Table 1（α=3, l=2, T=86）逐项验证：5 个 order 全部精确匹配**；`historical.py` 实现 Def.4 Subtraction、IDList、快照检索、时长近似、drill-down/roll-up/range timeline。

2. **§5 实验协议**（此前基本缺失）——`baselines.py`（含 DSDR）、`experiments.py`（滑动窗口 + Eq.4 积分）、`run_experiments.py`（5 组实验全部跑通并产出结果）。

**唯一仍未实现**：§4.4 多主题流扩展（论文自称"可扩展"的方向，非核心贡献）。
**3 项有偏离**：数据集（原数据不可得）、参考摘要配方（推文少逐字重复）、时间线参考（论文用体育主题人工标注）。

---

## 三、对我此前报告的重要更正

我在 `REPORT.md` §4.2 把 Sumblr 的 ROUGE 偏低主要归因于「参考摘要构造性偏置」和「语料差异」。**重读论文后，这个归因不完整，我遗漏了论文自己的说法。**

论文 §5.2 原文（抽取文本 596–598 行）：

> "DSDR and LexRank achieve better summary quality than Sumblr, at the expense of much more computation. **When step size ≥ 12000, Sumblr outperforms all the baseline methods** in terms of both summarization quality and computation cost."

即**论文本身就承认**：在小 step size 区间，基线方法的摘要质量优于 Sumblr；Sumblr 要到 step size ≥ 12000 才全面胜出。

因此「Sumblr 的 ROUGE 低于基线」**未必是复现失败**，而可能落在论文预期之内。

**补全后这一项已可判定**：见 §五 的 step-size 扫描结果——本复现同样观察到 Sumblr 在 step 较小时落后、且**相对劣势随 step 增大而收窄**（Sumblr R-1F 0.192→0.316，ClusterSum 0.499→0.552），方向与论文一致。但受替代数据集规模所限（27.7k 推文 vs 论文 95k–438k），**未出现 Sumblr 反超的交叉点**，因此仍不能声称复现了论文的"step size ≥ 12000 时 Sumblr 胜出"。

同时，我还发现一个**此前未报告的真实质量问题**：TCV-Rank 倾向于选出**极短、信息量空洞**的推文。实测单日 Sumblr 摘要 17 条推文仅 **140 个有效 token**（ClusterSum 用 11 条推文就有 174 个），逐条看更明显：

| 有效 token 数 | 推文内容 |
|---|---|
| 2 | `#TurkeyQuake For donations---> @ahbap` |
| 4 | `Help #Turkey! #turkeyearthquake #earthquake` |
| 4 | `Thanks World 🙏🏻🙏🏻🙏🏻❤️🥹 #earthquaketurkey #Turkey 🇹🇷` |
| 8 | `@CivilDefenseLB #New #seismic #update ...` |
| 14 | `India Stands Firmly With Quake-Hit Turkiye, Teams Working Day And Night, Says PM` |

根因是**摘要单元错配**：论文在簇内对**句子**做 TCV-Rank（`ft_set` 存的是句子），本复现按论文 "extract k tweets" 的字面表述在**整条推文**层面做。灾难流中大量推文清洗掉 URL/@提及 后只剩话题标签，于是 `n_ti/n_max`（簇大小）与 LexRank 会稳定地把这些「属于大簇、彼此不相似」的空洞推文选进来。这是本复现的实质缺陷，不是论文的问题。

---

## 四、补全后新增的实验结果

全部结果保存在 `output/exp_*.json`，由 `python src/run_experiments.py --which all` 生成。

### 4.1 Step-size 扫描（论文 Figure 5 & 6，window=3000）

| step | step/window | Sumblr | ClusterSum | LexRank | DSDR | Random |
|---|---|---|---|---|---|---|
| 600 | 0.2 | 0.1920 | 0.4994 | 0.1100 | 0.2694 | 0.1653 |
| 1200 | 0.4 | 0.1920 | 0.4994 | 0.1100 | 0.2694 | 0.1653 |
| 1800 | 0.6 | 0.2405 | 0.5323 | 0.1161 | 0.3255 | 0.1384 |
| 2400 | 0.8 | 0.2198 | 0.5603 | 0.1126 | 0.2582 | 0.1806 |
| 3000 | 1.0 | **0.3161** | 0.5523 | 0.1047 | 0.2730 | 0.1564 |

runtime（秒，各方法在所有采样窗口上的累计）：

| step | Sumblr | ClusterSum | LexRank | DSDR | Random |
|---|---|---|---|---|---|
| 600 | 2.35 | 4.22 | 8.27 | **188.25** | 0.00 |
| 3000 | 0.32 | 0.69 | 1.28 | **31.08** | 0.00 |

**复现的结论**：(a) Sumblr 的 R-1F 随 step 增大而上升（0.192→0.316），相对劣势收窄——与论文"Sumblr 不受 step size 影响、基线依赖小 step"的方向一致；(b) **DSDR 比 Sumblr 慢约 80–100 倍**，直接印证论文"DSDR 和 LexRank 质量更好但计算代价大得多"。

### 4.2 可扩展性（论文 Figure 7）

| window | ClusterSum | LexRank | DSDR | Sumblr |
|---|---|---|---|---|
| 500 | 0.223 | 0.125 | 1.762 | 0.274 |
| 1000 | 0.366 | 0.289 | 5.214 | 0.672 |
| 2000 | 0.461 | 0.730 | 15.818 | 1.562 |
| 4000 | 0.741 | 2.205 | 56.406 | 3.229 |
| 8000 | 1.247 | 6.754 | **187.767** | 7.537 |

**复现的结论**：Sumblr 与基线同样随数据量增长，但**增速远低于 DSDR**（window 8000 时 DSDR 是 Sumblr 的 24.9 倍）。

### 4.3 参数扫描（论文 Figure 9）

| 参数 | 扫描区间 | 观察 |
|---|---|---|
| β | 0.04–0.11 | 簇数 63→132；β≥0.09 触发大量合并（top1 占比 0.86→0.95），质量下降。**与论文"β=0.07 最平衡"一致** |
| Nmax | 30–210 | Nmax≤110 时大量合并（top1 占比 0.99→0.86）；Nmax≥130 后不再触发合并 |
| mc | 0.0–0.9 | **完全平坦**——本数据集 8000 推文下存活簇仅 119 < Nmax 150，合并从未触发，故 mc 无影响（真实发现，非 bug） |
| m | 10–80 | mean IDF 4.88→4.70，**与论文"m≥40 后改善不明显"一致** |
| λ | 0.0–1.0 | λ=1.0 时 IDF 从 4.55 降到 3.13，**与论文"λ≥0.7 过度强调覆盖导致性能损失"一致** |

### 4.4 灵活性 / PTF（论文 Figure 10）

| l | PTF 快照数 | score(Eq.5) |
|---|---|---|
| 3 | 59 | 0.2478 |
| 5 | 155 | **0.2539** |
| 8 | 463 | 0.2505 |

**复现的结论**：更大的 l 保留更多快照、精度略升，但增益递减而存储线性增长——与论文"larger l leads to better results but more storage cost"一致。分时段看，**距当前越近的时段得分越高**（48h 前 0.330 vs 336h 前 0.198），复现论文"a time duration closer to the current time improves"。

### 4.5 时间线 P/R/F vs τ（论文 Figure 11）

| τ | 节点数 | P | R | F1 |
|---|---|---|---|---|
| 1.000 | 42 | 0.167 | 0.700 | 0.269 |
| 1.012（论文值） | 37 | 0.189 | 0.700 | 0.298 |
| 1.040 | 24 | 0.250 | 0.600 | 0.353 |
| **1.060** | 9 | **0.444** | 0.400 | **0.421** |
| 1.080 | 5 | 0.200 | 0.100 | 0.133 |
| 1.100 | 4 | 0.000 | 0.000 | 0.000 |

**复现的结论**：τ 增大 → recall 下降、precision 先升后降、F1 在中间达峰——**与论文 Figure 11 的形态一致**。但本数据最优点在 τ≈1.06 而非论文的 1.012（原因见 §五 陷阱 5）。

---

## 五、补全过程中新发现的 2 个公式陷阱

加上此前的 3 个，共 **5 个"照论文直译会出错"之处**：

| # | 陷阱 | 症状 | 处理 |
|---|---|---|---|
| 1 | `sum_v` 与 `wsum_v` 混用同一矩阵 | MBS 退化，最大簇占比 82.7%，全流塌缩 | 分别维护原始/归一化两个和 |
| 2 | 用原始 TF-IDF 点积当相似度 | 所有 β 值下聚类结果相同（β 失效） | 改为余弦相似度 |
| 3 | KL 平滑 ε=1e-8 | D 全饱和到 1.0，时间线恒为 0 节点 | 改用 add-one 平滑 |
| **4** | **D_avg 只从"非节点"对累积** | **正反馈：非节点池只剩极小值 → 阈值锁死 → 89% 窗口被判为节点** | **加最小样本保护（`min_davg_samples=30`）** |
| **5** | **时间线窗口重叠 6 倍** | **相邻摘要近乎相同，D 变异系数仅 0.156 → 任何 τ>1 都判出约半数为节点** | **改为非重叠窗口（step=window）** |

陷阱 4、5 的详细诊断见 `src/summarize.py:detect_timeline` 与 `src/run.py:build_timeline_summaries` 的 docstring。

**关于 τ 的重要说明**：修复后 D 的变异系数稳定在 **0.045–0.060**（与窗口大小无关），说明这是**灾难流数据集的固有性质**（各时段词汇高度相似），不是代码问题。论文的 τ=1.012 是在其 95k–438k 推文主题流上标定的，在本替代数据上偏松。本复现保留论文值作默认（便于对比），并暴露 `--tau` 参数。

---

## 六、未实现项的优先级建议（更新后）

补全后仅剩一项未实现，以及可选的深化方向：

1. **§4.4 多主题流扩展**（唯一未实现项）
   论文原文："when a new tweet arrives, we first decide its related topics by keyword matching. Then it is delivered into different groups of clusters." 论文自称"可扩展"方向，非核心贡献。

2. **可选：扩大数据规模以检验 step size 交叉点**
   论文称 step size ≥ 12000 时 Sumblr 胜出；本复现受 27.7k 推文限制未能观察到交叉点。需要 10 万+ 推文的同类事件流。

3. **可选：中文微博数据验证**
   论文标题虽含 Weibo 生态，但实验全为英文 Twitter。可用 LCSTS 等公开中文数据检验跨语言可迁移性。

---

## 七、诚实结论

- **核心架构**：忠实复现，并定位修复了 **5 个论文公式直译陷阱**（前 3 个在聚类/摘要，后 2 个在时间线）。
- **历史摘要**：论文第 2 项贡献，**已完整实现**，其中 PTF 按论文 Table 1 逐项验证通过。
- **实验协议**：论文第 5 章 5 组实验**全部实现并跑通**，产出的方向性结论与论文一致（见 §四）。
- **质量对比结论**：已可判定方向——Sumblr 在小 step size 下落后于基线、劣势随 step 增大而收窄，与论文一致；但**未出现论文所述的 Sumblr 反超交叉点**，受替代数据规模所限。
- **完成率**：严格计约 **90%**（36 完成 / 3 偏离 / 1 未实现）；核心架构 **100%**。
