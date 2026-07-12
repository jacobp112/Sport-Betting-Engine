# Model Card: Baseline Models (v1.0)

## Overview

This document describes the two baseline prediction models trained for the EFL Championship:

1. **Independent Double Poisson GLM** (MODEL-1)
2. **Dynamic Elo Ratings** (MODEL-2)

Both models are evaluated against a **Naive Baseline** (league-wide average FTR distribution).

---

## Naive Baseline Definition

The **Naive Baseline** is a constant probability predictor defined by the historical class frequencies observed in the training set (seasons 21/22–23/24):
- $P(\text{Home Win}) = 43.15\%$
- $P(\text{Draw}) = 25.56\%$
- $P(\text{Away Win}) = 31.29\%$

Under argmax classification, this model always predicts a **Home Win** (as the class frequency mode). Consequently, its accuracy on the validation set is exactly the proportion of Home Wins in that set (45.83%).

---

## Model 1: Independent Double Poisson GLM

### Architecture

A Poisson Generalized Linear Model (GLM) with a **log-link function** fitted via Maximum Likelihood Estimation (MLE) over rolling form features.

Two separate Poisson regression models are trained:
- **Home Goals Model**: Predicts expected home goals ($\lambda$)
- **Away Goals Model**: Predicts expected away goals ($\mu$)

The log-link function ensures expected goals are always strictly positive:

$$\lambda = \exp(\theta_0 + \theta_1 X_1 + \theta_2 X_2 + \dots)$$

### Phrasing & Design Rationale

> [!NOTE]
> Bypassing the classic Dixon-Coles parameter-per-team model in favor of a feature-based Poisson GLM is a deliberate **design choice** to address the 25% annual team turnover in the Championship.
> Under a team-parameter model, relegated and promoted teams require arbitrary initial strength parameter seeding, whereas rolling form features naturally inherit prior-division stats. 
> Whether this generalizes better in practice remains a hypothesis to be verified by backtesting (Epic 4).

### Feature Set

**Home Goals Model inputs:**
- `home_rolling_gs_5`, `home_rolling_gs_10`, `away_rolling_gc_5`, `away_rolling_gc_10`
- `home_venue_rolling_gs_5`, `home_venue_rolling_gs_10`
- `home_rolling_gd_5`, `home_rest_days`

**Away Goals Model inputs:** Mirror structure using `away_rolling_gs_*`, `home_rolling_gc_*`, `away_venue_rolling_gs_*`, `away_rolling_gd_*`, `away_rest_days`.

### Probability Calculation

Match outcome probabilities are computed by constructing the joint probability grid:

$$P(X=x, Y=y) = \frac{\lambda^x e^{-\lambda}}{x!} \times \frac{\mu^y e^{-\mu}}{y!}$$

The grid (up to 15 goals) is summed:
- **Home Win**: $\sum_{x > y} P(X=x, Y=y)$
- **Draw**: $\sum_{x = y} P(X=x, Y=y)$
- **Away Win**: $\sum_{x < y} P(X=x, Y=y)$

### Known Limitation: Independence Assumption

> **This is an Independent Double Poisson model, NOT a Bivariate Poisson model.**
>
> The formula above assumes that home goals and away goals are statistically independent.
> In practice, EFL Championship matches exhibit a dependency: 0-0 and 1-1 draws occur
> more frequently than an independent model predicts. A true Bivariate Poisson model
> (e.g., Dixon-Coles with a $\tau$ correction factor) would address this, but is
> deferred to a future model iteration.

---

## Model 2: Dynamic Elo Ratings

### Architecture

A standard Elo rating system adapted for football, tracking team strength dynamically across matches.

**Parameters:**
- **Initial Rating**: 1500 (default rating for all teams)
- **K-factor**: 32 (base update speed)
- **HFA**: 80 (home field advantage rating boost, representing standard industry convention for domestic leagues)

### Rating Update

$$R_{new} = R_{old} + K \times M \times (S - W_{e})$$

where:
- $W_{e} = \frac{1}{10^{-(R_{Home} + HFA - R_{Away}) / 400} + 1}$ (expected score)
- $S$ = actual outcome (1.0 for Win, 0.5 for Draw, 0.0 for Loss)
- $M$ = Margin of Victory multiplier (FIFA standard):
  - Goal diff $\le 1$: $M = 1.0$
  - Goal diff $= 2$: $M = 1.5$
  - Goal diff $= 3$: $M = 1.75$
  - Goal diff $\ge 4$: $M = 1.75 + \frac{d - 3}{8}$

### 1X2 Probability Calibration

Elo ratings are mapped to 3-way probabilities via a **Multinomial Logistic Regression** calibrator that fits the pre-match rating difference ($\Delta R = R_{Home} + HFA - R_{Away}$) to the outcome FTR (mapped: H=0, D=1, A=2) on the training set.

Sorting is handled chronologically and deterministically by sorting on `["DateTime", "HomeTeam", "AwayTeam"]` to guarantee row alignment between history and targets.

---

## Evaluation Results

### Temporal Split
- **Train**: Seasons 21/22, 22/23, 23/24 (1,656 matches)
- **Validation**: Season 24/25 (552 matches)
- **Test**: Season 25/26 (552 matches) — **QUARANTINED**

### Validation Set Performance (Season 24/25)

| Model | Brier Score | Log-Loss | Accuracy |
|---|---|---|---|
| Naive (league avg) | 0.6475 | 1.0722 | 45.83% |
| Poisson GLM | 0.6364 | 1.0546 | **46.74%** |
| **Elo Ratings** | **0.6292** | **1.0441** | 45.11% |

### Interpretation

- **Elo Ratings** are the best-performing baseline on probability calibration, achieving a Brier Score of **0.6292** and Log-Loss of **1.0441**. This beats both the Naive and Poisson GLM baselines. Its classification accuracy is slightly lower (45.11%) because it actively predicts Away Wins (162 matches) which have higher variance than flatly predicting Home Wins.
- **Poisson GLM** provides the best classification accuracy at **46.74%** and is well-calibrated (Brier 0.6364), representing a strong, multi-feature baseline model.

### Calibration Notes

- **Draw Calibration**: Draw probabilities are compressed for both models. In the validation set, the actual draw rate was **28.26%**, whereas the Poisson model's predicted draw probabilities average **26.32%** (with a narrow standard deviation of 1.99%).
- **Low-Scoring Draws Slice**: Across the 121 actual low-scoring draws (0-0 or 1-1 matches, 21.92% of the validation set), the Poisson model's average predicted draw probability was **26.15%**. This slight underestimation confirms the independent Poisson assumption's limitation in capturing conservative draw-seeking behaviour in late-game low-scoring states.

---

## Intended Use

These baseline models serve as the **minimum viable performance floor** for the Sport Betting Engine. Any future model must demonstrate statistically significant improvement over these validation metrics to justify added complexity.
