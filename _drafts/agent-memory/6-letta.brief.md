---
post: _drafts/agent-memory/2199-01-01-agent-memory-6-letta.md
type: system deep-dive
status: draft
---

# Brief: Letta: an agent that edits its own memory (part 6)

Shared material is in `series.brief.md`. Source: `v1/2199-01-01-agent-memory-7-letta.md`, notebook `04-letta`, `agent-memory-eval/docs/findings/letta.md` (the longest findings file), `docs/tasks/letta-persona-rerun.md`.

## Reader

The series reader, who has heard of MemGPT, or who builds agents and wonders whether the agent should manage its own memory.

## The problem

What if no pipeline decides what to remember, and the agent that answers does it itself, with tool calls in the middle of its turn? Letta (from MemGPT) keeps a few small blocks of text in every prompt and lets the agent edit them. No search can miss what is always in the prompt. But the memory policy is now whatever the model decides on a given turn.

## What the reader should leave with

1. Blocks that are always in the prompt make reading trivial and reliable. All the facts that mattered fit in a few hundred characters.
2. When the agent writes in its turn, writing is optional. With no instruction on when to write, it often notices a change and does not write it down.
3. An edit in place keeps no history, and an undated line ("one month ago", "recently hit 500") goes stale silently.
4. Three lines of instruction (date every fact; update the line and keep the earlier value; search with one or two words) fixed most of it. In this design, the persona is the memory policy.
5. How it is fed matters: sent a whole session ending on an assistant message, the agent had nothing to answer and wrote nothing.

## Outline

| Section | Claim it supports | Evidence or artefact to show | Figure |
|---|---|---|---|
| Opening | The two choices in this part's words (the answering agent writes; the blocks are inserted, the rest is searched); the notebook link | Problem above | `letta` |
| Where it comes from: MemGPT | The prompt as main memory (system instructions, a small working context written only through function calls, a queue of recent messages) and external stores as disk. Function calls move data between them; "memory pressure" warnings tell the model to save before eviction. | v1, plus one sentence on why an operating system is the analogy (Anton's note on part 2). MemGPT's benchmark is now saturated, in one sentence. | `letta-context` |
| The test | Transcript; this design is most tested by the reversal (does the agent write it, and how) | Series brief | `conversation` |
| How a turn works | The agent's loop: read the message, optionally call `memory_insert`, `memory_replace` or `conversation_search`, chain calls, reply. Nothing in the base prompt says when to write. | The base prompt lines and the tool descriptions, quoted ("Do NOT attempt to replace long strings") | `letta-turn` |
| The run traced: session 1 | Wrote nothing on the first message and everything one turn later | The block, shown | none |
| The run traced: session 2 | "vegetarian" replaced in place; no history; "one month ago" and "(8 years)" undated; the whole block re-sent to change one line, against the tool's own advice; "can't eat shellfish" reworded | The block, shown | none |
| The run traced: reading | No retrieval to miss; it searched anyway and doubled the prompt | notebook 04 | none |
| Moving the writing out of the turn | A sleep-time agent (after the Sleep-time Compute paper) owns the blocks and writes better ones, with absolute dates, but merges two visits into one. The primary agent, left with only a search tool, looped and gave no reply on three turns, using this small model. | Both blocks; the "human block" search loop | `letta-sleeptime` |
| Where it breaks | From the benchmark, in words. (1) It notices and does not write: "Congratulations on hitting 600 followers!" and no edit. (2) The self-hosted search is a literal phrase match; paraphrased searches come back empty. (3) It trusts a stale block. Fed a whole session at once, it mostly took no step. How to notice: read the block after each revision; count edits per history. Fix: the three persona lines, quoted exactly, and what they changed (revisions written at the message 31 → 57 of 64), with the caveat that they were written after reading the failures. | findings/letta.md; v1 "On real data" (counts only; accuracy goes to part 8) | none |
| Cost | Every memory write is an extra call before the reply: 11 calls for six user turns in-line; sleep-time 4 in the background | notebook 04 | none |
| When it is the right design | The agent is the product, the facts fit in blocks, and you will write the persona that tells it when and how to write | v1 | none |
| Relatives | MemoryOS, MemOS, MIRIX: each adds a decision-maker; one sentence each, only if explained | v1 "Relatives" | none |
| How it was run / Try it | Letta's own prompt and tools driven by a local loop | Links | none |

## Running example

Version B. Tested most by the reversal: whether and how the agent writes it.

## Numbers

| Number | Out of what | From where | Compared with | So what |
|---|---|---|---|---|
| 31 → 57 of 64 | revisions written at the message carrying them, in the benchmark | findings/letta.md | before and after the persona lines | The sharpest evidence that the instruction is the policy; not a held-out score |
| 97 of 146 | searches at answer time that returned nothing | findings/letta.md | all searches | Phrase-match search cannot find paraphrases |
| ~1,500 → ~3,500 tokens | the prompt in the reading turn | notebook 04 | without the search | The search was unneeded and costly |

Accuracies (58%, 69%, 90%) go to part 8.

## Figures to make

`letta-context`, `letta-turn`, `letta-sleeptime` (new). `letta` exists.

## Left out

- The Letta blog's LoCoMo figure (a vendor's own number), unless it is used to make the "memory is managing context" point.
- Detailed MemOS cache timings.

## Links

- Notebook 04: https://anton-dergunov.github.io/agent-memory-eval/notebooks/04-letta.html
- Papers: MemGPT, Sleep-time Compute

## For search and for employers

- Title: "Letta: an agent that edits its own memory"
- Excerpt: "When the agent decides what to remember: always-visible memory blocks, why it forgets to write, and the three persona lines that fixed it."
- What this post shows: Anton diagnosed a chain of three failures and fixed it with one change, honestly scoped.

## Open questions for Anton

- None beyond the series questions.
