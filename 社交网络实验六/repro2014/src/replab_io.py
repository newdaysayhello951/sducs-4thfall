"""RepLab 2013 数据访问层。

只依赖官方数据集包（nlp.uned.es/replab2013），不依赖论文作者的任何代码。

数据集目录结构（节选）::

    replab2013-dataset/
        entities/replab2013_entities.tsv
        training/tweet_info/RL2013D01E001.dat      # tweet 元信息
        training/labeled/RL2013D01E001.dat         # 人工标注
        training/goldstandard/goldstandard_topic_detection.dat
        test/...
        evaluation/EVAL_TOPICDETECTION_RS.pl       # 官方评测脚本

关键限制：受 Twitter ToS 约束，数据集**只提供 tweet id，不提供正文**。
正文需要另行回捞（见 text_source.py）。
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

# ---------------------------------------------------------------- 路径

DEFAULT_ROOT = Path(__file__).resolve().parents[1] / "data" / "raw" / "replab2013-dataset"


def dataset_root(root: Optional[Path] = None) -> Path:
    root = Path(root) if root else DEFAULT_ROOT
    if not root.exists():
        raise FileNotFoundError(
            f"找不到 RepLab 2013 数据集：{root}\n"
            "请先下载 https://nlp.uned.es/replab2013/replab2013-dataset.tar.gz 并解压到 data/raw/"
        )
    return root


# ---------------------------------------------------------------- 读取原始表


def _read_dat(path: Path) -> pd.DataFrame:
    """读取 .dat（tab 分隔、全字段带引号、编码混杂）。"""
    return pd.read_csv(
        path,
        sep="\t",
        dtype=str,
        quoting=csv.QUOTE_ALL,
        encoding="utf-8",
        encoding_errors="replace",
        keep_default_na=False,
    )


def load_entities(root: Optional[Path] = None) -> pd.DataFrame:
    root = dataset_root(root)
    return _read_dat(root / "entities" / "replab2013_entities.tsv")


def load_tweet_info(split: str, root: Optional[Path] = None) -> pd.DataFrame:
    """合并某个 split 下 61 个实体的 tweet_info。

    split: "training" | "test"
    返回列：tweet_id, author, entity_id, tweet_url, language, timestamp,
            urls, extended_urls, md5_extended_urls, is_near_duplicate_of
    """
    root = dataset_root(root)
    d = root / split / "tweet_info"
    frames = [_read_dat(f) for f in sorted(d.glob("*.dat"))]
    if not frames:
        raise FileNotFoundError(f"{d} 下没有 .dat 文件")
    df = pd.concat(frames, ignore_index=True)
    df["timestamp"] = pd.to_numeric(df["timestamp"], errors="coerce")
    df["is_near_duplicate_of"] = df["is_near_duplicate_of"].fillna("-1")
    return df


def load_topic_gold(split: str, root: Optional[Path] = None) -> pd.DataFrame:
    """话题标注（只包含与实体相关、且被分到某个话题的推文）。"""
    root = dataset_root(root)
    df = _read_dat(root / split / "goldstandard" / "goldstandard_topic_detection.dat")
    df["topic"] = df["topic"].fillna("")
    return df[df["topic"] != ""].reset_index(drop=True)


def load_filtering_gold(split: str, root: Optional[Path] = None) -> pd.DataFrame:
    root = dataset_root(root)
    return _read_dat(root / split / "goldstandard" / "goldstandard_filtering.dat")


# ---------------------------------------------------------------- 实体级数据容器


@dataclass
class EntityData:
    """单个实体（test case）在某一 split 下的全部推文。

    下标 i 对应一条推文；所有列表等长且顺序一致。
    """

    entity_id: str
    tweet_ids: List[str]
    authors: List[str]
    timestamps: List[float]
    urls: List[List[str]]
    topics: List[str]
    texts: List[Optional[str]] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.tweet_ids)

    @property
    def has_text(self) -> bool:
        return bool(self.texts) and any(t is not None for t in self.texts)

    @property
    def n_topics(self) -> int:
        return len(set(self.topics))


def _split_urls(raw: str) -> List[str]:
    """urls 字段通常是单个链接；为稳妥起见同时按空白/逗号切分。"""
    if not raw:
        return []
    out: List[str] = []
    for chunk in raw.replace(",", " ").split():
        chunk = chunk.strip()
        if chunk:
            out.append(chunk)
    return out


def build_entities(
    split: str,
    drop_near_duplicates: bool = True,
    texts: Optional[Dict[str, str]] = None,
    root: Optional[Path] = None,
) -> Dict[str, EntityData]:
    """构造 {entity_id: EntityData}。

    按论文 3.1 节的口径：
      1. 只保留与实体相关、并被标注了话题的推文；
      2. 剔除 near-duplicate（`is_near_duplicate_of != "-1"`）。
    """
    info = load_tweet_info(split, root)
    gold = load_topic_gold(split, root)

    merged = gold.merge(
        info[["tweet_id", "entity_id", "author", "timestamp", "urls", "is_near_duplicate_of"]],
        on=["tweet_id", "entity_id"],
        how="inner",
    )

    if drop_near_duplicates:
        merged = merged[merged["is_near_duplicate_of"].fillna("-1") == "-1"]

    merged = merged.sort_values(["entity_id", "timestamp"], kind="mergesort").reset_index(drop=True)

    texts = texts or {}
    out: Dict[str, EntityData] = {}
    for ent, g in merged.groupby("entity_id", sort=True):
        out[ent] = EntityData(
            entity_id=ent,
            tweet_ids=g["tweet_id"].tolist(),
            authors=g["author"].fillna("").tolist(),
            timestamps=g["timestamp"].fillna(0.0).astype(float).tolist(),
            urls=[_split_urls(u) for u in g["urls"].fillna("").tolist()],
            topics=g["topic"].tolist(),
            texts=[texts.get(t) for t in g["tweet_id"].tolist()],
        )
    return out


def dataset_summary(entities: Dict[str, EntityData]) -> pd.DataFrame:
    rows = [
        {
            "entity_id": e.entity_id,
            "n_tweets": len(e),
            "n_topics": e.n_topics,
            "has_text": e.has_text,
        }
        for e in entities.values()
    ]
    return pd.DataFrame(rows)
