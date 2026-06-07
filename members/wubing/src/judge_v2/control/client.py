from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

from judge_v2.common.models import VerifyReq


class BackendError(RuntimeError):
    def __init__(self, message: str, *, retryable: bool = True, status_code: int | None = None) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.status_code = status_code


class BackendClient:
    def health(self, base_url: str, *, timeout: float) -> dict[str, Any]:
        return _get_json(f"{base_url.rstrip('/')}/health", timeout=timeout)

    def verify(self, base_url: str, req: VerifyReq, *, timeout: float) -> dict[str, Any]:
        payload = json.dumps(req.model_dump(), ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"{base_url.rstrip('/')}/verify",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            retryable = exc.code in {429, 500, 502, 503, 504}
            raise BackendError(
                f"backend HTTP {exc.code}: {body}",
                retryable=retryable,
                status_code=exc.code,
            ) from exc
        except OSError as exc:
            raise BackendError(f"backend request failed: {exc}", retryable=True) from exc


def _get_json(url: str, *, timeout: float) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise BackendError(
            f"backend health HTTP {exc.code}: {body}",
            retryable=True,
            status_code=exc.code,
        ) from exc
    except OSError as exc:
        raise BackendError(f"backend health failed: {exc}", retryable=True) from exc

