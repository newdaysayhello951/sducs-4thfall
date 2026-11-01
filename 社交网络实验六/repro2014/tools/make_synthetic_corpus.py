"""生成一个 RepLab 2013 格式的迷你合成语料，用于端到端验证「有正文」的通路。

真实 RepLab 2013 不提供推文正文，导致 term / semantic / hashtags / namedusers
四类特征无法计算。为了证明这些代码路径确实可用，这里造一个小语料：

  * 每个话题有专属关键词，同话题推文共享这些词
  * 时间上话题集中在各自窗口内
  * 部分推文共享 URL 与 hashtag

在这样的语料上，文本特征应当能把 SVM 准确率推到很高，HAC 也能还原话题。

用法::

    python -m tools.make_synthetic_corpus            # 输出到 data/synthetic
    python -m src.run_pipeline --data-root data/synthetic \
        --text-file data/synthetic/texts.tsv --pairs 6000 --folds 5 --cuts 20
"""

from __future__ import annotations

import csv
import random
from pathlib import Path
from typing import List

OUT = Path(__file__).resolve().parents[1] / "data" / "synthetic"

N_ENTITIES = 4
TOPICS_PER_ENTITY = 4
TWEETS_PER_TOPIC_TRAIN = 30
TWEETS_PER_TOPIC_TEST = 30

FILLER = ["really", "today", "people", "think", "going", "great", "about",
          "there", "would", "thing", "again", "still"]

TOPIC_WORDS = {
    "launch": ["launch", "unveil", "newmodel", "press", "event", "showroom"],
    "recall": ["recall", "defect", "safety", "repair", "notice", "service"],
    "sponsor": ["sponsor", "olympic", "athlete", "partnership", "campaign"],
    "finance": ["earnings", "quarter", "revenue", "profit", "investor", "shares"],
}


def _write_dat(path: Path, header: List[str], rows: List[List[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", quoting=csv.QUOTE_ALL)
        w.writerow(header)
        w.writerows(rows)


def main() -> int:
    rng = random.Random(7)
    OUT.mkdir(parents=True, exist_ok=True)

    tweet_info_cols = ["tweet_id", "author", "entity_id", "tweet_url", "language",
                       "timestamp", "urls", "extended_urls", "md5_extended_urls",
                       "is_near_duplicate_of"]
    gold_rows: List[List[str]] = []
    texts: List[List[str]] = []
    tweet_counter = 10_000_000

    for split, n_per_topic, t_base in (
        ("training", TWEETS_PER_TOPIC_TRAIN, 1_340_000_000),
        ("test", TWEETS_PER_TOPIC_TEST, 1_355_000_000),
    ):
        per_entity_info = {}
        for e in range(N_ENTITIES):
            ent_id = f"SYNTHD01E{e:03d}"
            rows = []
            for t_idx, (topic, words) in enumerate(TOPIC_WORDS.items()):
                url = f"http://example.com/{ent_id}/topic{t_idx}"
                for k in range(n_per_topic):
                    tweet_counter += 1
                    tid = str(tweet_counter)
                    # 话题词 + 填充词，词序打乱，保证不是简单复制
                    picked = rng.sample(words, k=min(4, len(words)))
                    body = picked + rng.sample(FILLER, k=4)
                    rng.shuffle(body)
                    tag = f"#{topic}" if k % 3 == 0 else ""
                    text = " ".join(body) + (" " + tag if tag else "")
                    author = f"user_{e}_{k % 7}"
                    ts = t_base + t_idx * 5_000 + k * 60
                    share_url = url if k % 4 == 0 else ""
                    rows.append([tid, author, ent_id, f"https://twitter.com/x/status/{tid}",
                                 "EN", str(ts), share_url, share_url, "", "-1"])
                    gold_rows.append([ent_id, tid, topic])
                    texts.append([tid, text])
            per_entity_info[ent_id] = rows
            _write_dat(OUT / split / "tweet_info" / f"{ent_id}.dat", tweet_info_cols, rows)

        _write_dat(OUT / split / "goldstandard" / "goldstandard_topic_detection.dat",
                   ["entity_id", "tweet_id", "topic"], gold_rows)
        gold_rows = []

    _write_dat(OUT / "entities" / "replab2013_entities.tsv",
               ["entity_id", "query", "entity_name", "domain", "homepage",
                "wikipedia_page_en", "wikipedia_page_es", "md5_homepage",
                "md5_wikipedia_page_en"],
               [[f"SYNTHD01E{e:03d}", f"entity{e}", f"Synthetic Entity {e}", "automotive",
                 "", "", "", "", ""] for e in range(N_ENTITIES)])

    with (OUT / "texts.tsv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["tweet_id", "text"])
        w.writerows(texts)

    print(f"合成语料已写入 {OUT}")
    print(f"  实体 {N_ENTITIES}，话题 {len(TOPIC_WORDS)}，推文 {len(texts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
