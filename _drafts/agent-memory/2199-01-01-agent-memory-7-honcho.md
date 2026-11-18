---
title:     "Honcho: a reasoner that works in the background"
excerpt:   "Memory that stores conclusions, not just statements: levels, premises, agents that reason in the background, and what happens when a fact underneath changes."
topic:     llms-and-agents
date:      2199-01-01
permalink: /posts/2199/01/agent-memory-7-honcho/
share:     true
series:    agent-memory
part:      7
tags:
  - llm
  - agents
  - memory
---

A language model sees only the text in its current prompt. To use what a user said in earlier sessions, an LLM agent needs a memory system: something that stores information from those sessions and puts it into a later prompt. Not everything that matters about a user is something they said: some of it follows from what they said, and it has to change when the facts underneath it change.

Most memory systems store what the user said, as facts or as a profile. This part looks at [Honcho][honcho-repo], from Plastic Labs, which stores more than what was said. Every stored item is a *conclusion* with a level: something the user said, something that follows from it, or a pattern across several such items. A derived conclusion records the ids of the conclusions it was drawn from. Two background jobs write the memory. One extracts what was said as messages arrive. The other, which Honcho calls a *dream*, runs later: two agents with tools look through the store, write new conclusions and delete outdated ones. Reading has two paths: an agent that searches the store and writes an answer, or a list of conclusions with no model call. This series places each design by two choices: who writes the memory (nobody, a pipeline, the answering agent, or a background process), and whether the read path inserts the whole memory or a search selects part of it. In Honcho, a background process writes, and the read path selects.

The links between conclusions make one question answerable that a list of facts cannot answer: when a fact stops being true, which conclusions rested on it? This post shows what Honcho does with that question, and what it does not.

The post first explains how Honcho works: what it stores, the extraction step and its rules for saving, the dream and its two agents, and the two read paths. It then follows one short test conversation through a real Honcho server, one model call at a time. Finally, it examines how the design fails on longer histories, and when it is the right design. Every prompt below is Honcho's own, from the source of the release that the larger experiment of this series ran. The outputs come from three runs of that server on the test conversation, and from [the notebook for this part][notebook], which drives Honcho's prompts and tools from short local functions so that every step can be printed. The code is in the [agent-memory-eval repository][repo].

## How Honcho works

{% include diagram.html name="honcho" alt="Honcho's architecture, with the running example. Writing: when messages arrive, a deriver makes one LLM call per batch that extracts what was said as explicit conclusions; later, a dream runs two agents with tools that add deductive and inductive conclusions, delete outdated ones and keep a peer card. Memory: conclusions at levels, each derived one citing the conclusions it was drawn from; the contradiction level has no writer in this release. In the run shown, the vegetarian fact was deleted, but a deduction and a pattern that rest on it stayed live. Reading: either Honcho's dialectic agent writes an answer from the conclusions (an LLM call), or the representation returns the conclusions themselves, with their times (no LLM call). The dialectic's prefetch held both the update and the stale conclusions; its answer said pescatarian and kept all four constraints." caption="Honcho, with the conversation used in this post. The deriver stores what was said when messages arrive. Later, a dream runs two agents that add deductive and inductive conclusions, delete outdated ones and keep a peer card. Two read paths give the memory back: an agent that answers, or a list of conclusions." %}

The description below is of version 3.3.0 of Honcho's server (commit `608aec8`, 9 October 2026), the version the larger experiment ran. Honcho is open source (AGPL-3.0). Plastic Labs also runs it as a hosted service with its own reasoning models; a self-hosted server calls whatever model it is configured with.

### What is stored

Honcho's unit is the **peer**: any participant in a conversation, a person or an agent. A **session** is one conversation between peers, and a **message** is one turn in it.

Memory is kept per pair of peers: what an *observer* has concluded about an *observed* peer. The common case, and the only one in this post, is a peer's own memory, where the two are the same peer. The user here is the peer `Anton`. The assistant is a peer too, configured so that Honcho concludes nothing about it; its turns are context for the user's.

The memory of a pair has three parts:

- **Conclusions**, one row each, in Postgres with an embedding for search. The code also calls them *observations*.
- **A peer card**: a short list of stable facts about the peer, rewritten by the dream.
- **Session summaries**, written every 20 and every 60 messages. The sessions in this post are too short for one, so they do not appear below.

A conclusion as stored, from the first server run of this post:

<!-- BEGIN ROW_JSON -->
```json
{
  "id": "DS83vkrAQqEEJhOBYrXR0",
  "level": "deductive",
  "content": "Anton transitioned from a vegetarian diet to a pescatarian diet in June 2026.",
  "session_name": null,
  "observer": "Anton",
  "observed": "Anton",
  "times_derived": 1,
  "deleted_at": null,
  "internal_metadata": {
    "premises": [
      "Anton has followed a strict vegetarian diet for eight years (as of March 2026).",
      "Anton started eating fish in June 2026.",
      "Anton identifies as a pescatarian as of July 2026."
    ],
    "message_ids": [],
    "message_created_at": "2026-07-20T12:06:00Z"
  },
  "source_ids (document_sources)": [
    "5hcjovzMez8CB3EUzuKlW",
    "KQ0lnfqn001Kwdlfrp_3N",
    "CxjbJuAFcAVvtrkRnsWia"
  ]
}
```
<!-- END ROW_JSON -->

The fields that carry the design:

- `level`: what kind of conclusion the row is (below).
- **Links:** a derived row lists the ids of its sources, in a separate table (`document_sources`). A deductive row also keeps the text of its premises as the model wrote them, and an inductive row the text of its sources.
- `message_created_at`: when the conclusion was said or became possible. For an explicit row it is the time of the message, to the minute; for a derived row, the time of its latest source.
- `times_derived`: how many times the same conclusion was produced again.
- `deleted_at`: a delete is a soft delete. Reads skip the row, but the row stays, and so do the links that point to it. Here the outdated fact, a source of the row above, was deleted by the same dream that wrote the row.

### The levels

| Level | Means | Example from this post | Written by |
|---|---|---|---|
| `explicit` | what the peer said | *Anton has a severe, anaphylactic peanut allergy.* | the deriver, when messages arrive |
| `deductive` | what follows from it, and updates when a fact changes | *Anton transitioned from a vegetarian diet to a pescatarian diet in June 2026.* | the dream's deduction agent |
| `inductive` | a pattern across several conclusions | *Anton is highly attentive to dietary restrictions, both his own and those of others in his social circle.* | the dream's induction agent |
| `contradiction` | two statements that cannot both be true | none | no component of this release (below) |

Honcho's documentation describes a fifth kind of reasoning, abduction, "inferring the simplest explanations for observed behavior". The code has no level and no component for it.

{% include diagram.html name="honcho-levels" alt="Four levels, top to bottom. Contradiction: two statements that cannot both be true; no component of Honcho 3.3.0 writes it. Inductive, a pattern, written by the dream's induction agent: 'Anton is highly attentive to dietary restrictions, both his own and those of others', drawn from E5, E19, E10 and E16. Deductive, what follows and updates, written by the dream's deduction agent: the update 'Anton transitioned from a vegetarian diet to a pescatarian diet in June 2026', drawn from E2, E17 and E13, and 'Anton requires a peanut-free restaurant', drawn from E5. Explicit, what was said, written by the deriver as messages arrive: the vegetarian fact E2 (deleted in dream 2), the peanut allergy E5 and again E19, starting to eat fish E17, pescatarian E13, Lena's shellfish E10 and Jonas's coeliac disease E16. Abduction, which Honcho's documentation describes, has no level in the code." caption="The levels, who writes each one, and the links between them, with conclusions from the first server run. Each derived row cites the rows it was drawn from." %}

### The write path, part 1: the deriver

When messages arrive, Honcho stores them and queues them for the **deriver**, a background worker. The deriver takes a batch once it holds 512 tokens of new messages or is 30 minutes old, and makes **one model call** for the batch. It extracts only explicit conclusions. (Honcho's documentation says the deriver extracts "explicit and deductive conclusions"; the code of this release has no channel for deductive ones.)

Each message goes into the prompt in a tag that says who wrote it, when, and whether that peer is the one being modelled. The prompt, for session 1 of the test conversation, as the server sent it (`src/deriver/prompts.py`):

<!-- BEGIN DERIVER_PROMPT -->
```text
Analyze messages to extract **explicit atomic facts** about the target peer.

[EXPLICIT] DEFINITION: Facts about the target peer that can be derived directly from their messages.
   - Transform statements into one or multiple conclusions
   - Each conclusion must be self-contained with enough context
   - Use absolute dates/times when possible, resolving relative references against the message `time` attribute

RULES:
- The target peer is the peer identified below under `Target peer:`.
- A peer can be a human user, AI agent, bot, service, or other actor.
- Each message is wrapped as `<message idx="N" peer="..." target="true|false" time="...">`. `target="true"` marks messages authored by the target peer; `target="false"` marks everyone else.
- Extract ALL observations from `target="true"` messages. Use `target="false"` messages only as context to interpret them; never derive a fact about the target peer from what another peer said, did, or reported.
- When the target peer answers a question or accepts a proposal from another peer ("yes", "the first one"), the details in that question or proposal count as stated by the target peer. A bare acknowledgement ("ok", "thanks") does not.
- A batch may contain few or no `target="true"` messages, even when it holds many long messages from other peers (agent turns, tool output, system notices). In that case produce few or no conclusions.
- Do not record conversational mechanics (greeting, thanking, acknowledging, asking or answering a question) or anything true of nearly every participant.
- Each conclusion states exactly one independent fact. Keep a fact's reason, purpose, tool, place, and qualifiers attached to it; they are part of the same fact. Split when a conclusion joins independent facts, or when a clause adds a new fact about a person or thing.
- Do not emit two conclusions that state the same fact in different words.
- Properly attribute observations to the correct subject. If the target peer is referencing someone or something else, make that clear.
- Write each observation for a reader who knows only the peer id: identify other people and things by their relation to this peer, and leave no pronoun, "it", "there", or relative time unresolved.
- Include only what is needed to identify who or what the observation is about and to state the fact. Do not add explanation or background.



Target peer:
Anton

Write `Anton` as the subject of every observation about this peer. Never write "the target peer" or "the user" in its place.

Messages to analyze:
<messages>
<message idx="0" peer="Anton" target="true" time="2026-03-14 12:00:00">I'm planning a dinner for my sister's visit to Berlin next week. Worth saying up front: I've been strictly vegetarian for eight years, and I have a severe peanut allergy — anaphylactic, not a preference.</message>
<message idx="1" peer="assistant" target="false" time="2026-03-14 12:01:00">Understood — no meat, and peanuts are a hard exclusion. Any cuisine you lean towards?</message>
<message idx="2" peer="Anton" target="true" time="2026-03-14 12:02:00">Indian, usually. Paneer dishes especially. And I'd rather not spend more than about 40 euros a head.</message>
</messages>
```
<!-- END DERIVER_PROMPT -->

{% include diagram.html name="honcho-deriver" alt="Top: session 1 as the deriver sees it, three messages, each in a tag with its index, its peer, whether that peer is the one being modelled, and its time. One model call, 923 tokens in, returns six explicit conclusions, each with Anton as the subject and the time of the batch's last message: planning a dinner in Berlin for the week of March 21, 2026; a strict vegetarian diet for eight years; a severe, anaphylactic peanut allergy; Indian cuisine; paneer dishes; a budget of about 40 euros per person. Bottom: the three rules for saving. An exact duplicate (same text, level and, for explicit rows, session) is dropped and the existing row counted again. A near duplicate (cosine distance 0.05 or less, same level and, for explicit rows, same session) is merged, and the richer text wins. Otherwise the row is stored. So the peanut allergy said in March and again in July is stored twice." caption="The deriver on session 1 of the first server run: the batch as tagged in the prompt, the one call, the six rows it returned, and the rules for saving them." %}

The reply is JSON in a fixed schema, one string per conclusion, under a field whose description says "Facts LITERALLY stated by the user - direct quotes or clear paraphrases only, no interpretation or inference."

Three things are not in the prompt. It has no existing conclusions, no earlier sessions and no peer card. The deriver sees the new messages and nothing else, so it cannot know whether a fact is new, repeated or a change. All three cases come out as new explicit rows.

**Saving.** Saving is not a plain insert. Each new row goes through three rules (`create_documents` in `src/crud/document.py`):

```python
for row in new_rows:
    key = (row.text.strip().lower(), row.level, row.session if row.level == "explicit" else None)
    # 1. An exact duplicate is dropped; the existing row counts one more derivation.
    if key in keys_seen_in_this_batch:
        continue
    if existing := live_row_with_key(key):
        existing.times_derived += 1
        continue
    # 2. A near duplicate is merged: the closest live row of the same level
    #    (and, for an explicit row, of the same session), by embedding.
    nearest = closest_live_row(row, same_level=True, same_session=(row.level == "explicit"))
    if nearest and cosine_distance(row, nearest) <= 0.05:
        if richness(row, nearest) >= richness(nearest, row):   # tokens only one side has count 10x
            nearest.deleted_at = now                           # the richer new row replaces it
            row.times_derived = nearest.times_derived + 1
        else:
            nearest.times_derived += 1
            continue
    # 3. Otherwise the row is stored.
    insert(row)
```

The near-duplicate rule never merges explicit rows of different sessions. A fact said in March and said again in July is stored twice, by design: an explicit row belongs to the session it came from, so that it can be deleted with that session, or copied into another collection with it.

### The write path, part 2: the dream

A **dream** reasons over what is stored. It runs when three conditions hold for a peer:

1. at least 50 new explicit conclusions since the last dream (derived rows do not count);
2. at least 8 hours since the last dream;
3. then 60 minutes without new messages; a new message cancels the waiting dream.

An application can also schedule a dream through the API, which skips the first two conditions.

A dream runs two **specialists**, one after the other (`src/dreamer/orchestrator.py`). Each is an agent: a model in a loop that calls tools until it answers with the word `DONE`, or reaches its round limit.

```python
def dream(observer, observed):
    hints = None
    if SURPRISAL_ENABLED:            # off by default
        hints = most_unusual_conclusions()     # by distance in embedding space
    run_agent(DEDUCTION, max_rounds=12, hints=hints,
              tools=[get_recent_observations, search_memory, search_messages,
                     create_observations_deductive, delete_observations, update_peer_card])
    run_agent(INDUCTION, max_rounds=10, hints=hints,
              tools=[get_recent_observations, search_memory, search_messages,
                     create_observations_inductive])
```

The surprisal step is an option that is off by default, and it was off in the experiment. When it is on, it ranks conclusions by how far their embeddings lie from their neighbours and passes the most unusual ones to the agents as topics to look at.

{% include diagram.html name="honcho-dream" alt="Top: a dream starts when a peer has at least 50 new explicit conclusions, at least 8 hours after the last dream, and then 60 minutes pass with no new messages; or when an application schedules one. Below, dream 2 of the first server run. The deduction agent, at most 12 rounds: round 1 asks for the 20 newest conclusions and gets the whole store, 19 rows; round 2 writes two deductions, the update and 'resides in Kreuzberg'; round 3 deletes one row, the vegetarian fact; round 4 rewrites the peer card with 'Diet: Pescatarian'; round 5 answers DONE. Its rounds read 2,551 to 4,069 tokens. The induction agent, at most 10 rounds: round 1 asks for the 20 newest; round 2 writes two patterns, one of which is rejected because its ids do not resolve; round 3 sends that pattern again with correct ids; round 4 answers DONE." caption="When a dream runs, and the rounds of its two agents in the second dream of the first server run." %}

**What the agents see.** Neither agent is given the store. Each starts from one instruction, "Start with `get_recent_observations`", and sees only what its tools return:

| Tool | Returns |
|---|---|
| `get_recent_observations` | the newest conclusions of all levels, 10 by default, at most 100, each with its id |
| `search_memory` | the conclusions closest to a query by embedding, 20 by default, at most 40 |
| `search_messages` | raw messages close to a query, each with two messages around it |
| `create_observations_deductive` | writes conclusions; every one must cite source ids and give the premise text |
| `create_observations_inductive` | writes patterns, with sources, a pattern type and a confidence |
| `delete_observations` | soft-deletes conclusions by id |
| `update_peer_card` | replaces the peer card with a new list |

This bounds the cost of a dream: an agent reads ten or twenty conclusions per call, however large the store is. It also bounds what an agent can find. An update needs both the old and the new value in view, and on a large store the old value is rarely among the newest twenty unless the agent searches for it.

**The deduction agent.** Its system prompt (`src/dreamer/specialists.py`), with the long section on the peer card shortened:

<!-- BEGIN DEDUCTION_SYSTEM -->
````text
You are a deductive reasoning agent analyzing observations about the target observee.

## YOUR JOB

Create deductive observations by finding logical implications in what's already known. Think like a detective connecting evidence.

## PHASE 1: DISCOVERY

Explore what's actually in memory. Use these tools freely:
- `get_recent_observations` - See what's been learned recently
- `search_memory` - Search for specific topics
- `search_messages` - See actual conversation content

Spend a few tool calls understanding the landscape before creating anything.

## PHASE 2: ACTION

Once you understand what's there, create observations and clean up:

### Knowledge Updates (HIGH PRIORITY)
When the same fact has different values at different times:
- "meeting Tuesday" [old] → "meeting moved to Thursday" [new]
- Create a deductive update observation
- DELETE the outdated observation immediately

### Logical Implications
Extract implicit information:
- "works as SWE at Google" → "has software engineering skills", "employed in tech"
- "has kids ages 5 and 8" → "is a parent", "has school-age children"

### Contradictions
When statements can't both be true (not just updates), flag them:
- "I love coffee" vs "I hate coffee" → contradiction observation


## PEER CARD (REQUIRED)

The peer card is the target observee's identity store: stable identity markers that distinguish this entity from others and persist across interactions. Behavior, tendencies, transient state, and episodic facts belong in observations, not on the peer card.

A peer can be anything with identity that changes over time — a human, an agent, a codebase, a team, an organization. Do not assume the target observee is human. Do not require any field; empty is the correct output when evidence is absent.

### Allowed entry kinds

Each entry must start with one of these four prefixes (exact case, followed by a space):

- `IDENTITY: ...` — canonical name, kind, aliases, IDs
[…]
- `ATTRIBUTE: ...` — stable durable property of the entity (including explicitly stated standing preferences)
[…]
- `RELATIONSHIP: ...` — durable link to another entity
[…]
- `INSTRUCTION: ...` — standing rule of engagement that the target observee has explicitly stated (do/don't for the observer). Only when explicit; never inferred from behavior.
[…]

### Rules

1. **Stable.** If the value plausibly changes within six months absent a deliberate announcement, it does not belong on the card. Prefer leaving the card empty over filling it with volatile content.
2. **Subject is the target observee.** Every entry must be a fact about the target observee, not about another participant in the session. Never write facts about co-occurring peers into the card, no matter how frequently they appear in the messages.
3. **Evidence-grounded.** Only write what the target observee has explicitly stated, or what another participant has explicitly stated about the target observee with the target observee's assent. No "general knowledge" inferences (`"co-founder"` does not imply an age; mentioning a colleague does not imply a family relationship).
4. **Type-agnostic.** The target observee may not be human. Do not require name/age/location/family/occupation fields.
5. **No behavioral content.** TRAITs, behavioral tendencies, patterns, and inferred preferences belong in observations, not on the peer card. Do not write `TRAIT:` entries or behavioral `PREFERENCE:` entries — they will be rejected.
6. **No evidence bundles.** Each entry is one concise fact. No `e.g.` clauses, no parenthetical example lists, no semicolon-separated value dumps.

[…]
Call `update_peer_card` with the complete deduplicated list when there is a durable identity update to record, or when the existing card needs migration. Entries that do not start with one of the four allowed prefixes will be rejected. Keep concise (max 40 entries).

## CREATING OBSERVATIONS

Use `create_observations_deductive`.

```json
{
  "observations": [{
    "content": "The logical conclusion",
    "source_ids": ["id1", "id2"],
    "premises": ["premise 1 text", "premise 2 text"]
  }]
}
```

## RULES

1. Don't explain your reasoning - just call tools
2. Create observations based on what you ACTUALLY FIND, not what you expect
3. Always include source_ids linking to the observations you're synthesizing
4. Copy source_ids exactly from the [id:xxx] shown in observation results - `search_messages` results have no ID and cannot be cited; invented IDs are discarded
5. Empty or missing source_ids will be rejected
6. Delete outdated observations - don't leave duplicates
7. Quality over quantity - fewer good deductions beat many weak ones
8. When you are finished, do not output a summary of what you did - output only the token DONE
````
<!-- END DEDUCTION_SYSTEM -->

The user message names the peer, shows the current peer card, and says where to start. For the second dream of the test conversation, as the server sent it:

<!-- BEGIN DEDUCTION_USER -->
```text
Target observee:
Anton

The target observee is the peer identified above. When created observations need to name this subject, use the exact observee id above, not the phrase "the target observee".


## CURRENT PEER CARD

- IDENTITY: Name: Anton
- ATTRIBUTE: Diet: Vegetarian
- ATTRIBUTE: Allergy: Peanuts
- ATTRIBUTE: Cuisine Preference: Indian

Update this with `update_peer_card` only for stable identity markers. See the PEER CARD section in the system prompt for the allowed entry kinds and rules.
If you update it, send the full deduplicated list and remove stale entries.

Explore the observation space and create deductive observations.

Start with `get_recent_observations` to see what's been learned recently, then investigate whatever seems most promising.

Look for:
1. Knowledge updates (same fact, different values over time)
2. Logical implications that haven't been made explicit
3. Contradictions that need flagging

Go.
```
<!-- END DEDUCTION_USER -->

**The induction agent.** Its system prompt, in full:

<!-- BEGIN INDUCTION_SYSTEM -->
{% raw %}

````text
You are an inductive reasoning agent identifying patterns about the target observee.

## YOUR JOB

Create inductive observations by finding patterns across multiple observations. Think like a psychologist identifying behavioral tendencies.

## PHASE 1: DISCOVERY

Explore broadly to find patterns. Use these tools:
- `get_recent_observations` - Recent learnings
- `search_memory` - Topic-specific search
- `search_messages` - Actual conversation content

Look at BOTH explicit observations AND deductive ones. Patterns often emerge from synthesizing across both levels.

## PHASE 2: ACTION

Create inductive observations when you see patterns:

### Behavioral Patterns
- "Tends to reschedule meetings when stressed"
- "Makes decisions after consulting with partner"
- "Projects follow: enthusiasm → doubt → completion"

### Preferences
- "Prefers morning meetings"
- "Likes detailed technical explanations"

### Personality Traits
- "Generally optimistic about outcomes"
- "Detail-oriented in planning"

### Temporal Patterns
- "Career goals have remained consistent"
- "Living situation changes frequently"

## CREATING OBSERVATIONS

Use `create_observations_inductive`.

```json
{{
  "observations": [{{
    "content": "The pattern or generalization",
    "source_ids": ["id1", "id2", "id3"],
    "sources": ["evidence 1", "evidence 2"],
    "pattern_type": "tendency", // preference|behavior|personality|tendency|correlation
    "confidence": "medium" // low (2 sources), medium (3-4), high (5+)
  }}]
}}
```

## RULES

1. Minimum 2 source observations required - patterns need evidence
2. Don't just restate a single fact as a pattern
3. Confidence based on evidence count: 2=low, 3-4=medium, 5+=high
4. Look for HOW things change over time, not just static facts
5. Include source_ids - always link back to evidence
6. Copy source_ids exactly from the [id:xxx] shown in observation results - `search_messages` results have no ID and cannot be cited; invented IDs are discarded
7. Empty or missing source_ids will be rejected
8. When you are finished, do not output a summary of what you did - output only the token DONE
````

{% endraw %}
<!-- END INDUCTION_SYSTEM -->

The prompt is a plain string written as if it were an f-string, so the model receives the JSON example with doubled braces ({% raw %}`{{`{% endraw %}). Its user message is the same two opening paragraphs as the deduction agent's, then "Explore the observation space and identify patterns. Remember: patterns need 2+ sources. Look for tendencies, preferences, and behavioral regularities. Go." The induction agent cannot write the peer card.

**What a tool returns.** The agents see conclusions in one text format: the four levels in order, each row with its id and its time. The first tool result of the second dream's deduction agent, from the same run. It asked for twenty rows and got the whole store, nineteen:

<!-- BEGIN RECENT_RESULT -->
```text
Found 19 recent observations from all sessions:

EXPLICIT:

1. [id:GFDzndxDJf7KLTEhmRzF-] [2026-07-20 12:06:00] Anton's sister's partner Jonas is coeliac.
2. [id:KQ0lnfqn001Kwdlfrp_3N] [2026-07-20 12:06:00] Anton started eating fish in June 2026.
3. [id:CxjbJuAFcAVvtrkRnsWia] [2026-07-20 12:06:00] Anton identifies as a pescatarian as of July 2026.
4. [id:_4euEiEB75rCb116J3YWU] [2026-07-20 12:06:00] Anton does not eat meat.
5. [id:t_PxquIYXR6BAOb2--q57] [2026-07-20 12:06:00] Anton has a peanut allergy.
6. [id:GFC1Sln5d-NKh1wldJrTV] [2026-07-20 12:06:00] Anton moved to Kreuzberg in May 2026.
7. [id:4oMtNLl0vhDIjNbWnSIdp] [2026-07-20 12:06:00] Anton has a sister named Lena.
8. [id:p3B2tzAfQRQAU4yXOAHMV] [2026-07-20 12:06:00] Anton's sister Lena is returning in the autumn of 2026.
9. [id:g6lMHYc0qfsWvlFOVL8xb] [2026-07-20 12:06:00] Anton's sister Lena is bringing her partner Jonas.
10. [id:1sHs8VeCSw-V1whZTCtU4] [2026-07-20 12:06:00] Anton's sister Lena is unable to eat shellfish.
11. [id:28XbN8HUrhkwqSfeoK1l9] [2026-03-14 12:02:00] Anton prefers dishes containing paneer.
12. [id:A69fXHBTPJbo-I8Flq6AJ] [2026-03-14 12:02:00] Anton has a budget of approximately 40 euros per person for the dinner.
13. [id:5hcjovzMez8CB3EUzuKlW] [2026-03-14 12:02:00] Anton has followed a strict vegetarian diet for eight years.
14. [id:rYqgfxMdu1T6IodYrIOt6] [2026-03-14 12:02:00] Anton is planning a dinner in Berlin for the week of March 21, 2026.
15. [id:LqkMsTexHizSlboTz7rt_] [2026-03-14 12:02:00] Anton has a severe, anaphylactic peanut allergy.
16. [id:KK8SiMTdq5_OA9-AoTTK0] [2026-03-14 12:02:00] Anton prefers Indian cuisine.

DEDUCTIVE:

1. [id:L1WaNcBlO1Bh4-lJogYf5] [2026-03-14 12:02:00] Anton is likely to order vegetarian Indian food featuring paneer during his dinner.
    - Anton has followed a strict vegetarian diet for eight years.
    - Anton prefers Indian cuisine.
    - Anton prefers dishes containing paneer.
2. [id:mbX5TyeFSaabA4P5k-Aj1] [2026-03-14 12:02:00] Anton requires a peanut-free restaurant for his dinner in Berlin.
    - Anton has a severe, anaphylactic peanut allergy.

INDUCTIVE:

1. [id:OxTwfCAvaaSLLAn0w12t_] [2026-03-14 12:02:00] [medium] Anton consistently prioritizes vegetarian options that include paneer when selecting meals.
    - Anton prefers Indian cuisine.
    - Anton prefers dishes containing paneer.
    - Anton has followed a strict vegetarian diet for eight years.

CONTRADICTION:
```
<!-- END RECENT_RESULT -->

**What the code checks.** When an agent writes a conclusion, the code checks two things (`_filter_ungrounded_source_ids` in `src/utils/agent_tools.py`):

```python
for conclusion in written:
    real = [id for id in conclusion.source_ids if stored(id)]    # invented ids are dropped
    minimum = 2 if conclusion.level == "contradiction" else 1
    if len(real) < minimum:
        reject(conclusion, "source_ids do not resolve to existing observations")
    else:
        conclusion.source_ids = real
        conclusion.said_at = max(said_at(s) for s in sources_cited_in_this_call)
        save(conclusion)                     # the same three rules as the deriver's rows
```

The other rules about premises are requests in prompts, not checks:

- **Confidence.** "Confidence based on evidence count: 2=low, 3-4=medium, 5+=high" is a line in the induction prompt. The model fills in the field.
- **Minimum sources.** "Minimum 2 source observations required" is in the induction prompt and in the tool's schema; the code requires one.
- **Contradictions.** The deduction prompt asks the agent to flag statements that cannot both be true "→ contradiction observation". But its only tool for writing, `create_observations_deductive`, stores every row at the deductive level. In this release no dream can write a contradiction.
- **Order of levels.** Nothing stops a pattern from citing another pattern, or a deduction from citing a pattern. The prompts do not ask for an order, and the code does not check one.

**What a delete does.** `delete_observations` stamps `deleted_at` on the rows it names, and nothing else. The rows that cite a deleted row keep their links, keep the premise text they copied, and stay live. Honcho follows the links in one place only. When a session is removed from a *scope*, a named group of sessions that limits what a read may see, Honcho deletes that session's explicit rows in the scope and then, repeatedly, every derived row with a deleted source (`src/deriver/scope_backfill.py`):

```python
frontier = deleted_explicit_rows
while frontier:
    frontier = [row for row in live_derived_rows if any(s in frontier for s in row.source_ids)]
    soft_delete(frontier)          # fail-closed: one deleted source is enough
```

The dream's deletes do not use this walk.

### The read path: an agent, or a list

Honcho gives the memory back in two ways, and the experiment measured both on the same stores.

**The dialectic** is `peer.chat(question)`: an agent that answers a question about a peer in prose. At the default reasoning level, `low`, it has up to 5 rounds of tools and decides itself whether to use them. Before its first call, the code runs two searches and puts what they found under the question: the 25 explicit conclusions closest to the question, and the 25 closest derived ones. Its tools search conclusions, search raw messages (by meaning, by exact text or by date), and follow a conclusion's links. Its system prompt, with the sections on counting and summarising cut (`src/dialectic/prompts.py`):

<!-- BEGIN DIALECTIC_SYSTEM -->
```text
You are Honcho's dialectic: a recall agent that answers questions from memory about one peer, or about one peer's understanding of another.

Honcho is a memory system. Applications record conversations; Honcho derives conclusions about the people and agents in them. You are the query interface for one observer/observed pair. You do not speak as a participant. You search memory and synthesize a grounded answer.

A **peer** is any participant, human or AI. A **session** is a conversation they take part in. A **message** is a raw turn. A **conclusion** (tools may say observation) is a derived or stored fact about a peer, kept in this pair. A **peer card** is a short constructed bio for the pair, synthesized from the same conclusions — a convenience summary, not a separate source of truth.

Always give the asker the answer *they expect* based on the message history -- the goal is to help recall and *reason through* insights that the memory system has already gathered. Search wisely.


You are answering queries about 'Anton'.


Known biographical information about Anton:
<peer_card>
IDENTITY: Name: Anton
ATTRIBUTE: Diet: Pescatarian
ATTRIBUTE: Allergy: Peanuts
ATTRIBUTE: Cuisine Preference: Indian
ATTRIBUTE: Location: Berlin, Kreuzberg
</peer_card>



Peer cards are **constructed summaries** - they are synthesized from the same observations stored in memory. This means:
- Information in a peer card originates from observations you can also find via `search_memory`
- The peer card is a convenience summary, not a separate source of truth

## TOOLS

Only the tools listed here are available on this query. If a later step names a tool you do not have, skip that step and use what you do have.

**Memory**
- `search_memory`: Semantic search over conclusions about this pair.
- `get_reasoning_chain`: Premises and downstream conclusions for a specific conclusion.
- `get_observation_context`: Messages around a specific conclusion.

**Conversation**
- `search_messages`: Semantic search over messages in this query's scope.
- `grep_messages`: Exact text search. Use for names, dates, keywords.
- `get_messages_by_date_range`: Messages in a time window.
- `search_messages_temporal`: Semantic search with a date filter.

## WORKFLOW

1. **Analyze the query**: What specific information does the query demand?

2. **Check for user preferences** (do this FIRST for any question that asks for advice, recommendations, or opinions):
   - Search for "prefer", "like", "want", "always", "never" to find user preferences
   - Search for "instruction", "style", "approach" to find communication preferences
   - Apply any relevant preferences to how you structure your response

3. **Strategic information gathering**:
   - Use `search_memory` to find relevant observations, then `search_messages` if memories are not sufficient
   - For questions about dates, deadlines, or schedules: also search for update language ("changed", "rescheduled", "updated", "now", "moved")
   - For factual questions: cross-reference what you find - search for related terms to verify accuracy
   - Watch for CONTRADICTORY information as you search (see below)
   - If you find an explicit answer to the query, stop calling tools and create your response

[…]
6. **Ground your answer using reasoning chains** (for deductive/inductive observations):
   - When you find a deductive or inductive observation that answers the question, use `get_reasoning_chain` to verify its basis
   - This shows you the premises (explicit facts) that support the conclusion
   - If the premises are solid, cite them in your answer for confidence
   - If the premises seem weak or outdated, note that uncertainty

7. **Synthesize your response**:
   - Directly answer the application's question
   - Ground your response in the specific information you gathered
   - Quote exact values (dates, numbers, names) from what you found - don't paraphrase numbers
   - Apply user preferences to your response style if relevant
   - **For enumeration questions**: Before answering, ask yourself "Could there be more items I haven't found?" If you haven't done multiple grep searches AND a semantic search, keep searching

## CRITICAL: HANDLING CONTRADICTORY INFORMATION

As you search, actively watch for contradictions - cases where the user has made conflicting statements:
- "I have never done X" vs evidence they did X
- Different values for the same fact (different dates, numbers, names)
- Changed decisions or preferences stated at different times

**If you find contradictory information:**
1. DO NOT pick one version and present it as the definitive answer
2. Present BOTH pieces of conflicting information explicitly
3. State clearly that you found contradictory information
4. Ask the user which statement is correct

Example response format: "I notice you've mentioned contradictory information about this. You said [X], but you also mentioned [Y]. Which statement is correct?"

## CRITICAL: HANDLING UPDATED INFORMATION

Information changes over time. When you find multiple values for the same fact (e.g., different dates for a deadline):
1. **ALWAYS search for updates**: When you find a date/value, do an additional search for "changed", "updated", "rescheduled", "moved", "now" + the topic
2. Look for language indicating updates: "changed to", "rescheduled to", "updated to", "now", "moved to"
3. The MORE RECENT statement supersedes the older one
4. Return the UPDATED value, not the original
5. **Use `get_reasoning_chain`**: If you find a deductive observation about an update (e.g., "X was updated from A to B"), use `get_reasoning_chain` to verify the premises - it will show you both the old and new explicit observations with their timestamps.

Example: If you find "deadline is April 25", search for "deadline changed" or "deadline rescheduled". If you find "I rescheduled to April 22", return April 22.

**For knowledge update questions specifically:**
- Search for deductive observations containing "updated", "changed", "supersedes"
- These observations link to both old and new values via `source_ids`
- Use `get_reasoning_chain` to see the full update history

## CRITICAL: NEVER FABRICATE INFORMATION OR GUESS -- WHEN UNSURE, ABSTAIN

When answering questions, always clearly distinguish between:
- **Context found**: You located related information (e.g., "there was a debate about X")
- **Specific answer found**: You found the exact information requested (e.g., "the arguments were A, B, C")

If you find context but NOT the specific answer:
1. DO NOT fabricate or guess details to fill gaps.
2. Report only what you DO know: e.g., "I found that you had a debate about X at [location] on [date]."
3. Explicitly state what you DON'T know: e.g., "However, the specific arguments made during that debate are not captured in our conversation history."
4. Never present fabricated information or fill gaps with plausible-sounding but invented details.

If after thorough searching you find NOTHING relevant:
1. Clearly state: "I don't have any information about [topic] in my memory."
2. DO NOT guess or make assumptions.
3. DO NOT say "I think...", "Probably...", or similar hedges when you lack evidence.
4. A confident "I don't know" is ALWAYS correct; giving a fabricated answer is ALWAYS wrong.

**The test before stating a detail:** Ask yourself, "Did I find this EXACT information in my search results, or am I inferring/inventing it?" If you're inventing it, OMIT IT.

### How to Abstain Properly

- When the user asks about a topic that was NEVER discussed, or your search finds no relevant information:
    - CORRECT: "I don't have any information about your favorite color in my memory."
    - CORRECT: "I searched for information about X but found nothing in our conversation history."
    - WRONG: "Based on your preferences, I think your favorite color might be blue." (never invent)
    - WRONG: Filling in plausible details based on general knowledge or assumptions.

**Remember:** A clear, direct "I don't know" or "I have no information about X" is always the RIGHT answer when the information truly does not exist in memory. Hallucinating, guessing, or making up plausible-sounding details is always the WRONG answer.

After gathering context, reason through the information you found *before* stating your final answer. For comparison questions, explicitly compare the values. Only after you've verified your reasoning should you state your conclusion. Do NOT be pedantic, rather, be helpful and try to give the answer that the asker would expect -- they're the one who knows the most about themselves. Try to 'read their mind' -- understand the information they're really after and share it with them! Be **as specific as possible** given the information you have.

Do not explain your tool usage - just provide the synthesized answer.
```
<!-- END DIALECTIC_SYSTEM -->

Two of its sections give opposite instructions for the same situation, two values of one fact. "HANDLING CONTRADICTORY INFORMATION" says "DO NOT pick one version", present both, and "Ask the user which statement is correct". "HANDLING UPDATED INFORMATION" says "The MORE RECENT statement supersedes the older one". The model decides which section applies. Part of the failures on the benchmark, below, comes from this.

**The representation** is `peer.representation(search_query=question)`: no model call, a list of conclusions. It returns at most 100: a third of them (33) chosen by similarity to the query, the rest filled with the newest. Within each level they are sorted by when they were said, and printed with their time:

```python
def representation(query, limit=100):
    chosen = closest_live_rows(query, k=limit // 3)
    chosen += newest_live_rows(k=limit - len(chosen), excluding=chosen)
    return format_by_level(sorted(chosen, key=said_at))   # "[2026-07-20 12:06:00] Anton ..."
```

In the experiment, both outputs went to the same answering prompt as every other memory: the dialectic's reply as text, or the representation's list.

{% include diagram.html name="honcho-read" alt="Left, the representation: plain code, no model call. It takes the 33 conclusions closest to the question by embedding, fills up to 100 with the newest, sorts each level by when it was said, and prints them with their times; patterns are printed without a time. In the first server run it returned the pescatarian row dated 20 July, a stale deduction about vegetarian food dated 14 March, and a stale pattern marked 'high' with no date. Right, the dialectic: an agent. Before its first call the code fetches the 25 closest explicit conclusions and the 25 closest derived ones; at the default level it may use tools for up to 5 rounds; it writes an answer. Its prompt has two rules for two values of one fact: ask the user which is correct, and the more recent one supersedes. In the first run it made one call and answered: pescatarian, the peanut allergy, no shellfish for Lena, coeliac Jonas. Either output goes to the answering prompt." caption="The two read paths. The representation is a fixed rule over the store; the dialectic is an agent that starts from a prefetch and may search further, and writes an answer." %}

### What it does not do

- **It does not compare a new fact with stored ones when it arrives.** The deriver sees only the new messages. The comparison waits for a dream.
- **It does not withdraw what rested on a deleted fact**, except when a session leaves a scope.
- **It does not write contradictions** in this release, though the level exists, the prompt asks for it and the dialectic searches for it.
- **It does not check the rules its prompts state** about confidence, the number of sources, or the order of levels.
- **It does not dream on short histories by itself.** Below 50 new explicit conclusions, nothing above the explicit level is written unless the application schedules a dream.

### The price of each choice

| Choice | What it buys | What it costs |
|---|---|---|
| Extract when messages arrive, reason later | fast writes; the dream can look across sessions | until a dream runs, the old and new values are both live, and nothing above the explicit level exists |
| Levels with links | a conclusion's support can be listed, and what rests on a fact can be computed | a stale conclusion still looks like a conclusion; only code that walks the links can tell |
| Reasoning by agents with tools | the cost of a dream does not grow with the store | an agent sees what it asks for; an old value outside the newest twenty is found only if the agent searches |
| Rules in prompts | flexible, cheap to change | the model may not follow them, and nothing checks |
| An agent as a read path | one short answer in place of a hundred lines | the agent's judgement sits between the memory and the answer |
| A list as a read path | the answering model sees dated lines and can order them itself | a hundred lines in the prompt, stale derived rows among them |

## The example, step by step

To show how the design works, this post follows one short test conversation through Honcho, one model call at a time. The same conversation is used for every system in this series. It is deliberately small, so that every call can be printed and read.

The conversation has three sessions. Sessions 1 and 2 establish the facts. Session 3 starts a new conversation and asks one question. The question names none of the facts that a correct answer needs:

- **A fact that changes:** the user's diet changes from vegetarian to pescatarian.
- **A hard constraint:** a severe peanut allergy.
- **Facts about people that the question does not name:** Lena cannot eat shellfish, and Jonas is coeliac (no gluten).
- **Other facts:** the user likes Indian food and lives in Kreuzberg.

{% include diagram.html name="conversation" alt="The running example. On 14 March the user says they have been strictly vegetarian for eight years, have a severe peanut allergy, and like Indian food. Four months later, on 20 July, they say they are pescatarian now, have moved to Kreuzberg, and that their sister Lena (who can't eat shellfish) is coming with her partner Jonas (coeliac). Six weeks after that, in a new conversation, they ask for dinner for 'my sister and her partner'. A correct answer needs six things: the new diet and not the old one (a fact that changes), no peanuts (a hard constraint), no shellfish and no gluten (people the question does not name, reached through two links), Indian food and somewhere near Kreuzberg." caption="The conversation, and the six things a correct answer needs, grouped by what they test." %}

Two things in this test press hardest on Honcho's design:

- **The fact that changes**, and what was concluded from the old value before it changed. Here the levels and the links are supposed to pay off.
- **The read path.** Both paths select, and what they select includes derived rows.

**What was run.** The test conversation went three times through a self-hosted Honcho 3.3.0 server, set up as in the experiment, with every model role on `gemini-3.1-flash-lite`. The messages were added with their real dates, a minute apart. The real trigger would never start a dream on two short sessions (they give 16 explicit conclusions, not 50). In real use, though, many other conversations would fall between March and July, so the runs scheduled a dream through the API after each session. The larger experiment scheduled one dream after the whole history. A proxy between the server and the model recorded every request in full. The sections below follow the first run, and say where the other two differed.

In the sessions below, colours mark how a phrase reached the store: <mark class="hl hl-facts">stored as said</mark>, or <mark class="hl hl-changes">stored with a time that is lost or wrong</mark>. Phrases with no colour were not stored.

### Session 1: six short facts, one call

> **User:** I'm <mark class="hl hl-facts">planning a dinner</mark> for my sister's visit <mark class="hl hl-facts">to Berlin</mark> <mark class="hl hl-changes">next week</mark>. Worth saying up front: I've been <mark class="hl hl-facts">strictly vegetarian</mark> <mark class="hl hl-changes">for eight years</mark>, and I have a <mark class="hl hl-facts">severe peanut allergy — anaphylactic</mark>, not a preference.
>
> **Assistant:** Understood — no meat, and peanuts are a hard exclusion. Any cuisine you lean towards?
>
> **User:** <mark class="hl hl-facts">Indian, usually. Paneer dishes especially.</mark> And I'd <mark class="hl hl-facts">rather not spend more than about 40 euros a head</mark>.

The deriver made one call for the session, with the prompt shown above, and stored six explicit rows:

<!-- BEGIN S1_ROWS -->
```text
[2026-03-14 12:02:00] Anton is planning a dinner in Berlin for the week of March 21, 2026.
[2026-03-14 12:02:00] Anton has followed a strict vegetarian diet for eight years.
[2026-03-14 12:02:00] Anton has a severe, anaphylactic peanut allergy.
[2026-03-14 12:02:00] Anton prefers Indian cuisine.
[2026-03-14 12:02:00] Anton prefers dishes containing paneer.
[2026-03-14 12:02:00] Anton has a budget of approximately 40 euros per person for the dinner.
```
<!-- END S1_ROWS -->

Each row has `Anton` as its subject and is stamped 12:02, the time of the session's last message. Two times went wrong. "Next week", said on Saturday 14 March, became "the week of March 21", a Saturday. "For eight years" stayed relative: in July, it no longer says when the diet began. The other two runs differed in exactly these places ("since 2018"; "the week of March 16th"; "in the week following 2026-03-14"). The sister's visit, the reason for the dinner, was not stored in this run.

### Dream 1: a deduction, a pattern and a peer card

The first dream ran on these six rows. The deduction agent took four rounds:

1. `get_recent_observations` with a limit of 20, which returned all six rows;
2. `create_observations_deductive` with two conclusions;
3. `update_peer_card`;
4. `DONE`.

It never searched: the six rows were all there was. Its two conclusions:

```text
Anton requires a peanut-free restaurant for his dinner in Berlin.
    - Anton has a severe, anaphylactic peanut allergy.
Anton is likely to order vegetarian Indian food featuring paneer during his dinner.
    - Anton has followed a strict vegetarian diet for eight years.
    - Anton prefers Indian cuisine.
    - Anton prefers dishes containing paneer.
```

The first follows from its premise. The second is a prediction, with "likely" in it, stored at the level whose prompt asks for "logical implications". And the peer card:

```text
IDENTITY: Name: Anton
ATTRIBUTE: Diet: Vegetarian
ATTRIBUTE: Allergy: Peanuts
ATTRIBUTE: Cuisine Preference: Indian
```

The card's rule is that a value which "plausibly changes within six months absent a deliberate announcement" does not belong on it. The agent judged a diet stable enough. The card, like the rows, now says "Vegetarian".

The induction agent took three rounds and wrote one pattern from three sources: *"Anton consistently prioritizes vegetarian options that include paneer when selecting meals"*, confidence "medium" (the prompt's rule also says medium for three sources).

After dream 1, the outdated fact supports three things: a deduction, a pattern and a line on the peer card.

### Session 2: the old value and the new one, side by side

> **User:** Small update on the food thing — I <mark class="hl hl-facts">started eating fish about a month ago</mark>. So I'm <mark class="hl hl-facts">pescatarian now</mark>, not vegetarian. <mark class="hl hl-facts">Still no meat</mark>, and the <mark class="hl hl-facts">peanut situation obviously hasn't changed</mark>.
>
> **Assistant:** Noted, fish is in. Anything else shifted?
>
> **User:** I <mark class="hl hl-facts">moved to Kreuzberg in May</mark>, so anything walkable from there is a plus.
>
> **Assistant:** Kreuzberg, noted. Anything else for next time?
>
> **User:** Yes — my <mark class="hl hl-facts">sister Lena is coming back in the autumn</mark>, and she's <mark class="hl hl-facts">bringing her partner, Jonas</mark>.
>
> **Assistant:** Lovely. Anything I should know about what they eat?
>
> **User:** <mark class="hl hl-facts">Lena can't eat shellfish, and Jonas is coeliac</mark>.

One deriver call, ten rows:

<!-- BEGIN S2_ROWS -->
```text
[2026-07-20 12:06:00] Anton started eating fish in June 2026.
[2026-07-20 12:06:00] Anton identifies as a pescatarian as of July 2026.
[2026-07-20 12:06:00] Anton does not eat meat.
[2026-07-20 12:06:00] Anton has a peanut allergy.
[2026-07-20 12:06:00] Anton moved to Kreuzberg in May 2026.
[2026-07-20 12:06:00] Anton has a sister named Lena.
[2026-07-20 12:06:00] Anton's sister Lena is returning in the autumn of 2026.
[2026-07-20 12:06:00] Anton's sister Lena is bringing her partner Jonas.
[2026-07-20 12:06:00] Anton's sister Lena is unable to eat shellfish.
[2026-07-20 12:06:00] Anton's sister's partner Jonas is coeliac.
```
<!-- END S2_ROWS -->

The relative times were resolved: "about a month ago" became June 2026, and "now" became "as of July 2026". The deriver did not see session 1, so nothing marks the diet as a change. The store now holds both values as explicit rows, March's and July's, each true when it was said. The peanut allergy is stored a second time, as the saving rules require for different sessions.

### Dream 2: the update, and what stayed

The second dream is where the change is handled. The deduction agent took five rounds.

**Round 1:** `get_recent_observations`, limit 20. The store held 19 live rows, so it saw all of them, old and new (the result is shown above, in "What a tool returns").

**Round 2:** two deductions.

```text
Anton transitioned from a vegetarian diet to a pescatarian diet in June 2026.
    - Anton has followed a strict vegetarian diet for eight years (as of March 2026).
    - Anton started eating fish in June 2026.
    - Anton identifies as a pescatarian as of July 2026.
Anton resides in Berlin, specifically the Kreuzberg district.
    - Anton is planning a dinner in Berlin for the week of March 21, 2026.
    - Anton moved to Kreuzberg in May 2026.
```

The first is the update the prompt asks for, dated by its sources to 20 July. Its first premise is not the stored text: the model added "(as of March 2026)", and the premise text is whatever the model writes.

**Round 3:** `delete_observations` on one row, the outdated fact.

**Round 4:** the peer card, with "Diet: Pescatarian" and a new line, "Location: Berlin, Kreuzberg".

**Round 5:** `DONE`.

The induction agent took four rounds. Its first write had two patterns. One of them failed the check on ids: the model had joined four ids into one string, so none of them resolved, and the tool answered "Failed 1: … source_ids do not resolve to existing observations". The agent sent that pattern again, correctly, in the next round. The other pattern of that first write was this:

```text
[high] Anton has a consistent preference for vegetarian cuisine, specifically Indian dishes containing paneer.
    - Anton prefers Indian cuisine.
    - Anton prefers dishes containing paneer.
    - Anton consistently prioritizes vegetarian options that include paneer when selecting meals.
```

It was written after the update, in the same dream. Its third source is dream 1's pattern, which still said "vegetarian". The deletion had removed the explicit fact but not the pattern built on it, and the induction agent, which reads the newest rows, built a new pattern on the old one. Then the saving rules found the two patterns near-identical (distance 0.05 or less) and kept the richer text: the new pattern replaced dream 1's, and inherited its count (`times_derived` 2). Its confidence is "high", from three sources; the prompt's rule says medium.

{% include diagram.html name="honcho-retire" alt="The first server run, after dream 2. The explicit row 'Anton has followed a strict vegetarian diet for eight years' was deleted. Three conclusions cite it. The update, 'Anton transitioned from a vegetarian diet to a pescatarian diet in June 2026', cites it on purpose. 'Anton is likely to order vegetarian Indian food featuring paneer during his dinner' is still live and carries the old value. Dream 1's pattern 'consistently prioritizes vegetarian options' was replaced by a near duplicate written in dream 2, after the update: 'a consistent preference for vegetarian cuisine', confidence high, derived twice, which cites the old pattern. The peer card was rewritten from Vegetarian to Pescatarian. Bottom: a dream's delete stamps only the rows it names; removing a session from a scope deletes every derived row with a deleted source, repeatedly, and would delete all three live rows here, the update included." caption="What happened to the vegetarian fact and to what rested on it, in the first server run. The fact was deleted; a deduction drawn from it stayed live, and a new pattern was built on an old one." %}

After dream 2, two live conclusions rest on the deleted fact or on a row derived from it:

- *"Anton is likely to order vegetarian Indian food featuring paneer during his dinner"*, which cites the deleted fact;
- *"Anton has a consistent preference for vegetarian cuisine…"*, which cites the replaced pattern, which cited the deleted fact.

Both carry the old value as if it were current, and nothing in either row says otherwise. The links say it: following them from either row reaches a deleted row in one or two steps.

**The other two runs.** All three second dreams wrote an update:

| Run | Update written | Deleted by the deduction agent | Live conclusions that still say "vegetarian" |
|---|---|---|---|
| 1 | "transitioned from a vegetarian diet to a pescatarian diet in June 2026" | the outdated fact | a deduction and a pattern |
| 2 | "pescatarian, updating from vegetarian" | *"Anton does not eat meat"* (still true) | the outdated fact itself, a deduction and a pattern |
| 3 | "changed from strictly vegetarian to pescatarian" | the outdated fact, and *"Anton does not eat meat"* | a deduction and a pattern |

Two of the three runs deleted a fact that had not changed. The user said "Still no meat" in July; the agent read "does not eat meat" as part of the old diet. Run 2 kept the outdated fact and deleted the true one. In every run, conclusions drawn from the old value stayed live.

### Session 3: the two read paths

> **User:** My sister and her partner are in town tonight. Book the three of us somewhere for dinner — you know what we can and can't eat.

**The representation** returned every live conclusion, since there were fewer than 100, grouped by level and dated:

<!-- BEGIN REPRESENTATION -->
```markdown
## Explicit Observations

[2026-03-14 12:02:00] Anton is planning a dinner in Berlin for the week of March 21, 2026.
[2026-03-14 12:02:00] Anton prefers Indian cuisine.
[2026-03-14 12:02:00] Anton has a budget of approximately 40 euros per person for the dinner.
[2026-03-14 12:02:00] Anton has a severe, anaphylactic peanut allergy.
[2026-03-14 12:02:00] Anton prefers dishes containing paneer.
[2026-07-20 12:06:00] Anton has a sister named Lena.
[2026-07-20 12:06:00] Anton's sister Lena is bringing her partner Jonas.
[2026-07-20 12:06:00] Anton identifies as a pescatarian as of July 2026.
[2026-07-20 12:06:00] Anton moved to Kreuzberg in May 2026.
[2026-07-20 12:06:00] Anton does not eat meat.
[2026-07-20 12:06:00] Anton has a peanut allergy.
[2026-07-20 12:06:00] Anton's sister's partner Jonas is coeliac.
[2026-07-20 12:06:00] Anton's sister Lena is returning in the autumn of 2026.
[2026-07-20 12:06:00] Anton's sister Lena is unable to eat shellfish.
[2026-07-20 12:06:00] Anton started eating fish in June 2026.

## Deductive Observations

[2026-03-14 12:02:00] Anton requires a peanut-free restaurant for his dinner in Berlin.
   Premises:
   - Anton has a severe, anaphylactic peanut allergy.

[2026-03-14 12:02:00] Anton is likely to order vegetarian Indian food featuring paneer during his dinner.
   Premises:
   - Anton has followed a strict vegetarian diet for eight years.
   - Anton prefers Indian cuisine.
   - Anton prefers dishes containing paneer.

[2026-07-20 12:06:00] Anton transitioned from a vegetarian diet to a pescatarian diet in June 2026.
   Premises:
   - Anton has followed a strict vegetarian diet for eight years (as of March 2026).
   - Anton started eating fish in June 2026.
   - Anton identifies as a pescatarian as of July 2026.

[2026-07-20 12:06:00] Anton resides in Berlin, specifically the Kreuzberg district.
   Premises:
   - Anton is planning a dinner in Berlin for the week of March 21, 2026.
   - Anton moved to Kreuzberg in May 2026.


## Inductive Observations

 **Pattern** [high]: Anton has a consistent preference for vegetarian cuisine, specifically Indian dishes containing paneer.
   **Type**: preference
   **Sources**:
   - Anton prefers Indian cuisine.
   - Anton prefers dishes containing paneer.
   - Anton consistently prioritizes vegetarian options that include paneer when selecting meals.

 **Pattern** [medium]: Anton is highly attentive to dietary restrictions, both his own and those of others in his social circle.
   **Type**: behavior
   **Sources**:
   - Anton has a peanut allergy.
   - Anton has a severe, anaphylactic peanut allergy.
   - Anton's sister Lena is unable to eat shellfish.
   - Anton's sister's partner Jonas is coeliac.
```
<!-- END REPRESENTATION -->

The explicit level is current: the old row is gone, and the row with the new value is there with its date. The deductive level has the update, dated 20 July, and also *"likely to order vegetarian Indian food"*, dated 14 March. The inductive level has two patterns; the one about the diet is the stale one, marked "high". Patterns are printed with no date at all, so an answering model cannot tell that this one is older than the update.

**The dialectic** made one call and no tool calls: the 25 + 25 conclusions of its prefetch were all it used. Its prefetch held the same rows as the representation, in order of similarity, with ids and premises for the derived ones. Its reply:

<!-- BEGIN CHAT -->
> I cannot book a reservation for you, but I have compiled the necessary dietary requirements to help you choose a suitable place in Kreuzberg:
>
> To accommodate your group tonight, any restaurant you select must be able to handle these specific restrictions:
>
> *   **Anton (You):** Pescatarian, severe anaphylactic peanut allergy.
> *   **Lena (Sister):** No shellfish.
> *   **Jonas (Partner):** Coeliac (requires strictly gluten-free options/cross-contamination awareness).
>
> Given your strong preference for Indian cuisine and your interest in paneer-based dishes, searching for an Indian restaurant in Kreuzberg that explicitly offers gluten-free options and is highly rated for allergy awareness (specifically for peanuts and shellfish) would be the best approach.
>
> Please let me know if you would like me to search for any specific restaurants in the area that meet these criteria.
<!-- END CHAT -->

All six needs are there: pescatarian, the peanut allergy, shellfish for Lena, gluten-free for Jonas, Indian food and Kreuzberg. The replies of the other two runs also said "Pescatarian"; the second added that "you transitioned to a pescatarian diet in June 2026". On this store, the dialectic chose the update over the stale rows. The experiment, below, shows the case where two values of a fact reach it with nothing to choose between them.

### What the links make possible

The notebook for this part runs the same pipeline with Honcho's prompts and tools, from short local functions, and prints every step. Its run behaved like the server runs: dream 2 wrote an update, deleted the outdated fact and, as in run 3, the true *"Anton does not eat meat"*, and left two conclusions that cite the deleted fact. It then does three things that Honcho does not.

**It lists what rests on a deleted row.** Following the links from the deleted rows takes a few lines, and gives an exact list of five: the two stale conclusions; the two deductions about the change, which cite the old fact on purpose; and a pattern built on one of those. Honcho's scope rule, applied to this list, would delete all five, the update included, because it fails closed. A rule that keeps a conclusion while any of its sources still holds would keep all five, the stale ones included, because each of them also cites a fact that is still true. One rule is too strict and the other too lenient. What the links give is the list itself, computed by code, without asking a model; deciding what to do with each row on it is a further step.

**It checks the rules the prompts state.** In the notebook's run the induction agent wrote "medium" for two patterns with two sources each, where the prompt's rule says "low". A rule that a conclusion may only cite rows of a lower level takes a few more lines; it would have refused run 1's pattern, which cites another pattern.

**It shows what the missing level would write.** Asked for "the most plausible explanation" of the store, with a prompt of the notebook's own, the model wrote that Anton's change of diet "was likely motivated by a desire to simplify his complex social dining planning". Nobody said that. Honcho's documentation describes this kind of reasoning as part of the system; the code of 3.3.0 does not do it.

### What it costs

Calls and input tokens of the first server run, by step:

| Step | Model calls | Tokens in | Tokens out |
|---|--:|--:|--:|
| Deriver, session 1 | 1 | 923 | 155 |
| Dream 1, deduction | 4 | 11,385 | 248 |
| Dream 1, induction | 3 | 4,302 | 158 |
| Deriver, session 2 | 1 | 1,115 | 243 |
| Dream 2, deduction | 5 | 18,321 | 366 |
| Dream 2, induction | 4 | 8,941 | 503 |
| **Writing, total** | **18** | **44,987** | **1,673** |
| Dialectic (the answer's context) | 1 | 4,598 | 181 |

Writing also made 9 embedding calls, in batches: the server embeds new rows and the messages when it saves them, and each search query. The other two runs took 17 and 19 model calls and 41,552 and 45,737 tokens to write. The notebook's run took 19 model calls and 49,766 tokens.

{% include diagram.html name="honcho-cost" alt="Nineteen bars, one per model call of the first server run, grouped by step. The deriver read 923 tokens for session 1 and 1,115 for session 2. Dream 1: the deduction agent's four rounds read 2,460 to 3,069 tokens, the induction agent's three 1,028 to 1,705. Dream 2: the deduction agent's five rounds read 2,551 to 4,069, the induction agent's four 1,028 to 2,861. In every round of an agent, the part equal to its first round is sent again; the rest is what it has read since. The dialectic's one call read 4,598 tokens. In all, 49,585 tokens, 44,987 of them for writing." caption="Input tokens of every model call in the first server run. The deriver reads about a thousand tokens per session; each round of a dream agent sends its instructions again, plus everything it has read so far." %}

The deriver is cheap: about a thousand tokens per session, most of them the prompt's rules. The dream is where the cost is. Each round sends the agent's instructions and tool descriptions again (the first deduction call read 2,460 tokens before it had seen a single conclusion), plus every tool result so far, so the later rounds of an agent read the most. The second dream cost more than the first because its tool results were longer and its agents took more rounds. Both dreams asked for the newest twenty rows, and in both the store was smaller than that, so each read the whole store; by the second dream it had grown to nineteen rows.

For the same two sessions, the systems in the other parts of this series used:

- textual memory: 2 model calls, 916 tokens read;
- Mem0: 2 model calls and 4 embedding calls, 16,862 tokens read;
- Zep/Graphiti: 38 model calls and 25 embedding calls, 60,374 tokens read;
- Letta: the in-line agent, which writes inside its replies, 17 model calls and 47,677 tokens for seven user turns; its sleep-time agent, which does the pipelines' job, 4 calls and 12,775 tokens.

Honcho is near Graphiti and Letta in tokens and second to Graphiti in calls, and most of its write cost is in a separate job after the conversation, which the application can schedule. Textual memory and Letta's sleep-time agent also write after the conversation, but in one or a few calls. The size of the store does not drive that cost; the number of dreams and of agent rounds does.

## Where it breaks

The larger experiment of this series ran the same server on 67 questions from the LongMemEval benchmark, each about a fact that the user stated and later changed, in a history of about ten sessions. One store was built per question, with one dream after the whole history, and read through both paths. [Part 8][part-8] has the accuracies. The failures below are what the stores and the replies show, from the [findings][findings] and from the stores themselves.

{% include diagram.html name="honcho-window" alt="Top: one benchmark store, 114 explicit conclusions from oldest to newest. The dream's agents asked for the newest twenty. The old value of the question, '20 titles', is row 48; the new value, '25 titles', is row 88: both outside the twenty. The dream wrote three deductions and two patterns, about sleep, glaciology and journalism, the topics of the newest rows. Bottom: in the 41 stores where both values could be located, the newest twenty rows held both values in none, the new value only in 21, the old value only in 3, and neither in 17. Across all 67 stores: 7,434 explicit conclusions, 158 deductive, none of which records a change, 146 inductive, and no contradictions." caption="What a dream agent looked at in a benchmark store, against where the old and new values were; and what the 67 stores held, by level." %}

**Failure 1: the dream rarely sees both values.** The 67 stores hold 7,434 explicit conclusions, about 111 per question; 158 deductive and 146 inductive ones, about two of each per question; and no contradiction. I read all 158 deductive conclusions. None records that a value changed. (Two say "contradictory", written as deductions.) The old value was still stored, and still read as current, in most of the questions.

The example shows why. A dream agent sees what its tools return. In the example it asked for the newest twenty rows, and twenty rows were the whole store, old value included. In a benchmark store, the newest twenty are the last session or two, and the old value was said several sessions earlier.

I located both values by their text in 41 of the 67 stores. In none of the 41 were both among the newest twenty explicit rows; the new value alone was there in 21, the old value alone in 3, and neither in 17.

To see both, an agent would have to search, and in the experiment's cached replies the dream agents never called `search_memory`. They called `get_recent_observations`, mostly with a limit of 20, wrote what they saw, and stopped. In all the dreams of the experiment's runs, the cache holds 13 calls of `delete_observations`, which deleted 18 rows in total. (The cache keeps each distinct reply once, across all runs of the experiment, so this is an estimate of the order of magnitude, not a count per question.)

So on the benchmark, Honcho's handling of a changed fact was not the dream's update but the explicit rows' timestamps: both values stayed, each with the minute it was said, and the read path had to choose.

**Failure 2: the dialectic asks the user instead of answering.** When the dialectic agent found two values, it often wrote the conflict up as a question. For "How many titles are currently on my to-watch list?", both "20 titles" (20 May) and "25 titles" (22 May) were stored. The dialectic's reply:

> Based on your conversation history, there is contradictory information regarding the number of titles on your to-watch list:
>
> *   On **May 20, 2023**, it was noted that your list consisted of **20 titles**.
> *   On **May 22, 2023**, it was noted that your list consisted of **25 titles**.
>
> I do not have information confirming whether your list was updated or if one of these figures was recorded in error. Which of these numbers is correct?

The answering model, given this reply as the memory, declined too. The representation path, on the same store, handed over both lines with their times, and its answer took the later one. In five of the chat path's nine wrong answers, the dialectic had written two values up as a conflict, or as unconfirmed, and the answer declined. "Where did Rachel move to after her recent relocation?" got "Could you clarify which of these locations is correct?"; "What time do I wake up on Saturday mornings?" got "Which of these times is correct?".

This is the dialectic prompt doing what one of its sections says. "HANDLING CONTRADICTORY INFORMATION" tells the agent to present both values and "Ask the user which statement is correct"; "HANDLING UPDATED INFORMATION" tells it that the more recent statement supersedes. Two values of one fact, a few days apart, fit both descriptions, and the agent often chose the first. Its reply goes to a program, which cannot answer the question.

Honcho's own workspace-level agent, in the same file, has a section titled "NO CLARIFYING QUESTIONS" for exactly this reason: "Your answer goes to a program, not to someone who can reply."

The pair-level dialectic of 3.3.0 does not. Version 3.5.0 (released 30 October 2026, after the experiment) changed it: the dialectic "answers as a single turn", and "Answers no longer end with an offer or a question the caller can't reply to ('If you want, I can…', 'Which statement is correct?')", while "contradictions in memory are still reported".

{% include diagram.html name="honcho-conflict" alt="A benchmark question: 'How many titles are currently on my to-watch list?' The store holds two explicit conclusions: 20 titles, said on 20 May at 10:21, and 25 titles, said on 22 May at 03:29. Left, the representation hands both dated lines to the answering model, which answers: 'The most recent record… is from May 22, 2023, which states the list consists of 25 titles.' Correct. Right, the dialectic's prompt has two rules for this case: ask the user which statement is correct, and the more recent statement supersedes. Its reply lists both values and ends 'Which of these numbers is correct?'. The answering model, given that reply, answers that it is not possible to determine the number. Five of the dialectic path's nine wrong answers were of this kind. Honcho 3.5.0 later made the dialectic answer in a single turn." caption="One store, two read paths, in the experiment. The representation hands both dated values to the answering model, which takes the later one. The dialectic's prompt has two rules for the same case, and its reply often asks which value is correct." %}

**Failure 3: guesses filed as deductions.** The deduction prompt asks for "logical implications", with the example `"has kids ages 5 and 8" → "is a parent"`. Many of the benchmark's deductive rows are plausible readings instead:

- *"user is currently pregnant"*, drawn from *"user is interested in obtaining more information regarding step 3 of the management of symptoms for an eight-week pregnancy"*, which could equally be a question for someone else;
- *"user is a dancer"*, from attending dance classes on Tuesdays;
- *"user is currently managing digestive health concerns, possibly related to dairy sensitivity"*, with "possibly" in a deduction.

In the example, *"likely to order vegetarian Indian food"* is the same kind of row. Each is stored at the level the dialectic is told to treat as following from the facts, and it is shown to every later read. Some of these rows are about health, which makes a wrong inference more than an accuracy problem: the memory now holds a sentence about the person that they never said.

**Failure 4: extraction keeps the value and drops the context.** The deriver's rows are short and literal, and the qualifier that decides a question is sometimes not in them. "My new 70-200mm zoom lens" became *"user owns a 70-200mm zoom lens"*, while an earlier *"user recently acquired a 50mm prime lens"* kept its "recently", and the representation's answer to "What type of camera lens did I purchase most recently?" was the 50mm. In another history, the user first said they had misplaced a screwdriver and would buy one, and four days later that they had a spare; the second statement produced no conclusion, and both read paths answered that there was no evidence of a spare.

### How to notice and fix these failures

**Read the store by level.** The derived levels are small enough to read in full, two or four rows per history in the experiment. Read each deduction with its premises and ask whether it follows. A word like "likely" or "possibly" in a deductive row is a guess at the wrong level.

**List what rests on deleted rows.** The links are in a table, so the question is one query:

```sql
SELECT d.id, d.level, d.content
FROM documents d
JOIN document_sources l ON l.derived_id = d.id
JOIN documents s ON s.id = l.source_id
WHERE d.deleted_at IS NULL AND s.deleted_at IS NOT NULL;
```

In the first server run it returns the stale deduction, the stale pattern and the update; in the third, two deductions, a pattern and the update. In the second, where the agent deleted the true row and kept the outdated fact, it returns only the update: the stale rows there rest on a row that is still live, and no query over the links can find them. A non-empty result after a dream is a list of conclusions to review; an empty one does not prove that nothing is stale.

**Compare the two read paths** on questions whose answer changed. Where the dialectic declines and the representation answers, the memory had the value and the read path lost it.

**Fixes, each small:**

- **Act on the list above.** After a dream's deletes, give the rows that cite a deleted row back to the deduction agent to rewrite or delete, or mark them stale so that the read paths can leave them out. The walk already exists in Honcho's code, for scopes.
- **Show the dream both values.** The deriver knows which rows it has just written. Passing them to the deduction agent as topics, so that its first step is a search for each one and not the newest twenty, puts the old value in view. Honcho's agents already accept such topics, as "hints".
- **Compute what the prompt asks the model to count.** Confidence from the number of sources; the minimum of two sources; a contradiction level written by its own tool.
- **Give the dialectic one rule for two values:** the newer one wins and the older one is mentioned, as 3.5.0 now does. Or read through the representation, whose dated lines let the answering model choose.
- **Date the patterns.** The representation prints a time for explicit and deductive rows, but not for inductive ones.

## When a background reasoner is the right design

**Use it when:**

- the answers depend on what follows from what the user said, not only on what they said: habits, constraints that combine, the reasons behind a request;
- conversations are long and many, so that dreams have something to work on, and their cost can be spent off the user's path;
- you need to know why the memory believes something: every derived row names its sources, and the dialectic can follow them;
- you will act on the links, for example to withdraw what rested on a fact that changed, or on a session the user deleted.

**Do not use it when:**

- the job is "remember what I said and use the newest value". The explicit level with its timestamps does that, and the rest of the machinery adds cost and rows that can go stale;
- you cannot afford to store sentences about a person that nobody said, or to review them;
- histories are short and dreams would rarely run: then Honcho is an extractor with timestamps.

**The read path is a separate decision.** On the same store, the representation gave the answering model dated lines and let it choose, and the dialectic sometimes chose not to answer. Pick the read path by what the consumer can do with it: a program needs an answer or the evidence, never a question.

## History and related work

**Generative Agents.** [Generative Agents][generative-agents] (2023) kept every perception of a simulated character in a "memory stream" of natural-language records, and added *reflections*: when the summed importance of recent events passed a threshold, the agent asked itself three questions about its last 100 records, retrieved evidence for each, and wrote insights that cite the records they came from. Reflections could build on reflections, forming trees (p. 10). Removing reflection made the characters' answers in interviews worse (p. 14). Honcho's dream is a reflection pass with types: its levels say what kind of insight a row is, and its links are the citations.

**Violation of expectation.** Plastic Labs' earlier paper, [Violation of Expectation via Metacognitive Prompting][voe] (2023), ran on Bloom, a tutoring chatbot. The model predicted the user's next message, compared the prediction with what the user actually wrote, and stored facts about the user derived from the difference; a later prediction retrieved them (p. 3). With the stored facts, the predictions of GPT-4, OpenAI's model that ran the whole system, were rated "wrong" less often, 33% against 43% of messages (p. 4, Fig. 2), on one deployment, with GPT-4 also acting as the judge. The idea that memory of a person is built by reasoning about them, and not by recording, is the one Honcho is built on. Honcho 3.3.0 has an optional step with a similar name, surprisal, but it measures distance in embedding space, not the error of a prediction.

**Belief revision.** When a fact changes, what else must change? [Fundamental Problems With Model Editing][model-editing] (2024) asks this of facts stored in a model's weights, and builds a test with known dependencies between facts. After an edit, the edited fact itself was right, but accuracy on facts that depend on it, and should change with it, fell from 0.97 to 0.01 (p. 14, Table 4). The same gap appears in Honcho's store: the edited fact changed, and what was concluded from it did not. [Belief Memory][belief-memory] (2026) argues that storing one conclusion per observation leads to "self-reinforcing error", where an agent acts on the stored conclusion and stops testing the alternatives; it keeps several candidates per attribute, each with a probability (pp. 1–6).

**Honcho's own history.** Honcho has no paper; its changelog dates the design.

- **Version 2.4.0 (9 October 2025)** added dreaming as a "WIP Dreaming Feature" (WIP: work in progress).
- **Version 3.0.0 (19 January 2026)** made the dreamer agentic ("Agentic Dreamer for intelligent memory consolidation using LLM agents") and added the reasoning levels of the dialectic.
- **Version 3.0.12 (10 August 2026)** kept explicit rows tied to their session and dated derived rows to their latest source.
- **Version 3.1.0 (25 August 2026)** added scopes, and with them the walk that deletes derived rows whose sources left a scope.
- **Version 3.2.0 (15 September 2026)** stripped invented source ids before saving.
- **Version 3.3.0 (9 October 2026)** is the one described here.
- After the experiment, **3.5.0** (released 30 October 2026) changed the dialectic to answer in a single turn, and made explicit rows cite the messages they came from; **3.6.0** (10 November 2026) records each dream as a run, listing what it created, with sources, and what it removed.

Plastic Labs' hosted service uses its own models; its documentation names one, Neuromancer XR, as "the explicit reasoning model". The runs in this post used a general small model in every role.

## Run it yourself

The [notebook][notebook] for this post drives Honcho's own prompts and tool descriptions from short local functions. Everything the model is told is Honcho's text, fetched from Honcho's repository at the commit of 3.3.0, and checked against the requests the real server sent for this conversation: with the same inputs, every prompt and tool description is identical. The rules are written out as plain Python: what is saved and merged, what each tool returns, the grounding check, and how the two read paths choose conclusions. Then it adds what Honcho does not: the walk over the links, the checks that are only requested in prompts, and a level for explanations.

I re-implemented the loop rather than only running the server so that every step could be printed and changed. Four things are simpler than on the server, and none changes what the notebook shows: the model runs at temperature 0, so that a rerun gives similar replies (the server leaves the temperature to the provider); the store is a dictionary; the dreams are started by hand; and "richer text" counts words where Honcho counts tokens. The three server runs in this post are separate, at the server's settings.

I used `gemini-3.1-flash-lite` for every role. It is available on the free tier of the Gemini API, which is enough for the few dozen calls that the notebook makes. All systems in this series use the same model, so that differences in their results come from their designs.

Even at temperature 0, model replies vary between runs and between versions of a model. A rerun of the notebook can differ in details from what is shown above, such as the wording of a conclusion or what a dream changes, and a different model can change more. The mechanism stays the same.

The larger experiment ran the real Honcho server, with one store per question and both read paths. [Part 8][part-8] describes it, and the code is in the same [repository][repo].

Here are a few experiments worth trying in the notebook:

- Run one dream after both sessions, as the experiment did. Does the update still happen when the old value is not among the newest rows?
- Pass the rows that the deriver has just written to the deduction agent as hints. Does its first step become a search, and does it find the old value?
- After dream 2, give the rows that cite a deleted row back to the deduction agent. What does it do with each one?
- Remove the section on contradictory information from the dialectic's prompt, store two values of one fact a few days apart, and ask for it.
- Say the change less directly: "grabbed some salmon last night, been doing that a lot lately". Does dream 2 still write an update?

## References

<!-- REFS -->

Papers:

- Park et al., [Generative Agents: Interactive Simulacra of Human Behavior][generative-agents] (2023)
- Leer et al., [Violation of Expectation via Metacognitive Prompting Reduces Theory of Mind Prediction Error in Large Language Models][voe] (2023)
- Hase et al., [Fundamental Problems With Model Editing: How Should Rational Belief Revision Work in LLMs?][model-editing] (2024)
- Liao et al., [Belief Memory: Agent Memory Under Partial Observability][belief-memory] (2026)

<!-- /REFS -->

Other sources:

- Plastic Labs, [Honcho on GitHub][honcho-repo], and [the source at 3.3.0][honcho-330]: [the deriver's prompt][honcho-deriver], [the dream's specialists][honcho-specialists], [the agents' tools][honcho-tools], [the dialectic's prompt][honcho-dialectic]
- Plastic Labs, [Honcho's documentation on reasoning][honcho-reasoning] and [on dreaming][honcho-dreaming]
- Plastic Labs, [release notes of Honcho 3.5.0][honcho-350]

[generative-agents]: https://arxiv.org/abs/2304.03442
[voe]: https://arxiv.org/abs/2310.06983
[model-editing]: https://arxiv.org/abs/2406.19354
[belief-memory]: https://arxiv.org/abs/2605.05583
[honcho-repo]: https://github.com/plastic-labs/honcho
[honcho-330]: https://github.com/plastic-labs/honcho/tree/608aec8a928da13c540262ed980c569448fb53ab
[honcho-deriver]: https://github.com/plastic-labs/honcho/blob/608aec8a928da13c540262ed980c569448fb53ab/src/deriver/prompts.py
[honcho-specialists]: https://github.com/plastic-labs/honcho/blob/608aec8a928da13c540262ed980c569448fb53ab/src/dreamer/specialists.py
[honcho-tools]: https://github.com/plastic-labs/honcho/blob/608aec8a928da13c540262ed980c569448fb53ab/src/utils/agent_tools.py
[honcho-dialectic]: https://github.com/plastic-labs/honcho/blob/608aec8a928da13c540262ed980c569448fb53ab/src/dialectic/prompts.py
[honcho-reasoning]: https://github.com/plastic-labs/honcho/blob/608aec8a928da13c540262ed980c569448fb53ab/docs/v3/documentation/core-concepts/reasoning.mdx
[honcho-dreaming]: https://github.com/plastic-labs/honcho/blob/608aec8a928da13c540262ed980c569448fb53ab/docs/v3/documentation/features/advanced/dreaming.mdx
[honcho-350]: https://github.com/plastic-labs/honcho/releases/tag/v3.5.0
[repo]: https://github.com/anton-dergunov/agent-memory-eval
[notebook]: https://anton-dergunov.github.io/agent-memory-eval/notebooks/05-honcho.html
[findings]: https://github.com/anton-dergunov/agent-memory-eval/blob/main/docs/findings/honcho.md
[part-8]: /posts/2199/01/agent-memory-8-experiment/
