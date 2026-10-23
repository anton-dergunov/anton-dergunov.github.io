---
title:     "What happens when you give an LLM a paper? PDFs, markdown and a coding agent"
date:      2199-01-01
permalink: /posts/2199/01/papers-as-markdown-for-agents/
tags:
  - machine-learning
  - llm
  - agents
  - information-retrieval
published: false
---

**Status: draft.** This is the background half of the post: what the assistants do with a PDF, what the published evidence says, and what I expect. The experiment that tests these expectations is planned but not run; its numbers will replace the "expected" lines below. Where an expectation turns out wrong, I will leave it in.

I keep about 2,200 machine-learning papers as markdown, next to their PDFs, and read them with Claude Code beside me. The agent answers from the markdown, cites the page, and opens the PDF when the markdown is not enough. Getting the markdown right took most of the work: arXiv's HTML where a paper has it, layout analysis and an equation model where it does not, and a log of every conversion problem found while reading, fixed at its cause in the converter. The engine is public: [agentic-paper-library](https://github.com/anton-dergunov/agentic-paper-library).

Before telling anyone this is worth doing, I wanted to know two things. What do Claude, ChatGPT and Gemini already do when you attach a PDF? And does careful markdown change the answers, or only the bill?

## What the assistants do with a PDF

None of them converts a single attached paper to markdown. They put the whole paper in the model's context, as the PDF's raw text layer and as an image of every page:

- **Claude** (API and claude.ai): every page goes in as extracted text plus a rendered image ([docs](https://platform.claude.com/docs/en/build-with-claude/pdf-support)). claude.ai looks at the images for PDFs up to 100 pages; from 101 to 1,000 pages it reads the text only ([help](https://support.claude.com/en/articles/8241126)). A Project switches to retrieval when its files approach the context window ([help](https://support.claude.com/en/articles/11473015-retrieval-augmented-generation-rag-for-projects)).
- **ChatGPT**: a file under about 110K tokens goes into the context whole; above that, its text and images go into a private search index, searched once per prompt with keyword and semantic search ([help](https://help.openai.com/en/articles/10029836)). The API sends text and page images to vision models ([docs](https://developers.openai.com/api/docs/guides/pdf-files)).
- **Gemini** reads PDF pages as images, 258 tokens a page ([docs](https://ai.google.dev/gemini-api/docs/document-processing)).
- **Claude Code's `Read` tool** reads a PDF 20 pages at a time, text plus page image, and keeps nothing between sessions. An open feature request asks for a text-only mode because of what the images cost ([issue](https://claudeissues.com/issue/80449-read-tool-pdfs-cost-way-more-tokens-than-they-need-to-because-of-the-image-rende)).

So "it reads only the relevant parts" is true only of collections. For one paper the model sees everything, and the page image covers for what the text layer mangles: a flattened equation, a table run into the paragraph beside it, a plot. Retrieval starts when the files outgrow the context, and it retrieves fixed-size chunks, so a chunk cut out of a table or a derivation loses its caption and its context.

## What a page costs

I expected markdown to be an order of magnitude cheaper than page images. It is not. Claude charges an image by its 28×28-pixel patches, not by its bytes: `⌈width/28⌉ × ⌈height/28⌉` tokens, capped at 1,568 tokens on older models and 4,784 on Claude 4.7 and later ([docs](https://platform.claude.com/docs/en/build-with-claude/vision)). A 100 KB page image and a page of text land in the same range, a thousand to a few thousand tokens.

I measured it on the DPO paper (27 pages), sent to Claude Opus 5.5 in each form:

| The DPO paper as | Input tokens | Per page |
|---|---|---|
| a PDF attachment (text layer + page images) | 79,300 | 2,900 |
| its raw text layer only | 37,400 | 1,390 |
| my library's markdown | 44,800 | 1,660 |
| Claude Code reading 10 of its pages with `Read` | ~19,000 | ~1,900 |

The markdown costs about 55% of the PDF. That is less than I expected, and it is more than the raw text, because the markdown carries what the text layer drops: equations as LaTeX, tables as tables, links from each citation to its reference. Subtracting the text from the PDF leaves about 1,550 tokens a page for the image, which is the old 1,568-token cap. So the page images look like they are sent at roughly 115 dots per inch, even to a model that accepts images three times larger (my inference from the counts; the experiment checks it). At that resolution body text is legible and the small print of a dense table or a plot's tick labels is borderline. That is presumably why the text layer goes along with the image.

Raw arXiv HTML, the other obvious thing to hand a model, is larger still: DPO's page is 411,000 characters, about four times the markdown, most of it MathML.

## What the evidence says about accuracy

- **[DocBench](https://arxiv.org/abs/2407.10701)** (2024) tested real products on 229 uploaded documents. On academic papers the best product, Claude-3 Opus, reached 73.9% against 83.0% for people, and a crude pipeline that extracted the text with PyMuPDF and handed it to GPT-4 reached 70.0%. The failures were finding the right table or figure, reading values off it, and long documents. These were 2024 models; the gaps today are smaller.
- **[OCR Hinders RAG](https://arxiv.org/html/2412.02592v4)** (ICCV 2025) measured how parsing errors carry through to question answering. The best parser scored 31.1 against 36.1 for perfect text, about 14% worse, and the loss sat in tables, formulas and charts (charts fell from 32.9 to about 10 for the pipeline parsers). Wrong *content* hurt badly: at the heaviest noise, retrieval and answers fell by about half. Wrong *formatting* cost large models about 7%, and only on table and formula questions. Feeding page images directly competed on tables and charts and lost on plain text.
- **Long contexts degrade.** Accuracy falls as the context grows and depends on where the evidence sits: [Lost in the Middle](https://arxiv.org/abs/2307.03172), [RULER](https://arxiv.org/abs/2404.06654), [NoLiMa](https://arxiv.org/abs/2502.05167), and Chroma's [context-rot report](https://trychroma.com/research/context-rot), which adds that similar-but-wrong passages hurt more than unrelated ones. Pasting thirty papers into one prompt is not free even when it fits.
- **My own earlier measurements agree that models shrug off formatting.** Stripped LaTeX source answered 47.5 of 48 questions against 48 for the markdown. Dropping a table's shading cost 4 of 15 questions that depended on it, and three of those four answers were elsewhere in the paper. Per-paper notes and area reviews made answers cheaper, not more accurate: sessions that read only the papers did as well.

## Is markdown for agents new?

No. arXiv MCP servers download papers and convert them to markdown ([one of several](https://glama.ai/mcp/servers/blazickjp/arxiv-mcp-server)); zotero-fulltext-mcp does it for a Zotero library ([listing](https://mcpservers.org/servers/54yyyu/zotero-mcp)); ScholarAIO converts with MinerU, keeps LaTeX and figures, indexes with keyword and vector search and stores an agent's notes per paper ([page](https://www.sourcepulse.org/projects/27131024)); Ai2's Asta has a Claude Code skill that converts PDFs to markdown and cuts them into 2,000-character chunks for vector search ([skill](https://www.skills.sh/allenai/asta-plugins/local-paper-index)); alphaXiv serves a paper's full text as markdown; and Karpathy's "LLM Wiki" made a markdown knowledge base kept by an LLM, searched without RAG, a popular pattern ([coverage](https://venturebeat.com/data/karpathy-shares-llm-knowledge-base-architecture-that-bypasses-rag-with-an)).

What I did not find in any of them is a measured conversion. None of them records the problems found while reading, files them by cause, fixes the converter with a test and converts the affected papers again, and none of them says how often its output is wrong. The other choices that matter are arXiv's HTML as the source (it carries the authors' own LaTeX; arXiv says about 75% of papers convert without errors, [2026 report](https://arxiv.org/pdf/2605.16562)), a PDF page number on every heading so that an answer can cite "p. 7, Table 2", and an agent that searches whole papers with grep instead of retrieving chunks, the choice Claude Code's authors made for code ([interview](https://newsletter.pragmaticengineer.com/p/building-claude-code-with-boris-cherny)), on evidence they themselves called mostly vibes. I could not check how Elicit, SciSpace or alphaXiv parse papers; they do not publish it.

## Which conversion errors matter

Not all of them. The evidence above and my own runs say that a model reads past ugly formatting. What it cannot read past is a wrong value. An agent reading only markdown never sees the page, so it trusts what it reads: a table cell printed as 53.4 where the PDF says 3.4 (an invisible padding digit, which my converter once printed in 256 cells of five papers), a column shifted by one, a dropped objective function, a missing page. A model reading the PDF has the page image to fall back on. So markdown has to be *more* reliable than the PDF's text layer, or it is worse than attaching the PDF. That is the case for chasing conversion bugs, and it is narrower than "better formatting": correct and complete, not pretty.

A slow conversion is affordable only ahead of time. Layout analysis plus an equation model took 0.5 to 2.5 minutes a paper and 6.9 hours for my 283 papers without HTML; no chat product will do that while you wait for an answer.

## What I expect the experiment to show

The experiment asks Claude Opus 5.5 the same questions about the same papers in each form: the PDF attached, the PDF's text layer, the raw arXiv HTML, the library's markdown, and Claude Code working in the library or in a folder of PDFs. My expectations, to be checked:

- **Prose questions:** about the same in every form.
- **Table and equation values:** markdown at or above the PDF; the text layer clearly below both.
- **Values that exist only in a plot:** the PDF ahead; the markdown has the figure only as a file the agent may or may not open.
- **Cost:** the markdown at about half the PDF's tokens; raw HTML the most expensive of all.
- **Questions across several papers:** the library well ahead of a folder of PDFs, and ahead of attaching the papers to one prompt.
- **Conversion fixes:** an old conversion with a wrong table value gives a confident wrong answer, where the PDF gives the right one; the fixed markdown gives the right one at half the cost.

*Results: to come.*
