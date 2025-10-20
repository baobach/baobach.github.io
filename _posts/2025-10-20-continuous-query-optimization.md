---
title: 'AJOSC: Adaptive Join Order Selection for Continuous Queries'
date: 2025-10-20
categories: [Programming, Database Systems]
tags:
  - query-optimization
  - database
  - continuous-queries
  - join-order
  - algorithms
  - dynamic-programming
math: true
description: "An exploration of adaptive join order selection techniques for optimizing multi-way joins in continuous data streams."
---

> **TL;DR:** Traditional static query optimization techniques fail in dynamic streaming environments. AJOSC introduces a novel Look-Ahead cost model and incremental reordering algorithm that reduces overhead from $O(n^2 2^n)$ to $O(n2^n)$ while adapting to changing data distributions.

> **Paper Reference:** This post is based on "[AJOSC: Adaptive Join Order Selection for Continuous Queries](https://dl.acm.org/doi/10.1145/3725263)" by Xinyi Ye, Xiangyang Gou, Lei Zou, and Wenjie Zhang, published in *Proceedings of the ACM on Management of Data* (SIGMOD 2025). All figures and tables referenced are from the original paper.

## Introduction

Modern applications increasingly rely on continuous data streams—think real-time analytics, IoT sensor networks, or financial trading systems. These systems must process an endless flow of tuple insertions and deletions while maintaining registered queries efficiently. However, traditional query optimization techniques designed for static databases struggle in this dynamic environment.

The challenge? **Join order selection**—deciding which tables to combine first—dramatically impacts query performance. While we've solved this problem elegantly for static queries, the continuous setting introduces unique complications. When data distributions shift or update patterns change, the optimal join order can become suboptimal, leading to significant performance degradation.

This post explores AJOSC (Adaptive Join Order Selection for Continuous Queries), a breakthrough algorithm that addresses these challenges through innovative cost modeling and incremental optimization techniques.

## The Problem: Static Techniques in Dynamic Settings

### Multi-Way Joins and Continuous Queries

A multi-way join combines tuples from multiple tables based on join predicates. Given a registered query $Q$ over several tables, we need to:

1. Compute the initial result set
2. Update results as new tuples arrive (insertions/deletions)
3. Maintain optimal performance as data characteristics evolve

The **join order** determines which tables to combine first, directly influencing the number of executed subqueries (denoted $P$). Choose poorly, and you'll compute massive intermediate results before filtering them down.

### Why Traditional Dynamic Programming Fails

The classic approach from Selinger et al. [1] works beautifully for static queries. It recursively computes the optimal order using:

$$
T_i = \arg\min_{T \in \text{CandL}(P)} ( \text{SCost}(P-\{T\}) + \text{SJC}(P - \{T\}, T))
$$

where:
- $P$ is a subquery containing $i$ tables $\{T_1, T_2, \ldots, T_i\}$
- $\text{SCost}(\cdot)$ is the cost of computing results using the optimal order
- $\text{SJC}(\cdot)$ is the cost to join a subquery result with a table

**The critical flaw in continuous settings:** When a tuple updates table $T_i$, the join order *must* start from $T_i$ (since it contains the changes). This creates two major problems:

1. **Massive overhead from recomputation** - Every update triggers recalculation of costs from scratch. Time complexity explodes from $O(n2^n)$ in static settings to $O(n^2 2^n)$ in dynamic settings.

2. **Stale join orders** - As data distributions shift, the previously optimal order becomes suboptimal, but the system doesn't adapt efficiently.

> **Visualization:** See Figure 3 in the [original paper](https://dl.acm.org/doi/10.1145/3725263) for a detailed visualization of the search process during query execution and how updates propagate through the join order.

## The Solution: AJOSC Algorithm

AJOSC addresses these challenges through three key innovations:

### 1. Look-Ahead Cost Model (LA Cost)

Instead of computing the cost to produce a subquery result, AJOSC computes the **expected cost to use a subquery instance to compute the final results**:

$$
\text{LA}(P) = \min_{T\in\text{CandN}(P)} \left((1+w(P,T) \times \text{LA}(P \cup \{T\})) \times \sum_{T' \in P, (T',T)\in E} \deg(T',T)\right)
$$

This formulation has powerful properties:

- **Reduced recomputation:** $\text{LA}(P)$ focuses on an instance of $P$, not all instances. When an update doesn't affect query results, no recomputation is needed.
- **Update independence:** The cost of using $P$ to compute $Q$ remains stable even when unrelated tables update.

The model is controlled by parameters $\theta$ and $\delta$ (typically $\theta = 0.04, \delta = 0.05$), which balance between exploration and exploitation in the join order search space.

### 2. Cost Dependency Graph (CDG)

To efficiently compute and update LA costs, AJOSC uses a directed graph structure:

- **Nodes:** Each subquery $P$ of the main query $Q$
- **Edges:** Dependency relationships between LA costs
- **Structure:** One leaf (query $Q$), $n$ roots (individual tables)

> **Visualization:** Figure 4 in the [original paper](https://dl.acm.org/doi/10.1145/3725263) shows the CDG structure and how dependencies flow through the graph.

**Computing initial orders:** Perform bottom-up breadth-first search (BFS) to compute all LA costs.

**Finding optimal order for updated table $T_i$:** Traverse from node $T_i$ following minimum LA costs.

**Time complexity:** $O(n2^n)$ — a significant improvement over the $O(n^2 2^n)$ naive approach.

### 3. Incremental Order Recomputation (LBR)

When data distributions change significantly, AJOSC needs to update the CDG. But visiting all $2^n$ nodes is expensive. The **Lower Bound based computation Reduction (LBR)** technique solves this:

**Key insight (Theorem 5.2 in the paper):** If a node isn't on any optimal order path, its exact value doesn't matter for determining optimal orders.

**Implementation:** Tag each node as either:
- `EXACT`: Current value is accurate
- `LOWERBOUND`: Accurate value is ≥ stored value, but exact value isn't needed

When a change won't affect optimal orders, mark the node as `LOWERBOUND` without recomputing. This dramatically reduces updates while maintaining correctness.

### 4. Reordering Delay Mechanism

To prevent overreacting to transient changes or outliers:

1. Track two values per statistic: initial and current
2. Increment a counter when ratio exceeds threshold $thre = 1.5$
3. Trigger reordering only when counter reaches $c = 200$

This mechanism provides **temporal stability**, preventing expensive reorderings from temporary data anomalies.

## Performance Analysis

The authors evaluated AJOSC on three benchmark datasets:
- **JOB** (Join Order Benchmark) [2]
- **LDBC-SNB** (Social Network Benchmark) [3]
- **JCC-H** (Join-Cross-Correlation Benchmark) [4]

> **Dataset Details:** See Table 2 in the [original paper](https://dl.acm.org/doi/10.1145/3725263) for detailed properties of these datasets and their characteristics.

### Key Results

**Execution Time Improvements:**
- At least **2× faster** than state-of-the-art methods
- Outperforms static DP even under stable distributions (due to reduced overhead)
- **Efficiency scales with query complexity** — larger joins see greater benefits

> **Performance Data:** Table 3 in the [original paper](https://dl.acm.org/doi/10.1145/3725263) presents comprehensive execution time comparisons across all datasets and query complexities.

**Component Effectiveness:**
- LBR technique significantly reduces recomputation overhead
- Reordering delay mechanism prevents performance degradation from outliers

## Critical Considerations and Trade-offs

While AJOSC represents a significant advance, implementation requires careful attention:

### Parameter Sensitivity

The algorithm's performance heavily depends on four parameters:
- $\theta = 0.04$ and $\delta = 0.05$ (LA cost model)
- $thre = 1.5$ and $c = 200$ (reordering trigger)

**Challenge:** Suboptimal parameter choices can negate performance gains. Values that work well for one workload may perform poorly for another.

**Implication:** Requires extensive analysis and potentially adaptive tuning mechanisms for production deployment.

### Memory Overhead

The CDG stores LA costs for all $2^n$ subqueries. For queries with many tables, this can consume significant memory.

### Cold Start

Initial CDG construction requires computing all LA costs, which takes $O(n2^n)$ time. For very complex queries, this initialization period may be noticeable.

## Conclusion

AJOSC elegantly addresses the fundamental mismatch between static query optimization and dynamic streaming environments. By introducing the Look-Ahead cost model and incremental reordering techniques, it achieves both lower overhead and better adaptivity.

The key takeaways:

1. **Static techniques don't transfer directly** - Continuous queries need fundamentally different optimization approaches
2. **Cost model matters** - Looking ahead to final results rather than intermediate costs enables dramatic efficiency improvements  
3. **Selective recomputation** - The LBR technique shows that you don't need perfect information everywhere to find optimal solutions
4. **Robustness through delay** - Temporal dampening prevents overreaction to transient changes

If you're building systems that process continuous data streams with complex multi-way joins, AJOSC's techniques deserve serious consideration—just be prepared to invest time in parameter tuning for your specific workload.

## References

1. P. Griffiths Selinger, M. M. Astrahan, D. D. Chamberlin, R. A. Lorie, and T. G. Price. "Access path selection in a relational database management system." *Proceedings of the 1979 ACM SIGMOD International Conference on Management of Data*, 1979, pp. 23-34.

2. Viktor Leis, Andrey Gubichev, Atanas Mirchev, Peter Boncz, Alfons Kemper, and Thomas Neumann. "How good are query optimizers, really?" *Proceedings of the VLDB Endowment*, vol. 9, no. 3, 2015, pp. 204-215.

3. Orri Erling, Alex Averbuch, Josep Larriba-Pey, Hassan Chafi, Andrey Gubichev, Arnau Prat, Minh-Duc Pham, and Peter Boncz. "The LDBC social network benchmark: Interactive workload." *Proceedings of the 2015 ACM SIGMOD International Conference on Management of Data*, 2015, pp. 619-630.

4. Peter Boncz, Angelos-Christos Anatiotis, and Steffen Kläbe. "JCC-H: adding join crossing correlations with skew to TPC-H." *Technology Conference on Performance Evaluation and Benchmarking*, Springer, 2017, pp. 103-119.

5. Balakrishna R. Iyer and Arun N. Swami. "Method for optimizing processing of join queries by determining optimal processing order and assigning optimal join methods to each of the join operations." US Patent 5,345,585, 1994.

6. Xinyi Ye, Xiangyang Gou, Lei Zou, and Wenjie Zhang. "AJOSC: Adaptive Join Order Selection for Continuous Queries." *Proceedings of the ACM on Management of Data*, vol. 3, no. 3, 2025, pp. 1-27. [https://dl.acm.org/doi/10.1145/3725263](https://dl.acm.org/doi/10.1145/3725263)

---

**Questions or insights?** Have you encountered join order optimization challenges in streaming systems? I'd love to hear about your experiences. Connect with me on [LinkedIn](https://www.linkedin.com/in/robertbachvan/) to continue the discussion.
