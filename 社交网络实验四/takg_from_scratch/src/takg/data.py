from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

import torch
from torch.utils.data import Dataset

from .utils import ROOT, atomic_torch_save, save_json


PAD, UNK, BOS, EOS = "<pad>", "<unk>", "<bos>", "<eos>"
SPECIALS = [PAD, UNK, BOS, EOS]
ENGLISH_STOPWORDS = set("a an and are as at be by for from has have he in is it its of on or that the this to was were will with you your i me my we our they their not but if so than then can could should would do does did".split())
CHINESE_STOPWORDS = set("的 了 和 是 在 我 有 就 不 人 都 一 一个 上 也 很 到 说 要 去 你 会 着 没有 看 好 自己 这".split())


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_parallel(folder: Path, split: str, source_limit: int = 0):
    sources = (folder / f"{split}_src.txt").read_text(encoding="utf-8").splitlines()
    targets = (folder / f"{split}_trg.txt").read_text(encoding="utf-8").splitlines()
    if len(sources) != len(targets):
        raise ValueError(f"{split} source/target line counts differ")
    if source_limit:
        sources, targets = sources[:source_limit], targets[:source_limit]
    records = []
    for line_number, (source, target) in enumerate(zip(sources, targets), 1):
        source_tokens = source.strip().split()
        target_phrases = [phrase.strip().split() for phrase in target.split(";") if phrase.strip()]
        if not source_tokens or not target_phrases:
            raise ValueError(f"Empty record in {split}, line {line_number}")
        records.append((source_tokens, target_phrases))
    return records


@dataclass
class Vocabulary:
    token_to_id: dict
    id_to_token: list

    def __len__(self):
        return len(self.id_to_token)

    def encode(self, tokens):
        unknown = self.token_to_id[UNK]
        return [self.token_to_id.get(token, unknown) for token in tokens]


def build_vocabulary(train_records, maximum_size):
    counts = Counter(token for source, targets in train_records for token in source)
    counts.update(token for _, targets in train_records for phrase in targets for token in phrase)
    tokens = [token for token, _ in counts.most_common(maximum_size - len(SPECIALS)) if token not in SPECIALS]
    id_to_token = SPECIALS + tokens
    return Vocabulary({token: index for index, token in enumerate(id_to_token)}, id_to_token), counts


def useful_bow_token(token, dataset):
    if token in SPECIALS or len(token) <= 1:
        return False
    if dataset == "Weibo":
        return token not in CHINESE_STOPWORDS and any("\u4e00" <= char <= "\u9fff" or char.isalpha() for char in token)
    return token.lower() not in ENGLISH_STOPWORDS and bool(re.search(r"[A-Za-z]", token))


def build_bow_vocabulary(train_records, dataset, maximum_size, minimum_frequency):
    counts = Counter(token for source, _ in train_records for token in source if useful_bow_token(token, dataset))
    tokens = [token for token, count in counts.most_common() if count >= minimum_frequency][:maximum_size]
    return Vocabulary({token: index for index, token in enumerate(tokens)}, tokens)


class TrainingDataset(Dataset):
    def __init__(self, records, word_vocab, bow_vocab, max_source_length, max_target_length):
        self.items = []
        for source, phrases in records:
            source = source[:max_source_length]
            for phrase in phrases:
                self.items.append(self._encode(source, phrase[:max_target_length], word_vocab, bow_vocab))

    @staticmethod
    def _encode(source, target, word_vocab, bow_vocab):
        vocabulary_size = len(word_vocab)
        source_ids = word_vocab.encode(source)
        extended_source = []
        oov_tokens = []
        oov_to_index = {}
        for token, normal_id in zip(source, source_ids):
            if normal_id != word_vocab.token_to_id[UNK]:
                extended_source.append(normal_id)
            else:
                if token not in oov_to_index:
                    oov_to_index[token] = len(oov_tokens)
                    oov_tokens.append(token)
                extended_source.append(vocabulary_size + oov_to_index[token])
        target_ids, extended_target = [], []
        for token in target + [EOS]:
            normal_id = word_vocab.token_to_id.get(token, word_vocab.token_to_id[UNK])
            target_ids.append(normal_id)
            extended_target.append(vocabulary_size + oov_to_index[token] if normal_id == word_vocab.token_to_id[UNK] and token in oov_to_index else normal_id)
        bow_counts = Counter(bow_vocab.token_to_id[token] for token in source if token in bow_vocab.token_to_id)
        return {"source": source_ids, "extended_source": extended_source, "target": target_ids,
                "extended_target": extended_target, "bow": list(bow_counts.items()), "oov_tokens": oov_tokens}

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        return self.items[index]


class InferenceDataset(Dataset):
    def __init__(self, records, word_vocab, bow_vocab, max_source_length):
        self.items = []
        for source, targets in records:
            source = source[:max_source_length]
            encoded = TrainingDataset._encode(source, [], word_vocab, bow_vocab)
            encoded["source_tokens"] = source
            encoded["targets"] = targets
            self.items.append(encoded)

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        return self.items[index]


def collate_training(items, padding_id, bow_size):
    batch_size = len(items)
    source_lengths = torch.tensor([len(item["source"]) for item in items], dtype=torch.long)
    target_lengths = torch.tensor([len(item["target"]) for item in items], dtype=torch.long)
    max_source, max_target = int(source_lengths.max()), int(target_lengths.max())
    source = torch.full((batch_size, max_source), padding_id, dtype=torch.long)
    extended_source = torch.full_like(source, padding_id)
    target = torch.full((batch_size, max_target), padding_id, dtype=torch.long)
    extended_target = torch.full_like(target, padding_id)
    source_mask = torch.zeros((batch_size, max_source), dtype=torch.bool)
    target_mask = torch.zeros((batch_size, max_target), dtype=torch.bool)
    bow = torch.zeros((batch_size, bow_size), dtype=torch.float)
    for row, item in enumerate(items):
        sl, tl = len(item["source"]), len(item["target"])
        source[row, :sl] = torch.tensor(item["source"])
        extended_source[row, :sl] = torch.tensor(item["extended_source"])
        target[row, :tl] = torch.tensor(item["target"])
        extended_target[row, :tl] = torch.tensor(item["extended_target"])
        source_mask[row, :sl] = True
        target_mask[row, :tl] = True
        for index, count in item["bow"]:
            bow[row, index] = count
    return {"source": source, "source_lengths": source_lengths, "source_mask": source_mask,
            "extended_source": extended_source, "target": target, "extended_target": extended_target,
            "target_mask": target_mask, "bow": bow, "oov_tokens": [item["oov_tokens"] for item in items]}


def prepare_data(config):
    data_folder = ROOT / "data" / config.dataset
    cache_folder = ROOT / "cache" / config.dataset
    cache_folder.mkdir(parents=True, exist_ok=True)
    limits = {"train": config.train_limit, "valid": config.valid_limit, "test": config.test_limit}
    records = {split: read_parallel(data_folder, split, limits[split]) for split in ("train", "valid", "test")}
    word_vocab, counts = build_vocabulary(records["train"], config.vocabulary_size)
    bow_vocab = build_bow_vocabulary(records["train"], config.dataset, config.bow_vocabulary_size, config.min_bow_frequency)
    if not bow_vocab.id_to_token:
        raise ValueError("The BoW vocabulary is empty")
    train = TrainingDataset(records["train"], word_vocab, bow_vocab, config.max_source_length, config.max_target_length)
    valid = TrainingDataset(records["valid"], word_vocab, bow_vocab, config.max_source_length, config.max_target_length)
    test = InferenceDataset(records["test"], word_vocab, bow_vocab, config.max_source_length)
    payload = {"word_vocab": word_vocab, "bow_vocab": bow_vocab, "train": train, "valid": valid, "test": test}
    cache_path = cache_folder / ("smoke.pt" if config.smoke else "full.pt")
    atomic_torch_save(payload, cache_path)
    manifest = {"dataset": config.dataset, "records": {key: len(value) for key, value in records.items()},
                "training_pairs": len(train), "word_vocabulary": len(word_vocab), "bow_vocabulary": len(bow_vocab),
                "files": {path.name: file_sha256(path) for path in sorted(data_folder.glob("*.txt"))}}
    save_json(manifest, cache_path.with_suffix(".json"))
    return cache_path, manifest


def load_data(config):
    cache_path = ROOT / "cache" / config.dataset / ("smoke.pt" if config.smoke else "full.pt")
    if not cache_path.exists():
        prepare_data(config)
    with cache_path.open("rb") as stream:
        return torch.load(stream, map_location="cpu", weights_only=False)
