---
title:     "Why look inside agent memory"
excerpt:   "LLM assistants and agents now remember their users, and from the outside you cannot tell what their memory does. A nine-part series that takes five memory systems apart, measures them, and compares them with what ChatGPT, Claude and Gemini ship."
topic:     llms-and-agents
date:      2199-01-01
permalink: /posts/2199/01/agent-memory-1-intro/
share:     true
series:    agent-memory
part:      1
tags:
  - llm
  - agents
  - memory
---

Since 2024, LLM assistants have started to remember their users. ChatGPT, Claude and Gemini carry what they learn from one conversation into the next, and the coding agents from the same companies have started to do the same. Developers who build their own LLM agents can add memory from one of many open-source libraries. In each case, a memory system sits between the conversations. It decides what to keep from a conversation, stores it outside the model, and puts some of it into the prompt of a later conversation.

What the memory puts into the prompt decides the answer. Yet neither the user nor the developer can see what was kept, or what was put back. And when memory goes wrong, nothing reports an error. A fact that was never stored, or an old value that was never replaced, still produces a fluent and confident answer.

The published comparisons do not tell you which design to use either. Most memory libraries come with a paper in which they beat the others. When other groups run the same systems, with their own settings, the order changes. On the same benchmark, one well-known memory system came out one point behind its main rival in one paper, and seventeen points ahead of it in another.

I build LLM agents, and I wanted to understand why a memory system works, not only whether its score is high. Much of agent memory is retrieval: finding the few stored items that a new request needs. As an ML engineer, I knew that part well. The other part was new to me. Something has to decide, during a conversation or after it, what is worth keeping, and what to do when a new fact contradicts an old one.

So I took five memory systems apart. This series shows how each one works, with every prompt it sends and everything it stores. It follows one short test conversation through each system, one model call at a time. It then measures all five on a public benchmark, on cost as well as accuracy. It ends with the memory that ChatGPT, Claude and Gemini ship, compared with the same designs.

All the code, the notebooks and the results for every question are in the [agent-memory-eval repository][repo].

## What a memory system does

A language model sees only the text in its current prompt. Its weights hold what it learned in training and do not change while you use it. Its context window holds the current prompt and is gone when the call ends. Neither carries anything from one conversation to the next. Tell a coding agent on Monday that the project has moved from MySQL to PostgreSQL. On Friday, in a new session, it does not know this, unless something puts that fact back into its prompt.

A memory system is that something. Every memory system in this series has two parts:

- a **write path**, which turns a conversation into memory: it decides what is worth keeping, reconciles it with what is already stored, and stores it;
- a **read path**, which runs when a new request arrives: it finds what the request needs in the memory and puts it into the prompt.

The model that answers does not change. Everything a memory system does, it does through the prompt.

{% include diagram.html name="overview" alt="The two paths of a memory system, around a model that does not change. Write: a conversation is turned into memory; consolidation turns it into candidate memories, and updating adds, merges, replaces or ignores each one. The question here is who writes: nobody, a pipeline, the answering agent or a background process. Memory: what is kept, in a shape that differs per system: a text profile (textual memory), a list of facts (Mem0), a graph with dates (Zep/Graphiti), blocks in the prompt (Letta), conclusions at levels (Honcho). Read: a new question gets what it needs; retrieval finds it and condensation makes it short enough. The question here is whether the whole memory goes in or a search selects part of it. Use: the answering model receives the instructions, what memory returned, and the new question." caption="The two paths of every memory system in this series. The systems differ in what fills each step, and in the shape of what they keep." %}

Each path has its own hard part:

1. **The write path has to decide before anyone asks.** When a conversation is stored, nobody knows yet which of its facts a later request will need. A fact mentioned in passing, in a message about something else, is easy to miss.
2. **Facts change.** A user moves, changes jobs, changes their mind. The newer value has to win, and sometimes the older value still matters ("where did I live last year?").
3. **The read path has to find what a request needs**, even when the request shares no words with the stored fact, and it has to fit what it finds into a prompt of limited size.

[Part 2][part-2] gives the full picture: where else memory can be kept (the model's internal state or its weights), the operations on the two paths, the questions on which designs differ, and what independent research has found.

## How the designs differ

Memory systems differ in many details: what unit they store (a message, a fact, a profile), the shape of the store (a list, a vector index, a graph), and when they run. Two questions, though, explain most of what a design does well, does badly and costs.

**1. Who writes the memory?**

- **Nobody.** The raw conversation is the memory, and the read path searches it or reads all of it.
- **A pipeline** of model calls that runs after each message or each session and extracts what to store.
- **The answering agent itself**, which edits its memory with tool calls in the middle of its turn.
- **A background process** that rewrites the memory, or reasons over it, between conversations.

Each writer runs at a different moment, sees a different part of the conversation, and misses facts in its own way.

**2. How much of the memory reaches the prompt?**

- **All of it.** The whole memory is inserted into every prompt. Nothing can be missed, but the memory must stay small enough to fit, and every request pays for reading it.
- **A part chosen by a search.** The memory can grow without limit, but the search can leave out the one fact that the request needed.

The map below places the systems of this series on these two questions, together with the memory of several products.

{% include diagram.html name="map" alt="A map of memory systems on two axes: who writes the memory (nobody, a pipeline, the answering agent, a background process) and whether the read path inserts everything or selects. Nobody writes: full context inserts everything; plain retrieval, and Claude's and ChatGPT's search over past chats, select. A pipeline writes: Mem0 and Zep/Graphiti select. The answering agent writes: Letta's core memory blocks and ChatGPT's saved memories are inserted; Letta's search over its message log and Claude's API memory tool select. A background process writes: textual memory, Mastra's Observational Memory and ChatGPT's dreaming summary are inserted; Honcho selects." caption="The systems run in this series (in boxes) and the memory of several products (in italics), placed on the two questions. Some systems sit in two cells, because one part of their memory is always inserted and another is searched." %}

## How this series looks inside

The series takes the systems apart rather than comparing their feature lists. These are the choices behind it, each with its reason.

- **Five systems, from the simplest to the most elaborate.** Textual memory (one profile, rewritten after each conversation), [Mem0][mem0-repo], [Zep and Graphiti][graphiti-repo], [Letta][letta-repo] and [Honcho][honcho-repo]. With the two baselines described below, they cover every kind of writer and both kinds of read path on the map above. Their code is open, so every step can be read.
- **Every prompt and every stored item, shown.** What a memory system does is decided by its prompts and by the code around them. Each part shows the prompts in full, and what was stored after each step.
- **One small test conversation.** Each system part follows the same short, hand-written conversation through the system. The user states some facts, changes one of them months later, mentions other people with needs of their own, and finally asks for something that is right only if the memory kept the newer value and can connect the people. The conversation is small on purpose, so that every model call can be printed and read.
- **The vendors' own code and prompts.** The textual-memory notebook is the whole implementation, in a few dozen lines, and the Mem0 notebook runs the real library. The notebooks for Graphiti, Letta and Honcho drive the vendors' own prompts and tools from short local code, so that each step can be printed; each says what it keeps and what it simplifies. The benchmark runs the real libraries and servers.
- **One small model for everything.** Every system writes and answers with the same model, so that differences come from the designs and not from the models. It is a small model, and a stronger one would write better memory. An independent study ([MemoryTax][memorytax], 2026) shows why this matters: a stronger model reading the memory did not recover what a weaker model had left out when writing it.
- **A public benchmark, on cost as well as accuracy.** One short conversation shows how a mechanism works, but not how often it fails. [Part 8][part-8] runs all five systems and two baselines without memory on a public benchmark, with the same answering prompt and the same judge. For every answer, it also records what the system had stored and what reached the answering model, so that each wrong answer can be traced to the step that lost it.
- **The products, from what can be seen.** ChatGPT, Claude and Gemini cannot be run as libraries. [Part 9][part-9] uses vendor pages, the code that some vendors publish, and reverse engineering, and marks every claim with the kind of source it rests on.

## The parts of the series

Each part is written to be read on its own. Read in order, they go from concepts, to five designs, to measurement, to products.

**[Part 2, How agent memory works.][part-2]** The general picture, before any one system. Where memory can be kept (as text, in the model's internal state, or in its weights) and why almost every system keeps text. The labels other articles use for kinds of memory. The write and read paths, and the operations on each. Five design questions, what writing and reading cost, and how memory differs from retrieval and from a long prompt. What independent research has found, and the three papers from 2023 whose ideas later systems reuse. Start here if the field is new to you.

**[Part 3, Textual memory: one profile, rewritten.][part-3]** The simplest design, and the baseline for the others. After each conversation, one model call rewrites a single text profile, and the whole profile goes into every prompt. It handles a changed fact well, because the rewrite sees the old and the new value together. It also changes things that nobody asked it to change.

**[Part 4, Mem0: facts in a vector store.][part-4]** A pipeline extracts short facts from each conversation, and a similarity search picks the facts for a new request. The part shows what happens between `add()` and `search()`: the update step that the paper describes and the current release removed, the links between facts that the library drops, and what a similarity cut leaves out.

**[Part 5, Zep and Graphiti: facts with dates, in a graph.][part-5]** A pipeline of four model calls per message builds a knowledge graph, and every fact in it carries the dates when it was true. A contradicted fact is closed, not deleted, so old values stay as history. It is the most expensive design here in model calls, and its search can return the closed fact instead of the one that replaced it.

**[Part 6, Letta: an agent that edits its own memory.][part-6]** The opposite choice: the agent that answers the user also decides what to remember, and edits small blocks of text that are in every prompt. Whatever is in the blocks always reaches the model. But the agent often does not write, and three lines in its instructions changed that more than anything else.

**[Part 7, Honcho: a reasoner that works in the background.][part-7]** Memory that stores conclusions, not only what the user said: what follows from a statement, and patterns across several, each linked to what it was drawn from. Agents reason over the store between conversations. The part asks what happens to the conclusions when a fact underneath them changes.

**[Part 8, Evaluating memory systems on LongMemEval.][part-8]** The five systems and two baselines on a public benchmark: accuracy, cost, and why each wrong answer was wrong. It ends with a guide to which design to use when.

**[Part 9, What ChatGPT, Claude and Gemini ship.][part-9]** How the assistants and their coding agents remember, placed on the same two questions, with one run of an open design close to what the products describe.

The systems come from the simplest to the most elaborate, because each later design adds parts to the earlier ones and is easier to follow after them. The benchmark comes after the systems it measures. The products come last, because they are compared with the designs and with the benchmark's findings.

## What the series found

The details are in the parts. In short:

### Finding 1: the designs land close together in accuracy, and far apart in cost

[LongMemEval][longmemeval] (Wu et al., 2024) is a public benchmark of long chat histories between a user and an assistant, with questions about what the user said. The series used its 67 questions about a fact that the user stated and later changed in passing. Each history was cut to 10 sessions, about 25,000 tokens, so it still fits into the prompt of a current model.

On these questions, eight configurations of the systems and baselines scored between 82% and 97%. With only 67 questions, the intervals of these scores overlap, so their order is not a result. Reading the whole history, with no memory system, scored 90%.

The costs were far apart. A keyword search over the raw messages, which writes no memory at all, was at the top of the range and cost $0.002 per question. The knowledge graph (Zep and Graphiti) cost $0.64 per question, more than 300 times as much, for no gain in accuracy here.

{% include diagram.html name="results" alt="Two panels for nine configurations on 67 LongMemEval questions about changed facts. Accuracy with 95% intervals: full context 90%, retrieval 97%, textual memory 93%, Mem0 84%, Graphiti 82%, Letta 69%, Letta with a persona that keeps facts current 90%, Honcho dialectic chat 87%, Honcho representation 93%. Cost per question, building the memory included: full context $0.007, retrieval $0.002, textual memory $0.022, Mem0 $0.039, Graphiti $0.640, Letta $0.132, Letta with the persona $0.152, Honcho chat $0.029, Honcho representation $0.028." caption="Accuracy and cost per question on the 67 questions, with 10 sessions of history each. The shaded band is the interval of reading the whole history (full context). Part 8 explains every row." %}

These histories fit into the prompt, and each history had one question. A check on 25 of the questions with their whole histories, about 108,000 tokens each, kept the same order, while reading everything slipped by two answers and the cost of writing a memory grew with the history. With many questions about one history, a memory that is written once would pay off sooner. An independent study on another benchmark ([MemoryTax][memorytax], 2026, one conversation of LoCoMo) points the same way: with strong models, Mem0 did not beat reading the whole history, and building Mem0's memory alone cost more than the whole run of reading everything.

### Finding 2: the most common loss is a change that was never stored

When a memory system answered wrongly, the most common single cause was that the change had never been stored: 4 of Mem0's 11 wrong answers, 6 of Graphiti's 12, and 14 of Letta's 21. The change was usually one clause in a message about something else, such as "By the way, I just finished my 5th project since starting painting classes". A keyword search over the raw messages cannot lose a fact this way, because it writes nothing.

Larger studies point the same way. [HaluMem][halumem] (2025) scores each step of the write path, and most systems it tests extract fewer than 60% of the facts they should. [PersonaMem-v3][personamem-v3] (2026) finds that a text memory that is rewritten as it grows drops or rewords about 14% of its lines at each update, although most of the content survives in other words (p. 22). The same study also finds that, on its tasks, the larger problem is how the answering model judges the evidence it is given, rather than whether the evidence reaches it (p. 23): storing a fact is only the first step.

### Finding 3: with dates, a memory does not have to resolve every change

Most systems did not resolve a change when they wrote it. Mem0, for example, still presented the old value as current in 43% of the questions that have an earlier value, because its current release only adds facts. Yet when both values reached the answering model, each with its date, the model picked the newer one in most cases: in 41 of 45 such questions for Mem0. With dates, resolving the change at write time became an optimisation rather than a requirement. Without them, an old line such as "recently hit 500 followers" reads as current months later.

### Finding 4: how a system is fed decides whether it remembers at all

The first run of Graphiti answered 18% of the 67 questions. It cut each conversation into pieces of up to 8,000 characters, many messages each. But Graphiti's prompts are written for one message from one speaker, and they tell the model not to extract anything it is unsure of. With long pieces, the model extracted two or three things from each, and most of the changes were never stored. Fed one message at a time, as Graphiti's own examples do, the same system answered 82%.

No setting changed between the two runs, and nothing reported an error in the first. Letta's first run failed in a similar way: it was sent each conversation at once, had nothing to reply to, and mostly wrote nothing. The lesson: look at what a memory system stored before you look at its score.

### Finding 5: each design breaks in its own way, and the fixes are often small

The failures follow from the designs:

- **The text profile** is rewritten whole, so each rewrite can also change what nobody asked it to change: a month became an exact date, and a constraint was reworded into a different claim.
- **Mem0** only adds. An old value and the new one stay side by side as two facts, and an answer once added them up.
- **Zep and Graphiti**, in the test conversation, closed an outdated fact correctly, and then its search returned the closed fact and missed the one that replaced it, because the new fact scored just under a fixed similarity threshold.
- **Letta's agent** often noticed a change and did not write it down. It replied "Congratulations on hitting 600 followers!" and made no memory edit. Three lines added to its instructions, saying when to write, how to date a change and what to do with the old value, raised its accuracy from 69% to 90%. (The lines were written after reading its failures, so 90% is not a score on unseen data.)
- **Honcho's** background reasoning deleted an outdated fact, and kept the conclusions it had drawn from that fact.

None of these shows in a score. Each one was found by reading what the system stored and what reached the answering model. And several fixes were small: three lines of instructions for Letta's agent, one message at a time for Graphiti, and the conversation's own dates passed in when Mem0 writes.

### Finding 6: the products converged on text

None of the assistants ships a vector store of facts or a knowledge graph as its memory. They ship a summary, a list of short entries or plain Markdown files, put into the prompt, and often a search over past chats. They disagree about who should write: ChatGPT and Codex moved the writing into a background process, while the Claude app moved toward writing during the conversation. The problem they all describe is staleness: a fact that was true, and then changed. And the coding agents arrived at the same layout: a short index loaded into every session, and topic files read only when the index points to them.

### No single winner

The data does not support a winner, and the right design depends on the situation: how long the history is, whether a person must be able to read and correct the memory, how many model calls per message the application can pay for, and whether questions need earlier values as well as current ones. [Part 8][part-8] ends with a guide to which design to start from in which situation.

## Further reading

These are the sources I found most useful, beyond the papers that the parts cite.

**Surveys**

- [Memory for Autonomous LLM Agents][autonomous] (Du, 2026): the shortest survey, organised along three axes, with practical advice.
- [Memory in the Age of AI Agents][age-of-agents] (Hu et al., 2025): the fullest map of the field, from text to the model's weights.
- [Rethinking Memory in LLM-based Agents][rethinking] (Du et al., 2025): memory described as six operations, which part 2 uses.

**Where the ideas come from**

- [Generative Agents][generative-agents] (Park et al., 2023): a stream of memories scored by recency, importance and relevance, and reflections drawn from it.
- [MemGPT][memgpt] (Packer et al., 2023): the context window treated as the main memory of an operating system, managed by the model itself; Letta grew out of it.

**Measuring memory**

- [LongMemEval][longmemeval] (Wu et al., 2024): what a memory benchmark should test, and why a long prompt struggles with it.
- [Are We Ready For An Agent-Native Memory System?][agent-native] (Zhou et al., 2026): twelve systems compared one module at a time (storage, extraction, retrieval, maintenance), with the finding that no system leads on every task. Two of its authors work for the company behind one of the systems tested (MemOS).
- [MemoryTax][memorytax] (Peng, 2026): a short study of whether designed memory still helps once the model is strong enough to search the raw history itself.
- [DolphinBench][dolphinbench] (Rathi et al., 2026): a benchmark from Mem0's authors that tests memory through tasks rather than questions, and requires cost and latency next to accuracy.

**Engineering posts**

- Lilian Weng, [LLM Powered Autonomous Agents][weng] (2023): the memory section shows how the field first saw memory, as a vector store searched at question time.
- Harrison Chase, [Memory for agents][chase] (LangChain, 2024): kinds of memory in practice, and writing memory during the agent's turn ("in the hot path") or in the background.
- Anthropic, [Effective context engineering for AI agents][anthropic-ce] (2025): memory as one of several ways to manage what goes into the prompt, next to compaction.
- Chroma, [Context Rot][chroma] (2025): 18 models read long prompts less reliably as the prompt grows, which is one reason memory is needed even when a history fits.
- Letta, [Benchmarking AI agent memory: is a filesystem all you need?][letta-bench] (2025): a vendor's run in which an agent that searched a plain file of the history, with a small model, scored above what Mem0 reported for its own best variant on the LoCoMo benchmark.

**The products**

- Simon Willison on [ChatGPT's memory][willison-chatgpt] (2025), and why a user loses control of what goes into the prompt; and on [Claude's memory][willison-claude] (2025), where reading memory is a tool call that the user can see. The second links Shlok Khemani's reverse engineering of both products.

## Run it yourself

Each system has a notebook that runs the test conversation through it, with every prompt and reply printed. The notebooks are in the [repository][repo], and their rendered pages read well on a tablet:

- [notebook 0][nb-00]: the test conversation, with no memory and with the whole history;
- [notebook 1][nb-01]: textual memory;
- [notebook 2][nb-02]: Mem0;
- [notebook 3][nb-03]: Zep and Graphiti;
- [notebook 4][nb-04]: Letta;
- [notebook 5][nb-05]: Honcho.

The benchmark experiment of part 8, with the results and the analysis of every answer, and the run of Mastra's Observational Memory from part 9, are in the same repository.

Every system writes its memory and answers with `gemini-3.1-flash-lite`, whose free tier is enough for the notebooks. Model replies vary from run to run, even with the same prompt, and a different model can change more. The mechanisms stay the same.

## References

<!-- REFS -->

Papers:

- Peng, [MemoryTax: The Bitter Lesson of Agent Memory][memorytax] (2026)
- Wu et al., [LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory][longmemeval] (2024)
- Chen et al., [HaluMem: Evaluating Hallucinations in Memory Systems of Agents][halumem] (2025)
- Jiang et al., [PersonaMem-v3: Toward Omni-Platform Personal Intelligence for Holistic User Understanding, Recommendation, and Agentic Tasks][personamem-v3] (2026)
- Du, [Memory for Autonomous LLM Agents:Mechanisms, Evaluation, and Emerging Frontiers][autonomous] (2026)
- Hu et al., [Memory in the Age of AI Agents][age-of-agents] (2025)
- Du et al., [Rethinking Memory in LLM based Agents: Representations, Operations, and Emerging Topics][rethinking] (2025)
- Park et al., [Generative Agents: Interactive Simulacra of Human Behavior][generative-agents] (2023)
- Packer et al., [MemGPT: Towards LLMs as Operating Systems][memgpt] (2023)
- Zhou et al., [Are We Ready For An Agent-Native Memory System?][agent-native] (2026)
- Rathi et al., [DolphinBench: Mapping the Pareto Frontier of Agent Memory][dolphinbench] (2026)

<!-- /REFS -->

Other sources:

- Lilian Weng, [LLM Powered Autonomous Agents][weng] (June 2023)
- Harrison Chase, [Memory for agents][chase] (October 2024)
- Anthropic, [Effective context engineering for AI agents][anthropic-ce] (September 2025)
- Chroma, [Context Rot: How Increasing Input Tokens Impacts LLM Performance][chroma] (July 2025)
- Letta, [Benchmarking AI Agent Memory: Is a Filesystem All You Need?][letta-bench] (August 2025)
- Simon Willison, [I really don't like ChatGPT's new memory dossier][willison-chatgpt] (May 2025) and [Comparing the memory implementations of Claude and ChatGPT][willison-claude] (September 2025)
- [agent-memory-eval][repo], the code and results for this series

[longmemeval]: https://arxiv.org/abs/2410.10813
[halumem]: https://arxiv.org/abs/2511.03506
[personamem-v3]: https://arxiv.org/abs/2608.21381
[memorytax]: https://arxiv.org/abs/2610.29823
[dolphinbench]: https://arxiv.org/abs/2609.24971
[agent-native]: https://arxiv.org/abs/2606.24775
[autonomous]: https://arxiv.org/abs/2603.07670
[age-of-agents]: https://arxiv.org/abs/2512.13564
[rethinking]: https://arxiv.org/abs/2505.00675
[generative-agents]: https://arxiv.org/abs/2304.03442
[memgpt]: https://arxiv.org/abs/2310.08560
[weng]: https://lilianweng.github.io/posts/2023-06-23-agent/
[chase]: https://blog.langchain.com/memory-for-agents/
[anthropic-ce]: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
[chroma]: https://research.trychroma.com/context-rot
[letta-bench]: https://www.letta.com/blog/benchmarking-ai-agent-memory
[willison-chatgpt]: https://simonwillison.net/2025/May/21/chatgpt-new-memory/
[willison-claude]: https://simonwillison.net/2025/Sep/12/claude-memory/
[mem0-repo]: https://github.com/mem0ai/mem0
[graphiti-repo]: https://github.com/getzep/graphiti
[letta-repo]: https://github.com/letta-ai/letta
[honcho-repo]: https://github.com/plastic-labs/honcho
[repo]: https://github.com/anton-dergunov/agent-memory-eval
[nb-00]: https://anton-dergunov.github.io/agent-memory-eval/notebooks/00-introduction.html
[nb-01]: https://anton-dergunov.github.io/agent-memory-eval/notebooks/01-textual.html
[nb-02]: https://anton-dergunov.github.io/agent-memory-eval/notebooks/02-mem0.html
[nb-03]: https://anton-dergunov.github.io/agent-memory-eval/notebooks/03-zep-graphiti.html
[nb-04]: https://anton-dergunov.github.io/agent-memory-eval/notebooks/04-letta.html
[nb-05]: https://anton-dergunov.github.io/agent-memory-eval/notebooks/05-honcho.html
[part-2]: /posts/2199/01/agent-memory-2-how-memory-works/
[part-3]: /posts/2199/01/agent-memory-3-textual-memory/
[part-4]: /posts/2199/01/agent-memory-4-mem0/
[part-5]: /posts/2199/01/agent-memory-5-graphiti/
[part-6]: /posts/2199/01/agent-memory-6-letta/
[part-7]: /posts/2199/01/agent-memory-7-honcho/
[part-8]: /posts/2199/01/agent-memory-8-experiment/
[part-9]: /posts/2199/01/agent-memory-9-assistants/
