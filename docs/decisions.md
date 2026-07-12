# Decision Log

This log tracks all major architectural, statistical, modelling, and operational decisions made throughout the lifecycle of the project.

| Date | Decision | Reasoning | Alternatives Considered | Decided By |
| :--- | :--- | :--- | :--- | :--- |
| 2026-07-12 | Project initialization, directories, and documentation setup (Epic 0). | Establish a clear, structured repository layout and document communication/role guidelines before starting data ingestion to ensure project reproducibility and traceability. | None. Standard best practice for project onboarding. | Jacob |
| 2026-07-12 | Target League selection: English Football League (EFL) Championship. | Leverage domain knowledge (team quality, transfer news, injury context), gain a larger sample size (552 matches/season vs. EPL's 380) for backtesting and paper trading, and exploit less modeled/attention-heavy markets where bookmakers put less pricing effort. | English Premier League (EPL), NBA (Basketball), NFL (American Football). | Jacob |
| 2026-07-12 | Ingest League One (E2) historical data alongside Championship (E1). | Championship has heavy promotion/relegation turnover (3 teams per season). Downloading League One data upfront allows rolling-form and head-to-head features (FEAT-1/FEAT-4) to use cross-league history for newly promoted sides instead of nulling them out. | Null out features for newly promoted teams at start of season. | Jacob |
