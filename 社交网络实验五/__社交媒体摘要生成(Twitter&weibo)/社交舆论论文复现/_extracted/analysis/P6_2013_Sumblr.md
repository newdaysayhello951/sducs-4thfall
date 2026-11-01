# Sumblr: Continuous Summarization of Evolving Tweet Streams

## Bibliographic info (authors, venue, year)

- **Authors:** Lidan Shou (1,2), Zhenhua Wang (1), Ke Chen (1), Gang Chen (1)
  - 1: College of Computer Science and Technology, Zhejiang University, Hangzhou, China
  - 2: State Key Lab of CAD&CG, Zhejiang University
  - Emails listed: `{should, wzh-cs, chenk, cg}@zju.edu.cn`
- **Venue:** SIGIR'13 — "SIGIR'13, July 28–August 1, 2013, Dublin, Ireland." Pages 533–542 (page numbers 533–542 appear at the foot of each page).
- **Year:** 2013 (ACM copyright "Copyright 2013 ACM 978-1-4503-2034-4/13/07 ...$15.00")
- **Category/Subject Descriptors:** "H.3.1 [Content Analysis and Indexing]: Abstracting methods; H.3.4 [Systems and Software]: Performance evaluation (efficiency and effectiveness)"
- **Keywords:** "Tweet stream; continuous summarization; timeline"
- **Funding:** "supported by the National Science Foundation of China (GrantNo. 61170034)"

## Task (what is summarized, input -> output, extractive vs abstractive)

- **Input:** a *topic-based tweet stream* (single-topic stream; the paper states "So far we have assumed a tweet stream of only one topic as the input to Sumblr" and sketches a multi-topic extension by keyword matching). Tweets are represented as the tuple `(tv_i, ts_i, w_i)` — textual vector, posted timestamp, UserRank of the author.
- **Output:** three artifacts:
  1. **Online summaries** — "retrieved directly from the current clusters maintained in the memory."
  2. **Historical summaries** — for a *user-specified arbitrary time duration* `H` ending at `tse`; "range timeline", "drill-down summary", "roll-up summary" are the motivating use cases (Fig. 1 example: topic "Apple", 22 Oct 2012–11 Nov 2012, or 8 am to 11 pm on 5 Nov).
  3. **Timelines** — "a timeline is a sequence of time-stamped summaries (nodes)"; both **continuous timelines** and **range timelines** are produced by "monitoring a quantity called summary-based variation."
- **Type:** **Extractive.** "In this paper, we focus on extractive summarization." The system "aim[s] to extract k tweets from T". Summary length is bounded: "summary length are limited in terms of words (250 words)" and in the experiments "The length of each summary is limited to 250 words."
- **Framing of the problem:** "continuous tweet summarization, which represents the massive tweets in a set of short text pieces covering the main topics (or sub-topics of course)." The paper claims to be "the first to study continuous tweet stream summarization."

## Method (core algorithm in implementable detail)

### Overall framework (Figure 2)
Two components: a **Tweet Stream Clustering module** and a **High-level Summarization module**. The clustering module maintains two structures: **Tweet Cluster Vector (TCV)** (compressed in-memory cluster statistics, "considered as potential sub-topic delegates") and the **Pyramidal Time Frame (PTF)** (disk-stored cluster snapshots for historical retrieval). The summarization module produces online/historical summaries and feeds a **topic evolvement detection** step that emits timelines.

### 3.1 Tweet representation
- Text vector `tv_i` uses TF-IDF style word scores; a tweet is "not only textual, but also having temporal nature".
- Weight `w_i` = **UserRank** of the tweet's author, "compute[d] ... based on social relationships among users ... as [5]" (Chen et al., SIGMOD 2011).
- For the four newly crawled datasets, "we do not have access to the respective users' social networks for these four, we set their weights of tweets `w_i` to the default value of 1."

### 3.2 Tweet Cluster Vector (Definition 1)
For a cluster `C` with tweets `t1..tn`:
`TCV(C) = (sum_v, wsum_v, ts1, ts2, n, ft_set)` where
- `sum_v = Σ_{i=1..n} tv_i/||tv_i||` (sum of normalized textual vectors)
- `wsum_v = Σ_{i=1..n} w_i · tv_i` (sum of weighted textual vectors)
- `ts1 = Σ ts_i` (sum of timestamps)
- `ts2 = Σ (ts_i)^2` (quadratic sum of timestamps)
- `n` = number of tweets in the cluster
- `ft_set` = "a focus tweet set of size m, consisting of the closest m tweets to the cluster centroid"

Implementation note from the paper: "we only store the identifiers and sums of values of the words occurring in the cluster" — sparse storage. Focus-tweet selection uses **cosine similarity**.

Cluster centroid: `cv = (Σ w_i·tv_i)/n = wsum_v / n` (Equation 1).

"Like in [28], our TCV structure can also be updated in an incremental way when new tweets arrive."

### 3.3 Pyramidal Time Frame (Definition 2, from CluStream [1])
- Snapshots classified into orders `0 .. log(T)` where `T` = time elapsed since stream start.
- "Snapshots of the i-th order occur at time intervals of `α^i` ... each snapshot of the i-th order is taken at a moment in time when the timestamp from the beginning of the stream is exactly divisible by `α^i`."
- "At any given moment in time, only the last `α^l + 1` (`l ≥ 1`) snapshots of order i are stored."
- Properties: max order is `log(T)`; "The maximum number of snapshots maintained at T is `(α^l + 1) · log(T)`."
- Worked example: "Let `α = 3` and `l = 2`, then there are at most `3^2+1 = 10` snapshots stored in each order." With stream start at timestamp 1 and current timestamp 86, Table 1 gives order-4: {81}; order-3: {54, 27}; order-2: {72, 63, 45, 36, 18, 9}; order-1: {84, 78, 75, 69, 66, 60, 57, 51, 48, 42}; order-0: {86, 85, 83, 82, 80, 79, 77, 76, 74, 73}. "Redundancy is removed by storing each snapshot only in its highest possible order."
- "we only maintain the current clusters in main memory, and store all historical snapshots in the PTF on disk."

### 4.1 Tweet stream clustering
**4.1.1 Initialization:** "we collect a small number of tweets and use a **k-means** clustering algorithm to create the initial clusters. The value of `k` and the initial cluster centroids are decided via the **Canopy [18]** method." Then the first set of TCVs is initialized per Definition 1.

**4.1.2 Incremental clustering (Algorithm 1):**
```
Input: a cluster set S
1 while !stream.end() do
2     Tweet t = stream.next();
3     choose Cp in S whose centroid is the closest to t;
4     if MaxSim(co_p, t) < MBS then
5         create a new cluster Cnew = {t};
6         S = S ∪ Cnew;
7     else
8         update Cp with t;
9     if TS_current % (α^i) == 0 then
10        store S into PTF;
```
- Heuristic 1: "If `MaxSim(co, t)` is smaller than a Minimum Bounding Similarity (MBS), then t is upgraded to a new cluster. Otherwise, t is added to its closest cluster."
- `MBS = β · Sim(co, t_i)`, "where β is a bounding factor (0 < β < 1) and `Sim(co, t_i)` is the average cosine similarity between `co` and tweets included in `Cp`". The paper derives `Sim(co, t_i) = wsum_v · sum_v / (n · ||wsum_v||)` from TCV contents.
- **Focus tweet set maintenance:** since storing all tweets is impossible, "we use a heuristic strategy to choose promising candidates instead of exact focus tweets: for the newly absorbed tweet and those already in `ft_set`, we compute their cosine distances to the new centroid, and select the closest `m` tweets." Rationale: "it gives a higher probability for fresh tweets to get into the focus set, which usually represent new statuses of the topic."
- **Complexity:** finding the closest cluster is `O(N d)` per tweet (`d` = vocabulary size); Heuristic 1 is `O(d)`; TCV update is `O(m d)`; total `O((N + m) d)`.

**4.1.3 Deleting outdated clusters:**
- Temporal statistics give `µ_c = ts1/n`, `σ_c = sqrt(ts2/n − (ts1/n)^2)`.
- "Assuming that the tweet timestamps are normally distributed", the start timestamp of the last p percent of tweets is obtained via the `(100 − p/2)`-th percentile: `x = µ_c + σ_c · sqrt(2) · erf^{-1}(2p' − 1)` where `p' = (100 − p/2)%`; "erf^{-1}(z) ... can be calculated using the Maclaurin series expansion [31]".
- "We empirically set a freshness threshold as **3 days** ... and set **p = 10**. If `tsp=2` is smaller than this threshold, i.e., the average timestamp of the latest 10 percent tweets is more than 3 days old, then we regard C as an outdated cluster and remove it."
- Deletion cost `O(N)`, merging cost `O(N^2)`; "we use the former method for periodical examination and use the latter method only when memory limit is reached."

**4.1.4 Merging clusters:**
- "we specify an upper limit for the number of clusters as `Nmax`. When the limit is reached, a merging process starts."
- Greedy: sort cluster pairs by centroid similarity descending; merge most similar pair; composite clusters get an **IDList**; skip pairs already in the same composite cluster; "This process continues until there are only `mc` percentage of the original clusters left (`mc` is a merge coefficient)".
- Aggregation Operation (Definition 3): `sum_v = sum_v1 + sum_v2`; `wsum_v = wsum_v1 + wsum_v2`; `ts1 = ts1_1 + ts1_2`; `ts2 = ts2_1 + ts2_2`; `n = n1 + n2`; "`ft_set` consists of the first m tweets in `ft_set1 ∪ ft_set2`, sorted by distance to the newly merged centroid."
- Worked example: 10 clusters, `mc = 0.7` → "we need to remove `10 × (1 − 0.7) = 3` clusters"; sorted pairs `(c1,c2), (c2,c4), (c1,c4), (c5,c7), (c4,c5), ...`; merges give `{c1,c2}` → `{c1,c2,c4}` → `{c5,c7}`.
- Access bound: at most `C(N',2) + 1 = N'(N'−1)/2 + 1` pairs where `N' = Nmax × (1 − mc)`.

### 4.2 High-level summarization
- **Historical duration approximation:** given duration length `H` ending at `tse`, "we can retrieve two snapshots whose timestamps are either equal to or right before `tse` and `tse − H`"; the original `[tse − H, tse]` "is approximated by `[ts2, ts1]`."
- **Subtraction Operation (Definition 4)** for cluster-set subtraction: `sum_v = sum_v1 − sum_v2`; `wsum_v = wsum_v1 − wsum_v2`; `ts1 = ts1_1 − ts1_2`; `ts2 = ts2_1 − ts2_2`; `n = n1 − n2`; "`ft_set` consists of tweets which exist in `ft_set1` but not in `ft_set2`."

**4.2.1 TCV-Rank Summarization (Algorithm 2):**
- NP-hardness (Lemma 1): the problem reduces to **Max-k-Cover**, "which is NP-hard. Therefore, our summarization problem is also NP-hard."
- Algorithm 2:
```
Input: a cluster set D(c)      Output: a summary set S
1 S = ∅, T = {all the tweets in ft sets of D(c)};
2 Build a similarity graph on T;
3 Compute LexRank scores LR;
4 Tc = {tweets with the highest score in each cluster};
5 while |S| < L do
6     foreach tweet ti in Tc do
7         calculate vi according to Equation (2);
8     select tmax with the highest vi;
9     S = S ∪ tmax;
10 while |S| < L do
11    foreach tweet t'i in T − S do
12        calculate v'i according to Equation (2);
13    select t'max with the highest v'i;
14    S = S ∪ t'max;
15 return S;
```
- **Objective (Equation 2):** `t = argmax_{t_i} [ λ · (nt_i/n_max) · LR(t_i) − (1 − λ) · avg_{t_j ∈ S} Sim(t_i, t_j) ]`
  - `λ (0 ≤ λ ≤ 1)` weight parameter; `nt_i` size of the cluster containing `t_i`; `n_max` size of the biggest cluster; `LR(t_i)` LexRank score; `S` the summary set already chosen.
  - "The motivation of Equation (2) is analogous to that of Maximal Marginal Relevance (MMR) [4] ... the first component ... favors tweets which have high scores and belong to big clusters (content coverage); the second component penalizes redundant tweets with similar contents to those already chosen (novelty)."
  - Note the paper's prose describes Equation (2) as selecting from `Tc` first (one top-LexRank tweet per TCV), then globally over `T − S` if length is not reached.
- **Complexity:** LexRank `O(r|T|^2)` with `r` = iteration number; `|T| ≤ N × m`; selection worst case `O(N^2 + (|S| − N)·|T|)`; "the total cost for our algorithm is `O(r|T|^2 + N^2) = O(r m^2 N^2)`."

### 4.3 Topic evolvement detection
- Uses **Kullback-Leibler divergence** between word distributions of successive summaries:
  `D_KL(Sc||Sp) = Σ_{w∈V} p(w|Sc) ln [ p(w|Sc) / p(w|Sp) ]` (Equation 3)
  with `p(w|Sc) = tf(w,Sc) / Σ_{w'} tf(w',Sc)` and `p(w|Sp) = (tf(w,Sp) + ε) / Σ_{w'} (tf(w',Sp) + ε)`; "`ε` is a small positive constant for Laplace Smoothing" (value not stated).
- Normalization: "we normalize the distance into interval `[0, 1)` using `D = 1 − e^{−D_KL}`".
- Node decision rule: `D_cur / D_avg > τ` "where `D_cur` is the distance between current summary and its previous neighboring summary, `D_avg` is the average distance of all the previous successive summary pairs which do not produce time nodes, and `τ (τ ≥ 1)` is the decision threshold." — "we detect topic evolvement when there is a burst in distances between successive summaries."

### 4.4 Discussion
- **Handling noises:** two mechanisms — outdated-cluster deletion in clustering, and low LexRank scores / small cluster sizes making noise tweets "far less likely to be selected into summary."
- **Multi-topic extension:** "when a new tweet arrives, we first decide its related topics by keyword matching. Then it is delivered into different groups of clusters. Clusters are grouped by their corresponding topical IDs." — "this mechanism allows for distributed system implementation."

### Hyperparameter values (as stated)
| Parameter | Value | Source |
|---|---|---|
| `β` (bounding factor in MBS) | **0.07** ("A good choice is β = 0.07"); swept 0.04–0.11 | §5.3 |
| `Nmax` (max clusters) | **150** ("A balanced value for Nmax is 150"); swept 30–210 | §5.3 |
| `mc` (merge coefficient) | **0.7** ("An ideal value for mc is 0.7"); swept 0.0–1.0 | §5.3 |
| `m` (focus tweet set size) | **40** ("We choose m = 40"); swept 10–80 | §5.3 |
| `λ` (coverage vs. novelty) | **0.4** ("we set λ = 0.4 as a balanced factor"); swept 0–1 step 0.1 | §5.3 |
| `α` (PTF interval base) | **2** ("We fix α at 2") | §5.4 |
| `l` (PTF depth) | varied: **3, 5, 8** (giving 63, 173, 592 snapshots) | §5.4 |
| Freshness threshold | **3 days**; `p = 10` | §4.1.3 |
| `τ` (timeline threshold) | best at **1.012**; swept 1.000–1.020 | §5.5 |
| Snapshot interval | "The interval between two successive snapshots (timestamp unit) is one hour." | §5.4 |
| Summary length | **250 words** | §4.2.1, §5.1 |
| `k` / `L` (tweets per summary) | not stated as a numeric value; the text says "extract k tweets from T" and Algorithm 2 uses `L` | §4.2.1 |
| `ε` (Laplace smoothing) | not stated | §4.3 |
| `r` (LexRank iterations) | not stated | §4.2.1 |

## Datasets (names, sizes, language, domain, HOW OBTAINED)

Table 2 "Basic information of 5 datasets" (all **English**, all **Twitter**):

| Topics (filtering keywords) | #Tweets | Time Span |
|---|---|---|
| Obama | 95,055 | 2009.2 – 2009.10 |
| Chelsea | 438,884 | 2012.11 – 2012.12 |
| Arsenal Arsene Wenger | 323,555 | 2012.11 – 2012.12 |
| Tablet Smartphone Cellphone | 231,011 | 2012.11 – 2012.12 |
| Black Friday | 124,684 | 2012.11 – 2012.12 |

Total ≈ **1,213,189 tweets**. Language: English (all five are English-language Twitter topics). Domains: politics (Obama), sports/football (Chelsea, Arsenal), consumer tech (Tablet Smartphone Cellphone), shopping (Black Friday).

**How obtained:**
- "One is obtained by conducting **keyword filtering** on a Twitter dataset (from Feb. to Oct., 2009) used by [5]." — i.e., the Obama set is derived from the dataset of Chen et al., SIGMOD 2011 (the "Ti" indexing paper). No public URL for that source is given in this paper.
- "The other four include more recent tweets acquired in one month via **Twitter's keyword tracking API**" — footnote 2 gives `https://dev.twitter.com/docs/api/1.1/post/statuses/filter`. So four of five datasets were **crawled by the authors** using the (now deprecated/paid) Twitter streaming filter API.
- "As we do not have access to the respective users' social networks for these four, we set their weights of tweets `w_i` to the default value of 1." — meaning UserRank is effectively disabled (uniform weight) for 4 of 5 datasets; only the Obama set could use social-network-derived UserRank (and the paper does not explicitly confirm it did).

**Ground truth for summaries (not human-annotated from scratch):**
- "As no previous work has conducted similar study on continuous summarization, we have to build our own ground truth (reference summaries). However, manual creation of these summaries is apparently impractical due to the huge size of the datasets."
- Two-step method: (1) run three algorithms — **ClusterSum [13], LexRank [6], DSDR [11]** — on the retrieved tweet subset to get three candidate summaries; (2) "the final reference summary is manually extracted from three candidate summaries. Priority is given to those sentences appearing in at least two candidate summaries. The length of each summary is limited to 250 words."
- **Ground truth for timelines:** "the reference timelines are manually produced. We choose the 'Arsenal' and 'Chelsea' datasets for this experiment, as the ground truth for sport topics are relatively easier to build manually. Specifically, we read through all the related news during one month from news websites (**Yahoo! and ESPN**), and select those dates as nodes on the reference timeline when important events happen, e.g., football matches, players' signing of new contracts, etc."

## Data/code availability stated in the paper (quote)

Footnote 3, attached to the ground-truth-for-timelines paragraph, states verbatim:

> "Our datasets and ground truth are available at **http://db.zju.edu.cn/s/sumblr/**."

That is the **only** availability statement in the paper. There is:
- **No code release statement** — no GitHub, no "we will release our implementation", no binary/tool link.
- **No license, no file-format description, no size-on-disk, no tweet-ID list** statement.
- **No** statement about releasing the UserRank social graph.

**Verified status of that URL (checked during this analysis):** `http://db.zju.edu.cn/s/sumblr/` redirects to `https://db.zju.edu.cn/s/sumblr/`, which returns **HTTP 404 Not Found** (nginx). So the advertised artifact page is **dead** as of this check. Combined with the fact that four of five datasets came from the Twitter streaming filter API under the 2012–2013 Twitter ToS, the raw tweet text almost certainly cannot be legally redistributed today, and even tweet IDs would suffer from massive deletion/erasure.

## Evaluation (metrics, human evaluation required? protocol, folds)

- **Metric:** "We apply the popular **ROUGE** toolkit [15] for evaluation. Among supported metrics, **ROUGE-1** has been demonstrated to be the most consistent with human judgement [16]. Considering the short and informal nature of the tweet contents, we decide that ROUGE-1 is suitable for measuring tweet summaries."
- Only **F-score** is reported: "we find similar trends in the comparison of precision, recall and F-score ... Therefore, we shall only report the F-score results to save space. The F-score results presented are **averaged on all five datasets**." (Timeline generation does report precision, recall and F-score — Figure 11.)
- **No human evaluation of summary quality** is performed. Human labor enters only in (a) assembling the reference summaries from the three candidate summaries, and (b) manually building the Arsenal/Chelsea reference timelines. The paper itself flags the resulting bias: "as the ground truth is generated using these baseline methods, the summary quality is to some extent biased in favor of them."
- **No cross-validation / folds.** This is not a trainable model; there is no train/test split and no folds anywhere in the paper.
- **Continuous-period metric:** "To evaluate the metrics on a continuous time period `[T0, T]`, we have to calculate the integral of the metric over the period" — Equation (4) `∫_{T0}^{T} metric(t) dt`. "The integral requires unaffordable number of samplings during the period. In practice, we only sample the metrics by each arrival of a certain number of new tweets. This number is called the **sampling interval**. Note the sampling interval must be no greater than the step size."
- **Sliding-window protocol for baselines (Figure 8):** "each window contains a certain number (window size) of tweets which are summarized as a document. After that, the window moves forward by a step size, so that the oldest tweets are discarded and the new ones are added into the window." — "The windows are dimensioned by **number of tweets** instead of time duration, because the number of tweets may vary dramatically across fixed-length durations."
- **Main comparison setting:** "we set **window size to 20000, sampling interval to 2000**. The step size varies from **4000 to 20000**."
- **Flexibility experiment:** "we extract a subset of one-month period from each dataset as the input stream. The interval between two successive snapshots (timestamp unit) is one hour." Drill-down/roll-up evaluated over durations `len` from 1 day to 10 days, reporting `score(ts) = Σ_len F-score([ts − len, ts]) / 10` (Equation 5), reported "by interval of 48 hours", with `α` fixed at 2 and `l ∈ {3, 5, 8}`.
- **Scalability experiment:** "evaluates the efficiency results of a single window, while varying the window size. It simulates the case of a large burst of tweets in a short period." Data size swept 0 to 40k.

## Baselines

Baselines are the three summarizers used (also) for ground-truth construction, wrapped in the sliding-window scheme, plus a trivial control:

1. **Random** — "we also give a baseline Random method, which selects tweets randomly from each window."
2. **ClusterSum [13]** (Inouye & Kalita, SocialCom 2011) — "first clusters the tweets and then summarizes each cluster by picking the most weighted post according to the hybrid TF-IDF weighting described in [13]."
3. **LexRank [6]** (Erkan & Radev, JAIR 2004) — "first builds a sentence similarity graph, and then selects important sentences based on the concept of eigenvector centrality."
4. **DSDR [11]** (He et al., AAAI 2012) — "models the relationship among sentences using linear reconstruction, and finds an optimal set of representative sentences to approximate the original documents, by minimizing the reconstruction error."

All three (ClusterSum, LexRank, DSDR) were re-implemented by the authors in sliding-window form. Related work that is **discussed but not used as an experimental baseline**: CluStream [1], Aggarwal & Yu's text/categorical stream clustering [2], Phrase Reinforcement [20], Hybrid TF-IDF / Cluster-based [13], Harabagiu & Hickl [9], p-median microblog summarization [21], ETS (Evolutionary Timeline Summarization) [24], Yang et al. Twitter feed summarization [25], Ti [5].

## Reported results (key numbers, so a reproducer knows the target)

- **Quality vs. step size (Figure 5, F-score, averaged over all 5 datasets):** F-score axis spans roughly 0.25–0.50. The narrative: "when the step size is small (4000), DSDR and LexRank achieve better summary quality than Sumblr, at the expense of much more computation. **When step size ≥ 12000, Sumblr outperforms all the baseline methods in terms of both summarization quality and computation cost.** Although the efficiency of LexRank is comparable with our method when step size ≥ 16000, its summary quality is significantly worse." Also: "**Sumblr is not affected by the step size, as it supports continuous summarization inherently.**" (Exact per-point F-scores are only readable from the plot; the text does not tabulate them.)
- **Efficiency vs. step size (Figure 6):** runtime (sec) axis 0–40,000; baselines' cost grows steeply as step size shrinks. "These methods rely on a small step size to produce quality summaries. Unfortunately, small step size leads to very frequent and expensive computations for windows. In contrast, Sumblr strikes a good balance between summary quality and efficiency."
- **Scalability (Figure 7, log-scale y-axis):** "**When the data size is above 15000, Sumblr is faster than LexRank by nearly an order of magnitude, and outperforms the other two by more than that.** The small fluctuations in Sumblr may be caused by the cluster deletions and merges."
- **Parameter tuning (Figure 9):** quality curves for `β`, `Nmax`, `mc`, `m`, `λ` sit in roughly the **F-score 0.34–0.42** band; runtime curves for `β` span ~600–2400 s and for `Nmax` ~600–2700 s. "When `m ≥ 40`, the improvement is not obvious." "When `λ ≥ 0.7`, the extreme emphasis on coverage causes performance loss."
- **Flexibility (Figure 10):** precision/recall/F-score are plotted over timestamps 288–624 with F-score roughly in 0.34–0.44. Two findings: "as a time duration is closer to the current time, the summary quality improves"; and "A larger `l` leads to better results but more storage cost (the numbers in the parentheses represent the amounts of snapshots in PTF)" — `l = 3 (63)`, `l = 5 (173)`, `l = 8 (592)`. "for real-time summarization, a small l is enough; while for historical review, a large l is needed."
- **Timeline detection (Figure 11):** precision, recall, F-score vs. `τ ∈ [1.000, 1.020]`. "The recall declines as τ increases. ... **The precision and F-score both reach the highest value when τ = 1.012.** ... Surprisingly, when τ > 1.012, precision also drops. This may result from the incompleteness of our manual timeline or noises in the datasets."
- **Qualitative timeline output (Table 3, "Arsenal")** — detected nodes and representative tweets, e.g.:
  - `12.12`: "1. Yes Bradford! WENGER OUT. 2. Arsenal lose to Bradford: Should Arsene Wenger go? 3. Arsenal Chief Executive Ivan Gazidis has apologised to the club's fans..."
  - `12.16`: "1. Every arsenal fan knows how chelsea fans feel like right now. ... 3. RVP: 'I'm sorry to Arsenal fans...'"
  - `12.18`: "1. Arsenal vs Reading Come on arsenal ♯Arsenal 2. What a come back! Cazorla is a class!..."
  - `12.19`: "1. Good news for Arsenal fans: Wilshere, Oxlade-Chamberlain, Ramsey, Gibbs and Jenkinson sign new contracts. 2. ♯afc Arsenal's Premier League match against West Ham on Boxing Day is called off because of a possible tube strike. ..."
  - `12.20`: "1. Champions League draw: Manchester United v Real Madrid, Arsenal v Bayern Munich, Celtic v Juventus."
  - `12.22`: "1. Arsenal better win the game against wigan. 2. Wilshere hails Arsenal's fighting spirit after Wigan win."
  - Paper's comment: "our summary-based timeline not only detects important events (e.g. a match is called off due to a tube strike), but also contains popular public opinions (e.g. public calling for WENGER OUT)."
- **No absolute wall-clock throughput numbers** (tweets/sec) are given; runtime is reported only as per-window seconds in the figures.

## Implementation complexity

**High** (leaning toward **high**, not "very high" — the algorithms are all classical and fully specified, but there is a lot of moving machinery and no reference code).

Why:
- **Many coupled components must all be built and tuned:** Canopy+k-means initialization, incremental TCV clustering with Heuristic 1, focus-tweet-set maintenance, PTF snapshotting/retrieval, outdated-cluster deletion via an inverse-error-function percentile, greedy `O(N^2)` cluster merging with IDList bookkeeping and TCV aggregation, cluster-set subtraction across two snapshots, LexRank over `N·m` tweets, greedy MMR-style TCV-Rank selection with incremental novelty updates, and KL-divergence-based evolvement detection with a running `D_avg`.
- **The evaluation harness is itself substantial:** sliding-window re-implementations of **three** external baselines (ClusterSum, LexRank, DSDR — DSDR alone is a linear-reconstruction optimization), ROUGE-1 integration over sampled time integrals, and a multi-`l` PTF flexibility sweep.
- **Ground truth must be synthesized**, because the paper's own reference summaries were produced by a semi-automatic pipeline over the (now unavailable) data. A reproducer cannot just download labels.
- **Mitigating factor:** the paper is unusually explicit — Algorithm 1 and Algorithm 2 are given as pseudocode, Definitions 1/3/4 give exact arithmetic for aggregation and subtraction, all six main hyperparameters have concrete tuned values, and the complexity of each step is stated. Nothing requires training a neural model; no GPU is needed; the largest dataset is 438,884 tweets.

## Reproducibility obstacles (concrete)

1. **Dead artifact URL.** The paper's only availability claim, `http://db.zju.edu.cn/s/sumblr/`, now returns **HTTP 404** (verified). No mirror, no GitHub, no tweet-ID list is mentioned anywhere.
2. **Private/proprietary Twitter data.** Four of five datasets (Chelsea, Arsenal Arsene Wenger, Tablet Smartphone Cellphone, Black Friday, 2012.11–2012.12) were crawled "via Twitter's keyword tracking API" (footnote: `https://dev.twitter.com/docs/api/1.1/post/statuses/filter`). That endpoint is now behind paid X/Twitter API tiers, and the historical 2012 tweet stream cannot be re-crawled at all. The Obama set depends on a **third-party 2009 Twitter dataset from Chen et al. [5] (Ti, SIGMOD 2011)**, also not publicly hosted by this paper.
3. **Semi-synthetic, baseline-derived ground truth.** Reference summaries were "manually extracted from three candidate summaries" produced by ClusterSum/LexRank/DSDR, with priority to sentences in ≥2 candidates. This makes the labels (a) not independently reproducible without re-running the same three baselines, (b) contaminated by those baselines, and (c) acknowledged by the authors as "to some extent biased in favor of them." It also means a reproducer's ROUGE numbers are only comparable if they rebuild the labels the same way — which is a judgement call ("manually extracted") with no annotation guidelines, no inter-annotator agreement, and no annotator count.
4. **Manual timeline ground truth with no protocol.** Arsenal/Chelsea reference timelines were hand-built by reading "Yahoo! and ESPN" news. The dates, the definition of "important event," and the completeness of the reference are unspecified — the authors themselves note "the incompleteness of our manual timeline" as a confound. Table 3 shows only "Selected part of the timeline."
5. **UserRank / social-graph component is unusable.** `w_i` comes from a social-influence matrix computed as in [5], but "we do not have access to the respective users' social networks for these four" — so for 4/5 datasets `w_i = 1`. The social component is effectively never evaluated, and a reproducer cannot reconstruct the follower graph from 2012 Twitter.
6. **Unspecified values that matter:** `ε` (Laplace smoothing), `r` (LexRank iteration count), the number of tweets `k`/`L` per summary (only "250 words" is fixed), the number of tweets used for k-means initialization ("a small number"), the Canopy thresholds (T1/T2), the TF-IDF weighting details (which IDF corpus?), the tokenizer/stopword list/stemmer, and the exact `τ` sweep grid beyond 1.000–1.020.
7. **No released code for the three baselines** as the authors implemented them (sliding-window variants), so baseline numbers in Figures 5–7 cannot be checked against a canonical implementation.
8. **Figure-only quantitative targets.** The paper reports F-scores and runtimes almost entirely as plots with no data tables, so exact target numbers must be digitized from figures; only the narrative comparisons ("Sumblr faster than LexRank by nearly an order of magnitude above 15000", "τ = 1.012 best", "step size ≥ 12000 Sumblr wins") are textual.
9. **Tooling age.** `https://dev.twitter.com/docs/...` is a dead documentation host; `db.zju.edu.cn` is unreachable/404; the paper's data pipeline assumes a 2013 Twitter firehose that no longer exists in that form.
10. **Language/domain caveat for this course:** the paper is **English-only Twitter** despite the course theme covering Weibo. It offers no Chinese resource, so a Weibo reproduction would require full data substitution.

## Minimum viable reproduction plan (2–4 weeks)

**Goal:** rebuild the *algorithmic pipeline* faithfully and validate it on substituted data; treat the paper's numbers as directional rather than exact.

**Week 1 — data substitution and preprocessing.**
- Pick a public, legal substitute corpus with timestamps and topical subsets. Realistic options: a public tweet-ID dataset rehydrated to whatever fraction survives (e.g. a keyword-filtered subset of an academic Twitter dump), or a fully public alternative such as Reddit/Pushshift-style topical streams, news-headline streams, or an existing event-summarization benchmark. For a Weibo angle, use a public Weibo dataset (e.g. NLPCC/Weibo event datasets) — but note that this abandons comparability with the paper.
- Build **5 topical subsets** mirroring Table 2's shape (one politics, two sports, one tech, one shopping) with sizes on the order of 50k–150k items each if possible; even 10k–50k per topic is workable given `Nmax = 150` and `m = 40`.
- Implement the tweet tuple `(tv, ts, w)` with `w = 1` for everything (matching what the paper actually did for 4/5 datasets). Do **not** attempt UserRank.
- Fix and document: tokenizer, stopwords, stemming, TF-IDF/IDF corpus. This is unavoidable because the paper does not state them.

**Week 2 — Sumblr core.**
- Implement TCV per Definition 1 (sparse word-id → value dicts) and centroid `cv = wsum_v / n`.
- Implement Canopy + k-means initialization for `k` and initial centroids (or substitute plain k-means with `k` from a Canopy-style heuristic — document the deviation).
- Implement Algorithm 1 with Heuristic 1 using `β = 0.07`, `MBS = β · (wsum_v · sum_v)/(n · ||wsum_v||)`, focus-set maintenance with `m = 40`, snapshot storage when `TS % α^i == 0` with `α = 2` and `l ∈ {3, 5, 8}`.
- Implement outdated-cluster deletion with `µ_c`, `σ_c`, `p = 10`, 3-day freshness threshold (use `scipy.special.erfinv` in place of the Maclaurin expansion — a documented, equivalent substitution).
- Implement `Nmax = 150` greedy merging with `mc = 0.7`, IDList, and Definition 3 aggregation.
- Implement Definition 4 subtraction and the two-snapshot duration approximation.

**Week 3 — Summarization and evaluation.**
- Implement Algorithm 2: LexRank over `T = ∪ ft_set` (use `r ≈ 10` iterations; state the choice), then greedy selection with Equation (2) at `λ = 0.4`, two-stage (per-TCV `Tc` first, then global `T − S`), stopping at a 250-word budget. Choose a words-to-tweets mapping and document it (the paper says "the number of words and that of tweets are linearly dependent" but gives no ratio).
- Implement the sliding-window harness (window size 20000 or scaled down, step sizes 4000–20000 or proportional, sampling interval 2000) and re-implement **at least ClusterSum and LexRank** as baselines; add Random as a sanity floor. DSDR is the most expensive to re-implement — it is optional and can be replaced by a simpler MMR or TextRank baseline with the substitution clearly flagged.
- Build ground truth the paper's way: run ClusterSum/LexRank/DSDR(-substitute), then select sentences appearing in ≥2 candidates, cap at 250 words. This makes the comparison internally consistent even though it inherits the paper's bias.
- Evaluate with ROUGE-1 F-score (e.g. via `rouge` / `pyrouge` or a reimplementation), averaging over topics, and sample metrics by sampling interval.

**Week 4 — timelines, flexibility, write-up.**
- Implement KL-based evolvement detection (Equation 3, `D = 1 − e^{−D_KL}`, running `D_avg`, `τ` sweep around 1.0–1.02) and manually build a small reference timeline for one sports-like topic from public news (this is unavoidable human labor; budget 1–2 days).
- Reproduce the PTF flexibility sweep: one-month subset, one-hour snapshot interval, `len` 1–10 days, Equation (5).
- Produce the paper's figures: F-score vs. step size, runtime vs. step size, runtime vs. data size, F-score vs. `β`/`Nmax`/`mc`/`m`/`λ`, F-score vs. `l`, precision/recall/F-score vs. `τ`.

**What to substitute:** the datasets (mandatory), UserRank (drop, as the paper effectively did), `erf^{-1}` via SciPy (equivalent), DSDR (optional/simpler baseline), `ε` and `r` (pick and document), summary-length-to-tweet-count mapping (pick and document), and the 2009 Ti dataset (unavailable).

**Numbers to expect:** a faithful rebuild should land in the paper's reported band, i.e. **ROUGE-1 F-score roughly 0.35–0.45** with Sumblr near the top once the step size is large (≥12000 in the paper's scale), Sumblr's runtime essentially flat in step size while window-based baselines grow, and a clear efficiency win at large data sizes. Expect the **absolute** values to differ (different corpus, different ROUGE implementation, different tokenization); the reproducible claims are the **trends** — step-size invariance, flat runtime, sub-quadratic scaling versus LexRank/DSDR, and the qualitative shape of the parameter curves (optima near `β ≈ 0.07`, `Nmax ≈ 150`, `mc ≈ 0.7`, `m ≈ 40`, `λ ≈ 0.4`, `τ ≈ 1.01`). Treat timeline precision/recall as a soft target given the reference-timeline subjectivity.

## Verdict

Sumblr is a **good but demanding** reproduction target, and specifically a good one for a student who is comfortable with classical IR/NLP engineering and wants a system-building project rather than a model-training project. On the plus side, the paper is exceptionally explicit for a 2013 SIGIR paper: Algorithms 1 and 2 are printed as pseudocode, Definitions 1/3/4 pin down every arithmetic detail of the TCV structures, and every major hyperparameter has a concrete tuned value (`β = 0.07`, `Nmax = 150`, `mc = 0.7`, `m = 40`, `λ = 0.4`, `α = 2`, 3-day freshness, `p = 10`, 250-word summaries). It needs no GPU and no training data; the largest dataset is 438,884 tweets, so a laptop or a single modest server suffices. The task is also well aligned with the course theme — Twitter/Weibo stream summarization with timelines and topic evolvement — and the code is genuinely writable in 2–4 weeks. On the minus side, **the paper is not reproducible as literally specified**: its only artifact link (`http://db.zju.edu.cn/s/sumblr/`) is dead (HTTP 404, verified), four of five datasets came from a 2012 Twitter streaming API that cannot be re-crawled, the labels are semi-automatically derived from the very baselines being compared against (bias the authors admit), the timeline ground truth is informal manual news-reading with no protocol or agreement statistics, the UserRank/social-graph component is effectively unevaluated (`w_i = 1` for four datasets), and several consequential knobs (`ε`, LexRank `r`, tweets-per-summary, Canopy thresholds, tokenizer/IDF setup) are simply not stated. In practice a student reproduces the **architecture and the trends**, not the numbers: substitute a public timestamped corpus (English Twitter IDs that survive, or a public Weibo/event dataset if the Chinese angle matters), drop UserRank, re-derive ground truth with the paper's own pipeline, and expect ROUGE-1 F-scores in the ~0.35–0.45 band with the qualitative claims (step-size invariance, flat runtime, order-of-magnitude speedup over LexRank above ~15k tweets, optima near the stated parameter values) holding. It is a **poor** target for anyone who needs exact numeric replication, cheap baselines, or a ready-made dataset download; it is a **strong** target for a student who wants to build a real streaming system end-to-end and is willing to own the data-substitution and ground-truth-construction work as part of the project.
