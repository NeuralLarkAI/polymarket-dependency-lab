from __future__ import annotations
from dataclasses import dataclass
import asyncio, random

@dataclass(frozen=True)
class LatencyProfile:
    base_ms: int
    jitter_ms: int
    tail_prob: float
    extra_tail_ms: int
    drop_prob: float

class RegionLatency:
    def __init__(self, profiles: dict[str, LatencyProfile], region: str):
        self.profiles = profiles
        self.region = region
    def _p(self) -> LatencyProfile:
        return self.profiles.get(self.region) or LatencyProfile(150,45,0.08,250,0.01)
    async def wait(self) -> tuple[bool, float]:
        p = self._p()
        if random.random() < p.drop_prob:
            return (False, 0.0)
        jitter = random.randint(-p.jitter_ms, p.jitter_ms) if p.jitter_ms else 0
        ms = max(0, p.base_ms + jitter)
        if random.random() < p.tail_prob:
            ms += p.extra_tail_ms
        sec = ms / 1000.0
        await asyncio.sleep(sec)
        return (True, sec)
