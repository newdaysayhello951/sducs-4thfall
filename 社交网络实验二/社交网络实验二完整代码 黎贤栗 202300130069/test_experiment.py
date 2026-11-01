import unittest
import numpy as np
from load_data import split_story
from textrank import pagerank, summarize, split_sentences
from metrics import evaluate, corpus_bleu, lcs_length


class ExperimentTests(unittest.TestCase):
    def test_parser(self):
        self.assertEqual(split_story('news'), ('news', []))
        self.assertEqual(split_story('news @highlight a @highlight  '), ('news', ['a']))

    def test_pagerank_stationary_distribution(self):
        scores, _, converged = pagerank([[0, 1, 0], [1, 0, 1], [0, 1, 0]])
        self.assertTrue(converged)
        np.testing.assert_allclose(scores, [0.25675676, 0.48648649, 0.25675676], atol=1e-6)
        scores, _, _ = pagerank(np.zeros((3, 3)))
        np.testing.assert_allclose(scores, [1/3]*3)

    def test_empty_and_order(self):
        self.assertEqual(summarize('')['summary'], '')
        text = 'Dr. Smith studies cats. Cats eat fish. Fish swim.'
        sentences = split_sentences(text)
        self.assertEqual(len(sentences), 3)
        for method in ('overlap', 'tfidf'):
            result = summarize(text, 2, method)
            self.assertEqual(result['indices'], sorted(result['indices']))
            self.assertEqual(result['summary'], ' '.join(sentences[i] for i in result['indices']))

    def test_metrics(self):
        result = evaluate('one two three four five', 'one two three four five')
        self.assertEqual(result['rouge1']['f1'], 1)
        self.assertEqual(result['rougeL']['f1'], 1)
        self.assertEqual(corpus_bleu([result['bleu_counts']]), 1)
        self.assertEqual(evaluate('a a a', 'a b')['rouge1']['precision'], 1/3)
        self.assertEqual(lcs_length(['a', 'b', 'c'], ['b', 'a', 'c']), 2)
        self.assertEqual(corpus_bleu([evaluate('', 'a')['bleu_counts']]), 0)


if __name__ == '__main__':
    unittest.main()
