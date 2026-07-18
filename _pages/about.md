---
permalink: /
title: "About"
author_profile: true
redirect_from:
  - /about/
  - /about.html
---

<img align="right" src="images/profile.jpg" alt="Photo" style="width: 210px; border-radius: 10px; padding: 8px 8px 8px 8px"/>

I'm Anton Dergunov, a machine learning engineer and applied scientist based in London.

My work sits where machine learning meets real user behaviour: I build production systems that learn from how millions of people search, click, and choose — and that have to prove, in live experiments, that they actually got better. Most of that work has been in search ranking, recommendations, and NLP at large scale, from classical learning-to-rank through transformer-based models and LLM-powered pipelines.

## What I've built

At Microsoft, I spent over seven years as a Senior Applied Scientist working on ranking and recommendation systems across Microsoft 365. I led improvements to natural-language people search for [Microsoft 365 Copilot](https://www.microsoft.com/en-us/microsoft-365/copilot) — helping users find the right colleagues, contacts, and experts — evaluating embedding models and cross-encoders, and using LLM-based assessment and synthetic data generation to measure quality. I also built, end to end, the training and evaluation pipeline behind the contact-ranking models used across Teams, Outlook, Bing, and Windows: a system that learns from very large volumes of behavioural log data under strict privacy constraints ("eyes-off" processing), with models deployed to production and validated through online A/B experiments showing gains in click-through rate and time-to-success.

On the recommendation side, I worked on [Meeting Insights](https://www.microsoft.com/en-us/research/publication/calendar-aware-proactive-email-recommendation/) in Outlook — a feature that surfaces emails and documents relevant to upcoming meetings. This was greenfield work on a brand-new product, with the cold-start problem that entails: I designed and owned the training-data pipeline from the ground up, scaling it through engineering and weak-supervision techniques. I started working with transformer models soon after they appeared (such as BERT), applying them to content similarity and distilling them into lightweight models ready for production.

Before Microsoft, I worked on video search at [Yandex](https://yandex.com/company/), improving ranking quality through feature engineering for its gradient-boosted ranking system and building text-classification pipelines over web-scale data. Earlier, I spent a decade at [Intel](https://www.intel.com/) on performance-analysis tools for parallel software — including major components of the VTune profiler — which is where I learned to care deeply about how software actually behaves at scale.

A few threads run through all of this. I like owning systems end to end: data, features, models, evaluation, deployment, and the experiments that tell you the truth about whether anything improved. And I'm deeply interested in evaluation itself — designing the right metrics, building offline and online experiments you can trust, and understanding what models are actually doing (I've built internal tools for explaining their predictions).

## Recent projects

My recent personal projects centre on modern neural systems: neural retrieval and ranking models, multimodal architectures, and post-training pipelines for LLMs (supervised fine-tuning, reward modelling, reinforcement learning). I've also been building LLM-powered tools for language learning, including a speech-analysis tool for pronunciation practice — a nice evaluation-design problem, since even native speakers don't match a single "ideal" pronunciation, so I chose rich visual feedback over a brittle automated score. Code and write-ups appear here on the [blog](blog) and on [GitHub](https://github.com/anton-dergunov).

## Background

I hold a PhD in Computer Science, where my research on automated performance diagnosis for parallel programs became a shipped capability in Intel's developer tools. Earlier in my career I taught university courses in artificial intelligence and machine learning and supervised student research projects.

## This blog

Technical articles, implementation notes, experiments, and project write-ups on machine learning systems, retrieval, NLP, and applied AI engineering — written for practitioners who like to see how things actually work.

## Beyond work

I'm a language learner (the origin of several of my side projects) and a keen hiker — the solo [Tour du Mont Blanc](https://www.autourdumontblanc.com/en/) remains a highlight. I love travelling and immersing myself in nature, I enjoy photography, and I stay active with gym, yoga, and cycling.

If you'd like to talk about retrieval, ranking, LLM evaluation, or anything you've read here, reach out on [LinkedIn](https://www.linkedin.com/in/anton-dergunov/) — I'm always happy to connect.
