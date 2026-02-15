from __future__ import annotations
import csv, os, time, json, math
from dataclasses import dataclass
from typing import List, Optional, Tuple

def _mean_std(xs: List[float]) -> Tuple[float, float]:
    n = len(xs)
    if n < 2:
        return 0.0, 0.0
    m = sum(xs) / n
    v = sum((x - m) ** 2 for x in xs) / (n - 1)
    return m, math.sqrt(v)

def _max_drawdown(equity: List[float]) -> float:
    peak = equity[0]
    max_dd = 0.0
    for e in equity:
        peak = max(peak, e)
        dd = (peak - e) / max(peak, 1e-9)
        max_dd = max(max_dd, dd)
    return max_dd

def _regime_split(returns: List[float], vol_window: int, high_thr: float):
    low, high = [], []
    roll = []
    for r in returns:
        roll.append(r)
        if len(roll) > vol_window:
            roll.pop(0)
        if len(roll) < max(10, vol_window // 3):
            low.append(r)
            continue
        mu = sum(roll) / len(roll)
        var = sum((x - mu) ** 2 for x in roll) / max(1, (len(roll) - 1))
        s = math.sqrt(var)
        (high if s >= high_thr else low).append(r)
    return low, high

@dataclass
class PerformanceTracker:
    equity_csv_path: str
    summary_json_path: str
    returns_window_points: int = 720
    log_interval_sec: int = 5
    print_interval_sec: int = 15
    regime_enabled: bool = True
    regime_vol_window_points: int = 60
    regime_high_vol_threshold: float = 0.0015
    regime_min_points_each: int = 80

    def __post_init__(self):
        os.makedirs(os.path.dirname(self.equity_csv_path), exist_ok=True)
        if not os.path.exists(self.equity_csv_path):
            with open(self.equity_csv_path, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(["ts", "equity", "cash", "realized_pnl", "unrealized_pnl", "fills"])
        self._last_log = 0.0
        self._last_print = 0.0
        self._equity: List[float] = []
        self._ts: List[float] = []

    def update(self, *, ts: float, equity: float, cash: float, realized_pnl: float, unrealized_pnl: float, fills: int):
        self._equity.append(float(equity))
        self._ts.append(float(ts))
        if len(self._equity) > self.returns_window_points * 3:
            self._equity = self._equity[-self.returns_window_points * 3 :]
            self._ts = self._ts[-self.returns_window_points * 3 :]

        now = time.time()
        if now - self._last_log >= self.log_interval_sec:
            self._last_log = now
            with open(self.equity_csv_path, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([ts, equity, cash, realized_pnl, unrealized_pnl, fills])
            self._write_summary(ts, equity, cash, realized_pnl, unrealized_pnl, fills)

        if now - self._last_print >= self.print_interval_sec:
            self._last_print = now
            s = self._compute_summary(ts, equity, cash, realized_pnl, unrealized_pnl, fills)
            print("[PERF]", {k: s[k] for k in ["equity","fills","max_drawdown_pct","sharpe_like","points_low","points_high","regime_ok"]})

    def _compute_summary(self, ts, equity, cash, realized_pnl, unrealized_pnl, fills):
        eq = self._equity[-self.returns_window_points :] if len(self._equity) > 10 else self._equity
        if len(eq) < 3:
            return {"ts": ts, "equity": equity, "cash": cash, "fills": fills, "max_drawdown_pct": 0.0, "sharpe_like": 0.0,
                    "sharpe_low": 0.0, "sharpe_high": 0.0, "points_low": 0, "points_high": 0, "regime_ok": False}
        returns = [(eq[i] / eq[i - 1] - 1.0) for i in range(1, len(eq)) if eq[i - 1] > 0]
        m, s = _mean_std(returns)
        sharpe_like = (m / s * math.sqrt(len(returns))) if s > 0 else 0.0
        dd = _max_drawdown(eq)

        sharpe_low = sharpe_high = 0.0
        points_low = points_high = 0
        regime_ok = False
        if self.regime_enabled:
            low, high = _regime_split(returns, self.regime_vol_window_points, self.regime_high_vol_threshold)
            points_low, points_high = len(low), len(high)
            ml, sl = _mean_std(low); mh, sh = _mean_std(high)
            sharpe_low = (ml / sl * math.sqrt(len(low))) if sl > 0 else 0.0
            sharpe_high = (mh / sh * math.sqrt(len(high))) if sh > 0 else 0.0
            regime_ok = points_low >= self.regime_min_points_each and points_high >= self.regime_min_points_each

        return {
            "ts": ts,
            "equity": float(equity),
            "cash": float(cash),
            "realized_pnl": float(realized_pnl),
            "unrealized_pnl": float(unrealized_pnl),
            "fills": int(fills),
            "max_drawdown_pct": float(dd),
            "sharpe_like": float(sharpe_like),
            "sharpe_low": float(sharpe_low),
            "sharpe_high": float(sharpe_high),
            "points_low": int(points_low),
            "points_high": int(points_high),
            "regime_ok": bool(regime_ok),
        }

    def _write_summary(self, ts, equity, cash, realized_pnl, unrealized_pnl, fills):
        s = self._compute_summary(ts, equity, cash, realized_pnl, unrealized_pnl, fills)
        os.makedirs(os.path.dirname(self.summary_json_path), exist_ok=True)
        with open(self.summary_json_path, "w", encoding="utf-8") as f:
            json.dump(s, f, indent=2)

    def finalize(self):
        if self._ts:
            ts = self._ts[-1]
            equity = self._equity[-1]
            self._write_summary(ts, equity, cash=0.0, realized_pnl=0.0, unrealized_pnl=0.0, fills=0)
