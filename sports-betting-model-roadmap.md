# Sports Betting Model — Project Backlog

A detailed, phased backlog for building, validating, and (eventually) live-testing a statistical sports betting model. Structured as epics → user stories → sub-tasks → acceptance criteria → definition of done, sized for pasting directly into GitHub Issues or a Projects board (one story = roughly one issue).

**Suggested repo structure:**
```
/data          → raw + cleaned historical data (raw/ and processed/ subfolders)
/notebooks     → exploration, one-off analysis
/src           → reusable pipeline code (features, model, backtester)
/backtests     → saved results per model version, named by date + model version
/docs          → roadmap, model cards, decision log, metrics glossary
/logs          → paper trading and live betting logs
```

**Suggested labels:** `epic`, `data`, `feature`, `model`, `backtest`, `validation`, `paper-trading`, `live`, `risk`, `infra`

**Estimate key:** S = under a day, M = 1–3 days, L = 3+ days / needs breaking down further once started.

---

## Global Definition of Ready (applies before starting any story)
- [ ] Acceptance criteria are specific enough that two different people would agree on whether it's done
- [ ] Any upstream dependency (data, prior story) is actually finished, not "mostly done"
- [ ] If a judgment call is required, it's flagged in the issue for team discussion before coding starts

## Global Definition of Done (applies before closing any story)
- [ ] Output (script, notebook, dataset, doc) committed with a commit message referencing the issue number
- [ ] Any non-obvious decision is logged in `/docs/decisions.md` (date, decision, reasoning, alternatives considered, who decided)
- [ ] No lookahead bias introduced — explicitly check that nothing uses information not available before kickoff
- [ ] Reviewed by at least one other person on the team before merging — leakage bugs are very rarely caught by the person who wrote the code
- [ ] If the story produces a number (accuracy, ROI, etc.), that number is written down somewhere permanent, not just observed and forgotten

---

## Epic 0: Project Setup & Team Workflow
**Goal:** Repo, roles, and communication norms exist before anyone touches data, so decisions are traceable and disagreements have a process.

### Stories

**`SETUP-1`** — As a team, we want a repo with a clear README, so anyone (including future us) can understand the project's goal and current phase at a glance.
- Sub-tasks:
  - [ ] Create repo with folder structure above
  - [ ] README states: target sport/league, current phase, how to reproduce the pipeline end to end
  - [ ] Add a `STATUS.md` that's updated at the end of each epic with one paragraph: what's true now, what changed
- AC: A person with zero context can read the README and know what phase the project is in within 2 minutes.
- Estimate: S

**`SETUP-2`** — As a team, we want a decision log, so we don't relitigate the same modelling choices or forget why we made them.
- Sub-tasks:
  - [ ] Create `/docs/decisions.md` with columns: date, decision, reasoning, alternatives considered, decided by
  - [ ] Agree as a team that every non-trivial choice (feature included/excluded, threshold chosen, market selected) gets an entry
- AC: By the end of Epic 3, the log has at least one entry per major modelling choice made.
- Estimate: S

**`SETUP-3`** — As a team, we want a shared bet-tracking schema defined before we need it, so paper trading and live betting use the same format from day one.
- Sub-tasks:
  - [ ] Define fields: date, competition, match, market, side, odds taken, bookmaker, closing odds, stake, stake % of bankroll, model probability, de-vigged market probability, result, profit/loss, CLV
  - [ ] Decide where this lives (shared spreadsheet, lightweight database) and who has write access
- AC: Schema is documented in `/docs/`, and a test row can be filled in manually without ambiguity about what goes in each field.
- Estimate: S

**`SETUP-4`** — As a team, we want agreed roles and a review process, so work doesn't get merged without a second set of eyes.
- Sub-tasks:
  - [ ] Decide who owns data/infra, who owns modelling, who owns validation/risk (can overlap, but should be explicit)
  - [ ] Agree that no story closes without at least one other person reviewing it
  - [ ] Set a weekly (or regular) check-in cadence to review the decision log and current phase status
- AC: Roles and review process written down in README or `/docs/team.md`.
- Estimate: S

**Epic DoD:** Repo exists and is cloned by all collaborators; README, decision log, tracking schema, and roles are all in place before Epic 1 starts.

---

## Epic 1: Data Foundation
**Goal:** Clean, joined, reproducible historical match + odds data spanning multiple seasons, with every join and gap documented.

### Stories

**`DATA-1`** — As a modeller, I want historical match results for the target league(s) covering 3–5+ seasons, so there's enough sample size to train and test on.
- Sub-tasks:
  - [ ] Identify and document data source(s) (e.g. football-data.co.uk or equivalent for the chosen sport)
  - [ ] Pull raw data into `/data/raw/`, unmodified
  - [ ] Record season coverage and row counts per season in `/docs/data_inventory.md`
- AC: Data covers at least 3 full seasons with no unexplained gap greater than a few matches per season.
- Estimate: M

**`DATA-2`** — As a modeller, I want historical closing odds joined to match results, so I can later check the model against what the market actually priced.
- Sub-tasks:
  - [ ] Source closing odds for the same matches (ideally from more than one bookmaker for later de-vig comparison)
  - [ ] Join odds to match data by date + team pairing
  - [ ] Log join success rate (% of matches successfully matched to odds)
- AC: Join success rate is 95%+ or the shortfall is explained (e.g. odds unavailable for lower-tier matches in early seasons) and documented, not silently dropped.
- Estimate: M

**`DATA-3`** — As a modeller, I want team names normalised across all data sources, so joins don't silently fail on naming mismatches.
- Sub-tasks:
  - [ ] Build a name-mapping table (e.g. "Man Utd" → "Manchester United")
  - [ ] Run the mapping across all sources and log any names that still don't match
  - [ ] Version-control the mapping table so it can be extended as new sources are added
- AC: Zero unmatched team names remain unexplained after mapping is applied.
- Estimate: S

**`DATA-4`** — As a modeller, I want postponed/abandoned/void matches flagged and handled consistently, so they don't corrupt training or feature calculations.
- Sub-tasks:
  - [ ] Identify all non-standard match statuses in the raw data
  - [ ] Decide and document a rule per status (exclude entirely vs. flag and keep for context)
  - [ ] Apply the rule and verify row counts before/after
- AC: A documented rule exists and is applied consistently across the whole dataset; no ad hoc exceptions.
- Estimate: S

**`DATA-5`** — As a modeller, I want a reproducible pipeline from raw source to clean joined dataset, so the whole team can regenerate it identically.
- Sub-tasks:
  - [ ] Turn the manual cleaning steps above into a single runnable script/notebook
  - [ ] Confirm a teammate can run it from scratch and get an identical output
- AC: Running the pipeline twice produces byte-identical (or row-count-identical) output.
- Estimate: M

**Epic DoD:** A single clean, joined dataset exists in `/data/processed/`, is fully reproducible from raw sources, and `/docs/data_inventory.md` documents coverage, join rates, and every handling rule applied.

---

## Epic 2: Feature Engineering
**Goal:** A documented, leakage-checked feature set built only from information available before kickoff.

### Stories

**`FEAT-1`** — As a modeller, I want rolling form features (goals for/against over the last N matches), so recent performance is captured rather than a season-long average that reacts too slowly.
- Sub-tasks:
  - [ ] Implement rolling windows for at least two sizes (e.g. last 5, last 10 matches)
  - [ ] Confirm the window for match *N* only uses matches *before* match *N*
  - [ ] Handle the "start of season" edge case (not enough prior matches yet) with a documented rule
- AC: For a randomly sampled set of 10 matches, manually verify the rolling feature value only reflects strictly prior matches.
- Estimate: M

**`FEAT-2`** — As a modeller, I want home/away performance splits, so home advantage is captured explicitly rather than blended into a general average.
- Sub-tasks:
  - [ ] Compute separate rolling stats for home and away performance
  - [ ] Sanity-check that home stats are systematically stronger than away stats league-wide (a good general signal that the split is working)
- AC: Home vs. away split is visibly different in a summary table across the whole league.
- Estimate: S

**`FEAT-3`** — As a modeller, I want rest-days-since-last-match per team, so fatigue and scheduling congestion are available to the model.
- Sub-tasks:
  - [ ] Calculate days between each team's current and previous match
  - [ ] Flag mid-week/cup-congestion periods if relevant to the chosen league
- AC: Feature values look reasonable on spot-check (e.g. no negative or impossible rest values).
- Estimate: S

**`FEAT-4`** — As a modeller, I want head-to-head history between the two teams, so matchup-specific patterns are captured.
- Sub-tasks:
  - [ ] Compute historical results between the specific pair, using only matches before the one being predicted
  - [ ] Decide and document how far back head-to-head history should count (recency-weighted vs. simple average)
- AC: Feature is populated for all matches with any prior head-to-head history, and correctly empty/null for first-ever meetings.
- Estimate: M

**`FEAT-5`** — As a modeller, I want every feature documented with its source and a "confirmed available before kickoff" justification, so leakage is auditable at any point later in the project.
- Sub-tasks:
  - [ ] Create `/docs/features.md`: feature name, description, data source, pre-kickoff justification
  - [ ] Review the full list as a team specifically hunting for leakage (this review should feel adversarial — actively try to find a feature that's secretly using future information)
- AC: Every feature in the model has a corresponding row in `/docs/features.md`, and the team review explicitly signs off with no unresolved concerns.
- Estimate: M

**`FEAT-6`** — As a modeller, I want the full feature pipeline running end-to-end from clean data to a model-ready feature table, so nothing requires manual steps.
- Sub-tasks:
  - [ ] Combine FEAT-1 through FEAT-4 into a single pipeline
  - [ ] Output one row per match, all features populated, ready for modelling
- AC: Pipeline runs without manual intervention and produces a feature table with no unexplained nulls.
- Estimate: M

**Epic DoD:** Feature pipeline runs end-to-end automatically; `/docs/features.md` is complete; team has done an adversarial leakage review and signed off.

---

## Epic 3: First Model — Poisson / Elo Baseline
**Goal:** A simple, interpretable model producing calibrated probabilities — the foundation everything else is measured against.

### Stories

**`MODEL-1`** — As a modeller, I want team attack/defense strength ratings (Poisson-based), so I can estimate expected goals for any matchup.
- Sub-tasks:
  - [ ] Fit attack and defense ratings per team using historical goals data
  - [ ] Decide on a recency-weighting scheme (recent matches count more) and document the choice
- AC: Ratings produce sensible rankings (strong teams rate higher on attack, weaker defenses rate correctly as "leakier") when spot-checked against known team quality.
- Estimate: L

**`MODEL-2`** — As a modeller, I want the model to output a full scoreline probability distribution, so I can derive any market's probability from it rather than just a single predicted score.
- Sub-tasks:
  - [ ] Combine attack/defense ratings into an expected-goals estimate for each side
  - [ ] Generate a probability for every realistic scoreline (e.g. 0-0 through 5-5)
  - [ ] Derive 1X2 probabilities and Asian Handicap probabilities from the scoreline grid
- AC: Probabilities across all scorelines sum to (approximately) 1; derived 1X2 probabilities are directionally sensible for known lopsided matchups.
- Estimate: L

**`MODEL-3`** — As a modeller, I want an Elo-style rating as an independent second baseline, so I have a sanity check against the Poisson model rather than trusting one method blindly.
- Sub-tasks:
  - [ ] Implement Elo updates match-by-match using only prior results
  - [ ] Decide on K-factor (update sensitivity) and document reasoning
- AC: Elo and Poisson broadly agree on which team is favored in at least 90% of matches; disagreements are logged for manual review, not ignored.
- Estimate: M

**`MODEL-4`** — As a modeller, I want a documented "model card," so the assumptions and limitations of this baseline are explicit and not just living in someone's head.
- Sub-tasks:
  - [ ] Write up: what the model does, key assumptions (e.g. goals follow a Poisson process independently for each side), known limitations (e.g. doesn't account for red cards, injuries mid-match)
- AC: Model card exists in `/docs/` and is understandable by a teammate who didn't build the model.
- Estimate: S

**Epic DoD:** Model runs on the full historical dataset producing probabilities for every match with no errors; Elo/Poisson cross-check completed; model card written.

---

## Epic 4: Backtesting Framework
**Goal:** A framework that measures the model honestly — this is the epic most likely to reveal whether any of this actually works.

### Stories

**`BT-1`** — As a modeller, I want a strict train/test split by season, so no future information leaks into training.
- Sub-tasks:
  - [ ] Define train seasons vs. test season explicitly (chronological, never random shuffling)
  - [ ] Add a hard rule: the test season is not touched, viewed, or used for any tuning decision until the model is fully finalized
- AC: Test season data literally isn't loaded into any notebook until the finalized model is ready to be scored.
- Estimate: S

**`BT-2`** — As a modeller, I want bookmaker odds de-vigged, so I'm comparing against the market's true probability estimate, not its inflated one.
- Sub-tasks:
  - [ ] Implement a de-vig method (e.g. proportional/multiplicative method) on the closing odds
  - [ ] Verify de-vigged probabilities across all outcomes sum to 1
- AC: De-vig calculation verified by hand on at least 5 sample matches.
- Estimate: S

**`BT-3`** — As a modeller, I want flagged "edge" bets identified automatically, so I can evaluate them as a group rather than eyeballing individual matches.
- Sub-tasks:
  - [ ] Define the edge threshold (model probability minus de-vigged market probability, above some minimum gap)
  - [ ] Log every flagged bet with match, market, model prob, market prob, edge size
- AC: Flagged bet list is generated automatically from the test season with zero manual selection.
- Estimate: M

**`BT-4`** — As a modeller, I want fractional Kelly stake sizing applied in the backtest, so simulated results reflect realistic bankroll behaviour rather than flat betting.
- Sub-tasks:
  - [ ] Implement Kelly formula using model probability and offered odds
  - [ ] Apply a fractional multiplier (e.g. 1/4 or 1/2 Kelly) — document which fraction and why
  - [ ] Cap maximum stake size regardless of Kelly output (a sanity ceiling, e.g. never more than 5% even if Kelly suggests more)
- AC: Stake sizes across the backtest never exceed the documented cap; sizing shrinks appropriately as edge shrinks.
- Estimate: M

**`BT-5`** — As a modeller, I want a full backtest report (ROI, CLV, max drawdown, bet count, win rate), so I can judge statistical meaningfulness rather than just a final bankroll number.
- Sub-tasks:
  - [ ] Calculate ROI on stakes, average CLV across flagged bets, max peak-to-trough drawdown, total bets, win rate
  - [ ] Add an automatic flag if ROI exceeds a suspicious threshold (e.g. +10%), prompting a leakage review before any celebration
- AC: Report is generated automatically at the end of a backtest run and saved to `/backtests/` with a timestamp and model version.
- Estimate: M

**`BT-6`** — As a modeller, I want to manually audit a sample of flagged bets, so I catch leakage that automated checks might miss.
- Sub-tasks:
  - [ ] Randomly sample 10–15 flagged bets from the backtest
  - [ ] For each, manually verify that every input used was genuinely available before kickoff
- AC: Audit completed and logged in the decision log; any leakage found is fixed before proceeding to Epic 5.
- Estimate: M

**Epic DoD:** Backtest runs end-to-end on one full season, produces the full report, and passes a manual audit of flagged bets with no leakage found.

---

## Epic 5: Honest Validation
**Goal:** Prove or disprove the model on data it has never influenced in any way — the epic where most projects find out the truth.

### Stories

**`VALID-1`** — As a modeller, I want a pre-registered success threshold, so the bar for "worth paper trading" is decided before results exist, not fitted to whatever the results turn out to be.
- Sub-tasks:
  - [ ] As a team, agree and write down the threshold (e.g. "positive average CLV across 300+ flagged bets spanning two independent holdout seasons")
  - [ ] Log this in `/docs/decisions.md` with a timestamp, before running validation
- AC: Threshold is committed to version control with a date stamp that predates the validation run.
- Estimate: S

**`VALID-2`** — As a modeller, I want the model run on a second, previously untouched holdout season, so I have confirmation beyond a single test set.
- Sub-tasks:
  - [ ] Run the finalized (unmodified) model and backtest framework on the second holdout season
  - [ ] Generate the same report as `BT-5` for this season
- AC: Report generated with zero changes to the model between Epic 4 and this run — same code, new data only.
- Estimate: M

**`VALID-3`** — As a modeller, I want CLV tracked as the primary success metric rather than ROI or win rate alone, so short-term luck isn't mistaken for edge.
- Sub-tasks:
  - [ ] Confirm CLV is calculated consistently across both holdout seasons
  - [ ] Compare CLV trend across the two seasons for consistency
- AC: CLV reported per season and combined, with a plain statement of whether the pre-registered threshold (`VALID-1`) was met.
- Estimate: S

**`VALID-4`** — As a team, we want a documented, honest pass/fail statement, so the project doesn't quietly drift into "well it's probably fine" without a clear decision point.
- Sub-tasks:
  - [ ] Write a short validation summary: threshold, actual result, pass/fail, and what changes (if any) are proposed before re-testing
- AC: Summary committed to `/docs/`, dated, and includes the phrase "fail" plainly if the threshold wasn't met — no euphemisms.
- Estimate: S

**Epic DoD:** Two independent holdout seasons tested against the pre-registered threshold; a plain pass/fail statement is documented, with next steps agreed by the team regardless of outcome.

---

## Epic 6: Paper Trading
**Goal:** Simulate real-time betting with no money on the line, to catch problems backtesting structurally can't.

### Stories

**`PAPER-1`** — As a team, we want the model generating picks on real upcoming fixtures, so it's tested under genuine real-time information constraints.
- Sub-tasks:
  - [ ] Automate (or manually run on a fixed schedule) the model against the current week's fixtures
  - [ ] Pull live odds at the time of the pick, not after the fact
- AC: Picks are generated on a consistent schedule (e.g. same day/time each week) with no missed rounds.
- Estimate: M

**`PAPER-2`** — As a team, we want every pick timestamped before kickoff, so there's no possibility of adjusting a pick after seeing how a match unfolds.
- Sub-tasks:
  - [ ] Log timestamp, odds taken, and model probability at time of pick
  - [ ] Store this in a way that can't be edited after the fact (e.g. append-only log)
- AC: Every logged pick has a timestamp clearly before the match's kickoff time.
- Estimate: S

**`PAPER-3`** — As a team, we want paper trading results logged in the same schema defined in `SETUP-3`, so the transition to live betting requires no rework.
- Sub-tasks:
  - [ ] Confirm paper trading log uses identical fields to the live betting schema
- AC: A paper trading row and a (future) live betting row are structurally identical.
- Estimate: S

**`PAPER-4`** — As a team, we want a running dashboard or weekly summary of CLV/ROI, so trends are visible without waiting until the end of the season.
- Sub-tasks:
  - [ ] Build a simple weekly summary (spreadsheet chart is fine) tracking cumulative CLV, bet count, running ROI
  - [ ] Review it as a team weekly, logging any surprises in the decision log
- AC: Summary is updated and reviewed on a consistent weekly cadence throughout paper trading.
- Estimate: M

**Epic DoD:** A full season (or the team's pre-agreed minimum bet count, e.g. 200+) is paper-traded with timestamped picks, and the final result is compared against the `VALID-1` threshold.

---

## Epic 7: Small Real-Money Test
**Goal:** Validate the model with real stakes, sized so that being wrong doesn't meaningfully hurt.

### Stories

**`LIVE-1`** — As a team, we want a fixed starting bankroll and a hard stake-sizing rule agreed before the first bet, so no single bet or bad stretch can meaningfully damage the bankroll.
- Sub-tasks:
  - [ ] Agree on starting bankroll amount (kept deliberately small)
  - [ ] Agree on fractional Kelly sizing with a hard cap (e.g. never more than 1–2% per bet, regardless of what Kelly suggests)
  - [ ] Write this rule down and get explicit agreement from everyone contributing money
- AC: Stake-sizing rule is documented and signed off by all participants before any bet is placed.
- Estimate: S

**`LIVE-2`** — As a team, we want every live bet logged identically to paper trading, so CLV tracking continues without interruption.
- Sub-tasks:
  - [ ] Confirm live log uses the same schema as `SETUP-3` / `PAPER-3`
- AC: No schema drift between paper and live logs.
- Estimate: S

**`LIVE-3`** — As a team, we want a pre-agreed stop condition, so a bad variance stretch doesn't turn into an emotional decision mid-stream.
- Sub-tasks:
  - [ ] Agree a concrete drawdown threshold (e.g. "pause all betting and review as a team if bankroll drops 30% from peak")
  - [ ] Write down what "review" means — is it a pause-and-analyse, or a full stop?
- AC: Stop condition is numeric, specific, and agreed before betting starts — not left as a vague "we'll know if things go wrong."
- Estimate: S

**`LIVE-4`** — As a team, we want a pre-agreed scale-up condition, so increasing stakes is evidence-based rather than driven by a good week.
- Sub-tasks:
  - [ ] Define the exact bar for scaling (e.g. "only after 500+ combined bets show sustained positive CLV across paper + live")
  - [ ] Agree that a short hot streak alone doesn't qualify
- AC: Scale-up condition is written down with a specific bet-count and CLV bar, agreed before betting starts.
- Estimate: S

**Epic DoD:** Stop and scale conditions are documented and agreed by everyone contributing money *before* the first real bet is placed.

---

## Epic 8: Bankroll & Risk Governance
**Goal:** Formalize the money-management rules so they don't get relitigated (or ignored) once real stakes and real emotions are involved.

### Stories

**`RISK-1`** — As a team, we want a written staking policy, so sizing decisions are mechanical, not discretionary in the moment.
- Sub-tasks:
  - [ ] Document the Kelly fraction used, the hard cap, and how bankroll is recalculated (e.g. weekly, not bet-by-bet, to avoid overreacting to short-term swings)
- AC: Policy is a standalone document any participant can read and apply without asking questions.
- Estimate: S

**`RISK-2`** — As a team, we want a shared understanding of what "the edge disappeared" would look like, so we can tell the difference between normal variance and an actual problem.
- Sub-tasks:
  - [ ] Define a statistical check (e.g. CLV trend over a rolling window) that would trigger a "let's re-examine the model" conversation
- AC: A specific, numeric trigger condition is documented, not just "if it feels like it's not working."
- Estimate: S

**`RISK-3`** — As a team, we want a record-keeping process for tax/legal purposes, so this doesn't become a problem later.
- Sub-tasks:
  - [ ] Confirm the legal status of sports betting in each participant's jurisdiction
  - [ ] Document how winnings/losses will be recorded for tax purposes (rules vary significantly by country)
- AC: Each participant has confirmed their local legal and tax position; this is not left as an assumption.
- Estimate: M

**Epic DoD:** Staking policy, edge-monitoring trigger, and legal/tax process are all documented before Epic 7 begins.

---

## Epic 9: Execution & Multi-Book Logistics
**Goal:** Handle the practical reality that a working model is only useful if you can actually get money down on it.

### Stories

**`EXEC-1`** — As a team, we want accounts at multiple bookmakers, so we can shop for the best available line on any given bet.
- Sub-tasks:
  - [ ] Identify which bookmakers offer the best odds/limits for the target league and market type
  - [ ] Set up accounts under the appropriate participant(s)
- AC: At least 2–3 bookmaker accounts are active and funded at the small test-bankroll level.
- Estimate: M

**`EXEC-2`** — As a team, we want a process for tracking odds across books before placing a bet, so we're not settling for a worse price out of convenience.
- Sub-tasks:
  - [ ] Decide on a manual or semi-automated way to compare current odds across accounts at bet time
- AC: Every logged bet in the live tracking sheet includes which book was used and what the best available alternative price was.
- Estimate: M

**`EXEC-3`** — As a team, we want awareness of account limiting risk, so it doesn't come as a surprise.
- Sub-tasks:
  - [ ] Document that consistently winning accounts often get stake-limited or restricted by bookmakers
  - [ ] Discuss as a team what the plan is if/when this happens (e.g. is this an expected end-state, not a failure?)
- AC: This risk is explicitly written into `/docs/decisions.md` so it's not mistaken for a model problem if/when it happens.
- Estimate: S

**Epic DoD:** Multiple accounts active, line-shopping process in place, and account-limiting risk explicitly acknowledged by the team.

---

## Epic 10: Monitoring & Iteration
**Goal:** Keep the model honest over time — sports markets and team quality both drift, and a model that worked last season isn't guaranteed to keep working.

### Stories

**`MON-1`** — As a team, we want a defined retraining cadence, so the model incorporates new data on a schedule, not ad hoc.
- Sub-tasks:
  - [ ] Decide how often ratings/features are refreshed (e.g. weekly during the season)
  - [ ] Confirm retraining never touches future/unseen fixtures — same leakage discipline as Epic 1–2
- AC: Retraining cadence documented and followed for at least one full cycle without deviation.
- Estimate: M

**`MON-2`** — As a team, we want a way to detect model drift (performance degrading over time), so we catch a declining edge before it costs significant money.
- Sub-tasks:
  - [ ] Track rolling CLV over the trailing N bets, not just cumulative CLV
  - [ ] Set the specific trigger threshold from `RISK-2` into an actual alert (even a manual weekly check counts)
- AC: A rolling CLV chart exists and is checked on the agreed cadence.
- Estimate: M

**`MON-3`** — As a team, we want a lightweight process for testing model changes without repeating the entire validation cycle from scratch every time, so iteration doesn't stall the project indefinitely.
- Sub-tasks:
  - [ ] Define what counts as a "minor tweak" (can be tested on a smaller holdout) vs. a "major change" (requires the full Epic 4–5 process again)
- AC: This distinction is documented so the team doesn't skip validation rigor on changes that actually deserve it.
- Estimate: S

**Epic DoD:** Retraining cadence running, drift monitoring in place, and a documented policy for how much validation rigor any future model change requires.

---

## Appendix A: Metrics Glossary
- **ROI (Return on Investment):** Total profit divided by total amount staked, across a set of bets.
- **CLV (Closing Line Value):** The difference between the odds you got and the odds available at kickoff (closing odds). Consistently beating the closing line is considered a stronger long-run skill signal than short-term win rate.
- **De-vig / de-vigorish:** Removing the bookmaker's built-in margin from odds to get the market's "fair" implied probability.
- **Kelly Criterion:** A staking formula that sizes a bet based on your edge and the odds offered, to maximize long-run bankroll growth. Fractional Kelly (e.g. 1/4 or 1/2) reduces the size to lower variance.
- **Calibration:** Whether predicted probabilities match real-world frequency (e.g. events predicted at 60% should occur close to 60% of the time across many instances).
- **Lookahead bias / leakage:** Accidentally using information in training or features that wouldn't actually have been available before the event being predicted.
- **Overfitting:** A model that has learned the noise/randomness in historical data rather than a real, generalizable pattern — looks great on training data, fails on new data.

## Appendix B: Rough Timeline
| Epic | Rough duration |
|---|---|
| 0 — Setup | 2–3 days |
| 1 — Data Foundation | 2–4 weeks |
| 2 — Feature Engineering | 2–3 weeks |
| 3 — First Model | 2–4 weeks |
| 4 — Backtesting Framework | 2–3 weeks |
| 5 — Honest Validation | Depends on holdout data availability; analysis itself is 1–2 weeks |
| 6 — Paper Trading | 1 full season (real-time, can't be rushed) |
| 7 — Small Real-Money Test | 1 full season minimum |
| 8 — Risk Governance | Runs in parallel with 6–7 |
| 9 — Execution Logistics | 1–2 weeks setup, then ongoing |
| 10 — Monitoring & Iteration | Ongoing indefinitely |

## Appendix C: Risk Register
| Risk | Mitigation |
|---|---|
| Overfitting to historical data | Strict train/test split, adversarial leakage review, suspicion of implausibly high backtest ROI |
| Small sample size (false confidence from short streaks) | Pre-registered thresholds before validation; CLV over raw win rate |
| Account limiting once winning consistently | Multiple accounts, line shopping, treat limiting as an expected end-state |
| Aggressive stake sizing wiping the bankroll during normal variance | Fractional Kelly with a hard cap, agreed stop condition before betting starts |
| Model drift as leagues/teams change over time | Scheduled retraining, rolling CLV monitoring |
| Legal/tax exposure | Confirm jurisdiction rules per participant before real-money betting |
