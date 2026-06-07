#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Sequence
from urllib.parse import parse_qs, unquote, urlsplit

if __package__ in (None, ""):
    repo_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo_root / "src"))
    sys.path.insert(0, str(repo_root))

from math_distill_stage2.order5_columnar_graph_store import (  # noqa: E402
    DEFAULT_STORE_DIR,
    ColumnarImplicationStore,
)
from math_distill_stage2.order5_pair_dataset import read_equations  # noqa: E402


DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
ASSET_DIR = Path(__file__).resolve().parent / "order5_columnar_graph_dashboard"
COUNT_LATEST_PATH = Path("evidence/exact_count_latest.json")
COUNT_HISTORY_PATH = Path("evidence/exact_count_history.jsonl")
_EQUATION_CACHE: dict[Path, list[str]] = {}


def build_response(
    raw_path: str,
    *,
    method: str = "GET",
    store_dir: Path = DEFAULT_STORE_DIR,
    static_dir: Path = ASSET_DIR,
) -> tuple[int, str, bytes]:
    parsed = urlsplit(raw_path)
    path = parsed.path
    query = parse_qs(parsed.query)
    method = method.upper()
    if method != "GET":
        return _json_response(405, {"error": "method_not_allowed", "method": method})

    try:
        if path == "/api/health":
            payload = {
                "service": "order5-columnar-graph-dashboard",
                "status": "ok",
                "store_dir": str(store_dir),
            }
            return _json_response(200, payload)
        if path == "/api/summary":
            payload = build_summary(
                store_dir,
                count_bits=_bool_param(query, "count_bits", default=False),
                evidence_limit=_int_param(query, "evidence_limit", default=12, minimum=0, maximum=200),
            )
            return _json_response(200, payload)
        if path == "/api/evidence":
            store = ColumnarImplicationStore.open(store_dir)
            payload = build_evidence_summary(
                Path(store_dir),
                store.manifest,
                limit=_int_param(query, "limit", default=50, minimum=0, maximum=500),
            )
            return _json_response(200, payload)
        if path == "/api/status":
            payload = build_pair_status(store_dir, query)
            return _json_response(200, payload)
        if path == "/api/row-summary":
            payload = build_row_summary(store_dir, query)
            return _json_response(200, payload)
        if path == "/api/frontier":
            payload = build_frontier(store_dir, query)
            return _json_response(200, payload)
        if path == "/api/row-targets":
            payload = build_row_targets(store_dir, query)
            return _json_response(200, payload)
        if path == "/api/row-map":
            payload = build_row_map(store_dir, query)
            return _json_response(200, payload)
        if path == "/api/target-summary":
            payload = build_target_summary(store_dir, query)
            return _json_response(200, payload)
        if path == "/api/target-sources":
            payload = build_target_sources(store_dir, query)
            return _json_response(200, payload)
        if path == "/api/target-map":
            payload = build_target_map(store_dir, query)
            return _json_response(200, payload)
    except (FileNotFoundError, KeyError, ValueError, IndexError, OSError, json.JSONDecodeError) as exc:
        return _json_response(400, {"error": exc.__class__.__name__, "message": str(exc)})

    return _static_response(path, static_dir=static_dir)


def build_summary(
    store_dir: Path,
    *,
    count_bits: bool = False,
    evidence_limit: int = 12,
) -> dict:
    started_at = time.perf_counter()
    store_path = Path(store_dir)
    store = ColumnarImplicationStore.open(store_path)
    manifest = store.manifest
    row_width = store.law_count if store.include_self else store.law_count - 1
    layer_rows = []
    for layer_name, record in manifest["layers"].items():
        bitset_path = store_path / record["bitset_path"]
        layer_row = {
            "name": layer_name,
            "bitset_path": str(bitset_path),
            "bit_count": int(record["bit_count"]),
            "byte_count": int(record["byte_count"]),
            "file": _file_summary(bitset_path),
        }
        if count_bits:
            set_bits = store.layer_count(layer_name)
            layer_row["set_bits"] = set_bits
            layer_row["density"] = set_bits / store.pair_count if store.pair_count else 0.0
        layer_rows.append(layer_row)

    latest_counts = load_latest_count_bits(store_path)
    payload = {
        "store_dir": str(store_path),
        "generated_at_unix": time.time(),
        "manifest": manifest,
        "law_count": store.law_count,
        "include_self": store.include_self,
        "row_width": row_width,
        "pair_count": store.pair_count,
        "layers": layer_rows,
        "evidence": build_evidence_summary(store_path, manifest, limit=evidence_limit),
    }
    if count_bits:
        exact_counts = store.exact_pair_counts()
        latest_counts = save_count_bits_record(
            store_path,
            store=store,
            layer_rows=layer_rows,
            exact_counts=exact_counts,
            elapsed_seconds=time.perf_counter() - started_at,
        )
    if latest_counts:
        payload["exact_counts"] = latest_counts["exact_counts"]
        payload["count_bits_cache"] = {
            "latest_path": str(store_path / COUNT_LATEST_PATH),
            "history_path": str(store_path / COUNT_HISTORY_PATH),
        }
    return payload


def build_evidence_summary(store_dir: Path, manifest: dict, *, limit: int) -> dict:
    evidence_record = manifest.get("evidence", {})
    batch_path = store_dir / evidence_record.get("batch_log_path", "evidence/evidence_batches.jsonl")
    pair_path = store_dir / evidence_record.get("pair_log_path", "evidence/pair_evidence.jsonl")
    batch_file = _file_summary(batch_path)
    pair_file = _file_summary(pair_path)
    return {
        "batch_log_path": str(batch_path),
        "batch_log": batch_file,
        "batch_log_line_count": _line_count_if_small(batch_path),
        "pair_log_path": str(pair_path),
        "pair_log": pair_file,
        "pair_log_line_count": _line_count_if_small(pair_path),
        "last_batches": _read_jsonl_tail(batch_path, limit=limit),
    }


def load_latest_count_bits(store_dir: Path) -> dict | None:
    path = Path(store_dir) / COUNT_LATEST_PATH
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_count_bits_record(
    store_dir: Path,
    *,
    store: ColumnarImplicationStore,
    layer_rows: list[dict],
    exact_counts: dict,
    elapsed_seconds: float,
) -> dict:
    counted_at_unix = time.time()
    record = {
        "kind": "order5_columnar_graph_count_bits",
        "counted_at_unix": counted_at_unix,
        "counted_at_iso": _iso_from_unix(counted_at_unix),
        "elapsed_seconds": elapsed_seconds,
        "law_count": store.law_count,
        "pair_count": store.pair_count,
        "exact_counts": {
            **exact_counts,
            "counted_at_unix": counted_at_unix,
            "counted_at_iso": _iso_from_unix(counted_at_unix),
        },
        "layer_counts": {
            row["name"]: {
                "set_bits": row.get("set_bits"),
                "density": row.get("density"),
            }
            for row in layer_rows
            if "set_bits" in row
        },
    }
    latest_path = Path(store_dir) / COUNT_LATEST_PATH
    history_path = Path(store_dir) / COUNT_HISTORY_PATH
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    latest_path.write_text(json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    with history_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
        handle.write("\n")
    return record


def build_pair_status(store_dir: Path, query: dict[str, list[str]]) -> dict:
    store = ColumnarImplicationStore.open(store_dir)
    layers = _csv_param(query, "layers")
    if _first(query, "pair_index"):
        result = store.status(pair_index=_int_param(query, "pair_index", minimum=0), layers=layers)
    else:
        result = store.status(
            eq1_id=_int_param(query, "source_id", minimum=1),
            eq2_id=_int_param(query, "target_id", minimum=1),
            layers=layers,
        )
    return {**result, "equations": _equations_for_pair(store_dir, store.manifest, result)}


def build_row_summary(store_dir: Path, query: dict[str, list[str]]) -> dict:
    store = ColumnarImplicationStore.open(store_dir)
    return store.row_summary(
        _int_param(query, "source_id", minimum=1),
        layers=_csv_param(query, "layers"),
    )


def build_frontier(store_dir: Path, query: dict[str, list[str]]) -> dict:
    store = ColumnarImplicationStore.open(store_dir)
    return store.source_frontier(
        _int_param(query, "source_id", minimum=1),
        known_layers=_csv_param(query, "known_layers") or ("true", "false"),
        limit=_int_param(query, "limit", default=20, minimum=0, maximum=1000),
    )


def build_row_targets(store_dir: Path, query: dict[str, list[str]]) -> dict:
    store = ColumnarImplicationStore.open(store_dir)
    layer = _first(query, "layer") or "true"
    source_id = _int_param(query, "source_id", minimum=1)
    limit = _int_param(query, "limit", default=50, minimum=0, maximum=1000)
    return {
        "layer": layer,
        "source_id": source_id,
        "targets": store.row_targets(layer, source_id, limit=limit),
        "limit": limit,
    }


def build_row_map(store_dir: Path, query: dict[str, list[str]]) -> dict:
    store = ColumnarImplicationStore.open(store_dir)
    source_id = _int_param(query, "source_id", minimum=1)
    if source_id > store.law_count:
        raise ValueError(f"source_id must be <= {store.law_count}; got {source_id}")
    row_width = store.law_count if store.include_self else store.law_count - 1
    row_start = (source_id - 1) * row_width
    masks = {}
    for layer_name in store.layers:
        with store.layer(layer_name).open() as layer:
            masks[layer_name] = layer.window_mask(row_start, row_width)

    true_mask = masks.get("true", 0)
    false_mask = masks.get("false", 0)
    conflict_mask = masks.get("conflict", 0) | (true_mask & false_mask)
    approx_true_mask = masks.get("approx_true", 0)
    approx_false_mask = masks.get("approx_false", 0)
    status_codes = bytearray(row_width)
    counts = {
        "unknown": 0,
        "true": 0,
        "false": 0,
        "conflict": 0,
        "approx_true": 0,
        "approx_false": 0,
        "approx_both": 0,
    }
    true_bits = true_mask
    false_bits = false_mask
    conflict_bits = conflict_mask
    approx_true_bits = approx_true_mask
    approx_false_bits = approx_false_mask
    for slot in range(row_width):
        if conflict_bits & 1:
            code = 3
            counts["conflict"] += 1
        elif true_bits & 1:
            code = 1
            counts["true"] += 1
        elif false_bits & 1:
            code = 2
            counts["false"] += 1
        elif (approx_true_bits & 1) and (approx_false_bits & 1):
            code = 6
            counts["approx_both"] += 1
        elif approx_true_bits & 1:
            code = 4
            counts["approx_true"] += 1
        elif approx_false_bits & 1:
            code = 5
            counts["approx_false"] += 1
        else:
            code = 0
            counts["unknown"] += 1
        status_codes[slot] = code
        true_bits >>= 1
        false_bits >>= 1
        conflict_bits >>= 1
        approx_true_bits >>= 1
        approx_false_bits >>= 1

    return {
        "source_id": source_id,
        "law_count": store.law_count,
        "include_self": store.include_self,
        "row_width": row_width,
        "code_format": "one byte per row slot, target order excludes source when include_self=false",
        "status_bytes_b64": base64.b64encode(bytes(status_codes)).decode("ascii"),
        "counts": counts,
        "legend": {
            "0": "unknown",
            "1": "true",
            "2": "false",
            "3": "conflict",
            "4": "approx_true",
            "5": "approx_false",
            "6": "approx_both",
        },
    }


def build_target_summary(store_dir: Path, query: dict[str, list[str]]) -> dict:
    store = ColumnarImplicationStore.open(store_dir)
    return store.target_summary(
        _int_param(query, "target_id", minimum=1),
        layers=_csv_param(query, "layers"),
    )


def build_target_sources(store_dir: Path, query: dict[str, list[str]]) -> dict:
    store = ColumnarImplicationStore.open(store_dir)
    layer = _first(query, "layer") or "true"
    target_id = _int_param(query, "target_id", minimum=1)
    limit = _int_param(query, "limit", default=50, minimum=0, maximum=1000)
    return {
        "layer": layer,
        "target_id": target_id,
        "sources": store.target_sources(layer, target_id, limit=limit),
        "limit": limit,
    }


def build_target_map(store_dir: Path, query: dict[str, list[str]]) -> dict:
    store = ColumnarImplicationStore.open(store_dir)
    result = store.target_map(
        _int_param(query, "target_id", minimum=1),
        layers=_csv_param(query, "layers"),
    )
    status_codes = result.pop("status_codes")
    return {
        **result,
        "status_bytes_b64": base64.b64encode(status_codes).decode("ascii"),
    }


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "Order5GraphDashboard/0.1"

    def do_GET(self) -> None:
        store_dir = Path(getattr(self.server, "store_dir"))  # type: ignore[arg-type]
        static_dir = Path(getattr(self.server, "static_dir"))  # type: ignore[arg-type]
        status, content_type, body = build_response(
            self.path,
            method="GET",
            store_dir=store_dir,
            static_dir=static_dir,
        )
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store" if self.path.startswith("/api/") else "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def run_server(
    *,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    store_dir: Path = DEFAULT_STORE_DIR,
    static_dir: Path = ASSET_DIR,
) -> None:
    httpd = ThreadingHTTPServer((host, port), DashboardHandler)
    httpd.store_dir = Path(store_dir)
    httpd.static_dir = Path(static_dir)
    print(f"order5 graph dashboard listening on http://{host}:{port}", flush=True)
    print(f"store: {store_dir}", flush=True)
    httpd.serve_forever()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Serve a local dashboard for the order5 columnar implication graph.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--store-dir", type=Path, default=DEFAULT_STORE_DIR)
    parser.add_argument("--static-dir", type=Path, default=ASSET_DIR)
    args = parser.parse_args(argv)

    run_server(
        host=args.host,
        port=args.port,
        store_dir=args.store_dir,
        static_dir=args.static_dir,
    )
    return 0


def _static_response(path: str, *, static_dir: Path) -> tuple[int, str, bytes]:
    requested = "/index.html" if path in {"", "/"} else path
    if requested.startswith("/assets/"):
        relative = requested.removeprefix("/assets/")
    elif requested == "/index.html":
        relative = "index.html"
    else:
        return _json_response(404, {"error": "not_found", "path": path})
    safe_relative = Path(unquote(relative))
    if safe_relative.is_absolute() or ".." in safe_relative.parts:
        return _json_response(404, {"error": "not_found", "path": path})
    file_path = static_dir / safe_relative
    if not file_path.is_file():
        return _json_response(404, {"error": "not_found", "path": path})
    content_type = {
        ".css": "text/css; charset=utf-8",
        ".html": "text/html; charset=utf-8",
        ".js": "application/javascript; charset=utf-8",
    }.get(file_path.suffix, "application/octet-stream")
    return 200, content_type, file_path.read_bytes()


def _json_response(status: int, payload: object) -> tuple[int, str, bytes]:
    return (
        status,
        "application/json; charset=utf-8",
        json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8"),
    )


def _file_summary(path: Path) -> dict:
    if not path.exists():
        return {"exists": False}
    stat = path.stat()
    return {
        "exists": True,
        "bytes": stat.st_size,
        "modified_at_unix": stat.st_mtime,
        "modified_at_iso": _iso_from_unix(stat.st_mtime),
    }


def _line_count_if_small(path: Path, *, max_bytes: int = 32 * 1024 * 1024) -> int | None:
    if not path.exists():
        return 0
    if path.stat().st_size > max_bytes:
        return None
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def _read_jsonl_tail(path: Path, *, limit: int) -> list[dict]:
    if limit <= 0 or not path.exists():
        return []
    raw_tail = _read_tail_lines(path, limit=limit)
    rows = []
    for line in raw_tail:
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            rows.append({"raw": line, "parse_error": str(exc)})
    return rows


def _read_tail_lines(path: Path, *, limit: int, chunk_size: int = 8192) -> list[str]:
    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        cursor = handle.tell()
        chunks: list[bytes] = []
        line_count = 0
        while cursor > 0 and line_count <= limit:
            read_size = min(chunk_size, cursor)
            cursor -= read_size
            handle.seek(cursor)
            chunk = handle.read(read_size)
            chunks.append(chunk)
            line_count += chunk.count(b"\n")
        data = b"".join(reversed(chunks))
    return data.decode("utf-8", errors="replace").splitlines()[-limit:]


def _equations_for_pair(store_dir: Path, manifest: dict, status: dict) -> dict:
    equations_path = _resolve_manifest_path(store_dir, manifest.get("equations_path"))
    if equations_path is None or not equations_path.exists():
        return {}
    equations = _EQUATION_CACHE.get(equations_path)
    if equations is None:
        equations = read_equations(equations_path)
        _EQUATION_CACHE[equations_path] = equations
    return {
        "source": equations[int(status["eq1_id"]) - 1],
        "target": equations[int(status["eq2_id"]) - 1],
    }


def _resolve_manifest_path(store_dir: Path, raw: object) -> Path | None:
    if not raw:
        return None
    path = Path(str(raw))
    if path.is_absolute():
        return path
    candidates = (
        Path.cwd() / path,
        Path(__file__).resolve().parents[2] / path,
        Path(store_dir).parent.parent / path,
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return (Path.cwd() / path).resolve()


def _int_param(
    query: dict[str, list[str]],
    name: str,
    *,
    default: int | None = None,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    raw = _first(query, name)
    if raw is None or raw == "":
        if default is None:
            raise ValueError(f"missing required integer parameter: {name}")
        value = default
    else:
        value = int(raw)
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be >= {minimum}; got {value}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{name} must be <= {maximum}; got {value}")
    return value


def _bool_param(query: dict[str, list[str]], name: str, *, default: bool = False) -> bool:
    raw = _first(query, name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


def _csv_param(query: dict[str, list[str]], name: str) -> tuple[str, ...] | None:
    raw = _first(query, name)
    if not raw:
        return None
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def _first(query: dict[str, list[str]], name: str) -> str | None:
    values = query.get(name)
    if not values:
        return None
    return values[0]


def _iso_from_unix(timestamp: float) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))


if __name__ == "__main__":
    raise SystemExit(main())
