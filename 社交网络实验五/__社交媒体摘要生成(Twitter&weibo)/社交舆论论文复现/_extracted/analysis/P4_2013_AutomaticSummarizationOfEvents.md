# Automatic Summarization of Events From Social Media

> Source text analysed: `_extracted/2013Automatic Summarization of Events From Social Media.txt` (991 lines, read in full).

## Bibliographic info (authors, venue, year)

- **Title:** Automatic Summarization of Events From Social Media
- **Authors:** Freddy Chong Tat Chua (Living Analytics Research Centre, Singapore Management University, 80 Stamford Road, Singapore) and Sitaram Asur (Social Computing Lab, Hewlett Packard Research Labs, Palo Alto, California, USA). Emails given in the paper: `freddy.chua.2009@smu.edu.sg`, `sitaram.asur@hp.com`.
- **Venue / year:** "Proceedings of the Seventh International AAAI Conference on Weblogs and Social Media" (ICWSM 2013). Running page numbers in the extracted text run from **81** to **90**. Copyright line: "Copyright c 2013, Association for the Advancement of Artificial Intelligence (www.aaai.org). All rights reserved."
- **Footnote on author:** "The work was completed when the author visited HPLabs in the summer of 2012."
- **Paper type:** full research paper, unsupervised probabilistic topic modelling + extractive summarization, with crowdsourced human evaluation.

## Task (what is summarized, input -> output, extractive vs abstractive)

**Formal problem definition, quoted verbatim:**

> "Given a time-ordered sample of tweets D representing an event of interest e, the task is to extract K number of tweets from D to form a summary S_e, such that each of these tweets d ∈ S_e adequately covers different aspects of the event e, where K is a choice of parameter that the human reader may choose, with larger values of K yielding longer summaries."

- **Input:** a time-ordered tweet sample `D` for a targeted event `e`, plus a set of keyword queries `Q` used to seed retrieval. "the event of interest can refer also to search terms used to query for tweets."
- **Output:** a summary `S_e` consisting of **K whole tweets** (one representative tweet per discovered topic). "Since we choose one tweet from each topic, then the number of topics K determines the number of selected tweets for the summarized event."
- **Extractive, not abstractive.** The output is literally a subset of the input tweets: "the task is to extract K number of tweets from D". The paper contrasts itself with abstractive work: "(Ganesan, Zhai, and Viegas 2012) have proposed the generation of abstract short text summaries from text... In our event summarization, we follow the traditional approach of finding an intermediate representation using topics and modeling n-grams using noun phrases in tweets."
- **Two sub-tasks are evaluated:** (1) summary quality (Wikipedia-referenced true summaries + MTurk), and (2) "Search Results" — retrieving *additional* relevant tweets `D_e2` that "do not contain the keywords in the queries".
- **Domain:** general social-media event summarization, covering "natural disasters, politics and company events". Language is English only (all four events and all queries are English).

## Method (core algorithm in implementable detail: model, components, features, objective, hyperparameters with values)

### Overall "Search and Summarize" framework (Figure 1)

The framework "performs search and summarization in a bootstrapping manner" and is iterative:

1. "From D, we extract all tweets that match at least one of the queries q ∈ Q. A tweet matches a query q if it contains **all** of the keywords in q. The set of tweets obtained is denoted by D_e1."
2. "Next, we apply a topic model on D_e1, to find keywords that describe the main aspects of the event that are being discussed. We have developed two topic models DTM and GDTM that are designed to extract relevant tweets."
3. "Once we have obtained the set of topics Z from the topic models, the top ranked words in each topic z ∈ Z are the keywords that describe various aspects of the event e. We may obtain the additional set of tweets D_e2 by finding tweets d ∈ D that are not present in D_e1 by selecting those with **high** perplexity score with respect to the topics." *(Note: this sentence contradicts step 5 and the later Search Results section, which both rank **ascending** — "lower perplexity being more relevant to event e". This is an internal inconsistency in the paper; treat "lower perplexity = more relevant" as the operative definition.)*
4. "D_e1 and D_e2 can be merged to refine the model and improve upon the topics for the event e."
5. "Using the final set of topics z ∈ Z, we can summarize the event e by selecting the tweets d from each topic z that give the best (lowest) perplexity."
- "The whole process can be performed for several iterations to improve the quality of the summary." (number of iterations: **not stated**)

Query example from the paper: for "Facebook IPO", `Q = { { facebook, ipo }, { fb, ipo }, { facebook, initial, public, offer }, { fb, initial, public, offer }, { facebook, initial, public, offering }, { fb, initial, public, offering } }`.

### Base representation: NP+LDA (noun-phrase LDA)

Motivation quoted: "Due to the noisy nature of tweets, it is typical to find that many of the words in a tweet contribute little or no information to the aspects of the target event."

- "we remove stop-words and only consider noun phrases by applying a Part-of-Speech Tagger to extract noun phrases using the following regular expressions":
  - `Base NP := determiner? adjectives* nouns+`
  - `Conj NP := Base NP (of Base NP)*`
- "We then model the noun phrases in tweets using the NP+LDA model as described in Chua et al. (Chua et al. 2012). Instead of generating a topic for every word, we only generate a topic for each noun phrase which may consist of several words". The reference is: Chua, F. C. T.; Cohen, W. W.; Betteridge, J.; and Lim, E.-P. 2012. *Community-based classification of noun phrases in twitter.* CIKM '12.
- "The subsequent topic models we propose in the rest of the paper extends from NP+LDA."

### Temporal correlation motivation

Claimed empirical observation (contribution 1): "given three tweets d1, d2, d3 ∈ D_e, that are written respectively at t1, t2, t3, suppose t1 << t2 << t3, then the similarity between d1 and d2 will be higher than the similarity between d1 and d3." Illustrated with word-frequency-over-time plots for the "Facebook IPO" event: `{ "date", "17", "may", "18" }` (launch date topic, Figure 3) and `{ "price", "28", "35", "38" }` (launch price topic, Figure 4); x-axis time bins are **days**.

Problem with short documents: "most of which consist of typically **20 to 30 words**", so "there is less likelihood for words to co-occur with one another across different documents". Fix: "we could arrange the set of tweets in a sorted order such that tweets written around the same time can 'share' words from other tweets to compensate for their short length."

### Decay Topic Model (DTM) — generative process

Notation from the paper: `p_{i,z}` = "the number of words in tweet d_i that belong to topic z"; `δ_z` = "the decay factor associated with topic z"; "The larger the value of δ_z, the faster the topic z loses its novelty"; `t_i` = "the time that tweet d_i was written"; `V` = total vocabulary size; `|np|` = number of words in the noun phrase; `|v ∈ np|` = number of times `v` appears in `np`; `q_{k,v}` = number of times `v` is inferred as topic `k`; `q_k` = number of words in topic `k`.

1. "For each topic z, sample the prior word distribution from a symmetric Dirichlet distribution, φ_z ∼ Dir(β)"
2. "For the first tweet d1 ∈ D_e, sample the prior topic distribution from a symmetric Dirichlet distribution, θ_d1 ∼ Dir(α)"
3. "For all other tweets d_n ∈ D_e, sample the prior topic distribution from an **asymmetric** Dirichlet distribution,"
   `θ_dn ∼ Dir( α + Σ_{i=1}^{n−1} p_{i,z} · exp[−δ_z (t_n − t_i)] )`
4. "For each noun phrase np in tweet d, sample a topic variable z_{d,np} from a multinomial distribution using θ_d as parameters. z_{d,np} ∼ Mult(θ_d)"
5. "For each noun phrase np, sample words w_{np,v} ... using topic variable z_{d,np} and the topic word distribution φ_z":
   `P(w_{d,np} | z_{d,np}=k, φ) = Π_{v∈np} φ_{k,v}`

**Computational notes given:** "Although the summation seems to involve an O(n) operation, the task can be made **O(1) via memoization**, a programming technique." The paper explicitly rejects duplicating inherited words because it "will inflate the corpus" and cause a "snowball effect".

**DTM collapsed Gibbs inference equation (verbatim):**
```
P(z_{d,np}=k | w_{d,np}, α, β, δ_k) ∝
  [ Π_{v∈np} Γ(β + q_{k,v} + |v ∈ np|) / Γ(β + q_{k,v}) ]
  · [ Γ(Vβ + q_k) / Γ(Vβ + |np| + q_k) ]
  · [ α + Σ_{i=1}^{n−1} p_{i,k} · exp(−δ_k (t_n − t_i)) ]
```

**Observed deficiency (the paper's own empirical finding):** "After performing inference on the set of tweets D_facebook ipo for the 'Facebook IPO' event, we observe the trend of the topics... Figure 6 shows the intensity (y-axis) of every topic... However, we are not able to observe a smooth transition of topics between different times." Diagnostic quantity: `E_day(z) = Σ_{d ∈ D_day} θ_{d,z}`.

### Gaussian Decay Topic Model (GDTM) — DTM + per-topic Gaussian time distribution

"The generative process for the Gaussian Decay Topic Model (GDTM) follows that of DTM with the addition of the time stamp generation for each noun phrase":

1. "In addition to topic word distribution φ_z, each topic z has an additional topic time distribution G_z approximated by the Gaussian distribution with mean µ_z and variance σ_z². G_z ∼ N(µ_z, σ_z²)"
2. "Then the time t for a noun phrase np is given by the following,"
   `P(t_np | z, G_z) = 1/√(2πσ_z²) · exp( −(t_np − µ_z)² / (2σ_z²) )`

**Decay parameter derivation via half-life (this is the key implementable novelty):**
- "We use the concept of half-life to estimate the value of δ_z. Given that we want to find the δ_z value that causes a tweet to discard half of the topic from previous tweet," `exp(−δ·(t_n − t_{n−1})) = 0.5` → `δ·ΔT = log 2` → `δ = log 2 / ΔT`.
- "The value of ΔT is affected by the variance (width) of the distribution. To estimate ΔT, let `ΔT = τ Δt` where **τ is a parameter** and Δt is estimated as follows," giving `Δt = √(2σ² log 2)`.
- **Equation (1):** `δ = log 2 / ( τ √(2σ² log 2) )`
- "As shown in Equation 1, the larger the variance σ² is, the smaller the δ (decay) and vice versa." Interpretation quoted: "Topics having small values of variance σ_z² indicate aspects that have short lifespans and should decay quickly (larger δ_z), while topics with large variance represent aspects that should decay slowly giving it a smaller δ_z."

**GDTM collapsed Gibbs inference equation (verbatim):**
```
P(z_{d,np}=k | w_{d,np}, α, β, δ_k, µ_k, Σ_k) ∝
  [ Γ(Vβ + q_k) / Γ(Vβ + |np| + q_k) ]
  · [ Π_{v∈np} Γ(β + q_{k,v} + |v ∈ np|) / Γ(β + q_{k,v}) ]
  · [ (1/√(2πσ_k²)) exp( −(t_np − µ_k)² / (2σ_k²) ) ]^{|np|}
  · [ α + Σ_{i=1}^{n−1} p_{i,k} · exp(−δ_k (t_n − t_i)) ]
```

**Why Gaussian (stated):** "we choose the Gaussian distribution because of the ease of computing sufficient statistics for inference using Gibbs Sampling. We also exploit the symmetry of Gaussian distribution in estimating δ. This symmetric property cannot be observed in most continuous distributions."

### Perplexity scores (used for both retrieval and tweet selection)

- **Eq. (2), tweet perplexity:** `perplexity(d) = exp( −log P(d | θ, φ, G) / N_d )`, "where N_d is the number of words in tweet d. Since tweets with fewer words tend to have higher probabilities and therefore lower perplexity, we normalized by N_d in order to favour tweets with more words."
- **Per-topic tweet perplexity:** "To choose the most representative tweet for topic z, we compute the perplexity with respect only to topic z for all tweets d ∈ D_e and choose the tweet that has lowest perplexity with respect to z."
  `perplexity(d, z) = exp( −log P(d, z | θ, φ_z, G_z) / N_d )`
- **Retrieval of D_e2:** "Instead of applying a threshold on selecting the top-k keywords for query expansion, we compute a perplexity score for each tweet d ∈ D, d ∉ D_e1. Tweets relevant to the event e are then ranked in ascending order with lower perplexity being more relevant to event e."
- **Summarization objective (multi-objective, described but not formalized as a single loss):** "On one hand we want to select tweets such that we maximize the total perplexity using as few tweets as possible. But we also want the topic overlap between the selected tweets to be as low as possible." In practice, diversity is obtained by taking exactly one tweet per topic: "The list of representative tweets for each topic forms the summary of the event e."

### Hyperparameters stated in the paper

| Parameter | Value stated |
|---|---|
| Dirichlet prior constants α, β | "The constants for the prior distributions are set as **0.1**" (footnote 1) — same for the LDA baseline |
| Number of topics K | **K = 8** and **K = 10** ("to obtain 8-tweet summaries and 10-tweet summaries for each event"); "We choose these values of K to avoid generating long summaries for the events so that the human evaluation task in Mechanical Turk will be easier" |
| τ (decay scale in Eq. 1) | "τ is a parameter" — **value not stated** |
| Gibbs sampling iterations / burn-in | **not stated** |
| δ_z values | **not tabulated**; derived from σ_z² via Eq. (1) |
| Number of framework iterations (D_e1 ∪ D_e2 refinement rounds) | **not stated** ("several iterations") |
| POS tagger used | **not stated** (only "a Part-of-Speech Tagger") |
| Vocabulary size / stopword list / tokenization | **not stated** |
| Summary length | 8 tweets (K=8) and 10 tweets (K=10) |

## Datasets (names, sizes, language, domain, HOW OBTAINED - crawled by authors? public? URL given?)

Four real-world events, all English, all Twitter. Sizes are exactly as stated in the paper:

| # | Event | Queries used | # tweets | Domain |
|---|---|---|---|---|
| 1 | **Facebook IPO** | `{ { (Facebook — FB), IPO }, { (Facebook — FB), Initial, Public, (Offer — Offering) } }` | **9,570** | company event |
| 2 | **Obamacare** (Patient Protection and Affordable Care Act) | `{ { Obamacare }, { PPACA }, { Obama, Health, Care }, { Obama (Healthcare — Health-care) } }` (the hyphen in "Health-care" is a line-break artifact in the extracted text) | **136,761** | politics |
| 3 | **Japan Earthquake** (2011 Tōhoku) | `{ { Fukushima }, { (Japan — Tokyo), (Earthquake — Quake — Tsunami } }` (the closing paren is missing in the source text) | **251,802** | natural disaster |
| 4 | **BP Oil Spill** (Deepwater Horizon) | `{ { BP, Oil, Spill }, { Gulf, Mexico, Oil, Spill } }` | **79,676** | natural disaster / company |

Quote on scale: "the number of tweets for these events ranges from a small 9,570 tweets for Facebook IPO to a mammoth 251,802 tweets for the Japan Earthquake."

**How obtained (quoted):** "We have used the **Twitter search API** to extract the tweets relevant to our four events." The authors also note this is extensible: "This can also be done in an incremental manner to gain full coverage of an ongoing event." The paper also assumes: "we have access to a time-ordered sample of tweets. This can be obtained via a set of search queries Q".

**Ground-truth summaries** are also constructed, not collected from annotators: "Due to the difficulty of obtaining human generated summaries from our data sets, we construct the true summaries by using the **headlines of news articles found in the reference section of the events' Wikipedia articles**." The four Wikipedia article URLs given (as "web a"–"web d"):
- `http://en.wikipedia.org/wiki/2011_Tōhoku_earthquake_and_tsunami`
- `http://en.wikipedia.org/wiki/Deepwater_Horizon_oil_spill`
- `http://en.wikipedia.org/wiki/Facebook_IPO`
- `http://en.wikipedia.org/wiki/Patient_Protection_and_Affordable_Care_Act`

No train/dev/test split is used; no held-out set is used for the main evaluation (the paper explicitly rejects perplexity/log-likelihood comparison as an evaluation route: "We therefore evaluate the temporal correlation and the two derivative models by comparing 1) the quality of the summaries ... and 2) their utility towards finding additional tweets"). No folds, no cross-validation.

## Data/code availability stated in the paper (quote any URL, 'available at', 'we will release', download link; if none, say NONE)

**NONE.** The paper contains **no** statement that the tweet data, tweet IDs, annotations, models or code will be released or are available at any URL. There is no "available at", no "we will release", no GitHub link, no download link. The only URLs in the entire paper are:

1. `www.aaai.org` in the copyright line (publisher, not data).
2. The four Wikipedia event articles listed above (web a–web d), which are the *source of the reference/true summaries*, not the tweet data.
3. Bibliographic reference URLs only in the citation entries (there are none beyond the Wikipedia ones).

There is likewise no stated data-sharing arrangement, no MTurk task template link, and no appendix with the generated summaries.

## Evaluation (metrics, human evaluation required? protocol, folds)

Three separate evaluations; **human evaluation is required for one of the three and is a major part of the paper's claims.**

### (A) Quantitative comparison against Wikipedia-derived true summaries

- True summary construction: "For each of the Wikipedia references for our events, we extract the **headline text** which gives a one-line summary of the corresponding news article... To construct a true summary for each event from its corresponding Wikipedia article, we **aggregate the one-line summaries of all the news articles referenced** in the Wikipedia article."
- Metric: "adapted from the **ROUGE** metric proposed by Lin and Hovy (Lin and Hovy 2003)". It "counts the total number of matching n-grams (**excluding stop-words**) between the true summary S_tr and the summary S_m generated from model m."
  - Eq. (3): `g_n = Σ_{ng ∈ NG^m_n} min(|ng ∈ NG^tr_n|, |ng ∈ NG^m_n|)` — "In order not to let a few frequent n-gram dominate the counts, each n-gram is limited to the minimum number of counts between the true summary and the generated summary."
  - Eq. (4): `Sim(S_tr, S_m) = 0.2·g_1 + 0.3·g_2 + 0.5·g_3` — "The weights allocated are meant to give a higher importance to 3-grams and lower importance to 1-grams."
- Settings: K = 8 and K = 10 (two separate result figures, Figures 9(a) and 9(b)).
- Figure 9 y-axis range: 0 to 20 ("Sim(S_tr, S_m)").

### (B) Qualitative evaluation on Amazon Mechanical Turk (human evaluation — REQUIRED)

- Protocol quoted: "To each mechanical turk worker (mturker), we presented the generated summaries of the four events from each model. Since each event has three summaries from the three models, mturkers were instructed to **choose 1 or 2 out of the 3 summaries** as the best representations of the event. We also provided a feature for mturkers to leave comments."
- Bias controls: "we did **not** show which model generated the summaries and we **randomized the order** of presented summaries."
- Worker qualifications: "1) have **approval rating of ≥ 95%**, 2) have completed **more than 1000 tasks**, and 3) are **located in United States (USA)** because the events 'Facebook IPO', 'Obamacare' and 'BP Oil Spill' are more relevant to the population of USA."
- Scale: "We employed a total of **100 different mturkers**. Each mturker spent an average of **7 minutes and 10 seconds** to complete the task which translated to an hourly wage of approximately **USD$4.2**."
- Metric: number of votes per model, aggregated across events (Figure 10, y-axis "# of votes", 0–70 per event).

### (C) Search Results — precision/recall of the additional tweet set D_e2

- Relevance is graded by n-gram overlap, not binary: "we do not make a binary decision as to whether each tweet is relevant to the event. Instead, we compute the number of n-grams that matched between the top-k tweets and the true summary."
- Formulas given: `g_n = Σ_{np ∈ NG^{top−k}_n} min(|ng ∈ NG^tr_n|, |ng ∈ NG^{top−k}_n|)`; `PR^n_k = g_n / |D^{top−k}|`; `RC^n_k = g_n / |NG^tr_n|`; and `PR_k = 0.2·PR1_k + 0.3·PR2_k + 0.5·PR3_k`, `RC_k = 0.2·RC1_k + 0.3·RC2_k + 0.5·RC3_k`.
- "Varying k from 1 to the size of the tweet sample gives the Precision-Recall curve (PR-curve) as shown in Figure 11."
- Figure 11 axes: Precision 0–0.02, Recall 0–0.7.

**No folds, no cross-validation, no significance testing, no inter-annotator agreement** are reported.

## Baselines (list them)

1. **LDA** — the single explicit baseline. "we evaluate the two models DTM and GDTM with respect to the LDA baseline. Unlike our DTM and GDTM models, the LDA baseline does not consider the use of noun phrases and assumes that every tweet has no temporal relation to other tweets." Its prior constants are also 0.1 (footnote 1).
2. **DTM (Decay Topic Model)** — the authors' own intermediate model, effectively also a comparison point against GDTM.
3. **GDTM (Gaussian Decay Topic Model)** — the authors' proposed best model.

So the comparison is a 3-way LDA vs DTM vs GDTM, i.e. only **one** external baseline. The paper does not compare against Phrase Reinforcement (Sharifi et al. 2010), NNMF (Yang et al. 2012), TM-LDA (Wang, Agichtein, and Benzi 2012), Topics-over-Time (Wang and McCallum 2006), or Metzler et al.'s structured retrieval, even though all are discussed in Related Work.

## Reported results (key numbers, so a reproducer knows the target)

- **MTurk votes aggregated over all four events (Figure 10):** "**GDTM has the most number of votes with 207 votes followed by DTM with 146 votes and finally LDA with 130 votes**." (207 + 146 + 130 = 483 votes total; 100 mturkers × ~4–5 votes each.)
- **Wikipedia-based Sim(S_tr, S_m), K = 8 and K = 10 (Figures 9(a), 9(b)):** "GDTM consistently gives better performance than LDA. **DTM is shown to be better than GDTM for 'Obamacare' at K=8** in Figure 9(a) and **'Facebook IPO' at K=10** in Figure 9(b). Overall, GDTM shows better performance over DTM and LDA with DTM showing inconsistent performance. DTM is sometimes better than LDA and sometimes slightly worse-off than LDA. This suggests that estimating the appropriate decay parameters is important for using the temporal correlation features."
  - **Exact Sim values are NOT tabulated anywhere in the text** — they exist only as bar heights in Figure 9 with a y-axis running 0–20. The text gives no per-event numeric scores. This is a hard target-number gap for a reproducer.
- **Search / D_e2 PR curve (Figure 11):** "Figure 11 shows us that the results given by **GDTM is significantly better than DTM and DTM is in turn better than LDA**." Magnitudes are very small: "The precision and recall does not give high values because the true summaries are keywords from Wikipedia articles which are different corpus from the generate summaries." (Precision axis tops out near 0.02.)
- **Qualitative MTurk comments quoted in the paper (5 examples):**
  1. "I think these (GDTM) best summarize Facebook IPO because it shows a broad range of information related to the event."
  2. "Well I learned that their co-founder renounced his US citizenship just now!"
  3. "I believe that other summaries (non-GDTM) had a large amount of personal opinion and not fact."
  4. "If I wanted to find information, Summaries (DTM) and (GDTM) had the most."
  5. "There is too much garbage posts in the other summaries (non-GDTM), and not true news."
- **Qualitative temporal plots:** Figure 6 (DTM topic intensity) shows topics not well separated in time; Figure 8(a) (GDTM) shows better chronological differentiation; Figure 8(b) shows the per-topic Gaussian components (y-axis scaled "x 10⁻⁹", range 0–1.8).

**Reproduction targets to aim for:** (i) GDTM > DTM > LDA ordering in a ROUGE-style weighted n-gram score against Wikipedia news headlines; (ii) GDTM > DTM > LDA ordering in human preference votes, with an approximate 207 : 146 : 130 split; (iii) GDTM > DTM > LDA ordering in the D_e2 precision–recall curve with very low absolute precision (< 0.02).

## Implementation complexity (low/medium/high/very high + WHY)

**HIGH.**

Reasons:
- **Two novel collapsed Gibbs samplers must be derived and implemented from scratch.** DTM and GDTM are not in any library. The GDTM posterior includes a per-topic Gaussian time term raised to the power `|np|`, a per-topic half-life-derived decay `δ_k`, and a memoized `O(1)` prefix sum `Σ_{i=1}^{n−1} p_{i,k}·exp(−δ_k(t_n − t_i))` over *all* earlier tweets. That memoized recurrence (updating the running sum as tweets arrive in time order, per topic, with per-topic δ) is the single trickiest engineering piece, and the paper describes it in one sentence ("the task can be made O(1) via memoization, a programming technique") without giving the recurrence.
- **NP+LDA plumbing:** POS tagging + the two chunk regexes (`Base NP`, `Conj NP`), stopword removal, and a topic assigned per *noun phrase* rather than per word, following Chua et al. 2012 (CIKM) — a second paper the student must also read and reimplement.
- **Two distinct perplexity computations** (`perplexity(d)` over all topics, and `perplexity(d,z)` per topic) plus an iterative bootstrap loop that re-trains on `D_e1 ∪ D_e2`.
- **Scale:** 9,570 → 251,802 tweets per event × 2 models × 2 values of K, with the DTM/GDTM Gibbs samplers being much heavier per iteration than vanilla LDA. Feasible on a laptop for the small event, slow for the Japan Earthquake event.
- **Evaluation cost:** the paper's headline evidence is a 100-worker MTurk study with US-only, ≥95%-approval, >1000-task workers and a paid wage; plus extraction of news headlines from a specific historical revision of four Wikipedia articles.
- Not "very high" because: everything is unsupervised (no training labels), the mathematics is fully specified in the paper, the components (LDA, Gibbs sampling, POS chunking, ROUGE-style n-gram overlap) are all standard, and there is no neural architecture or large-scale compute.

## Reproducibility obstacles (concrete: private Twitter API data, crowdsourced labels, dead tools, huge compute, unavailable lexicons, Chinese/Arabic resources, unspecified hyperparameters)

1. **The tweet data is not released and cannot be re-collected.** The paper says only "We have used the Twitter search API to extract the tweets relevant to our four events." No tweet IDs, no dataset URL, no "available at", no "we will release". The events are from **2011–2012** (Facebook IPO = May 2012; Japan Earthquake = 2011). Twitter's search API at the time allowed historical keyword search; the modern API does not. Post-2023 API tiers and the discontinuation of the Academic Research track make historical keyword search for 2011–2012 effectively impossible without already holding the data. **This alone makes exact reproduction infeasible.**
2. **Ground-truth summaries are time-dependent and were never frozen.** The "true summaries" are the news headlines referenced in the *reference sections of Wikipedia articles*. Wikipedia reference sections change continuously; the paper does not give the article revision IDs or the snapshot date, and does not list which headlines were used. A reproducer pulling the same articles today will get a different (likely larger) reference set and therefore different `Sim` scores.
3. **Exact headline extraction procedure is unspecified.** "we extract the headline text" — from the citation template, the `<ref>` title attribute, or the article title? Not stated. This materially changes `g_1, g_2, g_3`.
4. **Key hyperparameter τ is not given a value.** `ΔT = τ Δt` with "τ is a parameter" — no number anywhere. Since `δ = log2/(τ√(2σ²log2))` controls the entire temporal decay of GDTM, the central novelty cannot be numerically matched. The reader can only infer the *direction* (larger σ² → smaller δ).
5. **Gibbs sampling schedule unspecified:** number of iterations, burn-in, whether δ_z, µ_z, σ_z² are re-estimated each iteration (and from which statistics), and the update order — none stated. Results for topic models are sensitive to these.
6. **Number of framework bootstrap iterations unspecified** ("several iterations"), as is the size of `D_e2` selected per round and whether perplexity thresholds are used.
7. **No per-event numeric results are published.** Figure 9 has no data table; only bar heights on a 0–20 axis. The reproducer cannot know the target `Sim` value, only the model ordering.
8. **Internal inconsistency about the D_e2 selection direction** ("high perplexity" in the framework step 3 vs "ascending order with lower perplexity being more relevant" later). Ambiguous as written.
9. **Human evaluation requires paid crowdsourcing.** MTurk with US-only, ≥95% approval, >1000 completed tasks, 100 workers, ~7 min 10 s each at ~USD$4.2/hr. Not reproducible for a course project without budget, an MTurk requester account, and a US worker pool; and the 2013 MTurk worker population is not the 2020s population.
10. **Baseline ambiguity:** the "LDA baseline" is non-standard (bag-of-words over raw tweets, no noun phrases, α=β=0.1, unspecified iteration count and unspecified tokenizer/stopword list), so its exact numbers are not pinned down.
11. **POS tagger and tokenizer are unnamed** ("applying a Part-of-Speech Tagger"), and the noun-phrase regexes use linguistic categories (`determiner? adjectives* nouns+`) that map differently onto different tag sets (Penn Treebank vs Universal Dependencies).
12. **Minor:** Figure 3/4/6/8 axis labels are garbled in the extracted text ("Tiime (ms)" for what is described as day bins), so the exact binning and units used for the temporal figures cannot be read off reliably.
13. **No code, no model files, no lexicon dependency** — the approach needs no external lexicon, which is a mild plus, but there is also nothing to bootstrap from.

## Minimum viable reproduction plan (what a student could realistically build in 2-4 weeks, what to substitute, what numbers to expect)

**Realistic scope: reimplement LDA + NP+LDA + DTM + GDTM and reproduce the *ordering* of results on 1–2 substitute events. Exact numbers from the paper are not attainable — aim for the qualitative claims.**

**Week 1 — Data substitution.**
- Abandon the four original events (unrecoverable). Pick 1–2 events that have *publicly released Twitter data with IDs or text*, for example: an event from a released crisis/event tweet collection (e.g. CrisisLex/CrisisNLP collections, or a released event-tweet dataset with tweet IDs), or a fresh event crawled over 2–4 weeks with `snscrape`/a Twitter API developer key (if the student has one).
- Target size: match the paper's small event (≈10k tweets, Facebook-IPO-like) for the fast path, and optionally one ≈80k–130k event. Do not attempt 250k on a laptop with a custom Gibbs sampler unless prepared for long runtimes.
- Substitute the "true summary" with: (a) the current Wikipedia article's reference headlines via the MediaWiki API (`action=parse` / `prop=extracts`), documenting that this is a later revision than the original; or (b) GDELT/news headlines for the event window (deterministic, timestamped, and arguably closer to the 2013 snapshot). Report which one was used.
- Preprocessing to match: tokenize, lowercase, remove stopwords, POS-tag, and extract noun phrases with the paper's regexes `Base NP := determiner? adjectives* nouns+` and `Conj NP := Base NP (of Base NP)*`.

**Week 2 — Models.**
- `LDA` baseline: gensim/sklearn LDA on raw bag-of-words, α = β = 0.1, K ∈ {8, 10} — cheap and gives the reference point.
- `NP+LDA`: reimplement the noun-phrase-level topic assignment (topic per NP, not per word) as a collapsed Gibbs sampler, or approximate with gensim LDA over concatenated noun-phrase tokens (document this as an approximation).
- `DTM`: collapsed Gibbs with the asymmetric Dirichlet prior `α + Σ_{i<n} p_{i,k}·exp(−δ_k(t_n − t_i))`; implement the memoized per-topic running sum by processing tweets in timestamp order and updating `S_k ← S_k·exp(−δ_k·Δt) + p_{n−1,k}` at each step. δ_k can be initialized at a constant (e.g. δ = log2/ΔT with ΔT = one day) and re-estimated from the topic time variance.
- `GDTM`: add per-topic Gaussian `(µ_k, σ_k²)` over NP timestamps; set `δ_k = log2 / (τ·√(2σ_k² log2))`; since τ is unpublished, **fix τ = 1 and state this substitution explicitly**, then run a small sensitivity sweep (τ ∈ {0.5, 1, 2}) and report it — this is a genuinely useful contribution given the paper's omission.

**Week 3 — Summarization + quantitative evaluation.**
- Select one lowest-perplexity tweet per topic → K-tweet summary. Implement both `perplexity(d)` and `perplexity(d, z)` exactly as Eqs. (2) and the per-topic form, normalizing by `N_d`.
- Implement the ROUGE-style metric `Sim = 0.2·g_1 + 0.3·g_2 + 0.5·g_3` with the `min(count)` capping and stopword exclusion, matching Eqs. (3)–(4).
- Implement the D_e2 retrieval evaluation: rank `D \ D_e1` ascending by perplexity, compute `PR^n_k`, `RC^n_k`, then `PR_k = 0.2·PR1_k + 0.3·PR2_k + 0.5·PR3_k` and the recall analogue; plot PR curves per model.
- Sanity check against the paper's qualitative claim: GDTM > DTM > LDA.

**Week 4 — Human evaluation substitute + write-up.**
- Replace MTurk with a small in-class study: 15–30 raters, each shown the 3 blinded, order-randomized summaries per event and asked to "choose 1 or 2 best", replicating the paper's protocol exactly. Report vote counts alongside the 207/146/130 benchmark *as a proportion*, not as an absolute comparison (100 US workers ≠ 20 classmates).
- Also run the paper's own diagnostic: plot per-day expected topic intensity `E_day(z) = Σ_{d∈D_day} θ_{d,z}` for DTM and GDTM to check whether GDTM really produces better time separation (the paper's Figure 6 vs Figure 8(a) claim).

**Expected numbers to expect (and to report honestly as "in the same regime as" the paper):**
- `Sim(S_tr, S_m)` values will be small non-negative numbers on roughly the 0–20 axis of Figure 9, with **GDTM ≥ DTM ≥ LDA in most events** and occasional DTM wins (the paper itself reports DTM > GDTM for Obamacare at K=8 and Facebook IPO at K=10, and DTM sometimes *worse* than LDA). Do not expect a clean sweep.
- Human votes should trend **GDTM > DTM > LDA** (paper: 207 / 146 / 130).
- D_e2 precision will be **very low (order 10⁻³–10⁻²)** with recall reaching ~0.4–0.7 at large k — the paper attributes this to the Wikipedia corpus mismatch, and a reproducer should expect the same, since it is a property of the metric, not the model.
- Success criterion for the course project should be **reproducing the ordering and the ablation conclusion** ("estimating the appropriate decay parameters is important for using the temporal correlation features"), not matching magnitudes.

**Minimum viable fallback if data collection fails:** run the whole pipeline on any public tweet dataset with timestamps and a known event (even a 5k-tweet single-event dump), report that the four original events were unavailable, and evaluate with an intrinsic temporal-coherence diagnostic (`E_day(z)` separation) plus the human preference study. That still tests the paper's central hypothesis.

## Verdict (one paragraph: how good a reproduction target is this paper, and for whom)

This is a **medium-to-poor exact-reproduction target but an excellent method-reimplementation target**. The exact reproduction is essentially impossible: the four event tweet sets (9,570 Facebook IPO / 136,761 Obamacare / 251,802 Japan Earthquake / 79,676 BP Oil Spill) were collected with the 2013 Twitter Search API and are not released — there is **no data URL, no code URL, no "available at", no "we will release" anywhere in the paper** — and the "true summaries" are derived from Wikipedia reference sections that have since drifted. On top of that, the key decay hyperparameter τ has **no stated value**, the Gibbs sampling schedule is unspecified, and the paper publishes no per-event numeric scores (only bar heights in Figures 9–11). What makes it a *good* target is that it is entirely unsupervised and fully specified mathematically: the DTM and GDTM collapsed Gibbs posteriors, the half-life derivation `δ = log2/(τ√(2σ²log2))`, the NP regexes, the perplexity formulas, and the `0.2/0.3/0.5` weighted n-gram metric are all given explicitly, so a competent student can reimplement LDA → NP+LDA → DTM → GDTM in numpy/gensim in 2–3 weeks and test the paper's real claim (does per-topic temporal decay improve extractive tweet summaries?) on substitute public event data, substituting a small in-class rater study for MTurk. It is best suited to a student comfortable with **probabilistic graphical models and hand-written Gibbs samplers** who wants a mathematically substantive, literature-anchored project and is willing to accept that the deliverable is "reproduces the reported ordering and the ablation finding", not "reproduces the reported numbers".
