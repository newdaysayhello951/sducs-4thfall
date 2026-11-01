"""RepLab 2013 话题检测官方指标：Reliability (R)、Sensitivity (S)、F1(R,S)。

论文 3.3 节明确说明：在聚类任务中 R&S 等价于 BCubed 的 Precision 与 Recall，
F1(R,S) 是每个 test case 上 R、S 的调和平均再对 61 个实体做宏平均。

这里按官方评测脚本 EVAL_TOPICDETECTION_RS.pl（随数据集发布）的定义逐条实现，
语义完全一致：

    对实体内每一条推文 d1：
      S_d1 = |{d2 : gold(d2)=gold(d1) 且 sys(d2)=sys(d1)}| / |{d2 : gold(d2)=gold(d1)}|
      R_d1 = |{d2 : sys(d2)=sys(d1) 且 gold(d2)=gold(d1)}| / |{d2 : sys(d2)=sys(d1)}|
    其中若 d1 不在系统输出里：S_d1 = 0，R_d1 = 1（官方脚本的行为）
    若 sys(d1) 为空簇（分母为 0）：R_d1 = 1

    R = mean_d1 R_d1,  S = mean_d1 S_d1,  F = 2RS/(R+S)
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np


MISSING = "__MISSING__"


@dataclass
class EntityScore:
    entity_id: str
    reliability: float
    sensitivity: float
    f1: float


def score_entity(entity_id: str, gold: Sequence[str], sys_labels: Sequence[Optional[str]]) -> EntityScore:
    """计算单个实体的 R / S / F。sys_labels 中 None 表示系统未输出该推文。"""
    if len(gold) != len(sys_labels):
        raise ValueError(f"{entity_id}: gold 与 sys 长度不一致")
    n = len(gold)
    if n == 0:
        return EntityScore(entity_id, 0.0, 0.0, 0.0)

    s = [MISSING if x is None else x for x in sys_labels]
    pair_counts = Counter(zip(gold, s))
    gold_counts = Counter(gold)
    sys_counts = Counter(s)

    sum_s = 0.0
    sum_r = 0.0
    for g, sy in zip(gold, s):
        if sy == MISSING:
            sum_s += 0.0
            sum_r += 1.0
            continue
        inter = pair_counts[(g, sy)]
        denom_s = gold_counts[g]
        denom_r = sys_counts[sy]
        sum_s += inter / denom_s if denom_s else 1.0
        sum_r += inter / denom_r if denom_r else 1.0

    R = sum_r / n
    S = sum_s / n
    F = 2 * R * S / (R + S) if (R > 0 and S > 0) else 0.0
    return EntityScore(entity_id, R, S, F)


def score_system(
    gold_by_entity: Dict[str, Sequence[str]],
    sys_by_entity: Dict[str, Sequence[Optional[str]]],
) -> Tuple[List[EntityScore], Dict[str, float]]:
    """对整套系统输出打分，返回 (逐实体明细, 汇总指标)。"""
    rows: List[EntityScore] = []
    for ent in sorted(gold_by_entity):
        rows.append(score_entity(ent, gold_by_entity[ent], sys_by_entity.get(ent, [])))
    summary = {
        "n_entities": len(rows),
        "reliability": float(np.mean([r.reliability for r in rows])) if rows else 0.0,
        "sensitivity": float(np.mean([r.sensitivity for r in rows])) if rows else 0.0,
        "f1": float(np.mean([r.f1 for r in rows])) if rows else 0.0,
    }
    return rows, summary


# ---------------------------------------------------------------- 曲线级指标


def auc_rs(curve: Sequence[Tuple[float, float]]) -> float:
    """R&S 曲线下面积：点集为 (Sensitivity, Reliability)，按 S 排序后梯形积分。"""
    pts = sorted(curve, key=lambda x: x[0])
    if len(pts) < 2:
        return 0.0
    xs = np.array([p[0] for p in pts], dtype=float)
    ys = np.array([p[1] for p in pts], dtype=float)
    return float(np.trapz(ys, xs))


def mar_rs(curve: Sequence[Tuple[float, float]]) -> float:
    """Mean Average Reliability：MAP 在 R&S 曲线上的对应物。

    按 Sensitivity 从高到低遍历工作点，对 Reliability 取平均。
    """
    if not curve:
        return 0.0
    pts = sorted(curve, key=lambda x: -x[0])
    return float(np.mean([p[1] for p in pts]))


def summarize_curve(
    per_entity_curves: Dict[str, List[Tuple[float, float]]]
) -> Dict[str, float]:
    """把每个实体在各阈值上的 (S, R) 序列汇总成 AUC / MAR / maxF。"""
    aucs, mars, maxfs = [], [], []
    for curve in per_entity_curves.values():
        if not curve:
            continue
        aucs.append(auc_rs(curve))
        mars.append(mar_rs(curve))
        best = 0.0
        for S, R in curve:
            if R > 0 and S > 0:
                best = max(best, 2 * R * S / (R + S))
        maxfs.append(best)
    if not aucs:
        return {"auc": 0.0, "mar": 0.0, "max_f1": 0.0}
    return {
        "auc": float(np.mean(aucs)),
        "mar": float(np.mean(mars)),
        "max_f1": float(np.mean(maxfs)),
    }
