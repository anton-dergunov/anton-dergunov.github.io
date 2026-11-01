---
post: _drafts/agent-memory/2199-01-01-agent-memory-9-assistants.md
type: map
status: draft
---

# Brief: What ChatGPT, Claude and Gemini ship (part 9)

Shared material is in `series.brief.md`. Source: `v1/2199-01-01-agent-memory-3-frontier-assistants.md` and Anton's 13 notes on it.

## Reader

The series reader, and also a wider one: anyone who uses these assistants daily and wondered what "memory" means in them. Many readers will arrive here first, so this part is fully self-contained. It is the last part and closes the series.

## The problem

ChatGPT, Claude and Gemini all remember things between conversations now, and each has changed how in the last year. Their makers publish what the user can control, rarely how it works. A reader cannot tell whether these products resemble the memory systems in papers, or what to expect from them.

## What the reader should leave with

1. The products converged on text, not on vector stores of extracted facts or knowledge graphs. They ship a summary or a list of short entries put into the prompt, plus, at most, a search over past chats.
2. They disagree about who should write: ChatGPT moved writing into a background process, and Claude's app moved to entries written during the chat. Each choice has a known failure mode.
3. The problem they name is staleness, a fact that was true and changed. Their answers so far are a background rewrite, a timestamp on each entry, and controls for the user to correct it.
4. What can be known about a product is limited. Label each source: the vendor's own page, reverse engineering, or a third party.

## Outline

| Section | Claim it supports | Evidence or artefact to show | Figure |
|---|---|---|---|
| Opening | The assistants readers use every day, what changed recently, and what this part can and cannot say | Problem above | none |
| Two questions to ask of any memory | Who writes, and whether everything is inserted or a search selects, in this part's own words with a short example. No reference to "the map" (Anton). | Series terms | none |
| What can be known | Three kinds of source, labelled; "as of" date | v1 | none |
| ChatGPT | Saved memories (2024: the model writes during the chat; everything inserted) → referencing chat history (2025) → dreaming as the memory (2026: a background process synthesises a summary). OpenAI's own words on the weakness of notes taken during the conversation. Its examples (the Singapore trip; a vegetarian user asking for meal ideas, the same kind of test this series uses). | v1; check "memory summary page" against the source (Anton: "Check it") | `chatgpt-timeline`; the reverse-engineered context layout drawn as a stack |
| Claude | The app: from a daily summary to topics written as you chat ("how it reads": say what is documented about reading and what is not). Past-chat search: plain retrieval. Claude Code: an index always loaded plus topic files read on demand, each stamped with a modified time, which addresses the undated-line problem (Anton: rewrite as "it solves this"). The API memory tool: when a developer would use it (Anton: "describe better"), what the application implements, and its pairing with compaction. | v1 | `claude-code-memory` |
| Gemini | Past chats, renamed "memory"; saved info written by the user; what Personal Intelligence (connected apps) has to do with memory (Anton: "how related?"), or cut | v1 | none |
| Mastra's Observational Memory | Why it is here `[TODO Anton: why Mastra, and how you found it]`. How the Observer and Reflector interact, as a diagram (Anton). Answer his questions: the observed messages are dropped from the prompt of the model the user talks to, so the chat is compressed automatically; what happens in a new session `[check the Mastra docs]`; why these thresholds (defaults, from the docs). Its LongMemEval figures labelled as the vendor's and not comparable. "The most developed version" scoped or removed (Anton: "why the most?"). | v1; Mastra docs | `observer-reflector` |
| The products side by side | The table, and the products on the two choices | v1 table | `products-map` |
| Three observations | Converged on text; disagree on who writes; the named problem is staleness. Each is tied to what the experiment found, stated here in a sentence so it stands alone (e.g. "in a benchmark run in this series, an agent that wrote during its turn often noticed a change and did not write it down"). | v1, findings | none |
| What to take from the series | A short close: the ideas of the series in a paragraph, and where to read more (the decision guide in part 8, the notebooks) | Series ideas | none |

## Running example

Not used, except the note that OpenAI's post uses a similar vegetarian example (Anton asked whether we use the same one: the series' example is a vegetarian user who becomes pescatarian).

## Numbers

| Number | Out of what | From where | Compared with | So what |
|---|---|---|---|---|
| ~33 saved facts, ~15 recent-chat entries | one user's ChatGPT context | Gupta, reverse engineering, Dec 2025 | none | The shape, not the detail; marked unverifiable |
| 200 lines / 25 KB | the part of MEMORY.md loaded at start | Claude Code docs | none | Why an index plus topic files |
| 30,000 / 40,000 tokens | Mastra's default thresholds | Mastra docs | none | When the Observer and Reflector run |
| 94.87% / 84.23% | Mastra on LongMemEval, with gpt-5-mini / gpt-4o | Mastra (vendor) | not comparable with part 8 | Labelled as the vendor's |

Every product claim needs a date; re-check all of them before publishing.

## Figures to make

`chatgpt-timeline`, `claude-code-memory`, `observer-reflector`, `products-map` (new).

## Left out

- Third-party guides by companies selling memory products.
- Experiment tables (part 8); only sentences that stand alone.

## Links

- The vendor sources listed in v1 part 3 (OpenAI Dreaming post and FAQ; Anthropic help, blog, release notes, Claude Code docs, memory tool docs; Google posts and help; Mastra post and docs; Gupta's write-up)

## For search and for employers

- Title: "What ChatGPT, Claude and Gemini ship"
- Excerpt: "How the memory in ChatGPT, Claude and Gemini works, as far as their makers say, and how it compares with open memory systems."

## Anton's notes on v1, and where each is handled

| Note | Handled by |
|---|---|
| "Check it" (memory summary page) | ChatGPT section, re-checked against the source |
| "Do we happen to use the same example?" | Yes, similar; noted |
| "Should probably go last" | Now part 9 |
| "Rewrite: it solves this issue" | Claude Code |
| "How it reads?" | Claude app |
| "Describe better… when I use APIs?" | API memory tool |
| "How related to memory?" (Personal Intelligence) | Explained or cut |
| "Why this system? How did you find it?" (Mastra) | `[TODO Anton]` |
| "Is it from the prompt… auto summarized?" | Mastra section |
| "Why these numbers? … Draw diagram" | `observer-reflector`; defaults from the docs |
| "Even if I start a new session?" | Mastra section, after checking the docs |
| "Why the *most*?" | Scoped or removed |
| "Which map? … references between the parts must be minimal" | No "map" references; the two questions restated here |

## Open questions for Anton

- Why Mastra, and how you came across it.
