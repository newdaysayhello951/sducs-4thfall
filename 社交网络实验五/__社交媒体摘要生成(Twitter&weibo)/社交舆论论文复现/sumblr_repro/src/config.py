"""Shared configuration for the Sumblr reproduction.

Hyperparameter defaults follow Shou et al., SIGIR 2013 (Section 5.3-5.5).
Values the paper does not state are marked NOT STATED and given a documented choice.
"""
from dataclasses import dataclass, field
from typing import Optional
import os

# --- Paths -----------------------------------------------------------------
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_DIR = os.path.dirname(SRC_DIR)
DATA_DIR = os.path.join(PROJ_DIR, "data")
OUT_DIR = os.path.join(PROJ_DIR, "output")

RAW_CSV = os.path.join(DATA_DIR, "turkey_earthquake_tweets.csv")


@dataclass
class SumblrConfig:
    # --- Stream selection --------------------------------------------------
    # Experiment day: the peak of the stream (2023-02-10) or None for all data.
    day: Optional[str] = "2023-02-10"
    max_tweets: Optional[int] = None      # cap for quick runs (None = all)

    # --- Clustering (paper Section 4.1) ------------------------------------
    beta: float = 0.07        # bounding factor in MBS              [paper: 0.07]
    n_max: int = 150          # upper limit on number of clusters   [paper: 150]
    mc: float = 0.7           # merge coefficient                   [paper: 0.7]
    m: int = 40               # focus tweet set size                [paper: 40]
    freshness_days: float = 3.0   # outdated-cluster threshold      [paper: 3 days]
    p_percent: float = 10.0       # last-p-percent tweets           [paper: p = 10]
    init_size: int = 200      # tweets used for k-means init        [NOT STATED -> 200]
    init_k: int = 15          # clusters for k-means init           [NOT STATED -> 15]
    canopy_cap: int = 15      # Canopy candidate centroids          [NOT STATED -> init_k]
    min_cluster_size: int = 2 # discard singleton clusters in summary [NOT STATED -> 2]
    check_interval: int = 500 # tweets between outdated-cluster checks [NOT STATED -> 500]

    # --- Pyramidal Time Frame (paper Section 3.3 / 5.4) --------------------
    alpha: int = 2            # PTF interval base                   [paper: 2]
    ptf_l: int = 3            # PTF depth                           [paper: 3/5/8]
    snapshot_minutes: int = 60    # snapshot interval              [paper: 1 hour]

    # --- Summarization (paper Section 4.2.1) -------------------------------
    lam: float = 0.4          # coverage vs. novelty trade-off      [paper: 0.4]
    summary_words: int = 250  # summary length in words             [paper: 250]
    max_summary_tweets: int = 25  # tweet cap (paper's k/L not stated -> 25)
    min_tweet_tokens: int = 3     # drop near-empty candidates      [NOT STATED -> 3]
    lexrank_iters: int = 10   # LexRank power iterations            [NOT STATED -> 10]
    lexrank_damping: float = 0.85  # LexRank damping                 [NOT STATED -> 0.85]
    lexrank_threshold: float = 0.1  # graph sparsification threshold [LexRank default]

    # --- Timeline (paper Section 4.3) --------------------------------------
    # Evolvement decision threshold. The paper's value (1.012) was tuned on its
    # own 95k-438k-tweet topic streams, where the summary-to-summary distance D
    # has enough spread for a tight threshold to discriminate. On our substitute
    # disaster stream, D is far more concentrated (coefficient of variation
    # 0.045-0.060, versus a much wider spread in the paper's setting), so
    # tau=1.012 flags 50-73% of windows as nodes. The paper itself reports that
    # its optimum is data-dependent ("the precision and F-score both reach the
    # highest value when tau = 1.012"), and we measured our own optimum at
    # tau ~= 1.06 on this stream. We therefore default to the paper's value for
    # comparability and expose --tau / --tau-values so the calibration can be
    # reproduced; see REPORT.md for the sweep.
    tau: float = 1.012
    # Laplace smoothing for the KL divergence. The paper says only "a small
    # positive constant"; add-one is the standard reading. A tiny value (1e-8)
    # saturates D = 1 - e^-KL at 1.0 and makes the tau test unable to fire.
    kl_epsilon: float = 1.0
    # Timeline window length in minutes. The window advances by a full window
    # (non-overlapping), so this also sets the number of successive summaries.
    # The value is chosen per stream length so that the number of bins stays in
    # the low tens, which is the regime where the D_cur / D_avg test is
    # meaningful: a single day yields ~12 bins, and the full 20-day stream
    # (~470 h) yields ~20 bins. Passing --timeline-window overrides this.
    timeline_window_min: int = 120
    timeline_target_bins: int = 20   # used to auto-scale the window
    # D_avg mode for detect_timeline. "paper" = the paper's non-node-only
    # average, guarded by a minimum sample count because the literal version
    # degenerates into a positive feedback loop (see detect_timeline
    # docstring). "paper_strict" = unguarded literal rule; "all" = average over
    # all previous pairs.
    davg_mode: str = "paper"
    min_davg_samples: int = 30   # warmup guard for the non-node pool

    # --- Text processing ---------------------------------------------------
    min_token_len: int = 2
    max_features: int = 20000
    use_stemming: bool = True

    # --- Misc --------------------------------------------------------------
    seed: int = 42
    verbose: bool = True
    stopwords: set = field(default_factory=set)
