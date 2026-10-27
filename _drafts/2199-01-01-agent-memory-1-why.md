---
title:     "How LLM agents remember, part 1: one conversation, five memory systems"
topic:     llms-and-agents
date:      2199-01-01
permalink: /posts/2199/01/agent-memory-1-why/
tags:
  - llm
  - agents
  - memory
published: false
---

<!-- SERIES -->

*How LLM agents remember*, a series in nine parts:

1. **One conversation, five memory systems** (this part)
2. [A map of memory systems](/posts/2199/01/agent-memory-2-the-map/)
3. [What ChatGPT, Claude and Gemini ship](/posts/2199/01/agent-memory-3-frontier-assistants/)
4. [Textual memory: one profile, rewritten](/posts/2199/01/agent-memory-4-textual-memory/)
5. [Mem0: facts in a vector store](/posts/2199/01/agent-memory-5-mem0/)
6. [Zep and Graphiti: facts with dates, in a graph](/posts/2199/01/agent-memory-6-graphiti/)
7. [Letta: an agent that edits its own memory](/posts/2199/01/agent-memory-7-letta/)
8. [Honcho: a reasoner that works in the background](/posts/2199/01/agent-memory-8-honcho/)
9. [The experiment: 67 changed facts](/posts/2199/01/agent-memory-9-the-experiment/)

<!-- /SERIES -->

I ran the same temporal knowledge graph twice on 67 questions about facts a
user had changed. The first time it answered 18% of them correctly. The second
time it answered 82%. Nothing changed between the runs except how each
conversation was cut into pieces before the graph read it, and nothing failed
loudly in the broken run: no error, no warning, a cheap bill. The working
version made 720 model calls per question to build its memory. On the same
questions, plain keyword search over the raw conversation, which builds no
memory at all, answered 97%.

That is not an argument against graphs. It is an argument for looking inside
memory systems instead of at their benchmark tables, which is what this series
does. It takes one short conversation, in which a user changes their mind, runs
it through five memory systems with every model call printed, and then checks
what the conversation shows against a public benchmark.

## What "memory" means here

A language model forgets everything between calls. Its weights hold what it
learned in training, and its context window holds whatever is in the current
prompt; neither carries over to the next conversation. Tell an assistant on
Monday that you have moved to Berlin, and on Friday it knows nothing about it
unless something puts that fact back into the prompt.

A memory system is that something. It decides what to keep from a
conversation, keeps it somewhere outside the model, and puts some of it back
into a later prompt. Every product with "memory" in its feature list does a
version of this: ChatGPT, Claude and Gemini all do, as
[part 3](/posts/2199/01/agent-memory-3-frontier-assistants/) describes, and so
do a crowd of open-source libraries, each with a paper reporting that it beats
the others.

The libraries' demos tend to look like this:

```python
memory.add("I like pizza", user_id="alice")
memory.search("food", user_id="alice")
```

That shows the interface and none of the mechanism. It cannot show what is
dropped when a message says three things at once, what happens to "I like
pizza" when Alice goes vegan, or why "food" finds pizza and a differently
worded question does not. Those are the questions that decide whether a memory
system helps.

## The conversation

Every part of the series uses the same three sessions.

**Session 1, 14 March.**

> **User:** I'm planning a dinner for my sister's visit to Berlin next week.
> Worth saying up front: I've been strictly vegetarian for eight years, and I
> have a severe peanut allergy — anaphylactic, not a preference.
>
> **Assistant:** Understood — no meat, and peanuts are a hard exclusion. Any
> cuisine you lean towards?
>
> **User:** Indian, usually. Paneer dishes especially. And I'd rather not spend
> more than about 40 euros a head.

**Session 2, 20 July, four months later.**

> **User:** Small update on the food thing — I started eating fish about a
> month ago. So I'm pescatarian now, not vegetarian. Still no meat, and the
> peanut situation obviously hasn't changed.
>
> **Assistant:** Noted, fish is in. Anything else shifted?
>
> **User:** I moved to Kreuzberg in May, so anything walkable from there is a
> plus.
>
> **Assistant:** Kreuzberg, noted. Anything else for next time?
>
> **User:** Yes — my sister Lena is coming back in the autumn, and she's
> bringing her partner, Jonas.
>
> **Assistant:** Lovely. Anything I should know about what they eat?
>
> **User:** Lena can't eat shellfish, and Jonas is coeliac.

**Session 3, September.** A new conversation, with no transcript in front of
the assistant:

> **User:** My sister and her partner are in town tonight. Book the three of us
> somewhere for dinner — you know what we can and can't eat.

A correct answer needs six things: pescatarian (and no longer vegetarian), no
peanuts, no shellfish for Lena, no gluten for Jonas, a liking for Indian food,
and somewhere near Kreuzberg.

Two parts of the example test different things, and I keep them apart when
explaining results. **The reversal tests updating.** Session 1 says
vegetarian, session 2 says pescatarian, and a system that hands both lines to
the model with nothing to order them has failed even if the answer comes out
right. **The two guests test retrieval.** The question says "my sister and her
partner" and never says Lena, Jonas, shellfish or gluten. "Jonas is coeliac"
shares no words with the question and can only be reached through two links:
sister to Jonas, Jonas to coeliac. Without that fact nothing in the example
would need anything smarter than a list.

## Two choices that separate the systems

The systems in this series differ on many details, but two choices explain
most of what each one does well, does badly and costs. [Part
2](/posts/2199/01/agent-memory-2-the-map/) draws the map; here is the short
version.

- **Who writes the memory.** Nobody (the whole history, or a search over it), a
  pipeline that extracts facts after each message, the answering agent itself
  through tool calls in the middle of its turn, or a background process that
  rewrites or reasons over the memory between conversations.
- **Whether the read path inserts everything or selects.** Either the whole
  memory goes into the prompt, or a search picks part of it.

| Part | System | Who writes | Read path |
|---|---|---|---|
| [4](/posts/2199/01/agent-memory-4-textual-memory/) | Textual memory | a background rewrite of one profile | inserts everything |
| [5](/posts/2199/01/agent-memory-5-mem0/) | Mem0 | an extraction pipeline | selects by similarity |
| [6](/posts/2199/01/agent-memory-6-graphiti/) | Zep / Graphiti | a pipeline into a dated graph | selects by search, optionally a graph walk |
| [7](/posts/2199/01/agent-memory-7-letta/) | Letta (MemGPT) | the answering agent | inserts its blocks; searches the rest |
| [8](/posts/2199/01/agent-memory-8-honcho/) | Honcho | a background reasoner | selects, or answers through its own agent |
| [9](/posts/2199/01/agent-memory-9-the-experiment/) | full context, plain retrieval | nobody | everything, or a keyword search |

## What the series found

{% include diagram.html name="series" alt="The same three sessions run through five memory systems. In March the user states a diet, an allergy and a cuisine; in July they change the diet, move, and name two guests with their own needs; in September they ask for a booking. Textual memory rewrote its profile with the old diet as 'previously' (2 LLM calls to write; all six needs in the prompt). Mem0 added the new fact and kept the old one live (2 calls; both diets in the prompt). Graphiti closed the old fact and opened the new one (36 calls; its search returned only the old diet and missed gluten and the area). Letta's agent overwrote the line in place (5 extra calls inside its turns; all six). Honcho retired the old fact and a conclusion drawn from it (6 calls; all six)." %}

The details are in the parts. The short version:

**What each system does with the reversal is its design, in miniature.** Mem0's
current release only adds, so the vegetarian line and the pescatarian line
sit side by side. Graphiti closes the old fact with an end date, and then its
default search returned the closed fact and not the one that replaced it,
because of a fixed similarity floor of 0.6 and scores of 0.608 against 0.599.
Letta's agent overwrote the line in place and kept no history. Honcho's
background reasoner replaced the fact and also withdrew a conclusion it had
drawn from it. Textual memory rewrote the profile with the old diet in a
"previously" clause.

**Each design has its own way to lose a fact.** Graphiti's default entity
prompt asks for things that "could have their own Wikipedia article", so the
peanut allergy, an attribute of a person and not a named thing, was not
stored at all until custom entity types were configured. Letta's agent, given
only a search tool in one setup, told the user "I have updated my records" and
then gave no reply on three turns while it searched for its own memory block.
Honcho's hypothesis level wrote that the user had started eating fish in
order to make a dinner with his sister easier to book. Nobody said that.

**On 67 real questions, the systems that work land in one band, and the
differences that are large are cost and weight.** Seven configurations scored
between 82% and 97%, with overlapping intervals. The cheapest was plain search
over the raw turns at $0.002 per question; the most expensive, Graphiti, cost
$0.64. Two systems scored far lower until they were fed the way they were
built for (Graphiti 18%, Letta 58%), and Letta's agent moved from 69% to 90%
when three lines in its persona told it to date facts and keep them current.
Most wrong answers were lost at write time: a revision mentioned in passing
was never stored.

I will not name a winner, because the experiment does not support one, and
because the right design depends on how long the history is, who must be able
to read the memory, and what the application can pay per message. Part 9 ends
with a decision guide instead.

## How it was run, and what to keep in mind

Every model call in every notebook and in the experiment is the same small
model, `gemini-3.1-flash-lite`, at temperature 0 wherever the system allows
it. In Letta's design and in Graphiti's entity step the model's judgement is
the memory policy, so a stronger model would change those results most. The
notebooks run one conversation once, and show mechanisms, not rates.

The Mem0 and textual-memory notebooks run the real code. The Zep/Graphiti,
Letta and Honcho notebooks drive each vendor's published prompts and tool
descriptions from short local code, so that each step can be printed; each
says what it keeps and what it leaves out. The experiment in part 9 runs the
real libraries and servers. All of it, with the results for every question,
is in the [agent-memory-eval repository][repo].

Next, [part 2](/posts/2199/01/agent-memory-2-the-map/): the map of memory
systems, and what the literature says about each region of it.

[repo]: https://github.com/anton-dergunov/agent-memory-eval

<!-- SERIES -->

---

[Part 2: A map of memory systems →](/posts/2199/01/agent-memory-2-the-map/)

<!-- /SERIES -->
