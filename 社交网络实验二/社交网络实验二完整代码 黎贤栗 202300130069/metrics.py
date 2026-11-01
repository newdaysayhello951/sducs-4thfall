"""自实现评测：小写词元，无停用词过滤/词干化，分数均为 0~1。
ROUGE-L 使用整个摘要的 LCS，不是 Lsum；BLEU 固定四阶、无平滑。
不宣称与 sumeval 的默认配置分数一致。
"""
import math
from collections import Counter
from textrank import tokenize


def ngrams(words, n):
    return Counter(tuple(words[i:i+n]) for i in range(len(words)-n+1))


def prf(matches, predicted, reference):
    p = matches/predicted if predicted else 0.0
    r = matches/reference if reference else 0.0
    return {'precision': p, 'recall': r, 'f1': 2*p*r/(p+r) if p+r else 0.0}


def lcs_length(a, b):
    if len(a) < len(b):
        a, b = b, a
    previous = [0]*(len(b)+1)
    for x in a:
        current = [0]
        for j, y in enumerate(b, 1):
            current.append(previous[j-1]+1 if x == y else max(previous[j], current[-1]))
        previous = current
    return previous[-1]


def evaluate(summary, reference):
    predicted, target = tokenize(summary), tokenize(reference)
    result, matches, totals = {}, [], []
    for n in range(1, 5):
        p, r = ngrams(predicted, n), ngrams(target, n)
        matched = sum((p & r).values())
        matches.append(matched)
        totals.append(sum(p.values()))
        if n <= 2:
            result[f'rouge{n}'] = prf(matched, sum(p.values()), sum(r.values()))
    result['rougeL'] = prf(lcs_length(predicted, target), len(predicted), len(target))
    result['bleu_counts'] = {'matches': matches, 'totals': totals,
                             'predicted_length': len(predicted), 'reference_length': len(target)}
    return result


def corpus_bleu(counts):
    matches = [sum(c['matches'][i] for c in counts) for i in range(4)]
    totals = [sum(c['totals'][i] for c in counts) for i in range(4)]
    length = sum(c['predicted_length'] for c in counts)
    reference = sum(c['reference_length'] for c in counts)
    if not length or any(m == 0 or t == 0 for m, t in zip(matches, totals)):
        return 0.0
    return math.exp(min(0, 1-reference/length) + sum(math.log(m/t) for m, t in zip(matches, totals))/4)
