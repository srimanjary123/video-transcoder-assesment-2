aws_secrets.py
--------------
Optional Secrets Manager helper.

- If AWS access isn't available or SECRETS_DISABLE is set, we fall back to env vars.
- Region defaults to ap-southeast-2.
- Backwards compatible with your original `get_secret(name, env_fallback=None)`.

Env knobs:
  AWS_REGION=ap-southeast-2
  SECRETS_DISABLE=true|1|yes   # force env fallbacks (great for local dev)
  SECRETS_CACHE_TTL=300        # seconds
"""

from __future__ import annotations
import os, json, time
from typing import Optional, Tuple, Any

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except Exception:  # pragma: no cover
    boto3 = None
    BotoCoreError = ClientError = Exception  # type: ignore

AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-2")
SECRETS_DISABLE = os.getenv("SECRETS_DISABLE", "").lower() in {"1", "true", "yes"}
_CACHE_TTL = int(os.getenv("SECRETS_CACHE_TTL", "300"))

_sm = None  # lazy
_cache: dict[str, tuple[float, Any]] = {}  # name -> (ts, value)

def _client():
    global _sm
    if _sm is None and not SECRETS_DISABLE and boto3:
        _sm = boto3.client("secretsmanager", region_name=AWS_REGION)
    return _sm

def _get_secret_string(name: str) -> Optional[str]:
    """Fetch SecretString with simple in-memory caching."""
    now = time.time()
    if name in _cache:
        ts, val = _cache[name]
        if now - ts < _CACHE_TTL:
            return val  # may be None or str
    sm = _client()
    if not sm:
        _cache[name] = (now, None)
        return None
    try:
        res = sm.get_secret_value(SecretId=name)
        val = res.get("SecretString")
        _cache[name] = (now, val)
        return val
    except (ClientError, BotoCoreError, Exception):
        _cache[name] = (now, None)
        return None

# -----------------------
# Backward-compatible API
# -----------------------
def get_secret(name: str, env_fallback: Optional[str] = None) -> Optional[str]:
    """
    Return the whole SecretString for `name`. If unavailable, and `env_fallback`
    is provided, return os.getenv(env_fallback). Otherwise None.

    This preserves your original function signature/behavior.
    """
    if SECRETS_DISABLE:
        return os.getenv(env_fallback) if env_fallback else None
    val = _get_secret_string(name)
    if val is not None:
        return val
    return os.getenv(env_fallback) if env_fallback else None

# -----------------------
# Helpful new utilities
# -----------------------
def get_secret_with_source(name: str, env_fallback: Optional[str] = None) -> Tuple[Optional[str], str]:
    """Like get_secret, but also returns source: 'secrets' or 'env'."""
    if SECRETS_DISABLE:
        return (os.getenv(env_fallback) if env_fallback else None), "env"
    val = _get_secret_string(name)
    if val is not None:
        return val, "secrets"
    return (os.getenv(env_fallback) if env_fallback else None), "env"

def get_secret_json(name: str, env_json_fallback: Optional[str] = None) -> Tuple[Optional[dict], str]:
    """
    Fetch a JSON secret and parse it. If missing, tries env_json_fallback (env var
    containing JSON). Returns (dict_or_none, source).
    """
    if SECRETS_DISABLE:
        raw = os.getenv(env_json_fallback) if env_json_fallback else None
        try:
            return (json.loads(raw) if raw else None), "env"
        except Exception:
            return None, "env"

    raw = _get_secret_string(name)
    if raw:
        try:
            return json.loads(raw), "secrets"
        except Exception:
            # secret exists but not JSON; still return as None for JSON purposes
            return None, "secrets"

    raw = os.getenv(env_json_fallback) if env_json_fallback else None
    try:
        return (json.loads(raw) if raw else None), "env"
    except Exception:
        return None, "env"

def get_secret_field(name: str, field: str, env_fallback: Optional[str] = None) -> Tuple[Optional[str], str]:
    """
    Convenience: read a JSON secret and return a single field (e.g., apiKey, password).
    If missing, read env_fallback (an env var containing the value directly).
    Returns (value, source).
    """
    data, src = get_secret_json(name)
    if isinstance(data, dict) and field in data:
        return str(data[field]), src
    return (os.getenv(env_fallback) if env_fallback else None), "env"
