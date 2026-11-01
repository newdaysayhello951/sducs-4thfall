from pathlib import Path
import sys
import unittest

import torch

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "src"))

from takg.config import ExperimentConfig
from takg.data import BOS, EOS, PAD, UNK, Vocabulary, TrainingDataset, collate_training, read_parallel
from takg.metrics import evaluate_records, is_present
from takg.model import NeuralTopicModel, TAKG, topic_model_loss


class ReproductionTests(unittest.TestCase):
    def setUp(self):
        tokens = [PAD, UNK, BOS, EOS, "yellow", "pants", "team", "super", "bowl"]
        self.vocab = Vocabulary({token: index for index, token in enumerate(tokens)}, tokens)
        bow_tokens = ["yellow", "pants", "team"]
        self.bow = Vocabulary({token: index for index, token in enumerate(bow_tokens)}, bow_tokens)

    def test_public_data_is_parallel(self):
        for dataset, expected in (("Weibo", (37036, 4630, 4630)),
                                  ("StackExchange", (39557, 4945, 4945))):
            folder = PROJECT / "data" / dataset
            counts = tuple(len(read_parallel(folder, split)) for split in ("train", "valid", "test"))
            self.assertEqual(counts, expected)

    def test_topic_model_outputs_distribution_and_finite_loss(self):
        model = NeuralTopicModel(bow_size=3, hidden_size=8, topic_count=2)
        counts = torch.tensor([[2.0, 1.0, 0.0], [0.0, 1.0, 3.0]])
        topics, log_words, mean, log_variance = model(torch.nn.functional.normalize(counts, dim=1))
        self.assertEqual(topics.shape, (2, 2))
        self.assertTrue(torch.allclose(topics.sum(-1), torch.ones(2), atol=1e-6))
        self.assertTrue(torch.allclose(log_words.exp().sum(-1), torch.ones(2), atol=1e-6))
        loss = topic_model_loss(log_words, counts, mean, log_variance)
        loss.backward()
        self.assertTrue(torch.isfinite(loss))

    def test_oov_copy_indices_are_local_to_each_post(self):
        item = TrainingDataset._encode(["yellow", "new_team", "new_team"], ["new_team"], self.vocab, self.bow)
        self.assertEqual(item["oov_tokens"], ["new_team"])
        self.assertEqual(item["extended_source"], [4, len(self.vocab), len(self.vocab)])
        self.assertEqual(item["extended_target"][0], len(self.vocab))

    def test_full_model_normalizes_extended_distribution_and_backpropagates_topics(self):
        dataset = TrainingDataset([(["yellow", "pants", "new_team"], [["super", "bowl"]])],
                                  self.vocab, self.bow, 10, 5)
        batch = collate_training([dataset[0]], self.vocab.token_to_id[PAD], len(self.bow))
        model = TAKG(len(self.vocab), len(self.bow), self.vocab.token_to_id[PAD],
                     embedding_size=8, encoder_hidden_size=6, encoder_layers=2,
                     decoder_hidden_size=12, topic_count=2, topic_hidden_size=8, dropout=0.0)
        output, attention, topic_words, mean, log_variance = model(
            batch["source"], batch["source_lengths"], batch["source_mask"],
            batch["extended_source"], batch["bow"], batch["target"], self.vocab.token_to_id[BOS])
        self.assertEqual(output.shape[-1], len(self.vocab) + 1)
        self.assertTrue(torch.allclose(output.sum(-1), torch.ones_like(output.sum(-1)), atol=1e-5))
        self.assertTrue(torch.allclose(attention.sum(-1), torch.ones_like(attention.sum(-1)), atol=1e-5))
        (-output[0, 0, self.vocab.token_to_id["super"]].log()).backward()
        self.assertIsNotNone(model.topic_model.mean.weight.grad)
        self.assertGreater(model.topic_model.mean.weight.grad.abs().sum().item(), 0)

    def test_present_phrase_requires_contiguous_tokens(self):
        self.assertTrue(is_present(("a", "b", "c"), ("b", "c")))
        self.assertFalse(is_present(("a", "b", "c"), ("a", "c")))

    def test_metrics_known_answer(self):
        metrics = evaluate_records([
            (["deep", "learning"], [["deep", "learning"], ["neural", "network"]],
             [["deep", "learning"], ["wrong"]]),
            (["graph"], [["graph"]], []),
        ], "StackExchange")["all"]
        self.assertAlmostEqual(metrics["P@1"], 0.5)
        self.assertAlmostEqual(metrics["R@1"], 0.25)
        self.assertAlmostEqual(metrics["F1@1"], 1 / 3)
        self.assertAlmostEqual(metrics["MAP@5"], 0.25)


if __name__ == "__main__":
    unittest.main()
