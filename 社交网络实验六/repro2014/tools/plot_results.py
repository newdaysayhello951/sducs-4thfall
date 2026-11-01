"""把复现结果画成图：R&S 曲线 + 与论文报告值的对照。

用法::

    python -m tools.plot_results
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"


def main() -> int:
    curve = pd.read_csv(RES / "topic_detection_curve.csv")
    agg = curve.groupby("cut").agg(
        sensitivity=("sensitivity", "mean"),
        reliability=("reliability", "mean"),
        f1=("f1", "mean"),
        n_clusters=("n_clusters", "mean"),
    ).reset_index()

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))

    # --- 左：R&S 曲线
    ax = axes[0]
    ax.plot(agg["sensitivity"], agg["reliability"], "-o", ms=3.5, color="#c0392b", lw=1.6)
    best = agg.loc[agg["f1"].idxmax()]
    ax.scatter([best["sensitivity"]], [best["reliability"]], s=110, facecolors="none",
               edgecolors="#2c3e50", linewidths=1.8, zorder=5)
    ax.annotate(f"max F1 = {best['f1']:.3f}\n(paper 0.47)",
                xy=(best["sensitivity"], best["reliability"]),
                xytext=(0.55, 0.80), fontsize=9,
                arrowprops=dict(arrowstyle="->", color="#2c3e50", lw=1))
    ax.set_xlabel("Sensitivity (BCubed Recall)")
    ax.set_ylabel("Reliability (BCubed Precision)")
    ax.set_title("Topic detection: R&S curve (RepLab 2013 test, 61 entities)")
    ax.set_xlim(0, 1.02)
    ax.set_ylim(0, 1.02)
    ax.grid(alpha=0.3, linestyle=":")

    # --- 右：Table 2 对照
    ax = axes[1]
    t2 = pd.read_csv(RES / "table2_similarity_learning.csv")
    paper_ref = {
        "time": 0.56, "metadata": 0.58, "terms_jaccard": 0.59, "semantics": 0.59,
        "terms": 0.59, "terms+time": 0.61, "terms+semantics": 0.60,
        "terms+semantics+metadata": 0.62, "terms+semantics+time": 0.61, "all": 0.63,
    }
    labels, ours, refs = [], [], []
    for _, row in t2.iterrows():
        name = row["signal_combination"]
        if pd.isna(row["svm_accuracy"]):
            continue
        labels.append(name)
        ours.append(float(row["svm_accuracy"]))
        refs.append(paper_ref[name])

    y = range(len(labels))
    ax.barh([i + 0.2 for i in y], refs, height=0.38, label="paper", color="#95a5a6")
    ax.barh([i - 0.2 for i in y], ours, height=0.38, label="this reproduction", color="#c0392b")
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=8.5)
    ax.axvline(0.5, color="#2c3e50", ls="--", lw=1)
    ax.set_xlim(0.4, 0.7)
    ax.set_xlabel("SVM accuracy (10-fold CV)")
    ax.set_title("Table 2 comparison (only computable rows)")
    ax.legend(fontsize=8, loc="lower right")
    ax.grid(axis="x", alpha=0.3, linestyle=":")

    fig.tight_layout()
    out = RES / "figure_rs_curve.png"
    fig.savefig(out, dpi=160)
    print(f"图已保存：{out}")

    # 控制台摘要
    print("\n各切点宏平均：")
    print(agg.round(3).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
