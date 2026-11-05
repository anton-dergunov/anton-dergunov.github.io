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

An assistant that works with the same person over weeks or months has to carry what it learns in one conversation into the next. Some of those facts stay fixed. Others change, such as where the person lives or works, the state of a project, or a decision that was later reversed, and then the newer value has to replace the older one. The language model cannot do this by itself, because it keeps nothing between calls and sees only what is in its prompt. Whatever an assistant knows about a user is text that some mechanism stores and later puts back into that prompt.

The simplest mechanism that still deserves the name memory keeps one plain-text profile of the user. After each conversation, a separate model call reads the current profile and the new conversation, and writes the whole profile again. When a new conversation starts, the whole profile goes into the prompt. I call it textual memory here, after the benchmark baseline it is taken from. It is close to what some consumer assistants ship, and every other design in this series adds machinery to it, so it is the one to understand first.

Most of what a memory system does well, does badly and costs follows from two choices: who writes the memory, and whether the read path puts all of it into the prompt or a search picks part of it. Textual memory makes the simplest choice on both. A separate model call writes, after each conversation, so the user never waits for it. And the read path inserts everything, so nothing has to be found. The price of the first choice is that every line of the profile is rewritten by a model on every pass. The price of the second is that the profile has to fit in the prompt.

This post runs one short test conversation through that loop, call by call: the profile after each rewrite, the answer, and what it cost. Then it looks at how the design fails on longer histories, and when it is enough. Every prompt and reply below comes from [the notebook for this part][notebook], which you can open and run; the code is in the [agent-memory-eval repository][repo].

{% include diagram.html name="textual" alt="Textual memory's architecture, with the running example. Writing: after each session, one LLM call reads the current profile and the new session and writes the whole profile again. Memory: one text profile under four headings, 153 words after two sessions; the diet line now says pescatarian and keeps the old diet as 'previously'. Reading: no search; the whole profile goes into the prompt, and the answer covers every constraint." caption="Textual memory, with the conversation used in this post. After each session one LLM call rewrites the whole profile. At question time there is no search: the whole profile goes into the prompt." %}

## Where the design comes from

The ancestor of this system is the user portrait in [MemoryBank][memorybank] (2023). MemoryBank kept three layers of memory: the raw conversation turns, summaries of each day's events, and a portrait of the user that a model rolled up from daily observations into one description (p. 3). At answer time, the portrait went into the prompt whole, next to the turns that a search retrieved (p. 4–5). Textual memory keeps only the portrait.

The version I ran follows the *Textual Memory* baseline of [PersonaMem-v3][personamem-v3] (2026). PersonaMem-v3 is a benchmark for personal assistants, seeded from more than a million anonymised real engagement histories across social media, chatbots, calendars and companion apps, in which the users' preferences change over time. Its textual memory is one note about the user, with sections such as who the user is, interests and preferences, people and places, and what is currently going on (§4.8, p. 22). A model rewrites the note as it reads the history in chronological chunks, and the note is held under a cap of 4,096 tokens. The authors kept the prompt deliberately simple (§4.4, p. 18):

> You maintain a running memory of one user, updated as you read their activity in chronological chunks. Remember the useful parts of the user's persona and preferences from their activities across these apps; maintain the memory with ADD, EDIT, REMOVE, and MERGE actions; and the memory should contain only the resulting persona profile rather than a raw log of activity.

In the PersonaMem-v3 paper, this simple baseline handled changed preferences better than a retrieval-based memory did. One of the benchmark's probes, *tracking preference changes*, asks a question after one of the user's preferences has expired, and a judge records whether the answer still relied on the outdated preference. With GPT-5.5 and textual memory, the answers fell back on an expired preference about a quarter of the time (25.7%). With Mem0, which extracts short facts into a vector store and retrieves the ones most similar to the question, they did so about half the time (51.4%) (§4.3, p. 18).

The paper's reading is that "a topically relevant retrieved fact can remain too sticky after expiry." My reading of the mechanism is that a rewrite sees the whole profile and can demote the old preference when it writes, while a similarity search keeps finding the old preference because it is still about the same topic.

A close relative comes from a different problem. [Dynamic Cheatsheet][dynamic-cheatsheet] (2025) gives a model a memory while it solves a stream of problems, such as maths competition questions. The memory is one document, the cheatsheet, which holds strategies, code snippets and insights rather than facts about a user. After each problem, a second call to the same model, the curator, reads the current cheatsheet, the problem and the model's answer, and writes the cheatsheet again: it keeps what looks useful and general, corrects or removes entries that turned out wrong, and condenses the rest (§2.1, p. 3). The curator never sees the correct answers, so it has to judge the model's work itself. In the variant closest to textual memory, the whole cheatsheet goes into the prompt for the next problem, with no retrieval.

Its results carry a lesson for reading any result of this kind. On the 30 problems of AIME 2024, an American mathematics competition for secondary-school students, Claude 3.5 Sonnet solved 7 with a plain prompt and 15 with a curated cheatsheet. But the same prompt with an empty cheatsheet already solved 11 (Table 1, p. 6). About half of the gain came from the instructions around the memory, not from the memory itself. When a memory that a model rewrites is compared with no memory at all, the fair baseline is the same prompt with the memory left empty.

[Part 9][part-9] looks at a more developed open version of the same idea, Mastra's Observational Memory, in which two background agents compress the history into a dated log and then rewrite it.

## The test: one conversation in three sessions

To see what the design does, I ran one short conversation through it, the same conversation that runs through every system in this series. It is a test case, small on purpose so that every model call can be printed and read; the dinner itself is not the point. It tests three things: a fact that changes, a hard constraint, and facts about people that the question does not name.

**Session 1, 14 March 2026**

> **User:** I'm planning a dinner for my sister's visit to Berlin next week. Worth saying up front: I've been strictly vegetarian for eight years, and I have a severe peanut allergy — anaphylactic, not a preference.
>
> **Assistant:** Understood — no meat, and peanuts are a hard exclusion. Any cuisine you lean towards?
>
> **User:** Indian, usually. Paneer dishes especially. And I'd rather not spend more than about 40 euros a head.

**Session 2, 20 July 2026, four months later**

> **User:** Small update on the food thing — I started eating fish about a month ago. So I'm pescatarian now, not vegetarian. Still no meat, and the peanut situation obviously hasn't changed.
>
> **Assistant:** Noted, fish is in. Anything else shifted?
>
> **User:** I moved to Kreuzberg in May, so anything walkable from there is a plus.
>
> **Assistant:** Kreuzberg, noted. Anything else for next time?
>
> **User:** Yes — my sister Lena is coming back in the autumn, and she's bringing her partner, Jonas.
>
> **Assistant:** Lovely. Anything I should know about what they eat?
>
> **User:** Lena can't eat shellfish, and Jonas is coeliac.

**Session 3, 1 September 2026, a new conversation with no transcript of the earlier ones**

> **User:** My sister and her partner are in town tonight. Book the three of us somewhere for dinner — you know what we can and can't eat.

A correct answer needs six things: pescatarian and no longer vegetarian, no peanuts, no shellfish for Lena, no gluten for Jonas, a liking for Indian food, and somewhere near Kreuzberg. The question mentions none of them.

{% include diagram.html name="conversation" alt="The running example. On 14 March the user says they have been strictly vegetarian for eight years, have a severe peanut allergy, and like Indian food. Four months later, on 20 July, they say they are pescatarian now, have moved to Kreuzberg, and that their sister Lena (who can't eat shellfish) is coming with her partner Jonas (coeliac). Six weeks after that, in a new conversation, they ask for dinner for 'my sister and her partner'. A correct answer needs six things: the new diet and not the old one (a fact that changes), no peanuts (a hard constraint), no shellfish and no gluten (people the question does not name, reached through two links), Indian food and somewhere near Kreuzberg." caption="The conversation, and the six things a correct answer needs, grouped by what they test. Jonas's coeliac disease is two links away from the question: from \"my sister and her partner\" to Jonas, and from Jonas to coeliac." %}

This design is tested most by the reversal in July. The rewrite can replace the vegetarian line, keep both diets, or lose one of them. And because every line is written again on every pass, the peanut allergy has to survive two rewrites without being weakened.

## How the rewrite works

The write path is one model call per conversation. Its inputs are the current profile (empty before the first conversation) and the new conversation, with the conversation's date on its first line. Its output is the whole profile, written again. Nothing else runs: there is no extraction step, no search for related facts, and no code that compares an old fact with a new one. In a product, this call would run after the conversation ends, so the user would not wait for it.

The read path is hardly a step at all. When a new conversation starts, the profile goes into the prompt as it is, after today's date and the line "What you remember about this user:", and before the user's request.

The rewrite prompt is ours, written after PersonaMem-v3's description of its baseline; it is what I tested, not a prompt the benchmark provides. It asks for four headings (personal facts; preferences and habits; ongoing situations and plans; changes over time) and at most 3,000 words. Two of its rules do most of the work:

```text
- When the new conversation changes or contradicts something in the profile,
  replace it with the new information and record that it changed, with dates
  (for example "Now X, since 2023-05-26; previously Y").
- Write dates as absolute dates, resolving words like "last week" against the
  conversation's date.
```

The first rule is the whole policy for a fact that changes: replace it, and keep the old value as history. The second rule is the reason the date goes into the prompt. "Next week" and "eight years" mean nothing in a profile read months later, so the rewrite turns them into dates while it still knows when they were said.

## After session 1: everything kept, and one guess

The profile starts empty. One call reads session 1 and writes this, 91 words:

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

Everything from session 1 is there, and the dates were resolved: "eight years", said in March 2026, became "since 2018", and "next week" became "the week of March 16, 2026". One line is a guess. The user never said "Currently based in or planning for Berlin"; they said that their sister was visiting Berlin. The rewriter hedged, and the hedge is now part of the profile, where nothing marks it as a guess.

## After session 2: the changed fact replaced, and four changes nobody asked for

The second call is given that profile and session 2. It does not edit the profile; it writes a new one, 153 words long:

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

The vegetarian line is gone, and its history is not. The diet line now reads "Pescatarian (since June 2026; previously strictly vegetarian since 2018)", and the change is recorded again under "Changes over time" with a full date: "about a month ago", counted back from 20 July, became 2026-06-20. There is one current diet in the profile, not two lines that contradict each other. In the other systems in this series, the same step needs a search for the old fact and a separate decision about it. Here one rule in the prompt is enough, because the call that writes the new diet has the old one in front of it.

{% include diagram.html name="profile-diff" alt="The textual-memory profile after session 1 (91 words) and after session 2 (153 words), under the same four headings. The diet line was replaced, as the prompt asks: pescatarian since June 2026, previously strictly vegetarian since 2018, and the change is recorded again under 'Changes over time' as 2026-06-20. The allergy, cuisine and budget lines survived word for word. Lena, Jonas and their needs, Kreuzberg and the walking distance were added. Four changes nobody asked for are marked: 1, 'moved in May' became 'since 2026-05-01'; 2, 'can't eat shellfish' became 'has a shellfish allergy'; 3, the guess from session 1, 'based in or planning for Berlin', is kept as what the user said before; 4, the March dinner was dropped." caption="The two profiles side by side. The diet line changed as the prompt's rule asks. The numbered marks are changes the rewriter made on its own." %}

The rewrite also changed four things that nobody asked it to change, marked 1 to 4 in the figure. Each one is small. The reworded constraint shows why they matter. "Lena can't eat shellfish" could mean an allergy, an intolerance or a dislike; the profile now says allergy, and an assistant asked why Lena avoids shellfish would answer with a fact the user never gave. The guess from March has a similar afterlife: it is now recorded as the user's previous location.

The lines that did not change in the conversation (the allergy, the cuisine, the budget) survived word for word this time. Nothing in the design guarantees that. Every line of the profile is the model's own wording, and the model writes all of them again on every pass.

## Reading: the whole profile in the prompt

The question goes in with the profile as it is, and today's date. The answer:

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

The peanut allergy, Lena's shellfish, Jonas's coeliac disease, the Indian food and Kreuzberg all reached the answer, and so did the budget. The two-step link from "my sister and her partner" to "Jonas is coeliac" needed no work at all: both names and both needs sit on one line of the profile, and the whole profile is in the prompt. A design that searches its memory has to find that line from a question that shares no words with it.

The answer does not mention the diet, and it does not act on the old one either. It also says that a table is booked, which the model cannot do, at a restaurant it chose itself. That comes from the answering model, not from the memory, which only decides what the model knows about the user.

## Where it breaks

Every failure of this design comes from the rewrite, because the rewrite is the only part that runs. The run above showed small versions of it. Longer histories show larger ones.

I ran the same rewrite prompt in a larger experiment, on a public benchmark of long chat histories in which the user states a fact and later changes it in passing; [part 8][part-8] reports it in full. Two of its wrong answers show the two typical ways this design goes wrong.

The first comes from the history clause, the same rule that handled the diet. A user said in August that they had added 17 postcards to their collection "since I started collecting again", and in November that they had added 25. Both numbers counted from the same restart, so the answer to "How many new postcards have I added to my collection since I started collecting again?" is 25. The rewrite recorded them as a collection that grew: "The user has 25 postcards in their collection as of 2023-11-30 (up from 17 items reported on 2023-08-11)". The answering model took the history as a cue to subtract, and replied "25 - 17 = 8". A count of videos watched "in the past few weeks" failed in the same way.

The second is a detail mentioned once, in passing. A user said that they kept their old sneakers under the bed. The first rewrite wrote down their plan to take the sneakers to a cobbler, and left out where they were kept. When the question later asked where the sneakers had been at first, the profile had no answer. A rewrite chooses what to keep every time it runs, and a detail that looked minor when it was said can disappear without trace.

PersonaMem-v3 measured this drift on its long histories. Its textual memory "drops or rephrases about 14.4% of its lines at each update", and exact wording survives poorly, especially for content added early or in the middle of the history. Much of that is rewording rather than loss: at the 4,096-token cap, 83.1% of the facts were still present as concepts at the end (§4.5, p. 19).

Dynamic Cheatsheet shows the same pressure from the curator's side. Its curator prompt has to warn the model that "once the cheatsheet is updated, any previous content not directly included will be lost and cannot be retrieved" (Fig. 14, p. 21). Even so, the authors saw the curator abbreviate the memory with placeholders such as "Previous content [...] preserved" instead of writing it out, which made what was stored worse over time (p. 9).

You notice these failures by reading the profile, not the answers. A diff of the profile before and after each rewrite, like the figure above, shows every line that was dropped, reworded or made more precise, and it is easy to produce because the profile is plain text. Two small changes would address the failures above. Writing the history so that it does not suggest a difference ("now 25; reported 17 on 2023-08-11" rather than "up from 17") should remove the cue to subtract; I have not re-run the experiment with that wording. Keeping the raw conversations next to the profile, and searching them when the profile has no answer, would recover details that a rewrite dropped, at the cost of a search step that this design otherwise does without.

## What it costs

Every call the notebook made:

| Call | Tokens in | Tokens out |
|---|--:|--:|
| Rewrite after session 1 | 357 | 158 |
| Rewrite after session 2 | 559 | 295 |
| Answer | 365 | 142 |

It took two calls to store two sessions, and one to answer. Mem0 also makes two model calls to store the same sessions; Zep/Graphiti made 36, the Honcho re-implementation made 6, and Letta's agent writes with extra calls inside its own replies, while the user waits. Textual memory needs no embeddings and no database, only the model.

The cost that grows is in the first column. The second rewrite read 559 tokens against 357 for the first, and most of the difference is the profile it had to read: 158 tokens, the length of the first rewrite's output. Session 2 itself added little. On a long history the profile grows towards its cap, and every new conversation pays to read all of it and write all of it again. The read stays cheap: one call, with a prompt about the size of the profile.

## When it is enough

Textual memory resolves a changed fact when it writes, and it cannot miss anything when it reads. It pays for both in the rewrite: every line is the model's own wording, written again on every pass, and every pass costs more as the profile grows.

I would start with it when three things hold: the profile of a user fits comfortably in the prompt, facts change and the newest must win, and someone should be able to read and correct what the system believes. A plain-text profile is the easiest memory in this series to read. It is a poor fit when the exact wording matters, since every line is the model's paraphrase; when the history is long enough that rewriting the whole profile after every conversation dominates the cost; and when the profile no longer fits in the prompt. At that point something has to select what goes in, and the design becomes one of the others in this series.

## How it was run

The notebook implements the design as a prompt and two short functions, one that rewrites the profile and one that answers. There is no library to install, because the design has no other parts. The rewrite prompt is the same one the larger experiment used for its textual-memory arm, copied into the notebook so that it runs on its own. Its cap of 3,000 words is about 4,000 tokens, close to PersonaMem-v3's cap of 4,096.

Every model call in this series uses the same small, inexpensive model, `gemini-3.1-flash-lite`, so that differences between the systems come from their design rather than from the model. The free tier of its API is enough to run every notebook. [TODO: why this model rather than another small one?] The temperature is 0, which makes the model pick its most likely reply each time, so that a re-run gives nearly the same output.

This is one conversation, run once. It shows the mechanism and the kinds of change a rewrite makes, not how often each one happens; the PersonaMem-v3 measurements above give a sense of that.

## Try it

The [notebook][notebook] prints every prompt and reply in this post. It ends with experiments worth running yourself: state the reversal less directly ("grabbed some salmon last night, been doing that a lot lately") and see whether the rewrite still replaces the vegetarian line; delete the rule about contradictions and see what the profile does with two diets; or lower the cap to 60 words and see what the rewrite drops first. The experiment's account of every wrong answer is in [docs/findings/textual.md][findings], and the code is in the [repository][repo].

## References

<!-- REFS -->

Papers:

- Zhong et al., [MemoryBank: Enhancing Large Language Models with Long-Term Memory][memorybank] (2023)
- Jiang et al., [PersonaMem-v3: Toward Omni-Platform Personal Intelligence for Holistic User Understanding, Recommendation, and Agentic Tasks][personamem-v3] (2026)
- Suzgun et al., [Dynamic Cheatsheet: Test-Time Learning with Adaptive Memory][dynamic-cheatsheet] (2025)

<!-- /REFS -->

Other sources:

- Mastra, [Observational Memory][mastra-om]

[memorybank]: https://arxiv.org/abs/2305.10250
[personamem-v3]: https://arxiv.org/abs/2608.21381
[dynamic-cheatsheet]: https://arxiv.org/abs/2504.07952
[mastra-om]: https://mastra.ai/research/observational-memory
[repo]: https://github.com/anton-dergunov/agent-memory-eval
[notebook]: https://anton-dergunov.github.io/agent-memory-eval/notebooks/01-textual.html
[findings]: https://github.com/anton-dergunov/agent-memory-eval/blob/main/docs/findings/textual.md
[part-8]: /posts/2199/01/agent-memory-8-experiment/
[part-9]: /posts/2199/01/agent-memory-9-assistants/
