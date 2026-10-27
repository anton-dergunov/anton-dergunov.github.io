---
title:     "Does an agent need your papers converted? PDF, text layer and markdown, measured"
date:      2199-01-01
permalink: /posts/2199/01/reading-formats-measured/
tags:
  - machine-learning
  - llm
  - agents
---

<!--
RAW NOTES, collected 25 Oct 2026 so that nothing is lost; not yet a post.
Companion to the earlier draft "papers-as-markdown-for-agents" (the background research before measuring).
Source of truth for the numbers: agentic-paper-library/experiments/reading-formats/PROGRESS.md and results/summary.md;
the plan: agentic-paper-library/docs/plans/reading-formats.md.
-->

## The question

I keep a library of about 2,275 research papers that I read with Claude Code. Every paper is converted to markdown (arXiv's HTML through pandoc, or the PDF through docling), with page markers, notes, overviews and reviews written from it. The conversion is the expensive part to maintain: about 20 conversion tickets fixed and 30 open, a reconversion every time a converter changes, and errors of its own that nothing flags. Does an agent actually answer better from the markdown than from the PDF, or from the PDF's plain text layer (`pdftotext -layout`)?

## How it was measured

- Claude Opus through `claude -p` on a Pro subscription; no API key. Requests without the user's settings and background traffic.
- Forms of one paper, whole paper in one request: closed book (c0), the PDF (what an attachment sends: each page's text plus a page image), the text layer, arXiv's HTML, the library's markdown.
- Agents: Claude Code with Read, Grep, Glob, Bash in read-only copies of the library (x-lib: markdown, notes, reviews, indexes), of the PDFs (x-pdf), of the text layers with a `[page N]` line per page (x-txt), and the named papers' PDFs attached to one request (x-att).
- Questions written in advance with gold answers checked against the PDF pages: tables, equations, appendix details, figure-only values, unanswerable traps; later, questions mined from the library's own reviews, and aggregations over the whole library.
- Papers published after the model's training cutoff (June 2026) as well as famous ones, because the famous ones are answered from memory.
- A blind judge grading all answers to a question in one request, shuffled; every disagreement between conditions asked twice more; only differences holding in two of three runs count. Hand check of every disagreement and ten agreements.
- Total so far: about $80 of API-equivalent requests, roughly two and a half five-hour windows.

## What it found so far

- **Single paper, 51 questions over 9 papers (5 famous, 4 unseen): the PDF is right on all; the text layer and the markdown on all but the figure-only ones,** which they decline (3 of 3 runs, never guessing). On the four unseen papers: PDF 24/24, text 20, markdown 20, closed book 2.
- **DPO and InstructGPT are answered from memory** (closed book right on nearly everything); unseen papers were needed to see what a form loses.
- **Tables, equations, appendix details: text layer = markdown.** 17 equation questions over 7 papers, including one built so that no prior could complete it (a bound spread over three lines of the text layer with its fraction bar lost): the text layer answered it with every coefficient. The markdown's LaTeX bought no accuracy.
- **Converter errors reach the answer.** An old conversion with a padding digit (3.4 printed 53.4) gave a confident wrong answer 3 of 3; a missing table or equation gave a decline. The plain text layer had none of these errors. An impossible value (a 199.3% share) was caught and repaired by the model.
- **Numbers printed inside vector figures** (bar labels, heatmap cells, p-values) are in the text layer and lost in the markdown: the only questions where the text layer beat the markdown.
- **Small print in dense tables is read from a 1,255 px page image** (about 115 dpi); the cheapest form that answers a question about a known page is that image (about 2,250 tokens against 3,900–5,100 for a one-page PDF). Image token counts were not stable (the same 2,576 px image counted as 4,530 or 10,110 tokens).
- **Tokens:** markdown is 40–73% of the PDF's tokens and 0.94–1.36× the text layer (LaTeX and HTML tables make it dearer); raw HTML is 2.5× the PDF; a PDF page is 2,600–4,000 tokens, about 1,550 of them the image.
- **Across papers (13 questions, Claude Code as the agent): library, PDFs and text layers answer alike.** Every question naming its papers right in all four conditions. Aggregations over the whole library ("which papers report AlpacaEval win rates?", "which evaluate on LoCoMo?"): all three agent conditions found every paper on my gold lists and eight more that my own search had missed. The only differences came from questions whose gold I had taken from the library's own reviews (the review grouped a paper under "remedies for lost-in-the-middle" that never mentions it; the agent in the library read the review and agreed with it).
- **Cost and time per cross-paper question:** text layers $0.30, PDFs $0.36, library $0.42, attaching the PDFs $1.72; median time the same (about 45 s), aggregations fastest over text layers (78–122 s against 142–266 s in the library). The library is not cheaper for an agent: its guide adds 5K tokens to every session, and it reads notes and whole files where grep over text finds the line.
- **The agent with PDFs never looked at a page.** In all 13 sessions it ran `pdftotext` itself (once on all 2,275 PDFs) and read the text: an agent handed PDFs builds the text layer it needs.
- **The text layer rarely fails in an arXiv-heavy library:** a scan of all 2,275 PDFs found none without a text layer; about 2 broken (a PostScript conversion, an OCR layer) and about 60 imperfect (under 3%). 58% of the PDFs have at least one raster figure, whose numbers no text form carries.
- **Page citations:** the markdown gives a page per heading, so a table floating past its section's first page is cited a page early (the library's reviews did this for three papers); a scan of 137 papers found 1,224 of 1,861 captions on a later page than their heading's marker. The text layer's `[page N]` per page is exact.
- **Side lesson on evaluation:** gold lists built by a search are incomplete (the agents beat them), and golds taken from the library's own reviews favour the condition that reads the reviews.

## What comes next (planned)

- **Figures with the PDF at hand:** an agent in a copy with text layers and PDFs, with and without one line saying "a value drawn in a figure is not in the text: read that page" — does Claude Code open the page by itself when the text lacks the value?
- **Where the text layer is weak:** questions on the broken and flawed text layers, as text layer alone (worst case), markdown, and text layer plus PDF (the realistic case).
- **Writing notes:** notes from the text layer against the existing notes from markdown, judged blind against the PDF, on four papers after the training cutoff.
- If all three hold: the text layer with page markers becomes the agent's copy, markdown only where the text layer is broken; a cheap canary rerun on every Claude Code release, since "read the text, open the page when needed" is Claude Code's behaviour, not the library's.
- Precise citations: the text layer knows each word's position, so a citation can carry a rectangle and the PDF viewer can highlight it.

## How the assistants handle a PDF (from the earlier draft's research)

- Claude API / claude.ai: each page as extracted text plus a rendered image ([docs](https://platform.claude.com/docs/en/build-with-claude/pdf-support)); claude.ai reads images only up to 100 pages ([help](https://support.claude.com/en/articles/8241126)); Projects switch to retrieval as files approach the context window ([help](https://support.claude.com/en/articles/11473015-retrieval-augmented-generation-rag-for-projects); a user reports it earlier: [issue](https://github.com/anthropics/claude-code/issues/25759)).
- ChatGPT: under about 110K tokens the file goes into the context whole ([help](https://help.openai.com/en/articles/10029836)); the API sends text plus page images ([docs](https://developers.openai.com/api/docs/guides/pdf-files)).
- Gemini: pages as images, 258 tokens a page ([docs](https://ai.google.dev/gemini-api/docs/document-processing)).
- Claude Code's `Read` on a PDF: text plus page image, 20 pages a call; an open request asks for a text-only mode because of the cost ([issue](https://claudeissues.com/issue/80449-read-tool-pdfs-cost-way-more-tokens-than-they-need-to-because-of-the-image-rende)).

## Prior work found (search of 25 Oct 2026; no head-to-head study of PDF vs text layer vs markdown for QA on papers turned up)

- Closest controlled study: OCR text vs markdown about equal for extraction from layout-rich documents (0.650 vs 0.648), model-dependent: [Problem Solved? Information Extraction Design Space for Layout-Rich Documents using LLMs](https://arxiv.org/pdf/2502.18179).
- OCR and parsing errors cost at least 14% of end-to-end RAG quality; semantic noise worst, formatting noise mainly for multimodal questions; VLMs without OCR as a route: OHRBench, [ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/html/Zhang_OCR_Hinders_RAG_Evaluating_the_Cascading_Impact_of_OCR_on_ICCV_2025_paper.html), [arXiv](https://arxiv.org/abs/2412.02592v4), [v1 HTML](https://arxiv.org/html/2412.02592v1), [leaderboard](https://www.alphaxiv.org/benchmarks/shanghai-ai-laboratory/ohrbench).
- Questions on figures and tables of CS papers: [SPIQA (NeurIPS 2024)](https://arxiv.org/pdf/2407.09413), [Google Research page](https://research.google/pubs/spiqa-a-dataset-for-multimodal-question-answering-on-scientific-papers/).
- Long-PDF understanding leaderboards: MMLongBench-Doc on [benchlist](https://benchmarklist.com/benchmarks/mmlongbench_doc/) (Claude 4.5 Opus 61.9%, unverified), [official results (OpenIXCLab)](https://huggingface.co/datasets/OpenIXCLab/mmlongbench-doc-results/blame/main/README.md), [LLM Stats](https://llm-stats.com/benchmarks/mmlongbench-doc), [BenchLM](https://benchlm.ai/benchmarks/mmlongbenchdoc); a multi-agent framework on it: [DocLens](https://arxiv.org/pdf/2511.11552). Claude model cards used to report DocVQA and ChartQA (from memory, to check).
- Converter choice matters more than format, in an enterprise extraction study: [Hybrid OCR-LLM Framework](https://arxiv.org/pdf/2510.10138). Markdown best of PDF, LaTeX, JSON, markdown for one extraction task: [Quantum Cascade Lasers via LLMs](https://arxiv.org/pdf/2605.09927). Also turned up: [Healthy LLMs?](https://arxiv.org/pdf/2505.06046), [ExtractBench](https://arxiv.org/pdf/2607.29677).
- Vendor and blog posts, small or self-interested samples: [HURIDOCS](https://huridocs.org/2026/06/markdown-conversion-tool/), [Extend](https://www.extend.ai/resources/pdf-to-markdown-llm-pipelines), [MDisBetter](https://mdisbetter.com/blog/pdf-to-text-vs-pdf-to-markdown-which-is-better), [scrape.do](https://scrape.do/blog/llm-ready-data/) (PDF 6/10 vs markdown 10/10), [web2md](https://web2md.org/blog/markdown-vs-html-for-llm).
- PDF pipeline descriptions: [Anthropic PDF support (older docs)](https://docs.anthropic.com/en/docs/build-with-claude/pdf-support), [claudemaster write-up](https://claudemaster.net/features/api-pdf-support), [Simon Willison on the PDF beta](https://simonwillison.net/b/8270).

## Possible angles for the post

- "Conversion buys cost, not accuracy" turned out wrong too: it buys neither for an agent; what it adds is silent errors.
- What a PDF is to Claude: the text layer plus a picture of the page. The picture is the only thing the text forms lack.
- Memory hides what a format loses: test on papers the model cannot know.
- Your gold answers are worse than the agent: search-built lists and review-derived golds.
