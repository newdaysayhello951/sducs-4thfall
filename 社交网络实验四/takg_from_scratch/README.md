# TAKG：根据论文从零复现

这是对 Wang et al. (ACL 2019) 论文 *Topic-Aware Neural Keyphrase Generation for Social Media Language* 的独立实现。

本目录中的模型、训练、解码和评估代码均根据论文正文及公式重新编写，没有复制、导入或修改作者 GitHub 中的实现代码。作者提供的公开数据只保留在 `data/` 中：

- `data/Weibo`：37,036 条训练、4,630 条验证、4,630 条测试数据；
- `data/StackExchange`：39,557 条训练、4,945 条验证、4,945 条测试数据；
- Twitter 数据受 TREC 许可限制，作者没有公开，因此这里不伪造或替换。

## 实现与论文的对应关系

`src/takg/model.py` 包含论文的两个主体模块：

1. 神经主题模型：BoW 编码器预测均值与方差，通过重参数化得到潜变量，再得到主题分布；训练目标由词袋重构损失和 KL 散度组成。
2. 关键短语生成模型：两层双向 GRU 编码正文，单向 GRU 解码关键短语。主题向量进入解码状态、注意力计算和复制开关。最终分布是词表生成分布与原文复制分布的加权和。

`src/takg/train.py` 实现论文描述的训练顺序：

1. 神经主题模型预训练 100 个 epoch；
2. 生成器预训练 1 个 epoch；
3. 按 `L = L_NTM + gamma * L_KG` 联合训练，并依据验证集生成损失保存最佳模型。

`src/takg/decode.py` 实现 beam search；`src/takg/metrics.py` 实现词干化后的 F1@K、MAP@5，以及 present/absent 关键短语分开评估。

## 环境

```powershell
D:/anaconda/envs/cpu_2.5.0/python.exe -m venv --system-site-packages .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
./run.ps1 doctor
```

## 快速验证

快速配置仅使用少量真实数据，用于检查流程和代码正确性，不是论文复现成绩：

```powershell
./run.ps1 all --config configs/weibo_smoke.json
```

## 正式训练

```powershell
./run.ps1 prepare --config configs/weibo_full.json
./run.ps1 train --config configs/weibo_full.json
./run.ps1 predict --config configs/weibo_full.json
./run.ps1 evaluate --config configs/weibo_full.json
```

意外中断后续训：

```powershell
./run.ps1 train --config configs/weibo_full.json --resume
```

也可以在后台启动完整微博实验，并随时查看状态：

```powershell
./start_full_weibo.ps1
./status.ps1
```

StackExchange 使用 `configs/stackexchange_full.json`。完整配置在无 GPU 的机器上会运行数小时；训练日志、最佳模型、主题词、预测和评估结果写入 `runs/<run_name>/`。

## 测试

```powershell
./.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -v
```

测试覆盖公开数据行数、主题概率、ELBO、文章内 OOV 复制、扩展词表概率归一化、生成损失向主题网络反向传播、present/absent 判断和已知答案的评价指标。

## 复现边界

论文没有公开所有实现细节，例如主题模型内部各层的精确非线性形式、所有初始化方式和早停细节。因此本工程对这些部分采用了明确且可审查的实现选择，并在配置文件中固定所有论文明确给出的主要超参数。所谓“复现”表示重建论文方法并在公开数据上重新实验，不保证逐位得到作者当年的数值。
