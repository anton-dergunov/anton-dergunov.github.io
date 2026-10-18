---
title:     "How LLM agents remember, part 9: 67 changed facts, nine configurations"
topic:     llms-and-agents
date:      2199-01-01
permalink: /posts/2199/01/agent-memory-9-the-experiment/
tags:
  - llm
  - agents
  - memory
  - evaluation
published: false
---

<!-- SERIES -->

*How LLM agents remember*, a series in nine parts:

1. [One conversation, five memory systems](/posts/2199/01/agent-memory-1-why/)
2. [A map of memory systems](/posts/2199/01/agent-memory-2-the-map/)
3. [What ChatGPT, Claude and Gemini ship](/posts/2199/01/agent-memory-3-frontier-assistants/)
4. [Textual memory: one profile, rewritten](/posts/2199/01/agent-memory-4-textual-memory/)
5. [Mem0: facts in a vector store](/posts/2199/01/agent-memory-5-mem0/)
6. [Zep and Graphiti: facts with dates, in a graph](/posts/2199/01/agent-memory-6-graphiti/)
7. [Letta: an agent that edits its own memory](/posts/2199/01/agent-memory-7-letta/)
8. [Honcho: a reasoner that works in the background](/posts/2199/01/agent-memory-8-honcho/)
9. **The experiment: 67 changed facts** (this part)

<!-- /SERIES -->

Parts [4](/posts/2199/01/agent-memory-4-textual-memory/) to
[8](/posts/2199/01/agent-memory-8-honcho/) ran one hand-written conversation,
in which a user changes their diet, through five memory systems with every
model call shown. One conversation shows mechanisms; it cannot show how often
they matter. This part checks the same behaviour on a public benchmark, with
the real systems, and with the two baselines from
[part 2](/posts/2199/01/agent-memory-2-the-map/) in the first rows: the whole
history in the prompt, and plain search over the raw turns.

## Why not just cite the published numbers

Every memory-system paper reports beating the others, usually on LoCoMo. When
other groups re-run the same systems, the numbers move by more than the
margins being claimed:

| Reported in | Answer model | Mem0 | Zep |
|---|---|--:|--:|
| [Mem0][mem0] (p. 11, Table 2) | gpt-4o-mini | 66.88 | 65.99 |
| [MemOS][memos] (p. 23, Table 3) | gpt-4o-mini | 64.57 | 59.22 |
| [MIRIX][mirix] (p. 11, Table 2) | gpt-4.1-mini | 62.47 | 79.09 |

The same Zep is six points below Mem0 in one paper and seventeen above it in
another. Four causes recur.

- **Configuration.** The answer model, the judge and the number of items
  retrieved differ from paper to paper, and each can swing a result. In
  [Memanto][memanto], raising the number of retrieved items from 10 to 40 adds
  20.4 points on LongMemEval (p. 8). In [SAGE][sage], a small judge model gives
  scores of 85–98 to answers whose word overlap with the reference is 5–15
  (p. 6, Table 1).
- **Who ran it.** Mem0, Zep, MemOS and MIRIX were each evaluated by the
  company that sells them.
- **The benchmarks.** An [audit of LoCoMo][penfield] found 6.4% of its answer
  key wrong, and its judge accepted 62.81% of answers written to be wrong but
  on topic. MemGPT's own benchmark is saturated: a plain full-conversation
  baseline scores 94.4% against 93.4% for MemGPT ([Zep][zep], p. 6, Table 1).
- **Copied baselines.** Some papers report a competitor's own published
  numbers as if they had re-run it.

So a single paper's ranking is evidence about its setup more than about the
systems. The 2026 benchmarks run by third parties
([MemoryAgentBench][memoryagentbench], [EvoMemBench][evomembench],
[AgentMemBench][agentmembench]) find, in different ways, that a plain long
context often matches the memory systems. What memory reliably buys there is
cost.

This experiment has no vendor. It runs every system on the same model and the
same questions, with the same judge, and it records enough about each answer
to say why it was wrong.

## The data: LongMemEval's knowledge-update questions

[LongMemEval][longmemeval] has 500 questions, each with its own chat history
between one user and an assistant, and each labelled with the sessions that
hold the evidence. The 78 *knowledge-update* questions are the ones where the
user states a fact and later revises it, which is the scenario the notebooks
are built on. On the standard *S* version, measured on the cleaned release:

| | Value |
|---|---|
| Sessions per question | 48 on average (38 to 62) |
| Turns per session | about 10 |
| Tokens per question | about 122,000 |
| Share of tokens in the user's turns | 13% |
| Evidence sessions, knowledge-update | exactly 2, in all 78 questions |
| Days between the two evidence sessions | median 40 |

An example: "What was my personal best time in the charity 5K run?" The first
evidence session says 27:12. The second says, in passing, "By the way, I'm
hoping to beat my personal best time of 25:50 this time around." The answer
is 25:50. Updates are often this incidental, and that is what makes them hard
to extract. The other sessions are distractors by construction: half are
unrelated public chats, half are simulated sessions about the same user's
other attributes.

Answers are scored by an LLM judge with a prompt per question type, which the
paper validated against human experts at more than 97% agreement. It is
a real accuracy, not a rubric score.

## The design

**Questions.** The 78 knowledge-update questions minus 6 abstention questions
leave 72. Five went to a pilot, used for checking the pipeline and for no
reported number; the other 67 are the main run.

**History.** Running all ~48 sessions through every system would have cost
about $2 per question, almost all of it Graphiti. So the main run trims each
history to its two evidence sessions plus 8 distractors sampled with a fixed
seed, kept in date order with their timestamps: about 28,000 tokens per
question. Then 25 of the 67 were run again with the whole history, about
124,000 tokens, for the four systems cheap enough to afford it.

Trimming keeps the evidence and removes three things, and the results should
be read with them in mind. It removes retrieval difficulty: searching 10
sessions is far easier than searching 48. It removes interference at write
time: fewer unrelated memories, fewer wrong merges. And it removes most of the
headroom over the baseline: at 28,000 tokens, reading the whole history is
close to its ceiling. The main run therefore tests the write path and conflict
resolution, mostly not the read path, in the regime where memory is not needed
for capacity. Any loss there is the price of the memory layer.

**Models.** One model in every seat, `gemini-3.1-flash-lite`: every model call
inside every system, and every answer. `gemini-embedding-001` for every
embedding. The judge is `gemini-3.1-pro-preview` with LongMemEval's own
knowledge-update prompt; a second judge, `gemini-3.8-flash`, agreed on 130 of
132 answers judged by both.

**Systems**, each at its library defaults unless noted, and each fed the
session dates:

| Arm | Who writes | What runs | Read path |
|---|---|---|---|
| full context | nobody | the whole trimmed history in the prompt | everything |
| retrieval | nobody | BM25 over rounds (a user message and the reply after it) | top 10 rounds, with dates |
| textual memory | a rewrite call after each session | about 50 lines of my code, after PersonaMem-v3 | the whole profile |
| Mem0 | an extraction pipeline | mem0ai 2.2.1 | `search()` defaults |
| Honcho, chat | a background reasoner | Honcho v3.3.0, self-hosted | the dialectic agent |
| Honcho, repr | the same store | the same server | dated conclusions, no model call |
| Graphiti | a pipeline into a dated graph | graphiti-core 0.31.1 on Neo4j | `search()` defaults |
| Letta | the answering agent | Letta 0.16.8, self-hosted | the agent answers itself |

**Measures.** Beyond accuracy, probes read the whole memory after each history
and the context given to the answer, and record whether the new value was
stored, whether the old value was still stored and still presented as
current, and whether each reached the answer. A fact can be written correctly
and still never reach the answering model, and one "recall" number hides
which of the two failed. Cost is taken from a ledger of every call each
system made.

With 67 yes/no questions, the 95% interval on each score is about ±8 to ±12
points. Only large gaps mean anything.

## The results, every variant in one table

Graphiti and Letta were each run more than once, for reasons the next section
explains. All runs are here, the baselines first.

| Arm | Accuracy (n = 67) | 95% interval | USD per question | model calls to write | seconds to write | servers |
|---|--:|---|--:|--:|--:|---|
| full context | 90% | 80–95% | 0.007 | 0 | 0 | none |
| retrieval (BM25, top 10 rounds) | **97%** | 90–99% | **0.002** | 0 | 0 | none |
| textual memory | 93% | 84–97% | 0.022 | 10 | 27 | none |
| Mem0 | 84% | 73–91% | 0.040 | 10 | 38 | none (local files) |
| Honcho, dialectic chat | 87% | 76–93% | 0.029 | 38 | 115 | API, deriver, Postgres, Redis |
| Honcho, representation | 93% | 84–97% | 0.028 | 38 | 115 | the same |
| Graphiti, 8,000-character episodes | 18% | 11–29% | 0.238 | 121 | 145 | Neo4j |
| Graphiti, one episode per message | 82% | 71–89% | 0.640 | 720 | 839 | Neo4j |
| Letta, a whole session per request | 58% | 46–69% | 0.029 | 11 | 43 | Letta server, Postgres |
| Letta, one step per user message | 69% | 57–78% | 0.132 | 81 | 379 | the same |
| Letta, with a persona that keeps facts current | 90% | 80–95% | 0.152 | 88 | 265 | the same |

Read the rows that work as one band. Seven configurations sit between 82%
and 97% with overlapping intervals, and the order among them is not a result.
Plain retrieval over raw turns is at the top of the band and the bottom of the
cost column. Letta at its defaults is the one configuration clearly below the
others; with three lines in its persona it joins them.

The differences that are large are cost and weight. Graphiti spends about
thirty times what textual memory spends and more than three hundred times what
retrieval spends, for no gain in accuracy here, and needs a graph database.
Textual memory and retrieval need nothing but the model.

## 1. How a system is fed decides whether it remembers

The first runs of Graphiti and Letta scored 18% and 58%. Neither number was
about the system; both were about how the conversation was handed to it.

| Arm | how it was fed | accuracy | update never stored | calls to write | USD per question |
|---|---|--:|--:|--:|--:|
| Graphiti | sessions cut into episodes of up to 8,000 characters | 18% | 45 | 121 | 0.24 |
| Graphiti | one episode per message, as its own examples do | 82% | 5 | 720 | 0.64 |
| Letta | each session in one request, ending on an assistant message | 58% | 22 | 11 | 0.03 |
| Letta | one agent step per user message | 69% | 15 | 81 | 0.13 |

Graphiti's extraction prompts are written for one message from a named
speaker, and it adds the previous ten episodes as context. With 8,000-character
episodes every extraction prompt carried 60,000–80,000 characters, mostly the
assistant's long answers, and the model returned two or three entities per
episode; an update that was in the prompt produced no fact to update
([part 6](/posts/2199/01/agent-memory-6-graphiti/)). Letta's agent decides
what to remember during its own turn. Sent a whole session ending on an
assistant message, it had nothing to answer and mostly took no turn; its
`human` block stayed empty after 43 of 67 histories
([part 7](/posts/2199/01/agent-memory-7-letta/)).

Neither fix changes a setting. Both make the input look like the input each
system was built for. That contract is written down in neither API, nothing
fails when it is broken, and keeping it is expensive: Graphiti's working run
costs 2.7 times the broken one, Letta's 4.6 times. If you evaluate a memory
system, check what it stored before you look at its score.

## 2. What memory looks like after an update

| Arm | new value stored | old value still stored | old value still current | both delivered | correct when both delivered | tokens given to the answer |
|---|--:|--:|--:|--:|--:|--:|
| full context | n/a | n/a | n/a | 58 | 52/58 | 27,890 |
| retrieval | n/a | n/a | n/a | 54 | 52/54 | 5,761 |
| textual memory | 85% | 64% | 7% | 39 | 37/39 | 1,513 |
| Mem0 | 78% | 81% | 37% | 45 | 41/45 | 930 |
| Honcho, chat | 82% | 81% | 64% | 39 | 33/39 | 77 |
| Honcho, repr | 82% | 81% | 64% | 53 | 51/53 | 935 |
| Graphiti | 78% | 70% | 21% | 39 | 37/39 | 284 |
| Letta | 42% | 33% | 24% | 15 | 12/15 | 884 |
| Letta, persona | 79% | 66% | 9% | 43 | 42/43 | 1,288 |

Three readings.

**Almost nobody resolves the conflict when writing, and with dates it mostly
does not matter.** Mem0 keeps the old value as a current fact in a third of
the questions, Honcho in two thirds; Graphiti, the system built to close
superseded facts, still presents the old one as current in a fifth. When both
values reach the answering model with their dates, it picks the newer one
about nine times in ten.

**The systems that overwrite keep less, not better.** Textual memory rewrites
its profile and keeps the old value as current in only 7% of questions, at the
price of occasionally dropping a detail. Letta's memory held the new value in
only 42% of questions; its agent wrote often, but not at the message that
mattered.

**What reaches the prompt differs by a factor of 360**, from Honcho's 77-token
dialectic summary to full context's 27,890 tokens, with accuracy inside the
same interval. And the summary is the path that lost answers: the same Honcho
store scored 87% as a summary and 93% as dated lines.

Eight questions ask for an earlier value ("What was my *previous* frequent
flyer status?") and three for both. The expectation was that the systems that
overwrite would lose the earlier value. It did not show: textual memory
answered seven of the eight, because its rewrites keep the history in the line
("15 … as of 2023-09-30; previously 12 as of 2023-08-11"). Eight questions are
too few to measure a difference of this kind.

## 3. Why the answers were wrong

I read every wrong answer next to its history and its stored memory. With 2 to
21 failures per configuration these are mechanisms, not rates.

**Three questions are flawed.** They account for 12 of the 39 wrong answers
among full context, retrieval, textual memory, Mem0 and Honcho. In one, two
sessions on the same day say six and then four, the key says six, and every
one of those systems answers four. Leaving them out moves every score up by a
few points and changes no conclusion.

**Most loss is at write time.** "The update was never stored" is 4 of Mem0's
11 wrong answers, 6 of Graphiti's 12 and 14 of Letta's 21. The revision is
typically one clause in a message about something else: "By the way, I just
finished my 5th project since starting painting classes". This is what
[HaluMem][halumem] measures across systems: most of them recall fewer than
60% of the facts they should have extracted, and more than half of failed
updates fail because the original fact was never extracted (p. 11, Table 3).
Retrieval over raw turns cannot lose a fact this way, because it writes
nothing; the revision is still there, word for word, in its round.

Then each system has a failure of its own, one per part:

| System | Its characteristic failure | Example |
|---|---|---|
| textual memory ([part 4](/posts/2199/01/agent-memory-4-textual-memory/)) | the "previously" clause invites arithmetic | "25 postcards… (up from 17)", answered as 25 − 17 = 8 |
| Mem0 ([part 5](/posts/2199/01/agent-memory-5-mem0/)) | two values kept as two facts, then combined | "three sessions" and "five sessions", answered as 8 |
| Graphiti ([part 6](/posts/2199/01/agent-memory-6-graphiti/)) | dating by when a fact became true closes the wrong fact | Paris, said later but dated earlier, closed as superseded by Hawaii |
| Letta ([part 7](/posts/2199/01/agent-memory-7-letta/)) | notices the revision and does not write it; the phrase-match search cannot find it | "Congratulations on hitting 600 followers!", and no edit, 18 times |
| Honcho ([part 8](/posts/2199/01/agent-memory-8-honcho/)) | the dialectic agent refuses to choose between two dated values | "there is conflicting information… clarification is required", 5 of 9 errors |
| full context | the new value in the prompt, the old one in the answer | "She moved to Chicago" outweighed the later "moved back to the suburbs again" |

The last row matters as a control. Full context had both values in the prompt
in all 58 questions that have an old value, and was marked wrong in six of
them, some of those flawed questions. That is roughly the answering model's
share of the error, and it is small, as
[DynamicMem][dynamicmem] also finds (the answer model causes 2–7% of
failures there, p. 12, Fig. 9).

**Telling the agent what to do fixed most of Letta.** Three lines in the
persona block (date every fact, update the line when a value changes and keep
the earlier one, search with one or two words) raised the revisions written
at the message from 31 to 57 of 64, and the score from 69% to 90%. The persona
was written after reading these failures, on the same questions, so 90% is not
a held-out score; the count of revisions written is the sharper evidence. No
other system was re-run with a changed prompt.

## 4. What trimming hid: the full history

The same 25 questions with all ~48 sessions, for the four systems cheap enough
to run on 124,000-token histories:

| Arm | accuracy, 10 sessions | accuracy, full history | tokens to the answer | USD per question, 10 → full |
|---|--:|--:|---|---|
| full context | 92% | 84% | 27,677 → 123,631 | 0.007 → 0.028 |
| retrieval | 100% | 96% | 5,825 → 5,881 | 0.002 → 0.002 |
| textual memory | 96% | 92% | 1,515 → 5,567 | 0.022 → 0.277 |
| Mem0 | 84% | 84% | 919 → 910 | 0.040 → 0.181 |

**Full context slips; it does not collapse.** All four of its errors on the
full history are the new value in the prompt and the old one in the answer
(27:12 instead of the later 25:50). On 25 questions the drop from 92% to 84%
is two answers, inside the interval. The LongMemEval paper's GPT-4o fell from
0.870 with only the evidence sessions to 0.606 with all of them (p. 6, Fig. 3).
A model that reads 124,000 tokens well removes most of the capacity argument
for memory on this benchmark, which an audit of LoCoMo also remarks on:
LongMemEval-S "fits entirely in modern context windows".

**The cost of memory grows with the history at write time.** Textual memory
costs 13 times more on the full history (one rewrite per session, of a growing
profile), Mem0 4.5 times. Retrieval costs the same, because it does nothing
until it is asked. What reaches the prompt stays flat for every memory system.

## What memory does not fix

These benchmarks measure whether a fact is recalled. A second problem is how a
recalled fact is used, and adding memory makes it worse.

- In [OP-Bench][op-bench], which tests restraint (not inserting user facts
  into unrelated questions, not agreeing with a false claim because it matches
  the profile, not repeating itself), GPT-4o-mini scores 83.10 with no memory,
  55.96 with retrieval, 46.32 with Mem0 and 41.86 with MemOS (p. 5, Table 2).
  The memory that personalises most restrains least.
- [PersonaMem-v3][personamem-v3] calls this an over-personalisation tax and
  finds it depends on the model: GPT-5.5 restrains itself less with textual
  memory than with the raw history (71.0% against 75.4%), Gemini-3.5-Flash
  more (69.9% against 57.0%) (§4.4, p. 18).
- [MemSyco-Bench][memsyco] finds that memory makes models more sycophantic:
  on objective factual questions, adding memory lowers Qwen3-8B's accuracy
  from 49.1 to 26–36 (p. 7, Table 1).
- [HorizonBench][horizonbench] isolates the update itself, with six-month
  histories in which life events change preferences: the best of 25 models
  answers 52.8%, and when models err on an evolved preference, more than a
  third of the time they pick the value the user first stated. The failure is
  in updating a belief, not in finding the evidence.

None of this shows up in an accuracy score on recall questions, including
mine.

## Where the headroom is

Every system in this series that writes memory decides what to write with a
prompt, and the experiment says that decision is where most answers are lost. The literature
is moving the decision from prompts to rules that are trained or derived.
[Memory-R1][memory-r1] trains Mem0's four operations with reinforcement
learning from 152 question–answer pairs. [SAGE][sage] replaces most write
decisions with a novelty test over the stored embeddings and calls a model
only for borderline cases. [DeMem][demem] treats memory as rate–distortion:
two histories may share one memory as long as the same action is right for
both, which gives an exact rule for what can be forgotten, and it shows that
similarity between descriptions barely predicts which memories can be merged
(AUC 0.548). [Belief Memory][belief-memory] keeps several candidate
conclusions with probabilities instead of one. The evidence for each rests
mostly on LoCoMo and small models; the direction is clear, the size of the
gain is not.

Two questions stay open. What to forget has no training signal: no outcome
says that a memory should have been dropped, which is why forgetting curves
everywhere have constants a human chose. And whether an update should mark
the old fact as replaced and keep it (Zep, Mem0's graph variant) or remove it
(Mem0's DELETE, what a privacy request requires) has, as far as I can find, no
paper comparing the two on the same task. This experiment covers both camps,
plus "add only" and "overwrite in place", and on knowledge-update questions
with dates, which camp a system was in mattered less than whether it stored
the update at all.

## A decision guide

No winner, but some defaults.

- **If the history fits in the prompt, start with no memory.** Put the whole
  history in, or search it. On this benchmark plain BM25 over the raw turns,
  with their dates, scored highest at the lowest cost, and wrote nothing that
  could be lost.
- **When it no longer fits, a text profile is enough for most assistants.**
  One rewrite per session, with a rule for what to do when something changes
  and absolute dates, resolved the conflict at write time better than anything
  else here, and a person can read it.
- **Add retrieval when the profile outgrows the prompt**, and pass the
  conversation's dates in at write time and show them at read time. With dates,
  the answering model picks the newer value about nine times in ten.
- **A graph earns its cost** when the questions need history or paths between
  entities, and you are willing to tune its prompts and thresholds for your
  data and pay for a model call per fact on every message.
- **A background reasoner earns its cost** when the answers depend on what the
  user implies more than states, and when retracting a fact must retract what
  was built on it.
- **An agent that writes its own memory** needs instructions on when to write,
  how to date and what to do with the old value. Three lines moved it from the
  bottom of this table to the middle.
- **Whatever you build, check what it stored.** Two of the systems here
  scored 18% and 58% with no error anywhere, until the stored memory was read.

## Limits

- Trimmed histories for the main run, one question type, 67 questions, one
  model in every seat. In Graphiti's extraction and Letta's agent the model's
  judgement is the memory policy, so a stronger model would change those two
  rows most.
- Each fact is stated once and revised once. Nothing is repeated across many
  sessions, so a system whose value is inferring patterns from repetition
  (Honcho's claim) has nothing to work on.
- Every system ran at its library defaults, with the exceptions listed in its
  module. Graphiti and Letta were re-run with their ingestion fixed, and Letta
  once more with a changed persona; the earlier runs are kept and reported.
- Letta ran as its self-hosted server, whose conversation search is a literal
  phrase match unless a hosted vector service is configured.
- One run per configuration, at temperature 0 (Letta's agent at its own
  default of 1.0).
- **These numbers are not comparable to published LongMemEval results.** The
  history is trimmed, there is one question type, and the models differ.
- No vendor took part, and none was asked to tune its system.

## Reproducing it

The code, the result files for every question and arm, and the per-system
accounts of every wrong answer are in the
[agent-memory-eval repository][repo]. The whole experiment cost about $110 on
Vertex AI, smoke tests and every Graphiti and Letta run included; rebuilding
every table from the committed results costs nothing. The raw model calls are
kept, but not published.

That ends the series. The short version is in
[part 1](/posts/2199/01/agent-memory-1-why/), and the map in
[part 2](/posts/2199/01/agent-memory-2-the-map/).

## References

<!-- REFS -->

Papers:

- Chhikara et al., [Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory][mem0] (2025)
- Li et al., [MemOS: A Memory OS for AI System][memos] (2025)
- Wang and Chen, [MIRIX: Multi-Agent Memory System for LLM-Based Agents][mirix] (2025)
- Abtahi et al., [Memanto: Typed Semantic Memory with Information-Theoretic Retrieval for Long-Horizon Agents][memanto] (2026)
- Wang et al., [SAGE: A Novelty Gate for Efficient Memory Evolution in Agentic LLMs][sage] (2026)
- Rasmussen et al., [Zep: A Temporal Knowledge Graph Architecture for Agent Memory][zep] (2025)
- Hu et al., [Evaluating Memory in LLM Agents via Incremental Multi-Turn Interactions][memoryagentbench] (2025)
- Wang et al., [EvoMemBench: Benchmarking Agent Memory from a Self-Evolving Perspective][evomembench] (2026)
- Cherif, [AgentMemBench: A Systematic Benchmark for Evaluating Long-Term Memory Management Strategies in Conversational AI Agents][agentmembench] (2026)
- Wu et al., [LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory][longmemeval] (2024)
- Chen et al., [HaluMem: Evaluating Hallucinations in Memory Systems of Agents][halumem] (2025)
- Xie et al., [DynamicMem: A Long-Horizon Memory Benchmark in Real-World Settings][dynamicmem] (2026)
- Hu et al., [OP-Bench: Benchmarking Over-Personalization for Memory-Augmented Personalized Conversational Agents][op-bench] (2026)
- Jiang et al., [PersonaMem-v3: Toward Omni-Platform Personal Intelligence for Holistic User Understanding, Recommendation, and Agentic Tasks][personamem-v3] (2026)
- Xiang et al., [MemSyco-Bench: Benchmarking Sycophancy in Agent Memory][memsyco] (2026)
- Li et al., [HorizonBench: Long-Horizon Personalization with Evolving Preferences][horizonbench] (2026)
- Yan et al., [Memory-R1: Enhancing Large Language Model Agents to Manage and Utilize Memories via Reinforcement Learning][memory-r1] (2025)
- Zou et al., [Remember the Decision, Not the Description: A Rate-Distortion Framework for Agent Memory][demem] (2026)
- Liao et al., [Belief Memory: Agent Memory Under Partial Observability][belief-memory] (2026)

<!-- /REFS -->

Other sources:

- Penfield Labs, [We audited LoCoMo: 6.4% of the answer key is wrong and the judge accepts up to 63% of intentionally wrong answers][penfield]
- [agent-memory-eval][repo], the code and results for this series

[mem0]: https://arxiv.org/abs/2504.19413
[memos]: https://arxiv.org/abs/2507.03724
[mirix]: https://arxiv.org/abs/2507.07957
[memanto]: https://arxiv.org/abs/2604.22085
[sage]: https://arxiv.org/abs/2605.30711
[zep]: https://arxiv.org/abs/2501.13956
[memoryagentbench]: https://arxiv.org/abs/2507.05257
[evomembench]: https://arxiv.org/abs/2605.18421
[agentmembench]: https://arxiv.org/abs/2608.00009
[longmemeval]: https://arxiv.org/abs/2410.10813
[halumem]: https://arxiv.org/abs/2511.03506
[dynamicmem]: https://arxiv.org/abs/2606.22877
[op-bench]: https://arxiv.org/abs/2601.13722
[personamem-v3]: https://arxiv.org/abs/2608.21381
[memsyco]: https://arxiv.org/abs/2607.01071
[horizonbench]: https://arxiv.org/abs/2604.17283
[memory-r1]: https://arxiv.org/abs/2508.19828
[demem]: https://arxiv.org/abs/2605.10870
[belief-memory]: https://arxiv.org/abs/2605.05583
[penfield]: https://penfieldlabs.substack.com/p/we-audited-locomo-64-of-the-answer
[repo]: https://github.com/anton-dergunov/agent-memory-eval

<!-- SERIES -->

---

[← Part 8: Honcho: a reasoner that works in the background](/posts/2199/01/agent-memory-8-honcho/)

<!-- /SERIES -->
