# Part 5: the notebook rerun and the checks (2026-11-15)

Material for the post. Notebook 03 was rerun on graphiti-core 0.31.1, the version that `uv.lock` installs and that the experiment ran. Anton chose this over keeping the committed run on 0.30.

## What changed in the notebook's code

The control flow now follows 0.31.1 where the two versions differ, or where the old notebook had taken a shortcut:

- A name that the fact step uses and the entity step did not find becomes a new entity, matched like any other (`dangling_endpoints.py`). The prompt still says such an edge "will cause the edge to be rejected".
- The fact step runs for every message. The old notebook skipped it when a message had one entity, and the library does not.
- Same-pair facts are found in both directions.
- `close_contradicted` also closes the new fact when a contradicted fact starts later, and marks a fact that arrives with an end date as expired (`_apply_temporal_invalidation`).
- An undated new fact gets the `extract_timestamps` call. The same sentence between the same two entities is a repeat without a call. Future-tense facts are dated by when they were said (`normalize_future_temporal_bounds`). None of these fired.
- The prompt slots carry the library's fields: `["Entity", "Person"]` labels, and the entity type's description in the matching prompt.
- A new cell runs steps 2 and 3 with the three default entities.

Still left out, and why it does not matter here: summaries, attributes, communities, the cross-encoder, and the fuzzy MinHash name match. The best Jaccard score among this conversation's names is 0.733 ("Anton's sister Lena" against "Anton's sister"), and the threshold is 0.9.

Unchanged requests replayed earlier replies from `.cache/gemini/`; the cache keys on the full request. Changed requests called Gemini on 2026-11-15.

## Three runs of the same conversation

| | Committed run, 0.30 (October) | Trial: 0.31.1, old control flow | Adopted: 0.31.1 |
|---|---|---|---|
| Default types: entities | 3 | 3 | 3 |
| Default types: facts about the diet or allergy | not run | not run | none (2 facts: dinner, visit) |
| Custom types, s1.1: facts | 3 | 3 | 4 (the dinner sentence on two edges) |
| "Eight years" dated | 2018-03-14 | 2026-03-14 | 2026-03-14 |
| New value of the changed fact, as stored | "started following a pescatarian diet about a month ago" | "adopted a pescatarian diet approximately one month prior to 2026-07-20" | "started following a pescatarian diet about a month ago, replacing his previous vegetarian diet" |
| Its `valid_at` | 2026-06-20 | 2026-06-20 | 2026-07-20 (dated by the message) |
| Old fact closed | yes, 2026-06-20 | yes, 2026-06-20 | yes, 2026-07-20 |
| Repeated allergy caught as a same-pair duplicate | yes | yes | yes |
| "Lena" against "Anton's sister" | 0.595, second node | 0.595 | 0.595, second node |
| Facts stored | 13, 1 closed | 13, 1 closed | 14, 1 closed |
| Default search returns | 9 | 10 | 10 |
| Closed fact | in, 0.608 | in, 0.608 | in, 0.608, 10th |
| New value | out, 0.599 | in, 0.616 | out, 0.592 |
| Peanut allergy | in, 0.602, 9th | in, 10th | **out, 11th** (0.602) |
| Coeliac | out, 0.596 | out | out, 0.596 |
| Default answer | allergy, shellfish; no diet, no gluten | allergy, shellfish; no gluten | shellfish, "fish is acceptable" (from the assistant's fact); **no allergy**, no gluten |
| Tuned read | gains coeliac | gains coeliac and the diet; loses the allergy | gains coeliac; allergy 11th, diet 12th |
| Model calls / tokens read | 36 / 51,290 | 36 / 55,780 | 38 / 60,374 |

The point for the post: the mechanisms held in all three runs (default types store nothing about the diet or the allergy; the reversal closes; the second Lena node; the walk finds coeliac). What reaches the answer did not: it turned on how the model worded one sentence months earlier, at the third decimal against the floor, and on the limit of ten.

## Checks

Scripts and outputs in `replays/`.

- **A** (`graphiti_replay.py`): the committed run's comparison for the reversal, sent with the stricter 0.31.1 prompt: `contradicted_facts: [0]` in 3 of 3.
- **B** (same script): step 3 for s1.1 with the three default entities: 2 facts, no new entity, in 3 of 3. The adopted run's new cell shows the same.
- **C** (`graphiti_dangling_in_logs.py`, on the archived log of the experiment's Graphiti arm): 52 of 22,795 extracted facts (0.2%) named an endpoint outside the entity list.
- **D** (same as A): "Lena" against "Anton's sister" 0.595, against "Anton's sister Lena" 0.779, against "Lena's partner Jonas" 0.787. The matched node keeps the old name, so its name never gets "Lena" in it.
- **E** (release history): not done yet.

## Version differences worth a sentence in the post

- The contradiction prompt became stricter in 0.31 ("A contradiction requires explicit evidence that the old fact stopped being true or was replaced… Do NOT infer contradiction from recency alone"). The findings file quotes this text.
- The fact prompt gained rules that date a plan by when it was said.
- The code keeps facts with an endpoint that the entity step did not find; the prompt still says they are rejected.
- The rule for ongoing facts ("set `valid_at` to the timestamp of the episode") is the same in both versions. 2018 against 2026 is the model's judgement, not the version.
