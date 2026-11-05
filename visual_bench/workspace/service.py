"""In-memory online-visitor count (WS-04).

The service runs as one uvicorn process, so a process-local map from client id to last heartbeat
is the whole state: no IPs, no persistence, and a restart refills within one heartbeat interval.
Running several workers or replicas would need this map in a shared store.
"""
from __future__ import annotations

import threading
import time
from collections.abc import Callable


class PresenceService:
    def __init__(self, window_s: int = 90, clock: Callable[[], float] = time.monotonic) -> None:
        self.window_s = window_s
        self._clock = clock
        self._seen: dict[str, float] = {}
        self._lock = threading.Lock()

    def beat(self, client_id: str) -> int:
        """Record a heartbeat, drop browsers silent for longer than the window, return the count."""
        with self._lock:
            now = self._clock()
            self._seen[client_id] = now
            cutoff = now - self.window_s
            self._seen = {cid: t for cid, t in self._seen.items() if t >= cutoff}
            return len(self._seen)
