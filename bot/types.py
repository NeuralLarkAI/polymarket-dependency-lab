from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class TopOfBook:
    token_id: str
    ts: float
    bid: Optional[float]
    ask: Optional[float]
    @property
    def midpoint(self) -> Optional[float]:
        if self.bid is None or self.ask is None:
            return None
        return (self.bid + self.ask) / 2.0

@dataclass
class OrderIntent:
    token_id: str
    side: str
    price: float
    size_usd: float

@dataclass
class BookLevel:
    price: float
    size: float

@dataclass
class OrderBook:
    token_id: str
    bids: List[BookLevel]
    asks: List[BookLevel]
