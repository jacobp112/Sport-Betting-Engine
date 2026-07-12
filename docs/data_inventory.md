# Data Inventory

This document tracks the raw datasets ingested into the `/data/raw/` directory and the verified/cleaned datasets in `/data/processed/`, including coverage, odds join rates, and metadata.

---

## Data Sources
- **Source**: [Football-Data.co.uk](https://www.football-data.co.uk)
- **Leagues**: EFL Championship (E1), EFL League One (E2)
- **Coverage**: 5 seasons (2021/2022 to 2025/2026)

---

## Raw Data Inventory

| League | Season | File Name | Matches | Expected | Shortfall Reason |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Championship | 2122 | `championship_2122.csv` | 552 | 552 | None |
| Championship | 2223 | `championship_2223.csv` | 552 | 552 | None |
| Championship | 2324 | `championship_2324.csv` | 552 | 552 | None |
| Championship | 2425 | `championship_2425.csv` | 552 | 552 | None |
| Championship | 2526 | `championship_2526.csv` | 552 | 552 | None |
| League One | 2122 | `league_one_2122.csv` | 552 | 552 | None |
| League One | 2223 | `league_one_2223.csv` | 552 | 552 | None |
| League One | 2324 | `league_one_2324.csv` | 552 | 552 | None |
| League One | 2425 | `league_one_2425.csv` | 552 | 552 | None |
| League One | 2526 | `league_one_2526.csv` | 552 | 552 | None |

### Raw Gap Verification
- All files contain exactly 552 matches per season. No shortfalls detected. Data is fully complete without unexplained gaps (meets DATA-1 AC).

---

## Odds Verification and Join Rates (DATA-2)

We verified the availability of opening and closing odds across Pinnacle, Bet365, Market Average, and Market Maximum.
Pinnacle serves as the primary sharp reference for de-vigging and has a strict 95%+ coverage requirement.

| League | Total Matches | Pinnacle Opening | Pinnacle Closing | Bet365 Opening | Bet365 Closing | Market Avg Opening | Market Avg Closing | Market Max Opening | Market Max Closing |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Championship | 2760 | 89.42% | 89.82% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |
| League One | 2760 | 85.98% | 85.98% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% | 100.00% |

### ⚠️ Pinnacle 25/26 Data Limitation
During verification, we identified a critical data collection limitation in the raw source files from Football-Data.co.uk:
- **Seasons 21/22 to 24/25**: Pinnacle opening and closing odds have **100.00%** coverage.
- **Season 25/26**: Pinnacle coverage drops to **49.09%** (Championship) and **29.89%** (League One) due to scraping failures/omissions at the source from late October 2025 onwards.
- **Mitigation**: Bet365, Market Average, and Market Maximum are **100.00%** populated across all seasons (including 25/26). Downstream de-vigging in Epic 4 will fall back to Market Average odds (`AvgH/D/A`, `AvgCH/CD/CA`) for matches where Pinnacle odds are missing, ensuring no training data is lost.

---

## Processed Dataset Details

Processed data is stored chronologically in:
- `data/processed/championship.csv`
- `data/processed/league_one.csv`

### Column Descriptions

| Column Name | Type | Description |
| :--- | :--- | :--- |
| `Div` | String | Division code (`E1` = Championship, `E2` = League One) |
| `Date` | Date (YYYY-MM-DD) | Standardised ISO date |
| `Time` | Time (HH:MM) | Kick-off time |
| `HomeTeam` | String | Home team name |
| `AwayTeam` | String | Away team name |
| `FTHG` | Integer | Full-time home goals |
| `FTAG` | Integer | Full-time away goals |
| `FTR` | String | Full-time result (`H` = Home win, `D` = Draw, `A` = Away win) |
| `season` | String | Season identifier (e.g., `2122`, `2223`, etc.) |
| `B365H` / `B365D` / `B365A` | Float | Bet365 Opening Odds (Home/Draw/Away) |
| `PSH` / `PSD` / `PSA` | Float | Pinnacle Opening Odds (Home/Draw/Away) |
| `AvgH` / `AvgD` / `AvgA` | Float | Market Average Opening Odds (Home/Draw/Away) |
| `MaxH` / `MaxD` / `MaxA` | Float | Market Maximum Opening Odds (Home/Draw/Away) |
| `B365CH` / `B365CD` / `B365CA` | Float | Bet365 Closing Odds (Home/Draw/Away) |
| `PSCH` / `PSCD` / `PSCA` | Float | Pinnacle Closing Odds (Home/Draw/Away) |
| `AvgCH` / `AvgCD` / `AvgCA` | Float | Market Average Closing Odds (Home/Draw/Away) |
| `MaxCH` / `MaxCD` / `MaxCA` | Float | Market Maximum Closing Odds (Home/Draw/Away) |
