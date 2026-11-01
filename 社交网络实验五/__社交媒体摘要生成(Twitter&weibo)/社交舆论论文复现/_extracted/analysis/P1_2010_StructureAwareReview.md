# Structure-Aware Review Mining and Summarization

> **Scope warning (read first):** This paper is **NOT about Twitter or Weibo microblogs**. It is about **product/movie reviews** (long-form e-commerce and film reviews, sentence-level). There are no tweets, no hashtags, no retweets, no user timelines, no temporal streams, and no social-network structure anywhere in the paper. The only connection to the "social media summarization" theme of this workspace is that it performs **opinion/aspect-based summarization** of user-generated review text. Any use of this paper as a Twitter/Weibo baseline would be a category error; it must be repositioned as an **aspect-based opinion-mining / review-summarization** baseline.

## Bibliographic info

- **Title:** Structure-Aware Review Mining and Summarization
- **Authors:** Fangtao Li¹, Chao Han¹, Minlie Huang¹, Xiaoyan Zhu¹, Ying-Ju Xia², Shu Zhang², Hao Yu²
  - ¹ State Key Laboratory of Intelligent Technology and Systems; Tsinghua National Laboratory for Information Science and Technology; Department of Computer Science and Technology, Tsinghua University
  - ² Fujitsu Research and Development Center
  - Emails listed: `fangtao06@gmail.com`; `zxy_dcs@tsinghua.edu.cn`
- **Venue:** *Proceedings of the 23rd International Conference on Computational Linguistics (Coling 2010)*, pages **653–661**, Beijing, August 2010. (9 pages.)
- **Year:** 2010.
- **Type:** Full conference paper, supervised machine-learning (structured prediction) approach.
- **Funding stated:** "partly supported by Chinese NSF grant **No.60973104** and **No. 60803075**, a grand from **Fujitsu Research Center**, and a grant from the **International Development Research Center, Ottawa, Canada**."
- **Acknowledgements:** thanks "the anonymous reviewers, **Qiang Yang, Lei Zhang and Qiu Long**".

## Task

**Object-feature-based review summarization, decomposed into three subtasks** (Section 1):

1. Extract all the object features and opinions;
2. Determine the sentiment polarities for opinions;
3. For each object feature, determine the relevant opinions, i.e. **object feature–opinion pairs**.

The paper formulates **subtasks 1 and 2 jointly** as a *joint structure tagging problem*: for each sentence in a review, one model simultaneously tags object features, positive opinions, and negative opinions. Subtask 3 (pairing) is done **afterwards by a simple heuristic**, not learned: "we identify the **nearest opinion word/phrase** for each object feature as object feature-opinion pair, which is widely used in previous work (Hu and Liu, 2004; Jin and Ho, 2009)."

**Input → output:**
- Input: a review **sentence** (the unit of analysis is the sentence; "In our framework, we focus on sentence-level review extraction").
- Output: a **BIO tag sequence** over the words of that sentence; then, at the summary level, a list of structured feature–opinion pairs grouped by feature and polarity, with opinions "ranked by their frequencies" (Figure 1 example: movie *Gone With The Wind*, features `Movie`, `Actor`, `Music`, each with Positive and Negative opinion lists).

**Definitions given verbatim:**
- **Definition (Object Feature):** "is defined as whole target expression that the subjective expressions have been commented on. Object features can be products, services or their elements and properties, such as 'character', 'movie', 'director' for movie review, and 'battery', 'battery life', 'memory card' for product review."
- **Definition (Review Opinion):** "is defined as the whole subjective expression on object features. For example, in sentence 'The camera is easy to use', 'easy to use' is a review opinion."
- **Definition (Opinion Polarity):** "the sentiment category for review opinion. In this paper, we consider two types of polarities: positive opinion and negative opinion." (No neutral class as a *target*; neutral words fall under `O`.)

**Extractive / structural, not abstractive:** the "summary" is a structured list of extracted pairs (Figure 1), not generated prose. No text is rewritten or generated.

**What "structure-aware" means (important conceptual claim):** "'structure-aware' refers to the **output structure**, which model the relationship among output labels. This is significantly different from the previous **input structure** methods, which consider the linguistic structure as heuristic rules (Ding and Liu, 2007) or input features for classification (Wilson et al. 2009)." So conjunction/syntactic structure is encoded as **edges between output label variables**, not as input features.

## Method (implementable detail)

### Tag set (Table 1) — 8 tags

BIO encoding. Three expression types × Begin/Inside, plus negation and other:

| Tag | Meaning |
|---|---|
| `FB` | Feature Beginning |
| `FI` | Feature Inside |
| `PB` | Positive Beginning |
| `PI` | Positive Inside |
| `CB` | Negative Beginning |
| `CI` | Negative Inside |
| `N` | Negation Word |
| `O` | Other |

"the non-opinion and neutral opinion words are represented as 'O'. With Negation (N), which is only one word, such as 'not', 'don't', as an independent tag, there are totally **8 tags**."

Worked tagging example from the paper:
`The/O camera/FB comes/O with/O a/O pitiful/CB 32mb/FB compact/FI flash/FI card/FI ./O`

### Models (Figure 2) — a family of CRFs over the output structure

**Common CRF formulation (Section 3.2.5):** undirected graphical model `G` of the conditional distribution `P(Y|X)`; conditional probability written as a normalized product of **state functions on nodes** and **transition functions on edges**, with parameters estimated (Sutton and McCallum, 2006). Objective: **maximize log-likelihood** `L = Σ_{i=1}^{N} log P(y^(i) | x^(i))` over training data `D = {(x^(i), y^(i))}`.

**Inference / optimization:**
- Linear CRFs: **dynamic programming** for MAP of `Y` given `X`; **L-BFGS** to optimize the log-likelihood.
- "For more complicated graphs with cycles, we employ **Tree Re-Parameterization (TRP)** algorithm (Wainwright et al. 2001) for approximate inference" and "for complicated CRFs, TRP is used instead to calculate the marginal probability."
- Implementation note: TRP has **no published hyperparameters in this paper** (no iteration count, no convergence threshold, no damping) — **not stated**.

**(a) Linear-chain CRFs (3.2.1).** Each word is a node; adjacent nodes are connected by a **linear edge**. Motivated by examples: "if the previous word is a positive opinion, the next word is more likely a positive opinion"; "if the previous word is an adjective, and it is an opinion, the next noun word is more likely an object feature."

**(b) Skip-chain CRFs (3.2.2)** — encodes **conjunction structure**. Two edge types: **linear-edge** and **skip-edge**.
Construction procedure (implementable as stated):
1. "We first identify the conjunctions in the review sentence, with a **collected conjunction set**, including **'and', 'but', 'or', 'however', 'although' etc.**"
2. "For each conjunction, we extract its connected **two text sequences**. The nearest two words with **same part of speech** from the two text sequences are connected with the skip-edge. Here, we just consider the **noun, adjective, and adverb**."
3. Additionally, "We also employ the general sentiment lexicons, **SentiWordNet** (Esuli and Sebastiani, 2006), to connect opinions. Two nearest opinion words, detected by sentiment lexicon, from two sequences, will also be connected by skip-edge."
4. Distance cutoff: "If the nearest distance exceeds the threshold, this skip edge will be discarded. Here, we consider the threshold as **nine**."

Worked example: in "good pictures and beautiful music", two skip-edges are created — one between adjectives `good`–`beautiful`, one between nouns `pictures`–`music`.

**(c) Tree CRFs (3.2.3)** — encodes the **syntactic tree structure**. "Each node is corresponding to a word in the dependency tree. The edge is corresponding to dependency tree edge." Dependency representation is from **Klein and Manning (2003)**. Example tree for "I really like this long movie" (Figure 3) with dependency labels `nsubj`, `advmod`, `dobj`, `det`, `amod`.

**(d) Skip-Tree CRFs (3.2.4)** — the proposed unified model. "consists of two types of edges: **tree edges and conjunction skip-edges**." Rationale: "We also notice that there is a relationship 'conj' in syntactic dependency tree. However, we find that it only connects two head words for a few coordinating conjunction, such as 'and', 'or', 'but'. Our designed conjunction skip-edge provides more information for joint structure tagging."

### Feature space (Figure 4) — the full feature list

**Word Feature**
- Word token
- Word lemma
- Word part of speech
- Previous word token, lemma, part of speech
- Next word token, lemma, part of speech
- Negation word appears in previous **4** words (binary)
- Is superlative degree (binary, e.g. "best")
- Is comparative degree (binary, e.g. "better")

**Dictionary Feature**
- WordNet Synonym
- WordNet Antonym
- SentiWordNet Prior Polarity — "We use the words with positive or negative score above a threshold (**0.6**)."

**Sentence Feature**
- Num of positive words in SentiWordNet
- Num of negative words in SentiWordNet
- Num of Negation word

**Syntactic Features**
- Parent word
- Parent SentiWordNet Prior Polarity
- In subject
- In copular
- In object

**Edge Feature**
- Conjunction word
- Syntactic relationship

Note on usage: "For classification and linear CRFs models, we just add this edge features as general features" (i.e. only the graph models exploit them as genuine edge factors).

### Hyperparameters actually stated in the paper (complete list)

| Item | Value |
|---|---|
| Skip-edge max distance threshold | **9** (words) |
| SentiWordNet polarity inclusion threshold | **0.6** |
| Negation window | previous **4** words |
| POS classes used for skip-edges | noun, adjective, adverb |
| Conjunction set | "and", "but", "or", "however", "although" etc. ("etc." — full list **not stated**) |
| Train/test split | **4 of 5 parts train, 1 part test** (5-fold partition; only one split reported) |
| CRF regularization (L1/L2, C) | **not stated** |
| TRP iterations / convergence | **not stated** |
| Rule-based seed lexicon size | **25** positive adjectives + **25** negative adjectives |

## Datasets

| Dataset | Items | Reviews | Sentences | Language | How obtained |
|---|---|---|---|---|---|
| Movie review | **5 movies** | **500 reviews** | **2,207 sentences** | Not stated explicitly; English data (all examples and all lexical resources — WordNet, SentiWordNet — are English) | "In this paper, we **manually annotate** two types of these review data sets." Original source of the raw reviews is **not stated** (no crawl source, no site, no URL). |
| Product review | **4 products** | **601 reviews** | **2,533 sentences** | same | same |

Total annotated sentences: **4,740** (2,207 + 2,533).

**Annotation protocol (as stated):** "We need to label all object features, positive opinions, negative opinions, and the **object feature-opinion pairs** for all sentences. Each sentence is labeled by **two annotators**. The conflict is checked by the **third person**." Inter-annotator agreement statistic: **not stated**. Annotator guidelines document: **not stated**. Movie/product identities (titles, product names): **not stated**.

**Split:** "For each type, including movie and product, the data set is divided into **five parts**. We select **four parts as training data, and the fifth part as testing data**." The actual partition is **not released**.

## Data/code availability stated in the paper

**NONE.**

I searched the entire text (abstract, body, conclusion, acknowledgement, references) for any URL, repository, dataset release, or code statement. There is:
- **no URL of any kind** (no `http`, no `github`, no project page, no email for data requests);
- **no dataset release statement** — the two annotated corpora (500 + 601 reviews; 4,740 sentences) are described as manually annotated for this paper only and are **not offered** to readers;
- **no code release statement** — the CRF/TRP implementation, the feature templates, and the skip-edge construction code are **not available**;
- the only resource pointers are to **third-party public resources used as features**: WordNet, and "SENTIWORDNET: A Publicly Available Lexical Resource for Opinion Mining" (Esuli and Sebastiani, LREC 2006), plus the dependency parser of Klein and Manning (2003).

The acknowledgement names grants (Chinese NSF 60973104, 60803075; Fujitsu Research Center; IDRC Ottawa) but attaches no artifact to them.

## Evaluation

- **Metrics:** "**Precision, Recall and F measure** are used to test our results, as Jin and Ho (2009)." Reported separately for four columns: **Object Features**, **Positive Opinions**, **Negative Opinions**, and **Overall** — each with P(%), R(%), F(%).
- **Human evaluation required?** **No.** There is no human/qualitative evaluation, no user study, no pairwise preference judgement. Evaluation is purely automatic P/R/F against the manually annotated gold tags. The only human involvement is *annotation of the gold data*, not evaluation of output quality.
- **Protocol:** single 4:1 train/test partition per domain (movie, product), one reported run. No cross-validation averaging despite the 5-part partition; no variance/confidence intervals; no significance testing. The definition of the **"Overall"** column (micro-average vs macro-average over the three expression types) is **not stated**.
- **Comparability caveat:** Table 3 explicitly restricts learning methods to two features — "(the learning methods only employ **word token and part of speech** as features)" — so Table 3 is a *controlled low-feature* comparison against rule/lexicon/L-HMM baselines, while Table 4 ("Comparative experiments with **all features**") is the main system comparison. Table 5 is a feature ablation on the movie set with the Skip-Tree CRF.

## Baselines

Four baselines (Section 5.2), all re-implemented by the authors:

1. **Rule based Method** (from Jin and Ho 2009, motivated by Hu and Liu 2004; Turney 2002). Four POS-pattern rules over a 3-word window (Table 2):
   - `JJ` + `NN or NNS` + `Anything`
   - `RB, RBR or RBS` + `JJ` + `NN or NNS`
   - `JJ` + `JJ` + `NN or NNS`
   - `NN or NNS` + `JJ` + `Not NN or NNS`
   "The matching adjective is identified as opinion, and matching nouns are extracted as object features. To determine the polarities of the opinions, **25 positive adjectives and 25 negative adjectives** are used as seeds, and then expanded by searching synonyms and antonyms in **WordNet**."
2. **Lexicon based Method** — "The object features and opinions extraction is same as rule based method. The general sentiment lexicon **SentiWordNet** is employed to detect the polarity for each word."
3. **Lexicalized HMM (L-HMM)** (Jin and Ho, 2009) — "a variant of HMM. It has two observations... uses **word token and part of speech** as two observations. The current tag is not only related with the previous tag, but also correlates with previous two observations." The paper notes it "uses linear interpolation smoothing technique" but "the data sparsity problem seriously hurt the performance. There are many sentences with zero probability."
4. **Classification based Method (Maximum Entropy, MaxEnt)** — "Each word is considered as an instance. Maximum Entropy (MaxEnt) is used in this paper."

System variants compared against each other: **Linear CRFs**, **Skip CRFs** (Skip-chain), **Tree CRFs**, **Skip-Tree CRFs** (proposed).

## Reported results (key numbers as targets)

### Table 3 — learning methods with **only word token + POS** features (Overall P/R/F %)

| Domain | Method | Object Features F | Positive F | Negative F | **Overall P / R / F** |
|---|---|---|---|---|---|
| Movie | Rule | 36.2 | 45.3 | 17.3 | 49.2 / 25.7 / **33.8** |
| Movie | Lexicon | 36.2 | 47.8 | 10.2 | 41.6 / 25.8 / **31.8** |
| Movie | L-HMM | 65.9 | 61.9 | 50.6 | 78.7 / 47.8 / **59.5** |
| Movie | MaxEnt | 79.1 | 72.6 | 42.2 | 79.9 / 56.5 / **66.2** |
| Movie | Linear CRFs | 80.1 | 70.7 | 45.2 | 79.0 / 58.2 / **67.0** |
| Product | Rule | 42.8 | 34.6 | 11.7 | 48.3 / 22.3 / **30.6** |
| Product | Lexicon | 42.8 | 40.0 | 5.9 | 39.1 / 23.0 / **29.0** |
| Product | L-HMM | 61.6 | 69.8 | 32.9 | 73.8 / 43.6 / **54.8** |
| Product | MaxEnt | 66.4 | 72.6 | 40.4 | 76.6 / 49.9 / **60.4** |
| Product | Linear CRFs | 69.6 | 78.5 | 44.0 | 82.5 / 53.1 / **64.6** |

Selected full triples: Movie Linear CRFs object features **81.8 / 78.4 / 80.1**; Movie Linear CRFs positive **79.1 / 63.9 / 70.7**; Movie L-HMM object features **88.0 / 52.6 / 65.9**; Product Linear CRFs object features **91.1 / 56.3 / 69.6**; Product Linear CRFs positive **88.7 / 70.4 / 78.5**.

*Extraction caveat:* in the extracted text, the MaxEnt **positive-opinion** cell is identical for movie and product (`82.2 / 65.0 / 72.6`), which is suspicious and may be an artifact of PDF text extraction. Verify against the PDF before quoting.

### Table 4 — main comparison, **all features** (Overall P/R/F %)

| Domain | Method | Object F | Positive F | Negative F | **Overall P / R / F** |
|---|---|---|---|---|---|
| Movie | MaxEnt | 79.6 | 73.5 | 50.5 | 81.9 / 60.2 / **69.4** |
| Movie | Linear CRFs | 79.2 | 74.5 | 60.9 | 77.4 / 66.8 / **71.7** |
| Movie | Skip CRFs | 81.2 | 77.4 | 68.2 | 80.3 / 71.5 / **75.7** |
| Movie | Tree CRFs | 81.5 | 78.9 | 67.9 | 81.2 / 72.2 / **76.2** |
| **Movie** | **SkipTreeCRFs** | **83.7** | **81.1** | **72.7** | **82.6 / 76.2 / 79.3** |
| Product | MaxEnt | 75.1 | 74.3 | 47.8 | 76.9 / 58.1 / **66.2** |
| Product | Linear CRFs | 78.1 | 78.6 | 54.5 | 77.0 / 64.8 / **70.4** |
| Product | Skip CRFs | 78.7 | 80.6 | 59.6 | 81.2 / 66.1 / **73.2** |
| Product | Tree CRFs | 77.5 | 79.4 | 59.2 | 78.0 / 67.0 / **72.1** |
| **Product** | **SkipTreeCRFs** | **80.1** | **83.6** | **67.0** | **86.6 / 69.3 / 77.0** |

Full triples for the proposed model: Movie Skip-Tree object features **85.5 / 82.0 / 83.7**; positive **82.3 / 80.0 / 81.1**; negative **80.2 / 66.4 / 72.7**. Product Skip-Tree object features **87.1 / 74.1 / 80.1**; positive **91.8 / 76.7 / 83.6**; negative **81.1 / 57.0 / 67.0**.

**Headline deltas (targets):**
- Skip-Tree CRF vs Linear CRF overall F: movie **79.3 vs 71.7 (+7.6)**, product **77.0 vs 70.4 (+6.6)**.
- Skip CRF vs Linear CRF overall F: movie **75.7 vs 71.7 (+4.0)**, product **73.2 vs 70.4 (+2.8)**.
- Tree CRF vs Linear CRF: movie **76.2 vs 71.7 (+4.5)**, product **72.1 vs 70.4 (+1.7)**.
- Best non-CRF baseline (MaxEnt, all features): **69.4** movie / **66.2** product.
- Weakest baselines (word+POS only): rule **33.8** movie / **30.6** product; lexicon **31.8** / **29.0**.
- Negative-opinion extraction is the hardest column throughout (best F **72.7** movie, **67.0** product).

### Table 5 — feature ablation, Skip-Tree CRF, **movie** (Overall F %)

| Feature set | Object Features F | Positive F | Negative F | **Overall P / R / F** |
|---|---|---|---|---|
| Basic (word token only) | 81.4 | 75.0 | 49.8 | 79.8 / 62.4 / **70.0** |
| Basic + Word Feature | 82.7 | 77.4 | 60.2 | 80.7 / 68.6 / **74.1** |
| Basic + Dictionary | 78.5 | 79.4 | 67.4 | 80.0 / 71.0 / **75.2** |
| Basic + Sentence | 78.9 | 77.8 | 60.0 | 82.3 / 65.9 / **73.2** |
| Basic + Syntactic | 77.0 | 76.7 | 59.8 | 81.2 / 64.2 / **71.7** |
| Basic + Edge | 82.1 | 77.4 | 60.6 | 82.0 / 67.8 / **74.2** |
| **All Features** | **83.7** | **81.1** | **72.7** | **82.6 / 76.2 / 79.3** |

Findings stated: "The **dictionary features are the most important features**, especially for positive opinion and negative opinion identification"; word features help (POS, superlative/comparative forms); "**Syntactic features acquire limited improvement** in this experiment. They may overlap with CRF based structure model"; sentence-level features and edge features both contribute; "When combing all the features, the result is significantly improved compared with any single feature set."

**Qualitative example given:** "although this camera takes great pictures, it is extremely fragile.", "fragile" is not correctly classified by MaxEnt and Linear CRFs. But the Skip-chain CRFs can correctly classify "fragile" as negative opinion, with conjunction "although", and the skip edge between "great" and "fragile"." (Note: the paper calls `although` a conjunction here, though its own conjunction-set rationale in 3.2.2 assigns same-polarity to "and" and different-polarity to "but".)

## Implementation complexity

**HIGH** (the *minimum viable subset* is **medium**).

Why high:
1. **Four model variants, two of which are loopy graphical models.** Linear-chain CRF is a solved problem (CRFsuite / `sklearn-crfsuite` / `pytorch-crf`). But Skip-chain, Tree, and Skip-Tree CRFs have **cycles**, and the paper uses **Tree Re-Parameterization (TRP)** for approximate inference — a nontrivial algorithm to implement, and the paper gives **no** iteration count, damping, or convergence criterion. There is no off-the-shelf library that takes an arbitrary skip/tree edge structure and does TRP training.
2. **Two heterogeneous edge types must be built and factorized.** Conjunction skip-edges require: conjunction detection over a set that is only partially enumerated ("etc."), splitting the sentence into the two text sequences governed by the conjunction, POS tagging, nearest-same-POS matching restricted to noun/adjective/adverb, an additional SentiWordNet-driven opinion-to-opinion matching, and a distance cutoff at 9. Tree edges require a **dependency parse** (Klein & Manning 2003; modern substitute: Stanford CoreNLP / spaCy / Stanza) plus mapping dependency arcs to label-variable edges.
3. **Rich, overlapping features across four categories** (word, dictionary, sentence, syntactic) plus **edge features** that must be wired as *edge factors* for graph models but as *node features* for MaxEnt/linear CRF — two different feature-injection paths.
4. **BIO tag scheme with 8 tags** and three interacting expression types; the paper itself notes a structural failure mode: for product object features Tree CRFs declined because "the tags 'FB' and 'FI' are out of order when transferring to tree structure."
5. **Gold data does not exist publicly.** The 4,740-sentence token-level, 8-tag annotated corpus must be substituted or re-annotated.

Why the MVP is only medium: a Linear-CRF baseline with the same feature set is a few hundred lines on top of `sklearn-crfsuite`, and Skip-chain CRFs can be *approximated* as a linear CRF augmented with skip-edge features (which the paper itself does for the non-graph models), giving most of the reported gain.

## Reproducibility obstacles (concrete)

1. **No code, no data, no URL.** Availability is **NONE**. Both annotated corpora are withheld; the CRF/TRP implementation is withheld. Exact-number reproduction of Tables 3–5 is therefore impossible without re-annotating everything.
2. **The corpora cannot be reconstructed.** Movie titles (5) and product names (4) are not stated; the review source/crawl is not stated; only aggregate counts (500/601 reviews; 2,207/2,533 sentences) are given. There is no way to obtain the identical sentences.
3. **Token-level gold labels required.** The task needs per-word labels over 8 tags. Public ABSA datasets (SemEval-2014 Task 4, Hu & Liu) provide **aspect terms and aspect-level polarity**, not per-word `FB/FI/PB/PI/CB/CI/N/O` spans. A mapping is possible but lossy and will not match the paper's label distribution (notably the separate `N` negation tag and multi-word opinion spans).
4. **TRP under-specified.** No iterations, no damping, no convergence tolerance, no initialization. Results on loopy graphs are sensitive to these.
5. **CRF training under-specified.** No regularization type/strength, no feature-template listing (only the feature *types* in Figure 4 — no actual feature function strings, no cutoffs on word frequency, no scaling), no number of L-BFGS iterations.
6. **Parser unspecified beyond a citation.** "Klein and Manning (2003)" refers to a factored parsing model; which parser binary/version produced Figure 3's trees is not stated. Different dependency schemes (e.g. Universal Dependencies vs the paper's `nsubj/advmod/dobj/det/amod` labels) change the tree-edge structure materially.
7. **Lexicon versions unspecified.** WordNet version, SentiWordNet version (1.0 vs 3.0), and how "positive or negative score above a threshold (0.6)" resolves the *difference* `PosScore − NegScore` versus the raw score are all **not stated**. SentiWordNet scores differ substantially across versions, and the dictionary feature is reported as the single most important feature — so this ambiguity directly moves the headline number.
8. **Conjunction set incomplete.** "and", "but", "or", "however", "although" **etc.** — the closed set is not enumerated, and the paper's own worked example treats `although` as a conjunction while the polarity rationale in 3.2.2 only covers `and` (same polarity) and `but` (different polarity). Behavior for the remaining conjunctions is undefined.
9. **Metric ambiguity.** The **"Overall"** column's aggregation (micro vs macro over object features / positive / negative) is not stated; reproducing 79.3 exactly requires guessing it.
10. **No statistical rigor.** Single split, no averaging, no significance tests, no error bars — so a reproduction that lands within ±3 F cannot be judged as success or failure.
11. **PDF extraction artifacts.** The extracted text shows at least one likely corrupted/duplicated table cell (MaxEnt positive opinions identical across movie and product in Table 3). Numbers must be verified against the original PDF.
12. **Annotator agreement absent.** With two annotators and a third adjudicator but no reported agreement (no κ), the gold standard's ceiling is unknown; a reproducer cannot tell whether their ~75 F is a modeling gap or a label-noise gap.

## Minimum viable reproduction plan (2–4 week student scope)

**Reframe first:** this is an **aspect-based sentiment / opinion-mining** reproduction, *not* a microblog summarization one. Do not present it as a Twitter/Weibo system.

**Substitutions (all realistic):**

| Paper element | Substitute |
|---|---|
| Withheld 4,740-sentence corpus | **SemEval-2014 Task 4** (Restaurant + Laptop) aspect-term data, or **Hu & Liu** customer-review corpus. Restaurant ≈ 3,041 train / 800 test sentences; Laptop ≈ 2,958 train / 800 test — comparable scale. |
| Per-word `FB/FI/PB/PI/CB/CI/N/O` gold | Derive from SemEval aspect terms: map aspect-term tokens to `FB`/`FI`; derive opinion words from a lexicon (SentiWordNet / VADER / SenticNet) or from SemEval opinion-target annotations where available; mark `not`/`n't`/`don't` as `N`. Document the mapping as a known deviation. |
| Klein & Manning 2003 dependency parser | **spaCy** `en_core_web_sm` or **Stanza** dependency parse; remap labels to the paper's set. |
| TRP approximate inference for loopy CRFs | (i) **`sklearn-crfsuite`** linear-chain CRF as the workhorse; (ii) approximate Skip-chain CRF by **adding skip-edge features to the linear model** (the paper's own treatment of edge features for non-graph models); (iii) optional stretch: implement skip edges as real factors with loopy BP / TRP in PyTorch, time permitting. |
| WordNet / SentiWordNet features | `nltk.corpus.wordnet` + `nltk.corpus.sentiwordnet` (SentiWordNet 3.0); use `max(PosScore, NegScore) ≥ 0.6` and record the choice explicitly. |

**Week-by-week:**
- **Week 1 — data + labels.** Load SemEval-2014 restaurant (and laptop if time), build the token-level 8-tag conversion, write the conversion script + label-distribution report, implement the exact Figure 4 feature extractor (word, dictionary, sentence, syntactic), and the conjunction skip-edge builder (conjunction set, same-POS nearest match over noun/adj/adv, SentiWordNet opinion matching, distance ≤ 9).
- **Week 2 — baselines.** Implement Rule based (Table 2's four POS patterns + 25/25 seed adjectives expanded via WordNet) and Lexicon based (SentiWordNet polarity). These are cheap and give the low-end anchor. Report P/R/F per column and Overall.
- **Week 3 — models.** MaxEnt (per-word classifier, `scikit-learn`) → Linear CRF (`sklearn-crfsuite`, with and without the full feature set, to mirror Table 3 vs Table 4) → Skip-augmented CRF. Add a small hyperparameter sweep (L2 `c1`/`c2`) since the paper leaves it open. Also implement the nearest-opinion pairing heuristic and emit the Figure-1-style structured summary.
- **Week 4 — analysis + writeup.** Feature ablation mirroring Table 5 (Basic / +Word / +Dictionary / +Sentence / +Syntactic / +Edge / All), error analysis on negative opinions (the weak column everywhere), and a short discussion of deviations from the paper.

**Expected numbers (honest targets on substituted data):**
- Rule based: **~30–40 Overall F** (paper: 33.8 movie / 30.6 product) — should land close, since the rules are fully specified.
- Lexicon based: **~28–40 Overall F** (paper: 31.8 / 29.0).
- MaxEnt, word+POS only: **~55–65 Overall F** (paper: 66.2 / 60.4).
- Linear CRF, word+POS only: **~58–66 Overall F** (paper: 67.0 / 64.6).
- Linear CRF, all features: **~68–74 Overall F** (paper: 71.7 / 70.4).
- Skip-augmented CRF, all features: **~72–78 Overall F** (paper: 75.7 / 73.2) — i.e. expect **+2 to +4 F** from conjunction skip information, matching the paper's own delta direction.
- Full Skip-Tree CRF: **unlikely to be reproduced**; treat **79.3 / 77.0** as the paper's upper-bound reference only.
- Per-column shape to expect: object features strongest (**~80 F**), positive opinions next (**~75–80 F**), **negative opinions clearly weakest (~50–65 F)** — this asymmetry is the paper's most robust and easily reproduced finding.

**Success criterion:** reproducing the *ordering* (rule < lexicon < L-HMM-like < MaxEnt < Linear CRF < skip/tree-augmented CRF) and the *negative-opinion weakness*, with Overall F within ~5 points of the paper on a substituted dataset.

## Verdict

This is a solid, clearly-written 2010 Coling paper from Tsinghua + Fujitsu that makes one genuinely useful conceptual move: instead of feeding conjunction and syntactic structure in as *input features or hand-written rules* (the prevailing practice of Hu & Liu, Ding & Liu, Wilson et al.), it encodes them as **edges over the output label variables** in a CRF family — Linear → Skip-chain (conjunction skip-edges) → Tree (dependency tree edges) → **Skip-Tree CRFs** — and shows a monotone, consistent gain on two domains (movie overall F **71.7 → 75.7 → 76.2 → 79.3**; product **70.4 → 73.2 → 72.1 → 77.0** over the Linear CRF), with the honest and well-supported observation that negative-opinion extraction is the hard column and that dictionary (SentiWordNet) features matter most. The paper is also commendably explicit about its one structural failure (product Tree CRF dropping because "FB" and "FI" tags are "out of order when transferring to tree structure"). For a student reproduction, however, it is a **hostile target for exact replication**: there is **no released data and no released code (availability: NONE)**, the 4,740-sentence token-level 8-tag corpus cannot be reconstructed because the 5 movies and 4 products are unnamed and the review source is unstated, and the loopy-graph half of the method depends on a **TRP inference procedure whose hyperparameters are entirely absent** (as are CRF regularization, feature templates, WordNet/SentiWordNet versions, the "Overall" metric definition, and annotator agreement). The pragmatic path is to substitute SemEval-2014 ABSA data, reproduce the fully-specified pieces (Table 2's rules, the 25+25 seed lexicon, the Figure 4 feature set, the threshold-9 conjunction skip-edges), implement Linear CRF + skip-augmented CRF, and treat the paper's numbers as an upper-bound reference rather than a pass/fail bar. Most importantly for this workspace: **the paper has nothing to do with Twitter or Weibo** — it is product/movie review mining, and should be repositioned as an aspect-based opinion-mining baseline rather than a microblog-summarization one.
