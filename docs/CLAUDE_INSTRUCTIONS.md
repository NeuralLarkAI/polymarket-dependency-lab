# Instructions for Claude AI

You are continuing development of **Polymarket Dependency Lab + Control Tower**.

## Goal
Build a system that finds **conditional dependencies** between Polymarket markets and trades mispricing gaps with realistic paper simulation and an optimizer (evolution + Bayesian fine-tune).

## What's already implemented in this bundle (MVP)
- `bot/app.py`: runnable mock feed → dependency triggers → FOK fills vs depth → logs artifacts.
- `bot/paper/*`: broker, L2 book, depth FOK fill, latency model, adverse selection penalty, run folder manager, performance summary.
- `bot/tournament/*`: tournament manager + evolutionary optimizer (population search) + simple walk-forward scoring + market-vol balanced fold picker.
- `control_tower/*`: FastAPI endpoints to start/stop bot and list runs; Next.js UI to view runs.

## What to implement next (priority)
1) Replace mock feed with real Polymarket CLOB:
   - Use py-clob-client for REST + WS
   - Parse WS book deltas/snapshots into `WSL2BookStore`
   - Maintain Top-of-Book updates for each market

2) Add real market mapping:
   - config lists Polymarket markets (condition IDs / token IDs) and pairing sets
   - dynamic cluster discovery (cross-correlation + lead/lag)

3) Improve dependency fair value:
   - regression fit on rolling window
   - cointegration / error-correction style signal
   - confidence weighting + minimum liquidity gates

4) Control Tower:
   - stream live events to frontend (WS)
   - show equity chart (read CSV), fills table, attempts table
   - ability to start evolution mode and view evolution results

## Non-negotiables (keep stable)
- Runs folder format:
  - `equity_timeseries.csv`
  - `paper_fills.csv`
  - `order_attempts.csv`
  - `performance_summary.json`
  - `run_meta.json`
- Evolution outputs in `runs/evolution/*.json`
- `tools/leaderboard.py` and `tools/paper_report.py` should keep working.
