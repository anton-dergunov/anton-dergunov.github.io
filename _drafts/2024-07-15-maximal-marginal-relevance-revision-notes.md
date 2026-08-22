---
title:     "Revision notes — Maximal Marginal Relevance"
published: false
---

# Revision notes: *Maximal Marginal Relevance*

**Target post:** `_posts/2024-07-15-maximal-marginal-relevance.md`
**Published:** 15 July 2024 · also on Medium at <https://medium.com/@adergunov/maximal-marginal-relevance-144c23b42be5>
**Notebook:** <https://github.com/anton-dergunov/blog-code/blob/main/2024-07-maximal-marginal-relevance/maximal_marginal_relevance.ipynb>
**Notes written:** 12 August 2026 · all model/paper facts verified on that date

This file is the working checklist for revising the post. Items are ordered by priority: P0 items are outright technical errors that are live on the internet under his name, P1 is the analytical insight that would make the post original, and the rest is expansion material.

**Do not change the permalink** (`/posts/2024/07/maximal-marginal-relevance`). Add an "Updated: &lt;date&gt;" line under the title. Every fix must also be applied to the **Medium cross-post**.

---

## Diagnosis

What the post does well, and what must survive any rewrite:

- It builds from a concrete problem rather than from a definition.
- The code runs and is short enough to read.
- The λ sweep (0.5 → 0.7 → 0.8) is exactly the right pedagogical move, and showing the λ=0.8 case where a duplicate pair comes *back* is genuinely instructive.
- It cites the 1998 primary sources (Carbonell & Goldstein; Goldstein & Carbonell) rather than a blog post about them. That is already above the median for this topic.
- The notebook contains a small unit-test suite for the MMR function. Keep it and extend it.

The problem, which matches his own read: **everything in the post is downstream of the LangChain how-to page.** There is no experiment, no failure analysis, no evaluation, and no position. It documents what a technique does. It never says what he thinks about it, when it breaks, or what he would ship. That is why the audience skewed to novices — it was written for them.

The gap to close is not "more content". It is **evidence and judgement**.

---

## P0 — Technical errors. These are live under his name; fix first.

### P0.1 The embedding function has a real bug: mean-pooling over padding

```python
inputs = tokenizer(text_list, return_tensors="pt", padding=True, truncation=True)
with torch.no_grad():
    outputs = model(**inputs)
embeddings = outputs.last_hidden_state.mean(dim=1)
```

`padding=True` pads every sequence to the length of the longest sequence **in the batch**. The mean is then taken across *all* positions, including every `[PAD]` token. Consequences:

- A short title is diluted by a dozen-plus pad vectors; a long one is barely diluted at all. The embedding becomes partly a function of **title length**.
- Because padding is to the batch maximum, the embedding of a document depends on **what else happened to be in the batch**. Re-batch the same corpus differently and the vectors change.
- In this post everything is embedded in one call, so the effect is systematic rather than random — but it is still wrong, and it is silently degrading every number in the article.

Correct implementation:

```python
def get_embeddings(text_list, model_name="sentence-transformers/all-MiniLM-L6-v2"):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    inputs = tokenizer(text_list, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        outputs = model(**inputs)
    mask = inputs["attention_mask"].unsqueeze(-1).float()
    embeddings = (outputs.last_hidden_state * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
    return torch.nn.functional.normalize(embeddings, p=2, dim=1).numpy()
```

Note the added L2 normalisation: with unit vectors, cosine similarity is a plain dot product, so the whole similarity matrix becomes one `E @ E.T` (see P0.4).

**Do not fix this silently.** This is the single most common mistake in hand-rolled embedding code, and writing it up — *"here is the bug I shipped, here is why the numbers looked strange, here is how to spot it"* — is worth more than the fix. It is exactly the experienced-engineer signal he is after, because only someone who has actually shipped embeddings has this scar.

### P0.2 `bert-base-uncased` is the wrong model, and the post's own numbers prove it

Raw BERT was never trained to produce sentence embeddings. Its representation space is strongly **anisotropic**: vectors occupy a narrow cone rather than spreading over the sphere, so *everything* is similar to *everything*. Mean-pooled BERT embeddings are commonly reported with mean pairwise cosine similarity around 0.99. Under those conditions cosine similarity loses most of its discriminative power.

The evidence is already in the published tables and the post never notices it:

- The top-7 similarity-ranked results span **0.6879 to 0.7104** — a range of **0.022** across seven supposedly differently-relevant documents.
- **"Python Tips for Mastering Data Science" scores 0.5159 against the query "London".** A document with no relationship whatsoever to the query sits at 73% of the top result's score. That is not a quirk of the toy dataset. That is the model telling you its geometry is degenerate.

Cite those two numbers directly in the rewrite. Using the post's own published output as the evidence for the post's own flaw is a strong move and costs nothing to produce.

**Fixes:**

- **Toy version:** `sentence-transformers/all-MiniLM-L6-v2`. Fast, tiny, runs on CPU anywhere, trained with a contrastive objective so the space is usable.
- **Serious version (verified Aug 2026):** `gemini-embedding-001` and Tencent's `KaLM-Embedding-Gemma3-12B` currently top the MMTEB multilingual board; `Qwen3-Embedding-8B` is the strongest widely-available open model; `BGE-M3` remains the practical open-source production default; `voyage-3-large` is the leading retrieval-tuned commercial option. **Report retrieval-specific nDCG@10, not the MTEB overall average** — a model that wins on classification can lose on retrieval, and retrieval is the only task that matters here. Re-check the leaderboard before publishing; this list ages in months.
- **Mention asymmetry.** Proper retrieval models expect an asymmetric setup — a query prefix and a document prefix (E5's `query:` / `passage:`, or the model's own instruction format). The post encodes the query and the documents identically, which is another silent quality loss and a mistake worth naming because almost every tutorial makes it.

### P0.3 A one-word query has no aspects to diversify over

"London" has no intent structure. There is nothing to *cover*, so "diversity" collapses into "spread out in embedding space", which is the least interesting version of the idea.

Diversification research is fundamentally about **ambiguous or multi-aspect queries** — "jaguar" (car / animal / OS), "python" (language / snake), "apple", or an informational query with several legitimate angles ("how do I treat a fever" → medication, when to see a doctor, children vs adults, home remedies). With a query like that, the correct behaviour is visible and checkable: did the result set cover the intents?

Pick one such query for the toy example. The demo becomes far more convincing, and it sets up the explicit-diversification material in P4 naturally.

### P0.4 Code quality issues that undermine the "engineer" signal

- `get_embeddings` reloads the tokenizer **and the model** on every call. Harmless here (called once) but it is the first thing a reviewer notices.
- The similarity matrix is built with a Python double loop calling a scalar `cosine_similarity`. With normalised embeddings this is one line: `similarities = embeddings @ embeddings.T`. O(n²) Python loops in a post about retrieval read badly.
- **Packing the query and the documents into one matrix is the real readability problem.** The `i+1` / `j+1` offsets (`similarities[i+1, j+1]`, `similarities[i+1, 0]`) make the implementation hard to check against the formula, and they are a bug factory. Split them:

  ```python
  sim_query = q_emb @ d_emb.T          # shape (n,)
  sim_docs  = d_emb @ d_emb.T          # shape (n, n)
  ```

  Then the MMR line reads exactly like the paper:

  ```python
  score[i] = lam * sim_query[i] - (1 - lam) * max(sim_docs[i, j] for j in selected)
  ```

- Typo: `quiery_and_documents` → `query_and_documents` (in both post and notebook).
- The notebook's `pip install transformers` / `pip install torch` cells should pin versions, or the notebook will stop reproducing.

### P0.5 A definitional imprecision worth correcting

The post says λ=0 "computes a maximal diversity ranking among documents in R". True but vague. With the **max**-over-selected penalty, greedy MMR at λ=0 is exactly **Gonzalez's farthest-point traversal** — the classic greedy 2-approximation for the k-center problem. Each step picks the candidate whose *nearest already-selected neighbour* is furthest away.

Naming it is more correct, more memorable, and it signals that he knows where this sits in the algorithms literature rather than only in the LangChain docs.

### P0.6 The first selection ignores λ — say so

Both the post's implementation and LangChain's pick the single most query-relevant document first, unconditionally. That is a **convention**, not something the formula requires: at step 1 the selected set is empty, so the `max` over it is undefined and the redundancy term vanishes. Implementations differ in how they handle this (some define the empty max as 0, some special-case step 1). It is a small point, but stating it is the kind of precision that distinguishes someone who implemented the algorithm from someone who called it.

---

## P1 — The insight that would make this post original: λ is scale-sensitive

**This is the most valuable single addition available, and it costs one paragraph plus one plot.** Almost no MMR write-up mentions it, and it explains the post's own results.

The objective is:

```
λ · Sim₁(Dᵢ, Q) − (1 − λ) · max_{Dⱼ ∈ S} Sim₂(Dᵢ, Dⱼ)
```

This linear interpolation is **only meaningful if Sim₁ and Sim₂ live on comparable scales.** They almost never do:

- Query–document similarity and document–document similarity have different distributions, because a query is short and a document is not, and because the query is a different kind of object.
- With an anisotropic space (P0.2), doc–doc similarities sit *higher and tighter* than query–doc similarities. The redundancy term therefore dominates at any moderate λ.

**This is why the post had to push λ to 0.7 to get sensible output.** The article presents 0.7 as the outcome of tuning. It is actually compensating for a broken embedding geometry. Notably, Elastic's own MMR guide also recommends starting around λ ≈ 0.7 — the same value, arrived at independently, which is itself a hint that everyone is compensating for the same unnamed problem.

The consequences to spell out:

1. **λ is not transferable.** A λ tuned on one embedding model, or one corpus, or one chunk size, is not valid on another. This explains why every blog and every vector-store default recommends a different value — they are all reporting a number fitted to their own similarity distributions.
2. **The fix is normalisation, and it is cheap.** Before combining, put both terms on the same footing:
   - **min–max** over the candidate pool (simple, but sensitive to outliers),
   - **z-score** over the candidate pool (better behaved),
   - **rank-based** — replace each raw score with its rank or reciprocal rank within the pool. This is the most robust option because it discards the scale entirely, and it connects directly to the rank-aggregation article already in the pipeline (`Work/Blog.org`: RRF and score fusion — the *same* problem of combining incomparable scores, solved the same way).
3. **Sim₁ and Sim₂ need not be the same function.** The original formulation explicitly allows them to differ; the post notes this in passing and then uses cosine for both "for simplicity". This is worth exploring rather than waving at: semantic near-duplicates and *lexical* near-duplicates are different phenomena. Cosine for relevance and something lexical (Jaccard over entities, character n-gram overlap, SimHash distance) for redundancy is often better in practice, because the thing you actually want to suppress is usually "this is the same story again", not "this is in the same topic".

**Experiment 2 below turns this into a measured result.** If only one experiment gets done, it should be this one.

---

## P2 — The intuition section (interview-proofing)

Motivation: he cited MMR in a job interview, was asked to explain it, and could recall the iterative idea but not the formula or the mechanism. The post should be written so that re-reading it for two minutes restores the whole thing. That also happens to be what makes a technical post re-readable in general.

Put a **TL;DR box at the very top of the post**, before the narrative, containing the formula and the one-sentence gloss.

### The one-sentence version

> Score each candidate as **how much it helps the query**, minus **how much it repeats what you have already picked** — where "repeats" means similarity to its *nearest* already-selected neighbour, not the average one. Pick the winner, add it to the set, recompute, repeat.

Mnemonic: **relevance minus your nearest twin.**

### The three things to anchor

**1. The `max` is load-bearing.** The redundancy penalty is the *maximum* similarity to the selected set, so a candidate is punished only by its single closest twin, and not at all by the rest of the set. If you used a **sum** or a **mean** instead, you would penalise a document for sitting in a dense region of the corpus — a different and usually worse behaviour, because it punishes documents for the company they keep rather than for being redundant. This choice is also precisely what separates MMR from DPP-style objectives, which score the *whole set's* volume rather than any pairwise maximum (see P4.2).

**2. It is greedy and incremental, so it is a re-ranker, not a retriever.** The choice at step *k* depends on steps 1..*k*−1, so it cannot be folded into an ANN index — there is no way to ask HNSW for "the 5 best *as a set*". This is why every vector store that offers MMR also exposes a **`fetch_k`**: retrieve 50 by pure similarity, then MMR down to 5. Two immediate implications worth stating: the candidate pool size is a real hyperparameter that nobody tunes, and it costs quadratically (you need the pool's pairwise similarity matrix).

**3. Both ends of λ are named algorithms.**
- **λ = 1** → plain relevance ranking. Sort by score.
- **λ = 0** → farthest-point traversal / greedy k-center (P0.5). Maximum spread, relevance ignored.
- **MMR is the straight-line interpolation between "sort by score" and "spread out maximally".**

### The caveat that makes it stick

End the section with P1: *the interpolation is only meaningful if the two similarity terms are on the same scale, and they usually are not.* That is the correct answer when an interviewer asks about weaknesses, and it is the thing most candidates — and most blog posts — miss entirely. Knowing the formula makes you competent; knowing why the formula is fragile makes you senior.

---

## P3 — When MMR is a bad idea (the biggest missing section)

The post is entirely positive about the technique. A section on failure modes is what most changes who the article reads as being written by.

1. **When redundancy is exact rather than semantic.** If the problem is literal duplicates — the same article syndicated to five sites, the same product listed twice, the same chunk indexed twice — **dedupe them**. URL canonicalisation, exact hashing, MinHash/SimHash for near-duplicates. It is O(n), deterministic, explainable, and it costs you no relevance at all. MMR is an expensive, fuzzy, relevance-sacrificing solution to a problem that frequently has a cheap exact one. *Reach for MMR only when the redundancy is genuinely semantic.*

2. **When you actually know the aspects.** If you have query facets, categories, or intent labels, **explicit** diversification (xQuAD, PM-2, IA-Select) beats MMR, and the IR literature is consistent on this — explicit methods outperform implicit MMR across all the standard measures. MMR is the method for when you *cannot* enumerate the aspects. Say that plainly; it is the correct scoping of the technique.

3. **After a cross-encoder reranker.** Reranker scores are calibrated and carry real information. The diversity term will cheerfully demote a 0.95 document below a 0.60 one. If diversification is needed post-rerank, apply it **only within bands of near-tied scores**, so it breaks ties rather than overriding the model.

4. **In RAG over chunks of a single document.** Chunks from one document are similar to each other *by construction*. MMR will scatter the context across many documents and destroy exactly the local coherence that multi-sentence reasoning needs. For "summarise the termination clause of this contract", MMR is not merely useless, it is **actively harmful**. This is the most common real-world misapplication and it deserves the most space.

5. **When it silently costs recall.** MMR lowers nDCG and recall@k almost by definition — that is what it is trading. If the downstream benefit is not being measured, you have traded a metric you can see for one you cannot. State the rule: *never deploy MMR without an end-to-end metric, because its cost is always visible and its benefit never is.*

6. **When λ was tuned somewhere else.** See P1. The failure is insidious: it works on the corpus you tuned on and quietly misbehaves on the next one, with no error and no alarm.

7. **Latency and cost.** O(k · |pool| · d) on top of retrieval, and it is inherently serial — you cannot parallelise across the k selection steps. Elastic explicitly recommends capping re-ranking depth for this reason. In a latency-budgeted search path this is a real constraint, not a footnote.

---

## P4 — Adjacent techniques and alternatives

### The reframing that makes the post land for a senior audience

> **Top-k is a set-selection problem, not a sorting problem.**

Ranking sorts items independently. The moment you care about *what the k results look like together*, you have left ranking and entered constrained set selection — and diversity is only one of several possible set-level objectives:

- **Diversity** — the items differ from each other.
- **Novelty** — the items are new *to this user*, relative to what they have already seen. Not the same as diversity within a list.
- **Serendipity** — relevant *and* unexpected.
- **Coverage / proportionality** — the set's aspect distribution matches the query's aspect distribution (this is PM-2's objective).
- **Calibration** — the list's genre/topic mix matches the user's historical mix (Steck, *Calibrated Recommendations*, RecSys 2018). Subtly different from diversity: a user who watches 70% documentaries should get 70% documentaries, not maximum spread.
- **Fairness / exposure** — of providers, authors, or demographic groups across the ranking.
- **Information gain** — total relevant information the set conveys (P4.1).
- **Budget** — the set must fit a token budget, a latency budget, or a screen.

### Direct alternatives to MMR, ranked by how much each would add

**P4.1 Dartboard / relevant information gain — the best foil.**
Pickett, Hartman, Bhowmick, Alam & Vempaty, *Better RAG using Relevant Information Gain*, [arXiv:2407.12101](https://arxiv.org/abs/2407.12101) (July 2024, revised February 2025).

The critique is precisely aimed: MMR treats relevance and diversity as **competing objectives** requiring a hand-tuned trade-off parameter, which creates an inherent tension. Dartboard instead optimises a **single** probabilistic objective — the total relevant information about the query contained in the retrieved set — and **diversity emerges as a byproduct, with no λ at all**. Evaluated as a drop-in replacement for the retrieval component of a RAG system on the RGB benchmark; reports state-of-the-art results, outperforming methods that optimise relevance and diversity directly.

This is the ideal foil for the rewritten post because it reframes the λ discussion from "here is a knob to tune" to "here is a design smell, and here is what removing it looks like."

**P4.2 Determinantal Point Processes.**
Chen, Zhang & Zhou, *Fast Greedy MAP Inference for DPP to Improve Recommendation Diversity*, [arXiv:1709.05135](https://arxiv.org/abs/1709.05135), NeurIPS 2018.

DPPs model diversity as the **volume** spanned by the selected item vectors — a determinant — which is a genuine set-level measure rather than a pairwise maximum. MAP inference is NP-hard, and the contribution that made DPPs production-viable is the fast greedy algorithm using incremental Cholesky updates, O(M³) and far faster than prior exact implementations. Their experiments report **DPP > MMR > MSD (max-sum dispersion) > no diversification** on the relevance-diversity trade-off across public datasets.

If the post wants one "and here is the better method, with a number" comparison, this is it. It is also the natural place to explain *why* the max-based penalty is a weaker model of diversity than a volume-based one.

**P4.3 Explicit diversification — the classical IR canon.**
- **IA-Select** — Agrawal et al., WSDM 2009. Maps queries and results onto a known category taxonomy and spreads results across categories.
- **xQuAD** — Santos, Macdonald & Ounis, WWW 2010. Generates sub-queries for candidate aspects and greedily picks results that improve aspect coverage. A variant was among the top performers in the TREC 2009 and 2010 diversity tasks.
- **PM-2** — Dang & Croft, SIGIR 2012. Proportionality: the result set should reflect the *distribution* of aspects, not merely cover them.
- **Gollapudi & Sharma**, WWW 2009 — an axiomatic framework for diversification, worth citing for the framing that diversification objectives can be characterised by which axioms they satisfy.
- **NTCIR INTENT task** — the Japanese counterpart to TREC diversity, which additionally required systems to *predict* the intents before diversifying.

The honest finding to report: **explicit methods beat implicit MMR when aspects are available.** MMR's niche is precisely the case where they are not.

**P4.4 Submodular maximization.**
Facility-location and coverage objectives are submodular, so greedy carries the classic **1 − 1/e** approximation guarantee (Lin & Bilmes, ACL 2011, for extractive summarization).

The subtle and worth-stating point: **MMR's objective is not submodular in general**, because of the max term — so greedy MMR has *no* approximation guarantee. This is why AdaGReS (below) has to establish only **ε-approximate** submodularity under practical embedding-similarity conditions in order to claim near-optimality for its greedy procedure. Getting this right in the post is a strong signal; getting it wrong is worse than not mentioning it, so verify the claim against the sources before writing.

**P4.5 AdaGReS — the 2025 answer to the λ problem.**
Peng, Wang, Long & Sheng, [arXiv:2512.25052](https://arxiv.org/abs/2512.25052) (December 2025).

Greedy context selection optimising a set-level objective combining query–chunk relevance with an intra-set redundancy penalty — i.e. MMR's shape — but with **instance-adaptive calibration** of the relevance/redundancy trade-off, eliminating manual tuning by adapting to the candidate pool's statistics and the token budget. Evaluated on Natural Questions and a deliberately high-redundancy biomedical drug corpus, measuring redundancy control, context quality, end-to-end answer quality and robustness.

This is the direct answer to the weakness the post should have identified, published by people who identified it. Citing it makes the post current.

**P4.6 Field collapsing — the boring production answer.**
Elasticsearch `collapse`, Solr result grouping, Vespa grouping: return at most one (or *n*) results per domain, per author, per product family. Cheap, exact, explainable, and **in practice this is what most production search actually ships instead of MMR.** Including it is a credibility move: it says he has thought about what actually goes to production rather than only about what is in papers.

### Related but distinct, worth a sentence each

- **Length diversity** — *Considering Length Diversity in Retrieval-Augmented Summarization* ([arXiv:2503.09249](https://arxiv.org/abs/2503.09249)), a reminder that "diverse" can mean dimensions other than topic.
- **DF-RAG** and similar 2025–2026 work extending MMR to dynamically balance relevance and diversity per query at test time.

---

## P5 — Where MMR actually runs in production

He asked specifically about production usage. This section is easy to write and disproportionately raises credibility, because it shows the technique's real footprint rather than its paper footprint.

- **LangChain** — `max_marginal_relevance_search` on the vector stores (with the `fetch_k` candidate-pool parameter), and `MaxMarginalRelevanceExampleSelector` for few-shot example selection. The post already links the implementation source; worth actually reading it and noting where it differs from the post's version.
- **LlamaIndex** — MMR-based node postprocessing.
- **Haystack** — a diversity ranker component.
- **Azure AI Search** — ships MMR for RAG scenarios.
- **Elastic** — published an [implementation guide](https://www.elastic.co/search-labs/blog/maximum-marginal-relevance-diversify-results) framing MMR for e-commerce discovery and RAG, recommending λ ≈ 0.7 as a starting point (see P1) and explicitly warning to limit re-ranking depth for latency. Note they give no latency benchmarks — an opening for him to publish some.
- **KeyBERT** — uses MMR so that extracted keyphrases are not near-synonyms of each other. [Documented as its own module.](https://maartengr.github.io/KeyBERT/api/mmr.html)
- **BERTopic** — offers MMR as a topic *representation* model, for the same reason: topic keywords should describe the topic's spread rather than cluster around its centroid.

KeyBERT and BERTopic are the least glamorous and most convincing citations available: MMR running quietly inside two widely-used libraries, doing a job nobody writes blog posts about.

### The scaled-up cousin: pretraining data selection

The strongest available bridge from a 1998 IR paper to frontier LLM work:

- **SemDeDup** — semantic deduplication via clustering in embedding space, removing documents that are near-duplicates in meaning rather than in text.
- **D4** — Tirumala, Simig, Aghajanyan & Morcos, *D4: Improving LLM Pretraining via Document De-Duplication and Diversification*, [arXiv:2308.12284](https://arxiv.org/abs/2308.12284). Combines SemDeDup with SSL-prototype-based selection to diversify the distribution locally and globally. Reports **18–20% efficiency gains** on validation perplexity and **~2% average 0-shot downstream accuracy** across 16 NLP tasks at the **6.7B** scale, with the largest gains when the source pool is roughly 4× the target size.

That is MMR's core intuition — *do not pay twice for the same information* — applied to trillions of tokens with measured results. The 1998 paper selected 7 documents for a human to read; the 2023 paper selects a pretraining corpus. Same objective, eight orders of magnitude apart.

### The closing idea — build post B around this

Once "select a set under a budget" is the frame, the same shape appears everywhere:

- RAG context assembly under a token budget
- Few-shot / in-context example selection
- Pretraining and instruction-tuning data curation (D4, SemDeDup)
- Active learning and coreset selection
- Diverse decoding — diverse beam search, and diversity in best-of-*n* sampling for test-time compute

And its **mirror image**, which is the genuinely interesting closing thought:

> **Self-consistency and Minimum Bayes Risk decoding pick the centroid. MMR picks the spread.**

Both are set-level procedures over a pool of candidates, and they want *opposite* things. For reasoning you want consensus — the answer most agreed upon — so you take the mode. For retrieval you want coverage — the answers that together span the space — so you take the spread. **When do you want the mode and when do you want the spread** is a real question with a clean answer (it depends on whether the candidates are competing hypotheses about one truth, or complementary pieces of one context), and it does not appear to have been written up anywhere.

---

## P6 — Better datasets

Ordered by effort. The current dataset is hand-written, synthetic, and constructed so the technique works — which a knowledgeable reader spots instantly.

1. **BEIR / MTEB retrieval subsets.** The standard, loadable via `datasets` in a few lines. Best picks:
   - **Quora** — duplicate-question pairs, so near-duplicates *are* the labelled ground truth. Ideal for showing precisely what MMR removes and whether it removes the right things.
   - **TREC-COVID** — multi-aspect biomedical queries, high redundancy.
   - **NFCorpus** — small, nutrition/medical, quick to iterate on.
   - **DBpedia-Entity** — entity ambiguity, so genuinely multi-intent queries.

   Using BEIR at all immediately signals familiarity with the field, and it makes results comparable to published numbers.

2. **TREC Web Track Diversity (ClueWeb09/09B, 2009–2012).** The *correct* dataset for this topic, because it ships **subtopic judgments**. That unlocks the field's actual metrics — **α-nDCG**, **ERR-IA**, **subtopic recall (S-recall)** — instead of eyeballing a table of seven titles. ClueWeb requires a data agreement, but the topics and qrels are public, and even reporting on a subset would put the post in a different category. This is the single change that moves it from "blog post" to "small study".

3. **RGB (Retrieval-Augmented Generation Benchmark).** Used by the Dartboard paper (P4.1), so their MMR baseline can be reproduced and extended directly.

4. **HotpotQA / MuSiQue.** Multi-hop QA, where answering genuinely requires *different* documents. This is what gives diversity a measurable downstream effect and enables Experiment 1.

5. **A real, messy corpus.** Wikipedia paragraph chunks, arXiv abstracts, or his own blog and notes. Real chunked documents exhibit the "chunks of the same document are similar by construction" pathology (P3.4), which is exactly the failure mode most worth demonstrating and which no synthetic dataset will reproduce.

### Metrics to report

- **Diversity side:** α-nDCG@k, ERR-IA@k, S-recall@k where subtopic labels exist; otherwise descriptive statistics (mean pairwise dissimilarity within the selected set, number of distinct source documents).
- **Cost side:** nDCG@k and recall@k — always, because MMR's cost lands here and reporting only the diversity side is how people fool themselves.
- **Downstream:** exact-match / F1 answer accuracy at a fixed token budget.

---

## P7 — The experiments

The post's current evidence is "look at these seven titles, they seem better." Replace it with measurements.

### Experiment 2 — λ scale-sensitivity (do this one first; it is the post's new backbone)

**Setup.** One corpus (a BEIR subset). Three embedding models: raw mean-pooled `bert-base-uncased` (the original, as a baseline and as the negative control), `all-MiniLM-L6-v2`, and one 2026 SOTA model.

**Measure.**
1. Plot the distributions of query–document and document–document cosine similarity for each model, on the same axes. The anisotropy of raw BERT will be immediately visible, and the plot alone is worth the post.
2. Sweep λ from 0 to 1 for each model and plot the resulting quality (α-nDCG or downstream accuracy).
3. Show that **the optimal λ moves substantially across models** — i.e. λ is not transferable, which explains the contradictory recommendations across the whole internet.
4. Repeat with rank-normalised / z-scored terms and show that the optimal λ becomes far more stable.

**Why this one.** It is cheap, it is entirely his own, it explains an observation everyone has made and nobody has diagnosed, it directly serves anyone shipping MMR, and it connects to the rank-aggregation work already in flight.

### Experiment 1 — does MMR actually help downstream?

**Setup.** Fixed token budget for the RAG context. Retrieve top-N candidates, select k by: (a) plain top-k, (b) MMR at several λ, (c) DPP greedy MAP, (d) Dartboard. Hold everything else constant.

**Measure.** Answer accuracy on HotpotQA and MuSiQue (multi-hop) *and* on a single-hop set such as Natural Questions, plus retrieval metrics on both.

**Prediction, stated in advance in the post:** **MMR helps on multi-hop and hurts on single-hop.** Multi-hop questions need genuinely different documents; single-hop questions need the one best document and its supporting neighbours, which MMR actively pushes away.

If that is what the data shows, it is a genuinely publishable blog finding and it explains why the advice online is so contradictory — people are reporting real results from different regimes without naming the regime. Registering the prediction before running it, and reporting it either way, is itself a credibility move.

### Experiment 3 — the padding-bug ablation

Same pipeline with and without the attention mask. Quantify how far the rankings move (rank correlation between the two orderings; change in the metrics). Turns the P0.1 bug into content and gives readers a way to detect it in their own code.

### Experiment 4 (optional) — asymmetric redundancy metrics

Test the P1.3 idea: cosine for relevance, but a lexical measure (Jaccard over entities, character n-gram overlap, SimHash distance) for redundancy. Hypothesis: the lexical redundancy metric suppresses "the same story again" better than the semantic one, at lower cost. Small, cheap, and nobody appears to have published it.

---

## P8 — Staged plan

Each stage ships something usable on its own.

- **Stage 0 — errata pass (1–2 hours).** Fix P0.1 (padding), P0.2 (model), P0.4 (code quality), P0.5, P0.6 in both the post and the notebook. Regenerate the tables with the corrected pipeline. Add an update note explaining the change. **Do this even if nothing else happens** — a live post with a known bug in it is a liability, and the fix is a small post in itself.
- **Stage 1 — intuition and failure modes (half a day, prose only).** Add the TL;DR box, the P2 intuition section, and the P3 "when not to use it" list. No experiments required. This alone changes who the post reads as being written by, and it directly solves the interview problem that prompted all of this.
- **Stage 2 — Experiment 2 (1–2 days).** The λ study on a BEIR subset, with plots. This becomes the post's spine.
- **Stage 3 — the comparison (2–3 days).** MMR vs DPP vs Dartboard vs plain top-k, with proper metrics. Probably the point at which the material outgrows one post.
- **Stage 4 — Experiment 1 (optional, several days).** The downstream RAG evaluation. The most work and the most interesting result.

### Split, do not grow

One post cannot carry all of this without becoming a survey, and surveys are the thing nobody finishes reading.

**Post A — "MMR, properly."** The corrected implementation, the intuition (P2), the failure modes (P3), and the λ scale-sensitivity study (P1 + Experiment 2). This is the evergreen reference and the natural home for the existing permalink and its accumulated traffic.

**Post B — "Beyond MMR: set-level selection for RAG."** DPP, Dartboard, AdaGReS, explicit diversification, the submodularity point, field collapsing, the pretraining-data-selection connection (D4/SemDeDup), and the mode-vs-spread closing idea. **This is the one to link from the CV and from LinkedIn** — it is the one that reads as written by someone who works in retrieval rather than someone who has read about it.

Keep post A's virtues from the original: the build-up from a concrete problem, runnable code, the λ sweep. Being concrete is why the original got read at all.

---

## P9 — Positioning: how to signal an experienced engineer

He asked for this explicitly. In order of effect:

1. **Report a negative result.** *"I expected MMR to help; on single-hop QA it did not — here is the data."* Nothing signals experience like publishing something that did not work. It is also the single hardest thing to fake.
2. **Name what everyone gets wrong, with evidence.** The λ scale mismatch (P1) and the padding bug (P0.1) both qualify, and both are demonstrable from his own published output. Diagnosing your own shipped mistake in public is a stronger signal than never having made it.
3. **Say what you would actually ship.** A recommendation *with conditions* is what seniority sounds like. Something like: *"In production I would deduplicate by hash first, use field collapsing wherever there is a natural grouping key, and reach for MMR only when I have no aspect labels and the redundancy is genuinely semantic — and I would not deploy it without an end-to-end metric, because its cost is always visible and its benefit never is."*
4. **Be precise about provenance.** Distinguish what he measured from what he read. The submodularity point (P4.4) in particular must be verified against the sources, not asserted.
5. **Date the fast-moving claims.** Embedding-model recommendations and leaderboard positions age in months. A dated line ("verified August 2026") is a small thing that reads as professional.

---

## Verify before publishing

1. **Actually run the corrected pipeline** and regenerate every table. Do not hand-edit numbers.
2. **Re-check the MTEB/MMTEB retrieval leaderboard** immediately before publishing; the P0.2 model list will have moved.
3. **Verify the submodularity claim** (P4.4) directly against Lin & Bilmes and the AdaGReS paper before stating that MMR's objective is not submodular.
4. **Read LangChain's MMR implementation** (already linked in the post's references) and confirm what it does differently from the post's version, particularly around normalisation and the first-selection step.
5. **Confirm the Dartboard and AdaGReS results** as described, from the papers rather than from abstracts.
6. **Update the Medium cross-post** with at least the Stage 0 fixes.

---

## Sources

- [Carbonell & Goldstein, *The use of MMR, diversity-based reranking...*, SIGIR 1998](https://dl.acm.org/doi/10.1145/290941.291025) · [Goldstein & Carbonell, TIPSTER 1998](https://aclanthology.org/X98-1025/) — already cited in the post; keep.
- [Pickett et al., *Better RAG using Relevant Information Gain* (Dartboard), arXiv:2407.12101](https://arxiv.org/abs/2407.12101)
- [Chen, Zhang & Zhou, *Fast Greedy MAP Inference for DPP*, arXiv:1709.05135, NeurIPS 2018](https://arxiv.org/abs/1709.05135)
- [Peng et al., *AdaGReS*, arXiv:2512.25052](https://arxiv.org/abs/2512.25052)
- [Tirumala et al., *D4: Improving LLM Pretraining via Document De-Duplication and Diversification*, arXiv:2308.12284](https://arxiv.org/abs/2308.12284)
- [Santos, Macdonald & Ounis, *Intent-Aware Search Result Diversification* (xQuAD)](http://terrierteam.dcs.gla.ac.uk/publications/santos2011sigir-a.pdf)
- [*Considering Length Diversity in Retrieval-Augmented Summarization*, arXiv:2503.09249](https://arxiv.org/abs/2503.09249)
- [Maximum Marginal Relevance & Elastic: Diversifying search results](https://www.elastic.co/search-labs/blog/maximum-marginal-relevance-diversify-results)
- [KeyBERT — MMR module](https://maartengr.github.io/KeyBERT/api/mmr.html) · [BERTopic — representation models](https://maartengr.github.io/BERTopic/getting_started/representation/representation.html)
- [Masking in pooling layer from BERT output — huggingface/transformers #8148](https://github.com/huggingface/transformers/issues/8148)
- [Ethayarajh, *How Contextual are Contextualized Word Representations?*, arXiv:1909.00512](https://arxiv.org/abs/1909.00512) — the anisotropy reference.
