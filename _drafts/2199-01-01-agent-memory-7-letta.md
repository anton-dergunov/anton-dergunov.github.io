---
title:     "How LLM agents remember, part 7: Letta, an agent that edits its own memory"
topic:     llms-and-agents
date:      2199-01-01
permalink: /posts/2199/01/agent-memory-7-letta/
tags:
  - llm
  - agents
  - memory
published: false
---

<!-- SERIES -->

*How LLM agents remember*, a series in nine parts:

1. [One conversation, five memory systems](/posts/2199/01/agent-memory-1-why/)
2. [A map of memory systems](/posts/2199/01/agent-memory-2-the-map/)
3. [What ChatGPT, Claude and Gemini ship](/posts/2199/01/agent-memory-3-frontier-assistants/)
4. [Textual memory: one profile, rewritten](/posts/2199/01/agent-memory-4-textual-memory/)
5. [Mem0: facts in a vector store](/posts/2199/01/agent-memory-5-mem0/)
6. [Zep and Graphiti: facts with dates, in a graph](/posts/2199/01/agent-memory-6-graphiti/)
7. **Letta: an agent that edits its own memory** (this part)
8. [Honcho: a reasoner that works in the background](/posts/2199/01/agent-memory-8-honcho/)
9. [The experiment: 67 changed facts](/posts/2199/01/agent-memory-9-the-experiment/)

<!-- /SERIES -->

The running example of this series: in March a user tells an assistant they
are strictly vegetarian and have a severe peanut allergy; in July they say
they eat fish now, have moved to Kreuzberg, and that their sister Lena (no
shellfish) is coming with her partner Jonas (coeliac); in September they ask
the assistant to book dinner for the three of them
([part 1](/posts/2199/01/agent-memory-1-why/)). On the map of
[part 2](/posts/2199/01/agent-memory-2-the-map/), this part's system is the
answering agent writing its own memory, with a read path that inserts
everything it wrote.

## The idea

In [Letta][letta-repo], the memory is part of the prompt. A few labelled
blocks of text, such as `human` (what the agent knows about the user) and
`persona` (who the agent is), sit in every prompt the agent sees, and the
agent edits them itself with tool calls, in the middle of its turn. Older
messages leave the prompt and stay searchable through another tool.

{% include diagram.html name="letta" alt="Letta's architecture, with the running example. Writing: the answering agent itself decides mid-turn what to remember and edits its human memory block with a tool call (memory_replace); a sleep-time agent can do this in the background instead. Memory: small text blocks that are in the agent's prompt on every call, plus a recall log of every message. In July the vegetarian line was replaced in place, with no history kept. Reading: no search is needed for the blocks; the agent may search recall with a tool. All six constraints were in the prompt." %}

There is no extraction pipeline and no search over memories to miss: the
model that answers is the model that decides what to remember. That makes it
the purest version of the agent-managed design, and the reason it is here.

## Where it comes from: MemGPT

Letta is the company and the open-source server built around
[MemGPT][memgpt] (2023), which framed memory as an operating-system problem.
The prompt is main memory, split into read-only system instructions, a
*working context* (a fixed-size block of facts that only function calls can
write), and a first-in, first-out queue of recent messages. Everything else is
external: recall storage holds the full message history, archival storage
holds arbitrary text. The model's completions are read as function calls that
move data between the two. A `request_heartbeat=true` argument lets it chain
calls without a user turn in between, and when the prompt passes about 70% of
the window, a "memory pressure" warning tells the model to save what matters
before old messages are evicted into recall storage.

Two things in that design have travelled far. The always-visible working
context is the ancestor of every profile block that rewrites itself in place:
MIRIX's core memory, ChatGPT's saved memories, Letta's blocks. And the idea
that the model manages its own memory through tools reappears in Claude's API
memory tool ([part 3](/posts/2199/01/agent-memory-3-frontier-assistants/)).

MemGPT's own benchmark has not aged well. On DMR, a plain full-conversation
baseline now scores 94.4%, against 93.4% for MemGPT and 94.8% for Zep
([Zep][zep], p. 6, Table 1); the original headline gain had been over a lossy
summary baseline. Letta's team has since argued the point themselves: a Letta
agent on gpt-4o-mini that simply kept conversation histories in files scored
74.0% on LoCoMo, which they read as a sign that memory "is more about how
agents manage context than the exact retrieval mechanism used"
([Letta blog][letta-files], a vendor's own figure).

## The run

The [notebook][notebook] drives Letta's own base prompt and tool descriptions
from a short local loop, so each step can be printed, with
`gemini-3.1-flash-lite` at temperature 0. The agent's whole instruction about
memory is the base prompt:

> You have an advanced memory system that enables you to remember past
> interactions and continuously improve your own capabilities. Your memory
> consists of memory blocks and external memory: … Memory management tools
> allow you to edit existing memory blocks and query for external memories.

Nothing in it says when to write, or what to do when something written
becomes untrue. The `human` block is described as storing "key details about
the person you are conversing with". The tools are `memory_insert`,
`memory_replace` (an exact string replacement; "Do NOT attempt to replace
long strings") and `conversation_search`.

### Writing: the agent decides, in its turn

On the first message, which states the diet and the allergy, the agent
answered and wrote nothing. It wrote everything one turn later. After
session 1 the block read:

```text
The user is a vegetarian (8 years) and has a severe, anaphylactic peanut allergy.
They enjoy Indian cuisine, specifically paneer dishes.
Budget: ~40 euros per person.
Location: Berlin.
```

The default prompt never says when to write, so the timing is whatever the
model decides on a given turn. Here it caught up. In the LongMemEval run below
it often did not.

### Revising: overwritten in place

After session 2:

```text
The user is a pescatarian (started eating fish one month ago) and has a severe,
anaphylactic peanut allergy.
They enjoy Indian cuisine, specifically paneer dishes.
Budget: ~40 euros per person.
Location: Berlin (Kreuzberg).
Family: Sister (Lena) and her partner (Jonas) are visiting in the autumn. Lena
has a shellfish allergy, and Jonas is coeliac.
```

No search and no contradiction check were needed, because the whole block is
always in the prompt: the agent saw "vegetarian" and replaced it. Three things
about how it got there are the character of this design.

- **The old fact is gone.** The block says pescatarian. Nothing says the user
  was vegetarian until June, and there is no way to ask what was true in
  April. An edit leaves no history.
- **The dates are as said.** "Started eating fish one month ago", written in
  July, will still say one month ago when it is read in September, and "(8
  years)" will stay eight years for as long as the line does.
- **To change one line, the agent re-sent the whole block**, the very thing
  the tool's description says not to do. Every such edit is a chance to drop
  or reword a line that was not meant to change. One was reworded here: "Lena
  can't eat shellfish" became "Lena has a shellfish allergy".

### Reading

The block is in the prompt, so there is no retrieval to miss. The agent
searched its recall storage anyway, and the search results more than doubled
the prompt for that turn, from about 1,500 to 3,500 tokens. All the
constraints fit in 350 to 450 characters that are always present, and the
answers were the best of the four notebooks: the peanut allergy, both guests'
restrictions and Kreuzberg in the in-line run, and the diet as well in the
sleep-time run below.

### Moving the writing out of the turn

Letta also offers a *sleep-time* agent, after the [Sleep-time
Compute][sleep-time] paper, which shows that thinking about a context before
any question arrives can cut the compute needed at question time by about
five times at equal accuracy, and by 2.5 times per query when several related
questions share a context (abstract). In Letta the sleep-time agent is a
second agent that reads the transcript in the background and owns the memory
blocks; the primary agent that talks to the user loses its write tools.

The background agent wrote a better block, in four calls:

```text
- Dietary restrictions: Pescatarian (since June 2026), severe anaphylactic peanut allergy.
- Preferences: Enjoys Indian cuisine, specifically paneer dishes.
- Budget: Up to 40 euros per head.
- Location: Lives in Kreuzberg (since May 2026). Planning a dinner in Berlin for
  sister's visit (originally March 2026, now updated to autumn 2026).
- Guests: Sister (Lena) and her partner (Jonas).
- Guest dietary restrictions: Lena (no shellfish), Jonas (coeliac).
```

The dates are absolute, and Lena's constraint is kept as said. It also made a
mistake of its own: "originally March 2026, now updated to autumn 2026" merges
two visits into one that was postponed. The March visit happened. A model
rewriting a block is writing a summary, and a summary can be wrong.

The primary agent, left with only a search tool, fell apart. On the first turn
it searched recall six times and told the user "I have updated my records",
which it could not have done. On three of the seven turns it searched for
"human block", "human block value", "human block metadata", hit the step limit
of the loop, and gave no reply at all. The base prompt tells it that it has
memory blocks that tools can edit, and this small model kept trying to reach
them through the only tool it had. That is the model's failure, not the
design's, and a stronger model in the primary's seat would probably just
answer. It is still a fair example of the point: in this design, the behaviour
of the memory is the behaviour of the model operating it.

### Cost

11 model calls for six user turns in-line, 13 with the question: every memory
write is a second call before the reply. With the sleep-time split, 4 calls in
the background, and 34 that the user waited for, nearly all of them the search
loop; a primary that answered in one call per turn would have made 6.

## What it does well, and how it fails

**It does well** at the read path. The facts that matter are always in front
of the model, in a few hundred characters, and no similarity score decides
whether the allergy is included.

**It fails** where its write policy is whatever the model decides on the turn.
Nothing makes it write at the right moment, date what it writes, or keep the
earlier value. With a small model and a blank persona, all three go wrong, and
the run on real data shows how often.

## Relatives

The operating-system family hands the decision of what stays in context to
different deciders. [MemoryOS][memoryos] uses a "heat" score (visits,
interaction length, recency) to promote topic segments from a mid-term store
into a long-term profile of the user, and spends 4.9 model calls per response
against 13.0 for A-MEM (p. 7, Table 3). [MemOS][memos] schedules memories
across text, key–value cache and weights, and finds that injecting a memory as
a precomputed cache instead of prompt text cuts time-to-first-token by 19–94%,
most for long memories and short questions (p. 26, Table 8); that needs
control of the serving stack, which a hosted API does not give. [MIRIX][mirix]
routes entries into six typed stores (core, episodic, semantic, procedural,
resources, and a vault for sensitive data that ordinary retrieval cannot
reach), each managed by its own agent. Each of these adds a decision-maker
whose decisions now need evaluating, and none of the papers evaluates that
component on its own.

## On real data

The experiment in [part 9](/posts/2199/01/agent-memory-9-the-experiment/)
runs the real Letta server, 0.16.8 (its last Python release), self-hosted,
with Letta's defaults: one agent per question, the two default blocks, and
the server's sampling temperature of 1.0. It was run three times, and the
three runs make the point of this part better than the notebook does.

| Run | how it was fed | accuracy | revision written at the message | USD per question |
|---|---|--:|--:|--:|
| `letta-batch` | each session in one request, ending on an assistant message | 58% | | 0.03 |
| `letta` | one agent step per user message | 69% | 31 of 64 | 0.13 |
| `letta-persona` | the same, with three lines added to the persona | 90% | 57 of 64 | 0.15 |

**Fed a whole session at once**, the agent had nothing to answer and in most
sessions took no step at all: in a trace, 6 of 10 sessions produced nothing,
and the `human` block stayed empty after 43 of 67 histories.

**Fed one message at a time**, it edited memory about ten times per history
and scored 69% (95% interval 57–78%), the one system in the experiment clearly
below the others. Its failures were a chain of three, each of which the next
could have caught:

1. **It noticed the revision and did not write it down.** At the user message
   carrying the new value, it recorded the value in 31 of 64 questions. In 18
   of the others its own reply named it: "By the way, I just checked and I'm
   now at 600 followers" drew "Congratulations on hitting 600 followers!" and
   no memory edit.
2. **The search could not find what was not written.** On a self-hosted
   server, `conversation_search` is a literal phrase match that returns the
   five newest matching messages, though its description promises "hybrid
   search (text + semantic similarity)"; the semantic part needs a hosted
   vector service. The agent searched with paraphrases ("painting projects
   completed"), and 97 of its 146 searches at answer time returned nothing.
3. **It trusted a stale block.** In six wrong answers the block still said
   "has completed 4 projects", "recently hit 500 followers", the searches came
   back empty, and the agent answered from the block.

**Told what to do, it fixed most of it.** The persona block is the part of
Letta its users are meant to write, and it had been Letta's blank starter
text. Three lines were added, one per link of the chain:

> How I keep my memory of the user:
> - Every user message starts with its date in square brackets, for example
>   [2024-01-15 09:30]. I write that date on each fact I save about the user,
>   never the server's time shown on tool results or in my system prompt.
> - When the user mentions a new value for something already in my memory (a
>   count, a time, a place, a status), even in passing, I update that line at
>   once with memory_replace and keep the earlier value with its date, for
>   example "has 4 herb plants on the balcony (2024-03-02; earlier 2,
>   2024-01-15)".
> - When the user asks about themselves, I check my memory and also search
>   past messages. The search matches my query word for word, so I search with
>   one or two distinctive words, not a whole phrase.

The revisions written at the message rose from 31 to 57 of 64, the new value
was in memory at the end in 79% of questions instead of 42%, and the score
rose from 69% to 90% (80–95%), level with the other memory systems. The edits
now read "Reached 600 followers (2023-05-28; earlier 500, 2023-05-27)". Two
caveats belong next to that number. The persona was written after reading the
failures, on the same questions, so 90% is not a held-out score. And at
temperature 1.0 two runs of the same agent differ question by question. The
count of revisions written, 31 against 57, is the sharper measure.

Of the seven answers still wrong, one is a lost update, two had the right
dated lines and reasoned wrongly ("you switched to more water… you are now
using less water"), and one is a plan counted as a fact: "I'm definitely going
to add" two films turned 25 titles into 27.

## When it is the right design

Agent-managed memory is the right design when the agent is the product, the
memory is small enough to stay in the prompt, and the model in the seat is
strong enough to be trusted with the policy. Its read path is the best in this
series; its write path is as good as its instructions. What the experiment
suggests is that the instructions are not optional. A blank persona leaves the
three decisions that matter (when to write, how to date, what to do with the
old value) to chance, and three lines of English fixed most of what the
machinery around them could not. Moving the writing to a background agent
removes it from the turn, and adds a second model whose summary can be wrong
in its own way.

Next, [part 8](/posts/2199/01/agent-memory-8-honcho/) keeps the background
process and asks it to reason: Honcho.

The notebook for this part is [04-letta.ipynb][notebook]; the experiment's account
of every wrong answer, with every tool call logged, is in
[docs/findings/letta.md][findings].

## References

<!-- REFS -->

Papers:

- Packer et al., [MemGPT: Towards LLMs as Operating Systems][memgpt] (2023)
- Rasmussen et al., [Zep: A Temporal Knowledge Graph Architecture for Agent Memory][zep] (2025)
- Lin et al., [Sleep-time Compute: Beyond Inference Scaling at Test-time][sleep-time] (2025)
- Kang et al., [Memory OS of AI Agent][memoryos] (2025)
- Li et al., [MemOS: A Memory OS for AI System][memos] (2025)
- Wang and Chen, [MIRIX: Multi-Agent Memory System for LLM-Based Agents][mirix] (2025)

<!-- /REFS -->

Other sources:

- [Letta on GitHub][letta-repo]
- Letta, [Benchmarking AI Agent Memory: Is a Filesystem All You Need?][letta-files] (August 2025)

[memgpt]: https://arxiv.org/abs/2310.08560
[zep]: https://arxiv.org/abs/2501.13956
[sleep-time]: https://arxiv.org/abs/2504.13171
[memoryos]: https://arxiv.org/abs/2506.06326
[memos]: https://arxiv.org/abs/2507.03724
[mirix]: https://arxiv.org/abs/2507.07957
[letta-repo]: https://github.com/letta-ai/letta
[letta-files]: https://www.letta.com/blog/benchmarking-ai-agent-memory
[notebook]: https://github.com/anton-dergunov/agent-memory-eval/blob/main/notebooks/04-letta.ipynb
[findings]: https://github.com/anton-dergunov/agent-memory-eval/blob/main/docs/findings/letta.md

<!-- SERIES -->

---

[← Part 6: Zep and Graphiti: facts with dates, in a graph](/posts/2199/01/agent-memory-6-graphiti/) · [Part 8: Honcho: a reasoner that works in the background →](/posts/2199/01/agent-memory-8-honcho/)

<!-- /SERIES -->
