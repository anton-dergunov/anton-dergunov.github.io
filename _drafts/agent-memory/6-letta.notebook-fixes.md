# Notebook 04 (Letta): differences from the server, and a trial rerun

**Decision: option B** (Anton, 2026-11-15). Applied the same day: `notebooks/letta_source.py`, `notebooks/04-letta.ipynb` (code, markdown, outputs) and the figure `letta`. Runs and replays: `6-letta.runs.md`.

Written 2026-11-15 while planning part 6. The notebook re-implements Letta's agent loop around Letta's own prompt texts. Read next to the Letta 0.16.8 server (`vendor/letta/src`) and a request the server sent in the experiment (`.cache/calls/calls-33743.jsonl`), it differs in six places. Notebooks may simplify on purpose (HANDOFF rule 12), so each difference is judged by whether it changes what the post says.

| # | Notebook | Server 0.16.8 | Verdict |
|---|---|---|---|
| 1 | Tool descriptions: the docstring's summary only (`letta_source.tool_declaration` cuts at "Args:") | Summary, rest of the description, then the docstring from "Examples:" to its end (`schema_generator.generate_schema`, `extract_examples_section`) | Fidelity. Replay R1 (`replays/letta_replay_output.txt`): the whole-block replace happens with either description, 20 of 20. Replay R2: on the first message the agent wrote in 0 of 10 with the notebook's descriptions, 2 of 10 with the server's |
| 2 | `conversation_search` counts shared words, returns the 10 best | Self-hosted: the whole query as one substring (`ILIKE`), the 5 newest, tool messages dropped after the cut; dates ignored. The "hybrid search" of the description needs Turbopuffer | **Substantial.** Under the server's rule, 33 of the notebook's 34 searches return nothing (`replays/letta_server_search_output.txt`), including the in-line agent's search before its answer, so the notebook's "the search doubled the prompt" does not happen on the server. The notebook's line "Letta mixes text and embedding search" is wrong for a self-hosted server |
| 3 | A memory edit returns "The memory block has been edited." | It returns the whole new block | Fidelity; it is also the "echo" mechanism of failure 2 in the experiment |
| 4 | `memory_metadata`: "The current system date is: <session date>" | Agent id, conversation id, "System prompt last recompiled: <time>", the recall count | Fidelity |
| 5 | Sleep-time agent once after each session | Every 5 turns by default, on the messages since its last run | Kept (Anton, 2026-11-15); the post states the server's default |
| 6 | Temperature 0; block limit 20,000 | 1.0; 100,000 | Kept; stated in "Run it yourself" |

## The trial (fixes 1–4)

A copy of the notebook with fixes 1–4 (`letta_source.py` builds the server's descriptions, checked equal to the logged request for all three tools; the search, tool return and metadata as the server has them), run at temperature 0 in the scratchpad. 37 new chat calls, all now in `.cache/gemini/`, so a rerun of the same code replays them.

What changes in what the notebook shows:

| | committed notebook | trial with fixes 1–4 |
|---|---|---|
| In-line, session 1 | nothing on message 1; one insert of four lines on message 2, including the guess "Location: Berlin" | nothing on message 1; one insert on message 2, one paragraph, with the sister's visit, no location guess |
| In-line, session 2 | four edits: three whole-block replaces (one only to add "(Kreuzberg)"), one insert; "(started eating fish one month ago)" | four edits: two whole-block replaces, two inserts; "(recently started eating fish)", and "(8 years)" dropped |
| Reworded constraint | "can't eat shellfish" → "has a shellfish allergy" | the same |
| In-line, session 3 | one search, 10 results from the word-count search; the answer step read 3,509 tokens against 1,496 | five searches, shortening: three full phrases find nothing, "restaurant recommendations" finds 1 message and "Kreuzberg" finds 4, all of them the agent's own earlier replies; then the answer |
| Primary (sleep-time set-up) | loops on "human block" searches, no reply on 3 of 7 turns, "I have updated my records" | one search per turn, all empty, then a normal reply on every turn |
| Sleep-time agent | absolute dates ("since June 2026", "since May 2026"); merges the March visit and the autumn visit into one postponed visit | writes "(next week)" after session 1 despite its prompt; "Pescatarian (started July 2026)", the wrong month (the user said "about a month ago" on 20 July); drops the March visit; no merge |
| Final answers | both have every constraint | both have every constraint (in-line: Amrit and Chutnify) |
| Calls | in-line 13; sleep-time set-up 36 + 4 | in-line 17; sleep-time set-up 16 + 4 |

## Options

- **A. Markdown only.** Keep the outputs. Correct the notebook's explanations: the search is a simplified stand-in (what the server does, and that its rule would have returned nothing here); the tool descriptions omit the Examples; the tool result and the metadata are simplified. The post explains the doubled prompt as an effect of the notebook's search, and uses the experiment's ledger for the real cost of searching.
- **B. Apply fixes 1–4 and rerun** (the trial, committed). The notebook then behaves as the server does in everything but fixes 5–6, and its session 3 shows the phrase-match search at work. It loses the primary's loop and the merged visits; it gains a sleep-time agent that writes a relative date and a wrong month despite a prompt that asks for absolute dates. The markdown of sections 1–5 and the takeaways table must be rewritten for the new outputs, and the architecture figure `letta` (its search box) and its alt text change.
