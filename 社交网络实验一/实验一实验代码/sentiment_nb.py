"""IMDb sentiment classification with a manually implemented multinomial NB.

Train: python sentiment_nb.py train
Predict: python sentiment_nb.py predict --text "This movie was wonderful"
Only the Python standard library is required.
"""

import argparse
from collections import Counter
import csv
import html
import json
import math
from pathlib import Path
import re
import tarfile
import time


TOKEN = re.compile(r"[a-z]+(?:'[a-z]+)?")
HTML_TAG = re.compile(r"<[^>]+>")
CLASSES = ("neg", "pos")


def tokenize(text):
    return TOKEN.findall(HTML_TAG.sub(" ", html.unescape(text)).lower())


def documents(root, split, archive_path=None):
    if archive_path is not None:
        with tarfile.open(archive_path, 'r:gz') as archive:
            for member in archive:
                parts = Path(member.name).parts
                if (member.isfile() and len(parts) == 4
                        and parts[0] == 'aclImdb' and parts[1] == split
                        and parts[2] in CLASSES and parts[3].endswith('.txt')):
                    with archive.extractfile(member) as handle:
                        tokens = tokenize(handle.read().decode('utf-8'))
                    yield root / split / parts[2] / parts[3], parts[2], tokens
        return
    for label in CLASSES:
        directory = root / split / label
        files = sorted(directory.glob("*.txt"))
        if not files:
            raise ValueError(f"No reviews found in {directory}")
        for path in files:
            yield path, label, tokenize(path.read_text(encoding="utf-8"))


class MultinomialNB:
    """P(c) and smoothed P(word|c) estimated directly from training counts."""

    def __init__(self, alpha=1.0):
        if not math.isfinite(alpha) or alpha <= 0:
            raise ValueError("alpha must be finite and positive")
        self.alpha = alpha
        self.log_prior = {}
        self.log_prob = {}

    def fit(self, rows):
        word_counts = {label: Counter() for label in CLASSES}
        doc_counts = Counter()
        for index, (_, label, tokens) in enumerate(rows, 1):
            word_counts[label].update(tokens)
            doc_counts[label] += 1
            if index % 5000 == 0:
                print(f"Training: {index} reviews read", flush=True)
        if any(doc_counts[label] == 0 for label in CLASSES):
            raise ValueError("Both classes must have training documents")
        vocabulary = sorted(set(word_counts['neg']) | set(word_counts['pos']))
        if not vocabulary:
            raise ValueError("Training vocabulary is empty")
        total_docs = sum(doc_counts.values())
        self.log_prior = {
            label: math.log(doc_counts[label] / total_docs) for label in CLASSES
        }
        denominators = {
            label: sum(word_counts[label].values()) + self.alpha * len(vocabulary)
            for label in CLASSES
        }
        self.log_prob = {
            word: [math.log((word_counts[label][word] + self.alpha)
                            / denominators[label]) for label in CLASSES]
            for word in vocabulary
        }
        return dict(doc_counts)

    def predict(self, tokens):
        scores = [self.log_prior[label] for label in CLASSES]
        for word, count in Counter(tokens).items():
            probabilities = self.log_prob.get(word)
            # Ignore words absent from the training vocabulary.
            if probabilities is not None:
                for index in range(len(CLASSES)):
                    scores[index] += count * probabilities[index]
        return CLASSES[max(range(len(CLASSES)), key=lambda index: scores[index])]

    def save(self, path):
        path.write_text(json.dumps({
            "alpha": self.alpha, "classes": CLASSES,
            "log_prior": self.log_prior, "log_prob": self.log_prob,
        }), encoding="utf-8")

    @classmethod
    def load(cls, path):
        data = json.loads(path.read_text(encoding="utf-8"))
        if tuple(data['classes']) != CLASSES:
            raise ValueError("Unsupported class order")
        model = cls(data['alpha'])
        model.log_prior = data['log_prior']
        model.log_prob = data['log_prob']
        return model


def train(args):
    args.output.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    model = MultinomialNB(args.alpha)
    training_counts = model.fit(documents(args.data, "train", args.archive))
    training_seconds = time.perf_counter() - started
    model_path = args.output / "model.json"
    model.save(model_path)
    # Evaluate the persisted model to verify that it can be loaded for reuse.
    model = MultinomialNB.load(model_path)
    evaluation_started = time.perf_counter()
    confusion = {actual: {predicted: 0 for predicted in CLASSES} for actual in CLASSES}
    with (args.output / "predictions.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["file", "actual", "predicted", "correct"])
        for index, (path, actual, tokens) in enumerate(documents(args.data, "test", args.archive), 1):
            predicted = model.predict(tokens)
            confusion[actual][predicted] += 1
            writer.writerow([path.relative_to(args.data).as_posix(), actual,
                             predicted, int(actual == predicted)])
            if index % 5000 == 0:
                print(f"Evaluation: {index} reviews predicted", flush=True)
    total = sum(sum(row.values()) for row in confusion.values())
    correct = sum(confusion[label][label] for label in CLASSES)
    metrics = {
        "algorithm": "Handwritten multinomial Naive Bayes",
        "features": "Unigram token counts; vocabulary fitted on train only",
        "alpha": args.alpha,
        "data_source": str(args.archive if args.archive else args.data),
        "train_counts": training_counts,
        "vocabulary_size": len(model.log_prob),
        "test_count": total, "correct": correct, "accuracy": correct / total,
        "confusion_matrix_actual_then_predicted": confusion,
        "training_seconds": round(training_seconds, 3),
        "evaluation_seconds": round(time.perf_counter() - evaluation_started, 3),
    }
    (args.output / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(metrics, indent=2, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    training = commands.add_parser("train")
    training.add_argument("--data", type=Path, default=Path("aclImdb"))
    training.add_argument("--output", type=Path, default=Path("results"))
    training.add_argument("--alpha", type=float, default=1.0)
    training.add_argument("--archive", type=Path,
                          help="Read the same reviews sequentially from tar.gz for faster I/O")
    prediction = commands.add_parser("predict")
    prediction.add_argument("--model", type=Path, default=Path("results/model.json"))
    prediction.add_argument("--text", required=True)
    args = parser.parse_args()
    if args.command == "train":
        train(args)
    else:
        model = MultinomialNB.load(args.model)
        print(model.predict(tokenize(args.text)))


if __name__ == "__main__":
    main()
