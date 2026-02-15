# Polymarket Dependency Lab + Control Tower (MVP Bundle)

A research-grade prediction-market trading lab with:
- Multi-market monitoring with **LIVE Polymarket data** via py-clob-client
- Dependency trigger → fair value → mispricing gap → FOK depth-aware execution
- Paper trading realism: latency + adverse selection + L2 depth
- Runs folder artifacts: equity, fills, attempts, summary, meta
- Evolutionary optimizer (walk-forward + market-vol balanced folds)
- Control Tower UI (FastAPI + Next.js) to start/stop bot + view runs

## Quick start

### Important: Configure Live Markets First!
Before running the bot, you need to update `config.yaml` with real Polymarket market token IDs.
See `docs/FINDING_MARKETS.md` for instructions on finding active markets.

### 1) Backend + bot
```bash
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp config.example.yaml config.yaml

# IMPORTANT: Edit config.yaml and update the market token IDs!
# See docs/FINDING_MARKETS.md for help

python run.py
```

### 2) Control Tower backend
```bash
cd control_tower/backend
uvicorn app:app --reload --port 8000
```

### 3) Control Tower frontend
```bash
cd control_tower/frontend
pnpm install
pnpm dev
```

Open:
- Frontend: http://localhost:3000
- Backend:  http://localhost:8000

## Claude instructions
See: `docs/CLAUDE_INSTRUCTIONS.md`
