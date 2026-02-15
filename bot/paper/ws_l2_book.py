from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import bisect
from bot.types import OrderBook, BookLevel

@dataclass
class _SideBook:
    px_to_sz: Dict[float, float]
    prices: List[float]
    bids: bool
    max_levels: int
    def __init__(self, bids: bool, max_levels: int):
        self.px_to_sz = {}
        self.prices = []
        self.bids = bids
        self.max_levels = max_levels
    def _key(self, px: float) -> float:
        return -px if self.bids else px
    def upsert(self, px: float, sz: float) -> None:
        px = float(px); sz = float(sz)
        if sz <= 0:
            self.remove(px); return
        existed = px in self.px_to_sz
        self.px_to_sz[px] = sz
        if not existed:
            keys = [self._key(p) for p in self.prices]
            i = bisect.bisect_left(keys, self._key(px))
            self.prices.insert(i, px)
        if len(self.prices) > self.max_levels:
            drop = self.prices[self.max_levels:]
            self.prices = self.prices[:self.max_levels]
            for p in drop: self.px_to_sz.pop(p, None)
    def remove(self, px: float) -> None:
        px = float(px)
        if px in self.px_to_sz:
            self.px_to_sz.pop(px, None)
            try: self.prices.remove(px)
            except ValueError: pass
    def levels(self) -> List[BookLevel]:
        return [BookLevel(price=float(px), size=float(self.px_to_sz.get(px, 0.0))) for px in self.prices if px in self.px_to_sz]

class WSL2BookStore:
    def __init__(self, max_levels: int = 200):
        self.max_levels = max_levels
        self._bids: Dict[str, _SideBook] = {}
        self._asks: Dict[str, _SideBook] = {}
    def _get(self, token_id: str) -> Tuple[_SideBook, _SideBook]:
        if token_id not in self._bids:
            self._bids[token_id] = _SideBook(bids=True, max_levels=self.max_levels)
            self._asks[token_id] = _SideBook(bids=False, max_levels=self.max_levels)
        return self._bids[token_id], self._asks[token_id]
    def on_message(self, msg: dict) -> None:
        token_id = msg.get("token_id") or msg.get("tokenId") or msg.get("asset_id") or msg.get("assetId")
        payload = msg.get("payload") or msg.get("data") or msg
        if not token_id and isinstance(payload, dict):
            token_id = payload.get("token_id") or payload.get("tokenId") or payload.get("asset_id")
        if not token_id: return
        token_id = str(token_id)
        bids_side, asks_side = self._get(token_id)
        bids = payload.get("bids") if isinstance(payload, dict) else None
        asks = payload.get("asks") if isinstance(payload, dict) else None
        if isinstance(bids, list) and isinstance(asks, list):
            bids_side.px_to_sz.clear(); bids_side.prices.clear()
            asks_side.px_to_sz.clear(); asks_side.prices.clear()
            for px, sz in _iter_levels(bids): bids_side.upsert(px, sz)
            for px, sz in _iter_levels(asks): asks_side.upsert(px, sz)
    def get_book(self, token_id: str) -> Optional[OrderBook]:
        token_id = str(token_id)
        if token_id not in self._bids or token_id not in self._asks: return None
        return OrderBook(token_id=token_id, bids=self._bids[token_id].levels(), asks=self._asks[token_id].levels())

def _iter_levels(raw: list):
    for row in raw:
        try:
            if isinstance(row, list) and len(row) >= 2:
                yield float(row[0]), float(row[1])
            elif isinstance(row, dict) and "price" in row and "size" in row:
                yield float(row["price"]), float(row["size"])
        except Exception:
            continue
