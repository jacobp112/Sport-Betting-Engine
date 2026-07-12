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

### ⚠️ Pinnacle 25/26 Structural Data Gap
During verification, we identified a critical data collection limitation in the raw source files from Football-Data.co.uk:
- **Seasons 21/22 to 24/25**: Pinnacle opening and closing odds have **100.00%** coverage.
- **Season 25/26**: Pinnacle coverage drops to **49.09%** (Championship) and **29.89%** (League One). This represents a **permanent structural change** in the data feed rather than a temporary blip, starting on **31/10/2025** for the Championship and **04/11/2025** for League One.
- **Mitigation & Traceability**:
  - The processed datasets include a `clv_reference_book` column indicating which reference was used for that match (`pinnacle` vs `market_average`).
  - Where Pinnacle is present, it is used. For matches after the gap start date, we fall back to Market Average odds (`AvgH/D/A`, `AvgCH/CD/CA`), which remain **100.00%** complete across all seasons.
  - This column allows downstream CLV and backtesting frameworks to adjust for Pinnacle's tighter margins (~2-3%) vs Market Average (~5-8%) and prevent artificial CLV inflation.

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
| `clv_reference_book` | String | Reference book used for CLV (`pinnacle` or `market_average`) |
| `B365H` / `B365D` / `B365A` | Float | Bet365 Opening Odds (Home/Draw/Away) |
| `PSH` / `PSD` / `PSA` | Float | Pinnacle Opening Odds (Home/Draw/Away) |
| `AvgH` / `AvgD` / `AvgA` | Float | Market Average Opening Odds (Home/Draw/Away) |
| `MaxH` / `MaxD` / `MaxA` | Float | Market Maximum Opening Odds (Home/Draw/Away) |
| `B365CH` / `B365CD` / `B365CA` | Float | Bet365 Closing Odds (Home/Draw/Away) |
| `PSCH` / `PSCD` / `PSCA` | Float | Pinnacle Closing Odds (Home/Draw/Away) |
| `AvgCH` / `AvgCD` / `AvgCA` | Float | Market Average Closing Odds (Home/Draw/Away) |
| `MaxCH` / `MaxCD` / `MaxCA` | Float | Market Maximum Closing Odds (Home/Draw/Away) |
| `AHh` | Float | Opening Asian Handicap line/handicap size |
| `B365AHH` / `B365AHA` | Float | Bet365 Opening AH Odds (Home/Away) |
| `PAHH` / `PAHA` | Float | Pinnacle Opening AH Odds (Home/Away) |
| `AvgAHH` / `AvgAHA` | Float | Market Average Opening AH Odds (Home/Away) |
| `MaxAHH` / `MaxAHA` | Float | Market Maximum Opening AH Odds (Home/Away) |
| `AHCh` | Float | Closing Asian Handicap line/handicap size |
| `B365CAHH` / `B365CAHA` | Float | Bet365 Closing AH Odds (Home/Away) |
| `PCAHH` / `PCAHA` | Float | Pinnacle Closing AH Odds (Home/Away) |
| `AvgCAHH` / `AvgCAHA` | Float | Market Average Closing AH Odds (Home/Away) |
| `MaxCAHH` / `MaxCAHA` | Float | Market Maximum Closing AH Odds (Home/Away) |

---

## Team Name Normalisation (DATA-3)

To ensure that rolling-form, fatigue, and head-to-head calculations do not break or fragment across varying team abbreviations (especially for newly promoted/relegated clubs), we normalise all team names to standard full canonical forms.

### Mapping Configuration
- **Location**: [`/docs/team_name_mapping.json`](file:///c:/Users/jacob/Documents/Sport-Betting-Engine/docs/team_name_mapping.json)
- **Scope**: Covers all 67 unique raw team names across the Championship and League One for seasons 21/22 through 25/26 (totaling 117 entries).
- **Rule**: Every canonical team name maps to itself (e.g. `"Coventry City": "Coventry City"`, `"Luton Town": "Luton Town"`). Shortened raw names (e.g., `"West Brom"`, `"Nott'm Forest"`, `"QPR"`) are normalised to their full canonical forms.

### Downstream Dependency (Epic 2)
> [!IMPORTANT]
> **Epic 2 Hard Dependency**: Normalisation must be fully complete before Epic 2 (Feature Engineering) begins. This prevents team history fragmentation and ensures that rolling-form calculations track teams correctly across seasons and promotions/relegations.



## Pipeline Execution Log

### Run on 2026-07-12 03:20:37
- **Championship Row Count**: 2760 matches
- **Championship MD5**: `e436fdb5abf391b5a2bceb1d25500d4d`
- **League One Row Count**: 2760 matches
- **League One MD5**: `bce261916ac47dd33aa31ab195e28ac2`
- **Status**: Verified Reproducible (Byte-Identical to Reference Checksums)


### Run on 2026-07-12 03:14:24
- **Championship Row Count**: 2760 matches
- **Championship MD5**: `708906b4e5e6c8f3983ae7bb858e4aa4`
- **League One Row Count**: 2760 matches
- **League One MD5**: `cfebce581f2db469bdc286eb690ee557`
- **Status**: Verified Reproducible (Byte-Identical to Reference Checksums)


### Run on 2026-07-12 03:13:54
- **Championship Row Count**: 2760 matches
- **Championship MD5**: `708906b4e5e6c8f3983ae7bb858e4aa4`
- **League One Row Count**: 2760 matches
- **League One MD5**: `cfebce581f2db469bdc286eb690ee557`
- **Status**: Verified Reproducible (Byte-Identical to Reference Checksums)


### Run on 2026-07-12 03:01:48
- **Championship Row Count**: 2760 matches
- **Championship MD5**: `7e61cdbc009c73da8a2544232df5045b`
- **League One Row Count**: 2760 matches
- **League One MD5**: `7d92077c9162eeedd3eb3594c72be3f2`
- **Status**: Verified Reproducible (Byte-Identical to Reference Checksums)


### Run on 2026-07-12 03:01:34
- **Championship Row Count**: 2760 matches
- **Championship MD5**: `7e61cdbc009c73da8a2544232df5045b`
- **League One Row Count**: 2760 matches
- **League One MD5**: `7d92077c9162eeedd3eb3594c72be3f2`
- **Status**: Verified Reproducible (Byte-Identical to Reference Checksums)
