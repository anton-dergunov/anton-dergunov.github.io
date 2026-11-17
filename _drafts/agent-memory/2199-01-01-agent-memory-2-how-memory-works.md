---
title:     "How agent memory works"
excerpt:   "How memory systems for LLM agents work: where memory can be kept, what happens when it is written and read, the design choices that separate systems, and what the research has found."
topic:     llms-and-agents
date:      2199-01-01
permalink: /posts/2199/01/agent-memory-2-how-memory-works/
share:     true
series:    agent-memory
part:      2
tags:
  - llm
  - agents
  - memory
---

A language model sees only the text in its current prompt. Its weights do not change while you use it, and each new conversation starts with an empty context. An LLM agent that should know where the user lives, what they prefer, or what state a project is in therefore needs a memory system. A memory system keeps information from earlier conversations, updates it when it changes, drops what is no longer needed, and finds the right part of it for a new request.

There are many such systems. Open-source libraries offer memory to developers, research papers each propose a new design, and ChatGPT, Claude and Gemini now remember things about their users. New systems appear often, and some disappear as quickly. Most of them, though, combine a small number of ideas that recur from one system to the next.

This part explains those ideas, without focusing on any one system. It covers where a memory can be kept, the labels that other articles use for kinds of memory, what happens when a memory is written and when it is read, the questions on which designs differ, what each design costs, how memory differs from retrieval and from a long prompt, and what independent research has found. It ends with three early papers whose ideas later systems reuse. The later parts of this series take five designs apart, one at a time.

The figures in this part were drawn for this series, and their code is in the [agent-memory-eval repository][repo], next to the notebooks that the later parts use.

## What memory means for an LLM agent

A language model has two kinds of memory built in:

- its **weights**, which hold what it learned in training and do not change when you use the model;
- its **context window**, which holds the current prompt and is gone when the call ends.

Neither carries information from one conversation to the next. Suppose a user tells an assistant on Monday that they have moved from Munich to Berlin. On Friday, in a new conversation, the assistant does not know this, unless something puts the fact back into the prompt.

In this series, **memory** means any mechanism that carries information from one conversation to a later one. A memory system has four jobs:

1. **Keep:** decide what in a conversation is worth keeping, and in what form.
2. **Update:** when a fact changes, make the newer value win. "Lives in Munich" must give way to "lives in Berlin".
3. **Drop:** remove what is outdated, unimportant, or what the user asked to delete.
4. **Find:** for a new request, find the few stored items it needs and put them into the prompt.

The first three jobs happen when a conversation is turned into memory. The fourth happens later, when a new request arrives. These two moments, writing and reading, organise the rest of this part.

## Where memory can be kept: text, cache or weights

The broadest way to sort memory systems is by the form in which the memory is kept. The survey [Memory in the Age of AI Agents][age-of-agents] (Hu et al., 2025) uses three forms as its first dimension (p. 13): text outside the model, internal state of the model, and the model's weights.

{% include diagram.html name="three-homes" alt="Three places a memory can be kept, side by side. Text outside the model: notes, facts or a profile, pasted into the prompt; a person can read it, one fact can be corrected or deleted, and it works with any model, including a hosted one; reading it costs prompt tokens on every request. Internal state of the model: cached keys and values or memory vectors that the model attends to; nobody can read it, a single fact can rarely be deleted, and it needs access to the model's internals; reading it costs a pass over the cache. Weights: knowledge written into the parameters by editing or training; nobody can read it, a single fact cannot be deleted, and it needs the weights; reading it costs nothing extra, writing it costs training or an edit. Under the three, a note: a vector store is text memory, because its embeddings are only an index, and the model reads the text that the search finds." caption="The three forms of memory. The form decides who can read the memory, whether one fact can be removed, and which models can use it." %}

### Text outside the model

The memory is text: facts, notes, summaries, a profile of the user, or a graph whose nodes and edges are labelled with text. It is kept in a file or a database, and the parts that a request needs are pasted into the prompt. The survey calls this *token-level memory*.

- A person can read it, correct one entry, or delete it on request.
- It works with any model, including one that is only available through an API, because an API accepts text.
- Its cost is paid in prompt tokens on every request: whatever is pasted in has to be read by the model each time.

### Internal state of the model

The memory is part of the model's own computation: the keys and values that the attention layers compute for a piece of text, or a set of learned memory vectors. The model attends to this state later, as it attends to the tokens of its prompt. The survey calls this *latent memory*. Three examples show the range:

- **[Memorizing Transformers][memorizing]** keeps the keys and values of past text in a searchable store, and one layer of the model attends to the closest ones. In the paper the store holds up to 262K tokens of a document.
- **[MemoryLLM][memoryllm]** adds a fixed pool of memory vectors to every layer of the model. New text is written into the pool by a forward pass, and old content is gradually pushed out. In the paper's test, questions about a piece of text are still answered better than without it after about 20 later updates, roughly 10,000 tokens, and the accuracy keeps falling (p. 8, Fig. 5).
- **[Cartridges][cartridges]** trains a small cache for a fixed collection of documents, offline. On the paper's benchmarks it matches the quality of putting the documents into the prompt with 38.6 times less memory (p. 2). Training one cartridge takes about 30 minutes on eight H100 GPUs (p. 12).

A latent memory is compact and cheap to read, but nobody can read it. It is a set of vectors that only this model can interpret: there is no line that says "lives in Berlin" to correct or delete. [Larimar][larimar] is an exception among the papers I read: it can remove one written fact exactly (p. 7). Latent memory also needs access to the model's internals, which a hosted model's API does not give.

### The model's weights

The memory is written into the model's parameters. There are several ways to do this:

- **Editing.** [MEMIT][memit] computes a change to the weights that writes thousands of facts into a model at once.
- **Memory layers.** [Memory Layers at Scale][memory-layers] adds very large layers of trainable keys and values that the model looks up. At the same compute, a 1.3B model with them answers almost twice as many factual questions as one without (Natural Questions: 13.68 against 7.76, p. 8, Table 1).
- **Fine-tuning** the model on a user's data, for example with a small adapter.
- **Learning while running.** [Titans][titans] trains a small memory network on the fly as the model reads. It resets this network for every new input, so it is a long working memory, not a memory of a user.

A memory in the weights costs no prompt tokens at all. But writing it needs training or an edit, nobody can inspect it, and a single fact cannot be removed again. An edit can also change the target fact without changing what follows from it. [Fundamental Problems With Model Editing][model-editing] tests this on a small model trained on facts whose dependencies are known. After an edit, the edited fact changes, but on facts that depend on it and should also change, accuracy falls from 0.97 to 0.01 (p. 14, Table 4). In the example of this part, an update to "lives in Berlin" should also change the user's nearest airport.

### Why most memory systems keep text

The survey sums up the trade-offs as a division of labour (p. 30–31): text for facts that change often and must be auditable, weights for stable behaviour such as a persona or a style, latent memory where compactness or privacy matters. Facts about one user, which may change next month and which the user may ask to see or delete, are the first kind.

There is also a practical reason. Most people who build an LLM agent use a model through a vendor's API. They cannot read the model's cache or change its weights, so text is the only form of memory available to them. Almost every memory system for agents, and every system in this series, keeps text.

### Where embeddings fit

Many text memory systems store an embedding next to each item: a vector computed from the text by an embedding model. This does not make them latent memory. The embedding is an index: a search compares it with the embedding of the request to find the closest items. What goes into the prompt is the text of those items. A vector store such as the one Mem0 uses is therefore text memory with a vector index, and the model never sees the vectors.

## Working, episodic, semantic and procedural memory

Many articles on agent memory start with four labels: working, episodic, semantic and procedural memory. The labels come from cognitive psychology. [Cognitive Architectures for Language Agents][coala] (Sumers et al., 2023), known as CoALA, applied them to language agents (p. 9–10), and most of the later literature uses CoALA's definitions.

{% include diagram.html name="memory-kinds" alt="The four kinds of memory in the CoALA framework, each with the mechanism it corresponds to. At the bottom, working memory: the prompt of the current call, with the instructions, what was retrieved and the conversation so far. Above it, three long-term memories. Episodic: records of past sessions, such as the raw turns or summaries of them. Semantic: facts and knowledge, such as a profile of the user, extracted facts, or a document collection that retrieval-augmented generation reads but never writes. Procedural: how to act, kept in the model's weights, the agent's code, and instructions or skill files. Retrieval brings long-term memory into the prompt; learning writes from the prompt into long-term memory. Memory about a user, the subject of this series, is episodic and semantic; procedural memory is left out." caption="The four labels as CoALA defines them, each with what it is in a running system. Retrieval reads long-term memory into the prompt; learning writes the other way." %}

- **Working memory** holds what the agent is working with now. CoALA defines it as a data structure that persists across the model calls of one task, from which each prompt is built. In a chat assistant, it is the prompt of the current call: the instructions, what was retrieved, and the conversation so far.
- **Episodic memory** stores experience from earlier steps or conversations: the raw turns of past sessions, summaries of them, or an agent's past attempts at a task.
- **Semantic memory** stores knowledge about the world and about the agent itself: a profile of the user, a list of extracted facts, a knowledge graph. CoALA notes that retrieval-augmented generation reads from a semantic memory of documents, but a "fixed, read-only" one (p. 10). A memory system writes its semantic memory itself.
- **Procedural memory** stores how to act. CoALA places it in the model's weights and in the agent's code. Today it also includes instructions and skill files that an agent reads when it needs them. CoALA warns that writing to procedural memory is "significantly riskier than writing to episodic or semantic memory" (p. 10), because a wrong write changes how the agent behaves.

These labels say what a memory is about and what it is used for. The forms in the previous section say where it is kept. The two are independent: procedural memory, for example, can be kept in the weights or in a skill file.

The surveys do not all keep these labels. [Rethinking Memory in LLM-based Agents][rethinking] (Du et al., 2025) uses all four, and notes that for LLMs "the boundary between semantic and episodic memory is often blurred" (p. 5). Memory in the Age of AI Agents argues that terms like declarative, episodic, semantic and parametric have multiplied and blurred the field (p. 5). It replaces the four labels with three functions: factual memory (what the agent knows), experiential memory (how the agent improves from past tasks), and working memory (what it is working on now) (p. 31). [Externalization in LLM Agents][externalization] (2026) treats skills as a separate part of an agent, next to its memory.

This series is about memory of a user: the facts the user stated, which are semantic memory, and the records of past conversations, which are episodic memory. Memory of skills and procedures, which agents such as [ExpeL][expel] or [ReasoningBank][reasoningbank] keep from their past tasks, is a different problem, and the series leaves it out.

## The write path and the read path

A text memory system does its work in two places:

- the **write path** turns a conversation into memory. It runs after a conversation, or during it.
- the **read path** gets from memory what a new request needs and puts it into the prompt. It runs when the request arrives.

The answering model sees neither path. It receives a prompt with its instructions, whatever the read path returned, and the request. Nothing else from earlier conversations reaches it.

Rethinking Memory in LLM-based Agents names six operations that a memory performs (§2.4, p. 6–7). The figure places them on the two paths, with the example of the user who moved to Berlin.

{% include diagram.html name="operations" alt="How a text memory works, as two paths around a store. The write path runs after or during a conversation and can run in the background: consolidation turns the conversation into candidate memories (“I moved to Berlin in May” becomes “lives in Berlin, since May 2026”); updating reconciles each one with what is stored (it replaces “lives in Munich”); indexing builds what a read will use, such as an embedding or a keyword index. Forgetting drops or decays entries in the store. The read path runs on every request while the user waits: retrieval finds what the request needs (“any good bakeries near me?” finds “lives in Berlin”), and condensation shortens it to fit the prompt. The answering model gets the instructions, what memory returned, and the request. Each operation is tagged with the survey's group: encoding, evolving or adapting." caption="The six operations on the two paths. The write path can run in the background; the read path runs while the user waits. The answering model sees only what the read path returns." %}

On the write path:

1. **Consolidation** turns a conversation into memories that last: candidate facts, a summary, an updated profile. "I moved to Berlin in May" becomes "lives in Berlin, since May 2026".
2. **Updating** reconciles a new memory with what is already stored. It can add the new memory, merge it with an old one, replace an old one, or ignore the new one as already known. Here, "lives in Berlin" replaces "lives in Munich".
3. **Indexing** builds what a later read will use: an embedding of each item, a keyword index, links between items that mention the same entity, timestamps.
4. **Forgetting** removes or weakens entries that are outdated, unused, or that the user asked to delete. It often runs as a separate job, in batches.

On the read path:

5. **Retrieval** finds the stored items that a request needs: by similarity of embeddings, by keywords, by following links in a graph, or by a search that the model itself asks for.
6. **Condensation** shortens what was found so that it fits the prompt: it drops repeats, summarises, or keeps only a fixed budget of tokens. The survey uses this word for compression at read time, and keeps "consolidation" for summarising at write time.

The survey groups the six into three pairs: encoding (consolidation and indexing), evolving (updating and forgetting) and adapting (retrieval and condensation). The figure shows these groups as tags.

Written as code, a generic memory system looks like this. Each design in the later parts fills in these functions differently, and some leave one out:

```python
# The write path: after a conversation, or during it
def write(conversation, memory):
    candidates = consolidate(conversation)        # usually a model call
    for item in candidates:
        related = memory.search(item)             # what is already stored about it
        decision = reconcile(item, related)       # add, merge, replace, or nothing
        memory.apply(decision)
    memory.index()                                # embeddings, keywords, links
    memory.forget()                               # often a separate job, in batches

# The read path: on every request
def answer(request, memory):
    found = memory.retrieve(request)              # or the whole memory, if it fits
    context = condense(found, budget)
    prompt = INSTRUCTIONS + context + request
    return model(prompt)
```

Two things follow from this split.

- **The two paths are paid for at different times.** The write path runs once per conversation, and it can run in the background, after the user has left. The read path runs on every request, and the user waits for it. A design that moves work from the read path to the write path makes answers faster, and pays for it when it writes.
- **Most papers improve one operation.** [Memory-R1][memory-r1] trains the updating decision with reinforcement learning. [SeCom][secom] changes what consolidation produces: topic segments instead of single turns or whole sessions. [HippoRAG][hipporag] changes retrieval to a walk through a graph. [LightMem][lightmem] moves updating to an offline phase. Reading a new paper, it helps to ask which operation it changes and what it keeps from the others.

## Five design questions

Besides the choice of form, most memory systems differ in how they answer five questions. Each question has several common answers:

1. **What is one memory?** A raw turn of the conversation, a topic segment, an extracted fact, an entity with its relations, a block of text, a whole profile. SeCom (Pan et al., 2025) compares the units on the same data: topic segments score 71.57, single turns 65.58 and whole sessions 63.16 (p. 6, Table 1).
2. **Who writes it?** Nobody (the raw history is kept as it is), a pipeline that runs after each message or session, the answering agent through tool calls, or a background process that runs between conversations. The decision itself can be a fixed rule, a model following a prompt, or a policy trained for the job.
3. **What shape is the store?** A list, one document, a graph, several typed stores, or tiers. Tiers are levels of different size and speed: in [MemGPT][memgpt], a small "main context" inside the prompt and large external stores outside it.
4. **How is a read chosen?** The whole memory is inserted into the prompt, or a search selects part of it: by embedding similarity, by keywords, by a walk through a graph, or by a search the model issues itself.
5. **When is the work done?** When the memory is written, in the background between conversations, or when it is read.

This series uses two of the five as its main axes: who writes (question 2) and how a read is chosen (question 4). In the systems that the later parts examine, these two choices explained most of what a system did well, what it did badly, and what it cost. The next two sections look at each, and the section after them places the five systems of the series.

### Who writes the memory

There are four kinds of writer, and each runs at a different moment.

{% include diagram.html name="writers" alt="A timeline of two conversations with a gap between them, and four rows, one per kind of writer. Nobody: the raw messages are kept as they arrive, and nothing is lost or cleaned up, so old and new values both stay. A pipeline: an extraction call runs after each message or at the end of the session; it loses what its prompt does not ask for. The answering agent: it writes with a tool call inside its own turn, while the user waits; it loses what it does not decide to write. A background process: it runs later, between the conversations; it can rewrite or drop what it should keep, and its result is not ready until it has run." caption="The four writers on the timeline of two conversations. Each runs at a different moment, and each loses facts in its own way (in red)." %}

- **Nobody.** The raw messages are the memory, kept as they arrive. Nothing is lost when writing, but nothing is reconciled either. Both "lives in Munich" and "lives in Berlin" stay, and the read path or the answering model has to work out which one is current.
- **A pipeline.** A separate model call reads each new message or each finished session and extracts what to keep. Its prompt decides what is kept. So a pipeline loses what its prompt does not ask for. It runs outside the answering model's turn, so the user does not wait for it.
- **The answering agent.** The model that answers the user also has tools to write memory, and it calls them during its turn. It knows the conversation best. But it has to decide, in the middle of answering, that something is worth writing, and it loses whatever it does not decide to write. The user waits while it writes.
- **A background process.** A job runs later, between conversations, and rewrites or reasons over the memory. It can take its time and look at everything stored. But its result is not ready until it has run, and a rewrite can change or drop what it should have kept.

Who writes also decides who resolves a contradiction. A pipeline resolves it with its prompt, an agent with its own judgement, a background process with a later pass. When nobody writes, nobody resolves it at write time, and the answering model meets both values in its prompt.

### Whether the read path inserts or selects

The read path can put the whole memory into the prompt, or let a search pick part of it.

{% include diagram.html name="insert-vs-select" alt="Two read paths side by side. Insert: the whole memory, here eight short entries, goes into the prompt with the request; no stored fact can be missed, but the prompt grows with the memory and stops at the context window, and the model must find the relevant lines among the rest. Select: a search compares the request (a trip for next weekend) with the stored entries and puts the three best matches into the prompt (lives in Berlin, runs on weekends, sister in Hamburg); the prompt stays small however much is stored, but the entry the answer needed (has a dog), which the request does not mention, ranks fourth and is left out. Under both, a design that does both: an index that is always in the prompt, and topic files read only when the index points to them, as in Claude Code." caption="The same memory and the same request, read in the two ways. A search ranks entries by how close they are to the request, and a fact the request does not mention can fall below the cut." %}

**Inserting** puts every stored item into every prompt. No stored fact can be missed. But the prompt grows with the memory and stops at the context window, every request pays to read all of it, and the model has to find the few lines that matter among the rest.

**Selecting** runs a search and puts only the best matches into the prompt. The prompt stays small however much is stored. But the one fact that a request needs can rank just below the cut, especially when the request does not mention it. How many items to take is itself a setting that changes results. In [Memanto][memanto]'s ablation of its own system, raising the number of retrieved items from 10 to 40 added 20.4 points on the LongMemEval benchmark (p. 8).

A search can also be one that the model asks for, through a tool. That gives the model control over when to search, and adds a new way to fail: Memory in the Age of AI Agents describes a "silent failure mode" in which the agent does not search because it overestimates what it already knows (p. 61).

Some designs do both. Claude Code keeps an index file that is always in the prompt, one line per memory, and topic files that the model reads only when the index points to them. Part 9 of this series describes this and other product designs.

### The systems of this series on these two choices

The five systems that parts 3 to 7 take apart, and the two baselines of the experiment in part 8, sit in different cells of these two choices.

{% include diagram.html name="map-systems" alt="The five memory systems of this series and the two baselines, on two axes: who writes the memory (nobody, a pipeline, the answering agent, a background process) and whether the read path inserts everything or selects. Nobody writes: full context inserts the whole history; plain retrieval selects with BM25 over the raw turns. A pipeline writes: Mem0 and Zep/Graphiti select. The answering agent writes: Letta inserts its core memory blocks, and the agent searches its log of past messages. A background process writes: textual memory inserts one profile; Honcho selects among its conclusions." caption="The systems of this series on the two choices. The cells are not a ranking: inserting is better while everything fits, and selecting is needed when it does not." %}

- **Full context** (a baseline): nobody writes, and the whole history goes into the prompt.
- **Retrieval over the raw turns** (a baseline): nobody writes, and a keyword search (BM25) selects the turns closest to the request.
- **Textual memory** ([part 3][part-3]): a background call rewrites one profile of the user after each session, and the whole profile is inserted.
- **Mem0** ([part 4][part-4]): a pipeline extracts short facts into a vector store, and a similarity search selects.
- **Zep and Graphiti** ([part 5][part-5]): a pipeline writes facts with dates into a graph and closes the facts that a newer one replaces. A search over the graph selects. Of the five systems here, it is the only one that keeps a replaced value as dated history by construction: the old fact stays in the graph, with an end date. Textual memory also keeps an old value as history, but only because its prompt asks the rewrite to.
- **Letta** ([part 6][part-6]): the answering agent edits memory blocks that are always in the prompt, and can search the log of past messages.
- **Honcho** ([part 7][part-7]): a background reasoner writes conclusions about the user, each at a level of reasoning (what the user said, what follows from it, or a pattern across several statements), and a search or a model that answers questions about the user selects from them.

The cells are not a ranking. Inserting is the better choice while the whole memory fits in the prompt and costs little to read. Selecting is needed when it does not.

## Write cost and read cost

The fifth design question, when the work is done, explains why the costs reported for memory systems are hard to compare. A memory system has three separate budgets:

- **building** the memory: the model calls of the write path, paid once per conversation and possibly in the background;
- **storing** it: the size of what is kept;
- **reading** it: the tokens put into every prompt, paid on every request while the user waits.

{% include diagram.html name="cost-timing" alt="A schematic of cost over eight conversations, for three designs. Full context writes nothing; on every request it reads the whole history, so the cost of each request grows with every conversation. A write-heavy memory, such as an extraction pipeline or a graph, pays for several model calls after each conversation, in the background, and puts a short selection of about the same size into every prompt. A rewritten profile pays for one call after each conversation and inserts a profile that stays about the same size. Write costs are paid once and can wait; read costs are paid on every request while the user waits." caption="When each design pays, as a schematic. Full context pays nothing to write and more on every request as the history grows. A design that works hard when writing keeps every read small." %}

The three budgets are unrelated numbers, and a paper tends to report the one that suits its system. The [Mem0][mem0] paper gives an example on LoCoMo, a benchmark of long conversations between two people with questions about them. A whole LoCoMo conversation is about 26,000 tokens (p. 14):

- **Stored:** Mem0's store holds about 7,000 tokens per conversation. Zep's graph holds more than 600,000, because it keeps a summary at every node and the facts on the edges between them (p. 14).
- **Read:** Mem0 puts 1,764 tokens into the prompt, and Zep 3,911 (p. 11, Table 2).
- **Built:** the paper reports that Zep's new memories answered questions correctly only after "a delay of several hours", because the graph is built by many model calls in the background (p. 14).

These measurements come from a competitor of Zep, and I report them as such. Still, they show that a store more than twenty times the size of the conversation can put a short text into the prompt.

The cost of building also differs widely. On LongMemEval, the [LightMem][lightmem] paper counts the tokens that each system spent to build its memory: about 1,606,000 for A-MEM, 1,153,000 for Mem0, and 28,000 for LightMem, which buffers messages by topic and defers its updates to an offline phase (p. 7, Table 2). That is the paper's own run of the other systems.

Moving work into idle time is a design choice of its own. [Sleep-time Compute][sleep-time] (Lin et al., 2025) lets a model work through a context before any question arrives. On its two benchmarks this reduces the compute needed at question time by about five times, at the same accuracy (p. 1).

## Memory, retrieval and long context

Two neighbouring techniques are often confused with memory, and both are baselines that a memory system has to beat.

**Retrieval-augmented generation (RAG)** searches a collection of documents that someone else wrote and puts the best matches into the prompt. Nothing is written, so there is no decision about what to keep, no conflict between an old fact and a new one, and nothing to forget. Memory in the Age of AI Agents notes that the line between the two has blurred, and that in practice it falls by task: RAG is evaluated on questions over large document collections, memory on long interactions where facts change (p. 10–11). A memory system that only searches the raw history, without writing anything, is retrieval over that history. In this series it is one of the two baselines: a keyword search over the stored turns.

**A long context** puts the whole history into the prompt. This removes the need to select, and it is the other baseline of this series. While the history fits in the context window, it is a strong one (see Finding 1 below).

A third baseline is easy to miss: **the same prompt with an empty memory**. A memory system usually comes with its own prompt, and the prompt alone can change results. [Dynamic Cheatsheet][dynamic-cheatsheet] (Suzgun et al., 2025), a memory of solution strategies for maths problems, shows this on AIME 2024 with Claude 3.5 Sonnet (p. 6, Table 1):

| Setting | Problems solved |
|---|---|
| A plain prompt | 23.3% |
| The memory's prompt, with an empty memory | 36.7% |
| The memory's prompt, with the memory it built | 50.0% |

About half of the gain over the plain prompt comes from the prompt, before anything is stored. A fair comparison of a memory system therefore needs the same prompt with an empty memory, and not only a plain prompt.

## What the research has found

Since 2025, groups other than the authors of each system have re-run memory systems on common benchmarks. Their results agree on four points. Each finding below ends with how strong the evidence is.

### Finding 1: a long context is a strong baseline

The Mem0 paper's own table shows it. On LoCoMo, putting the whole conversation into the prompt scores 72.90 with an LLM judge, against 66.88 for Mem0 (p. 11, Table 2). What Mem0 buys is speed: 95% of its answers come within 1.44 seconds, against 17.12 seconds for the whole conversation.

[MemoryAgentBench][memoryagentbench] (Hu et al., 2025), run by a group unrelated to the systems it tests, finds the same. Agents that read the whole input lead overall: GPT-5-mini scores 60.6, and the best memory agent, HippoRAG-v2, scores 41.6 (p. 8, Table 3). The comparison is not even, though: the memory agents ran on GPT-4o-mini, and some long-context agents on stronger models.

[MemoryTax][memorytax] (Peng, 2026), a short independent study on one LoCoMo conversation, adds the model as a variable. With GPT-4o-mini, Mem0 scored 78% against 74% for the whole conversation; with two stronger models, Mem0 no longer beat it, and building Mem0's memory alone cost more than the whole run with the full conversation (p. 3). The study also swapped the model that reads a store: a stronger reader did not recover what a weaker writer had left out (p. 3). It is one conversation and one run per setting, as its author notes.

Memory starts to win when the history is too long to fit, or too long to be read well. [LongMemEval][longmemeval] (Wu et al., 2024) builds chat histories of about 115,000 tokens, with questions about facts spread across sessions. GPT-4o answers 87.0% of its questions when given only the sessions that hold the answer, and 60.6% when given the whole history (p. 6, Fig. 3). The [Zep][zep] paper reports 71.2% for Zep on the same benchmark, against 60.2% for the whole history, with 1,600 tokens in the prompt instead of 115,000 (p. 7, Table 2); that is the vendor's own run.

*How strong the evidence is:* consistent across papers, but it depends on the length of the history and on the model. LoCoMo's conversations fit easily into a modern context window; LongMemEval's are long enough to hurt.

### Finding 2: published comparisons between memory systems do not transfer

Each memory system's paper reports that it beats the others, usually on LoCoMo. When other papers run the same two systems, their order changes. Here are Mem0 and Zep in three papers:

| Reported in | Answering model | Mem0 | Zep | Zep minus Mem0 |
|---|---|---|---|---|
| [Mem0][mem0] (p. 11, Table 2) | gpt-4o-mini | 66.88 | 65.99 | −0.9 |
| [MemOS][memos] (p. 24, Table 3) | gpt-4o-mini | 64.57 | 59.22 | −5.4 |
| [MIRIX][mirix] (p. 11, Table 2) | gpt-4.1-mini | 62.47 | 79.09 | +16.6 |

The same Zep is one point below Mem0 in one paper and seventeen points above it in another. The papers differ in the answering model, the judge, how many items are retrieved, and how each system was configured. Each of these three papers was also written by the makers of a competing system. As Memanto's ablation showed above, a single retrieval setting can move a result by 20 points.

*How strong the evidence is:* strong. It rests on the papers' own tables, read side by side. One paper's ranking of memory systems says more about its set-up than about the systems.

### Finding 3: most facts are lost when the memory is written

When a memory system answers wrongly, the usual cause is not that the search missed a stored fact. More often the fact was never stored, or was stored without the detail that was needed. [HaluMem][halumem] (2025) scores each step of the write path against the facts that should have been stored:

- every system except MemOS stores fewer than 60% of the facts it should have extracted;
- for most systems, more than half of the updates are missed, because a fact that was never extracted cannot be updated;
- no system answers more than 70% of the questions correctly (p. 11, Table 3).

[DynamicMem][dynamicmem] (2026) agrees that the memory, not the answering model, is where most failures lie: over 93% of the failures it analyses trace to what the memory system retrieved (p. 3). It does not separate what was never written from what was written and not found.

*How strong the evidence is:* several independent papers agree, though most use simulated users.

### Finding 4: updating and forgetting are the hardest operations

Storing a fact is easier than knowing that it is no longer true.

- **Old and new values mixed.** [A-TMA][a-tma] (2026) calls this "ghost memory": the old, the current and an intermediate version of a fact are retrieved together, and the answer mixes them.
- **Deletion.** [ForgetEval][forgeteval] (2026) tests whether a memory can be made to forget a fact. Graph memories pass few of its adversarial cases (Graphiti 7%, HippoRAG 9.5%), because turning text into entities loses the exact wording that a targeted deletion needs. One extra model call at the moment a fact changes raises simple stores from 63–68% to 92–93% (p. 7, Table 2). The study has a single author, who also built one of the systems it tests.
- **Two answers to what an update should do.** Some systems mark the old fact as replaced and keep it, with dates: Zep does this, and can then answer questions about the past. Others remove the old fact, which keeps it out of the prompt and is what a request to delete requires. Among the papers I read, none compares the two on the same task.

The model-editing result from the section on weights is the same problem in another form: an update should also change the facts that follow from it, whether the memory is text or weights.

*How strong the evidence is:* many 2026 papers point the same way, but each uses its own synthetic test.

## Where the designs came from

Three papers from 2023 introduced ideas that later systems reuse. The timeline places them among the systems, benchmarks and surveys that this part mentions.

{% include diagram.html name="timeline" alt="A timeline of papers from 2023 to 2026 in four rows. Systems: Generative Agents (April 2023), MemoryBank (May 2023), MemGPT (October 2023), Zep (January 2025), A-MEM (February 2025), Mem0 (April 2025), MemOS and MIRIX (July 2025), LightMem (October 2025). Learned write policies: Memory-R1 (August 2025) and Mem-α (September 2025). Benchmarks: LoCoMo (February 2024), LongMemEval (October 2024), MemoryAgentBench (July 2025), HaluMem (November 2025), EvoMemBench (May 2026), ForgetEval (June 2026). Surveys: CoALA (September 2023), Rethinking Memory (May 2025), Memory in the Age of AI Agents (December 2025), Memory for Autonomous LLM Agents (March 2026). The systems cluster in 2023 and 2025; the independent benchmarks that re-run them cluster in late 2025 and 2026." caption="Memory papers by the month of their first version. The systems came in two waves, in 2023 and 2025; most of the benchmarks that re-ran them came later." %}

**[Generative Agents][generative-agents] (Park et al., April 2023).** Twenty-five simulated characters live in a small town, each driven by a language model. Each character keeps a *memory stream*: every observation, written as a sentence with a timestamp. To retrieve, the system scores every memory by the sum of three parts, each scaled to the range 0 to 1 (p. 9):

- **recency**, which decays by a factor of 0.995 for every game hour since the memory was last used;
- **importance**, a number from 1 to 10 that the model gives each memory when it is stored, with this prompt: "On the scale of 1 to 10, where 1 is purely mundane (e.g., brushing teeth, making bed) and 10 is extremely poignant (e.g., a break up, college acceptance), rate the likely poignancy of the following piece of memory.";
- **relevance**, the cosine similarity between the memory's embedding and the query's.

When the importance of recent events adds up past a threshold, the model is asked for higher-level conclusions, *reflections*, which are written back into the stream as memories, for example "Klaus Mueller is dedicated to his research on gentrification" (p. 10). Writing conclusions in the background and storing them next to observations is what Honcho does ([part 7][part-7]).

**[MemoryBank][memorybank] (Zhong et al., May 2023).** It keeps three layers for a companion chatbot (p. 3):

- the raw turns, with timestamps;
- a summary of each day's events, rolled up into a global summary;
- a *portrait* of the user: each day's personality traits, rolled up into one description.

The portrait is written by two prompts, which the paper gives in full: "Based on the following dialogue, please summarize the user's personality traits and emotions.[dialog]", and then, over many days, "The following are the user's exhibited personality traits and emotions throughout multiple days. Please provide a highly concise and general summary of the user's personality[daily Personalities]" (p. 3–4). The example portrait in the paper's Figure 1 reads "open-minded, curious, … and receptive to advice" (p. 3). The global portrait and the global summary go into every prompt; turns and daily summaries are retrieved by similarity. A profile that is rewritten and inserted whole is the design of textual memory ([part 3][part-3]).

MemoryBank also proposed forgetting after Ebbinghaus's forgetting curve. Each memory has a retention $$R = e^{-t/S}$$, where $$t$$ is the time since it was learned and the strength $$S$$ grows by one each time it is recalled. The authors call this "an exploratory and highly simplified memory updating model" (p. 4), and the paper does not say how a low retention becomes a deletion.

**[MemGPT][memgpt] (Packer et al., October 2023).** An operating system gives a program the illusion of more memory than the machine has, by moving pages between fast main memory and a slow disk. MemGPT applies this to the context window. The prompt is the main memory, and external stores are the disk. The model itself moves information between them by calling functions (p. 1–3):

- it edits a small block of facts that stays in the prompt;
- it saves to and searches an archive outside the prompt;
- older messages are moved out of the prompt into a searchable log;
- when the prompt nears its limit, a "memory pressure" warning asks the model to save what matters first (p. 3).

An agent that writes its own memory with tool calls is Letta's design ([part 6][part-6]); Letta is the company and framework that grew out of MemGPT.

**After 2023.** The two benchmarks that most papers now use came in 2024: [LoCoMo][locomo] in February and LongMemEval in October. In 2025 came a wave of memory systems with papers, among them Zep in January, A-MEM in February, Mem0 in April, and MemOS and MIRIX in July, each reporting that it beat the others, most of them on LoCoMo (Zep on LongMemEval and on MemGPT's DMR benchmark). In the same year, Memory-R1 and [Mem-α][mem-alpha] began to train the decision about what to write with reinforcement learning. From late 2025, most new papers re-ran existing systems instead of adding one, and their results are the findings above.

For further reading, three surveys cover the field from different angles: [Memory for Autonomous LLM Agents][autonomous] (2026) is the shortest, Memory in the Age of AI Agents the fullest, and Rethinking Memory in LLM-based Agents is organised by the six operations.

## The rest of this series

Each of the next five parts takes one design apart, with every prompt shown and one short test conversation followed through it call by call: textual memory ([part 3][part-3]), Mem0 ([part 4][part-4]), Zep and Graphiti ([part 5][part-5]), Letta ([part 6][part-6]) and Honcho ([part 7][part-7]). [Part 8][part-8] measures all five against the two baselines on LongMemEval, on accuracy and on cost. [Part 9][part-9] places the memory of ChatGPT, Claude, Gemini and the coding agents on the same two choices. The code for all of them is in the [repository][repo].

## References

<!-- REFS -->

Papers:

- Hu et al., [Memory in the Age of AI Agents][age-of-agents] (2025)
- Wu et al., [Memorizing Transformers][memorizing] (2022)
- Wang et al., [MEMORYLLM: Towards Self-Updatable Large Language Models][memoryllm] (2024)
- Eyuboglu et al., [Cartridges: Lightweight and general-purpose long context representations via self-study][cartridges] (2025)
- Das et al., [Larimar: Large Language Models with Episodic Memory Control][larimar] (2024)
- Meng et al., [Mass-Editing Memory in a Transformer][memit] (2022)
- Berges et al., [Memory Layers at Scale][memory-layers] (2024)
- Behrouz et al., [Titans: Learning to Memorize at Test Time][titans] (2024)
- Hase et al., [Fundamental Problems With Model Editing: How Should Rational Belief Revision Work in LLMs?][model-editing] (2024)
- Sumers et al., [Cognitive Architectures for Language Agents][coala] (2023)
- Du et al., [Rethinking Memory in LLM based Agents: Representations, Operations, and Emerging Topics][rethinking] (2025)
- Zhou et al., [Externalization in LLM Agents: A Unified Review of Memory, Skills, Protocols and Harness Engineering][externalization] (2026)
- Zhao et al., [ExpeL: LLM Agents Are Experiential Learners][expel] (2023)
- Ouyang et al., [ReasoningBank: Scaling Agent Self-Evolving with Reasoning Memory][reasoningbank] (2025)
- Yan et al., [Memory-R1: Enhancing Large Language Model Agents to Manage and Utilize Memories via Reinforcement Learning][memory-r1] (2025)
- Pan et al., [On Memory Construction and Retrieval for Personalized Conversational Agents][secom] (2025)
- Gutiérrez et al., [HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models][hipporag] (2024)
- Fang et al., [LightMem: Lightweight and Efficient Memory-Augmented Generation][lightmem] (2025)
- Packer et al., [MemGPT: Towards LLMs as Operating Systems][memgpt] (2023)
- Abtahi et al., [Memanto: Typed Semantic Memory with Information-Theoretic Retrieval for Long-Horizon Agents][memanto] (2026)
- Chhikara et al., [Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory][mem0] (2025)
- Lin et al., [Sleep-time Compute: Beyond Inference Scaling at Test-time][sleep-time] (2025)
- Suzgun et al., [Dynamic Cheatsheet: Test-Time Learning with Adaptive Memory][dynamic-cheatsheet] (2025)
- Hu et al., [Evaluating Memory in LLM Agents via Incremental Multi-Turn Interactions][memoryagentbench] (2025)
- Peng, [MemoryTax: The Bitter Lesson of Agent Memory][memorytax] (2026)
- Wu et al., [LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory][longmemeval] (2024)
- Rasmussen et al., [Zep: A Temporal Knowledge Graph Architecture for Agent Memory][zep] (2025)
- Li et al., [MemOS: A Memory OS for AI System][memos] (2025)
- Wang and Chen, [MIRIX: Multi-Agent Memory System for LLM-Based Agents][mirix] (2025)
- Chen et al., [HaluMem: Evaluating Hallucinations in Memory Systems of Agents][halumem] (2025)
- Xie et al., [DynamicMem: A Long-Horizon Memory Benchmark in Real-World Settings][dynamicmem] (2026)
- Shi et al., [A-TMA: Decoupling State-Aware Memory Failures in Long-Term Agent Memory][a-tma] (2026)
- Yang, [Control-Plane Placement Shapes Forgetting: An Architectural Study of Agent Memory Across Thirteen System Configurations][forgeteval] (2026)
- Park et al., [Generative Agents: Interactive Simulacra of Human Behavior][generative-agents] (2023)
- Zhong et al., [MemoryBank: Enhancing Large Language Models with Long-Term Memory][memorybank] (2023)
- Maharana et al., [Evaluating Very Long-Term Conversational Memory of LLM Agents][locomo] (2024)
- Wang et al., [Mem-α: Learning Memory Construction via Reinforcement Learning][mem-alpha] (2025)
- Du, [Memory for Autonomous LLM Agents:Mechanisms, Evaluation, and Emerging Frontiers][autonomous] (2026)

<!-- /REFS -->

[age-of-agents]: https://arxiv.org/abs/2512.13564
[rethinking]: https://arxiv.org/abs/2505.00675
[coala]: https://arxiv.org/abs/2309.02427
[externalization]: https://arxiv.org/abs/2604.08224
[autonomous]: https://arxiv.org/abs/2603.07670
[memorizing]: https://arxiv.org/abs/2203.08913
[memoryllm]: https://arxiv.org/abs/2402.04624
[cartridges]: https://arxiv.org/abs/2506.06266
[larimar]: https://arxiv.org/abs/2403.11901
[memit]: https://arxiv.org/abs/2210.07229
[memory-layers]: https://arxiv.org/abs/2412.09764
[titans]: https://arxiv.org/abs/2501.00663
[model-editing]: https://arxiv.org/abs/2406.19354
[expel]: https://arxiv.org/abs/2308.10144
[reasoningbank]: https://arxiv.org/abs/2509.25140
[memory-r1]: https://arxiv.org/abs/2508.19828
[mem-alpha]: https://arxiv.org/abs/2509.25911
[secom]: https://arxiv.org/abs/2502.05589
[hipporag]: https://arxiv.org/abs/2405.14831
[lightmem]: https://arxiv.org/abs/2510.18866
[memgpt]: https://arxiv.org/abs/2310.08560
[memanto]: https://arxiv.org/abs/2604.22085
[mem0]: https://arxiv.org/abs/2504.19413
[zep]: https://arxiv.org/abs/2501.13956
[sleep-time]: https://arxiv.org/abs/2504.13171
[dynamic-cheatsheet]: https://arxiv.org/abs/2504.07952
[memoryagentbench]: https://arxiv.org/abs/2507.05257
[memorytax]: https://arxiv.org/abs/2610.29823
[longmemeval]: https://arxiv.org/abs/2410.10813
[locomo]: https://arxiv.org/abs/2402.17753
[memos]: https://arxiv.org/abs/2507.03724
[mirix]: https://arxiv.org/abs/2507.07957
[halumem]: https://arxiv.org/abs/2511.03506
[dynamicmem]: https://arxiv.org/abs/2606.22877
[a-tma]: https://arxiv.org/abs/2607.01935
[forgeteval]: https://arxiv.org/abs/2606.15903
[generative-agents]: https://arxiv.org/abs/2304.03442
[memorybank]: https://arxiv.org/abs/2305.10250
[repo]: https://github.com/anton-dergunov/agent-memory-eval
[part-3]: /posts/2199/01/agent-memory-3-textual-memory/
[part-4]: /posts/2199/01/agent-memory-4-mem0/
[part-5]: /posts/2199/01/agent-memory-5-graphiti/
[part-6]: /posts/2199/01/agent-memory-6-letta/
[part-7]: /posts/2199/01/agent-memory-7-honcho/
[part-8]: /posts/2199/01/agent-memory-8-experiment/
[part-9]: /posts/2199/01/agent-memory-9-assistants/
