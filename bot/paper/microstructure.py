from __future__ import annotations
from dataclasses import dataclass
from collections import deque
from typing import Deque, Optional
from bot.types import TopOfBook

@dataclass(frozen=True)
class MicroSnapshot:
    ts: float
    mid: float

@dataclass(frozen=True)
class MicroStats:
    window_sec: float
    start_mid: float
    end_mid: float
    abs_move_pct: float
    signed_move_pct: float
    updates: int

class MicrostructureTracker:
    def __init__(self, maxlen: int = 5000):
        self._buf: Deque[MicroSnapshot] = deque(maxlen=maxlen)
    def on_tob(self, tob: TopOfBook):
        mid = tob.midpoint
        if mid is None: return
        self._buf.append(MicroSnapshot(ts=tob.ts, mid=mid))
    def stats_over(self, lookback_sec: float) -> Optional[MicroStats]:
        if len(self._buf) < 3: return None
        now = self._buf[-1].ts
        cutoff = now - lookback_sec
        start = None
        for s in self._buf:
            if s.ts >= cutoff:
                start = s; break
        if start is None: start = self._buf[0]
        end = self._buf[-1]
        signed = (end.mid - start.mid) / max(start.mid, 1e-9)
        return MicroStats(lookback_sec, start.mid, end.mid, abs(signed), signed, sum(1 for x in self._buf if x.ts >= cutoff))
