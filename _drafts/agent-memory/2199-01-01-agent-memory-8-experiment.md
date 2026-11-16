---
title:     "Five memory systems on a public benchmark"
excerpt:   "Five LLM memory systems and two baselines on LongMemEval's questions about changed facts: accuracy, cost, and why each wrong answer was wrong."
topic:     llms-and-agents
date:      2199-01-01
permalink: /posts/2199/01/agent-memory-8-experiment/
share:     true
series:    agent-memory
part:      8
tags:
  - llm
  - agents
  - memory
  - evaluation
---

A language model sees only the text in its current prompt. To use what a user said in earlier sessions, an LLM agent needs a memory system: something that stores information from those sessions and puts it into a later prompt. Some stored facts stay true. Others change, and then the newer value has to win.

The earlier parts of this series took five memory systems apart, one per part: textual memory, Mem0, Zep/Graphiti, Letta and Honcho. Each part followed one short test conversation (two sessions and a question) through the system, one model call at a time. The conversation was small on purpose: small enough that every prompt, every stored item and every reply could be printed and read. It shows how each mechanism works. It cannot show how often a mechanism fails, or what it costs, on histories of realistic length.

This part runs the same five systems on a public benchmark, LongMemEval, with real-length chat histories. The questions are of one kind: the user states a fact, later changes it in passing, and then asks about it. This is what the test conversation of the earlier parts did once; here it is done 67 times. Every system runs with the same model, answers the same questions and is scored by the same judge. Two baselines without any memory system run next to them. For every answer, the experiment also records what the system had stored and what reached the answering model, so that each wrong answer can be traced to the step that lost it.

Why run the systems again, when every one of them has a paper with benchmark results? Because those numbers are hard to compare. Each paper reports the benchmark and the setting its system does well in. Competitors are re-run with different answer models, different judges and different code, or their numbers are copied from another paper. The differences that come from the setup can be larger than the differences between the systems. One example: the authors of MIRIX, another memory system, ran Zep on the LoCoMo benchmark twice, with the same answer model. With Zep's own evaluation code it scored 79.09; with the code from Mem0's repository it scored 49.09 (MIRIX, p. 10, p. 11 and p. 17).

The code, the results for every question and the analysis of every wrong answer are in the [agent-memory-eval repository][repo].

Most memory systems in this series differ in two choices, and these explain most of the results below:

1. **Who writes the memory:** a pipeline of model calls that runs after the conversation, or the agent itself, in its own turn.
2. **How the memory is read:** the whole memory goes into the prompt, or a search selects part of it.

## Benchmarks for memory systems

A benchmark for memory systems has three parts:

- **a history:** one or more conversations, usually split into dated sessions;
- **questions** asked after the history, each with a reference answer;
- **a way to score** an answer against the reference: word overlap, multiple choice, or a judge model that reads both.

The system under test reads the history session by session, as it would in use. It then answers each question with whatever it kept. Benchmarks differ in how the history is made (real, simulated, or pasted together from other datasets), how long it is, and which abilities the questions test. Here are the main ones, in order of publication:

| Benchmark | The history | The questions | Scoring |
|---|---|---|---|
| [MemGPT's Deep Memory Retrieval][memgpt] (DMR, 2023) | Multi-session chats from the MSC dataset, 5 sessions each | One generated question per chat that needs an earlier session | Accuracy |
| [LoCoMo][locomo] (2024) | 50 conversations between two simulated people, about 300 turns and 9,000 tokens each, over up to 35 sessions | 7,512 questions: single-hop, multi-hop, temporal, open-domain and unanswerable | Word overlap (F1) in the paper; most later papers use a judge model |
| [LongMemEval][longmemeval] (2024) | One history per question, between a user and an assistant: about 115,000 tokens (S) or 1.5 million (M) | 500 questions over five abilities, including knowledge updates | A judge model, with a prompt per question type |
| [MemBench][membench] (2025) | Simulated dialogues and observation logs, up to about 100,000 tokens | Multiple choice, about facts and about preferences inferred from several statements | Accuracy |
| [MemoryAgentBench][memoryagentbench] (2025) | Existing long-context datasets cut into chunks and fed in order, 103,000 to 1.44 million tokens | 2,071 questions over four competencies, one of them "selective forgetting" of overwritten facts | Accuracy, F1, a judge for some tasks |
| [BEAM][beam] ("Beyond a Million Tokens", 2025) | 100 coherent single-user conversations of up to 10 million tokens | 2,000 questions over ten abilities, including updates and contradictions | A judge model, scoring parts of the answer |
| [HaluMem][halumem] (2025) | 20 simulated users, about 160,000 tokens each, or about 1 million with filler | 3,467 questions, plus scoring of each stored memory | A judge model, for each memory operation separately |
| [HorizonBench][horizonbench] (2026) | 360 simulated users over six months, about 163,000 tokens each | 4,245 multiple-choice questions about preferences that changed after a life event | Accuracy |
| [DynamicMem][dynamicmem] (2026) | 10 users' app logs, about 2.2 million tokens each, with profiles that change over time | Fill in a user's current profile; act on it | A judge model |
| [PersonaMem-v3][personamem-v3] (2026) | Real engagement histories from several apps, about 410,000 tokens per query | Personalised answers, recommendations, restraint, agentic tasks | Rubrics and a judge model |

DMR was the first benchmark of its kind, and it is now saturated: in Zep's paper, a model that simply reads the whole conversation scores 94.4%, slightly above MemGPT's 93.4% (Zep, p. 6, Table 1).

**LoCoMo** is the benchmark that most memory papers report, so it is worth a closer look. Its conversations are between two simulated people, each with a persona and a timeline of life events. It became the common reference because it was early, public and cheap to run: one conversation serves about 150 questions. Three things limit what it can show:

- **The histories are short.** Most papers use the ten released conversations, about 26,000 tokens each by Mem0's count (Mem0, p. 11), and the Mem0 and MIRIX papers treat reading the whole conversation as the upper bound (MIRIX, p. 17). A memory system can mostly only lose to that baseline.
- **Few facts change.** LongMemEval's comparison of benchmarks marks LoCoMo as not testing knowledge updates (LongMemEval, p. 3, Table 1).
- **The answer key and the judge have errors.** An audit by Penfield Labs found 99 of 1,540 answers in the key wrong (6.4%), and the commonly used judge accepted 62.81% of answers that were written to be wrong but on topic ([Penfield Labs][penfield], 2026).

For this experiment I needed a benchmark with four properties:

1. **Questions about facts that change.** LongMemEval has a question type for exactly this, *knowledge update*.
2. **Labelled evidence.** Every LongMemEval question lists the sessions that hold its answer. This makes it possible to check what a system stored against what was said.
3. **Scoring that can be trusted.** The questions were written and checked by people, and the judge was validated against human experts.
4. **A moderate size.** Every memory system has to read every session, and some make dozens of model calls per message. LongMemEval's knowledge-update questions are few (78), and each history is long but not huge. That made it possible to run five systems with their full write paths.

PersonaMem-v3, BEAM and DynamicMem test more realistic or much longer histories, and HorizonBench isolates preference changes more sharply. Each would make a good second experiment. LongMemEval fits this question at a cost that allows every system to run on every question.

## The LongMemEval benchmark

[LongMemEval][longmemeval] (Wu et al., ICLR 2025) is a benchmark of chat assistants' long-term memory. It has 500 questions, and each comes with its own chat history between one user and an assistant.

### How it was built

The authors started from an ontology of 164 user attributes in five categories: lifestyle, belongings, life events, situational context and demographic information (p. 4). For each attribute, a model wrote a background paragraph about a user and proposed questions about it. Human experts then filtered and rewrote all the questions, and split each answer into one or more *evidence statements* (p. 5).

Each evidence statement was then woven into its own chat session between a simulated user and an assistant. The user model was told to convey the statement *indirectly*: instead of saying "I bought a new car last month", it might ask for help with car insurance and mention the car in passing (p. 5). People then checked and edited every evidence session.

Finally, each question gets a history: its evidence sessions, inserted among many unrelated sessions, all with plausible dates. The unrelated sessions come from two sources (p. 5):

- **simulated chats with the same user** about other attributes, chosen so that they do not conflict with the evidence;
- **public chat logs** from the ShareGPT and UltraChat datasets.

The authors compare the result to a needle-in-a-haystack test, except that the needles are whole sessions and there can be several of them.

### Five abilities and seven question types

The questions test five abilities: information extraction, multi-session reasoning, knowledge updates, temporal reasoning, and abstention (saying "you never told me" when the answer is not in the history) (p. 4). They come in seven types. The paper's Figure 1 shows one example of each:

{% include diagram.html name="benchmark-types" alt="The paper's Figure 1: one example for each of LongMemEval's seven question types, each with the user's statements on the left and the question and answer on the right. The knowledge-update example is outlined: the user mentions a family trip to Hawaii, later a family trip to Paris, and the question asks where the most recent family trip was; the answer is Paris." caption="LongMemEval's seven question types, from the paper (Wu et al., ICLR 2025, Figure 1, CC BY 4.0; the outline is added). This experiment uses only the knowledge-update questions." %}

The 500 questions split into the types like this:

- multi-session: 133;
- temporal reasoning: 133;
- knowledge update: 78;
- single-session-user: 70;
- single-session-assistant: 56;
- single-session-preference: 30.

Abstention is not a separate pool: 30 of these questions were rewritten to ask about something that was never said.

This experiment uses only the **knowledge-update** questions, because they test the problem this series is about: a fact is stated, later changed, and the newer value must win. The example in the figure, a family trip to Hawaii followed by one to Paris, is one of them, and one of the systems below answered it wrongly.

### The versions of the dataset

The benchmark comes in three versions, which differ only in how many unrelated sessions surround the evidence:

- **Oracle:** only the evidence sessions. It measures how well a model answers when it has exactly what it needs.
- **S:** about 115,000 tokens per question, roughly 40 to 60 sessions.
- **M:** about 500 sessions per question, around 1.5 million tokens.

I used **S**. Its histories still fit into the prompt of a current model, which matters: reading the whole history is one of the baselines a memory system has to beat, and on M that baseline cannot run at all. M would also have multiplied the cost of every system that writes memory by about ten.

I used the *cleaned* release of S. In September 2025 the authors replaced the data with a version that "removes noisy history sessions that interfere with the answer correctness", as its dataset card puts it. The data, like the code, is released under the MIT licence.

### The knowledge-update questions

Of the 78 knowledge-update questions, 6 are abstention questions, which ask about something the user never said (more on them at the end of this section). That leaves 72. Here is what their histories look like, measured on the cleaned S file:

- **Sessions per history:** 48 on average, between 39 and 55, of about ten turns each.
- **Who writes most of the text:** the assistant. The user's turns are 13% of the characters; the rest is the assistant's long replies.
- **Unrelated sessions:** about half are simulated chats with the same user and half are public chat logs, as the paper's recipe says (p. 19).
- **Evidence:** exactly two sessions per question, in all 72. The first states the fact; the second changes it.
- **Time between them:** a median of 50 days, from the same day to 255 days. The question is asked a median of 15 days after the second session.

Eight of the 72 questions ask for the earlier value ("What was my *previous* personal best?"), and three ask for both. The rest ask for the current value.

### One question, as it is stored

Here is one question from the file, with every field. The 40 sessions of its history are shortened to their first entries, and the long assistant replies are cut:

```json
{
  "question_id": "6a1eabeb",
  "question_type": "knowledge-update",
  "question": "What was my personal best time in the charity 5K run?",
  "question_date": "2023/06/25 (Sun) 13:22",
  "answer": "25 minutes and 50 seconds (or 25:50)",
  "answer_session_ids": ["answer_a25d4a91_1", "answer_a25d4a91_2"],
  "haystack_session_ids": ["6387e969", "sharegpt_wsUEkMN_0", "e32f5666_3", …],
  "haystack_dates": ["2023/04/23 (Sun) 08:57", "2023/04/24 (Mon) 09:36", "2023/04/27 (Thu) 13:38", …],
  "haystack_sessions": [
    [
      {"role": "user", "content": "…", "has_answer": false},
      {"role": "assistant", "content": "…", "has_answer": false},
      …
    ],
    …
  ]
}
```

The fields, in order:

- **`question` and `question_date`.** The question, and the date on which the user asks it. A system answers as if on that date.
- **`answer`.** The reference answer for the judge. It allows two spellings of the same value.
- **`answer_session_ids`.** The two evidence sessions, by their ids. The ids starting with `answer_` are evidence sessions; `sharegpt_…` and `ultrachat_…` are public chats; the rest are simulated chats with this user about other things.
- **`haystack_session_ids`, `haystack_dates` and `haystack_sessions`.** Three parallel lists, one entry per session: the id, the date, and the turns. Each turn has a `role`, its `content`, and a flag `has_answer` that marks the turn holding the evidence.

The two evidence turns are these. On 23 May, in a session that began with the user asking when their next soccer game is:

```json
{"role": "user", "content": "That's really helpful, thanks! I've been doing some running lately, and I'm happy to say that I recently set a personal best time in a charity 5K run with a time of 27:12. Do you have any tips on how to improve my running technique to make me more efficient and effective on the soccer field?", "has_answer": true}
```

And a week later, on 30 May, as the first message of a session about endurance training:

```json
{"role": "user", "content": "I'm training for another charity 5K run coming up and I was wondering if you could give me some tips on how to improve my endurance. By the way, I'm hoping to beat my personal best time of 25:50 this time around.", "has_answer": true}
```

Three things in this example are typical of the knowledge-update questions:

- **The change is said in passing**, in a "by the way" clause of a message about something else. Nothing says "my personal best has changed". A system that stores what each message is mainly about will miss it.
- **The new value has to be inferred.** The user never says that they ran 25:50. They say they hope to beat a personal best of 25:50, which implies that the best is now 25:50 and no longer 27:12.
- **The evidence is a small part of the history.** The two turns sit in 2 of the 40 sessions. Ten turns later, the second session repeats the request almost word for word, without the number.

The figure below shows where the two sessions sit in the history:

{% include diagram.html name="lme-history" alt="The history of the question 'What was my personal best time in the charity 5K run?' as a row of 40 sessions from 23 April to 30 May 2023: most are simulated chats about the same user's other topics, some are public chats, and two are evidence sessions. On 23 May the user mentions a personal best of 27:12 while asking about soccer; on 30 May, asking about endurance training, they hope to beat their personal best of 25:50. The question is asked on 25 June; the answer is 25:50. A second row shows the trimmed history used in the main run: the two evidence sessions and eight others, in date order." caption="One question's history, session by session. The first row is the whole history of the S version; the second is the shorter history that the main run used (described under \"Limitations of this experiment\")." %}

One more detail of the file matters for a memory system. The sessions are listed day by day, but within a day their order does not follow their times: in this question, the evidence session of 30 May, at 13:53, comes after sessions dated 15:35, 18:35 and 19:15 on the same day. The experiment sorts every history by its dates before feeding it to a system, because that is the order in which a user would have had the conversations. For one question, this order turns out to contradict the answer key (see "Why the wrong answers were wrong").

### Questions that were left out

The six knowledge-update questions marked as abstention questions ask about something the user never said. One asks "How many Italian restaurants have I tried in my city?" in a history where the user talks about Korean restaurants. The expected answer is that the information is not there: "You mentioned trying Korean restaurants but not Italian restaurants."

These questions test whether a system refuses to answer, not whether it updates a fact. They were left out, which leaves 72 questions. Five of them went to a pilot run, which was used to check the pipeline and the cost estimates and is not reported. The other **67 questions** are the main run, and every number below is out of 67 unless it says otherwise.

## How answers are scored

Every answer is scored by a judge model with LongMemEval's own prompts. The answering prompt is also LongMemEval's own, so the only thing that differs between the systems is what each puts into the prompt.

{% include diagram.html name="eval-pipeline" alt="Six steps from left to right. History: ten sessions fed one at a time with their dates. Write: the memory system turns each session into memory; the baselines skip this step. Memory: what the system keeps. Read: at the question's date, a search or a model call picks what the answering model sees. Answer: the same model and LongMemEval's answer prompt for every system. Judge: LongMemEval's knowledge-update judge prompt, yes or no. Three probes read the memory, the context given to the answer, and the answer." caption="How one question is run and scored. The judge gives the score. The three probes, described under \"Analysis of the answers\", say where a wrong answer was lost." %}

### The answering prompt

The two baselines give the answering model raw chat history; the memory systems give it what they returned. LongMemEval's code has a prompt for each case, and they differ only in their first sentences ([LongMemEval's code][lme-code], `src/generation/run_generation.py`, and the experiment's [`prompts.py`][prompts-py]):

```text
I will give you several history chats between you and a user. Please answer the question based on the relevant chat history. Answer the question step by step: first extract all the relevant information, and then reason over the information to get the answer.


History Chats:

{context}

Current Date: {date}
Question: {question}
Answer (step by step):
```

```text
I will give you several facts extracted from history chats between you and a user. Please answer the question based on the relevant facts. Answer the question step by step: first extract all the relevant information, and then reason over the information to get the answer.


History Chats:

{context}

Current Date: {date}
Question: {question}
Answer (step by step):
```

The second prompt goes to every memory system except Letta, whose agent answers the question itself, in its own reply; answering is part of what Letta does.

For the 5K question, Mem0's search returned 20 stored facts. The first two were these, with the dates the experiment adds to each fact:

```text
- User recently set a personal best time of 27:12 in a charity 5K run. (from a chat on 2023-05-23)
- User is training for an upcoming charity 5K run and aims to beat their personal best time of 25:50. (from a chat on 2023-05-30)
```

The other 18 were about soccer, tennis, a photo album, document folders and other things the user had talked about. The answering model replied, step by step:

```text
2.  **Reason over the information:**
    *   The information from 2023-05-23 mentions a personal best of 27:12.
    *   The information from 2023-05-30 indicates that the user's current personal best goal is to beat 25:50. This implies that the user achieved a time of 25:50 at some point between the two chats (or that 25:50 is the established personal best they are currently trying to improve upon).
    *   Therefore, the most recent and accurate personal best time mentioned in the history is 25:50.

**Answer:** Your personal best time in the charity 5K run is 25:50.
```

### The judge

The judge reads the question, the reference answer and the whole reply, and answers yes or no. LongMemEval has one judge prompt per question type. This is the one for knowledge updates ([LongMemEval's code][lme-code], `src/evaluation/evaluate_qa.py`):

```text
I will give you a question, a correct answer, and a response from a model. Please answer yes if the response contains the correct answer. Otherwise, answer no. If the response contains some previous information along with an updated answer, the response should be considered as correct as long as the updated answer is the required answer.

Question: {question}

Correct Answer: {answer}

Model Response: {response}

Is the model response correct? Answer yes or no only.
```

The last sentence of its first paragraph matters for this question type: an answer may mention the old value, as Mem0's reply above does, as long as the answer it gives is the new one. The judge said yes.

The paper checked its judge (GPT-4o with these prompts) against human experts and found more than 97% agreement (p. 6). This experiment uses another judge model, so I checked it too, against a second judge model: on 132 answers that both judged (12 questions, every configuration), they agreed on 130.

### How precise the scores are

Each configuration answers 67 yes-or-no questions. With so few, a score has a wide margin. A 95% interval (Wilson's) on a score of 90% runs from 80% to 95%, and on a score of 84% from 73% to 91%. **Only large differences mean anything.**

For pairs of configurations, a sharper test is to compare them on the same questions: McNemar's test counts the questions that only one of the two got right. Even the clearest gap among the configurations that work, retrieval over Mem0, is 9 questions that only retrieval got right against none for Mem0. That gives p = 0.004 for the one comparison. But there are 28 such pairs. Testing that many pairs and taking the best one inflates the chance of a fluke, so a Bonferroni correction asks for p below 0.05 / 28 ≈ 0.0018, and this pair does not reach it. So the order among the systems that work is not a result.

The numbers are also **not comparable to published LongMemEval results**: the histories here are trimmed (see "Limitations of this experiment"), there is only one question type, and the models differ.

## The systems compared

Seven configurations ran on every question: two baselines and five memory systems. Each memory system is the real software, at its library's defaults, except where the experiment had to change something; each change is listed, with its reason, at the top of that system's module in the [repository][arms].

| Configuration | Who writes the memory | What is read at question time |
|---|---|---|
| **Full context** (baseline) | nobody | the whole history, in the prompt |
| **Retrieval** (baseline) | nobody: the raw turns are indexed | the 10 rounds (a user message and the reply after it) that best match the question by BM25 keyword search, with their dates |
| **Textual memory** | a model call after each session rewrites one plain-text profile | the whole profile |
| **Mem0** (mem0ai 2.2.1) | a model call after each session extracts short facts into a vector store | up to 20 most similar facts (the library's default) |
| **Graphiti** (graphiti-core 0.31.1, on Neo4j) | a pipeline of model calls per message builds a graph of dated facts and closes the ones that a newer fact contradicts | the 10 best facts by a hybrid keyword and embedding search, each with its dates |
| **Letta** (0.16.8 server) | the answering agent itself, with memory tools, in its own turn | the agent's memory blocks, plus whatever it finds by searching past messages |
| **Honcho** (3.3.0 server) | a background reasoner draws conclusions from each message, and a later "dream" draws more from those | two read paths from the same store: an agent that searches the conclusions and writes a summary (**chat**), or a search that returns dated conclusions (**representation**) |

The parts of this series explain each design in detail: [textual memory][part-3], [Mem0][part-4], [Graphiti][part-5], [Letta][part-6] and [Honcho][part-7].

**Why these two baselines.** A memory system exists to do better than doing nothing. With a history this long, "nothing" has two forms. Full context reads everything every time: it is the most a model can know, at the highest cost per answer. Retrieval over raw turns keeps everything and searches it at question time, with no model call to write anything. A memory system that loses to both is adding cost and failure modes without a benefit.

**What was held constant**, so that differences come from the systems:

- **One model in every seat.** Every model call that any system makes, and every answer, uses the same small model, `gemini-3.1-flash-lite`. Embeddings use `gemini-embedding-001`. A bigger model would raise every score, but would also hide the difference between designs behind the model's own skill.
- **The session dates.** Every system is given each session's date. Without dates, a system cannot tell which of two values is newer; several systems needed a change in the experiment's wrapper to accept one (Mem0, Graphiti, Letta and Honcho each take the time of the run as a message's date, unless told otherwise).
- **The same order.** Sessions go in one at a time, in date order, as a user would have had them.

No system was set up or tuned by the people who make it, and none of them was asked to; I ran each one as its documentation describes. Where a system was run more than once, every run is reported.

## Limitations of this experiment

The main limitation is the length of the histories, so it comes first: the main run used shorter histories than the benchmark provides. The section ends with the other limits.

### Shorter histories

Running every system on the whole history of all 67 questions would have cost about $2 per question, almost all of it Graphiti, which makes several model calls for every message. So the main run **trims** each history:

- it keeps **both evidence sessions**, so the information needed to answer is always there;
- it adds **8 of the other sessions**, drawn at random with a fixed seed;
- it keeps all 10 sessions **in date order, with their original dates**.

The second row of the history figure above shows the result for the 5K question. A trimmed history is about 25,000 tokens long on average (between about 15,000 and 34,000), against about 110,000 for a whole one.

Trimming keeps the evidence, but it removes three things that a whole history has:

- **Retrieval difficulty.** Finding two sessions among 10 is easier than among 48, for every system that searches.
- **Interference at write time.** Fewer unrelated sessions mean fewer unrelated memories that a new fact can be confused with or merged into.
- **Headroom over full context.** At 25,000 tokens, a model reads the whole history easily, so the full-context baseline is close to its best. A memory system can mostly only lose to it.

The main run therefore tests mainly the write path: whether a system stores the change, and what it does with the old value. It tests the read path less. And it tests memory where memory is not needed for capacity, so any loss compared with full context is the price of the memory layer.

**The check.** To see whether trimming changed the picture, 25 of the 67 questions were run again with their whole histories, about 48 sessions and 110,000 tokens each. Only four systems were run this way: the two baselines, textual memory and Mem0. Graphiti, Letta and Honcho cost several times more per session, and a whole history has five times as many sessions.

{% include diagram.html name="trimming-check" alt="Two slope charts for four systems, from the trimmed history of 10 sessions to the whole history. Accuracy on the same 25 questions: retrieval 100% to 96%, textual memory 96% to 92%, full context 92% to 84%, Mem0 84% to 84%; the order is the same in both runs. Cost per question: retrieval stays at $0.0016; full context goes from $0.0065 to $0.028; Mem0 from $0.040 to $0.18; textual memory from $0.022 to $0.28." caption="The same 25 questions with 10 sessions and with the whole history. The scores drop by one or two answers and keep their order. The cost of writing memory grows with the history." %}

| Configuration | Correct, 10 sessions | Correct, whole history | USD per question, 10 sessions → whole history |
|---|--:|--:|---|
| Full context | 23 of 25 (92%) | 21 of 25 (84%) | 0.0065 → 0.028 |
| Retrieval | 25 of 25 (100%) | 24 of 25 (96%) | 0.0016 → 0.0016 |
| Textual memory | 24 of 25 (96%) | 23 of 25 (92%) | 0.022 → 0.28 |
| Mem0 | 21 of 25 (84%) | 21 of 25 (84%) | 0.040 → 0.18 |

Three things follow:

- **The order of the systems did not change.** Every score moved by at most two answers, and on 25 questions one answer is 4 points. Retrieval stayed first, then textual memory, then full context and Mem0.
- **Full context slips but does not collapse.** All four of its wrong answers on whole histories gave the old value, which was in its prompt next to the new one. The 5K question was one of them: with the whole history, the answer was 27:12. In the LongMemEval paper, GPT-4o fell much further, from 0.870 with only the evidence sessions to 0.606 with the S history (p. 6, Fig. 3). Current models read long prompts better, which weakens the case for memory as a way to fit a history into the prompt, at least at this length.
- **Writing memory costs more as the history grows; reading does not.** Textual memory costs 13 times more per question on whole histories, because it rewrites a growing profile after every session. Mem0 costs about 4.5 times more, because it extracts facts from every session. Retrieval costs the same, because it does nothing until it is asked. What each answer reads stayed flat for Mem0 and retrieval; textual memory's profile grew from about 1,500 to 5,600 tokens.

### The other limits

- **One question type.** Only knowledge updates. The results say nothing about multi-session reasoning, temporal questions or preferences.
- **67 questions.** Enough to see large differences and to read every failure, too few to rank close systems.
- **One small model.** In Graphiti's extraction and in Letta's agent, the model's judgement *is* the memory policy, so a stronger model would change these two systems most.
- **One run per configuration.** A rerun would move each score by a few answers. Letta's agent runs at its own default temperature of 1.0, so it varies the most.
- **Library defaults.** Each system ran at its defaults, apart from the changes listed in its module. Tuning would help every system; it would also make the comparison depend on how much effort each one received.
- **Each fact changes once.** In every question a fact is stated once and changed once. A system whose strength is finding patterns across many sessions, which is what Honcho is built for, has little to work on here.
- **Letta's search.** The self-hosted Letta server searches past messages by literal phrase match unless a hosted vector service is configured. That affects how Letta recovers facts it did not write down.
- **The probes are model calls.** The checks described under "Analysis of the answers" are made by a model that reads text. They are reliable for clear cases and can misread unclear ones, which is why every wrong answer was also read by hand.

## Results: accuracy and cost

The chart shows the main result: accuracy with its interval, and the cost per question of building the memory and answering.

{% include diagram.html name="results" alt="Two panels for nine configurations. Accuracy with 95% intervals: full context 90%, retrieval 97%, textual memory 93%, Mem0 84%, Graphiti 82%, Letta 69%, Letta with a persona that keeps facts current 90%, Honcho dialectic chat 87%, Honcho representation 93%. Cost per question, building the memory included: full context $0.007, retrieval $0.002, textual memory $0.022, Mem0 $0.039, Graphiti $0.640, Letta $0.132, Letta with the persona $0.152, Honcho chat $0.029, Honcho representation $0.028." caption="Accuracy and cost per question on the 67 questions, with 10 sessions of history each. The shaded band is full context's interval." %}

The table has every run, including the first runs of Graphiti and Letta, which fed the conversation to them differently (see the next section):

| Configuration | Correct (of 67) | 95% interval | USD per question | Model calls to write | Seconds to write | Servers to run |
|---|--:|---|--:|--:|--:|---|
| Full context | 60 (90%) | 80–95% | 0.007 | 0 | 0 | none |
| Retrieval | 65 (97%) | 90–99% | 0.002 | 0 | 0 | none |
| Textual memory | 62 (93%) | 84–97% | 0.022 | 10 | 27 | none |
| Mem0 | 56 (84%) | 73–91% | 0.039 | 10 | 38 | none (local files) |
| Graphiti | 55 (82%) | 71–89% | 0.64 | 720 | 839 | Neo4j |
| Graphiti, first run | 12 (18%) | 11–29% | 0.24 | 121 | 145 | Neo4j |
| Letta | 46 (69%) | 57–78% | 0.13 | 81 | 379 | Letta server, Postgres |
| Letta, first run | 39 (58%) | 46–69% | 0.029 | 11 | 43 | Letta server, Postgres |
| Letta, with a persona that keeps facts current | 60 (90%) | 80–95% | 0.15 | 88 | 265 | Letta server, Postgres |
| Honcho, chat | 58 (87%) | 76–93% | 0.029 | 38 | 115 | Honcho API and worker, Postgres, Redis |
| Honcho, representation | 62 (93%) | 84–97% | 0.028 | 38 | 115 | the same |

The columns: *USD per question* is what the system spent on model calls to write its memory, search it and answer (judging is extra, and the same for all); *model calls to write* and *seconds to write* are per question, for its whole history.

What the table shows:

- **Eight configurations form one band**, from 82% to 97%, and their intervals overlap. As the previous section explained, the order inside the band is not a result.
- **Retrieval over raw turns is at the top of the band and the bottom of the cost column.** It writes nothing, so it cannot lose an update at write time; the revision is still in its index, word for word.
- **Letta at its defaults is the one working configuration clearly below the others.** With three lines added to its persona, it joins the band (see "Telling Letta's agent what to do").
- **The large differences are in cost and in what has to run.** Graphiti spends about 30 times what textual memory spends, and more than 300 times what retrieval spends, for no gain in accuracy here, and it needs a graph database. Textual memory and retrieval need nothing but the model.

The cost above includes building the memory. Once it is built, each answer has its own cost, and here the order changes:

{% include diagram.html name="answering" alt="Two panels for nine configurations, once the memory is built. Tokens read per answer, searching the memory and answering: full context 24,706, retrieval 5,389, textual memory 1,495, Mem0 1,127, Graphiti 456, Letta 9,778, Letta with the persona 13,643, Honcho chat 5,284, Honcho representation 1,328. Cost to answer: from $0.0004 for Graphiti to $0.0065 for full context." caption="What one answer reads and costs once the memory is built: every model call made to search the memory and to answer one question." %}

Full context reads the whole history for every answer, about 25,000 tokens; the memory systems read between about 450 and 14,000. Letta and Honcho's chat read the most of the memory systems, because an agent reads its instructions again with every step of its search. A memory system pays its cost once, when it writes; full context pays on every question. With many questions about one long history, that difference grows. With one question per history, as here, the write cost dominates.

## Analysis of the answers

An accuracy number says how often a system was right. It does not say why it was wrong. This section takes the answers apart: how the memory was inspected, what went wrong with two systems' first runs, what the memory held after a fact changed, and why each wrong answer was wrong.

### How the memory was inspected

A wrong answer about a changed fact can be lost at three points:

1. **The write.** The system never stored the new value.
2. **The read.** The new value was stored but did not reach the answering model.
3. **The answer.** The new value reached the model, but the model answered with the old one, or with something else.

To tell them apart, the experiment runs three *probes* on every answer: model calls (with `gemini-3.8-flash`) that read text and answer a few yes-or-no questions in JSON. Each needs the value before the change, which another model call reads once per question from the first evidence session. For the 5K question, it read `"old_value": "27:12"` and `"new_value": "25:50"`.

- **Probe 1, stored**, reads everything the system holds: is the new value there; is the old value there; and is the old value still presented as current, that is, not marked as replaced, ended or past?
- **Probe 2, delivered**, reads the context given to the answering model: did the new value reach it, and did the old one?
- **Probe 3, answered**, reads the answer: did it give the old value?

For Mem0 on the 5K question, the record is:

```json
"stored":    {"new_present": true, "old_present": true, "old_as_current": false},
"delivered": {"new_present": true, "old_present": true},
"stale":     {"gave_old": false, "gave_new": true}
```

Mem0 stored both values, the old one as the earlier personal best rather than the current one; both reached the answering model, which answered with the new one. The full probe prompts are in [`prompts.py`][prompts-py].

From the three probes, each wrong answer is sorted into one of five groups: the update was never stored; it was stored but not delivered; it was delivered and the answer gave the old value; it was delivered and the answer was wrong in another way; or the probes could not classify it. The last group is mostly the 9 questions that have no probes. Six of them ask for the earlier value, or for both values, so "old" and "new" do not separate; in the other three, the model that reads the old value found none in the first evidence session.

{% include diagram.html name="answer-loss" alt="Stacked bars, one per configuration, of all 67 answers. Correct: full context 60, retrieval 65, textual memory 62, Mem0 56, Graphiti 55, Graphiti's first run 12, Letta 46, Letta's first run 39, Letta with the persona 60, Honcho chat 58, Honcho representation 62. Update never stored: 0, 0, 1, 6, 5, 45, 15, 22, 3, 1, 2. Stored but not delivered: 2 for Graphiti, 1 for Honcho chat. Delivered and answered with the old value: full context 5, retrieval 2, and 0 to 3 for the others. Delivered, other error: 0 to 4. Not classified: 0 to 9." caption="All 67 answers of each configuration, sorted by the probes. Where the memory systems lost answers, it was mostly at write time." %}

A single "recall" number would merge these groups. The chart separates them. Two things stand out. The baselines lost their few answers at the last step, with both values in front of the model. And the memory systems lost theirs mostly at the first: the update was never stored.

### How a system is fed decides whether it remembers

The first runs of Graphiti and Letta scored 18% and 58%. Neither number turned out to be about the system. Both were about how the conversation was handed to it, and neither system reported an error.

{% include diagram.html name="feeding" alt="Two panels. Graphiti: in the first run each session was cut into episodes of up to 8,000 characters; 18% correct, 45 updates never stored, $0.24 per question. Fed one message per episode, as its own examples do: 82%, 5, $0.64. Letta: in the first run each session was sent in one request ending on an assistant message, and the agent mostly took no step; 58%, 22, $0.03. With one agent step per user message, it edited its memory about nine times per history: 69%, 15, $0.13." caption="The same two systems, fed the conversation in two ways. No setting of either system changed between the runs." %}

**Graphiti.** Graphiti adds data to its graph in *episodes*. The first run cut each session into episodes of up to 8,000 characters, many messages each. But Graphiti's extraction prompts are written for one message from a named speaker, and they tell the model to skip generic activities and, "when in doubt, do not extract". Graphiti also adds the previous ten episodes as context. With long episodes, every extraction prompt carried 60,000 to 80,000 characters, mostly the assistant's long answers, and the model returned two or three entities per episode.

In one traced question, the revision "I just finished my 5th project since starting painting classes" was in the prompt, and the model extracted `assistant` and `bold colors`. There was no fact about projects to update. Fed one message per episode, as Graphiti's own chat examples do, the same sentence produced the entities `user`, `painting project` and `painting classes`, and the fact "The user has completed their 5th project since they began attending painting classes".

**Letta.** Letta's agent decides what to remember during its own turn, when it replies to a user. The first run sent each session as one request containing all its messages, ending on an assistant message. The agent had nothing to reply to, and in most sessions it took no step at all. Its block of notes about the user was still empty after 43 of the 67 histories. The second run sent one user message at a time and let the agent reply to each itself; it then edited its memory about nine times per history.

Neither fix changed a setting. Both made the input look like the input each system was built for. That contract is written down in neither API, nothing fails when it is broken, and keeping it costs money: Graphiti's working run costs 2.7 times the broken one, Letta's 4.6 times. The practical lesson is for anyone who evaluates a memory system, or puts one into production: look at what it stored before you look at its score.

### What memory holds after a fact changes

The stored probe answers a question that accuracy cannot: once a fact has changed, what does the memory contain? The shares are of the 58 questions that have probes (57 for Letta, which could not build one history):

| Configuration | New value stored | Old value still stored | Old value still presented as current | Both values reached the answer | Correct when both reached it | Context given to the answer (tokens, est.) |
|---|--:|--:|--:|--:|--:|--:|
| Full context | n/a | n/a | n/a | 58 | 52 | 27,890 |
| Retrieval | n/a | n/a | n/a | 54 | 52 | 5,761 |
| Textual memory | 98% | 74% | 9% | 39 | 37 | 1,513 |
| Mem0 | 90% | 93% | 43% | 45 | 41 | 930 |
| Graphiti | 90% | 81% | 24% | 39 | 37 | 284 |
| Letta | 49% | 39% | 28% | 15 | 12 | 884 |
| Letta, persona | 93% | 77% | 11% | 43 | 42 | 1,288 |
| Honcho, chat | 95% | 93% | 74% | 39 | 33 | 77 |
| Honcho, representation | 95% | 93% | 74% | 53 | 51 | 935 |

The context column is an estimate (characters divided by four) of the text that the read path handed to the answering model. Three readings follow from the table.

**1. Few systems resolve the change when they write, and with dates it mostly does not matter.** A system can handle a change at write time, by replacing or closing the old value, or leave both values and let the answering model decide. Most left both. Mem0 still presents the old value as current in 43% of the questions: its current release only adds facts, so both values stay. Honcho does so in 74%: its conclusions stay side by side, and in this experiment its background "dream" recorded no change. Even Graphiti, the system built to close a superseded fact, still presents the old value as current in about a quarter of the questions.

Yet the answers were mostly right. When both values reached the answering model, each with its date, it picked correctly in most cases: 41 of 45 for Mem0, 51 of 53 for Honcho's representation. Dates turned resolving the change at write time from a requirement into an optimisation.

**2. The systems that overwrite keep less, not better.** Textual memory rewrites its whole profile after each session, and its rule for changes keeps the old value only as history. It presents the old value as current in only 9% of the questions, the fewest of the configurations that work. Its rewrites often keep the earlier value in the same line ("15 … as of 2023-09-30; previously 12 as of 2023-08-11"), which is why the old value is still *stored* in 74%. Letta's agent also overwrites, but only when it decides to write. It held the new value in only 49% of the questions, because, as the next sections show, it often did not write at the moment the change was mentioned.

**3. What reaches the prompt differs by a factor of about 360, and the shortest form lost answers.** Honcho's chat path hands the answering model a short summary written by its agent, about 77 tokens; full context hands it the whole history, about 28,000 tokens by the same estimate. Accuracy is within the same band. But the same Honcho store scored 87% through the summary and 93% as a list of dated conclusions. The summary is where answers were lost: its agent read both values and declined to choose between them (see the next section).

**Asking for the earlier value.** Eight questions ask for the value *before* the change, and three ask for both. My expectation was that the systems that overwrite would lose the earlier value. It did not show:

| Configuration | Current value (56) | Earlier value (8) | Both (3) |
|---|--:|--:|--:|
| Full context | 50 | 7 | 3 |
| Retrieval | 54 | 8 | 3 |
| Textual memory | 52 | 7 | 3 |
| Mem0 | 48 | 6 | 2 |
| Graphiti | 46 | 8 | 1 |
| Letta | 39 | 6 | 1 |
| Letta, persona | 50 | 8 | 2 |
| Honcho, chat | 48 | 7 | 3 |
| Honcho, representation | 52 | 7 | 3 |

Textual memory answered 7 of the 8, because its rewrites keep the history in the line. Eight questions are too few to measure a difference of this kind; the table answers the question I asked, but it does not separate the systems.

### Why the wrong answers were wrong

This is the error analysis. I read every wrong answer next to its history, what the system stored and what reached the answering model; the accounts, one per system, are in the repository's [findings][findings-dir]. With between 2 and 21 wrong answers per configuration, these are mechanisms, not rates. The counts below are from reading each answer, so they differ slightly from the probes' automatic classification in the chart above.

**Three questions are flawed.** They account for 12 of the 39 wrong answers of full context, retrieval, textual memory, Mem0 and Honcho's two paths (402 answers in all). In each, the dataset is at least as much at fault as the systems:

- **The sneakers (`618f13b2`).** "How many times have I worn my new black Converse…?" The session the dataset labels as the first says "four times"; the one it labels as the second says six, and the key says six. But both are dated the same day, and the times put the "six" session first (17:45) and the "four" session last (22:16). Every system read them in date order and answered four. This is the order within a day, described above, contradicting the key.
- **The mortgage (`852ce960`).** "What was the amount I was pre-approved for when I got my mortgage from Wells Fargo?" The history has $350,000 and later $400,000, and the key is the later value. Full context and retrieval read "when I got my mortgage" as asking for the first; full context says so in its answer.
- **A 5K run, again (`e66b632c`).** Another user asks "What was my *previous* personal best time for the charity 5K run?" The key is 27:45. But the later session says the new best is 26:30, "about a minute and a half" faster, which makes the previous one about 28:00. The systems answered 28:00 or 26:30.

Leaving these three questions out moves every score up by a few points and changes no conclusion. They are counted as they are.

**Most loss is at write time.** For the systems that write memory, the most common cause of a wrong answer is that the change was never stored: 4 of Mem0's 11 wrong answers, 6 of Graphiti's 12, and 14 of Letta's 21. The change is usually one clause in a message about something else, like "By the way, I just finished my 5th project since starting painting classes". This agrees with [HaluMem][halumem], which scores each memory operation separately: most systems there recall fewer than 60% of the facts they should have extracted, and most omit more than half of the updates, largely because a fact that was never extracted cannot be updated (p. 11). Retrieval over raw turns cannot lose a fact this way, because it writes nothing.

**Each system also has a failure of its own**, which follows from its design:

| System | Its characteristic failure | Example from the experiment |
|---|---|---|
| Full context | Both values in the prompt; the answer gives the old one | "She moved to Chicago" outweighed a later message that Rachel had moved to the suburbs (`830ce83f`) |
| Textual memory ([part 3][part-3]) | The profile's "previously" invites arithmetic | "The user has 25 postcards in their collection as of 2023-11-30 (up from 17 items reported on 2023-08-11)", answered as 25 − 17 = 8 (key: 25) |
| Mem0 ([part 4][part-4]) | Two values kept as two facts, then combined | "attended three sessions" and "attended five sessions … last year", answered as 3 + 5 = 8 (key: five) |
| Graphiti ([part 5][part-5]) | A fact is dated by when it became true, so the wrong fact can be closed | Paris, mentioned later as a trip "last month", was dated 1 April; Hawaii, mentioned as "recent", was dated the day it was said, 26 May. Graphiti closed Paris as superseded by Hawaii, and the answer followed (key: Paris) |
| Letta ([part 6][part-6]) | The agent notices the change and does not write it down | "By the way, I just checked and I'm now at 600 followers" drew "Congratulations on hitting 600 followers!" and no memory edit; 18 changes went this way |
| Honcho ([part 7][part-7]) | The chat agent declines to choose between two dated values | "…Clarification is required to resolve the discrepancy": 5 of the chat path's 9 wrong answers |

The Graphiti example is the knowledge-update question of the paper's Figure 1 above. Every other system answered it correctly.

**Full context is the control.** It had both values in its prompt in all 58 questions that have an earlier value, and it answered 6 of them wrongly, some of those on the flawed questions. That is roughly the answering model's share of the error, and it is small. [DynamicMem][dynamicmem] finds the same with other systems: the answering model causes 2–7% of failures, and most failures come from what the memory delivered (p. 13).

### Telling Letta's agent what to do

Letta's failures came in a chain. Its agent noticed changes without writing them down; when it did write, it wrote no dates; and when the value was missing at question time, its search could not find the message again, because the self-hosted server's search is a literal phrase match and the agent searched with paraphrases. In the default run, 97 of its 146 searches at question time returned nothing.

Letta has a place for instructions like these: the *persona* block, the part of the agent's memory that its users are expected to write. In the default run it held Letta's blank starter text. The third run added three lines to it, one for each link of the chain:

```text
How I keep my memory of the user:
- Every user message starts with its date in square brackets, for example [2024-01-15 09:30]. I write that date on each fact I save about the user, never the server's time shown on tool results or in my system prompt.
- When the user mentions a new value for something already in my memory (a count, a time, a place, a status), even in passing, I update that line at once with memory_replace and keep the earlier value with its date, for example "has 4 herb plants on the balcony (2024-03-02; earlier 2, 2024-01-15)".
- When the user asks about themselves, I check my memory and also search past messages. The search matches my query word for word, so I search with one or two distinctive words, not a whole phrase.
```

What each line fixes:

- **The first** gives every fact a date. An earlier pilot's persona said only that every message starts with its date, and the agent dated one whole history with the server's date, which every tool result carries; the line now names the date in brackets.
- **The second** makes the agent write at the moment a value changes, even when the change is said in passing, and keep the earlier value with its date.
- **The third** matches the search the agent actually has.

The agent wrote the new value at the message that carried it in 57 of the 64 questions that have such a message, against 31 before. The score rose from 69% to 90%, and 14 of the 17 answers it gained can be traced to these lines. Of its 7 remaining wrong answers, one is a lost update.

One caveat: I wrote the persona after reading these failures, on the same questions, so 90% is not a score on unseen data. The lines are general and none names a question. The change in what the agent wrote, 57 of 64 against 31, depends less on single answers than the score does, and it is the stronger evidence. No other system was rerun with a changed prompt.

## What recall benchmarks do not measure

LongMemEval, like most benchmarks above, asks whether a fact is recalled. A second problem is how a recalled fact is used, and some recent benchmarks find that memory makes it worse:

- **Over-personalisation.** [OP-Bench][op-bench] tests restraint: not bringing user facts into unrelated questions, and not agreeing with a false claim because it fits the profile. GPT-4o-mini scores 83.10 with no memory, 55.96 with retrieval, 46.32 with Mem0 and 41.86 with MemOS (p. 6). The memory that personalises most restrains least.
- **It depends on the model.** [PersonaMem-v3][personamem-v3] calls this an "over-personalization tax" and finds that it varies: GPT-5.5 restrains itself less with textual memory than with the raw history (71.0% against 75.4%), and Gemini-3.5-Flash more (69.9% against 57.0%) (p. 18).
- **Sycophancy.** [MemSyco-Bench][memsyco] finds that memory makes models agree with the user more: on objective factual questions, adding memory lowers Qwen3-8B's accuracy from 49.12 to between 26 and 36 (p. 7).
- **Belief update without a restatement.** [HorizonBench][horizonbench] isolates the update itself: a life event changes a preference, and the user never restates it. The best of 25 models answers 52.8% (p. 2), and when models err on a changed preference, more than a third of the time they pick the value the user first stated (p. 8). This is the same failure as above, without the "by the way" sentence that LongMemEval at least provides.

None of this shows up in an accuracy score on recall questions, including the ones in this experiment.

## Where memory systems are heading

Every system in this series that writes memory decides what to write with a prompt, and the error analysis above says that this decision is where most answers were lost. Recent research moves the decision from prompts to rules that are trained or derived:

- **Trained write decisions.** [Memory-R1][memory-r1] trains Mem0's four operations (add, update, delete, do nothing) with reinforcement learning, from only 152 question–answer pairs (p. 1–2).
- **A test instead of a prompt.** [SAGE][sage] decides most writes with a novelty test over the stored embeddings, and calls a model only when the test is unsure.
- **What can be forgotten.** [DeMem][demem] treats memory as a compression problem: two histories may share one memory as long as the same action is right for both. This gives an exact rule for what can be merged or forgotten. It also shows that similarity between descriptions barely predicts which memories can be merged (AUC 0.548, p. 2).
- **Several answers instead of one.** [Belief Memory][belief-memory] keeps several candidate conclusions with probabilities, instead of committing to one per observation.

Most of the evidence for these methods comes from LoCoMo and small models, so the direction is clear and the size of the gain is not.

Two questions stay open, as far as I can find:

- **What to forget.** No outcome tells a system that a memory should have been dropped, so there is little to train on. Forgetting rules in today's systems use constants that a person chose.
- **Close or delete.** When a fact changes, a system can keep the old fact and mark it as replaced (Graphiti), or remove it (the delete operation of Mem0's paper, and what a privacy request requires). I found no study that compares the two on the same task. This experiment covers both camps, plus "only add" (Mem0's current release) and "overwrite in place" (textual memory, Letta). On these questions, with dates, which camp a system belonged to mattered less than whether it stored the change at all.

## Which memory design to use when

There is no single winner in these results. But they support a few defaults:

{% include diagram.html name="decision-guide" alt="Seven rows: a situation, the design to start from, and what this experiment showed. The history fits in the prompt: no memory, the whole history or a keyword search over the raw turns with their dates. A person should read and correct the memory: textual memory. Too many facts for one profile: a fact store with search, with dates. Earlier values or links between people and things matter: a dated graph fed one message at a time. The agent should decide what to keep: an agent that edits its memory, told when to write, how to date and what to do with the old value. Answers depend on what the user implies: a background reasoner, read as dated conclusions. In every case: read what the system stored." caption="Which design to start from, by situation, with what this experiment showed about each." %}

- **If the history fits in the prompt, start with no memory system.** Put the whole history in, or search the raw turns. Here, a plain keyword search over raw turns, with their dates, scored highest at the lowest cost, and it wrote nothing that could be lost.
- **When a person should be able to read and correct the memory, use a text profile.** One rewrite per session, with a rule for what to do when a value changes, and absolute dates. It resolved changes at write time better than anything else here, and its memory is plain text. Its write cost grows with the history.
- **When the facts outgrow one profile, add a store with search,** and pass the conversation's dates in when writing and show them when reading. With dates, the answering model chose the newer value in most questions where both reached it.
- **A dated graph earns its cost** when questions need earlier values or paths between people and things, and you can pay for several model calls per message. Feed it one message at a time.
- **An agent that writes its own memory needs instructions:** when to write, how to date, what to do with the old value. Three lines moved Letta from the bottom of the table to the band.
- **A background reasoner earns its cost** when answers depend on what the user implies rather than states. Read its conclusions as a dated list, not through a summary.
- **Whatever you use, read what it stored.** Two configurations here scored 18% and 58% with no error anywhere, until the stored memory was read.

## Run it yourself

The [repository][repo] has the experiment's code, the result file of every question and configuration (with what the system stored, what it returned, its answer, the judge's verdict and the probes), the log of every model call's tokens and cost, and the accounts of every wrong answer. [`docs/experiment.md`][experiment-md] explains how to run it; [`docs/experiment-results.md`][results-md] summarises the results.

Every model call used `gemini-3.1-flash-lite` on Vertex AI: every call inside every system, and every answer. Embeddings used `gemini-embedding-001`. The judge was `gemini-3.1-pro-preview`, and the probes and the second judge `gemini-3.8-flash`. I used one small, cheap model everywhere so that the differences come from the memory systems, not the models, and so that systems with hundreds of model calls per question could run on every question. The systems were mem0ai 2.2.1, graphiti-core 0.31.1 on Neo4j 5.26, the Letta 0.16.8 server (its last Python release) and the Honcho 3.3.0 server, run between 17 and 18 October 2026.

The whole experiment cost about $110 on Vertex AI: $93 for the main run (of which $11 for Letta's persona run and $6 for judging and probes), $13 for the whole-history run, $3 for the pilot, and the rest for smoke tests and traces. Every table in this post can be rebuilt from the committed result files without any model call (`python -m memeval.findings`). Running the systems again costs about as much as the first time.

Model replies vary from run to run, even with the same prompt, and a different model changes more. A rerun will move each score by a few answers, and some failures will change places; the mechanisms described above stay the same.

Each part of this series also has a notebook that runs one system on a short test conversation, with every model call printed; they are linked from the [repository][repo].

Here are a few experiments worth trying:

- **Run another question type.** LongMemEval's multi-session and temporal-reasoning questions test different abilities; the systems may order differently there.
- **Run the whole histories for every system,** or the M version, where the history no longer fits in the prompt and full context drops out.
- **Change the answering model.** Use a stronger model for the answers only, or for everything, and see which systems gain most.
- **Rewrite textual memory's rule for changes** to record "now 25; reported 17 on 2023-08-11" instead of "up from 17", and see whether the arithmetic failures go away.
- **Remove the section on contradictory information from the prompt of Honcho's chat agent,** and see whether the chat path recovers the answers it declined.

## References

<!-- REFS -->

Papers:

- Packer et al., [MemGPT: Towards LLMs as Operating Systems][memgpt] (2023)
- Maharana et al., [Evaluating Very Long-Term Conversational Memory of LLM Agents][locomo] (2024)
- Wu et al., [LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory][longmemeval] (2024)
- Tan et al., [MemBench: Towards More Comprehensive Evaluation on the Memory of LLM-based Agents][membench] (2025)
- Hu et al., [Evaluating Memory in LLM Agents via Incremental Multi-Turn Interactions][memoryagentbench] (2025)
- Tavakoli et al., [Beyond a Million Tokens: Benchmarking and Enhancing Long-Term Memory in LLMs][beam] (2025)
- Chen et al., [HaluMem: Evaluating Hallucinations in Memory Systems of Agents][halumem] (2025)
- Li et al., [HorizonBench: Long-Horizon Personalization with Evolving Preferences][horizonbench] (2026)
- Xie et al., [DynamicMem: A Long-Horizon Memory Benchmark in Real-World Settings][dynamicmem] (2026)
- Jiang et al., [PersonaMem-v3: Toward Omni-Platform Personal Intelligence for Holistic User Understanding, Recommendation, and Agentic Tasks][personamem-v3] (2026)
- Hu et al., [OP-Bench: Benchmarking Over-Personalization for Memory-Augmented Personalized Conversational Agents][op-bench] (2026)
- Xiang et al., [MemSyco-Bench: Benchmarking Sycophancy in Agent Memory][memsyco] (2026)
- Yan et al., [Memory-R1: Enhancing Large Language Model Agents to Manage and Utilize Memories via Reinforcement Learning][memory-r1] (2025)
- Wang et al., [SAGE: A Novelty Gate for Efficient Memory Evolution in Agentic LLMs][sage] (2026)
- Zou et al., [Remember the Decision, Not the Description: A Rate-Distortion Framework for Agent Memory][demem] (2026)
- Liao et al., [Belief Memory: Agent Memory Under Partial Observability][belief-memory] (2026)
- Wang and Chen, [MIRIX: Multi-Agent Memory System for LLM-Based Agents][mirix] (2025)
- Chhikara et al., [Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory][mem0] (2025)
- Rasmussen et al., [Zep: A Temporal Knowledge Graph Architecture for Agent Memory][zep] (2025)

<!-- /REFS -->

Other sources:

- Penfield Labs, [We audited LoCoMo: 6.4% of the answer key is wrong and the judge accepts up to 63% of intentionally wrong answers][penfield] (2026)
- Wu et al., [LongMemEval's code and data][lme-code], and [the cleaned data on Hugging Face][lme-data]
- [agent-memory-eval][repo], the code and results for this series

[memgpt]: https://arxiv.org/abs/2310.08560
[locomo]: https://arxiv.org/abs/2402.17753
[longmemeval]: https://arxiv.org/abs/2410.10813
[membench]: https://arxiv.org/abs/2506.21605
[memoryagentbench]: https://arxiv.org/abs/2507.05257
[beam]: https://arxiv.org/abs/2510.27246
[halumem]: https://arxiv.org/abs/2511.03506
[horizonbench]: https://arxiv.org/abs/2604.17283
[dynamicmem]: https://arxiv.org/abs/2606.22877
[personamem-v3]: https://arxiv.org/abs/2608.21381
[mirix]: https://arxiv.org/abs/2507.07957
[mem0]: https://arxiv.org/abs/2504.19413
[zep]: https://arxiv.org/abs/2501.13956
[op-bench]: https://arxiv.org/abs/2601.13722
[memsyco]: https://arxiv.org/abs/2607.01071
[memory-r1]: https://arxiv.org/abs/2508.19828
[sage]: https://arxiv.org/abs/2605.30711
[demem]: https://arxiv.org/abs/2605.10870
[belief-memory]: https://arxiv.org/abs/2605.05583
[penfield]: https://penfieldlabs.substack.com/p/we-audited-locomo-64-of-the-answer
[lme-code]: https://github.com/xiaowu0162/LongMemEval
[lme-data]: https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned
[repo]: https://github.com/anton-dergunov/agent-memory-eval
[arms]: https://github.com/anton-dergunov/agent-memory-eval/tree/main/src/memeval/arms
[prompts-py]: https://github.com/anton-dergunov/agent-memory-eval/blob/main/src/memeval/prompts.py
[findings-dir]: https://github.com/anton-dergunov/agent-memory-eval/tree/main/docs/findings
[experiment-md]: https://github.com/anton-dergunov/agent-memory-eval/blob/main/docs/experiment.md
[results-md]: https://github.com/anton-dergunov/agent-memory-eval/blob/main/docs/experiment-results.md
[part-3]: /posts/2199/01/agent-memory-3-textual-memory/
[part-4]: /posts/2199/01/agent-memory-4-mem0/
[part-5]: /posts/2199/01/agent-memory-5-graphiti/
[part-6]: /posts/2199/01/agent-memory-6-letta/
[part-7]: /posts/2199/01/agent-memory-7-honcho/
