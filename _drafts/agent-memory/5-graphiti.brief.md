---
post: _drafts/agent-memory/2199-01-01-agent-memory-5-graphiti.md
type: system deep-dive
status: draft
---

# Brief: Zep and Graphiti: facts with dates, in a graph (part 5)

Shared material is in `series.brief.md`. Source: `v1/2199-01-01-agent-memory-6-graphiti.md`, notebook `03-zep-graphiti` (the deepest notebook: four steps, the four dates, three ways closing can fail, the 0.6 floor, the graph walk), `agent-memory-eval/docs/findings/graphiti.md`.

## Reader

The series reader, curious whether a knowledge graph is worth its weight for memory.

## The problem

Graphs are the most elaborate memory design in common use. Zep's Graphiti stores facts as edges between entities, gives every fact a date range, and closes a fact when a newer one contradicts it, so nothing is lost and "what was true in April?" becomes a filter. That is a lot of machinery, and many model calls per message. The question is what it buys over a list of facts, and where it breaks.

## What the reader should leave with

1. Graphiti closes a superseded fact cleanly: a model judges that two facts conflict, and ordinary code decides which ends and when, from the dates.
2. Its extraction prompt is written for named things. Attributes of a person, such as a diet or an allergy, are not stored until custom entity types are configured.
3. Storing an update and delivering it are separate problems. The search returned the closed fact and missed the new one, decided at the third decimal by a fixed 0.6 floor.
4. The graph earns its cost when a question names one thing and the answer is about something linked to it (sister → Jonas → coeliac). For facts that are one step from the user, a table with dates would do.
5. It is expensive and sensitive to how it is fed: one message per episode, as its own examples do.

## Outline

| Section | Claim it supports | Evidence or artefact to show | Figure |
|---|---|---|---|
| Opening | The two choices in this part's words (a pipeline writes into a dated graph; a search selects); the notebook link | Problem above | `graphiti` |
| Where it comes from | The Zep paper: three layers (episodes, entities and facts, communities); four timestamps on two timelines; three searches fused and reranked | v1 "What the paper describes", shortened. The paper's LongMemEval result vs full context in one sentence, labelled as the vendor's. | none |
| The test | Transcript; this design is most tested by the reversal (closing) and by the two-hop guests (the walk) | Series brief | `conversation` |
| How a message is written: four steps | Find entities → match to stored entities → extract facts → compare each new fact with related stored facts. Every message goes through all four, in order. | For each step, the instruction lines that do the work (e.g. the entity prompt's "could have their own Wikipedia article or database entry… when in doubt, do NOT extract"), and the step's output in the run | `graphiti-steps` |
| How time works | Four dates per fact: true in the world from/to, and known to the system from/to. A contradicted fact gets an end date, not a deletion. | Pseudocode of the closing rule; the four dates on the vegetarian fact | `graphiti-dates` |
| The run traced: session 1 | With the default prompt: three entities (Anton, Anton's sister, Berlin), no diet, no allergy. Custom entity types (Person, Place, Preference, HealthCondition) bring them in. | The entities before and after | none |
| The run traced: session 2 | The vegetarian edge closed on 2026-06-20; the repeated allergy caught as a duplicate between the same two nodes; "my sister Lena" matched, plain "Lena" not (0.595 vs 0.6), so a second Lena node | Notebook outputs | `graphiti-dates` |
| The run traced: reading | The default search returned nine facts, including the closed vegetarian one (0.608), and missed pescatarian (0.599), Jonas's coeliac disease (0.596) and Kreuzberg. The answer looked complete and was not. | The score table | `graphiti-floor` |
| What the graph buys | A walk from the named entities finds "Jonas is coeliac" in two steps, which text search cannot. The walk is not the default search; a tuned read (current facts only, text search, then a walk) found it. | Notebook section 5 | `graphiti-walk` |
| Where it breaks | (1) Prompt written for named things. (2) Fixed similarity floor. (3) Entity matching at a threshold, which duplicates nodes. (4) From the benchmark, in words: fed whole sessions, it extracted almost nothing (the prompts are written for one message from a named speaker); fed one message at a time, it worked, at about 2.7 times the cost. (5) Dating by when a fact became true can close the newer fact (Paris, said later, dated earlier). How to notice: count entities and facts per message; read the store after a revision. Fixes: custom entity types; one episode per message; current-facts-only search plus a walk. | notebook "What went wrong"; findings/graphiti.md | none |
| Cost | 36 model calls and 24 embedding calls for ten short messages; about 51,000 input tokens to store thirteen facts; the assistant's messages cost 9 calls for one fact nobody needed | notebook 03 | none |
| When a graph earns its cost | Questions that need history or paths between entities, and a willingness to tune prompts and thresholds for your data | v1 | none |
| How it was run / Try it | Graphiti's own prompts driven by local code, with no database; what is left out (summaries, communities, cross-encoder) | Links | none |

## Running example

Version B. Tested most by the reversal (the closing works) and by the two-hop guests (the search misses Jonas; the walk finds him).

## Numbers

| Number | Out of what | From where | Compared with | So what |
|---|---|---|---|---|
| 0.608 / 0.599 / 0.596 vs a 0.6 floor | cosine scores in the example | notebook 03 | the floor | Delivery decided at the third decimal |
| 36 calls vs 2 | writing the two sessions | notebook 03 and 02 | Mem0 (named, no part number) | The price of the machinery |
| 0.595 vs 0.6 | "Lena" against "Anton's sister" | notebook 03 | the floor | A duplicate node |

The 18%/82% result belongs to part 8. Here it appears in words only (fed whole sessions vs one message at a time).

## Figures to make

`graphiti-steps`, `graphiti-dates`, `graphiti-floor`, `graphiti-walk` (all new). `graphiti` exists.

## Left out

- The paper's community layer and rerankers in detail: one sentence.
- "Three reasons for a graph, and the case against" from v1: folded into "What the graph buys" and "When".
- LongMemEval scores.

## Links

- Notebook 03: https://anton-dergunov.github.io/agent-memory-eval/notebooks/03-zep-graphiti.html
- Papers: Zep

## For search and for employers

- Title: "Zep and Graphiti: facts with dates, in a graph"
- Excerpt: "How a temporal knowledge graph stores, dates and closes facts, and why its search returned the closed fact instead of the new one."

## Open questions for Anton

- None beyond the series questions.
