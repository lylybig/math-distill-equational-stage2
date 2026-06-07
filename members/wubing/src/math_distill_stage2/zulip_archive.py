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
    return {
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
    payload = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
        for row in rows
    )
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
        write_jsonl(path, [merged[key] for key in sorted(merged)])
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


def _message_text(record: dict[str, Any]) -> str:
    return f"{record.get('topic', '')} {record.get('content', '')}"


def _section_records(records: list[dict[str, Any]], words: tuple[str, ...]) -> list[dict[str, Any]]:
    result = []
    for record in records:
        text = _message_text(record).lower()
        if any(word in text for word in words):
            result.append(record)
    return result


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
        if _contains_keyword(_message_text(record)):
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
            topic = record.get("topic") or "(empty topic)"
            lines.append(f"- 消息 {record['id']}（{topic}）：{_excerpt(record.get('content', ''))}")
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
    official_records = _section_records(keyword_records, ("rule", "rules", "official", "dataset"))
    if official_records:
        for record in official_records:
            lines.append(f"- 消息 {record['id']}：{_excerpt(record.get('content', ''))}")
    else:
        lines.append("- 无明确规则、官方信息或数据集关键词命中。")

    lines.extend(["", "## Judge / Lean / Certificate", ""])
    proof_records = _section_records(keyword_records, ("judge", "lean", "certificate"))
    if proof_records:
        for record in proof_records:
            lines.append(f"- 消息 {record['id']}：{_excerpt(record.get('content', ''))}")
    else:
        lines.append("- 无 judge、Lean 或 certificate 关键词命中。")

    lines.extend(["", "## Solver 策略线索", ""])
    solver_records = _section_records(keyword_records, ("solver",))
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

    lines.extend(
        [
            "",
            "## 待跟进",
            "",
            "- 需要人工复查摘要中的 Zulip 信息是否已被官方规则或 judge 仓库确认。",
            "",
            "## 原文索引",
            "",
        ]
    )
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
        raw_batch = payload.get("messages", [])
        if not raw_batch:
            break
        if since_timestamp is None:
            messages.extend(raw_batch)
        else:
            messages.extend(
                message
                for message in raw_batch
                if int(message["timestamp"]) >= since_timestamp
            )
            if min(int(message["timestamp"]) for message in raw_batch) < since_timestamp:
                break
        if payload.get("found_oldest"):
            break
        anchor = min(int(message["id"]) for message in raw_batch)
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
