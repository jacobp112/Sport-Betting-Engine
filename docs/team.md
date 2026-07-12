# Team Roles & Review Process

This document defines roles, responsibilities, review workflows, and communication policies for the project.

---

## 👥 Roles & Responsibilities

| Role | Owner | Key Responsibilities |
| :--- | :--- | :--- |
| **Data & Infrastructure** | Jacob | Ingesting raw match/odds data, cleaning datasets, maintaining features pipeline, folder organization. |
| **Modelling** | Jacob | Building ratings models (Poisson, Elo), fitting parameters, developing the predictor. |
| **Validation & Risk** | Jacob | Structuring train/test splits, running backtests, verifying de-vigging, enforcing risk thresholds, monitoring bankroll. |

---

## 🔍 Self-Review & Merging Process

1. **Review Policy**: To maintain high standards, every story must undergo a self-review before being closed. Particular focus is placed on:
   - Sanity-checking manual inputs, code edits, and configurations.
   - Performing an adversarial leakage review (e.g., in Epic 2).
2. **Definition of Done (DoD) Checks**: Before closing any story, verify:
   - No lookahead bias or data leakage.
   - Any non-obvious decision is documented in `/docs/decisions.md`.
   - Results (metrics, ROI, etc.) are written down.

---

## 📅 Meeting & Review Cadence

* **Frequency:** Weekly or at the end of each Epic (whichever is more frequent).
* **Agenda:**
  1. Review status of the current Epic.
  2. Audit and update `/docs/decisions.md`.
  3. Inspect any new findings, feature distributions, or model metrics.
  4. Align on the goal/plan for the next Epic.
