# The constraint tax, measured on a real pipeline

Raw notes for a possible post. Everything here was measured on 12 Sep 2026 against live Gemini
models (free tier and Vertex, personal account). Scripts are in this folder and re-runnable.

## The symptom that started it

A vocabulary app picks a short clip of recorded speech for each sense of a word, and asks one model
call to do two things: choose the segment, and translate it. Two stored rows came back like this:

    translation = "I'm going to take something to snack on, something to eat.,
                   segmentId: seg_4270b0b102db1a08454c"
    matchedTranslationForm = ""

An internal id inside a user-visible sentence. Another run produced:

    "And it's going to start itching her because it's weird, guys .Y ella ya le va a empezar a
     picar porque es raro, chicos. Wait, no. And she's going to start to itch because it's weird,
     guys. Wait, it's going to start itching, because it's odd, guys. Let's write a clean
     translation: And it's going to s..."

That is the model **drafting inside the JSON string value** — writing a version, rejecting it
("Wait, no."), trying again. It never stopped, so the string never closed cleanly.

The call had `responseMimeType: application/json` + `responseJsonSchema` set. Constrained decoding.

## Four hypotheses, all wrong

Worth recording because the wrong ones were each plausible:

1. **"That model can't do JSON."** Wrong: 4/5, then 9/10 clean runs. n=2 is not a proof.
2. **`additionalProperties: false` causes it.** Wrong: a larger run reproduced the rambling
   without it.
3. **The client library is merging thinking tokens into content.** Wrong, and checkable — LiteLLM
   routes `part.thought is True` to `reasoning_content`, never to `content`. More to the point,
   `reasoning_content` came back **empty on every call**: this model exposes no thought channel
   here at all.
4. **It's prose under constraint.** Wrong: the speech *translate* stage is pure prose with a schema
   and is immaculate — 123–130 characters for a 128-character source, 0.7 s, zero drafting.

## What is actually true

Of four callers in the same codebase, on the same models, through the same client:

| caller | output | schema | result |
|---|---|---|---|
| image brief | judgement + lots of prose | yes | clean, 3/3, 1.9–2.0 s |
| speech translate | prose | yes | clean, 123–130 chars, 0.7 s |
| speech align | ids only | yes | clean, 3/3 |
| **clip selection** | judgement + prose, 20 candidates | **yes** | **266, 364, 549, 1039 chars; 3-of-4 timeouts** |
| clip selection | same | **no** | **61, 61, 61, 61 chars; 0 errors; fastest** |

61–65 characters is what a correct translation of that sentence weighs.

So it is not "schemas are bad" and not "this model is bad". It is specific and it is repeatable.

## The literature calls this the constraint tax

- *The Constraint Tax: Measuring Validity-Correctness Tradeoffs in Structured Outputs for Small
  Language Models* — arXiv 2605.26128
- *When Correct Isn't Usable: Improving Structured Output Reliability in Small Language Models* —
  arXiv 2605.02363
- Practitioner write-ups report a ~17% "creativity cost" and latency 3.6×–8.2× versus naive
  prompting, and warn: *"Constraining the model too tightly too early can suppress reasoning. If
  the schema is {answer: int} and the task is hard, the model has to commit to a number on the
  first decoded token — no room to think."*
- Documented mitigations: a `reasoning: string` field **inside** the schema as a scratchpad, or
  two-stage generation (unconstrained reasoning, then constrained extraction).
- vLLM had to special-case it: structured-output masking is *suspended* between `<think>` and
  `</think>`, then resumed.
- One survey of reasoning tokens across five models found reasoning is dropped in `json_schema`
  and `json_object` modes on most of them.

Our observation is a clean field instance of a known effect, with the twist that the drafting
lands **in a user-visible field** rather than being discarded — an invisible failure, since a
plausible-looking sentence with an id glued on the end passes every structural check.

## The finding I did not expect: it breaks outright at scale

The alignment schema constrains every id to an enum of *that request's* tokens — the one case where
a schema plausibly does work a prompt cannot. Ground truth constructed so the correct answer is
unambiguous (`align_experiment.py`). Two runs per cell:

| model | source tokens | mode | valid | accuracy | seconds |
|---|---|---|---|---|---|
| 3.1-flash-lite | 21 | constrained | 2/2 | 100% | 2.8 |
| 3.1-flash-lite | 21 | prose | 2/2 | 100% | **1.8** |
| 3.1-flash-lite | 60 | constrained | 2/2 | 100% | 3.8 |
| 3.1-flash-lite | 60 | prose | 2/2 | 100% | 3.9 |
| 3.1-flash-lite | 120 | constrained | **0/2** | **0%** | **HTTP 400** |
| 3.1-flash-lite | 120 | prose | 2/2 | **100%** | 7.4 |
| 3.5-flash-lite | 120 | constrained | **0/2** | **0%** | **HTTP 400** |
| 3.5-flash-lite | 120 | prose | 2/2 | **100%** | 5.8 |

**Constrained decoding bought no accuracy at any size where it worked, and stopped working
between 90 and 105 source tokens:**

    75 tokens  -> OK
    90 tokens  -> OK
    105 tokens -> 400 INVALID_ARGUMENT
    120 tokens -> schema is 3,064 characters with two 120-element enums -> 400

The error maps to a *terminal* classification in our chain — it is not retried at the next model,
because a rejected configuration is a mistake to fix rather than a condition to route around. So a
long passage does not degrade; it fails the whole chain.

The headline: **the schema was there to guarantee valid ids, and at realistic sizes it guaranteed
no answer at all.** Prose-and-validate returned 100% valid, 100% accurate output at every size.

## Latency varies 20× across rows in one chain

| row | clip-selection call |
|---|---|
| gemini-free 3.5-flash-lite | 0.9–1.8 s |
| vertex 3.5-flash | 7–33 s |
| vertex 3.8-flash | 21–37 s |

Any single timeout is wrong for someone. A bound sized for the free tier makes the paid fallback
unusable; a bound sized for the fallback restores the hang it was meant to remove. Timeouts belong
per row, beside the other per-provider facts.

## What I would tell someone starting out

- **Constrained decoding buys validity, not correctness.** They are different claims and only the
  first is guaranteed. Validate afterwards regardless.
- **Suspect it when the task needs judgement**, not when the output is complex. The most complex
  schema here (the brief, eight fields of prose) was fine; the one requiring a choice among 20
  candidates was not.
- **Per-request enums do not scale.** They grow with the input and there is a cliff.
- **A malformed field that still parses is the dangerous failure**, because nothing downstream
  notices. Guard the content, not just the shape: our fix refuses a translation that contains its
  own segment id, or that runs past 3× the length of its source.
- **Measure before believing anyone, including yourself.** Four of my hypotheses died; the log of
  model calls that made them checkable was worth more than any of them.


## Every experiment run, in order

Kept because the order matters: each one killed a theory, and the cheap checks were the ones that
paid. Models are `gemini/gemini-3.1-flash-lite` and `gemini/gemini-3.5-flash-lite` on the free tier
unless noted; Vertex rows are `vertex_ai/gemini-3.8-flash` and `vertex_ai/gemini-3.5-flash`.

### 0 · The zero-cost check that found the original bug

No API calls at all. The schema as transmitted, read back out of the client library:

    per-sense properties: senseId, styleId, anchorExampleId, situation, subject, brief,
                          refused, refusalReason
    per-sense required  : ['senseId']

Eight fields offered, one required. Under constrained decoding `{"senses":[{"senseId":"s1"}]}` is a
fully legal answer, and the parser rejected it as unusable — so the chain walked every model in turn
producing the same legal nothing. The prompt had named all eight fields the whole time and was
simply outranked. **A schema that says less than the prompt is worse than no schema.**

### 1 · Does the model return any thinking channel at all?

    json_schema, no thinking     thinking=NONE   longest_translation=  266
    json_schema + effort=low     thinking=NONE   longest_translation= 1039
    prose only (no schema)       thinking=NONE   longest_translation=   61

`reasoning_content` empty in every case. There is no hidden channel being mishandled — there is no
channel. And asking for a thinking budget made it *worse*, which killed the scratchpad theory.

### 2 · Is it `additionalProperties: false`?

    3.1-flash-lite  current                  leaked 0/5
    3.1-flash-lite  no additionalProperties  leaked 0/5
    3.5-flash-lite  current                  leaked 1/5
    3.5-flash-lite  no additionalProperties  leaked 0/5

Suggestive at n=5 — and wrong. A larger run reproduced the rambling without it. Kept as a reminder
of how easily one event becomes a theory.

### 3 · Which caller is actually affected?

Four callers, same models, same client, same session:

    image brief         judgement + eight prose fields   schema   3/3 usable, 1.9-2.0s
    speech translate    pure prose                       schema   123-130 chars for a 128-char
                                                                  source, 0.7s, no drafting
    speech align        ids only                         schema   3/3 valid
    clip selection      judgement + prose, 20 candidates schema   266/364/549/1039 chars,
                                                                  3 of 4 timed out
    clip selection      same                             none     61/61/61/61, no errors

This is where "schemas are bad" and "this model is bad" both died. It is one caller.

### 4 · Is it the union type?

The clip schema is the only one carrying `{"type": ["string", "null"]}` — how a sense declines.

    union  [string,null]   longest=[340, 549]        2 timeouts
    plain  string          longest=[65, 198, 211]    1 timeout
    no schema (prose)      longest=[61, 61, 61, 61]  0 errors, fastest

The union makes it worse and is not the cause. Only removing the schema is clean.

### 5 · Vertex, same experiment

    gemini-3.8-flash   union   [52, 52]            21.9-36.8s
    gemini-3.8-flash   plain   [122, 225, 355]     21.0-23.2s
    gemini-3.8-flash   none    [0, 52, 68]         10.7-23.6s
    gemini-3.5-flash   union   [0, 0]               9.1-15.4s
    gemini-3.5-flash   plain   [68, 211]            6.9-7.7s
    gemini-3.5-flash   none    [0, 0, 70]           9.2-32.8s

Bigger models bloat too, so it is not a small-model failing. `0` means the model chose no clip for
any sense — a legitimate refusal, and a measurement artefact of recording "longest translation".

The incidental finding that changed a production setting: **latency varies 20× across rows in one
chain** (0.9-1.8s free tier, 21-37s Vertex). No single timeout can serve both.

### 6 · The alignment experiment (the decisive one)

Above. Constructed ground truth, accuracy identical where it worked, hard failure above ~100 tokens.

    75 tokens  -> OK
    90 tokens  -> OK
    105 tokens -> 400 INVALID_ARGUMENT
    120 tokens -> 3,064-character schema, two 120-element enums -> 400

## What changed in the product

- No schema is sent anywhere. `call.text` has no `schema` argument to pass one through.
- JSON *mode* is still requested where a row understands it — "answer with a JSON object" — and the
  shape is stated in the prompt.
- Content guards where a malformed field would otherwise be invisible: a clip translation is refused
  if it contains its own segment id, or runs past three times the length of its source.
- Timeouts moved into the catalogue per row, because of the 20× spread.
- A rotating log of every model call — caller, provider:model, outcome, latency, and an excerpt of
  what came back when an answer was refused. It cost an evening and paid for itself the same day:
  the "two minute hang" turned out to be a 1.97-second brief queued behind a dead connection.

## Reproducing

    align_experiment.py    ground-truth alignment accuracy, constrained vs prose, by size
    (probes for the clip selector, brief and translate stages are described above; each is the
     real production prompt plus the real request builder, with only response_format varying)

Set `GEMINI_API_KEY`, optionally `ACERVO_VERTEX_PROJECT` plus ADC, then:

    RUNS=2 SIZES=21,60,120 python align_experiment.py

## Notes

It has a name: the constraint tax — arXiv 2605.26128 measures exactly this validity-vs-correctness trade-off, and arXiv 2605.02363 covers usable-vs-correct. Practitioners report a ~17% creativity cost and 3.6–8.2× latency (Aidan Cooper, zeroentropy), and warn that "constraining the model too tightly too early can suppress reasoning… no room to think." vLLM had to suspend masking inside <think> blocks. Documented mitigations are a reasoning field inside the schema, or two-stage generation.
https://arxiv.org/pdf/2605.26128
https://arxiv.org/pdf/2605.02363
https://www.aidancooper.co.uk/constrained-decoding/
https://zeroentropy.dev/concepts/constrained-decoding/
https://docs.vllm.ai/en/latest/features/reasoning_outputs/
