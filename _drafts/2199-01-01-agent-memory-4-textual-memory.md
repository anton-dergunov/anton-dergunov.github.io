---
title:     "How LLM agents remember, part 4: textual memory, one profile rewritten"
topic:     llms-and-agents
date:      2199-01-01
permalink: /posts/2199/01/agent-memory-4-textual-memory/
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
4. **Textual memory: one profile, rewritten** (this part)
5. [Mem0: facts in a vector store](/posts/2199/01/agent-memory-5-mem0/)
6. [Zep and Graphiti: facts with dates, in a graph](/posts/2199/01/agent-memory-6-graphiti/)
7. [Letta: an agent that edits its own memory](/posts/2199/01/agent-memory-7-letta/)
8. [Honcho: a reasoner that works in the background](/posts/2199/01/agent-memory-8-honcho/)
9. [The experiment: 67 changed facts](/posts/2199/01/agent-memory-9-the-experiment/)

<!-- /SERIES -->

The running example of this series: in March a user tells an assistant they
are strictly vegetarian and have a severe peanut allergy; in July they say
they eat fish now, have moved to Kreuzberg, and that their sister Lena (no
shellfish) is coming with her partner Jonas (coeliac); in September they ask
the assistant to book dinner for the three of them, "you know what we can and
can't eat" ([part 1](/posts/2199/01/agent-memory-1-why/)). On the map of
[part 2](/posts/2199/01/agent-memory-2-the-map/), this part's system is a
background process that writes, and a read path that inserts everything.

## The idea

The memory is one plain-text profile of the user. After each conversation, a
separate model call reads the current profile and the new conversation and
writes the whole profile again, under a size cap. The answering model never
writes; it reads the whole profile, every time.

{% include diagram.html name="textual" alt="Textual memory's architecture, with the running example. Writing: after each session, one LLM call reads the current profile and the new session and writes the whole profile again. Memory: one text profile under four headings, 153 words after two sessions; the diet line now says pescatarian and keeps the old diet as 'previously'. Reading: no search; the whole profile goes into the prompt, and the answer covers every constraint." %}

There is no vector store, no graph, no search and no tool call. This is the
simplest design that still deserves the name memory, and it is close to what
consumer assistants ship: ChatGPT's memory is now a summary synthesised in the
background and inserted into the prompt ([part 3](/posts/2199/01/agent-memory-3-frontier-assistants/)).
It is also the baseline every other system in this series has to beat,
because each of them adds machinery to this loop.

## Where it comes from

The user portrait of [MemoryBank][memorybank] (2023) is the ancestor: next to
the raw turns and summarised events, it kept a portrait of the user
synthesised from the history. The version I ran follows the *Textual Memory*
baseline of [PersonaMem-v3][personamem-v3] (2026), a personalisation
benchmark built from real engagement histories. Its memory is one profile,
with sections for who the user is, their interests and preferences, people
and places, and what is currently going on, rewritten as the history is read
in chronological chunks and held under a 4,096-token cap. The prompt is
deliberately plain:

> You maintain a running memory of one user, updated as you read their
> activity in chronological chunks. Remember the useful parts of the user's
> persona and preferences from their activities across these apps; maintain
> the memory with ADD, EDIT, REMOVE, and MERGE actions; and the memory should
> contain only the resulting persona profile rather than a raw log of
> activity.

In that paper this baseline did something the more elaborate systems did not.
On the task that tests whether a model has noticed that a preference changed,
GPT-5.5 with textual memory scored 79.9% and used the outdated stance in 25.7%
of answers; Mem0 with retrieval scored 56.9% and used it in 51.4% (§4.3, p.
17). Its reading: "a topically relevant retrieved fact can remain too sticky
after expiry." The whole history in the prompt scored 73.1%, between the two.

Two relatives are worth knowing. [Dynamic Cheatsheet][dynamic-cheatsheet]
keeps a single self-curated document for an agent, rewritten after each task,
and shows how much of such a gain can come from the structure of the prompt
alone: on AIME, 23.3 with no cheatsheet, 36.7 with an empty one, 50.0 with a
curated one (p. 5, Table 1). [Mastra's Observational Memory][mastra-om] is the
most developed open version of the family, with two background agents that
compress and then rewrite a dated log (see part 3).

## The run

The [notebook][notebook] uses one rewrite prompt, written after the
PersonaMem-v3 description and identical to the one in the LongMemEval
experiment of [part 9](/posts/2199/01/agent-memory-9-the-experiment/). It
has a 3,000-word cap and four headings. Two of its rules do most of the work:

```text
- When the new conversation changes or contradicts something in the profile,
  replace it with the new information and record that it changed, with dates
  (for example "Now X, since 2023-05-26; previously Y").
- Write dates as absolute dates, resolving words like "last week" against the
  conversation's date.
```

The rewriter is given each session with its date, `[Session date:
2026-03-14]`, so it can resolve "next week" and "eight years". Every model
call is `gemini-3.1-flash-lite` at temperature 0, as everywhere in this
series.

### Writing: the profile after session 1

One call, about 90 words:

```text
### Personal facts
*   **Dietary restrictions:** Strictly vegetarian (since 2018).
*   **Allergies:** Severe, anaphylactic peanut allergy.
*   **Family:** Has a sister who is visiting Berlin.
*   **Location:** Currently based in or planning for Berlin.

### Preferences and habits
*   **Cuisine preference:** Indian food, specifically paneer dishes.
*   **Budget:** Prefers to spend no more than 40 euros per person for dining.

### Ongoing situations and plans
*   **Upcoming event:** Planning a dinner for a sister's visit to Berlin,
    scheduled for the week of March 16, 2026.

### Changes over time
*   None.
```

Everything from session 1 is there, and the dates were resolved: "eight
years", said in March 2026, became "since 2018", and "next week" became "the
week of March 16, 2026". Compare Mem0 in
[part 5](/posts/2199/01/agent-memory-5-mem0/), which resolved the same phrase
against the day the notebook was run. One line is a guess: "Currently based
in or planning for Berlin" is not something the user said. The rewriter
hedged, and the hedge is now part of the profile.

### Revising: the profile after session 2

The second call is given that profile and session 2, which says "pescatarian
now, not vegetarian". It does not edit the profile. It writes a new one:

```text
### Personal facts
*   **Dietary restrictions:** Pescatarian (since June 2026; previously
    strictly vegetarian since 2018).
*   **Allergies:** Severe, anaphylactic peanut allergy.
*   **Family:** Sister named Lena; her partner is named Jonas.
*   **Location:** Residing in Kreuzberg, Berlin (since May 2026).

### Preferences and habits
*   **Cuisine preference:** Indian food, specifically paneer dishes.
*   **Budget:** Prefers to spend no more than 40 euros per person for dining.
*   **Location preference:** Prefers restaurants within walking distance of
    Kreuzberg.
*   **Dietary considerations for guests:** Sister (Lena) has a shellfish
    allergy; partner (Jonas) has coeliac disease (must be gluten-free).

### Ongoing situations and plans
*   **Upcoming event:** Planning a dinner for a visit from sister Lena and her
    partner, Jonas, in the autumn of 2026.

### Changes over time
*   **Dietary status:** Now pescatarian (since 2026-06-20; previously strictly
    vegetarian since 2018).
*   **Location:** Moved to Kreuzberg, Berlin (since 2026-05-01; previously
    based in or planning for Berlin generally).
```

**The vegetarian line is gone, and its history is not.** There is one current
diet in the profile, with the old one in a "previously" clause, and the change
recorded again with a full date: "about a month ago", counted back from 20
July, is 20 June. This is the step the other systems in this series handle
with machinery: Mem0 only adds, Graphiti closes an edge, Honcho marks a row as
replaced. Here it is one sentence in a prompt.

The rewrite also did four things nobody asked for, and they are the
character of this design:

- **It added precision.** "I moved to Kreuzberg in May" became "since
  2026-05-01". The first of May is a guess, written down as a date.
- **It reworded a constraint.** "Lena can't eat shellfish" became "has a
  shellfish allergy". For a booking the difference does not matter; for a
  question about why, it does. Letta's agent made the same change
  ([part 7](/posts/2199/01/agent-memory-7-letta/)).
- **It kept the history of its own guess.** "Previously based in or planning
  for Berlin generally" records the hedge from session 1 as if the user had
  said it.
- **It dropped the March dinner.** The plan for "the week of March 16" was
  replaced by the autumn visit. Here that is right; the March dinner is over.
  It is also the kind of thing a rewrite can lose without saying so, because
  nothing outside the model decides what is still true.

The lines that did not change in the conversation (the allergy, the cuisine,
the budget) survived word for word. Nothing guarantees that. Every line of the
profile was written by the model twice.

### Reading: the whole profile, no search

The question goes in with the profile as it is, and today's date:

```text
I have booked a table for three at **Chutnify (Kreuzberg)** for tonight,
September 1st, at 19:30.

*   **Why:** They offer excellent Indian cuisine with plenty of paneer options.
*   **Safety:** They are well-versed in handling allergies. I have noted the
    **peanut allergy** (you), **shellfish allergy** (Lena), and **coeliac
    disease** (Jonas) in the reservation.
*   **Budget:** Well within your 40€/person limit.
*   **Location:** Located in Kreuzberg, within walking distance.
```

Every constraint reached the answer: the peanut allergy, Lena's shellfish,
Jonas's coeliac disease, Indian food, Kreuzberg, the budget. The guests are
named from the profile, so the two-step link from "my sister and her partner"
to "Jonas is coeliac", the one fact in the example that shares no words with
the question, cost nothing: both are on one line, and the whole profile is in
the prompt.

The diet is not stated in the answer, and the old one is not acted on either.
And the model says it booked a table, which it cannot do, at a restaurant it
chose itself. That is the answering model, not the memory; the answer given
without any memory in the Mem0 notebook invented a confirmation in the same
way.

### Cost

| Call | tokens in | tokens out |
|---|--:|--:|
| rewrite after session 1 | 357 | 158 |
| rewrite after session 2 | 559 | 295 |
| answer | 365 | 142 |

Two calls to store two sessions, and one to answer. That is the same number
of write calls as Mem0 and far fewer than the rest of this series (36 for
Zep/Graphiti, 11 for Letta, 6 for the Honcho re-implementation), with no
embeddings and nothing to run but the model.

The price is in the first column. Each rewrite reads the whole current
profile, so its input grows with the profile: 357 tokens, then 559, though
session 2 was only a few lines longer than session 1. On a long history the
profile grows towards its cap, and every session pays to read it and write all
of it again.

## What it does well, and how it fails

**It resolves the conflict when it writes.** Of all the memory systems in this
series, it is the only one whose store usually holds one current value for a
fact that changed. Its prompt tells it to, and one model call that sees the
whole profile can do it, because the old line is in front of it. A pipeline
that sees only the ten most similar facts cannot always say the same.

**It cannot miss at read time.** Everything is inserted. There is no
similarity threshold, no top-k, no search to phrase well.

**Its failures are the rewrite's.** Everything the profile says is something
a model chose to write, in its own words, on every pass. The run above shows
the small versions: a date made more precise than what was said, a constraint
reworded, a hedge kept as history. [PersonaMem-v3][personamem-v3] measures the
large version: its textual memory "drops or rephrases about 14.4% of its lines
at each update", and at the 4,096-token cap 83.1% of facts survive as
concepts, while their exact wording mostly does not (§4.5, p. 19). Facts added
early or in the middle of a long history are the most at risk, a
lost-in-the-middle effect inside the memory's own evolution, and raising the
cap to 8,192 tokens keeps more facts without removing the dip. In
[DynamicMem][dynamicmem], systems that merge a new statement into an
existing memory blur the old and the new as more history piles up behind the
change: on changed preferences A-Mem falls from 89% to 39%, while plain
retrieval over raw chunks, which only appends, ends at 59% (p. 11).

## On real data

On the 67 LongMemEval knowledge-update questions of
[part 9](/posts/2199/01/agent-memory-9-the-experiment/), the same prompt
answered 62 (93%, 95% interval 84–97%), at 10 model calls and $0.022 per
question. A probe that reads the whole memory after the history found the old
value still presented as current in only 7% of questions, against 21–64% for
every other memory system.

Its five wrong answers came from the same rewrite that made it work. One is a
flawed question. One is a detail mentioned once in passing and dropped in the
first rewrite (where the user kept their old sneakers). The other three are
the "previously" clause doing too much:

- The user said twice that they had added a number of postcards "since I
  started collecting again": 17 in August, 25 in November. The profile wrote
  "The user has 25 postcards in their collection as of 2023-11-30 (up from 17
  items reported on 2023-08-11)", and the answer to "How many new postcards
  have I added…?" became "25 - 17 = 8". The key is 25.
- "In the past few weeks" became a running total with a previous value, and
  the answer subtracted again: 15 − 12 = 3.
- The rewrite did the arithmetic itself. "A month now" in April became "since
  March 2023"; in October the user said "3 months", and the rewrite counted
  from its own March date, wrote "Now 7 months", and kept the user's three
  months as the previous value.

On the 25 questions run again with the whole history (about 48 sessions and
124,000 tokens each), accuracy went from 96% to 92%, and the cost rose 13
times, to $0.28 per question: one rewrite per session, of a profile that grew
to about 5,600 tokens. Plain retrieval cost the same on both histories,
because it does nothing until it is asked.

## When it is enough

Textual memory is the right first build when the profile of a user fits
comfortably in the prompt, when facts change and the newest must win, and
when someone should be able to read and correct what the system believes. It
is a poor fit when the exact wording matters, when the history is long enough
that rewriting the whole profile every session is the dominant cost, or when
the profile no longer fits and something must select. Two cheap changes
address its typical failures: keep the raw history next to the profile, so a
detail the rewrite dropped can still be found, and phrase the history clause
so that it does not invite arithmetic ("now 25; reported 17 on 2023-08-11"
rather than "up from 17").

Next, [part 5](/posts/2199/01/agent-memory-5-mem0/) splits the profile into
separate facts and searches them: Mem0.

The notebook for this part, with every prompt and reply, is
[01-textual.ipynb][notebook]; the experiment's account of every wrong answer is
in [docs/findings/textual.md][findings].

## References

<!-- REFS -->

Papers:

- Zhong et al., [MemoryBank: Enhancing Large Language Models with Long-Term Memory][memorybank] (2023)
- Jiang et al., [PersonaMem-v3: Toward Omni-Platform Personal Intelligence for Holistic User Understanding, Recommendation, and Agentic Tasks][personamem-v3] (2026)
- Suzgun et al., [Dynamic Cheatsheet: Test-Time Learning with Adaptive Memory][dynamic-cheatsheet] (2025)
- Xie et al., [DynamicMem: A Long-Horizon Memory Benchmark in Real-World Settings][dynamicmem] (2026)

<!-- /REFS -->

Other sources:

- Mastra, [Observational Memory][mastra-om]

[memorybank]: https://arxiv.org/abs/2305.10250
[personamem-v3]: https://arxiv.org/abs/2608.21381
[dynamic-cheatsheet]: https://arxiv.org/abs/2504.07952
[dynamicmem]: https://arxiv.org/abs/2606.22877
[mastra-om]: https://mastra.ai/research/observational-memory
[notebook]: https://github.com/anton-dergunov/agent-memory-eval/blob/main/notebooks/01-textual.ipynb
[findings]: https://github.com/anton-dergunov/agent-memory-eval/blob/main/docs/findings/textual.md

<!-- SERIES -->

---

[← Part 3: What ChatGPT, Claude and Gemini ship](/posts/2199/01/agent-memory-3-frontier-assistants/) · [Part 5: Mem0: facts in a vector store →](/posts/2199/01/agent-memory-5-mem0/)

<!-- /SERIES -->
