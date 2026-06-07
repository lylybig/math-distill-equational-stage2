from __future__ import annotations

import hashlib


def verify_cache_key(
    *,
    problem_id: str,
    verdict: str,
    code: str,
    service_rev: str,
) -> str:
    """Stable cache key for one judge verification request."""
    h = hashlib.sha256()
    for part in (problem_id, verdict, code, service_rev):
        h.update(part.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()

