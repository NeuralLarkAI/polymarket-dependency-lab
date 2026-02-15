from __future__ import annotations
from dataclasses import dataclass
from bot.types import OrderIntent, OrderBook

@dataclass(frozen=True)
class DepthFillResult:
    ok: bool
    filled_usd: float
    filled_shares: float
    avg_price: float
    reason: str

def fok_fill_vwap_against_depth(intent: OrderIntent, book: OrderBook, *, fee_bps: float = 0.0, slippage_bps: float = 0.0, extra_slippage_bps: float = 0.0, liquidity_shrink: float = 0.0) -> DepthFillResult:
    fee = fee_bps / 10_000.0
    slip = (slippage_bps + extra_slippage_bps) / 10_000.0
    remaining = float(intent.size_usd)
    filled_usd = 0.0
    filled_sh = 0.0
    px_x_sh = 0.0
    side = intent.side.upper()
    if side == "BUY":
        for lvl in book.asks:
            if lvl.price > intent.price: break
            avail = lvl.size * (1.0 - liquidity_shrink)
            if avail <= 0: continue
            eff_px = lvl.price * (1.0 + slip) * (1.0 + fee)
            max_cost = eff_px * avail
            take = min(remaining, max_cost)
            sh = take / eff_px
            remaining -= take
            filled_usd += take
            filled_sh += sh
            px_x_sh += eff_px * sh
            if remaining <= 1e-9: break
    elif side == "SELL":
        for lvl in book.bids:
            if lvl.price < intent.price: break
            avail = lvl.size * (1.0 - liquidity_shrink)
            if avail <= 0: continue
            eff_px = lvl.price * (1.0 - slip) * (1.0 - fee)
            max_sh = remaining / max(eff_px, 1e-9)
            sh = min(avail, max_sh)
            proceeds = sh * eff_px
            remaining -= proceeds
            filled_usd += proceeds
            filled_sh += sh
            px_x_sh += eff_px * sh
            if remaining <= 1e-9: break
    else:
        return DepthFillResult(False, 0.0, 0.0, 0.0, "bad side")
    if filled_usd + 1e-9 < intent.size_usd:
        return DepthFillResult(False, 0.0, 0.0, 0.0, "FOK not filled")
    avg_px = px_x_sh / max(filled_sh, 1e-9)
    return DepthFillResult(True, filled_usd, filled_sh, avg_px, "filled")
