"""File-backed cache with in-memory hot path for provider responses."""

from __future__ import annotations

import json
import os
import tempfile
import time
from dataclasses import dataclass
from hashlib import sha1
from pathlib import Path
from typing import Any, Dict, Optional

__all__ = ["get", "set", "cache_path", "clear_memory"]


@dataclass
class _CacheEntry:
    expires_at: float
    data: Dict[str, Any]


def _resolve_cache_dir() -> Path:
    root = os.getenv("PROVIDERS_CACHE_DIR")
    if root:
        base = Path(root)
    else:
        base = Path(tempfile.gettempdir()) / "corealpha_providers"
    base.mkdir(parents=True, exist_ok=True)
    return base


_CACHE_DIR = _resolve_cache_dir()
_MEMORY: Dict[str, _CacheEntry] = {}


def cache_path(key: str) -> Path:
    """Return the on-disk path for a cache key."""

    digest = sha1(key.encode("utf-8"), usedforsecurity=False).hexdigest()
    return _CACHE_DIR / f"{digest}.json"


def clear_memory() -> None:
    """Clear the in-memory cache (useful in tests)."""

    _MEMORY.clear()


def get(key: str) -> Optional[Dict[str, Any]]:
    """Return cached data if present and not expired."""

    now = time.time()
    entry = _MEMORY.get(key)
    if entry and entry.expires_at > now:
        return entry.data
    if entry and entry.expires_at <= now:
        _MEMORY.pop(key, None)

    path = cache_path(key)
    if not path.exists():
        return None

    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        try:
            path.unlink()
        except OSError:
            pass
        return None

    expires_at = float(payload.get("expires_at", 0))
    if expires_at <= now:
        try:
            path.unlink()
        except OSError:
            pass
        return None

    data = payload.get("data")
    if not isinstance(data, dict):
        try:
            path.unlink()
        except OSError:
            pass
        return None

    _MEMORY[key] = _CacheEntry(expires_at=expires_at, data=data)
    return data


def set(key: str, data: Dict[str, Any], ttl_s: int) -> None:
    """Store data in both memory and file cache."""

    expires_at = time.time() + ttl_s
    entry = _CacheEntry(expires_at=expires_at, data=data)
    _MEMORY[key] = entry
    payload = {"expires_at": expires_at, "data": data}
    path = cache_path(key)
    tmp_path = path.with_suffix(".tmp")
    try:
        tmp_path.write_text(json.dumps(payload, separators=(",", ":")))
        tmp_path.replace(path)
    except OSError:
        try:
            tmp_path.unlink()
        except OSError:
            pass
