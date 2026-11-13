---
post: _drafts/agent-memory/2199-01-01-agent-memory-3-textual-memory.md
type: system deep-dive
status: draft
---

# Brief: Textual memory: one profile, rewritten (part 3)

Shared material is in `series.brief.md`. Source: `v1/2199-01-01-agent-memory-4-textual-memory.md` and Anton's 11 notes on it, notebook `01-textual`, `agent-memory-eval/docs/findings/textual.md`.

## Reader

The series reader. They may have arrived here first, so the opening re-introduces the problem and the two choices in a few sentences of this part's own.

## The problem

Before reaching for vector stores and graphs, an engineer should know how far the simplest design goes: one plain-text profile of the user, rewritten by a model after each conversation and put whole into the prompt. It is close to what consumer assistants ship, and it is the baseline every other design adds machinery to. Its risk is that every line is rewritten by a model on every pass.

## What the reader should leave with

1. A single rewrite call that sees the whole profile can resolve a changed fact when it writes. One rule in the prompt ("replace it, and record that it changed, with dates") does what the other systems need machinery for.
2. Inserting the whole profile cannot miss at read time, and stops working once the profile no longer fits.
3. Everything in the profile is the model's own wording, written again on every pass. Small drifts (a guessed date, a reworded constraint, a hedge kept as history) are the price.
4. The write cost grows with the profile, because each rewrite reads and writes all of it.

## Outline

<Order follows the system deep-dive skeleton in writing-guide `structure.md` (2026-11-12): mechanism first, the example traced session by session with cost, failures, judgement, history last. "Show in full" lists what the section shows verbatim; prompts are shown whole, with […] for cuts.>

| Section | Claim it supports | Show in full | Figure | Words |
|---|---|---|---|--:|
| Opening | A model sees only its prompt, so an LLM agent needs a memory system; textual memory is the simplest (one plain-text profile; no embeddings, graph or database); PersonaMem-v3 names it; close to the memory in consumer LLM chat products; why we start with it; the notebook link | Problem above | none | 230 |
| How textual memory works | Write path: one call per session, after it ends, reads the profile and the dated session and writes the whole profile again; nothing else runs. Read path: no search; the whole profile goes into the prompt as it is. The two rules that matter (changes with dates; absolute dates). The prompt is mine, after PersonaMem-v3's description [TODO: why it differs]. The price of each choice, as two labelled points. | The rewrite prompt in full; the answer prompt and its system line in full | `textual` | 500 |
| The example, step by step | What it tests, as a list; three sessions, the third names none of the facts. Session 1: everything kept; dates resolved; one hedge ("Currently based in or planning for Berlin"). Session 2: one current diet, the old one as history with a date; four unrequested changes, numbered. Session 3: every constraint reached the answer; the booking claim is the answering model, not the memory. Cost: tokens in split into instructions, profile and new input; the other systems' call counts as a list, named as later parts. | Each session's transcript in its subsection, phrases coloured by profile heading; profile 1; profile 2 as a diff; the answer; the cost table | `conversation`, `profile-diff` | 1,400 |
| Where it breaks | **Failure 1:** the history clause invites arithmetic (25 − 17 = 8). **Failure 2:** a detail mentioned once is dropped (the sneakers). Drift at scale: PersonaMem-v3 (§4.5, p. 19), 14.4% of lines per update, 83.1% of facts kept as concepts; Dynamic Cheatsheet's placeholders. How to notice and fix (a subsection). | findings/textual.md (linked here) | none | 640 |
| When it is enough | Use it when the profile fits, facts change and the newest must win, and someone should read it; not when exact wording matters, rewriting dominates cost, or the profile no longer fits | none | none | 180 |
| History and related work | **MemoryBank:** the portrait. **PersonaMem-v3:** the baseline, its prompt, and 25.7% vs 51.4% on tracking preference changes, with my reading of why. **Dynamic Cheatsheet:** the same memory for maths strategies; 7 / 11 / 15 and the fair baseline. **Observational Memory:** part 9. | The PersonaMem-v3 prompt, quoted | none | 720 |
| Run it yourself | A standalone implementation with no extra dependencies; same prompts and outputs as the post; any model, Gemini 3.1 Flash-Lite on the free tier; part 8 for scale; ideas to try | Links | none | 200 |

## Running example

Version B. Tested most by the reversal (the update at write time) and by the hard constraint surviving two rewrites word for word.

## Numbers

| Number | Out of what | From where | Compared with | So what |
|---|---|---|---|---|
| 2 calls to write, 1 to answer | the two-session example | notebook 01 | the other systems (named without part numbers) | The cheapest write that resolves the conflict |
| 357 → 559 input tokens | the two rewrites | notebook 01 | session 2 being only slightly longer | The input grows with the profile |
| ~14.4% of lines dropped or rephrased per update; 83.1% of facts survive as concepts at the cap | PersonaMem-v3's textual memory | PersonaMem-v3, §4.5, p. 19 | none | Drift is measured, not hypothetical |

LongMemEval scores (93%, 7% stale) go to part 8 (Anton: "would read much better in part 9").

## Figures to make

`profile-diff` (new). `textual` and `conversation` are shared.

## Left out

- Dynamic Cheatsheet: kept since 2026-11-12, in "History and related work", as one analogy (a memory of solution strategies instead of user facts) with the 7 / 11 / 15 result explained. Its fair-baseline point may move to part 2 (open question there).
- Mastra Observational Memory: one line, pointing to part 9.
- The PersonaMem-v3 Mem0 comparison (79.9% vs 56.9%): keep only if the paragraph says first what the task measures. Otherwise cut.
- DynamicMem's A-Mem result: cut unless it supports the drift point directly.
- "Compare Mem0 in part 5" and every other back-reference.

## Links

- Notebook 01: https://anton-dergunov.github.io/agent-memory-eval/notebooks/01-textual.html
- Papers: MemoryBank, PersonaMem-v3, Dynamic Cheatsheet

## For search and for employers

- Title: "Textual memory: one profile, rewritten"
- Excerpt: "The simplest LLM memory design: one profile rewritten after each conversation. How it resolves changed facts, and how a rewrite drifts."
- What this post shows: Anton starts from the simplest baseline and shows exactly what it does and costs.

## Anton's notes on v1, and where each is handled

| Note | Handled by |
|---|---|
| "We need to put the exact example here! … reference the notebook" | Each session's transcript in its own subsection (since 2026-11-12); notebook link in the opening and after session 1 |
| "Show an example of this" / "Show it! Specific example!" | Profiles shown in the run sections |
| "The ancestor of this system is…" (word order) | Wording rule (writing-guide plain-writing.md) |
| "Which one?" / "Paragraph of what?" | Name the paper; say what the result measures |
| "Make it clear that this is what we test" | "How textual memory works", with both prompts in full |
| "This is a detail…" (model, temperature) | The model and its reason in "Run it yourself"; the temperature cut |
| "I got nothing from it!" (Dynamic Cheatsheet) | Kept as one analogy, at the end, after Anton's 2026-11-12 read |
| "Readers are reading one blog after another…" (Compare Mem0) | No back-references |
| "Would read much better in part 9" (real data) | Scores go to part 8; one failure stays, in words |

## Open questions for Anton

- Why does the rewrite prompt differ from PersonaMem-v3's (whole profile and four headings, instead of ADD/EDIT/REMOVE/MERGE actions)? The post has a TODO there.
- The fair-baseline point (7 / 11 / 15): keep in part 3, or move to part 2?

## Anton's notes on the 2026-11 draft (STE version), and where each is handled

The full feedback is in writing-guide `experiments/2026-11-ste100/feedback-full-read.txt`. The structural lessons are in writing-guide `lessons.md` (2026-11-12).

| Note | Handled by |
|---|---|
| No single section on the mechanism; the prompts hidden | "How textual memory works", with both prompts in full |
| History interrupts the narrative | "History and related work", last |
| The test transcript up front, as if it were the point | Each session's transcript in its subsection, highlighted; "what it tests" as a list |
| Cost belongs with the example | "What it costs" is the last subsection of the example, with tokens split by part |
| "How it was run" and "Try it" are one section | "Run it yourself" |
| "Assistant", "consumer assistants", "I call this" | LLM agent, LLM chat products; PersonaMem-v3 named as the source of the name |
| Page numbers in the middle of sentences | Locations next to the paper's name |
| Failures without labels | **Failure 1**, **Failure 2**, and a subsection on noticing and fixing them |
| Mem0 and the other systems named before the reader knows them | "Described later in this series" |
