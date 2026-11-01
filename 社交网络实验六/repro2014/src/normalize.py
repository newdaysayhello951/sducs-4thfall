"""按论文 3.1 节的归一化流程处理推文文本。

论文原文：
    "Before computing the features, tweets were normalized by removing
     punctuation, lowercasing, tokenizing by whitespaces and removing
     stopwords and words with less than three characters."

即四步：去标点 -> 小写 -> 按空白分词 -> 去停用词 + 去长度小于 3 的词。

数据集含英语与西班牙语两种推文，所以停用词表需要双语。
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from typing import Iterable, List, Set

# 英文停用词（标准列表）
_EN = """
a about above after again against all am an and any are aren't as at be because been
before being below between both but by can't cannot could couldn't did didn't do does
doesn't doing don't down during each few for from further had hadn't has hasn't have
haven't having he he'd he'll he's her here here's hers herself him himself his how
how's i i'd i'll i'm i've if in into is isn't it it's its itself let's me more most
mustn't my myself no nor not of off on once only or other ought our ours ourselves out
over own same shan't she she'd she'll she's should shouldn't so some such than that
that's the their theirs them themselves then there there's these they they'd they'll
they're they've this those through to too under until up very was wasn't we we'd we'll
we're we've were weren't what what's when when's where where's which while who who's
whom why why's with won't would wouldn't you you'd you'll you're you've your yours
yourself yourselves
""".split()

# 西班牙语停用词（标准列表）
_ES = """
a al algo algunas alguno algunos ante antes aquel aquella aquellas aquellos aqui asi
aun aunque bien cada como con contra cual cuales cualquier cuando de del desde donde
dos el ella ellas ello ellos en entre era eran eres es esa esas ese eso esos esta
estaba estado estais estamos estan estar estas este esto estos estoy fue fueron ha
haber habia han has hasta hay la las le les lo los mas me mi mis mucho muy nada ni no
nos nosotros o os otra otras otro otros para pero poco por porque que quien se sea
segun ser si sido sin sobre son su sus tal tambien tan tanto te tiene tienen todo
todos tu tus un una unas uno unos vosotros y ya yo
""".split()

STOPWORDS: Set[str] = set(_EN) | set(_ES)

# 论文说"去掉标点"。这里用 Unicode 标点类别统一处理，比列举 ASCII 标点更干净。
_PUNCT_TABLE = {i: None for i in range(0x110000)
                if unicodedata.category(chr(i)).startswith("P")}

_WS = re.compile(r"\s+")


def strip_punctuation(text: str) -> str:
    """删除所有 Unicode 标点符号。"""
    return text.translate(_PUNCT_TABLE)


def normalize_text(text: str, min_len: int = 3, stopwords: Set[str] = STOPWORDS) -> List[str]:
    """把一条推文归一化成词列表。

    步骤与论文一致：
      1. 去标点
      2. 小写
      3. 按空白分词
      4. 去停用词、去长度 < min_len 的词
    """
    if not text:
        return []
    s = strip_punctuation(text).lower()
    tokens = _WS.split(s)
    return [t for t in tokens if len(t) >= min_len and t and t not in stopwords]


@lru_cache(maxsize=200_000)
def normalize_text_cached(text: str) -> tuple:
    """带缓存的版本：同一文本在成对特征里会被反复用到。"""
    return tuple(normalize_text(text))


def term_set(text: str) -> Set[str]:
    return set(normalize_text_cached(text))


def normalize_corpus(texts: Iterable[str]) -> List[List[str]]:
    return [normalize_text(t) for t in texts]


# ---------------------------------------------------------------- 从文本抽取 Twitter 特有信号
# 论文的 namedusers / hashtags 两个特征需要从正文里抽 @提及 与 #话题。
# 注意：必须在"去标点"之前抽取，因为 @ 和 # 本身会被当标点删掉。

_MENTION = re.compile(r"@([A-Za-z0-9_]{1,15})")
_HASHTAG = re.compile(r"#([^\s#@]+)")


def extract_mentions(text: str) -> Set[str]:
    return {m.lower() for m in _MENTION.findall(text or "")}


def extract_hashtags(text: str) -> Set[str]:
    return {h.lower() for h in _HASHTAG.findall(text or "")}
