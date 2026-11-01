"""运行摘要实验并保存可复查的逐篇输出、汇总和案例。"""
import argparse
import csv
import json
import platform
import random
import time
from pathlib import Path

import numpy as np
from load_data import load_stories
from metrics import evaluate, corpus_bleu
from textrank import summarize, split_sentences, tokenize

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=ROOT/'data/cnn_stories_tokenized')
    parser.add_argument('--output', type=Path, default=ROOT/'results')
    parser.add_argument('--limit', type=int, default=0, help='0 表示全部；正数表示固定种子随机抽样')
    parser.add_argument('--sentences', type=int, default=3)
    parser.add_argument('--damping', type=float, default=.85)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--study', action='store_true', help='增加句数和阻尼系数对照（探索性分析，不用于声称独立测试效果）')
    args = parser.parse_args()
    if args.limit < 0 or args.sentences < 1 or not 0 <= args.damping < 1:
        parser.error('limit >= 0, sentences >= 1, 0 <= damping < 1')
    if not args.data.is_dir():
        parser.error(f'Data directory not found: {args.data}')
    loaded = load_stories(args.data)
    skipped = [x['id'] for x in loaded if not tokenize(x['story']) or not tokenize(' '.join(x['highlights']))]
    invalid = set(skipped)
    stories = [x for x in loaded if x['id'] not in invalid]
    if args.limit:
        stories = random.Random(args.seed).sample(stories, min(args.limit, len(stories)))
    if not stories:
        parser.error('No valid stories')
    configs = [(f'lead-{args.sentences}', 'lead', args.sentences, args.damping),
               ('textrank-overlap', 'overlap', args.sentences, args.damping),
               ('textrank-tfidf', 'tfidf', args.sentences, args.damping)]
    if args.study:
        for k in (1, 2, 3, 4, 5):
            if k != args.sentences:
                configs.extend([(f'overlap-k{k}', 'overlap', k, args.damping), (f'lead-{k}', 'lead', k, args.damping)])
        for d in (.70, .95):
            if d != args.damping:
                configs.append((f'overlap-d{d}', 'overlap', args.sentences, d))
    args.output.mkdir(parents=True, exist_ok=True)
    config = {**vars(args), 'data': str(args.data.resolve()), 'output': str(args.output.resolve()),
              'python': platform.python_version(), 'numpy': np.__version__, 'files_found': len(loaded),
              'evaluated': len(stories), 'skipped_ids': skipped,
              'reference': 'all highlights joined into one reference',
              'metrics': 'lowercase word tokens; no stemming or stopword removal; macro ROUGE P/R/F1; whole-summary LCS; corpus BLEU-4 unsmoothed; scale 0..1',
              'configs': configs}
    (args.output/'config.json').write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding='utf-8')
    rows, examples = [], []
    with (args.output/'predictions.jsonl').open('w', encoding='utf-8') as output:
        for name, method, k, damping in configs:
            evaluations, elapsed, iterations, failures, lengths = [], [], [], 0, []
            for index, item in enumerate(stories):
                start = time.perf_counter()
                if method == 'lead':
                    sentences = split_sentences(item['story'])
                    result = {'summary': ' '.join(sentences[:k]), 'indices': list(range(min(k, len(sentences)))), 'iterations': 0, 'converged': True}
                else:
                    result = summarize(item['story'], k, method, damping)
                duration = time.perf_counter()-start
                reference = ' '.join(item['highlights'])
                scores = evaluate(result['summary'], reference)
                evaluations.append(scores)
                elapsed.append(duration)
                iterations.append(result['iterations'])
                failures += not result['converged']
                lengths.append(len(tokenize(result['summary'])))
                record = {'id': item['id'], 'method': name, **result, 'reference': reference, 'metrics': scores, 'seconds': duration}
                output.write(json.dumps(record, ensure_ascii=False)+'\n')
                if index < 3:
                    examples.append(record)
                if (index+1) % 500 == 0:
                    print(f'{name}: {index+1}/{len(stories)}', flush=True)
            row = {'method': name, 'articles': len(stories)}
            for metric in ('rouge1', 'rouge2', 'rougeL'):
                for stat in ('precision', 'recall', 'f1'):
                    row[f'{metric}_{stat}'] = float(np.mean([e[metric][stat] for e in evaluations]))
            row.update(bleu4=corpus_bleu([e['bleu_counts'] for e in evaluations]),
                       mean_words=float(np.mean(lengths)), mean_seconds=float(np.mean(elapsed)),
                       mean_iterations=float(np.mean(iterations)), nonconverged=failures)
            rows.append(row)
            print(json.dumps(row), flush=True)
    with (args.output/'metrics.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    stats = {'articles': len(stories), 'mean_story_words': float(np.mean([len(tokenize(x['story'])) for x in stories])),
             'mean_reference_words': float(np.mean([len(tokenize(' '.join(x['highlights']))) for x in stories]))}
    (args.output/'dataset_stats.json').write_text(json.dumps(stats, indent=2), encoding='utf-8')
    report = ['# 实验结果', '', f'实际评测 {len(stories)} 篇；无效文件 {len(skipped)} 篇。',
              '所有分数范围 0–1；ROUGE 为逐篇 F1 的平均值；BLEU 为语料级 BLEU-4。', '',
              '| 方法 | ROUGE-1 | ROUGE-2 | ROUGE-L | BLEU-4 | 平均摘要词数 | 平均耗时/秒 |',
              '|---|---:|---:|---:|---:|---:|---:|']
    for r in rows:
        report.append(f"| {r['method']} | {r['rouge1_f1']:.4f} | {r['rouge2_f1']:.4f} | {r['rougeL_f1']:.4f} | {r['bleu4']:.4f} | {r['mean_words']:.1f} | {r['mean_seconds']:.5f} |")
    report.extend(['', '## 结果解读', '',
        '相同句数仍可能产生不同词数，因此应结合摘要长度解读指标。Lead 基线利用新闻开头的信息；图排序偏向与其他句子共享词汇的句子，不能保证抓住关键事件。',
        '本次运行属于固定配置评测；参数扫描属于同一批数据上的探索性分析，没有训练或独立调参测试划分，不能作为调参后的独立测试结论。',
        'ROUGE/BLEU 衡量词面重合，不能直接判断事实正确性和指代连贯性。ROUGE-BE 未实现。', '', '## 固定案例（输入顺序前三篇）'])
    for e in examples:
        report.extend(['', f"### {e['id']} / {e['method']}", '', '参考摘要：'+e['reference'], '',
                       '输出摘要：'+e['summary'], '', f"原文句子下标（从 0 开始）：{e['indices']}"])
    (args.output/'report.md').write_text('\n'.join(report), encoding='utf-8')
    print(f'Results saved to {args.output.resolve()}')


if __name__ == '__main__':
    main()
