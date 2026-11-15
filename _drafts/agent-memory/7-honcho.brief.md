---
post: _drafts/agent-memory/2199-01-01-agent-memory-7-honcho.md
type: system deep-dive
status: draft
---

# Brief: Honcho: a reasoner that works in the background (part 7)

Revised 2026-11-15, after reading Honcho v3.3.0's source, three runs of the real server on the example, and the rerun of notebook 05 (`7-honcho.runs.md`). Shared material is in `series.brief.md`. Sources: Honcho v3.3.0 (commit 608aec8); `replays/honcho_server_runs/run{1,2,3}.json`; notebook `05-honcho` (realigned with the server and rerun); `agent-memory-eval/docs/findings/honcho.md`; `results/main/honcho-*`; `v1/2199-01-01-agent-memory-8-honcho.md` for facts only.

## Reader

The series reader, interested in memory that infers things about a person and not only stores what they said.

## The problem

The other designs store what the user said. Honcho also stores what follows from it, in levels, and a derived conclusion records the conclusions it was drawn from. Two background jobs write: a deriver per batch of messages, and a "dream" in which two agents with tools add conclusions and delete outdated ones. The links make a question answerable that a list of facts cannot answer, namely what rested on a fact that stopped being true, but Honcho's dream does not ask it. And the system writes sentences about a person that nobody said.

## What the reader should leave with

1. Levels and links make an update traceable: what rested on a deleted fact can be computed by code. In Honcho v3.3.0 only removing a session from a scope uses the links; the dream's deletes leave the derived conclusions in place, and they reach the answer.
2. The model enforces most of the rules, and code enforces few: code checks that cited ids exist; the confidence rule, the minimum number of sources, the contradiction level and the order of levels are requests in prompts, or not there at all.
3. Derived levels are where a memory starts writing things nobody said. "Deductive" conclusions in the benchmark are often plausible guesses ("user is currently pregnant", from a question about pregnancy symptoms).
4. The cost of a dream is set by its agent rounds, not by the size of the store: each agent sees ten or twenty conclusions per tool call. That and the trigger (50 new conclusions, 8 hours, an idle hour) are why it runs in the background.
5. The read path decides what the stored conclusions do: dated lines given to the answering model kept answers that the dialectic agent's written answer lost, because its prompt says both "ask the user which statement is correct" and "the more recent statement supersedes".

## Outline

| Section | Claim it supports | Show in full | Figure | Words |
|---|---|---|---|--:|
| Opening | The problem; the two choices (a pipeline in the background writes; the read path is a selection or an agent); links | — | — | 350 |
| How Honcho works | Peers, collections, levels, the deriver (prompt, save rules), the dream (trigger, two agents, prompts, tools, grounding, soft delete), the peer card, the two read paths (dialectic prompt, prefetch; representation blend), what it does not do, the price | deriver prompt; deduction and induction prompts (peer-card section cut); tool list; dialectic prompt (enumeration/summarisation cut); one stored row as JSON; pseudocode for saving, the dream, grounding, the representation | `honcho`, `honcho-levels`, `honcho-deriver`, `honcho-dream`, `honcho-read` | 4,500 |
| The example, step by step | Server run 1 traced: session 1, dream 1, session 2, dream 2, session 3 (both read paths); the three runs compared; the notebook's link walk and checks; cost | session transcripts; deriver output; tool rounds; the store; representation; the dialectic reply | `conversation`, `honcho-retire`, `honcho-cost` | 3,500 |
| Where it breaks | **Failure 1** stale conclusions survive the update, and the dream rarely writes one at scale (0 of 158 deductions); **Failure 2** the dialectic asks the user (5 of the chat path's 9 wrong answers; v3.5.0 changed it); **Failure 3** guesses filed as deductions; **Failure 4** extraction keeps the value and drops the context; how to notice and fix | findings/honcho.md examples | `honcho-conflict`, `honcho-bench-levels` | 1,600 |
| When it is the right design | Use when the answers depend on what follows from what was said, and when what rests on a changed fact must be found; not for "remember the newest value" | — | — | 300 |
| History and related work | Generative Agents' reflections; violation of expectation; belief revision (Belief Memory, model editing); Honcho's own changelog | papers' page numbers | — | 700 |
| Run it yourself | The notebook drives Honcho's text with local functions; the server runs; ideas | — | — | 350 |

## Running example

Version B. Tested most by the fact that changes and by what was concluded from the old value; then by the read path.

## Numbers

| Number | Out of what | From where | Compared with | So what |
|---|---|---|---|---|
| 18–20 calls, 46–50k tokens in | storing two sessions, two dreams, one dialectic call | server runs 1–3 | notebook: 20 calls (+2 answers), 56k; other parts' costs | The dream is the cost |
| 3 of 3 runs wrote an update; 2 of 3 deleted a still-true fact; 3 of 3 kept conclusions resting on the old fact | the server runs | run files | the notebook | The update is a model decision; the links are not used |
| 7,434 / 158 / 146 / 0 | conclusions by level across 67 stores | results/main/honcho-repr | — | The dream writes little, and no contradictions |
| 0 of 158 | benchmark deductions that record an update | same, read by hand | probe: old value current in 64% | Failure 1 at scale |
| 5 of 9 | the chat path's wrong answers that were refusals over two values | findings/honcho.md | the representation path | Failure 2 |
| median 1 call | dialectic calls per benchmark question | ledger | up to 5 rounds allowed | It answered from its prefetch |

## Figures to make

`honcho` (redrawn), `honcho-levels`, `honcho-deriver`, `honcho-dream`, `honcho-retire`, `honcho-read`, `honcho-conflict`, `honcho-bench-levels`, `honcho-cost`.

## Left out

- Accuracies and intervals for the two read paths (part 8).
- Session summaries and the session-context endpoint (sessions here are too short to be summarised); scopes beyond the one rule they illustrate; workspace chat; surprisal beyond one sentence (off by default).

## Links

- Notebook 05: https://anton-dergunov.github.io/agent-memory-eval/notebooks/05-honcho.html
- Honcho repository at v3.3.0; Generative Agents; violation of expectation (Plastic Labs)

## For search and for employers

- Title: "Honcho: a reasoner that works in the background"
- Excerpt: "Memory that stores conclusions, not just statements: levels, premises, agents that reason over the store in the background, and what happens to a conclusion when the fact under it changes."

## Open questions for Anton

- Whether to keep "Beyond Honcho: abduction" in the notebook and the one paragraph about it in the post.
