---
title:     "Letting an LLM agent maintain a 40-file Org planning system"
date:      2199-01-01
permalink: /posts/2199/01/llm-agent-org-planning-system/
tags:
  - automation
  - emacs
  - productivity
---

**Status: stub.** Captured here: the angle, the background argument, the prior-art survey, and the differentiators. The post itself is not written.

---

TODO Also mention the changed approach:
from bottom up to top down

## The angle: planning, not knowledge management

Get this straight before writing a word, because the obvious framing is the wrong one.

Almost everything published in this space is about **ingestion** — pointing an agent at sources so it reads, links and files them into a growing knowledge base. That is not what this is. My vault and my plans are separate systems and may well deserve separate processes.

This post is about **the review step**. Specifically:

> I did the first half of GTD for ten years and never did the second half.

Allen's method is *collect*, then *organise*. I collected relentlessly — forty files, up to a thousand lines each. I never organised, because organising requires sitting with each item and making a judgement, and there was nobody to make it with. So the collection kept its shape and lost its truth. When I finally went through it this month, my own estimate is that **at least 70% was outdated or plainly wrong**: books superseded, repos archived, techniques the research has since contradicted, whole sections that were the same idea filed three times under different names. Notes I did not recognise as mine.

The agent is not automating that. It is being the second person in the room — the interlocutor that the organise step always required and that I never had.

And it is deliberately, almost perversely, slow. I could hand the folder over and have a clean result in an hour. Instead this has taken more than a week, because I argue with each finding. **The point is not a tidy plan; it is a plan that is mine.** A plan I did not argue with is an abstract copy of the internet, and I would not follow it.

That distinction — *interlocutor versus automation* — is the spine of the post. Everything below serves it.

---

## The background argument (the "why this matters" section)

The framing to open with is not "AI second brain". It is: *which specific, load-bearing part of an established method does this repair, and why did that part keep breaking?*

### Externalisation is the one part of GTD with a mechanism

Most of Getting Things Done is procedure. One piece of it has an actual psychological mechanism behind it, and it is the piece everybody who has ever used the method reports feeling: writing things down so you stop holding them.

Allen's own phrasing is "your mind is for having ideas, not holding them." The underlying finding is the **Zeigarnik effect** — unfinished goals intrude on attention, occupying working memory until they are resolved. The important refinement came from **Masicampo & Baumeister (2011)**, who showed that the intrusion is released not by *completing* the task but by *making a specific plan* for it. Unfinished goals stopped interfering with an unrelated task once participants had planned how they would be finished.

That is the whole engine of externalisation, and it is worth stating precisely because it is narrower than the folklore. It is not "writing things down feels nice." It is: *the mind releases an open loop in exchange for a credible plan.* Which immediately tells you what the system has to deliver to keep working — credibility. A capture system you do not trust does not release anything, because the loop stays open regardless of what is written in it.

### GTD's two abandonment points are both mechanical

GTD asks for two recurring rituals, and they are precisely the two things people stop doing:

1. **Processing the inbox** — taking each captured item and deciding what it is, whether it is actionable, what the next action is, and where it belongs.
2. **The weekly review** — a full pass over everything open: what moved, what is stuck, what is no longer worth doing.

The weekly review in particular is the immune system of the method. It is also the most expensive thing in it, and it is the first thing to go in a busy month. And once it goes, the system stops being trustworthy, and once it stops being trustworthy, externalisation stops releasing the loops, and the whole thing quietly becomes a graveyard of stale text files. That failure chain is worth spelling out, because it explains why so many people describe GTD as something they "did for a while."

Now: look at what those two rituals actually consist of. Routing an item to the right place. Noticing what has gone stale. Spotting the same thing captured three times. Deciding that something is no longer worth doing. **These are mechanical, judgement-shaped, and boring — which is the exact profile of the work an LLM is now good at.**

So the thesis is not "AI makes you productive." It is narrower and more defensible: *the two rituals whose cost caused people to abandon the method are now cheap, and that changes whether the method is viable.*

### The counter-argument, which the post must not dodge

If Masicampo & Baumeister are right that the release comes from *making the plan*, then handing the planning to an agent is not obviously a win. Possibly you get a well-organised system and a head that is just as full, because you never did the cognitive act that closes the loop.

This is the most interesting question in the whole area and nobody in the current literature is asking it. Do not resolve it cheaply. Two candidate answers to explore, both testable against my own use:

- The approval step *is* the planning act, compressed. Reading "this task is stale, here is why, delete it?" and deciding yes may do the same work as generating the thought, at a fraction of the cost.
- Or it is not, and the loop only closes for the items you actually argued with. In which case the design implication is that the agent's job is to force the decision, not to make it — which is what the approval protocol below already does, though for a different reason.

There is a real experiment here: track which decisions I rubber-stamped versus argued with, and see which ones I stop thinking about afterwards.

---

## Prior art, part 2: the planning direction

Searched separately from the knowledge-management survey below, because it is a different question. Result: **the work exists, but almost entirely at team scale.**

- **Agentic backlog grooming is a solved and well-covered problem for Jira, GitLab and Agile product backlogs.** Stale-label sweeps at 90 days, duplicate detection across titles and descriptions, obsolete tickets referencing features that no longer exist. One published case cut a backlog from 847 tickets to 312 and found 73 sets of duplicates. Every lens in my pipeline has a team-scale counterpart already shipping.
- One line from that literature transfers almost verbatim and is worth stealing for the post: **"Backlogs grow not because people are careless, but because creating a ticket is cheap while closing one has a social cost."**

  The personal version is worse, and this is the observation the post should be built on. In a personal plan there is no colleague to embarrass you — the cost of closing is internal and heavier. **Deleting "learn TRIZ" is not admitting a ticket is stale. It is admitting I am not going to become the person who learns TRIZ.** That is why ten-year-old plans do not get pruned by their owners, and it is exactly why a second party helps: the agent has no stake in who I was going to be, so it will say the thing plainly, and I only have to agree.
- At *personal* scale the published work is thin and pointed at the wrong half: "replace your todo app with Claude Code" pieces are about **capture and execution** — get tasks in, get them done. I found nothing serious on an agent as the counterparty for **periodic review of a personal plan**.
- Org-mode plus agent is thinner still, and the one closest example — a daily todo generator pulling from calendar, Linear and GitHub — is generation, not review, has no approval step, and its author abandoned it and went back to paper by March 2026.

**Conclusion: the review framing at personal scale is the genuinely thin spot.** Not the tooling, not the approval mechanism, not the pruning — those all exist somewhere. What is unclaimed is the argument that *GTD's organise step is the thing that broke, the reason it broke is that it needs a second person, and an LLM is now a serviceable second person.*

## Prior art, part 1: the knowledge-management space

Crowded, and worth citing precisely so the post cannot be dismissed as unaware. **Do not write as if the idea is new.** Checked August 2026:

- **`AgriciDaniel/claude-obsidian`** — 10.3k stars, created April 2026, actively maintained. A self-organizing second brain for Claude Code plus Obsidian: drop in sources, it reads them, writes linked notes, flags contradictions, maintains a living index. Critically, **it already has an approval mechanism** — preview-then-apply, JSON plans, SHA-256 hashes, one recoverable transaction per knowledge operation.
- A steady stream of 2026 tutorials on Obsidian + Claude Code as a second brain (DEV, MindStudio, various personal blogs), most of them variations on Karpathy's LLM-wiki pattern.
- **Org-mode specifically** is thinner but not empty: `majorgreys/org-roam-skill` (Claude Code plugin for org-roam via emacsclient), `karthink/gptel`, `rksm/org-ai`, agent-shell as an Emacs agent frontend. Teal Larson wrote up an agent that pulls calendar, Linear and GitHub into a generated daily org todo list — no approval step, and he abandoned it by March 2026 and went back to pen and paper.
- The **human-in-the-loop** framing is well established in the enterprise-governance literature, including the specific pattern of the agent writing to a review folder rather than the canonical store, and the known problem of **automation bias** — humans trusting the agent more than is warranted.

**The honest correction to my own note in `Blog.org`:** I wrote that the approval protocol was "a working answer I have not seen written up." That is no longer true — `claude-obsidian` shipped a more rigorous version of the transactional part four months ago. The differentiator has to be somewhere else, and it is.

---

## What is actually new here

The strongest claim is the framing itself, set out at the top: **GTD's organise step is what broke, it broke because it needs a second person, and an LLM is now a serviceable second person.** The six below are what makes that concrete. None has to be unclaimed on its own.

### 1. The system is built around deletion, not accretion

Every project above is an **ingestion** engine: capture more, link more, index more, never remove. The vault only grows.

My pipeline runs `vet → dup → task → destination`, and `vet` — the gate that everything else runs behind — is a *deletion* lens. It asks whether the item deserves to exist at all: superseded, abandoned, dead link, SEO listicle where a primary source exists, six links where two would do. A `DROP` verdict ends the item there. The instruction in my own repo is literally "prune, don't preserve."

This inverts the premise of the entire category, and the argument for it is strong: **an LLM makes accretion free, which means accretion is no longer the bottleneck — curation is.** When ingesting a source costs nothing, a knowledge base grows until its own size is the problem. The scarce operation in 2026 is not "file this," it is "this is obsolete, here is why, and here is what replaced it." I have not seen anyone build for that, and it is a genuinely contrarian thesis in a category where everyone is racing to ingest faster.

Concrete material to show: entries that survived ten years untouched and died in ten seconds under `vet`, with the reason. Speed reading, dead GitHub projects, a plugin archived by its own author, a book resting on a failed replication.

### 2. Charters: per-file editorial intent as the spec the agent is graded against

Each of my 40 files opens with a charter — what lives here, **what does not live here**, and what "good" means *in this file specifically*. Not a global standard. A technical plan wants currency and job-relevance; a hobby file wants clean design and things worth doing; a travel file wants personally interesting over comprehensive.

The "what does not live here" clause is the load-bearing one, and it is what actually resolves routing. The competing systems do vault linting and health checks from generic rules — orphan notes, broken links, missing frontmatter. Nobody is asking the owner to write down their editorial intent per file and then holding the agent to it.

Two things make this worth a post rather than a paragraph:

- **The charter is falsifiable.** My own instructions say a charter can be wrong, and that if it produces a bad result the agent should say so and propose the alternative. So the spec and the agent argue with each other, and the spec gets revised. That is a much more interesting relationship than "config file."
- **It scales the human's attention correctly.** I do not have to remember the boundary between forty files. I wrote it down once per file, and the boundary questions get decided against text rather than against whatever I happen to think this afternoon.

### 3. The findings ceiling as an anti-rubber-stamp mechanism

`claude-obsidian`'s approval is *transactional* — hashes, atomic apply, rollback. Mine is *cognitive*: a hard cap of about fifteen findings per pass, with an explicit instruction to stop and propose staging if a scope produces more.

The reason is stated in the skill itself: **long lists get rubber-stamped, and rubber-stamping loses exactly the corrections that make the review worth doing.** An approval step that a human clicks through without reading is not an approval step; it is a compliance ritual that produces the *feeling* of oversight while providing none.

This is the automation-bias problem from the governance literature, operationalised as a batch-size limit. That literature names the failure; I have not seen anyone name the fix as *cap the batch*. It is one sentence in a skill file and it is probably the most transferable idea I have.

### 4. It is a *planning* system, not a knowledge base

Everything above is notes and wikis. Mine is tasks with state — TODO, NEXT, INPR, WAIT, MAYB, DONE — feeding a live agenda.

The stakes are different and the failure mode is different. An agent that garbles a note leaves you with a wrong fact you will probably catch. An agent that garbles a plan changes what you actually do next week, and you will not catch it, because the plan *is* the thing you consult instead of thinking. Worth being explicit that this is the higher-risk case, and that the approval protocol is not paranoia.

### 5. The substrate is ten years of real, messy notes

Not a demo vault. Forty files accreted since roughly 2015, some still in Russian, entries captured with genuine interest and no follow-through, dead links, three sections that were the same idea under different names. Every tutorial in the survey above is written against a clean vault built for the tutorial.

The failure modes only appear on real data, and they are the interesting part: the agent confidently proposing a modern replacement that does not exist, mistaking old-but-foundational for obsolete (there is an explicit guard for this in my instructions — "SVM, PCA, KL-divergence, Sutton & Barto are foundational, not stale"), or flattening a section's voice while tidying it.

---

### 6. It is slow on purpose

Worth its own section because it cuts against everything else written about agents. Every piece in the survey sells throughput: how fast the vault organises itself, how many tickets the sweep closed. Mine is a week and counting on forty files, one section at a time, arguing with individual findings.

The justification is the Masicampo mechanism above. If the release comes from making the plan, then speed is not just unnecessary, it is **counterproductive** — a plan produced without my judgement in it does not close any loops, however tidy it looks. The batch ceiling exists for the same reason: it is a deliberate throughput limit whose only purpose is to keep me reading.

"I built an agent workflow and then capped its throughput on purpose, here is why" is a better post than another speed benchmark.

---

## Was Emacs and Org the right choice? (a section the post should include)

Readers will ask, and the honest answer is more interesting than a defence.

**What org bought, and it turns out these are exactly the properties the review protocol needs:**

- **A formal grammar.** Org has a real parseable spec — keywords, priority cookies, tags, timestamps, drawers. The state machine (TODO → NEXT → INPR → WAIT → MAYB → DONE) is defined in the Emacs configuration, and the agent's instruction file is *generated from that configuration* rather than hand-maintained. So the conventions the agent is held to cannot drift from the conventions the system enforces. Markdown checkboxes have no equivalent.
- **The agenda is a query across all forty files.** "What is open everywhere, what is stale, what is scheduled" is answerable at all. That is what makes a whole-system review tractable.
- **Diff review.** This is the big one, and it was luck rather than foresight: **the approval protocol requires a diff-review environment, and Emacs is one.** Proposed changes appear as diffs next to the text, in the editor, under git. Obsidian is not a diff-review environment in any meaningful sense. The protocol I ended up needing would have been much harder to run there.

**What it cost:**

- Mobile is second class. Orgzly and Beorg work, but they are not the desktop experience, and the queries most worth asking often happen away from the desk.
- Roughly 9.8k lines of Elisp to get an agenda worth looking at. That would be a damning number if it had stayed private, but it became a product, so it is investment rather than sunk cost.
- A smaller ecosystem and fewer integrations than the Obsidian world.

**Verdict: not a mistake, and it looks better in hindsight than it did at the time** — because the review discipline I eventually arrived at leans on properties org happens to have. Obsidian would have made capture and mobile easier and made this month's work considerably harder.

**The honest self-criticism, which belongs in the post:** I built the agenda before I had a review discipline. Nine thousand lines of Elisp made the plan *visible*; they did nothing to make it *true*. The thing that actually fixed the files was the charter-plus-lens protocol — a few hundred lines of prose — and I could have written that on day one. Tooling first, judgement later, is the same mistake as collect-then-never-organise, one level up.

---

## Do we even need tasks? (the sharpest question, and it deserves a section)

Put the challenge at its strongest: if 70% of a task system was dead weight, maybe the task system was the error. Maybe it should all have been a vault.

**The case against tasks.** Most of what was in those files was never a task. It was *interest*. "Book X." "Article Y." A bookmark wearing a TODO keyword. And a TODO keyword on a bookmark is a small lie that accrues interest — every agenda view re-presents it as a commitment, so it generates a little guilt, and guilt about a thing you were never going to do is pure cost. In a vault those same items are inert and harmless. Nothing about "here is a list of books on productivity" needs a state machine.

**The case for tasks.** Some things genuinely are commitments with a next action, a state, and a consequence for not doing them. Take the screener. Fix the schema before generating more notes. Those need to *leave my head*, and by the Masicampo mechanism that only happens if they are somewhere I trust to resurface them at the right moment. A note does not resurface. That is the entire function of an agenda, and no amount of good vault structure replaces it.

**So the answer is a boundary, not a choice — and the mistake was never "using tasks", it was admitting non-tasks into the task system.** Every `Book X` heading was a category error, and forty files of category errors is what 70% dead weight actually looks like.

The general form, which is the transferable idea:

> A task system's integrity depends entirely on a high bar for entry. Capture tools exist to lower that bar to zero. GTD knew this — the inbox is the low-bar zone and *processing* is where the bar gets applied. Skip processing and the low-bar zone silently becomes the whole system.

Which is exactly what happened to me, and it closes the loop with the opening: the second half of the method is not optional decoration, it is the part that keeps the first half from poisoning you.

The architecture I ended up with — **commitments in org, reference and shelves in the vault, one link between them** — is the right one. I just arrived at it a decade late and by paying off the debt by hand.

**The test of whether any of this worked** is not how good the files look today. It is whether the entry bar holds. If I am doing this again in a year, it did not, and the honest follow-up post is about why.

---

## Notes for writing

- **Uniqueness is not the bar.** Papers need novelty; a blog post needs a specific, credible, first-person account. The crowded prior art makes this post *more* useful, not less — "I read those and here is where they did not fit my case" is a service. Stop optimising for nobody-has-done-this and optimise for nobody-has-done-this-*and-written-honestly-about-what-broke*.
- **Lead with the failure chain, not the tooling.** Collected for ten years, never organised → 70% dead → untrusted plan → externalisation stops releasing anything → guilt-generating graveyard. That earns the rest of the post from readers who do not care about Emacs.
- **Do not bury the prior art.** Cite `claude-obsidian` early and generously, then say what is different. A post that pretends the space is empty gets dismissed in the first comment.
- Titles, favouring the review framing over the deletion one now: *"I did the first half of GTD for ten years"*, *"The organise step needs a second person"*, or on the deletion angle *"Your second brain does not need more ingestion"*.
- **Concrete before-and-after is the strongest evidence available and it is free** — I have the git history. One real section, before and after, with the reasons. Productivity.org went from ~70 accreted items to ~35 with bodies.
- Screenshots carry the Emacs half, same budget note as the agenda-rebuild post.
- The Masicampo counter-argument is the section that makes this more than a tutorial. Do not cut it for length.
- Cross-reference: this shares a spine with the agenda-rebuild post in `Blog.org`. Decide which one goes first — probably that one, so this can assume the system exists.

## References to check before publishing

- Masicampo, E. J., & Baumeister, R. F. (2011). "Consider it done! Plan making can eliminate the cognitive effects of unfulfilled goals." *Journal of Personality and Social Psychology*. Verify the exact claim and effect before citing.
- Zeigarnik (1927) — cite as the origin, note that the effect itself has a mixed replication record; the Masicampo result is the load-bearing one.
- Allen, D. *Getting Things Done* (2015 revised edition). My own full summary is in the vault.
- https://github.com/AgriciDaniel/claude-obsidian
- https://www.teallarson.dev/blog/2026-01-28-agentic-org-file-gen
- https://github.com/majorgreys/org-roam-skill
