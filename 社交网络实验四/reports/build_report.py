import base64
import html
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = Path(__file__).resolve().parent
ASSET_DIR = REPORT_DIR / "assets"
RUN_DIR = ROOT / "runs" / "weibo_takg_seed9527"
ASSET_DIR.mkdir(parents=True, exist_ok=True)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_history():
    return [json.loads(line) for line in (RUN_DIR / "history.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def save_topic_curve(history):
    rows = [r for r in history if r["phase"] == "topic_pretraining"]
    fig, ax = plt.subplots(figsize=(8.4, 3.8), dpi=180)
    ax.plot([r["epoch"] for r in rows], [r["loss"] for r in rows], color="#1f5a94", linewidth=2.2)
    ax.scatter([1, 100], [rows[0]["loss"], rows[-1]["loss"]], color="#d98c2b", s=36, zorder=3)
    ax.annotate(f'{rows[0]["loss"]:.2f}', (1, rows[0]["loss"]), xytext=(8, 8), textcoords="offset points")
    ax.annotate(f'{rows[-1]["loss"]:.2f}', (100, rows[-1]["loss"]), xytext=(-40, 10), textcoords="offset points")
    ax.set_title("Neural Topic Model Pretraining")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Topic loss")
    ax.grid(True, alpha=0.22)
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "topic_loss.png", bbox_inches="tight")
    plt.close(fig)


def save_joint_curve(history):
    rows = [r for r in history if r["phase"] == "joint_training"]
    epochs = [r["epoch"] for r in rows]
    train = [r["generation_nll"] for r in rows]
    valid = [r["validation"]["generation_nll"] for r in rows]
    fig, ax = plt.subplots(figsize=(8.4, 4.2), dpi=180)
    ax.plot(epochs, train, marker="o", linewidth=2.1, label="Training NLL", color="#1f5a94")
    ax.plot(epochs, valid, marker="o", linewidth=2.1, label="Validation NLL", color="#d36b43")
    ax.axvline(3, color="#4a8a60", linestyle="--", linewidth=1.5, label="Best checkpoint: epoch 3")
    ax.set_title("Joint Training and Early Stopping")
    ax.set_xlabel("Joint epoch")
    ax.set_ylabel("Generation NLL")
    ax.set_xticks(epochs)
    ax.grid(True, alpha=0.22)
    ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "joint_nll.png", bbox_inches="tight")
    plt.close(fig)


def save_comparison_chart(metrics):
    ours = [metrics["F1@1"] * 100, metrics["F1@3"] * 100, metrics["MAP@5"] * 100]
    paper = [34.99, 24.42, 41.29]
    labels = ["F1@1", "F1@3", "MAP@5"]
    x = list(range(len(labels)))
    width = 0.34
    fig, ax = plt.subplots(figsize=(8.4, 4.3), dpi=180)
    p1 = ax.bar([i - width / 2 for i in x], paper, width, label="Paper TAKG (5-seed mean)", color="#1f5a94")
    p2 = ax.bar([i + width / 2 for i in x], ours, width, label="Reproduction (seed 9527)", color="#d98c2b")
    ax.bar_label(p1, fmt="%.2f", padding=3, fontsize=9)
    ax.bar_label(p2, fmt="%.2f", padding=3, fontsize=9)
    ax.set_ylabel("Score (%)")
    ax.set_title("Weibo Test-set Result Comparison")
    ax.set_xticks(x, labels)
    ax.set_ylim(0, 48)
    ax.grid(axis="y", alpha=0.2)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "paper_comparison.png", bbox_inches="tight")
    plt.close(fig)


def save_architecture():
    fig, ax = plt.subplots(figsize=(10.2, 4.0), dpi=180)
    ax.set_xlim(0, 10.2)
    ax.set_ylim(0, 4)
    ax.axis("off")

    def box(x, y, w, h, text, color):
        patch = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.08",
                               linewidth=1.5, edgecolor=color, facecolor=color + "18")
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=10.5, color="#17324d")

    def arrow(x1, y1, x2, y2, label=None):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=13,
                                     linewidth=1.4, color="#53677a"))
        if label:
            ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.14, label, ha="center", fontsize=8.5, color="#53677a")

    box(0.2, 2.55, 1.25, 0.72, "Token sequence", "#3973a5")
    box(0.2, 0.72, 1.25, 0.72, "BoW vector", "#7b5aa6")
    box(2.05, 2.35, 1.55, 1.12, "2-layer\nBiGRU encoder", "#3973a5")
    box(2.05, 0.48, 1.55, 1.12, "VAE neural\ntopic model", "#7b5aa6")
    box(4.35, 0.72, 1.35, 0.72, "Topic mixture θ", "#7b5aa6")
    box(4.35, 2.55, 1.35, 0.72, "Encoder memory", "#3973a5")
    box(6.45, 1.55, 1.65, 1.12, "Topic-aware GRU\n+ attention", "#2f876e")
    box(8.72, 1.55, 1.25, 1.12, "Generate / copy\nmixture", "#d17a34")
    arrow(1.45, 2.91, 2.05, 2.91)
    arrow(1.45, 1.08, 2.05, 1.08)
    arrow(3.60, 1.08, 4.35, 1.08)
    arrow(3.60, 2.91, 4.35, 2.91)
    arrow(5.70, 1.08, 6.70, 1.64, "state / attention / gate")
    arrow(5.70, 2.91, 6.70, 2.58)
    arrow(8.10, 2.11, 8.72, 2.11)
    ax.text(5.1, 3.72, "Independent TAKG reproduction based on the paper", ha="center",
            fontsize=13, fontweight="bold", color="#17324d")
    fig.tight_layout()
    fig.savefig(ASSET_DIR / "architecture.png", bbox_inches="tight", transparent=False)
    plt.close(fig)


def pct(value):
    return f"{value * 100:.2f}%"


def build_html(history, config, environment, manifest, metric_doc):
    all_m = metric_doc["metrics"]["all"]
    present = metric_doc["metrics"]["present"]
    absent = metric_doc["metrics"]["absent"]
    topic_rows = [r for r in history if r["phase"] == "topic_pretraining"]
    gen = next(r for r in history if r["phase"] == "generator_pretraining")
    joint = [r for r in history if r["phase"] == "joint_training"]
    topic_seconds = sum(r["seconds"] for r in topic_rows)
    joint_seconds = sum(r["seconds"] for r in joint)
    training_seconds = topic_seconds + gen["seconds"] + joint_seconds
    best = min(joint, key=lambda r: r["validation"]["generation_nll"])

    def hours(seconds):
        return f"{seconds / 3600:.2f} 小时"

    def img_uri(name):
        payload = base64.b64encode((ASSET_DIR / name).read_bytes()).decode("ascii")
        return f"data:image/png;base64,{payload}"

    # Word handles this HTML subset reliably and embeds the local images when saved as DOCX.
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>TAKG 论文复现实验报告</title>
<style>
@page {{ size: A4; margin: 2.3cm 2.35cm 2.2cm 2.35cm; }}
body {{ font-family: SimSun, "宋体", serif; font-size: 10.5pt; line-height: 1.58; color: #172536; }}
h1 {{ font-family: "Microsoft YaHei", SimHei, sans-serif; font-size: 17pt; color: #1f5a94; margin: 18pt 0 8pt; page-break-after: avoid; }}
h2 {{ font-family: "Microsoft YaHei", SimHei, sans-serif; font-size: 13.5pt; color: #234d72; margin: 14pt 0 6pt; page-break-after: avoid; }}
h3 {{ font-family: "Microsoft YaHei", SimHei, sans-serif; font-size: 11.5pt; color: #365f7d; margin: 10pt 0 4pt; page-break-after: avoid; }}
p {{ margin: 0 0 7pt; text-align: justify; }}
.cover {{ page-break-after: always; text-align: center; padding-top: 82pt; }}
.cover .kicker {{ color: #6c7b88; letter-spacing: 2pt; font-family: "Microsoft YaHei"; font-size: 11pt; }}
.cover .title {{ color: #173f63; font-family: "Microsoft YaHei"; font-size: 27pt; font-weight: bold; line-height: 1.32; margin: 34pt 0 12pt; }}
.cover .subtitle {{ color: #4c6478; font-family: "Microsoft YaHei"; font-size: 14pt; margin-bottom: 48pt; }}
.cover table {{ width: 82%; margin: 0 auto; border-collapse: collapse; }}
.cover td {{ border-bottom: 1px solid #d5dde4; padding: 8pt 7pt; text-align: left; }}
.cover td:first-child {{ width: 25%; color: #627386; font-weight: bold; }}
.cover .date {{ margin-top: 55pt; color: #647483; }}
.lead {{ border-left: 5px solid #d98c2b; background: #f6f8fa; padding: 11pt 14pt; margin: 10pt 0 14pt; }}
.equation {{ text-align: center; font-family: Cambria, serif; font-size: 11pt; margin: 9pt 0; color: #173f63; }}
table.data {{ width: 100%; border-collapse: collapse; margin: 8pt 0 12pt; page-break-inside: avoid; }}
table.data th {{ background: #e9f0f6; color: #173f63; font-family: "Microsoft YaHei"; font-size: 9.7pt; padding: 7pt 6pt; border: 1px solid #9fb3c5; text-align: center; }}
table.data td {{ padding: 6pt 6pt; border: 1px solid #b8c5d0; vertical-align: middle; font-size: 9.5pt; }}
table.data td.num {{ text-align: center; font-family: Calibri, sans-serif; }}
.caption {{ text-align: center; color: #526679; font-size: 9pt; margin: 3pt 0 12pt; }}
.figure {{ text-align: center; margin: 10pt 0 4pt; page-break-inside: avoid; }}
.figure img {{ max-width: 96%; }}
ul, ol {{ margin: 3pt 0 8pt 20pt; }}
li {{ margin-bottom: 4pt; }}
.code {{ font-family: Consolas, monospace; font-size: 8.8pt; background: #f4f6f8; border: 1px solid #d7dee5; padding: 8pt 10pt; margin: 6pt 0 10pt; white-space: pre-wrap; page-break-inside: avoid; }}
.page-break {{ page-break-before: always; }}
.small {{ font-size: 9pt; color: #576978; }}
.positive {{ color: #236b43; font-weight: bold; }}
.negative {{ color: #9b3b2b; font-weight: bold; }}
.nowrap {{ white-space: nowrap; }}
.keep {{ page-break-inside: avoid; }}
</style>
</head>
<body>
<div class="cover">
  <div class="kicker">社交网络实验 · 论文复现</div>
  <div class="title">主题感知社交媒体<br>关键短语生成实验报告</div>
  <div class="subtitle">Topic-Aware Neural Keyphrase Generation for Social Media Language</div>
  <table>
    <tr><td>复现论文</td><td>Wang et al., ACL 2019</td></tr>
    <tr><td>实验数据</td><td>Weibo 公共数据集（46,296 条帖子）</td></tr>
    <tr><td>实现方式</td><td>依据论文正文与公式独立编写，仅使用论文提供的数据集</td></tr>
    <tr><td>实验运行</td><td>weibo_takg_seed9527，PyTorch 2.5.0，CPU</td></tr>
    <tr><td>报告内容</td><td>方法复现、代码实现、训练过程、结果对比与误差分析</td></tr>
  </table>
  <div class="date">报告日期：2026 年 9 月 30 日</div>
</div>

<h1>摘要</h1>
<p>本实验依据论文《Topic-Aware Neural Keyphrase Generation for Social Media Language》从零实现主题感知神经关键短语生成模型（TAKG），未复制或导入作者仓库代码，只保留论文公开的 Weibo 与 StackExchange 数据。本次正式实验选择 Weibo 数据集，完成数据校验、神经主题模型预训练、生成器预训练、联合训练、束搜索解码以及 F1@K、MAP@5、present/absent 分类评估。复现模型在 Weibo 测试集上取得 F1@1={pct(all_m['F1@1'])}、F1@3={pct(all_m['F1@3'])}、MAP@5={pct(all_m['MAP@5'])}。与论文报告的 34.99%、24.42% 和 41.29% 相比，分别低 2.21、0.96 和 1.98 个百分点，但三项指标均超过论文中的 Seq2Seq-Copy 强基线。本实验说明，独立实现已正确重建序列生成、复制机制和主题感知联合学习的主要流程，但尚未完全复现论文中完整模型的增益。</p>
<p><b>关键词：</b>关键短语生成；神经主题模型；序列到序列；复制机制；Weibo；论文复现</p>

<div class="lead"><b>核心结论：</b>本次复现属于“方法与趋势复现成功、数值接近但未完全一致”。最佳模型出现在联合训练第 3 轮，之后验证损失连续恶化，程序在第 6 轮按 patience=3 自动早停。最终 F1@1 达到论文结果的 93.7%，F1@3 达到 96.1%，MAP@5 达到 95.2%。</div>

<h1>1　实验背景与目标</h1>
<p>社交媒体文本短、口语化且噪声较多，用户标注的关键短语经常不直接出现在原文中。传统关键词抽取方法只能从原文选择词语，因此无法处理 absent keyphrase。论文采用生成式 seq2seq 框架，并引入语料级潜在主题，以缓解短文本中的数据稀疏问题。主题信息同时进入解码状态、注意力和生成/复制开关，使模型既能复制原文词语，也能生成原文中没有出现的关键词。</p>
<p>本实验的目标包括：第一，严格使用论文提供的数据，在不参考作者 GitHub 代码的条件下独立实现模型；第二，验证从数据处理到评估的完整流水线；第三，在 Weibo 测试集上与论文表 3 的结果进行同口径比较；第四，结合训练曲线和实现选择分析数值差异。</p>

<h1>2　论文方法与模型原理</h1>
<h2>2.1　总体结构</h2>
<div class="figure"><img src="{img_uri('architecture.png')}" width="600"></div>
<div class="caption">图 1　根据论文重新实现的 TAKG 数据流</div>
<p>模型包含两个主体模块：神经主题模型（Neural Topic Model, NTM）读取无词序的词袋向量，学习帖子所属的主题混合；关键短语生成器读取保留词序的 token 序列，使用双向 GRU 编码帖子，再使用主题感知 GRU 解码关键短语。两个模块在联合训练阶段由同一个总损失连接。</p>

<h2>2.2　神经主题模型</h2>
<p>词袋编码器用两层 ReLU 感知机处理归一化 BoW，分别预测高斯潜变量的均值 μ 与对数方差 log σ²。训练时使用重参数化采样，推理时使用均值以保证同一检查点的预测稳定。潜变量经过 softmax 映射得到 50 维主题混合 θ，并由主题—词分布重构原始词袋。</p>
<div class="equation">z = μ + ε ⊙ exp(0.5 log σ²)，　θ = softmax(f<sub>θ</sub>(z))</div>
<div class="equation">L<sub>NTM</sub> = −Σ<sub>w</sub> x<sub>w</sub> log p(w|θ) + KL(q(z|x) || N(0,I))</div>
<p>代码中的 <code>NeuralTopicModel.forward()</code> 实现编码、重参数化、主题混合和词袋重构，<code>topic_model_loss()</code> 实现重构负对数似然与 KL 散度之和。</p>

<h2>2.3　主题感知生成与复制机制</h2>
<p>序列编码器为两层双向 GRU，每个方向隐藏维度为 150，拼接后得到 300 维编码表示。解码器为单层 300 维 GRU。主题向量 θ 在三个位置发挥作用：</p>
<ol>
  <li>与当前输入词向量拼接后更新解码状态，对应论文公式 5；</li>
  <li>加入源词注意力能量函数，对应论文公式 6—7；</li>
  <li>加入生成/复制概率 λ 的计算，对应论文公式 10。</li>
</ol>
<div class="equation">p(y<sub>j</sub>) = λ<sub>j</sub> · p<sub>gen</sub> + (1−λ<sub>j</sub>) · p<sub>copy</sub></div>
<p>复制分布由注意力权重构成。对于词表外但在当前帖子中出现的词，代码为每条帖子建立局部扩展词表，再通过 <code>scatter_add</code> 将注意力概率累加到相应扩展索引。这样既能生成固定词表中的词，也能复制当前原文中的 OOV 词，同时避免不同帖子之间的 OOV 索引泄漏。</p>

<h2>2.4　联合训练目标</h2>
<p>关键短语生成损失采用 teacher forcing 下的 token 级负对数似然，联合目标与论文一致：</p>
<div class="equation">L = L<sub>NTM</sub> + γL<sub>KG</sub>，　γ = 1.0</div>
<p>训练顺序为 NTM 预训练 100 轮、冻结 NTM 后预训练生成器 1 轮、随后联合训练。联合阶段中生成损失可以通过主题向量反向传播到主题网络。</p>

<h1 class="page-break">3　独立复现代码设计</h1>
<h2>3.1　代码组织</h2>
<table class="data">
<tr><th style="width:25%">文件</th><th style="width:31%">职责</th><th>与论文的对应关系</th></tr>
<tr><td><code>src/takg/data.py</code></td><td>读取数据、构造词表与 BoW、扩展词表、批处理</td><td>同时生成序列表示 x 与词袋表示 x<sub>bow</sub></td></tr>
<tr><td><code>src/takg/model.py</code></td><td>NTM、双向 GRU、主题感知解码器、复制机制</td><td>论文公式 1、5—12</td></tr>
<tr><td><code>src/takg/train.py</code></td><td>三阶段训练、验证、早停、断点续训</td><td>论文公式 13—14及参数设置</td></tr>
<tr><td><code>src/takg/decode.py</code></td><td>束搜索、扩展词表还原、预测输出</td><td>论文推理阶段的 beam search</td></tr>
<tr><td><code>src/takg/metrics.py</code></td><td>F1@K、MAP@5、present/absent 评估</td><td>论文第 5.1 节评价方式</td></tr>
<tr><td><code>src/takg/utils.py</code></td><td>随机种子、设备选择、原子保存</td><td>保证运行可恢复和结果可追踪</td></tr>
</table>
<div class="caption">表 1　论文模块与独立实现文件的映射</div>

<h2>3.2　数据处理</h2>
<p>公开数据中的正文与标签按行对应，多个关键短语以分隔符存储。训练时把一条正文的多个关键短语展开为多个“正文—单个短语”样本，因此 37,036 条训练帖子形成 39,188 个训练对。正文最大长度设为 100，目标最大长度设为 10。词序序列供 GRU 使用，词袋计数供 NTM 使用。</p>
<p>词表由训练集构建，生成词表大小为 50,000，BoW 词表大小为 10,000。每条帖子单独维护 OOV 列表；若目标 OOV 在源帖子中出现，则其监督标签指向扩展词表索引，否则使用 UNK。</p>

<h2>3.3　训练、保存与恢复</h2>
<p><code>train.py</code> 为 topic、generator 和 joint 三个阶段分别建立 Adam 优化器。每轮结束后将模型参数、三个优化器状态、训练计划、配置与 Python/NumPy/PyTorch 随机状态保存至 <code>last.pt</code>。文件采用临时文件替换的原子写入方式，因此实验中断后可从最近完整轮次继续。联合训练依据验证集 generation NLL 保存 <code>best.pt</code>。</p>

<h2>3.4　推理与评价</h2>
<p>推理采用 beam size 50、最大生成长度 6，候选按累计对数概率排序，不额外采用长度惩罚。重复短语去重后保留前 50 个候选。评价时计算宏平均 P@K、R@K、F1@K 与 MAP@5，并依据关键短语是否在正文中连续出现，拆分为 present 和 absent 两组。</p>

<h1>4　实验设置</h1>
<h2>4.1　数据集</h2>
<table class="data">
<tr><th>数据集</th><th>训练</th><th>验证</th><th>测试</th><th>总数</th><th>训练对</th></tr>
<tr><td class="num">Weibo</td><td class="num">{manifest['records']['train']:,}</td><td class="num">{manifest['records']['valid']:,}</td><td class="num">{manifest['records']['test']:,}</td><td class="num">{sum(manifest['records'].values()):,}</td><td class="num">{manifest['training_pairs']:,}</td></tr>
</table>
<div class="caption">表 2　正式实验使用的数据规模</div>
<p>总计 46,296 条帖子，与论文表 2 的 Weibo 帖子总量完全一致。项目缓存清单同时保存六个原始数据文件的 SHA-256，用于确认训练前后数据未被修改。</p>

<h2>4.2　运行环境与超参数</h2>
<table class="data">
<tr><th style="width:23%">项目</th><th style="width:27%">设置</th><th style="width:23%">项目</th><th>设置</th></tr>
<tr><td>计算设备</td><td class="num">{html.escape(environment['device'])}</td><td>PyTorch</td><td class="num">{html.escape(environment['torch'])}</td></tr>
<tr><td>随机种子</td><td class="num">{config['seed']}</td><td>batch size</td><td class="num">{config['batch_size']}</td></tr>
<tr><td>词向量维度</td><td class="num">{config['embedding_size']}</td><td>主题数 K</td><td class="num">{config['topic_count']}</td></tr>
<tr><td>编码器</td><td class="num">2 层 BiGRU</td><td>解码器</td><td class="num">1 层 GRU，300维</td></tr>
<tr><td>学习率</td><td class="num">{config['learning_rate']}</td><td>梯度裁剪</td><td class="num">{config['gradient_clip']}</td></tr>
<tr><td>γ</td><td class="num">{config['gamma']}</td><td>dropout</td><td class="num">{config['dropout']}</td></tr>
<tr><td>最大联合轮次</td><td class="num">{config['joint_epochs']}</td><td>早停 patience</td><td class="num">{config['patience']}</td></tr>
<tr><td>beam size</td><td class="num">{config['beam_size']}</td><td>最大解码长度</td><td class="num">{config['decode_max_length']}</td></tr>
</table>
<div class="caption">表 3　正式复现实验环境与核心配置</div>

<h2>4.3　正确性测试</h2>
<p>正式训练前运行 6 项单元测试并全部通过，覆盖：公开数据行数与平行性、主题概率分布与有限 ELBO、OOV 扩展索引的帖子局部性、最终扩展分布归一化、生成损失向主题网络的梯度传播、连续 present 短语判断和已知答案评价指标。测试命令如下：</p>
<div class="code">.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v</div>

<h1 class="page-break">5　训练过程与模型选择</h1>
<h2>5.1　主题模型预训练</h2>
<div class="figure"><img src="{img_uri('topic_loss.png')}" width="590"></div>
<div class="caption">图 2　NTM 预训练 100 轮的损失变化</div>
<p>主题损失由第 1 轮的 {topic_rows[0]['loss']:.3f} 降至第 100 轮的 {topic_rows[-1]['loss']:.3f}，下降 {topic_rows[0]['loss']-topic_rows[-1]['loss']:.3f}。整体曲线平滑下降，后期趋于稳定，说明词袋重构与潜变量正则化优化正常。主题预训练记录耗时合计约 {hours(topic_seconds)}。</p>

<h2>5.2　生成器预训练</h2>
<p>生成器预训练 1 轮，训练 generation NLL 为 {gen['generation_nll']:.4f}，验证 NLL 为 {gen['validation']['generation_nll']:.4f}，验证困惑度为 {gen['validation']['perplexity']:.4f}，用时 {gen['seconds']/60:.2f} 分钟。该阶段冻结主题模型，因此日志中的 topic_loss 为 0。</p>

<h2>5.3　联合训练与早停</h2>
<div class="figure"><img src="{img_uri('joint_nll.png')}" width="590"></div>
<div class="caption">图 3　联合训练的训练/验证 generation NLL</div>
<table class="data">
<tr><th>轮次</th><th>训练 NLL</th><th>验证 NLL</th><th>验证困惑度</th><th>是否刷新最佳</th><th>耗时/分钟</th></tr>
{''.join(f'<tr><td class="num">{r["epoch"]}</td><td class="num">{r["generation_nll"]:.4f}</td><td class="num">{r["validation"]["generation_nll"]:.4f}</td><td class="num">{r["validation"]["perplexity"]:.4f}</td><td class="num">{"是" if r["best"] else "否"}</td><td class="num">{r["seconds"]/60:.2f}</td></tr>' for r in joint)}
</table>
<div class="caption">表 4　联合训练历史</div>
<p>第 {best['epoch']} 轮取得最佳验证 NLL={best['validation']['generation_nll']:.4f}。第 4—6 轮训练 NLL 继续下降，但验证 NLL 从 1.3307 上升至 1.4558，表明模型开始过拟合。连续 3 轮未改善后触发早停，最终预测加载第 3 轮的 <code>best.pt</code>，而不是第 6 轮的最后模型。三个训练阶段的日志累计计算时间约 {hours(training_seconds)}。</p>

<h1>6　测试结果与论文对比</h1>
<h2>6.1　论文表 3 主指标</h2>
<div class="figure"><img src="{img_uri('paper_comparison.png')}" width="590"></div>
<div class="caption">图 4　Weibo 测试集：论文 TAKG 与本次复现</div>
<table class="data">
<tr><th>指标</th><th>论文 TAKG<br>5种子均值</th><th>本次复现<br>seed 9527</th><th>绝对差值</th><th>达到论文比例</th></tr>
<tr><td class="num">F1@1</td><td class="num">34.99 ± 0.30%</td><td class="num"><b>{pct(all_m['F1@1'])}</b></td><td class="num negative">−2.21</td><td class="num">93.7%</td></tr>
<tr><td class="num">F1@3</td><td class="num">24.42 ± 0.20%</td><td class="num"><b>{pct(all_m['F1@3'])}</b></td><td class="num negative">−0.96</td><td class="num">96.1%</td></tr>
<tr><td class="num">MAP@5</td><td class="num">41.29 ± 0.40%</td><td class="num"><b>{pct(all_m['MAP@5'])}</b></td><td class="num negative">−1.98</td><td class="num">95.2%</td></tr>
</table>
<div class="caption">表 5　论文完整模型与本次独立复现的主指标对比（百分点）</div>
<p>三项指标均低于论文完整 TAKG，但绝对差距控制在 0.96—2.21 个百分点。F1@3 最接近论文结果。论文结果是 5 个随机初始化种子的均值和标准差，而本次仅训练一个种子，因此两者并非完全对等的统计比较。</p>

<h2>6.2　与论文强基线及消融模型的关系</h2>
<table class="data">
<tr><th>模型</th><th>F1@1</th><th>F1@3</th><th>MAP@5</th></tr>
<tr><td>论文 Seq2Seq-Copy</td><td class="num">32.01%</td><td class="num">22.69%</td><td class="num">38.01%</td></tr>
<tr><td>本次复现</td><td class="num positive">32.78%</td><td class="num positive">23.46%</td><td class="num positive">39.31%</td></tr>
<tr><td>论文完整 TAKG</td><td class="num">34.99%</td><td class="num">24.42%</td><td class="num">41.29%</td></tr>
</table>
<div class="caption">表 6　本次复现与论文基线的对比</div>
<p>本次复现分别超过 Seq2Seq-Copy 0.77、0.77 和 1.30 个百分点，说明复制机制以上的主题感知设计产生了正向作用。不过，本次 F1@1=32.78% 与论文消融实验中的 “Our model (separate train)” 32.75% 几乎相同，低于完整模型 34.99%。这表明基础生成与复制部分已较好复现，但论文中端到端联合主题学习带来的全部收益尚未恢复。</p>

<h2>6.3　Present 与 Absent 结果</h2>
<table class="data">
<tr><th>关键词类别</th><th>有效样本数</th><th>F1@1</th><th>F1@3</th><th>F1@5</th><th>MAP@5</th></tr>
<tr><td>全部</td><td class="num">{all_m['count']}</td><td class="num">{pct(all_m['F1@1'])}</td><td class="num">{pct(all_m['F1@3'])}</td><td class="num">{pct(all_m['F1@5'])}</td><td class="num">{pct(all_m['MAP@5'])}</td></tr>
<tr><td>Present</td><td class="num">{present['count']}</td><td class="num">{pct(present['F1@1'])}</td><td class="num">{pct(present['F1@3'])}</td><td class="num">{pct(present['F1@5'])}</td><td class="num">{pct(present['MAP@5'])}</td></tr>
<tr><td>Absent</td><td class="num">{absent['count']}</td><td class="num">{pct(absent['F1@1'])}</td><td class="num">{pct(absent['F1@3'])}</td><td class="num">{pct(absent['F1@5'])}</td><td class="num">{pct(absent['MAP@5'])}</td></tr>
</table>
<div class="caption">表 7　本次复现的分类评价结果</div>
<p>Present F1@1 达到 {pct(present['F1@1'])}，说明编码器、注意力和复制机制能够准确提取原文中的关键词。Absent F1@1 为 {pct(absent['F1@1'])}、R@5 为 {pct(absent['R@5'])}，证明模型并非只会抽取，还能生成原文未出现的短语。论文图 2 只能近似读数：Weibo 的 Present F1@1 约 84%，Absent R@5 约 39%；本次分别为 {pct(present['F1@1'])} 和 {pct(absent['R@5'])}，同样低约 1—2 个百分点。</p>

<h1>7　结果不一致的原因分析</h1>
<h2>7.1　随机种子数量不同</h2>
<p>论文表 3 报告 5 个随机初始化种子的均值与标准差，本次受 CPU 时间限制只运行 seed=9527。神经网络的初始权重、样本打乱顺序和 VAE 采样都会引入随机性，因此单次结果可能偏离论文均值。要进行严格复现，应至少运行 5 个种子，并报告均值、标准差和显著性检验。</p>

<h2>7.2　论文没有给出全部工程细节</h2>
<p>论文明确给出了主题数、GRU 层数和维度、词向量维度、学习率、梯度裁剪、预训练轮次与 γ，但没有完整说明 NTM 每层的精确结构、参数初始化、归一化方式、方差参数化、dropout 位置和优化器状态切换方式。本实现采用两层 ReLU 的 BoW 编码器、多项式词袋重构、log-variance 截断以及推理时使用潜变量均值。这些选择符合论文描述，但不保证与作者实现逐项相同。</p>

<h2>7.3　联合优化与早停策略差异</h2>
<p>论文描述为依次更新各模块及其组合，但没有给出每种更新的精确频率与 patience。本实现先预训练两个模块，再使用独立 joint Adam 优化器一次性更新全部参数，并设置 patience=3。训练曲线显示第 3 轮后训练 NLL继续下降而验证 NLL上升，早停选择是合理的；但如果论文采用不同的交替更新、学习率衰减或更长 patience，可能获得更好的联合主题收益。</p>

<h2>7.4　束搜索排序和候选后处理差异</h2>
<p>论文只说明采用 beam search，没有完整描述长度归一化、重复 token 限制、UNK 过滤、短语去重、候选截断与无效短语处理。本实现按累计对数概率排序且不加入长度惩罚，这可能偏好较短的候选。F1@1 与 MAP@5 对候选顺序敏感，因此解码细节足以造成 1—2 个百分点的差距。</p>

<h2>7.5　评价实现边界</h2>
<p>本实现对 Weibo 使用分词 token 的小写精确匹配，present 必须是正文中的连续 token 片段；英文数据才使用 Porter stemming。论文只概括说明采用宏平均 F1 和词干化匹配，没有给出中文符号清理、重复标签和空预测等边界情况。宏平均 P/R 后再计算 F1、逐样本先计算 F1 再平均等实现顺序也可能造成细微差异。</p>

<h2>7.6　数据展开与目标组织方式</h2>
<p>本实现把一条帖子对应的多个关键短语展开为多个一对一训练样本。论文给出了数据统计和 seq2seq 目标，但没有完整说明多标签帖子在训练批次中的组织方式。若作者把多个关键短语拼接为一个序列，或采用不同的采样/加权方法，目标分布和每个 epoch 的有效样本权重都会发生变化。</p>

<div class="keep"><h2>7.7　CPU、软件版本与数值路径</h2>
<p>本次使用 CPU 和 PyTorch 2.5.0；论文发表于 2019 年，使用的 PyTorch、底层 BLAS、随机数实现和数值稳定策略均可能不同。硬件不会系统性决定模型优劣，但浮点累积顺序会使优化轨迹逐渐分叉。该因素通常小于架构和解码差异，但在单种子比较中不能忽略。</p></div>

<div class="lead"><b>综合判断：</b>最主要的原因是“单种子比较 + 论文未公开的训练/解码细节 + 联合训练更新方式”。从指标位置看，本次结果已经超过 Seq2Seq-Copy，却接近论文 separate-train 消融模型，说明差距主要集中在主题模块与生成器的联合增益，而不是基础 seq2seq 或复制机制失效。</div>

<h1>8　结论</h1>
<p>本实验仅使用论文公开数据，完成了 TAKG 的独立代码复现。实现覆盖 VAE 神经主题模型、两层双向 GRU 编码器、主题感知解码状态、主题感知注意力、主题感知复制开关、扩展词表、三阶段训练、断点续训、beam search 和完整评价。训练过程稳定，6 项正确性测试全部通过，最佳检查点能够在测试集上生成 present 与 absent 关键短语。</p>
<p>测试结果与论文总体趋势一致：主题感知模型超过复制式 seq2seq 基线，对 present 关键词表现尤其突出，并具备生成 absent 关键词的能力。主指标距离论文完整模型 0.96—2.21 个百分点，属于接近复现。若继续提高复现精度，建议依次进行：5 个随机种子重复实验；复核宏平均计算与中文预处理；尝试论文描述的模块交替更新；对 beam search 长度归一化和候选过滤进行消融；比较不同 patience 与学习率衰减设置。</p>

<h1 class="page-break">9　复现实验操作与产物</h1>
<h2>9.1　执行命令</h2>
<div class="code"># 数据准备<br>.&#92;run.ps1 prepare --config configs/weibo_full.json<br><br># 完整训练<br>.&#92;run.ps1 train --config configs/weibo_full.json<br><br># 中断后恢复<br>.&#92;run.ps1 train --config configs/weibo_full.json --resume<br><br># 预测与评价<br>.&#92;run.ps1 predict --config configs/weibo_full.json<br>.&#92;run.ps1 evaluate --config configs/weibo_full.json</div>

<h2>9.2　关键产物</h2>
<ul>
  <li><code>runs/weibo_takg_seed9527/best.pt</code>：联合训练第 3 轮的最佳模型；</li>
  <li><code>history.jsonl</code>：100 轮主题预训练、1 轮生成器预训练和 6 轮联合训练记录；</li>
  <li><code>predictions.txt</code>：4,630 条测试帖子的候选关键词；</li>
  <li><code>metrics.json</code>：全部、present 与 absent 指标；</li>
  <li><code>topics.json</code>：50 个主题各自概率最高的词；</li>
  <li><code>examples.json</code>：前 30 个测试样例及注意力信息。</li>
</ul>

<h1>参考文献</h1>
<p>[1] Wang, Y., Li, J., Chan, H. P., King, I., Lyu, M. R., & Shi, S. Topic-Aware Neural Keyphrase Generation for Social Media Language. Proceedings of ACL 2019.</p>
<p>[2] Meng, R., Zhao, S., Han, S., He, D., Brusilovsky, P., & Chi, Y. Deep Keyphrase Generation. Proceedings of ACL 2017.</p>
<p>[3] Miao, Y., Yu, L., & Blunsom, P. Neural Variational Inference for Text Processing. Proceedings of ICML 2016.</p>
<p class="small">说明：论文对比数值取自原论文表 3 与图 2；本次复现数值取自 <code>runs/weibo_takg_seed9527/metrics.json</code> 和 <code>history.jsonl</code>。</p>
</body>
</html>'''


def main():
    history = read_history()
    config = read_json(ROOT / "configs" / "weibo_full.json")
    environment = read_json(RUN_DIR / "environment.json")
    manifest = read_json(ROOT / "cache" / "Weibo" / "full.json")
    metrics = read_json(RUN_DIR / "metrics.json")
    save_topic_curve(history)
    save_joint_curve(history)
    save_comparison_chart(metrics["metrics"]["all"])
    save_architecture()
    report_html = build_html(history, config, environment, manifest, metrics)
    (REPORT_DIR / "TAKG_reproduction_report.html").write_text(report_html, encoding="utf-8")
    print(json.dumps({
        "html": str(REPORT_DIR / "TAKG_reproduction_report.html"),
        "assets": [str(p) for p in sorted(ASSET_DIR.glob("*.png"))],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
