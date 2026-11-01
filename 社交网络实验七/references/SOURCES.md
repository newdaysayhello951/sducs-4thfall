# 实现依据

未使用现成模型源码。下面列的是论文，代码按公式独立推导。

|模型|论文位置|采用内容|
|---|---|---|
|TrustSVD|项目根目录2015TrustSVD PDF，pp.125–127|预测式、Eq.(1)目标、Eq.(2)梯度、实验参数与5折|
|PMF|2007_pmf.pdf，Section 2 Eq.(5)|实际实验使用sigmoid，评分映射(r-min)/(max-min)|
|SVD++|2008_svdpp.pdf，Eq.(15)及相应梯度下降描述|偏置、显式因子与归一化物品隐式历史|
|SoRec|项目根目录2008SoRec PDF|共享用户空间分解评分和信任，度数置信度Eq.(4)|
|RSTE|项目根目录2009Social Trust Ensemble PDF|个人因子与归一化可信邻居因子的混合|
|SocialMF|项目根目录2010Trust Propagation PDF|用户向量与可信邻居均值之间的平方距离正则|
|SoReg|项目根目录2011Social Regularization PDF|逐朋友约束Eq.(11)，PCC映射至[0,1]|
|TrustMF|2013_trustmf.pdf|Truster Eq.(5)、Trustee Eq.(6)、组合Eq.(7)|

UserAvg和ItemAvg直接按训练记录取均值；没有读取第三方实现。

## 独立实现与原文未指定项

原论文没有提供原始随机折、完整初始化、步长和停止规则。本次明确选定这些设置并保存；数学式一致不保证训练轨迹及最后数值逐项相同。

TrustSVD印刷版Eq.(1)最后的w_v惩罚未写求和符号，按所有v求和，得到与Eq.(2)一致的梯度。没有依据公开源码修正这个解释。

SVD++的L2按每条评分更新的曝光次数累积；主论文TrustSVD按其打印的全局加权目标施加一次正则。这是本项目明确区分的两种目标，未按结果优劣切换。

## 网址

- https://guoguibing.github.io/papers/guo2015trustsvd.pdf
- https://papers.nips.cc/paper/2007/file/d7322ed717dedf1eb4e6e52a37ea7bcd-Paper.pdf
- https://people.engr.tamu.edu/huangrh/Spring16/papers_course/matrix_factorization.pdf
- https://www.ijcai.org/Proceedings/13/Papers/404.pdf
