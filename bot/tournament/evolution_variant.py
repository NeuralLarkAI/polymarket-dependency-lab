from __future__ import annotations
from copy import deepcopy
from typing import Dict, Any
from bot.tournament.evolution_genome import Genome

def apply_genome(base_cfg: Dict[str, Any], g: Genome, *, tag: str) -> Dict[str, Any]:
    cfg = deepcopy(base_cfg)
    cfg["mode"] = "paper"
    cfg.setdefault("dependency", {})
    cfg["dependency"]["trigger_move_pct"] = float(g.dependency_shift_pct)
    cfg["dependency"]["min_gap_pct"] = float(g.min_gap_pct)
    cfg.setdefault("dependency", {}).setdefault("linear", {})
    cfg["dependency"]["linear"]["beta"] = float(g.beta)
    cfg["dependency"]["linear"]["intercept"] = float(g.intercept)
    cfg.setdefault("news", {}).setdefault("sentiment_weight", {})["multiplier"] = float(g.sentiment_weight)
    cfg.setdefault("paper", {})["slippage_bps"] = float(g.slippage_bps)
    cfg.setdefault("paper", {}).setdefault("micro", {}).setdefault("advsel", {})["k_bps_per_vol"] = float(g.adv_k_bps_per_vol)
    cfg.setdefault("paper", {}).setdefault("runs", {})["enabled"] = True
    cfg["paper"]["runs"]["tag"] = tag
    return cfg
