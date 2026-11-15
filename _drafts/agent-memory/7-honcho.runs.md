# Part 7 (Honcho): runs, checks and server facts

Written 2026-11-15. Scripts and outputs are in `replays/honcho_*`. The server ran on Vertex AI (the blog project); the notebook on the Gemini API free tier. Every model call is `gemini-3.1-flash-lite`.

## The real server on the example (three runs)

- **Set-up.** `infra/honcho/up.sh` in agent-memory-eval (Honcho 3.3.0, commit 608aec8), started with `COMPOSE_PROJECT_NAME=memeval-honcho`. Without it, Compose takes the project name `honcho` and adopts the stopped containers and volume of `~/projects/consulting/honcho`. Every model role goes through `memeval.proxy`, which logs every request in full.
- **Credentials.** The machine's Application Default Credentials belong to adergunov.grotto and returned 403 on the blog project. `replays/honcho_server_run.py` therefore takes its token from `gcloud auth print-access-token` (adergunov.blog) for both chat and embeddings, and reads the project from `GOOGLE_CLOUD_PROJECT`. If you want ADC to be the blog account, run `gcloud auth application-default login` as adergunov.blog.
- **What a run does.** Session 1 with message times a minute apart from 14 March 2026, then a dream scheduled by hand; session 2 (20 July), then a second dream; then `peer.chat(QUESTION)` and `peer.representation(search_query=QUESTION)`. Peers are `Anton` and `assistant` (`observe_me=False`). Each run has its own reply cache, so runs 2 and 3 made real calls. The stored state (documents including soft-deleted ones, `document_sources`, the peer card) was read with `SELECT` from the server's Postgres.
- **Why a dream after each session** (Anton, 2026-11-15): the test conversation is short on purpose. In real use, many other conversations would fall between March and July, enough for Honcho's own trigger (50 new explicit conclusions, 8 h, 60 idle minutes). The experiment scheduled one dream after the whole history.
- **Outputs.** `honcho_server_runs/run{1,2,3}.json` (every request and reply, the stored rows, links, peer card, both read outputs, the ledger); `honcho_server_summary.py [--brief]` prints them.

| Run | Model calls (deriver / deduction / induction / dialectic) | Tokens in, writing | Update written | Deleted by the deduction agent | Live rows that still say "vegetarian" |
|---|---|--:|---|---|---|
| 1 | 2 / 9 / 7 / 1 | 44,987 | yes | the vegetarian fact | a deduction; a pattern written after the update, which replaced the old pattern as a near duplicate |
| 2 | 2 / 10 / 7 / 1 | 45,737 | yes | "does not eat meat" (still true) | the vegetarian fact, a deduction, a pattern |
| 3 | 2 / 9 / 6 / 1 | 41,552 | yes | the vegetarian fact and "does not eat meat" | a deduction, a pattern |

- All three dialectic replies said "pescatarian", and each answered in one call with no tools.
- Writing also made 8 to 10 embedding calls per run.
- In run 1, the grounding check rejected one induction write, because four ids had been joined into one string; the agent resent it correctly.

## Notebook 05, realigned and rerun

- **Rewritten** to drive Honcho's own text, fetched by the new `notebooks/honcho_source.py` from commit 608aec8:
  - the deriver prompt and message tags;
  - the deduction and induction prompts, including the peer-card section;
  - the three tool sets;
  - the dialectic's system prompt and first message.
- **Rules written out as plain functions:** saving with exact and near duplicates; the tool results in Honcho's formats; the grounding check; soft delete; the representation's 33 + newest blend; the dialectic's 25 + 25 prefetch and its 5-round loop. One loop serves every agent, with Honcho's synthesis prompt at the round limit.
- **Kept or added for intuition, and labelled:**
  - the walk over the links (`rests_on`), next to Honcho's scope-removal rule;
  - the level-order check, which Honcho does not have;
  - the confidence check;
  - abduction, which is the notebook's own prompt, in a section "Beyond Honcho".
- **Simplifications, named in the notebook:**
  - temperature 0;
  - a dictionary instead of Postgres;
  - dreams after each session, started by hand;
  - short ids;
  - "richer text" counted in words where Honcho counts tokens (no tiktoken in the environment);
  - the 3,072-dimension Gemini embedding where the server used 1,536.
- **The run:** 20 calls for Honcho's own work plus 2 answering calls; 56,272 tokens in. Dream 2 wrote an update, deleted the vegetarian fact and the still-true "does not eat meat" (as server run 3 did), and left two stale conclusions live. The answer built from the dialectic's reply kept two of the four constraints; the one built from the representation kept all four.
- **Re-execution** from `.cache/gemini/` with `MEMORY_NOTEBOOKS_CACHE=1` makes no new calls and reproduces every output.
- `replays/honcho_verify_source.py`: with the inputs of server run 1, every prompt and tool schema that `honcho_source.py` builds equals what the server sent (11 checks, all equal).

## Offline checks on the experiment (no model calls)

| Name | What | Result |
|---|---|---|
| Levels | conclusions by level in the 67 `honcho-repr` stores | 7,434 explicit, 158 deductive, 146 inductive, 0 contradiction |
| Deductions | all 158 deductive rows, read by hand | none records a change of value; 2 say "contradictory"; many are guesses ("user is currently pregnant", from a question about pregnancy symptoms) |
| Dream tools | tool calls in `.cache/llm/` replies | `create_observations_inductive` 93, `create_observations_deductive` 90, `update_peer_card` 65, `get_recent_observations` 13 (limit 20 in 10), `delete_observations` 13 (18 rows), `search_memory` 0. The dream's first request is the same for every question, so one cached reply served all first rounds |
| Window (`honcho_dream_window.py`) | old and new values against the 20 newest explicit rows | both values located in 41 of 67 stores; in the newest 20: both 0, new only 21, old only 3, neither 17 |
| Read cost | `results/main/ledger.jsonl` | the dialectic made a median of 1 call per question (max 3); writing took a median of 38 chat calls and 69k input tokens per question |

## Server facts checked in the source (3.3.0)

- **The deriver** extracts explicit conclusions only (`PromptRepresentation` has one field), and sees only the batch. A batch is taken at 512 tokens or 30 minutes. The docs say it also writes deductive conclusions; the code does not.
- **Saving** (`create_documents`): exact duplicates are keyed on normalised text, level, and session for explicit rows. Near duplicates need cosine distance ≤ 0.05 within the same level (and session, for explicit rows), and the "richer text" wins. Session-pure explicit rows came in 3.0.12.
- **The dream.** The trigger counts explicit rows only, needs 8 h since the last dream and 60 idle minutes; a manual schedule bypasses the threshold and cooldown. Deduction has 12 rounds and induction 10. Surprisal is off by default. The deduction tool forces the `deductive` level, so no contradiction can be written. `delete_observations` is a soft delete with no cascade. The only transitive cascade is scope removal (3.1.0), and it fails closed.
- **Grounding** (3.2.0): invented ids are stripped; a row needs ≥ 1 real source (≥ 2 for a contradiction); its date is the latest source cited in the call.
- **The induction prompt** is a plain string written as if it were an f-string, so the model sees doubled braces in its JSON example.
- **The dialectic** runs at level `low`: 5 rounds, tool choice `auto`, a 25 + 25 prefetch. Its prompt has both "Ask the user which statement is correct" and "The MORE RECENT statement supersedes"; the workspace prompt has "NO CLARIFYING QUESTIONS", the pair prompt does not. v3.5.0 (released 2026-10-30) made pair chat single-turn.
- **The representation** returns at most 100 rows: ⌊100/3⌋ by similarity, then the newest. Inductive rows are printed without a time.

## Not changed

- `notebooks/02-mem0.ipynb` quotes the old Honcho cost ("4,543 tokens in seven model calls"). Anton reruns notebook 02 in a later session; its comparison should then use the new numbers: 19 calls and 49,766 tokens in the notebook's writing, or 18 calls and 44,987 tokens on the server.
- `docs/blog/outline.md` still describes the old Honcho notebook (6 calls, abduction). It is a planning document, as noted in part 6.
- The run JSON files contain the induction prompt's doubled braces, so Jekyll prints Liquid warnings for them; the build succeeds.
