---
title: "Specific Title That Names the Technique"
categories: [Quantitative Finance, Tutorial]
tags: [monte-carlo, options, python]
description: "One concrete sentence for the search snippet, 50 to 160 characters long."
---

> **TL;DR:** Optional. One or two sentences with the main result.

Start with the technical content: the problem, the model, or the code. No broad introduction.

## A Subtitle That Says What This Section Shows

One or two sentences on what this section covers, then the explanation in prose.

$$
\mathbb{E}[\varphi(X)] \geq \varphi(\mathbb{E}[X])
$$

```python
import numpy as np

rng = np.random.default_rng(42)
paths = rng.standard_normal((10_000, 252)).cumsum(axis=1)
```

![What the figure shows, in words](figure-1.png)

> [!tip] Optional callout
> Obsidian callouts become Chirpy prompts.

## Another Meaningful Subtitle

Overview sentence, then the deeper part.

## What This Leaves Open

At most four sentences on practical implications and open problems. No "In conclusion".

---

**What are your thoughts?** Discuss in the comments below or connect with me on [LinkedIn](https://www.linkedin.com/in/robertbachvan/).
