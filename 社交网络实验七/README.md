# TrustSVD 独立复现

目标论文：Guibing Guo, Jie Zhang, Neil Yorke-Smith. *TrustSVD: Collaborative Filtering with Both the Explicit and Implicit Influence of User Trust and of Item Ratings*. AAAI 2015, pp.123–129。

本项目根据论文的公式独立编写。**未读取、复制或导入作者发布的 TrustSVD 实现，以及其他现成模型实现。** 使用 NumPy/SciPy 处理数值与稀疏矩阵、Numba 加速自己编写的循环、SciPy 的通用优化器；这些不是现成推荐模型。

公式、梯度推导及其与代码的对应关系见 [METHOD.md](METHOD.md)。主训练使用自己编写的梯度下降，通用SciPy优化器仅用于分开保存的补充探索。

## Ciao 补充实验（用户已同意采用可获得版本）

2026-10-26：使用找回的 Ciao 作者原始包，排除超出声明评分范围的34条0分记录，保留其余284,052条评分（7,375用户、105,096物品）和111,781条信任边。保留重复观察，按用户-物品对分组划分以避免泄漏。该版本不等同于论文280,391条评分、99,746物品的输入。

预处理来源、规则和原始/输出校验值见 `datasets/ciao/preparation.json`。补充实验单独保存于 `results/ciao_original_gd/`，日志为 `results/ciao_original_training.log`。Flixster 按用户要求不再查找和运行。

```powershell
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
D:\anaconda\python.exe -u -m trustsvd_repro.experiment --datasets ciao --allow-mismatch ciao --run ciao_original_gd --optimizer gd --maxiter 200 --jobs 2
D:\anaconda\python.exe -m trustsvd_repro.report --run ciao_original_gd
D:\anaconda\python.exe -m trustsvd_repro.audit --run ciao_original_gd
```

Ciao补充实验已完成100/100组，0失败，100组结果复核通过。连同此前两个数据集共完成300组评估；汇总见 [三数据集实验汇总](results/combined_report/三数据集实验汇总.md)，Ciao详细报告见 [Ciao实验报告](results/ciao_original_gd/report/实验报告.md)。Ciao的TrustSVD All RMSE为0.965598（d=5）、0.966041（d=10），本次未优于SVD++。

以下为此前仅完成两个匹配数据集时的记录。

## 当前范围

- 主实验已完成FilmTrust、Epinions共200组评估（10个模型×2种维度×5折×2个数据集），18项数学/隔离测试和200组结果文件复核通过。
- **当前仍是部分复现：缺少Ciao与Flixster指定版本，且本次All RMSE没有重现TrustSVD相对SVD++的优势。** 真实分数与原文分数分开保存。
- 实现 TrustSVD，以及 Table 2 的 UserAvg、ItemAvg、PMF、RSTE、SoRec、SoReg、SocialMF、TrustMF、SVD++。
- 实现 5 折评估、d=5/10、All/Cold Start、信任度分组、信任覆盖/相关性分析、配对检验和 Table 3 对照。
- FilmTrust 和 Epinions 的原始数据已下载，四项统计与论文一致。
- 第二轮已找回作者发布的Ciao原始压缩包，但其统计与论文仍有差异；新的Flixster包只有社交图。详见 [第二轮核查结果](dataset_check/retry/第二轮核查结果.md)。正式实验输入和既有结果未被替换。
- **Ciao、Flixster 的论文指定版本仍缺失；程序严格核对规模，不会用不同版本冒充。** 找到的 Ciao 镜像有284,086条评分、105,114个不同物品，与论文280,391条评分、99,746个物品不符。
- Table 3 的 Fang 方法数值标记为“原文引用”，不是本项目训练的输出。原 TrustSVD 论文也直接复用其发表结果。
- 主实验采用独立编写的梯度下降，结果见 `results/gradient_descent/report/实验报告.md`。L-BFGS的部分补充运行保存在 `results/paper/`，两者不混合汇总。数据缺失、数值不一致及训练设置差异会如实报告。

## 环境与运行

Python 3.10+，CPU 即可。推荐新建环境并安装依赖：

```powershell
python -m pip install -r requirements-lock.txt
python -m pytest -q tests
$env:OPENBLAS_NUM_THREADS='1'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
python -u -m trustsvd_repro.experiment --datasets filmtrust epinions ciao flixster --maxiter 200 --jobs 2 --optimizer gd --run gradient_descent
python -m trustsvd_repro.report --run gradient_descent
python -m trustsvd_repro.audit --run gradient_descent
```

本机已安装且本次实际使用的解释器为 `D:\anaconda\python.exe`，不需要GPU、PyTorch或CUDA。
本次Python为3.12.7；`requirements-lock.txt`记录实际使用的库版本，`requirements.txt`提供兼容范围。

完整批次梯度下降使用Armijo回溯与标量步长选择，命令行选项为 `--optimizer gd`。也提供 `--optimizer lbfgs`，但必须使用另一运行目录；结果不混合汇总。梯度下降求解器经过实际目标函数下降检查。

快速验证单折（不能称为完整交叉验证结果）：

```powershell
python -m trustsvd_repro.experiment --datasets filmtrust --models TrustSVD --dims 5 --folds 0 --run smoke
```

程序可以续跑：同一运行目录中已经完成且预测文件存在的任务会跳过。**更改实现、参数、随机种子或数据后应使用新的 `--run` 名称，或者显式 `--force`，避免混合结果。** 默认不会在训练过程中访问网络。

## 从论文到实现

论文预测式为：

\[
\hat r_{uj}=\mu+b_u+b_j+q_j^T\left(p_u+|I_u|^{-1/2}\sum_{i\in I_u}y_i+|T_u|^{-1/2}\sum_{v\in T_u}w_v\right).
\]

- `p`：用户的显式偏好；`q`：物品向量。
- `y`：用户评价过哪些物品的隐式影响。
- `w`：用户信任哪些人的隐式影响；同时用于重建显式信任 `p_u^T w_v`。
- 训练目标为原文 Eq.(1) 的评分误差、信任重建误差和按逆平方根加权的正则项。
- 正则项在全局目标中按公式计算一次，没有悄悄改成“对每条评分再重复施加”。全局目标整体除以训练评分数不改变最小值。
- 原文最后一项 `w_v` 正则缺少显式求和符号，本实现按所有 trustee 求和，与 Eq.(2) 的梯度一致。
- 空历史/空信任邻域的隐式影响定义为0；所有训练隐式历史仅来自当前训练集。
- 稀疏矩阵乘法将隐式邻域求和与其梯度传播聚合，避免逐评分重复遍历整段历史。结果与公式相同。

`tests/test_math.py` 对全部可训练模型做中心差分梯度检查，并检查 TrustSVD 完整目标函数、冷用户的信任梯度、评分泄漏和指标计算。

## 实验设置与原文未说明的部分

原文规定5折、d=5/10以及各数据集正则系数，但没有给出原始折文件、随机种子、完整初始化及停止规则。因此不能保证逐项重现原始数字。

本项目明确采用以下设置，它们都保存在结果文件中：

1. 固定种子20261026。相同数据集所有模型共享外层5折。划分文件位于 `results/splits/`。
2. FilmTrust有3条额外重复用户-物品观察，其中两组评分不同。保留35,497条原始观察，但同一用户-物品对必须在同一折，防止泄漏；隐式历史按不同物品去重。
3. 每个外层训练集再划分10%内部验证集，只选择训练迭代数；然后在完整外层训练集上从相同初始化重新训练相应迭代数。外层测试不参与模型选择。
4. 主实验使用全批次解析梯度及独立编写的梯度下降，配合Armijo回溯和标量步长选择；另保留L-BFGS-B的部分补充运行。**原文未给出完整步长/停止设置，不能把本项目称为作者训练轨迹的逐步复刻。** 最多200次迭代，每5次检查验证集，连续5次检查无改善停止选择。
5. 输出裁剪到合法评分范围；未裁剪预测及指标也保留。UserAvg/ItemAvg遇到无训练评分的用户/物品时退回训练全局均值。
6. “Cold Start”分别以训练评分数<5、全部评分数<5计算。原文未清楚说明计数发生在划分前还是划分后，因此同时报告，不选择更好看的定义。
7. 所有观察到的信任边作为辅助信息保留，不把缺失边当成负样本。信任图不使用评分测试标签。
8. 对比模型按其原论文公式实现。SoReg使用PCC映射至[0,1]，无共同评分或方差为0时权重置0；这些边界行为是明确选择。
9. SVD++采用按观察次数累计的标准L2正则；TrustSVD采用本论文Eq.(1)的全局逆平方根正则。二者不同，不混用。
10. TrustMF先独立训练truster和trustee两个模型，再按原论文Eq.(7)组合向量（包括交叉项），并不是简单平均两个预测分数。
11. PMF采用其原论文实验部分Eq.(5)的sigmoid观测模型，评分映射到[0,1]。曾试验的原始评分线性PMF版本单独归档在 `results/superseded_pmf_raw/`，不进入最终对比。

这些选择可能导致与原表格不同的结果。报告不会把原文分数填入本次运行结果。

## 文件结构

```text
trustsvd_repro/
  data.py             数据核对、映射、去重历史与分组折
  objectives.py       从公式推导的模型目标函数及解析梯度
  experiment.py       内部验证、外部5折训练、保存预测和模型
  paper_reference.py  原文数值，只供比较，不参与训练
  report.py           图1、表2、图2、表3和统计检验
  audit.py            从逐条预测重算指标、检查折与模型重载
tests/test_math.py    数学正确性及泄漏检查
datasets/            核验过的数据；不一致镜像不会放入正式目录
dataset_check/        来源检查和不一致镜像，不能直接当正式实验数据
results/gradient_descent/        主实验JSON、测试预测、TrustSVD模型
results/gradient_descent/report/ 汇总CSV、PNG/SVG、中文报告
results/paper/                   L-BFGS部分补充结果，非完整主实验
```

## 增补缺失数据

准确版本确认后，将三个字段的评分文件保存为 `datasets/ciao/ratings.txt` 或 `datasets/flixster/ratings.txt`（用户ID、物品ID、评分）；信任文件保存为同目录 `trust.txt`（信任者ID、被信任者ID、值）。原始ID可以不连续。程序会检查用户数、物品数、评分数和信任边数是否与论文表1一致；规模一致仍不等于逐条文件一致，还需审查来源。

本次没有把原始Ciao镜像删行、删物品或自行抽样Flixster，以凑出论文规模。它们不能证明是同一个实验子集。

## 论文来源（无模型源码）

- TrustSVD：项目根目录中的2015年原文；[作者论文PDF](https://guoguibing.github.io/papers/guo2015trustsvd.pdf)。
- SoRec、RSTE、SoReg、SocialMF：项目根目录中的对应原文。
- TrustMF：[IJCAI 2013原文](https://www.ijcai.org/Proceedings/13/Papers/404.pdf)，另存 `dataset_check/trustmf_paper.pdf`。
- PMF：[NeurIPS原文](https://papers.nips.cc/paper/2007/file/d7322ed717dedf1eb4e6e52a37ea7bcd-Paper.pdf)，采用第2节Eq.(5)的实验设置。
- SVD++：[KDD 2008原文](https://people.engr.tamu.edu/huangrh/Spring16/papers_course/matrix_factorization.pdf)，预测式见Eq.(15)。
- FilmTrust：[作者发布页](https://guoguibing.github.io/librec/datasets.html)。
- Epinions：[Cornac数据加载来源说明](https://raw.githubusercontent.com/PreferredAI/cornac/master/cornac/datasets/epinions.py)。先前数据检索中读过该通用下载器；没有读取或复制任何推荐模型实现。
