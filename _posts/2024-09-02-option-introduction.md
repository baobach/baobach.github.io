---
title: 'In-Depth Guide to Simulating Paths with the Euler-Maruyama Scheme for Exotic Options Pricing'
date: 2024-09-11
permalink: /posts/2024/09/devdocs/
tags:
  - quantitative finance
  - options
  - pricing model
  - option pricing theory
---

In the world of finance, exotic options offer unique payoff structures that are highly sensitive to the path taken by the underlying asset. Traditional pricing models like Black-Scholes are not sufficient for such path-dependent options, so we turn to simulation methods. One of the most efficient methods for simulating asset prices is the **Euler-Maruyama scheme**, which is used to approximate solutions for stochastic differential equations (SDEs) like the geometric Brownian motion (GBM) that models asset prices.

This article delves into how to simulate asset price paths using the **Euler-Maruyama scheme** and leverage these simulations to price **Asian** and **Lookback options**, two of the most common exotic options in financial markets. We will explore the mathematical underpinnings, discuss the implementation, and showcase results for pricing these options through Monte Carlo simulations.

## Pricing Options Under the Risk-Neutral Framework

In quantitative finance, the price of an option is typically the expected value of its discounted payoff under the **risk-neutral density** $\mathbb{Q}$:

$$
V(S,t) = e^{-r(T-t)}\mathbb{E}^\mathbb{Q}[\mathbf{Payoff}(S_{T})]
$$

Where:

- $V(S,t)$ is the option value at time $t$
- $r$ is the risk-free interest rate
- $T$ is the expiry of the option
- $\mathbb{E}^\mathbb{Q}$ denotes the expectation under the risk-neutral measure
- $\mathbf{Payoff}(S_T)$ is the payoff of the option at expiry

For our examples, we’ll assume the following input data:

$$
\begin{align*}
\text{Today's stock price }S_{0} &= 100 \\
\text{Strike price } E &= 100 \\
\text{Time to expiry }(T - t) &= \text{1 year} \\
\text{Volatility } \sigma &= 20\% \\
\text{Constant risk-free interest rate } r &= 5\%
\end{align*}
$$

```python
# Importing libraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
# Define parameters and variables
S0 = 100
E = 100
T = 1
vol = 0.2
risk_free_rate = 0.05
```

## Simulating Paths Using the Euler-Maruyama Scheme

To simulate the price paths of an asset, we use the **Euler-Maruyama scheme**, a numerical method to solve stochastic differential equations (SDEs). A common SDE for modeling asset prices is the **geometric Brownian motion**:

$$
dS = r S \, dt + \sigma S \, dW
$$

Where:

- $S$ is the price of the asset
- $r$ is the risk-free interest rate
- $\sigma$ is the volatility
- $dW$ represents the Wiener process or Brownian motion

The logarithmic transformation of $S$ simplifies the SDE:

$$
d(\log S) = \left(r - \frac{1}{2} \sigma^{2}\right) dt + \sigma dW
$$

By integrating this equation, we obtain the exact solution:

$$
S(t) = S_0 \exp \left(\left(r - \frac{1}{2} \sigma^{2}\right) t + \sigma W(t)\right)
$$

This exact solution is useful for understanding the dynamics of $S$, but for practical purposes, we approximate it using the Euler-Maruyama scheme:

$$
S_{t + dt} = S_t \exp \left(\left(r - \frac{1}{2} \sigma^{2}\right) dt + \sigma \sqrt{dt} \, \phi \right)
$$

Where $\phi$ is a random variable drawn from a standard normal distribution. The **Euler-Maruyama scheme** is accurate enough for most pricing problems and has an error of order $O(\Delta t)$.

### Implementation in Python

We can now implement the Euler-Maruyama scheme to simulate multiple paths of the asset price:

```python
# Define simulation function
def simulate_path(s0, risk_free_rate, vol, horizon, timesteps, n_sims):
    # Seed for reproducibility
    seed = 2023
    rng = np.random.default_rng(seed)
    
    # Parameters
    S0 = s0 
    r = risk_free_rate
    T = horizon
    t = timesteps
    n = n_sims
    vol = vol
    
    # Time step size
    dt = T/t
    
    # Initialize array to store simulated paths
    S = np.zeros((t,n))
    S[0] = S0
    for i in range(0, t-1):
        w = rng.standard_normal(n)
        S[i+1] = S[i] * np.exp((r - 0.5 * vol**2) * dt + vol * np.sqrt(dt) * w)
    return S
```

Let’s simulate the asset paths with the following parameters:

- **Number of paths**: `100,000`
- **Time steps**: `252` trading days

```python
# Monte Carlo parameters
n = 100000  # Number of iterations
t = 252     # Number of trading days
# Simulate paths and assign to DataFrame
S = pd.DataFrame(simulate_path(S0, risk_free_rate, vol, T, t, n))
# Plot the first 100 simulated paths
plt.plot(S.iloc[:,:100])
plt.xlabel('Time steps')
plt.ylabel('Stock price')
plt.title('Euler-Maruyama Scheme - 100 Simulated Paths')
plt.show()
```

![Euler-Maruyama Plot](https://quantfin.net/images/blogs/euler-method.png)

## Pricing Exotic Options

With our simulated paths in hand, we can now calculate the payoffs for exotic options and determine their price by averaging the payoff across all paths and discounting to the present value.

### 1. **Asian Options Pricing**

An **Asian option** is an exotic option where the payoff depends on the average price of the underlying asset over a specific time period. There are two types of Asian options based on how the average is used in the payoff:

1. **Average strike option**: The average price is used in place of the strike price.
2. **Average rate option**: The average price is used in place of the underlying price.

The formulas for the payoffs are as follows:

- Average strike call: $\max(S - A, 0)$
- Average strike put: $\max(A - S, 0)$
- Average rate call: $\max(A - E, 0)$
- Average rate put: $\max(E - A, 0)$

Where $A$ is the arithmetic average of the underlying prices:

$$
A_i = \frac{1}{i} \sum_{k=1}^{i} S(t_k)
$$

**Python Implementation:**

```python
# Average price across the paths
A = S.mean(axis=0)
# Calculate Asian option payoffs
C_asian = np.exp(-risk_free_rate * T) * np.mean(np.maximum(A - E, 0))
P_asian = np.exp(-risk_free_rate * T) * np.mean(np.maximum(E - A, 0))
# Print values
print(f"Asian Call Option Value is {C_asian:.4f}")
print(f"Asian Put Option Value is {P_asian:.4f}")
```

The output for the Asian options is:

```zsh
Asian Call Option Value is 5.7608
Asian Put Option Value is 3.3467
```

### 2. **Lookback Options Pricing**

A **Lookback option** is another type of exotic option where the payoff depends on the maximum or minimum price of the underlying asset during the option’s life. The two types of Lookback options are:

1. **Floating strike option**: The strike price is determined by the minimum or maximum price observed during the life of the option.
2. **Fixed strike option**: The strike price is fixed, and the payoff is based on the maximum or minimum asset price.

The payoffs are:

- Floating strike call: $\max(S - M_{\min}, 0)$
- Floating strike put: $\max(M_{\max} - S, 0)$
- Fixed strike call: $\max(M_{\max} - E, 0)$
- Fixed strike put: $\max(E - M_{\min}, 0)$

Where $M_{\max}$ and $M_{\min}$ are the maximum and minimum prices of the asset:

$$
M_{\max} = \max_{0 \leq \tau \leq t} S(\tau), \quad M_{\min} = \min_{0 \leq \tau \leq t} S(\tau)
$$

**Python Implementation:**

```python
# Tracking variables for maximum and minimum
M_max = np.max(S, axis=0)
M_min = np.min(S, axis=0)
# Calculate Lookback option payoffs
C_lookback = np.exp(-risk_free_rate * T) * np.mean(np.maximum(M_max - E, 0))
P_lookback = np.exp(-risk_free_rate * T) * np.mean(np.maximum(E - M_min, 0))
# Print values
print(f"Lookback Call Option Value is {C_lookback:.4f}")
print(f"Lookback Put Option Value is {P_lookback:.4f}")
```

The output for the Lookback options is:

```zsh
Lookback Call Option Value is 18.3007
Lookback Put Option Value is 13.4701
```

## Conclusion

In this guide, we walked through the process of simulating asset price paths using the Euler-Maruyama scheme, a widely-used numerical method for approximating stochastic differential equations. We then applied Monte Carlo simulations to price two types of exotic options: Asian options and Lookback options.

The Euler-Maruyama method allows us to model complex path-dependent payoffs, and by adjusting our payoff functions, this technique can be extended to other exotic options, such as **barrier options** or **rainbow options**. As a next step, readers can explore variations of the parameters—such as volatility, time to maturity, and interest rates—to see how they affect the pricing of these exotic options.

By mastering these simulation techniques, you can gain a deeper understanding of how exotic options are priced and open the door to pricing more sophisticated financial derivatives.

---
