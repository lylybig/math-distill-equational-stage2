# Stage 2 Zulip Channel Digest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible Stage 2 Zulip channel sync workflow that archives full original messages and writes daily Chinese Markdown digests.

**Architecture:** Add a standard-library-only archive module under `src/math_distill_stage2/`, a CLI under `scripts/data/`, and a project skill under `skills/stage2-info-zulip-channel/`. The module owns normalization, JSONL archive merging, state updates, digest rendering, Zulip config parsing, REST pagination, and fixture-driven sync for tests. The skill orchestrates the workflow and keeps Zulip-derived notes separate from official competition snapshots.

**Tech Stack:** Python 3.10+, `urllib.request`, `configparser`, JSONL files, Markdown docs, pytest.

---

## File Structure

- Create `src/math_distill_stage2/zulip_archive.py`: focused business logic for message normalization, archive merging, state management, digest rendering, Zulip config parsing, REST API pagination, and fixture-backed sync.
- Create `scripts/data/sync_zulip_channel.py`: thin CLI wrapper matching the existing `scripts/data/download_public_data.py` import pattern.
- Create `tests/data/test_zulip_archive.py`: focused tests for archive behavior and CLI smoke coverage.
- Modify `tests/skills/test_stage2_skills.py`: require the new `stage2-info-zulip-channel` skill and metadata.
- Create `skills/stage2-info-zulip-channel/SKILL.md`: workflow instructions for daily Zulip update.
- Create `skills/stage2-info-zulip-channel/agents/openai.yaml`: skill UI metadata.
- Modify `docs/README.md`: document `docs/zulip-digests/` and the new skill.
- Modify `docs/data-inventory.md`: document local Zulip raw archive paths.
- Modify `docs/architecture.md`: mention Zulip digest in data snapshot and project skill layers.

## Task 1: Archive Module Tests

**Files:**
- Create: `tests/data/test_zulip_archive.py`
- Later implementation target: `src/math_distill_stage2/zulip_archive.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/data/test_zulip_archive.py` with:

```python
import json
import subprocess
import sys
from pathlib import Path

from math_distill_stage2.zulip_archive import (
    DEFAULT_CHANNEL,
    CHANNEL_SLUG,
    archive_messages_by_date,
    normalize_message,
    render_daily_digest,
    update_state,
)


def sample_message(message_id: int, timestamp: int, topic: str, content: str) -> dict:
    return {
        "id": message_id,
        "timestamp": timestamp,
        "sender_full_name": "Ada Lovelace",
        "sender_email": "ada@example.test",
        "sender_id": 42,
        "subject": topic,
        "content": content,
        "rendered_content": f"<p>{content}</p>",
        "reactions": [{"emoji_name": "thumbs_up"}],
        "stream_id": 13,
        "last_edit_timestamp": timestamp + 10,
        "edit_history": [{"timestamp": timestamp + 10, "prev_content": "old"}],
    }


def test_normalize_message_preserves_raw_dates_and_links():
    message = sample_message(
        101,
        1_778_284_800,
        "judge details",
        "Lean certificate update: https://example.test/rules",
    )

    normalized = normalize_message(message)

    assert normalized["id"] == 101
    assert normalized["datetime_utc"] == "2026-05-05T00:00:00+00:00"
    assert normalized["date_utc"] == "2026-05-05"
    assert normalized["topic"] == "judge details"
    assert normalized["links"] == ["https://example.test/rules"]
    assert normalized["raw"] == message
    assert normalized["last_edit_timestamp"] == 1_778_284_810
    assert normalized["edit_history"] == [{"timestamp": 1_778_284_810, "prev_content": "old"}]


def test_archive_messages_by_date_merges_sorts_and_updates_existing_ids(tmp_path: Path):
    archive_root = tmp_path / "data" / "raw" / "references" / "zulip" / CHANNEL_SLUG
    first = normalize_message(sample_message(102, 1_778_284_860, "solver", "old solver note"))
    second = normalize_message(sample_message(101, 1_778_284_800, "judge", "judge note"))
    archive_messages_by_date([first, second], archive_root)

    edited = normalize_message(sample_message(102, 1_778_284_860, "solver", "new solver note"))
    changed_paths = archive_messages_by_date([edited], archive_root)

    assert changed_paths == [archive_root / "messages" / "2026-05-05.jsonl"]
    rows = [
        json.loads(line)
        for line in (archive_root / "messages" / "2026-05-05.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
    ]
    assert [row["id"] for row in rows] == [101, 102]
    assert rows[1]["content"] == "new solver note"


def test_update_state_records_max_message_id_and_batch_stats(tmp_path: Path):
    state_path = tmp_path / "state.json"
    messages = [
        normalize_message(sample_message(102, 1_778_284_860, "solver", "solver note")),
        normalize_message(sample_message(101, 1_778_284_800, "judge", "judge note")),
    ]

    state = update_state(
        state_path,
        messages,
        channel=DEFAULT_CHANNEL,
        site="https://zulip.sair.foundation",
        fetched_batches=3,
        generated_at="2026-05-07T01:02:03+00:00",
    )

    assert state["last_message_id"] == 102
    assert state["channel"] == DEFAULT_CHANNEL
    assert state["site"] == "https://zulip.sair.foundation"
    assert state["last_sync_message_count"] == 2
    assert state["last_sync_batch_count"] == 3
    assert json.loads(state_path.read_text(encoding="utf-8")) == state


def test_render_daily_digest_groups_topics_links_and_keywords():
    records = [
        normalize_message(
            sample_message(
                101,
                1_778_284_800,
                "rules",
                "Official rule and dataset clarification https://example.test/rules",
            )
        ),
        normalize_message(
            sample_message(
                102,
                1_778_284_860,
                "solver",
                "Lean certificate accepted by judge",
            )
        ),
    ]

    digest = render_daily_digest(
        "2026-05-05",
        records,
        channel=DEFAULT_CHANNEL,
        generated_at="2026-05-07T01:02:03+00:00",
    )

    assert digest.startswith("# Zulip 每日摘要：2026-05-05")
    assert "## 按 Topic 整理" in digest
    assert "### rules" in digest
    assert "### solver" in digest
    assert "## Judge / Lean / Certificate" in digest
    assert "Lean certificate accepted by judge" in digest
    assert "https://example.test/rules" in digest
    assert "消息 101" in digest
    assert "消息 102" in digest


def test_sync_script_help_runs_when_invoked_by_path():
    root = Path(__file__).resolve().parents[2]

    result = subprocess.run(
        [sys.executable, "scripts/data/sync_zulip_channel.py", "--help"],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "--fixture-json" in result.stdout


def test_sync_script_can_archive_fixture_without_zulip_credentials(tmp_path: Path):
    root = Path(__file__).resolve().parents[2]
    fixture_path = tmp_path / "messages.json"
    fixture_path.write_text(
        json.dumps(
            [
                sample_message(101, 1_778_284_800, "rules", "Official rule note"),
                sample_message(102, 1_778_284_860, "solver", "Lean certificate note"),
            ]
        ),
        encoding="utf-8",
    )
    output_root = tmp_path / "data" / "raw"
    digest_dir = tmp_path / "docs" / "zulip-digests"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/data/sync_zulip_channel.py",
            "--fixture-json",
            str(fixture_path),
            "--output-root",
            str(output_root),
            "--digest-dir",
            str(digest_dir),
            "--generated-at",
            "2026-05-07T01:02:03+00:00",
        ],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    summary = json.loads(result.stdout)
    assert summary["message_count"] == 2
    assert summary["archive_root"].endswith(f"zulip/{CHANNEL_SLUG}")
    assert (digest_dir / "2026-05-05.md").exists()
    assert (
        output_root
        / "references"
        / "zulip"
        / CHANNEL_SLUG
        / "messages"
        / "2026-05-05.jsonl"
    ).exists()
```

- [ ] **Step 2: Run the archive tests to verify they fail**

Run:

```bash
pytest tests/data/test_zulip_archive.py -q
```

Expected: FAIL during collection with `ModuleNotFoundError: No module named 'math_distill_stage2.zulip_archive'` or import errors for the missing functions.

- [ ] **Step 3: Commit the failing tests**

Run:

```bash
git add tests/data/test_zulip_archive.py
git commit -m "test: cover zulip archive workflow"
```

Expected: commit includes only the new test file.

## Task 2: Archive Module Implementation

**Files:**
- Create: `src/math_distill_stage2/zulip_archive.py`
- Test: `tests/data/test_zulip_archive.py`

- [ ] **Step 1: Implement the module**

Create `src/math_distill_stage2/zulip_archive.py` with:

```python
from __future__ import annotations

import base64
import configparser
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_CHANNEL = "Math Distillation Challenge - equational theories"
DEFAULT_SITE = "https://zulip.sair.foundation"
CHANNEL_SLUG = "math-distillation-challenge-equational-theories"
DEFAULT_OUTPUT_ROOT = Path("data/raw")
DEFAULT_DIGEST_DIR = Path("docs/zulip-digests")
KEYWORDS = (
    "judge",
    "lean",
    "certificate",
    "solver",
    "dataset",
    "rule",
    "rules",
    "official",
    "stage 2",
    "stage2",
)
URL_RE = re.compile(r"https?://[^\s<>)\"']+")


@dataclass(frozen=True)
class ZulipConfig:
    site: str
    email: str
    key: str


class ZulipApiError(RuntimeError):
    pass


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def archive_root_for(output_root: Path, channel_slug: str = CHANNEL_SLUG) -> Path:
    return output_root / "references" / "zulip" / channel_slug


def extract_links(*texts: str | None) -> list[str]:
    links: list[str] = []
    seen: set[str] = set()
    for text in texts:
        if not text:
            continue
        for match in URL_RE.findall(text):
            link = match.rstrip(".,;:")
            if link not in seen:
                seen.add(link)
                links.append(link)
    return links


def normalize_message(message: dict[str, Any]) -> dict[str, Any]:
    timestamp = int(message["timestamp"])
    dt = datetime.fromtimestamp(timestamp, timezone.utc)
    topic = message.get("topic", message.get("subject", ""))
    content = message.get("content", "")
    rendered_content = message.get("rendered_content", "")
    normalized = {
        "id": int(message["id"]),
        "timestamp": timestamp,
        "datetime_utc": dt.isoformat(),
        "date_utc": dt.date().isoformat(),
        "sender_full_name": message.get("sender_full_name", ""),
        "sender_email": message.get("sender_email", ""),
        "sender_id": message.get("sender_id"),
        "topic": topic,
        "content": content,
        "rendered_content": rendered_content,
        "reactions": message.get("reactions", []),
        "links": extract_links(content, rendered_content),
        "stream_id": message.get("stream_id"),
        "last_edit_timestamp": message.get("last_edit_timestamp"),
        "edit_history": message.get("edit_history", []),
        "raw": message,
    }
    return normalized


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    path.write_text(payload, encoding="utf-8")


def archive_messages_by_date(messages: list[dict[str, Any]], archive_root: Path) -> list[Path]:
    by_date: dict[str, list[dict[str, Any]]] = {}
    for message in messages:
        by_date.setdefault(message["date_utc"], []).append(message)

    changed_paths: list[Path] = []
    for date, records in sorted(by_date.items()):
        path = archive_root / "messages" / f"{date}.jsonl"
        merged = {int(row["id"]): row for row in read_jsonl(path)}
        for record in records:
            merged[int(record["id"])] = record
        sorted_rows = [merged[key] for key in sorted(merged)]
        write_jsonl(path, sorted_rows)
        changed_paths.append(path)
    return changed_paths


def load_state(state_path: Path) -> dict[str, Any]:
    if not state_path.exists():
        return {}
    return json.loads(state_path.read_text(encoding="utf-8"))


def update_state(
    state_path: Path,
    messages: list[dict[str, Any]],
    *,
    channel: str,
    site: str,
    fetched_batches: int,
    generated_at: str,
) -> dict[str, Any]:
    previous = load_state(state_path)
    previous_last = int(previous.get("last_message_id", 0) or 0)
    current_last = max((int(message["id"]) for message in messages), default=previous_last)
    state = {
        **previous,
        "channel": channel,
        "site": site,
        "last_message_id": max(previous_last, current_last),
        "last_synced_at": generated_at,
        "last_sync_message_count": len(messages),
        "last_sync_batch_count": fetched_batches,
    }
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    return state


def _contains_keyword(text: str) -> bool:
    lower = text.lower()
    return any(keyword in lower for keyword in KEYWORDS)


def _excerpt(text: str, limit: int = 180) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 3].rstrip() + "..."


def render_daily_digest(
    date: str,
    records: list[dict[str, Any]],
    *,
    channel: str,
    generated_at: str,
) -> str:
    sorted_records = sorted(records, key=lambda row: int(row["id"]))
    topics: dict[str, list[dict[str, Any]]] = {}
    links: list[str] = []
    seen_links: set[str] = set()
    keyword_records: list[dict[str, Any]] = []
    for record in sorted_records:
        topics.setdefault(record.get("topic") or "(empty topic)", []).append(record)
        for link in record.get("links", []):
            if link not in seen_links:
                seen_links.add(link)
                links.append(link)
        haystack = f"{record.get('topic', '')} {record.get('content', '')}"
        if _contains_keyword(haystack):
            keyword_records.append(record)

    lines = [
        f"# Zulip 每日摘要：{date}",
        "",
        f"- 频道：`{channel}`",
        f"- 生成时间：`{generated_at}`",
        f"- 消息数：{len(sorted_records)}",
        "",
        "## 关键信息",
        "",
    ]
    if keyword_records:
        for record in keyword_records:
            lines.append(f"- 消息 {record['id']}（{record.get('topic') or '(empty topic)'}）：{_excerpt(record.get('content', ''))}")
    else:
        lines.append("- 当日归档中没有命中 Stage 2 关键词的消息。")

    lines.extend(["", "## 按 Topic 整理", ""])
    for topic, topic_records in sorted(topics.items()):
        lines.append(f"### {topic}")
        lines.append("")
        for record in topic_records:
            sender = record.get("sender_full_name") or record.get("sender_email") or "unknown"
            lines.append(f"- 消息 {record['id']}，{sender}：{_excerpt(record.get('content', ''))}")
        lines.append("")

    lines.extend(["## 规则与官方信息", ""])
    official_records = [
        record
        for record in keyword_records
        if _contains_keyword(f"{record.get('topic', '')} {record.get('content', '')}")
        and any(word in f"{record.get('topic', '')} {record.get('content', '')}".lower() for word in ("rule", "rules", "official", "dataset"))
    ]
    if official_records:
        for record in official_records:
            lines.append(f"- 消息 {record['id']}：{_excerpt(record.get('content', ''))}")
    else:
        lines.append("- 无明确规则、官方信息或数据集关键词命中。")

    lines.extend(["", "## Judge / Lean / Certificate", ""])
    proof_records = [
        record
        for record in keyword_records
        if any(word in f"{record.get('topic', '')} {record.get('content', '')}".lower() for word in ("judge", "lean", "certificate"))
    ]
    if proof_records:
        for record in proof_records:
            lines.append(f"- 消息 {record['id']}：{_excerpt(record.get('content', ''))}")
    else:
        lines.append("- 无 judge、Lean 或 certificate 关键词命中。")

    lines.extend(["", "## Solver 策略线索", ""])
    solver_records = [
        record
        for record in keyword_records
        if "solver" in f"{record.get('topic', '')} {record.get('content', '')}".lower()
    ]
    if solver_records:
        for record in solver_records:
            lines.append(f"- 消息 {record['id']}：{_excerpt(record.get('content', ''))}")
    else:
        lines.append("- 无 solver 关键词命中。")

    lines.extend(["", "## 重要链接", ""])
    if links:
        for link in links:
            lines.append(f"- {link}")
    else:
        lines.append("- 无链接。")

    lines.extend(["", "## 待跟进", "", "- 需要人工复查摘要中的 Zulip 信息是否已被官方规则或 judge 仓库确认。", "", "## 原文索引", ""])
    for record in sorted_records:
        lines.append(f"- 消息 {record['id']}：topic `{record.get('topic') or '(empty topic)'}`")
    lines.append("")
    return "\n".join(lines)


def write_daily_digests(
    archive_root: Path,
    digest_dir: Path,
    dates: list[str],
    *,
    channel: str,
    generated_at: str,
) -> list[Path]:
    digest_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for date in sorted(set(dates)):
        records = read_jsonl(archive_root / "messages" / f"{date}.jsonl")
        path = digest_dir / f"{date}.md"
        path.write_text(
            render_daily_digest(date, records, channel=channel, generated_at=generated_at),
            encoding="utf-8",
        )
        written.append(path)
    return written


def read_zulip_config(path: Path) -> ZulipConfig:
    parser = configparser.ConfigParser()
    read_paths = parser.read(path, encoding="utf-8")
    if not read_paths:
        raise FileNotFoundError(f"Zulip config file not found: {path}")
    if not parser.has_section("api"):
        raise ValueError(f"Zulip config file missing [api] section: {path}")
    site = parser.get("api", "site", fallback=DEFAULT_SITE).rstrip("/")
    email = parser.get("api", "email", fallback="")
    key = parser.get("api", "key", fallback="")
    if not email or not key:
        raise ValueError(f"Zulip config file missing email or key: {path}")
    return ZulipConfig(site=site, email=email, key=key)


class ZulipRestClient:
    def __init__(self, config: ZulipConfig):
        self.config = config

    def get_messages(
        self,
        *,
        channel: str,
        anchor: int | str,
        num_before: int,
        num_after: int,
        include_anchor: bool,
    ) -> dict[str, Any]:
        narrow = json.dumps([{"operator": "channel", "operand": channel}])
        query = urllib.parse.urlencode(
            {
                "anchor": str(anchor),
                "num_before": str(num_before),
                "num_after": str(num_after),
                "include_anchor": json.dumps(include_anchor),
                "narrow": narrow,
            }
        )
        url = f"{self.config.site}/api/v1/messages?{query}"
        token = base64.b64encode(f"{self.config.email}:{self.config.key}".encode()).decode()
        request = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Basic {token}",
                "User-Agent": "math-distill-stage2/0.1",
            },
        )
        try:
            with urllib.request.urlopen(request) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise ZulipApiError(f"Zulip API HTTP {exc.code}: {body}") from exc
        if payload.get("result") != "success":
            raise ZulipApiError(f"Zulip API error: {payload.get('msg', payload)}")
        return payload


def fetch_incremental_messages(
    client: ZulipRestClient,
    *,
    channel: str,
    last_message_id: int,
    batch_size: int,
) -> tuple[list[dict[str, Any]], int]:
    messages: list[dict[str, Any]] = []
    anchor = last_message_id
    batches = 0
    while True:
        payload = client.get_messages(
            channel=channel,
            anchor=anchor,
            num_before=0,
            num_after=batch_size,
            include_anchor=False,
        )
        batches += 1
        batch = payload.get("messages", [])
        if not batch:
            break
        messages.extend(batch)
        anchor = max(int(message["id"]) for message in batch)
        if payload.get("found_newest"):
            break
    return messages, batches


def fetch_full_backfill_messages(
    client: ZulipRestClient,
    *,
    channel: str,
    batch_size: int,
    since_timestamp: int | None,
) -> tuple[list[dict[str, Any]], int]:
    messages: list[dict[str, Any]] = []
    anchor: int | str = "newest"
    include_anchor = True
    batches = 0
    while True:
        payload = client.get_messages(
            channel=channel,
            anchor=anchor,
            num_before=batch_size,
            num_after=0,
            include_anchor=include_anchor,
        )
        batches += 1
        batch = payload.get("messages", [])
        if not batch:
            break
        if since_timestamp is not None:
            batch = [message for message in batch if int(message["timestamp"]) >= since_timestamp]
        messages.extend(batch)
        if payload.get("found_oldest"):
            break
        if since_timestamp is not None and batch and min(int(message["timestamp"]) for message in batch) <= since_timestamp:
            break
        anchor = min(int(message["id"]) for message in payload.get("messages", []))
        include_anchor = False
    deduped = {int(message["id"]): message for message in messages}
    return [deduped[key] for key in sorted(deduped)], batches


def parse_since_date(value: str | None) -> int | None:
    if not value:
        return None
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def sync_zulip_channel(
    *,
    raw_messages: list[dict[str, Any]],
    archive_root: Path,
    digest_dir: Path,
    state_path: Path,
    channel: str,
    site: str,
    fetched_batches: int,
    generated_at: str,
) -> dict[str, Any]:
    normalized = [normalize_message(message) for message in raw_messages]
    archive_paths = archive_messages_by_date(normalized, archive_root)
    dates = sorted({message["date_utc"] for message in normalized})
    digest_paths = write_daily_digests(
        archive_root,
        digest_dir,
        dates,
        channel=channel,
        generated_at=generated_at,
    )
    state = update_state(
        state_path,
        normalized,
        channel=channel,
        site=site,
        fetched_batches=fetched_batches,
        generated_at=generated_at,
    )
    return {
        "channel": channel,
        "site": site,
        "message_count": len(normalized),
        "dates": dates,
        "archive_root": str(archive_root),
        "archive_paths": [str(path) for path in archive_paths],
        "digest_paths": [str(path) for path in digest_paths],
        "state_path": str(state_path),
        "last_message_id": state.get("last_message_id", 0),
    }
```

- [ ] **Step 2: Run the focused archive tests**

Run:

```bash
pytest tests/data/test_zulip_archive.py -q
```

Expected: FAIL only for `test_sync_script_help_runs_when_invoked_by_path` and `test_sync_script_can_archive_fixture_without_zulip_credentials`, because the CLI file does not exist yet. The normalization, archive, state, and digest tests should pass.

- [ ] **Step 3: Commit the core implementation**

Run:

```bash
git add src/math_distill_stage2/zulip_archive.py
git commit -m "feat: add zulip archive utilities"
```

Expected: commit includes only the new module.

## Task 3: Sync CLI

**Files:**
- Create: `scripts/data/sync_zulip_channel.py`
- Test: `tests/data/test_zulip_archive.py`

- [ ] **Step 1: Implement the CLI**

Create `scripts/data/sync_zulip_channel.py` with:

```python
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))
    sys.path.insert(0, str(repo_root))

from math_distill_stage2.zulip_archive import (
    DEFAULT_CHANNEL,
    DEFAULT_DIGEST_DIR,
    DEFAULT_OUTPUT_ROOT,
    DEFAULT_SITE,
    ZulipRestClient,
    archive_root_for,
    fetch_full_backfill_messages,
    fetch_incremental_messages,
    load_state,
    parse_since_date,
    read_zulip_config,
    sync_zulip_channel,
    utc_now_iso,
)


def default_config_file() -> Path:
    configured = os.environ.get("ZULIP_CONFIG_FILE")
    if configured:
        return Path(configured).expanduser()
    return Path("~/.zuliprc").expanduser()


def load_fixture(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"fixture must be a JSON list: {path}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", default=DEFAULT_CHANNEL)
    parser.add_argument("--site", default=DEFAULT_SITE)
    parser.add_argument("--config-file", type=Path, default=None)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--digest-dir", type=Path, default=DEFAULT_DIGEST_DIR)
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument("--since", default=None, help="ISO date/datetime for first backfill")
    parser.add_argument("--fixture-json", type=Path, default=None)
    parser.add_argument("--generated-at", default=None)
    args = parser.parse_args()

    generated_at = args.generated_at or utc_now_iso()
    archive_root = archive_root_for(args.output_root)
    state_path = archive_root / "state.json"

    if args.fixture_json is not None:
        raw_messages = load_fixture(args.fixture_json)
        fetched_batches = 1
        site = args.site.rstrip("/")
    else:
        config_path = args.config_file.expanduser() if args.config_file else default_config_file()
        config = read_zulip_config(config_path)
        site = config.site
        client = ZulipRestClient(config)
        state = load_state(state_path)
        last_message_id = int(state.get("last_message_id", 0) or 0)
        if last_message_id:
            raw_messages, fetched_batches = fetch_incremental_messages(
                client,
                channel=args.channel,
                last_message_id=last_message_id,
                batch_size=args.batch_size,
            )
        else:
            raw_messages, fetched_batches = fetch_full_backfill_messages(
                client,
                channel=args.channel,
                batch_size=args.batch_size,
                since_timestamp=parse_since_date(args.since),
            )

    summary = sync_zulip_channel(
        raw_messages=raw_messages,
        archive_root=archive_root,
        digest_dir=args.digest_dir,
        state_path=state_path,
        channel=args.channel,
        site=site,
        fetched_batches=fetched_batches,
        generated_at=generated_at,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the focused archive tests**

Run:

```bash
pytest tests/data/test_zulip_archive.py -q
```

Expected: PASS.

- [ ] **Step 3: Run CLI help manually**

Run:

```bash
python scripts/data/sync_zulip_channel.py --help
```

Expected: exit code 0 and output includes `--fixture-json`, `--output-root`, `--digest-dir`, and `--config-file`.

- [ ] **Step 4: Commit the CLI**

Run:

```bash
git add scripts/data/sync_zulip_channel.py
git commit -m "feat: add zulip sync cli"
```

Expected: commit includes only the CLI.

## Task 4: Project Skill

**Files:**
- Modify: `tests/skills/test_stage2_skills.py`
- Create: `skills/stage2-info-zulip-channel/SKILL.md`
- Create: `skills/stage2-info-zulip-channel/agents/openai.yaml`

- [ ] **Step 1: Write failing skill tests**

Modify `tests/skills/test_stage2_skills.py`:

1. Add `root / "skills" / "stage2-info-zulip-channel"` to the `expected` list in `test_stage2_skill_directories_exist`.
2. Add a new test at the end:

```python
def test_stage2_update_zulip_channel_skill_mentions_archive_and_digest_paths():
    skill_dir = (
        Path(__file__).resolve().parents[2]
        / "skills"
        / "stage2-info-zulip-channel"
    )
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = frontmatter_text(skill_dir)

    assert "name: stage2-info-zulip-channel" in frontmatter
    assert "Zulip" in frontmatter
    assert "scripts/data/sync_zulip_channel.py" in text
    assert "data/raw/references/zulip" in text
    assert "docs/zulip-digests" in text
    assert "ZULIP_CONFIG_FILE" in text
    assert "stage2-info-competition" in text
    assert (skill_dir / "agents" / "openai.yaml").exists()
```

- [ ] **Step 2: Run skill tests to verify they fail**

Run:

```bash
pytest tests/skills/test_stage2_skills.py -q
```

Expected: FAIL because `skills/stage2-info-zulip-channel/` does not exist.

- [ ] **Step 3: Create the skill**

Create `skills/stage2-info-zulip-channel/SKILL.md` with:

```markdown
---
name: stage2-info-zulip-channel
description: Use when the user asks to update, sync, archive, fetch, crawl, summarize, digest, or review the SAIR Zulip Math Distillation Challenge equational theories channel, including daily message summaries or full original Zulip message archives.
---

# Stage2 Info Zulip Channel

Use this skill to sync the SAIR Zulip channel `Math Distillation Challenge - equational theories`, archive original messages, and generate daily Chinese digests.

## Workflow

1. Check credential availability without printing secrets:
   - Prefer `ZULIP_CONFIG_FILE`.
   - Otherwise use `~/.zuliprc`.
   - Expected config fields under `[api]`: `site`, `email`, `key`.
2. Run the reproducible sync command:
   ```bash
   python scripts/data/sync_zulip_channel.py
   ```
3. For a bounded first backfill, pass an ISO date:
   ```bash
   python scripts/data/sync_zulip_channel.py --since 2026-05-01
   ```
4. Confirm updated outputs:
   - `data/raw/references/zulip/math-distillation-challenge-equational-theories/state.json`
   - `data/raw/references/zulip/math-distillation-challenge-equational-theories/messages/YYYY-MM-DD.jsonl`
   - `docs/zulip-digests/YYYY-MM-DD.md`
5. Read the generated digest and preserve source boundaries:
   - Zulip is useful discussion context.
   - Official rules, official API snapshots, and the official judge repository remain authoritative.
   - Use `stage2-info-competition` when a Zulip message claims an official fact that should be checked against official sources.
6. Run focused validation:
   ```bash
   pytest tests/data/test_zulip_archive.py tests/skills/test_stage2_skills.py -q
   ```
7. Report message count, dates, archive paths, digest paths, state path, and validation result.

## Daily Automation

This skill may be used from cron or systemd timer by running:

```bash
cd /home/bing/.openclaw/workspace-fenshen-executor-agent/Math-Distill-Stage2
python scripts/data/sync_zulip_channel.py
```

Do not modify the user's crontab or systemd user units unless explicitly requested.

## Hard Constraints

- Do not print, commit, copy, or summarize Zulip API keys.
- Do not commit `data/raw/` unless the project policy changes; it is local generated snapshot storage.
- Do not rewrite `solver.py`, official run artifacts, official snapshots, or judge certificates while using this skill.
- Do not treat LLM-generated digest text as official fact.
- Keep new user-facing docs in Chinese by default.
- If Zulip credentials are missing or the channel is not accessible, stop after reporting the local credential path checked.
```

Create `skills/stage2-info-zulip-channel/agents/openai.yaml` with:

```yaml
interface:
  display_name: "Stage2 Info Zulip Channel"
  short_description: "Archive Zulip and write daily digests"
  default_prompt: "Use $stage2-info-zulip-channel to sync the Stage 2 Zulip channel, archive original messages, and generate daily Chinese summaries."

policy:
  allow_implicit_invocation: true
```

- [ ] **Step 4: Run skill tests**

Run:

```bash
pytest tests/skills/test_stage2_skills.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit the skill**

Run:

```bash
git add tests/skills/test_stage2_skills.py skills/stage2-info-zulip-channel
git commit -m "feat: add stage2 zulip update skill"
```

Expected: commit includes the skill, metadata, and skill tests.

## Task 5: Documentation Updates

**Files:**
- Modify: `docs/README.md`
- Modify: `docs/data-inventory.md`
- Modify: `docs/architecture.md`
- Test: `tests/skills/test_stage2_skills.py`

- [ ] **Step 1: Add doc expectations to existing tests**

Append these assertions to `test_docs_readme_mentions_solver_skills` in `tests/skills/test_stage2_skills.py`:

```python
    assert "stage2-info-zulip-channel" in text
    assert "zulip-digests" in text
```

Append this assertion to `test_architecture_mentions_solver_first_skills_role`:

```python
    assert "stage2-info-zulip-channel" in text
```

Add this new test:

```python
def test_data_inventory_mentions_zulip_archive_paths():
    text = (Path(__file__).resolve().parents[2] / "docs" / "data-inventory.md").read_text(
        encoding="utf-8"
    )
    assert "data/raw/references/zulip" in text
    assert "docs/zulip-digests" in text
```

- [ ] **Step 2: Run doc-related tests to verify they fail**

Run:

```bash
pytest tests/skills/test_stage2_skills.py -q
```

Expected: FAIL because docs do not mention the new skill and paths yet.

- [ ] **Step 3: Update docs**

In `docs/README.md`, update the core or repository convention sections to include:

```markdown
- `zulip-digests/`：Zulip 频道每日中文摘要。原文归档保存在 `data/raw/references/zulip/`，摘要只作为讨论线索，不替代官方规则快照。
```

Also update the skill sentence so it includes `stage2-info-zulip-channel`:

```markdown
- 当前主线技能包括 `stage2-evaluate`、`stage2-analyze-run`、`stage2-improve-solver`、`stage2-info-competition` 和 `stage2-info-zulip-channel`。
```

In `docs/data-inventory.md`, add a Zulip entry near raw references or local snapshots:

```markdown
### Zulip 频道归档

- 路径：`data/raw/references/zulip/math-distillation-challenge-equational-theories/`
- 内容：`Math Distillation Challenge - equational theories` Zulip 频道可见消息原文归档、`messages/YYYY-MM-DD.jsonl` 和 `state.json`。
- 生成命令：`python scripts/data/sync_zulip_channel.py`
- 摘要路径：`docs/zulip-digests/YYYY-MM-DD.md`
- 说明：Zulip 内容是讨论线索；官方页面、API 和 judge 仓库仍是规则事实的权威来源。
```

In `docs/architecture.md`, update these sections:

- In data snapshot layer, add a bullet:

```markdown
   - `scripts/data/sync_zulip_channel.py` 使用本地 Zulip API 凭据同步 `Math Distillation Challenge - equational theories` 频道，原文归档到 `data/raw/references/zulip/`，每日中文摘要写入 `docs/zulip-digests/`。
```

- In project skill layer, add:

```markdown
   - `skills/stage2-info-zulip-channel`：同步 Zulip 频道原文归档并生成每日中文摘要。
```

- In architecture iteration rules, add:

```markdown
- Zulip 摘要只记录讨论线索；涉及官方事实变更时，必须再用 `stage2-info-competition` 对官方来源做验证。
```

- [ ] **Step 4: Run doc-related tests**

Run:

```bash
pytest tests/skills/test_stage2_skills.py -q
```

Expected: PASS.

- [ ] **Step 5: Commit docs**

Run:

```bash
git add docs/README.md docs/data-inventory.md docs/architecture.md tests/skills/test_stage2_skills.py
git commit -m "docs: document zulip archive workflow"
```

Expected: commit includes docs and the doc assertions.

## Task 6: Verification and Real-Run Readiness

**Files:**
- No new source files.
- Commands validate all files added above.

- [ ] **Step 1: Run focused tests**

Run:

```bash
pytest tests/data/test_zulip_archive.py tests/skills/test_stage2_skills.py -q
```

Expected: PASS.

- [ ] **Step 2: Run data test regression**

Run:

```bash
pytest tests/data/test_download_public_data.py tests/data/test_zulip_archive.py -q
```

Expected: PASS.

- [ ] **Step 3: Run CLI fixture smoke**

Run:

```bash
tmpdir="$(mktemp -d)"
cat > "$tmpdir/messages.json" <<'JSON'
[
  {
    "id": 1,
    "timestamp": 1778284800,
    "sender_full_name": "Smoke Sender",
    "sender_email": "smoke@example.test",
    "sender_id": 1,
    "subject": "solver",
    "content": "Lean certificate smoke https://example.test/smoke",
    "rendered_content": "<p>Lean certificate smoke https://example.test/smoke</p>",
    "reactions": [],
    "stream_id": 13
  }
]
JSON
python scripts/data/sync_zulip_channel.py \
  --fixture-json "$tmpdir/messages.json" \
  --output-root "$tmpdir/data/raw" \
  --digest-dir "$tmpdir/docs/zulip-digests" \
  --generated-at "2026-05-07T01:02:03+00:00"
test -f "$tmpdir/data/raw/references/zulip/math-distillation-challenge-equational-theories/messages/2026-05-05.jsonl"
test -f "$tmpdir/docs/zulip-digests/2026-05-05.md"
```

Expected: all commands exit 0 and the printed JSON summary has `"message_count": 1`.

- [ ] **Step 4: Check git status for scoped changes**

Run:

```bash
git status --short
```

Expected: no uncommitted changes from this feature. Existing unrelated dirty files may remain if they predated the work; do not revert them.

- [ ] **Step 5: Optional real Zulip sync readiness check**

Run only if the user has credentials installed:

```bash
python scripts/data/sync_zulip_channel.py --since 2026-05-01
```

Expected: if credentials are valid and the account can access the channel, the command prints a JSON summary and writes local archive files under `data/raw/references/zulip/` plus Markdown digests under `docs/zulip-digests/`. If credentials are missing, it should fail without printing secrets.

Do not commit `data/raw/` generated by a real sync.

## Self-Review Notes

- Spec coverage: Task 1 covers focused tests; Tasks 2 and 3 cover full archive, digest, state, credentials, API pagination, and fixture mode; Task 4 covers the project skill; Task 5 covers documentation; Task 6 covers validation and real-run readiness.
- Placeholder scan: The plan contains no unfinished placeholder steps or unexpanded "write tests" steps.
- Type consistency: Function names used by tests match the implementation snippets: `normalize_message`, `archive_messages_by_date`, `update_state`, `render_daily_digest`, `sync_zulip_channel`, and `ZulipRestClient`.
