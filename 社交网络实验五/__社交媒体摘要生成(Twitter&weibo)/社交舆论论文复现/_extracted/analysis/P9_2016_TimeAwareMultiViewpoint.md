# Time-aware Multi-Viewpoint Summarization of Multilingual Social Text Streams

## Bibliographic info (authors, venue, year)

- **Authors:** Zhaochun Ren (University of Amsterdam, `z.ren@uva.nl`), Oana Inel (VU University Amsterdam, `oana.inel@vu.nl`), Lora Aroyo (VU University Amsterdam, `lora.aroyo@vu.nl`), Maarten de Rijke (University of Amsterdam, `derijke@uva.nl`).
- **Venue / year:** CIKM'16 — Proceedings of the 2016 ACM Conference on Information and Knowledge Management, October 24–28, 2016, Indianapolis, IN, USA, **pp. 387–396**. ACM ISBN 978-1-4503-4073-1/16/10.
- **DOI:** `10.1145/2983323.2983710` (the file is the UvA-DARE repository copy, download date 26 2019).
- **Keywords (verbatim):** "Multi-viewpoint summarization; Dynamic viewpoint modeling; Topic modeling; Multilingual social text streams".
- **Acknowledgment (relevant to data):** "We thank Kai Wu, Wei Zhang, Hongya Song and Shanshan Huang at Shandong University for collecting the dataset for us." Funding: Ahold, Amsterdam Data Science, Blendle, Bloomberg Research Grant, COMMIT, Elsevier, FP7 grant 312827 (VOX-Pol), ESF ELIAS, KNAW Elite Network Shifts, Microsoft Research Ph.D. program, Netherlands eScience Center 027.012.105, NWO projects, Yahoo Faculty Research, Yandex.

## Task (what is summarized, input -> output, extractive vs abstractive)

- **Definition given by the authors:** "The task we address is time-aware multi-viewpoint summarization of multilingual social text streams: we extract a set of informative social text documents to highlight the generation, propagation and drift process of viewpoints in a given social text stream."
- **Core concept — viewpoint:** "A viewpoint is a triple consisting of an entity, a topic related to this entity and sentiment towards this topic." Formally "a viewpoint to be a finite mixture over the sentiment, entity and topic, i.e., a tuple v = ⟨z, l, e⟩." Because viewpoints drift, "for each viewpoint at time t, we represent it as a tuple v = ⟨z, l, e, t⟩." Example in the intro: entity "Japan" within topic "#Whale hunting" with negative sentiment.
- **Input:** a multilingual social text stream D with T time periods, split into two languages, D_t = D_t^(A) ∪ D_t^(B) — in practice English tweets and Chinese weibos about the same topic. Each document is short, and "we assume that in each document d ∈ D_t only one viewpoint v_d exists."
- **Output:** a sequence of summaries S = {S_1, S_2, …, S_T}, one per time period, each a **set of selected documents** ("select a set of relevant documents as S_1 as a summary of viewpoints V_1"). At t = 1 the target is relevant documents; for 1 < t ≤ T "the target is to select a set of both relevant and novel documents, to summarize both the content of viewpoints V_t at time period t and the difference between V_t and viewpoints V_{t−1}."
- **Extractive vs abstractive:** purely **extractive** — documents (tweets/weibos) are ranked and selected, never rewritten. The only "generation" is a generated *summary set*, and the qualitative example output in Fig. 1 is shown as short quoted tweet snippets (e.g., "Brazil police, protesters clash as World Cup begins", "Netherlands beats Mexico in World Cup").
- **Four challenges named:** "(1) the ambiguity of entities in social text streams; (2) viewpoint drift, so that a viewpoint's statistical properties change over time; (3) multi-linguality, and (4) the shortness of social text streams." Conclusion repeats them as "ambiguous entities, viewpoint drift, multi-linguality, and the shortness of social text streams."
- **Four contributions claimed:** (1) proposing the task; (2) the VTTM model; (3) entity-based cross-language viewpoint alignment; (4) a Markov random walk summarization strategy. The paper states "As far as we know, no previous work has addressed time-aware multi-viewpoint summarization."

## Method (core algorithm in implementable detail: model, components, features, objective, hyperparameters with values)

Three phases (Fig. 2): **(A) dynamic viewpoint modeling → (B) cross-language viewpoint alignment → (C) multi-viewpoint summarization**.

### Notation (Table 1)
D = all documents; W = vocabulary; E = entity set; L = sentiments; Z = topics; V = viewpoints; K = |Z| = number of topics; E = number of entities; D_t = documents at t; N_d = words in document d; d_t = a document in D_t; v_d, e_d; w_i, z_i, l_i; π_t = distribution of viewpoints at t; θ_t = distribution of entities over viewpoints at t; μ_t = distribution of topics over viewpoints at t; φ_{v,z,l,t} = distribution of words over v, z and l at t; S_t = time-aware multi-viewpoint summary at t.

### Phase A — VTTM (viewpoint tweet topic model), §4.2
An "extension of dynamic topic models [6]" (Blei & Lafferty, DTM) — "a dynamic latent factor model, the viewpoint tweets topic model (VTTM), that jointly models viewpoints, topics, entities and sentiment labels in D_t at each time interval t."

- **Entity detection:** "Using a state-of-the-art entity linking method for social media [35]" (= Meij, Weerkamp & de Rijke, "Adding semantics to microblog posts", WSDM 2012), "for each document d at t, we discover entities by calculating the COMMONNESS value of the document."
- **Sentiment labels:** L = {positive, negative, neutral}; "we set l_i = −1 when word w_i is 'negative', whereas l_i = 1 when w_i is 'positive'."
- **Sentiment Markov chain:** "we assume that the sentiment label l_i for a word w_i depends on the sentiment label for its previous word w_{i−1} and the topic z_i simultaneously." A transition variable x ∈ X decides the source of l_i:
  - x_i = 1 → l_i identical to l_{i−1}; set "when w_i and w_{i−1} are connected by a correlative conjunction, such as 'and' and 'both'";
  - x_i = −1 → l_i opposite to l_{i−1}; set "when w_i and w_{i−1} are connected by an adversative conjunction, such as 'but' and 'whereas'";
  - x_i = 0 → "other kinds of conjunctions", and then "l_i ∼ Bern(ρ_{v_d,z_i})".
- **Generative process (Fig. 3, verbatim structure):**
  - For each topic z ∈ Z and sentiment l at time t: Draw φ_{z,l,t} ∼ Dir(φ_{z,l,t−1} · β_t).
  - For each viewpoint v ∈ V: Draw π_{v,t} ∼ Dir(α · π_{v,t−1}); Draw μ_{v,t} ∼ Dir(χ); θ_{v,t} ∼ Dir(δ); For each topic z, draw ρ_{v,z} ∼ Beta(η).
  - For each document d ∈ D_t: Draw viewpoint v_d ∼ Multi(π_t); Draw entity e_d ∼ Multi(θ_{v_d,t}); Draw σ ∼ Dir(τ); For each word w_i ∈ N_d, 0 < i < N_d: Draw topic z_i ∼ Multi(μ_{v_d,t}); Draw x_i ∼ Multi(σ); if x_i = 1, l_i ∼ l_{i−1}; if x_i = −1, l_i ∼ (−1)·l_{i−1}; if x_i = 0, l_i ∼ Bern(ρ_{v_d,z_i}); Draw word w_i ∼ Multi(φ_{z_i,l_i,t}).
  - Temporal dependency is thus carried by π_t (Dirichlet mixture over π_{t−1}) and φ_t (Dirichlet over φ_{t−1}·β_t), plus μ_t, θ_t (drawn from fixed χ, δ).
- **Inference:** "We apply a Gibbs sampling method [12]" to approximate p(v_d, z_d, l_d, x_d | W, Z, V, E, t). Two sampling steps:
  1. Document-level viewpoint (Eq. 1): P(v_d = v | V_{−d}, E, W, Z) ∝ [ (n^{−d}_{v,t} + α·π_{t−1}) / (n^{−d}_t + 1) ] · Π_{e∈E} [ (n^{−d}_{v,e,t} + δ) / (n^{−d}_{v,t} + Eδ) ] · Π_{z∈Z} [ (n^{−d}_{v,z,t} + χ_{z,t}) / (n^{−d}_{z,t} + Σ_{z∈Z} χ_{z,t}) ] · Π_{l∈L} Π_{w∈N_d} [ (n^{w}_{z,l,v,t} + β_t·φ^{t−1,w}) / (n^{−i}_{z,l,v,t} + Σ_{w∈N_t} β_t·φ^{t−1,w}) ].
  2. Word-level topic + sentiment + transition (Eq. 2), when x_i ≠ 0 and x_{i+1} ≠ 0: P(z_i = k, l_i = l, x_i = x | X_{−i}, L_{−i}, Z_{−i}, W, v_d) ∝ [ (n^{−i}_{v_d,k,t} + χ_{k,t}) / (n^{−i}_{v_d,t} + Σ_{z∈Z} χ_{z,t}) ] · [ (n^{w_i,−i}_{k,l,v_d,t} + β_t·φ^{k,l,v_d}_{t−1,w_i}) / (n^{−i}_{k,l,v_d,t} + Σ_{w∈N_d} β_t·φ^{k,l,v_d}_{t−1,w}) ] · [ (n^{w_i}_{−i,x} + τ_x) / (n^{−i}_x + Σ_{x∈X} τ_x) ] · [ (n^{w_{i+1}}_{−(i+1),x_{i+1}} + I(x_{i+1} = x_i) + τ_x) / (n^{−(i+1)} + 1 + Σ_{x∈X} τ_x) ]. When x_i = 0 the last factor is replaced by a posterior over η: (n^{−i}_{z,l,v,t} + η_l) / (n^{−i}_{v,z,t} + Σ_{l∈L} η_l).
  - After sampling, "we approximate the random variable φ_t … a viewpoint distribution π_t, a topic distribution μ_t over viewpoints, and entity distribution θ_t over viewpoints, similar to Iwata et al. [25]."
- **Hyperparameters given (§5.4, "Following existing topic models [20]" = Griffiths & Steyvers):** α_{u,t} = **50/V**; β_t = **0.5**; χ = δ = **0.5**; default number of viewpoints V = **20**. (η, τ, σ values are **not stated**.) T (number of time periods) and the time-bin granularity are **not stated** explicitly; the crowdsourcing novelty task uses days, and Table 5 shows dated viewpoints (2014-01-26, 2014-03-27, 2014-05-05, 2014-06-03), suggesting day-level bins.

### Phase B — cross-language viewpoint alignment (CLVA), §4.3
- Rationale: "Shortness and sparseness hinder statistical machine translation in social text streams. We consider entities, i.e., concepts that can be linked to a specific Wikipedia document, as a means to connect viewpoints by comparing the similarity between two linked Wikipedia documents."
- Split V into V_A, V_B by language; E into E_A, E_B. For v_A ∈ V_A take the entity e_i ∈ E_A with highest θ_{v,e_i,t} = P(e_i | v, t); same for v_B.
- Eq. 3: `sim_t(v_A, v_B | t) = sim(e_i, e_j) · θ_{v_A,e_i,t} · θ_{v_B,e_j,t}`.
- Eq. 4: `sim(e_i, e_j) = |φ̃_{W_{e_i}} · φ̃_{W̃_{e_j}}| / (|φ̃_{W_{e_i}}| · |φ̃_{W_{e_j}}|)` — cosine over **LDA topic vectors** ("We use LDA [7] to represent each Wikipedia document W as a K-dimension topic vector φ̃_W"); the non-English entity's Wikipedia doc is first translated to English "using links to English Wikipedia documents" (described as "a state-of-the-art SMT approach" in Fig. 2).
- Aggregate: `sim(v_A, v_B) = Σ_t sim_t(v_A, v_B)`; for each v_A ∈ V_A pick the v_B with the highest sim → viewpoint pair set V_s.
- Deduplicate/rank pairs with a random-walk ranking: transition probability between pairs Eq. 5 `tr((v_A,v_B),(v_A',v_B')) = |sim(v_A,v_B)·sim(v_A',v_B')| / (|sim(v_A,v_B)|·|sim(v_A',v_B')|)`; initial score 1/|V_s|; Eq. 6 `sa(i)^{(c)} = μ·Σ_{i≠j} (tr(i,j)/Σ_{j'∈V_s} tr(i,j'))·sa(j)^{(c−1)} + (1−μ)/|V_s|` with **decay μ = 0.85**. Iterate "until it convergences". Take top |V_C| pairs and merge each pair into one viewpoint. V_C = viewpoints shared by V_A and V_B; V_L = (V_A ∪ V_B) \ V_C.

### Phase C — time-aware multi-viewpoint summarization (TaMVS), §4.4
Co-ranking update summarization inspired by Wan [44], with **novelty** and **coverage**.
- Three transmission matrices: M^A between candidate documents d_i, d_j ∈ D_t (Eq. 7: `M^A_{i,j} = [Σ_{e,e'} sim(e,e') · Σ_{z∈Z}Σ_{l∈L} φ^{z,l,v}_{d_i,t}·φ^{z,l,v}_{d_j,t}] / (‖Φ_{v_{d_i},t}‖·‖Φ_{v_{d_j},t}‖)`, where φ^{z,l,v}_{d,t} is the average of φ^{z,l,v}_{t,w} over all w ∈ d); M^B among previous summaries {S_s}; M^AB between D_t and {S_s}. All row-normalized to M̂ (stochastic matrix).
- Divergence matrix W^AB (Eq. 8): `W^{AB}_{i,j} = |t − s| · |π_{v,t} − π_{v,s}| · ‖Φ_{v_{d_i},t} − Φ_{v_{d_j},t}‖ / (‖Φ_{v_{d_i},t}‖·‖Φ_{v_{d_j},t}‖)`, row-normalized to Ŵ^AB.
- Viewpoint-biased relevance κ_{d,v} = [κ_{d_i,v}] = ‖Φ_{v_{d_i},t}‖, normalized to κ̂.
- Co-ranking iterations (Eq. 9, 10): `nov(d_i)^{(c)} = ε1 Σ_{j∈D_t, i≠j} M̂^A_{i,j}·nov(d_j)^{(c−1)} + ε2 Σ_{j∈{S_s}} Ŵ^AB_{i,j}·nov(d_j)^{(c−1)} + ((1−ε1−ε2)/(D+S))·κ_{d_i,v}`; `cov(d_i)^{(c)} = γ1 Σ M̂^A_{i,j}·cov(d_j)^{(c−1)} + γ2 Σ M̂^AB_{i,j}·cov(d_j)^{(c−1)} + ((1−γ1−γ2)/(D+S))·κ_{d_i,v}`. Initialization: nov(d_i) = cov(d_i) = 1/D_t. After each iteration both are normalized.
- Eq. 11: `sco(d_i)^{(c)} = nov(d_i)^{(c)} + cov(d_i)^{(c)}` → per-viewpoint ranking list R_v for each v ∈ V_C ∪ V_L.
- **Algorithm 1** (greedy, redundancy-aware): input V_C, V_L, {R_v}, {S_s}_{s=1}^{t−1}, D_t, π_t, θ_t, φ_t and all previous distributions; Ω ← null, T ← predefined threshold, L ← summary length; while |Ω| < L: for each v, take top document d_i from R_v, remove it from R_v, and if `max_{d_j ∈ Ω} sim(d_i, d_j | v, t) < T` then add d_i to Ω; stop when |Ω| = L. Output S_t.
- **Hyperparameters (§5.4):** ε1 = ε2 = **0.4** (Eq. 9); γ1 = γ2 = **0.4** (Eq. 10); co-ranking convergence threshold = **0.0001**; summary length L = **200 words per time period**. The redundancy threshold T in Algorithm 1 and the |V_C| cutoff are **not stated** as numeric values.

## Datasets (names, sizes, language, domain, HOW OBTAINED - crawled by authors? public? URL given?)

- **How obtained:** "we collect a dataset of microblogs in two languages. We define multilingual queries about 6 well-known topics in 2014 and crawl English and Chinese microblogs via the Twitter streaming API [https://dev.twitter.com/docs/streaming-apis] and a Sina Weibo crawler [http://www.weibo.com], respectively." Crawled by the authors (collected by collaborators at Shandong University per the acknowledgment). "The tweets and weibos are posted between January, 2014 and August, 2014."
- **No dataset name is given** (no "TAMVS-2014" or similar), and no download link appears anywhere in the paper.
- **Table 2** ("Each item is divided into two parts: the number of documents annotated, and the number of documents for each topic"):

| Topic | # English tweets (annotated / total) | # Chinese weibos (annotated / total) |
|---|---|---|
| 1. The World Economic Forum | 2,000 / 2,000 | 1,978 / 1,978 |
| 2. Whaling hunting | 566 / 566 | 1,072 / 1,072 |
| 3. FIFA Worldcup 2014 | 1,120 / 1,963 | 1,801 / 1,801 |
| 4. Missing MH370 | 3,124 / 6,308 | 4,725 / 4,725 |
| 5. Anti-Chinese in Vietnam 2014 | 825 / 2,001 | 1,095 / 1,095 |
| 6. Sinking of the MV Sewol | 403 / 2,000 | 1,400 / 1,881 |

- **Stated totals:** "In total, 8,308 English tweets and 12,071 Chinese weibos were annotated." (Note: the English annotated column sums to **8,038**, not 8,308 — an internal inconsistency of 270 documents; the Chinese column sums correctly to **12,071**.)
- **Languages:** English (Twitter) and Chinese (Sina Weibo) — "we suppose there are two different languages used in D."
- **Domain:** microblog posts about 6 2014 news/event topics (economics forum, whaling, FIFA World Cup, MH370, anti-Chinese protests in Vietnam, MV Sewol ferry sinking). Summary length 200 words per time period.
- **Annotation:** crowdsourced on the **CrowdTruth platform [24]** with CrowdTruth metrics [5], workers labelling "in their native language (i.e., Chinese or English)". Three tasks: **Topic annotation** (relevant tweets per topic + relevant topic mentions, with relevance scores), **Sentiment annotation** (sentiment + intensity high/medium/low for each topic mention and overall), **Novelty ranking** (pair-wise comparison: tweets of a day sorted chronologically, "every tweet of a particular day is compared to all the following tweets, resulting in n(n−1)/2 comparison pairs per day"; the crowd indicates which tweet is more salient → "per day, a ranked list of salient tweets").
- **Table 3 (crowdsourcing results):**

| Task | Topic | Sentiment | Novelty ranking |
|---|---|---|---|
| Units | 6,225 | 5,317 | 5,211 |
| Jobs | 92 | 77 | 82 |
| #Total workers | 6,337 | 6,555 | 5,336 |
| #Unique workers | 557 | 500 | 341 |
| #Spam workers | 1,085 | 1,334 | 1,284 |
| #Total judgments | 43,575 | 53,170 | 78,165 |
| #Spam judgments | 7,562 | 10,519 | 14,475 |
| Total cost | $1,136 | $1,328 | $1,444 |

- Annotation quality control: "Only the quality annotations were used as ground truth basis for further experiments. We validate the results by performing manual evaluation of the annotations." Pool of workers scored 0 (quality) / 1 (low quality); precision, recall, accuracy and F1 computed against CrowdTruth metrics — "Overall, we obtain high scores for each of the measures (above 0.85) and across tasks."
- External resources required: **Wikipedia** (entity linking targets + per-entity LDA topic vectors + cross-language Wikipedia links), **Twitter streaming API** (now restricted/paid), **Sina Weibo crawler**, **CrowdTruth platform**, an **SMT system** for entity translation, and the entity linker of Meij et al. [35].

## Data/code availability stated in the paper (quote any URL, 'available at', 'we will release', download link; if none, say NONE)

**NONE.** The paper contains **no** statement that the dataset is available, no "available at", no "we will release", no download link, and no code/implementation release. The only URLs in the entire paper are:

- `https://dev.twitter.com/docs/streaming-apis` (footnote 1, the Twitter streaming API used for crawling) — dead/restricted today.
- `http://www.weibo.com` (footnote 2, "Chinese microblogging platform").
- `https://doi.org/10.1145/2983323.2983710` and `http://dx.doi.org/10.1145/2983323.2983710` (the paper's own DOI).
- `https://uba.uva.nl/en/contact` and `http://dare.uva.nl` (UvA-DARE repository boilerplate, not data).

The dataset is described only as crawled by the authors; the crowdsourced ground truth was paid for on CrowdTruth ($1,136 + $1,328 + $1,444 = **$3,908** total). The paper's only mention of the data's provenance is the acknowledgment to Shandong University colleagues "for collecting the dataset for us."

## Evaluation (metrics, human evaluation required? protocol, folds)

- **Research questions:** (RQ1) VTTM performance in time-aware viewpoint modeling / drift detection; (RQ2) cross-language viewpoint alignment (CLVA) performance; (RQ3) end-to-end TaMVS performance vs baselines, plus effect of only novelty or only coverage.
- **Phase A metrics:** "we adapt the **purity** and **accuracy** evaluation metrics, which are widely used in topic modeling and clustering experiments [37, 40]."
- **Summarization metrics:** "We adopt the **ROUGE** evaluation metrics: **ROUGE-1** (unigram), **ROUGE-2** (bigram) and **ROUGE-W** (weighted longest common sequence)." Compared against ground-truth summaries derived from the crowdsourced annotations.
- **Significance testing:** "two-tailed paired t-test", strong significance α = 0.01 (marked N / H), weak significance α = 0.05 (marked M / O).
- **Human evaluation: YES, and it is mandatory** — the ground truth *is* human (crowdsourced) data: topic relevance, sentiment/intensity, and per-day novelty rankings, validated by manual assessment with "high scores … (above 0.85)". The paper also names manual/online user evaluation as missing future work: "an extrinsic online user evaluation would give deeper insights into the performance of our approach."
- **Folds:** not stated — no cross-validation or train/test split is described; the models are unsupervised and evaluation is per topic over the full annotated set. No held-out split is mentioned.

## Baselines (list them)

**Our methods (Table 4):**
- **VTTM** — dynamic viewpoint modeling in phase A (§4.2).
- **VTTM-S** — stationary viewpoint modeling in phase A.
- **CLVA** — LDA-based cross-language viewpoint alignment in phase B.
- **CLVA-T** — "the alignment method that applies term frequency in viewpoint similarity calculation".
- **CLVA-E** — "the alignment method that only checks the consistency of entities".
- **TaMVS** — full pipeline (A+B+C); **TaMVS-V** — TaMVS without phase B; **TaMVSN** — TaMVS with only novelty; **TaMVSC** — TaMVS with only coverage.

**External baselines:**
- Topic models: **Sen-TM** (sentiment LDA based contrastive summarization, Li et al. [28], COLING 2010); **TAM** (topic-aspect model based contrastive summarization, Paul & Girju [36], AAAI 2010). "We use the Topic-aspect model [36, TAM] and the Sentiment-topic model [28, Sen-TM] as baselines for topic models."
- Summarization: **CoRUS** (co-ranking update summarization, Wan [44], COLING 2012) — "generates an update summary using a co-ranking strategy, but without VTTM"; **IUS** (incremental update summarization, McCreadie et al. [33], CIKM 2014); **LexRank** (Erkan & Radev [13]) — "ranks sentences via a Markov random walk strategy".
- The paper notes: "No previous work has addressed the same task as we do in this paper."

## Reported results (key numbers, so a reproducer knows the target)

**Example VTTM viewpoints (Table 5):** entity `Search_for_Malaysia_Airlines_Flight_370` / topic `#Missing MH370` / pos 0.077, neu 0.422, neg 0.501 / 2014-03-27; `Whaling_in_Japan` / `#Whaling hunting` / 0.015, 0.317, 0.668 / 2014-05-05; `China-Japan_relations` / `#The World Economic Forum` / 0.110, 0.166, 0.724 / 2014-01-26 and `#Anti-Chinese in Vietnam` / 0.017, 0.621, 0.362 / 2014-06-03 (illustrating drift).

**Table 6 — viewpoint modeling (purity / accuracy):**

| Topic | EN VTTM pur/acc | EN TAM | EN Sen-LDA | ZH VTTM | ZH TAM | ZH Sen-LDA |
|---|---|---|---|---|---|---|
| The World Economic Forum | 0.497 / 0.516 | 0.401 / 0.415 | 0.419 / 0.425 | 0.441 / 0.472 | 0.352 / 0.371 | 0.391 / 0.407 |
| Whaling hunting | 0.454 / 0.463 | 0.432 / 0.435 | 0.451 / 0.462 | 0.493 / 0.505 | 0.442 / 0.458 | 0.501 / 0.513 |
| FIFA Worldcup 2014 | 0.472 / 0.423 | 0.432 / 0.442 | 0.445 / 0.451 | 0.541 / 0.561 | 0.432 / 0.442 | 0.483 / 0.497 |
| Missing MH370 | 0.463 / 0.471 | 0.391 / 0.403 | 0.427 / 0.445 | 0.501 / 0.542 | 0.343 / 0.352 | 0.451 / 0.462 |
| Anti-Chinese in Vietnam | 0.491 / 0.511 | 0.406 / 0.415 | 0.452 / 0.557 | 0.522 / 0.541 | 0.482 / 0.495 | 0.503 / 0.517 |
| Sinking of the MV Sewol | 0.425 / 0.438 | 0.361 / 0.372 | 0.407 / 0.411 | 0.625 / 0.642 | 0.497 / 0.507 | 0.559 / 0.572 |
| **Overall** | **0.474 / 0.482** | 0.384 / 0.397 | 0.417 / 0.428 | **0.524 / 0.543** | 0.437 / 0.452 | 0.482 / 0.504 |

Claimed gains: "VTTM achieves an increase in purity over TAM of up to 23.4%, while accuracy increases by up to 21.4%. Compared with Sen-LDA, VTTM offers an increase of up to 12.0%, whereas accuracy increases by up to 12.6%." Error analysis: "for 67.2% of those documents the sentiment labeling results are incorrect, whereas for 75.4% of those documents the topic prediction results are incorrect."

**Table 7 — VTTM vs VTTM-S (caption says "Chinese viewpoint modeling task", but the numbers are identical to the English VTTM column of Table 6):** VTTM pur/acc overall 0.474 / 0.482 vs VTTM-S 0.461 / 0.474; per topic e.g. Sinking of the MV Sewol 0.425/0.438 vs 0.422/0.435; Missing MH370 0.463/0.471 vs 0.433/0.448. Conclusion: "VTTM responds better to topic drift than VTTM-S, which neglects the dependency of viewpoints between two adjacent intervals."

**Table 8 — cross-language alignment accuracy:** CLVA overall **0.711** vs CLVA-T **0.669** vs CLVA-E **0.615**. Per topic CLVA: WEF 0.754, Whaling 0.737, FIFA 0.643, MH370 0.727, Anti-Chinese 0.787, Sewol 0.854. "CLVA outperforms the other two methods, CLVA-T and CLVA-E, for each topic. CLVA-T outperforms CLVA-E."

**Table 9 — VTTM-based summarization (ROUGE-1 / ROUGE-2 / ROUGE-W):**

| Topic | TaMVS | TaMVS-V | TaMVSN | TaMVSC |
|---|---|---|---|---|
| The World Economic Forum | 0.383 / 0.082 / 0.184 | 0.316 / 0.055 / 0.131 | 0.369 / 0.057 / 0.136 | 0.351 / 0.052 / 0.145 |
| Whaling hunting | 0.294 / 0.047 / 0.152 | 0.197 / 0.037 / 0.092 | 0.221 / 0.032 / 0.138 | 0.221 / 0.032 / 0.138 |
| FIFA Worldcup 2014 | 0.436 / 0.094 / 0.202 | 0.351 / 0.068 / 0.142 | 0.404 / 0.083 / 0.194 | 0.404 / 0.083 / 0.194 |
| Missing MH370 | 0.425 / 0.087 / 0.232 | 0.324 / 0.074 / 0.132 | 0.402 / 0.082 / 0.170 | 0.394 / 0.079 / 0.162 |
| Anti-Chinese in Vietnam | 0.409 / 0.065 / 0.169 | 0.226 / 0.046 / 0.127 | 0.403 / 0.047 / 0.139 | 0.395 / 0.042 / 0.129 |
| Sinking of the MV Sewol | 0.373 / 0.064 / 0.171 | 0.314 / 0.051 / 0.131 | 0.362 / 0.055 / 0.134 | 0.341 / 0.046 / 0.133 |
| **Overall** | **0.387 / 0.085 / 0.188** | 0.318 / 0.061 / 0.132 | 0.377 / 0.062 / 0.139 | 0.359 / 0.056 / 0.150 |

**Table 10 — TaMVS vs external baselines (ROUGE-1 / ROUGE-2):** TaMVS overall 0.387 / 0.085; TAM 0.297 / 0.047; Sen-TM 0.302 / 0.052; LexRank 0.309 / 0.052; IUS 0.345 / 0.062; CoRUS 0.375 / 0.079. Per topic TaMVS R-1: 0.383, 0.294, 0.436, 0.425, 0.409, 0.373. Claimed: "TaMVS achieves 3.2% and 7.5% increases over CoRUS in terms of ROUGE-1 and ROUGE-2, respectively, and 12.1% and 37.1% increases over IUS … Compared to Sen-TM, TaMVS achieves a statistical significant improvement of up to 28.1% in terms of ROUGE-1 and 63.4% in terms of ROUGE-2." Also: "novelty is the most important part of our multi-viewpoint summarization process" (TaMVS > TaMVSN > TaMVSC).

**Number of viewpoints (Fig. 5):** "for both metrics and methods, the performance peaks when the number of viewpoints equals **40**, i.e., higher than our default value of 20."

**Fig. 4:** common viewpoints |V_C| per topic — Weibo and Twitter users share more viewpoints on "#Missing MH370" and "#FIFA Worldcup 2014" than on other topics.

## Implementation complexity (low/medium/high/very high + WHY)

**VERY HIGH.**

- **Two coupled custom inference procedures.** VTTM is a dynamic latent factor model with a Markov sentiment chain; the paper gives only the conditional equations (Eq. 1–2), and the sampling/update recipes for φ_t, π_t, μ_t, θ_t are deferred to "similar to Iwata et al. [25]". A reproducer must re-derive the dynamic Dirichlet update (`Dir(φ_{t−1}·β_t)`, `Dir(α·π_{t−1})`) and the auxiliary counts (`n^{w}_{z,l,v,t}`, `χ_{z,t}`, `φ^{t−1,w}`) correctly — several symbols (η, τ, σ, x-priors, initial counts) are never assigned values.
- **A whole NLP toolchain is assumed as plug-in:** a social-media entity linker with a COMMONNESS score ([35] Meij et al., WSDM 2012 — the SEM7/"Semanticizer" style system), Wikipedia-to-Wikipedia cross-language links, an SMT system for entity translation, LDA over Wikipedia articles, POS/conjunction detection to set x_i ∈ {1, −1, 0} for English *and* Chinese, plus a Chinese sentiment lexicon. Each is its own project.
- **Co-ranking summarization with three matrices** (M^A, M^B, M^AB) plus a divergence matrix W^AB, three normalization steps, two coupled iterative updates (Eq. 9–10), and a greedy redundancy-filtering loop with an unspecified threshold T and unspecified |V_C| cutoff.
- **Data cost and access:** 20k+ annotated microblogs, 175k crowdsourced judgments, ~$3.9k of crowdsourcing, Twitter streaming API access from 2014, and a Sina Weibo crawler — none released.
- **Missing numbers:** η, τ, σ, T (Algorithm 1 threshold), |V_C|, the number of time periods T, the time-bin size, the number of LDA topics for Wikipedia vectors, Gibbs iteration/burn-in counts, and the convergence criterion are all unstated.

## Reproducibility obstacles (concrete)

1. **No data release, no code release.** The paper gives no dataset URL, no repository, and no "available at"/"we will release" statement (see the availability section). The 8,308 annotated English tweets + 12,071 Chinese weibos exist only as an internal UvA/Shandong artifact; the ground truth was crowd-generated and paid for.
2. **Twitter API data is effectively unrecoverable.** The tweets were crawled Jan–Aug 2014 via `https://dev.twitter.com/docs/streaming-apis` (dead endpoint). Reconstructing the same 2014 tweet sets is impossible now (deleted accounts, API pricing/tier limits, no tweet IDs published).
3. **Sina Weibo crawler not published**, and Weibo data is subject to Chinese platform restrictions; the 12,071 Chinese weibos cannot be re-crawled historically.
4. **Crowdsourced labels cannot be reproduced.** The Novelty task requires `n(n−1)/2` pairwise comparisons per day per topic (78,165 judgments, 341–557 unique workers, $1,444 for that task alone). CrowdTruth's spam-filtering metrics (precision/recall/accuracy/F1 > 0.85) and the worker-quality pooling step are also needed to rebuild the ground truth.
5. **Ground-truth construction is under-specified:** how topic relevance scores and per-day novelty rankings were converted into reference summaries for ROUGE (and with what tokenization for Chinese) is not described.
6. **Tool dependency risk:** the entity linker of Meij et al. [35] is a 2012 research system; the SMT-based entity translation and Wikipedia cross-language links depend on a Wikipedia dump snapshot that is not pinned.
7. **Unspecified hyperparameters** (listed above: η, τ, σ, T, |V_C|, T periods, time-bin size, Wikipedia LDA topic count, Gibbs iterations) make exact numerical replication impossible even with data.
8. **Chinese/Arabic-style resource dependence:** Chinese word segmentation, a Chinese sentiment lexicon, and Chinese conjunction detection for the Markov sentiment chain are all required but no resources are named.
9. **Language/eval friction:** ROUGE-1/2/W on Chinese requires segmentation choices that can shift scores by several points — the paper does not state its segmentation.
10. **Internal inconsistencies to resolve during reproduction:** Table 2's annotated English column sums to 8,038 vs the stated 8,308; Table 6 shows VTTM *below* TAM on FIFA English accuracy (0.423 vs 0.442) despite the claim "VTTM outperforms TAM for all topics"; Table 7's caption says Chinese while its values equal Table 6's English VTTM column; Table 9 shows TaMVSN = TaMVSC on two topics (identical 0.221/0.032/0.138 and 0.404/0.083/0.194).

## Minimum viable reproduction plan (what a student could realistically build in 2-4 weeks, what to substitute, what numbers to expect)

**Realistic scope: re-implement the pipeline on a modern, obtainable dataset and report the same metric families, not the same numbers.**

Week 1 — data substitution:
- Replace the private 2014 crawl with a public event/topic microblog set. Best options: **CrisisNLP / CrisisLex** event collections (Twitter IDs, multilingual), **Event2012/Event2018** (with English + Chinese variants of some events), or a fresh crawl of one 2024–2025 event with `snscrape`-alternatives / an academic Twitter dump plus Weibo posts via an open dataset. Pick **one topic** (not six) with ≥2,000 English and ≥1,000 Chinese posts spanning ≥8 time bins (day or week).
- Substitute the entity linker with **spaCy NER + a Wikipedia/Wikidata entity-linking library** (e.g., `wikidata`/`REL`/`BLINK`) or a modern LLM-based linker; use Wikidata cross-language sitelinks as the "translate to English Wikipedia" step (this replaces the SMT component entirely — a legitimate simplification since the paper's own Eq. 4 only needs a shared English Wikipedia vector).

Week 2 — VTTM re-implementation (the core deliverable):
- Implement VTTM as a Gibbs sampler with document-level viewpoint, entity, topic, sentiment, and transition variables, following Eq. 1–2 and Fig. 3. Reuse an existing **DTM / TopicTrackingModel** implementation as scaffolding.
- Practical simplifications to declare explicitly: drop the x_i conjunction transition variable (set x_i = 0 always, falling back to `l_i ∼ Bern(ρ_{v,z})`) and use a standard sentiment lexicon (VADER for English, a Chinese lexicon such as HowNet/`snownlp` for Chinese) to pre-assign l_i; use weekly rather than daily bins; set V = 20 and also sweep 10/20/30/40 to reproduce the Fig. 5 peak-at-40 shape.
- Hyperparameters to use: α = 50/V, β = 0.5, χ = δ = 0.5, plus pick and *report* η = τ = 0.5 and 1,000 Gibbs iterations with 200 burn-in (values the paper leaves unstated).
- Evaluate phase A with purity and accuracy against a small hand-labeled set of ~150–300 posts per language, or against the event's official category labels if available.

Week 3 — CLVA + TaMVS:
- Implement Eq. 3–6: entity-based viewpoint similarity using LDA (or any topic model) vectors over English Wikipedia articles, random-walk ranking with μ = 0.85.
- Implement phase C: the three matrices M^A/M^B/M^AB, divergence W^AB (Eq. 8), co-ranking iterations (Eq. 9–11) with ε = γ = 0.4 and threshold 0.0001, then Algorithm 1 with L = 200 words and a redundancy threshold T that must be chosen and reported (e.g., cosine < 0.7).
- Baselines to implement: **LexRank** (off-the-shelf), **IUS**-style incremental novelty selection, **CoRUS**-style co-ranking without VTTM, and TaMVS-V/TaMVSN/TaMVSC ablations. TAM and Sen-TM are harder; a simpler stationary-LDA + sentiment baseline (the paper's VTTM-S idea) is an acceptable stand-in.

Week 4 — evaluation and write-up:
- Ground truth: build a small human/LLM-assisted reference summary per time bin (e.g., pick the 10 most salient posts by 3 annotators or a strong LLM judge, report inter-annotator agreement) and compute ROUGE-1/2/W with `rouge-score` (segment Chinese with `jieba` and report that choice).
- Report the *relative ordering* the paper establishes: TaMVS > TaMVS-V (alignment helps), TaMVS > TaMVSN > TaMVSC (novelty matters more than coverage), CLVA > CLVA-T > CLVA-E, VTTM > VTTM-S. Those four qualitative claims are the reproducible scientific content.

**Numbers to expect:** absolute ROUGE will not match. The paper's targets are ROUGE-1 ≈ **0.387** / ROUGE-2 ≈ **0.085** overall for TaMVS with a *large* human-annotated reference; with a small hand-built reference on a different event, expect ROUGE-1 in the 0.20–0.45 band and ROUGE-2 in the 0.03–0.10 band, and alignment/purity/accuracy in the 0.4–0.6 range for viewpoint modeling (paper: purity 0.474 EN / 0.524 ZH, accuracy 0.482 / 0.543; CLVA accuracy 0.711). Aim to reproduce the *gaps* (TaMVS − TaMVS-V ≈ +0.07 ROUGE-1; TaMVS − CoRUS ≈ +0.01 to +0.03 ROUGE-1), not the absolute values.

## Verdict (one paragraph: how good a reproduction target is this paper, and for whom)

This is a **high-risk, high-effort reproduction target** and a poor fit for a 2–4 week course project *if* the goal is to match published numbers: the dataset is private (8,308 English tweets + 12,071 Chinese weibos crawled in 2014 via a now-dead Twitter streaming API and an unpublished Weibo crawler), the ground truth cost ~$3,908 of crowdsourcing on CrowdTruth with 175k pairwise judgments, and the paper states **no** data or code availability of any kind. The method itself is also only partially specified — VTTM's dynamic Dirichlet updates are deferred to "similar to Iwata et al. [25]", and η, τ, σ, the Algorithm-1 redundancy threshold, |V_C|, the number of time periods, the time-bin size and Gibbs iteration counts are all unstated — while the pipeline additionally presupposes a 2012 research entity linker, Wikipedia cross-language links, an SMT system, and English/Chinese conjunction and sentiment resources. It is nevertheless an **attractive target for a strong, methodologically minded student** (or a 2-person team) who is willing to treat it as a *re-implementation and ablation study* rather than a numerical replication: the four-phase design (dynamic viewpoint topic model → cross-language entity alignment → co-ranking update summarization → greedy redundancy-filtered selection) is fully described at the equation level, the four headline claims (alignment helps, novelty beats coverage, CLVA beats term/entity-only similarity, dynamic beats stationary viewpoint modeling) are directly testable with public event data, and the writing-up value of reproducing a *multilingual* Twitter+Weibo summarizer is high. Students who want a quick, data-available reproduction should look elsewhere in this collection; students who want a substantial topic-modeling implementation project with a clear ablation story should take this one, budget for data substitution, and state up front that absolute ROUGE targets are unreachable.
