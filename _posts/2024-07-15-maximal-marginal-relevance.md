---
title:     "Maximal Marginal Relevance"
date:      2024-07-15
permalink: /posts/2024/07/maximal-marginal-relevance
tags:
  - machine learning
---


```python
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
```


```python
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


```python
sentiments = [
    "Amazing", "Awful", "Bad", "Beautiful", "Boring", "Brilliant", "Clunky", "Confusing", "Cool", 
    "Delightful", "Disappointing", "Dreadful", "Effective", "Enjoyable", "Excellent", "Exceptional", 
    "Exciting", "Fantastic", "Fascinating", "Flawless", "Frustrating", "Good", "Great", "Horrible", 
    "Impressive", "Incredible", "Inspiring", "Interesting", "Lame", "Lackluster", "Lovely", "Magnificent", 
    "Mediocre", "Memorable", "Miserable", "Nice", "Outstanding", "Overrated", "Pathetic", "Perfect", 
    "Phenomenal", "Pleasing", "Poor", "Predictable", "Refreshing", "Remarkable", "Rewarding", "Riveting", 
    "Satisfying", "Sensational", "Slow", "Spectacular", "Stale", "Stunning", "Subpar", "Superb", 
    "Surprising", "Terrible", "Thrilling", "Tiresome", "Top-notch", "Unbelievable", "Underwhelming", 
    "Uninspired", "Unpleasant", "Unsatisfactory", "Unwatchable", "Uplifting", "Vibrant", "Wondrous", 
    "Worthless", "Wretched", "Zippy", "Appalling", "Astounding", "Average", "Cheesy", "Competent", 
    "Depressing", "Disastrous", "Engaging", "Enigmatic", "Exceptional", "Forgettable", "Heartwarming", 
    "Inconsistent", "Inspiring", "Lackluster", "Mediocre", "Overwhelming", "Pathetic", "Predictable", 
    "Repetitive", "Refreshing", "Stunning", "Tense", "Thought-provoking", "Timeless", "Uneven", "Unpredictable"
]
```


```python
def cosine_similarity(vector1, vector2):
    dot_product = np.dot(vector1, vector2)
    norm_vector1 = np.linalg.norm(vector1)
    norm_vector2 = np.linalg.norm(vector2)
    return dot_product / (norm_vector1 * norm_vector2)
```


```python
def compute_similarities(entities, query):
    embeddings = get_embeddings([query] + entities)
    num_words = embeddings.shape[0]
    similarities = np.zeros((num_words, num_words))

    for i in range(num_words):
        for j in range(num_words):
            similarities[i, j] = cosine_similarity(embeddings[i], embeddings[j])

    return similarities

similarities = compute_similarities(sentiments, query="Something really positive")
```


```python
def similarity_relevance(similarities):
    return sorted(range(len(similarities) - 1), key=lambda i: similarities[0, i+1], reverse=True)

similarity_order = similarity_relevance(similarities)
```


```python
def print_selected(ranking, similarities, entities):
    for i in ranking:
        print(f"{similarities[0, i+1]}\t{entities[i]}")
```


```python
print_selected(similarity_order[:7], similarities, sentiments)
```

    0.7485777735710144	Cool
    0.7452228665351868	Sensational
    0.7436078190803528	Nice
    0.7379644513130188	Amazing
    0.7372422814369202	Interesting
    0.7350696325302124	Surprising
    0.7315787672996521	Perfect


Reference implementation:
https://github.com/langchain-ai/langchain/blob/18da9f5e59892051be90b5070ae0c03180fef0b1/libs/community/langchain_community/vectorstores/utils.py#L23


```python
def maximal_marginal_relevance(similarities, num_to_select, lambda_param):
    most_similar = np.argmax(similarities[0, 1:])

    selected = [most_similar]
    candidates = set(range(len(similarities) - 1))
    candidates.remove(most_similar)

    while (len(selected) < num_to_select):
        if not candidates:
            break

        mmr_scores = {}
        for i in candidates:
            mmr_scores[i] = lambda_param * similarities[i+1, 0] - (1 - lambda_param) * max([similarities[i+1, j+1] for j in selected])

        next_best = max(mmr_scores, key=mmr_scores.get)
        selected.append(next_best)
        candidates.remove(next_best)
    return selected
```


```python
import unittest

class TestMaximalMarginalRelevance(unittest.TestCase):
    def test_basic_case(self):
        similarities = np.array([
            [1, 0.8, 0.6],
            [0.8, 1, 0.5],
            [0.6, 0.5, 1]
        ])
        result = maximal_marginal_relevance(similarities, 2, 0.5)
        self.assertEqual(result, [0, 1])

    def test_single_selection(self):
        similarities = np.array([
            [1, 0.8, 0.9],
            [0.8, 1, 0.7],
            [0.9, 0.7, 1]
        ])
        result = maximal_marginal_relevance(similarities, 1, 0.5)
        self.assertEqual(result, [1])

    def test_all_selection(self):
        similarities = np.array([
            [1, 0.8, 0.6, 0.4],
            [0.8, 1, 0.5, 0.2],
            [0.6, 0.5, 1, 0.1],
            [0.4, 0.1, 0.2, 1]
        ])
        result = maximal_marginal_relevance(similarities, 3, 0.5)
        self.assertEqual(result, [0, 2, 1])

    def test_lambda_param(self):
        similarities = np.array([
            [1, 0.8, 0.6, 0.4],
            [0.8, 1, 0.5, 0.2],
            [0.6, 0.5, 1, 0.1],
            [0.4, 0.1, 0.2, 1]
        ])
        result = maximal_marginal_relevance(similarities, 3, 0.9)
        self.assertEqual(result, [0, 1, 2])

unittest.main(argv=[''], exit=False)
```

    ....
    ----------------------------------------------------------------------
    Ran 4 tests in 0.002s
    
    OK





    <unittest.main.TestProgram at 0x10685f410>




```python
selected = maximal_marginal_relevance(similarities, num_to_select = 10, lambda_param = 0.7)
```


```python
print_selected(selected[:7], similarities, sentiments)
```

    0.7485777735710144	Cool
    0.7452228665351868	Sensational
    0.7044647932052612	Inspiring
    0.7350696325302124	Surprising
    0.7195003628730774	Phenomenal
    0.7436078190803528	Nice
    0.6781834363937378	Unwatchable



```python
article_titles = [
    # Culture
    "The Revival of Ancient Traditions in Modern Society",
    "Exploring the Intersection of Art and Technology",
    "A Deep Dive into Indigenous Music Around the World",
    "How Street Art is Shaping Urban Culture",
    "Cultural Festivals You Can't Miss This Year",
    "The Impact of Globalization on Local Cultures",
    "Art Exhibitions That Will Transform Your Perspective",
    "The Evolution of Theatre in London",
    "The Influence of Eastern Philosophy in Western Culture",
    "Exploring London's Cultural Scene",

    # Weather
    "Understanding the Science Behind Extreme Weather Events",
    "How Climate Change is Affecting Global Weather Patterns",
    "Preparing for Hurricane Season: What You Need to Know",
    "The Future of Weather Forecasting: Innovations and Challenges",
    "Heatwaves: Causes, Effects, and Mitigation Strategies",
    "The Impact of El Niño and La Niña on Global Weather",
    "Winter Storms: Preparing for the Unexpected",
    "How Urbanization Affects Local Weather Patterns",
    "Weather Patterns Affecting London This Summer",
    "How London's Weather Has Changed Over the Decades",

    # World News
    "Global Leaders Convene to Discuss Climate Action",
    "The Economic Impacts of the Latest Trade Agreements",
    "Technological Advancements in Developing Nations",
    "Elections Around the World: Key Outcomes and Implications",
    "The Role of Social Media in Modern Revolutions",
    "Global Health Initiatives: Progress and Challenges",
    "Diplomatic Tensions and Their Global Ramifications",
    "The Growing Influence of Social Media on Photography",
    "London's Role in Global Climate Talks",
    "Brexit and Its Impact on London's Economy",

    # Programming Languages
    "Top 10 Programming Languages to Learn in 2024",
    "How Python Became the Go-To Language for Data Science",
    "The Growing Popularity of Rust in Systems Programming",
    "Comparing Functional and Object-Oriented Programming Paradigms",
    "The Impact of Open Source on Programming Language Development",
    "The Role of Swift in Apple's Ecosystem",
    "Emerging Programming Languages to Keep an Eye On",
    "Python Tips for Mastering Data Science",
    "London's Tech Scene and Programming Trends",
    "How London's Startups are Using AI",

    # Photography News
    "The Intersection of Photography and Virtual Reality",
    "How Drones are Revolutionizing Aerial Photography",
    "The Best New Cameras and Lenses of the Year",
    "Exploring the World of Underwater Photography",
    "The Art of Portrait Photography: Techniques and Tips",
    "The Role of Post-Processing in Modern Photography",
    "The Intersection of Photography and Virtual Reality",
    "How to Build a Professional Photography Portfolio",
    "Exploring London's Best Photography Spots",
    "The Best Photography Exhibitions in London",

    # Things to Do in London
    "Historic Landmarks You Can't Miss in London",
    "Family-Friendly Activities in London",
    "Family-Friendly Events in London",
    "The Best Parks and Green Spaces in London",
    "Unique Shopping Experiences in London",
    "Day Trips from London: Exploring the Countryside",
    "Cultural Festivals in London This Year",
    "Top Photography Spots in London",
    "London's Tech Scene and Programming Trends",
    "Best Photo Spots in London"
]
```


```python
article_similarities = compute_similarities(article_titles, query="London")
```


```python
article_similarity_order = similarity_relevance(article_similarities)
print_selected(article_similarity_order[:7], article_similarities, article_titles)
```

    0.7103888392448425	Family-Friendly Activities in London
    0.7099422812461853	The Best Photography Exhibitions in London
    0.7076156735420227	Unique Shopping Experiences in London
    0.7006320357322693	Family-Friendly Events in London
    0.6981644034385681	Best Photo Spots in London
    0.6938719153404236	Top Photography Spots in London
    0.6879022121429443	Exploring London's Cultural Scene


- Includes very similar "Family-Friendly Activities in London" and "Family-Friendly Events in London"
- Includes very similar "Best Photo Spots in London" and "Top Photography Spots in London"


```python
article_mmr_order = maximal_marginal_relevance(article_similarities, num_to_select = 10, lambda_param = .7)
print_selected(article_mmr_order[:7], article_similarities, article_titles)
```

    0.7103888392448425	Family-Friendly Activities in London
    0.685788631439209	The Evolution of Theatre in London
    0.7099422812461853	The Best Photography Exhibitions in London
    0.7076156735420227	Unique Shopping Experiences in London
    0.6879022121429443	Exploring London's Cultural Scene
    0.6938719153404236	Top Photography Spots in London
    0.6432080268859863	Day Trips from London: Exploring the Countryside


- Does not include these duplicated articles
- All articles are still related to London


```python
article_mmr_order = maximal_marginal_relevance(article_similarities, num_to_select = 10, lambda_param = .5)
print_selected(article_mmr_order[:7], article_similarities, article_titles)
```

    0.7103888392448425	Family-Friendly Activities in London
    0.685788631439209	The Evolution of Theatre in London
    0.6981644034385681	Best Photo Spots in London
    0.6072949767112732	Weather Patterns Affecting London This Summer
    0.5159177780151367	Python Tips for Mastering Data Science
    0.6396927237510681	The Best Parks and Green Spaces in London
    0.7076156735420227	Unique Shopping Experiences in London


- Does not include these duplicated articles
- But includes an article "Python Tips for Mastering Data Science" which is not very related to London


```python
article_mmr_order = maximal_marginal_relevance(article_similarities, num_to_select = 10, lambda_param = .8)
print_selected(article_mmr_order[:7], article_similarities, article_titles)
```

    0.7103888392448425	Family-Friendly Activities in London
    0.7099422812461853	The Best Photography Exhibitions in London
    0.7076156735420227	Unique Shopping Experiences in London
    0.685788631439209	The Evolution of Theatre in London
    0.6879022121429443	Exploring London's Cultural Scene
    0.6938719153404236	Top Photography Spots in London
    0.6981644034385681	Best Photo Spots in London


- Now all articles are related to London
- But still includes a similar pair of articles "Top Photography Spots in London" and "Best Photo Spots in London"
