import json
from pathlib import Path

from math_distill_stage2.proof_bank.storage import (
    content_addressed_path,
    read_json,
    write_content_addressed_text,
    write_json,
)


def test_write_content_addressed_text_uses_first_two_sha_chars(tmp_path: Path):
    result = write_content_addressed_text(tmp_path, "proof_bodies", "hello\n", ".lean")

    assert result.sha256 == "5891b5b522d5df086d0ff0b110fbd9d21bb4fc7163af34d08286a2e846f6be03"
    assert result.path == tmp_path / "proof_bodies" / "58" / f"{result.sha256}.lean"
    assert result.path.read_text(encoding="utf-8") == "hello\n"


def test_content_addressed_path_is_deterministic(tmp_path: Path):
    sha = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    assert content_addressed_path(tmp_path, "certificates", sha, ".lean") == (
        tmp_path / "certificates" / "01" / f"{sha}.lean"
    )


def test_write_and_read_json(tmp_path: Path):
    path = tmp_path / "nested" / "payload.json"
    write_json(path, {"b": 2, "a": 1})

    assert json.loads(path.read_text(encoding="utf-8")) == {"a": 1, "b": 2}
    assert read_json(path) == {"a": 1, "b": 2}
