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

<Order follows the system deep-dive skeleton in writing-guide `structure.md` (2026-11-12): mechanism first, the example traced session by session with cost, failures, judgement, history last. "Show in full" lists what the section shows verbatim; prompts are shown whole, with […] for cuts.>

| Section | Claim it supports | Show in full | Figure | Words |
|---|---|---|---|--:|
| Opening | The two choices in this part's words (the answering agent writes; the blocks are inserted, the rest is searched); the notebook link | Problem above | `letta` | 250 |
| How Letta works | The context as memory: system instructions, memory blocks written only through function calls, a queue of recent messages; external stores searched through tools. A turn: read the message, optionally call `memory_insert`, `memory_replace` or `conversation_search`, chain calls, reply. Nothing in the base prompt says when to write. The sleep-time variant moves the writing to a background agent. What it does not do: no separate writer after the session (in the default), no history of edits. | The base prompt in full and the tool descriptions ("Do NOT attempt to replace long strings"); a memory block as stored | `letta`, `letta-context`, `letta-turn` | 1,100 |
| The example, step by step | What it tests, as a list (does the agent write the reversal, and how). Session 1: wrote nothing on the first message and everything one turn later. Session 2: "vegetarian" replaced in place; no history; "one month ago" and "(8 years)" undated; the whole block re-sent to change one line, against the tool's own advice; "can't eat shellfish" reworded. Reading: no retrieval to miss; it searched anyway and doubled the prompt. Moving the writing out of the turn: a sleep-time agent owns the blocks and writes better ones, with absolute dates, but merges two visits into one; the primary agent, left with only a search tool, looped and gave no reply on three turns, using this small model. Cost: every memory write is an extra call before the reply: 11 calls for six user turns in-line; sleep-time 4 in the background. | Each session's transcript in its subsection; the block after each session, as a diff; both sleep-time blocks; the "human block" search loop | `conversation`, `letta-sleeptime` | 1,500 |
| Where it breaks | From the benchmark, in words. **Failure 1:** it notices and does not write: "Congratulations on hitting 600 followers!" and no edit. **Failure 2:** the self-hosted search is a literal phrase match; paraphrased searches come back empty. **Failure 3:** it trusts a stale block. Fed a whole session at once, it mostly took no step. How to notice: read the block after each revision; count edits per history. Fix: the three persona lines, quoted exactly, and what they changed (revisions written at message 31 → 57 of 64), with the caveat that they were written after reading the failures. | findings/letta.md (linked here); v1 "On real data" (counts only; accuracy goes to part 8) | none | 600 |
| When it is the right design | The agent is the product, the facts fit in blocks, and you will write the persona that tells it when and how to write | v1 | none | 200 |
| History and related work | **MemGPT:** the prompt as main memory and external stores as disk, with one sentence on why an operating system is the analogy; "memory pressure" warnings tell the model to save before eviction; its benchmark is now saturated, in one sentence. **Sleep-time Compute.** **Relatives:** MemoryOS, MemOS, MIRIX, one sentence each, only if explained. | v1, v1 "Relatives" | none | 450 |
| Run it yourself | Letta's own prompt and tools driven by a local loop; part 8 for scale; ideas to try | Links | none | 200 |

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
