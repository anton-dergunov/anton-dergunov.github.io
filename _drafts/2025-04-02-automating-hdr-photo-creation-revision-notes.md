---
title:     "Revision notes — Automating HDR Photo Creation in Adobe Lightroom"
published: false
---

# Revision notes: *Automating HDR Photo Creation in Adobe Lightroom*

**Target post:** `_posts/2025-04-02-automating-hdr-photo-creation-in-adobe-lightroom.md`
**Published:** 2 April 2025 · also cross-posted to Medium
**Notes written:** 12 August 2026 · all tool/version facts verified on that date
**Plugin repo:** <https://github.com/anton-dergunov/lightroom-exposure-bracket-auto-stacker>

This file is the working checklist for revising the post. It is not a draft of the post itself. Items are ordered by priority: P0 items break the article for readers today, P1–P3 are the content gaps that decide whether the article is worth keeping alive, and the rewrite options at the end decide the shape.

**Do not change the permalink** (`/posts/2025/04/automating-hdr-photo-creation-in-adobe-lightroom`). The post is indexed and currently ranks on the first page for queries about Lightroom bracket auto-stacking — as of August 2026 it came up as the #2 organic result for "Lightroom Classic 2026 HDR merge automatic bracket detection batch". Add an "Updated: &lt;date&gt;" line under the title instead. Whatever gets fixed here must also be applied to the **Medium cross-post**, which currently carries the same broken instructions.

---

## P0 — Blocking bugs. Fix these today, independently of everything else.

### P0.1 The clone URL is dead

The post says:

```sh
git clone https://github.com/anton-dergunov/lightroom-hdr-auto-stack.git
cd lightroom-hdr-auto-stack
```

`anton-dergunov/lightroom-hdr-auto-stack` returns **404**. The repository is `anton-dergunov/lightroom-exposure-bracket-auto-stacker`, which the post links correctly in the intro, the "Final Thoughts" section and reference 1 — but not in the one place a reader actually copies from. Anyone following the walkthrough fails at step 2 of the installation.

Correct block:

```sh
git clone https://github.com/anton-dergunov/lightroom-exposure-bracket-auto-stacker.git
cd lightroom-exposure-bracket-auto-stacker
```

### P0.2 The plugin folder name is wrong

The post says: *"Click **Add** and select the `auto-stacker.lrplugin` folder."*

The repository contains **`auto-stacker.lrdevplugin`**. Lightroom treats `.lrdevplugin` (unpackaged, source-visible, for development) and `.lrplugin` (packaged for release) differently, and a reader looking for a folder that does not exist will either give up or add the wrong thing.

This is almost certainly what produced the only support issue the project has ever received: [issue #1, "The 'Plug in Extra' menu is empty"](https://github.com/anton-dergunov/lightroom-exposure-bracket-auto-stacker/issues/1) (gonn95, 6 June 2025). An empty Plug-in Extras menu is the classic symptom of a plugin folder that Lightroom loaded but could not register, or of the user pointing the Plug-in Manager at the wrong directory.

Two things to decide:

1. **Short term:** correct the post to say `auto-stacker.lrdevplugin`.
2. **Better:** ship a proper `auto-stacker.lrplugin` release. Rename the folder for distribution, attach a zip to a GitHub Release, and have the post point at the release rather than at a `git clone`. Most Lightroom plugin users are photographers, not developers; asking them to clone a repo is already a conversion filter, and asking them to clone a repo *and* find a `.lrdevplugin` folder is two.

### P0.3 Reference 6 is misspelled

"Photomatrix" → **Photomatix**. It reads as a first-time-hearing-of-it mistake in a post whose authority depends on knowing the field.

### P0.4 Two repo links inside one post disagree

Audit every URL in the post in one pass. The plugin is referred to as "Lightroom Auto Stacker Plugin" in prose, `lightroom-hdr-auto-stack` in the shell block, and `lightroom-exposure-bracket-auto-stacker` in the links. Pick one name and use it everywhere — see the naming discussion in P6.4.

---

## P1 — The article's central premise is now out of date

**Adobe released Lightroom Classic 15 on 28 November 2025**, eight months after publication. Three changes bear directly on the post's argument.

### P1.1 Auto-Stack by Capture Time now has millisecond resolution

The post's stated justification for building the plugin is:

> *"In theory, this should group all bracketed sequences automatically. In practice, however, I've found this method can be unreliable."*

With only second-level granularity, that was a fair finding — a 3-frame bracket and the next handheld frame can share a timestamp. Lightroom Classic 15 added **milliseconds** to Auto-Stack by Capture Time. A burst fired at, say, 8 fps separates cleanly at millisecond precision in a way it cannot at second precision.

**This must be re-tested before the post can honestly keep its current framing.** If millisecond stacking now works well on his own files, the post's premise has to be rewritten — not deleted, but restated (see P1.4). If it still fails, that is a *stronger* result than the original claim, because it now survives the obvious objection.

### P1.2 Auto-Stack by Visual Similarity is new

Lightroom Classic 15 also added AI-based grouping by visual similarity, reachable from the same place (right-click in Library, or Photo → Stacking) as well as from the new Assisted Culling panel. Reported behaviour is that it **over-groups**: reviewers note it will stack a horizontal and a vertical frame of the same subject, in materially different compositions, because it recognises the subject rather than the burst.

That is exactly the wrong failure mode for exposure brackets — over-grouping silently merges two adjacent brackets of the same scene into one stack, which then merges into one wrong HDR. Worth demonstrating with a real example.

### P1.3 Other HDR-relevant changes in Classic 15

- A **headroom slider** for HDR.
- **Open in Photoshop as 32-bit** for HDR images, which makes a true 32-bit round trip possible.
- Assisted Culling (AI-assisted selection), which is adjacent to the "review all options up front" workflow the post describes in its Real-World Workflow section.

### P1.4 Turn the obsolescence into the article's new spine

This is the opportunity, not the embarrassment. There are now **four** ways to group exposure brackets in the Adobe ecosystem, and nobody has compared them honestly:

| Method | Signal | Available in |
|---|---|---|
| Auto-Stack by Capture Time (seconds) | timestamp gap | Classic, pre-15 |
| Auto-Stack by Capture Time (milliseconds) | timestamp gap | Classic 15+, Nov 2025 |
| Auto-Stack by Visual Similarity | pixel content / learned embedding | Classic 15+, Nov 2025 |
| This plugin | `MakerNotes` sequence fields | any Classic with plugin support |

The rewritten article should run **all four over the same real shoot with known ground truth** and report precision and recall per method. Concretely: take a day's take with a mix of single frames, 3-frame brackets and 5-frame brackets, hand-label the true grouping once, and score each method against it.

The engineering point the article should land, stated plainly:

> Three of these methods infer the bracket. One reads it. Time and pixels are both *proxies* for "these frames were fired as one sequence"; the camera already recorded that fact directly, and it is sitting in the file.

That framing is what turns a plugin announcement into an article worth reading, and it is the same point regardless of how the millisecond re-test comes out.

---

## P2 — The article uses the 2010s meaning of "HDR" and misses the biggest change of the decade

Throughout the post, "HDR" means: merge brackets → tone-map down → SDR image. That was the complete meaning of the term until 2023. It is no longer.

**Adobe added true HDR edit and export on 10 October 2023** — Lightroom Classic v13, Lightroom (cloud) v7, Lightroom iOS/Android v9, with partial support at lightroom.adobe.com. That is a year and a half *before* this post was published, and the post does not mention it at all. This is the single largest content gap.

### What the new section has to cover

- **HDR display, not HDR merge.** The modern sense is an image that actually renders brighter-than-diffuse-white on an HDR-capable screen, rather than one whose range has been compressed into SDR.
- **Gain maps.** A gain map is an embedded second layer that encodes the difference between the SDR rendering and the HDR rendering. Standardised as **ISO 21496-1**. The base image stays SDR, so the file degrades gracefully: an SDR viewer shows the ordinary photo, an HDR viewer applies the gain map. In Lightroom, a gain map is written when HDR output *and* "maximize compatibility" are both on (the latter is implied for JPG).
- **Export formats.** The HDR Output toggle is only offered for **JPG, AVIF and JXL**. TIFF preserves HDR data by default when the photo was edited in HDR mode; Lightroom Classic can also write **32-bit TIFF** and **JXL**. Practical guidance: JPG-with-gain-map for the web (Lightroom and desktop Chrome render it; other apps fall back to SDR), AVIF for iOS Photos full-screen, JXL or 32-bit TIF when the file needs to stay editable.
- **Hardware.** Needs an HDR-capable display. Automatic on Apple displays and mobile devices; PC often needs manual configuration. **This is directly relevant to him** — he culls and edits on an iPad, which has an HDR display, so this is not a theoretical section.
- **What it changes about tone mapping.** Half of the post's "Common Issues with HDR" list is really a list of *tone-mapping* artifacts, and tone mapping is now partly optional.

### Reframe his own example with this

The post says of the Goblin Teller photo:

> *"it appears flat, lacking clear separation between the foreground and background."*

That is a tone-mapping artifact with a mechanical explanation worth giving: global contrast is the budget being spent to compress the scene's range into SDR, so the more range you recover, the flatter the mid-tones become. In HDR-output mode a large part of that trade goes away because the highlights no longer have to be squeezed into the same 0–100 nit box. Re-processing that exact frame in HDR mode and showing the two side by side would be the most persuasive single image pair in the article.

*(Caveat to state honestly in the post: a side-by-side comparison of SDR vs HDR output cannot itself be shown accurately on an SDR screen. Say so, and describe what the reader would see on an HDR display rather than pretending the screenshot conveys it.)*

---

## P3 — The post conflates HDR merge with exposure fusion

The post treats these as one operation and mentions LR/Enfuse in passing as just another tool. They are fundamentally different algorithms, and the distinction is the most interesting technical content available here.

**True HDR merge** — Debevec & Malik (1997), Robertson et al. (1999). Recovers the camera response curve, then reconstructs a **linear, scene-referred radiance map** in floating point. Tone mapping is a *separate* subsequent step that maps that radiance map to a displayable range. This is what Lightroom's Photo Merge → HDR does, which is why the output is a floating-point DNG rather than an image.

**Exposure fusion** — Mertens, Kautz & Van Reeth (2007). Never builds a radiance map at all. Blends the LDR frames directly using per-pixel weights derived from three measures: local contrast, saturation, and well-exposedness (how close a pixel is to mid-tone). Usually implemented as a Laplacian pyramid blend to avoid seams. There is no tone-mapping step because there is never anything outside display range. This is what `enfuse` does, and it is why fusion output tends to look more "natural" and less "HDR-looking".

Why the distinction matters practically:

- Fusion **cannot** produce a true HDR file, because it never has more range than the display. So fusion and the P2 gain-map story are mutually exclusive paths, and the article should say which one it is recommending for which purpose.
- Merge preserves scene linearity, which is what makes further editing (white balance, exposure) behave physically.
- Fusion is more robust to a badly chosen bracket and to sensor noise, because it is picking well-exposed pixels rather than solving for radiance.

**The demonstration to build:** one bracket set, four outputs, side by side:

1. Lightroom Photo Merge → HDR (Debevec-family merge + Adobe tone mapping)
2. `align_image_stack` + `enfuse` (Mertens fusion)
3. OpenCV `createMergeMertens` (Mertens again, but as code the reader can run and modify)
4. Lightroom Photo Merge → HDR with **HDR output** enabled (the 2026 answer)

Nobody else has published that comparison on the same frames. It is the thing that would lift this above every other HDR tutorial online.

---

## P4 — Free and open-source alternatives (the survey he asked for)

**Verification date: 12 August 2026.** Star counts, last-commit dates and release dates were read from the GitHub API on that date. Re-check before publishing — a table like this is only useful if it is dated, and its value decays.

**Headline conclusion: nothing meets all four criteria** (genuinely good quality, open source on GitHub, still developed, decent interface). The free HDR-merge ecosystem peaked around 2015 and the maintained projects are raw *developers*, not mergers.

| Tool | Status (12 Aug 2026) | Verdict for this workflow |
|---|---|---|
| [**HDRMerge**](https://github.com/jcelaya/hdrmerge) (jcelaya) | 428★ · last commit 24 Jul 2026 but only **1 commit in the last 52 weeks** · last tagged release **v0.5.0, January 2015** · a "nightly" tag from 2018 · 57 open issues | Algorithmically the closest free analogue to Lightroom's merge: takes raws via LibRaw, outputs a **floating-point DNG 1.4** you then develop normally. Has a CLI with `-o`/`-a` for batch use, which is exactly the scriptable primitive this workflow wants. But it is a maintenance-mode project with an 11-year-old release, and critically it has **no auto-alignment** — handheld brackets are on their own. |
| [**Luminance HDR**](https://github.com/LuminanceHDR/LuminanceHDR) | 669★ · last commit **June 2025** · last release **v2.6.0, July 2019** · 99 open issues | Stale. Eight tone-mapping operators, LibRaw-backed, alignment and anti-ghosting present. It is a competent 2010s tone-mapping application and it looks and behaves like one. Ignore the SEO sites currently calling it "the best free HDR software (2026 guide)" — check the repository, not the listicle. |
| [**darktable**](https://github.com/darktable-org/darktable) | 12.9k★ · very active · **5.6.0, June 2026** | Alive, excellent, and a genuine Lightroom alternative *as a raw developer*. But its "create HDR" function has **no automatic alignment** — [feature request #17326](https://github.com/darktable-org/darktable/issues/17326), open since August 2024, is titled exactly "Better HDR merge with auto-allignment". Handheld brackets come out misaligned. This is the deciding fact for anyone who does not shoot on a tripod. |
| [**RawTherapee**](https://github.com/Beep6581/RawTherapee) 5.13 (Jul 2026) / [**ART**](https://github.com/artpixls/ART) 1.26.7 (Jul 2026) | Both active | Excellent raw developers with strong highlight recovery and local tone mapping, but **no true bracket merge**. Not alternatives for this task. |
| **`align_image_stack` + `enfuse`** (Hugin) | Mature, stable, CLI, fully scriptable | **The strongest free option for this specific workflow.** It solves precisely what HDRMerge and darktable lack: `align_image_stack` handles the alignment, `enfuse` does Mertens exposure fusion with tunable `--exposure-weight`, `--saturation-weight`, `--contrast-weight`. No GUI, output quality genuinely good, and it batches trivially — which is the whole point of this project. Note it produces *fused LDR*, not a radiance map (see P3). |
| **OpenCV** (`createAlignMTB`, `createMergeDebevec`, `createMergeRobertson`, `createMergeMertens`, `createTonemapReinhard`/`Drago`/`Mantiuk`) + [**rawpy**](https://github.com/letmaik/rawpy) / LibRaw | Both very active (OpenCV pushed Aug 2026; rawpy May 2026) | Not a product — a toolkit. But this is the interesting one *for him specifically*: it makes the whole pipeline inspectable and writable in Python, which is both the natural home for the P3 comparison and the bridge to the career angle below. |
| [**libultrahdr**](https://github.com/google/libultrahdr) (Google) | 334★ · pushed Aug 2026 · active | Not a merger — a gain-map encoder/decoder. Relevant only to the P2 section: it is how you would produce Ultra HDR / gain-map JPEGs outside Adobe. |

### Paid alternatives

- **Photomatix** (HDRsoft) — still the serious commercial competitor, and notably it sells an [HDR Merge Batch Plugin for Lightroom](https://www.hdrsoft.com/download/hdr-batch-lightroom-plugin.html) (Lightroom 6 and Classic CC; Windows 10/11; macOS 11.5 through macOS 26 Tahoe) with 40 presets and DNG/TIFF/JPG/OpenEXR output. **It does not auto-detect brackets** — it requires photos already grouped into stacks, or a flat selection where every bracketed set has the same number of exposures. That makes it **complementary to this plugin, not competing with it**, and saying so in the post is both honest and good positioning: "if you want a different merge engine, use theirs — but you still need something to build the stacks, and that is what this does."
- **easyHDR** — still sold, still updated, no compelling advantage.
- **Aurora HDR** — discontinued. Do not recommend it.
- **Overall:** no paid tool is compellingly better than Lightroom's merge in 2026. Adobe caught up years ago, and the paid tools' historic selling point was aggressive tone mapping — which is exactly the look that dated worst.

### The recommendation to state in the article

**Do not switch.** Lightroom wins on the one thing that decides handheld bracket quality — automatic alignment plus deghosting — and it is already paid for. The single free tool worth adding to the workflow is `align_image_stack` + `enfuse`, and it should be added as a *comparison point and a scriptable escape hatch*, not as a replacement.

Note the interaction with the existing task in `Play/Photo.org`: *"Try Darktable seriously once, then decide whether free can replace Lightroom."* This survey answers a piece of that question in advance — for **HDR merge specifically**, free cannot replace Lightroom, because the free merge implementations do not align. That does not settle the general raw-development question, which is still worth doing on its own terms.

---

## P5 — Lightroom Classic vs cloud: what is actually true

The post says the two are separate and leaves it there. He was right in substance, but the details are the part everyone gets wrong, and publishing them clearly would be a service.

Verified facts (August 2026):

- **Separate catalogs.** They are not one library, and Classic syncs only one catalog at a time. Two Classic installs on two computers cannot sync catalogs with each other.
- **Classic *can* push to the cloud** via **synced collections** (or "All Synced Photographs"). But it uploads **2560px Smart Previews only — never originals**. The cloud side is therefore not a backup, and the full-resolution file cannot be retrieved on the iPad.
- **Smart previews do not count against the cloud storage quota** — which is a genuine advantage for anyone with a small plan or a slow connection, and worth stating.
- **Edits made in the cloud apps sync back to Classic**, where the original lives. So "cull and edit on iPad, export the final from Classic" is a real, supported workflow.
- **Smart collections do not sync** — only ordinary collections. Adobe has effectively frozen Classic's sync feature set.
- **Video syncs upward only** (mobile → Classic), never Classic → cloud.
- **Keywords only began syncing in the June 2026 release** — a long-standing gap that has just closed.
- Lightroom Queen explicitly warns that **photos created by "Edit in Photoshop" or by HDR/Panorama merge are easily missed during selective sync** — which is precisely this workflow's output.

### The workflow consequence worth testing and then writing up

The post's current Real-World Workflow ends with: export the HDR DNGs from Classic, then import them into Lightroom cloud. That round trip may be unnecessary.

**Alternative to test:** put the merged HDR DNGs into a *synced collection* in Classic. They appear on the iPad as smart previews. Cull and edit there. Edits sync back to Classic, which holds the full-resolution originals. Export finals from Classic.

**The trade-off, stated honestly:** the 1TB cloud library stops holding those originals, so the "my whole library is accessible from any device" property he describes in the post is weakened — he gets 2560px proxies instead. It is a real trade, not a free win, and which side is right depends on whether he values device-independence or round-trip elimination more.

Either way, *"which half of Adobe's ecosystem should hold your originals"* is a question thousands of photographers have and almost nobody has written up clearly. It could carry a section, or a short standalone post.

---

## P6 — Claims that need evidence, and content that is missing

### P6.1 "More reliable" is asserted, never measured

> *"I found this method to be more reliable, because it works even when timing between shots is inconsistent."*

This is the article's core claim and it has no evidence behind it. The P1.4 benchmark fixes it. Report precision and recall per method against hand-labelled ground truth on a real take. The repo already has `tests/` with `test_grouping.py` and a GitHub Actions workflow, so a labelled fixture set is a natural extension rather than new infrastructure.

### P6.2 "HDR isn't always the better version" — give the number

The post says he sometimes keeps the HDR and sometimes prefers a single exposure. **What fraction?** Over one real trip: how many brackets shot, how many HDRs kept, how many originals preferred, and — the interesting one — how often the *middle* exposure won. One honest number ("I keep the HDR in roughly 40% of cases") does more work than the three paragraphs currently there, and it is the kind of detail that makes a reader trust everything else.

### P6.3 The EXIF explanation muddles which fields are load-bearing

The post explains `EXIF:ExposureCompensation` arithmetic in careful detail (base 0.3, ±1.0 EV → −0.7, 1.3) but the plugin's grouping actually keys on `MakerNotes:ReleaseMode`, `MakerNotes:SequenceLength` and `MakerNotes:SequenceImageNumber`. A reader trying to port this to another camera will chase the wrong field. State explicitly: which fields are **required** for grouping, which are **corroborating**, and which are merely **illustrative**.

### P6.4 Missing: what the tool does *not* do

Add an explicit anti-goals paragraph. It does not merge anything — Lightroom does that. It does not tone-map, deghost or align. It does one thing: recover the grouping the camera already recorded. Saying so makes the tool easier to understand, easier to trust, and easier to contribute to.

### P6.5 Missing: false positives and edge cases

None of this is currently addressed and all of it will bite a reader:

- **5-frame and 7-frame brackets.** The post's example is 3. Does the tool handle other lengths? (`SequenceLength` says so, but the post never confirms it.)
- **Continuous vs single bracket drive mode** on Sony — different `ReleaseMode` behaviour.
- **DRO bracketing and white-balance bracketing.** Sony offers both, both produce sequences, and neither should be merged as HDR. If they set the same `ReleaseMode`, that is a false-positive source the tool must handle and the post must document.
- **RAW+JPEG shooting** — does it produce duplicate or half-populated groups?
- **Which Sony bodies were actually tested?** The post says "Sony cameras", generalising from an RX100 VII. He also shoots an A7C II and a ZV-E10, and `MakerNotes` tags vary by generation and body. Name the bodies actually verified; it costs nothing and it is the difference between a claim and a measurement.
- **Handheld bracket alignment** — the RX100 VII fires a bracket fast, but not instantly. Does Lightroom's auto-align cope, and at what frame rate does it stop coping?

### P6.6 Missing: `Shift+Cmd+H`, the headless merge

The walkthrough sends readers through the HDR Merge dialog. Lightroom Classic supports a **headless merge** (`Shift+Ctrl+H` / `Shift+Cmd+H`) which merges the selection using the last-used settings with no dialog at all — Auto Align and Auto Tone on, low deghosting. For a batch of 100 stacks this is the difference between a workflow and a chore, and the post never mentions it. This is probably the single largest remaining chunk of manual work the post could remove for its readers, and it requires no code.

### P6.7 Missing: how a reader inspects their own camera

Give the reader the exiftool one-liner so they can check what their own body records, and make it easy for them to report it back:

```sh
exiftool -G -a -s -ExposureMode -ReleaseMode -Sequence* -BracketMode -Bracket* -ExposureCompensation *.ARW
```

Then invite them to open an issue with the output for their camera. That converts passive readers into the exact contribution the project needs (see P7.2), and it is one paragraph.

### P6.8 Missing: this generalises beyond HDR

Exposure brackets are not the only sequence a camera records. **Focus bracketing** (the A7C II does it — and there is already a task in `Play/Photo.org` about learning macro focus bracketing on that body) and **panorama sets** have exactly the same shape: a burst that belongs together, recorded in metadata, that Lightroom will not group for you. Adobe's own long-running feature request is titled *"Better auto stacking for bracketing, HDR, Focus stacking and panoramas"* — one request covering all three, which is a strong signal that they are one problem.

This is both a natural feature expansion for the tool and a better story for the article: the tool is not an HDR utility, it is a *sequence recovery* utility, and HDR is the first application.

### P6.9 Smaller nits

- `--extension` defaults to `ARW`, which is Sony-only. Foreground that; a reader with Canon files will not guess.
- The Auto-Stack screenshot and the HDR Merge screenshot are pre-15 UI and will need retaking.
- The "Tip: when in doubt, bracket" box is good advice and should stay.
- The Le Gray / Ansel Adams history section is genuinely charming and gives the post character — **do not cut it** in any rewrite. It is one of the few things distinguishing this from generic tutorial content.
- The honest failure examples (the flat Goblin, the noisy Monster Book) are the second such thing. Also keep, and extend per P2.

---

## P7 — Plugin work (tracked separately in `Work/Products.org`)

Summarised here so the article and the code stay in sync; the org file carries the tasks.

### P7.1 Rename the project

The current name describes the *implementation* (it stacks) rather than the *idea* (it recovers the sequence the camera recorded). "Auto Stacker" also collides directly with Lightroom's own "Auto-Stack" feature, which now has two variants of its own — so the name will read as a clone of a built-in rather than as the thing that is more correct than both.

Better framing: **a stack-automation tool driven by camera metadata**. Name candidates to weigh: `camera-sequence-stacker`, `lightroom-bracket-tags`, `exif-stacker`. Whatever is chosen, GitHub redirects the old URL, so renaming is cheap — but the post, the README and the Medium copy must all be updated together.

### P7.2 Per-vendor configuration table — the architecture

[Issue #2, "Compatibility for Canon CR3 / DNG"](https://github.com/anton-dergunov/lightroom-exposure-bracket-auto-stacker/issues/2) has been open since 12 October 2025.

Do not merge a Canon special case. Restructure so a vendor is **data, not code**: a declarative table mapping vendor → the tags that identify a sequence, the tag giving its length, the tag giving position within it, and the values that mean "exposure bracket" as opposed to DRO/WB/focus bracketing.

Starting points for the table:

- **Sony:** `MakerNotes:ReleaseMode` (5 = exposure bracketing), `MakerNotes:SequenceLength`, `MakerNotes:SequenceImageNumber`, `MakerNotes:SequenceFileNumber`
- **Canon:** `MakerNotes:BracketMode`, `MakerNotes:BracketValue`, `MakerNotes:BracketShotNumber`
- **Nikon:** `MakerNotes:ExposureBracketValue`, `MakerNotes:AEBracketCompensation`
- **Fujifilm:** `MakerNotes:SequenceNumber` and related
- **Standard fallback:** `EXIF:ExposureMode` (2 = Auto Bracket) plus `EXIF:ExposureCompensation` deltas, which is vendor-neutral but weaker

This is the design that makes the project contributable: a Canon owner adds five lines of configuration and a test fixture instead of reading Lua and Python.

**The argument this supports — worth putting in the article as an aside, because it explains why the gap exists at all:** Adobe almost certainly has not implemented metadata-based bracket detection precisely *because* it would mean tracking every vendor's proprietary `MakerNotes` across every camera generation, forever. They already carry an enormous burden supporting the raw formats themselves. A per-vendor rule table maintained by the people who own those cameras is a shape that works for a community project and does not work for a vendor with a support contract — which is exactly why the built-in features are heuristics over time and pixels instead.

### P7.3 Collapse the two-step workflow

The Lua plugin runs inside Lightroom and can invoke external processes. Either have it call exiftool directly and drop the Python step, or have it invoke the Python script itself. Either way the `groups.txt` intermediate disappears from the user's view, and "run a script, then import a file into Lightroom" becomes one menu item. This is the single biggest usability win available and it is the thing the post currently apologises for.

### P7.4 Investigate driving the merge from the plugin

Check whether the Lightroom SDK can trigger Photo Merge → HDR, or whether the headless `Shift+Cmd+H` path can be scripted. If it can, the entire workflow becomes one click. If it cannot — which is the likely answer — document that clearly and prominently surface the headless shortcut instead (P6.6).

### P7.5 Ship the benchmark

Labelled fixture set + a scoring script over all four grouping methods, wired into the existing CI. This is what makes the article's central claim measured rather than asserted, and it is reusable every time Adobe ships a new heuristic.

### P7.6 Fix discoverability

5 stars, 0 forks, 2 issues in ~15 months. Given that the install instructions have been broken the entire time, quality is probably not the bottleneck — discovery is. After P0:

- Publish a tagged GitHub Release with a packaged `.lrplugin` zip.
- List it on [photographers-toolbox.com](https://www.photographers-toolbox.com/) — where the post already sends readers for LR/Enfuse, so it is demonstrably where this audience looks.
- Consider Adobe Exchange.
- Post it once to r/Lightroom and the Adobe community thread on bracket auto-stacking, where the demand is already documented.

---

## Rewrite options

### Option A — 2026 refresh (about half a day)

Keep one post. Fix P0 entirely. Add an "Update: what changed in Lightroom Classic 15" box (P1). Add an HDR-output / gain-map section (P2). Add the Classic-vs-cloud explainer (P5). Add the headless merge shortcut (P6.6). Fix the nits.

This is the minimum that makes the post defensible. Do it if the ambitious version is not going to happen soon, because P0 alone justifies the trip.

### Option B — split into two posts (recommended)

**Post 1 — for photographers.** Working title: *"Auto-stacking exposure brackets in Lightroom: time, pixels, or metadata."*

Spine: the four grouping methods, benchmarked on a real shoot with precision and recall. The plugin arrives as the *conclusion* rather than the premise. Closes with the dated free-and-paid alternatives table from P4 — that table alone is a search magnet, and nobody has an honest, dated version of it.

**Post 2 — for the technically curious.** Working title: *"What 'HDR' actually means in 2026."*

Spine: merge vs fusion (Debevec/Robertson vs Mertens), radiance maps, the camera response curve, why tone mapping produces the flat look, and how gain maps (ISO 21496-1) change the answer. Illustrated with the same bracket processed four ways per P3. Explains why phone photos look brighter than camera photos on the same screen — a question every reader has and almost nobody can answer.

The history section (Le Gray, Ansel Adams) belongs in post 2, where it frames the whole arc: every generation has fought the same fight with the tools it had.

### On the career angle

He asked whether this could connect to his career. Post 2 is the route, and it works without forcing:

- Bracketing → radiance recovery → tone mapping is a clean, visual introduction to **linear vs perceptual space**, which is a real and recurring source of bugs in image ML — the same mistake as doing arithmetic on gamma-encoded pixels.
- Exposure fusion's per-pixel weight maps (contrast, saturation, well-exposedness) are a hand-designed attention mechanism. Saying so is accurate and illuminating rather than a stretch.
- Dynamic-range normalisation, and the fact that the sensor's range and the display's range are different problems, is exactly the kind of thing that separates people who have processed images from people who have only trained on them.
- The plugin story is a small, real systems parable: *the correct signal was already in the metadata; two heuristics and an AI feature all approximate what one field states exactly.* That interviews well.

**But do not bolt an ML paragraph onto post 1.** A hobby article that is obviously careful signals more competence than a forced professional connection. If the ML link does not fit naturally, leave it out and let the craft speak.

---

## Verify before publishing

1. **Re-test millisecond Auto-Stack** in Lightroom Classic 15 on his own brackets. The millisecond claim comes from a single feature roundup and must be confirmed first-hand — the whole framing of post 1 depends on it.
2. **Test Auto-Stack by Visual Similarity** on a take containing two adjacent brackets of the same scene, to confirm or refute the over-grouping report.
3. **Test the Classic→cloud smart-preview round trip** with a merged HDR DNG, on the iPad, end to end — including whether the HDR DNG actually appears in the sync at all, given the documented warning about merge output being missed.
4. **Confirm the current Photomatix batch plugin price and Lightroom version support** before naming either.
5. **Re-check the alternatives table dates** (P4) immediately before publishing.
6. **Update the Medium cross-post** with every P0 fix at minimum.

---

## Sources

- [jcelaya/hdrmerge](https://github.com/jcelaya/hdrmerge) · [LuminanceHDR](https://github.com/LuminanceHDR/LuminanceHDR) · [darktable](https://github.com/darktable-org/darktable) · [darktable issue #17326 — Better HDR merge with auto-alignment](https://github.com/darktable-org/darktable/issues/17326) · [RawTherapee](https://github.com/Beep6581/RawTherapee) · [ART](https://github.com/artpixls/ART) · [google/libultrahdr](https://github.com/google/libultrahdr) · [rawpy](https://github.com/letmaik/rawpy)
- [Enfuse — PanoTools wiki](https://hugin.sourceforge.io/docs/manual/Enfuse.html) · [Batch merge handheld images — PanoTools wiki](https://wiki.panotools.org/Batch_merge_handheld_images)
- [Lightroom Classic 15 (2026) new features — PhotoshopCAFE](https://photoshopcafe.com/lightroom-classic-2026-new-features-lightroom-15/) · [Lightroom Classic 15 news — Alexander S. Kunz](https://www.alex-kunz.com/lightroom-classic-15/) · [What's New in Lightroom 15.4 — The Lightroom Queen](https://www.lightroomqueen.com/whats-new-in-lightroom-2026-06/)
- [Limitations of syncing Classic with the cloud — The Lightroom Queen](https://www.lightroomqueen.com/limitations-syncing-classic-with-cloud/) · [Lightroom Classic sync FAQ — Adobe](https://helpx.adobe.com/lightroom-classic/kb/sync-faq.html)
- [Lightroom now supports HDR — Greg Benz](https://gregbenzphotography.com/hdr-photos/lightroom-adds-hdr-edit-and-export/) · [Export HDR photos in Lightroom on mobile — Adobe](https://helpx.adobe.com/lightroom/mobile/share-save-and-export/export-hdr-photos.html) · [HDR photo merge in Lightroom Classic — Adobe](https://helpx.adobe.com/lightroom-classic/help/hdr-photo-merge.html)
- [Photomatix HDR Merge Batch Plugin for Lightroom](https://www.hdrsoft.com/download/hdr-batch-lightroom-plugin.html)
- [Adobe feature request: Better auto stacking for bracketing, HDR, focus stacking and panoramas](https://community.adobe.com/t5/lightroom-classic-ideas/p-better-auto-stacking-for-bracketing-hdr-focus-stacking-and-panoramas/idi-p/12250005)
- [Sony tag names — ExifTool](https://exiftool.org/TagNames/Sony.html)
