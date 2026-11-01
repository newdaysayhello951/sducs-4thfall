"""单链接层次凝聚聚类（HAC），论文 2.2.1 与 3.3 节。

论文要点：
  * 相似度来自上一步 SVM 的正类置信度；
  * 用单链接（single linkage）HAC；
  * 用相似度阈值作为停止条件，切出平坦聚类；
  * 阈值按相似度的百分位扫描，得到 R&S 曲线。

单链接 + 距离阈值切割，等价于在最大生成树上按边权切分，这里直接用
scipy 的 linkage/fcluster 实现。
"""

from __future__ import annotations

from typing import List, Sequence

import numpy as np
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform


def similarity_to_condensed_distance(sim: np.ndarray) -> np.ndarray:
    """相似度矩阵 -> 压缩距离向量。distance = 1 - similarity。"""
    d = 1.0 - np.asarray(sim, dtype=np.float64)
    np.fill_diagonal(d, 0.0)
    d = np.clip(d, 0.0, None)
    d = (d + d.T) / 2.0  # 数值上强制对称
    return squareform(d, checks=False)


def build_linkage(sim: np.ndarray, method: str = "single") -> np.ndarray:
    return linkage(similarity_to_condensed_distance(sim), method=method)


def cut_at_distance(Z: np.ndarray, distance_threshold: float, n_items: int) -> np.ndarray:
    """在给定距离阈值处切树，返回长度 n_items 的簇标签（从 1 开始）。"""
    return fcluster(Z, t=distance_threshold, criterion="distance")


def percentile_thresholds(sim: np.ndarray, percentiles: Sequence[float]) -> List[float]:
    """按两两相似度的百分位生成距离阈值。

    论文："Each dot in a curve represents the output of the HAC algorithm at
    different similarity thresholds (in percentiles)."
    相似度越低 -> 距离越大 -> 簇越大 -> Sensitivity 越高、Reliability 越低。
    """
    iu = np.triu_indices_from(sim, k=1)
    vals = sim[iu]
    if vals.size == 0:
        return [0.5]
    thresholds = []
    for p in percentiles:
        sim_cut = float(np.percentile(vals, p))
        thresholds.append(float(1.0 - sim_cut))
    return sorted(set(thresholds))


def linkage_thresholds(Z: np.ndarray, n_points: int = 25) -> List[float]:
    """在层次树的合并高度上取阈值。

    单链接 HAC 的簇结构只由最小生成树的边权决定：切在第 k 小的边权处，
    就得到 k+1 个簇。直接在两两相似度的百分位上切，当相似度分布被压缩
    （例如模型很弱、置信度都挤在 0.5 附近）时，所有阈值会落在极窄区间，
    曲线退化成几个点。改用合并高度扫描可以保证从「全单点」到「全一簇」
    的整条层次都被覆盖，与论文「扫描阈值得到 R&S 曲线」的意图一致。
    """
    heights = np.unique(Z[:, 2])
    if heights.size <= 1:
        return [float(heights[0]) if heights.size else 0.5]
    if heights.size <= n_points:
        return [float(h) for h in heights]
    qs = np.linspace(0.0, 1.0, n_points)
    picked = np.quantile(heights, qs)
    # 略微抬高一点，确保切在合并点之上
    return sorted({float(v) + 1e-9 for v in picked})


def cluster_at_thresholds(
    sim: np.ndarray, distance_thresholds: Sequence[float]
) -> List[np.ndarray]:
    """对同一实体在多个距离阈值上切树。linkage 只算一次。"""
    n = sim.shape[0]
    if n <= 1:
        return [np.ones(n, dtype=int) for _ in distance_thresholds]
    Z = build_linkage(sim)
    return [cut_at_distance(Z, t, n) for t in distance_thresholds]


def cluster_with_linkage(
    sim: np.ndarray, n_points: int = 25
) -> tuple[np.ndarray, List[float], List[np.ndarray]]:
    """一次建树，返回 (Z, 阈值列表, 各阈值下的标签列表)。"""
    n = sim.shape[0]
    Z = build_linkage(sim)
    ths = linkage_thresholds(Z, n_points)
    labels = [cut_at_distance(Z, t, n) for t in ths]
    return Z, ths, labels
