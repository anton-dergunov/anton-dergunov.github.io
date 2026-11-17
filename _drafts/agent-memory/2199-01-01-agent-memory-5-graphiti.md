---
title:     "Zep and Graphiti: facts with dates, in a graph"
excerpt:   "How a temporal knowledge graph stores, dates and closes facts, and why its search returned the closed fact instead of the new one."
topic:     llms-and-agents
date:      2199-01-01
permalink: /posts/2199/01/agent-memory-5-graphiti/
share:     true
series:    agent-memory
part:      5
tags:
  - llm
  - agents
  - memory
  - knowledge graphs
---

A language model sees only the text in its current prompt. To use what a user said in earlier sessions, an LLM agent needs a memory system: something that stores information from those sessions and puts it into a later prompt. Some stored facts stay true. Others change, and then the newer value has to win. Sometimes the older value still matters too, for a question such as "where did I live last year?".

This part looks at a knowledge graph with dates, the design in this series that makes the most model calls per message. [Zep][zep] is a hosted memory service, and [Graphiti][graphiti-repo] is the open-source library at its core. After every message, a pipeline of model calls turns what was said into entities (people, places, things) and facts between them. Each fact is an edge between two entities, and it carries the dates between which it was true. When a new fact contradicts a stored one, the stored fact is not deleted or overwritten: it gets an end date. When a new request arrives, a search selects the facts to put into the prompt. This series places each design by two choices: who writes the memory (nobody, a pipeline, the answering agent, or a background process), and whether the read path inserts the whole memory or a search selects part of it. Here a pipeline writes the memory outside the conversation, and a search selects what the answering model reads.

This post first explains how the library works: the four steps it runs for every message, with each prompt in full, the rule that closes a fact, and the search. It then follows one short test conversation through the design, one model call at a time. Finally, it examines how the design fails on longer histories, and when a graph is worth what it costs. Every prompt and reply below comes from [the notebook for this part][notebook], which drives Graphiti's own prompts from short local code, or from a replay of its calls, marked as such. The code is in the [agent-memory-eval repository][repo].

## How Zep and Graphiti work

{% include diagram.html name="graphiti" alt="Zep and Graphiti's architecture, with the running example. Writing: every message goes through four LLM steps (find entities, match them to stored ones, extract facts, compare with stored facts), 38 calls for ten messages. Memory: a graph of entities whose edges are facts with dates; the old value of the changed fact was closed on 20 July 2026 and the new value opened. Reading: a hybrid search with a 0.6 similarity floor returned ten facts, including the closed one; the new value, Jonas's coeliac disease and Kreuzberg fell below the floor, and the peanut allergy came eleventh, so the answer missed the changed fact, the allergy, gluten and the area." caption="Zep / Graphiti, with the conversation used in this post. Every message goes through four LLM steps that turn it into dated facts between entities. At question time a search by words and by meaning selects ten facts." %}

Graphiti has the two components that most memory systems have:

- a **write path**, which runs when the application calls `add_episode()` with a piece of conversation;
- a **read path**, which runs when the application calls `search()` with a question.

The description below is of version 0.31.1 of the `graphiti-core` Python library (October 2026), read from its source. The design in the Zep paper differs from it in a few places, which "History and related work" lists.

### What is stored

The graph holds three kinds of object:

- An **episode** is one piece of input, as the application passed it: here, one message. Episodes are kept as they are, and each entity and fact records which episodes it came from.
- An **entity** is a node: a name, such as "Anton" or "peanut allergy", and a type. Graphiti has one built-in type, `Entity`. An application can add its own types, which the example below does.
- A **fact** is an edge from one entity to another. It has a relation name in capitals (`LIVES_IN`), a sentence, an embedding of the sentence, and four dates.

This is one stored fact from the example, with its four dates:

```text
Anton  --LIVES_IN-->  Kreuzberg
fact        Anton moved to the neighborhood of Kreuzberg in May 2026.
valid_at    2026-05-01      when it became true in the world
invalid_at  (none)          when it stopped being true in the world
created_at  2026-07-20      when the graph learned it
expired_at  (none)          when the graph stopped holding it
```

The first two dates are about the world: the user moved in May. The second two are about the graph: it learned this on 20 July, when the user said it. A system with one date per fact has to choose one of the two.

### The write path: four steps for every message

`add_episode()` takes one episode and runs four steps. Each step is one model call or more:

1. **Find entities** (one model call). The model lists the things the message mentions, each with a type.
2. **Match them to stored entities** (code, then at most one model call). Each name found is either an entity the graph already has, or a new one.
3. **Extract facts** (one model call). The model writes facts between pairs of the entities found, each with dates.
4. **Compare each new fact with stored facts** (code, then one model call per new fact). The model says which stored facts the new one repeats or contradicts. Code then decides what is stored and which facts end, from the dates.

{% include diagram.html name="graphiti-steps" alt="The four steps for one message, traced with the first message of session 2, which changes a fact. Step 1, an LLM call, finds three entities: Anton, the new value of the changed fact, and peanut allergy. Step 2 matches Anton and peanut allergy by exact name, with no call; the third name scores 0.691 against the stored old value, over the 0.6 floor, so an LLM call decides they are different things and a new entity is made. Step 3, an LLM call, extracts two facts with dates. Step 4: for the changed fact, code finds no fact between the same two entities and seven by search; an LLM call says it contradicts the stored old value; code ends the old fact on 20 July. For the allergy, code finds the stored allergy fact between the same two entities; an LLM call says it is a duplicate, so nothing new is stored. Five LLM calls and three embedding calls in all." caption="The four steps for the message that changes a fact. The model makes judgements; plain code decides what is stored and when a fact ends." %}

Here is the same write path as pseudocode. It follows `add_episode` in the library's `graphiti_core/graphiti.py` and the functions it calls, with the database work left out:

```python
def add_episode(message, reference_time, entity_types):
    previous = last_episodes(10, before=reference_time)     # context for every prompt

    # Step 1: find entities
    found = llm(extract_nodes.extract_message, message, previous, entity_types)

    # Step 2: match each name to a stored entity, or make it new
    for entity in found:
        if graph.has_name(entity.name):                      # exact name, any case
            entity.same_as = that_entity
        else:
            entity.candidates = [e for e in graph.entities
                                 if cosine(embed(entity.name), e.name_embedding) >= 0.6][:15]
    unsure = [e for e in found if e.candidates]
    if unsure:
        llm(dedupe_nodes.nodes, unsure, all_candidates)     # one call for all of them

    # Step 3: extract facts between the entities found
    facts = llm(extract_edges.edge, message, previous, found, reference_time)
    for name in names_used_in(facts) - names_of(found):     # a name step 1 did not find
        found.append(match_or_create(name))                  # becomes an entity too

    # Step 4: compare each new fact with the stored ones
    for fact in facts:
        same_pair = search(fact, among=facts_between(fact.source, fact.target))
        related = search(fact, among=graph.facts) - same_pair    # top 10
        if not same_pair and not related:
            graph.add(fact)
            continue
        duplicates, contradicted = llm(dedupe_edges.resolve_edge, fact, same_pair, related)
        kept = duplicates[0] if duplicates else graph.add(fact)
        close(kept, contradicted)                            # the rule shown below
```

Messages must be added one at a time and in order. The library's documentation says so ("It's important that each episode is added sequentially and awaited before adding the next one"), because step 4 compares each fact with what the earlier messages stored.

The real library also writes short summaries of the entities after step 4, with more model calls. In the larger experiment of this series, there was about one such call for every five messages. The notebook leaves summaries out, because they do not change which facts are stored or closed.

#### Step 1: find the entities

The model gets the new message, the ten messages before it, and a list of entity types. This is the prompt, `extract_message` in [`graphiti_core/prompts/extract_nodes.py`][prompt-nodes]. It has six worked examples; I show the first and cut the rest, marked […]. The system instruction is:

```text
You are an entity extraction specialist for conversational messages. NEVER
extract abstract concepts, feelings, or generic words.
```

And the user prompt (line breaks added for readability):

```text
NEVER extract any of the following:
- Pronouns (you, me, I, he, she, they, we, us, it, them, him, her, this, that,
  those)
- Abstract concepts or feelings (joy, balance, growth, resilience, happiness,
  passion, motivation)
- Generic common nouns or bare object words (day, life, people, work, stuff,
  things, food, time, way, tickets, supplies, clothes, keys, gear)
- Generic media/content nouns unless uniquely identified in the node name
  itself (photo, pic, picture, image, video, post, story)
- Generic event/activity nouns unless uniquely identified in the node name
  itself (event, game, meeting, class, workshop, competition)
- Broad institutional nouns unless explicitly named or uniquely qualified
  (government, school, company, team, office)
- Ambiguous bare nouns whose meaning depends on sentence context rather than
  the node name itself
- Sentence fragments or clauses ("what you really care about", "results of
  that effort")
- Adjectives or descriptive phrases ("amazing", "something different", "new
  hair color")
- Duplicate references to the same real-world entity. Extract each entity at
  most once per message, even if it appears multiple times or both as a
  speaker label and in the body text.
- Bare relational or kinship terms (dad, mom, mother, father, sister, brother,
  husband, wife, spouse, son, daughter, uncle, aunt, cousin, grandma, grandpa,
  friend, boss, teacher, neighbor, roommate) and bare animal/pet words (dog,
  cat, pet, puppy, kitten). These are too generic on their own. Instead,
  qualify them with the possessor: extract "Nisha's dad" not "dad", "Jordan's
  dog" not "dog".
- Bare generic objects that cannot be meaningfully qualified with a possessor,
  brand, or distinguishing detail (e.g., NEVER extract "supplies" from "I
  picked up some supplies")

Your task is to extract **entity nodes** that are **explicitly** mentioned in
the CURRENT MESSAGE. Pronoun references such as he/she/they or this/that/those
should be disambiguated to the names of the reference entities. Only extract
distinct entities from the CURRENT MESSAGE.

<ENTITY TYPES>
{entity_types}
</ENTITY TYPES>

<PREVIOUS MESSAGES>
{previous_episodes}
</PREVIOUS MESSAGES>

<CURRENT MESSAGE>
{episode_content}
</CURRENT MESSAGE>

1. **Speaker Extraction**: Always extract the speaker (the part before the
   colon `:` in each dialogue line) as the first entity node.
   - If the speaker is mentioned again in the message, treat both mentions as
     a **single entity**.

2. **Entity Identification**:
   - Extract named entities and specific, concrete things that are
     **explicitly** mentioned in the CURRENT MESSAGE.
   - Only extract entities that are specific enough to be uniquely
     identifiable. Ask: "Could this have its own Wikipedia article or database
     entry, OR is it specific enough to distinguish from other items of the
     same category within this conversation?"
   - For objects, possessions, and physical items, extract when they are
     specific enough to distinguish from other items of the same category.
     SHOULD be extracted:
     - Brand-named items ("Gamecube", "Ford Mustang", "Moen faucet")
     - Qualified items ("wool coat", "red and purple lighting", "cracked
       windshield", "dog leash")
     - Items with a concrete distinguishing descriptor (color, material, size,
       model, owner, specific use)
     Should NOT be extracted:
     - Bare head nouns alone ("car", "coat", "game", "lighting", "windshield")
   - When a speaker or named person refers to a relative, pet, or associate
     using a bare term (e.g., "my dad", "his cat"), extract the entity
     qualified with the possessor's name (e.g., "Nisha's dad", "Jordan's cat").
     Do NOT extract the bare term alone.
   - **Exclude** entities mentioned only in the PREVIOUS MESSAGES (they are for
     context only).

3. **Entity Classification**:
   - Use the descriptions in ENTITY TYPES to classify each extracted entity.
   - Assign the appropriate `entity_type_id` for each one.

4. **Exclusions**:
   - Do NOT extract entities representing relationships or actions.
   - Do NOT extract dates, times, or other temporal information — these will
     be handled separately.
   - When in doubt, do NOT extract.

5. **Specificity**:
   - Always use the **most specific form** mentioned in the message. If the
     message says "road cycling", extract "road cycling" not "cycling". If it
     says "wool coat", extract "wool coat" not "coat".
   - When context makes an object's type clear, include that context in the
     name. For example, if the message mentions forgetting a leash while
     discussing a dog walk, extract "dog leash" not "leash".
   - If a phrase would not be distinguishable when read alone later, do NOT
     extract it.

6. **Formatting**:
   - Be **explicit and unambiguous** in naming entities (e.g., use full names
     when available).

<EXAMPLE>
Message: "Jordan: We just moved to Denver last month. My spouse started a new
role at Lockheed Martin and I enrolled in a ceramics workshop at the Belmont
Arts Center."
Good extractions: "Jordan" (speaker), "Denver" (Location), "Lockheed Martin"
(Organization), "Belmont Arts Center" (Location), "ceramics" (Topic)
Do NOT extract: "spouse" (generic reference — extract only if named), "new
role" (not an entity), "last month" (temporal), "we" (pronoun)
</EXAMPLE>

[…]

{custom_extraction_instructions}
```

The library fills the slots as follows:

- **`entity_types`** is a list of types, each with a number, a name and a description. Without custom types, the list has one entry, the built-in `Entity`, whose description ends "When in doubt, do not extract the entity". With custom types, each one is added with its class's docstring as the description.
- **`previous_episodes`** holds the last ten messages, with their timestamps. The prompt says they are "for context only".
- **`episode_content`** is the message. The library expects a speaker before a colon ("Anton: …"), and rule 1 makes the speaker the first entity.
- **`custom_extraction_instructions`** is empty unless the application passes instructions.

Three rules decide what this step leaves out:

- **The test for an entity, in rule 2** ("Could this have its own Wikipedia article or database entry, OR is it specific enough to distinguish from other items of the same category within this conversation?"). The prompt is written for a knowledge graph of named things.
- **The first item of the list of things never to extract** ("Abstract concepts or feelings"), and the list of generic nouns and activities after it.
- **The last rule of exclusions** ("When in doubt, do NOT extract"), repeated in the description of the built-in type.

This matters more here than in other designs, because a fact is an edge between two entities. The next step that writes facts is shown the entities this step found, and the example below shows what happens to a fact whose second entity was never found.

#### Step 2: match the names to stored entities

The same person or thing is often mentioned again in other words: "my sister", then "my sister Lena", then "Lena". This step decides, for each entity just found, whether the graph already has it. It follows `resolve_extracted_nodes` in `graphiti_core/utils/maintenance/node_operations.py`:

```python
for entity in found:
    if graph.has_exact_name(entity.name):          # lower case, spaces collapsed
        same_as[entity] = that_entity              # no model call
        continue
    candidates = [e for e in graph.entities        # by the name's embedding only
                  if cosine(embed(entity.name), e.name_embedding) >= 0.6]
    candidates = top(candidates, 15)
    if not candidates:
        new_entity(entity)                         # no model call
    elif near_identical_spelling(entity, candidates):   # MinHash, Jaccard >= 0.9
        same_as[entity] = that_candidate
    else:
        ask_model.append(entity)                   # one call for all of these
```

Two thresholds decide which stored entities the model ever sees: a cosine similarity of 0.6 between the names' embeddings (`NODE_DEDUP_COSINE_MIN_SCORE`), and at most 15 candidates. A stored entity that scores 0.599 is never shown to the model. The candidates are found by name only. An entity's summary is shown to the model, cut at 120 characters, but only for candidates that have already passed the floor.

The prompt for the remaining names is `nodes` in [`graphiti_core/prompts/dedupe_nodes.py`][prompt-dedupe-nodes]. The system instruction:

```text
You are an entity deduplication assistant. NEVER fabricate entity names or
mark distinct entities as duplicates.
```

The user prompt, in full. The library fills in the number of entities where this copy shows `{n}` and `{n-1}`:

```text
<PREVIOUS MESSAGES>
{previous_episodes}
</PREVIOUS MESSAGES>

<CURRENT MESSAGE>
{episode_content}
</CURRENT MESSAGE>

<ENTITIES>
{extracted_nodes}
</ENTITIES>

<EXISTING ENTITIES>
{existing_nodes}
</EXISTING ENTITIES>

Each of the above ENTITIES was extracted from the CURRENT MESSAGE.
For each entity, determine if it is a duplicate of any EXISTING ENTITY.
Entities should only be considered duplicates if they refer to the *same
real-world object or concept*.

NEVER mark entities as duplicates if:
- They are related but distinct.
- They have similar names or purposes but refer to separate instances or
  concepts.

Task:
ENTITIES contains {n} entities with IDs 0 through {n-1}.
Your response MUST include EXACTLY {n} resolutions with IDs 0 through {n-1}.
Do not skip or add IDs.

For every entity, provide:
- `id`: integer id from ENTITIES
- `name`: the best full name for the entity (preserve the original name unless
  a duplicate has a more complete name)
- `duplicate_candidate_id`: the `candidate_id` of the EXISTING ENTITY that is
  the best duplicate match, or -1 if there is no duplicate

<EXAMPLE>
ENTITY: "Sam" (Person)
EXISTING ENTITIES: [{"candidate_id": 0, "name": "Sam", "entity_types":
["Person"], "summary": "Sam enjoys hiking and photography"}]
Result: duplicate_candidate_id = 0 (same person referenced in conversation)

ENTITY: "NYC"
EXISTING ENTITIES: [{"candidate_id": 0, "name": "New York City",
"entity_types": ["Location"]}, {"candidate_id": 1, "name": "New York Knicks",
"entity_types": ["Organization"]}]
Result: duplicate_candidate_id = 0 (same location, abbreviated name)

ENTITY: "Java" (programming language)
EXISTING ENTITIES: [{"candidate_id": 0, "name": "Java", "entity_types":
["Location"], "summary": "An island in Indonesia"}]
Result: duplicate_candidate_id = -1 (same name but distinct real-world things)

ENTITY: "Marco's car"
EXISTING ENTITIES: [{"candidate_id": 0, "name": "Marco's vehicle",
"entity_types": ["Entity"], "summary": "Marco drives a red sedan."}]
Result: duplicate_candidate_id = 0 (synonym — "car" and "vehicle" refer to the
same thing, same possessor)
</EXAMPLE>
```

The prompt asks for "the best full name" of each entity. The library does not use it: a matched entity keeps the name it was stored with. The example shows why that matters.

#### Step 3: extract the facts

The model gets the message again, with the entities found, and writes facts between pairs of them. The prompt is `edge` in [`graphiti_core/prompts/extract_edges.py`][prompt-edges]. The system instruction:

```text
You are an expert fact extractor that extracts fact triples from text. 1.
Extracted fact triples should also be extracted with relevant date
information. 2. The CURRENT_MESSAGE may contain multiple episodes, each with
its own timestamp. Use each episode's timestamp to resolve temporal references
within that episode. REFERENCE_TIME is a fallback for when no per-episode
timestamp is available.
```

The user prompt, in full, without the section for custom fact types, which this post does not use:

```text
<PREVIOUS_MESSAGES>
{previous_episodes}
</PREVIOUS_MESSAGES>

<CURRENT_MESSAGE>
{episode_content}
</CURRENT_MESSAGE>

<ENTITIES>
{nodes}
</ENTITIES>

<REFERENCE_TIME>
{reference_time}  # ISO 8601 (UTC); used to resolve relative time mentions
</REFERENCE_TIME>

# TASK
Extract all factual relationships between the given ENTITIES based on the
CURRENT MESSAGE.
Only extract facts that:
- involve two DISTINCT ENTITIES from the ENTITIES list,
- are clearly stated or unambiguously implied in the CURRENT MESSAGE,
    and can be represented as edges in a knowledge graph.
- Facts should include entity names rather than pronouns whenever possible.

You may use information from the PREVIOUS MESSAGES only to disambiguate
references or support continuity.


{custom_extraction_instructions}

# EXTRACTION RULES

1. **Entity Name Validation**: `source_entity_name` and `target_entity_name`
   must use only the `name` values from the ENTITIES list provided above.
   - **CRITICAL**: Using names not in the list will cause the edge to be
     rejected
2. Each fact must involve two **distinct** entities — `source_entity_name`
   and `target_entity_name` NEVER refer to the same entity.
3. Prefer facts that involve two distinct entities from the ENTITIES list.
   When a sentence describes a specific, concrete detail about a single entity
   (a brand name, a specific item, a physical description, a quantity, a
   location, a named activity), do NOT drop it. Instead, look for a second
   entity in the ENTITIES list that the detail relates to and form a proper
   triple (e.g., Entity -> OWNS -> item-entity, Entity -> LIVES_IN ->
   place-entity, Entity -> HAS_ATTRIBUTE -> detail-entity). Only skip the fact
   when no second entity in the ENTITIES list can anchor the detail.
   - BAD: "Alice feels happy" (vague single-entity state with no concrete
     detail — what is Alice happy about?)
   - GOOD: "Alice feels happy about Bob's promotion" → Alice ->
     FEELS_HAPPY_ABOUT -> Bob's promotion
   - GOOD: "Nate plays games on a Gamecube" → Nate -> PLAYS_GAMES_ON ->
     Gamecube (when "Gamecube" is in ENTITIES)
   - GOOD: "Alice congratulated Bob" (relationship between two entities),
     "Alice lives in Paris" (relationship between entity and place)
4. Do not emit semantically redundant facts, even across episodes within the
   CURRENT_MESSAGE. However, if a later episode adds specific details to a
   previously stated fact (e.g., adding a brand name, a count, a color, a
   location, or any concrete attribute), extract the more detailed version as
   a NEW fact — it is NOT a duplicate. Only treat facts as duplicates when
   they convey the same specificity.
   - NOT a duplicate: "user plays video games" (Episode 0) vs. "user plays
     games on a Gamecube" (Episode 1) → extract the second, more detailed
     fact.
   - IS a duplicate: "user plays games on a Gamecube" (Episode 0) vs. "user
     plays Gamecube games" (Episode 1) → extract once, list both episodes in
     `episode_indices`.
5. The `fact` MUST preserve all specific details from the source text: proper
   nouns, brand names, product names, model numbers, quantities, counts,
   colors, materials, physical descriptions, specific items, named locations,
   and named activities. Paraphrase the sentence structure but NEVER
   generalize:
   - NEVER generalize "Gamecube" to "gaming console", "Ford Mustang" to "car",
     "wool coat" to "coat", "red and purple lighting" to "lighting", "cracked
     windshield" to "car damage", or "three screenplays" to "several
     screenplays".
   - Do not verbatim quote the original text, but every concrete noun, number,
     and descriptor in the source should survive into the `fact`.
6. Use `REFERENCE_TIME` to resolve vague or relative temporal expressions
   (e.g., "last week"). When the CURRENT_MESSAGE contains multiple episodes
   with per-episode timestamps, prefer the timestamp of the specific episode
   the fact originates from.
7. Do **not** hallucinate or infer temporal bounds from unrelated events.

# DATETIME RULES

- Use ISO 8601 with "Z" suffix (UTC) (e.g., 2025-04-30T00:00:00Z).
- If the fact is ongoing (present tense), set `valid_at` to the timestamp of
  the episode the fact originates from. If no per-episode timestamp is
  available, use REFERENCE_TIME.
- If the fact is a future-tense plan, promise, scheduled event, or deadline,
  set `valid_at` to the episode timestamp / REFERENCE_TIME. Do NOT set
  `valid_at` to the future occurrence date.
- Preserve future occurrence dates and deadlines in the `fact` text. Do NOT
  use a soft deadline ("by March 2026", "by the end of Q3 2025") as
  `invalid_at`.
- Use a future date as `invalid_at` only when the fact describes an ongoing
  state that ends then (for example, "is unavailable until December 25, 2024"
  or "works at Acme until January 15, 2027").
- If a change/termination is expressed, set `invalid_at` to the relevant
  timestamp.
- Leave both fields `null` if no explicit or resolvable time is stated.
- If only a date is mentioned (no time), assume 00:00:00.
- If only a year is mentioned, use January 1st at 00:00:00.
- Examples with REFERENCE_TIME 2020-01-01T00:00:00Z:
  - "Emma will relocate to Tokyo on December 25, 2022" -> valid_at
    2020-01-01T00:00:00Z, invalid_at null.
  - "Alice will complete the project by July 30, 2024" -> valid_at
    2020-01-01T00:00:00Z, invalid_at null.
  - "The team will ship version 2.0 by the end of Q3 2025" -> valid_at
    2020-01-01T00:00:00Z, invalid_at null.
```

`nodes` is the list of entities found in step 1, each with its type labels. `reference_time` is the time the application passed for the message. Graphiti has no other source for dates: without it, every fact would start on the day the code runs.

Four rules decide what a fact is and when it starts:

- **The first rule, for names** ("Using names not in the list will cause the edge to be rejected"). The code does not do this. Since version 0.31, a name that the model uses and step 1 did not find becomes a new entity, matched against the graph like any other, and the fact is kept (`dangling_endpoints.py`). In the larger experiment of this series, this happened to 52 of 22,795 extracted facts (0.2%).
- **The fifth rule, for details** ("every concrete noun, number, and descriptor in the source should survive into the `fact`"). A fact is a full sentence with names in place of pronouns. It can be read, embedded and searched on its own, without the graph around it.
- **The rule for ongoing facts**, the second of the date rules ("If the fact is ongoing (present tense), set `valid_at` to the timestamp of the episode"). A fact stated in the present tense starts on the day it was said, unless the message gives another date.
- **The rule for plans**, the third of the date rules. A plan starts on the day it was said, not on the day it will happen. The code enforces it again after the model replies: when the sentence matches words such as "will", "plans to" or "scheduled to", a start date later than the message is moved back to the message.

A fact that comes back with no dates at all gets one more small model call (`extract_timestamps`), which asks only for the two dates.

#### Step 4: compare each new fact with the stored facts

For each new fact, code collects two lists from the stored facts:

- **Facts between the same two entities**, in either direction. These are the candidates for a duplicate.
- **The ten facts closest to the new one** by a search over the whole graph, the same search the read path uses (below). These are the candidates for a contradiction.

When both lists are empty, the fact is added without a model call. When a stored fact between the same two entities has exactly the same sentence, the new fact is taken as a repeat, also without a call. Otherwise the model gets both lists. The prompt is `resolve_edge` in [`graphiti_core/prompts/dedupe_edges.py`][prompt-dedupe-edges]. The system instruction:

```text
You are a fact deduplication assistant. NEVER mark facts as contradicted
unless the new fact explicitly makes the old fact false.
```

The user prompt, in full:

```text
NEVER mark facts as duplicates if they have key differences, particularly
around numeric values, dates, or key qualifiers.

Only mark a fact as contradicted when the NEW FACT and the existing fact
cannot both be true.
Do NOT treat additional activity, progress, status, or project-update facts as
contradictions of role, ownership, responsibility, membership, or assignment
facts. A person doing work on a project is compatible with that person
remaining responsible for, owning, leading, or being the DRI for the project.

IMPORTANT constraints:
- duplicate_facts: ONLY idx values from EXISTING FACTS (NEVER include FACT
  INVALIDATION CANDIDATES)
- contradicted_facts: idx values from EITHER list (EXISTING FACTS or FACT
  INVALIDATION CANDIDATES)
- The idx values are continuous across both lists (INVALIDATION CANDIDATES
  start where EXISTING FACTS end)

<EXISTING FACTS>
{existing_edges}
</EXISTING FACTS>

<FACT INVALIDATION CANDIDATES>
{edge_invalidation_candidates}
</FACT INVALIDATION CANDIDATES>

<NEW FACT>
{new_edge}
</NEW FACT>

You will receive TWO lists of facts with CONTINUOUS idx numbering across both
lists.
EXISTING FACTS are indexed first, followed by FACT INVALIDATION CANDIDATES.

1. DUPLICATE DETECTION:
   - If the NEW FACT represents identical factual information as any fact in
     EXISTING FACTS, return those idx values in duplicate_facts.
   - If no duplicates, return an empty list for duplicate_facts.

2. CONTRADICTION DETECTION:
   - Determine which facts the NEW FACT directly contradicts from either list.
   - A contradiction requires explicit evidence that the old fact stopped
     being true or was replaced,
     such as clear termination, replacement, transfer, or mutually exclusive
     current-state language.
   - Do NOT infer contradiction from recency alone, episode dates, meeting
     dates, weekly snapshots,
     section headings such as "updates" or "status changes", or a new event
     involving the same entities.
   - Do NOT mark a role/ownership/responsibility/assignment fact as
     contradicted merely because the
     NEW FACT describes work performed, updates shipped, documents created,
     progress made, blockers,
     next steps, or collaboration involving the same person and project.
   - A fact from EXISTING FACTS can be both a duplicate AND contradicted only
     when the same assertion is restated with an explicit incompatible change.
   - Return all contradicted idx values in contradicted_facts.
   - If no contradictions, return an empty list for contradicted_facts.

<EXAMPLE>
EXISTING FACT: idx=0, "Alice joined Acme Corp in 2020"
NEW FACT: "Alice joined Acme Corp in 2020"
Result: duplicate_facts=[0], contradicted_facts=[] (identical factual
information)

EXISTING FACT: idx=1, "Alice works at Acme Corp as a software engineer"
NEW FACT: "Alice works at Acme Corp as a senior engineer"
Result: duplicate_facts=[], contradicted_facts=[1] (same relationship but
updated title — contradiction, NOT a duplicate)

EXISTING FACT: idx=2, "Bob ran 5 miles on Tuesday"
NEW FACT: "Bob ran 3 miles on Wednesday"
Result: duplicate_facts=[], contradicted_facts=[] (different events on
different days — neither duplicate nor contradiction)
</EXAMPLE>
```

The model returns two lists of numbers: the duplicates and the contradicted facts. Two rules of this prompt set how often a fact is closed:

- **The system instruction** ("NEVER mark facts as contradicted unless the new fact explicitly makes the old fact false").
- **The second point of contradiction detection** ("A contradiction requires explicit evidence that the old fact stopped being true or was replaced"), and the point after it: "Do NOT infer contradiction from recency alone".

These rules are new in version 0.31.0 (October 2026). The release brought "extraction, dedup, and temporal fixes" from Zep's internal fork into the open-source library, and its description says: "The edge contradiction rules in `dedupe_edges` are stricter" ([pull request 1964][graphiti-pr]). The earlier prompt had none of these rules; it asked to "Determine which facts the NEW FACT contradicts from either list". A strict rule closes fewer facts that are still true, and leaves more facts open that are no longer true. The vendor moved this setting between two releases.

**The closing rule.** The model only says *that* a fact is contradicted. Code decides *which* fact ends and *when*, from the dates. This is the rule, after `_apply_temporal_invalidation` and `resolve_edge_contradictions` in `graphiti_core/utils/maintenance/edge_operations.py`:

```python
def close(new, contradicted, now):
    if new.invalid_at and not new.expired_at:
        new.expired_at = now                 # the new fact arrived already ended
    if not new.expired_at:
        for old in sorted(contradicted, key=valid_at):
            if old.valid_at > new.valid_at:  # a fact that starts later wins:
                new.invalid_at = old.valid_at        # the NEW fact is closed
                new.expired_at = now
                break
    for old in contradicted:
        if old.invalid_at and old.invalid_at <= new.valid_at:
            continue                         # the old fact had already ended
        if new.invalid_at and new.invalid_at <= old.valid_at:
            continue                         # the new fact ended before the old began
        if old.valid_at < new.valid_at:
            old.invalid_at = new.valid_at    # the old fact ends where the new starts
            old.expired_at = old.expired_at or now
```

The rule needs both facts to have a start date. When either is missing, none of the conditions holds, and nothing is closed although the model said "contradicted". And the rule orders facts by when they became true, not by when they were said. A fact said later can be closed by one said earlier, if the earlier one starts later. "Where it breaks" shows this happening.

### Time: two timelines on every fact

Each fact carries four dates, in two pairs:

| Date | What it answers | Who sets it |
|---|---|---|
| `valid_at` | When did this become true in the world? | the model, in step 3 |
| `invalid_at` | When did it stop being true? | the model, if the message says so; otherwise code, when a newer fact contradicts it |
| `created_at` | When did the graph learn it? | code, when the message is stored |
| `expired_at` | When did the graph stop holding it? | code, when the fact is closed |

Nothing is deleted. A closed fact stays in the graph with its end date, so "what was true on 15 April?" is a filter on the dates, not a reconstruction. And a fact said in July about May can be placed in May.

### The read path: a search selects ten facts

`graphiti.search(question)` makes one embedding call and no model call. It follows the search recipe `EDGE_HYBRID_SEARCH_RRF` in `graphiti_core/search/`:

1. **Search by words.** A full-text search over the fact sentences, in the graph database, returns up to 20 facts.
2. **Search by meaning.** The question is embedded, and the facts whose sentence embeddings have a cosine similarity of at least 0.6 to it (`DEFAULT_MIN_SCORE`) are ranked; up to 20 are kept.
3. **Merge the two rankings** by reciprocal rank fusion: a fact scores 1 / its position in each list it appears in, and the scores are added.
4. **Cut** at ten facts.

The default search does not filter by date. A closed fact is ranked like any other. Filters by date exist (`SearchFilters`), and the application has to ask for them.

The library also has a walk along the graph: a breadth-first search that follows edges outward from chosen entities, up to three steps. It is part of other search recipes, and the application chooses where it starts. `graphiti.search()` does not use it.

`search()` returns the facts. The application decides how to put them into a prompt. The notebook uses the wording of Graphiti's own helper (`search_results_to_context_string`), which lists each fact with its two world dates:

```text
These are the most relevant facts and their valid and invalid dates. Facts are
considered valid between their valid_at and invalid_at dates. Facts with an
invalid_at date of "Present" are considered valid.
<FACTS>
[
 {"fact": "…", "valid_at": "…", "invalid_at": "Present"},
 […]
]
</FACTS>
```

The answering call puts this list into a short prompt, with this system instruction:

```text
You are a booking assistant for Anton. Today is 01 September 2026. Be brief
and concrete.
```

```text
What you remember about this user:
{facts}

Their request: {question}
```

The system instruction is written for the test conversation in this post, where the user asks the assistant to book a dinner.

### What it does not do

- **It does not rewrite what is stored.** Unlike a profile that a model rewrites after each session, a stored fact keeps its sentence. Only its end dates change.
- **It does not delete.** A contradicted fact is closed, not removed.
- **It does not batch.** Every message goes through all four steps, in order, whatever it says.
- **It does not read the messages at question time.** The episodes are kept, but the default search returns facts only.

### The price of each choice

Each design choice has a cost:

- **Every message costs several model calls, each with a long fixed prompt.** Steps 1 and 3 run for every message, step 2 for most, and step 4 once for every new fact. The prompt of step 1 alone is about 2,400 tokens. In the example below, storing ten short messages took 38 model calls and about 60,000 tokens read. That is more model calls than any other design in this series, by a wide margin. In tokens the margin is smaller: Honcho read about 45,000 tokens for the same two sessions, in 18 longer calls.
- **Messages must be added one at a time, in order.** Writing cannot be batched, and an assistant's long answers go through the same four steps as the user's messages.
- **What step 1 does not name is not stored.** The entity prompt is written for named things. A fact needs two entities, and step 3 is shown only the ones step 1 found.
- **Two fixed thresholds decide what is matched and what is returned.** Both are a cosine similarity of 0.6, and both depend on the embedding model in use.
- **The dates come from the model.** The closing rule is exact, but it is only as good as the start dates the model wrote in step 3.

## The example, step by step

To show how the design works, this post follows one short test conversation through the library, one call at a time. The same conversation is used for every system in this series. It is deliberately small, so that the notebook can print every call and you can read each one.

The conversation has three sessions. Sessions 1 and 2 establish the facts. Session 3 starts without the earlier transcripts and asks one question. The question names none of the facts that a correct answer needs:

- **A fact that changes:** the user's diet changes from vegetarian to pescatarian.
- **A hard constraint:** a severe peanut allergy.
- **Facts about people that the question does not name:** Lena cannot eat shellfish, and Jonas is coeliac (no gluten).
- **Other facts:** the user likes Indian food and lives in Kreuzberg.

{% include diagram.html name="conversation" alt="The running example. On 14 March the user states a fact that will change, a severe peanut allergy, and a liking for Indian food. Four months later, on 20 July, they change that fact, say they have moved to Kreuzberg, and that their sister Lena (who can't eat shellfish) is coming with her partner Jonas (coeliac). Six weeks after that, in a new conversation, they ask for dinner for 'my sister and her partner'. A correct answer needs six things: the new value and not the old one (a fact that changes), no peanuts (a hard constraint), no shellfish and no gluten (people the question does not name, reached through two links), Indian food and somewhere near Kreuzberg." caption="The conversation, and the six things a correct answer needs, grouped by what they test." %}

Two parts of this test press hardest on Graphiti's design:

- **The fact that changes** tests the closing rule: the old value should end and stay as history.
- **Jonas's coeliac disease** tests what the graph adds. The question says "my sister and her partner". Getting from there to "Jonas is coeliac" takes two links, sister to Jonas and Jonas to coeliac, and the fact shares no word with the question.

The notebook passes each message to the four steps as one episode, with the speaker's name before it ("Anton: …") and its time: 19:00 on the day of its session, one minute apart within a session. It uses Graphiti's prompts and thresholds, with the control flow written out in plain Python and the graph kept in Python objects ("Run it yourself" says what is left out).

In the sessions below, colours mark what happened to each phrase: <mark class="hl hl-facts">it became part of a stored fact</mark>, or <mark class="hl hl-prefs">it gave a time that the stored fact did not keep</mark>. Unmarked phrases were not stored.

### Session 1: the built-in type stores nothing about the user

**14 March 2026**

> **User:** I'm <mark class="hl hl-facts">planning a dinner for my sister's visit to Berlin next week</mark>. Worth saying up front: I've been <mark class="hl hl-facts">strictly vegetarian</mark> <mark class="hl hl-prefs">for eight years</mark>, and I have a <mark class="hl hl-facts">severe peanut allergy — anaphylactic</mark>, not a preference.
>
> **Assistant:** Understood — no meat, and peanuts are a hard exclusion. Any cuisine you lean towards?
>
> **User:** <mark class="hl hl-facts">Indian, usually. Paneer dishes especially.</mark> And I'd <mark class="hl hl-facts">rather not spend more than about 40 euros a head</mark>.

**With the built-in type.** Step 1 for the first message, with the prompt shown earlier and only the built-in `Entity` type, returned three entities:

```text
Anton            Entity
Anton's sister   Entity
Berlin           Entity
```

The speaker, the sister and the city. The fact that will change and the allergy are not there. The model followed the prompt: they are not things that could have "their own Wikipedia article or database entry", and "When in doubt, do NOT extract".

The notebook then ran steps 2 and 3 on these three entities, in a separate graph. Step 3 returned two facts:

```text
Anton           --PLANS_DINNER_FOR-->  Anton's sister
                Anton is planning a dinner for his sister's visit to Berlin next week.
Anton's sister  --VISITS-->            Berlin
                Anton's sister is visiting Berlin next week.
```

The model kept to the names it was given and named no new entity, so the code had nothing to add. With the built-in type, nothing about the changed fact or the allergy reaches the graph. This is not chance: a replay of the same step 3 call, three times, returned the same two facts each time.

**With custom entity types.** Graphiti's answer is custom entity types. The application describes the kinds of entity it cares about, as classes with a docstring, and passes them to `add_episode(entity_types=...)`. The descriptions go into the `entity_types` slot of the same prompt. The notebook defines four:

```python
class Person(BaseModel):
    """A specific person: the speaker, or someone they name or describe by their relation to a named person."""

class Place(BaseModel):
    """A named city, district, venue or address."""

class Preference(BaseModel):
    """Something a person likes, dislikes, chooses or avoids: a diet they follow, a cuisine or dish they favour, a budget they keep to."""

class HealthCondition(BaseModel):
    """An allergy, intolerance or medical condition that limits what a person can eat or do."""
```

With the same message, the same model and the same prompt apart from this list, step 1 returned five entities:

```text
Anton            Person
Anton's sister   Person
Berlin           Place
vegetarian       Preference
peanut allergy   HealthCondition
```

The rest of the run uses these four types. Without them, there would be nothing for session 2 to contradict.

**Steps 2 to 4.** The graph was empty, so step 2 made all five entities new, with no model call, and step 4 added every fact without one. Step 3 returned four facts:

| From | Relation | To | Fact | valid_at |
|---|---|---|---|---|
| Anton | PLANS_TO_VISIT | Anton's sister | Anton is planning a dinner for his sister's visit to Berlin next week. | 2026-03-14 |
| Anton | PLANS_TO_VISIT | Berlin | Anton is planning a dinner for his sister's visit to Berlin next week. | 2026-03-14 |
| Anton | HAS_DIETARY_PREFERENCE | vegetarian | Anton has been strictly vegetarian for eight years. | 2026-03-14 |
| Anton | HAS_HEALTH_CONDITION | peanut allergy | Anton has a severe anaphylactic peanut allergy. | 2026-03-14 |

Two things in this reply matter later:

- **One sentence was stored twice**, on two edges: to Anton's sister and to Berlin. Nothing merges them, because they join different pairs of entities.
- **Every fact starts on the day it was said.** "Strictly vegetarian for eight years" started on 14 March 2026, not around 2018. This follows the rule for ongoing facts ("set `valid_at` to the timestamp of the episode"). An earlier run of this notebook, on version 0.30 of the library, whose rule for ongoing facts was the same, dated the same fact 2018-03-14. Which one the model chooses is a judgement, and it can go either way.

**The rest of the session.** The assistant's message went through all four steps too: three model calls, which found one entity, *Assistant*, and no fact. The third message added three facts, about Indian cuisine, paneer dishes and the budget, each compared with the stored facts in step 4 and found to be new. After session 1, the graph holds seven facts, and every one starts at Anton.

### Session 2: the old value closes, and a second node for Lena

**20 July 2026, four months later**

> **User:** Small update on the food thing — I <mark class="hl hl-facts">started eating fish</mark> <mark class="hl hl-prefs">about a month ago</mark>. So <mark class="hl hl-facts">I'm pescatarian now, not vegetarian</mark>. Still no meat, and the peanut situation obviously hasn't changed.
>
> **Assistant:** <mark class="hl hl-facts">Noted, fish is in.</mark> Anything else shifted?
>
> **User:** <mark class="hl hl-facts">I moved to Kreuzberg in May</mark>, so anything walkable from there is a plus.
>
> **Assistant:** Kreuzberg, noted. Anything else for next time?
>
> **User:** Yes — <mark class="hl hl-facts">my sister Lena is coming back in the autumn, and she's bringing her partner, Jonas.</mark>
>
> **Assistant:** Lovely. Anything I should know about what they eat?
>
> **User:** <mark class="hl hl-facts">Lena can't eat shellfish, and Jonas is coeliac.</mark>

**The first message: the changed fact.** The figure at the start of "The write path" shows this message's four steps. In short:

- **Step 1** found Anton, *pescatarian diet* and *peanut allergy*.
- **Step 2** matched Anton and peanut allergy by exact name. *Pescatarian diet* scored 0.691 against the stored *vegetarian*, over the floor, so the model was asked, and it answered that they are different things. The new value became a new entity.
- **Step 3** returned two facts: "Anton started following a pescatarian diet about a month ago, replacing his previous vegetarian diet.", dated 2026-07-20, and "Anton has a severe, anaphylactic peanut allergy.", dated 2026-03-14 from the earlier message in its context.
- **Step 4** handled the two facts differently.

For the new value, nothing was stored between *Anton* and *pescatarian diet*, so the list of duplicates was empty, and the search returned all seven stored facts as candidates. This is the comparison prompt's middle part as the model received it:

```text
<EXISTING FACTS>
[]
</EXISTING FACTS>

<FACT INVALIDATION CANDIDATES>
[{'idx': 0, 'fact': 'Anton has been strictly vegetarian for eight years.'},
{'idx': 1, 'fact': 'Anton prefers Indian cuisine for his dinner plans.'},
{'idx': 2, 'fact': 'Anton has a budget of 40 euros a head for his dinner
plans.'}, {'idx': 3, 'fact': 'Anton specifically enjoys paneer dishes within
Indian cuisine.'}, {'idx': 4, 'fact': "Anton is planning a dinner for his
sister's visit to Berlin next week."}, {'idx': 5, 'fact': 'Anton has a severe
anaphylactic peanut allergy.'}, {'idx': 6, 'fact': "Anton is planning a dinner
for his sister's visit to Berlin next week."}]
</FACT INVALIDATION CANDIDATES>

<NEW FACT>
Anton started following a pescatarian diet about a month ago, replacing his
previous vegetarian diet.
</NEW FACT>
```

The reply:

```text
{'duplicate_facts': [], 'contradicted_facts': [0]}
```

The prompt asks for "explicit evidence that the old fact stopped being true or was replaced", and the new sentence carries it: "replacing his previous vegetarian diet". Step 3 had written that clause into the fact. The closing rule then did the rest. The old fact started on 14 March and the new one on 20 July, so the old fact now ends on 20 July.

{% include diagram.html name="graphiti-dates" alt="Three stored facts on a timeline from March to September 2026, each with two bars: when it was true in the world and when the graph held it. The old value of the changed fact is true from 14 March, the day it was said, until 20 July, and held over the same days. The new value is true from 20 July and held from 20 July; the user meant about 20 June, but the model dated it by the message. When it arrived, code ended the old fact where the new one starts. 'Moved to Kreuzberg in May' is true from 1 May but held only from 20 July. A line at 15 April crosses only the old value; a line at 1 September crosses the new value and Kreuzberg. A table says who sets each of the four dates." caption="The four dates of three facts after session 2. The old value ends where the new one starts, and a question about a day becomes a filter on the dates." %}

The dates are only as good as the model's reading of the message. The user said "about a month ago", which would be about 20 June. The model followed the rule for ongoing facts and dated the new fact by the message, so the old fact's end date is a month late. An earlier run on version 0.30 dated the same fact 2026-06-20.

For the repeated allergy, a stored fact joined the same two entities, so it was offered as a possible duplicate. The model agreed, and nothing new was stored. The stored fact kept its dates. This is the first place where the graph does work that a list of sentences could not: the lookup for duplicates is by a pair of entities, not by similar wording.

The stricter contradiction prompt of version 0.31 did not change this outcome. A replay sent the comparison from the earlier run on 0.30, whose new fact said only "Anton started following a pescatarian diet about a month ago", with the 0.31.1 prompt, three times. Each reply marked the old fact as contradicted.

**The rest of the session.** The other six messages went through the same four steps:

| Message | Entities found | Matched to a stored entity | Facts added | Facts closed |
|---|---|---|--:|--:|
| s2.2, assistant | Assistant, fish | fish → pescatarian diet | 1 | 0 |
| s2.3 | Anton, Kreuzberg | — | 1 | 0 |
| s2.4, assistant | Assistant, Kreuzberg | — | 0 | 0 |
| s2.5 | Anton, Anton's sister Lena, Lena's partner Jonas | Anton's sister Lena → Anton's sister | 2 | 0 |
| s2.6, assistant | Assistant | — | 0 | 0 |
| s2.7 | Anton, Lena, shellfish, Jonas, coeliac | Jonas → Lena's partner Jonas | 2 | 0 |

Going down the table:

- **s2.2.** The assistant's "Noted, fish is in" was stored as a fact: "The Assistant acknowledges that fish is now included in the dietary preferences.". Its entity *fish* was matched to *pescatarian diet*, which is a stretch. In step 4 the model marked the old value as contradicted by this fact as well, and the closing rule skipped it, because that fact had already ended (its first check).
- **s2.3.** "In May" became `valid_at` 2026-05-01. This fact shows the two timelines apart: true from 1 May, known from 20 July.
- **s2.5.** "My sister Lena" was matched to *Anton's sister* from March, and Jonas was added, with a fact from her to him. The model was asked for "the best full name" and answered "Lena", but the node keeps the name *Anton's sister*.
- **s2.7.** *Jonas* was matched to *Lena's partner Jonas*. *Lena* was not matched to anything. There are now two nodes for the same person, and "Lena cannot eat shellfish" hangs off the second one.

{% include diagram.html name="graphiti-matching" alt="How a name in a new message is matched to a stored entity. Only stored entities whose name scores at least 0.6 against the new name are shown to the model. Left, 'Anton's sister Lena' in message 5: Anton's sister scores 0.882 and Anton 0.756, both are shown, and the model picks Anton's sister. Right, plain 'Lena' in message 7: Lena's partner Jonas 0.7867 and Anton 0.6081 are shown; Assistant 0.5997 and Anton's sister 0.5949 fall just under the floor. The model rightly says Lena is neither of the two it was shown, so a second node for Lena is made." caption="Why there are two nodes for Lena. “Anton's sister” scored 0.595 against “Lena”, just under the floor, so the model was never asked about it." %}

The figure shows why. A first name alone carries little meaning for an embedding: "Lena" is about as close to "Berlin" (0.594) as to "Anton's sister" (0.595). The model was shown the two stored entities over the floor, *Lena's partner Jonas* and *Anton*, and rightly said that Lena is neither. The library would make the same second node. Its candidates are found by name only, and the matched node kept the name *Anton's sister*. A replay of the embedding shows that the name the model suggested would have matched: "Lena" scores 0.779 against "Anton's sister Lena".

**The graph after two sessions.** Fourteen facts, one of them closed:

{% include diagram.html name="graphiti-graph" alt="The graph after session 1 and after session 2, with every entity in the same place. Entities are coloured by type: person, place, preference, health condition. After session 1, seven facts all start at Anton: the dinner plan stored twice, to Anton's sister and to Berlin; the old value of the changed fact; the peanut allergy; Indian cuisine; paneer dishes; the budget. The assistant is an entity with no facts. After session 2, the old value's fact is dashed, closed on 20 July, and the new value's fact starts at Anton; the assistant has a fact pointing at the new value. Anton lives in Kreuzberg and has a sister named Lena, a second fact to Anton's sister. From Anton's sister a fact leads to Lena's partner Jonas, and from Jonas to coeliac. A second node called Lena, connected to nothing else, holds the shellfish fact." caption="The stored graph after each session. Each entity is drawn in the same place in both, so what session 2 added stands out: the closed fact (dashed), the chain from Anton's sister to Jonas to coeliac, and a second, unconnected node for Lena." %}

Because every fact has a start and an end, "what was true on a given day?" is a filter. On 15 April, the graph's facts about the diet give one row, "Anton has been strictly vegetarian for eight years."; on 1 September, one row, the new value. A store that overwrites the old value cannot answer the first question, and a store that only adds cannot tell which value is current.

### Session 3: what the search returned

**1 September 2026, a new session with no transcript of the earlier ones**

> **User:** My sister and her partner are in town tonight. Book the three of us somewhere for dinner — you know what we can and can't eat.

The read path ran the default search over the fourteen facts. The figure shows every fact, scored against the question, and what came back:

{% include diagram.html name="graphiti-floor" alt="The fourteen stored facts, sorted by the cosine similarity of their sentence to the question, between 0.54 and 0.74, with a dashed line at the 0.6 floor. The search returned ten: the dinner plan, stored twice (0.739), Indian cuisine (0.665), the budget (0.658), the assistant's note that fish is in (0.658), the sister named Lena (0.653), Lena cannot eat shellfish (0.636), the closed old value of the changed fact (0.608, tenth), paneer dishes (0.608), and Lena and Jonas as a couple (0.599, under the floor but returned for words it shares with the question). Not returned: the peanut allergy (0.602, over the floor but eleventh), Jonas's coeliac disease (0.596), the new value of the changed fact (0.592) and the move to Kreuzberg (0.542)." caption="Every stored fact scored against the question. The floor decides at the third decimal, a shared word gets a fact in anyway, and the limit of ten decides the rest. Of the four facts the answer needs, one was returned." %}

With this embedding model, every fact scores between 0.54 and 0.74 against the question, relevant or not, and eleven of the fourteen lie between 0.59 and 0.67. The floor of 0.6 cuts through the middle of that band:

- **The closed old value was returned** (0.608), in tenth place.
- **The new value that replaced it was not** (0.592, and no word in common with the question).
- **The peanut allergy was not returned.** It passed the floor (0.602) but came eleventh, one place after the closed fact. One of the ten places also went to the dinner sentence stored a second time.
- **Jonas's coeliac disease** (0.596) and **Kreuzberg** (0.542) were not returned; neither shares a word with the question.
- **A shared word gets a fact in anyway.** "Lena is in a relationship with Jonas, who will accompany her on her visit in the autumn." scored 0.599, under the floor, and came second, for the words it shares with the question.

So the write path stored the change correctly, and the read path delivered the old value without the new one, and without the hard constraint.

How close this is shows in the other runs. In the earlier run on version 0.30, the new value was stored as "Anton started following a pescatarian diet about a month ago." and scored 0.599, also just under the floor. In a trial run on 0.31.1, it was worded "Anton adopted a pescatarian diet approximately one month prior to 2026-07-20." and scored 0.616, and it was returned. What reaches the answer depends on how the model happened to word a sentence months earlier.

**The answer.** The ten facts went into the answering prompt shown earlier, each with its dates. The answer:

```text
I will book a table for three for tonight. Based on your preferences:

*   **Cuisine:** Indian (with paneer options).
*   **Dietary restrictions:** No shellfish; fish is acceptable.
*   **Budget:** €40 per head.

I am looking for a suitable restaurant now. Would you like me to aim for a
specific time?
```

The answer looks complete, and it is not:

- It has the cuisine, the budget and Lena's shellfish.
- **It has no peanut allergy**, the one constraint in this conversation that is dangerous.
- **It has no gluten**, so Jonas would be booked into a restaurant with no thought for coeliac disease.
- Its "fish is acceptable" did not come from the new value, which was not returned. It came from the stored note of the assistant's "Noted, fish is in".
- It has no area.

A filter to the facts still true on 1 September changes one thing: the closed fact drops out, and the tenth place goes to the peanut allergy.

### What the graph adds: a walk from the question's entities

So far the search has read the facts as a list of sentences, and nothing has needed a graph. Facts with dates could sit in a table. The graph adds something when a question names one thing and the answer is a fact about another thing linked to it, worded in a way that has nothing in common with the question.

"My sister and her partner" to "Jonas has coeliac disease" is that case. The notebook compares three ways of reading the same facts, all limited to the facts still true on 1 September:

1. **Text search**, as `graphiti.search()` does it.
2. **Text search, then a walk.** Take the entities that the text hits start from, follow edges outward for up to three steps, and merge the facts found on the way into the ranking. Graphiti's search recipes that include `bfs` (breadth-first search) do this.
3. **A walk from the entities the question names.** Find the stored entities whose names share a word with the question, here *Anton's sister* ("sister") and *Lena's partner Jonas* ("partner"), and follow edges from them for two steps. In Graphiti this is a search with `bfs_origin_node_uuids` set, which the application has to choose.

{% include diagram.html name="graphiti-walk" alt="The graph of facts still true in September, with the walk drawn on it. The two entities whose names share a word with the question, Anton's sister and Lena's partner Jonas, are ringed. Following edges from them reaches 'Lena is in a relationship with Jonas' and then 'Jonas has coeliac disease', drawn thick. The node Lena, which holds the shellfish fact, is connected to nothing, so no walk reaches it. A table compares three ways of reading for the four needed facts. Text search: the peanut allergy 10th, Lena's shellfish 4th, the new value of the changed fact and Jonas's coeliac disease not returned. Text search then a walk: the allergy 8th, shellfish 5th, the new value and coeliac not returned. A walk from the question's entities: only coeliac, 2nd." caption="A walk from the entities the question names reaches Jonas's coeliac disease in two steps. No reading returns all four facts the answer needs." %}

Take the four needed facts one at a time:

- **Jonas has coeliac disease.** Text search cannot find it. The second reading reaches it, three steps out from Anton, but merges it in behind the nearer facts, and it falls outside the ten. The third reading finds it in two steps: sister → Jonas → coeliac. That path exists only because step 2 matched "my sister Lena" and "Jonas" to entities that were already there.
- **Lena cannot eat shellfish.** Found by text search, through the word "eat". No walk can find it: it hangs on the second node for Lena, which is connected to nothing.
- **The new value of the changed fact.** Missed by all three. It is one step from Anton, but so are eight other facts still true, and it is ranked behind them.
- **The peanut allergy.** Found by text search, tenth of ten.

**A tuned read.** The notebook then answered once more, from a read tuned by hand: current facts only, a floor of 0.55 for the search by meaning, and the walk from the question's entities merged in, cut at ten. The answer:

```text
I will book an Indian restaurant for three people tonight. I will ensure the
menu includes paneer dishes and options that are shellfish-free and
gluten-free (for Jonas's coeliac disease). I will keep the budget at 40 euros
per person.

Shall I proceed with a reservation for 20:00?
```

The walk brought in Jonas's coeliac disease (fifth). But the lower floor let more facts through, the walk added two more, and the peanut allergy and the new value were pushed down to eleventh and twelfth, just outside the limit of ten. Each change to the read path moved some facts in and others out.

### What it costs

The notebook logged every model call. By step, for the ten messages of the two sessions:

| Step | Calls | Tokens in | Tokens out |
|---|--:|--:|--:|
| 1. Find entities | 10 | 24,118 | 1,273 |
| 2. Match entities | 7 | 7,194 | 487 |
| 3. Extract facts | 10 | 19,166 | 1,776 |
| 4. Compare with stored facts | 11 | 9,896 | 234 |
| **Total** | **38** | **60,374** | **3,770** |

There were also 25 embedding calls: one per message, for the names of its entities, and one for each of the 15 facts that step 3 extracted. Answering is one more embedding call for the question and one model call.

Three things drive the count:

- **Steps 1 and 3 run for every message.** The entity prompt is about 2,400 tokens each time, most of it the rules and examples shown earlier, and it grows with the ten earlier messages it carries.
- **Step 4 is one call per new fact**, so the count grows with how much a message says, not with how many messages there are.
- **The assistant's messages are not free.** Four of the ten messages are the assistant's. They took 11 of the 38 calls and produced one fact, the note that fish was now included.

{% include diagram.html name="graphiti-cost" alt="Tokens read to store the example's two sessions. Textual memory: 916 tokens in 2 LLM calls. Mem0: 16,862 tokens in 2 LLM calls and 4 embedding calls. Zep / Graphiti: 60,374 tokens in 38 LLM calls and 25 embedding calls, split by step: finding entities 24,118 in 10 calls, matching 7,194 in 7, extracting facts 19,166 in 10, comparing 9,896 in 11. Below, Graphiti's LLM calls per message: 2, 3 and 6 in session 1; 5, 4, 4, 2, 5, 2 and 5 in session 2; the assistant's four messages took 11 of the 38." caption="What storing the same ten messages cost three designs in this series, and where Graphiti's calls went, message by message." %}

For comparison, here is what other systems in this series read to store the same two sessions, from their notebooks:

- **Textual memory** ([part 3][part-3]), which rewrites one profile after each session, made two model calls that read 916 tokens.
- **Mem0** ([part 4][part-4]), which extracts facts into a vector store, made two model calls that read 16,862 tokens, most of it one long system prompt read twice.
- **Zep/Graphiti** made 38 model calls that read 60,374 tokens: about 66 times textual memory, and about 3.6 times Mem0.

The difference grows with the length of a history. The cost of Graphiti's write path is paid per message and per fact, and the assistant's long answers in real conversations hold many facts. Reading is cheap: one embedding call and a search, with no model call.

## Where it breaks

The example showed the failures in a small form: a changed fact and an allergy that the built-in type does not store, a second node for one person, a closed fact returned in place of the new one, and a hard constraint cut by the limit. Longer histories show what follows from them, and two more.

I ran the real library, version 0.31.1 on a Neo4j database, in the larger experiment of this series, on LongMemEval, a public benchmark of long chat histories in which users state facts and later change them in passing. [Part 8][part-8] describes the experiment. Every setting was the library's default, with no custom entity types. Each failure below is labelled with where it happens.

**Failure 1: the entity prompt is written for named things** (step 1). Out of the box, an attribute of a person is not an entity, and a fact needs two. In the example, the built-in type stored nothing about the changed fact or the allergy. The experiment ran without custom types, and the same rules ("Generic event/activity nouns", "When in doubt, do not extract") are part of why failure 6 below happened.

**Failure 2: a fixed floor decides delivery** (read path). The floor of 0.6 is one constant in the library, and what it does depends entirely on the embedding model. With the model used here, all fourteen facts scored within 0.20 of each other, and the floor fell in the middle of them. Which side a fact lands on is decided at the third decimal, by how the model worded it. The Zep paper's experiments used another embedding model, BGE-m3, for which this constant may have been chosen; the library does not say.

**Failure 3: closed facts come back, and take places** (read path). The default search does not filter by date, so a closed fact competes with current ones for the ten places. In the example it took the tenth place, and the peanut allergy came eleventh. In the experiment, when the closed old value reached the answering model marked as ended, next to the new one, the answer was right every time. The dates work when both values arrive.

**Failure 4: matching at a threshold makes duplicate nodes** (step 2). "Lena" missed "Anton's sister" by 0.005, and the shellfish fact landed on a second node that no walk reaches. The opposite also happens: in the experiment, two different people called Alex were merged into one node, so a friend from a music festival was also "in the process of buying a home" with the user.

**Failure 5: how the library is fed decides whether it remembers.** The first run of the experiment cut each session into episodes of up to 8,000 characters. The prompts are written for one message from a named speaker, and Graphiti adds the ten previous episodes as context, so each prompt carried 60,000 to 80,000 characters, mostly the assistant's long answers. The model returned two or three entities per episode, and most changed facts never reached the graph.

In a traced example, this update was in the prompt:

> I just finished my 5th project since starting painting classes

The model extracted only the entities `assistant` and `bold colors`, so no fact about projects existed to update. Fed one message per episode, as Graphiti's own examples do, the same sentence produced the entities `user`, `painting project` and `painting classes`, and this fact:

> The user has completed their 5th project since they began attending painting classes

Nothing failed loudly in the broken run. It cost less, and it was wrong. The working run cost about 2.7 times as much.

**Failure 6: a change said in passing is never extracted** (step 3). Even with one message per episode, the extraction keeps what a message is about and drops its asides. A user wrote:

> I just saw a Northern Flicker in my local park last weekend, which brings my total species count to 32.

This message produced four facts, about the Northern Flicker, sunflower seeds and suet, and none about the count. The earlier count, 27, had been the point of an earlier sentence, so it was stored cleanly, and it stayed current. This was the most common cause of wrong answers in the experiment.

**Failure 7: dating by when a fact became true can close the newer fact** (closing rule). A user mentioned "my recent family trip to Hawaii" on 26 May. Two days later, in another session, they said of Paris: "we just went there as a family last month". The two statements were dated on different principles:

- The Hawaii facts were dated by the message, 26 May, by the rule for ongoing facts.
- The Paris fact was dated by its phrase, 1 April.

The model correctly marked the Hawaii facts as contradicted by the later statement about Paris. Then the closing rule applied the dates. The Hawaii facts start later, and in the rule a fact that starts later wins, so it closed Paris. The answer to "Where did I go on my most recent family trip?" was Hawaii. Every other system in the experiment answered Paris.

The Zep paper (p. 3) describes the rule differently: on a contradiction, newer information always wins. The library decides by when each fact started, not by when it was said.

The complete account of every wrong answer in the experiment is in [docs/findings/graphiti.md][findings].

When its design worked, it worked well. Because closed facts stay in the graph with their dates, Graphiti answered every question in the experiment that asked for an earlier value ("What was my previous status?").

### How to notice and fix these failures

These failures are visible in the graph, not in the answers. Three checks find most of them:

- **Count entities and facts per message.** A user message that produced no fact, or an episode with two entities from a long text, is failure 1, 5 or 6.
- **Read the facts about one subject after a change.** Two open facts with different values, or a closed newer one, is failure 6 or 7.
- **Score a few known facts against a few known questions.** If the scores sit in a narrow band around 0.6, the floor decides, as in failure 2.

And the fixes, most of them settings:

- **For failure 1, describe the entity types** your application cares about. This is the first thing to configure for memory about a person.
- **For failure 5, feed one message per episode**, with the speaker's name, in order. Leaving out the assistant's messages would cut the cost by a large share; it would also lose the rare fact that only the assistant restated. I did not test this.
- **For failures 2 and 3, filter to current facts and set the floor** for the embedding model in use, or replace the floor with a fixed number of results.
- **For the hard constraint, do not leave it to the ranking.** A fact that must be in every answer needs a place the search does not control: for example, every fact between the user and an entity of type `HealthCondition`, read on every request.
- **For a question about linked people, walk from the entities the question names**, and merge the walk into the ranking with care: in the example, each fix moved some facts in and others out.
- **For failure 7, date a fact by when it was said** when the phrase is vague, or have the closing rule prefer the later statement when the model marked a contradiction. Either would trade one error for another; this is a design choice of the library, not a bug.

## When a graph earns its cost

Graphiti closes a superseded fact cleanly: a model judges that two facts conflict, and plain code decides which one ends and when, from the dates. Nothing is lost, and "what was true then?" is a filter. A walk can reach a fact through linked entities, which no search by words or meaning can do. These strengths come from the graph and the four dates. The costs come from the same machinery: several model calls for every message, prompts and thresholds that decide what is stored and returned, and dates that are only as good as the model's reading.

I would use a dated graph when three conditions hold:

- The questions need history: "where did she live last year?", "what was my previous plan?".
- Answers are reached through linked entities rather than through the words of the question, and the application can choose where a walk starts.
- Someone will configure the entity types and tune the thresholds for their data and their embedding model, and will check what is stored.

It is a poor fit in three situations:

- The newest value is all that is needed. Dates on plain facts, or a profile that a model rewrites, do that at a fraction of the cost.
- The facts are mostly about one user. They are all one step from the user's node, and a table with a subject column and the same dates would return the same rows.
- The cost of writing matters. Every message pays for the four steps, whether or not it says anything worth storing.

## History and related work

**The Zep paper.** [Zep][zep] (2025) describes the service and its engine (pp. 2–5). The graph has three layers:

- **episodes**, the raw messages, kept as the source of record;
- **entities and facts**, the layer that is searched;
- **communities**: groups of strongly connected entities, each with a summary, for broad questions. They are kept up to date by label propagation, chosen over the Leiden algorithm because a new entity can join the community most of its neighbours belong to.

The paper names the two timelines: a timeline of the world (`t_valid`, `t_invalid`) and a timeline of ingestion (`t'_created`, `t'_expired`). On a contradiction with an overlapping fact, the old fact's `t_invalid` is set to the new fact's `t_valid` (p. 3).

On LongMemEval with `gpt-4o` answering, the paper reports 71.2% against 60.2% for the whole history in the prompt, with about 1.6K tokens of context against 115K (p. 7, Table 2). These are the vendor's own figures, judged with the benchmark's prompts, and the only baseline is the whole history.

**From the paper to the library.** The library differs from the paper in four ways that matter for this post:

- **Context.** The paper says entity extraction sees the last four messages (n = 4) and adds a reflection pass to catch missed entities. The library passes the last ten messages, and runs no reflection pass.
- **Matching.** The paper finds candidate entities by embedding similarity and by a full-text search over names and summaries. The library finds them by exact name and by the name's embedding.
- **Search.** The paper describes three searches side by side: cosine similarity, a full-text search and a breadth-first walk. The library's default `search()` uses the first two; the walk is in other recipes, from starting points the application chooses.
- **The contradiction rule** became stricter in version 0.31.0 (October 2026), as described in step 4.

**A competitor's measurement.** The [Mem0 paper][mem0] (2025, p. 14) measured Zep on LoCoMo, a benchmark of long conversations between two people. It reports Zep's stored memory at more than 600,000 tokens per conversation, against about 7,000 for Mem0, and says that Zep's memories became usable only hours after ingestion. It is a competitor's measurement, made in 2025.

**Storing dated facts is not answering from the right one.** [A-TMA][a-tma] (2026) names the failure "ghost memory": old, current and transitional versions of a fact are retrieved together and reach the answer model with no mark of which is which (p. 1). It adds a layer that labels each retrieved fact as current, historical or transitional. With Graphiti/Zep as the host, the F1 score on LoCoMo's questions about time (the word overlap between an answer and the reference answer) rose from 0.0295 to 0.1705 (p. 11, Tables 3–4). Failure 3 above is one form of this: the closed fact was returned with its dates, and it took a place the hard constraint needed.

**Updates, in an independent comparison.** [Are We Ready For An Agent-Native Memory System?][agent-native] (2026) runs fourteen memory systems under one protocol. Two of its results bear on this design:

- **Updates.** On questions asked after facts changed, Zep scored best: 44.4 by exact substring match, against 20.0 for the whole history in the prompt and 15.6 for Mem0 (p. 9, Table 2).
- **Cost.** Zep was also among the slowest. It passed 84 on the paper's utility score only at 155 seconds per query (p. 11, Fig. 11).

**Two other reasons for a graph.** Papers use a graph for different reasons, and the example separates them. Zep wants time, and its handling of time needs only the dates. [HippoRAG][hipporag] (2024) wants multi-hop retrieval in one step: it builds a graph of noun phrases from a fixed corpus, and spreads probability from the entities in a question with Personalized PageRank, so a question that needs two links costs one sparse computation rather than one model call per link. [A-MEM][a-mem] (2025) wants a store that reorganises itself: each new note is linked to its nearest notes, and the model may rewrite those neighbours in the light of the new one (p. 5). In the example, the graph earned its place only on the fact two links away, which is HippoRAG's reason, not Zep's.

## Run it yourself

The [notebook][notebook] for this post is a re-implementation of Graphiti's write path and search, made so that every step can be read. It imports the prompts and the thresholds from `graphiti-core` 0.31.1, the version the larger experiment runs, and writes the control flow of `add_episode()` around them in about 150 lines of plain Python, with the graph kept in Python objects. Every prompt, reply, entity, fact and score in the example comes from it. The replays in this post are separate calls with the same prompts, and they are marked as replays.

It leaves out the parts that do not change which facts are stored or closed in this conversation:

- entity summaries and structured attributes;
- communities;
- the cross-encoder reranker, which other search recipes use;
- a comparison of long names by spelling (MinHash, Jaccard similarity of at least 0.9), which runs before the model is asked. The closest pair of names in this conversation scores 0.733.

The real library on a graph database is what the experiment runs, through the wrapper in the repository.

I used `gemini-3.1-flash-lite` for every model call and `gemini-embedding-001` for the embeddings. Both are available on the free tier of the Gemini API, which is enough for the 42 model calls that the notebook makes. All systems in this series use the same models, so that differences in their results come from their designs.

Model replies vary from run to run, even with the same prompt. A rerun of the notebook can word the extracted facts differently and change which ones are matched or closed, and a different model can change more. The mechanism stays the same.

The notebook runs one short conversation. To see how the design behaves on long histories, read [part 8][part-8]. Its experiment is in the same [repository][repo].

Here are a few experiments worth trying in the notebook:

- Lower `NODE_DEDUP_COSINE_MIN_SCORE` to 0.55 and run session 2 again. Does "Lena" now match "Anton's sister", and does a walk then reach the shellfish fact?
- Store the name the model suggests in step 2 ("Lena") on the matched entity, and run session 2 again.
- Add only the user's messages. How many calls does that save, and is anything lost?
- State the change less directly ("grabbed some salmon last night, been doing that a lot lately"). Does step 4 still mark a contradiction under the stricter prompt?
- Add a message that says "I ate fish until 2017". Which fact gets the end date?

## References

<!-- REFS -->

Papers:

- Rasmussen et al., [Zep: A Temporal Knowledge Graph Architecture for Agent Memory][zep] (2025)
- Chhikara et al., [Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory][mem0] (2025)
- Shi et al., [A-TMA: Decoupling State-Aware Memory Failures in Long-Term Agent Memory][a-tma] (2026)
- Zhou et al., [Are We Ready For An Agent-Native Memory System?][agent-native] (2026)
- Gutiérrez et al., [HippoRAG: Neurobiologically Inspired Long-Term Memory for Large Language Models][hipporag] (2024)
- Xu et al., [A-MEM: Agentic Memory for LLM Agents][a-mem] (2025)

<!-- /REFS -->

Other sources:

- Zep, [Graphiti on GitHub][graphiti-repo]
- Graphiti, the prompts at version 0.31.1: [entities][prompt-nodes], [matching][prompt-dedupe-nodes], [facts][prompt-edges], [comparison][prompt-dedupe-edges]
- Graphiti, [pull request 1964: extraction, dedup and temporal fixes from the Zep fork][graphiti-pr]

[zep]: https://arxiv.org/abs/2501.13956
[mem0]: https://arxiv.org/abs/2504.19413
[a-tma]: https://arxiv.org/abs/2607.01935
[agent-native]: https://arxiv.org/abs/2606.24775
[hipporag]: https://arxiv.org/abs/2405.14831
[a-mem]: https://arxiv.org/abs/2502.12110
[graphiti-repo]: https://github.com/getzep/graphiti
[prompt-nodes]: https://github.com/getzep/graphiti/blob/v0.31.1/graphiti_core/prompts/extract_nodes.py
[prompt-dedupe-nodes]: https://github.com/getzep/graphiti/blob/v0.31.1/graphiti_core/prompts/dedupe_nodes.py
[prompt-edges]: https://github.com/getzep/graphiti/blob/v0.31.1/graphiti_core/prompts/extract_edges.py
[prompt-dedupe-edges]: https://github.com/getzep/graphiti/blob/v0.31.1/graphiti_core/prompts/dedupe_edges.py
[graphiti-pr]: https://github.com/getzep/graphiti/pull/1964
[repo]: https://github.com/anton-dergunov/agent-memory-eval
[notebook]: https://anton-dergunov.github.io/agent-memory-eval/notebooks/03-zep-graphiti.html
[findings]: https://github.com/anton-dergunov/agent-memory-eval/blob/main/docs/findings/graphiti.md
[part-3]: /posts/2199/01/agent-memory-3-textual-memory/
[part-4]: /posts/2199/01/agent-memory-4-mem0/
[part-8]: /posts/2199/01/agent-memory-8-experiment/
