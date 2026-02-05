"""Thread-safe bounded in-memory cache with LRU eviction."""

import threading
from collections import OrderedDict
from typing import Any


class BoundedCache:
    """Thread-safe LRU cache with a configurable maximum size.

    Parameters
    ----------
    maxsize : int
        Maximum number of entries before LRU eviction kicks in.
    """

    def __init__(self, maxsize: int = 256):
        self._data: OrderedDict[str, Any] = OrderedDict()
        self._lock = threading.Lock()
        self._maxsize = maxsize

    def get(self, key: str) -> Any | None:
        """Return cached value or None. Moves key to most-recent on hit."""
        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
                return self._data[key]
            return None

    def set(self, key: str, value: Any) -> None:
        """Insert or update a key. Evicts least-recently-used if full."""
        with self._lock:
            if key in self._data:
                self._data.move_to_end(key)
                self._data[key] = value
            else:
                if len(self._data) >= self._maxsize:
                    self._data.popitem(last=False)
                self._data[key] = value
