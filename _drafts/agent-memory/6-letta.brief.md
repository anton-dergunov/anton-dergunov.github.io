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

<Updated 2026-11-15 after notebook 04 was rerun (option B; the differences from the server are in `6-letta.runs.md`); the runs and replays are in `6-letta.runs.md`. Order as in part 3. Prompts and tool descriptions are quoted from the 0.16.8 server; replies and blocks from the rerun notebook.>

| Section | Claim it supports | Show in full | Figure |
|---|---|---|---|
| Opening | The pipelines write outside the conversation; here the answering agent writes, in its turn; blocks inserted, recall searched | Problem above | none |
| How Letta works | What the agent sees (MemGPT's main memory and disk); the base prompt says nothing on when or how to write; tools: exact-string replace, insert, both return the block; nothing keeps history; the self-hosted search matches whole phrases, five newest, tool messages dropped after the cut; the sleep-time variant (every 5 turns, its own prompt asks for absolute dates); what it does not do; the price of each choice | `letta_v1` prompt; block layout; `memory_metadata`; the three tool descriptions as sent (Examples, cut); pseudocode of the loop, the two tools and the search; the sleep-time prompt, persona and preface | `letta`, `letta-context`, `letta-turn`, `letta-search`, `letta-sleeptime` |
| The example, step by step | Session 1: nothing on the first message ("I have noted…"), one paragraph on the second; R2. Session 2: replaced in place, whole block re-sent twice, date vaguer, constraint reworded; R2b (persona lines: earlier value kept and dated). Session 3: five searches shortening to "Kreuzberg", matching only the agent's replies. Sleep-time: the primary claims "I've noted that change!"; the background agent writes "(next week)", a wrong month, merges two facts; the primary's reply promises a search that never runs. Cost | each session's transcript; the block after each session; each tool call; the search queries; the sleep-time blocks; the call table | `conversation`, `letta-block-diff`, `letta-cost` |
| Where it breaks | Failure 1 noticed and not written; 2 phrase search crowded by echoes; 3 trusts a stale undated block; 4 overwrite deletes the earlier value a question needs; 5 fed a whole session, no step. How to notice; the persona lines and what they changed (31 → 57 of 64), with the caveat | findings/letta.md quotes and counts; the persona text | `letta-chain` |
| When it is the right design | Use when / do not use when; against parts 3–5 | | none |
| History and related work | MemGPT (OS analogy, memory pressure, heartbeats, DMR saturated); what Letta dropped since (heartbeats, the warning); Sleep-time Compute; Mem-α; MemoryAgentBench; control-plane placement; ACE's context collapse; MIRIX, MemoryOS; memory security | papers in ~/papers with pages | none |
| Run it yourself | Re-implementation around Letta's text, behaving like a self-hosted server; what is simpler and why; ideas | links | none |

## Running example

Version B. Tested most by the reversal: whether and how the agent writes it.

## Numbers

| Number | Out of what | From where | So what |
|---|---|---|---|
| 17 calls, 47,677 tokens | in-line agent, 7 user turns | notebook 04 (rerun) | every edit and search is a call before the reply, with the whole prompt re-read |
| ~1,600 of 2,294 tokens | first call of a session | `count_tokens` on the prompt's parts | the tool descriptions, with their examples, are the largest part of every call |
| 16 + 4 calls | sleep-time set-up, user-facing + background | notebook 04 | the background agent is cheap; here the primary searched instead of editing |
| 2/10, 3/10 vs 0/10 | replays writing on the first message, shipped vs persona lines | R2 | the persona lines do not ask to save a first statement |
| 6/10 kept, 0/10 dated vs 10/10, 9/10 | replays at the revision message | R2b | the persona lines change what is written at a revision |
| 31 → 57 of 64 | revisions written at the message carrying them | findings/letta.md | the instruction is the policy; not a held-out score |
| 97 of 146 | answer-time searches that returned nothing | findings, recounted (R4) | phrase match cannot find paraphrases |
| median 3 calls, ~3× the first call | Letta's answer turn in the experiment | ledger (R3b) | the cost of searching is mostly re-sending the prompt |

Accuracies (58%, 69%, 90%) go to part 8.

## Figures to make

`letta` (exists; updated for the rerun). New, drawn 2026-11-15: `letta-context`, `letta-turn`, `letta-search`, `letta-sleeptime`, `letta-block-diff` (which also shows what each replace sent), `letta-cost`, `letta-chain`.

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
