from __future__ import annotations
import csv, os, time
from dataclasses import dataclass
from typing import Optional

@dataclass
class MarketVolLogger:
    path: str
    log_interval_sec: float = 1.0
    def __post_init__(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            with open(self.path, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(["ts","token_id","mid"])
        self._last = 0.0
    def maybe_log(self, token_id: str, mid: Optional[float]):
        if mid is None: return
        now = time.time()
        if now - self._last < self.log_interval_sec: return
        self._last = now
        with open(self.path, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([now, token_id, float(mid)])
