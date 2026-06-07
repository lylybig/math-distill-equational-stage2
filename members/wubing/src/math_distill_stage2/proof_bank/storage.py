from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class StoredText:
    sha256: str
    path: Path
    byte_length: int


def text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def content_addressed_path(root: Path, kind: str, sha256: str, suffix: str) -> Path:
    if len(sha256) != 64:
        raise ValueError("sha256 must be a 64-character hex digest")
    if not suffix.startswith("."):
        raise ValueError("suffix must start with '.'")
    return root / kind / sha256[:2] / f"{sha256}{suffix}"


def write_content_addressed_text(root: Path, kind: str, text: str, suffix: str) -> StoredText:
    digest = text_sha256(text)
    path = content_addressed_path(root, kind, digest, suffix)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(text, encoding="utf-8")
    return StoredText(sha256=digest, path=path, byte_length=len(text.encode("utf-8")))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload
