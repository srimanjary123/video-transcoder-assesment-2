import os, json
from typing import Optional, Any
from pymemcache.client.base import Client

MEMCACHED_HOST = os.getenv("MEMCACHED_HOST", "127.0.0.1")
MEMCACHED_PORT = int(os.getenv("MEMCACHED_PORT", "11211"))
NAMESPACE = os.getenv("CACHE_NAMESPACE", "vt3")

_client: Optional[Client] = None
def _client_conn() -> Client:
    global _client
    if _client is None:
        _client = Client((MEMCACHED_HOST, MEMCACHED_PORT), timeout=0.3, connect_timeout=0.3)
    return _client

def _k(key: str) -> str:
    return f"{NAMESPACE}:{key}"

def cache_get(key: str):
    try:
        raw = _client_conn().get(_k(key))
        return None if raw is None else json.loads(raw)
    except Exception:
        return None

def cache_set(key: str, value: Any, ttl_seconds: int = 300) -> bool:
    try:
        return _client_conn().set(_k(key), json.dumps(value), expire=ttl_seconds)
    except Exception:
        return False
cache.py
import os, json
from pymemcache.client.base import Client

HOST = os.environ.get("MEMCACHED_HOST")
PORT = int(os.environ.get("MEMCACHED_PORT", "11211"))
NS   = os.environ.get("CACHE_NAMESPACE", "a2")

_client = Client((HOST, PORT), connect_timeout=1, timeout=1, no_delay=True)

def _k(key: str) -> str:
    return f"{NS}:{key}"

def cache_get(key: str):
    val = _client.get(_k(key))
    return None if val is None else json.loads(val)

def cache_set(key: str, value, ttl: int):
    _client.set(_k(key), json.dumps(value), expire=ttl)

def cache_delete(key: str):
    try:
        _client.delete(_k(key))
    except Exception:
        pass

def cache_stats():
    try:
        return _client.stats()
    except Exception:
        return {} 
