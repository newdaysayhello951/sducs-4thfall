"""Twitter 文本聚类：手写分词、词袋和 K-means，不使用现成机器学习实现。"""

from __future__ import annotations

import argparse
import csv
import json
import time
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix


def read_data(path: Path, limit: int | None = None) -> list[dict]:
    """数据文件是 JSON Lines，每行一条记录。"""
    records = []
    with path.open(encoding="utf-8-sig") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"第 {line_number} 行不是有效 JSON") from exc
            if not isinstance(row, dict):
                raise ValueError(f"第 {line_number} 行必须是 JSON 对象")
            records.append(row)
            if limit is not None and len(records) >= limit:
                break
    if not records:
        raise ValueError("数据文件没有记录")
    return records


def tokenize(text: str) -> list[str]:
    """按 README 要求直接按空白分词，并统一为小写。"""
    return text.lower().split()


def vectorize(
    texts: list[str], min_df: int = 2, max_features: int = 5000,
    normalize: bool = True,
) -> tuple[csr_matrix, list[str]]:
    """手写词袋：按文档频率筛词，再统计每篇文本的词频。

    SciPy 仅用于存储稀疏矩阵；没有使用 CountVectorizer 等向量化接口。
    """
    documents = [Counter(tokenize(text)) for text in texts]
    document_frequency = Counter()
    for counts in documents:
        document_frequency.update(counts.keys())
    vocabulary = sorted(
        (word for word, count in document_frequency.items() if count >= min_df),
        key=lambda word: (-document_frequency[word], word),
    )[:max_features]
    if not vocabulary:
        raise ValueError("筛选后词表为空，请减小 --min-df 或检查文本")
    word_index = {word: index for index, word in enumerate(vocabulary)}
    values, indices, offsets = [], [], [0]
    for counts in documents:
        for word, count in counts.items():
            if word in word_index:
                indices.append(word_index[word])
                values.append(float(count))
        offsets.append(len(values))
    matrix = csr_matrix(
        (np.asarray(values, dtype=np.float64), indices, offsets),
        shape=(len(texts), len(vocabulary)),
    )
    if normalize:
        lengths = np.sqrt(np.asarray(matrix.multiply(matrix).sum(axis=1)).ravel())
        scales = np.ones_like(lengths)
        np.divide(1.0, lengths, out=scales, where=lengths > 0)
        matrix = matrix.multiply(scales[:, None]).tocsr()
    return matrix, vocabulary


def assign_clusters(
    matrix: csr_matrix, centers: np.ndarray, batch_size: int,
) -> tuple[np.ndarray, np.ndarray]:
    """分批求平方欧氏距离，避免生成 样本数×簇数×词表大小 的数组。"""
    labels = np.empty(matrix.shape[0], dtype=np.int64)
    distances = np.empty(matrix.shape[0], dtype=np.float64)
    center_norms = np.einsum("ij,ij->i", centers, centers)
    for start in range(0, matrix.shape[0], batch_size):
        stop = min(start + batch_size, matrix.shape[0])
        block = matrix[start:stop]
        row_norms = np.asarray(block.multiply(block).sum(axis=1)).ravel()
        squared = row_norms[:, None] + center_norms[None, :] - 2 * (block @ centers.T)
        np.maximum(squared, 0, out=squared)
        nearest = squared.argmin(axis=1)
        labels[start:stop] = nearest
        distances[start:stop] = squared[np.arange(stop - start), nearest]
    return labels, distances


def initialize_centers(matrix: csr_matrix, k: int, rng: np.random.Generator) -> np.ndarray:
    """手写 K-means++：按到已选中心的最近距离平方进行抽样。"""
    n, dimensions = matrix.shape
    centers = np.empty((k, dimensions), dtype=np.float64)
    selected = np.zeros(n, dtype=bool)
    nearest = np.full(n, np.inf)
    norms = np.asarray(matrix.multiply(matrix).sum(axis=1)).ravel()
    index = int(rng.integers(n))
    for step in range(k):
        selected[index] = True
        centers[step] = matrix[index].toarray()[0]
        distances = norms + np.dot(centers[step], centers[step]) - 2 * (matrix @ centers[step])
        np.maximum(distances, 0, out=distances)
        nearest = np.minimum(nearest, distances)
        nearest[selected] = 0
        if step + 1 < k:
            total = nearest.sum()
            if total <= np.finfo(float).eps:
                index = int(rng.choice(np.flatnonzero(~selected)))
            else:
                index = int(rng.choice(n, p=nearest / total))
    return centers


def kmeans(
    matrix: csr_matrix, k: int, max_iter: int = 50, tol: float = 1e-4,
    seed: int = 42, batch_size: int = 1024, verbose: bool = True,
) -> dict:
    """Lloyd K-means：分配样本 -> 按簇求平均 -> 检查中心变化。"""
    if not 1 <= k <= matrix.shape[0]:
        raise ValueError("K 必须在 1 到有效样本数之间")
    if max_iter < 1 or batch_size < 1 or tol < 0:
        raise ValueError("迭代次数和批大小必须为正，容差不能为负")
    rng = np.random.default_rng(seed)
    centers = initialize_centers(matrix, k, rng)
    history = []
    converged = False
    for iteration in range(1, max_iter + 1):
        labels, distances = assign_clusters(matrix, centers, batch_size)
        counts = np.bincount(labels, minlength=k)
        membership = csr_matrix(
            (np.ones(matrix.shape[0]), (labels, np.arange(matrix.shape[0]))),
            shape=(k, matrix.shape[0]),
        )
        updated = (membership @ matrix).toarray()
        occupied = counts > 0
        updated[occupied] /= counts[occupied, None]
        # 空簇重新放在当前误差最大的样本上，下一轮重新分配。
        empty = np.flatnonzero(~occupied)
        if empty.size:
            farthest = np.argsort(-distances, kind="stable")[:empty.size]
            updated[empty] = matrix[farthest].toarray()
        shift = float(np.linalg.norm(updated - centers))
        relative_shift = shift / max(float(np.linalg.norm(centers)), 1e-12)
        history.append({
            "iteration": iteration, "inertia_before_update": float(distances.sum()),
            "relative_center_shift": relative_shift, "empty_clusters": int(empty.size),
        })
        if verbose:
            print(f"迭代 {iteration:02d}: SSE={distances.sum():.4f}, "
                  f"中心相对变化={relative_shift:.6f}, 空簇={empty.size}", flush=True)
        centers = updated
        if relative_shift <= tol:
            converged = True
            break
    # 最后一轮更新中心后，必须重新分配，确保输出标签与输出中心一致。
    labels, distances = assign_clusters(matrix, centers, batch_size)
    return {
        "labels": labels, "centers": centers, "distances": distances,
        "inertia": float(distances.sum()), "iterations": len(history),
        "converged": converged, "history": history,
    }


def evaluate(true_labels: list, predicted: np.ndarray) -> dict:
    """手写 ARI 和纯度；仅在聚类结束后使用真实标签。"""
    contingency = Counter(zip(true_labels, predicted.tolist()))
    true_counts = Counter(true_labels)
    predicted_counts = Counter(predicted.tolist())
    choose_two = lambda value: value * (value - 1) / 2
    pairs = choose_two(len(predicted))
    observed = sum(choose_two(value) for value in contingency.values())
    row_pairs = sum(choose_two(value) for value in true_counts.values())
    column_pairs = sum(choose_two(value) for value in predicted_counts.values())
    expected = row_pairs * column_pairs / pairs if pairs else 0.0
    denominator = (row_pairs + column_pairs) / 2 - expected
    ari = (observed - expected) / denominator if denominator else 1.0
    largest = Counter()
    for (_, cluster), size in contingency.items():
        largest[cluster] = max(largest[cluster], size)
    return {"adjusted_rand_index": float(ari),
            "purity": sum(largest.values()) / len(predicted)}


def save_results(
    output: Path, records: list[dict], texts: list[str], valid_indices: np.ndarray,
    vocabulary: list[str], result: dict, metrics: dict,
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    all_labels = np.full(len(records), -1, dtype=np.int64)
    all_labels[valid_indices] = result["labels"]
    with (output / "assignments.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["row_index", "tweetId", "clusterNo", "predicted_cluster", "textCleaned"])
        for index, (row, text) in enumerate(zip(records, texts)):
            writer.writerow([index, row.get("tweetId", ""), row.get("clusterNo", ""),
                             int(all_labels[index]), text])
    summaries = []
    for cluster, center in enumerate(result["centers"]):
        members = np.flatnonzero(result["labels"] == cluster)
        top = np.argsort(-center, kind="stable")[:10]
        representatives = members[np.argsort(result["distances"][members])[:3]]
        summaries.append({
            "cluster": cluster, "size": int(members.size),
            "keywords": [{"word": vocabulary[i], "weight": float(center[i])}
                         for i in top if center[i] > 0],
            "representatives": [
                {"row_index": int(valid_indices[i]), "text": texts[valid_indices[i]]}
                for i in representatives
            ],
        })
    artifacts = {
        "clusters.json": summaries, "metrics.json": metrics,
        "history.json": result["history"], "vocabulary.json": vocabulary,
    }
    for filename, content in artifacts.items():
        (output / filename).write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
    np.save(output / "centers.npy", result["centers"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path(__file__).with_name("Twitter_data"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("results"))
    parser.add_argument("--k", type=int, default=220, help="聚类数，默认 220；不从标签自动推断")
    parser.add_argument("--max-iter", type=int, default=50)
    parser.add_argument("--tol", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-df", type=int, default=2, help="词至少出现在多少篇文本中")
    parser.add_argument("--max-features", type=int, default=5000)
    parser.add_argument("--batch-size", type=int, default=1024)
    parser.add_argument("--limit", type=int, help="只读取前 N 条，用于快速试运行")
    parser.add_argument("--no-normalize", action="store_true", help="使用原始词频，不做 L2 归一化")
    args = parser.parse_args()
    if min(args.k, args.max_iter, args.min_df, args.max_features, args.batch_size) < 1:
        parser.error("K、迭代次数、文档频率、词表大小和批大小必须为正整数")
    if not np.isfinite(args.tol) or args.tol < 0 or args.seed < 0:
        parser.error("容差必须是有限非负数，随机种子必须为非负整数")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit 必须为正整数")
    start = time.perf_counter()
    records = read_data(args.data, args.limit)
    texts = [str(row.get("textCleaned") or row.get("text") or "") for row in records]
    matrix, vocabulary = vectorize(texts, args.min_df, args.max_features, not args.no_normalize)
    valid_indices = np.flatnonzero(np.asarray(matrix.getnnz(axis=1)).ravel() > 0)
    matrix = matrix[valid_indices]
    if args.k > len(valid_indices):
        parser.error(f"K={args.k} 超过非零文本向量数 {len(valid_indices)}")
    print(f"读取 {len(records)} 条，有效向量 {matrix.shape[0]} 条，词表 {matrix.shape[1]} 词，"
          f"K={args.k}", flush=True)
    result = kmeans(matrix, args.k, args.max_iter, args.tol, args.seed, args.batch_size)
    metrics = {
        "records": len(records), "clustered_records": len(valid_indices),
        "zero_vector_records": len(records) - len(valid_indices),
        "vocabulary_size": len(vocabulary), "k": args.k,
        "nonempty_clusters": int(np.unique(result["labels"]).size),
        "iterations": result["iterations"], "converged": result["converged"],
        "inertia": result["inertia"],
        "parameters": {key: str(value) if isinstance(value, Path) else value
                       for key, value in vars(args).items()},
    }
    # 无真实标签的记录不进入外部评价，仍照常参与无监督聚类。
    evaluated = [i for i, source in enumerate(valid_indices)
                 if records[source].get("clusterNo") is not None]
    metrics["evaluated_records"] = len(evaluated)
    if evaluated:
        true_labels = [records[valid_indices[i]]["clusterNo"] for i in evaluated]
        metrics.update(evaluate(true_labels, result["labels"][evaluated]))
    metrics["elapsed_seconds_before_export"] = time.perf_counter() - start
    save_results(args.output, records, texts, valid_indices, vocabulary, result, metrics)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"结果已保存至 {args.output.resolve()}")


if __name__ == "__main__":
    main()
