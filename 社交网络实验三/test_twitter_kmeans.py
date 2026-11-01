"""验证词袋计数、聚类优化与标签无关的评价，不依赖 sklearn。"""
import unittest

import numpy as np
from scipy.sparse import csr_matrix

from twitter_kmeans import assign_clusters, evaluate, kmeans, vectorize


class ClusteringTests(unittest.TestCase):
    def test_word_counts_and_empty_document(self):
        matrix, words = vectorize(["Cat cat dog", "dog bird", ""], min_df=1, normalize=False)
        self.assertEqual(words, ["dog", "bird", "cat"])
        np.testing.assert_array_equal(matrix.toarray(), [[1, 0, 2], [1, 1, 0], [0, 0, 0]])
        normalized, _ = vectorize(["cat cat dog", ""], min_df=1)
        self.assertAlmostEqual(float(normalized.multiply(normalized).sum()), 1.0)

    def test_known_two_groups(self):
        matrix = csr_matrix([[0., 0.], [0., 2.], [10., 10.], [10., 12.]])
        result = kmeans(matrix, 2, seed=7, verbose=False, batch_size=1)
        labels = result["labels"]
        self.assertEqual(labels[0], labels[1])
        self.assertEqual(labels[2], labels[3])
        self.assertNotEqual(labels[0], labels[2])
        self.assertAlmostEqual(result["inertia"], 4.0)
        for label in range(2):
            np.testing.assert_allclose(result["centers"][label],
                                       np.asarray(matrix[labels == label].mean(axis=0)).ravel())
        objectives = [step["inertia_before_update"] for step in result["history"]]
        self.assertTrue(all(a >= b - 1e-10 for a, b in zip(objectives, objectives[1:])))

    def test_duplicates_empty_clusters_and_final_assignment(self):
        matrix = csr_matrix([[1., 0.], [1., 0.], [0., 1.], [0., 1.]])
        result = kmeans(matrix, 3, max_iter=3, verbose=False)
        self.assertTrue(np.isfinite(result["centers"]).all())
        labels, distances = assign_clusters(matrix, result["centers"], 2)
        np.testing.assert_array_equal(labels, result["labels"])
        self.assertAlmostEqual(distances.sum(), 0.0)
        with self.assertRaises(ValueError):
            kmeans(matrix, 5, verbose=False)

    def test_evaluation_ignores_cluster_numbering(self):
        scores = evaluate([0, 0, 1, 1], np.array([9, 9, 3, 3]))
        self.assertEqual(scores, {"adjusted_rand_index": 1.0, "purity": 1.0})
        mixed = evaluate([0, 0, 1, 1], np.array([0, 1, 0, 1]))
        self.assertAlmostEqual(mixed["adjusted_rand_index"], -0.5)
        self.assertEqual(mixed["purity"], 0.5)


if __name__ == "__main__":
    unittest.main()
