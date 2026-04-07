import time

_cache: dict[str, dict] = {}
TTL = 3600  # 1 hour


def get(key: str):
    entry = _cache.get(key)
    if entry is None:
        return None
    if time.time() - entry["ts"] > TTL:
        _cache.pop(key, None)
        return None
    return entry["value"]


def set(key: str, value):
    _cache[key] = {"value": value, "ts": time.time()}
