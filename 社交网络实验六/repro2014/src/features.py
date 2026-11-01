"""论文 2.3 节的 13 个相似度特征。

论文把特征分成四族：

    term      : terms_jaccard, terms_lin_cf, terms_lin_tfidf
    semantic  : semantic_jaccard, semantic_lin_cf, semantic_lin_tfidf
    metadata  : author, namedusers, urls, hashtags
    time      : time_millis, time_hours, time_days

公式（论文式 3~7）::

    terms_jaccard(d,d') = |Wd ∩ Wd'| / |Wd ∪ Wd'|

    terms_lin_cf(d,d')  = 2 * Σ_{w∈∩} log(1/p(w))
                          / ( Σ_{w∈Wd} log(1/p(w)) + Σ_{w∈Wd'} log(1/p(w)) )
                          p(w) = cf(w) / Σ_i cf(w_i)

    terms_lin_tfidf 与上式同构，只是 p(w) 换成以实体伪文档为单位计算的 tf.idf 权重:
        p(w) = tf(w,D) * log(N/df(w)) / Σ_w' [tf(w',D) * log(N/df(w'))]
        D  = 该实体全部推文构成的伪文档
        N  = 集合中伪文档数（= 实体数 61）
        df(w) = 含 w 的伪文档数

    f_time(t,t') = 1 / (1 + |t - t'|)，分别用毫秒/小时/天三种时间单位

metadata 与 time 特征不依赖正文；term / semantic / hashtags / namedusers
依赖正文，在正文缺失时输出 NaN（由上层决定丢弃还是报错）。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set

import numpy as np
from scipy import sparse

from . import normalize as nz
from .replab_io import EntityData

TERM_FEATURES = ["terms_jaccard", "terms_lin_cf", "terms_lin_tfidf"]
SEMANTIC_FEATURES = ["semantic_jaccard", "semantic_lin_cf", "semantic_lin_tfidf"]
METADATA_FEATURES = ["author", "namedusers", "urls", "hashtags"]
TIME_FEATURES = ["time_millis", "time_hours", "time_days"]

ALL_FEATURES = TERM_FEATURES + SEMANTIC_FEATURES + METADATA_FEATURES + TIME_FEATURES

# 依赖推文正文的特征
TEXT_DEPENDENT = set(TERM_FEATURES) | set(SEMANTIC_FEATURES) | {"namedusers", "hashtags"}


# ---------------------------------------------------------------- 概念链接

class ConceptLinker:
    """把一条推文映射成 Wikipedia 概念集合。

    论文用的是 commonness 概率：

        commonness(c,q) = |L_{q,c}| / Σ_{c'} |L_{q,c'}|

    其中 L_{q,c} 是锚文本 q 指向概念 c 的链接集合。对推文中每个 n-gram
    取 commonness 最高的概念；n-gram 有重叠时只保留最长的。

    真正运行需要 Wikipedia 的锚文本统计（anchor dump）。这里只给出接口与
    最长匹配逻辑，默认实现返回空集合——语义特征因此不可用。
    """

    def link(self, text: str) -> Set[str]:
        raise NotImplementedError


class NullLinker(ConceptLinker):
    """没有 Wikipedia 资源时的占位实现。"""

    def link(self, text: str) -> Set[str]:
        return set()


class DictionaryLinker(ConceptLinker):
    """基于 anchor->(concept, count) 统计表的 commonness 链接器。

    anchors: {anchor_text: {concept: link_count}}
    """

    def __init__(self, anchors: Dict[str, Dict[str, int]], max_ngram: int = 6):
        self.anchors = anchors
        self.max_ngram = max_ngram

    def link(self, text: str) -> Set[str]:
        tokens = nz.normalize_text(text)
        concepts: Set[str] = set()
        i = 0
        while i < len(tokens):
            matched = None
            for n in range(min(self.max_ngram, len(tokens) - i), 0, -1):
                cand = " ".join(tokens[i:i + n])
                if cand in self.anchors:
                    counts = self.anchors[cand]
                    total = sum(counts.values())
                    if total > 0:
                        matched = max(counts.items(), key=lambda kv: kv[1] / total)[0]
                        i += n
                        break
            if matched is not None:
                concepts.add(matched)
            else:
                i += 1
        return concepts


# ---------------------------------------------------------------- 特征抽取


@dataclass
class CollectionStats:
    """集合级统计量，用于 Lin 相似度的 p(w)。"""

    cf: Dict[str, int]                 # 词频（整个 split 的所有推文）
    total_cf: int
    df: Dict[str, int]                 # 出现在多少个实体伪文档里
    n_docs: int                        # 伪文档总数 = 实体数


def compute_collection_stats(entities: Dict[str, EntityData]) -> CollectionStats:
    cf: Dict[str, int] = {}
    df: Dict[str, int] = {}
    for e in entities.values():
        seen_here: Set[str] = set()
        for t in e.texts:
            if t is None:
                continue
            for w in nz.normalize_text_cached(t):
                cf[w] = cf.get(w, 0) + 1
                seen_here.add(w)
        for w in seen_here:
            df[w] = df.get(w, 0) + 1
    return CollectionStats(cf=cf, total_cf=sum(cf.values()), df=df, n_docs=max(len(entities), 1))


def _binary_matrix(bags: Sequence[Set[str]]) -> tuple[sparse.csr_matrix, Dict[str, int]]:
    vocab: Dict[str, int] = {}
    rows: List[int] = []
    cols: List[int] = []
    for i, bag in enumerate(bags):
        for w in bag:
            j = vocab.get(w)
            if j is None:
                j = len(vocab)
                vocab[w] = j
            rows.append(i)
            cols.append(j)
    data = np.ones(len(rows), dtype=np.float32)
    mat = sparse.csr_matrix((data, (rows, cols)), shape=(len(bags), len(vocab)), dtype=np.float32)
    return mat, vocab


def _jaccard_from_binary(mat: sparse.csr_matrix) -> np.ndarray:
    inter = (mat @ mat.T).toarray().astype(np.float32)
    sizes = np.asarray(mat.sum(axis=1)).ravel().astype(np.float32)
    union = sizes[:, None] + sizes[None, :] - inter
    with np.errstate(divide="ignore", invalid="ignore"):
        sim = np.where(union > 0, inter / union, 0.0)
    return sim.astype(np.float32)


def _lin_from_binary(mat: sparse.csr_matrix, weights: np.ndarray) -> np.ndarray:
    """Lin 相似度：加权版本的 Jaccard。

    weights[j] 是词表第 j 个词的 log(1/p(w))。
    """
    weighted = mat.multiply(weights[None, :]).tocsr()
    inter = (weighted @ mat.T).toarray().astype(np.float32)  # Σ_{w∈∩} weight(w)
    denom_doc = np.asarray(weighted.sum(axis=1)).ravel().astype(np.float32)
    denom = denom_doc[:, None] + denom_doc[None, :]
    with np.errstate(divide="ignore", invalid="ignore"):
        sim = np.where(denom > 0, 2.0 * inter / denom, 0.0)
    return sim.astype(np.float32)


def _cf_weights(mat: sparse.csr_matrix, vocab: Dict[str, int], stats: CollectionStats) -> np.ndarray:
    """p(w) = cf(w)/Σcf，返回 log(1/p(w))。"""
    terms = list(vocab)                       # 词表按索引顺序排列
    total = max(stats.total_cf, 1)
    cf = np.fromiter((stats.cf.get(w, 0) for w in terms), dtype=np.float64, count=len(terms))
    p = cf / total
    with np.errstate(divide="ignore"):
        w = np.where(p > 0, np.log(1.0 / np.maximum(p, 1e-12)), 0.0)
    return w.astype(np.float32)


def _tfidf_weights(
    mat: sparse.csr_matrix, vocab: Dict[str, int], stats: CollectionStats
) -> np.ndarray:
    """以实体伪文档为单位算 tf.idf，归一化成 p(w) 后返回 log(1/p(w))。

    p(w) ∝ tf(w,D) * log(N/df(w))

    注意：tf 用整列求和一次算完（CSR 按列切片很慢，这里必须向量化，
    否则在大词表上会退化成 O(V·nnz)）。
    """
    terms = list(vocab)
    n_docs = max(stats.n_docs, 1)
    tf = np.asarray(mat.sum(axis=0)).ravel().astype(np.float64)
    df = np.fromiter((stats.df.get(w, 1) for w in terms), dtype=np.float64, count=len(terms))
    idf = np.log(n_docs / np.maximum(df, 1.0))
    idf = np.maximum(idf, 0.0)
    raw = tf * idf
    total = raw.sum()
    if total <= 0:
        return np.zeros(mat.shape[1], dtype=np.float32)
    p = raw / total
    with np.errstate(divide="ignore"):
        w = np.where(p > 0, np.log(1.0 / np.maximum(p, 1e-12)), 0.0)
    return w.astype(np.float32)


def _cooccurrence_matrix(bags: Sequence[Set[str]]) -> np.ndarray:
    """两个推文集合的交集大小矩阵（metadata 的 urls / hashtags / namedusers）。"""
    if not bags or all(len(b) == 0 for b in bags):
        return np.zeros((len(bags), len(bags)), dtype=np.float32)
    mat, _ = _binary_matrix(bags)
    return (mat @ mat.T).toarray().astype(np.float32)


def _time_matrix(timestamps: Sequence[float], unit_seconds: float) -> np.ndarray:
    """f_time(t,t') = 1/(1+|t-t'|)，t 以 unit_seconds 为单位。"""
    t = np.asarray(timestamps, dtype=np.float64) / unit_seconds
    dt = np.abs(t[:, None] - t[None, :])
    return (1.0 / (1.0 + dt)).astype(np.float32)


class EntityFeatureBuilder:
    """为单个实体预计算所有 n×n 特征矩阵。"""

    def __init__(
        self,
        entity: EntityData,
        stats: CollectionStats,
        linker: Optional[ConceptLinker] = None,
    ):
        self.entity = entity
        self.stats = stats
        self.linker = linker or NullLinker()
        self.n = len(entity)
        self._cache: Dict[str, np.ndarray] = {}

    # -- 单特征 ------------------------------------------------------

    def get(self, name: str) -> np.ndarray:
        if name not in self._cache:
            self._cache[name] = self._compute(name)
        return self._cache[name]

    def _compute(self, name: str) -> np.ndarray:
        e = self.entity

        if name == "time_millis":
            return _time_matrix(e.timestamps, 0.001)
        if name == "time_hours":
            return _time_matrix(e.timestamps, 3600.0)
        if name == "time_days":
            return _time_matrix(e.timestamps, 86400.0)

        if name == "author":
            a = np.array(e.authors, dtype=object)
            return (a[:, None] == a[None, :]).astype(np.float32)

        if name == "urls":
            return _cooccurrence_matrix(e.urls)

        if name in ("hashtags", "namedusers"):
            if not e.has_text:
                return np.full((self.n, self.n), np.nan, dtype=np.float32)
            fn = nz.extract_hashtags if name == "hashtags" else nz.extract_mentions
            return _cooccurrence_matrix([fn(t or "") for t in e.texts])

        if name in TERM_FEATURES:
            if not e.has_text:
                return np.full((self.n, self.n), np.nan, dtype=np.float32)
            bags = [nz.term_set(t or "") for t in e.texts]
            mat, vocab = _binary_matrix(bags)
            if name == "terms_jaccard":
                return _jaccard_from_binary(mat)
            if name == "terms_lin_cf":
                return _lin_from_binary(mat, _cf_weights(mat, vocab, self.stats))
            return _lin_from_binary(mat, _tfidf_weights(mat, vocab, self.stats))

        if name in SEMANTIC_FEATURES:
            if not e.has_text:
                return np.full((self.n, self.n), np.nan, dtype=np.float32)
            bags = [self.linker.link(t or "") for t in e.texts]
            if all(len(b) == 0 for b in bags):
                return np.full((self.n, self.n), np.nan, dtype=np.float32)
            mat, vocab = _binary_matrix(bags)
            if name == "semantic_jaccard":
                return _jaccard_from_binary(mat)
            if name == "semantic_lin_cf":
                return _lin_from_binary(mat, _cf_weights(mat, vocab, self.stats))
            return _lin_from_binary(mat, _tfidf_weights(mat, vocab, self.stats))

        raise KeyError(f"未知特征 {name}")

    # -- 批量 --------------------------------------------------------

    def pair_matrix(self, features: Sequence[str], idx_i: np.ndarray, idx_j: np.ndarray) -> np.ndarray:
        """按 (idx_i, idx_j) 取出特征，返回 shape=(len(idx_i), len(features)) 的矩阵。"""
        cols = []
        for f in features:
            m = self.get(f)
            cols.append(m[idx_i, idx_j])
        return np.vstack(cols).T.astype(np.float32)
