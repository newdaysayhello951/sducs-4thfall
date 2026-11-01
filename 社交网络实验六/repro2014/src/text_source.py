"""推文正文获取。

RepLab 2013 受 Twitter ToS 限制，**只发布 tweet id，不发布正文**。
而论文的 8 个特征（terms×3、semantic×3、hashtags、namedusers）都需要正文。

本模块提供三种正文来源，按顺序尝试：

  1. 本地文件（推荐用于离线复现）
     - JSONL：每行一个 tweet 对象，含 id_str/id 与 text/full_text
     - TSV/CSV：至少包含 tweet_id 与 text 两列

  2. X/Twitter API v2（需 bearer token）
     - 走 /2/tweets?ids=... 批量接口，每批 100 条
     - 需要设置环境变量 TWITTER_BEARER_TOKEN

  3. 空实现：返回空字典，上游自动降级为「仅元数据 + 时间」模式。

2026 年的现实：2012 年的推文删除率很高，即使有 token 也很难拿全，
所以复现时务必记录正文覆盖率。
"""

from __future__ import annotations

import csv
import json
import os
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import requests


# ---------------------------------------------------------------- 本地文件

def load_texts_from_jsonl(paths: Iterable[Path]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for p in paths:
        p = Path(p)
        with p.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                tid = obj.get("id_str") or obj.get("id")
                txt = obj.get("full_text") or obj.get("text")
                if tid is not None and txt:
                    out[str(tid)] = txt
    return out


def load_texts_from_table(path: Path, id_col: str = "tweet_id", text_col: str = "text") -> Dict[str, str]:
    out: Dict[str, str] = {}
    with Path(path).open("r", encoding="utf-8", errors="replace", newline="") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        delim = "\t" if sample.count("\t") >= sample.count(",") else ","
        reader = csv.DictReader(fh, delimiter=delim)
        for row in reader:
            tid = row.get(id_col)
            txt = row.get(text_col)
            if tid and txt:
                out[str(tid)] = txt
    return out


def load_texts(path: Optional[str]) -> Dict[str, str]:
    """按扩展名自动识别格式。path 可以是单个文件或目录。"""
    if not path:
        return {}
    p = Path(path)
    if p.is_dir():
        files = sorted(list(p.glob("*.jsonl")) + list(p.glob("*.json")))
        return load_texts_from_jsonl(files)
    if p.suffix in (".jsonl", ".json"):
        return load_texts_from_jsonl([p])
    return load_texts_from_table(p)


# ---------------------------------------------------------------- X API v2

API_URL = "https://api.twitter.com/2/tweets"


def rehydrate_via_api(
    tweet_ids: List[str],
    bearer_token: Optional[str] = None,
    batch_size: int = 100,
    sleep: float = 0.2,
    timeout: int = 30,
) -> Dict[str, str]:
    """用 X API v2 批量拉取推文正文。缺失/删除的推文不会出现在结果里。"""
    token = bearer_token or os.environ.get("TWITTER_BEARER_TOKEN")
    if not token:
        raise RuntimeError(
            "缺少 TWITTER_BEARER_TOKEN。请设置环境变量，或改用 --text-file 提供本地正文。"
        )
    headers = {"Authorization": f"Bearer {token}"}
    out: Dict[str, str] = {}
    uniq = list(dict.fromkeys(tweet_ids))
    for start in range(0, len(uniq), batch_size):
        chunk = uniq[start:start + batch_size]
        try:
            resp = requests.get(
                API_URL,
                headers=headers,
                params={"ids": ",".join(chunk), "tweet.fields": "created_at,author_id"},
                timeout=timeout,
            )
        except requests.RequestException as exc:
            print(f"[rehydrate] 请求失败（第 {start} 批）：{exc}")
            continue
        if resp.status_code != 200:
            print(f"[rehydrate] HTTP {resp.status_code}（第 {start} 批）：{resp.text[:200]}")
            continue
        payload = resp.json()
        for item in payload.get("data", []) or []:
            out[str(item["id"])] = item.get("text", "")
        time.sleep(sleep)
    return out


def coverage(tweet_ids: Iterable[str], texts: Dict[str, str]) -> float:
    ids = list(tweet_ids)
    if not ids:
        return 0.0
    return sum(1 for t in ids if t in texts) / len(ids)
