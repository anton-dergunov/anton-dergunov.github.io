---
post: _drafts/agent-memory/2199-01-01-agent-memory-4-mem0.md
type: system deep-dive
status: draft
---

# Brief: Mem0: facts in a vector store (part 4)

Shared material is in `series.brief.md`. Source: `v1/2199-01-01-agent-memory-5-mem0.md` (no notes from Anton yet), notebook `02-mem0`, `agent-memory-eval/docs/findings/mem0.md`.

## Reader

The series reader, who has probably seen Mem0's `add()`/`search()` demo and wants to know what happens between the two calls.

## The problem

Mem0 is the reference design of the field: a model extracts short standalone facts from a conversation, and a similarity search brings the closest ones back. It is the system almost every memory paper compares with. What a reader cannot see from the API is what happens to a fact that changes, what the search leaves out, and what dates end up on the facts.

## What the reader should leave with

1. Splitting a conversation into standalone facts is what lets a differently worded question find them. It is also where facts are lost: what the extractor does not write down is gone.
2. The paper's design decides ADD, UPDATE, DELETE or NOOP against the ten most similar facts. The current open-source release only adds. Old and new versions of a fact then sit side by side, and the reader has to sort them out.
3. A similarity score does not know that an allergy must never be cut. Close scores (0.59–0.74 here) mean the wording of the question decides what comes back.
4. Dates matter. The open-source library resolves "next week" against the day the code runs, not the day of the conversation.

## Outline

| Section | Claim it supports | Evidence or artefact to show | Figure |
|---|---|---|---|
| Opening | The reference design; the two choices in this part's words (a pipeline writes; a search selects); the notebook link | Problem above | `mem0` |
| Where it comes from | The Mem0 paper's two phases. Extraction: a summary, recent messages and the new pair, asking for salient facts. Update: the ten most similar stored facts, four operations chosen by the LLM through a tool call. The graph variant marks a fact invalid instead of deleting it. | v1 "What the paper describes". The paper's trade-off in one sentence: slightly below full context on LoCoMo, much faster (with LoCoMo explained in one clause). | `mem0-update` (paper vs release) |
| The test | Transcript (version B); this design is most tested by the reversal and by the cut at read time | Series brief | `conversation` |
| How a write works | Extract (one call per `add()`), look up related facts (embedding), write. In the release: add only, linking new facts to related ones by id. | Pseudocode of the write loop; the release's prompt line, quoted: "Your sole operation is ADD…" | `mem0-update` |
| The run traced: session 1 | Five standalone third-person facts; the date resolved against the wrong day ("week of October 12, 2026") | The table of five facts | none |
| The run traced: session 2 | Nine facts; the vegetarian line still there; the new fact describes the change itself ("transitioned from … to …"), because the old row was shown to the extractor. That saved this example and is not guaranteed. | The store as a table | none |
| The run traced: reading | `limit` is not a cap in this release; all nine come back, scores 0.59–0.74. Cut at six, both diet lines and the allergy would be gone. A different question ("what should I cook tonight?") reorders everything. | The scored list | a small score strip (optional, may reuse the `graphiti-floor` style) |
| Where it breaks | (1) Old and new facts both live. From the benchmark, in words: "three sessions" and "five sessions" kept as two facts and added up to eight. (2) A revision mentioned in passing is never extracted (the sculpture session with five facts about the sculpture and none about the hours). (3) Dates resolved against the wrong day. (4) Consistency is checked against ten neighbours only. How to notice: list the store after a revision; look for two values of one attribute. Fixes: pass the conversation's date; never cut some facts (O-Mem's argument: keep a profile of critical attributes, retrieved first); retire replaced facts (Memory-R1 trains the four operations; one paragraph, explained). | findings/mem0.md; v1 | none |
| Cost | Two model calls for two sessions plus four embedding calls; one embedding per question. The cheapest write in the series among systems that write. | notebook 02 | none |
| When it is the right design | The store will outgrow the prompt, reads must be fast, users must see and delete facts. It needs three things it does not provide: real dates, a rule for what is never cut, and a way to retire a fact. | v1 | none |
| How it was run / Try it | The real `mem0ai` library, local Qdrant, every call tapped | Links | none |

## Running example

Version B. Tested most by the reversal (both values kept) and by the cut at read time (the allergy at rank 7).

## Numbers

| Number | Out of what | From where | Compared with | So what |
|---|---|---|---|---|
| 9 facts, scores 0.589–0.740 | the example's store | notebook 02 | each other | The ranking is fragile; a cut at six drops the allergy |
| 2 model calls + 4 embedding calls | two sessions | notebook 02 | the other systems (without part numbers) | The cheapest write that extracts |
| 51.4% vs 25.7% outdated stance | PersonaMem-v3, changed preferences | §4.3, p. 17 | textual memory | Mention only with what the task measures, or cut |

## Figures to make

`mem0-update` (new). `mem0` and `conversation` are shared.

## Left out

- SeCom, xMemory and SAGE: cut, or one sentence each in a "relatives" paragraph, only if they explain a failure shown here. O-Mem and Memory-R1 stay, as fixes.
- HaluMem and the "agent-native" paper numbers: one of them stays as evidence for "extraction is where facts are lost", the other goes.
- LongMemEval scores (part 8).

## Links

- Notebook 02: https://anton-dergunov.github.io/agent-memory-eval/notebooks/02-mem0.html
- Papers: Mem0, O-Mem, Memory-R1, HaluMem, PersonaMem-v3

## For search and for employers

- Title: "Mem0: facts in a vector store"
- Excerpt: "What Mem0 does between add() and search(): extraction, the update step the release dropped, and what a similarity cut leaves out."

## Open questions for Anton

- Keep the relatives paragraph (SeCom, xMemory, SAGE) or cut to the two fixes?
