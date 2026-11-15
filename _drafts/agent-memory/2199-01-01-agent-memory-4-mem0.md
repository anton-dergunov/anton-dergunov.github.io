---
title:     "Mem0: facts in a vector store"
excerpt:   "What Mem0 does between add() and search(): extraction, the update step the release dropped, and what a similarity cut leaves out."
topic:     llms-and-agents
date:      2199-01-01
permalink: /posts/2199/01/agent-memory-4-mem0/
series:    agent-memory
part:      4
tags:
  - llm
  - agents
  - memory
---

A language model sees only the text in its current prompt. To use what a user said in earlier sessions, an LLM agent needs a memory system: something that stores information from those sessions and puts it into a later prompt. A simple memory system can put everything it has stored into every prompt. That stops working when the stored information no longer fits in the prompt, or when reading all of it on every request costs too much. The memory system then has to select: for each request, it must find the few stored items that the request needs.

This part looks at the best-known design that selects: [Mem0][mem0]. After a conversation, a model call extracts short, standalone facts about the user and stores them in a vector store. When a new request arrives, a similarity search returns the stored facts closest to it. So a pipeline writes the memory, outside the conversation, and a search selects what the answering model reads. Most papers on LLM memory systems compare their system with Mem0, and its API is two calls: `add()` and `search()`.

This post explains what happens inside those two calls. It first describes the write path and the read path of the open-source library, with its prompts and the code around them. It then follows one short test conversation through the library, one call at a time. Finally, it examines how the design fails on longer histories and when I would use it. Every prompt and reply below comes from [the notebook for this part][notebook], which runs the real `mem0ai` library, or from a replay of the notebook's calls, marked as such. The code is in the [agent-memory-eval repository][repo].

## How Mem0 works

{% include diagram.html name="mem0" alt="Mem0's architecture, with the running example. Writing: after each session, an LLM call extracts short standalone facts, seeing the related facts already stored, and only adds. Memory: a vector store of nine facts; the old and the new value of the changed fact are both kept. Reading: a similarity search embeds the question and returns all nine facts, which go into the prompt; the answer covers every constraint." caption="Mem0, with the conversation used in this post. After each session one LLM call extracts facts and adds them to a vector store. At question time a similarity search returns the closest facts." %}

Mem0 has the two components that most memory systems have:

- a **write path**, which runs when the application calls `add()` with the messages of a conversation;
- a **read path**, which runs when the application calls `search()` with a question.

The description below is of version 2.2.1 of the open-source Python library, read from its source. The design in the Mem0 paper differs from it in one important step, and this section shows both.

### The write path: one call extracts facts, and only adds

The application decides when to call `add()`: after every message, or once after a session. Each `add()` runs these steps:

1. **Embed the new messages** (code and one embedding call). The messages are joined into one text, and an embedding model turns the text into a vector.
2. **Fetch related facts** (code). A vector search returns the 10 stored facts closest to that vector, for this user.
3. **Build the prompt** (code). The user prompt gets the new messages, the 10 related facts, the last 10 earlier messages and two dates.
4. **Extract** (one model call). The model returns a JSON list of new facts.
5. **Drop exact duplicates** (code). A fact is dropped only when its text is identical, character for character, to one of the 10 related facts or to another fact in the same reply.
6. **Store** (code and one embedding call). The remaining facts are embedded in one batch and inserted into the vector store.

Here is the same write path as pseudocode. It follows `_add_to_vector_store` in the library's `mem0/memory/main.py`:

```python
def add(messages, user_id):
    text = join(messages)                              # "user: …\nassistant: …"
    related = store.search(embed(text), top_k=10, user=user_id)
    related = [{"id": str(i), "text": fact.text}       # ids 0, 1, 2 … replace the stored ids
               for i, fact in enumerate(related)]

    reply = llm(system=ADDITIVE_EXTRACTION_PROMPT,     # the same for every call
                user=build_prompt(new_messages=text,
                                  existing_memories=related,
                                  last_k_messages=history.last(10)))

    new = [m for m in reply["memory"]
           if md5(m["text"]) not in hashes(related)]   # the only check against the store
    store.insert(vectors=embed_batch(new),             # payload: text, hash, created_at,
                 payloads=new)                         # attributed_to, user_id
    history.save(messages)
```

No step in this path changes or removes a stored fact. The library has no other write step for facts that it runs by itself.

**The user prompt.** The library builds the user prompt from seven slots. This is the complete user prompt of the first `add()` in the notebook, when the store was still empty:

```text
## Summary


## Last k Messages


## Recently Extracted Memories
[]

## Existing Memories
[]

## New Messages
user: I'm planning a dinner for my sister's visit to Berlin next week. […]
assistant: Understood — no meat, and peanuts are a hard exclusion. […]
user: Indian, usually. Paneer dishes especially. […]


## Observation Date
2026-10-07

## Current Date
2026-10-07

# Output:
```

The open-source library fills the seven slots as follows:

- **`Summary`** and **`Recently Extracted Memories`** are always empty. The code that builds the prompt accepts values for them, but the library never passes any.
- **`Last k Messages`** holds the last 10 messages of earlier `add()` calls for this user, each cut at 300 characters. The library keeps these messages in a small SQLite database.
- **`Existing Memories`** holds the 10 related facts from step 2. The library numbers them 0, 1, 2 and so on in place of their stored ids, so that the model cannot return an id that does not exist.
- **`New Messages`** holds the messages passed to `add()`.
- **`Observation Date`** and **`Current Date`** both hold the day on which the code runs. The example below shows what follows from that.

**The system prompt.** The system prompt (`ADDITIVE_EXTRACTION_PROMPT` in [`mem0/configs/prompts.py`][mem0-prompts]) is the same for every call. It is 33,653 characters long, so I show only the parts that decide the behaviour described in this post. Cuts are marked […], and line breaks are added for readability:

```text
# ROLE

You are a Memory Extractor — a precise, evidence-bound processor responsible
for extracting rich, contextual memories from conversations. Your sole
operation is ADD: identify every piece of memorable information and produce
self-contained, contextually rich factual statements.

[…]

## Existing Memories

Memories currently in the system relevant to this conversation. Formatted as:
[{"id": "uuid-string", "text": "..."}, ...]

Use these ONLY for deduplication and linking — do NOT extract new memories
from Existing Memories. Your extractions must come exclusively from New
Messages. If new information in New Messages is semantically equivalent to an
Existing Memory with no meaningful new context, skip it.

[…]

## Observation Date

When the conversation actually took place (e.g., "2023-05-24"). This is your
ONLY temporal anchor for resolving time references.

[…]

CRITICAL: "User went to Paris last week" is useless 6 months later. "User
went to Paris the week of May 15, 2023" is meaningful forever. Always ground
relative references to specific dates.

[…]

### Contextually Rich, Not Atomic

[…]

This applies especially to **transitions and changes**. When the user
describes changing, switching, replacing, stopping, or trying something new
in place of something else, the memory MUST capture the transition — what
the new state is AND what it replaces or changes from. The relationship
between old and new is critical context. Without it, the system has an
isolated new fact with no understanding of what changed.

Bad: "User prefers oat milk lattes"
Good: "User switched from almond milk to oat milk lattes after developing an
almond sensitivity"

[…]

## Memory Linking

When extracting a new memory, check if it relates to any Existing Memory. Add
related Existing Memory IDs to "linked_memory_ids". Link when:

- **Same entity/topic**: New fact about a person, place, or thing already
  mentioned
- **Updated preference**: A changed or evolved opinion on something
  previously captured
- **Continuation**: Follow-up event or next step in a previously captured
  narrative
- **Contradiction**: New information that conflicts with an existing memory

[…]

# OUTPUT FORMAT

Return ONLY valid JSON parsable by json.loads(). No text, reasoning,
explanations, or wrappers.

## Structure

{
  "memory": [
    {"id": "0", "text": "First extracted memory", "attributed_to": "user",
     "linked_memory_ids": ["uuid-of-related-existing-memory"]},
    {"id": "1", "text": "Second extracted memory", "attributed_to": "assistant"}
  ]
}

[…]
```

Four rules in this prompt decide what happens to a fact that changes:

- **The role, for the only operation** ("Your sole operation is ADD"). The model can return new facts and nothing else. The output format has no field for changing or removing a stored fact.
- **The rule for transitions** ("the memory MUST capture the transition — what the new state is AND what it replaces or changes from"). Because the old fact stays in the store, the new fact is asked to say what it replaces, in its own sentence. This rule is the library's whole policy for a changed fact.
- **The rule for dates** ("This is your ONLY temporal anchor for resolving time references"). A phrase such as "last week" means nothing in a fact that a model reads months later. So the extraction converts it into a date, counted from the `Observation Date`.
- **The rule for links** ("Add related Existing Memory IDs to `linked_memory_ids`"). The model is asked to connect a new fact to the stored facts it continues, updates or contradicts.

The library does not use the links. The write loop reads two fields of each returned fact, `text` and `attributed_to`. The field `linked_memory_ids` is never read, and the table that maps the numbers 0, 1, 2 back to stored ids is built and then not used. The example and the section on failures show what the model put into this field.

**What is in 33,653 characters.** The system prompt has 8,131 tokens. It is the longest single prompt in the notebooks of this series. For comparison, the largest prompt of Zep/Graphiti ([part 5][part-5]) has about 2,400 tokens, and the prompt of textual memory ([part 3][part-3]), the simplest design in the series, has about 240.

{% include diagram.html name="mem0-prompt" alt="Two bars drawn to the same scale, one for each of the two extraction calls in the example. Each call reads the same system prompt of 8,131 tokens. By characters, the system prompt is 2.5% role, 11.6% a description of the inputs, 40.1% guidelines on what to extract and how to write a memory, 38.5% eleven worked examples, 3.5% a final checklist and 3.7% the output format. Next to it, the user prompt with the conversation is a thin slice: 161 tokens for the first session and 434 tokens for the second." caption="What each extraction call in the example reads, to scale. The system prompt is the same on every call; the conversation is the thin slice at the right." %}

By characters, the system prompt divides as follows:

| Part | Share | What it holds |
|---|--:|---|
| Role | 2.5% | the task, in three paragraphs |
| Inputs | 11.6% | the seven slots of the user prompt, and the rule for dates |
| Guidelines | 40.1% | what to extract, how to write a memory, what never to do, when to link |
| Examples | 38.5% | eleven worked examples, each with input and expected output |
| Checklist | 3.5% | an instruction to read every message again before answering |
| Output format | 3.7% | the JSON structure |

Reading the prompt next to the code, I noticed four things that the open-source library pays for on every call and does not use, or says more than once:

- The description of `Summary` and `Recently Extracted Memories`, two slots that the library leaves empty.
- The section on linking and its worked example, whose output the library does not store.
- Sections for shared photos and for conversations between two named speakers.
- The warning that one main topic can hide a secondary fact. It appears in five places: the role, the guidelines, two of the examples and the checklist. The section on failures shows that the extraction still lost secondary facts in this way.

These are observations about the prompt, not about its authors' reasons. A comment in the code says that the prompt builder was ported from the hosted platform, which may fill the slots that the library leaves empty.

**What is stored.** Each fact is one row in the vector store: an embedding of its text, and a payload. These are the payload's fields and what each one holds:

```text
data           User has a severe, anaphylactic peanut allergy.
hash           the MD5 hash of the text, for the duplicate check
text_lemmatized the text in base word forms, for the keyword score
created_at     when the row was written (not when the user said it)
updated_at     the same value
attributed_to  user
user_id        anton
```

A fact has no validity dates, no category and no link to the messages it came from.

### What the paper describes instead

The [Mem0 paper][mem0] (2025, pp. 3–4) describes a write path with two model steps. The open-source library worked this way before version 2.0:

1. **Extraction.** For each new pair of messages, a model call receives a summary of the conversation, the last ten messages and the new pair. It returns candidate facts.
2. **Update.** For each candidate fact, the system fetches the ten most similar stored facts. A second model call compares the candidate with them and chooses one of four operations: ADD the candidate as a new fact, UPDATE a stored fact with it, DELETE a stored fact that it contradicts, or do nothing (NOOP).

The prompt of that second step is still in the library's `prompts.py`, as `DEFAULT_UPDATE_MEMORY_PROMPT`, although `main.py` no longer imports it. It begins as follows (the rest is guidelines and examples for each operation; this prompt names the fourth operation NONE):

```text
You are a smart memory manager which controls the memory of a system.
You can perform four operations: (1) add into the memory, (2) update the
memory, (3) delete from the memory, and (4) no change.

Based on the above four operations, the memory will change.

Compare newly retrieved facts with the existing memory. For each new fact,
decide whether to:
- ADD: Add it to the memory as a new element
- UPDATE: Update an existing memory element
- DELETE: Delete an existing memory element
- NONE: Make no change (if the fact is already present or irrelevant)

[…]
```

{% include diagram.html name="mem0-update" alt="Two write paths side by side. The Mem0 paper: an LLM call extracts candidate facts from each pair of messages; code fetches the ten most similar stored facts for each candidate; a second LLM call chooses one of four operations, ADD, UPDATE, DELETE or NOOP, so a contradicted fact can be deleted. The release, mem0ai 2.2.1: code fetches the ten stored facts most similar to the whole session; one LLM call extracts new facts with those ten in view and can only add; code drops exact duplicates by hash and stores the rest. The model's links from a new fact to related stored facts are not stored. In the example, the old value of the changed fact stays in the store next to the new fact." caption="The write path in the paper and in the release. The paper's second LLM step can update or delete a stored fact. The release has one LLM step, and it only adds." %}

Version 2.0.0 of the library (April 2026) removed the second step. Its release notes describe the new write path as "Single-pass ADD-only extraction" with "No separate UPDATE/DELETE pass", and say what replaces that pass: "Hash-based deduplication prevents exact duplicates; ranking at retrieval time handles the rest."

So the release moves the handling of a changed fact from the write path to the read path. The old and the new value are both stored, and the search and the answering model have to deal with both.

### The read path: a search selects part of the store

`search()` with a question runs these steps, with no model call:

1. **Embed the question** (one embedding call).
2. **Rank the stored facts** of this user by the similarity of their vectors to the question's vector.
3. **Drop** every fact with a similarity below 0.1.
4. **Cut** the list at `top_k` facts. The default is 20.

`search()` returns the facts with their scores. The application decides how to put them into a prompt. In the notebook, the answering call uses this system instruction and this prompt, where `{packet}` is the list of returned facts, one per line:

```text
You are a booking assistant. Be brief and concrete.
```

```text
What you remember about this user:
{packet}

Their request: {question}
```

The system instruction is written for the test conversation in this post, where the user asks the assistant to book a dinner.

**Two more scores, when optional packages are installed.** With the library's `nlp` extra (spaCy) and the `fastembed` package, the score of a fact has up to three parts:

- the **similarity** of the embeddings, as above;
- a **keyword score**: a BM25 match (a standard formula for keyword search) between the words of the question and the words of the fact;
- an **entity boost**: at write time, the library extracts names and noun phrases from each fact; at read time, a fact gets a boost when the question mentions one of its entities.

The three parts are added and divided by the highest possible total. Without the optional packages, the library uses the similarity alone and reports no error. The notebook ran without them, so its scores are similarities. The larger experiment in this series ran with them. The example below shows how the keyword score changes the order.

### The price of each choice

Each of the three design choices has a cost:

- **The write path extracts.** A fact that the extraction does not write down cannot be found later. The original messages are not searched.
- **The write path only adds.** When a fact changes, the old value and the new value are both in the store, and nothing marks which one is current.
- **The read path selects by a score.** The score measures how close a fact is to the question. It does not measure how important the fact is. A fact that must be in every answer has no way to be marked as such.

## The example, step by step

To show how the design works, this post follows one short test conversation through the library, one call at a time. The same conversation is used for every system in this series. It is deliberately small, so that the notebook can print every call and you can read each one.

The conversation has three sessions. Sessions 1 and 2 establish the facts. Session 3 starts without the earlier transcripts and asks one question. The question names none of the facts that a correct answer needs:

- **A fact that changes:** the user's diet changes from vegetarian to pescatarian.
- **A hard constraint:** a severe peanut allergy.
- **Facts about people that the question does not name:** Lena cannot eat shellfish, and Jonas is coeliac (no gluten).
- **Other facts:** the user likes Indian food and lives in Kreuzberg.

{% include diagram.html name="conversation" alt="The running example. On 14 March the user says they have been strictly vegetarian for eight years, have a severe peanut allergy, and like Indian food. Four months later, on 20 July, they say they are pescatarian now, have moved to Kreuzberg, and that their sister Lena (who can't eat shellfish) is coming with her partner Jonas (coeliac). Six weeks after that, in a new conversation, they ask for dinner for 'my sister and her partner'. A correct answer needs six things: the new diet and not the old one (a fact that changes), no peanuts (a hard constraint), no shellfish and no gluten (people the question does not name, reached through two links), Indian food and somewhere near Kreuzberg." caption="The conversation, and the six things a correct answer needs, grouped by what they test." %}

Two parts of this test press hardest on Mem0's design:

- **The fact that changes** tests the write path. The library only adds, so the question is what the store holds after the change.
- **The hard constraint** tests the read path. The question does not mention it, so the question is where the search ranks it.

In the sessions below, colours mark the phrases that became stored facts: <mark class="hl hl-facts">a phrase stored as the user said it</mark>, and <mark class="hl hl-changes">a relative date that was stored as a wrong absolute date</mark>.

### Session 1: five facts, one with a wrong date

**14 March 2026**

> **User:** I'm <mark class="hl hl-facts">planning a dinner for my sister's visit to Berlin</mark> <mark class="hl hl-changes">next week</mark>. Worth saying up front: I've been <mark class="hl hl-facts">strictly vegetarian for eight years</mark>, and I have a <mark class="hl hl-facts">severe peanut allergy — anaphylactic</mark>, not a preference.
>
> **Assistant:** Understood — no meat, and peanuts are a hard exclusion. Any cuisine you lean towards?
>
> **User:** <mark class="hl hl-facts">Indian, usually. Paneer dishes especially.</mark> And I'd <mark class="hl hl-facts">rather not spend more than about 40 euros a head</mark>.

The notebook passes the three messages to one `add()` call. The store is empty, so the user prompt is the one shown earlier, with empty slots. The model's reply:

```json
{
  "memory": [
    {"id": "0", "text": "User is planning a dinner in Berlin for their sister's visit during the week of October 12, 2026.", "attributed_to": "user"},
    {"id": "1", "text": "User has been a strict vegetarian for eight years.", "attributed_to": "user"},
    {"id": "2", "text": "User has a severe, anaphylactic peanut allergy.", "attributed_to": "user"},
    {"id": "3", "text": "User prefers Indian cuisine, specifically paneer dishes.", "attributed_to": "user"},
    {"id": "4", "text": "User has a budget of approximately 40 euros per person for the dinner.", "attributed_to": "user"}
  ]
}
```

The library stored all five facts. The reply shows what extraction does:

- **The messages are gone.** The store holds sentences in the third person, each understandable without the others. A later question with different words can match such a sentence more easily than it can match a turn of a conversation.
- **Each fact is a separate row.** The allergy and the cuisine are in different rows, because different questions will need them.
- **The assistant's messages added nothing.** They only repeated what the user said, and the prompt tells the model not to extract such repetitions.

One fact is wrong. The user said "next week" on 14 March. The stored fact says "the week of October 12, 2026". The model followed the rule for dates: it counted from the `Observation Date`, and the library had set that date to 7 October, the day I ran the notebook.

The library has no way to say when a conversation happened:

- `add()` has a `timestamp` argument, but the open-source library rejects it with an error that says the argument is a feature of the hosted platform.
- The function that builds the prompt accepts a date, but `add()` does not pass one.

So relative dates come out right only when `add()` runs on the day of the conversation. Any history that is loaded later, as in this notebook, gets wrong dates, with no error.

### Session 2: four facts added, and both values kept

**20 July 2026, four months later**

> **User:** Small update on the food thing — <mark class="hl hl-facts">I started eating fish</mark> <mark class="hl hl-changes">about a month ago</mark>. So <mark class="hl hl-facts">I'm pescatarian now, not vegetarian. Still no meat</mark>, and the peanut situation obviously hasn't changed.
>
> **Assistant:** Noted, fish is in. Anything else shifted?
>
> **User:** <mark class="hl hl-facts">I moved to Kreuzberg in May, so anything walkable from there is a plus.</mark>
>
> **Assistant:** Kreuzberg, noted. Anything else for next time?
>
> **User:** Yes — <mark class="hl hl-facts">my sister Lena is coming back in the autumn, and she's bringing her partner, Jonas.</mark>
>
> **Assistant:** Lovely. Anything I should know about what they eat?
>
> **User:** <mark class="hl hl-facts">Lena can't eat shellfish, and Jonas is coeliac.</mark>

The second `add()` first looks up related facts. The store holds five facts, fewer than ten, so all five are returned, ordered by similarity to the new session. This is the part of the user prompt that the library filled from what it already had (line breaks added between the facts):

```text
## Last k Messages
user: I'm planning a dinner for my sister's visit to Berlin next week. […]
assistant: Understood — no meat, and peanuts are a hard exclusion. […]
user: Indian, usually. Paneer dishes especially. […]


## Recently Extracted Memories
[]

## Existing Memories
[{"id": "0", "text": "User is planning a dinner in Berlin for their sister's visit during the week of October 12, 2026."},
 {"id": "1", "text": "User has been a strict vegetarian for eight years."},
 {"id": "2", "text": "User has a budget of approximately 40 euros per person for the dinner."},
 {"id": "3", "text": "User has a severe, anaphylactic peanut allergy."},
 {"id": "4", "text": "User prefers Indian cuisine, specifically paneer dishes."}]
```

Session 1 is in this prompt in two forms: its three messages, word for word, and the five facts extracted from them. The fact that the new session contradicts has the id 1.

The model returned four facts, and the library added them. The store then held nine facts:

| # | Stored fact | Added after |
|--:|---|---|
| 1 | User is planning a dinner in Berlin for their sister's visit during the week of October 12, 2026. | session 1 |
| 2 | **User has been a strict vegetarian for eight years.** | session 1 |
| 3 | User has a severe, anaphylactic peanut allergy. | session 1 |
| 4 | User prefers Indian cuisine, specifically paneer dishes. | session 1 |
| 5 | User has a budget of approximately 40 euros per person for the dinner. | session 1 |
| 6 | **User transitioned from a strict vegetarian diet to a pescatarian diet in September 2026, meaning they now eat fish but no other meat.** | session 2 |
| 7 | User relocated to the Kreuzberg neighborhood in May 2026 and prefers restaurant options within walking distance. | session 2 |
| 8 | User's sister, Lena, is visiting in the autumn of 2026 and has a shellfish allergy. | session 2 |
| 9 | User's sister Lena is traveling with her partner, Jonas, who has coeliac disease and requires a gluten-free diet. | session 2 |

Four things happened in this call.

**Both values are in the store.** Fact 2, the old value, is unchanged. Nothing updated it, deleted it or marked it as replaced. Fact 6, the new value, sits next to it. Both are searchable in the same way.

**The new fact names the old value.** Fact 6 does not say "User is pescatarian". It says "transitioned from a strict vegetarian diet to a pescatarian diet". The model followed the rule for transitions. An answering model that reads fact 6 learns which value is current, even when it reads fact 2 as well.

I checked what this wording depends on with a replay: I sent the same prompt again with `Existing Memories` and `Last k Messages` emptied, three times. Each reply still began with "User transitioned from a vegetarian diet to a pescatarian diet". So the wording came from the user's own sentence ("pescatarian now, not vegetarian") and the rule for transitions, not from the old fact in the prompt. The old fact contributed one word, "strict". The wording therefore depends on the user stating the change as a change. A user who only says "I had salmon last night" gives the rule nothing to work with.

**The model linked the new fact to the old one, and the link was dropped.** The notebook did not print the raw reply of this call, so I replayed the call five times with the complete prompt. The five replies were identical. In each of them, the new fact carried `"linked_memory_ids": ["1"]`: a link to "User has been a strict vegetarian for eight years". The model identified the stored fact that the new fact replaces. The library does not read this field, so the store holds no trace of the link. (The replay's wording differed slightly from the notebook's run: "but continue to avoid meat" in place of "but no other meat".)

**A second wrong date.** Fact 6 says that the change happened "in September 2026". The user said "about a month ago" on 20 July, which is June. The model again counted from 7 October. Fact 7 has the right month, because the user named it ("in May"). Two of the nine facts now carry a date that was never true, and nothing in the store marks a date as computed.

The extraction also reworded a constraint, as other designs in this series do when a model rewrites what the user said: "Lena can't eat shellfish" became "has a shellfish allergy", a cause that the user did not give.

### Session 3: the search returns all nine, in an order that depends on the question

**1 September 2026, a new session with no transcript of the earlier ones**

> **User:** My sister and her partner are in town tonight. Book the three of us somewhere for dinner — you know what we can and can't eat.

The notebook calls `search()` with this question and `limit=6`. Nine facts came back:

| Rank | Score | Stored fact |
|--:|--:|---|
| 1 | 0.740 | User's sister, Lena, is visiting in the autumn of 2026 and has a shellfish allergy. |
| 2 | 0.732 | User's sister Lena is traveling with her partner, Jonas, who has coeliac disease and requires a gluten-free diet. |
| 3 | 0.725 | User is planning a dinner in Berlin for their sister's visit during the week of October 12, 2026. |
| 4 | 0.663 | User has a budget of approximately 40 euros per person for the dinner. |
| 5 | 0.623 | User relocated to the Kreuzberg neighborhood in May 2026 and prefers restaurant options within walking distance. |
| 6 | 0.616 | User prefers Indian cuisine, specifically paneer dishes. |
| 7 | 0.612 | User has a severe, anaphylactic peanut allergy. |
| 8 | 0.589 | User has been a strict vegetarian for eight years. |
| 9 | 0.588 | User transitioned from a strict vegetarian diet to a pescatarian diet in September 2026, meaning they now eat fish but no other meat. |

**Why nine came back when the notebook asked for six.** In this version of the library, the argument that limits the number of results is `top_k`. `search()` does not know the argument `limit` and ignores it, so `limit=6` had no effect and no error was raised. The default of 20 applied, and the store holds only nine facts. In a replay, `top_k=6` returned six facts.

The search worked for the people that the question does not name. "My sister and her partner" shares no name with the facts about Lena and Jonas, and both facts are at the top. Each of these two facts holds the whole connection in one sentence: the sister, her name and her constraint, or the sister, her partner's name and his constraint. The extraction wrote them that way.

Now read the list as an application would receive it with a limit of six, which is what the notebook intended:

- **The hard constraint is at rank 7.** The answering model would not see the peanut allergy.
- **Both values of the changed fact are at ranks 8 and 9.** The answering model would see neither.
- **The scores are close together.** All nine are between 0.588 and 0.740, and ranks 6 and 7 differ by 0.004. Such a small difference can change with the wording of the question.

The notebook shows this with three other questions. For "what should I cook tonight?", the first three facts are the cuisine, the budget and the dinner plan. The peanut allergy is not among them, although it matters more for cooking than the budget does. In a replay with the same nine facts, the allergy was last of the nine for this question.

{% include diagram.html name="mem0-ranking" alt="Three ranked lists of the same nine stored facts, each with a line after the sixth row. First list, the example's question scored by embedding similarity only: the facts about Lena, Jonas, the dinner plan, the budget, Kreuzberg and Indian food are in the first six; below the line are the peanut allergy at rank 7, the replaced fact at rank 8 and the fact that replaced it at rank 9. Second list, the same question with keyword scores added: the fact that replaced the old one rises to rank 5; the peanut allergy is at rank 8 and the replaced fact at rank 9. Third list, the question 'what should I cook tonight?': the replaced fact is at rank 6, inside the first six; the fact that replaced it is at rank 7; the peanut allergy is last, at rank 9." caption="The same nine facts in three orders: the example's question as the notebook scored it, the same question with the library's keyword score added, and a different question. The line marks a limit of six." %}

**The same search with the keyword score.** I stored the same nine facts again with the optional packages installed and repeated the search. The similarity part of each score was the same as in the notebook, to three decimals. The keyword score changed the order:

- The fact about the new diet moved from rank 9 to rank 5. It shares the word "eat" with the question.
- The peanut allergy moved from rank 7 to rank 8. It shares no word with the question.
- The entity boost was zero for every fact, because the question names no entity.

So with the keyword score and a limit of six, the answering model would see the current value of the changed fact, by the accident of one shared word. It would still not see the hard constraint.

**The answer.** The notebook gave the answering model all nine facts, because all nine came back:

```text
I have booked a table for three at **Chutnify** in Kreuzberg for tonight.

*   **Cuisine:** Indian (known for excellent paneer and gluten-free options).
*   **Dietary Notes:** I have informed the restaurant of the severe peanut
    allergy, the shellfish allergy, and the requirement for gluten-free dishes.
*   **Budget:** Fits within your 40€/person range.
*   **Location:** Walking distance in Kreuzberg.

Please confirm if you would like the specific reservation time.
```

The answer uses the right constraints: the peanut allergy, the two guests' needs, the cuisine, the budget and the location. It does not act on the old value of the changed fact. Two things made this possible, and neither is the search:

- The store is so small that nothing was cut.
- The extraction had written the change into the new fact, so the answering model did not have to choose between two contradictory lines.

As in the other parts of this series, the answer claims a booking that the model cannot make. That belongs to the answering model, not to the memory system.

### What it costs

The notebook logged every call that the library made. The answering call is not in the table, because the notebook makes it, not Mem0. The first two columns add up to the tokens that a model call read:

| Call | System prompt | + User prompt | = Tokens in |
|---|--:|--:|--:|
| `add()` for session 1: embed the session | – | – | (embedding) |
| `add()` for session 1: extract | 8,131 | 161 | 8,292 |
| `add()` for session 1: embed the 5 new facts | – | – | (embedding) |
| `add()` for session 2: embed the session | – | – | (embedding) |
| `add()` for session 2: extract | 8,131 | 434 | 8,565 |
| `add()` for session 2: embed the 4 new facts | – | – | (embedding) |
| `search()`: embed the question | – | – | (embedding) |

The notebook did not measure the output tokens, because the library returns only the text of a reply.

Storing two sessions took two model calls and four embedding calls. The two model calls read 16,857 tokens, and 96% of them were the system prompt, read twice.

The user prompt of the second call is larger than the first (434 tokens against 161) because it also carries the five stored facts and the three earlier messages.

Two properties of this cost follow from the design:

- **The cost of a write does not grow with the store.** An `add()` reads its fixed instructions, the new messages, at most ten related facts and at most ten earlier messages, however many facts are stored.
- **For short sessions, the instructions are most of the cost.** A session has to be about 8,000 tokens long before the conversation is half of what the call reads.

Reading is cheap: one embedding call per question, no model call, and the answering model reads only the returned facts.

For comparison, here is what the other systems in this series read in order to store the same two sessions, from their notebooks:

- **Textual memory** ([part 3][part-3]), which rewrites one profile after each session, also made two model calls. They read 916 tokens.
- **Zep/Graphiti** ([part 5][part-5]) made 36 model calls, which read about 51,000 tokens.
- **Honcho** ([part 7][part-7], a re-implementation) read 4,543 tokens in seven model calls, including its answer.
- **Letta** ([part 6][part-6]) writes inside the agent's own replies, so its write cost cannot be separated from the conversation.

## Where it breaks

The example showed the failures in a small form: two wrong dates, a replaced fact that stays in the store, and a hard constraint outside the first six results. Longer histories show what follows from them.

I ran the same library in the larger experiment of this series, on LongMemEval, a public benchmark of long chat histories in which users state facts and later change them in passing. [Part 8][part-8] describes the experiment. Two things were different from the notebook:

- **The date was passed in.** My wrapper gave the prompt builder each session's own date, so relative dates were resolved correctly. Each stored fact was also shown to the answering model with the date of its session.
- **The optional packages were installed**, so the keyword score and the entity boost were active. Most of the benchmark's questions name their subject (a support group, a sculpture), which is the case that these two scores are made for. I did not run the experiment without them, so I cannot say how much they changed.

With correct dates on both values, the add-only design often worked: when the old and the new value both reached the answering model, the model usually chose the newer one. The wrong answers show four ways in which the design fails.

**Failure 1: both values reach the answer, and the answer combines them.** In May, a user said they had attended three sessions of a support group. In October, they said: "the bereavement support group I attended last year. I remember attending five sessions". The second number corrects the first. Mem0 stored two facts:

> User attended three sessions of a bereavement support group […]
>
> User attended five sessions of a bereavement support group last year […]

Both were retrieved. The answering model read "last year" as a different period and answered: "add the two amounts together: 3 + 5 = 8".

The reply cache of the experiment holds the raw reply of that extraction. In it, the second fact carries a link: `"linked_memory_ids": ["0"]`, the first of the related facts shown to the model. The prompt of this call was not logged, so I cannot confirm that fact 0 was the "three sessions" fact. But the model marked the new fact as related to a stored one, and the library dropped the mark.

Across all the experiment's runs, the cache holds 1,901 extraction replies with 10,072 new facts. The model linked 328 of these facts (3.3%) to a stored fact, in 195 of the replies. None of these links was stored.

**Failure 2: a change mentioned in passing is never extracted.** One call extracts from a whole session, and a change is often one clause in a message about something else. A user had said earlier that they had spent 5–6 hours on a sculpture. In a later session, they wrote: "I've already put in 10-12 hours". The extraction of that session returned five facts, about the sculpture's theme, its materials and tools, and none about the hours. The store kept only "5-6 hours", and the answer repeated it.

The system prompt warns against this failure in five places. On these histories the warning was not enough. A fact that is not extracted cannot be recovered, because the search never reads the original messages.

**Failure 3: dates.** This failure has two forms:

- **Without the conversation's date**, relative dates are resolved against the day of ingestion, as in the example. The stored facts then contain wrong dates, and no error is raised.
- **With the conversation's date**, each fact has the day of its session, and no time. A user gave two follower counts in two sessions on the same day (1,250, then "close to 1300"). Both facts carried the same date, and the answering model could not tell which was later. It answered 1,250.

**Failure 4: a conflict is only looked for among ten neighbours.** This limit is in the paper's design as well as in the release. The update step of the paper compares a new fact with the ten most similar stored facts. The release shows the model the ten stored facts most similar to the whole session. A stored fact that the new session contradicts, but that is not among those ten, is never in front of the model. With a store of thousands of facts and a session about several topics, this is likely.

The complete account of every wrong answer in the experiment is in [docs/findings/mem0.md][findings].

**The same failures in other evaluations.** [HaluMem][halumem] (2025) is a benchmark that scores each step of a memory system separately: what was extracted, what was updated, and what was answered. It evaluated Mem0 as it was in 2025, before the add-only release, among other systems. Two of its results (p. 11) agree with failure 2:

- All systems but one extracted fewer than 60% of the facts that they should have extracted.
- For most systems, more than half of the updates were missed, because a fact that was never extracted cannot be updated.

### How to notice and fix these failures

These failures are visible in the store, not in the answers. After a user changes something, list the stored facts for that user and look for two values of the same attribute. `get_all()` returns every fact, and each fact is a readable sentence.

Four changes address the four failures:

- **For failure 3, pass the conversation's date.** The prompt builder accepts it, and `add()` does not. My wrapper in the experiment calls the builder with each session's date. To order two sessions on one day, the date needs a time as well.
- **For failure 1, retire a replaced fact.** The pieces exist. The model already returns a link from the new fact to the fact it updates or contradicts. Code could store the link and mark the older fact as replaced, or return the two facts together with their order. This is my proposal, and I did not test it. The paper's update step is another way. [Memory-R1][memory-r1] (2025) is a third: it keeps the paper's four operations and trains the model that chooses among them with reinforcement learning. The reward is whether a second model then answers a question correctly from the resulting store.
- **For failure 2, keep the original messages** and search them when the facts do not answer the question. This adds a second search. `add(..., infer=False)` stores the messages without any extraction, which is a way to compare the two.
- **For the hard constraint, do not leave it to the ranking.** A fact that must be in every answer needs a place that the search does not control. [O-Mem][o-mem] (2025) makes this argument: a search by similarity misses user information that matters but is not close to the question. O-Mem keeps a profile of the user's attributes next to the stored interactions and reads from both for every answer.

## When it is the right design

Mem0's read path is cheap and fast, and its store is a list of sentences that a person can read. Both strengths come from extracting short facts and searching them. The costs come from the same two choices: a fact that was not extracted is lost, and a score decides what the answering model sees.

I would use this design when three conditions hold:

- The store will grow beyond what fits in a prompt, so that something has to select.
- Reads must be fast and cheap: one embedding call, and no model call.
- A user must be able to see, correct and delete single facts.

The open-source library does not provide three things that this design then needs:

- **The conversation's own date** at write time.
- **A rule for what is never cut** at read time.
- **A way to retire a replaced fact**, so that the store does not keep both values of every fact that changes.

Without the third, a store about a person whose facts change holds every old value next to the new one. The answering model then has to order them, and it can do that only when each fact has a reliable date.

This design is a poor fit when the whole history still fits in the prompt. A design that puts everything it knows into the prompt cannot miss a fact at read time, and it costs less to write.

## History and related work

**The Mem0 paper.** [Mem0][mem0] (2025) describes the two-step write path shown earlier: extraction from each pair of messages, then an update step in which the model chooses one of four operations. The authors explain the second step as follows (pp. 3–4): "Rather than using a separate classifier, we leverage the LLM's reasoning capabilities to directly select the appropriate operation".

The paper evaluates the system on LoCoMo, a benchmark of ten long conversations between two people, each about 26,000 tokens, with questions about them. A judge model scores the answers. The paper's own results (Table 2, p. 11) show the trade that the design makes:

- Putting the whole conversation into the prompt scored 72.90.
- Mem0 scored 66.88.
- Mem0's slowest answers (the 95th percentile) took 1.44 seconds, against 17.12 seconds for the whole conversation.

So in the authors' own evaluation, Mem0 is less accurate than reading everything, and much faster.

**Mem0ᵍ.** The same paper describes a variant that stores entities and their relations in a graph. When a new relation contradicts a stored one, the stored one is not deleted. The paper says that a model marks such relations "as invalid rather than physically removing them to enable temporal reasoning". This is the idea that the add-only release lacks: a replaced fact that stays, but is marked. On LoCoMo the graph variant scored 68.44, about 1.5 points above Mem0. Version 2.0.0 of the library removed the graph memory and replaced it with the entity boost described earlier.

**From the paper to the release.** Up to version 1.0.11 (April 2026), the open-source library had the paper's update step, with the four operations. Version 2.0.0, released on 16 April 2026, replaced the write path with the one this post describes. The release notes give the reasons: one model call per `add()` in place of two steps, "roughly half the latency", and a model that "spends its capacity on understanding the input instead of diffing against existing memories". Results published for Mem0 before that date are results of a different write path from the one you install today.

**PersonaMem-v3.** [PersonaMem-v3][personamem-v3] (2026) is a benchmark for personal assistants whose users' preferences change. One part of it asks a question after a preference has changed, and a judge checks whether the answer still uses the old preference. The paper (§4.3, p. 18) compares Mem0 with a much simpler design, a single text profile that a model rewrites:

- With the rewritten profile, 25.7% of the answers used the old preference.
- With Mem0, 51.4% did, about twice as many.

The paper's explanation is that "a topically relevant retrieved fact can remain too sticky after expiry". The paper does not say which version of Mem0 it ran. My reading is that this is what an add-only store does: the old preference stays, it is about the same topic as the new one, and a search that finds one finds the other.

## Run it yourself

The [notebook][notebook] for this post runs the real `mem0ai` library, version 2.2.1, with a local Qdrant file as the vector store. It wraps the two model handles that the library uses, the chat model and the embedder, so that every call the library makes is logged and printed. The prompts, replies, stored facts and scores shown in the example come from it. The replays in this post are separate runs with the same prompts and facts, and they are marked as replays.

I used `gemini-3.1-flash-lite` for extraction and for the answer, and `gemini-embedding-001` for the embeddings. Both are available on the free tier of the Gemini API, which is enough for the few calls that the notebook makes. All systems in this series use the same models, so that differences in their results come from their designs.

The notebook runs one short conversation. To see how the design behaves on long histories, read [part 8][part-8]. Its experiment is in the same [repository][repo].

Here are a few experiments worth trying in the notebook:

- Call `search()` with `top_k=6`, give the answering model only those six facts, and read the answer.
- State the change less directly ("grabbed some salmon last night, been doing that a lot lately"). Then check whether the new fact still names the old value.
- Print the raw reply of the second `add()`, and look at `linked_memory_ids`.
- Install the optional packages (`mem0ai[nlp]` and `fastembed`) and call `search()` with `explain=True`, which returns the three parts of each score.
- Add a third session that changes the fact back, and list the store.

## References

<!-- REFS -->

Papers:

- Chhikara et al., [Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory][mem0] (2025)
- Chen et al., [HaluMem: Evaluating Hallucinations in Memory Systems of Agents][halumem] (2025)
- Yan et al., [Memory-R1: Enhancing Large Language Model Agents to Manage and Utilize Memories via Reinforcement Learning][memory-r1] (2025)
- Wang et al., [O-Mem: Omni Memory System for Personalized, Long Horizon, Self-Evolving Agents][o-mem] (2025)
- Jiang et al., [PersonaMem-v3: Toward Omni-Platform Personal Intelligence for Holistic User Understanding, Recommendation, and Agentic Tasks][personamem-v3] (2026)

<!-- /REFS -->

Other sources:

- Mem0, [the open-source library on GitHub][mem0-repo]
- Mem0, [the extraction and update prompts at version 2.2.1][mem0-prompts]
- Mem0, [release notes for version 2.0.0][mem0-release]

[mem0]: https://arxiv.org/abs/2504.19413
[halumem]: https://arxiv.org/abs/2511.03506
[o-mem]: https://arxiv.org/abs/2511.13593
[memory-r1]: https://arxiv.org/abs/2508.19828
[personamem-v3]: https://arxiv.org/abs/2608.21381
[mem0-repo]: https://github.com/mem0ai/mem0
[mem0-prompts]: https://github.com/mem0ai/mem0/blob/v2.2.1/mem0/configs/prompts.py
[mem0-release]: https://github.com/mem0ai/mem0/releases/tag/v2.0.0
[repo]: https://github.com/anton-dergunov/agent-memory-eval
[notebook]: https://anton-dergunov.github.io/agent-memory-eval/notebooks/02-mem0.html
[findings]: https://github.com/anton-dergunov/agent-memory-eval/blob/main/docs/findings/mem0.md
[part-3]: /posts/2199/01/agent-memory-3-textual-memory/
[part-5]: /posts/2199/01/agent-memory-5-graphiti/
[part-6]: /posts/2199/01/agent-memory-6-letta/
[part-7]: /posts/2199/01/agent-memory-7-honcho/
[part-8]: /posts/2199/01/agent-memory-8-experiment/
