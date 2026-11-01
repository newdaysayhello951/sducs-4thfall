"""训练对采样：论文 3.2 节。

    "We randomly sample 80,000 pairs of tweets from the RepLab 2013 training
     dataset, keeping the true and false classes balanced."

注意论文没有说明按什么分布采样，这里采用「先按实体内可用对数加权选实体，
再在实体内按话题分组采样」的做法，并保证同一实体内成对（话题是实体相关的）。
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np

from .replab_io import EntityData


def _topic_groups(topics: List[str]) -> Dict[str, List[int]]:
    groups: Dict[str, List[int]] = {}
    for i, t in enumerate(topics):
        groups.setdefault(t, []).append(i)
    return groups


def count_pairs(entity: EntityData) -> Tuple[int, int]:
    """返回 (正对数, 负对数)。"""
    n = len(entity)
    if n < 2:
        return 0, 0
    groups = _topic_groups(entity.topics)
    pos = sum(len(v) * (len(v) - 1) // 2 for v in groups.values() if len(v) > 1)
    total = n * (n - 1) // 2
    return pos, total - pos


def _sample_positive(
    rng: np.random.Generator, groups: List[List[int]], weights: np.ndarray
) -> Tuple[int, int]:
    """从「同话题」的推文对里抽一对。

    groups 与 weights 由调用方预先算好，避免每次采样都重建分组
    （实体大时那会退化成 O(n) per sample）。
    """
    g = groups[int(rng.choice(len(groups), p=weights))]
    i, j = rng.choice(len(g), size=2, replace=False)
    return g[i], g[j]


def _sample_negative(rng: np.random.Generator, entity: EntityData) -> Tuple[int, int]:
    n = len(entity)
    i = int(rng.integers(n))
    ti = entity.topics[i]
    for _ in range(100):
        j = int(rng.integers(n))
        if j != i and entity.topics[j] != ti:
            return i, j
    raise RuntimeError("负样本采样失败：话题过于集中")


def _positive_sampler(entity: EntityData):
    """预计算正样本采样所需的分组与权重，返回一个可复用的闭包。"""
    groups = [v for v in _topic_groups(entity.topics).values() if len(v) > 1]
    if not groups:
        return None
    sizes = np.array([len(v) for v in groups], dtype=np.float64)
    weights = sizes * (sizes - 1) / 2.0
    weights = weights / weights.sum()
    return groups, weights


def sample_training_pairs(
    entities: Dict[str, EntityData],
    n_pairs: int = 80_000,
    seed: int = 42,
) -> Dict[str, Tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """采样 n_pairs 个平衡对。

    返回 {entity_id: (idx_i, idx_j, label)}，label=1 表示同话题。
    正负各占一半。
    """
    rng = np.random.default_rng(seed)
    ent_ids = [e for e in sorted(entities) if len(entities[e]) >= 2]
    pos_counts = np.array([count_pairs(entities[e])[0] for e in ent_ids], dtype=np.float64)
    neg_counts = np.array([count_pairs(entities[e])[1] for e in ent_ids], dtype=np.float64)

    # 预计算每个实体的正样本分组（只算一次）
    pos_samplers = {e: _positive_sampler(entities[e]) for e in ent_ids}

    half = n_pairs // 2
    out: Dict[str, Tuple[List[int], List[int], List[int]]] = {e: ([], [], []) for e in ent_ids}

    for want, counts, label in ((half, pos_counts, 1), (n_pairs - half, neg_counts, 0)):
        valid = np.where(counts > 0)[0]
        if len(valid) == 0:
            continue
        w = counts[valid] / counts[valid].sum()
        picks = rng.choice(valid, size=want, p=w)
        for k in picks:
            ent = entities[ent_ids[k]]
            if label == 1:
                sampler = pos_samplers[ent_ids[k]]
                if sampler is None:
                    continue
                i, j = _sample_positive(rng, *sampler)
            else:
                i, j = _sample_negative(rng, ent)
            out[ent_ids[k]][0].append(i)
            out[ent_ids[k]][1].append(j)
            out[ent_ids[k]][2].append(label)

    return {
        e: (
            np.asarray(v[0], dtype=np.int64),
            np.asarray(v[1], dtype=np.int64),
            np.asarray(v[2], dtype=np.int64),
        )
        for e, v in out.items()
        if v[2]
    }
