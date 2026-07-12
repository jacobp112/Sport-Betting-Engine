# Project Status Log

This file is updated at the end of each Epic with a brief summary of what is true now and what changed.

---

### Epic 0: Project Setup & Team Workflow (Completed: 2026-07-12)
**Status:** Ready for Epic 1.
The initial repository structure has been established with standard directories for data, notebooks, source code, backtests, documentation, and logs. Key team workflow assets are in place, including the team roles definition (`/docs/team.md`), the decision log template (`/docs/decisions.md`), and the shared bet-tracking schema (`/docs/bet_tracking_schema.md`). The target league has been chosen as the English Football League (EFL) Championship. We are now fully prepared to begin Epic 1 (Data Foundation).

### Epic 1: Data Foundation (Completed: 2026-07-12)
**Status:** Ready for Epic 2.
We have successfully completed the data foundation phase. Historical match and odds data for the EFL Championship and League One across 5 full seasons (21/22 - 25/26) has been ingested, validated, and processed. The pipeline handles missing Pinnacle odds gracefully by soft-nulling and logging, enforces strict data validation (plausible goal range, cross-field FTR consistency, duplicate checks), and normalises all team names to standard canonical full names via a JSON map. A master script (`scripts/run_pipeline.py`) executes the end-to-end pipeline atomically and verifies byte-identical reproducibility using MD5 checksum assertions against a reference file. All raw and processed datasets are snapshot in version control.

