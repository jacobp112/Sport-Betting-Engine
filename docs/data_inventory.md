# Data Inventory

This document tracks the raw datasets ingested into the `/data/raw/` directory, including their sources, row counts, and any identified gaps.

## Data Sources
- **Source**: [Football-Data.co.uk](https://www.football-data.co.uk)
- **Leagues**: EFL Championship (E1), EFL League One (E2)
- **Coverage**: 5 seasons (2021/2022 to 2025/2026)

> [!IMPORTANT]
> **Odds Data (DATA-2 Context)**: The CSV files from Football-Data.co.uk bundle match results and odds together in the same file.
> Odds columns present: Bet365 (B365H, B365D, B365A), Pinnacle (PSCH, PSCD, PSCA), and Asian Handicap lines. 
> **DATA-2 action:** Verify and extract these columns; do not re-source odds from elsewhere as they are already satisfied by this download.

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

## Gap Verification
- All files assert exactly 552 matches per season.
- No shortfalls detected. Data is fully complete without any unexplained gaps (meets DATA-1 AC).
