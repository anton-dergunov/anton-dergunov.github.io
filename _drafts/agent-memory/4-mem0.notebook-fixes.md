# Notebook 02 (Mem0): two explanations to correct

Found while writing part 4 (2026-11-15) by reading `mem0ai` 2.2.1 and by replaying the notebook's calls. The notebook's outputs are right. Two of its explanations are not. Nothing here is applied yet.

## 1. `limit=6` is ignored; it does not "size an internal pool"

**What the code does.** In 2.2.1, `Memory.search(query, *, top_k=20, filters=None, threshold=0.1, …, **kwargs)`. `limit` is not a parameter, so `limit=6` lands in `**kwargs` and is dropped without an error. Inside, `limit = top_k`, and `score_and_rank` ends with `return scored[:top_k]`. So the list is cut, at `top_k`; nine facts are fewer than the default 20. A replay confirmed it: `limit=6` returned 9 facts, `top_k=6` returned 6.

**Option A: markdown only, no rerun.** Three places.

Cell 31, replace the first paragraph ("**`limit` is not a cap.** In this release it only sizes an internal pool … left to the caller.") with:

> **`limit=6` did nothing.** In this release the argument that caps the results is `top_k` (default 20). `search()` does not know `limit`, and ignores it without an error. So the default applied, and a store of nine facts came back whole. With `top_k=6` the list is cut at six.

Cell 31, in the first bullet, "If the caller had cut the list at six, as it asked to" can stay.

Cell 41, the "Reading" row of the table, replace "`limit` is not a cap" with "an unknown argument such as `limit` is ignored silently".

Cell 41, "Things worth trying", replace "**Cut the list at six yourself** (`hits[:6]`) and ask again." with "**Pass `top_k=6`** and ask again."

**Option B: with a rerun.** Keep the `limit=6` call as the trap, add a `top_k=6` search after it, and ask the answering model with only those six facts. This shows the real cut: no allergy and neither value of the changed fact in the prompt. A rerun changes the extracted wording, the scores and possibly the `mem0` figure. It would also run in an environment where spaCy and fastembed are now installed, which switches on keyword scoring and changes every score (see 3). To keep the notebook's current numbers, the rerun needs an environment without the `experiment` extra.

## 2. Why the new fact names the old value

Cell 24 ("The prompt of that call shows why") and cell 28 ("The new fact carries the replacement inside its own sentence, because the old row was in front of the extractor when it wrote it") give the old row in `Existing Memories` as the reason.

**What a replay shows.** The same prompt with `Existing Memories` and `Last k Messages` emptied, three times, still returned "User transitioned from a vegetarian diet to a pescatarian diet around September 2026, meaning they now eat fish but continue to avoid meat." Only the word "strict" was missing. The cause is the system prompt's rule for transitions ("the memory MUST capture the transition — what the new state is AND what it replaces or changes from") together with the user's own wording ("pescatarian now, not vegetarian").

**Suggested text for cell 28, first paragraph and first two bullets:**

> The new fact carries the replacement inside its own sentence. The system prompt asks for that: "When the user describes changing, switching, replacing … the memory MUST capture the transition — what the new state is AND what it replaces or changes from." That helps, and it is not a guarantee, for two reasons.
>
> - It relied on the user's wording being an explicit correction (*"not vegetarian"*). The same call with no stored facts in the prompt writes almost the same sentence.
> - Either way **the stale row survives**, and it will keep being retrieved.

And in cell 37, "The extractor did that work, not the search" stays true.

## 3. Worth adding, if the notebook is rerun anyway

- **Print the raw reply of the second `add()`.** In five replays the new fact carried `"linked_memory_ids": ["1"]`, the old row. The library never reads that field (`_add_to_vector_store` uses only `text` and `attributed_to`; `uuid_mapping` is built and not used).
- **Say that the scores are similarity only.** Cell 4's comment already says that the spaCy and fastembed extras are not needed. With them, the example's question ranks the new fact 5th (it shares "eat" with the question), the allergy 8th and the old fact 9th, and every score is divided by 2.
