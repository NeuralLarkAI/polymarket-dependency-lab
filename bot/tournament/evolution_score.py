from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any

@dataclass(frozen=True)
class Score:
    ok: bool
    value: float
    reason: str

def compute_score(summary: Dict[str, Any], objective: Dict[str, float], constraints: Dict[str, Any]) -> Score:
    fills = int(summary.get("fills", 0))
    equity = float(summary.get("equity", 0.0))
    dd = float(summary.get("max_drawdown_pct", 1.0))
    sharpe_low = float(summary.get("sharpe_low", summary.get("sharpe_like", 0.0)))
    sharpe_high = float(summary.get("sharpe_high", summary.get("sharpe_like", 0.0)))
    n_low = int(summary.get("points_low", 0))
    n_high = int(summary.get("points_high", 0))
    regime_ok = bool(summary.get("regime_ok", False))

    if fills < int(constraints.get("min_fills", 0)):
        return Score(False, -1e9, "min_fills")
    if dd > float(constraints.get("max_drawdown_pct", 1.0)):
        return Score(False, -1e9, "drawdown")
    if equity <= 0:
        return Score(False, -1e9, "equity")

    if bool(constraints.get("regime_required", False)):
        min_each = int(constraints.get("min_points_each_regime", 0))
        if not regime_ok or n_low < min_each or n_high < min_each:
            return Score(False, -1e9, "regime")

    wS = float(objective.get("w_sharpe", 1.0))
    wE = float(objective.get("w_equity", 0.0))
    wD = float(objective.get("w_drawdown", 0.0))
    wF = float(objective.get("w_fills", 0.0))

    blend = 0.55 * sharpe_high + 0.45 * sharpe_low
    eq_component = (equity - 1000.0) / 1000.0
    fills_component = min(1.0, fills / 50.0)
    val = (wS * blend) + (wE * eq_component) - (wD * dd) + (wF * fills_component)
    return Score(True, val, "ok")
