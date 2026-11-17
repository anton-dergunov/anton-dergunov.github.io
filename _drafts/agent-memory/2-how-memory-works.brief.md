---
post: _drafts/agent-memory/2199-01-01-agent-memory-2-how-memory-works.md
type: map
status: draft
---

# Brief: How agent memory works (part 2)

Rewritten 2026-11-16 from Anton's spoken notes (`~/tmp-spoken-plans/blog/next-part.txt`), which rejected the earlier brief's framing. Shared material is in `series.brief.md`. Sources: the literature review `~/papers/reviews/llm/memory.md`, the surveys and papers in `~/papers/library/llm/memory/` (notes in `~/papers/notes/`), CoALA in `~/papers/library/llm/agents/`. `v1/2199-01-01-agent-memory-2-the-map.md` is material for facts only.

## Reader

The series reader, who has heard of memory systems for LLM agents and wants to know how they work in general, before meeting any particular architecture. They may have read other posts that classify memory as working, episodic, semantic and procedural, and want to know how that relates to what a system actually does. This part is the overview of the whole area, and the most visual part of the series.

## The problem

New memory systems and memory products appear often, and some disappear as quickly. Each comes with its own names and diagrams. Most of them combine a small set of ideas: where the memory is kept, what is written and when, how a request gets what it needs, and what is paid for at each step. Without those ideas a reader cannot compare two systems, or tell a memory system from retrieval over documents or from a long prompt.

## What the reader should leave with

1. Memory can be kept as text outside the model, as internal state of the model, or in its weights. Text is the only form a person can read and correct, and the only one a hosted model accepts, which is why almost every memory system for agents uses it.
2. The labels "working, episodic, semantic, procedural" come from cognitive science through CoALA; each corresponds to a mechanism.
3. A text memory has a write path and a read path. The six operations of the Rethinking-Memory survey sit on them. The write path can run in the background; the read path runs while the user waits.
4. Systems differ in how they answer five design questions. Two of them explain most of a system's behaviour and cost: who writes, and whether the read path inserts the whole memory or selects part of it.
5. Retrieval over documents and a long context are not memory, but they are the baselines memory must beat. The research finds long context strong, published rankings unstable, most facts lost at write time, and updating the hardest part.

## Outline

| Section | Claim | Evidence or artefact | Figure |
|---|---|---|---|
| Opening (no heading) | A model sees only its prompt; carrying information between conversations needs a memory system that keeps, updates, drops and finds facts. Systems are many and come and go; this part explains the ideas they share. | Repository link line | none |
| What memory means for an LLM agent | Weights and context are the built-in memories; neither carries over. Definition of memory; the jobs it has. | Plain prose | none |
| Where memory can be kept: text, cache or weights | The form decides what can be read, corrected and used with a hosted model; text dominates for those reasons. An embedding in a vector store is an index, not latent memory. | Memory in the Age of AI Agents p. 13, p. 30–31; Memorizing Transformers, MemoryLLM, Cartridges; MEMIT, Memory Layers, Titans, Larimar; model-editing result (p. 14) | `three-homes` |
| Working, episodic, semantic and procedural memory | The labels and what each is mechanically; RAG as a read-only semantic memory; the later surveys' alternatives; what this series covers | CoALA p. 9–10; Rethinking p. 5–6; Age of AI Agents p. 5, p. 31; Externalization | `memory-kinds` |
| The write path and the read path | Every text memory has both; the six operations; when each runs; what the answering model receives | Rethinking p. 6–7; pseudocode | `operations` |
| Five design questions | Unit, writer, store shape, read selection, timing, each with examples | SeCom, Memory-R1, Zep, MemGPT, LightMem | none |
| ↳ Who writes the memory | Four writers, when each runs, how each loses facts | Age of AI Agents p. 61 ("silent failure") | `writers` |
| ↳ Whether the read path inserts or selects | Inserting cannot miss but has a ceiling; selecting scales and can miss; designs that do both | Claude Code's index and topic files | `insert-vs-select` |
| ↳ The systems of this series on the two choices | Five systems and two baselines, one line each | Graphiti scoped to "of the five here" | `map-systems` |
| Write cost and read cost | Paid once vs on every request; store size and prompt size are different numbers | Mem0 paper p. 11 (Table 2), p. 14; LightMem p. 7; Sleep-time Compute | `cost-timing` |
| Memory, retrieval and long context | The two baselines, and the fair one (same prompt, empty memory) | Age of AI Agents p. 10–11; Dynamic Cheatsheet p. 6 | none |
| What the research has found | Four labelled findings, each with how strong the evidence is | Mem0 p. 11; LongMemEval p. 6; MemoryAgentBench p. 8; Mem0/MemOS/MIRIX tables; HaluMem p. 11; ForgetEval; A-TMA; model editing p. 14 | small table |
| Where the designs came from | Three 2023 papers whose ideas later systems reuse, each shown; then 2024–2026 | Generative Agents p. 8–10; MemoryBank p. 3–4 and Fig. 1 (the portrait); MemGPT p. 1–3 | `timeline` |
| Closing paragraph | What the later parts do | Links | none |

## Running example

Not used in this part (Anton, 2026-11-16). Neutral one-line illustrations instead: a user who moved from Munich to Berlin.

## Numbers

| Number | Out of what | From where | Compared with | So what |
|---|---|---|---|---|
| 7K vs >600K tokens stored; 1,764 and 3,911 tokens in the prompt; 26K for the whole conversation | per LoCoMo conversation | Mem0 paper p. 14, p. 11 Table 2 | each other | store size and prompt size are different budgets; a competitor's measurement |
| 72.90 vs 66.88; p95 17.12 s vs 1.44 s | LoCoMo, judge score | Mem0 paper p. 11 Table 2 | the vendor's own system | full context is strong; memory buys speed |
| 0.870 → 0.606 | GPT-4o, evidence sessions only vs ~115K-token history | LongMemEval p. 6, Fig. 3 | itself | long histories are read badly |
| Zep 6 points below Mem0, or 17 above | LoCoMo, three papers | Mem0 p. 11, MemOS p. 24, MIRIX p. 11 | each other | published rankings do not transfer |
| < 60% extraction recall | every system but MemOS | HaluMem p. 11 | the facts it should have stored | most is lost at write time |
| 0.97 → 0.01 | downstream facts after an edit | Model-editing paper p. 14, Table 4 | before the edit | an edit does not change what follows from it |
| 23.3 / 36.7 / 50.0 | AIME 2024, Claude 3.5 Sonnet | Dynamic Cheatsheet p. 6, Table 1 | no memory, empty memory, curated | the fair baseline is the empty memory |

Experiment numbers stay in part 8.

## Left out

- The running example, and the reading guide to the parts (part 1).
- Products on the map (part 9).
- Memory of skills and procedures (ExpeL, ReasoningBank), named in the labels section as out of scope.
- Security and poisoning of memory (one survey, one benchmark): out of scope for an overview of how it works.

## For search and for employers

- Title: "How agent memory works"
- Excerpt: "How memory systems for LLM agents work: where memory can be kept, what happens when it is written and read, the design choices that separate systems, and what the research has found."
- What this post shows about Anton's work: he reads a field widely and reduces it to a frame others can use, with sources for every claim.

## Anton's spoken notes (2026-11-16), and where each is handled

| Note | Handled by |
|---|---|
| Part 2 is an overview of the whole area, for someone who wants to know how memory systems work in general | The reader and the outline above |
| "Looks like many inventions and is mostly one loop" reads as a strong, angry opinion | Neutral opening: many systems, a few shared ideas |
| Not a loop: memory runs per session; forgetting is not its only job | Two paths, write and read; the opening names keep, update, drop, find |
| Classify by form first: text, embeddings, weights; fine-tuning and online learning are options | "Where memory can be kept" comes first after the definition, with the embedding point |
| Many blogs start with working/episodic/semantic/procedural; maybe introduce it | Its own section, traced to CoALA and mapped to mechanisms |
| Text memory matters because most people have no access to frontier weights | Said in general terms in the forms section; no mention of earlier work |
| Titles must be plain and technical | Headings name the content |
| No diet, no dinner, no running example | Not used in this part |
| Keep the six operations, with a picture | `operations` figure |
| "Five questions that separate the designs": title disliked; group the design questions and mark them as design decisions | One section "Five design questions", with the two series axes as subsections |
| Where memory lives: a picture | `three-homes` figure |
| "What this series runs" competes with part 1 | Moved to part 1; one closing paragraph here |
| Part 1 should introduce the series, part 2 explain memory | Part 1 brief to be rewritten in its own session |

## Anton's notes on v1, and where each is handled

| Note | Handled by |
|---|---|
| "Is this the correct word? Not compression?" | "Condensation" kept (the survey's term), glossed as compression at read time |
| "What is this?" (tiers) | Defined with MemGPT's main context and external stores |
| "What does it mean?" (nobody can read) | Explained in the forms section: the memory is vectors, not sentences |
| "Keep pages?" | Only where a number can be checked |
| "Double check it is really so" (first row of every table) | Dropped here; part 8 says it where it is true |
| "Why CC said so?" (three papers contain most ideas) | Reworded: each idea traced to a later system |
| "How it looked like?" (MemoryBank portrait) | The portrait from Fig. 1 and the paper's two prompts |
| "Need more references on this claim" (re-runs) | Finding 2, with the three papers' tables |
| "Need some context on this here" (MemGPT RAM/disk) | One sentence on paging |
| "Strong statement… Or the only one here?" | Scoped to "of the five here" |

## Open questions for Anton

- None blocking. The plan's follow-ups (series brief idea 1 "One loop", part 9's recap, the `overview` subtitle) are listed in `HANDOFF.md`.
