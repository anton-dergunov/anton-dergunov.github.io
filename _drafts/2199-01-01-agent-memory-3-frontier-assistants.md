---
title:     "How LLM agents remember, part 3: what ChatGPT, Claude and Gemini ship"
topic:     llms-and-agents
date:      2199-01-01
permalink: /posts/2199/01/agent-memory-3-frontier-assistants/
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
3. **What ChatGPT, Claude and Gemini ship** (this part)
4. [Textual memory: one profile, rewritten](/posts/2199/01/agent-memory-4-textual-memory/)
5. [Mem0: facts in a vector store](/posts/2199/01/agent-memory-5-mem0/)
6. [Zep and Graphiti: facts with dates, in a graph](/posts/2199/01/agent-memory-6-graphiti/)
7. [Letta: an agent that edits its own memory](/posts/2199/01/agent-memory-7-letta/)
8. [Honcho: a reasoner that works in the background](/posts/2199/01/agent-memory-8-honcho/)
9. [The experiment: 67 changed facts](/posts/2199/01/agent-memory-9-the-experiment/)

<!-- /SERIES -->

[Part 2](/posts/2199/01/agent-memory-2-the-map/) placed memory systems on two
axes: who writes the memory (nobody, a pipeline, the answering agent, or a
background process), and whether the read path inserts all of it into the
prompt or selects part of it. This part puts the memory features of the large
assistants on that map, from what their makers have published, before the
rest of the series takes the open systems apart call by call.

## What can be known

None of these products can be run as a library, and none publishes its
prompts. What follows comes from three kinds of source, and I label which is
which:

- **The vendors' own pages**: announcements, help-centre articles and
  developer documentation. They say what a feature does and what the user can
  control, rarely how it works.
- **Reverse-engineering write-ups** by people who asked the model to describe
  its own context. They are informative and unverifiable, and the products
  change under them.
- **Third-party guides**, many written by companies that sell memory products.
  I have not relied on those.

Everything here describes the products as of October 2026. Several of them
changed in the last six months, and they will change again.

## ChatGPT: from saved notes to a background rewrite

OpenAI's own history of the feature, from its June 2026 post
[Dreaming: Better memory for a more helpful ChatGPT][openai-dreaming], has
three stages.

**2024: saved memories.** "Memory first launched in April 2024 (also known as
saved memories). The feature let you ask ChatGPT to remember information and
carry it forward into future chats." The model saved a short fact through a
tool call, during the conversation, and the saved facts were inserted into
later prompts. In the terms of this series, that is the agent writing during
its turn, with an insert-everything read path: Letta's core memory, in
[part 7](/posts/2199/01/agent-memory-7-letta/), in a product. OpenAI
describes its weakness plainly:

> Saved memories were only written during the conversation and relied on
> strong cues to decide when to trigger memory, such as an instruction to
> "remember I'm traveling to Singapore in July." In practice, interacting with
> this system could feel like talking to someone who took a few notes, but
> still forgot everything that wasn't written down. Saved memories also tend
> to go stale over time and eventually become incorrect or irrelevant.

Both failures are measured later in this series. An agent that writes memory
in the middle of its turn often does not write at all: in the LongMemEval run
of [part 9](/posts/2199/01/agent-memory-9-the-experiment/), Letta's agent
answered "Congratulations on hitting 600 followers!" and wrote nothing down,
18 times. And a line that was true when it was written stays in the prompt
after it stops being true.

**2025: referencing chat history.** "In April 2025, we updated ChatGPT's
memory by giving the model the ability to reference chat context outside of
the saved memories list; this was done by introducing the first version of
dreaming—a method for ChatGPT to automatically curate memories in the
background by referencing chat history."

What that looked like from inside is known only from reverse engineering. In
December 2025, before the next change, [Manthan Gupta asked ChatGPT to
describe its context][gupta] and reported this layout for every message:

```
[0] System Instructions
[1] Developer Instructions
[2] Session Metadata (ephemeral)
[3] User Memory (long-term facts)
[4] Recent Conversations Summary (past chats, titles + snippets)
[5] Current Session Messages (this chat)
[6] Your latest message
```

The user memory block held the saved facts (33 in his case), inserted into
every prompt. The recent-conversations block held about fifteen entries, each
a timestamp, a chat title and snippets of the user's own messages, not the
assistant's. And he found no search over past conversations at all: "No
vector databases. No RAG over conversation history." Treat the details with
the caution the author asks for; the shape is consistent with what OpenAI
says, a precomputed summary inserted whole rather than a retrieval step.

**June 2026: dreaming as the memory.** The current system "is built on top of
dreaming": a background process that "allows ChatGPT to learn from many
conversations and synthesize ChatGPT's memory state". The user sees it as a
memory summary page, where it can be corrected, and where a topic can be
marked "Don't mention this again". The [Memory FAQ][openai-faq] describes the
two experiences side by side: "Improved Memory continually updates a broader
summary of relevant context. Legacy saved memories use a more explicit list of
individual memory items." It also says what the memory may draw on, depending
on plan and region: past chats, saved memories, custom instructions, files in
the Library, and connected apps such as Gmail.

OpenAI's post states the problem the change addresses in the same terms as
this series. Its third goal for memory is to "stay current over time", and
its example is a trip: memory should move from "You're going to Singapore in
July" to "You went to Singapore in July 2026" once the trip is over. Its
second example is a vegetarian user asking for meal ideas. The post reports
gains on OpenAI's own evaluations for each goal, in charts without a public
test set, and says that serving the new system to free users became possible
after a roughly fivefold cut in compute.

On the map, ChatGPT moved from the agent writing during the turn to a
background process writing between conversations, keeping the
insert-a-summary read path. That is the textual-memory design of
[part 4](/posts/2199/01/agent-memory-4-textual-memory/), at the scale of
hundreds of millions of users, with the profile rewritten in the background
instead of after each session.

## Claude: topics written as you chat, search on request

Anthropic ships three different memory designs, one per product, and
documents all three.

**The Claude app.** Memory arrived in September 2025 for Team and Enterprise
plans, then for Pro and Max in October 2025 and for free users on 2 March
2026, according to Anthropic's [release notes][claude-notes]. The first
version generated a summary: in the help centre's words, "This synthesis is
updated every 24 hours and provides context for every new standalone
conversation." On 10 July 2026 that changed. The current
[help article][claude-memory] says "Claude saves memory as a set of individual
topics as you chat, rather than summarizing conversations after they end",
and Anthropic's [August 2026 post][claude-memory-blog] describes the entries
as "short files, one per topic", each of which the user can read, edit or
delete. Health, politics, religion and similar subjects stay out unless the
user opts in, and some data (government ID numbers, financial account
numbers) is never saved. Each project has its own memory.

So the app moved in the opposite direction to ChatGPT: from a background
summary to entries the model writes while the conversation happens. The
documentation does not say whether every topic is inserted into every
conversation or only the relevant ones are read.

**Search over past chats** is a separate feature, on paid plans. It is plain
retrieval, and the help article says so: "These searches use
Retrieval-Augmented Generation (RAG) and will appear as tool calls during your
conversations", with citations linking to the original chats. That is the
"nobody writes, select" cell of the map: no memory is written, and the model
searches the raw history when it decides to.

**Claude Code** keeps two kinds of memory in plain files, documented in
[How Claude remembers your project][claude-code-memory]:

- `CLAUDE.md` files, which the user writes, hold instructions and are loaded
  whole at the start of every session.
- *Auto memory*, which the model writes. Each project gets a directory with a
  `MEMORY.md` index and one topic file per memory. "The first 200 lines of
  `MEMORY.md`, or the first 25KB, whichever comes first, are loaded at the
  start of every conversation." The topic files are not: "Claude reads them on
  demand using its standard file tools when it needs the information." Each
  memory carries a type (`user`, `feedback`, `project` or `reference`), and
  Claude Code stamps a `modified` timestamp on each write, so that "the
  timestamp shows how current the fact is, both to you and to Claude when it
  reads the memory back".

That is both columns of the map in one design: a short index that is always
inserted, and detail that is selected. It also answers, with a time stamp, the
problem the experiment in this series keeps running into: an undated line
("recently hit 500 followers") reads the same months later.

**The memory tool in the API** hands the design to the developer. The
[memory tool][claude-memory-tool] is a directory, `/memories`, that the model
views and edits through six commands (`view`, `create`, `str_replace`,
`insert`, `delete`, `rename`). The application executes them against its own
storage: "Claude requests file operations, and your application executes
them." When the tool is enabled, the API adds an instruction to the system
prompt that begins "IMPORTANT: ALWAYS VIEW YOUR MEMORY DIRECTORY BEFORE DOING
ANYTHING ELSE." It is meant to pair with compaction of long conversations:
the summary keeps the context small, and the files keep what must survive
summarisation. This is MemGPT's design reduced to files: the agent writes, and
it reads what it chooses to read.

## Gemini: past chats, renamed "memory"

Google documents what the user controls and very little about the mechanism.

- In February 2025 the Gemini app began to [recall past chats][gemini-recall]
  for Gemini Advanced subscribers: "Starting today, Gemini can now recall your
  past chats to provide more helpful responses."
- In August 2025 this became a [personal-context setting][gemini-context]
  that is on by default ("This setting is on by default to help Gemini give
  you more relevant responses"), alongside Temporary Chats, which are kept out
  of personalisation.
- In January 2026 [Personal Intelligence][gemini-pi] connected Gmail, Photos,
  YouTube and Search history, for paying subscribers in the US at first.
- In March 2026 Google [renamed "past chats" to "memory"][gemini-import] and
  added an import: the user pastes a summary written by another assistant, and
  Gemini saves it "to your Gemini context".

The [help page][gemini-help] says that "Gemini can learn from your chats to
understand more about you and your world", and to find out what it used, the
user is told to ask it: "Did you use any info from past chats?" Whether it
retrieves earlier chats or keeps a summary is not stated. A separate feature,
saved info (now called instructions for Gemini), holds facts and preferences
that the user writes directly. On the map, saved info is the user writing and
the whole of it inserted; the memory of past chats cannot be placed from what
is published.

## Mastra's Observational Memory: the same idea, in the open

One open-source system makes the background-rewriter design explicit, and it
is worth putting next to the products because its code and its numbers are
public. In Mastra's [Observational Memory][mastra-om], two background agents
watch a conversation. When the raw message history passes a token threshold
(30,000 by default, according to the [documentation][mastra-docs]), an
Observer turns it into dated, prioritised observations, and the observed
messages are dropped from the prompt. When the observations pass a second
threshold (40,000 by default), a Reflector rewrites the whole log: "combining
related items, reflecting on patterns, and removing observations that have
been superseded."

There is no retrieval and no database. The log sits at the start of the
prompt and changes only when the Observer or Reflector runs, so the prompt
prefix stays the same between turns and can be served from the provider's
prompt cache. Mastra reports 94.87% on LongMemEval with gpt-5-mini answering,
and 84.23% with gpt-4o. Those are the vendor's own figures, measured on the
full benchmark; they are not comparable with the trimmed slice I ran in part 9.

It is the most developed version of the textual-memory family, and it is as
much a way of compressing a long context as a memory of a user, because the
log replaces the message history it was built from.

## The products on the map

| Product | Who writes | When | What the read path does | What the user can see and change | Source |
|---|---|---|---|---|---|
| ChatGPT, saved memories (2024–) | the model, through a tool, or the user's request | during the conversation | all saved facts inserted | a list of memories, editable | OpenAI |
| ChatGPT, memory from chat history (2025–) | a background process ("dreaming") | between conversations | a synthesised summary inserted; earlier, about 15 recent-chat snippets | a memory summary page, corrections, "don't mention this again" | OpenAI; context layout reverse-engineered |
| Claude app memory (July 2026–) | the model | during the conversation, one topic per entry | not documented | topics, each editable; sensitive topics off by default | Anthropic |
| Claude past-chat search | nobody | n/a | retrieval through tool calls, with citations | the source chats | Anthropic |
| Claude Code auto memory | the model | during the session | an index always loaded; topic files read on demand | plain files | Anthropic |
| Claude API memory tool | the model | during the session | files the model chooses to view | whatever the application exposes | Anthropic |
| Gemini memory of past chats | not documented | not documented | not documented | on/off; ask Gemini what it used | Google |
| Mastra Observational Memory | two background agents | when token thresholds are crossed | the whole observation log inserted | the log | Mastra (open source) |

Three things stand out.

**The products converged on text.** None of them advertises a vector store
of extracted facts or a knowledge graph, which is what most memory papers
build. What they ship is a summary or a list of short entries, inserted into
the prompt, plus, at most, a search over the raw chats. That is the left
column of the map and the "nobody writes" row, the two designs the
experiment in part 9 found cheapest.

**They disagree about who should write.** ChatGPT moved writing out of the
conversation into a background process, and gives as its reason that notes
taken during the conversation miss what was not flagged and go stale. Claude's
app moved the other way, from a daily summary to entries written as the user
chats. Both are defensible, and the system parts of this series show the cost
of each: an agent writing in its turn forgets to write
([part 7](/posts/2199/01/agent-memory-7-letta/)); a rewrite of the whole
profile can change what it was not asked to change
([part 4](/posts/2199/01/agent-memory-4-textual-memory/)).

**The problem they name is staleness.** OpenAI's Singapore trip is the
knowledge-update problem that the rest of this series measures: a fact that
was true, then changed, and must not be acted on in its old form. The
products' answers so far are a background rewrite (ChatGPT), a timestamp on
each entry (Claude Code), and controls that let the user correct the memory
by hand (all of them).

The next five parts open the systems whose code can be read, starting with
the design that the products resemble most:
[part 4, textual memory](/posts/2199/01/agent-memory-4-textual-memory/).

## References

<!-- REFS -->



<!-- /REFS -->

Vendor documentation and announcements:

- OpenAI, [Dreaming: Better memory for a more helpful ChatGPT][openai-dreaming] (June 2026)
- OpenAI Help Center, [Memory in ChatGPT][openai-faq]
- Anthropic, [Use Claude's chat search and memory to build on previous context][claude-memory]
- Anthropic, [Claude's memory works everywhere, and you decide what's in it][claude-memory-blog] (August 2026)
- Anthropic, [Claude release notes][claude-notes]
- Anthropic, [How Claude remembers your project][claude-code-memory] (Claude Code documentation)
- Anthropic, [Memory tool][claude-memory-tool] (Claude API documentation)
- Google, [The Gemini app can now recall past chats][gemini-recall] (February 2025)
- Google, [Gemini app personalizes responses based on past chats, plus new privacy controls][gemini-context] (August 2025)
- Google, [Personal Intelligence: Connecting Gemini to Google apps][gemini-pi] (January 2026)
- Google, [How to switch to Gemini: Import your chats and data from other AI apps][gemini-import] (March 2026)
- Google, [Get personalization with memory of your past Gemini chats][gemini-help] (Gemini Apps Help)
- Mastra, [Observational Memory][mastra-om] (research post) and [documentation][mastra-docs]

Reverse engineering:

- Manthan Gupta, [I Reverse Engineered ChatGPT's Memory System, and Here's What I Found!][gupta] (December 2025)

[openai-dreaming]: https://openai.com/index/chatgpt-memory-dreaming/
[openai-faq]: https://help.openai.com/en/articles/8590148-memory-faq
[gupta]: https://manthanguptaa.in/posts/chatgpt_memory/
[claude-memory]: https://support.claude.com/en/articles/11817273-using-claude-s-chat-search-and-memory-to-build-on-previous-context
[claude-memory-blog]: https://claude.com/blog/claudes-memory-works-everywhere-and-you-decide-whats-in-it
[claude-notes]: https://support.claude.com/en/articles/12138966-release-notes
[claude-code-memory]: https://code.claude.com/docs/en/memory
[claude-memory-tool]: https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
[gemini-recall]: https://blog.google/feed/gemini-referencing-past-chats/
[gemini-context]: https://blog.google/products-and-platforms/products/gemini/temporary-chats-privacy-controls/
[gemini-pi]: https://blog.google/innovation-and-ai/products/gemini-app/personal-intelligence/
[gemini-import]: https://blog.google/innovation-and-ai/products/gemini-app/switch-to-gemini-app/
[gemini-help]: https://support.google.com/gemini/answer/16598469
[mastra-om]: https://mastra.ai/research/observational-memory
[mastra-docs]: https://mastra.ai/docs/memory/observational-memory

<!-- SERIES -->

---

[← Part 2: A map of memory systems](/posts/2199/01/agent-memory-2-the-map/) · [Part 4: Textual memory: one profile, rewritten →](/posts/2199/01/agent-memory-4-textual-memory/)

<!-- /SERIES -->
