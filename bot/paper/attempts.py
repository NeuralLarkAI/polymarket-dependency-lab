from __future__ import annotations
import csv, os, time

class AttemptLogger:
    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            with open(self.path, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(["ts","token_id","side","limit_price","size_usd","ok","reason"])

    def log(self, token_id: str, side: str, limit_price: float, size_usd: float, ok: bool, reason: str):
        with open(self.path, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([time.time(), token_id, side, limit_price, size_usd, int(ok), reason])
