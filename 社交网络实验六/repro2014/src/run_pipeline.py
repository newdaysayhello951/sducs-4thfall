"""论文《Learning Similarity Functions for Topic Detection in Online
Reputation Monitoring》(SIGIR'14) 的端到端复现。

流程：
    1. 载入 RepLab 2013 训练/测试集（仅相关推文、剔除近重复）
    2. 采样 80,000 个平衡推文对，做特征消融 + 10 折交叉验证（对应论文 Table 2）
    3. 用全部可用特征训练最终 SVM
    4. 对测试集每个实体，计算两两相似度 -> 单链接 HAC -> 阈值扫描
    5. 用官方 R/S/F 指标评测，输出 AUC / MAR / maxF（对应论文 Table 3、Table 4）

用法::

    python -m src.run_pipeline                       # 仅用可得的元数据+时间特征
    python -m src.run_pipeline --text-file texts.jsonl
    python -m src.run_pipeline --pairs 80000 --folds 10
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np
import pandas as pd

from . import clustering, metrics, model, sampling, text_source
from .features import (
    ALL_FEATURES,
    TEXT_DEPENDENT,
    CollectionStats,
    EntityFeatureBuilder,
    compute_collection_stats,
)
from .replab_io import build_entities, dataset_root

OUT = Path(__file__).resolve().parents[1] / "results"
OUT.mkdir(parents=True, exist_ok=True)


def set_output_dir(path: str | None) -> Path:
    global OUT
    if path:
        OUT = Path(path)
        if not OUT.is_absolute():
            OUT = Path(__file__).resolve().parents[1] / OUT
        OUT.mkdir(parents=True, exist_ok=True)
    return OUT


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------- 阶段 1


def load_data(text_file: str | None, data_root: str | None = None):
    texts = text_source.load_texts(text_file) if text_file else {}
    train = build_entities("training", texts=texts, root=data_root)
    test = build_entities("test", texts=texts, root=data_root)

    all_ids = [t for e in train.values() for t in e.tweet_ids] + [
        t for e in test.values() for t in e.tweet_ids
    ]
    cov = text_source.coverage(all_ids, texts)

    log(f"训练集：{len(train)} 个实体 / {sum(len(e) for e in train.values())} 条相关推文 / "
        f"{sum(e.n_topics for e in train.values())} 个话题")
    log(f"测试集：{len(test)} 个实体 / {sum(len(e) for e in test.values())} 条相关推文 / "
        f"{sum(e.n_topics for e in test.values())} 个话题")
    log(f"正文覆盖率：{cov:.1%}")
    return train, test, texts, cov


# ---------------------------------------------------------------- 阶段 2


def run_ablation(
    train, builders: Dict[str, EntityFeatureBuilder], pairs, n_pairs: int, folds: int
) -> pd.DataFrame:
    rows: List[dict] = []
    for name, feats in model.SIGNAL_COMBINATIONS.items():
        try:
            X, y, kept = model.build_pair_matrix(train, pairs, feats, builders)
        except ValueError as exc:
            log(f"  {name:28s} 跳过：{exc}")
            rows.append({"signal_combination": name, "features_used": "",
                         "n_features": 0, "svm_accuracy": np.nan, "note": str(exc)})
            continue
        t0 = time.time()
        mean, std, _ = model.cross_validate(X, y, folds=folds)
        log(f"  {name:28s} acc={mean:.4f} ± {std:.4f}  "
            f"({len(kept)} 特征, {time.time()-t0:.1f}s)")
        rows.append({
            "signal_combination": name,
            "features_used": ",".join(kept),
            "n_features": len(kept),
            "svm_accuracy": round(mean, 4),
            "svm_std": round(std, 4),
            "note": "" if len(kept) == len(feats) else f"缺 {set(feats)-set(kept)}",
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- 阶段 3-4


def predict_similarity(
    entity, builder: EntityFeatureBuilder, clf, features: Sequence[str]
) -> np.ndarray:
    n = len(entity)
    sim = np.zeros((n, n), dtype=np.float32)
    if n < 2:
        return sim
    ii, jj = np.triu_indices(n, k=1)
    X = builder.pair_matrix(features, ii, jj)
    scores = clf.decision_function(X.astype(np.float64))
    vals = model.decision_to_similarity(scores)
    sim[ii, jj] = vals
    sim[jj, ii] = vals
    np.fill_diagonal(sim, 1.0)
    return sim


def cluster_and_score(
    test, clf, features: Sequence[str], n_points: int
) -> Tuple[pd.DataFrame, Dict[str, List[Tuple[float, float]]]]:
    rows: List[dict] = []
    curves: Dict[str, List[Tuple[float, float]]] = {}

    stats_test = compute_collection_stats(test)
    for ent_id in sorted(test):
        ent = test[ent_id]
        if len(ent) < 2:
            continue
        builder = EntityFeatureBuilder(ent, stats_test)
        sim = predict_similarity(ent, builder, clf, features)
        Z, thresholds, labelings = clustering.cluster_with_linkage(sim, n_points=n_points)

        curve: List[Tuple[float, float]] = []
        for k, (thr, labels) in enumerate(zip(thresholds, labelings)):
            sc = metrics.score_entity(ent_id, ent.topics, [str(x) for x in labels])
            curve.append((sc.sensitivity, sc.reliability))
            rows.append({
                "entity_id": ent_id, "cut": k, "distance_threshold": thr,
                "n_tweets": len(ent), "n_clusters": int(len(set(labels))),
                "reliability": sc.reliability, "sensitivity": sc.sensitivity, "f1": sc.f1,
            })
        curves[ent_id] = curve
    return pd.DataFrame(rows), curves


# ---------------------------------------------------------------- 主流程


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="SIGIR'14 论文复现")
    ap.add_argument("--text-file", default=None, help="推文正文文件（jsonl/csv/tsv）或目录")
    ap.add_argument("--data-root", default=None, help="数据集根目录（默认为 RepLab 2013）")
    ap.add_argument("--out", default=None, help="结果输出目录（默认 results/）")
    ap.add_argument("--pairs", type=int, default=80_000, help="训练对数量（论文用 80,000）")
    ap.add_argument("--folds", type=int, default=10, help="交叉验证折数（论文用 10）")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--cuts", type=int, default=25, help="HAC 合并高度上取多少个阈值点")
    args = ap.parse_args(argv)
    set_output_dir(args.out)

    log("=" * 70)
    log("阶段 1/5  载入 RepLab 2013")
    train, test, texts, cov = load_data(args.text_file, args.data_root)

    log("阶段 2/5  构建特征与采样训练对")
    stats_train = compute_collection_stats(train)
    builders = {e: EntityFeatureBuilder(train[e], stats_train) for e in train}
    pairs = sampling.sample_training_pairs(train, n_pairs=args.pairs, seed=args.seed)
    log(f"采样到 {sum(len(v[2]) for v in pairs.values())} 个推文对，"
        f"正例 {sum(int(v[2].sum()) for v in pairs.values())}")

    log("阶段 3/5  特征消融 + 10 折交叉验证（论文 Table 2）")
    ablation = run_ablation(train, builders, pairs, args.pairs, args.folds)
    ablation.to_csv(OUT / "table2_similarity_learning.csv", index=False)

    log("阶段 4/5  训练最终模型并对测试集预测")
    X, y, used = model.build_pair_matrix(train, pairs, ALL_FEATURES, builders)
    clf = model.fit_final(X, y)
    log(f"最终模型使用 {len(used)} 个特征：{used}")
    log(f"（论文 'all' 组合为 13 个特征，实际可用 {len(used)} 个，"
        f"缺少 {sorted(TEXT_DEPENDENT - set(used))}）")

    t0 = time.time()
    detail, curves = cluster_and_score(test, clf, used, args.cuts)
    log(f"聚类+评测完成，用时 {time.time()-t0:.1f}s")
    detail.to_csv(OUT / "topic_detection_curve.csv", index=False)

    summary = metrics.summarize_curve(curves)
    if not detail.empty:
        best_cut = detail.groupby("cut")["f1"].mean().idxmax()
        best = detail[detail["cut"] == best_cut]
        summary["best_cut"] = float(best_cut)
        summary["best_f1"] = float(best["f1"].mean())
        summary["best_reliability"] = float(best["reliability"].mean())
        summary["best_sensitivity"] = float(best["sensitivity"].mean())
        summary["mean_n_clusters_at_best"] = float(best["n_clusters"].mean())

    log("阶段 5/5  汇总")
    log(f"  AUC(R&S) = {summary['auc']:.3f}   MAR = {summary['mar']:.3f}   "
        f"maxF1 = {summary['max_f1']:.3f}")

    report = {
        "paper": "Spina, Gonzalo, Amigo. Learning Similarity Functions for "
                 "Topic Detection in Online Reputation Monitoring. SIGIR 2014.",
        "text_coverage": round(cov, 4),
        "features_used": used,
        "features_missing": sorted(TEXT_DEPENDENT - set(used)),
        "n_train_tweets": int(sum(len(e) for e in train.values())),
        "n_test_tweets": int(sum(len(e) for e in test.values())),
        "n_train_topics": int(sum(e.n_topics for e in train.values())),
        "n_test_topics": int(sum(e.n_topics for e in test.values())),
        "n_pairs_sampled": int(len(y)),
        "topic_detection": {k: round(float(v), 4) for k, v in summary.items()},
        "paper_reported": {
            "table2_all_features_accuracy": 0.63,
            "table3_svm_all_auc": 0.41,
            "table3_svm_all_mar": 0.61,
            "table3_max_f1": 0.47,
        },
    }
    (OUT / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"结果已写入 {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
