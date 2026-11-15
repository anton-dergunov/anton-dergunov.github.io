# Part 6 (Letta): runs, replays and checks

Written 2026-11-15. Scripts and outputs are in `agent-memory-eval/scripts/replays/letta_*`. All Gemini calls use `gemini-3.1-flash-lite`; 147 chat calls in all.

## The notebook

- **Notebook 04 was rerun on 2026-11-15** with four fixes that make the re-implementation behave as a self-hosted Letta 0.16.8 server does (option B in `6-letta.notebook-fixes.md`, chosen by Anton): the tool descriptions as the server builds them (with the docstrings' Examples), the server's search rule (whole query as one substring, five newest), an edit returning the whole block, and the server's `memory_metadata` wording. Kept simpler: temperature 0, sleep-time once per session, block limit 20,000, the primary with only the search tool.
- The rerun made 37 new chat calls; they are in `.cache/gemini/`, so `MEMORY_NOTEBOOKS_CACHE=1` replays it. `agent-memory-eval/scripts/replays/letta_dump_run.py` rebuilds the run from the cache with live calls blocked and dumps every request, reply, block and recall message; the post quotes from that dump. The committed notebook equals the trial run call for call.
- New numbers: in-line agent 17 calls and 47,677 tokens read for seven user turns (was 13 and 25,655); sleep-time set-up 16 calls the user waits for plus 4 in the background (was 36 + 4). The first call of a session reads 2,294–2,390 tokens, of which about 1,600 are the three tool descriptions (`count_tokens` on the prompt's parts; the remainder is constant across calls).

## Replays and offline checks

| Name | What | Against | Result |
|---|---|---|---|
| R1 | the session-2 replace, 5× each with the notebook's and the server's tool descriptions, temperature 0 and 1 (`letta_replay.py`) | the notebook before the rerun | whole-block `old_string` in 20 of 20; the descriptions' examples do not change it |
| R2 (old) | first message, temperature 1.0, 10× each (`letta_replay.py`) | before the rerun | wrote in 0/10 as in the notebook, 2/10 with server descriptions, 7/10 with server descriptions + persona lines + dated message. Superseded by R2 below |
| R2 | first message, temperature 1.0, 10× each, run twice (`letta_replay_first_message.py`) | the committed notebook | wrote in 2/10 and 3/10 as in the notebook; 0/10 and 0/10 with the persona lines and a dated message. The persona lines are about dating and updating, not about saving a first statement |
| R2b | the message with the change (s2.1), temperature 1.0, 10× each (`letta_replay_revision.py`) | the committed notebook | as in the notebook: a whole-block replace 10/10, keeps the earlier value 6/10, dated 0/10. With the persona lines and dated messages: whole-block replace 10/10, keeps the earlier value 10/10, dated 9/10 ("started June 2026; previously vegetarian for 8 years", "as of 2026-07-20; …") |
| R3 | the server's search rule applied to every search of the notebook before the rerun (`letta_server_search.py`, offline) | before the rerun | 33 of 34 searches return nothing; the in-line agent's search before its answer among them, so "the search doubled the prompt" was an effect of the notebook's search |
| R3b | answer-turn tokens in the experiment, from `results/main/ledger.jsonl` (`letta_search_cost.py`, offline) | `letta`, `letta-persona` | median 3 calls per answer; the whole answer turn read a median 3.2× (pooled 4.0×) the tokens of its first call; tool calls and results are 16% (22% with the persona) of the tokens read while answering. The cost of searching is mostly the prompt sent again with each step |
| R4 | counts from `docs/findings/letta.md`, recounted from the result files | `letta`, `letta-persona`, `letta-batch` | 146 searches at answer time, 97 empty (`letta`); 151 and 71 (`letta-persona`); `human` block empty in 43 of 67 histories (`letta-batch`). The 31 → 57 of 64 revisions written comes from the findings' own classification (a pattern per question, then read by hand) and is cited as such |

## Server facts checked in `vendor/letta/src` (0.16.8)

- Default agent type `letta_v1_agent` ("simplification of the memgpt loop, no heartbeats or forced tool calls"); tools `conversation_search`, `memory_insert`, `memory_replace` (`calculate_base_tools(is_v2=True)` minus `send_message`); max 50 steps; `parallel_tool_calls=False` in the logged request; temperature 1.0.
- Tool description = docstring summary + long description + the docstring from "Examples:" to its end, "Returns:" included (`schema_generator.generate_schema`, `extract_examples_section`). `memory_insert`'s "None is always returned" is wrong: the executor returns the new block.
- `conversation_search` without Turbopuffer: `ILIKE '%query%'`, limit 5 (`RETRIEVAL_QUERY_DEFAULT_PAGE_SIZE`), newest first, tool messages dropped after the limit, dates not passed (findings/letta.md has the code path).
- Sleep-time: `enable_sleeptime` gives the primary `send_message`, `conversation_search`, `archival_memory_search`; the sleep-time agent `memory_replace`, `memory_insert`, `memory_rethink`, `memory_finish_edits` and a `memory_persona` block; it runs every 5 turns (`sleeptime_agent_frequency=5` in `server.py`) on the messages since the last processed one.
- Memory pressure: `MESSAGE_SUMMARY_WARNING_STR` is used only by the legacy `letta/agent.py`; `LettaAgentV3` compacts (summarises) when the context passes the trigger threshold, with no warning.

## Not changed

- `docs/blog/outline.md` (2026-10-24) still describes the notebook's earlier run (the primary's loop, the merged visits). It is a planning document from before the parts were drafted; Anton may want to update or drop it.
