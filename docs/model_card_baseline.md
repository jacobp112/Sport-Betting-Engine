# Model Card: Baseline Models (v1.0)

## Overview

This document describes the two baseline prediction models trained for the EFL Championship:

1. **Independent Double Poisson GLM** (MODEL-1)
2. **Dynamic Elo Ratings** (MODEL-2)

Both models are evaluated against a **Naive Baseline** (league-wide average FTR distribution).

---

## Model 1: Independent Double Poisson GLM

### Architecture

A Poisson Generalized Linear Model (GLM) with a **log-link function** fitted via Maximum Likelihood Estimation (MLE) over rolling form features.

Two separate Poisson regression models are trained:
- **Home Goals Model**: Predicts expected home goals ($\lambda$)
- **Away Goals Model**: Predicts expected away goals ($\mu$)

The log-link function ensures expected goals are always strictly positive:

$$\lambda = \exp(\theta_0 + \theta_1 X_1 + \theta_2 X_2 + \dots)$$

### Feature Set

**Home Goals Model inputs:**
| Feature | Description |
|---|---|
| `home_rolling_gs_5` | Home team's rolling goals scored (last 5 matches) |
| `home_rolling_gs_10` | Home team's rolling goals scored (last 10 matches) |
| `away_rolling_gc_5` | Away team's rolling goals conceded (last 5 matches) |
| `away_rolling_gc_10` | Away team's rolling goals conceded (last 10 matches) |
| `home_venue_rolling_gs_5` | Home team's goals scored at home only (last 5) |
| `home_venue_rolling_gs_10` | Home team's goals scored at home only (last 10) |
| `home_rolling_gd_5` | Home team's rolling goal difference (last 5) |
| `home_rest_days` | Days since home team's last match |

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
| Parameter | Value | Description |
|---|---|---|
| Initial Rating | 1500 | Default rating for all teams |
| K-factor | 32 | Base update speed |
| HFA | 80 | Home Field Advantage rating boost |

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

Elo natively outputs an expected score, not 3-way probabilities. A **Multinomial Logistic Regression** calibrator maps the pre-match rating difference ($\Delta R = R_{Home} + HFA - R_{Away}$) to $P(Home), P(Draw), P(Away)$.

The calibrator is fitted only on the **training set** (seasons 21/22–23/24), ensuring no data leakage into the validation evaluation.

---

## Evaluation Results

### Temporal Split
| Split | Seasons | Matches | Purpose |
|---|---|---|---|
| Train | 21/22, 22/23, 23/24 | 1,656 | Model fitting |
| Validation | 24/25 | 552 | Model evaluation |
| Test | 25/26 | 552 | **QUARANTINED** — reserved for future Epics |

### Validation Set Performance (Season 24/25)

| Model | Brier Score | Log-Loss | Accuracy |
|---|---|---|---|
| Naive (league avg) | 0.6475 | 1.0722 | 45.83% |
| **Poisson GLM** | **0.6364** | **1.0546** | **46.74%** |
| Elo Ratings | 0.6465 | 1.0706 | 45.83% |

### Interpretation

- **Poisson GLM** is the best-performing baseline, beating the Naive model on all three metrics.
  - Brier improvement: 0.0111 (1.7% relative improvement)
  - Log-Loss improvement: 0.0176 (1.6% relative improvement)
- **Elo Ratings** show marginal improvement over Naive but are largely captured by the league-wide average. The Elo calibrator concentrates predictions in narrow bands (e.g., all 552 Home Win predictions fall in the 0.40–0.50 bin), suggesting the single-feature ($\Delta R$) logistic model lacks discriminative power compared to the multi-feature Poisson GLM.

### Calibration Notes

The Poisson GLM shows reasonable calibration across the Home Win bins (predicted 0.36 → actual 0.44; predicted 0.45 → actual 0.45; predicted 0.54 → actual 0.56). Draw probabilities are compressed into a single narrow band (~0.26), which is consistent with the inherent difficulty of predicting draws — a known challenge in football modeling.

---

## Intended Use

These baseline models serve as the **minimum viable performance floor** for the Sport Betting Engine. Any future model must demonstrate statistically significant improvement over the Poisson GLM's validation Brier Score of **0.6364** to justify added complexity.

## Leakage Review

- [x] Features use strict `shift(1)` chronological ordering — no future data in features
- [x] Model coefficients fitted on training set only (seasons 21/22–23/24)
- [x] Elo calibrator fitted on training set only
- [x] Validation metrics computed on season 24/25 (unseen during fitting)
- [x] Test set (season 25/26) **completely quarantined** — never loaded, never evaluated
