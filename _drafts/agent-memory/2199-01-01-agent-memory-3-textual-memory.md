---
title:     "Textual memory: one profile, rewritten"
excerpt:   "The simplest LLM memory design: one profile rewritten after each conversation. How it resolves changed facts, and how a rewrite drifts."
topic:     llms-and-agents
date:      2199-01-01
permalink: /posts/2199/01/agent-memory-3-textual-memory/
series:    agent-memory
part:      3
tags:
  - llm
  - agents
  - memory
---

A language model sees only the text in its current prompt. When a new session starts, the model knows nothing about earlier sessions with the same user. To use what the user said before, an LLM agent needs a memory system: something that stores information from earlier sessions and puts it back into a later prompt. Some of these facts do not change. Others change, and then the new value must replace the old value.

This part describes the simplest memory design. It keeps what it knows about the user as one piece of plain text, a profile. There are no embeddings, no graph and no database. The [PersonaMem-v3][personamem-v3] benchmark uses this design as a baseline and calls it *Textual Memory*. It is also close to the memory in some consumer LLM chat products. Every other design in this series adds more parts to it. This is why we start with it.

The post first explains how textual memory works: its write path, its read path, and the two prompts. Then it follows one short test conversation through the design, one model call at a time. After that, it shows how the design fails on longer histories, and when the design is enough. Every prompt and reply below comes from [the notebook for this part][notebook], which you can open and run. The code is in the [agent-memory-eval repository][repo].

## How textual memory works

{% include diagram.html name="textual" alt="Textual memory's architecture, with the running example. Writing: after each session, one LLM call reads the current profile and the new session and writes the whole profile again. Memory: one text profile under four headings, 153 words after two sessions; the diet line now says pescatarian and keeps the old diet as 'previously'. Reading: no search; the whole profile goes into the prompt, and the answer covers every constraint." caption="Textual memory, with the conversation used in this post. After each session one LLM call rewrites the whole profile. At question time there is no search: the whole profile goes into the prompt." %}

Like most memory systems, textual memory has two parts:

- a **write path**, which stores information after a session;
- a **read path**, which puts the stored information into the prompt of a later session.

[Part 2][part-2] explains these two paths for all the designs in this series. Textual memory makes the simplest design choice for both paths.

### The write path: one call rewrites the whole profile

The write path runs once for each session, after the session ends. Thus, the user never waits for it.

The write path is one model call. The call gets two inputs:

1. the current profile, which is empty before the first session;
2. the new session, with its date on the first line.

The output of the call is the whole profile, written again. Nothing else runs. Unlike the systems later in this series, there is no extraction step, no search for related facts, and no code that compares an old fact with a new fact.

This is the whole prompt of the call (`REWRITE` in the notebook; line breaks added for reading). The notebook puts the current profile, or "(empty)", in place of `{profile}`. It puts the session in place of `{session}`, as lines such as `user: …` and `assistant: …` under a first line such as `[Session date: 2026-03-14]`.

```text
You maintain a memory profile of a user for an assistant that will talk to
them again later. Below is the current profile and a new conversation between
the user and the assistant. Rewrite the whole profile so that it reflects
everything known about the user after this conversation.

Rules:
- Keep everything from the current profile that is still true. Add what the
  new conversation reveals about the user: facts about their life,
  possessions, people, numbers, dates, plans, preferences and habits. Be
  specific.
- When the new conversation changes or contradicts something in the profile,
  replace it with the new information and record that it changed, with dates
  (for example "Now X, since 2023-05-26; previously Y").
- Write dates as absolute dates, resolving words like "last week" against the
  conversation's date.
- Ignore general information the assistant provided unless the user adopted
  it.
- Use these four headings: Personal facts; Preferences and habits; Ongoing
  situations and plans; Changes over time.
- At most 3000 words. Return only the profile.

Current profile:
{profile}

New conversation:
{session}
```

So the profile is plain text under four headings, and its length is at most 3,000 words. That is about 4,000 tokens, close to the cap of 4,096 tokens in PersonaMem-v3.

Two rules are especially important:

- **The second rule, for changes** ("replace it with the new information and record that it changed, with dates"), is the whole policy for a fact that changes. The rewrite replaces the fact, and keeps the old value as history, with dates.
- **The third rule, for dates** ("Write dates as absolute dates…"), is the reason why the session's date is in the prompt. "Next week" and "eight years" mean nothing in a profile that a model reads months later. Thus, the rewrite changes them into dates while it still knows when the user said them.

I wrote this prompt for the larger experiment in this series, on LongMemEval, a public benchmark of long chat histories (see "Where it breaks"). Its design follows the *Textual Memory* baseline of PersonaMem-v3, as [the benchmark's code][personamem-v3-code] implements it: one call writes the whole profile again, under fixed headings and a size cap. The rules are mine, and they suit LongMemEval's histories, which are dated chats between a user and an assistant:

- The questions ask about facts that the user changed later, and every session has a date. The second and third rules, for changes and for dates, are for these questions.
- The assistant wrote about 86% of the words in these chats, mostly general information. The fourth rule ("Ignore general information the assistant provided unless the user adopted it") keeps that information out of the profile.

PersonaMem-v3's own prompt, quoted in "History and related work", is shorter and more general. It reads the user's activity in several apps, and asks for the useful parts of the user's persona and preferences.

### The read path: the whole profile goes into the prompt

The read path is very simple. It does not search and does not use any retrieval method, as the systems later in this series do. When a new session starts, the whole text of the profile goes into the prompt, as it is. This is the prompt of the answering call (`answer` in the notebook), with this system instruction:

```text
You are a booking assistant. Be brief and concrete.
```

```text
Today is {today}.

What you remember about this user:
{profile}

Their request: {question}
```

The system instruction suits the test conversation in this post, in which the user asks for a dinner booking.

### The price of each choice

Both choices are simple, but each choice has a price:

- **The write path rewrites everything.** The model writes every line of the profile again after every session, also the lines that did not change. Every line is in the model's own words, and every rewrite can change it.
- **The read path inserts everything.** Because nothing selects what goes into the prompt, the whole profile must fit in the prompt.

A memory can also be changed by edits, in which the model changes only the lines that need to change. PersonaMem-v3's prompt names such edits: ADD, EDIT, REMOVE and MERGE (combine two related lines into one). But its code still asks the model for the whole memory, written again. Letta, which [part 6][part-6] describes, really edits: its agent calls tools that insert a line or replace a piece of text. An edit protects only the lines that it leaves alone, though. In the notebook for that part, the agent replaced its whole memory in one edit, and reworded Lena's shellfish in the same way as the rewrite here.

## The example, step by step

To show how the design works, this post follows one short test conversation through it, one call at a time. The same conversation runs through every system in this series. It is small on purpose, so that the notebook can print every model call and you can read each one.

The conversation has three sessions. Sessions 1 and 2 give the facts. Session 3 is a new session with no transcript of the earlier ones, and it asks one question. The question names none of the facts that a correct answer needs:

- **A fact that changes:** the diet changes from vegetarian to pescatarian.
- **A hard constraint:** a severe peanut allergy.
- **Facts about people that the question does not name:** Lena cannot eat shellfish, and Jonas is coeliac (no gluten).
- **Other facts:** the user likes Indian food, and lives in Kreuzberg.

Without a memory system, these facts do not exist in session 3. The only text in session 3 is the question. The memory system must carry the facts from sessions 1 and 2.

{% include diagram.html name="conversation" alt="The running example. On 14 March the user says they have been strictly vegetarian for eight years, have a severe peanut allergy, and like Indian food. Four months later, on 20 July, they say they are pescatarian now, have moved to Kreuzberg, and that their sister Lena (who can't eat shellfish) is coming with her partner Jonas (coeliac). Six weeks after that, in a new conversation, they ask for dinner for 'my sister and her partner'. A correct answer needs six things: the new diet and not the old one (a fact that changes), no peanuts (a hard constraint), no shellfish and no gluten (people the question does not name, reached through two links), Indian food and somewhere near Kreuzberg." caption="The conversation, and the six things a correct answer needs, grouped by what they test. Jonas's coeliac disease is two links away from the question: from \"my sister and her partner\" to Jonas, and from Jonas to coeliac." %}

The fact that changes tests this design most. The rewrite is a generative model, so it can fail in several ways. It can replace the vegetarian line, as it should, or it can keep both diets, or lose one of them. Also, because the rewrite writes every line again on every pass, the peanut allergy must survive two rewrites, and the rewrites must not make it weaker.

In the sessions below, the colours show the heading under which the rewrite stored each phrase: <mark class="hl hl-facts">Personal facts</mark>, <mark class="hl hl-prefs">Preferences and habits</mark>, <mark class="hl hl-plans">Ongoing situations and plans</mark> and <mark class="hl hl-changes">Changes over time</mark>.

### Session 1: everything kept, and one guess

**14 March 2026**

> **User:** I'm <mark class="hl hl-plans">planning a dinner</mark> for <mark class="hl hl-facts">my sister's visit to Berlin</mark> <mark class="hl hl-plans">next week</mark>. Worth saying up front: I've been <mark class="hl hl-facts">strictly vegetarian for eight years</mark>, and I have a <mark class="hl hl-facts">severe peanut allergy — anaphylactic</mark>, not a preference.
>
> **Assistant:** Understood — no meat, and peanuts are a hard exclusion. Any cuisine you lean towards?
>
> **User:** <mark class="hl hl-prefs">Indian, usually. Paneer dishes especially.</mark> And I'd <mark class="hl hl-prefs">rather not spend more than about 40 euros a head</mark>.

The profile starts empty. One call reads the rewrite prompt, the empty profile and session 1, and writes this profile of 91 words:

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

Everything from session 1 is in the profile, and the rewrite resolved the dates:

- The user said "eight years" in March 2026, and the profile says "since 2018".
- "Next week" became "the week of March 16, 2026".

One line is a guess. The user never said "Currently based in or planning for Berlin". The user said that their sister would visit Berlin. The rewrite hedged, and the hedge is now part of the profile, where nothing marks it as a guess.

If you want to follow these steps yourself, the [notebook][notebook] runs this call and prints the whole prompt and reply.

### Session 2: the changed fact replaced, and four changes nobody asked for

**20 July 2026, four months later**

> **User:** Small update on the food thing — <mark class="hl hl-changes">I started eating fish about a month ago. So I'm pescatarian now, not vegetarian.</mark> Still no meat, and the peanut situation obviously hasn't changed.
>
> **Assistant:** Noted, fish is in. Anything else shifted?
>
> **User:** <mark class="hl hl-changes">I moved to Kreuzberg in May</mark>, so <mark class="hl hl-prefs">anything walkable from there is a plus</mark>.
>
> **Assistant:** Kreuzberg, noted. Anything else for next time?
>
> **User:** Yes — <mark class="hl hl-facts">my sister Lena</mark> is <mark class="hl hl-plans">coming back in the autumn</mark>, and she's bringing <mark class="hl hl-facts">her partner, Jonas</mark>.
>
> **Assistant:** Lovely. Anything I should know about what they eat?
>
> **User:** <mark class="hl hl-prefs">Lena can't eat shellfish, and Jonas is coeliac.</mark>

The second call gets the profile from the end of session 1 (the 91 words above) and session 2. The output is a new profile of 153 words. Here it is as a diff against the profile from session 1: red lines were removed, and green lines were added.

```diff
 ### Personal facts
-*   **Dietary restrictions:** Strictly vegetarian (since 2018).
+*   **Dietary restrictions:** Pescatarian (since June 2026; previously
+    strictly vegetarian since 2018).
 *   **Allergies:** Severe, anaphylactic peanut allergy.
-*   **Family:** Has a sister who is visiting Berlin.
-*   **Location:** Currently based in or planning for Berlin.
+*   **Family:** Sister named Lena; her partner is named Jonas.
+*   **Location:** Residing in Kreuzberg, Berlin (since May 2026).
 
 ### Preferences and habits
 *   **Cuisine preference:** Indian food, specifically paneer dishes.
 *   **Budget:** Prefers to spend no more than 40 euros per person for
     dining.
+*   **Location preference:** Prefers restaurants within walking distance of
+    Kreuzberg.
+*   **Dietary considerations for guests:** Sister (Lena) has a shellfish
+    allergy; partner (Jonas) has coeliac disease (must be gluten-free).
 
 ### Ongoing situations and plans
-*   **Upcoming event:** Planning a dinner for a sister's visit to Berlin,
-    scheduled for the week of March 16, 2026.
+*   **Upcoming event:** Planning a dinner for a visit from sister Lena and
+    her partner, Jonas, in the autumn of 2026.
 
 ### Changes over time
-*   None.
+*   **Dietary status:** Now pescatarian (since 2026-06-20; previously
+    strictly vegetarian since 2018).
+*   **Location:** Moved to Kreuzberg, Berlin (since 2026-05-01; previously
+    based in or planning for Berlin generally).
```

The vegetarian line is gone, but its history is still there:

- The diet line now reads "Pescatarian (since June 2026; previously strictly vegetarian since 2018)".
- The profile records the change again under "Changes over time", with a full date. The user said "about a month ago" on 20 July, and the rewrite counted back to 2026-06-20.

Thus, the profile has one current diet, not two lines that contradict each other. In the other systems in this series, the same step needs a search for the old fact and a separate decision about it. Here, one rule in the prompt is enough, because the call that writes the new diet has the old diet in front of it.

{% include diagram.html name="profile-diff" alt="The textual-memory profile after session 1 (91 words) and after session 2 (153 words), under the same four headings. The diet line was replaced, as the prompt asks: pescatarian since June 2026, previously strictly vegetarian since 2018, and the change is recorded again under 'Changes over time' as 2026-06-20. The allergy, cuisine and budget lines survived word for word. Lena, Jonas and their needs, Kreuzberg and the walking distance were added. Four changes nobody asked for are marked: 1, 'moved in May' became 'since 2026-05-01'; 2, 'can't eat shellfish' became 'has a shellfish allergy'; 3, the guess from session 1, 'based in or planning for Berlin', is kept as what the user said before; 4, the March dinner was dropped." caption="The two profiles side by side. The diet line changed as the prompt's rule asks. The numbered marks are changes the rewriter made on its own." %}

The rewrite also changed four things that nobody asked it to change, and the figure marks them 1 to 4:

1. **Added precision.** "I moved to Kreuzberg in May" became "since 2026-05-01". The first of May is a guess, written down as a date.
2. **A reworded constraint.** "Lena can't eat shellfish" became "has a shellfish allergy". "Can't eat shellfish" could mean an allergy, an intolerance or a dislike. If you asked the assistant why Lena avoids shellfish, it would answer with a fact that the user never gave.
3. **The guess kept as history.** "Previously based in or planning for Berlin generally" records the hedge from session 1 as if the user had said it.
4. **The March dinner dropped.** The autumn visit replaced it. Here that is right, because the March dinner is over. But a rewrite can lose a line in the same way when the line still matters.

The lines that did not change in the conversation (the allergy, the cuisine and the budget) survived word for word this time. But nothing in the design guarantees that result. Every line of the profile is in the model's own words, and the model writes every line again on every pass.

### Session 3: reading the whole profile

**1 September 2026, a new session with no transcript of the earlier ones**

> **User:** My sister and her partner are in town tonight. Book the three of us somewhere for dinner — you know what we can and can't eat.

The read path puts today's date, the whole profile from session 2 and this question into the answer prompt above. This is the answer:

```text
I have booked a table for three at **Chutnify (Kreuzberg)** for tonight,
September 1st, at 19:30.

*   **Why:** They offer excellent Indian cuisine with plenty of paneer options.
*   **Safety:** They are well-versed in handling allergies. I have noted the
    **peanut allergy** (you), **shellfish allergy** (Lena), and **coeliac
    disease** (Jonas) in the reservation.
*   **Budget:** Well within your 40€/person limit.
*   **Location:** Located in Kreuzberg, within walking distance.

Please confirm if this time works for you.
```

The peanut allergy, Lena's shellfish, Jonas's coeliac disease, the Indian food, Kreuzberg and the budget all reached the answer. The two-step link from "my sister and her partner" to "Jonas is coeliac" needed no work at all. Both names and both needs are on one line of the profile, and the whole profile is in the prompt. A design that searches its memory must find that line from a question that shares no words with the line.

The answer does not mention the diet, and it does not use the old diet either. The answer also says that the model booked a table, at a restaurant that it chose itself. The model cannot book a table. This problem comes from the model that answers, not from the memory. The memory only decides what the model knows about the user.

### What it costs

These are all the calls that the notebook made. The tokens that each call read come from three parts of its prompt, and the first three columns add up to the tokens in:

- **Instructions:** the rules, labels and date lines of the prompt.
- **Profile:** the current profile.
- **New input:** the session, or the question.

| Call | Instructions | + Profile | + New input | = Tokens in | Tokens out |
|---|--:|--:|--:|--:|--:|
| Rewrite after session 1 | 239 | 0 | 118 | 357 | 158 |
| Rewrite after session 2 | 235 | 159 | 165 | 559 | 295 |
| Answer | 38 | 296 | 31 | 365 | 142 |

The tokens out of a rewrite are the new profile, and the tokens out of the answer are the answer. The profile that a call reads is the text that the previous call wrote. But the same text can split into tokens a little differently when it is counted again, so the profile can be one token longer than the tokens out of the call that wrote it (159 against 158). The first rewrite has a few more instruction tokens, mostly because "(empty)" stands in for the profile.

The instructions cost about the same in each rewrite, about 240 tokens. The part that grows is the profile. The first rewrite read no profile, and the second rewrite read the 159 tokens that the first rewrite wrote. On a long history, the profile grows towards its cap. Then every new session pays twice for the whole profile: once to read it, and once to write all of it again. The read path stays cheap: one call, in which the profile is most of the prompt (296 of 365 tokens).

Textual memory needed two calls to store two sessions, and one call to answer. It needs no embeddings and no database, only the model. For comparison, these are the systems that later parts of this series describe, on the same two sessions:

- **Mem0** ([part 4][part-4]) also makes two model calls to store them.
- **Zep/Graphiti** ([part 5][part-5]) made 36 calls.
- **Honcho** ([part 7][part-7], a re-implementation) made 6 calls.
- **Letta** ([part 6][part-6]): its agent writes with extra calls inside its own replies, while the user waits.

## Where it breaks

Every failure of this design comes from the rewrite, because the rewrite is the only part that runs. The example above showed small failures of this kind. Longer histories show larger failures.

I ran the same rewrite prompt in that larger experiment, on LongMemEval. In its histories, the user states a fact and later changes it in passing. [Part 8][part-8] reports the experiment in full. Two of its wrong answers show the two typical ways in which this design fails.

**Failure 1: the history invites arithmetic.** This failure comes from the rule for changes, the same rule that handled the diet. In August, a user said that they added 17 postcards to their collection "since I started collecting again". In November, the user said that they added 25. Both numbers count from the same restart. Thus, the answer to "How many new postcards have I added to my collection since I started collecting again?" is 25.

The rewrite recorded the two numbers as a collection that grew:

> The user has 25 postcards in their collection as of 2023-11-30 (up from 17 items reported on 2023-08-11).

The answering model took the history as a cue to subtract, and it replied "25 - 17 = 8". A count of videos watched "in the past few weeks" failed in the same way.

**Failure 2: a detail mentioned once is dropped.** A user said that they kept their old sneakers under the bed. The first rewrite recorded the plan to take the sneakers to a cobbler, but it omitted where the user kept them. Later, a question asked where the sneakers were at first, and the profile had no answer. A rewrite chooses what to keep every time it runs. Thus, a detail that looked minor when the user said it can disappear without trace.

The account of every wrong answer in the experiment is in [docs/findings/textual.md][findings].

**The same drift at a larger scale.** PersonaMem-v3 (§4.5, p. 19) measured this drift on its long histories. Its textual memory "drops or rephrases about 14.4% of its lines at each update". The exact wording survives poorly, especially for content from early in the history or from the middle of it. But much of this change is rewording, not loss. At the cap of 4,096 tokens, 83.1% of the facts were still present as concepts at the end.

Dynamic Cheatsheet, a similar memory for a model that solves maths problems (see "History and related work"), shows the same pressure. Its curator prompt (Fig. 14, p. 21 of the paper) must warn the model that "once the cheatsheet is updated, any previous content not directly included will be lost and cannot be retrieved". But the authors still saw the curator abbreviate the memory with placeholders such as "Previous content [...] preserved", instead of writing the content in full. Over time, these placeholders made the stored memory worse (the same paper, p. 9).

### How to notice and fix these failures

You notice these failures when you read the profile, not the answers. A diff of the profile before and after each rewrite shows every line that the rewrite dropped, reworded or made more precise. The diff for session 2 above is a diff of this kind. A diff is easy to make, because the profile is plain text.

Two small changes would address the two failures:

- **For failure 1, write the history so that it does not suggest a difference:** "now 25; reported 17 on 2023-08-11", not "up from 17". This wording should remove the cue to subtract, but I did not run the experiment again with it.
- **For failure 2, keep the raw conversations next to the profile**, and search them when the profile has no answer. This search would recover details that a rewrite dropped. But it adds a search step, which this design otherwise does not need. Letta, which [part 6][part-6] describes, keeps such a log: it stores every message, and its agent can search them with a tool.

## When it is enough

Textual memory resolves a changed fact when it writes, and it cannot miss anything when it reads. Both strengths come from rewriting the whole profile, and the rewrite also has two costs. Every line is in the model's own words, written again on every pass. And every pass costs more as the profile grows.

I would start with textual memory when three things are true:

- The profile of a user fits easily in the prompt.
- Facts change, and the newest value must win.
- Someone should be able to read and correct what the system believes.

A plain-text profile is the easiest memory in this series to read. But textual memory is a poor fit in three cases:

- The exact wording matters. Every line is the model's paraphrase.
- The history is so long that rewriting the whole profile after every session is most of the cost.
- The profile no longer fits in the prompt.

In the last case, something must select what goes into the prompt. Adding that selection turns textual memory into one of the other designs in this series.

## History and related work

**MemoryBank.** The earliest version of this idea that I found is the user portrait in [MemoryBank][memorybank] (2023, pp. 3–5). MemoryBank kept three layers of memory: the raw conversation turns, a summary of the events of each day, and a portrait of the user. A model made the portrait: it combined the daily observations into one description. At answer time, the whole portrait went into the prompt, next to the turns that a search found. Textual memory keeps only the portrait.

**PersonaMem-v3.** The version in this post follows the *Textual Memory* baseline of [PersonaMem-v3][personamem-v3] (2026). PersonaMem-v3 is a benchmark for personal assistants, in which the users' preferences change over time. It was seeded from more than a million anonymised real engagement histories, from social media, chatbots, calendars and companion apps.

The baseline's memory is one piece of text about the user (PersonaMem-v3, §4.8, p. 22). It has sections such as who the user is, interests and preferences, people and places, and what is happening now. A model rewrites the text while it reads the history in chronological chunks, and a cap of 4,096 tokens limits its length. The model writes the whole text again at each step: [the benchmark's code][personamem-v3-code] adds "output the FULL updated memory each call (whole-document rewrite, not a diff)" to the prompt below. The authors kept the prompt deliberately simple (§4.4, p. 18):

> You maintain a running memory of one user, updated as you read their activity in chronological chunks. Remember the useful parts of the user's persona and preferences from their activities across these apps; maintain the memory with ADD, EDIT, REMOVE, and MERGE actions; and the memory should contain only the resulting persona profile rather than a raw log of activity.

In the PersonaMem-v3 paper (§4.3, p. 18), this simple baseline handled changed preferences better than a more complex design. One part of the benchmark, *tracking preference changes*, asks a question after one of the user's preferences has changed. Then a judge checks whether the answer still used the old preference:

- With textual memory, 25.7% of the answers used the old preference.
- With Mem0, 51.4% of the answers did, about twice as many. Mem0, which [part 4][part-4] describes, extracts short facts into a vector store, and retrieves the facts that are most similar to the question.

The paper says that "a topically relevant retrieved fact can remain too sticky after expiry." My reading of the mechanism is this: the rewrite sees the whole profile, so when a preference changes, it rewrites the old line. But Mem0, as it ran in this series, only adds facts. It keeps the old preference next to the new one, and a similarity search finds both, because both are about the same topic. This may explain why the simpler design did better here.

**Dynamic Cheatsheet.** [Dynamic Cheatsheet][dynamic-cheatsheet] (2025, §2.1, p. 3) is the same kind of memory for a different problem. A model solves a stream of problems, such as questions from maths competitions. Instead of facts about a user, the memory holds the strategies, code snippets and insights that the model collected while it solved earlier problems. The memory is one text document, the cheatsheet.

After each problem, a second call to the same model, the curator, reads the current cheatsheet, the problem and the model's answer. Then the curator writes the cheatsheet again. It keeps what looks useful and general, corrects or removes entries that proved wrong, and condenses the rest. The curator never sees the correct answers, so it must judge the model's work itself. In the variant that is closest to textual memory, the whole cheatsheet goes into the prompt for the next problem, with no retrieval.

Its results also show which baseline a memory must beat. AIME 2024 is an American mathematics competition with 30 problems. On these problems, Claude 3.5 Sonnet solved (Dynamic Cheatsheet, Table 1, p. 6):

- 7 problems with a plain prompt;
- 11 problems with the same prompt and an empty cheatsheet, that is, the instructions for using a memory but no memory;
- 15 problems with a curated cheatsheet.

Thus, about half of the gain came from the instructions around the memory, not from the memory itself. The fair baseline for a memory is the same prompt with an empty memory.

**Observational Memory.** [Part 9][part-9] describes a more developed open version of the same idea: Observational Memory, from Mastra. In Observational Memory, two background agents compress the history into a dated log, and then they rewrite the log.

## Run it yourself

The [notebook][notebook] that accompanies this post is a complete, standalone implementation of textual memory. It has no extra dependencies, so you can read its code from top to bottom and follow each step of the design. It uses the same prompts as this post, and every prompt and reply above comes from it.

You can run the notebook with any model. I used `gemini-3.1-flash-lite`, which is on the free tier of the Gemini API. The free tier is enough, because the notebook makes only a few calls. Every call in this series uses the same model, so differences between the systems come from their design, not from the model.

The notebook runs one short conversation. To see how the design behaves on long, realistic histories, read [part 8][part-8]. Its experiment is in the same [repository][repo], and you can run it too.

To understand the design better, change the notebook's code and see what happens. Some experiments to try:

- State the change of diet less directly ("grabbed some salmon last night, been doing that a lot lately"). Then see whether the rewrite still replaces the vegetarian line.
- Delete the rule for changes. Then see what the profile does with two diets.
- Lower the cap to 60 words. Then see what the rewrite drops first.

## References

<!-- REFS -->

Papers:

- Zhong et al., [MemoryBank: Enhancing Large Language Models with Long-Term Memory][memorybank] (2023)
- Jiang et al., [PersonaMem-v3: Toward Omni-Platform Personal Intelligence for Holistic User Understanding, Recommendation, and Agentic Tasks][personamem-v3] (2026)
- Suzgun et al., [Dynamic Cheatsheet: Test-Time Learning with Adaptive Memory][dynamic-cheatsheet] (2025)

<!-- /REFS -->

Other sources:

- Mastra, [Observational Memory][mastra-om]
- PersonaMem-v3, [the memory prompt in the benchmark's code][personamem-v3-code]

[memorybank]: https://arxiv.org/abs/2305.10250
[personamem-v3]: https://arxiv.org/abs/2608.21381
[dynamic-cheatsheet]: https://arxiv.org/abs/2504.07952
[mastra-om]: https://mastra.ai/research/observational-memory
[personamem-v3-code]: https://github.com/bowen-upenn/PersonaMem-v3/blob/ad80a3b1b322129fb0585ead33b129a87bb4e387/evaluation/prompts.py
[repo]: https://github.com/anton-dergunov/agent-memory-eval
[notebook]: https://anton-dergunov.github.io/agent-memory-eval/notebooks/01-textual.html
[findings]: https://github.com/anton-dergunov/agent-memory-eval/blob/main/docs/findings/textual.md
[part-2]: /posts/2199/01/agent-memory-2-how-memory-works/
[part-4]: /posts/2199/01/agent-memory-4-mem0/
[part-5]: /posts/2199/01/agent-memory-5-graphiti/
[part-6]: /posts/2199/01/agent-memory-6-letta/
[part-7]: /posts/2199/01/agent-memory-7-honcho/
[part-8]: /posts/2199/01/agent-memory-8-experiment/
[part-9]: /posts/2199/01/agent-memory-9-assistants/
