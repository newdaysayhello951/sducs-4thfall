# Joint Topic Modeling for Event Summarization across News and Social Media Streams

## Bibliographic info (authors, venue, year)

- **Authors:** Wei Gao (Qatar Computing Research Institute, Qatar Foundation, Doha, Qatar — `wgao@qf.org.qa`); Peng Li (Department of Computer Science and Engineering, Shanghai Jiaotong University, Shanghai, China — `jerryli1981@gmail.com`); Kareem Darwish (Qatar Computing Research Institute, Qatar Foundation, Doha, Qatar — `kdarwish@qf.org.qa`).
- **Author footnote:** "This work was done when the author worked as an intern at Qatar Computing Research Institute with Qatar Foundation." (attached to Peng Li)
- **Venue / year:** CIKM'12 — 21st ACM Conference on Information and Knowledge Management, October 29 – November 2, 2012, Maui, HI, USA. Pages 1173–1182 (page numbers 1173…1182 appear in the extracted text). Copyright line: "Copyright 2012 ACM 978-1-4503-1156-4/12/10 ...$15.00."
- **Categories / keywords given by authors:** "H.4 [Information Systems Applications]: Miscellaneous; I.2.7 [Natural Language Processing]: Text analysis"; General Terms "Algorithms, Experimentation, Performance"; Keywords "Cross-collection topic-aspect model, LDA, Gibbs sampling, Complementary summary".
- **Paper type:** Unsupervised (explicitly stated: "we aim to produce complementary summaries jointly from both sides, and also our approach is unsupervised considering the appropriate training data for the task is not available and is difficult to get").

## Task (what is summarized, input -> output, extractive vs abstractive)

**New problem definition.** The authors claim novelty: "To the best of our knowledge, the concept of complementary summary has never been defined in the literature. Our task is therefore a new one." The goal is "to summarize the given subject matter by jointly extracting important and complementary pieces of information across news media and Twitter."

**Definitions given in the paper (Section 3):**

- **Definition 1 (Subject):** "A subject is an event or subject matter whose relevant information could be found on both online news media and Twitter. This primarily refers to current affairs such as 'Russian presidential election', 'Death of Marie Colvin' and 'Poland rail crash'."
- **Definition 2 (Topic):** "A topic refers to some essential elements that make up of the complete description of the concerned subject, such as what, when, where, who, why, progress, numbers, countermeasures, etc."
- **Definition 3 (Aspect):** "An aspect is an underlying theme, perspective or viewpoint as to the topics of a subject. Each aspect spans all topics in a subject and may affect all topics in a similar manner. For example, in the subject of 'Israeli-Palestinian conflict', the main aspects usually consist of Israeli, Palestinian and/or US government in the different topics regarding this subject."
- **Definition 4 (Complementary relation):** given N = {n1, …, n_mn} (news sentences) and T = {t1, …, t_nt} (tweets), "The complementary relation is the set of K sentence-tweet pairs satisfying certain conditions described as follows: {(ni, tj) | 1 ≤ i ≤ mn; 1 ≤ j ≤ nt; Icomp(ni, tj) > 0}".
- **Definition 5 (Complementary summaries):** "the complementary summaries consist of two sets of excerpts SN and ST from R, where SN = {ni} and ST = {tj} are extracted respectively from the news portion and tweets portion of R according to the co-ranking measure described in Section 5 in such a way that the top sentences and tweets are selected until the predefined length threshold of the summaries is met."

**Input → output.** Input = a subject plus the two raw streams: news sentences from news articles about the subject, and the tweets collected for the subject (plus, in the gold standard, "standard summary" material). Output = **two separate extractive summaries**, one on the news side (SN) and one on the tweets side (ST), which are *complementary as a whole* (Summary-level, "SumLevel") or in strict sentence↔tweet correspondence (Sentence-level, "SentLevel"). The paper notes "the final summaries should be output and displayed in such a way that news summary and tweet summary are well separated at either side."

**Extractive vs abstractive:** strictly **extractive** — the outputs are selected news sentences and selected tweets, cut to a "predefined length threshold of the summaries"; there is no generation/rewriting step anywhere in the method.

**Motivation example (Table 1).** For the subject "Egyptian Revolution", topics × aspects (What happened / Reasons(why) / Where) × aspect (Authority / Protester) are paired, e.g. news "Egyptian tanks enter Tahrir Square." ↔ tweet "Oh yeah! As Mubarak is listening to us with tear gas!". This is the paper's motivating evidence that complementarity is discoverable at sentence level across topics and aspects.

## Method (core algorithm in implementable detail)

Pipeline: **(1)** build general / news-specific / tweet-specific word distributions with a new topic model **ccTAM** (cross-collection topic-aspect model = ccLDA + two-dimensional topic-aspect model); **(2)** use them to compute a *complementarity* score Icomp for every sentence–tweet pair; **(3)** co-rank sentences and tweets on a bipartite graph with a biased random walk whose jumping probability is multiplied by Icomp; **(4)** cut the two ranked lists to the length threshold.

### 1. Complementarity measure (Eq. 1–5)

Given three topic models for a subject — a **general** model M_G, a **news-specific** M_N and a **tweet-specific** M_T (Figure 1) — complementarity is a piecewise function of *commonality* Icomm and *difference* Idiff:

```
Icomp = Icomm / Idiff   if Icomm <= Idiff
Icomp = Idiff / Icomm   otherwise            (Eq. 1)
```

"the value of function Icomp reaches the peak when Icomm = Idiff and it approaches to 0 when the sentence and the tweet are either very similar or very different. As a result, the function encourages the sentence and tweet in the pair to be moderately similar and penalizes extreme cases where they are excessively common or different." (Both Icomp, Icomm, Idiff are in [0,1].)

With unigram distributions φ (general), φn (news-specific), φt (Twitter-specific):

```
Icomm(ni, tj) = Norm( p(ni|φ) · p(tj|φ) )                          (Eq. 2)

              ⎛ p(ni|φn)   p(tj|φt) ⎞
Idiff(ni, tj) = Norm ⎜ ───────── · ───────── ⎟                      (Eq. 3)
              ⎝ p(tj|φn)   p(ni|φt) ⎠
```

"Norm(.) is a normalization function to cast Icomm and Idiff into the same range of values"; p(e|f) = probability of sentence/tweet e generated from model f. Intuition quoted: "the more different ni and tj are, the higher the value of Eq. 3 is."

With topics z and aspects y, each word distribution has three versions (φz, φy, φzy), and with the general + two media-specific models there are **9 distributions**: φz, φy, φzy, φ^t_z, φ^t_y, φ^t_zy, φ^n_z, φ^n_y, φ^n_zy. The measure is evaluated under **5 configurations {z, y, zy, z+y, z+y+zy}**, "in which z + y + zy is the full configuration". Under the full configuration (Eq. 4, 5):

```
Icomm(ni, tj) = Norm( Σ_{X∈{z,y,zy}} p(ni|φX) · p(tj|φX) )

                                 ⎛ p(ni|φn^X)   p(tj|φt^X) ⎞
Idiff(ni, tj) = Norm( Σ_{X∈{z,y,zy}} ⎜ ────────── · ────────── ⎟ )
                                 ⎝ p(tj|φX)     p(ni|φt^X) ⎠
```

### 2. ccTAM generative process (Figure 2, quoted)

```
1. Draw background word distribution φb from Dir(β) and route distribution πx from Dir(γx)
2. For each topic z and aspect y,
   (a) draw general topic-word distribution φz
   (b) draw general aspect-word distribution φy
   (c) draw general topic-aspect-word distribution φzy
3. For each collection c (i.e., n and t),
   (a) draw specific topic-word distribution φcz
   (b) draw specific aspect-word distribution φcy
   (c) draw specific topic-aspect-word distribution φczy
4. For each document d,
   (a) choose a collection indicator c
   (b) draw doc topic distribution θd ~ Dir(α)
   (c) draw doc aspect distribution ψd ~ Dir(δ)
   (d) draw level distribution πl ~ Dir(γl)
   (e) for each word i,
       i.   draw z ~ Multi(θd)
       ii.  draw y ~ Multi(ψd)
       iii. draw ld,i ~ Multi(πl)
       iv.  draw xd,i ~ Multi(πx)
       if (ld,i = 0, xd,i = 0) draw wd,i ~ φb
       if (ld,i = 1, xd,i = 1) draw wd,i ~ φz
       if (ld,i = 1, xd,i = 2) draw wd,i ~ φy
       if (ld,i = 1, xd,i = 3) draw wd,i ~ φzy
       if (ld,i = 2, xd,i = 1) draw wd,i ~ φcz
       if (ld,i = 2, xd,i = 2) draw wd,i ~ φcy
       if (ld,i = 2, xd,i = 3) draw wd,i ~ φczy
```

Notation (Table 2): K = #topics, C = #collections, D = #documents in a collection, N = #words in a document, φb background word distribution, TG general topic-word, TS collection-specific topic-word, AG general aspect-word, AS collection-specific aspect-word, TAG general topic-aspect-word, TAS collection-specific topic-aspect-word, w word, y aspect index, z topic index, l level control variable, x route control variable, ψd aspect distribution, θd topic distribution, πl level distribution, πx route distribution, α Dirichlet prior for θd, β Dirichlet prior for all word distributions, δ Dirichlet prior for ψd, γl Dirichlet prior for πl, γx Dirichlet prior for πx.

**Two important data-handling statements:** "At Twitter side, note that we aggregate all the relevant tweets of each user as single document like previous studies [19]" (i.e., per-user tweet aggregation = one document); and "All these word distributions are assumed having a uniform Dirichlet prior with parameter β." Level l ∈ {0,1,2} = background / cross-collection / collection-specific; route x ∈ {0,1,2,3} = background / topic / aspect / topic-aspect mixture.

### 3. Inference (Gibbs sampling, Eq. 6–7)

"Gibbs sampling [7], a Markov Chain Monte Carlo method [1], is used to estimate each one of the distributions." The two collections are merged into "the single set of vocabulary of all words {wd,i}". Sample equations (general topic-word φz shown; "the analogous inference method also applies to draw aspects and topic-aspect mixture"):

```
p(zd,i = k | ld,i = 1, xd,i = 1, zd,¬i, w, α, β) ∝
        Ckd + α        Ck^{wd,i} + β
     ───────────── · ─────────────────          (Eq. 6)
        C(·)d + Kα     C(·)k + Vβ

p(ld,i = 1, xd,i = 1 | ld,¬i, xd,¬i, β, γl, γx) ∝
     C(ld,i=1)d + γl     C(ld,i=1,xd,i=1)k + γx     Ck^{wd,i} + β
   ──────────────── · ────────────────────────── · ─────────────   (Eq. 7)
      C(·)d + 3γl         C(ld,i=1)k + 4γx          C(·)k + Vβ
```

and the analogous collection-specific topic-word φcz:

```
p(zd,i = k | ld,i = 2, xd,i = 1, ...) ∝ (Ckc,d + α)/(C(·)c,d + Kα) · (Ck^{c,wd,i} + β)/(C(·)c,k + Vβ)
p(ld,i = 2, xd,i = 1 | ...)           ∝ (C(ld,i=2)d + γl)/(C(·)d + 3γl) · (C(ld,i=2,xd,i=1)k + γx)/(C(ld,i=2)k + 4γx) · (Ck^{c,wd,i} + β)/(C(·)c,k + Vβ)
```

**Hyperparameters with exact values (quoted):** "In our experiments, we empirically set the hyper-parameters α = 10, β = 0.01, γx = 10, γl = 10 and δ = 10. We run 100 burn-in iterations through all documents to stabilize the distribution of z, y, l and x before sampling starts. For each distribution, we take 10 samples with a gap of 10 iterations between two sampling, and average over these 10 samples to get the estimation for the distributions."

**NOT stated:** the numeric values of K (#topics) and A (#aspects) used in the experiments — the paper only says "Suppose there are K number of topics and A number of aspects"; no values for K, A, V, or the document/word counts are reported anywhere.

### 4. Summary generation: bipartite co-ranking (Section 5)

- **Jumping probability** based on "the normalized idf-modified-cosine similarity [6]", modified by Icomp:
  ```
  ρ(ni, tj) = sim(ni, tj) · Icomp(ni, tj)
  p(ni|tj) = ρ(ni, tj) / Σ_{ni'∈N} ρ(ni', tj)
  p(tj|ni) = ρ(ni, tj) / Σ_{tj'∈T} ρ(ni, tj')
  ```
- **Graph:** G = (N ∪ T, E), E = {(p(ni|tj), p(tj|ni))} directed edges with node-to-node jumping probabilities.
- **Initialization:** "We first initialize the graph nodes (i.e., sentences and tweets) with LexRank [6] scores to take into account representativeness factor." Both x⁰_i and y⁰_j = their LexRank scores.
- **Biased random walk** ("similar to the generalized Co-HITS algorithm [5]"):
  ```
  xi = λx⁰i + (1 − λ) Σ_{tj} p(ni|tj) yj
  yj = μy⁰j + (1 − μ) Σ_{ni} p(tj|ni) xi
  ```
  "Here we empirically set λ = μ = 0.5 and did not employ regularization for simplicity." Iterate "until convergence".
- **SumLevel generation:** "we can simply cut out the top ranked sentences and tweets at both sides to generate the news summary and tweet summary in such a way that the predefined length of the summaries are met." Note "there is not necessarily one-to-one correspondence of complementarity between news sentences and tweets".
- **SentLevel generation:** "we start from the top ranked sentences. For each sentence following the order, we then look up the transition matrix W^{N→T} to obtain the neighboring tweets of the chosen sentences whose transition probability is non-zero, from which the tweet with the highest complementarity score is selected to match the sentence. We gradually add the selected sentence-tweet pairs until the length of the summary is met." The paper explicitly adopts only the sentence-first order and leaves tweet-first and interleave variants "for future study".

## Datasets (names, sizes, language, domain, HOW OBTAINED)

**Name:** unnamed; the paper calls it "a dataset containing the news sentences and tweets for 10 trending subject matter" with "manually composed" gold-standard summaries. "Because we study a non-standard summarization task, there is no benchmark data sets available."

**How obtained (Section 6.1, quoted):**
1. "we collected 10 trending subjects that are popularly discussed on both traditional news media and Twitter during the first half year of 2012".
2. Gold news summaries: "The news summaries were taken from English Wikipedia and Wikinews." with URLs `http://en.wikipedia.org/wiki/Main_Page` and `http://en.wikinews.org/wiki/Main_Page`. "The first one or two paragraphs of an Wikipedia or Wikinews article usually contain a brief description of the subject which could be considered as a summary."
3. Gold tweet summaries: "we searched Twitter using the given subjects as queries, from the search results we manually selected the relevant tweets that appear complementary to the corresponding news sentences and added them into the tweets summaries."
4. Test corpus (the summarizer input): "we collected a set of test corpus (as the input of summarizer) for these 10 subjects by (1) referring to the news articles listed in the references of Wikipedia or Wikinews article about the subject, and (2) searching Twitter and collecting all the top ranked tweets. The news sentences and tweets in the standard summaries were excluded from the test corpus."

**Subjects (Table 3):** Death of Marie Colvin; Poland rail crash; Russian presidential election; Release of ipad 3; Syrian uprising; Death of Dick Clark; Mexican Drug War; Obama same sex marriage earn donation; Russian jet crash; Tymoshenho hunger strike.

**Statistics (Table 3; the extraction of the first two rows is column-interleaved — read as SN, then ST, then SUN, then SUT per column):**

| Subject | S_N (news sentences) | S_T (tweets) | S_UN (gold news summary words) | S_UT (gold tweet summary words) |
|---|---|---|---|---|
| Death of Marie Colvin | 266 | 168 | 198 | 206 |
| Poland rail crash | 135 | 114 | 192 | 185 |
| Russian presidential election | 199 | 157 | 151 | 214 |
| Release of ipad 3 | 217 | 405 | 207 | 194 |
| Syrian uprising | 164 | 690 | 161 | 196 |
| Death of Dick Clark | 139 | 209 | 180 | 94 |
| Mexican Drug War | 206 | 801 | 178 | 104 |
| Obama same sex marriage earn donation | 119 | 214 | 231 | 94 |
| Russian jet crash | 157 | 613 | 201 | 136 |
| Tymoshenho hunger strike | 125 | 581 | 249 | 92 |

Totals implied by the table: **1,727 news sentences** and **3,952 tweets** across the 10 subjects (sums of the S_N and S_T columns). Gold summary lengths are ~92–249 words (S_UN) and ~92–214 words (S_UT).

**Language / domain:** English; current-affairs news + Twitter (microblog) streams; first half of 2012. Note the sample outputs in Table 6 are raw tweets containing URLs (`bit.ly/KUbiee`), hashtags (`#Sukhoi SU95 #Indonesia`), typos and phone-number noise, i.e., the corpus is unnormalized.

**Additional gold-construction details:** "although we were unable to ensure that complementary tweets could be found for every news sentence, most of the sentences (nearly 85%) can still end up with some complementary tweets, from which we chose up to 2 tweets appearing the most complementary to each sentences." Worked example: "for the subject 'Death of Marie Colvin', we treated the paragraph in Wikipedia talking about her death as the news summary. Then we found the relevant tweets via Twitter search interface (choose 'top' – rank by relevance). For each sentence in the news summary, we looked for at most 2 tweets that are complementary to it."

**Preprocessing:** "we performed stemming but did not remove stop words, and the news articles were split into sentences using an online sentence split tool" with footnote URL `http://code.google.com/p/splitta/`.

## Data/code availability stated in the paper (quote any URL, 'available at', 'we will release', download link; if none, say NONE)

The only availability claim is in the contributions list:

> "4. We manually construct a gold-standard dataset of complementary summaries for the automatic evaluation of the problem, **which would be made publicly available**."

**No URL, no repository, no download link, no dataset name, no license, and no release statement beyond that future-tense sentence appears anywhere in the paper.** No code is released or promised; there is no "our code is available" statement. Future work says "Third, we will improve the quality of our data sets for more accurate ground truth." — again no link.

URLs that do appear in the paper are only tool/resource references, not data:
- `http://en.wikipedia.org/wiki/Main_Page` and `http://en.wikinews.org/wiki/Main_Page` (sources of the gold news summaries)
- `http://code.google.com/p/splitta/` (sentence splitter; **Google Code is defunct** — this link is dead)
- ROUGE-1.5.5 is named ("computed by running ROUGE-1.5.5") but no download URL is given.

**Verdict on availability: effectively NONE** (a vague promise, no artifact located in the paper).

## Evaluation (metrics, human evaluation required? protocol, folds)

- **Metric:** "We used the ROUGE metric [12] for automatically comparing the summaries produced with gold standard summaries. The recall values based on ROUGE-1, ROUGE-2 and ROUGE-SU4 were computed by running ROUGE-1.5.5."
- **Protocol:** "For fair comparison, all the methods to be compared were set up to generate summaries which have the same length limit. Each method was run for 10 times, and we took the average recall of the 10 runs over 10 subjects for the comparison among different methods. Based on the total 100 runs over the 10 subjects, we can also conduct statistical significance test using the 100 recall values." Significance by **paired t-test**: "Pairwised t-test indicates that all the improvements over the baseline methods are statistically significant at the confidence level of 95% (p<0.05)."
- **No folds / no cross-validation** — there is no train/test split because the method is unsupervised; all 10 subjects are used for both model fitting and evaluation.
- **Human evaluation: NOT performed.** The paper repeatedly flags this as missing: "In this regard, user experience study should be conducted in the future." and "the construction of gold-standard summaries reflecting sentence-level complementarity is also very hard and is subject to in a large extent the subjective judgement of human summarizers." Gold summaries are human-written but are used as automatic ROUGE references, not as a human-judged evaluation.
- **Ablation-style study:** Figure 5 reports ROUGE-1 recall under the 5 configurations of topics/aspects (z, y, zy, z+y, z+y+zy) for both the news summary and the tweets summary (axis values roughly 0.44–0.56 for news and 0.54–0.68 for tweets; exact per-bar values are not printed in the text).

## Baselines (list them)

"Since we're dealing with a new summarization problem, there is not a previous approach that we can compete directly. But some existing methods can be modified and/or performed on our data set."

- **BL-0: LexRank** [6] — run on the test corpus of both media; "LexRank simply did not take into account any complementarity features"; top ranked sentences and tweets output as summaries.
- **BL-1: KL-divergence (KLD)** — the contrastive-summarization approach of Lerman and McDonald [11] adapted to complementarity. Objective (Eq. 8): `L(SX, SY) = KL(P(TX),P(SX)) + KL(P(TY),P(SY)) + KL(P(TX),P(SY)) + KL(P(TY),P(SX))`, where "in order for complementary summaries instead of contrastive ones, we used the addition for KL(P(TX), P(SY)) and KL(P(TY), P(SX)) to replace the subtraction in Lerman and McDonald [11]"; P(.) is "the unigram model based on the word distributions estimated from our ccTAM model"; "We also used the greedy hill climbing algorithm for summary generation following [11]."
- **BL-2: Cosine and language modeling (LM)** — the jumping probability without the complementarity score: "p(ni|tj) and p(tj|ni) are reduced to be similarity-based." Two variants:
  - **Cosine** — idf-modified-cosine [6] as the similarity function.
  - **LM** — KL-divergence distance `KL(θni, θtj) = Σ_w p(w|θni) log( p(w|θni) / p(w|θtj) )` with Bayesian smoothing `p(w|θs) = (tf_{w,s} + μs · p(w|C)) / (|s| + μs)`, where "C is the corpus, μS is a smoothing parameter, and tfw,s is term frequency of w in s." (μs value **not stated**.)
- **BL-3: LexRank+Complementarity (LexComp)** — "This baseline extended the BL-0 by taking into account our complementarity score for choosing the corresponding tweets given the ranked news sentences... It is also a simplified version of our method for generating the sentence-level complementary summaries (see Section 5.3.2) by removing the random-walk-based co-ranking procedure."

The conclusion summarizes these as "four state-of-the-art baseline methods". Related work also positions against ccMix [21], ccLDA [15], contrastive summarization [10, 11, 17], DWFG/social context summarization [20], and TAM [16] (not run as baselines).

## Reported results (key numbers, so a reproducer knows the target)

**Table 4 — ROUGE recall, news summarization:**

| Method | ROUGE-1 | ROUGE-2 | ROUGE-SU4 |
|---|---|---|---|
| BL-0 LexRank | 0.3662 | 0.2178 | 0.2173 |
| BL-1 KLD | 0.4975 | 0.2975 | 0.3010 |
| BL-2 Cosine | 0.4018 | 0.2313 | 0.2358 |
| BL-2 LM | 0.4874 | 0.2952 | 0.2950 |
| BL-3 LexComp | 0.3662 | 0.2178 | 0.2173 |
| **Ours SumLevel** | **0.5533** | **0.3271** | **0.3325** |
| **Ours SentLevel** | **0.5533** | **0.3271** | **0.3325** |

"The improvements made by our method over the baselines are all statistically significant at 95% confidence level (p<0.05)."

**Table 5 — ROUGE recall, tweets summarization:**

| Method | ROUGE-1 | ROUGE-2 | ROUGE-SU4 |
|---|---|---|---|
| BL-0 LexRank | 0.5034‡ | 0.3632‡ | 0.3366‡ |
| BL-1 KLD | 0.6298‡ | 0.4340‡ | 0.4156‡ |
| BL-2 Cosine | 0.5581‡ | 0.3893‡ | 0.3704‡ |
| BL-2 LM | 0.6140‡ | 0.4282‡ | 0.4123‡ |
| BL-3 LexComp | 0.6300‡ | 0.4444† | 0.4271‡ |
| **Ours SumLevel** | **0.6643** | **0.4539** | **0.4425** |
| **Ours SentLevel** | **0.6726** | **0.4506** | **0.4411** |

"‡ — 95% confidence level (p<0.05); † — 90% confidence level (p<0.1)."

**Notes the authors give about these numbers:**
- "the performance of BL-0 (LexRank) and BL-3 (LexComp) are the same because the news summary produced by the two methods are generated by the same LexRank algorithm. Likewise, news summarization at SumLevel and SentLevel performs the same." (Hence identical news rows.)
- "There is not significant difference between our method at SumLevel and SentLevel. This is out of our original high expectation on the SentLevel complementarity, which indicates that the granularity of sentence level would be too rigorous for automatic complementarity finding."
- On the tweets side, the method beats all baselines at 95% "except for BL-3 (LexComp) by ROUGE-2 with a large margin at 90% confidence level".
- Configuration study: "the performance using aspect model (y) is better than using topic model (z)... Topic-aspect model (zy) performs better than topic or aspect model alone... Combining the all dimensions of topics, aspects and their mixture leads to the best results."

**Target for a reproducer (news side):** beat LexRank's ROUGE-1 ≈ 0.366 by a wide margin and land near **ROUGE-1 ≈ 0.55 / ROUGE-2 ≈ 0.33 / ROUGE-SU4 ≈ 0.33** on news; on tweets land near **ROUGE-1 ≈ 0.66–0.67 / ROUGE-2 ≈ 0.45 / ROUGE-SU4 ≈ 0.44**, with LexComp ≈ 0.63/0.44/0.43 as the strongest baseline. Table 6 gives a qualitative example (subject "Russian jet crash") comparing the method's SumLevel output, the gold output, and BL-0 output.

## Implementation complexity

**High** (bordering on very high if the goal is faithful replication).

Why:
1. **Custom topic model from scratch.** ccTAM is a novel combination of ccLDA [15] and the two-dimensional topic-aspect model [16]; neither is in standard toolkits (no gensim/MALLET implementation). It requires 9 coupled word distributions (φz, φy, φzy, φcz, φcy, φczy per collection, plus φb), a 3-valued level variable l and a 4-valued route variable x per token, with Gibbs update equations for each (topic, aspect, topic-aspect) × (general, news-specific, tweet-specific) combination. The paper shows only the topic equations (Eq. 6–7) and says aspects/topic-aspect "analogous" — the student must derive ~12 more conditional distributions.
2. **Long sampling schedule.** α=10, β=0.01, γx=10, γl=10, δ=10, 100 burn-in iterations, then 10 samples spaced 10 iterations apart (≈200+ full sweeps), for each of the 10 subjects, and each method is run 10 times → up to ~100 model fits. Small corpora (1.7k sentences, ~4k tweets) keep this feasible, but the per-token sampler with 9 distributions is fiddly and slow in pure Python.
3. **Two-stage system.** After the topic model, a second nontrivial component is needed: LexRank initialization, a bipartite graph with directed idf-modified-cosine × Icomp jumping probabilities, and a Co-HITS-style biased random walk (λ=μ=0.5) with convergence checking, plus two different summary-generation modes.
4. **Evaluation tooling.** ROUGE-1.5.5 is a Java-era tool with the familiar setup pain; ROUGE-SU4 recall with stemming is easy to get wrong, and the paper's protocol (10 runs × 10 subjects, paired t-test over 100 values) must be replicated for a comparable significance claim.
5. **No reference implementation, no data, and several unspecified numbers** (K, A, V, μs, convergence threshold, stemming algorithm, exact length limits) mean many micro-decisions.

Mitigating factor: the components are individually well documented in the cited literature (LDA/ccLDA [15], TAM [16], LexRank [6], Co-HITS [5]), and the corpora are tiny, so a patient student with topic-modeling experience can build an approximation. But an exact number-matching replication is not realistic.

## Reproducibility obstacles (concrete)

1. **No released dataset.** The paper only says the gold dataset "would be made publicly available" — no URL, no name, no repository. The paper's own test corpus (news sentences + tweets per subject) is also unreleased.
2. **Twitter data cannot be re-crawled.** The corpus is tweets from "the first half year of 2012" obtained by "searching Twitter and collecting all the top ranked tweets" and by "Twitter search interface (choose 'top' – rank by relevance)". Twitter/X search results are non-reproducible even today (personalized, time-decayed ranking), and the 2012 tweets are largely unavailable: the public API now requires paid access and historical full-archive search is a paid academic track; many 2012 accounts/tweets are deleted or suspended. The paper gives **no tweet IDs**, so hydration is impossible.
3. **Human-authored gold summaries with subjective complementarity labels.** "The creation of gold standard was done as the following… we manually selected the relevant tweets that appear complementary to the corresponding news sentences"; the authors themselves concede "the construction of gold-standard summaries reflecting sentence-level complementarity is also very hard and is subject to in a large extent the subjective judgement of human summarizers" and that "In the gold-standard summaries, it is even not clear-cut to tell which tweets are complementary to specific news sentences". Any new annotator will produce different references and therefore different ROUGE numbers.
4. **Gold news summaries depend on Wikipedia/Wikinews revisions.** The references were taken from live wiki articles, which are edited over time — the exact "first one or two paragraphs" of 2012 are not frozen (revision IDs not given).
5. **Dead tool.** The sentence splitter footnote is `http://code.google.com/p/splitta/`; Google Code shut down in 2015/2016, so the link is dead (the tool survives only in third-party mirrors/PyPI-ish forks).
6. **Unspecified hyperparameters.** K (#topics) and A (#aspects) are never given numerically; the LM baseline's smoothing μs is not stated; the "predefined length threshold of the summaries" is only implied by Table 3's S_UN/S_UT word counts; the random-walk convergence criterion and stemming algorithm are not stated; vocabulary size V is not reported.
7. **No code and no baseline implementations.** BL-1 (KLD) requires re-implementing Lerman & McDonald's [11] greedy hill-climbing objective with the paper's sign modification; BL-2 LM requires the Bayesian smoothing setup; none are provided.
8. **ROUGE-1.5.5** must be obtained and configured (Java, old scripts), and the paper's exact options ("we performed stemming but did not remove stop words") must be matched to compare against its numbers.
9. **Tiny evaluation scale.** 10 subjects, ~92–249-word gold summaries; ROUGE differences of a few points are within noise, which is exactly why the paper needs 100 runs and a paired t-test. A student with a different 10 subjects cannot expect the same absolute numbers.
10. **No human/user study** to fall back on: the paper defers it to future work, so there is no qualitative protocol to copy.

## Minimum viable reproduction plan (2–4 weeks)

**Realistic goal:** reproduce the *pipeline and the relative ordering of methods*, not the exact ROUGE values.

**Week 1 — data substitution (the crux).**
- Do not attempt to recover the 2012 Twitter corpus. Substitute a *publicly available* news+tweet event dataset for one or a few events, e.g. an event-centric collection with paired news articles and tweets that you can still download (a modern event dataset with tweet IDs that are still hydratable, or a public Weibo/Twitter event corpus if you also want the Chinese angle). Fall back to: Wikipedia/Wikinews lead paragraphs as gold news summaries (same recipe as the paper) + a small hand-collected set of tweets for a recent event that you can still search, and write your own gold tweet summary with the paper's rule ("at most 2 tweets complementary to each news sentence", target ≈100–250 words).
- Reuse the paper's preprocessing exactly where it is specified: stem, keep stop words, split news into sentences (substitute NLTK/spaCy for the dead `splitta` link). Aggregate tweets per user into one document, as the paper does.
- Aim for the paper's scale: ~10 subjects, ~1.7k news sentences, ~4k tweets total, gold summaries ~100–250 words. Even 3–5 subjects is workable if you keep the length limits.

**Week 2 — model (the hard part), simplified first.**
- Start with the **z + y configuration only** (topic model + aspect model, i.e. 2 general + 4 collection-specific distributions instead of 9). This alone captures the paper's central claim, since Figure 5 shows the full z+y+zy configuration is best but z and y individually already work.
- Implement a plain collapsed Gibbs sampler for the two-collection LDA (ccLDA) and add the aspect dimension; use α=10, β=0.01, γx=10, γl=10, δ=10, 100 burn-in iterations, 10 samples with a gap of 10 iterations — all directly from the paper. Sweep K ∈ {10, 20, 50} and A ∈ {3, 5, 10} since the paper does not state values.
- Implement Icomm/Idiff/Icomp exactly as Eq. 1–5 (including the piecewise peak at Icomm = Idiff, which is the paper's distinctive contribution and easy to get right).

**Week 3 — co-ranking and baselines.**
- Implement LexRank (or use an existing implementation) for initialization, the bipartite graph with ρ = idf-modified-cosine × Icomp, and the Co-HITS-style iteration with λ = μ = 0.5; stop on a small L1 change threshold (paper does not state one).
- Implement SumLevel (cut top-ranked lists to length limit) and SentLevel (sentence-first, pick argmax-Icomp neighbor with non-zero transition probability).
- Implement the baselines that are cheap and most informative: **BL-0 LexRank**, **BL-2 Cosine** and **BL-2 LM** (no complementarity), and **BL-3 LexComp** (LexRank + Icomp matching, no random walk). BL-1 KLD is optional (needs a greedy hill-climb objective) but it is the strongest news-side baseline, so include it if time permits.

**Week 4 — evaluation.**
- ROUGE-1/2/SU4 **recall** with ROUGE-1.5.5 (stemming on, stop words kept), same length limit across methods, 10 runs per method averaged over subjects, paired t-test over the runs.
- **Expected numbers.** If the data substitution is reasonable (news side dominated by well-formed article sentences), expect LexRank ≈ 0.35–0.40 ROUGE-1, Cosine ≈ 0.38–0.42, LM/KLD ≈ 0.45–0.52, LexComp ≈ 0.36–0.42 (news; it inherits LexRank's news summary) and ≈ 0.55–0.65 on tweets, with the full model on top at ≈ 0.50–0.57 (news) and ≈ 0.62–0.68 (tweets). The **relative ordering** — Ours > KLD/LM > Cosine > LexRank, and LexComp > LexRank on tweets — is the reproducible finding; exact values are not.
- Report the configuration ablation (z, y, zy, z+y, z+y+zy) on ROUGE-1 recall as a cheap, high-value figure that mirrors Figure 5.

**What to substitute, summarized:** dead `splitta` → NLTK/spaCy; unreleased 2012 corpus → public event dataset or self-built wiki+recent-tweet set; unreleased code → own implementation; unstated K/A → small grid search; BL-1 KLD → optional.

## Verdict

This is a **conceptually attractive but materially poor reproduction target**. On the plus side the paper is short, self-contained and unusually explicit about the parts that usually get lost: the full generative process, the Gibbs update equations, and a complete hyperparameter list (α = 10, β = 0.01, γx = 10, γl = 10, δ = 10, 100 burn-in + 10 samples with gap 10, λ = μ = 0.5), plus an explicit numeric target (news ROUGE-1 0.3662 → 0.5533; tweets 0.5034 → 0.6643) and a clear, small-scale protocol (10 subjects, ~1.7k sentences, ~4k tweets, 10 runs, paired t-test). On the minus side, essentially every input is irrecoverable: the dataset is promised but never released ("which would be made publicly available", no URL anywhere), the 2012 tweets have no IDs and cannot be re-crawled under today's Twitter/X API, the gold summaries are subjective human judgments the authors themselves call "not clear-cut", the sentence splitter link points at defunct Google Code, there is no code, K and A are never stated numerically, and no human evaluation exists to substitute for ROUGE. The method itself is also genuinely hard to re-implement faithfully — nine coupled word distributions, a two-stage pipeline, and a 100-run evaluation protocol. It is a good target for a **strong student who already knows topic modeling and is willing to rebuild the dataset from Wikipedia/Wikinews plus a modern event corpus**, treating the paper's numbers as an ordinal target rather than an exact one; it is a poor target for anyone who wants to download the data, run the authors' code, and check the table — that path does not exist here.
