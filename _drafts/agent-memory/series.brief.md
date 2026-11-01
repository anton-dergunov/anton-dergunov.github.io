---
series: agent-memory
status: draft
---

# Series brief: How LLM agents remember

Working name; the candidates are under "Open questions". The earlier drafts in `v1/` are the material: their content stays, but their order and framing do not.

## Reader and purpose

**Reader.** A senior engineer from a neighbouring field: knows programming, retrieval and the basics of LLMs; does not know Mem0, Graphiti, Letta or Honcho, and has not read the other parts. Reads one part from top to bottom, on a tablet, once. May arrive at any part from a search or a link.

**Purpose.** Readers should come away understanding how agent memory works inside, enough to choose or build one, and seeing where each design breaks. An employer reading one opening, the headings and one figure should see an engineer who:
- takes systems apart call by call;
- runs a fair experiment;
- reads every failure, explains it, and fixes it;
- does not name a winner the data does not support.

**Why Anton did this.** These are general reasons only. The series never mentions client or startup work.
- He uses ChatGPT and Claude every day, both now remember things about him, and he wanted to know what that means mechanically.
- The field is crowded: every memory library has a paper showing it beats the others, and when other groups re-run the systems the rankings do not hold.
- It is close to his own background as an ML engineer: much of memory is retrieval, which he knows well; the write path, which decides what to keep and what to do when a fact changes, is the new part.

## The ideas of the series

1. **One loop.** Every memory system is the same loop around a model that forgets: write, store, read, use.
2. **Two choices.** Most of what a system does well, does badly and costs follows from two choices: who writes the memory, and whether the read path puts all of it into the prompt or a search picks part of it.
3. **Storing is not delivering.** Storing a fact and getting it to the answering model are separate problems, and most facts are lost at write time.
4. **Feeding matters.** How a system is fed decides whether it remembers at all, and nothing fails loudly when it is fed wrong.
5. **Cost.** Measured on cost as well as accuracy, simple designs hold up well while the history fits in the prompt.
6. **Where it breaks.** Each design breaks in its own way. You find out by reading what it stored, not by looking at its score, and the fixes are often small.

## The parts

| # | Working title | Type | Its job | Ideas |
|---|---|---|---|---|
| 1 | Why look inside agent memory | series introduction | Why this is worth understanding; the shape of the answer; a reading guide | 1, 2, 6 (5 in general terms) |
| 2 | How agent memory works | map | The loop, its operations, where memory can live, the two choices, the baselines, where the designs came from. The most visual part. | 1, 2, 3 |
| 3 | Textual memory: one profile, rewritten | system deep-dive | The simplest design: a background rewrite of one profile, inserted whole | 2, 3, 6 |
| 4 | Mem0: facts in a vector store | system deep-dive | Extraction into short facts, similarity search | 2, 3, 6 |
| 5 | Zep and Graphiti: facts with dates, in a graph | system deep-dive | A pipeline into a dated graph; closing superseded facts | 2, 3, 4, 6 |
| 6 | Letta: an agent that edits its own memory | system deep-dive | The answering agent writes, in its turn | 2, 4, 6 |
| 7 | Honcho: a reasoner that works in the background | system deep-dive | Conclusions at levels of certainty, with premises | 2, 3, 6 |
| 8 | The experiment: 67 changed facts | experiment | The same behaviour on a public benchmark: accuracy, cost, error analysis, decision guide | 3, 4, 5, 6 |
| 9 | What ChatGPT, Claude and Gemini ship | map | The products readers use, placed on the two choices; closes the series | 2, 5 |

**Order.** The systems run from the simplest to the most elaborate, which is the repo's notebook order. The experiment comes after the systems it measures. The assistants part comes last because it compares products against designs the earlier parts explain, and uses the experiment's findings (agents forget to write things down; an undated line goes stale). It is also the part most readers find most familiar, so it is a good place to end.

## The running example

**What and why.** One hand-written conversation in three sessions, run through every system in the notebooks.
- It is a test case, deliberately small, so that every model call can be printed and read.
- It is not the use case. Booking dinner is not the point; the diet is a fact that changed, not a theme.
- It was kept rather than replaced because everyday facts give a reader immediate intuition, and the notebooks' most instructive failures came from it.
- An alternative (a coding assistant) is parked in `agent-memory-eval/docs/tasks/alternative-example.md`.

**What it tests**, the same in every part:
- **A fact that changes:** a diet is stated, then revised four months later. This tests updating.
- **A hard constraint:** a severe allergy, an attribute of a person and not a named thing.
- **Facts about other people that the question does not name:** "my sister and her partner" never mentions Lena, Jonas, shellfish or gluten, and "Jonas is coeliac" can only be reached through two links. This tests retrieval.

**Version A, for part 1** (abstract; no transcript):
> To see what each system does, I wrote one short conversation and ran it through all of them. In the first session the user mentions a few facts about themselves, including a hard constraint. Four months later they change one of those facts and mention two other people with constraints of their own. In a third, new conversation they ask for something that is only right if the assistant kept the updated fact and can connect "my sister and her partner" to the two people it was told about. The example is small on purpose, so that every model call can be printed and read. The same problem appears whenever an assistant keeps facts that change: [TODO Anton: check this list] where someone works or lives, the current state of a project, a decision that was later reversed.

**Version B, for parts 3–7:** the short transcript from v1 part 1 (sessions of 14 March, 20 July and September), followed by the six needs a correct answer must cover: pescatarian and no longer vegetarian, no peanuts, no shellfish for Lena, no gluten for Jonas, a liking for Indian food, somewhere near Kreuzberg. Then one sentence on which part of the example this system's design is most tested by. Optionally a small `conversation` figure next to it.

**Version C, for part 8:** one sentence saying the benchmark tests the same thing at scale: a fact stated, then revised in passing.

**Part 9:** does not need the example. It may note that OpenAI's own memory post uses a vegetarian user asking for meal ideas.

## Which part owns which numbers

- **Part 8** owns the LongMemEval results: accuracies, intervals, costs, probe rates and failure counts.
- **Part 1** may summarise them in general terms, explaining each thing it mentions:
  - LongMemEval is a public benchmark of long chat histories with questions about facts the user changed;
  - most systems landed within a few points of each other and of reading the whole history;
  - the cheapest way to answer cost a fraction of a cent per question and the most expensive cost a few tens of cents, a difference of about two orders of magnitude;
  - [maybe] one system scored 18% or 82% depending only on how the conversation was cut before it was stored.
  At most about three numbers in a paragraph, none in the opening paragraph.
- **Parts 3–7** own their notebook run: calls, tokens, stored items, similarity scores. Each may use its system's characteristic failure from the benchmark as an example of the mechanism, described in words, without scores.
- **Part 2** owns the published numbers about the field (survey and paper figures). It does not use the experiment's numbers.
- **Part 9** owns the products' dates and the vendors' own figures (for example Mastra's), each labelled as the vendor's own.

## Shared conventions

- **The repository and the part's notebook are linked in the opening**, in a short line after the first paragraph or two. They are linked again in "Try it" at the end. Rendered notebooks: `https://anton-dergunov.github.io/agent-memory-eval/notebooks/NN-name.html`.
- **The two choices are re-introduced in every part, in two or three sentences of its own.** No "the map of part 2", no "compare Mem0 in part 5", no "as part 3 showed". Links to other parts are further reading only ("Part 4 looks at Mem0 in detail").
- **Navigation:** front matter `series: agent-memory` and `part: N`. The layout shows the list of parts at the top (collapsed) and previous/next at the end, from `_data/series.yml`. No navigation markers in the text.
- **"How it was run"**, near the end of each part, gives the model and why one small model was used everywhere (so that differences come from the memory systems, not the models), and which code ran: the real library, or a re-implementation around the vendor's prompts, and why (so every step can be printed). Model names and temperatures stay out of the body unless they change a result.
- **Prompts:** show the few instruction lines that do the work, quoted exactly, never a whole prompt. **Code:** pseudocode only for logic that is not a model call (for example Graphiti's rule for closing a fact, Honcho's level check). No library plumbing.
- **Where it breaks:** every system part has this section: what broke, why, how you would notice (what to read in the store), and what fixed it or would fix it.
- **References:** `[label]: https://arxiv.org/abs/ID` definitions plus a `<!-- REFS -->` marker; `~/projects/writing/writing-guide/tools/refs.py POST.md` fills the list from `~/papers`. Vendor pages are listed by hand under "Other sources".
- **Figures:** the `diagram.html` include (light and dark SVG). For Medium, the PNG versions that `draw_diagrams.py` writes.

## Terms

| Term | Definition to reuse |
|---|---|
| memory (of an agent) | any mechanism that carries information from one conversation to a later one, outside the model's weights |
| session | one conversation, with a date |
| write path / read path | what happens when a conversation is turned into memory / when a new request gets what it needs from memory |
| insert vs select | the whole memory goes into the prompt / a search picks part of it |
| knowledge update | a fact the user stated and later changed; the newer value must win |
| full context | the whole history put into the prompt; one of two baselines |
| retrieval over raw turns | a keyword search (BM25) over the stored messages, with nothing written; the other baseline |
| round | one user message and the assistant reply after it (the unit the retrieval baseline searches) |
| consolidation, updating, indexing, forgetting, retrieval, condensation | the six operations of the Rethinking-Memory survey; defined in part 2, and elsewhere only where used |

## Figures

Existing figures are in `agent-memory-eval/docs/figures/` and are copied to `images/posts/agent-memory/`. New figures get one module each in `agent-memory-eval/scripts/diagrams/figures/<name>.py`, drawn with `uv run scripts/draw_diagrams.py <name> --copy-to <blog>/images/posts/agent-memory/`, with examples copied from committed notebook outputs.

| Figure | Shows | Parts | Status |
|---|---|---|---|
| overview | the loop: write, memory, read, use | 1, 2 | exists |
| map | the systems on the two choices | 1, 2 | exists |
| series | the same conversation through five systems | 1 | exists |
| textual, mem0, graphiti, letta, honcho | each architecture with the example | 3–7 | exist |
| results | accuracy and cost per arm | 8 (maybe 1) | exists |
| answering | tokens and cost per answer once memory is built | 8 | exists |
| conversation | the three sessions on a timeline, and the six needs | 1, 3–7 | new |
| operations | the six operations placed on the loop | 2 | new |
| three-homes | text vs cache vs weights | 2 | new |
| writers | when each kind of writer runs, relative to the user's turn | 2 | new |
| insert-vs-select | the two read paths side by side | 2 | new |
| cost-timing | write once vs pay on every read (schematic) | 2 | new |
| timeline | memory papers and products, 2023–2026 | 2 | new |
| profile-diff | the textual profile after session 1 and after session 2, changes marked | 3 | new |
| mem0-update | extract, compare with similar facts, decide (paper: four operations; release: add only) | 4 | new |
| graphiti-steps | the four LLM steps for one message | 5 | new |
| graphiti-dates | the four timestamps on a fact, and how the old edge closes | 5 | new |
| graphiti-floor | similarity scores on a strip, with the 0.6 floor | 5 | new |
| graphiti-walk | sister → Jonas → coeliac | 5 | new |
| letta-context | the context window as RAM and the stores as disk | 6 | new |
| letta-turn | tool calls inside one agent turn | 6 | new |
| letta-sleeptime | the background agent that owns the blocks | 6 | new |
| honcho-levels | explicit → deductive → inductive, with premises | 7 | new |
| honcho-retire | retiring a fact retires what rested on it | 7 | new |
| benchmark-types | LongMemEval's abilities and question types: the paper's Fig. 1 (CC BY 4.0, with credit) or redrawn | 8 | new or reused |
| trimming | 48 sessions → 2 evidence + 8 distractors | 8 | new |
| probe-funnel | stored → still current → delivered → answered | 8 | new |
| decision-guide | which design for which situation | 8 | new |
| products-map | the products on the two choices | 9 | new (or `map` with a product layer) |
| chatgpt-timeline | saved memories → chat history → dreaming | 9 | new |
| claude-code-memory | an index always loaded, topic files read on demand | 9 | new |
| observer-reflector | Mastra's two background agents and their thresholds | 9 | new |

## Left out of the series

- **Memory of skills and procedures** (ExpeL, ReasoningBank): a different problem from memory of a user.
- **More vendors** (Cognee, MemOS, MIRIX, A-MEM as runs): the series explains five designs well instead of listing many.
- **Client work:** none of it, in any part.

## Links

- Repository: https://github.com/anton-dergunov/agent-memory-eval
- Notebooks (rendered): https://anton-dergunov.github.io/agent-memory-eval/notebooks/
- Findings: `agent-memory-eval/docs/experiment-results.md`, `docs/findings/*.md`
- Earlier drafts: `_drafts/agent-memory/v1/` (Anton's notes are in the `.notes.json` files beside parts 1, 2, 3, 4 and 9)
- Papers: `~/papers/library/llm/memory/`, notes in `~/papers/notes/`

## Open questions for Anton

- **Series name**, to decide when titles are reviewed:
  - "How LLM agents remember" (current; long);
  - "Inside agent memory" (matches the look-inside angle);
  - "Agent memory, opened up".
  A kicker line above the title, rendered from `series.yml`, would let each `title` be the part's own name and stay under ~60 characters.
- The list of real situations in version A of the running example.
- Whether part 1 should tell the 18%/82% story, or leave it to part 8.
