"""Fill <!-- SERIES --> and <!-- REFS --> markers in the agent-memory drafts. Re-runnable.

Run from anywhere: python3 _drafts/agent-memory-series/fill.py. Reads ~/papers/library for author, title and year.
"""
import re, sys, pathlib

DRAFTS = pathlib.Path.home() / "Library/CloudStorage/Dropbox/notes/blog/_drafts"
PARTS = [
    ("1-why", "One conversation, five memory systems"),
    ("2-the-map", "A map of memory systems"),
    ("3-frontier-assistants", "What ChatGPT, Claude and Gemini ship"),
    ("4-textual-memory", "Textual memory: one profile, rewritten"),
    ("5-mem0", "Mem0: facts in a vector store"),
    ("6-graphiti", "Zep and Graphiti: facts with dates, in a graph"),
    ("7-letta", "Letta: an agent that edits its own memory"),
    ("8-honcho", "Honcho: a reasoner that works in the background"),
    ("9-the-experiment", "The experiment: 67 changed facts"),
]
url = lambda slug: f"/posts/2199/01/agent-memory-{slug}/"

# reference index from the paper library
lib = pathlib.Path.home() / "papers" / "library"
index = {}
for f in lib.rglob("*.md"):
    head = f.read_text(errors="ignore")[:3000]
    m = re.search(r"^arxiv:\s*'?([\d.]+)'?", head, re.M)
    if not m:
        continue
    title = re.search(r"^title:\s*(.*?)\s*$", head, re.M).group(1)
    if title[:1] in "'\"":
        title = title[1:-1].replace("''", "'")
    authors = re.search(r"^authors:\s*\[(.*?)\]", head, re.M)
    names = [a.strip().strip("'\"") for a in authors.group(1).split(",")] if authors else []
    sur = lambda n: n.split()[-1]
    who = (f"{sur(names[0])} et al." if len(names) > 2 else
           " and ".join(sur(n) for n in names) if names else "")
    year = re.search(r"^published:\s*'?(\d{4})", head, re.M)
    index[m.group(1)] = (who, title, year.group(1) if year else "")

def block(text, tag, body):
    pat = re.compile(rf"<!-- {tag} -->.*?<!-- /{tag} -->|<!-- {tag} -->", re.S)
    return pat.sub(lambda _m: f"<!-- {tag} -->\n\n{body}\n\n<!-- /{tag} -->", text)

missing = []
for n, (slug, short) in enumerate(PARTS, 1):
    path = DRAFTS / f"2199-01-01-agent-memory-{slug}.md"
    s = path.read_text()
    items = []
    for k, (sl, sh) in enumerate(PARTS, 1):
        items.append(f"{k}. **{sh}** (this part)" if k == n else f"{k}. [{sh}]({url(sl)})")
    top = "*How LLM agents remember*, a series in nine parts:\n\n" + "\n".join(items)
    prev = f"[← Part {n-1}: {PARTS[n-2][1]}]({url(PARTS[n-2][0])})" if n > 1 else ""
    nxt = f"[Part {n+1}: {PARTS[n][1]} →]({url(PARTS[n][0])})" if n < len(PARTS) else ""
    bottom = "---\n\n" + " · ".join(x for x in (prev, nxt) if x)
    # first marker = top, last = bottom
    parts = re.split(r"(<!-- SERIES -->(?:.*?<!-- /SERIES -->)?)", s, flags=re.S)
    markers = [i for i, p in enumerate(parts) if p.startswith("<!-- SERIES -->")]
    parts[markers[0]] = f"<!-- SERIES -->\n\n{top}\n\n<!-- /SERIES -->"
    parts[markers[-1]] = f"<!-- SERIES -->\n\n{bottom}\n\n<!-- /SERIES -->"
    s = "".join(parts)
    # references: arXiv link definitions, in order of first use in the text
    defs = re.findall(r"^\[([^\]]+)\]: https://arxiv\.org/abs/([\d.]+)\s*$", s, re.M)
    body_text = s.split("## References")[0]
    def first_use(label):
        i = body_text.find(f"][{label}]")
        return i if i >= 0 else 10**9
    defs.sort(key=lambda d: first_use(d[0]))
    lines = []
    for label, aid in defs:
        if aid not in index:
            missing.append((path.name, aid)); continue
        who, title, year = index[aid]
        lines.append(f"- {who}, [{title}][{label}] ({year})")
    if "<!-- REFS -->" in s:
        s = block(s, "REFS", "Papers:\n\n" + "\n".join(lines) if lines else "")
    path.write_text(s)
    print(f"{path.name}: {len(lines)} papers")
print("missing:", missing)
