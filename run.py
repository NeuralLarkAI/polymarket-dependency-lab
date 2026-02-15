from __future__ import annotations
import asyncio
import yaml
from pathlib import Path

def load_config(path: str = "config.yaml") -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError("config.yaml not found. Copy config.example.yaml to config.yaml")
    return yaml.safe_load(p.read_text(encoding="utf-8"))

async def main():
    cfg = load_config()

    if cfg.get("evolution", {}).get("enabled", False):
        from bot.tournament.evolution_manager import EvolutionManager
        await EvolutionManager(cfg).run()
        return

    if cfg.get("tournament", {}).get("enabled", False):
        from bot.tournament.manager import TournamentManager
        await TournamentManager(cfg).run()
        return

    from bot.app import App
    await App(cfg).run()

if __name__ == "__main__":
    asyncio.run(main())
