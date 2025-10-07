"""
Optional SSM helper.
- If SSM access is not granted, we fall back to environment variables.
"""
import os
from typing import Optional
try:
    import boto3
    _ssm = boto3.client("ssm")
except Exception:  # pragma: no cover
    _ssm = None

def get_parameter(name: str, with_decryption: bool = True, env_fallback: Optional[str] = None) -> Optional[str]:
    try:
        if _ssm:
            res = _ssm.get_parameter(Name=name, WithDecryption=with_decryption)
            return res["Parameter"]["Value"]
    except Exception:
        pass
    if env_fallback:
        return os.getenv(env_fallback)
    return None
