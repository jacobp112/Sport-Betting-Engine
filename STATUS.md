# Project Status Log

This file is updated at the end of each Epic with a brief summary of what is true now and what changed.

---

### Epic 0: Project Setup & Team Workflow (Completed: 2026-07-12)
**Status:** Ready for Epic 1.
The initial repository structure has been established with standard directories for data, notebooks, source code, backtests, documentation, and logs. Key team workflow assets are in place, including the team roles definition (`/docs/team.md`), the decision log template (`/docs/decisions.md`), and the shared bet-tracking schema (`/docs/bet_tracking_schema.md`). The target league has been chosen as the English Football League (EFL) Championship. We are now fully prepared to begin Epic 1 (Data Foundation).

### Epic 1: Data Foundation (Completed: 2026-07-12)
**Status:** Completed.
We have successfully completed the data foundation phase. Historical match and odds data for the EFL Championship and League One across 5 full seasons (21/22 - 25/26) has been ingested, validated, and processed. The pipeline handles missing Pinnacle odds gracefully by soft-nulling and logging, enforces strict data validation (plausible goal range, cross-field FTR consistency, duplicate checks), and normalises all team names to standard canonical full names via a JSON map. A master script (`scripts/run_pipeline.py`) executes the end-to-end pipeline atomically and verifies byte-identical reproducibility using MD5 checksum assertions against a reference file. All raw and processed datasets are snapshot in version control.

### Epic 2: Feature Engineering (Completed: 2026-07-12)
**Status:** Ready for Epic 3.
We have completed all feature engineering stories (FEAT-1 through FEAT-6). The pipeline generates 92 columns of model-ready features, including overall rolling averages (goals, points, goal difference), home/away venue splits, team rest days, schedule congestion flags, and chronological head-to-head history. Leakage prevention is enforced via chronological sorting and strict `shift(1)` offsets. Edge-case cold starts for promoted/relegated teams are handled using a mathematical blending formula with prior-season defaults. Features are fully documented in `/docs/features.md`, and the entire generation runs automatically via `scripts/build_features.py`. All unit tests pass.
### Epic 3: First Model — Poisson / Elo Baseline (Completed: 2026-07-12)
**Status:** Completed.
We have built and evaluated two baseline prediction models for the EFL Championship. **Model 1 (Independent Double Poisson GLM)** fits expected goals via MLE over rolling features with a log-link function, producing 1X2 probabilities through joint Poisson grid summation. **Model 2 (Dynamic Elo Ratings)** tracks team strength chronologically with Margin-of-Victory K-factor scaling and maps rating differences to 1X2 probabilities via a Multinomial Logistic Regression calibrator. Both models are trained on seasons 21/22–23/24 (1,656 matches) and validated on season 24/25 (552 matches). Season 25/26 (552 matches) is fully quarantined. Following the resolution of an unstable sorting bug in the Elo calibrator, the dynamic Elo model is the best-performing baseline with a validation Brier Score of **0.6292** and Log-Loss of **1.0441** (beating the Naive baseline of 0.6475 / 1.0722, and the Poisson GLM baseline of 0.6364 / 1.0546). The independence assumption (no Dixon-Coles $\tau$ correction) is documented as a known limitation in the model card (`/docs/model_card_baseline.md`). All 8 unit tests pass.

