# Bet Tracking Schema

This document defines the schema for recording simulated (paper trading) and real-money bets. A consistent format is critical to ensure that downstream metrics calculations (ROI, CLV, Drawdown) remain correct and simple to compute.

---

## 💾 Storage Configuration
* **Location:** `/logs/bet_tracker.csv` (and `/logs/paper_tracker.csv` for paper trading).
* **Write Access:** Jacob (and automated logging scripts).

---

## 📋 Schema Definition

| Field Name | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `date` | String (YYYY-MM-DD) | Date of the match. | `2026-08-15` |
| `competition` | String | League or competition name. | `EFL Championship` |
| `match` | String | Home Team vs Away Team. | `Leeds vs Coventry` |
| `market` | String | The betting market (e.g., 1X2, Over/Under 2.5, Asian Handicap). | `1X2` |
| `side` | String | The specific outcome bet on (e.g., Home, Away, Draw, Over, Under). | `Home` |
| `odds_taken` | Float | Decimal odds obtained at the time the bet was placed. | `1.85` |
| `bookmaker` | String | The bookmaker where the bet was placed. | `Bet365` |
| `closing_odds` | Float | The final decimal odds offered by the same bookmaker at kickoff. | `1.78` |
| `stake` | Float | The amount of money (or units) bet. | `100.00` |
| `stake_pct_bankroll` | Float | The stake size expressed as a percentage of the total current bankroll. | `1.5` |
| `model_probability` | Float | The probability estimated by the model for this side (0.0 to 1.0). | `0.58` |
| `devig_market_probability` | Float | The market probability estimated by removing the bookmaker's margin. | `0.54` |
| `result` | String | Outcome of the bet: `WIN`, `LOSS`, `VOID`, `HALF-WIN`, `HALF-LOSS`. | `WIN` |
| `profit_loss` | Float | Net profit or loss from the bet (Return - Stake). | `85.00` |
| `CLV` | Float | Closing Line Value, calculated as: `(odds_taken / closing_odds) - 1`. | `0.0393` |

---

## 📝 Test Row Example

To verify fields and avoid ambiguity:
```csv
date,competition,match,market,side,odds_taken,bookmaker,closing_odds,stake,stake_pct_bankroll,model_probability,devig_market_probability,result,profit_loss,CLV
2026-08-15,EFL Championship,Leeds vs Coventry,1X2,Home,1.85,Bet365,1.78,100.00,1.5,0.58,0.54,WIN,85.00,0.0393
```
