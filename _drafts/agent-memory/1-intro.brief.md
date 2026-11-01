---
post: _drafts/agent-memory/2199-01-01-agent-memory-1-intro.md
type: series introduction
status: draft
---

# Brief: Why look inside agent memory (part 1)

Shared material (reader, terms, running example, which part owns which numbers, conventions) is in `series.brief.md`. Source: `v1/2199-01-01-agent-memory-1-why.md` and Anton's 10 notes on it, notebook 00, the repo README.

## Reader

The series reader (`series.brief.md`), meeting the topic for the first time. This is also the part a recruiter is most likely to open. The opening and the headings alone should say what was done and why it is interesting.

## The problem

ChatGPT and Claude now remember things about you between conversations, and dozens of libraries offer "memory" to developers, each with a paper saying it beats the others. From the outside there is no way to tell what any of them does with a conversation: what it keeps, what it drops, what happens when a fact changes, and what it puts back in front of the model. Their demos show the interface, not the mechanism, and their benchmark tables disagree with each other.

## What the reader should leave with

1. Memory is a loop around a model that forgets: something writes, something is stored, something is read back into the prompt.
2. Two choices explain most of a design: who writes, and whether everything is inserted or a search selects.
3. Memory systems break in ways that a score hides, and you find out by reading what they stored; this series shows where each one breaks, why, and what fixed it.
4. On a public benchmark, simple designs held up well and the large differences were in cost (general terms only).

## Outline

| Section | Claim it supports | Evidence or artefact to show | Figure |
|---|---|---|---|
| Opening (no heading) | Memory is now everywhere, and from the outside you cannot tell what it does; this series looks inside | The combined opening below | none |
| What "memory" means here | A model forgets between calls; a memory system decides what to keep, keeps it outside the model, and puts some of it back | v1 "What memory means here" | `overview` |
| Why the demos are not enough | The API shows how to call it; the ideas behind it are what decide whether it helps. The notebooks exist to build that intuition. | The `add("I like pizza")` / `search("food")` snippet, introduced respectfully as the standard demo, then the three questions it cannot answer | none |
| Where memory breaks | The series follows each system to where it fails: why, how to notice, and what fixed it | Two or three one-line failure stories in words, e.g. a graph that stored nothing about an allergy because its prompt asks for things with "their own Wikipedia article"; an agent that congratulated the user on a change and never wrote it down; a system that remembered only after the conversation was fed to it one message at a time | none |
| One small test | Why one small conversation, what it tests (a changed fact, a hard constraint, facts about people the question does not name), and the real situations where this matters | Running example, version A (series brief) | `conversation` (small) |
| Two choices that separate the designs | Who writes × insert or select, with the five systems placed | Short definitions, then the map | `map` |
| The parts, as a reading guide | One short paragraph per part, saying what a reader learns there and why it comes in that order. This replaces the linked table. | Series brief "The parts" | none |
| What the series found | Each design handles the changed fact in its own way; on a public benchmark the working designs land close together and differ mostly in cost; most lost facts are lost when writing | The five outcomes in one sentence each; the experiment in general terms (see Numbers) | `series` |
| How it was run | Why one small model everywhere; which systems ran as real code and which as re-implementations around the vendor's prompts, and why | v1 "How it was run", reworded so it reads as reasons, not as technical detail (Anton's note) | none |
| Try it | The repository and the six notebooks | Links | none |

### The opening, combined from the three angles (a shape for Anton to edit)

> I use ChatGPT and Claude every day, and over the last year both started to remember things about me between conversations. I wanted to know what that means mechanically. What does the assistant write down, and when? What happens to a note when I change my mind? What does it put back in front of the model the next time I ask something?
>
> The same question applies to the libraries that offer memory to developers. There are dozens of them, and each comes with a paper showing it beats the others. When other groups re-run the systems, the rankings do not hold. Most of what is written about them is either a feature table or a benchmark score, and neither says what the system does with a conversation.
>
> As an ML engineer I found the question familiar and unfamiliar at once. Much of agent memory is retrieval: finding the few stored items a request needs, which is close to work I have done before. The other half is new. Something has to decide what is worth keeping, and what to do when a new fact contradicts an old one.
>
> So I took five memory systems apart. I ran the same short conversation through each one with every model call printed, then checked what the conversation showed on a public benchmark. This series explains how each system works, where it breaks, and what it costs.

Anton's wording, his to change. The guide's rule: no numbers in this paragraph, and no claims beyond what he said.

## Running example

Version A from the series brief: abstract, no transcript, framed as a test. The diet is not named as the topic. The real-world list is `[TODO Anton]`.

## Numbers

Use in general terms only, each explained where it appears:

- **The benchmark:** LongMemEval, a public benchmark of long chat histories. This series used its 67 questions about facts the user had changed (out of 500 questions, of seven types). Say what it is in one sentence.
- **Accuracy band:** seven configurations scored between 82% and 97%, with overlapping intervals, against 90% for reading the whole history. *So what:* on this benchmark, working memory systems lose little against reading everything. Mention as "within a few points of each other", or give the band once.
- **Cost:** from $0.002 per question (keyword search over the raw turns) to $0.64 (Graphiti). *Compared with:* each other. *So what:* the large differences are in cost, about two orders of magnitude, not in accuracy.
- **[maybe] 18% vs 82%:** the same graph system, fed whole sessions vs one message at a time. *So what:* how a system is fed decides whether it remembers, and nothing warned. Only if explained in two sentences. Otherwise part 8 tells it.

## Figures to make

- `conversation`: new, `scripts/diagrams/figures/conversation.py` (shared with parts 3–7).
- `overview`, `map`, `series`: exist.

## Left out

- The full transcript, which goes to parts 3–7.
- The 18%/82% story as an opening; it opened v1 with numbers the reader could not interpret (Anton's notes).
- The linked table of parts, replaced by the narrative reading guide.
- "A cheap bill" (Anton: remove).
- Model names and temperatures in the body.
- Graphiti's 0.608 vs 0.599 detail, which belongs to part 5.

## Links

- Repository: https://github.com/anton-dergunov/agent-memory-eval
- Notebook 00 (the conversation, no memory and full context): https://anton-dergunov.github.io/agent-memory-eval/notebooks/00-introduction.html

## For search and for employers

- Title (under ~60 characters): "Why look inside agent memory" (series name in the kicker line)
- Excerpt: "What ChatGPT-style memory and open-source memory libraries actually do with a conversation, and where they break: a nine-part series."
- What this post shows about Anton's work: he frames a crowded topic around the questions that matter, designs a small test that exposes mechanisms, and backs it with a fair benchmark run. And he says what does not work.

## Anton's notes on v1, and where each is handled

| Note | Handled by |
|---|---|
| "There must be intro before that" (opening numbers) | New opening, no numbers |
| "Say that it was with changes" | Numbers: 18%/82% is explained with the feeding change, or moves to part 8 |
| "a cheap bill": remove | Left out |
| "Why this example" (pizza demo) | The demos section introduces it as the standard demo and says what it shows and what it cannot |
| "Need to say why we intro it here" (the conversation) | "One small test" says why the test exists before showing it |
| "Will be good idea to show the diagram here" (two choices) | `map` figure in that section |
| "Better to put into failures" (the "previously" clause) | Moves to part 3's failure section |
| "Rewrite to explain background" ("Wikipedia article") | A one-line failure story with its reason; the detail goes to part 5 |
| "Rewrite so it does not sound like tech detail" | "How it was run", as reasons |

## Open questions for Anton

- Is the combined opening right in substance? It is your own reasoning from the planning call; edit freely.
- Which real situations to name for the test case.
- Whether to include the 18%/82% story here in two sentences, or keep it for part 8.
