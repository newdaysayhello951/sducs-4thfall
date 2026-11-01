"""把 HumAID 转成 RepLab 2013 的目录格式，作为「有正文」的替代语料。

为什么要做这件事
----------------
RepLab 2013 只发 tweet id、不发正文，导致论文 13 个特征里有 8 个算不出来。
为了验证文本特征通路在**真实推文**上确实有效，这里引入 HumAID：

    HumAID (Alam et al. 2021) — 41,152 条人工标注英文推文，覆盖 11 场自然灾害，
    每条带 tweet_id / tweet_text / class_label，且**直接提供正文**。

映射关系（注意：这是结构类比，不是同一个任务）：

    RepLab 2013          HumAID
    ------------------   --------------------------
    entity（实体）        event（灾害事件）
    topic（话题）         humanitarian class（人道主义信息类别）
    tweet 正文             tweet_text（有）
    时间戳                twitter snowflake id 还原
    author               无此字段（该特征退化为常数）
    urls                 从正文正则抽取
    hashtags / @提及      从正文正则抽取

HumAID 的类别是「信息类型」而非 RepLab 那种「具体事件话题」，两者语义不同。
因此本实验**不能**用来复现论文的数字，只能用来回答一个问题：
「补齐正文之后，terms / hashtags / namedusers 这些特征是不是真的能把相似度学习拉起来？」

用法::

    python -m tools.import_humaid
    python -m src.run_pipeline --data-root data/humaid \
        --text-file data/humaid/texts.tsv --pairs 60000 --folds 10 --cuts 25 \
        --out results/humaid
"""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

SRC = Path(__file__).resolve().parents[1] / "data" / "external" / "events_set1"
OUT = Path(__file__).resolve().parents[1] / "data" / "humaid"

# Twitter snowflake: 高 41 位是毫秒时间戳，偏移量 1288834974657
SNOWFLAKE_EPOCH_MS = 1288834974657
URL_RE = re.compile(r"https?://\S+")


def snowflake_to_ms(tweet_id: str) -> int:
    """从 snowflake id 还原毫秒时间戳。HumAID 不提供时间字段，但 id 里带着。"""
    return (int(tweet_id) >> 22) + SNOWFLAKE_EPOCH_MS


def _norm_for_dup(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def main() -> int:
    if not SRC.exists():
        raise SystemExit(f"找不到 HumAID 数据：{SRC}\n请先下载并解压 HumAID_data_events_set1_47K.tar.gz")

    events = sorted([d for d in SRC.iterdir() if d.is_dir()])
    if not events:
        raise SystemExit(f"{SRC} 下没有事件目录")

    tweet_info_cols = [
        "tweet_id", "author", "entity_id", "tweet_url", "language",
        "timestamp", "urls", "extended_urls", "md5_extended_urls",
        "is_near_duplicate_of",
    ]

    per_split: Dict[str, Dict[str, List[List[str]]]] = {
        "training": defaultdict(list),
        "test": defaultdict(list),
    }
    gold: Dict[str, List[List[str]]] = {"training": [], "test": []}
    texts: List[List[str]] = []
    seen_ids = set()
    stats = []

    for idx, ev in enumerate(events, start=1):
        entity_id = f"HUM{idx:02d}"
        # train + dev 合成训练集，test 作测试集（对齐 RepLab 的 training/test 划分）
        buckets: Dict[str, List[dict]] = {"training": [], "test": []}
        for f in sorted(ev.glob("*.tsv")):
            split = "test" if f.stem.endswith("_test") else "training"
            with f.open("r", encoding="utf-8", errors="replace", newline="") as fh:
                for row in csv.DictReader(fh, delimiter="\t"):
                    if row.get("tweet_id") and row.get("tweet_text"):
                        buckets[split].append(row)

        n_topics = len({r["class_label"] for r in buckets["training"] + buckets["test"]})
        stats.append((entity_id, ev.name, len(buckets["training"]), len(buckets["test"]), n_topics))

        for split, rows in buckets.items():
            seen_text: Dict[str, str] = {}
            for row in rows:
                tid = str(row["tweet_id"])
                if tid in seen_ids:      # 跨事件去重
                    continue
                seen_ids.add(tid)
                text = row["tweet_text"].replace("\t", " ").replace("\n", " ")
                urls = URL_RE.findall(text)
                url_field = " ".join(urls)
                key = _norm_for_dup(text)
                dup_of = seen_text.get(key, "-1")
                if dup_of == "-1":
                    seen_text[key] = tid

                per_split[split][entity_id].append([
                    tid,
                    "",                                   # HumAID 无作者字段
                    entity_id,
                    f"https://twitter.com/i/status/{tid}",
                    "EN",
                    str(snowflake_to_ms(tid)),
                    url_field,
                    url_field,
                    "",
                    dup_of,
                ])
                gold[split].append([entity_id, tid, row["class_label"]])
                texts.append([tid, text])

    # --- 写盘
    for split in ("training", "test"):
        for entity_id, rows in per_split[split].items():
            p = OUT / split / "tweet_info" / f"{entity_id}.dat"
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("w", encoding="utf-8", newline="") as fh:
                w = csv.writer(fh, delimiter="\t", quoting=csv.QUOTE_ALL)
                w.writerow(tweet_info_cols)
                w.writerows(rows)
        gp = OUT / split / "goldstandard" / "goldstandard_topic_detection.dat"
        gp.parent.mkdir(parents=True, exist_ok=True)
        with gp.open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, delimiter="\t", quoting=csv.QUOTE_ALL)
            w.writerow(["entity_id", "tweet_id", "topic"])
            w.writerows(gold[split])

    ep = OUT / "entities" / "replab2013_entities.tsv"
    ep.parent.mkdir(parents=True, exist_ok=True)
    with ep.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", quoting=csv.QUOTE_ALL)
        w.writerow(["entity_id", "query", "entity_name", "domain", "homepage",
                    "wikipedia_page_en", "wikipedia_page_es", "md5_homepage",
                    "md5_wikipedia_page_en"])
        for entity_id, name, _, _, _ in stats:
            w.writerow([entity_id, name, name.replace("_", " ").title(), "disaster", "", "", "", "", ""])

    with (OUT / "texts.tsv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t")
        w.writerow(["tweet_id", "text"])
        w.writerows(texts)

    print(f"已转换 {len(stats)} 个事件 -> {OUT}")
    print(f"{'entity':8s}{'event':32s}{'train':>8s}{'test':>8s}{'topics':>8s}")
    for entity_id, name, ntr, nte, nt in stats:
        print(f"{entity_id:8s}{name:32s}{ntr:8d}{nte:8d}{nt:8d}")
    print(f"\n合计：训练 {sum(s[2] for s in stats)} / 测试 {sum(s[3] for s in stats)} 条推文")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
