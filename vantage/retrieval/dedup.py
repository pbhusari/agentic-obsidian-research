from __future__ import annotations

import hashlib


class Deduplicator:
    def __init__(self) -> None:
        self._seen: set[str] = set()

    def seen(self, key: str) -> bool:
        h = hashlib.sha256(key.encode()).hexdigest()
        if h in self._seen:
            return True
        self._seen.add(h)
        return False
