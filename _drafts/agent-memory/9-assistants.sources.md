# Part 9 (the assistants): sources, checks and runs

Written 2026-11-16. Every product claim in the post has a row here, with its mark, its source and the date it was checked. Marks: **V** the vendor's own page; **C** code or a prompt the vendor published; **R** reverse engineering, or seen from inside a session; **T** a third party (used only to point at a primary source, or marked as such in the post).

Code was read at pinned commits: openai/codex `3257e1b3eb04a43a8721ad0e59470327807eb844`; google-gemini/gemini-cli `4fa64e71b9b4e1bb65a86cc2863574f561b82340`; mastra-ai/mastra tag `@mastra/memory@1.41.1` = commit `d60ba71be015e2acbdc303208a14563902fb1f39` (the run's package version; `main` was read too, at 1.41.2-alpha.2); xai-org/grok-prompts `main` (last push 2025-11-17).

Liquid: the Codex templates contain double-brace placeholders. They are not copied into this file; in the post they sit inside a raw block.

## OpenAI: ChatGPT

Checked 2026-11-16 against copies saved by Anton (HTML and PDF; quotes from the HTML), kept in `agent-memory-eval/private/part9-sources/web/openai/`.

| Claim | Mark | Source |
|---|---|---|
| Post dated 4 June 2026; history: "Memory first launched in April 2024 (also known as saved memories)…"; the "few notes" paragraph; April 2025 first version of dreaming; "a significantly more capable and compute-efficient memory architecture built on top of dreaming"; dreaming "was never sufficient as a standalone memory system"; "memory summary page"; three goals (carry forward; follow preferences, "a vegetarian user asks for meal prep suggestions"; "Stay current over time", Singapore); evals labelled "2024 : Saved memories", "2025 : Saved memories + Dreaming V0", "2026 : Dreaming V3", charts only; "reduced the compute required to serve dreaming to Free users by approximately 5x"; Plus and Pro in the US first | V | Dreaming post (reader copy and full copy) |
| Test 13 Feb 2024; "Memory updated" notice; "ask it to remember something specific or let it pick up details itself"; updates: 5 Sep 2024 all plans; 10 Apr 2025 chat history (Plus, Pro); 3 Jun 2025 a "lightweight version" for free users | V | "Memory and new controls for ChatGPT" with its dated updates |
| Release notes: 29 Apr 2024 Plus; 8 May 2025 EU (off by default); 15 Oct 2025 automatic management of saved memories ("how recent a detail is and how often you talk about a topic"), version history; 15 Jan 2026 "can now more reliably find specific details from your past chats… appears as a source"; 5 May 2026 memory sources on all plans, "faster at searching past conversations"; 4 Jun 2026 "Memory that stays more up to date", "twice as much memory capacity"; 12 Jun 2026 memory summary controls | V | ChatGPT release notes |
| FAQ: sources list; "Don't mention this again" ("reduces future references to the information. It does not delete the original source."); "The memory summary is a high-level view…"; "Does ChatGPT search my history for every response? No. ChatGPT looks for relevant context when it is likely to improve a response."; "Improved Memory continually updates a broader summary…" | V | Memory in ChatGPT (help article; its URL slug is now `memory-in-chatgpt`) |
| Corrections from the check: "Don't mention this again" is in the FAQ, not the post; the vegetarian example is "meal prep suggestions"; ChatGPT searches past chats since January 2026, so its read path is both kinds (the products map and table were updated) | — | — |
| Context layout [0]–[6]; 33 facts; ~15 recent-chat entries; "No vector databases. No RAG over conversation history." | R | Manthan Gupta, 2025-12-09 (before the January 2026 change) |
| Four headings of the injected chat-history summary | R | Simon Willison, 2025-05-21 |

## OpenAI: Codex (C, commit 3257e1b)

| Claim | Where |
|---|---|
| The feature flag `memories` is `Stage::Stable` with `default_enabled: false` | `codex-rs/features/src/lib.rs` (FeatureSpec MemoryTool) |
| Docs: "Memories are off by default"; enable in Settings > Personalization or `memories = true` under `[features]` | learn.chatgpt.com/docs/customization/memories (V, fetched) |
| A fresh profile with memories on gets v2 (`memories_v2/`); an existing `memories/` stays on v1 | `codex-rs/core/src/config/mod.rs` lines 3786–3798; docs agree |
| Defaults: 2 rollouts per startup; age ≤ 10 days; idle ≥ 6 hours (doc comment "> 12h recommended"); ≥ 25% rate limit left; 256 raw memories for consolidation; unused > 30 days drops out | `codex-rs/config/src/types.rs` lines 58–63 |
| When it runs: at the start of a root session, not ephemeral, not a sub-agent; in the background; Phase 1 then Phase 2 | `codex-rs/memories/README.md` |
| Phase 1: per rollout, in parallel with a cap; output `raw_memory`, `rollout_summary`, `rollout_slug`; secrets redacted; no-op allowed | README; `stage_one_system.md` (30 KB) |
| Phase 2: one global lock; files `raw_memories.md`, `rollout_summaries/`; git baseline under the memories root; `phase2_workspace_diff.md`; a consolidation sub-agent with "no approvals, no network, and local write access only" | README |
| v1 outputs: `memory_summary.md` (always loaded, first line `v1`, User Profile ≤ 350 words), `MEMORY.md` (handbook, grep), `skills/` | `consolidation.md` |
| Forgetting: deleted inputs in the workspace diff are "forgetting / stale-cleanup queue"; "Delete only memory supported by deleted inputs"; "fresher validated evidence usually wins"; "If evidence conflicts and validation is unclear, preserve the uncertainty explicitly" | `consolidation.md` lines 157–177, 334–350, 787 |
| v2 (added 2026-09-08, PR #43813): Phase 1 returns `rollout_summary` and `rollout_slug` only; Phase 2 writes `memory_summary.md` only, "comfortably under 10,000 UTF-8 bytes"; "later corrections supersede earlier claims" | `stage_one_system_v2.md`, `consolidation_v2.md` |
| Read path: `memory_summary.md` injected into developer instructions, truncated at 2,500 tokens; the rest read with tools on demand | `ext/memories/src/prompts.rs`, `ext/memories/src/lib.rs` |
| The model writes only on explicit request: one small note under `extensions/ad_hoc/notes/`, applied by consolidation | `read_path.md`, `read_path_v2.md` |
| Citations block `<oai-mem-citation>` at the end of a reply | `read_path*.md` |
| First memory commit 2026-02-10 (#11200); no release note mentions memories | `gh api` commits / releases |
| README is stale on one path (it names `read/templates/…`; the template is under `ext/memories/templates/`) | README vs tree |
| Docs mention "Computer History" (macOS); the `chronicle` flag is under development, off | docs; `features/src/lib.rs` |

## Anthropic: Claude

| Claim | Mark | Source |
|---|---|---|
| Release notes: 2025-08-11 search past chats (Max, Team, Enterprise); 2025-09-11 memory for Team, incognito chats; 2025-09-18 Enterprise; 2025-10-23 Max (and Pro); 2026-03-02 "Memory from chat history" for all users incl. free; 2026-07-09 Reflect (requires memory); 2026-07-10 "individual, categorized entries that Claude reads and updates"; 2026-08-25 memory across chat and Cowork in the cloud, editable topics, sensitive-topics setting | V | support.claude.com release notes, fetched |
| Help article (updated this week): topics as you chat, "rather than summarizing conversations after they end"; legacy: "This synthesis is updated every 24 hours…"; reading not documented; sensitive topics off by default, list; never saved: government ID numbers, criminal history, financial account numbers, immigration status; per-project memory; per-chat Memory toggle; incognito; chat search is RAG shown as tool calls; memory on by default for Free/Pro/Max/Ultra; Team/Enterprise orgs created on or after 2026-10-31 start with it on | V | support.claude.com/en/articles/11817273, fetched |
| Blog: "Claude now adds topics to memory as you chat, instead of summarizing conversations after they end"; "Mention that your project deadline moved to September, and your next conversation already knows…"; "a list of files under Topics in Memory settings, where you can read, edit, or delete each one. The files are short" (v1's "short files, one per topic" is not on the page) | V | claude.com blog, 2026-08-25, raw page checked |
| Sep 2025 (before memory reached Pro): "starts every conversation with a blank slate"; recall by searching raw history with two tools, `conversation_search` and `recent_chats`, only when invoked | R | Shlok Khemani, shloked.com, via Simon Willison 2025-09-12, fetched |
| Dec 2025 (the daily-summary version): prompt order system → `<userMemories>` block of distilled facts → history → message; background updates "not immediate"; a `memory_user_edits` tool; `conversation_search` (query, max_results 1–10) and `recent_chats` (n 1–20, before/after) called "only when it determines that past context is relevant"; his caveats | R | Manthan Gupta, 2025-12-14, fetched |
| No reverse engineering found of the topic version (after 2026-07-10) | — | searches 2026-11-16 |
| Claude Code: CLAUDE.md written by the user; auto memory by Claude; index `MEMORY.md` + topic files; first 200 lines or 25KB loaded; topic files read on demand; `modified` ISO 8601 in frontmatter "shows how current the fact is, both to you and to Claude"; warns near the limit and errors past it; four types | V | code.claude.com/docs/en/memory, fetched |
| Claude Code's instructions to the model (the "# Memory" block): name/description/type frontmatter; one fact per file; one-line pointer in `MEMORY.md`; update rather than duplicate; delete wrong memories; don't save what the repo records | R | seen in a Claude Code 2.1.314 session (VS Code), 2026-11-16; saved in the scratchpad's `src/claude-code-memory-block.md`; the session's own path is replaced in the post |
| Difference between the docs and the session's block: the docs name the frontmatter field `type`; the session's block nests it under `metadata:` | R/V | both, compared |
| API memory tool (the added system prompt compared by eye with the fetched page): `memory_20250818`; released 2025-09-29 with context editing; 39% over baseline on "an internal evaluation set for agentic search"; client-side ("Claude requests file operations, and your application runs them"); six commands; the auto-added system prompt (full text); pairs with context editing and with compaction ("compaction keeps the active context small…, and memory preserves the information that must survive summarization"); the multisession software development pattern; path traversal | V | platform.claude.com memory tool docs, fetched |

## Google: Gemini

| Claim | Mark | Source |
|---|---|---|
| 2025-02-13: recall past chats, English, Gemini Advanced | V | blog.google, fetched |
| 2025-08-13: personal context on by default, 2.5 Pro, select countries; Temporary Chats not used for personalization | V | blog.google, fetched |
| 2026-01-14: Personal Intelligence beta; Gmail, Photos, YouTube, Search; off by default; US AI Pro and Ultra | V | blog.google, fetched |
| 2026-01-21 document "Building Personal Intelligence": the model "agentically and securely executes searches for the personal information that's relevant", including "your past Gemini app chat conversations, Search queries and YouTube history"; "tool calls to retrieve specific details and reasoning across many complex sources"; "dense retrieval"; "context packing … into the working memory for the model"; connected apps off by default | V | ai.google PDF, downloaded, pp. 6–8 |
| 2026-02-26: past chats rolling out to free users worldwide except Europe | T | 9to5Google (no Google post found) |
| 2026-03-26: "past chats" renamed "memory"; import of another assistant's summary via a suggested prompt, saved "to your Gemini context"; ZIP chat-history import; not EEA, UK, CH | V | blog.google, fetched |
| Help page: "Gemini can learn from your chats to understand more about you and your world"; ask "Did you use any info from past chats?"; summarise vs search not stated | V | support.google.com/gemini/answer/16598469, fetched |
| Personalization page: "Ask Gemini to consider your past chats…"; "Ask Gemini to remember your interests and preferences" (saved info) | V | gemini.google/overview/personalization, fetched |

## Google: Gemini CLI (C)

| Claim | Where |
|---|---|
| `save_memory` from the first docs (2025-06-07), project scope 2026-03-31 (#24161), replaced 2026-04-22 (#25716) by prompt-driven editing across four tiers | commit history of `packages/core/src/tools/memoryTool.ts`, `docs/tools/memory.md` |
| The system prompt's memory section: "There is no `save_memory` tool."; four tiers; routing rules; "ask the user" if a fact fits more than one tier; "Never duplicate…"; private `MEMORY.md` index with sibling files read on demand; "Never save transient session state…" | `packages/core/src/prompts/snippets.ts`, `toolUsageRememberingFacts` |
| Auto Memory: experimental, off; sessions idle ≥ 3 h with ≥ 10 user messages; extraction agent writes `.patch` files to an inbox; nothing applied without approval (`/memory inbox`); "Default to no-op. Prefer 0-5 memory patches and 0-2 skills per run."; a preview Gemini Flash model | `docs/cli/auto-memory.md`; `packages/core/src/agents/skill-extraction-agent.ts` |

## Other assistants

| Claim | Mark | Source |
|---|---|---|
| Grok's published prompt: "You have memory. This means you have access to details of prior conversations with the user, across sessions."; forget via the book icon under a message that references a chat; "Assume all chats will be saved to memory."; "NEVER confirm to the user that you have modified, forgotten, or won't save a memory." | C | xai-org/grok-prompts `grok3_official0330_p1.j2` (AGPL-3.0) |
| Grok memory announced April 2025, beta, not in the EU or UK, "Referenced chats" | T | TechCrunch 2025-04-16 via Yahoo; to be re-fetched |
| Mistral Le Chat Memories (beta) 2025-09-02: "retrieving insights, decisions, and references from the past when needed"; add/edit/remove; import from ChatGPT; free plan | V | mistral.ai news, fetched |
| Mistral docs now: Memories is "a legacy Chat feature"; replaced by Knowledge; "recalled automatically when they're relevant"; Le Chat is now Vibe (May 2026) | V | docs.mistral.ai, fetched; help.mistral.ai "Le Chat is now Vibe" (search result) |
| Perplexity memory 2025-11-26: "Structured preferences…"; "retrieves relevant context from your memory store"; all models; off in incognito | V | perplexity.ai hub blog, fetched |
| Perplexity "Brain" (2026-06-18) remembers the agent's own work, Max | T | press; not used unless a Perplexity page is found |
| Meta AI: "Memory updated" notice after a saved detail; saves on its own or on request; delete in the app or by asking | V (via search excerpt) | meta.com help 1152856459900216 returns 400 to curl; the page Anton saved is about Meta's *business* assistant, a different product; still pending |
| DeepSeek: no memory feature found in DeepSeek's own pages; only vendor-selling third parties say so | — | left out of the post |
| Microsoft Copilot | — | left out (Anton) |

## Mastra Observational Memory

| Claim | Mark | Source |
|---|---|---|
| Mastra: "the modern TypeScript framework for AI-powered applications and agents"; repo created 2024-08-06; 29,546 stars on 2026-11-16; Apache-2.0 outside `ee/` directories (Kepler Software, Inc.) | C | GitHub API; `LICENSE.md` |
| OM added in `@mastra/memory@1.1.0` | V | docs page |
| Defaults: Observer 30,000 message tokens, temperature 0.3, buffer every 20% (6,000), activation keeps 20%; blockAfter 1.2 (36,000); maxTokensPerBatch 10,000; Reflector 40,000, temperature 0; model `google/gemini-2.5-flash` (docs: `auto`) | C/V | `constants.ts`; docs |
| Thread scope default, "Each thread has its own observations"; resource scope deprecated; retrieval mode adds a recall tool | V | docs |
| "The observed messages leave the context window and the observations take their place", "typically 5 to 40 times smaller" | V | docs |
| "97 to 99% prompt cache hit rates" | V | docs |
| Read prompt: `OBSERVATION_CONTEXT_PROMPT_THREAD`, `OBSERVATION_CONTEXT_INSTRUCTIONS` incl. KNOWLEDGE UPDATES and PLANNED ACTIONS | C | `constants.ts`; identical to the run's answer prompt |
| Observer prompt: STATE CHANGES AND UPDATES; TEMPORAL ANCHORING; FORMAT | C | `observer-agent.ts`; the run's prompt saved as `run_observer_system.txt` |
| Reflector prompt: "When the user changed their mind or a fact was updated, keep both the old and new values with their dates and say which is current"; compression levels 1–4; level 3 "Drop observations that are no longer relevant or have been superseded" | C | `reflector-agent.ts` |
| Research post 2026-02-09 (updated 02-17), Tyler Barnes: LongMemEval_s, 500 questions; gpt-5-mini 94.87%, gemini-3-pro-preview 93.27%, gemini-3-flash-preview 89.20%, gpt-4o 84.23%; Observer and Reflector on gemini-2.5-flash; gpt-4o judge; "latest run is reported"; self-reported | V | mastra.ai/research/observational-memory, fetched |
| Their benchmark runner used resource scope, reflection at 80,000 tokens, `recognizePatterns: false`, a mock agent during ingestion, and replaced some words in the dataset that tripped Gemini's content filter | C | `explorations/longmemeval/src/commands/prepare.ts` |

## The Mastra run (agent-memory-eval `scripts/mastra/`)

Two runs on question `6a1eabeb` (whole history: 40 sessions, 413 turns), `gemini-3.1-flash-lite`, `@mastra/memory` 1.41.1 with its defaults. Numbers from `om_summary_output.txt`.

- **Default flow:** 7 Observer calls (120,197 tokens in), 1 answer (28,583 in), then 1 Reflector call. The log held 2,652 tokens; 28,703 tokens of the newest messages were still unobserved when the question came. The 23 May value was observed ("✅ (13:01) User set a personal best time of 27:12 in a 5K charity run."); the 30 May value ("hoping to beat my personal best time of 25:50") was in the raw tail. Answer: 27:12 (wrong). The Reflector shrank the log to 986 tokens and kept "set 5K PR (27:12)".
- **Tail observed first:** the Observer wrote "(13:53) User is training for a charity 5K (PB: 25:50)", next to an earlier "User is a runner (5K personal best: 27:12)"; it did not mark it as a change in this run. The answer prompt was 4,040 tokens; answer 25:50 (right). The Reflector kept only "charity 5K (PB: 25:50)" (777 tokens).
- **A first, discarded attempt** observed without buffering and dated nothing wrong but read 33,000-token chunks; in it the Observer wrote "User stated their personal best 5K time is 25:50 (updating previous mention of 27:12)" when it observed the tail after the answer. Not quoted in the post (its feeding differed from the defaults).
- **Buffering in the run:** five Observer calls on about 6,000 new tokens each (10,000 with the log), then, after the first activation, two calls on about 25,000 new tokens (34,000 in). Cause in the code: the buffer boundary (`lastBufferedAtTokens`) is not lowered at activation, so the next interval is crossed only near 30,000 again. Seen through the public API (`getStatus`/`activate`/`buffer`); not checked against a live agent turn.
- **Part 8 agrees:** in the whole-history run of part 8, full context and Mem0 also answered 27:12 on this question.

## The series' experiment, as part 9 restates it

To check against `docs/experiment-results.md` and part 8 before the post keeps each sentence:
- An agent that writes in its own turn often did not write the change (Letta as shipped: new value stored in 49% of the probed questions).
- An undated line reads the same later; the dated variants did better (part 8).
- Mastra's numbers are not comparable with part 8 (another split, another answering model, the vendor's own run).

## Checks run on the draft (2026-11-16)

- Every quoted prompt block compared with its source, ignoring line breaks and allowing `[…]` cuts: Codex v2 (3 blocks), Claude Code's block, Gemini CLI (rendered with the code's tool names and the paths from its comments), Grok, Mastra (Observer, Reflector, read instructions), the run's observation block. All match. The memory tool's added prompt: by eye.
- Every quotation in running text checked against raw downloads of the pages (scratchpad `check_quotes.py`). Not found: the OpenAI quotes (pending copies), the title, the excerpt and one illustrative example of my own.
- Google PDF page numbers checked per page with `pdftotext`: "tool calls…", "dense retrieval", "context packing" definition on p. 7; "agentically and securely executes searches…" on p. 8.
- Claude Code auto memory: changelog entry under 2.1.59 ("Claude automatically saves useful context to auto-memory"), released 2026-02-25 (npm).
- Site build with drafts: the page renders, the raw blocks keep the double-brace placeholders, all six figures and all part links resolve.
