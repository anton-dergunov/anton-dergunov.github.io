---
post: _drafts/agent-memory/2199-01-01-agent-memory-8-experiment.md
type: experiment
status: agreed
---

# Brief: Evaluating memory systems on LongMemEval (part 8)

Shared material is in `series.brief.md`. Outline rewritten on 2026-11-16 from Anton's spoken notes (`~/tmp-spoken-plans/blog/next-part.txt`) and his comments on the plan. Sources: `agent-memory-eval/docs/experiment.md`, `docs/experiment-results.md`, `docs/findings/*.md`, `results/`, `data/longmemeval_s_cleaned.json`, `~/papers/notes/`. The v1 draft (`v1/…-9-the-experiment.md`) and its 14 notes are material for facts only: no wording and no section order from it.

## Reader

The series reader, who may not have read any system part and has never seen the repository. They want to know how the memory systems behave on realistic histories, what they cost, and how to tell why one fails. They will judge whether the experiment is fair. The system descriptions here are one or two sentences each.

## The problem

The system parts explain each mechanism on one tiny test conversation, small on purpose so that every model call can be read. A tiny example shows how a system works, not how often its failures matter. The papers do not settle it either: each reports the setting it does well in, re-runs of competitors are rare or copied, and the datasets, answer models and judges differ from paper to paper. This part runs all five systems and two baselines on the same public benchmark, with the same model and judge, and reads every wrong answer.

## What the reader should leave with

1. On questions about changed facts, working memory systems land within a few points of each other and of reading the whole history. The large differences are in cost.
2. How a system is fed decided whether two systems remembered at all, and nothing reported an error.
3. Most wrong answers were lost at write time: the revision was mentioned in passing and never stored. Retrieval over raw turns cannot lose a fact that way.
4. To evaluate a memory system, read what it stored and what reached the answer, not only the score.
5. Published rankings mostly reflect each paper's setup (said briefly and calmly, not as a headline).

## Outline

Headings are plain, and the headings alone read as a table of contents. Nothing punchy or bold. There is no length limit.

| Section | What it says | Show in full | Figure |
|---|---|---|---|
| Opening (no heading) | The earlier parts used one tiny conversation on purpose; this part runs the same systems on a public benchmark. The two choices in 2–3 sentences. One short paragraph on why papers' own numbers do not settle it, with one small example (Zep against Mem0 in two papers). Repository link. The running example in one sentence (version C). | | none |
| Benchmarks for memory systems | What a memory benchmark is; a table of the main ones (DMR, LoCoMo, LongMemEval, MemBench, MemoryAgentBench, HaluMem, BEAM, PersonaMem, HorizonBench, DynamicMem), each with what it tests and its size; a paragraph on LoCoMo because most papers use it; why LongMemEval fits: a question type about changed facts, labelled evidence, human-curated questions, a validated judge, and a moderate size. | benchmark table | none |
| The LongMemEval benchmark | How it was built; abilities and question types; the oracle, S and M versions, and the cleaned release; the knowledge-update questions and their statistics, each explained; **one item of the dataset shown as its real JSON record and walked through field by field** (Anton: one of the most illustrative points of the post); questions asking for the earlier value; abstention questions and why they are left out. | the 5K question's record | `benchmark-types` (paper Fig. 1, reused, credited), `lme-history` |
| How answers are scored | The answer prompt and judge prompt, LongMemEval's own, in full; one real answer and its verdict; the paper's agreement with experts and the second judge's; what 67 questions can resolve; "not comparable to published LongMemEval numbers". | both prompts; Mem0's answer to the 5K question | `eval-pipeline` |
| The systems compared | Each arm in one or two sentences; why these baselines; one model in every seat; defaults, with dates passed in; no system set up or tuned by its makers (plainly; "I am not a vendor"). | | `map` (optional) |
| Limitations of this experiment | Trimming first: why, what is kept, what it removes, and the check on 25 full histories (the order of the systems held; full context slips without collapsing; write cost grows with the history). Then the other limits as a list. | | `trimming-check` |
| Results: accuracy and cost | One chart and the full table (first runs included), then a paragraph on what it shows; then what each answer reads and costs. | | `results`, `answering` |
| Analysis of the answers | How the memory was inspected (the probes, on the 5K question); how a system is fed decides whether it remembers; what memory holds after a fact changes (three readings, a paragraph each); why the wrong answers were wrong (error analysis); telling Letta's agent what to do (the persona lines quoted). | probe record; persona lines | `answer-loss`, `feeding` |
| What recall benchmarks do not measure | Over-personalisation, sycophancy, belief update: OP-Bench, PersonaMem-v3, MemSyco-Bench, HorizonBench. | | none |
| Where memory systems are heading | Write decisions move from prompts to trained or derived rules; forgetting has no training signal; keep or delete a replaced fact. | | none |
| Which memory design to use when | Defaults by situation, each tied to a result; no winner. | | `decision-guide` |
| Run it yourself | Models and why; versions; cost; committed results, tables rebuilt without model calls; reruns differ; commands; ideas to try. | | none |

## Running example

Version C: one sentence. The benchmark's own 5K question does the work here, from the dataset record to the judge's verdict, the probes and the full-history run.

## Numbers

- Every number comes from `agent-memory-eval/scripts/replays/experiment_numbers.py` or from a cited page that was opened.
- Intervals beside accuracies; "only large gaps mean anything" said once, where scoring is explained.
- At most about three numbers per paragraph; the tables carry the rest.

## Facts checked for this brief (2026-11-16)

- LongMemEval paper: CC BY 4.0 (arXiv), ICLR 2025. Code (GitHub) and the cleaned dataset (Hugging Face): MIT.
- The cleaned release "removes noisy history sessions that interfere with the answer correctness" (dataset card).
- PersonaMem-v3's licence was never the reason it was not used; the earlier brief's line is dropped. LongMemEval was chosen for its question type and moderate size.
- Abstention questions are left out because "they test refusing rather than updating" (`src/memeval/data.py`).

## Figures

- `benchmark-types`: the paper's Fig. 1, reused (CC BY 4.0, credited), with the knowledge-update panel highlighted ("highlight added").
- New: `lme-history`, `eval-pipeline`, `trimming-check`, `answer-loss`, `feeding`, `decision-guide`.
- `results` and `answering` exist; their titles are made plain.

## Left out

- The sentence about raw model calls (Anton: drop).
- Per-system details of the mechanism (the system parts own them).
- Mastra's LongMemEval figures (part 9, labelled as the vendor's).
- Any mention of whose resources paid for the runs.

## Links

- Repository: https://github.com/anton-dergunov/agent-memory-eval
- Papers: LongMemEval, LoCoMo, MemGPT, MemBench, MemoryAgentBench, HaluMem, BEAM, PersonaMem-v3, HorizonBench, DynamicMem, Mem0, MIRIX, Zep, OP-Bench, MemSyco-Bench, Memory-R1, SAGE, DeMem, Belief Memory; the Penfield Labs LoCoMo audit.

## Title and excerpt

- Title: "Evaluating memory systems on LongMemEval" (Anton, 2026-11-16; slug stays `8-experiment`).
- Excerpt: "Five LLM memory systems and two baselines on LongMemEval's questions about changed facts: accuracy, cost, and why each wrong answer was wrong."
