"""In-memory online-visitor count with per-country totals (WS-04).

The service runs as one uvicorn process, so a process-local map from client id to last heartbeat
and country is the whole state: no IPs, no persistence, and a restart refills within one heartbeat
interval. The country is Cloudflare's CF-IPCountry header (requests reach the service through a
Cloudflare Tunnel, so the peer address is always local). Running several workers or replicas would
need this map in a shared store.
"""
from __future__ import annotations

import re
import threading
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass

_COUNTRY = re.compile(r"^[A-Z]{2}$")


@dataclass(frozen=True)
class PresenceSnapshot:
    online: int
    countries: list[tuple[str | None, int]]  # largest first; None = unknown or local


def normalize_country(header: str | None) -> str | None:
    """Keep real alpha-2 codes; Cloudflare's XX (unknown) and T1 (Tor) become unknown."""
    code = (header or "").strip().upper()
    return code if _COUNTRY.match(code) and code != "XX" else None


class PresenceService:
    def __init__(self, window_s: int = 90, clock: Callable[[], float] = time.monotonic) -> None:
        self.window_s = window_s
        self._clock = clock
        self._seen: dict[str, tuple[float, str | None]] = {}
        self._lock = threading.Lock()

    def beat(self, client_id: str, country: str | None = None) -> PresenceSnapshot:
        """Record a heartbeat, drop browsers silent for longer than the window, return the totals."""
        with self._lock:
            now = self._clock()
            self._seen[client_id] = (now, country)
            cutoff = now - self.window_s
            self._seen = {cid: v for cid, v in self._seen.items() if v[0] >= cutoff}
            by_country = Counter(c for _, c in self._seen.values())
            ranked = sorted(by_country.items(), key=lambda kv: (-kv[1], kv[0] is None, kv[0] or ""))
            return PresenceSnapshot(len(self._seen), ranked)
