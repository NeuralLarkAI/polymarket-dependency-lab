from __future__ import annotations
from dataclasses import dataclass, asdict
import random
from typing import Dict, Any

def _u(rng: random.Random, lo: float, hi: float) -> float:
    return lo + (hi - lo) * rng.random()

def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))

@dataclass
class Genome:
    dependency_shift_pct: float
    min_gap_pct: float
    beta: float
    intercept: float
    sentiment_weight: float
    slippage_bps: float
    adv_k_bps_per_vol: float
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def random_genome(rng: random.Random, space: Dict[str, list]) -> Genome:
    return Genome(
        dependency_shift_pct=_u(rng, *space["dependency_shift_pct"]),
        min_gap_pct=_u(rng, *space["min_gap_pct"]),
        beta=_u(rng, *space["beta"]),
        intercept=_u(rng, *space["intercept"]),
        sentiment_weight=_u(rng, *space["sentiment_weight"]),
        slippage_bps=_u(rng, *space["slippage_bps"]),
        adv_k_bps_per_vol=_u(rng, *space["adv_k_bps_per_vol"]),
    )

def crossover(rng: random.Random, a: Genome, b: Genome) -> Genome:
    def pick(x, y): return x if rng.random() < 0.5 else y
    return Genome(
        dependency_shift_pct=pick(a.dependency_shift_pct, b.dependency_shift_pct),
        min_gap_pct=pick(a.min_gap_pct, b.min_gap_pct),
        beta=pick(a.beta, b.beta),
        intercept=pick(a.intercept, b.intercept),
        sentiment_weight=pick(a.sentiment_weight, b.sentiment_weight),
        slippage_bps=pick(a.slippage_bps, b.slippage_bps),
        adv_k_bps_per_vol=pick(a.adv_k_bps_per_vol, b.adv_k_bps_per_vol),
    )

def mutate(rng: random.Random, g: Genome, space: Dict[str, list], rate: float = 0.25, strength: float = 0.20) -> Genome:
    d = g.to_dict()
    for k, bounds in space.items():
        lo, hi = bounds
        if rng.random() > rate:
            continue
        span = hi - lo
        jump = (rng.random() - 0.5) * 2.0 * strength * span
        d[k] = _clip(float(d[k]) + jump, lo, hi)
    return Genome(**d)
