"""三组实验对照：RepLab 无正文 / HumAID 无正文 / HumAID 有正文。

用法::

    python -m tools.compare_runs
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"

RUNS = [
    ("RepLab 2013\n(no tweet text, 5 feats)", RES / "summary.json", RES / "topic_detection_curve.csv", "#7f8c8d"),
    ("HumAID\n(no tweet text, 5 feats)", RES / "humaid_notext" / "summary.json",
     RES / "humaid_notext" / "topic_detection_curve.csv", "#2980b9"),
    ("HumAID\n(with tweet text, 10 feats)", RES / "humaid" / "summary.json",
     RES / "humaid" / "topic_detection_curve.csv", "#c0392b"),
]


def load(name: str, summary: Path, curve: Path, color: str) -> Dict:
    s = json.loads(summary.read_text(encoding="utf-8"))
    c = pd.read_csv(curve)
    agg = c.groupby("cut").agg(
        sensitivity=("sensitivity", "mean"), reliability=("reliability", "mean"),
        f1=("f1", "mean"),
    ).reset_index()
    return {"name": name, "color": color, "summary": s, "curve": agg}


def main() -> int:
    runs = [load(*r) for r in RUNS if r[1].exists()]

    # --- 控制台表格
    print(f"{'run':40s}{'#feat':>7s}{'AUC':>8s}{'MAR':>8s}{'maxF1':>8s}{'bestF1':>8s}")
    for r in runs:
        t = r["summary"]["topic_detection"]
        print(f"{r['name'].replace(chr(10),' '):40s}{len(r['summary']['features_used']):7d}"
              f"{t['auc']:8.3f}{t['mar']:8.3f}{t['max_f1']:8.3f}{t.get('best_f1', 0):8.3f}")

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 5))

    # --- 左：R&S 曲线
    ax = axes[0]
    for r in runs:
        c = r["curve"]
        ax.plot(c["sensitivity"], c["reliability"], "-o", ms=3, lw=1.7,
                color=r["color"], label=r["name"].replace("\n", " "))
        best = c.loc[c["f1"].idxmax()]
        ax.scatter([best["sensitivity"]], [best["reliability"]], s=90, facecolors="none",
                   edgecolors=r["color"], linewidths=1.6, zorder=5)
    ax.set_xlabel("Sensitivity (BCubed Recall)")
    ax.set_ylabel("Reliability (BCubed Precision)")
    ax.set_title("R&S curves: the effect of having tweet text")
    ax.set_xlim(0, 1.02)
    ax.set_ylim(0, 1.02)
    ax.grid(alpha=0.3, linestyle=":")
    ax.legend(fontsize=8, loc="lower left")

    # --- 右：关键指标柱状
    ax = axes[1]
    metrics = ["auc", "mar", "max_f1"]
    labels = ["AUC(R&S)", "MAR", "max F1"]
    x = range(len(metrics))
    w = 0.26
    for k, r in enumerate(runs):
        vals = [r["summary"]["topic_detection"][m] for m in metrics]
        ax.bar([i + (k - 1) * w for i in x], vals, width=w, color=r["color"],
               label=r["name"].replace("\n", " "))
        for i, v in zip(x, vals):
            ax.text(i + (k - 1) * w, v + 0.012, f"{v:.2f}", ha="center", fontsize=7.5)
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 0.75)
    ax.set_ylabel("score")
    ax.set_title("Topic detection summary")
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(axis="y", alpha=0.3, linestyle=":")

    fig.tight_layout()
    out = RES / "figure_text_ablation.png"
    fig.savefig(out, dpi=160)
    print(f"\n图已保存：{out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
