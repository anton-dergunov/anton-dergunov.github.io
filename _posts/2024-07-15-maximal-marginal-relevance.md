---
title:     "Maximal Marginal Relevance"
date:      2024-07-15
permalink: /posts/2024/07/maximal-marginal-relevance
tags:
  - machine learning
  - information retrieval
---

**Maximal Marginal Relevance (MMR)** is a technique designed to retrieve documents that are both *relevant* and *diverse*. This article provides an implementation of MMR and demonstrates its effectiveness using a dataset of news articles.

Imagine you want to find the most relevant news articles about `London` from a dataset. Here’s an example dataset containing news article titles:

```python
article_titles = [
    # Culture
    "The Revival of Ancient Traditions in Modern Society",
    "The Evolution of Theatre in London",
    ...

    # Weather
    "Understanding the Science Behind Extreme Weather Events",
    "How London's Weather Has Changed Over the Decades",
    ...

    # Things to Do in London
    "Historic Landmarks You Can't Miss in London",
    "Family-Friendly Activities in London",
    ...
]
```

You can find the complete dataset and source code for this article in the [Jupyter Notebook](https://github.com/anton-dergunov/ml-playground/blob/master/techniques/maximal_marginal_relevance.ipynb).

To approach this problem, one method is to use a [similarity measure](https://en.wikipedia.org/wiki/Similarity_measure) to rank documents by their relevance to a query. A common measure is [cosine similarity](https://en.wikipedia.org/wiki/Cosine_similarity) applied to [word embeddings](https://en.wikipedia.org/wiki/Word_embedding) of the documents and the query. The algorithm follows these steps:

1. Create word embedding representation of the documents and the query.
2. Compute cosine similarity between the representations of the query and each document.
3. Select `N` documents most similar to the query.

We can use the [transformers](https://huggingface.co/docs/transformers/en/index) library to leverage a pretrained language model (such as the classic `bert-base-uncased`) to generate text embeddings:

```python
from transformers import AutoTokenizer, AutoModel

def get_embeddings(text_list, model_name="bert-base-uncased"):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)

    inputs = tokenizer(text_list, return_tensors="pt", padding=True, truncation=True)
    
    with torch.no_grad():
        outputs = model(**inputs)
    
    embeddings = outputs.last_hidden_state.mean(dim=1)
    embeddings = embeddings.numpy()
    
    return embeddings
```

This function generates embeddings by averaging the hidden states of the model’s last layer for each input text.

Cosine similarity is computed as follows:

```python
def cosine_similarity(vector1, vector2):
    dot_product = np.dot(vector1, vector2)
    norm_vector1 = np.linalg.norm(vector1)
    norm_vector2 = np.linalg.norm(vector2)
    return dot_product / (norm_vector1 * norm_vector2)
```

To compute cosine similarities between the query and each document, we can combine the query and documents into a single list and then compute similarities between each pair of embeddings (that would also get us similarities between each document, but we would need that later in the article)):

```python
def compute_similarities(documents, query):
    quiery_and_documents = [query] + documents
    embeddings = get_embeddings(quiery_and_documents)
    num_embeddings = embeddings.shape[0]
    similarities = np.zeros((num_embeddings, num_embeddings))

    for i in range(num_embeddings):
        for j in range(num_embeddings):
            similarities[i, j] = cosine_similarity(embeddings[i], embeddings[j])

    return similarities

article_similarities = compute_similarities(article_titles, query="London")
```

Next, rank the documents based on their similarity to the query:

```python
def similarity_relevance(similarities):
    return sorted(range(len(similarities) - 1),
                  key=lambda i: similarities[0, i+1],
                  reverse=True)
```

Here are the top 7 relevant news articles:

```python
article_similarity_order = similarity_relevance(article_similarities)
print_selected(article_similarity_order[:7], article_similarities, article_titles)
```

| Cosine Similarity  | Top 7 Relevant News Articles               |
|--------------------|--------------------------------------------|
| 0.7103888392448425 | Family-Friendly Activities in London       |
| 0.7099422812461853 | The Best Photography Exhibitions in London |
| 0.7076156735420227 | Unique Shopping Experiences in London      |
| 0.7006320357322693 | Family-Friendly Events in London           |
| 0.6981644034385681 | Best Photo Spots in London                 |
| 0.6938719153404236 | Top Photography Spots in London            |
| 0.6879022121429443 | Exploring London's Cultural Scene          |

These articles are relevant to London, but some are duplicates:
- "Family-Friendly Activities in London" and "Family-Friendly Events in London"
- "Best Photo Spots in London" and "Top Photography Spots in London"

In many cases, retrieving both relevant and diverse documents is essential. For instance, when using [Retrieval-Augmented Generation](https://www.promptingguide.ai/techniques/rag) (RAG) in LLMs, the context window is limited, so we prefer selecting text snippets that are relevant but not duplicates. The [LangChain](https://www.langchain.com/) framework supports RAG and provides the [Maximal Marginal Relevance](https://aclanthology.org/X98-1025/) (MMR) technique [1, 2, 4, 5].

A document has **high marginal relevance** if it is both *relevant* to the query and contains *minimal similarity to previously selected documents*. **MMR** is defined as:

$$
MMR \overset{def}{=} \underset{D_i \in R \setminus S}{argmax}
      [ \lambda * Sim_1(D_i,Q) -
        (1-\lambda) * \underset{D_j \in S}{max}(Sim_2(D_i, D_j)) ] \hspace{1.5cm} \text{[1, 2]}
$$

where:
- C - document collection
- Q - query
- R - ranked list of documents retrieved by the IR system (\\( R \subseteq C \\))
- S - subset of documents in R already provided to the user (\\( S \subseteq C \\))
- R \\ S - subset of documents not yet offered to the user
- \\( \lambda \\) - hyperparameter to prefer more relevant or more diverse documents

Let's implement this technique (see [5, 6] for other implementations). First, we select the most relevant document. Then we iteratively select the document that gives the maximum MMR score (most relevant one and most dissimilar to the documents that we have already selected), until we select the requested number of documents.

We'll reuse the previously computed similarity matrix and now use similarities between each pair of documents. The document-document similarity metric can differ from the query-document similarity, but for simplicity, we'll use cosine similarity as well.

```python
def maximal_marginal_relevance(similarities, num_to_select, lambda_param):
    if len(similarities) <= 1 or num_to_select <= 0: return []

    most_similar = np.argmax(similarities[0, 1:])

    selected = [most_similar]
    candidates = set(range(len(similarities) - 1))
    candidates.remove(most_similar)

    while (len(selected) < num_to_select):
        if not candidates:
            break

        mmr_scores = {}
        for i in candidates:
            mmr_scores[i] = (lambda_param * similarities[i+1, 0] -
                (1 - lambda_param) * max([similarities[i+1, j+1] for j in selected]))

        next_best = max(mmr_scores, key=mmr_scores.get)
        selected.append(next_best)
        candidates.remove(next_best)
    return selected
```

Let's select the top 7 relevant news articles using the MMR technique:

```python
article_mmr_order = maximal_marginal_relevance(article_similarities,
                                               num_to_select = 7,
                                               lambda_param = .5)
print_selected(article_mmr_order, article_similarities, article_titles)
```

| Cosine Similarity  | Top 7 Relevant News Articles                  |
|--------------------|-----------------------------------------------|
| 0.7103888392448425 | Family-Friendly Activities in London          |
| 0.685788631439209  | The Evolution of Theatre in London            |
| 0.6981644034385681 | Best Photo Spots in London                    |
| 0.6072949767112732 | Weather Patterns Affecting London This Summer |
| 0.5159177780151367 | Python Tips for Mastering Data Science        |
| 0.6396927237510681 | The Best Parks and Green Spaces in London     |
| 0.7076156735420227 | Unique Shopping Experiences in London         |

The new set of articles does not contain duplicates. However, there is an article not quite related to our query: "Python Tips for Mastering Data Science". This issue can be mitigated by selecting a better \\( \lambda \\) value.

Referring to the MMR formula again:

- \\( \lambda = 1 \\): Computes incrementally the standard relevance-ranked list
- \\( \lambda = 0 \\): Computes a maximal diversity ranking among documents in R
- \\( \lambda \in [0,1] \\): Optimizes a linear combination of both criteria

According to [1]:

> Users wishing to sample the information space around the query, should set \\( \lambda \\) , at a smaller value, and those wishing to focus in on multiple potentially overlapping or reinforcing relevant documents, should set \\( \lambda \\), to a value closer to 1. For document retrieval, we found that a particularly effective search strategy... is to start with a small \\( \lambda \\) (e.g. \\( \lambda = .3 \\)) in order to understand the information space in the region of the query, and then to focus on the most important parts using a reformulated query and a larger value of \\( \lambda \\) (e.g. \\( \lambda = .7 \\)).

By setting a higher value of \\( \lambda = .7 \\):

```python
article_mmr_order_07 = maximal_marginal_relevance(article_similarities,
                                                  num_to_select = 7,
                                                  lambda_param = .7)
print_selected(article_mmr_order_07, article_similarities, article_titles)
```

| Cosine Similarity  | Top 7 Relevant News Articles                     |
|--------------------|--------------------------------------------------|
| 0.7103888392448425 | Family-Friendly Activities in London             |
| 0.685788631439209  | The Evolution of Theatre in London               |
| 0.7099422812461853 | The Best Photography Exhibitions in London       |
| 0.7076156735420227 | Unique Shopping Experiences in London            |
| 0.6879022121429443 | Exploring London's Cultural Scene                |
| 0.6938719153404236 | Top Photography Spots in London                  |
| 0.6432080268859863 | Day Trips from London: Exploring the Countryside |

Now, all articles are related to `London`, and there are no duplicates. Increasing \\( \lambda \\) further to .8, then we get:

```python
article_mmr_order_08 = maximal_marginal_relevance(article_similarities,
                                                  num_to_select = 7,
                                                  lambda_param = .8)
print_selected(article_mmr_order_08, article_similarities, article_titles)
```

| Cosine Similarity  | Top 7 Relevant News Articles               |
|--------------------|--------------------------------------------|
| 0.7103888392448425 | Family-Friendly Activities in London       |
| 0.7099422812461853 | The Best Photography Exhibitions in London |
| 0.7076156735420227 | Unique Shopping Experiences in London      |
| 0.685788631439209  | The Evolution of Theatre in London         |
| 0.6879022121429443 | Exploring London's Cultural Scene          |
| 0.6938719153404236 | Top Photography Spots in London            |
| 0.6981644034385681 | Best Photo Spots in London                 |

Again, all articles are related to `London`, but we have a duplicate pair: "Top Photography Spots in London" and "Best Photo Spots in London". For this example, \\( \lambda = .7 \\) works well.

For the complete implementation, refer to the [Jupyter Notebook](https://github.com/anton-dergunov/ml-playground/blob/master/techniques/maximal_marginal_relevance.ipynb).

References:

1. [J. Goldstein and J. Carbonell, ‘Summarization: (1) Using MMR for Diversity- Based Reranking and (2) Evaluating Summaries’, in TIPSTER TEXT PROGRAM PHASE III: Proceedings of a Workshop held at Baltimore, Maryland, October 13-15, 1998, Baltimore, Maryland, USA: Association for Computational Linguistics, Oct. 1998, pp. 181–195](https://aclanthology.org/X98-1025/)

2. [J. Carbonell and J. Goldstein, ‘The use of MMR, diversity-based reranking for reordering documents and producing summaries’, in Proceedings of the 21st annual international ACM SIGIR conference on Research and development in information retrieval, in SIGIR ’98. New York, NY, USA: Association for Computing Machinery, Aug. 1998, pp. 335–336](https://dl.acm.org/doi/10.1145/290941.291025)

3. [P. Lewis et al., ‘Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks’, Apr. 12, 2021](https://arxiv.org/abs/2005.11401)

4. LangChain Documentation: [How to select examples by maximal marginal relevance (MMR)](https://python.langchain.com/v0.2/docs/how_to/example_selectors_mmr/)

5. [Implementation of Maximal Marginal Relevance in LangChain project](https://github.com/langchain-ai/langchain/blob/18da9f5e59892051be90b5070ae0c03180fef0b1/libs/community/langchain_community/vectorstores/utils.py#L23)

6. [Implementation of Maximal Marginal Relevance in Python](https://github.com/stepgazaille/mmr)

