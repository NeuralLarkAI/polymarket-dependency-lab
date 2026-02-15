from __future__ import annotations
import csv, os, time
from dataclasses import dataclass
from typing import Dict, List, Optional
from bot.types import OrderIntent, OrderBook, TopOfBook
from bot.paper.depth_fill import fok_fill_vwap_against_depth

@dataclass
class Fill:
    ts: float
    token_id: str
    side: str
    price: float
    size_usd: float
    shares: float
    reason: str

class PaperBroker:
    def __init__(self, *, starting_cash_usd: float, fee_bps: float, slippage_bps: float, mark_method: str = "mid", save_fills_csv: bool = True, fills_csv_path: str = "./data/paper_fills.csv"):
        self.cash = float(starting_cash_usd)
        self.fee_bps = float(fee_bps)
        self.slippage_bps = float(slippage_bps)
        self.mark_method = mark_method
        self.save_fills_csv = bool(save_fills_csv)
        self.fills_csv_path = fills_csv_path
        self.pos_shares: Dict[str, float] = {}
        self.realized_pnl: float = 0.0
        self.fills: List[Fill] = []
        if self.save_fills_csv:
            os.makedirs(os.path.dirname(self.fills_csv_path), exist_ok=True)
            if not os.path.exists(self.fills_csv_path):
                with open(self.fills_csv_path, "w", newline="", encoding="utf-8") as f:
                    csv.writer(f).writerow(["ts","token_id","side","price","size_usd","shares","reason"])
    def try_fill_fok_with_depth(self, intent: OrderIntent, book: OrderBook, reason: str = "", *, extra_slippage_bps: float = 0.0, liquidity_shrink: float = 0.0) -> Optional[Fill]:
        res = fok_fill_vwap_against_depth(intent, book, fee_bps=self.fee_bps, slippage_bps=self.slippage_bps, extra_slippage_bps=extra_slippage_bps, liquidity_shrink=liquidity_shrink)
        if not res.ok: return None
        ts = time.time()
        side = intent.side.upper()
        if side == "BUY":
            if self.cash < res.filled_usd: return None
            self.cash -= res.filled_usd
            self.pos_shares[intent.token_id] = self.pos_shares.get(intent.token_id, 0.0) + res.filled_shares
        else:
            have = self.pos_shares.get(intent.token_id, 0.0)
            if have + 1e-9 < res.filled_shares: return None
            self.pos_shares[intent.token_id] = have - res.filled_shares
            self.cash += res.filled_usd
        fill = Fill(ts, intent.token_id, side, res.avg_price, res.filled_usd, res.filled_shares, reason)
        self.fills.append(fill)
        if self.save_fills_csv:
            with open(self.fills_csv_path, "a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow([fill.ts, fill.token_id, fill.side, fill.price, fill.size_usd, fill.shares, fill.reason])
        return fill
    def equity_mark_to_market(self, tob: Dict[str, TopOfBook]) -> float:
        eq = self.cash
        for token, sh in self.pos_shares.items():
            if abs(sh) < 1e-9: continue
            mid = tob.get(token).midpoint if token in tob else None
            if mid is None: continue
            eq += sh * mid
        return eq
    def unrealized_pnl(self, tob: Dict[str, TopOfBook]) -> float:
        return self.equity_mark_to_market(tob) - self.cash - self.realized_pnl
