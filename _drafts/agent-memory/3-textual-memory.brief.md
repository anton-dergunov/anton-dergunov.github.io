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

| Section | Claim it supports | Evidence or artefact to show | Figure |
|---|---|---|---|
| Opening | The simplest design that still deserves the name memory; the two choices in this part's words (a background writer, insert everything); the notebook link | Problem above | `textual` |
| Where it comes from | MemoryBank's user portrait is the ancestor ("The ancestor of this system is…", plain word order, per Anton's note). The version run here follows PersonaMem-v3's Textual Memory baseline: one profile under four headings, ADD/EDIT/REMOVE/MERGE, a 4,096-token cap. | The PersonaMem-v3 prompt quote. Name the paper when its result is cited ("In the PersonaMem-v3 paper…"), and say what the result measures before giving it. | none |
| The test | The full short transcript (version B); this design is most tested by the reversal | Series brief | `conversation` |
| How the rewrite works | Write path: after each session, one call reads the current profile and the session (with its date) and writes the whole profile again. Read path: the whole profile goes into the prompt. | The two rules that do the work, quoted exactly (replace and record the change with dates; absolute dates). Make clear this prompt is ours, written after PersonaMem-v3's description, not the benchmark's (Anton's note). | `textual` (or a small step figure) |
| The run traced: after session 1 | Everything kept; "eight years" becomes "since 2018", "next week" becomes "the week of March 16"; one hedge ("Currently based in or planning for Berlin") the user never said | The profile, shown exactly, as Anton asked | none |
| The run traced: after session 2 | One current diet, the old one in a "previously" clause with a date. Four things nobody asked for: added precision ("since 2026-05-01"), a reworded constraint ("can't eat shellfish" → "shellfish allergy"), the hedge kept as history, the March dinner dropped. | The second profile | `profile-diff` |
| The run traced: reading | Every constraint reached the answer, including the two-hop fact, because the guests sit on one line of a profile that is inserted whole. The "I have booked a table" claim is the answering model, not the memory. | The answer | none |
| Where it breaks | The "previously" clause invites arithmetic, from the benchmark run in words: "25 postcards (up from 17)" answered as 25 − 17 = 8. A detail mentioned once can be dropped in a rewrite. PersonaMem-v3 measures drift at scale (about 14.4% of lines dropped or rephrased per update). How to notice: diff the profile after each rewrite. Fixes: phrase history as "now 25; reported 17 on …"; keep the raw history beside the profile. | findings/textual.md; v1 "What it does well…" | none, or reuse `profile-diff` |
| Cost | Two calls to store two sessions, one to answer; each rewrite reads the whole profile (357 → 559 tokens in) | v1 cost table | none |
| When it is enough | Use it first when the profile fits, facts change and the newest must win, and someone should be able to read it. Do not use it when exact wording matters or rewriting dominates cost. | v1 "When it is enough" | none |
| How it was run / Try it | About 50 lines of our code; the same prompt as the experiment; the notebook | Links | none |

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

- Dynamic Cheatsheet: cut (Anton: "I got nothing from it"), or explained in a full paragraph if it earns one. The default is cut.
- Mastra Observational Memory: one line, pointing to part 9.
- The PersonaMem-v3 Mem0 comparison (79.9% vs 56.9%): keep only if the paragraph says first what the task measures. Otherwise cut.
- DynamicMem's A-Mem result: cut unless it supports the drift point directly.
- "Compare Mem0 in part 5" and every other back-reference.

## Links

- Notebook 01: https://anton-dergunov.github.io/agent-memory-eval/notebooks/01-textual.html
- Papers: MemoryBank, PersonaMem-v3

## For search and for employers

- Title: "Textual memory: one profile, rewritten"
- Excerpt: "The simplest LLM memory design: one profile rewritten after each conversation. How it resolves changed facts, and how a rewrite drifts."
- What this post shows: Anton starts from the simplest baseline and shows exactly what it does and costs.

## Anton's notes on v1, and where each is handled

| Note | Handled by |
|---|---|
| "We need to put the exact example here! … reference the notebook" | Transcript in "The test"; notebook link in the opening |
| "Show an example of this" / "Show it! Specific example!" | Profiles shown in the run sections |
| "The ancestor of this system is…" (word order) | Wording rule; voice.md change |
| "Which one?" / "Paragraph of what?" | Name the paper; say what the result measures |
| "Make it clear that this is what we test" | "How the rewrite works" |
| "This is a detail…" (model, temperature) | Moved to "How it was run" |
| "I got nothing from it!" (Dynamic Cheatsheet) | Cut, or a full explanation |
| "Readers are reading one blog after another…" (Compare Mem0) | No back-references |
| "Would read much better in part 9" (real data) | Scores go to part 8; one failure stays, in words |

## Open questions for Anton

- Cut Dynamic Cheatsheet entirely? (Recommended.)
