import json
import time
from typing import Optional, Any, Dict, Union

from app.core.config import settings

local_cache = {}
cache_expire_times = {}


def get_cache_key(key: str) -> str:
    return f"secret:{key}"


def set_cache(key: str, data: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
    cache_key = get_cache_key(key)
    ttl = max(ttl_seconds or 0, settings.CACHE_MIN_TTL)
    
    local_cache[cache_key] = json.dumps(data)
    cache_expire_times[cache_key] = time.time() + ttl


def get_cache(key: str) -> Optional[Dict[str, Any]]:
    cache_key = get_cache_key(key)
    
    if cache_key in local_cache and cache_key in cache_expire_times:
        if time.time() < cache_expire_times[cache_key]:
            return json.loads(local_cache[cache_key])
        else:
            delete_cache(key)
    return None


def delete_cache(key: str) -> None:
    cache_key = get_cache_key(key)
    if cache_key in local_cache:
        local_cache.pop(cache_key, None)
    if cache_key in cache_expire_times:
        cache_expire_times.pop(cache_key, None) 