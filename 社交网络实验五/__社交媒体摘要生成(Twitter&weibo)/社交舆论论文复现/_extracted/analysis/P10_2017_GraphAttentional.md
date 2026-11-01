# Abstractive Document Summarization with a Graph-Based Attentional Neural Model

## Bibliographic info (authors, venue, year)

- **Authors:** Jiwei Tan, Xiaojun Wan and Jianguo Xiao
- **Affiliation (as printed):** "Institute of Computer Science and Technology, Peking University" / "The MOE Key Laboratory of Computational Linguistics, Peking University"; emails `{tanjiwei,wanxiaojun,xiaojianguo}@pku.edu.cn`. "Xiaojun Wan is the corresponding author."
- **Venue / year:** "Proceedings of the 55th Annual Meeting of the Association for Computational Linguistics, pages 1171–1181, Vancouver, Canada, July 30 - August 4, 2017. c 2017 Association for Computational Linguistics" → **ACL 2017 (long paper, P17-1108)**.
- **DOI given in the paper:** `https://doi.org/10.18653/v1/P17-1108`
- **Funding acknowledged:** "863 Program of China (2015AA015403), NSFC (61331011), and Key Laboratory of Science, Technology and Standard in Press Industry".
- **Human evaluation credited to:** "Xinjie Zhou, Jianmin Zhang for doing human evaluation".

## Task (what is summarized, input -> output, extractive vs abstractive)

- **Task:** **single-document abstractive document summarization** of **English news articles**.
- **Input → output:** a document `d` = sequence of sentences `d = {s_i}`, each sentence `s_i = {w_{i,k}}` → a multi-sentence abstractive summary `Y = {y_1, ..., y_|Y|}`. The output is *generated word by word* (fully abstractive), not selected from the input; the paper explicitly contrasts this with extraction: "Extraction is far from the way humans write summaries."
- **Explicitly abstractive, not extractive.** The paper states that prior neural abstractive models "are still not competitive to extractive methods" and that its goal is to close that gap. `Cheng and Lapata (2016) also adopt a word extraction model, which is restricted to use the words of the source document to generate a summary, although the performance is much worse than the sentence extractive model.`
- **Domain caveat for this course:** this is **news summarization (CNN / DailyMail)**, i.e. *not* Twitter or Weibo, and the language is English. The paper never mentions Twitter, microblogs, Weibo, or social media. Only its *mechanism* (graph-based attention) is portable to social-media summarization.
- **Key sub-problems the paper claims to address:** "the saliency, fluency, coherence, and novelty requirements of the generated summary" — "Fluency is what neural generation models are naturally good at, but the other factors are less considered in previous neural abstractive models." Stated gap: "as far as we know, however, saliency has not been addressed by existing neural abstractive models."

## Method (core algorithm in implementable detail: model, components, features, objective, hyperparameters with values)

### Overall architecture
Hierarchical encoder–decoder "similar to (Li et al., 2015)", shown in Figure 1. Two novel contributions: (1) a **graph-based attention mechanism** (Figure 1b), and (2) a **hierarchical decoding algorithm with a reference mechanism**.

### Encoder
- Word-level LSTM encoder: `h_{i,k} = enc_word(h_{i,k-1}, e_{i,k})`, where `e_{i,k}` is the distributed representation of word `w_{i,k}` from embedding matrix `E_v`. The word sequence of each sentence is appended with an `"<eos>"` token.
- "The last hidden state (after the word encoder receives "<eos>") is denoted as `h_{i,-1}`, and used as the embedding representation of the sentence `s_i`, denoted as `x_i`."
- Sentence-level LSTM encoder: `h_i = enc_sent(h_{i-1}, x_i)`. "A pseudo sentence of an "<eod>" token is appended at the end of the document." `c = h_{-1}` is the document representation.
- LSTM type: "We use the Long Short-Term Memory (LSTM) (Hochreiter and Schmidhuber, 1997) as both the word encoder `enc_word` and sentence encoder `enc_sent`. In particular, we adopt the variant of LSTM structure in (Graves, 2013)."

### Decoder with attention (baseline formulation)
- Sentence decoder: `h'_0 = c`, `h'_j = dec_sent(h'_{j-1}, x'_{j-1})`, where `x'_{j-1}` is the encoded representation of the previously generated sentence `s'_{j-1}`.
- Word decoder: `h'_{j,0} = h'_j`, `h'_{j,k} = dec_word(h'_{j,k-1}, e_{j,k-1})`.
- Word representations are mapped to vocabulary-size vectors and softmax-normalized.
- Termination: "A word decoder stops when it generates the "<eos>" token and similarly the sentence decoder stops when it generates the "<eod>" token."
- Traditional attention: `c_j = Σ_i α_ij h_i`, with `α_ij = exp(η(h_i,h'_j)) / Σ_l exp(η(h_l,h'_j))` (Eq. 1), and "In this paper we use `η(a, b) = a^T M b` where M is a parameter matrix." (alternatives listed: `η(a,b)=a^T b`, `η(a,b)=a^T M b`, or a non-linear MLP).

### Graph-based attention mechanism (core novelty)
- Motivation from TextRank (Mihalcea and Tarau, 2004) / LexRank (Erkan and Radev, 2004) / PageRank: "a sentence is important in a document if it is heavily linked with many important sentences (Wan, 2010)."
- Graph: vertices `V` = the `n` sentences, edges `E` = sentence similarity. `W ∈ R^{n×n}` adjacency, with **`W(i, j) = h_i^T M h_j`** (same learned `M`), and the recursive ranking (Eq. 2):
  `f(t+1) = λ W D^{-1} f(t) + (1 − λ) y`
  where `f = [f_1, ..., f_n] ∈ R^n` are sentence rank scores, `D` is the diagonal matrix whose `(i,i)` element is the sum of the `i`-th column of `W`, and `y ∈ R^n` with all elements `1/n`.
- Closed form (Eq. 3): `f = (1 − λ)(I − λ W D^{-1})^{-1} y`.
- **Topic-sensitive PageRank twist** (inspired by Wan et al., 2007 query-focused graph-based extractive summarization, and Haveliwala 2002): "We treat the current decoding state `h'_j` as the topic and add it into the graph as the 0-th pseudo-sentence." Then `y_T = 1/|T|` if `i ∈ T`, else `0` (Eq. 4), so "`y_T` is always a one hot vector and only `y_0 = 1`, indicating the 0-th sentence is `s'_j`."
- `W_j` = new adjacency matrix with `h'_j` added; `D_j` = corresponding diagonal matrix. Final decoding-state-specific scores (Eq. 5):
  `f_j = (1 − λ)(I − λ W_j D_j^{-1})^{-1} y_T`
  "so that the importance scores of original sentences are different when decoding different state `h'_j`."
- **Distraction mechanism** (borrowed from Chen et al., 2016) to get the final attention weights (Eq. 6):
  `α_ij = max(f_i^j − f_i^{j−1}, 0) / Σ_l max(f_l^j − f_l^{j−1}, 0)`
  with "`f_0` is initialized with all elements equal to `1/n`." Effect: "subtracts the rank scores of the previous step, to penalize the model from attending to previously attended sentences, and also help to normalize the ranked scores `f_j`."
- Differentiability: "Both Eq. 5 and Eq. 6 are differentiable; thus we can use the graph-based attention function Eq. 6 to replace the traditional attention function Eq. 1, and the neural model using the graph-based attention can also be trained using traditional gradient-based methods."

### Training objective
- Negative log likelihood over training set `D` (Eq. 7–8):
  `L = Σ_{(Y,X)∈D} − log p(Y|X; θ)`, with
  `log p(Y|X;θ) = Σ_{τ=1}^{|Y|} log p(y_τ | {y_1,...,y_{τ-1}}, c; θ)`,
  where `X = {x_1,...,x_|X|}` and `Y = {y_1,...,y_|Y|}` "including the "<eos>" and "<eod>" tokens for structure information."
- Optimizer: **Adamax** (Kingma and Ba, 2014); "The parameters of Adamax are set to those provided in (Kingma and Ba, 2014)." (numeric learning rate / β values are **not stated** in this paper).

### Hierarchical decoding algorithm with reference mechanism
Motivating problems: "out-of-vocabulary (OOV) words, information incorrectness, error accumulation and repetition."
- **OOV / entity handling:** "we can first identify the entities of a document using NLP toolkit like Stanford CoreNLP" (`http://stanfordnlp.github.io/CoreNLP/`). "Then we prefix every entity with an "@entity" token and a number indicating how many words the entity has." E.g. `@entity 2 mary day`, `@entity 1 goa` in Figure 3. "After decoding we recover the OOV words by matching entities in the original document according to the contexts."
- **Word-level K-best beam search with reference term:**
  `score(y_τ) = p̃(y_τ) + γ ( ref(Y_{τ−1} + y_τ, s*) − ref(Y_{τ−1}, s*) )`,
  where `Y_{τ−1} = {y_1,...,y_{τ−1}}`, `p̃(y_τ) = log p(y_τ | Y_{τ−1}, c; θ)`, `s*` is an original sentence to refer to, and `ref` "calculates the ratio of bigram overlap between two texts."
  "The added term aims to favor the generated word `y_τ` with improving the bigram overlap between current generated summary `Y_{τ−1}` and the target original sentence `s*`."
  "`γ` is introduced to control the influence of the reference mechanism." Caveat stated: "because of the non-optimal search, the generated sentence will still be different to the original sentence even with an extremely large γ."
- **Sentence-level N-best beam search:** "to keep the N generated sentences by referring to N different original sentences, which have the highest attention scores and have not been used as a reference. With referring to N different sentences, the N candidate sentences are guaranteed diverse. Sentence-level beam search is realized by maximizing the accumulated score of all the sentences generated."
- Rationale for two levels: "The word-level beam search is not easy to be extended to the sentence level. The reason is that the K-best sentences generated by a word decoder will mostly be similar to each other, which is also noticed by Li et al. (2016)."

### Preprocessing and hyperparameters (all values as stated)
- "The documents and summaries are first lowercased and tokenized, and all digit characters are replaced with the "#" symbol, similar to (Nallapati et al., 2016, 2017)."
- "We keep the 40,000 most frequently occurring words and other words are replaced with the "<OOV>" token."
- "We use the corpora which are already provided with labeled entities (Nallapati et al., 2016)."
- Implementation framework: **Theano** (`https://github.com/Theano/Theano`).
- Layers: "for the word encoder and decoder we use three layers of LSTM, and for the sentence encoder and decoder we use one layer of LSTM."
- "The dimension of hidden vectors are all 512."
- Embeddings: "pre-trained GloVe (Pennington et al., 2014) vectors for the initialization of word vectors, which will be further trained in the model. The dimension of word vectors is 100." (`http://nlp.stanford.edu/projects/glove`)
- **λ = 0.9** (damping). "When λ = 1.0 the model fails to train because of running into a singular matrix." Figure 2a sweeps λ over `0.0, 0.1, ..., 0.9, 0.99`; "When using a larger λ, the performance is better and the convergence is faster."
- **γ = 300** ("γ is tuned on the validation set and the best choice is 300"); Figure 2b sweeps γ over `0, 1, 10, 100, 200, 300, 400, 500, 1e3, 1e4`. "γ = 0 is the baseline of the traditional decoding algorithm which does not refer to the original document."
- "The batch size is set to 8 documents, and an epoch is set containing 10,000 randomly sampled documents."
- "Convergence is reached within 200 epochs on the DailyMail dataset and 120 epochs on the CNN dataset. It takes about one day for every 30 epochs on a GTX-1080 GPU card."
- "The beam sizes for word decoder and sentence decoder are 15 and 2, respectively."
- Not stated: LSTM parameter initialization, learning rate/β1/β2/ε values, dropout, gradient clipping, vocabulary for the entity-prefix tokens, exact `ref` normalization details.

## Datasets (names, sizes, language, domain, HOW OBTAINED - crawled by authors? public? URL given?)

- **CNN** and **DailyMail** (the standard CNN/DailyMail news summarization corpora), **English**, **news domain**.
- Origin: "The corpora are originally constructed in (Hermann et al., 2015) by collecting human generated abstractive highlights from the news stories in the CNN and DailyMail website." → **public third-party corpora; the authors did NOT crawl them**.
- The authors additionally use a preprocessed variant: "We use the corpora which are already provided with labeled entities (Nallapati et al., 2016)."
- Statistics (Table 1), columns `Train / Valid / Test / D.L. / S.L.` where "D.L. and S.L. indicate the average number of sentences in the document and summary, respectively":

| Dataset | Train | Valid | Test | D.L. | S.L. |
|---|---|---|---|---|---|
| CNN | 83568 | 1220 | 1093 | 29.8 | 3.54 |
| DailyMail | 196557 | 12147 | 10396 | 26.0 | 3.84 |

- A **merged CNN/DailyMail test set** is also used for Table 4 ("Comparison results on the merged CNN/DailyMail test set using full-length F1 metric").
- **No dataset download URL is given in the paper** for either corpus or for the entity-labeled version.
- The only data-adjacent URL in the paper is a single example article used in the case study: `http://www.dailymail.co.uk/news/article-3041766/Benefits-cheat-pocketed-17-000-taxpayers-money.html` ("The original story and highlights can be found at ...").

## Data/code availability stated in the paper (quote any URL, 'available at', 'we will release', download link; if none, say NONE)

**NONE.** The paper contains **no statement that its own code, model, or preprocessed data is available**, no "available at", no "we will release", and no repository link for the proposed model. Searching the full text, the only URLs present are for third-party tools/resources:

- `http://stanfordnlp.github.io/CoreNLP/` (footnote 1, entity recognition toolkit)
- `https://github.com/Theano/Theano` (footnote 2, "We use Theano for implementation")
- `http://nlp.stanford.edu/projects/glove` (footnote 3, pre-trained GloVe vectors)
- `http://www.dailymail.co.uk/news/article-3041766/Benefits-cheat-pocketed-17-000-taxpayers-money.html` (footnote 4, the single case-study article)

The paper also relies on others' artifacts but only as citations, not links: "The output summaries of NN-SE are provided by the authors, and the output summaries of Distraction are achieved by running the code provided by the authors on the DailyMail dataset." → baseline outputs came from the *baseline* authors' code, which is not the same as this paper releasing code.

## Evaluation (metrics, human evaluation required? protocol, folds)

- **Automatic metric:** "We adopt the widely used ROUGE (Lin, 2004) toolkit for evaluation." Three different ROUGE configurations are used in different tables (a reproducer must match the right one):
  - Table 2 (CNN): "using the full-length F1 variants of Rouge" → ROUGE-1/2/L F1.
  - Table 3 (DailyMail): "using Rouge recall at 75 bytes" → ROUGE-1/2/L recall.
  - Table 4 (merged CNN/DailyMail): "using full-length F1 metric".
  - Table 6 (ablation, CNN): "using the full-length F1 variants of Rouge" with "Two-tailed t-tests demonstrate the difference between Our Method and other frameworks are all statistically significant (p < 0.01)."
- **Human evaluation: yes, performed.** "We also conducted human evaluation on **20 random samples from the DailyMail test set**" comparing against Lead-3, NN-SE (Cheng and Lapata, 2016) and Distraction (Chen et al., 2016). "**Three participants** were asked to compare the generated summaries with the human summaries, and assess each summary from four independent perspectives: (1) How informative the summary is? (2) How concise the summary is? (3) How coherent (between sentences) the summary is? (4) How fluent, grammatical the sentences of a summary are? Each property is assessed with a score from 1 (worst) to 5 (best)." The three participants are named in the Acknowledgments (Xinjie Zhou, Jianmin Zhang) — i.e. in-house annotators, not crowdworkers.
- **No cross-validation / folds are mentioned.** Fixed provided train/valid/test splits; single training run per setting; no seed/variance reporting is stated.
- **Hyperparameter/model selection:** "For efficiency we test on **500 random samples from the DailyMail test set**" (Figure 2a/2b), and "γ is tuned on the validation set". Note that λ and γ were partly selected on test-set samples, which a reproducer should be aware of.

## Baselines (list them)

**Table 2 (CNN test set, full-length F1):** Lead-3; Luhn; Edmundson; LSA; LexRank; TextRank; Sum-basic; KL-sum; Uni-GRU ("a non-hierarchical seq2seq baseline model"); Distraction-M3. These are "the reported results in (Chen et al., 2016)".

**Table 3 (DailyMail test set, ROUGE recall at 75 bytes):** LREG(500) ("a feature based method using linear regression"); NN-ABS(500) ("a neural abstractive baseline which is a simple hierarchical extension of (Rush et al., 2015)"); NN-WE(500) ("the abstractive model which restricts the generation of words from the original document"); Lead-3 ("a strong extractive baseline that uses the lead three sentences as the summary"); NN-SE (Cheng and Lapata, 2016); SummaRuNNer-abs ("an extractive model similar to SummaRuNNer but is trained directly on the abstractive summaries"); SummaRuNNer (Nallapati et al., 2017). "(500)" marks baselines "tested on 500 samples of the test set".

**Table 4 (merged CNN/DailyMail, full-length F1):** words-lvt2k; words-lvt2k-ptr; words-lvt2k-hieratt (Nallapati et al., 2016) — "The words-lvt2k and words-lvt2k-ptr are flat models and words-lvt2k-hieratt is a hierarchical extension."

**Human evaluation baselines (Table 5):** Lead-3; NN-SE; Distraction.

**Ablation variants (Table 6, CNN):** "w/o GraphAtt" (replace graph-based attention by a traditional attention function); "w/o SentenceBeam" (remove the sentence-level beam search); "w/o BeamSearch" (remove both sentence- and word-level beam search, "and use a greedy decoding algorithm with the reference mechanism").

## Reported results (key numbers, so a reproducer knows the target)

**Table 2 — CNN test set, full-length F1 (R-1 / R-2 / R-L):**

| Method | R-1 | R-2 | R-L |
|---|---|---|---|
| Lead-3 | 26.1 | 9.6 | 17.8 |
| Luhn | 23.2 | 7.2 | 15.5 |
| Edmundson | 24.5 | 8.2 | 16.7 |
| LSA | 21.2 | 6.2 | 14.0 |
| LexRank | 26.1 | 9.6 | 17.7 |
| TextRank | 23.3 | 7.7 | 15.8 |
| Sum-basic | 22.9 | 5.5 | 14.8 |
| KL-sum | 20.7 | 5.9 | 13.7 |
| Uni-GRU | 18.4 | 4.8 | 14.3 |
| Distraction-M3 | 27.1 | 8.2 | 18.7 |
| **Our Method** | **30.3** | **9.8** | **20.0** |

**Table 3 — DailyMail test set, ROUGE recall at 75 bytes:**

| Method | R-1 | R-2 | R-L |
|---|---|---|---|
| LREG(500) | 18.5 | 6.9 | 10.2 |
| NN-ABS(500) | 7.8 | 1.7 | 7.1 |
| NN-WE(500) | 15.7 | 6.4 | 9.8 |
| Lead-3 | 21.9 | 7.2 | 11.6 |
| NN-SE | 22.7 | 8.5 | 12.5 |
| SummaRuNNer-abs | 23.8 | 9.6 | 13.3 |
| SummaRuNNer | 26.2 | 10.8 | 14.4 |
| **Our Method** | **27.4** | **11.3** | **15.1** |

**Table 4 — merged CNN/DailyMail test set, full-length F1:**

| Method | R-1 | R-2 | R-L |
|---|---|---|---|
| words-lvt2k | 32.5 | 11.8 | 29.5 |
| words-lvt2k-ptr | 32.1 | 11.7 | 29.2 |
| words-lvt2k-hieratt | 31.8 | 11.6 | 28.7 |
| **Our Method** | **38.1** | **13.9** | **34.0** |

**Table 5 — human evaluation (1–5; Informative / Concise / Coherent / Fluent):**

| Method | Informative | Concise | Coherent | Fluent |
|---|---|---|---|---|
| Lead-3 | 3.60 | 3.75 | 4.16 | 3.85 |
| NN-SE | 3.85 | 3.70 | 3.48 | 3.78 |
| Distraction | 3.03 | 3.25 | 2.93 | 3.65 |
| **Our Method** | **3.93** | **3.82** | **3.53** | **3.80** |

**Table 6 — ablation, CNN test set, full-length F1:**

| Framework | R-1 | R-2 | R-L |
|---|---|---|---|
| Our Method | 30.3 | 9.8 | 20.0 |
| w/o GraphAtt | 29.2 | 9.0 | 19.0 |
| w/o SentenceBeam | 29.6 | 9.3 | 19.1 |
| w/o BeamSearch | 25.1 | 6.7 | 17.9 |

**Headline claims / qualitative targets:**
- "our abstractive method is able to outperform traditional extractive methods and the distraction-based abstractive model" on CNN (30.3 vs 27.1 R-1 for Distraction-M3).
- On DailyMail it "is able to outperform state-of-the-art neural extractive methods" (27.4 vs 26.2 R-1 for SummaRuNNer).
- Ablation: "the graph-based attention mechanism is significantly better than traditional attention mechanism for the document summarization task" (30.3 vs 29.2 R-1); "Beam search helps significantly improve the generated summaries" (25.1 → 30.3 R-1 when adding word+sentence beam search); "Our proposed decoding algorithm enables a sentence-level beam search, which helps improve the generated summaries with multiple sentences."
- "An interesting observation is the results of the hierarchical model in Table 4 are lower than the flat models, which may demonstrate the difficulty for a traditional attention model to identify the important information in a document." (words-lvt2k-hieratt 31.8 < words-lvt2k 32.5).
- Hyperparameters: best λ = 0.9 (λ = 1.0 → "running into a singular matrix"); best γ = 300; "The γ factor significantly affects the results, but the optimal value is easy to be decided on a validation set."
- Human eval commentary: "The Distraction method in fact usually produces the shortest summaries, but the conciseness score is low mainly because sometimes it generates repeated sentences." "not surprisingly Lead-3 gets the best scores" on coherence/fluency.

## Implementation complexity (low/medium/high/very high + WHY)

**Very high** for a faithful reproduction; **high** even for an approximation. Reasons:

1. **Dead framework.** "We use Theano for implementation." Theano is discontinued/archived (the linked `github.com/Theano/Theano` repo is deprecated); the entire model must be re-implemented in PyTorch/TensorFlow, including the custom differentiable graph-attention layer.
2. **Non-standard differentiable graph layer.** Eq. 5 requires a **matrix inverse of an `(n+1)×(n+1)` matrix per decoding step** (`f_j = (1−λ)(I − λ W_j D_j^{-1})^{-1} y_T`), with `n` = number of sentences (D.L. ≈ 26–29.8 on average but long tails exist). This must be batched, kept numerically stable, and differentiated through — a non-trivial engineering effort (the paper does not describe how, e.g. batched inverses or iterative unrolling, were implemented).
3. **Hierarchical multi-layer RNN.** 3-layer LSTM word encoder + 3-layer LSTM word decoder + 1-layer sentence encoder + 1-layer sentence decoder, all at 512 hidden dims, with hierarchical state passing.
4. **Custom hierarchical beam search** coupling word-level K-best (K=15) and sentence-level N-best (N=2) search with a bigram-overlap reference term (γ=300) and a "refer to N different unused high-attention original sentences" rule.
5. **Entity-tagging pre/post-processing pipeline:** Stanford CoreNLP NER + `@entity <len>` prefixing + post-hoc OOV recovery by context matching — described only at a high level, no algorithm/pseudocode, no evaluation of its own.
6. **Compute:** 40k vocabulary, up to 200 epochs × 10,000 documents = ~2M document instances, at "about one day for every 30 epochs on a GTX-1080 GPU card" → roughly **6–7 GPU-days for DailyMail, ~4 GPU-days for CNN** per full run, before hyperparameter search (λ sweep over 11 values, γ sweep over 10 values, 200/300-epoch variants in Figure 2).
7. **No released code** to anchor the reimplementation, and several hyperparameters/preprocessing details are unspecified (see obstacles).

## Reproducibility obstacles (concrete)

- **No code or model release anywhere in the paper** (see availability section) — everything must be rebuilt from prose, equations, and one architecture figure.
- **Theano is a dead tool** (explicitly the implementation framework); the linked repo is deprecated. Any reproduction must port to a modern framework.
- **Entity-labeled corpora dependency.** "We use the corpora which are already provided with labeled entities (Nallapati et al., 2016)" — the paper gives **no URL** for this preprocessed variant. If that specific artifact is unavailable or differs, entity prefixing/OOV recovery changes and numbers shift.
- **Huge compute budget:** ~1 GPU-day per 30 epochs on a GTX-1080, 120–200 epochs per dataset, ×2 datasets, ×multiple λ/γ settings; plus multi-layer LSTMs with no mention of gradient clipping, dropout, or early-stopping criteria.
- **Unspecified hyperparameters:** Adamax learning rate/β1/β2/ε are deferred ("set to those provided in (Kingma and Ba, 2014)") rather than stated; LSTM weight initialization, dropout, gradient clipping, teacher-forcing schedule, and the entity-prefix vocabulary/tokenization are **not stated**. No random seeds, no number of runs, no variance/confidence intervals for ROUGE (only p-values from t-tests in Table 6).
- **Mixed ROUGE protocols across tables** (CNN full-length F1; DailyMail recall@75 bytes; merged full-length F1) — reproducing "the" number requires matching three different ROUGE configurations, and Table 4's 38.1 R-1 on the merged set is far above the same model's 30.3 on CNN and above the contemporaneous literature, so it is a risky single target.
- **Baseline numbers are quoted from other papers, not re-run** ("We first compare with the reported results in (Chen et al., 2016)"; Table 3 "the results of state-of-the-art neural summarization methods reported in recent papers"). Reproducing comparisons therefore compares against heterogeneous preprocessing/ROUGE settings; the authors only re-ran Distraction ("achieved by running the code provided by the authors on the DailyMail dataset").
- **Human evaluation is not reproducible:** 20 samples, 3 in-house participants (two named in the acknowledgments), no annotation guidelines/agreement statistics released; the annotators' identity makes the 3.93/3.82/3.53/3.80 scores effectively private.
- **Test-set-based hyperparameter selection:** Figure 2a/2b use "500 random samples from the DailyMail test set" for the λ and γ sweeps, so some of the reported tuning is test-informed.
- **Domain mismatch for this course:** the data is **English news (CNN/DailyMail)**; there is no Twitter or Weibo content, no Chinese/Arabic resources, no lexicon dependency, but also no direct social-media transferability evidence. Nothing about microblog-specific phenomena (hashtags, retweets, very short texts, noise) is addressed.
- Minor: Table 1/Figure 2/Table 4 text extraction artifacts in the PDF (e.g. "Rouge" vs "ROUGE", "p̃(y_τ)"), and the paper's Table 4 merged-set numbers are internally inconsistent in magnitude with its own CNN numbers.

## Minimum viable reproduction plan (what a student could realistically build in 2-4 weeks, what to substitute, what numbers to expect)

**Goal for 2–4 weeks: reproduce the *mechanism and the ablation trend*, not the headline numbers.** The paper's own most defensible, cheapest-to-verify claim is Table 6: graph attention > traditional attention (+1.1 R-1), and beam search matters a lot (+5.2 R-1). That is the target to aim at.

**Week 1 — data + extractive baselines.**
- Use the public HuggingFace `cnn_dailymail` (3.0.0) dataset instead of chasing the entity-labeled Nallapati artifact (substitute; note the deviation). Train on a **20k–50k document subset**, validate on 1–2k, test on the standard 1,093 CNN or 11,490/10,396 DailyMail test items (or a fixed 500-sample subset for cheap iteration, as the authors themselves did).
- Implement **Lead-3** and **LexRank/TextRank** (both trivial, no training). Target on CNN full-length F1: Lead-3 ≈ 26.1 R-1 / 9.6 R-2 / 17.8 R-L; TextRank ≈ 23.3/7.7/15.8; LexRank ≈ 26.1/9.6/17.7. If you hit roughly these, your preprocessing and ROUGE setup are right — this is the sanity check the paper gives you for free.
- Preprocess exactly as stated: lowercase, tokenize, digits → `#`, keep 40,000 most frequent words, rest `<OOV>`, `#` and `<eos>`/`<eod>` tokens.

**Week 2 — hierarchical seq2seq baseline (the "w/o GraphAtt" and "w/o BeamSearch" rows).**
- PyTorch, 1-layer LSTM encoder/decoder at 256 hidden (halve the paper's 512 and use 1 layer instead of 3 for the word-level RNNs — a stated compute substitution), GloVe 100d or `glove-wiki-gigaword-100` initialization, Adam with lr 1e-3 (Adamax hyperparameters are not stated; use Adamax α=0.002/β1=0.9/β2=0.999 as in Kingma & Ba's paper, and say so).
- Truncate documents to the first 20–30 sentences so `n` stays small. Greedy decoding first. Expect ROUGE-1 in the low 20s at best; the paper's "w/o BeamSearch" (greedy + reference) is 25.1/6.7/17.9 on CNN — treat ~22–26 R-1 as your realistic band, and expect to *under*-shoot because of the smaller data/1-layer substitution.

**Week 3 — the actual contribution: graph-based attention + reference beam search.**
- Implement Eq. 2/3 (`f = (1−λ)(I − λ W D^{-1})^{-1} y`) with `W(i,j) = h_i^T M h_j`, then the topic-sensitive version Eq. 5 by prepending the decoding state as the 0-th pseudo-sentence, then the distraction combination Eq. 6 with `f_0 = 1/n`. Use `torch.linalg.solve` / `torch.linalg.inv` on the batched `(n+1)×(n+1)` matrix; verify gradients flow (the paper asserts differentiability, so a finite-difference gradient check is a good mini-experiment in itself).
- Set λ = 0.9; keep the λ sweep over 0.1–0.99 as an optional cheap ablation (expect the paper's finding: larger λ is better, λ = 1.0 fails/singular).
- Implement the reference beam search: `score(y_τ) = p̃(y_τ) + γ(ref(Y_{τ−1}+y_τ, s*) − ref(Y_{τ−1}, s*))` with `ref` = bigram-overlap ratio, word beam 5–15, sentence beam 2. γ = 300 is the paper's value; **re-tune γ on your own validation set over a small grid (e.g. 0, 1, 10, 100, 300)** because your model is smaller — an extremely large γ makes the model "copy too much from the original document" and reduces fluency.
- Substitute **spaCy NER for Stanford CoreNLP**; either implement `@entity <len>` prefixing + context-based OOV recovery, or (simpler and defensible) skip entity prefixing and report it as an ablated feature. This is the least-specified part of the paper, so don't let it eat a week.

**Week 4 — evaluation + write-up.**
- Use the official `rouge`/`pyrouge`-style scorer with the exact configurations per table: full-length F1 for CNN comparisons, ROUGE recall at 75 bytes for DailyMail-style comparisons. Report both if cheap.
- Run the ablation: Our Method vs w/o GraphAtt vs w/o SentenceBeam vs w/o BeamSearch. **Success criterion: the same ordering and direction of gaps as Table 6** (graph attention > traditional attention; sentence beam > none; both beams ≫ greedy), even if absolute ROUGE is ~5–8 points below the paper.
- Expected outcome on a 20k–50k CNN subset with 1-layer 256-dim LSTMs: roughly **R-1 22–27, R-2 7–10, R-L 18–22** with graph attention + beam search; the graph-attention ablation gain should be on the order of **+0.5 to +1.5 R-1**. Reaching the paper's 30.3/9.8/20.0 or 38.1/13.9/34.0 is **not realistic** in 2–4 weeks on one GPU.
- Optional stretch: swap in a Chinese microblog corpus (e.g. LCSTS-style Weibo short-text summarization data) to align with the course topic — **not stated in the paper**, entirely a substitution; expect the graph-attention idea to transfer poorly to single-sentence/very short inputs, where the sentence graph has almost no vertices.

**Do NOT attempt:** training to 200 epochs on full DailyMail on a single GPU (that alone is ~6–7 GPU-days per run), reproducing Table 4's merged-set 38.1 R-1, or reproducing Table 5's human scores (20 samples, 3 named in-house annotators).

## Verdict (one paragraph)

This is a **strong paper but a poor-to-mediocre reproduction target for a 2–4 week course project, and a poor topical fit for a Twitter/Weibo course**. It is a well-cited ACL 2017 long paper with a genuinely interesting, clearly specified core idea — replace standard attention with a topic-sensitive PageRank score over the sentence graph, made differentiable and combined with a distraction term (Eqs. 2–6), plus a reference-augmented hierarchical beam search. The mechanism is implementable from the equations alone, the data (CNN/DailyMail via Hermann et al., 2015) is public, and the paper hands the reproducer two cheap sanity checks (Lead-3/TextRank/LexRank extractive baselines) and a clean ablation table. Against that: the authors release **no code and no data**, the implementation is in **Theano (dead)**, training is **~6–7 GPU-days for DailyMail on a GTX-1080**, several hyperparameters are unstated (Adamax details, initialization, dropout), the entity/OOV pipeline leans on an unlinked "entity-labeled" corpus variant and Stanford CoreNLP, the human evaluation is 20 samples scored by three named in-house annotators, and the headline numbers sit under three *different* ROUGE protocols (CNN full-length F1 = 30.3 R-1; DailyMail recall@75 bytes = 27.4; merged full-length F1 = 38.1) whose internal consistency is questionable. Worst of all for this course, **the paper is about English news documents and never mentions Twitter, Weibo, or social media** — a student hoping for a microblog-summarization reproduction gets an out-of-domain dataset and no social-media evidence, and would have to supply a Weibo/LCSTS corpus themselves, at which point the sentence-graph premise weakens. Best suited to a student with solid PyTorch seq2seq experience, a real GPU budget, and an appetite for re-implementing a non-standard differentiable graph layer, who is willing to target the **ablation trend (Table 6: graph attention 30.3 vs traditional 29.2 R-1; beam search 25.1 → 30.3)** rather than the paper's absolute numbers; for a student who wants a quick, on-topic Twitter/Weibo reproduction, a different paper would serve far better.
