"""手写句子图与 PageRank；仅依赖 NumPy 的基础数组运算。"""
import math
import re
from collections import Counter
import numpy as np

STOPWORDS = set('a an the and or but if of at by for with about to from in out on off over under then there when where how all any both each more most other some no not only so than too very can will do does did is am are was were be been being have has had i me my we our you your he him his she her it its they them their this that these those as'.split())


def tokenize(text, remove_stopwords=False):
    words = re.findall(r"[a-z0-9]+(?:'[a-z]+)?", text.lower())
    return [w for w in words if w not in STOPWORDS] if remove_stopwords else words


def split_sentences(text):
    text = text.replace('-LRB-', '(').replace('-RRB-', ')')
    text = re.sub(r'\b(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|St|vs|etc)\.', lambda m: m[0].replace('.', '\uE000'), text, flags=re.I)
    text = re.sub(r'\b[A-Z]\.(?=\s*[A-Z])', lambda m: m[0].replace('.', '\uE000'), text)
    chunks = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"\x27(])|\n+', text)
    return [s.replace('\uE000', '.').strip() for s in chunks if tokenize(s)]


def similarity_matrix(sentences, method='overlap'):
    if method not in {'overlap', 'tfidf'}:
        raise ValueError('Unknown similarity method')
    bags = [Counter(tokenize(s, True)) for s in sentences]
    n = len(bags)
    weights = np.zeros((n, n), dtype=float)
    if method == 'tfidf':
        df = Counter(w for bag in bags for w in bag)
        vectors = [{w: count * (math.log((1+n)/(1+df[w]))+1) for w, count in bag.items()} for bag in bags]
        norms = [math.sqrt(sum(v*v for v in vec.values())) for vec in vectors]
    for i in range(n):
        for j in range(i+1, n):
            common = bags[i].keys() & bags[j].keys()
            if method == 'overlap':
                denominator = math.log(1+sum(bags[i].values())) + math.log(1+sum(bags[j].values()))
                score = len(common)/denominator if denominator else 0.0
            else:
                denominator = norms[i]*norms[j]
                score = sum(vectors[i][w]*vectors[j][w] for w in common)/denominator if denominator else 0.0
            weights[i, j] = weights[j, i] = score
    return weights


def pagerank(weights, damping=0.85, tolerance=1e-6, max_iterations=200):
    if not 0 <= damping < 1 or tolerance <= 0 or max_iterations < 1:
        raise ValueError('Invalid PageRank parameters')
    weights = np.asarray(weights, dtype=float)
    if weights.ndim != 2 or weights.shape[0] != weights.shape[1] or not np.isfinite(weights).all() or (weights < 0).any():
        raise ValueError('Weights must be a finite nonnegative square matrix')
    n = len(weights)
    if n == 0:
        return np.array([]), 0, True
    row_sums = weights.sum(axis=1)
    transition = np.divide(weights, row_sums[:, None], out=np.zeros_like(weights), where=row_sums[:, None] != 0)
    transition[row_sums == 0] = 1/n
    scores = np.full(n, 1/n)
    for iteration in range(1, max_iterations+1):
        updated = (1-damping)/n + damping*np.einsum('ij,i->j', transition, scores)
        error = np.abs(updated-scores).sum()
        scores = updated
        if error < tolerance:
            return scores, iteration, True
    return scores, max_iterations, False


def summarize(text, sentence_count=3, method='overlap', damping=0.85):
    if sentence_count < 1:
        raise ValueError('sentence_count must be positive')
    sentences = split_sentences(text)
    scores, iterations, converged = pagerank(similarity_matrix(sentences, method), damping)
    chosen = sorted(sorted(range(len(sentences)), key=lambda i: (-scores[i], i))[:sentence_count])
    return {'summary': ' '.join(sentences[i] for i in chosen), 'indices': chosen,
            'scores': scores.tolist(), 'iterations': iterations, 'converged': converged,
            'sentence_count': len(sentences)}
