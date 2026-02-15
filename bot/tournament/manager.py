from __future__ import annotations
import asyncio
from typing import Dict, Any
from bot.tournament.variant import StrategyVariant

class TournamentManager:
    def __init__(self, base_cfg: Dict[str, Any]):
        self.base_cfg = base_cfg
    async def run(self):
        tcfg = self.base_cfg.get("tournament", {})
        variants_cfg = tcfg.get("variants", [])
        max_parallel = int(tcfg.get("max_parallel", len(variants_cfg) or 1))
        sem = asyncio.Semaphore(max_parallel)
        variants = [StrategyVariant(self.base_cfg, v) for v in variants_cfg]
        async def _run(v):
            async with sem:
                await v.start()
        await asyncio.gather(*[_run(v) for v in variants])
