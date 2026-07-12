# Match Status & Data Validation Rules

This document defines the rules, validation policies, and edge-case handling for ingestion and cleaning of match results. 

---

## 🚦 Distinction Between Missing Results and Missing Odds

We enforce two distinct severity levels for missing data to balance model training sample size against pipeline execution safety:

1. **Missing Results (Hard Exclusion)**
   - **Trigger**: Any match missing full-time goals (`FTHG`/`FTAG`), containing non-numeric goals, goals outside the plausible range (0–15), or having an inconsistent full-time result (`FTR`).
   - **Action**: Skip and exclude the row entirely from the processed dataset.
   - **Reasoning**: A missing or corrupt result makes the match entirely unusable for training, backtesting, and feature calculations.

2. **Missing Odds (Soft Nulling)**
   - **Trigger**: Any match where specific bookmaker odds (e.g. Pinnacle `PSCH/CD/CA` or Bet365 `B365H/D/A`) are missing.
   - **Action**: Set the odds fields to null (`""`), but **retain the match result**.
   - **Reasoning**: A missing odds field does not invalidate the match result. The match remains 100% usable for team strength ratings (Poisson/Elo) and feature engineering. For backtesting and de-vigging in Epic 4/5, we can dynamically fallback to other bookmakers or the Market Average.

---

## 🔍 Validation Checks Applied
The `/scripts/process_data.py` script automatically runs the following verification rules for each row:

* **Plausible Goal Range Check**: Asserts that Home and Away goals are non-negative integers between `0` and `15` inclusive. Any value outside this range (or non-numeric text) is flagged and the match is skipped.
* **Cross-field Consistency Check**: Validates that `FTR` aligns perfectly with the goal difference:
  - If `FTHG > FTAG`, `FTR` must be `H`.
  - If `FTHG < FTAG`, `FTR` must be `A`.
  - If `FTHG == FTAG`, `FTR` must be `D`.
  If a row contains a contradiction (e.g. `FTHG=2, FTAG=1, FTR='D'`), it is skipped.
* **Duplicate Row Check**: Tracks seen matches using a tuple of `(HomeTeam, AwayTeam, Date)`. If a duplicate is detected, it logs a warning and skips the duplicate row.
* **Chronological Order Enforcement**: The processed datasets are sorted chronologically by `Date` and `Time` to ensure sequential logic and prevent lookahead bias.
* **Formulaic Count Verification**: Dynamically asserts the total processed match count matches the formula `552 * completed_seasons` (552 = 24 teams × 46 matches / 2).

---

## ⚠️ Downstream Feature Engineering Impact of Match Exclusions
If a match is excluded from the processed dataset:
- **Rest-Days Feature**: Excluding a match changes the elapsed time since a team's last played match, which will artificially inflate their calculated rest days for the *subsequent* fixture.
- **Rolling Form Feature**: Excluding a match removes a performance record, meaning rolling form (e.g. goals scored in the last 5 matches) will look back further in calendar time than intended.
- **Action Policy**: If any future validation rule drops a match, the data pipeline will print a stdout `WARNING` describing the exact match dropped. As a modeling owner, you must perform a manual sanity check on features in the subsequent weeks to ensure this does not introduce bias.
