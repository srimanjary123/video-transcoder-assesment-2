"""
Optional secrets helper.
- If AWS Secrets Manager access is not granted, we fall back to environment variables.
- Safe to keep in repo; does not fetch anything unless you call get_secret().
"""
import os
from typing import Optional
try:
    import boto3
    _sm = boto3.client("secretsmanager")
except Exception:  # pragma: no cover
    _sm = None

def get_secret(name: str, env_fallback: Optional[str] = None) -> Optional[str]:
    """Return secret from Secrets Manager, else from env var name if provided."""
    try:
        if _sm:
            res = _sm.get_secret_value(SecretId=name)
            if "SecretString" in res:
                return res["SecretString"]
    except Exception:
        pass
    if env_fallback:
        return os.getenv(env_fallback)
    return None
