---
title:     "Textual memory: one profile, rewritten"
excerpt:   "The simplest LLM memory design: one profile rewritten after each conversation. How it resolves changed facts, and how a rewrite drifts."
topic:     llms-and-agents
date:      2199-01-01
permalink: /posts/2199/01/agent-memory-3-textual-memory/
share:     true
series:    agent-memory
part:      3
tags:
  - llm
  - agents
  - memory
---

A language model sees only the text in its current prompt. When a new session starts, the model knows nothing about previous sessions with the same user. To use information from earlier conversations, an LLM agent needs a memory system: something that stores information from previous sessions and adds it to a later prompt. Some of these facts stay the same. Others change, in which case the new value must replace the old one.

This part introduces the simplest memory design. It stores everything it knows about the user as a single piece of plain text: a profile. There are no embeddings, graphs or databases. The [PersonaMem-v3][personamem-v3] benchmark uses this design as a baseline and calls it *Textual Memory*. It is also similar to the memory used by some consumer LLM chat products. Every other design in this series adds more components to it. That is why we start here.

This post first explains how textual memory works: its write path, its read path and the two prompts. It then follows one short test conversation through the design, one model call at a time. Finally, it examines how the design fails with longer histories and when the design is sufficient. Every prompt and reply below comes from [the notebook for this part][notebook], which you can open and run. The code is in the [agent-memory-eval repository][repo].

## How textual memory works

{% include diagram.html name="textual" alt="Textual memory's architecture, with the running example. Writing: after each session, one LLM call reads the current profile and the new session and writes the whole profile again. Memory: one text profile under four headings, 153 words after two sessions; the diet line now says pescatarian and keeps the old diet as 'previously'. Reading: no search; the whole profile goes into the prompt, and the answer covers every constraint." caption="Textual memory, with the conversation used in this post. After each session one LLM call rewrites the whole profile. At question time there is no search: the whole profile goes into the prompt." %}

Like most memory systems, textual memory has two components:

- a **write path**, which stores information after a session;
- a **read path**, which puts the stored information to the prompt of a later session.

[Part 2][part-2] explains these two paths across all the designs in this series. Textual memory takes the simplest possible approach to both paths.

### The write path: one call rewrites the whole profile

The write path runs once per session, after the session ends. The user therefore never has to wait for it.

The write path is a single model call with two inputs:

1. the current profile, which is empty before the first session;
2. the new session, with its date on the first line.

The output of the call is the entire profile, rewritten from scratch. It does not do anything else. Unlike the systems covered later in this series, there is no extraction step, no search for related facts and no code to compare old facts with new ones.

Here is the complete prompt for this call (`REWRITE` in the notebook; line breaks added for readability). The notebook substitutes the current profile, or "(empty)", for `{profile}`. It also substitutes the session for `{session}`, formatted as lines such as `user: …` and `assistant: …`, preceded by a line such as `[Session date: 2026-03-14]`.

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

The resulting profile is plain text organised under four headings, with a maximum length of 3,000 words. That is approximately 4,000 tokens, close to the 4,096-token limit in PersonaMem-v3.

Two rules are particularly important:

- **The second rule, for changes** ("replace it with the new information and record that it changed, with dates"), defines the entire policy for changing facts. The rewrite replaces the current fact while preserving the previous value as dated history.
- **The third rule, for dates** ("Write dates as absolute dates…"), explains why the session date is included in the prompt. Expressions such as "Next week" and "eight years" become meaningless in a profile that a model might read months later. The rewrite therefore converts them into absolute dates while it still knows when the user said them.

I wrote this prompt for the larger experiment in this series, which uses LongMemEval, a public benchmark of long chat histories (see "Where it breaks"). Its design follows the *Textual Memory* baseline of PersonaMem-v3, as implemented in [the benchmark's code][personamem-v3-code]: one call rewrites the entire profile under fixed headings and a size limit. The rules themselves are mine, tailored to LongMemEval's dated conversations between users and assistants:

- The questions ask about facts that users subsequently changed, and every session has a date. The second and third rules, covering changes and dates, address these questions.
- The assistant wrote about 86% of the words in these conversations, mostly general information. The fourth rule ("Ignore general information the assistant provided unless the user adopted it") prevents that information from entering the profile.

PersonaMem-v3's own prompt, quoted in "History and related work", is shorter and more general. It processes the user's activity across several apps and asks the model to extract useful information about the user's persona and preferences.

### The read path: the whole profile goes into the prompt

The read path is straightforward. It does not search or use any retrieval method, unlike the systems described later in this series. When a new session starts, the entire profile is inserted into the prompt as plain text.

Here is the prompt for the answering call (`answer` in the notebook), together with its system instruction:

```text
You are a booking assistant. Be brief and concrete.
```

```text
Today is {today}.

What you remember about this user:
{profile}

Their request: {question}
```

The system instruction is designed for the test conversation in this post, where the user asks the assistant to book a dinner.

### The price of each choice

Both design choices are simple, but each choice comes with a cost:

- **The write path rewrites everything.** After every session, the model rewrites every line of the profile, including those lines that did not changed. It uses its own wording for every line, and that wording can change with each rewrite.
- **The read path inserts everything.** Since nothing selects which information goes into the prompt, the entire profile must fit in the prompt.

A memory can also be updated through edits, where the model changes only the lines that need updating. PersonaMem-v3's prompt explicitly describes such operations: ADD, EDIT, REMOVE and MERGE (combining two related lines into one). However, its code still asks the model to output the entire memory again. Letta, covered in [part 6][part-6], performs actual edits: its agent calls tools to insert a line or replace a piece of text. But an edit only protects the lines it leaves untouched. In the notebook for that part, the agent replaced its entire memory in a single edit and reworded a person's shellfish restriction in the same way as the rewrite shown in the example below.

## The example, step by step

To demonstrate how the design works, this post follows one short test conversation through the system, one model call at a time. The same conversation is used across every system in this series. It is deliberately small so that the notebook can print every model call and you can inspect them individually.

The conversation consists of three sessions. Sessions 1 and 2 establish the facts. Session 3 starts without transcripts of the earlier sessions and asks a single question. That question does not mention any of the facts needed to answer it correctly:

- **A fact that changes:** the user's diet changes from vegetarian to pescatarian.
- **A hard constraint:** a severe peanut allergy.
- **Facts about people that the question does not name:** Lena cannot eat shellfish, and Jonas is coeliac (no gluten).
- **Other facts:** the user likes Indian food and lives in Kreuzberg.

Without a memory system, none of these facts is available in session 3. Its only input is the question. The memory system must carry the relevant information forward from sessions 1 and 2.

{% include diagram.html name="conversation" alt="The running example. On 14 March the user says they have been strictly vegetarian for eight years, have a severe peanut allergy, and like Indian food. Four months later, on 20 July, they say they are pescatarian now, have moved to Kreuzberg, and that their sister Lena (who can't eat shellfish) is coming with her partner Jonas (coeliac). Six weeks after that, in a new conversation, they ask for dinner for 'my sister and her partner'. A correct answer needs six things: the new diet and not the old one (a fact that changes), no peanuts (a hard constraint), no shellfish and no gluten (people the question does not name, reached through two links), Indian food and somewhere near Kreuzberg." caption="The conversation, and the six things a correct answer needs, grouped by what they test. Jonas's coeliac disease is two links away from the question: from \"my sister and her partner\" to Jonas, and from Jonas to coeliac." %}

The changing fact provides the strongest test of this design. Since the rewrite is performed by a generative model, several things can go wrong. It might replace the vegetarian entry, as intended, but it could also retain both diets or lose one of them. Furthermore, because every line is rewritten on every pass, the peanut allergy must survive two rewrites without becoming less precise.

In the sessions below, colours indicate the heading under which the rewrite stored each phrase: <mark class="hl hl-facts">Personal facts</mark>, <mark class="hl hl-prefs">Preferences and habits</mark>, <mark class="hl hl-plans">Ongoing situations and plans</mark> and <mark class="hl hl-changes">Changes over time</mark>.

### Session 1: everything kept, and one guess

**14 March 2026**

> **User:** I'm <mark class="hl hl-plans">planning a dinner</mark> for <mark class="hl hl-facts">my sister's visit to Berlin</mark> <mark class="hl hl-plans">next week</mark>. Worth saying up front: I've been <mark class="hl hl-facts">strictly vegetarian for eight years</mark>, and I have a <mark class="hl hl-facts">severe peanut allergy — anaphylactic</mark>, not a preference.
>
> **Assistant:** Understood — no meat, and peanuts are a hard exclusion. Any cuisine you lean towards?
>
> **User:** <mark class="hl hl-prefs">Indian, usually. Paneer dishes especially.</mark> And I'd <mark class="hl hl-prefs">rather not spend more than about 40 euros a head</mark>.

The profile is initially empty. One model call processes the rewrite prompt, the empty profile and session 1, producing the following 91-word profile:

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

The profile captures everything from session 1 and resolves the relative dates:

- The user said "eight years" in March 2026. The profile converts this to "since 2018".
- "Next week" becomes "the week of March 16, 2026".

However, one line is based on a guess. The user never said "Currently based in or planning for Berlin". They only mentioned that their sister would visit Berlin. The rewrite added a hedge, which then became part of the profile without any indication that it was an assumption.

To follow these steps yourself, the [notebook][notebook] runs this call and prints the complete prompt and reply.

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

The second call receives the profile produced at the end of session 1 (the 91 words shown above) and session 2. It outputs a new profile containing 153 words. The following diff compares it with the previous profile: red lines were removed, and green lines were added.

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

The vegetarian entry has disappeared, but its history remains:

- The diet entry now reads "Pescatarian (since June 2026; previously strictly vegetarian since 2018)".
- The change is also recorded under "Changes over time", this time with an absolute date. The user said "about a month ago" on 20 July, and the rewrite calculated the date as 2026-06-20.

The profile therefore contains one current diet rather than two contradictory entries. In the other systems in this series, handling the same change requires searching for the previous fact and making a separate decision about what to do with it. Here, a single prompt rule is sufficient because the call writing the new diet can already see the old one.

{% include diagram.html name="profile-diff" alt="The textual-memory profile after session 1 (91 words) and after session 2 (153 words), under the same four headings. The diet line was replaced, as the prompt asks: pescatarian since June 2026, previously strictly vegetarian since 2018, and the change is recorded again under 'Changes over time' as 2026-06-20. The allergy, cuisine and budget lines survived word for word. Lena, Jonas and their needs, Kreuzberg and the walking distance were added. Four changes nobody asked for are marked: 1, 'moved in May' became 'since 2026-05-01'; 2, 'can't eat shellfish' became 'has a shellfish allergy'; 3, the guess from session 1, 'based in or planning for Berlin', is kept as what the user said before; 4, the March dinner was dropped." caption="The two profiles side by side. The diet line changed as the prompt's rule asks. The numbered marks are changes the rewriter made on its own." %}

The rewrite also modified four things that nobody asked it to change. The figure marks these changes from 1 to 4:

1. **Added precision.** "I moved to Kreuzberg in May" became "since 2026-05-01". The first of May is an assumption, now recorded as an exact date.
2. **A reworded constraint.** "Lena can't eat shellfish" became "has a shellfish allergy". But "Can't eat shellfish" could mean an allergy, an intolerance or simply a dislike. If you ask the assistant why Lena avoids shellfish, it would give an explanation that the user never provided.
3. **The guess kept as history.** "Previously based in or planning for Berlin generally" preserves the hedge from session 1 as though the user had explicitly stated it.
4. **The March dinner dropped.** The autumn visit replaced the earlier event. In this case, dropping it is correct because the March dinner is over. However, the same rewriting process can remove information that is still relevant.

The entries that did not change during the conversation (the allergy, cuisine and budget) survived word for word in this example. But the design provides no guarantee that this will happen. Every line of the profile is expressed in the model's own words, and every line is rewritten on every pass.

### Session 3: reading the whole profile

**1 September 2026, a new session with no transcript of the earlier ones**

> **User:** My sister and her partner are in town tonight. Book the three of us somewhere for dinner — you know what we can and can't eat.

The read path inserts today's date, the entire profile from session 2 and the new question into the answering prompt shown earlier. Here is the resulting answer:

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

The answer successfully receives all six relevant facts:

- the peanut allergy;
- Lena's shellfish restriction;
- Jonas's coeliac disease;
- the preference for Indian food;
- the location in Kreuzberg;
- the budget.

The two-step connection between "my sister and her partner" and "Jonas is coeliac" requires no additional processing. Both names and their dietary requirements appear on the same line of the profile, and the entire profile is already in the prompt. A design that searches its memory must retrieve that line even though the question shares no words with it.

The answer does not mention the user's diet, nor does it rely on the previous diet. However, it also claims that the model booked a table at a restaurant it selected itself. The model cannot actually book a table. This issue belongs to the answering model, not the memory system. The memory only determines what information about the user is available to that model.

### What it costs

The notebook made the following calls. The tokens read by each call come from three parts of its prompt. The first three columns add up to the total input tokens:

- **Instructions:** the prompt's rules, labels and date lines.
- **Profile:** the current profile.
- **New input:** the session or question.

| Call | Instructions | + Profile | + New input | = Tokens in | Tokens out |
|---|--:|--:|--:|--:|--:|
| Rewrite after session 1 | 239 | 0 | 118 | 357 | 158 |
| Rewrite after session 2 | 235 | 159 | 165 | 559 | 295 |
| Answer | 38 | 296 | 31 | 365 | 142 |

The output tokens of a rewrite are the tokens in the new profile. The output tokens of the answering call are the tokens in its answer.

The profile read by each call is the same text produced by the previous call. However, tokenisation can differ slightly when the text is counted again. As a result, the profile can contain one more token than the output of the call that produced it (159 compared with 158). The first rewrite also has slightly more instruction tokens, mostly because "(empty)" is used in place of the profile.

The instructions account for approximately 240 tokens in each rewrite. The growing component is the profile itself. The first rewrite reads no profile, while the second reads the 159 tokens produced by the first. With a long history, the profile gradually approaches its size limit. At that point, every new session pays twice for the entire profile: once to read it and once to rewrite it. The read path remains inexpensive: a single call in which the profile accounts for most of the prompt (296 of 365 tokens).

Textual memory used two calls to store two sessions and one call to answer the question. It requires no embeddings or database, only the model. For comparison, here is the number of calls made by the systems described in later parts of this series when processing the same two sessions:

- **Mem0** ([part 4][part-4]) also makes two model calls to store them.
- **Zep/Graphiti** ([part 5][part-5]) made 38 calls.
- **Honcho** ([part 7][part-7], a run of its server) made 18 calls, 16 of them in two background "dreams".
- **Letta** ([part 6][part-6]): its agent makes additional calls inside its own replies while writing, so the user has to wait.

## Where it breaks

Every failure in this design originates in the rewrite, because that is the only operation it performs. The example above demonstrated some relatively small failures. Longer histories reveal more significant ones.

I used the same rewrite prompt in the larger LongMemEval experiment. In those histories, users state facts and later change them in passing. [Part 8][part-8] describes the experiment in detail. Two incorrect answers illustrate the two typical failure modes of this design.

**Failure 1: the history invites arithmetic.** This failure concerns the rule for changes, the same rule that correctly handled the diet. In August, a user said they had added 17 postcards to their collection "since I started collecting again". In November, they reported adding 25. Both numbers refer to the same restart date. Therefore, the answer to "How many new postcards have I added to my collection since I started collecting again?" is 25.

The rewrite recorded these two numbers as a growing collection:

> The user has 25 postcards in their collection as of 2023-11-30 (up from 17 items reported on 2023-08-11).

The answering model interpreted the history as a signal to calculate the difference and replied "25 - 17 = 8". A similar failure occurred with a count of videos watched "in the past few weeks".

**Failure 2: a detail mentioned once is dropped.** A user mentioned keeping their old sneakers under the bed. The first rewrite recorded their plan to take the sneakers to a cobbler but omitted their location. Later, the user asked where the sneakers had originally been kept, and the profile contained no answer. The rewrite makes a fresh decision about what to retain every time it runs. Consequently, a detail that seemed unimportant when first mentioned can disappear permanently.

The complete account of every incorrect answer in the experiment is available in [docs/findings/textual.md][findings].

**The same drift at a larger scale.** PersonaMem-v3 (§4.5, p. 19) measured this drift across its long histories. Its textual memory "drops or rephrases about 14.4% of its lines at each update". Exact wording is particularly unlikely to survive, especially for information from early or middle parts of the history. However, much of this change is rephrasing rather than actual information loss. Even at the 4,096-token limit, 83.1% of the facts remained present as concepts at the end.

Dynamic Cheatsheet, a similar memory system for a model that solves maths problems (see "History and related work"), exhibits the same problem. Its curator prompt (Fig. 14, p. 21 of the paper) explicitly warns that "once the cheatsheet is updated, any previous content not directly included will be lost and cannot be retrieved". Despite this warning, the authors observed the curator shortening the memory with placeholders such as "Previous content [...] preserved", rather than reproducing the full content. Over time, these placeholders degraded the stored memory (the same paper, p. 9).

### How to notice and fix these failures

These failures become visible when inspecting the profile, rather than the answers. Comparing the profile before and after each rewrite with a diff reveals every line that was dropped, reworded or made more precise. The diff for session 2 above is an example. Since the profile is plain text, generating such a diff is straightforward.

Two relatively small changes would address the two failure modes:

- **For failure 1, record the history without suggesting a difference:** "now 25; reported 17 on 2023-08-11", rather than "up from 17". This wording should remove the cue to subtract, although I did not rerun the experiment to verify it.
- **For failure 2, retain the raw conversations alongside the profile** and search them whenever the profile does not contain an answer. Such a search would recover details lost during rewriting. However, it introduces an additional search step that this design otherwise avoids. Letta, described in [part 6][part-6], retains this kind of log: it stores every message, and its agent can search the messages using a tool.

## When it is enough

Textual memory handles changing facts during the write operation and cannot miss information during reading. Both strengths come from rewriting the entire profile. But this approach also has two costs:

- Every line is expressed in the model's own words and rewritten on every pass.
- Each rewrite becomes more expensive as the profile grows.

I would start with textual memory when three conditions hold:

- The user's profile fits comfortably in the prompt.
- Facts change, and the newest value must take precedence.
- Someone needs to be able to read and correct what the system believes.

A plain-text profile is the easiest memory in this series to inspect. However, textual memory is a poor fit for three situations:

- The exact wording matters. Every line is a paraphrase produced by the model.
- The history is so long that rewriting the entire profile after every session accounts for most of the cost.
- The profile no longer fits in the prompt.

In the last situation, the system needs a mechanism to select which information goes into the prompt. Adding that selection mechanism turns textual memory into one of the other designs in this series.

## History and related work

**MemoryBank.** The earliest implementation of this idea that I found is the user portrait in [MemoryBank][memorybank] (2023, pp. 3–5). MemoryBank maintained three layers of memory:

- the raw conversation turns;
- a daily summary of events;
- a portrait of the user.

A model generated the portrait by combining observations from the daily summaries into a single description. When answering a question, the entire portrait was added to the prompt alongside conversation turns retrieved through search. Textual memory retains only the portrait.

**PersonaMem-v3.** The implementation in this post follows the *Textual Memory* baseline from [PersonaMem-v3][personamem-v3] (2026). PersonaMem-v3 is a benchmark for personal assistants whose users' preferences change over time. It was seeded from more than a million anonymised real engagement histories from social media, chatbots, calendars and companion apps.

The baseline stores information about the user as a single piece of text (PersonaMem-v3, §4.8, p. 22). It contains sections covering the user's identity, interests and preferences, people and places, and current activities. A model rewrites this text while processing the history in chronological chunks, with a 4,096-token limit on its length. At every step, the model outputs the entire text again. Indeed, [the benchmark's code][personamem-v3-code] adds the instruction "output the FULL updated memory each call (whole-document rewrite, not a diff)" to the following prompt. The authors deliberately kept the prompt simple (§4.4, p. 18):

> You maintain a running memory of one user, updated as you read their activity in chronological chunks. Remember the useful parts of the user's persona and preferences from their activities across these apps; maintain the memory with ADD, EDIT, REMOVE, and MERGE actions; and the memory should contain only the resulting persona profile rather than a raw log of activity.

In the PersonaMem-v3 paper (§4.3, p. 18), this simple baseline handled changing preferences better than a more complex design. One part of the benchmark, *tracking preference changes*, asks a question after one of the user's preferences has changed. A judge then checks whether the answer still reflects the old preference:

- With textual memory, 25.7% of answers used the old preference.
- With Mem0, 51.4% of answers did so, approximately twice as many. Mem0, described in [part 4][part-4], extracts short facts into a vector store and retrieves those most similar to the question.

The paper observes that "a topically relevant retrieved fact can remain too sticky after expiry." My interpretation of the underlying mechanism is as follows. The rewrite sees the entire profile, so when a preference changes, it can rewrite the old entry. But Mem0, as implemented in this series, only adds facts. The old preference remains alongside the new one, and a similarity search retrieves both because they concern the same topic. This could explain why the simpler design performed better in this particular test.

**Dynamic Cheatsheet.** [Dynamic Cheatsheet][dynamic-cheatsheet] (2025, §2.1, p. 3) applies the same general memory approach to a different problem. A model solves a sequence of problems, such as questions from mathematics competitions. Instead of storing facts about a user, its memory contains strategies, code snippets and insights gathered while solving previous problems. This memory takes the form of a single text document called the cheatsheet.

After each problem, a second call to the same model, called the curator, receives the current cheatsheet, the problem and the model's answer. The curator then rewrites the cheatsheet. It retains information that appears useful and general, corrects or removes entries that turned out to be wrong, and condenses the remaining content. The curator does not see the correct answers, so it must evaluate the model's work itself. In the variant closest to textual memory, the entire cheatsheet is included in the prompt for the next problem, without using any retrieval mechanism.

The results also illustrate the baseline that a memory system needs to outperform. AIME 2024 is an American mathematics competition consisting of 30 problems. On these problems, Claude 3.5 Sonnet solved the following numbers of problems (Dynamic Cheatsheet, Table 1, p. 6):

- 7 problems with a plain prompt;
- 11 problems with the same prompt and an empty cheatsheet, meaning that the memory instructions were present but the memory itself was empty;
- 15 problems with a curated cheatsheet.

Thus, approximately half of the improvement came from the instructions surrounding the memory, rather than from the memory itself. The appropriate baseline for evaluating a memory system is the same prompt with an empty memory.

**Observational Memory.** [Part 9][part-9] covers a more developed, open implementation of the same general idea: Observational Memory from Mastra. It uses two background agents to compress the conversation history into a dated log, which they subsequently rewrite.

## Run it yourself

The [notebook][notebook] accompanying this post is a complete, standalone implementation of textual memory. It has no additional dependencies, so you can read its code from beginning to end and follow each stage of the design. It uses the same prompts as this post, and every prompt and reply shown above comes directly from it.

You can run the notebook with any model. I used `gemini-3.1-flash-lite`, which is available on the free tier of the Gemini API. The free tier is sufficient because the notebook makes only a handful of calls. All systems in this series use the same model, ensuring that differences in their results come from their designs rather than from the models themselves.

Model replies vary from run to run, even with the same prompt. A rerun of the notebook can word the profile differently from what is shown above, and a different model can change more. The mechanism stays the same.

The notebook runs one short conversation. To see how the design performs on longer, realistic histories, read [part 8][part-8]. Its experiment is available in the same [repository][repo], and you can run it yourself.

You can also experiment by modifying the notebook's code and observing the results. Here are a few experiments worth trying:

- Describe the diet change less explicitly ("grabbed some salmon last night, been doing that a lot lately"). Then check whether the rewrite still replaces the vegetarian entry.
- Remove the rule for changes. Then see how the profile handles two different diets.
- Reduce the size limit to 60 words. Then observe which information the rewrite drops first.

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
