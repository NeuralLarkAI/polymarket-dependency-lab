from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class AdvSelConfig:
    k_bps_per_vol: float = 18.0
    max_extra_bps: float = 80.0
    liquidity_shrink_per_vol: float = 0.35
    max_liquidity_shrink: float = 0.75

@dataclass(frozen=True)
class AdvSelPenalty:
    extra_slippage_bps: float
    liquidity_shrink: float

def compute_advsel_penalty(abs_move_pct: float, cfg: AdvSelConfig) -> AdvSelPenalty:
    vol_pct = abs_move_pct * 100.0
    extra_bps = min(cfg.max_extra_bps, cfg.k_bps_per_vol * vol_pct)
    shrink = min(cfg.max_liquidity_shrink, cfg.liquidity_shrink_per_vol * vol_pct)
    return AdvSelPenalty(extra_slippage_bps=extra_bps, liquidity_shrink=shrink)
