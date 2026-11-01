---
post: _drafts/agent-memory/2199-01-01-agent-memory-8-experiment.md
type: experiment
status: draft
---

# Brief: The experiment: 67 changed facts (part 8)

Shared material is in `series.brief.md`. Source: `v1/2199-01-01-agent-memory-9-the-experiment.md` and Anton's 14 notes on it, `agent-memory-eval/docs/experiment.md`, `docs/experiment-results.md`, `docs/findings/*.md`, `docs/tasks/blog-post-plan.md` (dataset choice), `~/papers/notes/LongMemEval…md`.

## Reader

The series reader, who may not have read any system part. They want to know whether memory systems help, what they cost, and how to tell, and they will judge the experiment's fairness. The system descriptions here are one or two sentences each.

## The problem

Every memory paper reports beating the others, and when other groups re-run the same systems the numbers move by more than the claimed margins. A reader choosing a memory system cannot trust a single paper's ranking. This experiment runs every system on the same model, the same questions and the same judge, and records enough about each answer to say why it was wrong.

## What the reader should leave with

1. Published memory rankings mostly reflect each paper's setup (answer model, judge, retrieval budget, who ran it, a flawed benchmark).
2. On questions about changed facts, working memory systems land within a few points of each other and of reading the whole history. The large differences are in cost.
3. How a system is fed decided whether two systems remembered at all, and nothing reported an error.
4. Most wrong answers were lost at write time: the revision was mentioned in passing and never stored. Retrieval over raw turns cannot lose a fact that way.
5. To evaluate a memory system, read what it stored and what reached the answer, not only the score.

## Outline

| Section | Claim it supports | Evidence or artefact to show | Figure |
|---|---|---|---|
| Opening | The question (does what one conversation shows hold at scale, and at what cost); why it matters; what this part does; the repository link | Problem above; the running example in one sentence (version C) | none |
| Why not cite the published numbers | Rankings move by more than their margins between papers; four causes | The Mem0/MemOS/MIRIX table; Memanto (retrieval budget); SAGE (judge); the LoCoMo audit; copied baselines. LoCoMo explained at first use: what it is, why papers use it (Anton's note). "This experiment has no vendor" reworded: no system was run by the company that sells it, and none was tuned by its makers (Anton: "I am not a vendor"). | none |
| Choosing a dataset | What memory benchmarks exist, what each tests, and why LongMemEval's knowledge-update questions fit this question | A short table: LoCoMo (fits in context; answer-key errors; few revisions), LongMemEval, MemoryAgentBench, PersonaMem-v3 (non-commercial licence, so kept out), HaluMem, DMR (saturated). Facts about each from `~/papers/notes`. | none |
| LongMemEval, explained | Who made it and how: human-curated questions, evidence woven into task-oriented chats. Its five abilities and seven question types; why only knowledge-update (the scenario of the notebooks: a fact stated, then revised); the S, M and oracle versions and why S; why the cleaned release; what an abstention question is (false premise, the correct answer is "you never told me"), and why the 6 were dropped | `~/papers/notes/LongMemEval…md`; blog-post-plan.md; one example traced: the charity 5K, 27:12 then "my personal best time of 25:50", said in passing | `benchmark-types` (the paper's Fig. 1; CC BY 4.0, with credit, or redrawn) |
| How an answer is scored | An LLM judge with LongMemEval's own knowledge-update prompt, validated against human experts by the paper. Shown on one example: the prompt, an answer, the verdict. A second judge agreed on 130 of 132. | The judge prompt, quoted; one judged answer from results/ | none |
| Trimming the history | Why: all ~48 sessions cost about $2 per question, almost all of it Graphiti. What: 2 evidence sessions + 8 distractors, in date order. What trimming removes (retrieval difficulty, interference, headroom over full context), and why a 25-question full-history run exists. | v1 "The design" | `trimming` |
| The systems and the baselines | Each arm in one sentence: who writes, what is read. Why these two baselines: full context and retrieval over raw turns are what a memory system must beat. | v1 arms table | `map` (optional) |
| What was measured beyond accuracy | Probes read the whole memory after each history and the context given to the answer: was the new value stored, was the old one still stored and still current, did each reach the answer. Explained on one question (Anton: "explain better"). | One question's probe record | `probe-funnel` |
| Results | One chart, one paragraph: the band, the cost spread, the one configuration clearly below | results table (all runs) | `results` |
| 1. How a system is fed decides whether it remembers | Graphiti 18% → 82% and Letta 58% → 69%, by feeding alone; why each failed; neither API documents its contract, and nothing errors | v1 section 1 | none |
| 2. What memory looks like after an update | Each of the three readings in its own paragraph, explained more fully (Anton's note): almost nobody resolves the conflict at write time, and with dates it mostly does not matter; systems that overwrite keep less, not better; what reaches the prompt differs 360-fold, and a summary lost answers | v1 section 2 table | `probe-funnel` |
| 3. Error analysis: why the answers were wrong | Named as error analysis (Anton's note). Three flawed questions; most loss at write time (HaluMem agrees); one characteristic failure per system, each with its example; full context as the control | v1 section 3 table | none |
| 4. Telling the agent what to do | Letta's three persona lines quoted exactly, what each fixes, and the counts before and after, with the not-held-out caveat (Anton: "more details") | findings/letta.md | none |
| 5. The full history | Full context slips and does not collapse; the write cost of memory grows with the history; retrieval's does not; why the full-history run used only four systems | v1 section 4 | `answering` |
| What memory does not fix | Recall benchmarks miss over-personalisation and sycophancy (OP-Bench, PersonaMem-v3, MemSyco-Bench, HorizonBench), each in one sentence with what it measures | v1 | none |
| Where the headroom is | Write decisions are moving from prompts to trained or derived rules (Memory-R1, SAGE, DeMem, Belief Memory); what to forget has no training signal | v1 | none |
| A decision guide | Defaults by situation, no winner | v1 decision guide | `decision-guide` |
| Limits | Trimmed, one question type, one model, one run each, defaults; not comparable to published LongMemEval numbers | v1 Limits | none |
| How it was run / Reproducing it | Models and why; versions; about $110 in total; the results committed. "Costs nothing" reworded plainly; the sentence about raw calls dropped (Anton). | v1 | none |

## Running example

Version C: one sentence. The benchmark's own example (the 5K personal best) does the work here.

## Numbers

Every number in the results table has its four answers in v1: out of 67 questions, from our run, compared with full context and retrieval, and what it means. Rules for this part:

- Intervals beside every accuracy; "only large gaps mean anything" said once, early.
- At most about three numbers per paragraph. The tables carry the rest.
- "Not comparable to published LongMemEval results" stated where the numbers first appear.
- Check: the LongMemEval data licence (the paper says MIT) `[TODO: confirm on the repository]`.

## Figures to make

`benchmark-types`, `trimming`, `probe-funnel`, `decision-guide` (new). `results` and `answering` exist.

## Left out

- The sentence about raw model calls (Anton: drop).
- Per-system details of the mechanism (the system parts own them).
- Mastra's LongMemEval figures (part 9, labelled as the vendor's).

## Links

- Repository: https://github.com/anton-dergunov/agent-memory-eval (docs/experiment.md, docs/experiment-results.md, docs/findings/)
- Papers: LongMemEval, LoCoMo, MemoryAgentBench, HaluMem, DynamicMem, Memanto, SAGE, MemOS, MIRIX, OP-Bench, PersonaMem-v3, MemSyco-Bench, HorizonBench, Memory-R1, DeMem, Belief Memory; the Penfield Labs LoCoMo audit

## For search and for employers

- Title: "The experiment: 67 changed facts"
- Excerpt: "Five memory systems and two baselines on LongMemEval's changed-fact questions: accuracy, cost, and why every wrong answer was wrong."
- What this post shows: a fair, documented experiment with honest limits, full error analysis, and a decision guide.

## Anton's notes on v1, and where each is handled

| Note | Handled by |
|---|---|
| "Reword this… punchy" (costs nothing) | Reproducing it |
| "Either explain why, or don't write" (raw calls) | Dropped |
| "What is LoCoMo?…" | Explained at first use, and in the dataset table |
| "Rewrite. I am not a vendor" | Reworded |
| "Add context about it… what are others" (LongMemEval) | Choosing a dataset; LongMemEval, explained |
| "Say why versions" | S vs M vs oracle; cleaned release |
| "Value: explain better" | The statistics table gets a sentence per row, or becomes prose |
| "Show how exactly" (judge) | How an answer is scored |
| "What are they?" (abstention) | Explained |
| "Explain why" (whole history) | Trimming |
| "probes: explain better or later" | What was measured, on one question |
| "Three readings: explain each better" | Finding 2, a paragraph each |
| "Also say it is the error analysis" | Heading |
| "More details" (persona lines) | Finding 4 |

## Open questions for Anton

- Reuse the paper's Fig. 1 as an image (CC BY 4.0, credited), or redraw it in the series' style? Redrawing matches dark mode and Medium; reuse is faster.
