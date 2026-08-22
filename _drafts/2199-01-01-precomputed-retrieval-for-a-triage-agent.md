---
title:     "Can precomputed retrieval make a triage agent cheaper? Nine experiments"
date:      2199-01-01
permalink: /posts/2199/01/precomputed-retrieval-for-a-triage-agent/
tags:
  - machine-learning
  - information-retrieval
  - llm
  - agents
published: false
---

**Status: draft.** Third in a series. The first covers the Emacs planning setup; the
second covers using a coding agent to review and route those plans. This one is the
ML post: the retrieval experiments behind one feature of Info Triage, my personal
capture system.

Every number below comes from a run against my real notes. Where a result contradicts
what I expected, I have left the wrong expectation in, because that is the
interesting part.

---

## The problem

I capture links to a NAS. Once a day an agent reads the resulting inbox and files
each item into a 36-file Org planning repo, deciding for each one: is it worth
keeping, does it already exist somewhere, what task should it become, and which file
does it go in.

The expensive step is *does it already exist*. The agent has an item and no idea
where in the repo that item's neighbourhood lives, so it invents search vocabulary,
greps the whole repo, narrows, and reads whatever it hit. In one measured run over
six items it issued **17 repo-wide greps** with patterns like `watermark`,
`KV cache|kv-cache|prefill`, `distill|model stealing|reasoning trace`, then read one
850-line plan file at three separate offsets.

That is retrieval. Retrieval is a solved problem that does not need an agent loop. So
the hypothesis was: **precompute the neighbourhood on the server, hand the agent a
short list of `file:line` pointers, and the search disappears.**

It mostly did not work the way I expected, and understanding why was worth more than
the feature.

---

## The setup

Two corpora, both plain text on disk:

| corpus | unit | count |
|---|---|---|
| Org plans | heading + body, with ancestor breadcrumb | 2,902 tasks + 571 sections + 32 file charters |
| Obsidian vault | `##`/`###` section, windowed at 280 words | 4,472 |

**7,977 units, 561k words.** Small enough that exact cosine over everything is
microseconds — no approximate nearest neighbour index is needed or wanted, and I
want to flag that early because reaching for a vector database at this scale is a
common and expensive reflex.

Org structure is worth exploiting. A heading carrying a TODO keyword is a task; its
ancestors give a breadcrumb (`ML/Ranking.org > Recommender systems > Sequential and
generative recommendation`) that gets prepended to the indexed text. Vault notes get
`folder/note > section` the same way.

**Evaluation set: 22 queries.** Twelve real inbox items (all ML/LLM, which is a
limitation I will come back to), eight synthetic ones I wrote to span the rest of my
notes — photography, piano, Chinese vocabulary, vegan nutrition, tango musicality, ML
system-design interviews, A/B testing, Rust — and **two deliberate out-of-scope
controls**: restoring a 1960s Vespa engine, and beekeeping for beginners. The
controls exist because the failure I care about is not a missed match. It is a
confident wrong match, which costs the agent a wasted read and, as it turned out,
something worse.

---

## Experiment 1 — a bi-encoder cannot abstain

First attempt: embed everything with `intfloat/multilingual-e5-small` (118M, 384-dim,
multilingual because my notes contain Russian and Spanish), cosine against the item,
take the top few above a threshold.

Retrieval was fine. The **threshold** was the problem.

Across 116 returned hits the cosine distribution was: min **0.761**, max **0.932**,
mean **0.863**. The Vespa control — an item with genuinely nothing to match — scored
**0.83** against a job-search plan file. A real match on a photography item scored
**0.815**. There is no cut that separates them.

This is not a quirk of one model. Modern sentence encoders trained with contrastive
objectives compress everything into a narrow band of high cosine; the *ordering* is
informative and the *magnitude* is close to meaningless. If your design needs to
answer "is there anything relevant here at all?" — which any abstaining retriever
does — a bi-encoder score alone will not tell you.

**Learning: ranking and calibration are different problems. Do not ask a bi-encoder
for the second one.**

---

## Experiment 2 — the cross-encoder, and two bugs that looked like model failures

The standard fix is a reranking stage: a cross-encoder that sees query and candidate
*together* and produces a relevance score. I used `BAAI/bge-reranker-base` (278M,
XLM-RoBERTa, multilingual) over the top 40 candidates.

It worked immediately on the controls, and then produced two failures that I initially
read as "the model is bad".

**Failure A: score saturation on long queries.** My query was the item's title plus
its `intent` plus the first 120 words of the extracted lead. On 5 of 12 real items the
reranker returned probability **1.00 for every single candidate in the pool** —
including obvious junk. A watermarking post scored 1.00 against a task about building
a session analyser for agent transcripts, and 1.00 against a note on multiple-comparison
corrections.

The cause is structural, not a defect. A long, multi-topic query mentions enough
concepts that *something* in every candidate matches *something* in the query, and the
cross-encoder's job is to say whether the pair is relevant, not which parts. Feed it
a paragraph and everything is relevant.

The fix was to **decouple the two queries**: recall uses the long text (good for
coverage), reranking uses a short one — title plus first sentence, ~28 words. That
restored the ordering completely.

**Failure B: the sigmoid.** With short queries the scores stopped saturating at 1.0
and started clustering near 0.0 instead: correct top hits at 0.01–0.32, controls at
0.00–0.01. Same problem, other end.

`bge-reranker` outputs a logit that the library passes through a sigmoid by default.
Sigmoid is monotonic, so ranking is unaffected — but it destroys exactly the
information a threshold needs, because it squashes the entire "model is unsure" region
into a few thousandths. Taking the **raw logit** instead gave a usable spread:

| item | top-1 logit | verdict |
|---|---|---|
| A/B peeking (synthetic) | **+3.91** | correct |
| Pinterest recsys scaling | +1.44 | correct |
| Soy/protein (synthetic) | +0.91 | correct |
| KV-cache transfer paper | −0.76 | correct |
| Rust ownership (synthetic) | −1.11 | correct |
| Beekeeping **(control)** | **−8.45** | correctly nothing |
| Vespa restoration **(control)** | −4.48 | correctly nothing |

**Learning: two of my three "model quality" problems were input formatting and an
output activation. Check the plumbing before changing the model.**

---

## Experiment 3 — precision@k, and why k=2

Hand-judged, plan-side, 20 in-scope queries:

- **Precision@1: 15/20 exactly right**, 3 more landing in the correct file on a
  neighbouring task, 2 outright wrong.
- **Precision@3: roughly 40%.**

The exact hits are the ones that justify the feature, because they are the cross-file
cases a single grep would not find. A paper on cross-model KV cache transfer returned
*both* `ML/Generative_AI.org:48` ("KV cache as an architectural constraint") **and**
`ML/Systems.org:324` ("Prefill-decode disaggregation and KV cache transfer between
instances") — two different files, both correct. A synthetic A/B-testing item returned
four correct matches across four files.

The wrong ones are instructive too. A paper titled *GitSkills: A Dataset of Agent
Skills on GitHub* matched a task about `git bisect` — pure lexical bleed on the token
"git", which the reranker failed to veto.

The steep drop from ~75% at k=1 to ~40% at k=3 is the whole argument for a small k.
Each additional row costs the agent a verification read, and — as the next experiments
show — carries a cost I had not anticipated at all. **Two rows per corpus, not five.**

At an abstain cut of logit ≥ −3: 16 of 20 in-scope items get a pointer, both controls
emit nothing, and about 88% of emitted rows are correct.

One honest caveat on the threshold. The correct match for a retail semantic-search
item scored **−5.16**, *below* the Vespa control's **−4.48**. A single global cut
cannot separate a weak-but-correct hit from a confident-but-irrelevant one. I chose
the conservative side: a missed pointer costs nothing, a wrong one costs trust.

---

## Experiment 4 — the ablation that deleted the embedding model

Late in the process I ran the obvious control I should have run first: **how much is
the embedding actually contributing?** I labelled a single gold unit per query and
scored each retrieval mode alone.

| mode | hit@1 | hit@5 | hit@40 (the rerank pool) |
|---|---|---|---|
| BM25 over the item's full text | 4/15 | 8/15 | **15/15** |
| BM25 over title only | 4/15 | 8/15 | 14/15 |
| dense (`multilingual-e5-small`) | 2/15 | 8/15 | 12/15 |

**BM25 alone puts every gold answer into the top 40, which is all the reranker needs.**
The embedding misses three outright and ranks two of them **448th** and **537th**.

Those two failures are worth naming: an item about semantic search at a large retailer,
and one about scaling recommendation models. Both are cases where my notes and the item
share the *vocabulary* but not the *phrasing* — and the dense model, which is supposed
to be good at exactly that, was catastrophically worse than term matching.

Dense does win where vocabulary genuinely diverges (a Raschka repo item: rank 4 against
BM25's 20; an Anki/HSK item: 2 against 13), so hybrid retrieval still has the best
recall. But the margin does not justify the infrastructure: dropping the embedding
removes a model, a vector index, an index-transfer step and a rebuild job, taking peak
memory from 1.47 GB to ~600 MB and index build from 3.2 minutes to under a second of
pure Python.

Why does lexical do so well here? Because the corpus is jargon-dense and the query and
documents are written by the same person about the same fields. "KV cache",
"watermarking", "peeking", "ownership", "Anki" — these are rare, discriminative tokens
and IDF handles them beautifully. The general lesson everyone repeats is that embeddings
beat BM25; the specific lesson is that on a small, personal, high-jargon corpus they may
not, and it costs one afternoon to find out.

One distinction this does *not* license: "grep is good enough." The agent's greps are
one to three **guessed** terms. This is IDF-weighted BM25 over the whole item text.
Different instrument.

**Learning: run the no-ML baseline first. I ran it eighth.**

---

## Experiment 5 — the A/B, in which the hypothesis fails

Now the actual question: does handing the agent these pointers make it cheaper? Same
six real inbox items, same skill, same model, only the injected section differs.

| variant | tokens | cost | turns | wall clock |
|---|---|---|---|---|
| no section (control) | 997,415 | $1.0237 | 33 | 225 s |
| `## Related` | **1,010,462 (+1.3%)** | $1.0103 | 26 | 193 s |

**The feature made it slightly more expensive.** Turns fell 21% and wall clock 14%,
but tokens did not move.

The reason is visible once you look at where tokens go (Experiment 6): the bill is
dominated by context re-read on every turn, and grep results are small next to the
accumulated transcript. Removing fifteen greps is noise.

And then the part I did not predict at all. **The verdicts changed:**

| variant | decisions on the six items |
|---|---|
| control | 5 new tasks, 1 merge |
| `## Related` | **6 merges — every single item** |

On the two items where both runs found the *same* neighbouring line, they reached
**opposite** conclusions about whether that neighbour absorbs the item or sits beside
it. The control also ran a source-quality check the treatment skipped entirely: it
opened each LinkedIn post looking for a primary paper link, found none, and marked
three tasks `unverified` rather than passing along paraphrased benchmark numbers.

Being handed a plausible existing home converts the question *"is this new?"* into
*"where does this fit?"*. The retrieval was mostly right; the framing was the damage.

### The fix was prose, not code

I changed nothing about the rows. I changed the heading and added six lines of caveat:

> **Possible neighbours — unverified.** Machine retrieval, not a finding. These are the
> nearest passages a search found; roughly one in eight is wrong, and a hit here is
> *not* evidence the item is a duplicate. Judge quality first and on the item's own
> merits, then open these to check whether they actually cover it. An item with a
> neighbour is as likely to need a new task beside it as a merge into it.

| variant | tokens | cost | turns | verdicts |
|---|---|---|---|---|
| control | 997,415 | $1.0237 | 33 | 5 new, 1 merge |
| `## Related` | 1,010,462 | $1.0103 | 26 | 6 merge |
| **hedged wording** | **843,168 (−15.5%)** | $0.9445 | 24 | 4 merge, 2 new |

Same rows, same model. **−15.5% tokens and correct mixed verdicts, from a paragraph of
hedging.** It also got the contested case right and explained itself:

> **NEW task** → `ML/Systems.org`, sibling to line 324. This paper is a different
> mechanism — cross-*model* transfer … not cross-instance transfer of the same model —
> so it earns its own TODO rather than folding into 324.

That matches the file: line 324 is a one-liner among uniform one-liner siblings, and
folding a specific paper into it would break the section's granularity.

**Learning: an epistemic label on retrieved evidence is not documentation. It is a
parameter of the system, and it moved both cost and correctness more than any model
choice I made.**

Adding one more line — the *file* of the top-ranked neighbour, as a destination hint —
took it further: **696,545 tokens, −30.2% against the control.**

---

## Experiment 6 — where the tokens actually go

Worth measuring before optimising anything, and I did it too late.

**Turn one costs 49,000 tokens before a single note is read.** Context grows to ~98k by
the end of a six-item run. Across 45 billed assistant messages the fixed preamble is
roughly **68% of all context read**.

The editable share of that 49k is small:

| | tokens |
|---|---|
| repo instruction file | ~5,100 |
| shared skill definitions | ~2,500 |
| the skill itself | ~1,900 |
| generated conventions file | ~1,900 |
| **total editable** | **~11,400** |
| system prompt + tool definitions | ~37,000 (not mine to change) |

So trimming my own instruction files caps out at maybe 5–8% of the bill. **Splitting the
notes into smaller files would not help at all** — they are read in bounded chunks
already, and a line-anchored pointer is what prevents the "read one file at three
offsets" pattern.

Cost is `turns × context`, and context grows ~8k per item. That makes it **superlinear
in batch size**: roughly `T·fixed + growth·T²/2`. Fitting the measured constants and
minimising over batch size for 12 items:

| items per session | sessions | modelled total |
|---|---|---|
| 12 | 1 | 6.25M |
| 6 | 2 | 5.04M |
| 4 | 3 | 4.79M |
| **3** | **4** | **4.76M** |
| 2 | 6 | 4.94M |
| 1 | 12 | 5.97M |

Flat between 3 and 6, rising sharply above 8. **One large batch is the worst available
option**, which is the opposite of the intuition that batching amortises setup. Setup is
paid per *turn*, not per session, and total turns barely change.

---

## Experiment 7 — Sonnet vs Opus, where I was wrong by 3x

I assumed the stronger model would cost ~5x and be reserved for hard cases. Same input,
same six items, hedged wording plus destination hint:

| model | tokens | cost | turns |
|---|---|---|---|
| Sonnet | 696,545 | $0.8625 | 23 |
| **Opus** | **600,912** | $1.3894 | 24 |

**Opus used 14% fewer tokens**, making the real cost ratio **1.61x**, not 5x. It read
less, and said why: *"items 1 and 3 have complete abstracts and needed no Read"* — using
a metadata field my format provides for exactly that purpose, which Sonnet ignored.

The quality gap was larger than the price gap. On an item about product search at
200M-item scale:

- **Sonnet:** "ADD new task after line 150."
- **Opus:** identified that **four existing tasks already cover most of the post**
  (hard-negative mining, false-negative denoising, cross-batch negatives,
  cross-encoder distillation) and isolated the single genuinely uncovered idea —
  legacy-aware distillation warm-start when swapping a production backbone, because
  the new model discards years of mined hard negatives.

That is precisely the job the duplicate check exists to do, and only one of the two
models did it. Opus also **rejected my destination hint and explained why** — *"the
`Generative_AI.org:48` neighbour is the wrong file: this is operational, not
architectural"* — which is the ideal relationship between an agent and a retrieved
suggestion, and the exact opposite of the anchoring in Experiment 5.

**Learning: per-token price is not cost. A model that reads less can be cheaper in
absolute terms while being better, and the anchoring failure I attributed to the
feature was partly a property of the weaker model.**

---

## Experiment 8 — does it survive a 10x corpus?

My vault should grow by an order of magnitude; the plans should not. I subsampled the
vault to 10/25/50/100% — a 10x span — holding the plans fixed.

| vault | Org-side gold | vault-side gold |
|---|---|---|
| 10% | hit@5 11/15, **hit@40 15/15** | hit@5 6/6, hit@40 6/6 |
| 25% | hit@5 11/15, **hit@40 15/15** | hit@5 6/6, hit@40 6/6 |
| 50% | hit@5 11/15, **hit@40 15/15** | hit@5 5/6, hit@40 6/6 |
| 100% | hit@5 9/15, **hit@40 15/15** | hit@5 5/6, hit@40 6/6 |

**hit@40 does not move at all.** Since the top-40 pool is what the reranker consumes,
final quality is unaffected; only top-5 ordering drifts.

But the Org-side drift from 11/15 to 9/15 bothered me, because *the Org corpus never
changed*. It turned out to be an artifact of sharing one BM25 index between the two
corpora: adding vault documents changes the global IDF and average document length,
which silently reweights Org scoring. Giving each corpus **its own index** made Org-side
quality exactly invariant — 11/15 and hit@40 15/15 at every vault size.

**Learning: BM25's statistics are global. Mixing two corpora with different growth rates
into one index couples them in a way that looks like model drift and is really
bookkeeping.**

---

## Experiment 9 — the destination hint that failed

Each plan file opens with a charter: prose stating what belongs in it. Obvious idea:
rerank the item against the 32 charters to pick a destination file. That is the same
evidence a human would use.

It scored roughly **7/20**. Rust ownership → the personal-finance file. Photography →
the data-and-backups file. Chinese vocabulary → the software-engineering file.

Charters are short and abstract ("Search, information retrieval, recommendations,
ranking and ads"); paper titles are long and concrete. A cross-encoder has nothing to
latch onto, and the file with the longest, most general charter absorbs everything.

The version that works needs no extra computation at all: **take the file of the
top-ranked neighbour.** Task-level precision@1 was 15/20, but file-level was 18/20 —
**~90%** — because the two errors still landed in the right file. Coarser labels are
easier, and the coarse label was the one I actually needed.

**Learning: when a direct approach fails, check whether the answer is already a
projection of something you have.**

---

## What I would tell someone building this

1. **Run the lexical baseline first.** On a small personal corpus of technical notes,
   BM25 was better than a modern multilingual embedding model at getting the right
   answer into the candidate pool — 15/15 against 12/15 — and it removed an entire
   model, index and rebuild job from the design.
2. **Use a cross-encoder for the abstain decision**, not the retriever's score. And
   read raw logits, not the squashed probability.
3. **Keep the rerank query short even when the retrieval query is long.** They optimise
   different things and a long rerank query saturates.
4. **Emit few rows.** Precision fell from ~75% at k=1 to ~40% at k=3. Rows past the
   second cost verification work and invite anchoring.
5. **Label retrieved evidence as unverified, in prose, in the artifact.** This was worth
   −15.5% tokens and the difference between six wrong merges and a correct mixed
   verdict set. It is the highest-leverage change in the whole project and it is
   writing, not engineering.
6. **Measure token anatomy before optimising.** 68% of my bill was fixed preamble, so
   the search I was trying to eliminate was never the expensive part.
7. **Price the strong model by total cost, not per token.** Opus read less and came out
   at 1.6x, not 5x, for visibly better judgement on a judgement task.

### What I have not shown

Every A/B here is **n=1 per condition**. The verdict patterns are stark enough to
trust — 6 merges out of 6 is not run-to-run noise — but the token percentages are
single samples and should be repeated before anyone quotes them, including me.

The evaluation is 22 hand-judged queries on one person's notes, and the twelve real
items are all ML/LLM, which is exactly the region where my plan files are densest. The
eight synthetic queries exist to probe the rest, but I wrote them, so they are friendlier
than real captures would be.

I never measured recall properly. `hit@k` against one hand-picked gold unit per query
answers "did a useful pointer surface", which is the operational question, but it is not
recall — that would need exhaustive relevance labels over all 7,977 units.

And the growth simulation subsamples downward and reads the trend upward. It shows the
design is insensitive to distractor *count*. It cannot show what happens if the vault
grows in a way that changes its *character*.
