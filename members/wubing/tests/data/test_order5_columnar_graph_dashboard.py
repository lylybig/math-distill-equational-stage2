import base64
import json
from pathlib import Path

from math_distill_stage2.order5_columnar_graph_store import ColumnarImplicationStore
from scripts.data.serve_order5_columnar_graph_dashboard import build_response


def test_dashboard_summary_uses_manifest_without_counting_bits(tmp_path: Path):
    store = ColumnarImplicationStore.create(
        tmp_path / "store",
        law_count=4,
        layers=("true", "false", "conflict"),
    )
    store.set_pair("true", eq1_id=1, eq2_id=2)

    status, content_type, body = build_response(
        "/api/summary?evidence_limit=5",
        store_dir=tmp_path / "store",
    )

    assert status == 200
    assert content_type.startswith("application/json")
    payload = json.loads(body)
    assert payload["law_count"] == 4
    assert payload["pair_count"] == 12
    assert payload["row_width"] == 3
    assert "set_bits" not in payload["layers"][0]
    assert payload["evidence"]["batch_log_line_count"] == 0
    assert "exact_counts" not in payload

    status, _, body = build_response(
        "/api/summary?count_bits=1",
        store_dir=tmp_path / "store",
    )
    counted = json.loads(body)
    true_layer = next(layer for layer in counted["layers"] if layer["name"] == "true")
    assert status == 200
    assert true_layer["set_bits"] == 1
    assert true_layer["density"] == 1 / 12
    assert counted["exact_counts"]["exact_known_count"] == 1
    assert counted["exact_counts"]["exact_unknown_count"] == 11
    assert "counted_at_unix" in counted["exact_counts"]
    assert (tmp_path / "store" / "evidence" / "exact_count_latest.json").exists()
    assert (tmp_path / "store" / "evidence" / "exact_count_history.jsonl").exists()

    status, _, body = build_response(
        "/api/summary",
        store_dir=tmp_path / "store",
    )
    cached = json.loads(body)
    assert status == 200
    assert cached["exact_counts"]["exact_known_count"] == 1
    assert cached["exact_counts"]["exact_unknown_count"] == 11


def test_dashboard_pair_status_supports_eq_pair_without_chain_lookup(tmp_path: Path):
    store = ColumnarImplicationStore.create(
        tmp_path / "store",
        law_count=4,
        layers=("true", "false", "conflict"),
    )
    store.set_pair("false", eq1_id=3, eq2_id=4)
    store.set_pair("true", eq1_id=1, eq2_id=2)
    store.set_pair("true", eq1_id=2, eq2_id=4)

    status, _, body = build_response(
        "/api/status?source_id=3&target_id=4",
        store_dir=tmp_path / "store",
    )
    payload = json.loads(body)

    assert status == 200
    assert payload["verdict"] == "false"
    assert payload["layers"]["false"] is True
    assert "exact_true_chain" not in payload

    status, _, body = build_response(
        "/api/status?source_id=1&target_id=4",
        store_dir=tmp_path / "store",
    )
    assert status == 200
    payload = json.loads(body)
    assert payload["eq2_id"] == 4
    assert "exact_true_chain" not in payload


def test_dashboard_row_endpoints_and_static_index(tmp_path: Path):
    store = ColumnarImplicationStore.create(
        tmp_path / "store",
        law_count=5,
        layers=("true", "false", "conflict"),
    )
    store.set_pair("true", eq1_id=1, eq2_id=2)
    store.set_pair("false", eq1_id=1, eq2_id=3)

    status, _, body = build_response(
        "/api/row-summary?source_id=1",
        store_dir=tmp_path / "store",
    )
    assert status == 200
    assert json.loads(body)["unknown_count"] == 2

    status, _, body = build_response(
        "/api/frontier?source_id=1&limit=1",
        store_dir=tmp_path / "store",
    )
    assert status == 200
    assert json.loads(body)["targets"] == [4]

    status, _, body = build_response("/", store_dir=tmp_path / "store")
    assert status == 200
    assert b"Order5 Implication Graph" in body


def test_dashboard_row_map_encodes_one_source_row(tmp_path: Path):
    store = ColumnarImplicationStore.create(
        tmp_path / "store",
        law_count=5,
        layers=("true", "false", "approx_true", "approx_false", "conflict"),
    )
    store.set_pair("true", eq1_id=1, eq2_id=2)
    store.set_pair("false", eq1_id=1, eq2_id=3)
    store.set_pair("approx_true", eq1_id=1, eq2_id=4)

    status, _, body = build_response(
        "/api/row-map?source_id=1",
        store_dir=tmp_path / "store",
    )
    payload = json.loads(body)
    status_codes = list(base64.b64decode(payload["status_bytes_b64"]))

    assert status == 200
    assert payload["source_id"] == 1
    assert payload["row_width"] == 4
    assert status_codes == [1, 2, 4, 0]
    assert payload["counts"]["true"] == 1
    assert payload["counts"]["false"] == 1
    assert payload["counts"]["approx_true"] == 1
    assert payload["counts"]["unknown"] == 1


def test_dashboard_target_endpoints_scan_sources_for_one_target(tmp_path: Path):
    store = ColumnarImplicationStore.create(
        tmp_path / "store",
        law_count=5,
        layers=("true", "false", "approx_true", "approx_false", "conflict"),
    )
    store.set_pair("true", eq1_id=1, eq2_id=3)
    store.set_pair("false", eq1_id=2, eq2_id=3)
    store.set_pair("approx_true", eq1_id=4, eq2_id=3)

    status, _, body = build_response(
        "/api/target-map?target_id=3",
        store_dir=tmp_path / "store",
    )
    payload = json.loads(body)
    status_codes = list(base64.b64decode(payload["status_bytes_b64"]))

    assert status == 200
    assert payload["target_id"] == 3
    assert payload["column_width"] == 4
    assert status_codes == [1, 2, 4, 0]
    assert payload["counts"]["true"] == 1
    assert payload["counts"]["false"] == 1
    assert payload["counts"]["approx_true"] == 1
    assert payload["counts"]["unknown"] == 1

    status, _, body = build_response(
        "/api/target-sources?target_id=3&layer=true",
        store_dir=tmp_path / "store",
    )
    assert status == 200
    assert json.loads(body)["sources"] == [1]
