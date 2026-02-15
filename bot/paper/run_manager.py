from __future__ import annotations
from dataclasses import dataclass
import os, time, json
from typing import Optional

@dataclass(frozen=True)
class RunPaths:
    run_id: str
    run_dir: str
    equity_csv: str
    fills_csv: str
    attempts_csv: str
    summary_json: str
    meta_json: str

class RunManager:
    def __init__(self, base_dir: str = "./runs"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def start_run(self, tag: str = "paper", *, pair: Optional[dict] = None, cfg: Optional[dict] = None) -> RunPaths:
        ts = time.strftime("%Y%m%d-%H%M%S")
        run_id = f"{tag}-{ts}"
        run_dir = os.path.join(self.base_dir, run_id)
        os.makedirs(run_dir, exist_ok=True)

        paths = RunPaths(
            run_id=run_id,
            run_dir=run_dir,
            equity_csv=os.path.join(run_dir, "equity_timeseries.csv"),
            fills_csv=os.path.join(run_dir, "paper_fills.csv"),
            attempts_csv=os.path.join(run_dir, "order_attempts.csv"),
            summary_json=os.path.join(run_dir, "performance_summary.json"),
            meta_json=os.path.join(run_dir, "run_meta.json"),
        )

        meta = {
            "run_id": run_id,
            "created_at_ts": time.time(),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "pair": pair or {},
            "config": cfg or {},
        }
        with open(paths.meta_json, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        return paths
