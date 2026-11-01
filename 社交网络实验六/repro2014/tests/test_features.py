"""特征与预处理的单元测试：全部用可手算的用例验证公式实现。

运行::

    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import normalize as nz  # noqa: E402
from src.features import (  # noqa: E402
    CollectionStats,
    EntityFeatureBuilder,
    _binary_matrix,
    _cooccurrence_matrix,
    _jaccard_from_binary,
    _lin_from_binary,
    _time_matrix,
)
from src.replab_io import EntityData  # noqa: E402


class TestNormalize(unittest.TestCase):
    def test_punctuation_lowercase(self):
        self.assertEqual(nz.normalize_text("Hello, WORLD!!!"), ["hello", "world"])

    def test_stopwords_and_short_tokens(self):
        # the / is / a 都是停用词；"ok" 长度 2 被去掉；"good" 保留
        self.assertEqual(nz.normalize_text("the is a ok good"), ["good"])

    def test_spanish_stopwords(self):
        self.assertEqual(nz.normalize_text("el coche de la marca"), ["coche", "marca"])

    def test_mentions_hashtags(self):
        t = "@BMW great #M3 drive"
        self.assertEqual(nz.extract_mentions(t), {"bmw"})
        self.assertEqual(nz.extract_hashtags(t), {"m3"})

    def test_empty(self):
        self.assertEqual(nz.normalize_text(""), [])


class TestSimilarityFormulas(unittest.TestCase):
    def test_jaccard(self):
        # {a,b} vs {b,c}: 交 1，并 3 => 1/3
        mat, _ = _binary_matrix([{"a", "b"}, {"b", "c"}])
        sim = _jaccard_from_binary(mat)
        self.assertAlmostEqual(float(sim[0, 1]), 1 / 3, places=6)
        self.assertAlmostEqual(float(sim[0, 0]), 1.0, places=6)

    def test_jaccard_disjoint(self):
        mat, _ = _binary_matrix([{"a"}, {"b"}])
        self.assertAlmostEqual(float(_jaccard_from_binary(mat)[0, 1]), 0.0, places=6)

    def test_lin_equals_dice_when_uniform_weights(self):
        """所有词权重相同时，论文式(4) 退化为 Dice 系数 2|A∩B|/(|A|+|B|)。

        注意它不是 Jaccard：论文把 Lin 相似度称作 "weighted variation of
        Jaccard"，但公式本身是 Dice 形式，两者的分母不同。
        """
        bags = [{"a", "b", "c"}, {"b", "c", "d"}, {"a"}]
        mat, _ = _binary_matrix(bags)
        weights = np.ones(mat.shape[1], dtype=np.float32)
        lin = _lin_from_binary(mat, weights)
        self.assertAlmostEqual(float(lin[0, 1]), 2 * 2 / (3 + 3), places=6)  # 0.6667
        self.assertAlmostEqual(float(lin[0, 2]), 2 * 1 / (3 + 1), places=6)  # 0.5
        self.assertAlmostEqual(float(lin[1, 2]), 0.0, places=6)

    def test_lin_hand_computed(self):
        """两篇各含 2 个词、交 1 个词，且该词权重 1 => 2*1/(2+2)=0.5。"""
        mat, _ = _binary_matrix([{"a", "b"}, {"a", "c"}])
        weights = np.ones(mat.shape[1], dtype=np.float32)
        self.assertAlmostEqual(float(_lin_from_binary(mat, weights)[0, 1]), 0.5, places=6)

    def test_time_feature(self):
        # 相差 1 小时 => time_hours = 1/(1+1) = 0.5
        t = [0.0, 3600.0, 86400.0]
        hours = _time_matrix(t, 3600.0)
        self.assertAlmostEqual(float(hours[0, 1]), 0.5, places=6)
        # 相差 1 天 => time_days = 0.5
        days = _time_matrix(t, 86400.0)
        self.assertAlmostEqual(float(days[0, 2]), 0.5, places=6)
        # 毫秒口径下 1 小时差距很大，特征接近 0
        ms = _time_matrix(t, 0.001)
        self.assertLess(float(ms[0, 1]), 1e-3)

    def test_cooccurrence(self):
        bags = [{"u1", "u2"}, {"u2", "u3"}, {"u1"}]
        m = _cooccurrence_matrix(bags)
        self.assertEqual(float(m[0, 1]), 1.0)
        self.assertEqual(float(m[0, 2]), 1.0)
        self.assertEqual(float(m[1, 2]), 0.0)


class TestEntityFeatures(unittest.TestCase):
    def _entity(self, **kw):
        base = dict(
            entity_id="E1",
            tweet_ids=["1", "2"],
            authors=["alice", "bob"],
            timestamps=[0.0, 3600.0],
            urls=[[], []],
            topics=["t1", "t2"],
            texts=None,
        )
        base.update(kw)
        return EntityData(**base)

    def test_author_and_time_without_text(self):
        ent = self._entity()
        stats = CollectionStats(cf={}, total_cf=0, df={}, n_docs=1)
        b = EntityFeatureBuilder(ent, stats)
        self.assertEqual(float(b.get("author")[0, 0]), 1.0)
        self.assertEqual(float(b.get("author")[0, 1]), 0.0)
        self.assertAlmostEqual(float(b.get("time_hours")[0, 1]), 0.5, places=6)

    def test_text_features_nan_when_no_text(self):
        ent = self._entity()
        stats = CollectionStats(cf={}, total_cf=0, df={}, n_docs=1)
        b = EntityFeatureBuilder(ent, stats)
        for name in ("terms_jaccard", "semantic_jaccard", "hashtags", "namedusers"):
            self.assertTrue(np.all(np.isnan(b.get(name))), name)

    def test_terms_with_text(self):
        ent = self._entity(
            texts=["the quick brown fox", "the quick brown dog"], topics=["t1", "t1"]
        )
        stats = CollectionStats(
            cf={"quick": 2, "brown": 2, "fox": 1, "dog": 1},
            total_cf=6,
            df={"quick": 1, "brown": 1, "fox": 1, "dog": 1},
            n_docs=1,
        )
        b = EntityFeatureBuilder(ent, stats)
        # 归一化后 {quick,brown,fox} vs {quick,brown,dog} => 交 2 并 4 = 0.5
        self.assertAlmostEqual(float(b.get("terms_jaccard")[0, 1]), 0.5, places=6)


class TestSamplingPairs(unittest.TestCase):
    def test_pair_counts(self):
        from src.sampling import count_pairs

        ent = EntityData(
            entity_id="E",
            tweet_ids=["1", "2", "3", "4"],
            authors=["a"] * 4,
            timestamps=[0.0] * 4,
            urls=[[]] * 4,
            topics=["x", "x", "y", "y"],
            texts=None,
        )
        pos, neg = count_pairs(ent)
        self.assertEqual(pos, 2)   # 同话题 2 对
        self.assertEqual(neg, 4)   # 总 6 对 - 2


if __name__ == "__main__":
    unittest.main(verbosity=2)
