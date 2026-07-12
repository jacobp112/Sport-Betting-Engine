# Sports Betting Model Engine

A statistical modelling and simulation engine for sports betting, designed to build, validate, backtest, and run a predictive model.

---

## 🎯 Target Sport & League
* **Sport:** Football (Soccer)
* **League:** English Football League (EFL) Championship

---

## 🚦 Current Project Phase
We are currently in **Epic 1: Data Foundation**. 

### Phase Timeline & Progress
- [x] **Epic 0: Project Setup & Team Workflow** — *Completed*
  - Repository structure initialized.
  - Decision logs, roles, and bet-tracking schemas established.
- [ ] **Epic 1: Data Foundation** — *Not Started*
- [ ] **Epic 2: Feature Engineering** — *Not Started*
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
*(Detailed setup instructions will be updated as the pipeline is developed.)*

### 1. Prerequisites
- python 3.10+
- virtualenv

### 2. Setup
Create a virtual environment and install dependencies:
```bash
python -m venv venv
venv\Scripts\activate
# Dependencies will be added in Epic 1
```

### 3. Run Pipeline
To download raw data, clean it, and run feature engineering:
```bash
# Script entrypoints will be implemented in Epic 1 and 2
```
