# Time Aware Knowledge Extraction for Microblog Summarization on Twitter

## Bibliographic info (authors, venue, year)

- **Authors:** Carmen De Maio, Giuseppe Fenza, Vincenzo Loia (corresponding author, loia@unisa.it), Mimmo Parente — "Deparment of Computer Science, University of Salerno, Fisciano (SA), Italy". Emails given: cdemaio@unisa.it, gfenza@unisa.it, loia@unisa.it, parente@unisa.it.
- **Year:** 2015. The PDF header reads `arXiv:1501.06715v1 [cs.IR] 27 Jan 2015`, and the running footer reads "Preprint submitted to Journal of LATEX Templates — January 28, 2015".
- **Venue:** **not stated** in the text. The only venue string is the un-substituted LaTeX template placeholder ("Journal of LATEX Templates"). This is an arXiv preprint (arXiv:1501.06715v1, cs.IR, 27 Jan 2015).
- **Keywords (as given):** "Microblog Summarization, Time Awareness, Fuzzy Formal Concept Analysis, Wikification".
- **Note on naming:** the method is abbreviated **TAKE** throughout; the paper compares itself against work referred to as **[4]** = F. C. T. Chua, S. Asur, "Automatic summarization of events from social media", ICWSM 2013.

## Task (what is summarized, input -> output, extractive vs abstractive)

**Task: topic-based extractive microblog (Twitter) summarization with a user-controlled level of detail ("shrinking").**

The problem is stated formally as: "Given a topic-focused timestamped tweet stream and a level of shrinking `s`, the task is aimed to filter and chronologically order tweets in order to produce a Microblog Summary `MS_s` that provides a complete description of the story covering main concepts describing topic development over the timeline." The framework "is able to retrieve more or less detailed summary according to the user's demand in terms of the closure level of shrinking."

- **Input:** (i) a topic-focused, timestamped tweet stream (offline: the whole stream for one event), and (ii) a user-specified shrinking level `s ∈ [0,1]`.
- **Output:** `MS_s` = a set of **whole, unmodified tweets** selected from the stream, ordered chronologically starting from the most recent ones. Listing 2 declares: `Input: timed fuzzy lattice L, peak areas P, and shrinking level s` / `Output: a microblog summary MS_s of T tweets`.
- **Extractive, not abstractive.** The algorithm only ever does `MS_s = MS_s ∪ t_max` (Listing 2, line 16), i.e. it copies an existing tweet into the summary; no sentence fusion or generation is performed. The only text processing is *annotation* (wikification) of tweets for internal representation.
- **Online/offline split stated by the authors:** "Microblog Content Analysis and Time Aware Knowledge Extraction will be periodically performed offline also because they are time consuming activities. Instead, Microblog Summarization Algorithm is performed at execution time according to the user request in terms of topic and level of shrinking."

## Method (core algorithm in implementable detail)

The framework is a 3-phase pipeline (Figure 2: "Overall Process of the framework").

### Phase 1 — Microblog Content Analysis (Section 5)

Three steps: Peak Detection, Content Wikification, Inverse Tweet Frequency. Goal: "map the domain data (e.g., tweets content) into a fuzzy formal context, enabling FFCA execution."

**1a. Peak Detection (Section 5.1)** — uses the **Offline Peak-Finding Algorithm (OPAD)** from TwitInfo [9] (Listing 1), "based on the idea of TCP congestion control, which uses a weighted moving mean and variance to determine if there is a new peak area".
- Binning: "we group tweets that are posted within the same **1440 minute (i.e., 1 day)** time window" → counts `C = (C1, C2, ..., Ct)`.
- Trigger condition (line 6): `|Ci − mean| / meandev > τ` **and** `Ci > Ci−1`, with **τ = 2** ("we use τ = 2").
- Initialization (lines 2–3): `mean = C1`, `meandev = variance(C1, ..., Cp)`.
- Update function (lines 30–34): `diff = |oldmean − updatevalue|`; `newmeandev = α*diff + (1−α)*oldmeandev`; `newmean = α*updatevalue + (1−α)*oldmean`, with **α = 0.125 "as in [9]"**.
- Output: peak windows `(start, end)`; each tweet is annotated as `tweet_i = {⟨peak_i⟩}`.
- The algorithm itself is given in full as pseudo-code (Listing 1, 34 lines), so it is directly re-implementable.

**1b. Content Wikification (Section 5.2)** — "the tweet content is wikified to extract a set of `⟨topic, relevance⟩` pairs corresponding to Wikipedia articles that are related to the tweet content itself with a specific relevance degree [7]" (i.e. the Wikify! approach of Mihalcea & Csomai, 2007). Worked example: for the tweet *"President Obama just designated the largest marine reserve in the world"*, "the extracted topic (shown in Figure 3) are: `⟨Barack Obama, 0.678⟩`, `⟨President of the United States, 0.456⟩`".
Resulting annotation: `tweet_i = {⟨peak_i⟩} ∪ {⟨topic_i1, relevance_i1⟩, ..., ⟨topic_im, relevance_im⟩}` where "m is the number of topics detected by sentence wikification of the tweet_i".

**1c. Inverse Tweet Frequency (Section 5.3)** — refines relevance:
- `itf(w_i, T) = log( N / |{t_j ∈ T : w_i ∈ t_j}| )` where `N` = "total number of tweets analyzed" and the denominator = "number of tweet from which the topic w_i has been extracted".
- Final relevance: **`f_rel(w_i, t_j) = relevance(w_i, t_j) × itf(w_i, T)`**.
- Annotation becomes `tweet_i = {⟨peak_i⟩} ∪ {topic_j, f_rel_j, topic_j+1, f_rel_j+1, ..., ⟨topic_m, f_rel_m⟩}`.

### Phase 2 — TAKE / Time Aware Knowledge Extraction (Section 6)

Extends **Fuzzy Formal Concept Analysis (FFCA)** with time. Theoretical background definitions (Section 3):
- **Def. 1 Fuzzy Formal Context:** `K = (G, M, I = φ(G × M))`, membership `µ(g,m) ∈ [0,1]`.
- **Def. 3 Fuzzy Formal Concept:** with confidence threshold `T`: `A* = {m ∈ M | ∀g ∈ A : µ(g,m) ≥ T}`, `B* = {g ∈ G | ∀m ∈ B : µ(g,m) ≥ T}`; a concept is `(A_f = φ(A), B)` with `A* = B`, `B* = A`. Object membership `µ_g = min_{m∈B} µ(g,m)`; "if `B = {}` then `µ_g = 1` for every g". `A` and `B` are the **extent** and **intent**.
- **Def. 4 subconcept order:** `(φ(A1),B1) ≤ (φ(A2),B2)` iff `φ(A1) ⊆ φ(A2)` (⇔ `B2 ⊆ B1`).
- **Def. 5 Fuzzy Concept Lattice:** `F(K)` = all fuzzy concepts of K with the partial order `≤` at threshold `T`.
- **Def. 6 Fuzzy Formal Concept Similarity:** `E(K1,K2) = |φ(A1) ∩ φ(A2)| / |φ(A1) ∪ φ(A2)|`, with fuzzy intersection/union taken as min/max (t-norm/t-conorm), per footnote 1: `µ_{A∩B}(x) = min(µ_A(x), µ_B(x))`, `µ_{A∪B}(x) = max(µ_A(x), µ_B(x))`.
- **Def. 7 Time Aware Fuzzy Formal Context:** `K_t = (G, M ∪ T, I_M = φ(G × M), I_T)`, "where `T` is the set of time attributes and `I_T` is a **binary** time relation `I_T ⊆ G × T`". "if `g ∈ G` and `t ∈ T` are in relation `I_T` means that g happens at time `t ∈ T`."

Mapping: "a straight mapping defines a correspondence between the set of attributes `M` and linguistic terms extracted from tweets content, as well as the set `G` of objects and the tweets collection." The output structure is a **timed fuzzy lattice** in which "each node (i.e., a formal concept) includes the objects, attributes and time attributes", e.g. `(A_f = tweet1, tweet2, B = "word1, time000")` with `µ_tweet1 = 0.61`, `µ_tweet2 = 0.94`. **Temporal edges** ("in Figure 4 red dashed arrows") are added among related concepts to represent evolution, with a temporal precedence relation over time points; example chain: `c2 → c8 → c11`, i.e. `{Obama} → {Obama, election} → {Obama, President}`.

Worked illustration of the underlying fuzzy context (Figure 1): the example cross-table uses **confidence threshold T = 0.6** ("all the relationship with membership values less than 0.6 are not shown"), and concept `C4 = (A_f = tweet1, tweet5, B = "word1, word002, ...")` with `µ_tweet1 = 0.61`, `µ_tweet5 = 0.64`; `c5` is a subconcept of `c2` and `c3`.

### Phase 3 — Microblog Summarization Algorithm (Section 7, Listing 2)

Core quantities:
- **Level of shrinking of a concept:** `s(C) = 1 − support(C) = 1 − |A|/|G|`, where `|A|` = number of tweets in C and `|G|` = number of tweets in the overall stream.
- **Weight of a concept:** `w(c) = ( Σ_{m∈B} µ_m ) / |B|` where `|B|` = number of attributes in C and `µ_m = max_{g∈φ(A)} µ(g,m)`.
- In Listing 2 line 14 the argmax is over **uncovered** attributes: `c_max = argmax_{c_i ∈ (C*_{p_i} \ CC)} ( Σ_{m ∈ (B \ C_A)} µ_m ) / |B|` (numerator restricted to `B \ C_A`, denominator still `|B|`).

Algorithm (Listing 2, verbatim structure):
1. `C_A = Ø`, `C_C = Ø`, `MS_s = Ø`.
2. `C* = {c_i ∈ L | s(c_i) = 1 − support(c_i) > s}` — keep concepts whose shrinking exceeds the input threshold `s`.
3. `P = (p_1, p_2, ..., p_n)` with `∀i,j : p_i > p_j ⇔ i < j` — **peak areas sorted descending, i.e. most recent peak first**.
4. `C*_{p_i} = {c_i ∈ C* | c_i = (A,B), p_i ∈ B}` — group candidate concepts by peak area.
5. `for i = 1; i < len(P); i++ do` / `while C*_{p_i} \ C_C ≠ Ø do`:
   - `c_max` = argmax weight (over uncovered attributes),
   - `t_max = argmax_{g ∈ c_max} (µ_g)` — "the best tweet with highest degree of membership belonging to c_max",
   - `MS_s = MS_s ∪ t_max`, `C_A = C_A ∪ {m | µ_m ∈ c_max}`, `C_C = C_C ∪ c_max`.
6. **Output** the tweets in the summary, ordered chronologically.

Worked example in the paper (s = 70%, Figure 5 and Table 7.1):
- Candidate concepts by peak: `peak 1: c1, c2, c3`; `peak 2: c2, c3, c4, c5`; `peak 3: c5, c6`.
- Weights: `w(c1) = 0.89; w(c2) = 0.74; w(c3) = 0.94` → first selected concept `c3 = {tweet 1, tweet 2, tweet 11, tweet 4, tweet 6}` with `w = 0.94`, covered attributes "Obama, Party".
- Best tweet = `tweet 1` with membership `0.97`; after removing covered attributes the weight of `c1` and `c2` drops to 0, so peak1 is exhausted; the algorithm moves to peak2.
- Final: `MS_s = {tweet 1, tweet 7}`.

### Hyperparameters with values actually given
| Parameter | Value | Source |
|---|---|---|
| Peak bin size | 1440 minutes (1 day) | §5.1 |
| OPAD τ | 2 | §5.1 |
| OPAD α (update) | 0.125 | §5.1 / Listing 1 |
| FFCA confidence threshold `T` | **0.6 only in the illustrative example (Figure 1)**; the value used in the experiments is **not stated** | §3, Figure 1 |
| Shrinking level `s` | varied over `[0−1]`; specific reporting points 0.6, 0.7–0.9, ~0.9 | §8.3 |
| Number of topics per tweet `m` | not stated (data-dependent) | — |
| Wikification relevance threshold | not stated | — |
| Temporal-edge construction rule | described qualitatively only ("temporal precedence relation … over time points"), no formal rule or threshold given | §6 |

## Datasets (names, sizes, language, domain, HOW OBTAINED)

Section 8.1 "Tweet Streams": "The summarization framework has been applied on tweet streams focused on four real-world events: Facebook IPO, Obamacare, Japan Earthquake and BP Oil Spill."

**Table 8.1: Number of tweets for each dataset**

| Name | # Tweets |
|---|---|
| Facebook IPO | 9.570 |
| Obamacare | 136.761 |
| Japan Earthquake | 251.802 |
| BP Oil Spill | 79.676 |

- "The number of tweets for these events ranges from 9.570 tweets for Facebook IPO to 251.802 tweets for the Japan Earthquake." (Decimal commas = 9,570 / 136,761 / 251,802 / 79,676.)
- **Language:** English (all examples and Wikipedia gold summaries are English). Not explicitly stated but unambiguous from the example tweet and the English Wikipedia references.
- **Domain:** real-world news events — a tech/IPO event (Facebook IPO), US politics/health policy (Obamacare), a natural disaster (2011 Tōhoku Japan Earthquake), and an environmental disaster (BP/Deepwater Horizon Oil Spill).
- **How obtained — this is the critical point:** footnote 2 to the dataset section states **"Specifically, the data have been provided by authors of [4]"**, i.e. the tweet streams were *privately provided* by Chua & Asur (ICWSM 2013), **not crawled by the present authors and not downloaded from a public URL**. The Acknowledgement repeats: "The authors are indebted to the authors of [4] for the provisioning of tweet streams and gold summary in order to enable the comparison evaluation of the proposed framework."
- The four URLs in footnotes 3–6 are **Wikipedia articles about the events**, not data downloads:
  - Facebook IPO → `http://en.wikipedia.org/wiki/Initial_public_offering_of_Facebook`
  - Obamacare → `http://en.wikipedia.org/wiki/Patient_Protection_and_Affordable_Care_Act`
  - Japan Earthquake → `http://en.wikipedia.org/wiki/2011_T%C5%8Dhoku_earthquake_and_tsunami`
  - BP Oil Spill → `http://en.wikipedia.org/wiki/Deepwater_Horizon_oil_spill`
- **Gold summaries:** also from [4] — "gold summaries have been provided by authors of [4]. They are extracted considering the references of the relevant news articles cited in Wikipedia article corresponding to the topic/event of the tweet stream. For each of the Wikipedia references for the selected events, we extract the headline text which gives a one line summary of the corresponding news article." So the gold standard is a set of **news headlines** harvested from the Wikipedia articles' reference lists. This is not a human-written summary set and there is no human annotation of the tweet streams.

## Data/code availability stated in the paper

**NONE.**

- No data URL, no "available at", no "we will release", no GitHub/repository link appears anywhere in the paper.
- The only availability statement is the negative one quoted above: data and gold summaries "have been provided by authors of [4]" (private transfer), and the Acknowledgement thanks those authors "for the provisioning of tweet streams and gold summary".
- The only external links in the paper are: the four Wikipedia article URLs (background, not data), `tweetchup.com` and `twitalyzer.com` (commercial analytics services, mentioned in the Introduction as examples), `www.nist.gov/tac` (TAC, in Related Works), and reference URLs/DOIs.
- No code, no lattice implementation, no wikification configuration, no parameter files are released or promised.

## Evaluation (metrics, human evaluation required? protocol, folds)

Three metric families; **no human evaluation, no annotator study, no inter-annotator agreement, no train/test folds** (the method is unsupervised; the evaluation is a comparison of generated summaries against Wikipedia-derived gold summaries over the whole stream). "Since TAKE produces different summaries with different level of shrinking, the results have been evaluated by varying the level of `s` in `[0 − 1]`."

1. **Novelty Measurements** — two variants:
   - *Sequence Novelty Measurement* (from [6], Gao et al.): "measures average novelty among chronologically adjacent tweets included in the resulting summary", Eq. (1): `Novelty = 1/(|D|−1) * Σ_{i>1} ( I_{d_i} − I_{d_i, d_{i−1}} )`, where `|D|` = number of tweets in the generated summary, `I_{d_i}` = number of concepts in `d_i`, `I_{d_i,d_{i−1}}` = cardinality of the intersection of `d_i` and `d_{i−1}`.
   - *Historical Novelty Measurement* — "defined in this work": Eq. (2): `Novelty = 1/(|D|−1) * Σ_{i>1} [ I_{d_i} − | (∪_{k<i} I_{d_k}) ∩ I_{d_i} | ]`; `|D|` = number of new tweets added in the summary, `I_{d_k}` with `k = 1...|D|` = all tweets in the summary.
2. **Text-based Coverage of Wikipedia** (from [4], where "is called Quantitative Comparison with Wikipedia") — n-gram overlap between generated and gold summaries, excluding stop-words: Eq. (3) `g_n = (1/|NG^gold_n|) * Σ_{ng ∈ NG^gold_n} min(ng ∈ NG^gold_n, |ng ∈ NG^gen_n|)` — "each n-gram is limited to the minimum number of counts between the gold summary and the generated summary"; Eq. (4) `Sim(S_gold, S_gen) = 0,2·g_1 + 0,3·g_2 + 0,5·g_3` ("higher importance to 3-grams and lower importance to 1-grams"). Only 1-, 2- and 3-grams.
3. **Concept-based Coverage of Wikipedia** — "defined in this work": both gold and generated summary sentences are **wikified**, giving `C_gold = {c_1,...,c_m}` and `C_gen = {c'_1,...,c'_n}`; Eq. (5) `P = |C_gold ∩ C'_gen| / |C'_gen|`, `R = |C_gold ∩ C'_gen| / |C_gold|`; Eq. (6) `F = 2 × P×R/(P+R)`.

Reporting protocol: results are presented **only as plots** (Figures 6–10) grouped by tweet stream with a different colour per approach; for novelty, "TAKE has been evaluated by varying level of shrinking s in [0−1] and plotting the obtained minimum and maximum values for both novelty measures". Text-based Coverage is plotted as "the minimum value produced by TAKE … obtained setting the level of shrinking to 0.6"; Figure 10 plots Precision/Recall/F-measure curves "varying the level of shrinking in [0−1]" with x-axis 0.0–1.0.

## Baselines (list them)

"the framework has been validated comparing the obtained results with other existing methodologies, that are **LDA (Latent Dirichlet Allocation), GDTM (Gaussian Decay Topic Model), and DTM (Decay Topic Model)**" — all three are the methods of **[4] (Chua & Asur, ICWSM 2013)**, re-used rather than re-implemented by the present authors. "The selected tweet streams and measures have been used to evaluate both the proposed approach (i.e., referred as TAKE) and methods defined in [4]." The paper adds that "As highlighted in [4], these methodologies outperform the LDA baseline by exploiting temporal correlation between tweets and their semantics at two different stages."

Related work *discussed* but not used as numeric baselines: TweetMotif [13], Sharifi et al. [5][14][17], Liu et al. [15][18], Chakrabarti & Punera [16], Sumblr [19], Visual Backchannel [20], TwitInfo [9], and the sequential summarization of Gao et al. [6].

## Reported results (key numbers, so a reproducer knows the target)

**Warning for a reproducer: the paper contains no numeric results table.** All quantitative outcomes are in Figures 6–10, whose values are not printed in the text. The only numbers in the results section are the qualitative/verbal claims and the illustrative lattice example. The claims made are:

- **Sequence Novelty (Figure 6):** "the proposed approach produces summaries with maximum values of novelty highest than other approaches for each tweet stream" (i.e. TAKE's max > LDA/GDTM/DTM max on all four streams). "TAKE produces summaries with minimum values of novelty lower than other approaches only for the tweet stream of BP Oil Spill" (i.e. on the other three streams TAKE's minimum is at least as good).
- **Historical Novelty (Figure 7):** "TAKE produces summaries with maximum values of novelty highest than other approaches for each tweet stream. Minimum values … produced by TAKE are enough close to the results obtained with other approaches, and so they are acceptable results."
- **Text-based Coverage of Wikipedia (Figure 8):** "the minimum value produced by TAKE that is higher than the values produced by other approaches has been plotted. Specifically, it has been obtained setting the level of shrinking to **0.6**. For levels of shrinking greater than **0.6**, TAKE significantly outperforms other approaches."
- **Concept-based Coverage of Wikipedia (Figure 9):** "TAKE outperforms other techniques in terms of Concept-based Coverage of Wikipedia."
- **Precision/Recall/F-measure (Figure 10):** "TAKE reveals valuable performance in terms of Recall with acceptable values of Precision with level of shrinking between **0.7 and 0.9**." The Abstract states: "evaluating Concept-based Coverage of Wikipedia setting level of shrinking with values **∼ 0.9** (that is a verbose summary), the algorithm outperforms the results shown in [4] in terms of **F-Measure, with optimal Recall and comparable values of Precision**."
- **Illustrative (not experimental) numbers** from Section 7: `w(c1)=0.89, w(c2)=0.74, w(c3)=0.94`; best tweet membership `0.97`; `MS_s = {tweet 1, tweet 7}` at `s = 70%`.
- Also from §3's toy example: `µ_tweet1 = 0.61`, `µ_tweet5 = 0.64`, `T = 0.6`; and `⟨Barack Obama, 0.678⟩`, `⟨President of the United States, 0.456⟩` from wikification.

The paper's own summary of the takeaway: TAKE "outperforms the compared approaches considering at the same time temporal correlation among tweets and semantic of their content … ensuring good trade off between quality, completeness and redundancy."

## Implementation complexity

**High** (arguably very high for a faithful reproduction; medium for a simplified one). Reasons:

1. **Fuzzy Formal Concept Analysis + temporal extension must be built from scratch.** There is no public reference implementation cited; the paper gives definitions and a worked lattice but no algorithm for constructing the timed lattice (only pseudo-code for the *summarizer*, Listing 2). Concept-lattice enumeration is combinatorial — with hundreds of thousands of tweets (251,802 for Japan Earthquake) and thousands of Wikipedia-concept attributes, the intent set `B` can be very large; the paper never discusses complexity, pruning, or scalability, yet claims the offline phase is "time consuming".
2. **The temporal-edge construction rule is under-specified.** "A temporal precedence relation is defined over time points" is all that is said; there is no formal definition of when a temporal edge exists between two concepts, nor a threshold. This is a core part of the claimed novelty and cannot be reproduced exactly.
3. **The confidence threshold `T` used in experiments is not stated** (0.6 appears only in an illustrative figure), and it strongly controls lattice size and the quality of every metric.
4. **Wikification is an external, non-trivial component** (Wikify! [7]) with an unspecified relevance threshold; modern substitutes exist but shift the numbers.
5. **Three-phase pipeline with two different time scales** (daily peak bins + concept lattice) and a per-tweet annotation format that must be exactly consistent between phases.
6. **Baselines cannot be run from the paper** — LDA/GDTM/DTM are in [4] (ICWSM 2013) with their own unpublished code.
7. Nothing in the reported results is a number, so there is no numeric target to fit; verification must be done by re-deriving plots.

The one favourable factor: **Listing 1 (OPAD) and Listing 2 (summarization) are complete pseudo-code**, and all FFCA definitions (Defs. 1–7) are stated precisely enough to code.

## Reproducibility obstacles

- **Private data — the biggest obstacle.** The four tweet streams were *given* to the authors by the authors of [4]; they are not public and no URL is provided. The paper's own Acknowledgement makes clear this was a personal data transfer. Without contacting Chua & Asur, the exact experimental setup cannot be recreated.
- **No tweet IDs, no hydration path.** Even if the streams were originally Twitter-API collections, the paper publishes no tweet IDs and no collection script; Twitter/X API access is now paid and the historical academic endpoints used in 2013 are gone.
- **Gold summaries are also private** ("gold summary" provided by [4]) and are themselves a derived artefact (news headlines harvested from Wikipedia reference lists) whose exact Wikipedia revision is unspecified — Wikipedia changes, so the gold set is not reproducible even in principle without the original snapshot.
- **Crowdsourced labels: not applicable** — the paper uses no human judgements, so there is no annotation to re-collect; but this also means there is no human-validated gold standard, only n-gram/concept overlap with headline text.
- **Wikification service dependency.** The pipeline depends on sentence wikification producing `⟨topic, relevance⟩` pairs; the original Wikify! demo/service is long defunct, and a modern entity linker will yield different topics and different relevance values (hence different `f_rel` and different lattices).
- **No code release, no URL, no "available at"** — nothing to download and reuse; the entire FCA/timed-lattice machinery must be re-implemented.
- **Unspecified hyperparameters** for the actual runs: the FFCA confidence threshold `T`, the temporal-edge rule/threshold, the wikification relevance cutoff, and the exact number of peak bins/`s` values plotted.
- **Results exist only as figures** — no table of Precision/Recall/F/Novelty numbers, so a reproducer cannot check against a target value, only against qualitative claims ("TAKE is higher").
- **Decimal-comma formula** in Eq. (4) (`0,2·g_1 + 0,3·g_2 + 0,5·g_3`) is a minor but real transcription trap.
- **Internal inconsistency to be aware of:** `s(C) = 1 − |A|/|G|` (higher `s(C)` = *fewer* tweets) is filtered by `s(c_i) > s`, yet §8 says "the higher the level of shrinking the more detailed the resulting summary will be, that is the summary will include a greater amount of tweets". This is only consistent if one reads `s` as the admission threshold on *small* concepts (raising the threshold admits more, smaller concepts → longer summary); a reproducer must fix this reading explicitly.
- **Scale.** 251,802 tweets (Japan Earthquake) through fuzzy concept enumeration is a substantial compute/memory problem on a laptop, with no guidance on pruning.
- **No Chinese/Arabic resources involved** — this paper is English/Twitter only; that is *not* an obstacle here, but it also means it cannot be reused directly for a Weibo-focused project without substitution.

## Minimum viable reproduction plan (2–4 weeks)

**Realistic goal:** reproduce the *pipeline and the qualitative trend*, not the exact numbers (there are none). Target deliverable: an end-to-end system that takes a topic-timestamped tweet set plus `s`, emits a chronologically ordered extractive summary, and plots the three metric curves against a naive baseline.

Week 1 — Data and Phase 1.
1. Substitute the private [4] streams with a *publicly available* tweet dataset that has timestamps and topic labels. Options to check first: the Chua & Asur ICWSM 2013 data page (contact the authors directly — this is exactly what the present paper did), or a public crisis/event tweet-ID collection (e.g. CrisisNLP/CrisisLex, Event2012) hydrated through whatever API access you have; if hydration fails, fall back to any timestamped text stream (e.g. a Weibo event dataset, or Reddit/news comments) and document the substitution honestly. Aim for 5k–20k messages per event, 2–4 events.
2. Implement OPAD exactly from Listing 1 with bin = 1440 min, τ = 2, α = 0.125. Sanity-check that detected peaks align with known event dates.
3. Replace Wikify! with a local entity linker: spaCy NER + Wikipedia lookup, or a lightweight mention→Wikipedia-title mapping, producing `⟨topic, relevance⟩` with relevance = a documented confidence (e.g. linker score or 1.0). Implement `itf` and `f_rel = relevance × itf` exactly as given.

Week 2 — Phase 2.
4. Implement fuzzy formal context + concept enumeration with a confidence threshold `T` (start at 0.6, then sweep 0.3–0.9 and report sensitivity — the paper leaves this open, so a sensitivity study is a genuine contribution of your repro).
5. Implement the timed extension: add time attributes as **binary** relations `I_T ⊆ G × T` (one per peak window), exactly as Def. 7 says. Use a simple, documented temporal-edge rule (e.g. an edge `c_a → c_b` when `c_b`'s intent is a superset of `c_a`'s and `peak(c_b) > peak(c_a)`) and state that the paper does not specify this.
6. Practical scaling: cap the number of attributes (top-K Wikipedia topics by document frequency) and enumerate concepts with a standard closed-itemset/NextClosure or Charm-style algorithm with `T`-thresholded incidence. Report the cap.

Week 3 — Phase 3 and evaluation.
7. Implement Listing 2 literally, including the `B \ C_A` numerator variant of `w`, the descending peak order (most recent first), and `t_max = argmax µ_g`.
8. Build gold summaries from the same recipe the paper describes: Wikipedia article → reference list → news headlines (record the Wikipedia revision IDs so the gold set is frozen and citable). This makes the evaluation self-contained without [4].
9. Implement all three metrics: Sequence Novelty (Eq. 1), Historical Novelty (Eq. 2), Text-based Coverage (Eqs. 3–4 with 0.2/0.3/0.5 on 1/2/3-grams), Concept-based Coverage (Eqs. 5–6, wikifying both sides with your linker).

Week 4 — Baselines, plots, write-up.
10. Baselines: reimplementing DTM/GDTM is out of scope; use (a) **LDA-based selection** (the baseline [4] itself beats — cheap with sklearn/gensim), (b) random/chronological and (c) top-TFIDF or centroid-cosine greedy selection as redundancy-aware references. Note in the write-up that DTM/GDTM are unavailable.
11. Reproduce the paper's figure style: sweep `s` over `[0,1]` in 0.05–0.1 steps, plot min/max novelty bars per event, plot Text-based Coverage, plot P/R/F curves for Concept-based Coverage (paper's Figure 10).

**What to expect numerically:** you should reproduce the *shape* of the paper's claims — recall rising with `s` (longer summaries) up to a plateau, precision slowly decaying, F-measure peaking in the `s ≈ 0.7–0.9` region, novelty of TAKE ≥ LDA/greedy at the max but not dramatically at the min, and Text-based Coverage at `s ≈ 0.6` already above the LDA baseline. Absolute values will differ from the paper's (unreported) figures because the data, the wikifier, `T` and the gold snapshot all differ; report your own numbers and the *relative* ordering rather than trying to match an invisible target. Budget the risk that concept enumeration is too slow at 250k tweets — plan on ~10k tweets/event and say so.

## Verdict

This is a **medium-to-poor reproduction target for a faithful numerical replication, but a good one for a pipeline-reproduction course project with a methods-focused write-up.** Its appeal is that the algorithmic core is unusually well specified for a paper of this kind — OPAD is given as 34 lines of complete pseudo-code with all constants (1440-minute bins, τ = 2, α = 0.125), the summarization algorithm is given as a 20-line listing with its worked example (`w(c3)=0.94`, `tweet 1` at `µ=0.97`, `MS_s = {tweet 1, tweet 7}`), and Fuzzy FCA / timed-FFCA are given as clean Definitions 1–7 with explicit formulas for `s(C)`, `w(c)` and the three evaluation metrics including the exact n-gram weights `0.2/0.3/0.5`. Against that, three things block exact replication: the tweet streams and gold summaries are **private**, supplied by the authors of [4] with no URL and no release promise ("the data have been provided by authors of [4]"); the experiments' confidence threshold `T` and the temporal-edge construction rule are **not stated**; and the results are published **only as figures** with no numeric table, so there is no target to hit. A student with solid Python and an interest in formal concept analysis — ideally one willing to email Chua & Asur for the data and to substitute a modern entity linker for the dead Wikify! service — can build a credible 3–4 week reproduction (smaller event streams, spaCy/linker wikification, 0.6 default `T` with a sensitivity sweep, LDA + greedy baselines) and honestly report trend-level agreement plus an ablation on the unspecified parameters. A student who needs a paper with released data, released code and printed numbers should pick a different paper.
