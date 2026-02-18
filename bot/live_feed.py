from __future__ import annotations
import asyncio
import time
from typing import Dict, Optional, Callable, Any
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderBookSummary
from bot.types import TopOfBook

class PolymarketLiveFeed:
    """
    Connects to Polymarket CLOB API to fetch live market data.
    Provides top-of-book updates and L2 order book data.
    """

    def __init__(self, token_ids: list[str], on_tob_update: Optional[Callable] = None):
        """
        Args:
            token_ids: List of Polymarket token IDs to track
            on_tob_update: Optional callback for top-of-book updates
        """
        self.token_ids = token_ids
        self.on_tob_update = on_tob_update
        self.client = ClobClient(host="https://clob.polymarket.com", key="")
        self.tob: Dict[str, TopOfBook] = {}
        self.books: Dict[str, Any] = {}
        self._running = False
        self._tasks: list[asyncio.Task] = []

    async def start(self):
        """Start fetching live data for all token IDs."""
        self._running = True
        print(f"[LIVE FEED] Starting live feed for {len(self.token_ids)} markets")

        # Create polling tasks for each token
        for token_id in self.token_ids:
            task = asyncio.create_task(self._poll_market(token_id))
            self._tasks.append(task)

    async def stop(self):
        """Stop fetching live data."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        await asyncio.gather(*self._tasks, return_exceptions=True)
        print("[LIVE FEED] Stopped")

    async def _poll_market(self, token_id: str):
        """
        Poll a single market for updates.
        In production, this would use WebSocket for better performance.
        """
        poll_interval = 1.0  # Poll every second

        while self._running:
            try:
                # Fetch order book
                book_response: OrderBookSummary = self.client.get_order_book(token_id)

                # Store book for depth-based fills
                self.books[token_id] = book_response

                # Extract top of book
                now = time.time()
                bid = None
                ask = None

                if hasattr(book_response, 'bids') and book_response.bids and len(book_response.bids) > 0:
                    b = book_response.bids[0]
                    bid = float(b.price if hasattr(b, 'price') else b['price'])

                if hasattr(book_response, 'asks') and book_response.asks and len(book_response.asks) > 0:
                    a = book_response.asks[0]
                    ask = float(a.price if hasattr(a, 'price') else a['price'])

                # Create TopOfBook
                tob = TopOfBook(
                    token_id=token_id,
                    ts=now,
                    bid=bid,
                    ask=ask
                )

                self.tob[token_id] = tob

                # Callback if provided
                if self.on_tob_update:
                    self.on_tob_update(token_id, tob)

            except Exception as e:
                print(f"[LIVE FEED] Error polling {token_id}: {e}")

            await asyncio.sleep(poll_interval)

    def get_tob(self, token_id: str) -> Optional[TopOfBook]:
        """Get latest top-of-book for a token."""
        return self.tob.get(token_id)

    def get_book(self, token_id: str) -> Optional[Any]:
        """Get latest order book for a token."""
        return self.books.get(token_id)

    def get_book_for_ws_store(self, token_id: str) -> Optional[Dict]:
        """
        Convert Polymarket book format to WSL2BookStore format.
        Returns dict with bids/asks as list of [price, size] pairs.
        """
        book = self.books.get(token_id)
        if not book:
            return None

        bids = []
        asks = []

        if hasattr(book, 'bids') and book.bids:
            bids = [[float(level.price if hasattr(level, 'price') else level['price']),
                      float(level.size if hasattr(level, 'size') else level['size'])] for level in book.bids]

        if hasattr(book, 'asks') and book.asks:
            asks = [[float(level.price if hasattr(level, 'price') else level['price']),
                      float(level.size if hasattr(level, 'size') else level['size'])] for level in book.asks]

        return {
            "token_id": token_id,
            "payload": {
                "bids": bids,
                "asks": asks
            }
        }
