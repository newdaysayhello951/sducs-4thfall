from pathlib import Path

import numpy as np
from nltk.stem import PorterStemmer

from .data import read_parallel
from .utils import ROOT, save_json


STEMMER = PorterStemmer()


def normalize_phrase(tokens, dataset):
    lowered = [token.lower() for token in tokens]
    return tuple(STEMMER.stem(token) for token in lowered) if dataset != "Weibo" else tuple(lowered)


def unique_phrases(phrases, dataset):
    return list(dict.fromkeys(normalize_phrase(phrase, dataset) for phrase in phrases if phrase))


def is_present(source, phrase):
    return any(tuple(source[start:start + len(phrase)]) == phrase for start in range(len(source) - len(phrase) + 1))


def average_precision(matches, target_count, k=5):
    return sum(sum(matches[:index + 1]) / (index + 1) for index in range(min(k, len(matches))) if matches[index]) / target_count


def evaluate_records(records, dataset):
    rows = {group: [] for group in ("all", "present", "absent")}
    for source_tokens, target_phrases, predicted_phrases in records:
        source = normalize_phrase(source_tokens, dataset)
        targets = unique_phrases(target_phrases, dataset)
        predictions = unique_phrases(predicted_phrases, dataset)
        for group in rows:
            wanted = None if group == "all" else group == "present"
            group_targets = targets if wanted is None else [phrase for phrase in targets if is_present(source, phrase) == wanted]
            group_predictions = predictions if wanted is None else [phrase for phrase in predictions if is_present(source, phrase) == wanted]
            if not group_targets:
                continue
            matches = [int(phrase in group_targets) for phrase in group_predictions]
            result = {"AP@5": average_precision(matches, len(group_targets), 5)}
            for k in (1, 3, 5):
                correct = sum(matches[:k])
                precision = correct / min(k, len(group_predictions)) if group_predictions else 0.0
                recall = correct / len(group_targets)
                result[f"P@{k}"] = precision
                result[f"R@{k}"] = recall
            rows[group].append(result)
    summary = {}
    for group, group_rows in rows.items():
        if not group_rows:
            summary[group] = {"count": 0}
            continue
        result = {name: float(np.mean([row[name] for row in group_rows])) for name in group_rows[0]}
        for k in (1, 3, 5):
            precision, recall = result[f"P@{k}"], result[f"R@{k}"]
            result[f"F1@{k}"] = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        result["MAP@5"] = result.pop("AP@5")
        summary[group] = {"count": len(group_rows), **result}
    return summary


def evaluate_prediction_file(config, prediction_path):
    records = read_parallel(ROOT / "data" / config.dataset, "test", config.test_limit)
    prediction_lines = Path(prediction_path).read_text(encoding="utf-8").splitlines()
    if len(prediction_lines) != len(records):
        raise ValueError(f"Expected {len(records)} prediction lines, found {len(prediction_lines)}")
    predictions = [[phrase.split() for phrase in line.split(";") if phrase.strip()] for line in prediction_lines]
    metrics = evaluate_records(
        ((source, targets, predicted) for (source, targets), predicted in zip(records, predictions)),
        config.dataset,
    )
    result = {"dataset": config.dataset, "run_name": config.run_name, "smoke": config.smoke, "metrics": metrics}
    save_json(result, ROOT / "runs" / config.run_name / "metrics.json")
    return result
