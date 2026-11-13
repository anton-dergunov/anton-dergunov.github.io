---
post: _drafts/agent-memory/2199-01-01-agent-memory-2-how-memory-works.md
type: map
status: draft
---

# Brief: How agent memory works (part 2)

Shared material is in `series.brief.md`. Source: `v1/2199-01-01-agent-memory-2-the-map.md` and Anton's 10 notes on it, the surveys and papers in `~/papers/library/llm/memory/` (notes in `~/papers/notes/`).

## Reader

The series reader, who wants the concepts before the systems: an engineer who has heard "agent memory", "RAG" and "long context" and wants to know how they relate. This is the most visual part of the series. Every concept that takes more than a paragraph gets a figure.

## The problem

Every memory paper introduces its system with its own name and its own diagram, so the field looks like dozens of unrelated inventions. Underneath, almost all of them are the same loop with different answers to a few questions. Without that frame a reader cannot compare two systems, or tell a memory system from retrieval or from a long prompt.

## What the reader should leave with

1. Every memory system is one loop (write, store, read, use) wrapped around a model that does not change, and papers usually improve one step of it.
2. Where the memory lives (text, the model's cache, or its weights) decides what is possible. Text is the only form a person can read and delete and any hosted model can use, which is why products use it.
3. Within text memory, two choices separate the designs: who writes, and whether the read path inserts everything or selects.
4. Work on the write path is paid once; work on the read path is paid on every request. A paper's cost figure depends on which of the two it reports.
5. Long context and retrieval over the raw history are not memory, but they are the baselines every memory system has to beat.

## Outline

| Section | Claim it supports | Evidence or artefact to show | Figure |
|---|---|---|---|
| Opening | The field looks like many inventions and is mostly one loop; this part gives the frame for reading any memory system | A short version of the problem above; the notebooks link | none |
| A model that forgets, and the loop around it | Weights and context are the model's only built-in memories; neither carries over; a memory system is the loop that does | v1 "A stateless model…" | `overview` |
| Six operations on the loop | The vocabulary from the Rethinking-Memory survey, each with a one-line example from the running conversation | v1 table, turned into a figure. Keep "condensation" (the survey's term) and gloss it: compressing what was retrieved so it fits the prompt (Anton asked whether "compression" is meant) | `operations` |
| Where memory lives: text, cache or weights | Location decides readability, deletability and whether it works with a hosted API | v1 table, turned into a three-panel figure. Latent memory: Memorizing Transformers, MemoryLLM, Cartridges, each explained in one sentence with a picture of what is stored. "Nobody can read what was stored" explained: the memory is vectors, not sentences. Weights: MEMIT, Memory Layers, Titans, and the model-editing result (an edit does not change the facts that follow from it: "moved to Berlin" vs "nearest airport") | `three-homes` |
| Who writes | Four writers (nobody, a pipeline, the answering agent, a background process), drawn on a timeline of one turn. Each loses facts in its own way. | v1 "The two axes" | `writers` |
| Insert or select | Inserting cannot miss but stops at the prompt's size; selecting scales and can leave out the one fact that mattered | v1; the Claude Code example (an always-loaded index plus topic files read on demand) shows both in one design | `insert-vs-select` |
| The map | The five systems of the series on the two choices, each in one line | The map without products (products are part 9). Scope "the only one that models time explicitly" to "of the five here" (Anton's note) | `map` |
| When the work is paid for | The write cost is paid once and the read cost on every request; a paper tends to report the budget that flatters it | The Mem0 paper's store sizes (Mem0 about 7K tokens per conversation, Zep more than 600K, both 1–3K in the prompt; p. 14), with the caveat that this is a competitor's measurement. No experiment numbers here. | `cost-timing` |
| What memory is not | RAG has no write decision; a long context removes the need to select. Both are baselines, and full context is strong. | Mem0 paper: full context 72.90 vs Mem0 66.88 on LoCoMo, but p95 latency 17.12 s vs 1.44 s (p. 11). LongMemEval: GPT-4o 0.870 with only the relevant sessions vs 0.606 with all of them (p. 6, Fig. 3). Explain LoCoMo in one sentence where it first appears. | none, or a small pair |
| Where the designs came from | Three 2023 papers hold the ideas the later systems build on; each explained enough to be useful | Generative Agents (memory stream, importance × recency × relevance, reflections); MemoryBank (raw turns, event summaries, and a global user portrait written by the LLM, p. 3; the forgetting curve; show a portrait from the paper `[TODO: pull an example from the paper text in ~/papers]`, as Anton asked "how did it look like?"); MemGPT (context as RAM, external stores as disk, with one sentence on why that analogy: the model moves data with function calls, as a program moves pages). Then 2025–2026 in two sentences, with sources for "re-runs do not reproduce the rankings" (MemoryAgentBench, EvoMemBench, AgentMemBench; the Zep vs Mem0 swing). The claim "three papers contain most of the ideas" needs a source, or is reworded as Anton's own reading and marked as such. | `timeline` |
| What this series runs, and why these five | One idea per system; what was left out and why | v1 table, as prose plus a small table | none |
| How it was run / Try it | Notebook 00 and the repository | Links | none |

## Running example

Used lightly: one or two sentences, in the operations figure and the "who writes" section, to make the abstractions concrete ("the July session says pescatarian now"). No transcript.

## Numbers

| Number | Out of what | From where | Compared with | So what |
|---|---|---|---|---|
| Mem0 ~7K tokens vs Zep >600K stored; both 1–3K in the prompt | per LoCoMo conversation | Mem0 paper, p. 14 | each other | The store size and the prompt size are unrelated; measured by a competitor |
| 72.90 vs 66.88 (full context vs Mem0) on LoCoMo; p95 17.12 s vs 1.44 s | LoCoMo, judge score | Mem0 paper, p. 11, Table 2 | the vendor's own system | Full context is a strong baseline, and memory buys speed |
| 0.870 → 0.606 | GPT-4o accuracy on LongMemEval, relevant sessions only vs whole ~115K-token history | LongMemEval, p. 6, Fig. 3 | itself | Memory starts to win when the model reads a long history badly |
| 0.97 → 0.01 | downstream facts after a model edit | Model-editing paper, p. 14, Table 4 | before the edit | An edit to the weights does not propagate |

Page numbers only where a reader may check a number (Anton's "Keep pages?" note).

## Figures to make

`operations`, `three-homes`, `writers`, `insert-vs-select`, `cost-timing`, `timeline`, all in `agent-memory-eval/scripts/diagrams/figures/`. `overview` and `map` exist. Anton has seen better pictures of latent vs parametric memory elsewhere `[TODO Anton: which ones, to draw ours after them]`.

## Left out

- Products on the map (part 9).
- Experiment numbers, including "the systems differ by a factor of 360 in what they put into the prompt" (part 8).
- The claim "So the first row of every results table is the whole history" (Anton: "double check"); part 8 says it where it is true.
- Skill and procedure memory (ExpeL, ReasoningBank), named once in what is left out.

## Links

- Notebook 00: https://anton-dergunov.github.io/agent-memory-eval/notebooks/00-introduction.html
- Surveys: Rethinking Memory in LLM-based Agents (2505.00675); Memory in the Age of AI Agents (2512.13564)
- Papers: Generative Agents, MemoryBank, MemGPT, Mem0, Zep, LongMemEval, MemoryAgentBench, Memorizing Transformers, MemoryLLM, Cartridges, MEMIT, Memory Layers at Scale, Titans, Fundamental Problems With Model Editing

## For search and for employers

- Title: "How agent memory works"
- Excerpt: "The loop every LLM memory system shares, the two design choices that separate them, and the baselines they must beat, in diagrams."
- What this post shows about Anton's work: he reads a field widely and reduces it to a frame that others can use.

## Anton's notes on v1, and where each is handled

| Note | Handled by |
|---|---|
| "Is this the correct word? Not compression?" | Keep "condensation" (the survey's term), glossed as compression at read time |
| "What is this?" (tiers) | Define, with MemGPT's main memory and external stores as the example, or drop the word |
| "What does it mean?" (nobody can read) | Explained in the three-homes section |
| "Keep pages?" | Only where a number can be checked |
| "Double check it is really so" (first row of every table) | Moved to part 8 |
| "Why CC said so?" (three papers contain most ideas) | Source it, or mark it as Anton's reading |
| "How it looked like? This article must be highly readable." (MemoryBank portrait) | Show an example portrait |
| "Need more references on this claim" (re-runs) | Cite the third-party benchmarks |
| "Need some context on this here" (MemGPT RAM/disk) | One sentence of context |
| "Strong statement… Or the only one here?" | Scoped to "of the five here" |

## Open questions for Anton

- From part 3 (2026-11-12): Dynamic Cheatsheet's AIME result (7 problems with a plain prompt, 11 with an empty cheatsheet, 15 with a curated one) shows that the fair baseline for any memory is the same prompt with an empty memory. It is true of every design, so it may belong here rather than in part 3. Move it here?

- Which pictures of latent vs parametric memory you liked, so ours can be drawn after them.
- Whether "three papers from 2023 contain most of the ideas" is your view (then it stays, as an opinion) or should go.
