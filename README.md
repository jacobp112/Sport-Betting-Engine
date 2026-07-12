# Sports Betting Model Engine

A statistical modelling and simulation engine for sports betting, designed to build, validate, backtest, and run a predictive model.

---

## 🎯 Target Sport & League
* **Sport:** Football (Soccer)
* **League:** English Football League (EFL) Championship

---

## 🚦 Current Project Phase
We are currently starting **Epic 2: Feature Engineering**. 

### Phase Timeline & Progress
- [x] **Epic 0: Project Setup & Team Workflow** — *Completed*
  - Repository structure initialized.
  - Decision logs, roles, and bet-tracking schemas established.
- [x] **Epic 1: Data Foundation** — *Completed*
  - Historical data ingested, cleaned, and verified (opening & closing 1X2 and AH odds).
  - Version-controlled team normalisation mapping established.
  - Deterministic data pipeline entrypoint created with automated checksum checks.
- [ ] **Epic 2: Feature Engineering** — *Current Phase*
- [ ] **Epic 3: First Model — Poisson / Elo Baseline** — *Not Started*
- [ ] **Epic 4: Backtesting Framework** — *Not Started*
- [ ] **Epic 5: Honest Validation** — *Not Started*
- [ ] **Epic 6: Paper Trading** — *Not Started*
- [ ] **Epic 7: Small Real-Money Test** — *Not Started*
- [ ] **Epic 8: Bankroll & Risk Governance** — *Not Started*
- [ ] **Epic 9: Execution & Multi-Book Logistics** — *Not Started*
- [ ] **Epic 10: Monitoring & Iteration** — *Not Started*

---

## 📂 Repository Structure
```text
/data          → raw + cleaned historical data (raw/ and processed/ subfolders)
/notebooks     → exploration, one-off analysis
/src           → reusable pipeline code (features, model, backtester)
/backtests     → saved results per model version, named by date + model version
/docs          → roadmap, model cards, decision log, metrics glossary
/logs          → paper trading and live betting logs
```

---

## ⚙️ How to Reproduce the Pipeline

The data ingestion, validation, and team name normalisation are fully integrated into a single deterministic master script.

### 1. Prerequisites
- Python 3.13.0 (pinned via `.python-version`)

### 2. Setup
Create a virtual environment:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Run the Data Pipeline
Run the master pipeline script to process the datasets:
```bash
# Execute entire pipeline (downloads raw files, cleans results/odds, normalises team names, verifies checksums)
python scripts/run_pipeline.py

# Offline mode (reprocesses cached raw files without hitting football-data.co.uk)
python scripts/run_pipeline.py --skip-download
```

Output datasets will be written atomically to `data/processed/championship.csv` and `data/processed/league_one.csv`. The script will calculate MD5 checksums of the output files and assert them against `data/processed/checksums.txt` to guarantee byte-identical reproduction.

