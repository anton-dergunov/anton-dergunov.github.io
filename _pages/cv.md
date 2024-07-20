---
layout: archive
title: "CV"
permalink: /cv/
author_profile: true
redirect_from:
  - /resume
---

{% include base_path %}

{% include cv_download.html %}


Highlights and Skills
======

- Experience and high interest in applying Machine Learning. Python, Jupyter Notebooks, NumPy, Pandas, SciKit-Learn, PyTorch, Matplotlib, Vowpal Wabbit. Linear models, SVM, Decision Trees, Ensemble Learning, Gradient Boosting, Neural Networks, Deep Learning, CNN, RNN, LSTM, BERT, Autoencoders, Knowledge Representation, Natural Language Processing.

- Experience in all cycles of large software development (design, prototype, research, review, documentation, planning, implementation, etc.): C, C++, Java, Python, Bash, SQL, MongoDB. Linux, Windows, cross-platform. Focus on software quality ranging from software design, TDD to formal software verification.

- Expertise in parallel, concurrent and distributed software research and development. Performance analysis of serial and parallel software; algorithmic, threading and machine-dependent performance optimization. Intel VTune Analyzer, Intel Trace Analyzer and Collector, Intel Advisor, MPI, OpenMP, MapReduce.


Employment
======

- Current, From May 2018: Senior Applied Scientist, [Microsoft](https://www.microsoft.com/)
  - *Applying machine learning in Microsoft Office products.*
  - Contributed to improving relevance of recommendations of the new Meeting Insights feature in Microsoft Outlook (see [press release](https://www.microsoft.com/en-us/research/blog/the-story-of-an-office-ai-feature-how-ai-can-promote-efficient-meeting-preparation/) or [documentation](https://support.microsoft.com/en-gb/office/use-intelligent-technology-in-outlook-on-the-web-and-outlook-com-24b30683-8340-4b69-b8ac-4193ec528a70)). This feature recommends emails and documents which are relevant for a given meeting (`Python`, `SciKit-Learn`, `NumPy`, `Pandas`, `PyTorch`, `PySpark`, `LightGBM`, `Gradient Boosting`, `C#`).
  - Implemented and validated new features for this machine learning model, by exposing new signals or choosing their best form (such as social, content similarity, etc). Used `BERT` and related neural network architectures to improve relevance (`PyTorch`). Supervised students for their research project of applying `BERT`.
  - Explored various data sets, heuristically labelled data and their combinations for model training ([Snorkel](https://snorkel.ai/)). Conducted A/B experiments.
  - Improved data extraction pipeline, which allowed to get ~50x more training data for machine learning algorithm and consequently improved model performance (AUC increased 3%, AUPRC increased 12%). Subsequent data analysis allowed to fix bias in extracted data, further improve model performance (AUC increased 3%, AUPRC increased 4%, NDCG increased 11%) and enable 2x more features.
  - Implemented explanation facility tool for machine learning models. It was demonstrated that helps to detect root causes during error analysis and identify required treatment much quicker.
  - Prototyped complete pipeline for data extraction, feature extraction, training and validation of document-to-document recommendation system. Help and guidance for a colleague to implement email-to-email recommendation prototype.

- May 2017 - May 2018: Lead Application Developer, [JP Morgan](https://www.jpmorganchase.com/)
  - *Web services implementation.*
  - Implementation of backends of monitoring systems for tracking engineering practices of all bank applications and source code repository commits. (`Java`, `Spring`, `Python`, `SQL`, `MongoDB`, `MariaDB`, `Oracle Database`) Phone screening interviews.

- January 2016 - May 2017: Software Engineer, [Yandex](https://yandex.com/company/)
  - *Feature engineering for Internet video search and machine learning.*
  - Implemented calculation of several new characteristics of Internet videos and evaluated their usefulness as factors in
    [MatrixNet](https://yandex.com/company/technologies/matrixnet/) machine learning algorithm, used in [Yandex Video Search](https://yandex.com/video/) to query and rank videos on a search result page. Several of these factors contributed to improvement of video ranking quality as demonstrated by several metrics. (`C++`, `Python`, `MapReduce`, `Machine Learning`)
  - Implemented machine learning pipeline and made several experiments of large-scale web text classification for several tasks using logistic regression, LSTM, word2vec and other algorithms. (`Natural Language Processing`, `Vowpal Wabbit`, `Deep Learning`)
  - Using this infrastructure for classification of YouTube videos allowed to improve video ranking quality and click-through rate prediction.
  - Collaborated across teams and made research to improve integration of Video Search results on the main [Yandex Web Search](https://yandex.com/) page.

- February 2006 - December 2015: Senior Software Development Engineer, [Intel](http://intel.com)
  - *Applied research in performance analysis and implementation of performance tuning tools.*
  - Gained expertise in performance analysis of serial and parallel software; algorithmic, threading and machine-dependent performance optimization; CPU and hardware architecture; parallel, concurrent and distributed software research and development (`MPI`, `OpenMP`).
  - Implemented capability to represent knowledge about performance issues in applications (using `Python` code) and their automatic detection for [Intel VTune Amplifier](http://software.intel.com/en-us/intel-vtune-amplifier-xe) and [Intel Advisor](https://software.intel.com/en-us/intel-advisor-xe) products. (`Knowledge Representation`)
  - Defined metrics and methodology to identify parts of an application that are best suited for execution on main CPU or for offload to [Intel Xeon Phi](https://www.intel.com/content/www/us/en/products/processors/xeon-phi/xeon-phi-processors.html) processor, and implemented a tool automate detection of such parts.
  - Implemented [Performance Assistant](https://web.archive.org/web/20151022144828/https://software.intel.com/en-us/node/561522) capability in [Intel Trace Analyzer and Collector](http://software.intel.com/en-us/intel-trace-analyzer) for automatic detection of known performance issues in MPI applications, based on results of my [PhD thesis](https://search.rsl.ru/ru/record/01005013870). (`C++`, `MPI`, `Knowledge Representation`)
  - Full cycle development (design, prototype, research, review, documentation, planning, implementation, etc.) of new threading and performance profilers [Intel VTune Amplifier](http://software.intel.com/en-us/intel-vtune-amplifier-xe) and [Intel Performance Tuning Utility](http://software.intel.com/en-us/articles/intel-performance-tuning-utility) from scratch. Responsibility for several major data visualization and data provider components in these products. (`C++`, `Java`, `Python`, `OpenMP`, `SQLite`) Mentorship (5 collegues).
  - Implemented new approach for source-level performance information visualization based on synchronized views in [Intel VTune Amplifier](http://software.intel.com/en-us/intel-vtune-amplifier-xe) and [Intel Performance Tuning Utility](http://software.intel.com/en-us/articles/intel-performance-tuning-utility), which unlocked new usage models for senior performance engineers.
  - Made refactoring of several central components (with MVVM pattern) by gradually introducing "true" unit tests with TDD approach. Code duplication was reduced, bug backlog was reduced by multiple times and stopped growing, but new features were still implemented during this work.

- 2009 - 2012: Lecturer, Research Advisor, [Lobachevsky State University of Nizhni Novgorod](http://unn.ru/eng)
  - *Research and teaching Artificial Intelligence and Machine Learning.*
  - Research advisor for 3 bachelor and 5 master students (topics in artificial intelligence, machine learning, natural language processing, software verification, parallel programming, software engineering).
  - Created content and taught courses "Artificial Intelligence" (2010, 2011), "Databases and Expert Systems" (2009-2012).
  - Assistant for [Distributed and Outsourced Software Engineering project](http://se.inf.ethz.ch/courses/2012b_fall/dose/ (2011, 2012): provided support for projects of students.

- October 2003 - February 2006: Software Development Engineer, [Mera Networks](https://www.mera.com/)
  - *Telecommunication software implementation.*
  - Development of cellular base stations emulation software. (`C++`, `Java`, `Bash`, networking) Mentorship (3 collegues).
  - Participated in major redesign of the data model part of this software that resulted in significant improvements of execution speed and memory consumption (allowing to handle previously unsupported amount of data).


Personal Projects
======

- Small repository of various Jupyter notebooks:
  [https://github.com/anton-dergunov/ml-playground](https://github.com/anton-dergunov/ml-playground)


Education
======

- PhD in Theoretical Computer Science, [Lobachevsky State University of Nizhni Novgorod](http://unn.ru), July 2008 - July 2011
  - Thesis: [Models, methods and tools of knowledge representation for improving performance of MPI applications](https://search.rsl.ru/ru/record/01005013870).
  - Implemented some results of this work in [Intel Trace Analyzer and Collector](http://software.intel.com/en-us/intel-trace-analyzer), in its [Performance Assistant](https://web.archive.org/web/20151022144828/https://software.intel.com/en-us/node/561522) capability.

- Specialist Degree in Applied Computer Science, [Lobachevsky State University of Nizhni Novgorod](http://unn.ru), September 2001 - May 2006
  - Thesis: Neural network model for knowledge representation and extraction.


Publications
======

- Anton Dergunov. [Proving Termination and Computational Complexity of Computer Programs](http://anton-dergunov.ru/publications/proving_complexity_v2.pdf) Abstract of poster for "CSEDays. Algorithms and Complexity"  summer school.
- Anton Dergunov. [Generalized algebraic data types in Haskell](http://themonadreader.files.wordpress.com/2013/08/issue221.pdf) The Monad.Reader Issue 22, pp. 5-39. Etc.
- Anton Dergunov. [Specification and automatic detection of performance problems in message passing (MPI) applications](http://anton-dergunov.ru/publications/mpi_performance.pdf) Radioelectronic and Computer Systems, 2012, 7(59), pp. 217-222.
- Anton Dergunov. [Expert methodology for performance analysis of communicating processes in MPI applications](http://pavt.susu.ru/2012/full/159.pdf). In proceedings of conference "Parallel Computational Technologies", Chelyabinsk (Russia), 2012., pp. 134-144 (in Russian).
- Personal blog on machine learning: [https://anton-dergunov.github.io/blog/](https://anton-dergunov.github.io/blog/)

