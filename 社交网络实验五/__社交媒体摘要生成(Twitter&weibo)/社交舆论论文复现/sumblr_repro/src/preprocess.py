"""Module 1: data loading, cleaning and TF-IDF vectorization.

Implements the tweet representation of Shou et al., SIGIR 2013 (Section 3.1):
each tweet is a tuple (tv_i, ts_i, w_i) = (textual vector, timestamp, UserRank).

The paper's four newly-crawled datasets set w_i = 1 because the authors had no
social graph; we do the same (w_i = 1) and document it.
"""
import html
import os
import re
from typing import List, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from config import SumblrConfig, RAW_CSV

# --- Cleaning patterns -----------------------------------------------------
URL_RE = re.compile(r"https?://\S+|www\.\S+")
MENTION_RE = re.compile(r"@\w+")
HASHTAG_RE = re.compile(r"#(\w+)")
RT_RE = re.compile(r"^RT\s+@\w+:?\s*", re.IGNORECASE)
NON_WORD_RE = re.compile(r"[^a-z0-9\s]")
MULTISPACE_RE = re.compile(r"\s+")

# Minimal English stopword list (kept local so the pipeline has no NLTK download step).
STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "cannot", "could", "couldn",
    "did", "didn", "do", "does", "doesn", "doing", "don", "down", "during", "each",
    "few", "for", "from", "further", "had", "hadn", "has", "hasn", "have", "haven",
    "having", "he", "her", "here", "hers", "herself", "him", "himself", "his",
    "how", "i", "if", "in", "into", "is", "isn", "it", "its", "itself", "just",
    "me", "more", "most", "my", "myself", "no", "nor", "not", "now", "of", "off",
    "on", "once", "only", "or", "other", "our", "ours", "ourselves", "out", "over",
    "own", "same", "she", "should", "shouldn", "so", "some", "such", "than",
    "that", "the", "their", "theirs", "them", "themselves", "then", "there",
    "these", "they", "this", "those", "through", "to", "too", "under", "until",
    "up", "very", "was", "wasn", "we", "were", "weren", "what", "when", "where",
    "which", "while", "who", "whom", "why", "will", "with", "won", "would",
    "wouldn", "you", "your", "yours", "yourself", "yourselves", "rt", "via",
    "amp", "im", "u", "ur", "get", "got", "also", "us", "one", "two", "new",
}


def clean_text(text: str) -> str:
    """Strip URLs, mentions, retweet markers; keep hashtag words.

    Returns a normalized lowercase token string.
    """
    if not isinstance(text, str):
        return ""
    t = html.unescape(text)
    t = URL_RE.sub(" ", t)
    t = RT_RE.sub(" ", t)
    t = MENTION_RE.sub(" ", t)
    # Keep the hashtag word itself (it carries topic signal), drop the '#'.
    t = HASHTAG_RE.sub(r"\1", t)
    t = t.lower()
    t = NON_WORD_RE.sub(" ", t)
    t = MULTISPACE_RE.sub(" ", t).strip()
    return t


def _simple_stem(tokens: List[str]) -> List[str]:
    """Very light suffix stripping (Porter-lite).

    The paper does not state its stemmer; this keeps morphological variants
    together without an external dependency.
    """
    out = []
    for w in tokens:
        if len(w) > 4:
            for suf in ("ingly", "edly", "ing", "ies", "ied", "es", "ed", "s"):
                if w.endswith(suf) and len(w) - len(suf) >= 3:
                    w = w[: -len(suf)]
                    break
        out.append(w)
    return out


def tokenize(text: str, cfg: SumblrConfig) -> List[str]:
    """Clean -> split -> stopword filter -> optional stemming."""
    toks = clean_text(text).split()
    toks = [t for t in toks if len(t) >= cfg.min_token_len and t not in STOPWORDS]
    if cfg.use_stemming:
        toks = _simple_stem(toks)
    return toks


def count_words(text: str) -> int:
    """Raw word count used for the 250-word summary budget.

    The paper's length limit is in words of the produced summary, so this must
    NOT apply stopword removal or stemming (doing so would under-count and make
    the Sumblr summary artificially short relative to the baselines).
    """
    return len(clean_text(text).split())


def load_tweets(cfg: SumblrConfig) -> pd.DataFrame:
    """Load the raw CSV, filter by day, and parse timestamps.

    Returns a DataFrame sorted by time with columns:
        id, text, dt (tz-naive UTC), ts (epoch seconds), retweets, favorites
    """
    if not os.path.exists(RAW_CSV):
        raise FileNotFoundError(
            f"Raw dataset not found: {RAW_CSV}\n"
            "Run `python src/download_data.py` first."
        )

    df = pd.read_csv(RAW_CSV)
    df = df.dropna(subset=["text", "date"]).copy()

    dt = pd.to_datetime(df["date"], errors="coerce", utc=True)
    df["dt"] = dt.dt.tz_localize(None)
    df = df.dropna(subset=["dt"])

    if cfg.day is not None:
        df = df[df["dt"].dt.strftime("%Y-%m-%d") == cfg.day]

    df["retweets"] = pd.to_numeric(df.get("retweets"), errors="coerce").fillna(0)
    df["favorites"] = pd.to_numeric(df.get("favorites"), errors="coerce").fillna(0)

    df = df.sort_values("dt").reset_index(drop=True)

    # Deduplicate identical tweet texts (very common in disaster streams via RT).
    before = len(df)
    df = df.drop_duplicates(subset=["text"]).reset_index(drop=True)
    dup_removed = before - len(df)

    if cfg.max_tweets is not None:
        df = df.head(cfg.max_tweets).reset_index(drop=True)

    # Timestamps in seconds relative to stream start (paper uses ts_i units).
    df["ts"] = (df["dt"] - df["dt"].iloc[0]).dt.total_seconds()

    if cfg.verbose:
        print(f"[preprocess] loaded {len(df)} tweets"
              f" (dedup removed {dup_removed})")
        print(f"[preprocess] time span: {df['dt'].min()} -> {df['dt'].max()}")

    return df


def build_vectors(df: pd.DataFrame, cfg: SumblrConfig):
    """TF-IDF matrix over cleaned token strings.

    Returns (X_raw, X_norm, vectorizer).

    The paper keeps two distinct sums (Section 3.2):
        sum_v  = sum of NORMALIZED textual vectors   tv_i / ||tv_i||
        wsum_v = sum of RAW weighted textual vectors w_i * tv_i
    They are therefore different objects, and the MBS in Section 4.1.2
        Sim(co, t_i) = (wsum_v . sum_v) / (n * ||wsum_v||)
    is a genuine average cosine. Feeding a single normalized matrix to both
    collapses it to ||centroid||, so we build both.
    """
    docs = [" ".join(tokenize(t, cfg)) for t in df["text"]]

    vec = TfidfVectorizer(
        max_features=cfg.max_features,
        sublinear_tf=True,
        norm=None,                      # raw tf-idf; normalized separately
        token_pattern=r"(?u)\b\w+\b",
    )
    X_raw = vec.fit_transform(docs).astype(np.float32)
    X_norm = normalize(X_raw, norm="l2", copy=True).astype(np.float32)

    if cfg.verbose:
        print(f"[preprocess] TF-IDF matrix: {X_raw.shape[0]} tweets x "
              f"{X_raw.shape[1]} terms (nnz={X_raw.nnz})")

    return X_raw, X_norm, vec
