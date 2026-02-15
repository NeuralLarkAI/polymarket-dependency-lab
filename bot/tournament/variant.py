from __future__ import annotations
from copy import deepcopy
from typing import Dict, Any

class StrategyVariant:
    def __init__(self, base_cfg: Dict[str, Any], variant_cfg: Dict[str, Any]):
        self.name = variant_cfg["name"]
        self.cfg = deepcopy(base_cfg)
        self.cfg.setdefault("dependency", {})
        self.cfg["dependency"]["trigger_move_pct"] = float(variant_cfg.get("dependency_shift_pct", self.cfg["dependency"].get("trigger_move_pct", 0.03)))
        self.cfg.setdefault("news", {}).setdefault("sentiment_weight", {})["multiplier"] = float(variant_cfg.get("sentiment_weight", 0.6))
        self.cfg.setdefault("execution", {})["max_exposure_pct"] = float(variant_cfg.get("max_exposure_pct", 0.02))
        self.cfg.setdefault("paper", {}).setdefault("runs", {})["tag"] = f"paper-{self.name}"
    async def start(self):
        from bot.app import App
        await App(self.cfg).run()
