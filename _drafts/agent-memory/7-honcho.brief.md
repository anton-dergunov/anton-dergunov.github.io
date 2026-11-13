---
post: _drafts/agent-memory/2199-01-01-agent-memory-7-honcho.md
type: system deep-dive
status: draft
---

# Brief: Honcho: a reasoner that works in the background (part 7)

Shared material is in `series.brief.md`. Source: `v1/2199-01-01-agent-memory-8-honcho.md`, notebook `05-honcho`, `agent-memory-eval/docs/findings/honcho.md`.

## Reader

The series reader, interested in memory that infers things about a person and not only stores what they said.

## The problem

The other designs store what the user said. Honcho also stores what follows from it: every item is a conclusion at a stated level of certainty, linked to the conclusions it was drawn from, and a background process reasons over the store between conversations. That makes some things possible that a list of facts cannot do, such as withdrawing everything that rested on a fact that stopped being true. It also means the system writes sentences about a person that nobody said.

## What the reader should leave with

1. Typing each conclusion by certainty (explicit, deductive, inductive) and linking it to its premises makes an update traceable: when a fact is replaced, what rested on it can be found and withdrawn.
2. A rule like "a premise must rank below its conclusion" can be enforced by code, not just requested in a prompt.
3. The higher the level, the more plausible and less checkable the conclusion. A hypothesis that says how to test it is a cheap safeguard.
4. Reasoning passes read the whole store, so their cost grows with the profile. That is why the reasoning runs in the background.
5. How memory is read back matters: dated lines kept answers that a written summary lost.

## Outline

<Order follows the system deep-dive skeleton in writing-guide `structure.md` (2026-11-12): mechanism first, the example traced session by session with cost, failures, judgement, history last. "Show in full" lists what the section shows verbatim; prompts are shown whole, with […] for cuts.>

| Section | Claim it supports | Show in full | Figure | Words |
|---|---|---|---|--:|
| Opening | The two choices in this part's words (a background reasoner writes; a search or an agent reads); the notebook link | Problem above | `honcho` | 250 |
| How Honcho works | The levels (explicit, deductive, inductive, abductive), each with an example from the conversation. Write path: the deriver extracts explicit conclusions when messages arrive; later, the dreamer reasons over the store and adds deductive and inductive conclusions, replacing outdated ones. Read path: the dialectic agent answers in prose, or the representation endpoint returns the conclusions. | The deriver and dreamer prompts in full; the level rule as pseudocode (eleven lines in the notebook); the REJECTED line; one stored conclusion as stored | `honcho`, `honcho-levels` | 1,100 |
| The example, step by step | What it tests, as a list (the reversal, and what rested on it). Explicit and deductive: facts like Mem0's, tagged and linked; deductions range from useful to useless ("Lena is a person"). Revising: both diets briefly stored, then deduction replaced the vegetarian fact and "does not consume meat or fish", which rested on it. Induction and abduction: confidence labels from the model ignore the prompt's own rule; the one hypothesis says the user started eating fish *in order to* make the dinner easier, which nobody said; the "check:" line is the safeguard. Reading: the replaced row was not in the prompt, regardless of wording; all 23 live lines fitted, which will not hold for a real profile. Cost: seven calls vs two for the simplest extractor; reasoning input grows with the store (the second deduction read almost twice the first). | Each session's transcript in its subsection; store excerpts before and after; the hypothesis quoted | `conversation`, `honcho-retire` | 1,500 |
| Where it breaks | **Failure 1:** invention at the higher levels. **Failure 2:** from the benchmark, in words: the dialectic agent wrote two dated values up as a conflict and declined to answer, where the dated lines from the same store let the answer pick the newer one. **Failure 3:** it did not close old conclusions at scale. How to notice: read the store by level; compare the two read paths. Fixes: hypotheses that name their test; confidence computed from premise counts; reading dated lines. | findings/honcho.md (linked here); v1 | none | 600 |
| When a background reasoner earns its cost | When answers depend on what the user implies more than states, and when retracting a fact must retract what was built on it. The benchmark cannot test the pattern levels (each fact appears once). | v1 | none | 200 |
| History and related work | Generative Agents' reflections, made typed and traceable; Plastic Labs' "violation of expectation" (start from what most surprised the model). There is no paper, so this is read from the repository: the levels on main, the dreamer's specialists, abduction announced but not implemented. | v1 "Where it comes from", with the date checked | none | 350 |
| Run it yourself | The least faithful re-implementation: our prompts, written from Honcho's definitions; one call per specialist instead of an agent with tools; abduction implemented to see what it produces; part 8 for scale; ideas to try | Links | none | 200 |

## Running example

Version B. Tested most by the reversal and its consequences (the deduction that rested on the old diet).

## Numbers

| Number | Out of what | From where | Compared with | So what |
|---|---|---|---|---|
| 7 calls | writing and answering the example | notebook 05 | 2 for the simplest extractor (named) | The cost of reasoning |
| 461 → 888 input tokens | the two deduction passes | notebook 05 | each other | The reasoning cost grows with the store |
| 5 of 9 | the dialectic path's wrong answers that were refusals over two dated values | findings/honcho.md | the representation path | A summary lost answers that the raw lines kept; part 8 has the accuracies |

## Figures to make

`honcho-levels`, `honcho-retire` (new). `honcho` exists.

## Left out

- Belief Memory and the security survey: one sentence each, or cut.
- Accuracies and token counts for the two read paths (part 8).

## Links

- Notebook 05: https://anton-dergunov.github.io/agent-memory-eval/notebooks/05-honcho.html
- Honcho repository; Generative Agents; violation of expectation (Plastic Labs)

## For search and for employers

- Title: "Honcho: a reasoner that works in the background"
- Excerpt: "Memory that stores conclusions, not just statements: levels of certainty, premises, retracting what rested on a changed fact, and the risk of invention."

## Open questions for Anton

- None beyond the series questions.
