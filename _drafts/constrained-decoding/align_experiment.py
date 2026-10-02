"""Does constrained decoding buy better word alignment, or only cost latency?

The question this answers: an alignment schema restricts every id to an enum of *this request's*
tokens, which looks like real work a prompt cannot do. Does that show up as accuracy?

Ground truth is constructed rather than annotated, so it is unambiguous by design: each sentence is
built from clauses whose Spanish and English words correspond one-to-one, and every clause is used
once, so no word has a second plausible partner.

    ALIGN_MODELS="gemini/gemini-3.1-flash-lite,gemini/gemini-3.5-flash-lite" \
    RUNS=2 python align_experiment.py

Set ACERVO_VERTEX_PROJECT and authenticate ADC to include vertex_ai/* models.
"""
from __future__ import annotations

import json, os, random, sys, time

sys.path.insert(0, "/Users/anton/projects/products/vocab-learning-tools/src")
sys.path.insert(0, "/Users/anton/projects/experiments/spoken-usage-retrieval/src")

from speech_retrieval.prompt_registry import ALIGNMENT_PROMPT, alignment_schema
from acervo.models import call, load_catalogue
from acervo.speech.provider import json_schema

# Clauses whose words correspond one to one. Content words only — no articles or prepositions that
# could attach elsewhere — so the correct answer is not a matter of judgement.
CLAUSES = [
    (["el", "perro", "corre"], ["the", "dog", "runs"]),
    (["mi", "hermana", "canta"], ["my", "sister", "sings"]),
    (["los", "niños", "duermen"], ["the", "children", "sleep"]),
    (["ella", "compra", "pan"], ["she", "buys", "bread"]),
    (["nosotros", "bebemos", "agua"], ["we", "drink", "water"]),
    (["el", "gato", "salta"], ["the", "cat", "jumps"]),
    (["tú", "lees", "libros"], ["you", "read", "books"]),
    (["ellos", "cocinan", "arroz"], ["they", "cook", "rice"]),
    (["yo", "escribo", "cartas"], ["i", "write", "letters"]),
    (["usted", "conduce", "despacio"], ["you", "drive", "slowly"]),
    (["la", "maestra", "explica"], ["the", "teacher", "explains"]),
    (["nadie", "escucha", "música"], ["nobody", "hears", "music"]),
]


def make_case(tokens_wanted: int, seed: int):
    """A source/target pair of roughly `tokens_wanted` tokens, plus the true alignment."""
    picker = random.Random(seed)
    order = picker.sample(range(len(CLAUSES)), len(CLAUSES))
    src_words, tgt_words, truth = [], [], {}
    index = 0
    while len(src_words) < tokens_wanted:
        spanish, english = CLAUSES[order[index % len(order)]]
        for offset, word in enumerate(spanish):
            truth[f"s{len(src_words) + offset + 1}"] = f"t{len(tgt_words) + offset + 1}"
        src_words.extend(spanish)
        tgt_words.extend(english)
        index += 1
    src = [{"id": f"s{i+1}", "text": w} for i, w in enumerate(src_words)]
    tgt = [{"id": f"t{i+1}", "text": w} for i, w in enumerate(tgt_words)]
    return src, tgt, truth


def score(parsed, src, tgt, truth):
    """Validity and accuracy. Validity is the claim constrained decoding makes; accuracy is the
    claim it is assumed to imply."""
    rows = (parsed or {}).get("alignments")
    if not isinstance(rows, list):
        return {"valid": False, "why": "no alignments list", "accuracy": 0.0}
    source_ids = {t["id"] for t in src}
    target_ids = {t["id"] for t in tgt}
    named, invented, correct = [], 0, 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        sid = row.get("source_id")
        targets = [t for t in (row.get("target_ids") or [])]
        if sid not in source_ids or any(t not in target_ids for t in targets):
            invented += 1
            continue
        named.append(sid)
        if truth.get(sid) in targets:
            correct += 1
    covered = len(set(named)) == len(source_ids) and len(named) == len(source_ids)
    return {
        "valid": bool(covered and not invented),
        "why": "" if covered and not invented else f"invented={invented} covered={len(set(named))}/{len(source_ids)}",
        "accuracy": correct / max(1, len(source_ids)),
    }


def ask(model, row, src, tgt, constrained):
    schema = json_schema(alignment_schema([t["id"] for t in src], [t["id"] for t in tgt]))
    lines = lambda ts: "\n".join(f'{t["id"]}: {json.dumps(t["text"])}' for t in ts)
    user = (f"Source language: es\nTarget language: en\n"
            f"Source text: {' '.join(t['text'] for t in src)}\n"
            f"Target text: {' '.join(t['text'] for t in tgt)}\n\n"
            f"Source tokens:\n{lines(src)}\n\nTarget tokens:\n{lines(tgt)}")
    shape = ("" if constrained else
             "\n\nReturn a single JSON object, and nothing else, matching this JSON Schema:\n"
             + json.dumps(schema, ensure_ascii=False))
    started = time.monotonic()
    answered = call.text(
        user, row=row, model=model, system=ALIGNMENT_PROMPT.text + shape, timeout=120,
        **({"schema": schema} if constrained else {"as_json": True}),
    )
    return answered.parsed, time.monotonic() - started


def main():
    catalogue = load_catalogue()
    models = os.environ.get(
        "ALIGN_MODELS", "gemini/gemini-3.1-flash-lite,gemini/gemini-3.5-flash-lite"
    ).split(",")
    sizes = [int(s) for s in os.environ.get("SIZES", "21,60,120").split(",")]
    runs = int(os.environ.get("RUNS", "2"))

    print(f"{'model':28} {'tokens':>6} {'mode':12} {'valid':>7} {'accuracy':>9} {'seconds':>9}")
    for model in models:
        row = catalogue.find("vertex" if model.startswith("vertex") else "gemini-free")
        for size in sizes:
            for constrained in (True, False):
                valid, accuracy, times, errors = 0, [], [], []
                for run in range(runs):
                    src, tgt, truth = make_case(size, seed=1000 + run)
                    try:
                        parsed, spent = ask(model, row, src, tgt, constrained)
                    except Exception as error:
                        errors.append(getattr(error, "reason", type(error).__name__))
                        continue
                    result = score(parsed, src, tgt, truth)
                    valid += result["valid"]
                    accuracy.append(result["accuracy"])
                    times.append(spent)
                mean = sum(accuracy) / len(accuracy) if accuracy else 0.0
                spent = f"{sum(times)/len(times):.1f}" if times else "-"
                label = "constrained" if constrained else "prose"
                print(f"{model:28} {len(src):>6} {label:12} {valid:>3}/{runs:<3} "
                      f"{mean:>8.0%} {spent:>9} {' '.join(errors)}", flush=True)


if __name__ == "__main__":
    main()
