# Social Context Summarization

## Bibliographic info

- **Title:** Social Context Summarization
- **Authors:** Zi Yang⋆, Keke Cai†, Jie Tang⋆, Li Zhang†, Zhong Su†, Juanzi Li⋆
  - ⋆ Department of Computer Science and Technology, Tsinghua University, China
  - † IBM, China Research Lab
  - Emails: `{yangzi, tangjie, ljz}@keg.cs.tsinghua.edu.cn`, `{caikeke, lizhang, suzhong}@cn.ibm.com`
- **Venue / year:** SIGIR'11 — 34th ACM SIGIR conference, July 24–28, 2011, Beijing, China. Pages **255–264** (page numbers 255…264 appear in the extracted text). Copyright line: "Copyright 2011 ACM 978-1-4503-0757-4/11/07 ...$10.00."
- **Categories:** "H.3.1 [Information Storage and Retrieval]: Content Analysis and Indexing; H.2.8 [Database Management]: Data Mining; J.4 [Computer Applications]: Social and Behavioral Sciences"
- **General Terms:** "Algorithms, Experimentation"
- **Keywords:** "Document summarization, Social context, Factor graph, Twitter"
- **Funding (Acknowledgments):** "Natural Science Foundation of China (No. 61073073, No. 60703059, No. 60973102), Chinese National Key Foundation Research (No. 60933013, No.61035004), National High-tech R&D Program (No. 2009AA01Z138)."

## Task

**This paper IS about Twitter microblogs — but not about summarizing tweets alone.** It is about *summarizing standard Web documents (news pages) using Twitter as social context*, and simultaneously summarizing the tweet thread. This is **not** product-review summarization, and **Weibo is never mentioned** (the only microblog platform named is Twitter: "http://www.twitter.com, a microblogging system"). Language: English news documents + English tweets.

**Novel problem claimed:** "We study a novel problem of social context summarization for Web documents." The motivating question: "Which parts in a document are social users really caring about? How can we generate summaries for standard documents by considering both the informativeness of sentences and interests of social users?"

**Definitions given (Section 2):**

- **Definition 1 (Social context):** "Given a Web document d, its social context C_d is defined as ⟨M_d, U_d⟩, where M_d is a set of comments on d written by users U_d in a social network."
- **Definition 2 (Social Context Augmented Network, SCAN):** "Social Context Augmented Network G_d = (S_d, C_d, E_d) is defined as a network that is built upon the sentence set S_d of document d and its social context C_d, where the edge set E_d contains three types of edges: E_ds, E_dm, and E_du." E_ds = sentence–sentence relations, E_dm = message–message relations, E_du = user–user relations. Three layers: Document Layer (sentences s_i), Microblog Layer (tweets m_i), User Layer (users u_i).
- **Definition 3 (Social Context Summarization):** "Given a social context augmented network G_d, the goal of social context summarization is to generate a summary which consists of two pieces of information: the most important sentences S_d* ⊆ S_d and the most representative messages M_d* ⊆ M_d."

**Two sub-problems:** "Key Sentence Extraction and Tweet Summarization" — mutually reinforcing. Input: a Web document `d` (news article) + its social context (tweets containing the document URL, plus their authors). Output: selected sentences S_d* **and** selected tweets M_d*.

**Extractive vs abstractive:** strictly **extractive** — a subset of sentences and a subset of tweets are selected; no generation.

**Supervised:** "The overview of the proposed method is a supervised framework." Training requires per-sentence and per-tweet binary labels y_i (1 = important, 0 = unimportant).

## Method (implementable detail)

**Model: Dual Wing Factor Graph (DWFG).** A three-layer factor graph; upper "wing" models sentence extraction, lower "wing" models tweet summarization, bridged by inter-domain factors `h`. Binary variable y_i ∈ {0,1} per sentence s_i ∈ S_d or tweet m_i ∈ M_d.

### Three factor types

**(1) Local attribute factor (Eq. 1):**
```
f_{i,c}(λ_c, y_i) = exp(λ_c · x_{i,c} · y_i)
```
where x_{i,c} is the value of the c-th feature of sentence s_i or tweet m_i, and λ_c is the learned feature weight. (Paper also calls this "the local entropy".)

**(2) Intra-domain dependency factor (Eq. 2):**
```
g_{ij,c}(µ_c, y_i, y_j) = exp(µ_c)  if some condition holds
                        = 1        otherwise
```
"the interaction has a positive influence only if the weight µ_c is greater than 0."
- *Sentence pairs:* "the factor takes value exp µ_c if y_i ≠ 1 or y_j ≠ 1" — i.e., penalizes selecting two highly similar sentences simultaneously. "To avoid high computational complexity, we constrain only consecutive and similar sentences, i.e., establish sentence relation for sentence s_i and s_{i+1} whose mutual similarity (e.g., cosine similarity) exceeds the threshold θ_g."
- *Tweet pairs:* "we consider the two interactions between tweets: replying and retweeting. If tweet m_i replies or retweets tweet m_j, then m_j successfully excites and attracts attentions from others, and it is reasonable that m_j is more important than its succeeding tweets in the thread. Formally, for such a tweet pair m_i and m_j, the factor takes value exp µ_c if y_i ≤ y_j."

**(3) Inter-domain dependency factor (Eq. 3):**
```
h_ij(ν, y_i, y_j) = exp(ν)  if y_i = y_j
                  = 1       otherwise
```
"if tweet m_j is considered as a representative tweet, i.e., y_j = 1, then a sentence s_i highly similar to m_j (with similarity more than a threshold θ_h) should be biased towards the same label, i.e., y_i = 1." ν is the single inter-domain weight.

### Objective function (Eq. 4)

"the objective function can be defined as the normalized product of Eqs. 1 - 3 for all the instances":
```
max_Θ  (1/Z) · Π_i Π_{j∈T} Π_{c∈C}  f_{i,c}(λ_c, y_i) · g_{ij,c}(µ_c, y_i, y_j) · h_ij(ν, y_i, y_j)
```
Z = normalization factor summing P(Y|X, Θ) over all label configurations; Y = {y_i}_i; **Θ = {λ_c}_c ∪ {µ_c}_c ∪ {ν}**.

**Regularization:** "we add a penalty term −½‖Θ‖²/σ², a spherical Gaussian prior, into the objective function" (as in max-entropy/CRF work [6, 27, 28]). σ value: **not stated**.

**Optimizer:** "We use L-BFGS, a quasi-Newton method for solving the non-linear optimization problem (i.e., Eq. 4)."

**Degeneracy claims:** if ν = 0 and factors only defined for sentences → DWFG degenerates to "the summarization approach based on linear-chain CRF [28]"; if additionally all µ_c = 0 → "DWFG is turned into the logistic regression classifier [25]".

### Inference (Section 3.3, Algorithm 1)

The graph contains cycles, so exact forward–backward is impossible; "we propose an approximate inference approach based on the loopy sum-product or max-sum algorithm."

Messages: p_ij = message variable→factor, q_ij = factor→variable.
```
p_ij = r_i + Σ_{k∈N(i)\{j}} q_ik                                    (Eq. 5)
q_ij = max{t_ij(1,1) + p_ji, t_ij(1,0)} − max{t_ij(0,1) + p_ji, t_ij(0,0)}   (Eq. 6)
r_i  = Σ_{c∈C} ( log f_{i,c}(λ_c, y_i=1) − log f_{i,c}(λ_c, y_i=0) )        (Eq. 7)
t_ij(y_i, y_j) = log g_{ij,c}(µ_c, y_i, y_j)  or  log h_ij(ν, y_i, y_j)      (Eq. 8)
```
Simplified for the sentence dependency factor: `q_ij = max{p_ji − µ_c, 0} − max{p_ji, 0}`.
Final label: `y_i = 1 if p_ij + q_ij > 0 for some j, else 0` (Eq. 9).

**Algorithm 1 (Social context summarization with DWFG):**
```
input : document d with social context C_d and SCAN G_d, weight variables Θ, number of iterations I
output: summary: important sentences S_d* and messages M_d*
1  calculate {r_i}_i according to Eq. 7;
2  {q_ij}_{i,j} ← 0;
3  for i ← 1 to I do
4      update p_ij according to Eq. 5;
5      update q_ij according to Eq. 6;
6  foreach s_i ∈ S_d and m_i ∈ M_d do
7      calculate y_i according to Eq. 9;
8  S_d* ← {s_i ∈ S_d | y_i = 1};
9  M_d* ← {m_i ∈ M_d | y_i = 1};
```
**Value of I (number of iterations): not stated.**

**Complexity:** "proportional to I · (|E^s| + |E^m| + |E^c|)" where |E^s|, |E^m|, |E^c| are the numbers of sentence relations, tweet relations and inter-domain relations. "the inference algorithm can be easily parallelized or distributed onto clusters" — "the design of distributed algorithm will be reported elsewhere."

### Features — 11 features (Table 2), all shared in form across both domains

| N° | Domain | Description |
|----|--------|-------------|
| 1 | Web documents | sentence position in document |
| 2 | Web documents | sentence position in paragraph |
| 3 | Web documents | average TF-IDF score of words in sentence |
| 4 | Web documents | the number of common words to the title |
| 5 | Web documents | sentence length |
| 6 | Web documents | the log likelihood generated by the document |
| 7 | Tweets | average TF-IDF score of words in post |
| 8 | Tweets | tweet length |
| 9 | Tweets | the log likelihood generated by the tweet thread |
| 10 | Tweets | the number of users following the author |
| 11 | Tweets | the PageRank score of the post's author |

Nominal encoding for Feature 1: "4 if the sentence was extracted from the title of the document, 3 if it was extracted from the subtitle, 2 if the sentence was located in the first paragraph of the original document, 1 if the sentence was located in the last paragraph, and 0 otherwise."

**Normalization:** "we normalize the feature values by the mean value of corresponding feature" (ranges differ: max of Feature 4 = 15, max of Feature 6 = 1.495).

**Per-domain models:** "we trained an individual model on each domain respectively to capture the distinctiveness."

### Hyperparameters WITH VALUES

| Parameter | Value |
|---|---|
| θ_g (sentence-dependency similarity threshold) | **0.1** (default in main results); swept 0 → 1 in steps of 0.1 |
| θ_h (inter-domain sentence–tweet similarity threshold) | **0.8** (default in main results); swept 0 → 1 in steps of 0.1 |
| Cross-validation | **10-fold** ("one fold is for test and the other nine folds for training") |
| Optimizer | L-BFGS |
| Prior | spherical Gaussian, −½‖Θ‖²/σ² (σ value not stated) |
| Number of inference iterations I | not stated |
| Number of features | 11 ("we only extract 11 basic and straight-forward features") |
| Number of sentences/tweets extracted | set equal to the human summary length ("we keep the number of sentences extracted be equal with that of the human summary for fair comparison") |
| Similarity measure | cosine similarity ("e.g., cosine similarity") |
| Number of models | 1 per domain × 5 domains |

**Threshold sensitivity findings:** "when θ_g increases from 0.0 to 0.5, the performance drops by 5% ∼ 16% in terms of F1 and ROUGE"; "with θ_g is 0.7, the performance reaches a local maximum"; "the performance of sentence identification reaches the global maximum when θ_h is set between 0.5 and 0.6"; "the performance of important tweet extraction is relatively stable."

## Datasets

**Language:** English (English news pages + English tweets). Source platform: **Twitter** (crawled); document sources: CNN, BBC, MTV, ESPN, Mashable.

**How obtained (Section 4.1.1):**
1. Seed: "we selected the first and also one of the most popular users on Twitter, Jack Dorsey (@jack), and collected his followers. We took these users as seed users and used a crawler to collect all followers of these users by traversing following edges. We continue the traversing process, which produced in total **4,874,389 users**."
2. "The crawler monitored tweets posted by these users from **January 1st 2010 to July 17th 2010**. We extracted all tweets posted by these users and in total there are **404,544,462 tweets**."
3. "We use explicit URLs (starting with "http://" or "https://") to identify Web documents from the Twitter data." Shortened URLs (tinyurl.com, bit.ly) decoded: "We implemented a shorten URL decoder based on a HTTP client to obtain the decoded URLs and finally aligned the obtained URLs."
4. Deduplication by unique document ID, e.g. `http://news.bbc.co.uk/1/hi/england/8604663.stm`, `http://news.bbc.co.uk/2/hi/uk_news/england/8604663.stm`, `http://news.bbc.co.uk/2/hi/8604663.stm` → "We further group such Web documents according to the unique document ID: 8604663."
5. "Finally, we use the most frequent (**200,000**) URLs to constitute the collection of Web documents and employ their associated (**12,964,166**) tweets to construct the social context." (Distribution plotted in Figure 3, log-log; "the distribution of frequency follows the power law.")
6. Filtering: "many frequent URLs are advertisement pages. To guarantee the quality of the data set, we restrict ourselves to a few high-quality news websites such as CNN, BBC, Mashable etc."
7. "According to the selected URLs, we crawled the pointed webpages... The Web documents were then segmented into a set of sentences with the **jTokeniser Toolkit** (`http://code.google.com/p/jtokeniser/`)."

**Table 1 — Description on employed domains (Data Size: Doc / Tweet):**

| Domain | Description | Doc | Tweet |
|---|---|---|---|
| cnn.com | one of the most popular news websites | 1,303 | 62,225 |
| bbc.co.uk | the most popular news website in the UK | 336 | 10,264 |
| mtv.com | one of the most popular music television networks | 176 | 9,848 |
| espn.go.com | one of the world's leading sports media | 171 | 4,320 |
| mashable.com | the world's largest tech blog | 2,940 | 114,441 |

**Totals implied by Table 1: 4,926 Web documents and 201,098 tweets** (sums of the table; not stated as totals in the paper).

**Gold labels (Section 4.1.2):** "we further manually validated the informativeness of all the selected Web documents by posting both the Web documents and tweets on Amazon Mechanical Turk. We totally issued **1,145 HITs** on Mechanical Turk, and for each HIT we asked **at least two different workers** to read both Web documents and their corresponding tweets. All the HITs were divided into **12 batches** with each assignment entitled "Key sentences and tweets extraction from news and related tweets"." Instructions: "extract several sentences from news that attract them mostly", and "after reading the news, extract the most interesting tweets that appeal you mostly". "We required the workers to label **no less than 5 tweets and 10 Web document sentences**. Finally, **158 different users** have participated in annotating the benchmark."

**No train/test split files, no annotation guidelines document, and no per-instance labels are given in the paper.** No statistics on average document length / average tweets per document are reported.

## Data/code availability stated in the paper

**A release statement IS present (the only one), attached to the evaluation section:**

> "Related support materials (data description and software) of this work can be found at **http://arnetminer.org/socialcontext/**."

(Lines 400–401 of the extracted text; the sentence is split across the page break: "Related support materials (data description and software) of this work / can be found at http://arnetminer.org/socialcontext/.")

Other URLs quoted in the paper (all third-party tools, not releases of this work's data):
- `http://www.twitter.com` (footnote 1, "a microblogging system")
- `http://code.google.com/p/jtokeniser/` (footnote 5, tokenizer)
- `http://mturk.com` (footnote 6, annotation marketplace)
- `http://dragon.ischool.drexel.edu/` (footnote 7, Dragon Toolkit ROUGE implementation)

**No GitHub repository, no license, no data format description, and no statement about whether the Twitter crawl is redistributable.** Note: I attempted to fetch `http://arnetminer.org/socialcontext/` while preparing this analysis and received **HTTP 403 — "access to this content has been restricted by country restriction"**, so the release page is currently unreachable from this environment (the mirror/redirect status cannot be confirmed from the paper alone).

## Evaluation

**Metrics:**
1. **Precision, Recall, F-measure** — "two performance metrics applied in [29] were adopted". F1 reported: `P = |S_ref ∩ S_cand| / |S_cand|`, `R = |S_ref ∩ S_cand| / |S_ref|`, `F1 = 2PR/(P+R)`, where S_cand and S_ref are the candidate and reference summary sentences.
2. **ROUGE** — "We employ the ROUGE evaluation methods implemented in the Dragon Toolkit and report the experimental results in terms of **ROUGE-1 and ROUGE-2 with stop words filtered out**."

**Human evaluation required?** **YES — human judgment is the ground truth.** The reference summaries come from Amazon Mechanical Turk (1,145 HITs, ≥2 workers each, 158 annotators). However, no inter-annotator agreement statistic (e.g. kappa) is reported, and no automatic metric is used to validate the human labels.

**Protocol:**
- **10-fold cross validation** ("All experiments were conducted in the 10-fold cross validation procedure, where one fold is for test and the other nine folds for training").
- Separate model per domain; results reported per domain (CNN, BBC, MTV, ESPN, Mashable) and pooled ("All").
- "Since ROUGE is a recall-oriented metric, we keep the number of sentences extracted be equal with that of the human summary for fair comparison. Specifically, we select the sentences and tweets with the greatest positive beliefs according to p(y_i = 1|X) (cf. Eq. 9)."
- Two separate result tables: **Table 3 for Web documents**, **Table 4 for tweet thread**.
- Significance: "the performances are statistically significantly improved on the MTV and ESPN domains by conducting **sign test** on the results, where the **p values are much smaller than 0.01**." (Only MTV and ESPN tested/mentioned; no significance test for other domains or the pooled "All" column.)
- Belief thresholding detail (case study): "Beliefs taking values of 0.5 indicate that the corresponding factors have no preference... Beliefs taking values greater than 0.5 convey positive attitudes."

## Baselines

Six supervised baselines plus several unsupervised ones:

1. **SVM** — "SVM classifiers (SVM) ... are performed for each sentence and tweet only with its local features."
2. **LR** — "logistic regression classifiers (LR) ... only with its local features."
3. **LC-CRF** — "Linear-chain and tree-structured CRF models (LC-/TS-CRF) are respectively trained and tested on documents and tweet threads, i.e., inter-domain relationships are considered as a supplement to the basic local features. The linear-chain CRF baseline model employed in the sentence summarizaiton is equivalent to the method proposed in [28]." **Note: TS-CRF is described but does NOT appear as a row in Table 3 or Table 4.**
4. **SVM+** — feature-augmented SVM: "for each sentence s_i in a document, we append 11 features (x_{s_i,7}, ..., x_{s_i,17}), where each of x_{s_i,7}, ..., x_{s_i,12} adds up the corresponding feature values of its similar sentences, and each of x_{s_i,13}, ..., x_{s_i,17} adds up the corresponding feature values of its related tweets. Similarly, for each tweet in the thread, we append 11 features, which are the sums of feature values of its relevant sentences or tweets." (11 + 11 = 22 features.)
5. **LR+** — same feature augmentation with logistic regression.
6. **Random** — "randomly select sentences or tweets (Random) as the basic unsupervised method."
7. **DocLead** / 8. **ParaLead** — given jointly in one sentence: "Another baseline method for summarization is to select the sentences according to their positions in the document or paragraph (DocLead and ParaLead)." The paper does not separately define which of the two uses document position vs paragraph position.
9. **PR** — "we apply PageRank algorithm for summarization on the whole graph consisting of three types of relationships (PR) [24]."

The abstract's baseline list is "CRF, SVM, LR, PR, and DocLead".

## Reported results (key numbers as targets)

**Table 3 — Experimental results for Web documents** (F1 / ROUGE-1 / ROUGE-2), columns CNN, BBC, MTV, ESPN, Mash, All:

| Method | CNN | BBC | MTV | ESPN | Mash | **All** |
|---|---|---|---|---|---|---|
| SVM | 0.288 | 0.322 | 0.490 | 0.337 | 0.321 | 0.351 |
| LR | 0.284 | 0.340 | 0.531 | 0.352 | 0.297 | 0.361 |
| LC-CRF | 0.307 | 0.349 | 0.596 | 0.364 | 0.340 | 0.391 |
| SVM+ | 0.283 | 0.341 | 0.476 | 0.359 | 0.324 | 0.357 |
| LR+ | 0.277 | 0.332 | 0.482 | 0.366 | 0.305 | 0.352 |
| Random | 0.314 | 0.321 | 0.455 | 0.351 | 0.305 | 0.349 |
| DocLead | 0.334 | 0.356 | 0.441 | 0.317 | 0.415 | 0.373 |
| ParaLead | 0.298 | 0.316 | 0.508 | 0.338 | 0.323 | 0.356 |
| PR | 0.354 | 0.338 | 0.453 | 0.351 | 0.399 | 0.379 |
| **DWFG (F1)** | **0.341** | **0.450** | **0.642** | **0.518** | 0.330 | **0.456** |
| SVM (R-1) | 0.224 | 0.612 | 0.392 | 0.520 | 0.511 | 0.452 |
| LR (R-1) | 0.197 | 0.599 | 0.585 | 0.583 | 0.599 | 0.513 |
| LC-CRF (R-1) | 0.281 | 0.551 | 0.667 | 0.583 | 0.618 | 0.540 |
| SVM+ (R-1) | 0.176 | 0.563 | 0.400 | 0.635 | 0.546 | 0.464 |
| LR+ (R-1) | 0.171 | 0.610 | 0.362 | 0.620 | 0.605 | 0.473 |
| Random (R-1) | 0.429 | 0.426 | 0.455 | 0.470 | 0.405 | 0.437 |
| DocLead (R-1) | 0.410 | 0.473 | 0.542 | 0.372 | 0.576 | 0.475 |
| ParaLead (R-1) | 0.414 | 0.337 | 0.629 | 0.432 | 0.414 | 0.445 |
| PR (R-1) | 0.433 | 0.325 | 0.563 | 0.426 | 0.482 | 0.446 |
| **DWFG (R-1)** | 0.389 | **0.594** | **0.777** | **0.701** | **0.613** | **0.615** |
| SVM (R-2) | 0.151 | 0.500 | 0.336 | 0.412 | 0.412 | 0.362 |
| LR (R-2) | 0.131 | 0.491 | 0.522 | 0.481 | 0.496 | 0.424 |
| LC-CRF (R-2) | 0.197 | 0.496 | 0.542 | 0.515 | 0.516 | 0.453 |
| SVM+ (R-2) | 0.115 | 0.463 | 0.351 | 0.539 | 0.449 | 0.383 |
| LR+ (R-2) | 0.110 | 0.498 | 0.310 | 0.528 | 0.501 | 0.390 |
| Random (R-2) | 0.323 | 0.325 | 0.387 | 0.359 | 0.301 | 0.339 |
| DocLead (R-2) | 0.371 | 0.424 | 0.519 | 0.350 | 0.525 | 0.438 |
| ParaLead (R-2) | 0.363 | 0.320 | 0.569 | 0.370 | 0.354 | 0.395 |
| PR (R-2) | 0.389 | 0.307 | 0.533 | 0.387 | 0.441 | 0.411 |
| **DWFG (R-2)** | 0.228 | 0.417 | **0.687** | **0.612** | **0.557** | **0.500** |

**Table 4 — Experimental results for tweet thread** (F1 / ROUGE-1 / ROUGE-2):

| Method | CNN | BBC | MTV | ESPN | Mash | **All** |
|---|---|---|---|---|---|---|
| SVM | 0.323 | 0.542 | 0.640 | 0.610 | 0.379 | 0.499 |
| LR | 0.370 | 0.531 | 0.606 | 0.616 | 0.408 | 0.506 |
| LC-CRF | 0.378 | 0.547 | 0.637 | 0.603 | 0.417 | 0.516 |
| SVM+ | 0.378 | 0.537 | 0.641 | 0.607 | 0.405 | 0.514 |
| LR+ | 0.369 | 0.537 | **0.725** | 0.608 | 0.408 | **0.529** |
| Random | 0.356 | 0.486 | 0.665 | 0.586 | 0.353 | 0.489 |
| PR | 0.281 | 0.428 | 0.666 | 0.520 | 0.327 | 0.445 |
| **DWFG (F1)** | **0.380** | **0.547** | 0.639 | **0.633** | 0.380 | 0.516 |
| SVM (R-1) | 0.531 | 0.631 | 0.670 | 0.701 | 0.617 | 0.630 |
| LR (R-1) | 0.657 | 0.618 | 0.702 | 0.708 | 0.737 | 0.684 |
| LC-CRF (R-1) | 0.673 | 0.647 | 0.730 | 0.703 | 0.748 | 0.700 |
| SVM+ (R-1) | 0.661 | 0.659 | 0.672 | 0.694 | 0.740 | 0.685 |
| LR+ (R-1) | 0.655 | 0.660 | 0.692 | **0.756** | 0.737 | 0.700 |
| Random (R-1) | 0.631 | 0.617 | 0.740 | 0.704 | 0.622 | 0.663 |
| PR (R-1) | 0.167 | 0.382 | 0.522 | 0.439 | 0.229 | 0.348 |
| **DWFG (R-1)** | 0.669 | 0.647 | 0.731 | 0.763 | 0.700 | **0.702** |
| SVM (R-2) | 0.486 | 0.571 | 0.661 | 0.678 | 0.570 | 0.593 |
| LR (R-2) | 0.616 | 0.556 | 0.696 | 0.684 | 0.698 | 0.650 |
| LC-CRF (R-2) | 0.610 | 0.563 | 0.708 | 0.699 | 0.682 | 0.653 |
| SVM+ (R-2) | 0.620 | 0.598 | 0.663 | 0.671 | 0.700 | 0.651 |
| LR+ (R-2) | 0.613 | 0.601 | 0.684 | **0.731** | 0.698 | **0.666** |
| Random (R-2) | 0.572 | 0.533 | 0.724 | 0.671 | 0.557 | 0.611 |
| PR (R-2) | 0.157 | 0.356 | 0.519 | 0.432 | 0.218 | 0.337 |
| **DWFG (R-2)** | 0.599 | 0.563 | 0.709 | 0.722 | 0.631 | 0.645 |

**Headline claims to reproduce:**
- Abstract: "our approach obtains significant improvement (averagely **+5.0%-17.3%**) over several alternative methods (CRF, SVM, LR, PR, and DocLead) on the performance of summarization."
- Introduction: "by leveraging the social context information, our approach can significantly improve (on average **+10.8%**) the performance of summarization... our approach clearly outperforms (averagely **+5.0%-17.3%**) the baseline methods."
- **Document summarization (Table 3): DWFG wins on the pooled "All" column on all three metrics** (F1 0.456 vs best baseline LC-CRF 0.391; R-1 0.615 vs 0.540; R-2 0.500 vs 0.453). But per-domain it is NOT always best: DWFG loses F1 on CNN (0.341 vs PR 0.354), on Mashable (0.330 vs DocLead 0.415), and R-1 on CNN (0.389 vs PR 0.433), R-2 on CNN (0.228 vs PR 0.389) and BBC (0.417 vs SVM 0.500).
- **Tweet summarization (Table 4): DWFG does NOT win.** "DWFG performs comparably to the simpler CRF-based methods for tweet summarization." Pooled F1: DWFG 0.516 vs LC-CRF 0.516 (tie) and LR+ 0.529 (higher). Pooled R-1: DWFG 0.702 vs LC-CRF 0.700 / LR+ 0.700. Pooled R-2: DWFG 0.645 vs LR+ 0.666. The paper's explanation: "the ground truth data are manually annotated from the perspective of readers' interests and focuses... the identification of important sentences from the Web document domain rarely influences the results for identifying important tweets."
- Significance: "the performances are statistically significantly improved on the MTV and ESPN domains... p values are much smaller than 0.01."

**Feature-weight findings (Section 4.2.3, Figures 7–8):**
- Sentence level: "most of the local factors have positive contributions to our task except for Feature 4 (the number of common words to the title). On average, it seems that **Feature 5 (sentence length) and Feature 2 (sentence position in paragraph)** are the most important local factors for identifying the important sentences." (Y-axis weight values range roughly −0.1 to 0.5.)
- Tweet level: "the two most important local factors for identifying the representative tweets are **Feature 8 (tweet length) and Feature 7 (average TF-IDF)**. In fact, we find that long tweets tend to cover both the main ideas of the Web documents and the personal comments towards them."

**Case study (Section 4.2.4, Figure 9):** article "Women try to take body on plane at Liverpool airport" (`http://news.bbc.co.uk/2/hi/8604663.stm`). Frequent salient words in documents: "women", "dead person", "body", "Liverpool Airport"; in tweets: "Liverpool airport", "Weekend At Bernie's". Beliefs shown range ~0.39–0.76; "the related sentence (the fourth sentence) in the document then receives a higher belief (**0.51**)" because two tweets form a retweet pair.

## Implementation complexity

**HIGH.**

Why:
- **Data acquisition is the dominant cost.** Reproducing the *stated* dataset requires crawling ~4.87M Twitter users by traversing following edges, monitoring 404,544,462 tweets over a 6.5-month window (Jan 1 2010 – Jul 17 2010), implementing a shortened-URL resolver (tinyurl/bit.ly), and de-duplicating documents by unique news ID. Twitter's 2010-era API access no longer exists; the paper gives no dump, so this data cannot be re-collected as described. Any student reproduction must substitute an existing dataset (e.g. a news-comment corpus).
- **Gold labels require crowd annotation.** The benchmark is 1,145 MTurk HITs with ≥2 workers per HIT across 4,926 documents and 201,098 tweets. Even a scaled-down version (say 100 documents) needs careful annotation instructions and agreement checks; no annotation guidelines, no inter-annotator agreement, and no label files are released in the paper.
- **Model implementation is real but bounded.** DWFG requires (a) coding three factor types, (b) a Gaussian-prior regularized max-likelihood objective, (c) L-BFGS over a graph-structured likelihood, which in turn needs (d) a loopy sum-product/max-sum message-passing routine with correct log-domain messages (Eqs. 5–9) — "Calculating the marginal distribution for each factor (in deriving the log-gradient of the objective function) requires a loopy sum-product inference algorithm." The paper does not state the number of iterations I, the σ of the Gaussian prior, or convergence criteria, so the training loop must be re-derived.
- **Multi-domain evaluation protocol.** 10-fold CV × 5 domains × 2 tasks × 3 metrics × 9 baselines; needs Dragon Toolkit ROUGE and per-domain models.
- Not "very high" because the features are 11 simple statistical features (no embeddings, no deep learning), the model has only |C|+2 free weights per domain, and the extractive output selection is trivial once beliefs are computed. A competent student can implement the core factor graph in a few days; the bottleneck is data + labels, not the algorithm.

## Reproducibility obstacles (concrete)

1. **The released data is unreachable.** The paper's only release pointer is `http://arnetminer.org/socialcontext/`. Fetching it now returns **HTTP 403 "access to this content has been restricted by country restriction"**; there is no alternate mirror, DOI, or repository named. Whether the original archive ever contained the 4,926 documents, the tweet IDs, and the MTurk labels is unverifiable from the paper, which says only "data description and software".
2. **Raw Twitter data cannot be re-collected.** The crawl spans Jan 1 2010 – Jul 17 2010 from a follower graph seeded at @jack. The 2010 Twitter API endpoints, rate limits, and even much of the historical tweet content are gone. The 404,544,462-tweet corpus is not reconstructible.
3. **No tweet IDs / document URLs are listed** (only one example BBC article, ID 8604663, appears as a case study), so the corpus cannot be rebuilt from a public dump.
4. **Labels are not distributed** and the annotation protocol omits the crucial details: no inter-annotator agreement (kappa), no adjudication rule for worker disagreement (only "at least two different workers"), no per-document number of sentences/tweets labeled, and no summary length distribution — even though the evaluation sets the extractor's output length equal to the human summary length, so length is a hidden confound.
5. **Hyperparameter and training details missing:** the value of I (message-passing iterations), σ in the Gaussian prior, L-BFGS convergence tolerance, similarity function details (cosine is given only as "e.g., cosine similarity"), and how TF-IDF / "log likelihood generated by the document/tweet thread" are estimated (no smoothing, no reference corpus stated).
6. **Two thresholds interact with the graph size and are dataset-sensitive:** the reported optimum for θ_h (0.5–0.6) contradicts the default used in the main tables (θ_h = 0.8), so the headline numbers are not at the tuned optimum — a reimplementation that tunes θ_h may not match Table 3/4.
7. **Baseline definitions are under-specified:** the tree-structured CRF (TS-CRF) is described but has no reported results; PR's "three types of relationships" PageRank is not detailed; LC-CRF is only defined by reference to [28].
8. **Tool dependence:** jTokeniser (`code.google.com/p/jtokeniser/`) and the Dragon Toolkit ROUGE (`dragon.ischool.drexel.edu`) are legacy/possibly-dead Google Code and Drexel URLs; ROUGE-1/ROUGE-2 values will shift with a different ROUGE implementation, and "stop words filtered out" gives no stoplist.
9. **Domain skew:** Mashable contributes 2,940 of 4,926 documents (≈60%) and 114,441 of 201,098 tweets (≈57%), so the pooled "All" numbers are dominated by one domain; reproducing "All" requires matching that imbalance.
10. **Statistical testing is partial:** sign tests are mentioned only for MTV and ESPN ("p values are much smaller than 0.01"); no test is reported for the pooled comparison that carries the abstract's headline claim.

## Minimum viable reproduction plan (2–4 weeks, student scope)

**Goal:** reimplement DWFG and reproduce the *direction and rough magnitude* of the pooled Web-document gains (DWFG > LC-CRF/SVM/LR/DocLead) on a substitute dataset; treat the exact Table 3/4 numbers as unreachable.

**Week 1 — Data + labels (substitute).**
- Abandon the Twitter crawl. Substitute a **news + reader-comment** corpus that already has URL-keyed comments, e.g. a news-comment dataset or a Twitter news-URL subset (e.g. a public tweet-URL collection filtered to news domains). Keep the paper's structure: document sentences + comment/tweet thread + author metadata (follower count, PageRank on the reply/retweet graph).
- Scale down: **~100–200 documents across 3 domains** (e.g. CNN/BBC-style news + one tech blog to mirror the CNN/BBC/Mashable mix), aiming for ~3,000–10,000 tweets.
- Build the 11 features exactly as Table 2, with the nominal encoding for Feature 1 (4/3/2/1/0 for title/subtitle/first paragraph/last paragraph/other) and per-feature mean normalization.
- Annotate gold summaries: 2 annotators per document (author + one peer, or a small MTurk/Prolific batch), ≥10 sentences and ≥5 tweets per item, following the paper's two instructions verbatim. Compute Cohen's kappa and report it; adjudicate disagreements by intersection (a sentence is gold only if both annotators chose it) as the substitute for the paper's unstated rule. Fixed budget: ~40–60 HITs is enough for a course-scale claim.

**Week 2 — Baselines first, then DWFG.**
- Implement the baselines in the paper's own order so the comparison is meaningful: **Random, DocLead, ParaLead, PR** (PageRank over the 3-relation graph), **SVM, LR** (11 local features), **LC-CRF** (sentence chain; use `sklearn-crfsuite`), and **SVM+/LR+** (22 augmented features summing over similar sentences/tweets).
- Implement DWFG: local factor `exp(λ_c x_{i,c} y_i)`; sentence-pair factor penalizing `y_i ≠ 1 or y_j ≠ 1` for consecutive pairs with cosine > θ_g; tweet-pair factor `exp(µ_c)` if `y_i ≤ y_j` for reply/retweet pairs; inter-domain factor `exp(ν)` if `y_i = y_j` for sentence–tweet pairs with cosine > θ_h.
- Start with the paper's defaults **θ_g = 0.1, θ_h = 0.8**, then sweep θ_g and θ_h over 0.0–1.0 in 0.1 steps and report the curves (expect θ_g ≈ 0.7 local max and θ_h ≈ 0.5–0.6 global max, per Section 4.2.2).
- Practical training substitution: full max-likelihood over the graph with L-BFGS is the paper's method, but a far cheaper and usually sufficient substitute is **piecewise training / pseudo-likelihood** — train SVM or LR for the λ's, then grid-search µ_c and ν on a validation fold using the loopy message-passing inference. Document this substitution explicitly. Use `scipy.optimize.fmin_l_bfgs_b` only if the piecewise version underperforms.
- Inference: implement Eqs. 5–9 in the log domain with I = 20–50 iterations and a convergence check on max belief change (the paper leaves I unstated).

**Week 3 — Evaluate + tune.**
- 10-fold CV, per domain and pooled, matching the paper's protocol: **extract exactly as many sentences/tweets as the gold summary** (rank by belief `p(y_i=1|X)`), report **F1, ROUGE-1, ROUGE-2** (ROUGE with stopwords removed; use `rouge` or `sumeval`, not the dead Dragon Toolkit — expect absolute ROUGE values to differ from the paper).
- Run a sign test for DWFG vs the strongest baseline on each domain; the paper's claim is significance on the two smallest domains (MTV/ESPN), so with 3 domains expect significance only where documents are fewest.
- Report per-feature λ weights and compare the ranking to the paper: **Feature 5 (sentence length) and Feature 2 (sentence position in paragraph) should be the top sentence features, Feature 4 (common words to title) should be near zero or negative; Feature 8 (tweet length) and Feature 7 (average TF-IDF) should top the tweet features.** This is a cheap, strong sanity check on the reimplementation.

**Week 4 — Write-up + honest deltas.**
- Report what matched and what did not. Expected outcome: **DWFG ≥ LC-CRF on F1/ROUGE-1/ROUGE-2 for the pooled Web-document task, and DWFG ≈ LC-CRF/LR+ (no clear win) on the tweet task** — exactly the paper's own pattern (Table 3 vs Table 4).

**Expected numbers (realistic, substitute data, course scale):**
- Web-document pooled F1: aim for **DWFG ≈ 0.40–0.46** with LC-CRF ≈ 0.35–0.39 (paper: 0.456 vs 0.391). Pooled ROUGE-1 ≈ 0.50–0.60 (paper: 0.615) and ROUGE-2 ≈ 0.40–0.50 (paper: 0.500) — ROUGE is the metric most sensitive to implementation choice, so treat those as ±0.05 bands.
- Tweet pooled F1: **DWFG ≈ LC-CRF ≈ 0.50** (paper: 0.516 vs 0.516), ROUGE-1 ≈ 0.65–0.70, ROUGE-2 ≈ 0.60–0.65. **Do not expect DWFG to win here** — the paper does not claim it does.
- The "+5.0%–17.3%" and "+10.8%" headline deltas are relative to weak baselines on a corpus dominated by Mashable (60% of documents); on a balanced small substitute set, expect smaller gains (a few points) and be explicit that the original data are unavailable.

**Hard constraints to state in the write-up:** the original corpus, tweet IDs, gold labels, and any "software" at `http://arnetminer.org/socialcontext/` are not obtainable in this environment (HTTP 403 country restriction), so this is a **method reproduction, not a result reproduction**.

## Verdict

This is a **Twitter-based** (not Weibo, not product-review) paper: it summarizes *English news Web documents* by treating the tweets that link to them as social context, and it also extracts a tweet-side summary, using a supervised dual-wing factor graph (DWFG) that couples 11 simple local features with sentence-pair, tweet-reply/retweet-pair, and sentence–tweet similarity factors, trained by L-BFGS with a Gaussian prior and decoded by loopy max-sum message passing (θ_g = 0.1, θ_h = 0.8, 10-fold CV). The idea is clean, the method is fully specified at the equation level, and the reported pooled gains on the Web-document task (F1 0.456 vs 0.391 for LC-CRF; ROUGE-1 0.615 vs 0.540; ROUGE-2 0.500 vs 0.453, with significance claimed at p ≪ 0.01 on MTV and ESPN) are meaningful — but the paper is honest that DWFG does **not** beat the simpler CRF/LR+ baselines on the tweet task (pooled F1 0.516, tied with LC-CRF and below LR+'s 0.529), and it never reports inter-annotator agreement, the number of inference iterations, or the prior's σ. The decisive reproducibility problem is data, not algorithm: the corpus is a 2010 crawl of 4,874,389 users and 404,544,462 tweets reduced to 200,000 URLs / 12,964,166 tweets and finally to five news domains (4,926 documents, 201,098 tweets, 1,145 MTurk HITs from 158 annotators), and the single release pointer — `http://arnetminer.org/socialcontext/`, offering only "data description and software" — is currently blocked (HTTP 403, country restriction). A 2–4 week student project can therefore reproduce the *model* faithfully and the *qualitative* result (DWFG ≥ LC-CRF on documents, ≈ on tweets, with Feature 5/2 and Feature 8/7 as the dominant weights) on a substitute news-comment or news-URL dataset, but it should not promise the exact Table 3/4 numbers.
