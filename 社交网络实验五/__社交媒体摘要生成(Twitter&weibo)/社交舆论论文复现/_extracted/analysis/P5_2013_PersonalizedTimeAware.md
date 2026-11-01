# Personalized Time-Aware Tweets Summarization

> Source file analyzed: `_extracted/2013Personalized time-aware tweets summarization.txt` (880 lines, ~95 KB, full text read end to end).
> Everything below is drawn from that text. Where the extracted text is garbled or the two-column layout dropped text, this is flagged explicitly.

## Bibliographic info (authors, venue, year)

- **Authors:** Zhaochun Ren (ISLA, University of Amsterdam, z.ren@uva.nl), Shangsong Liang (ISLA, University of Amsterdam, s.liang@uva.nl), Edgar Meij (Yahoo! Research, Barcelona, Spain, emeij@yahoo-inc.com), Maarten de Rijke (ISLA, University of Amsterdam, derijke@uva.nl).
- **Venue / year:** SIGIR'13, July 28–August 1, 2013, Dublin, Ireland. Copyright line: "Copyright 2013 ACM 978-1-4503-2034-4/13/07 ...$15.00."
- **Categories:** "H.3.3 [Information Search and Retrieval]: Information filtering".
- **Keywords:** "Twitter, tweets summarization, data enrichment, topic modeling".
- **Task name used by the authors:** TaTS = personalized, time-aware tweets summarization.

## Task (what is summarized, input -> output, extractive vs abstractive)

**Extractive, tweet-level selection, personalized and time-segmented.**

- Problem statement quoted: "We focus on the problem of selecting meaningful tweets given a user's interests; the dynamic nature of user interests, the sheer volume, and the sparseness of individual messages make this an challenging problem." (Abstract)
- Formal definition quoted: "given a set of tweets D, a set of time periods T , and a maximum number of tweets per period, N , time-aware tweets summarization aims to extract multiple sets of tweets RTt (1 ≤ t ≤ T ) from D, where for each time period t, RTt = {dt,x1 , dt,x2 , . . . , dt,xN } is a set of representative tweets that summarize the period."
- Personalization is added on top: "personalized time-aware tweets summarization is defined similar to time-aware tweets summarization, but in this case the tweets selected for inclusion in RTt need to be relevant based on u's interests θu at time t."
- **Input:** a tweet collection D (candidate tweets Dt per period), a user u's own history Du,t, the user's social circles Cu,t (friend cliques), a time segmentation T, and a budget N. Optionally enriched with Wikipedia sentences.
- **Output:** for each time period t, a ranked/selected set RTu,t of N tweets for user u ("The output is the time-aware tweets summary, i.e., a selection of tweets (per period) satisfying the user's interest.").
- **Unit of summary:** whole tweets ("Most work in the literature concerns tweets as basic constituents to compose a summary"), not generated sentences → extractive. No abstractive generation anywhere in the method.
- Distinction from related work quoted: "The task is similar to tweet recommendation, but tweets summarization pays more attention to the quality of selected results, including notions such as representativeness and diversity."
- Three quality criteria the selection must satisfy: "novelty, preventing near-duplicate tweets to be included, (b) coverage, so as to be representative to candidate tweets, (c) diversity, covering as many aspects as possible."

## Method (core algorithm in implementable detail)

The pipeline has four stages: (1) **data enrichment** (entity linking + Wikipedia sentence extraction), (2) **TPM topic modeling** (Tweet Propagation Model), (3) **Gibbs EM inference** with hyperparameter re-estimation, (4) **iterative tweet selection** optimizing novelty/coverage/diversity. Notation is given in Table 1 (K topics, U users, V vocabulary, T periods, Dt candidate tweets at t, Cu,t social circles, θu,t user interests over topics at t, ϑt topic distribution of a tweet at t, φt word distribution over topics at t, λu,c,t weight of social circle c, N max tweets returned, hyperparameters β, α, σ, r).

### 0. Data enrichment (Section 5.1)

- Motivation quoted: "Since each tweet is only up to 140 characters long, the amount of textual evidence to work with is very limited."
- Entity linking via CMNS ([20] Meij et al., WSDM 2012): "CMNS (c, q) = |Lq,c| / Σc0 |Lq,c0|" (Eq. 13), "where Lq,c denotes the set of all links with anchor text q and target c."
- Then: "After we have obtained three Wikipedia articles with the highest CMNS score, we extract the most central sentences from these Wikipedia articles and append them to the tweet. In particular, we apply a query-sensitive graph-based summarization method, similar to [10] [Erkan & Radev, LexRank], to each Wikipedia article to ranking sentences, using the tweet dt as the query. This calculates the score of each sentence via 'votes' from other sentences in a document."
- Concrete example given in Figure 5, e.g. tweet "whenever i see lily tomlin, i call her debbie fiderer" → appended sentences from the Lily Tomlin article ("She is Executive Assistant to the President, and is portrayed by noted actor and comedienne Lily Tomlin", "She appeared on the dramatic series The West Wing for four years (2002–2006) ...").
- Note: "A mixture of the tweet and extracted wiki sentences will replace the original tweet in our experiments."

### 1. TPM — Tweet Propagation Model (Section 4.1)

A dynamic extension of the author-topic model [26]: "As a dynamic extension of the author-topic model [26], our proposed Tweet Propagation Model (TPM) aims to track both a user's interests and any topic drift arising with the passing of time."

**Social circle definition:** "If two users ui and uj follow each other, we define them to be friends on Twitter. Given this definition, we define a social circle around a user u to be a set of friends of u such that every pair of users in this set is in the friend relation." (Figure 1 shows two social circles among five users.) Also stated: "'social circles,' in which three or more users follow each other and form cliques."

**Interest decomposition into three topic classes:** "we split the topic set Zt at time t into three classes: Zt = Ztu ∪ Ztcom ∪ ZtB: there exist 'private' topics Ztu that solely depend on the user, there are common topics Ztcom that are influenced by friends from shared social circles, and there are topics from event-related, bursty sources, ZtB. The latter type of topic will typically transfer from initially being observed at time t into Z com at some later time t0."
And: "θu,t = {θu,t,z1 , · · · , θu,t,zK }" with the composition "θu,t = (θcom u,t , θBu,t , θu u,t)".

**Equation (1) — common/bursty interest propagation:**
xcom u,t = αu,t · θcom+B u,t−1 + (1 − αu,t) · Σ_{ci ∈ Cu,t−1} λci · θcom+B ci,t−1
where "θcom+B u,t−1 refers to the set {θcom u,t−1 , θB u,t−1 }" and "θcom+B ci,t−1 is equal to (1/|Cu,t−1|) Σ θui,t−1 , where ui ∈ Cu,t−1". "The hyperparameter αu,t indicates the weight of θcom+B u,t−1 in Equation 1."

**Dynamic propagation of word distributions:** "for common topics z ∈ Ztcom, we use the Dirichlet distribution to infer from φcom t−1 , φB t−1; for private topics z ∈ Ztu, φut is derived from φut−1." Weighted prior βt = {βtcom , βtu}.

**Bursty words:** "Similar to [32], we define a keyword to be 'bursty' if its frequency nw,t at time t is above a threshold value. We derive θB u,t from a Dirichlet distribution over the hyperparameter αB t." (The threshold value itself is **not stated**.)

**Generative process (Figure 3), verbatim structure:**
1. For each topic z ∈ Ztcom ∪ ZtB ∪ Ztu: draw φB t ∼ Dir(βB t ); draw φcom t ∼ Dir(βtcom ⟨φcom t−1 , φB t−1⟩); draw φut ∼ Dir(βtu ⟨φut−1⟩).
2. For each candidate tweet dt ∈ Dt: draw ϑt ∼ Dir(αt, αB t ); rt ∼ Dir(γt); for each word w in dt: draw q ∈ Multi(r); zw ∼ Multi(ϑt); if q = 0 draw w ∼ Multi(φcom z,t ); if q = 1 draw w ∼ Multi(φuz,t); if q = 2 draw w ∼ Multi(φB t ).
3. For user u ∈ U: draw θu,t ∼ Dir(⟨xuu,t , xcom u,t , αB t ⟩); draw πt ∼ Dir(σt); for each word w ∈ du,t: draw e ∼ Multi(π); zw,t ∼ Multi(θu,t); if e = 0 draw w ∼ Multi(φcom z,t ), e = 1 → Multi(φuz,t), e = 2 → Multi(φB t ).

So each word carries two latent switches: `e` (private / common / bursty for the *user* branch) and `q` (the same three-way switch for the *candidate tweet* branch).

### 2. Inference — Gibbs EM (Section 4.2, Algorithm 1)

- Quoted: "unlike many previous dynamic topic models, to infer weighted priors we use a Gibbs EM algorithm [29] [Wallach, ICML 2006] to handle the approximate posterior inference step."
- Sampling for user tweets, Eq. (2):
  p(ei = l, zi = z | W, e−i, Z−i, xu,t, σ, βtu) ∝ (n^{u,t}_{d,l,−i} + σ)/(n^{u,t}_{d,−i} + 3σ) · (n^{u,t}_{d,z,−i} + x^l_{u,z,t})/(Σ_{z0} n^{u,t}_{d,z0,−i} + x^l_{u,z0,t}) · (n^{u,t}_{w,z,−i} + β^l_t)/(Σ_{w0} n^{u,t}_{w0,z,−i} + N_{u,t} β^l_t).
- Sampling for candidate tweets, Eq. (3): p(qi = l, zi = z | W, d−i, Z−i, αt, γ, βtu) ∝ (n^t_{d,l,−i} + γ)/(n^t_{d,−i} + 3γ) · (n^t_{d,z,−i} + α^l_t)/(Σ_{z0} n^t_{d,z0,−i} + Z α^l_t) · (n^t_{w,z,−i} + β^l_t)/(Σ_{w0} n^{u,t}_{w0,z,−i} + N_{u,t} β^l_t).
- M-step re-estimates the weights by maximizing the posterior likelihood p(W | Φt−1, xu,t−1, αB, βt, σ, γ):
  - Eq. (4): α̂u,t = αu,t · [ Σ_{z∈Zcom_t} (θu,t−1,z − Σ_{ci∈Cu,t−1} λθci,t−1) A_{u,z,t} ] / [ Ψ(n^com_{u,t} + αu,t) − Ψ(αu,t) ], with Ψ(x) = ∂logΓ(x)/∂x and A_{u,z,t} = Ψ(n^com_{u,z,t} + x^com_{u,z,t}) − Ψ(x^com_{u,z,t}).
  - Eq. (5): β̂^l_{z,t} = β̂^l_{z,t} · [ Σ_{w∈Nt} φ^{w,z}_{t−1} ( Ψ(n_{w,z,t} + y^l_{t,t−1}) − Ψ(y^l_{t,t−1}) ) ] / [ Ψ(n_{z,t} + β^l_{z,t}) − Ψ(β^l_{z,t}) ], "and y^{w,z}_{t,t−1} is defined as βcom t φcom+B t−1".
- Update equations after sampling (Eq. 6): θu,z,t = (n^{u,t}_z + x_{u,z,t}) / Σ_{z∈Z} (n^{u,t}_{z0} + x_{u,z0,t}); ϑd,z,t = (n_{d,z,t} + α_{z,t}) / Σ_z (n_{d,z0,t} + α_{z0,t}); φw,z,t = (n_{w,z,t} + β_{w,z,t}) / Σ_z (n_{w,z,t} + β_{w,z,t}); πd,l,t = (n^{u,t}_{d,l} + σ)/(n^{u,t}_d + 3σ); rd,l,t = (n^t_{d,l} + γ)/(n^t_d + 3γ).
- **Algorithm 1 (Gibbs EM Sampling Process during period t)** — input "βt, βB, αB, αt, Xu,t, Φt−1, dt, U, Dt and R"; output "β̂^l_t , α̂t , ⟨e, zi⟩ and ⟨q, zi⟩"; loop `for u ∈ U`, `for r < R`: E-step samples ⟨ei, zi⟩ from Eq. 2 for d = 1..Du,t and ⟨qi, zi⟩ from Eq. 3 for d = 1..Dt; M-step computes θ, φ, ϑ, λ from Eq. 6 and 8 and maximizes α̂u,t, β̂^l_{z,t} from Eq. 4, 5. Then "Inference for our topic modeling process will then move on to period t + 1."
- **Social-circle weights λ (Eq. 7–8):** "we use a Markov random walk strategy, which calculates saliency of a social circle based on 'voting' from others." Circle-level interest is θcom+B ci,t−1 = Σ_{u0∈ci} θcom+B u0,t−1; similarity matrix SIM^{u,t}_{i,j} uses div(θci, θcj | θu) = Σ_z θci,z ln(θci,z/θu,z) − θcj,z ln(θci,z/θu,z) (Eq. 7). Eq. (8) is a random-walk update λu,ci,t = µ · Σ_{i≠j} sim(θ_dci,t , θcj,t | θu,t) · λu,ci,t + (1 − µ)/|Cu,t|, with µ = 0.85. *Caveat: Eq. (8) is visibly garbled by the PDF extraction (the `sim(θ_dci,t , θcj,t | θu,t)` argument list is mangled and the `|Cu,t|` denominator is displaced), so the exact normalization must be reconstructed from context.*
- R (number of Gibbs EM iterations) is named as an input in Algorithm 1 but its value is **not stated**.

### 3. Tweet selection — iterative optimization (Section 4.3, Algorithm 2)

Three objective terms, all built on KL-style divergences:

- **Novelty (Eq. 9):** LN(RTt | RTt0) = Σ_{p∈RT} min_{p0∈RTt0} div(ϑp, ϑp0 | θu,t) — "Novelty calculates the semantic divergence between the currently selected set RTu,t and the results in previous time periods RTt0. Our intention is to make the current results as different as possible from previous results as much as possible."
- **Coverage (Eq. 10–11):** LC(RT | Dt) = Σ_{d∈RT} exp( −min_z Σ_{d0∈Dt} div(ϑd,z, ϑd0,z | θu,z,t) ) with div(ϑd,z, ϑd0,z | θu,z,t) = ϑd,z ln(ϑd,z/θu,z,t) − ϑd0,z ln(ϑd,z/θu,z,t) (Eq. 11). Purpose: "a tweet summary should contain important aspects from all related tweets and minimize the information loss with the set of all candidate tweets."
- **Diversity (Eq. 12):** LD(RT) = Σ_{w,w0∈RT} max_z div(φw,z,t, φw0,z,t | Π_{d∈Dt} ϑd,z) — "Diversity calculates the information divergence among all tweets within the current candidate result set."
- **Combined saliency:** S_{RTu,t} = F(LC · LN · LD) (Algorithm 2; the function F is **not further specified**).
- **Algorithm 2 (Iterative Process for RTu,t Generation)** — input "Dt, RTu,t0 , θu,t , φt , N"; output "RTu,t":
  1. "Calculate Kullback-Leibler divergence KL(ϑd,t, θu,t);"
  2. "Rank and extract relevant tweets to Rt by e^{−KL(ϑd,t,θu,t)};"
  3. "Initialize: Extract N tweets from Rt to RTu,t;"
  4. repeat: Xt = {dx ∈ Rt ∩ dx ∉ RTu,t}; for each dx ∈ Xt and ∀dy ∈ RTu,t compute S and ΔS_{dx,dy} = S((RTu,t − dy) ∪ dx) − S(RTu,t); pick argmax ΔS; update RTu,t = (RTu,t − dˆy) ∪ dˆx; until ∀ ΔS_{dx,dy} < ε; return RTu,t.
  - Quoted: "an iterative optimization algorithm is used to select the set RTu,t. During each iteration n, we extract tweet dx such that dx ∈ Rt ∩ dx ∉ RTu,t to substitute dy ∈ RTu,t when the saliency gain ... gets a maximum value. The algorithm will converge when S(RTu,t) reaches its maximum value." (Inspired by [33] Yan et al., evolutionary timeline summarization.)

**Hyperparameter values actually given in Section 5.2 (verbatim list):**

| Parameter | Value stated in the paper |
|---|---|
| αu,t | "50/Ktu" |
| βt | "0.5" |
| αB | "50/KtB" |
| βB | "0.5" |
| σu = γcom | "0.5" |
| γu = σcom | "0.3" |
| γB = σB | "0.2" |
| initial λu,ci,t−1 | "1/Cu,t , the parameter µ is set as 0.85" |
| µ | 0.85 |
| ε (Algorithm 2) | 0.0001 |
| Z0u and Z0com (default) | "100, respectively" |
| Z0u and Z0com for TPM-ALL / TPM-TOP | "150, separately" |
| Number of topics chosen by perplexity | "After the number of topics becomes larger than 300, the perplexity of both approaches starts to flatten out." |
| N (tweets per period) | 40 and 60 |
| Time granularity | "10 contiguous weeks from November 1, 2009 onwards as the test period and separate it into 10 periods" (i.e. 1 week per period) |
| Gibbs EM iterations R | **not stated** |
| Bursty-word frequency threshold | **not stated** |

Preprocessing: "We remove stop words and apply Porter stemming [23]" and "We further remove non-English tweets through automatic language identification [3]".

## Datasets (names, sizes, language, domain, HOW OBTAINED)

No named dataset. Everything is crawled by the authors.

- **Tweets:** "we crawl tweets via the Twitter streaming API, which contains a random sample of around 10% of all items posted on Twitter."
  - "Timestamps in our dataset are from November 1, 2009 to December 31, 2010; the 2009 part contains 47,373,408 tweets and 562,361 users, while the numbers for 2010 are 295,145,421 and 5,828,356, respectively."
  - So roughly **342.5 million tweets** and **5.8M users** overall.
  - Language: English only after filtering — "We further remove non-English tweets through automatic language identification [3]."
  - Domain: general Twitter stream (microblog), not a topical corpus.
- **Social relations:** "For crawling the social relations, we use the dataset from [15] [Kwak, Lee, Park, Moon. 'What is twitter, a social network or a news media?' WWW 2010], which includes social relations for all users on Twitter until July 2009. In our experiments, we use only those tweets and users that appear in both datasets."
  - Assumption: "In our experiments we assume social relations among users to remain the same over the entire time period." (i.e., the friendship graph is frozen — a static 2009 snapshot applied to 2009–2010 activity.)
- **Evaluation subset:** "Since it is impossible to evaluate the effectiveness if a user posted nothing on Twitter, sparse postings obstruct our experimental evaluation. We therefore only consider users who posted a sufficient number of tweets for our evaluation: we collect users who post over 100 tweets in our dataset. This results in a subset containing 32,659 users. Thereafter we use social relations to build the social circles around those users."
  - Distribution note: "most users (75.2%) in our dataset wrote fewer than 100 tweets."
- **User classes used in Figure 10:** "(1) less than 400 tweets; (2) between 400 to 800 tweets; and (3) more than 800 tweets."
- **Enrichment resource:** Wikipedia articles linked via CMNS [20]; top-3 articles per tweet; sentence extraction per article.
- Dataset figures: Figure 4(a) histograms of tweets per user (x-axis bins 100/500/900/1000/3000/5000), Figure 4(b) tweets per user vs number of friends.

## Data/code availability stated in the paper

**NONE.** The paper states no dataset URL, no download link, no "available at", no "we will release", and no code repository. The only URLs in the entire text are:

- `http://blog.twitter.com/2012/03/twitter-turns-six.html` — the "half a billion users / 300 million tweets per day" statistic (footnote 1).
- `https://dev.twitter.com/docs/streaming-apis` — the Twitter Streaming API documentation (footnote 2), which is where the crawl came from.
- Footnote 3: "Version 1.5.5 is used in this paper." (ROUGE 1.5.5; no download link given.)

The social graph is referenced only as "the dataset from [15]" (Kwak et al., WWW 2010) — no URL. The entity-linking method is referenced only as [20] (Meij, Weerkamp, de Rijke, WSDM 2012) — no tool link. The paper explicitly lists a user study as *future* work: "As to future work, we aim to employ a user-study to enhance the accuracy of interest detection, e.g., via an online evaluation."

## Evaluation (metrics, human evaluation required? protocol, folds)

- **No human evaluation.** Explicit: "Evaluating the effectiveness of time-aware tweets summarization is a challenging task, especially in the absence of explicit user feedback."
- **Automatic ground truth from retweets:** "One possible solution is to use evidence from users themselves: we use a user's retweeted post(s) at time t + 1 as the ground truth to evaluate performance of comparisons at time t." (i.e., future retweets as a proxy for what the user found meaningful — a temporal hold-out, not cross-validation.)
- **Metrics:** "we adopt the ROUGE evaluation metrics [17], a widely-used recall-oriented metric ... In our experiments, ROUGE-1 (unigram based method), ROUGE-2 (bigram based method) and ROUGE-W (weighted longest common sequence) are used as evaluation metrics." ROUGE version 1.5.5.
- **Protocol:** "We measure the quality of summaries by counting overlapping textual units between the generated results and the ground truth results."
- **Test period:** "We select 10 contiguous weeks from November 1, 2009 onwards as the test period and separate it into 10 periods." Results are reported per period (Figure 8) and averaged over "all candidate tweets in all time periods" (Table 2).
- **Folds:** **not stated** — no k-fold cross-validation is described; the split is temporal (train = history up to t, test = period t, ground truth = retweets at t+1). A "held-out test set" is mentioned only for the perplexity/topic-count study ("the perplexity of both approaches ... on our held-out test set").
- **Significance testing:** "Statistical significance of observed differences between two comparisons is tested using a two-tailed paired t-test. In our experiments, statistical significance is denoted using N for significant differences for α = 0.01, or M for α = 0.05."
- **Variations studied:** number of tweets per period N ∈ {40, 60}; number of social circles 0–10; number of topics (perplexity curve, flattening after 300); user classes by tweet volume (<400, 400–800, >800).

## Baselines (list them)

Internal ablations, defined in §5.4:

- **TPM-ALL** — "the overall process as described in Section 4.1, which includes both the social influence modeling and time-aware topic and interests tracking."
- **TPM-SOC** — "the model that only considers users' social influence (so excluding time-aware topic propagation and it doesn't consider if some topic is private or not)."
- **TPM-TOP** — "the model that uses a user's own tweets (without social circles but considering topic and interests propagation with the time)."

External baselines (as named in Table 2, and partly described in §5.4, whose continuation text is truncated in the extracted file):

- **UBM** — "recent user behavior models on Twitter"; best-performing non-TPM baseline: "Except for our TPM-based strategies, UBM get the best performance than others." Full expansion **not stated** in the extracted text.
- **TLDA** — presumably Twitter-LDA [37]; only named in Table 2, description lost in extraction.
- **AT** — author-topic model [26]: "the AT-based method yields almost the worst performance. This can be explained by the fact that the topic modeling procedure in AT does not capture topic drift and users' social circles." (Also compared for perplexity: "we find that TPM-SOC outperforms the author-topic model with better generalization performance.")
- **TF-IDF** — term-frequency baseline.
- **Centroid** — centroid-based summarization [24] (Radev et al.).
- **Lex-R** — LexRank [10] (Erkan & Radev): "Since summarization baselines are not sensitive to users' interests, thus we find that Centroid, Lex-R (short for LexRank), and SUM-TF do not perform well."
- **SUM-TF** — term-frequency-based document-stream summarization [28] (Takamura et al.).
- **Random** — random selection.

> Extraction caveat: §5.4's left column ends mid-sentence at "For those topic" and the description of the remaining baselines (UBM, TLDA, etc.) does not appear anywhere else in the extracted text. Their full names/implementations are therefore **not stated** in this file.

## Reported results (key numbers, so a reproducer knows the target)

**Table 2 — "Overall ROUGE Performance for All Comparisons"** (average over all candidate tweets in all time periods):

Cut-off of N = 40 tweets per period:

| Metric | TPM-ALL | TPM-TOP | TPM-SOC | UBM | TLDA | AT | TF-IDF | Centroid | Lex-R | SUM-TF | Random |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ROUGE-1 | **0.428 N** | 0.403 N | 0.395 N | 0.387 | 0.374 | 0.355 | 0.341 | 0.302 | 0.291 | 0.274 | 0.252 |
| ROUGE-2 | **0.125 N** | 0.119 M | 0.116 M | 0.114 | 0.112 | 0.102 | 0.095 | 0.081 | 0.077 | 0.079 | 0.037 |
| ROUGE-W | **0.159 N** | 0.153 N | 0.149 M | 0.146 | 0.142 | 0.144 | 0.137 | 0.118 | 0.115 | 0.105 | 0.076 |

Cut-off of N = 60 tweets per period:

| Metric | TPM-ALL | TPM-TOP | TPM-SOC | UBM | TLDA | AT | TF-IDF | Centroid | Lex-R | SUM-TF | Random |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ROUGE-1 | **0.513 N** | 0.497 N | 0.482 N | 0.461 | 0.457 | 0.423 | 0.411 | 0.362 | 0.369 | 0.329 | 0.281 |
| ROUGE-2 | **0.149 N** | 0.142 M | 0.139 M | 0.134 | 0.127 | 0.122 | 0.116 | 0.097 | 0.102 | 0.095 | 0.041 |
| ROUGE-W | **0.197 N** | 0.191 N | 0.189 N | 0.178 | 0.176 | 0.166 | 0.161 | 0.131 | 0.135 | 0.119 | 0.081 |

(N = significant at α = 0.01 vs. UBM; M = significant at α = 0.05 vs. UBM.)

**Relative improvements quoted in §6.3:**
- N = 40: "TPM-ALL achieves an increase of 10.6%, 11.6% and 8.9% over UBM in terms of ROUGE-1, ROUGE-2, and ROUGE-W respectively."
- N = 60: "TPM-ALL gives an increase of 11.2%, 11.2% and 10.1% over UBM."
- N = 40: "TPM-TOP offers relative performance improvements of 4.1%, 6.25% and 4.8%, respectively, for the ROUGE-1, ROUGE-2 and ROUGE-W metrics, while the relative improvements are 7.8%, 6.7% and 7.3% on the same metrics for N = 60."
- Significance: "TPM-ALL outperforms the UBM baselines with a statistical significance difference at level α < 0.01 in terms of all ROUGE metrics, whereas TPM-TOP and TPM-SOC outperforms UBM with a statistical significance difference at level α < 0.05."

**Temporal behaviour (Figure 8):** "the AT model obtains the worst performance, while both TPM-ALL and TPM-TOP outperform all other strategies in terms of ROUGE metrics at all time intervals." A "cold-start" phenomenon is reported: "which results from the sparseness of the context in the first time period. In that condition, TPM-ALL and TPM-TOP are nearly equivalent to the UBM and AT since there are neither social circles nor burst topics during the first time period. After that, the performance of the TPM based methods keeps increasing over time until it achieves a stable performance after t = 3." Approximate axis ranges: ROUGE-1 spans ~0.30–0.50, ROUGE-2 ~0.09–0.17, ROUGE-W ~0.13–0.17 over the 10 periods.

**Social-circle count (Figure 9):** "the value increases and achieves a maximal value between 3 and 5 social circles. After that, the value decreases rapidly; redundant and irrelevant 'relations' seem to enter the picture." ROUGE-1 axis ~0.38–0.46, ROUGE-2 ~0.11–0.14. UBM/TPM-TOP are flat across circle counts since they ignore social influence.

**User classes (Figure 10):** "the difference between TPM-ALL and TPM-TOP is bigger for users with up to 400 tweets than for those with more than 400. This can be explained by the fact that the collaborative filtering used in TPM-ALL becomes more effective when there is a bigger data sparseness issue to overcome." ROUGE-1 axis ~0.40–0.50 (N=40) and ~0.44–0.56 (N=60); ROUGE-2 ~0.11–0.15.

**Perplexity study:** "After the number of topics becomes larger than 300, the perplexity of both approaches starts to flatten out."

## Implementation complexity

**Very high.** Reasons:

1. **Scale of the data pipeline.** The crawl covers ~342.5M tweets and 5.8M users across 14 months, requiring a Twitter Streaming API sample plus the Kwak et al. WWW 2010 social graph; the model is run per-user over 32,659 users with 100–150 private + 100–150 common topics each and 10 weekly periods.
2. **A custom dynamic topic model with three topic classes.** TPM is not LDA: it has private/common/bursty topics, per-word switch variables `e` and `q`, Dirichlet propagation priors from t−1, and a Gibbs **EM** loop that re-estimates αu,t and β^l_{z,t} in the M-step (Eq. 4–5, involving digamma functions). Implementing Eqs. 2–5 correctly from the paper alone is error-prone; the extracted equations have mangled sub/superscripts.
3. **Under-specified pieces.** R (Gibbs EM iterations), the bursty-word frequency threshold, the exact form of F(·) in the saliency function, the exact form of Eq. 8 (garbled), the exact divergence normalization in Eqs. 9–12, and the identity of UBM/TLDA are all either absent or corrupted in the text.
4. **Data enrichment stack.** Requires a working tweet→Wikipedia entity linker (CMNS, [20]) plus query-sensitive LexRank sentence extraction over Wikipedia — a whole second system, and the paper gives no code or tool URL.
5. **Evaluation depends on retweet ground truth**, which requires the raw tweet stream including retweet relationships; ROUGE 1.5.5 must be obtained and configured separately.
6. **Iterative selection is quadratic per iteration** — for each candidate dx against each selected dy, computing three divergence-based objectives, repeated until ΔS < ε = 0.0001.

Cheaper components that are individually tractable: the selection objective (Algorithms 2, Eqs. 9–12) is a self-contained combinatorial optimizer over any tweet-topic distributions, and a simplified single-class dynamic topic model is implementable in a few hundred lines.

## Reproducibility obstacles

- **Private Twitter API data.** The corpus is a 10% Streaming API sample from Nov 2009–Dec 2010. It is not public, was not released, and is not reconstructable: Twitter's streaming API no longer provides historical backfill, academic API access changed drastically post-2023, and tweet IDs (not even given) would suffer massive deletion. Redistribution would also violate the Twitter ToS.
- **Second private dataset.** The social graph comes from "the dataset from [15]" (Kwak et al., WWW 2010) with no URL; it is a July-2009 snapshot that also cannot be re-crawled (the API endpoint for follower enumeration is gone).
- **Ground truth requires retweets at t+1** — a field that is hard to reconstruct and is not distributed with any public dataset.
- **Dead/undocumented tools.** `https://dev.twitter.com/docs/streaming-apis` is a dead link; the CMNS entity linker [20] has no public release URL in the paper; ROUGE 1.5.5 is only available from an archived distribution.
- **Wikipedia dependence.** Enrichment needs a Wikipedia dump roughly contemporary with 2009–2010 to reproduce the entity-link and sentence-extraction behaviour; today's Wikipedia will link different articles.
- **Unspecified hyperparameters/algorithms.** R (Gibbs EM iterations), the bursty-frequency threshold, F(·) in S = F(LC·LN·LD), the exact Eq. 8 normalization, the number of candidate tweets per period, and the train/test user counts are not stated. UBM and TLDA are not defined in the extracted text.
- **Compute.** 32,659 users × (100–150 private + 100–150 common + bursty topics) × 10 periods × Gibbs EM sampling over hundreds of millions of tweets is far beyond a course-scale cluster; the paper's own perplexity experiment only settles after 300 topics.
- **No code and no artifact.** There is no reproducibility statement, no GitHub link, no appendix with implementation details, and no released model parameters.
- **Evaluation metric opacity.** ROUGE-W values (0.159 at N=40) are lower than ROUGE-2 in Table 2 while the paper calls ROUGE-W a weighted LCS measure; the exact ROUGE-1.5.5 configuration (stemming, stopwords, -n/-w parameters) is not stated.

## Minimum viable reproduction plan (2–4 weeks)

**Realistic scope: reproduce the *selection framework* and a *simplified TPM*, on a small substitute corpus, and validate the *relative ordering* of methods rather than the absolute ROUGE numbers.**

Substitutions:

1. **Data:** replace the private crawl with a public substitute — e.g. a public Twitter/X sample with retweets (or a Weibo dataset, since the course also covers Weibo), or, better for reproducibility, a public news/Reddit/microblog stream where "engagement at t+1" (upvote/repost) can proxy the retweet ground truth. Keep the structure: users with >100 posts, a friend/follow graph, weekly periods. Use 10 contiguous weekly periods for the test window to mirror the paper.
2. **Social circles:** implement clique enumeration (e.g. networkx `find_cliques`, or maximal-clique enumeration per user) exactly as defined — "every pair of users in this set is in the friend relation". Restrict to 3–5 circles, since Figure 9 shows the peak is "between 3 and 5 social circles".
3. **Topic model:** implement a simplified TPM: dynamic author-topic model with private/common/bursty topics, Dirichlet propagation φcom t ∼ Dir(βcom⟨φcom t−1, φB t−1⟩) and φut ∼ Dir(βu⟨φut−1⟩), Gibbs sampling with the `e`/`q` three-way switches. Drop the M-step hyperparameter re-estimation (Eqs. 4–5) and fix α, β at the paper's values (αu,t = 50/Ku, β = 0.5, αB = 50/KB, βB = 0.5, σu = γcom = 0.5, γu = σcom = 0.3, γB = σB = 0.2), which is the single biggest simplification and keeps the model runnable.
4. **Topic counts:** use far fewer topics than 100–150 per class (e.g. 10–30 private + 10–30 common) and note the deviation; the paper's own perplexity curve only flattens after 300 total.
5. **Enrichment:** skip the CMNS+Wikipedia pipeline or substitute a modern entity linker (e.g. spaCy NER + Wikipedia API) with a simple top-1 article and first-N-sentences heuristic; or run the pipeline twice (with/without enrichment) to quantify the enrichment contribution. The paper gives the CMNS formula (Eq. 13) explicitly, so a from-scratch prior-probability linker over a small Wikipedia dump is feasible.
6. **Selection:** implement Algorithms 2 and Eqs. 9–12 faithfully, with ε = 0.0001 and N ∈ {40, 60}. Use the simple KL ranking `e^{−KL(ϑd,t, θu,t)}` for the initial candidate set Rt.
7. **Baselines to re-implement:** Random, TF-IDF, Centroid, LexRank (all standard and cheap), plus AT (author-topic) and the ablations TPM-TOP / TPM-SOC / TPM-ALL. These ablations are the paper's core scientific claim and are the most valuable thing to reproduce.
8. **Metric:** ROUGE 1.5.5 (or the `rouge` Python package with ROUGE-1/2/W), using retweets/reposts at t+1 as gold.

**Expected numbers.** Do not expect Table 2's absolute values (0.428/0.125/0.159 at N=40; 0.513/0.149/0.197 at N=60) — those are tied to the 2009–2010 English Twitter sample and the Wikipedia enrichment. A realistic target on a substitute corpus is the **ordering and the gaps**: TPM-ALL > TPM-TOP ≈ TPM-SOC > UBM > TLDA > AT > TF-IDF > Centroid/LexRank/SUM-TF > Random, with TPM-ALL roughly 5–12% relatively above the strongest non-TPM baseline, a cold-start dip in period 1, gains stabilizing after t = 3, and peak performance at 3–5 social circles. Even the ablation gap (TPM-ALL − TPM-TOP ≈ 0.025 ROUGE-1 at N=40, 0.016 at N=60) is a fair reproduction target.

**What is not worth attempting in 2–4 weeks:** the full 342M-tweet crawl, 32,659-user evaluation, 300-topic perplexity sweeps, or exact ROUGE reproduction.

## Verdict

This is a **poor-to-moderate reproduction target on its own terms, but a good "concept reproduction" target for the right student.** On the negative side, it fails nearly every reproducibility test: the corpus is a private ~342M-tweet Twitter Streaming API sample from 2009–2010 that was never released and cannot be re-crawled, the social graph is an un-URL'd third-party 2009 snapshot, the ground truth depends on future retweets, the entity-linking component has no public tool, ROUGE 1.5.5 must be sourced separately, and the paper itself omits R, the bursty threshold, the F(·) saliency function, and the definitions of UBM/TLDA. Add a bespoke three-class dynamic topic model with a Gibbs EM M-step and per-user inference over 32k users, and full replication is effectively impossible for a course project. On the positive side, the paper is unusually explicit about its *framework*: the social-circle definition is a one-line clique definition, the three selection objectives (novelty/coverage/diversity) are fully written out with numbered equations, Algorithm 2's iterative substitution loop is given in pseudocode, and the hyperparameter table (50/Ku, 0.5, 50/KB, 0.5, 0.5/0.3/0.2, µ = 0.85, ε = 0.0001, 100–150 topics, N = 40/60) is complete enough to implement. So the paper suits a student who wants a **framework-level reproduction with substitutions**: rebuild a simplified dynamic author-topic model plus the exact novelty/coverage/diversity selection algorithm on a public microblog dataset, and verify the ablation ordering (TPM-ALL > TPM-TOP/TPM-SOC > UBM > AT) rather than the absolute ROUGE table. It is a bad fit for a student who needs to reproduce reported numbers, and a bad fit for anyone without solid probabilistic-modeling and Gibbs-sampling experience; students wanting a genuinely reproducible Twitter/Weibo summarization target should prefer papers that release data and code.
