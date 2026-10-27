---
title:     "How LLM agents remember, part 2: a map of memory systems"
topic:     llms-and-agents
date:      2199-01-01
permalink: /posts/2199/01/agent-memory-2-the-map/
tags:
  - llm
  - agents
  - memory
published: false
---

<!-- SERIES -->

*How LLM agents remember*, a series in nine parts:

1. [One conversation, five memory systems](/posts/2199/01/agent-memory-1-why/)
2. **A map of memory systems** (this part)
3. [What ChatGPT, Claude and Gemini ship](/posts/2199/01/agent-memory-3-frontier-assistants/)
4. [Textual memory: one profile, rewritten](/posts/2199/01/agent-memory-4-textual-memory/)
5. [Mem0: facts in a vector store](/posts/2199/01/agent-memory-5-mem0/)
6. [Zep and Graphiti: facts with dates, in a graph](/posts/2199/01/agent-memory-6-graphiti/)
7. [Letta: an agent that edits its own memory](/posts/2199/01/agent-memory-7-letta/)
8. [Honcho: a reasoner that works in the background](/posts/2199/01/agent-memory-8-honcho/)
9. [The experiment: 67 changed facts](/posts/2199/01/agent-memory-9-the-experiment/)

<!-- /SERIES -->

In [part 1](/posts/2199/01/agent-memory-1-why/) a user tells an assistant
about a diet, changes it four months later, mentions two guests, and then asks
for a dinner booking that only works if all of that was remembered. This part
is the map for the rest of the series: what every memory system has in
common, the two choices that separate them, and where each system I ran sits.

## A stateless model and the loop around it

A language model has two memories built in. Its weights hold what it learned
in training, and its context window holds whatever is in the current prompt.
Neither carries over from one conversation to the next. Tell an assistant on
Monday that you have moved to Berlin, and on Friday it knows nothing about it
unless something puts that fact back into the prompt.

"Memory", in the literature on agents, means any mechanism that carries
information across that gap. Strip the branding and every system I have read
about is the same loop wrapped around a model that does not change:

{% include diagram.html name="overview" alt="The loop every memory system in the series is built on. Write: a conversation is turned into memory (consolidation, updating), and the question is who writes: nobody, a pipeline, a background process or the answering agent. Memory: what is kept, in a shape that differs per system (a text profile, a list of facts, a dated graph, blocks in the prompt, conclusions at levels). Read: a new question gets what it needs (retrieval, condensation), and the question is whether everything is inserted or a search selects. Use: the answering model gets instructions, what memory returned, and the question." %}

The survey [Rethinking Memory in LLM-based Agents][rethinking] names six
operations inside that loop, and it is worth having the vocabulary, because
most papers improve one of them and are silent about the rest:

| Operation | What it does | When it runs |
|---|---|---|
| Consolidation | turns an interaction into candidate memories | write |
| Updating | reconciles a candidate with what is stored: add, merge, replace, ignore | write |
| Indexing | builds whatever structure a read will use | write |
| Forgetting | drops or decays entries | write, often in batch |
| Retrieval | finds the entries a request needs | read |
| Condensation | turns the entries found into something short enough for the prompt | read |

The split between write and read is the one that matters for cost. Work on the
write path is paid once per conversation and can run in the background. Work
on the read path is paid on every request, while the user waits. A system that
moves work from reading to writing buys latency with money, and a benchmark
that does not time the write never sees the bill.

## Five questions that separate the designs

Papers in this area each introduce a system with its own name and its own
diagram. Read side by side, most of them differ only in how they answer five
questions:

1. **What is one memory?** A raw turn, a topic segment, an extracted fact, an
   entity with its relations, a lesson from a past task, a block of text, a
   hidden state, a change to the weights.
2. **Who decides what to write?** Nobody (keep everything), a fixed rule, a
   model following a prompt, a policy trained for the job, or the answering
   agent itself.
3. **What shape is the store?** A flat list, a graph, tiers, several typed
   stores, a single document, a cache inside the model, the weights.
4. **How is a read chosen?** Embedding similarity, keywords, a walk through a
   graph, searches the model issues itself, or nothing at all: everything is
   inserted.
5. **When is the work done?** At write time, in the background, or at read
   time.

Two of these, the second and the fourth, are the axes of this series. Before
that, though, one choice comes before all five.

## Where the memory lives: text, cache or weights

The survey [Memory in the Age of AI Agents][age-of-agents] makes the location
of the memory its first axis, and it decides more than any other design
choice:

| | Text (token memory) | Cache (latent memory) | Weights (parametric memory) |
|---|---|---|---|
| What it is | facts, notes or summaries put into the prompt | hidden states or key–value pairs the model attends to | knowledge trained or edited into parameters |
| Cost of a read | prompt tokens on every request | a forward pass over the cache | nothing beyond the normal forward pass |
| Cost of a write | one or more model calls | a forward pass, or training per corpus | training or an edit |
| Can a person read it? | yes | no | no |
| Can one fact be deleted? | yes | rarely | no |
| Works with a hosted API? | yes | no | no |

Every system in this series stores text, and so does almost every
agent-memory system in production, because only text can be shown to a user,
deleted on request, and handed to whichever model answers next. The other two
forms are real research directions, so here they are in one paragraph each,
before I leave them.

**Latent memory** keeps the model's own internal states. [Memorizing
Transformers][memorizing] attends over a searchable cache of past key–value
pairs. [MemoryLLM][memoryllm] keeps a fixed pool of memory vectors in every
layer and updates it with forward passes alone; a fact mostly decays after
about 30 updates (p. 7, Fig. 5). [Cartridges][cartridges] trains a compact
cache per document collection offline and matches in-context quality with
38.6× less memory (p. 1), at about 30 minutes on eight H100s per corpus
(p. 12). Reads are cheap; nobody can read what was stored.

**Memory in the weights** puts knowledge into parameters. [MEMIT][memit] edits
thousands of facts directly into a transformer. [Memory Layers at
Scale][memory-layers] adds very large sparse key–value layers and nearly
doubles factual question answering at the same compute (NQ 13.68 against
7.76 for a dense 1.3B model, p. 8, Table 1). [Titans][titans] trains a small
memory network while the model reads, with a learned forget gate, but resets
it for every sequence, so it is a long working memory rather than a memory of
a user. And edits do not propagate: in [Fundamental Problems With Model
Editing][model-editing], accuracy on downstream facts that should change after
an edit falls from 0.97 to 0.01 (p. 14, Table 4). An update to "moved to
Berlin" should also change "nearest airport", and an edit to the weights does
not.

The surveys agree on a division of labour: text for facts that change often
and must be auditable, weights for stable general knowledge, latent memory
where compactness matters. Facts about one user that change next week are the
first kind. The rest of this series is about text.

## The two axes

Within text memory, two choices explain most of what a system does well, most
of what it does badly, and most of what it costs.

**Who writes the memory.** Nobody, a pipeline that runs after each message, a
background process that runs between conversations, or the answering agent
itself, through tool calls in the middle of its turn. This decides when facts
are lost (a pipeline loses what its prompt does not ask for; an agent loses
what it does not bother to write down) and who has to resolve a contradiction.

**Whether the read path inserts everything or selects.** Either the whole
memory goes into the prompt, or a search picks part of it. Inserting
everything cannot miss, and stops working when the memory outgrows the
prompt. Selecting scales, and every selection is a chance to leave out the
one fact that mattered.

Here is every system in the series, and the products from
[part 3](/posts/2199/01/agent-memory-3-frontier-assistants/), on that map:

{% include diagram.html name="map" alt="A map of memory systems on two axes: who writes the memory (nobody, a pipeline, the answering agent, a background process) and whether the read path inserts everything or selects. Nobody writes: full context inserts everything; plain retrieval, and Claude's and ChatGPT's search over past chats, select. A pipeline writes: Mem0 and Zep/Graphiti select. The answering agent writes: Letta's core memory blocks and ChatGPT's saved memories are inserted; Letta's archival store and Claude's API memory tool select. A background process writes: textual memory, Mastra's Observational Memory and ChatGPT's dreaming summary are inserted; Honcho selects." %}

| Who writes | Read path: insert everything | Read path: select |
|---|---|---|
| Nobody | full context (the whole history in the prompt) | plain retrieval over raw turns; Claude's and ChatGPT's search over past chats |
| An extraction pipeline | | Mem0; Zep/Graphiti |
| The answering agent | Letta's core memory blocks; ChatGPT's saved memories (2024) | Letta's archival store; Claude's API memory tool |
| A background process | textual memory; Mastra's Observational Memory; ChatGPT's "dreaming" summary | Honcho |

Two things about this table are worth saying before the system parts fill it
in.

"A text file" does not mean "no retrieval". Claude Code keeps an index file
that is always loaded and topic files that the model reads only when it needs
them: the always-loaded part is on the left, the topic files on the right.
The defining choice is whether the read path inserts or selects, not the
storage format.

And the cells are not rankings. The left column is better while everything
fits. In the notebook run of [part 6](/posts/2199/01/agent-memory-6-graphiti/),
the one system that really selected was the one that missed the most of what
the question needed, because a store of thirteen facts is a store that should
simply have been inserted whole. The right column earns its keep when the
memory no longer fits, and nothing in a small example shows that.

## What the store costs and what the prompt costs

The fifth question, when the work is done, is why published costs are so hard
to compare. Storage, ingestion and reading are three different budgets, and a
paper tends to report the one that flatters it. The [Mem0 paper][mem0] gives
the clearest example, measured on LoCoMo conversations (p. 14):

- Mem0's store holds about 7,000 tokens per conversation.
- Zep's graph holds more than 600,000 tokens for the same conversation, many
  times the raw conversation it was built from.
- Both put only 1,000–3,000 tokens into the prompt.
- New memories in Zep became usable only hours after they were written,
  because the graph is built by a queue of model calls.

That last measurement comes from a competitor, and I treat it as such. The
point stands without it: the size of the store and the size of what reaches
the prompt are unrelated numbers, and so are the cost of building the memory
and the cost of reading it. In [part 9](/posts/2199/01/agent-memory-9-the-experiment/)
the systems I ran differ by a factor of 360 in what they put into the prompt
and by more than 300 times in what they cost per question, with accuracy inside
the same interval.

## What memory is not

Two neighbours get confused with memory, and both are baselines for it.

**Retrieval-augmented generation** retrieves from a corpus someone else wrote.
There is no write decision, no contradiction between an old fact and a new
one, and no forgetting. A memory system that only searches the raw history is
retrieval, and it should be measured as such. In this series it is: plain
BM25 over the raw turns is one of the two baselines.

**A long context window** removes the need to select rather than selecting
well. The other baseline is to put the whole history in the prompt. That
baseline is strong. In the Mem0 paper's own table, full context scores 72.90
on LoCoMo against 66.88 for Mem0 (p. 11, Table 2); what Mem0 buys is a p95
latency of 1.44 seconds against 17.12. On MemoryAgentBench, run by a different
group, long-context agents lead overall ([Evaluating Memory in LLM
Agents][memoryagentbench], p. 8, Table 3). Memory starts to win when the
history no longer fits, or when the model reads a long history badly. On
[LongMemEval][longmemeval], whose histories are about 115,000 tokens long,
GPT-4o drops from 0.870 when given only the relevant sessions to 0.606 when
given all of them (p. 6, Fig. 3), and the [Zep paper][zep] reports 71.2%
against 60.2% for full context with 1.6K tokens in the prompt instead of 115K
(p. 7, Table 2).

So the first row of every results table in this series is the whole history
in the prompt, and the question for every system is what it buys over that.

## Where the designs came from

Three papers from 2023 contain most of the ideas the 2025 products are built
on.

[Generative Agents][generative-agents] stored everything a simulated character
perceived as a timestamped stream, ranked entries by a sum of recency,
importance and relevance, and every so often asked the model to write
"reflections", higher-level conclusions, back into the stream. Background
reasoning over memory, which is what Honcho does in
[part 8](/posts/2199/01/agent-memory-8-honcho/), descends from that.

[MemoryBank][memorybank] added a portrait of the user, synthesised from the
history, and a forgetting curve after Ebbinghaus: a retention score
`R = e^{-t/S}` whose strength `S` grows each time a memory is recalled. The
paper is candid that this is exploratory, and it never says how a low score
becomes a deletion (p. 4). The portrait is the ancestor of every
profile-document design, including the textual memory of
[part 4](/posts/2199/01/agent-memory-4-textual-memory/).

[MemGPT][memgpt] treated the context window as RAM and an external store as
disk, and gave the model function calls to move information between them. A
small editable block of facts stays in the prompt; older messages are evicted
to a searchable log. That is Letta, in
[part 7](/posts/2199/01/agent-memory-7-letta/).

Then came 2025: Zep in January, A-MEM, Mem0 in April, then MemoryOS, MemOS
and MIRIX by July, each with a paper and each reporting that it beat the others on
LoCoMo. And 2026 was mostly the year other groups re-ran them. Their findings,
which the [last part](/posts/2199/01/agent-memory-9-the-experiment/) comes
back to, are that a plain long context often matches memory systems, that the
published rankings do not reproduce, and that updating a fact is where they
fail.

## What this series runs

Each system part follows one conversation through one design, with every
model call shown, and then checks the same behaviour on real data.

| Part | System | The idea it represents | Why it is included |
|---|---|---|---|
| [4](/posts/2199/01/agent-memory-4-textual-memory/) | Textual memory | a separate call rewrites one text profile under a size cap | the baseline to beat, and closest to what consumer products ship |
| [5](/posts/2199/01/agent-memory-5-mem0/) | Mem0 | a pipeline extracts short facts into a vector store | the simplest complete design, and the reference every paper compares with |
| [6](/posts/2199/01/agent-memory-6-graphiti/) | Zep / Graphiti | a pipeline writes facts as dated edges in a graph and closes superseded ones | the only one that models time explicitly |
| [7](/posts/2199/01/agent-memory-7-letta/) | Letta (MemGPT) | the answering agent edits its own always-visible memory through tool calls | the agent-managed design |
| [8](/posts/2199/01/agent-memory-8-honcho/) | Honcho | a background reasoner derives conclusions at stated levels of certainty | the only one that stores inferences, not just statements |
| [9](/posts/2199/01/agent-memory-9-the-experiment/) | Full context, plain retrieval | nothing is written | the floor, and the reference for every cost |

Two honest notes about what "run" means. The Mem0 and textual-memory
notebooks run the real thing. The Zep/Graphiti, Letta and Honcho notebooks
drive each vendor's published prompts and tool descriptions from short local
code, so that every step can be printed; each says at the top what it takes
from the original and what it leaves out. The experiment in part 9 runs the
real libraries and servers: Mem0 2.2.1, Graphiti 0.31.1 on Neo4j, Honcho 3.3.0
and Letta 0.16.8.

I left out systems on purpose. Cognee sits in the same cell as Graphiti and is
aimed at knowledge from documents more than at a user whose preferences change.
A seventh or eighth vendor would turn the series into the kind of list it is
meant to improve on. Memory of skills and procedures (agents that keep lessons
from past tasks, such as [ExpeL][expel] or [ReasoningBank][reasoningbank]) is
a different problem from memory of a user, and it is not covered either.

Next, [part 3](/posts/2199/01/agent-memory-3-frontier-assistants/) puts
ChatGPT, Claude and Gemini on this map, from what their makers have published.

## References

<!-- REFS -->

Papers:

- Du et al., [Rethinking Memory in LLM based Agents: Representations, Operations, and Emerging Topics][rethinking] (2025)
- Hu et al., [Memory in the Age of AI Agents][age-of-agents] (2025)
- Wu et al., [Memorizing Transformers][memorizing] (2022)
- Wang et al., [MEMORYLLM: Towards Self-Updatable Large Language Models][memoryllm] (2024)
- Eyuboglu et al., [Cartridges: Lightweight and general-purpose long context representations via self-study][cartridges] (2025)
- Meng et al., [Mass-Editing Memory in a Transformer][memit] (2022)
- Berges et al., [Memory Layers at Scale][memory-layers] (2024)
- Behrouz et al., [Titans: Learning to Memorize at Test Time][titans] (2024)
- Hase et al., [Fundamental Problems With Model Editing: How Should Rational Belief Revision Work in LLMs?][model-editing] (2024)
- Chhikara et al., [Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory][mem0] (2025)
- Hu et al., [Evaluating Memory in LLM Agents via Incremental Multi-Turn Interactions][memoryagentbench] (2025)
- Wu et al., [LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory][longmemeval] (2024)
- Rasmussen et al., [Zep: A Temporal Knowledge Graph Architecture for Agent Memory][zep] (2025)
- Park et al., [Generative Agents: Interactive Simulacra of Human Behavior][generative-agents] (2023)
- Zhong et al., [MemoryBank: Enhancing Large Language Models with Long-Term Memory][memorybank] (2023)
- Packer et al., [MemGPT: Towards LLMs as Operating Systems][memgpt] (2023)
- Zhao et al., [ExpeL: LLM Agents Are Experiential Learners][expel] (2023)
- Ouyang et al., [ReasoningBank: Scaling Agent Self-Evolving with Reasoning Memory][reasoningbank] (2025)

<!-- /REFS -->

[age-of-agents]: https://arxiv.org/abs/2512.13564
[rethinking]: https://arxiv.org/abs/2505.00675
[generative-agents]: https://arxiv.org/abs/2304.03442
[memorybank]: https://arxiv.org/abs/2305.10250
[memgpt]: https://arxiv.org/abs/2310.08560
[mem0]: https://arxiv.org/abs/2504.19413
[zep]: https://arxiv.org/abs/2501.13956
[longmemeval]: https://arxiv.org/abs/2410.10813
[memoryagentbench]: https://arxiv.org/abs/2507.05257
[memorizing]: https://arxiv.org/abs/2203.08913
[memoryllm]: https://arxiv.org/abs/2402.04624
[cartridges]: https://arxiv.org/abs/2506.06266
[memit]: https://arxiv.org/abs/2210.07229
[memory-layers]: https://arxiv.org/abs/2412.09764
[titans]: https://arxiv.org/abs/2501.00663
[model-editing]: https://arxiv.org/abs/2406.19354
[expel]: https://arxiv.org/abs/2308.10144
[reasoningbank]: https://arxiv.org/abs/2509.25140

<!-- SERIES -->

---

[← Part 1: One conversation, five memory systems](/posts/2199/01/agent-memory-1-why/) · [Part 3: What ChatGPT, Claude and Gemini ship →](/posts/2199/01/agent-memory-3-frontier-assistants/)

<!-- /SERIES -->
