---
post: _drafts/agent-memory/2199-01-01-agent-memory-9-assistants.md
type: map
status: draft
---

# Brief: What ChatGPT, Claude and Gemini ship (part 9)

Shared material is in `series.brief.md`. Sources, checks and the Mastra run: `9-assistants.sources.md`. Earlier material: `v1/2199-01-01-agent-memory-3-frontier-assistants.md` and Anton's 13 notes on it. This brief was rewritten on 2026-11-16 from Anton's spoken notes (`~/tmp-spoken-plans/blog/next-part.txt`), starting from the map skeleton, not from v1's order.

## Reader

The series reader, and a wider one: anyone who uses these assistants or coding agents daily and wondered what "memory" means in them. Many will read only this part, so it stands alone: every mechanism it borrows from another part is explained here in a sentence or two, and the link is further reading. It is the last part and closes the series.

## The problem

ChatGPT, Claude, Gemini and the coding agents from the same companies all carry information from one conversation to the next, and each has changed how in the last two years. Their makers publish what the user can control, rarely how it works, and the products change under any description. A reader cannot tell what these products actually do, whether they resemble the memory systems in papers and open libraries, or what to expect from them.

## What the reader should leave with

1. The products converged on text: a summary, a list of short entries or plain files, put into the prompt, plus, at most, a search over past chats. None ships a vector store of extracted facts or a knowledge graph as its memory.
2. They disagree about who writes, and each choice has a known failure: ChatGPT and Codex moved writing to a background process; Claude's app moved to the model writing as the user chats; Gemini CLI asks the user to approve each change.
3. The problem they name is staleness, a fact that was true and changed. Their answers so far: a background rewrite, a timestamp on each entry, and controls for the user.
4. Where code exists, the mechanism can be read; where it does not, say which kind of source each claim rests on.

## Outline

| Section | Claim it supports | Show in full | Figure |
|---|---|---|---|
| **Opening** (one section, with the two questions) | The engineering problem in general terms. The assistants people use daily all remember now. Two questions place any memory design: **who writes** (the user, the model during its turn, a process after or between conversations) and **how it reads** (everything inserted, or a search selects), each with a one-line example. What this part does; no notebook, because the products cannot be run as libraries, but the open code is linked where it exists, and one open design was run | none | none |
| **What is known** | The word of caution: four kinds of source, each with a one-letter mark used through the post: **[V]** the vendor's own page, **[C]** code or a prompt the vendor published, **[R]** reverse engineering (people asking the model about its context, or what a session shows from inside), **[T]** a third party. As of November 2026; products change and can run several versions at once | none | none |
| **ChatGPT and Codex (OpenAI)** | Subsections. **ChatGPT, saved memories (2024)**: the model writes during the chat; everything inserted. **Referencing chat history (2025)**: what reverse engineering found (Gupta's layout; Willison's four headings). **Dreaming (2026)**: OpenAI's own words on why notes taken during the chat failed; its goals; the Singapore example; the memory summary page (re-checked against the saved copy). **Codex**: from the code, a two-phase pipeline (extraction per conversation, then consolidation by an agent with no network) into files; only a summary is loaded; the model writes only when asked; v2's prompts in full | OpenAI quotes; Gupta's layout; Codex v2 Phase 1 and Phase 2 prompts; Codex read prompt (v2) | `chatgpt-context`, `codex-memory` |
| **Claude (Anthropic)** | Four separate products, each a subsection. **The app**: daily summary (2025) → topics written as you chat (July 2026); what is documented about reading, and what reverse engineering found before the change. **Past-chat search**: retrieval as tool calls. **Claude Code**: CLAUDE.md written by the user; auto memory written by the model; an index loaded at start, topic files read on demand; the `modified` timestamp solves the undated-line problem; the instructions the model gets, in full, seen from inside a session. **The API memory tool**: for a developer building an agent on the API; the application stores the files; the six commands; the instruction the API adds; pairing with context editing and compaction | Claude Code's memory instructions; the memory tool's added system prompt | `claude-code-memory` |
| **Gemini (Google)** | **The app**: past chats (2025), on by default, renamed "memory" (2026); saved info written by the user; import from another assistant; how it reads is not documented. **Personal Intelligence**: Google's own document: the model searches connected apps and past chats and "packs" what it finds into context: a search that selects. **Gemini CLI**, from the code: `save_memory` (2025) replaced by plain files in four tiers (2026), an index plus topic files like Claude Code; Auto Memory proposes patches from idle sessions, and the user approves each | Gemini CLI's memory instructions; Auto Memory's rules (excerpt) | none |
| **Other assistants** | One paragraph each, only from [V] or [C] sources: Grok (its published prompt: memory is past chats, shown as referenced chats), Meta AI, Mistral (Le Chat, now Vibe), Perplexity | Grok's memory block | none |
| **Mastra's Observational Memory: the background rewrite, in open code** | What Mastra is and why it is here: the design the products describe (a background process rewrites a text log that sits in the prompt) in code that can be read and run, with published benchmark numbers. How it works: Observer and Reflector, thresholds and their reason, buffering, the observed messages leave the prompt (the chat is compressed automatically), thread scope (a new thread starts empty unless retrieval mode is on), the prompts. **One run on one benchmark question**: what the log held, where the changed value sat, the wrong answer, the right answer once the tail was observed, what the Reflector kept. Its LongMemEval numbers as the vendor's own | Observer prompt excerpt (state changes, dates); Reflector's consolidation rules; read instructions (KNOWLEDGE UPDATES); one observation block from the run | `observer-reflector` |
| **The products side by side** | The table (product, who writes, when, read path, what the user sees, source mark), the products on the two questions, and when each feature shipped | table | `products-map`, `assistants-timeline` |
| **Three observations** | Converged on text; disagree on who writes; the named problem is staleness. Each tied to the series' experiment in a sentence that stands alone. A fourth only if the facts support it: the coding agents converged on the same file layout (index loaded, topic files read on demand) | none | none |
| **What to take from the series** | The six ideas of the series in a short list; where to read more (the decision guide in part 8, the notebooks, the repository) | none | none |
| References | Vendor pages, code at pinned commits, reverse engineering, each with its mark | | |

## Running example

Not used. The series' example is not traced here. Only the note that OpenAI's dreaming post uses a vegetarian user asking for meal ideas, the same kind of test as the series' example, in neutral words. The Mastra run uses LongMemEval question `6a1eabeb` (a 5K personal best that changes, from part 8), introduced in this part in its own sentences.

## Numbers

| Number | Out of what | From where | Compared with | So what |
|---|---|---|---|---|
| ~33 saved facts, ~15 recent-chat entries | one user's ChatGPT context | Gupta, Dec 2025 [R] | none | The shape, not the detail |
| 2,500 tokens | the summary Codex loads into a new session | Codex code [C] | the rest read on demand | Only a summary is inserted |
| 10,000 bytes | Codex v2's summary cap | Codex prompt [C] | | |
| 200 lines / 25 KB | the part of `MEMORY.md` Claude Code loads | Claude Code docs [V] | | Why an index plus topic files |
| 30,000 / 40,000 tokens; 6,000 | Mastra's thresholds; buffering interval | Mastra code and docs [C/V] | | When the Observer and Reflector run |
| 94.87% / 84.23% | Mastra on LongMemEval_s, gpt-5-mini / gpt-4o answering | Mastra [V] | not comparable with part 8 | The vendor's own |
| 108,000 tokens → 2,652-token log + 28,703 tokens unobserved; 28,583-token answer prompt; 7 Observer calls | one run, one question | `scripts/mastra/om_summary_output.txt` | the whole history | What the design keeps in the prompt |
| 4,040 tokens | the answer prompt once the tail was observed | same | 28,583 | |

Every product claim needs a date; re-check the dated ones before publishing.

## Figures to make

In `agent-memory-eval/scripts/diagrams/figures/`:
- `assistants-timeline` (`assistants_timeline.py`): one lane per vendor, 2024–2026, each feature dated, with its source mark. Replaces the planned `chatgpt-timeline`.
- `products-map` (`products_map.py`): the two questions as a grid; each product placed, with its mark.
- `chatgpt-context` (`chatgpt_context.py`): the reverse-engineered context layout as a stack, marked [R].
- `claude-code-memory` (`claude_code_memory.py`): CLAUDE.md and the index loaded at start, topic files read on demand, the `modified` stamp.
- `codex-memory` (`codex_memory.py`): Phase 1 per conversation → Phase 2 consolidation → files → what the next session gets.
- `observer-reflector` (`observer_reflector.py`): the context over time with Mastra's defaults, from the run.

Screenshots by Anton (own accounts, no personal data), each credited; list in the hand-over.

## Left out

- Third-party guides by companies selling memory products (used only to find primary sources).
- DeepSeek: no memory feature found in DeepSeek's own pages.
- Microsoft Copilot (Anton worked on it).
- Leaked system prompts; only prompts a vendor published or that a session shows from inside.
- Experiment tables (part 8); only sentences that stand alone.

## Links

- Repository: https://github.com/anton-dergunov/agent-memory-eval (the Mastra run in `scripts/mastra/`)
- Sources: `9-assistants.sources.md`

## Title and excerpt

- Title: "What ChatGPT, Claude and Gemini ship"
- Excerpt: "How memory works in ChatGPT, Claude, Gemini and their coding agents, from vendor pages, open code and one run, and how it compares with open memory systems."

## Anton's notes, and where each is handled

On v1 (2026-10):

| Note | Handled by |
|---|---|
| "Check it" (memory summary page) | ChatGPT, against the saved copy of OpenAI's post |
| "Do we happen to use the same example?" | Yes, the same kind; one neutral sentence |
| "Should probably go last" | Part 9 |
| "Rewrite: it solves this issue" | Claude Code |
| "How it reads?" | Claude app: documented / reverse engineered before July 2026 / unknown since |
| "Describe better… when I use APIs?" | The memory tool: who uses it and when |
| "How related to memory?" (Personal Intelligence) | Gemini: Google's document says the model searches past chats among the sources |
| "Why this system? How did you find it?" (Mastra) | Motivated in the section's opening; how it was found is not needed |
| "Is it from the prompt… auto summarized?" | Yes: observed messages leave the prompt |
| "Why these numbers? … Draw diagram" | `observer-reflector`; the docs' reason; the run |
| "Even if I start a new session?" | Thread scope: a new thread starts empty |
| "Why the *most*?" | Dropped |
| "Which map? … references between the parts must be minimal" | The two questions restated in the opening |

On the brief (2026-11-16, spoken):

| Note | Handled by |
|---|---|
| Stand alone; brief reminders of mechanisms from other parts | Every borrowed mechanism explained in a sentence |
| Opening + two questions in one section; "What is known" as a word of caution | Outline |
| One-letter marks for the source labels | [V] [C] [R] [T] |
| App, Claude Code and the API tool are separate things | Subsections |
| Gemini looks underpowered | Personal Intelligence document, Gemini CLI code |
| Other assistants, not Copilot | Other assistants section |
| Mastra: what it is, why here, bigger | Section opening, the run |
| Timeline; screenshots | `assistants-timeline`; screenshots by Anton |
| Close summarising the series | What to take from the series |
| Most effort on research and double-checking | `9-assistants.sources.md` |

## Open questions for Anton

- The OpenAI page copies and the screenshots (list in the hand-over).
