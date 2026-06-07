from __future__ import annotations

import hashlib
import json
import mmap
import time
from collections import Counter
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from math_distill_stage2.counterexample.finite_magma import FiniteMagma
from math_distill_stage2.equations import parse_equation
from math_distill_stage2.order5_pair_dataset import read_equations
from math_distill_stage2.order5_pair_space import (
    DEFAULT_EQUATIONS_PATH,
    ids_to_pair_index,
    pair_count,
    pair_index_to_ids,
)


DEFAULT_STORE_DIR = Path("data/processed/order5_columnar_graph_store")
DEFAULT_LAYERS = (
    "true",
    "false",
    "approx_true",
    "approx_false",
    "conflict",
)
EXACT_VERDICT_LAYERS = {"true", "false"}
APPROX_VERDICT_LAYERS = {"approx_true", "approx_false"}
_BYTE_BIT_COUNTS = tuple(bin(value).count("1") for value in range(256))


def _bit_count(value: int) -> int:
    if hasattr(value, "bit_count"):
        return value.bit_count()
    if 0 <= value < 256:
        return _BYTE_BIT_COUNTS[value]
    return bin(value).count("1")


@dataclass(frozen=True)
class BitsetLayer:
    path: Path
    bit_count: int
    writable: bool = False

    @property
    def byte_count(self) -> int:
        return (self.bit_count + 7) // 8

    @classmethod
    def create(cls, path: Path, bit_count: int) -> "BitsetLayer":
        if bit_count < 0:
            raise ValueError(f"bit_count must be non-negative; got {bit_count}")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("ab") as handle:
            handle.truncate((bit_count + 7) // 8)
        return cls(path=path, bit_count=bit_count, writable=True)

    def open(self) -> "OpenBitsetLayer":
        return OpenBitsetLayer(self.path, self.bit_count, writable=self.writable)


class OpenBitsetLayer:
    def __init__(self, path: Path, bit_count: int, *, writable: bool = False) -> None:
        if bit_count <= 0:
            raise ValueError("bit_count must be positive for mmap-backed layers")
        self.path = Path(path)
        self.bit_count = bit_count
        self.writable = writable
        self.byte_count = (bit_count + 7) // 8
        mode = "r+b" if writable else "rb"
        self._handle = self.path.open(mode)
        actual_size = self.path.stat().st_size
        if actual_size != self.byte_count:
            self._handle.close()
            raise ValueError(
                f"{self.path} has {actual_size} bytes; expected {self.byte_count}"
            )
        access = mmap.ACCESS_WRITE if writable else mmap.ACCESS_READ
        self._mmap = mmap.mmap(self._handle.fileno(), self.byte_count, access=access)

    def __enter__(self) -> "OpenBitsetLayer":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def close(self) -> None:
        if self.writable:
            self._mmap.flush()
        self._mmap.close()
        self._handle.close()

    def get(self, bit_index: int) -> bool:
        self._validate_index(bit_index)
        byte_index = bit_index >> 3
        mask = 1 << (bit_index & 7)
        return bool(self._mmap[byte_index] & mask)

    def set(self, bit_index: int) -> bool:
        if not self.writable:
            raise OSError("bitset layer is read-only")
        self._validate_index(bit_index)
        byte_index = bit_index >> 3
        mask = 1 << (bit_index & 7)
        old_byte = self._mmap[byte_index]
        if old_byte & mask:
            return False
        self._mmap[byte_index] = old_byte | mask
        return True

    def clear(self, bit_index: int) -> bool:
        if not self.writable:
            raise OSError("bitset layer is read-only")
        self._validate_index(bit_index)
        byte_index = bit_index >> 3
        mask = 1 << (bit_index & 7)
        old_byte = self._mmap[byte_index]
        if not old_byte & mask:
            return False
        self._mmap[byte_index] = old_byte & ~mask
        return True

    def count(self, *, chunk_size: int = 8 * 1024 * 1024) -> int:
        total = 0
        for offset in range(0, self.byte_count, chunk_size):
            chunk = self._mmap[offset : min(offset + chunk_size, self.byte_count)]
            total += sum(_bit_count(byte) for byte in chunk)
        unused_bits = self.byte_count * 8 - self.bit_count
        if unused_bits:
            last_byte = self._mmap[self.byte_count - 1]
            total -= _bit_count(last_byte >> (8 - unused_bits))
        return total

    def iter_set_bits(
        self,
        *,
        start: int = 0,
        stop: int | None = None,
    ) -> Iterator[int]:
        stop = self.bit_count if stop is None else stop
        if start < 0 or stop < start or stop > self.bit_count:
            raise ValueError(f"invalid bit range: [{start}, {stop})")
        if start == stop:
            return
        start_byte = start >> 3
        end_byte = (stop + 7) >> 3
        for byte_index in range(start_byte, end_byte):
            value = self._mmap[byte_index]
            if value == 0:
                continue
            base = byte_index << 3
            while value:
                low_bit = value & -value
                bit_offset = low_bit.bit_length() - 1
                bit_index = base + bit_offset
                if start <= bit_index < stop:
                    yield bit_index
                value ^= low_bit

    def set_many(self, bit_indexes: Iterable[int]) -> int:
        changed = 0
        for bit_index in bit_indexes:
            if self.set(bit_index):
                changed += 1
        return changed

    def or_mask(self, start_bit: int, width: int, mask: int) -> tuple[int, int]:
        if not self.writable:
            raise OSError("bitset layer is read-only")
        self._validate_window(start_bit, width)
        if mask < 0:
            raise ValueError("mask must be non-negative")
        if width == 0 or mask == 0:
            return 0, 0
        if mask.bit_length() > width:
            mask &= (1 << width) - 1
        if mask == 0:
            return 0, 0

        bit_offset = start_bit & 7
        byte_start = start_bit >> 3
        byte_count = (bit_offset + width + 7) // 8
        shifted_mask = mask << bit_offset
        mask_bytes = shifted_mask.to_bytes(byte_count, "little")
        current = self._mmap[byte_start : byte_start + byte_count]
        updated = bytearray(current)
        newly_set_count = 0
        for index, mask_byte in enumerate(mask_bytes):
            if mask_byte == 0:
                continue
            old_byte = updated[index]
            changed_byte = mask_byte & ~old_byte
            if changed_byte:
                newly_set_count += _bit_count(changed_byte)
                updated[index] = old_byte | mask_byte
        if newly_set_count:
            self._mmap[byte_start : byte_start + byte_count] = updated
        return newly_set_count, _bit_count(mask) - newly_set_count

    def window_mask(self, start_bit: int, width: int) -> int:
        self._validate_window(start_bit, width)
        if width == 0:
            return 0
        bit_offset = start_bit & 7
        byte_start = start_bit >> 3
        byte_count = (bit_offset + width + 7) // 8
        raw = self._mmap[byte_start : byte_start + byte_count]
        return (int.from_bytes(raw, "little") >> bit_offset) & ((1 << width) - 1)

    def _validate_index(self, bit_index: int) -> None:
        if bit_index < 0 or bit_index >= self.bit_count:
            raise IndexError(f"bit_index must be in [0, {self.bit_count}); got {bit_index}")

    def _validate_window(self, start_bit: int, width: int) -> None:
        if start_bit < 0 or width < 0 or start_bit + width > self.bit_count:
            raise IndexError(
                f"bit window must fit in [0, {self.bit_count}); "
                f"got start={start_bit}, width={width}"
            )


@dataclass(frozen=True)
class ImportSummary:
    layer: str
    source_path: str
    read_count: int
    newly_set_count: int
    already_set_count: int
    conflict_count: int
    sha256: str
    elapsed_seconds: float

    def to_json(self) -> dict:
        return {
            "layer": self.layer,
            "source_path": self.source_path,
            "read_count": self.read_count,
            "newly_set_count": self.newly_set_count,
            "already_set_count": self.already_set_count,
            "conflict_count": self.conflict_count,
            "sha256": self.sha256,
            "elapsed_seconds": self.elapsed_seconds,
        }


class ColumnarImplicationStore:
    def __init__(self, store_dir: Path, manifest: dict) -> None:
        self.store_dir = Path(store_dir)
        self.manifest = manifest
        self.law_count = int(manifest["law_count"])
        self.include_self = bool(manifest.get("include_self", False))
        self.pair_count = int(manifest["pair_count"])
        self.layers = tuple(manifest["layers"].keys())

    @classmethod
    def create(
        cls,
        store_dir: Path = DEFAULT_STORE_DIR,
        *,
        law_count: int | None = None,
        equations_path: Path = DEFAULT_EQUATIONS_PATH,
        include_self: bool = False,
        layers: Iterable[str] = DEFAULT_LAYERS,
        force: bool = False,
    ) -> "ColumnarImplicationStore":
        store_dir = Path(store_dir)
        manifest_path = store_dir / "manifest.json"
        if manifest_path.exists() and not force:
            raise FileExistsError(f"{manifest_path} already exists; pass force=True to replace")

        if law_count is None:
            law_count = len(read_equations(equations_path))
        total_pairs = pair_count(law_count, include_self=include_self)
        layer_names = tuple(dict.fromkeys(layers))
        if not layer_names:
            raise ValueError("at least one layer is required")

        layers_dir = store_dir / "layers"
        evidence_dir = store_dir / "evidence"
        store_dir.mkdir(parents=True, exist_ok=True)
        layers_dir.mkdir(parents=True, exist_ok=True)
        evidence_dir.mkdir(parents=True, exist_ok=True)

        layer_manifest: dict[str, dict] = {}
        for layer_name in layer_names:
            _validate_layer_name(layer_name)
            relative_path = Path("layers") / f"{layer_name}.bitset"
            BitsetLayer.create(store_dir / relative_path, total_pairs)
            layer_manifest[layer_name] = {
                "bitset_path": str(relative_path),
                "bit_count": total_pairs,
                "byte_count": (total_pairs + 7) // 8,
            }

        manifest = {
            "schema_version": 1,
            "kind": "order5_columnar_implication_store",
            "description": (
                "Mmap-backed bitset layers over the implicit directed order<=5 pair space, "
                "with append-only JSONL evidence sidecars."
            ),
            "law_count": law_count,
            "include_self": include_self,
            "pair_count": total_pairs,
            "pair_index_base": 0,
            "eq_id_base": 1,
            "bit_order": "least_significant_bit_first_within_each_byte",
            "layers": layer_manifest,
            "evidence": {
                "batch_log_path": "evidence/evidence_batches.jsonl",
                "pair_log_path": "evidence/pair_evidence.jsonl",
            },
            "created_at_unix": time.time(),
            "equations_path": str(equations_path),
            "equations_sha256": _sha256_file(equations_path)
            if Path(equations_path).exists()
            else None,
        }
        _write_json(manifest_path, manifest)
        return cls(store_dir, manifest)

    @classmethod
    def open(cls, store_dir: Path = DEFAULT_STORE_DIR) -> "ColumnarImplicationStore":
        store_dir = Path(store_dir)
        manifest = json.loads((store_dir / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("kind") != "order5_columnar_implication_store":
            raise ValueError(f"not an order5 columnar implication store: {store_dir}")
        return cls(store_dir, manifest)

    def layer(self, layer_name: str, *, writable: bool = False) -> BitsetLayer:
        layer_record = self._layer_record(layer_name)
        bitset_path = self.store_dir / layer_record["bitset_path"]
        return BitsetLayer(
            path=bitset_path,
            bit_count=int(layer_record["bit_count"]),
            writable=writable,
        )

    def has_layer(self, layer_name: str) -> bool:
        return layer_name in self.manifest["layers"]

    def ids_to_pair_index(self, eq1_id: int, eq2_id: int) -> int:
        return ids_to_pair_index(
            eq1_id,
            eq2_id,
            law_count=self.law_count,
            include_self=self.include_self,
        )

    def pair_index_to_ids(self, pair_index: int) -> tuple[int, int]:
        return pair_index_to_ids(
            pair_index,
            law_count=self.law_count,
            include_self=self.include_self,
        )

    def status(
        self,
        *,
        pair_index: int | None = None,
        eq1_id: int | None = None,
        eq2_id: int | None = None,
        layers: Iterable[str] | None = None,
    ) -> dict:
        resolved_pair_index = self._resolve_pair_index(pair_index, eq1_id, eq2_id)
        resolved_eq1_id, resolved_eq2_id = self.pair_index_to_ids(resolved_pair_index)
        layer_names = tuple(layers or self.layers)
        layer_status: dict[str, bool] = {}
        for layer_name in layer_names:
            with self.layer(layer_name).open() as layer:
                layer_status[layer_name] = layer.get(resolved_pair_index)
        return {
            "pair_index": resolved_pair_index,
            "eq1_id": resolved_eq1_id,
            "eq2_id": resolved_eq2_id,
            "layers": layer_status,
            "verdict": _verdict_from_layers(layer_status),
        }

    def set_pair(
        self,
        layer_name: str,
        *,
        pair_index: int | None = None,
        eq1_id: int | None = None,
        eq2_id: int | None = None,
        update_conflict: bool = True,
    ) -> bool:
        resolved_pair_index = self._resolve_pair_index(pair_index, eq1_id, eq2_id)
        with self.layer(layer_name, writable=True).open() as layer:
            changed = layer.set(resolved_pair_index)
        if update_conflict and layer_name in EXACT_VERDICT_LAYERS:
            self._update_conflict_for_pair(resolved_pair_index)
        return changed

    def import_pair_indexes(
        self,
        input_path: Path,
        *,
        layer_name: str,
        source_id: str,
        source_kind: str = "pair_index_cache",
        write_pair_evidence: bool = False,
        update_conflicts: bool = True,
    ) -> ImportSummary:
        input_path = Path(input_path)
        started_at = time.perf_counter()
        sha256 = hashlib.sha256()
        read_count = 0
        newly_set_count = 0
        already_set_count = 0
        conflict_count = 0

        layer_record = self._layer_record(layer_name)
        del layer_record
        conflict_layer = None
        opposite_layer = None
        if update_conflicts and layer_name in EXACT_VERDICT_LAYERS and self.has_layer("conflict"):
            opposite_layer = "false" if layer_name == "true" else "true"
            if not self.has_layer(opposite_layer):
                opposite_layer = None

        with self.layer(layer_name, writable=True).open() as target:
            if opposite_layer is not None:
                opposite = self.layer(opposite_layer).open()
                conflict_layer = self.layer("conflict", writable=True).open()
            else:
                opposite = None
            try:
                for pair_index, raw_line in iter_pair_indexes(input_path):
                    sha256.update(raw_line)
                    self.pair_index_to_ids(pair_index)
                    read_count += 1
                    if target.set(pair_index):
                        newly_set_count += 1
                    else:
                        already_set_count += 1
                    if opposite is not None and conflict_layer is not None and opposite.get(pair_index):
                        if conflict_layer.set(pair_index):
                            conflict_count += 1
                    if write_pair_evidence:
                        self.append_pair_evidence(
                            {
                                "pair_index": pair_index,
                                "layer": layer_name,
                                "source_id": source_id,
                                "source_kind": source_kind,
                            }
                        )
            finally:
                if opposite is not None:
                    opposite.close()
                if conflict_layer is not None:
                    conflict_layer.close()

        summary = ImportSummary(
            layer=layer_name,
            source_path=str(input_path),
            read_count=read_count,
            newly_set_count=newly_set_count,
            already_set_count=already_set_count,
            conflict_count=conflict_count,
            sha256=sha256.hexdigest(),
            elapsed_seconds=time.perf_counter() - started_at,
        )
        self.append_evidence_batch(
            {
                **summary.to_json(),
                "source_id": source_id,
                "source_kind": source_kind,
                "write_pair_evidence": write_pair_evidence,
                "created_at_unix": time.time(),
            }
        )
        return summary

    def preview_pair_indexes(
        self,
        input_path: Path,
        *,
        layer_name: str,
        top_n: int = 10,
    ) -> dict:
        return self._preview_pair_index_iterable(
            (pair_index for pair_index, _ in iter_pair_indexes(input_path)),
            layer_name=layer_name,
            source_id=str(input_path),
            source_kind="pair_index_cache",
            top_n=top_n,
        )

    def set_source_target_block(
        self,
        layer_name: str,
        *,
        source_ids: Iterable[int],
        target_ids: Iterable[int],
        source_id: str,
        source_kind: str = "source_target_sets",
        update_conflicts: bool = True,
    ) -> dict:
        started_at = time.perf_counter()
        sources = tuple(sorted(set(int(source) for source in source_ids)))
        targets = tuple(sorted(set(int(target) for target in target_ids)))
        for source in sources:
            _validate_eq_id("source_id", source, self.law_count)
        for target in targets:
            _validate_eq_id("target_id", target, self.law_count)

        row_width = self.law_count if self.include_self else self.law_count - 1
        full_target_mask = _ids_to_mask(targets)
        read_count = sum(
            _bit_count(
                _source_target_row_mask(
                    full_target_mask,
                    source,
                    law_count=self.law_count,
                    include_self=self.include_self,
                )
            )
            for source in sources
        )
        newly_set_count = 0
        already_set_count = 0
        conflict_count = 0
        opposite_layer_name = None
        if update_conflicts and layer_name in EXACT_VERDICT_LAYERS and self.has_layer("conflict"):
            candidate = "false" if layer_name == "true" else "true"
            if self.has_layer(candidate):
                opposite_layer_name = candidate

        with self.layer(layer_name, writable=True).open() as target_layer:
            if opposite_layer_name is not None:
                opposite_layer = self.layer(opposite_layer_name).open()
                conflict_layer = self.layer("conflict", writable=True).open()
            else:
                opposite_layer = None
                conflict_layer = None
            try:
                for source in sources:
                    row_mask = _source_target_row_mask(
                        full_target_mask,
                        source,
                        law_count=self.law_count,
                        include_self=self.include_self,
                    )
                    if row_mask == 0:
                        continue
                    row_start = (source - 1) * row_width
                    changed, existing = target_layer.or_mask(row_start, row_width, row_mask)
                    newly_set_count += changed
                    already_set_count += existing
                    if opposite_layer is not None and conflict_layer is not None:
                        conflicting_mask = row_mask & opposite_layer.window_mask(
                            row_start,
                            row_width,
                        )
                        if conflicting_mask:
                            conflict_changed, _ = conflict_layer.or_mask(
                                row_start,
                                row_width,
                                conflicting_mask,
                            )
                            conflict_count += conflict_changed
            finally:
                if opposite_layer is not None:
                    opposite_layer.close()
                if conflict_layer is not None:
                    conflict_layer.close()

        summary = {
            "layer": layer_name,
            "source_id": source_id,
            "source_kind": source_kind,
            "source_count": len(sources),
            "target_count": len(targets),
            "read_count": read_count,
            "newly_set_count": newly_set_count,
            "already_set_count": already_set_count,
            "conflict_count": conflict_count,
            "elapsed_seconds": time.perf_counter() - started_at,
            "created_at_unix": time.time(),
        }
        self.append_evidence_batch(summary)
        return summary

    def preview_source_target_block(
        self,
        layer_name: str,
        *,
        source_ids: Iterable[int],
        target_ids: Iterable[int],
        source_id: str,
        source_kind: str = "source_target_sets",
        top_n: int = 10,
    ) -> dict:
        started_at = time.perf_counter()
        sources = tuple(sorted(set(int(source) for source in source_ids)))
        targets = tuple(sorted(set(int(target) for target in target_ids)))
        for source in sources:
            _validate_eq_id("source_id", source, self.law_count)
        for target in targets:
            _validate_eq_id("target_id", target, self.law_count)

        row_width = self.law_count if self.include_self else self.law_count - 1
        full_target_mask = _ids_to_mask(targets)
        read_count = 0
        already_set_count = 0
        newly_set_count = 0
        conflict_count = 0
        top_new_sources: Counter[int] = Counter()
        opposite_layer_name = _opposite_exact_layer(layer_name, self)

        with self.layer(layer_name).open() as target_layer:
            opposite_layer = self.layer(opposite_layer_name).open() if opposite_layer_name else None
            try:
                for source in sources:
                    row_mask = _source_target_row_mask(
                        full_target_mask,
                        source,
                        law_count=self.law_count,
                        include_self=self.include_self,
                    )
                    if row_mask == 0:
                        continue
                    row_start = (source - 1) * row_width
                    current_mask = target_layer.window_mask(row_start, row_width)
                    already = _bit_count(row_mask & current_mask)
                    new = _bit_count(row_mask & ~current_mask)
                    read_count += _bit_count(row_mask)
                    already_set_count += already
                    newly_set_count += new
                    if new:
                        top_new_sources[source] = new
                    if opposite_layer is not None:
                        conflict_count += _bit_count(
                            row_mask & opposite_layer.window_mask(row_start, row_width)
                        )
            finally:
                if opposite_layer is not None:
                    opposite_layer.close()

        return {
            "layer": layer_name,
            "source_id": source_id,
            "source_kind": source_kind,
            "source_count": len(sources),
            "target_count": len(targets),
            "read_count": read_count,
            "newly_set_count": newly_set_count,
            "already_set_count": already_set_count,
            "conflict_count": conflict_count,
            "top_new_sources": _counter_top(top_new_sources, top_n),
            "elapsed_seconds": time.perf_counter() - started_at,
        }

    def import_coverage_strategy(
        self,
        strategy,
        *,
        update_conflicts: bool = True,
    ) -> dict:
        if getattr(strategy, "deprecated", False):
            return {
                "strategy_id": getattr(strategy, "strategy_id", ""),
                "skipped": True,
                "skip_reason": "deprecated",
            }
        layer_name = "true" if bool(getattr(strategy, "verdict")) else "false"
        if not self.has_layer(layer_name):
            return {
                "strategy_id": getattr(strategy, "strategy_id", ""),
                "skipped": True,
                "skip_reason": f"missing layer {layer_name!r}",
            }

        rule = getattr(strategy, "coverage_rule")
        strategy_id = str(getattr(strategy, "strategy_id"))
        coverage_kind = str(getattr(rule, "coverage_kind", ""))
        if hasattr(rule, "pair_indexes"):
            started_at = time.perf_counter()
            pair_indexes = tuple(int(pair_index) for pair_index in getattr(rule, "pair_indexes"))
            newly_set_count = 0
            already_set_count = 0
            conflict_count = 0
            opposite_layer_name = None
            if (
                update_conflicts
                and layer_name in EXACT_VERDICT_LAYERS
                and self.has_layer("conflict")
            ):
                candidate = "false" if layer_name == "true" else "true"
                if self.has_layer(candidate):
                    opposite_layer_name = candidate

            with self.layer(layer_name, writable=True).open() as target_layer:
                if opposite_layer_name is not None:
                    opposite_layer = self.layer(opposite_layer_name).open()
                    conflict_layer = self.layer("conflict", writable=True).open()
                else:
                    opposite_layer = None
                    conflict_layer = None
                try:
                    for pair_index in pair_indexes:
                        self.pair_index_to_ids(pair_index)
                        if target_layer.set(pair_index):
                            newly_set_count += 1
                        else:
                            already_set_count += 1
                        if (
                            opposite_layer is not None
                            and conflict_layer is not None
                            and opposite_layer.get(pair_index)
                        ):
                            if conflict_layer.set(pair_index):
                                conflict_count += 1
                finally:
                    if opposite_layer is not None:
                        opposite_layer.close()
                    if conflict_layer is not None:
                        conflict_layer.close()

            summary = {
                "layer": layer_name,
                "source_id": strategy_id,
                "source_kind": f"strategy_registry.{coverage_kind or 'pair_indexes'}",
                "read_count": len(pair_indexes),
                "newly_set_count": newly_set_count,
                "already_set_count": already_set_count,
                "conflict_count": conflict_count,
                "coverage_kind": coverage_kind,
                "strategy_id": strategy_id,
                "elapsed_seconds": time.perf_counter() - started_at,
                "created_at_unix": time.time(),
            }
            self.append_evidence_batch(summary)
            return summary

        if hasattr(rule, "source_ids") and hasattr(rule, "target_ids"):
            summary = self.set_source_target_block(
                layer_name,
                source_ids=getattr(rule, "source_ids"),
                target_ids=getattr(rule, "target_ids"),
                source_id=strategy_id,
                source_kind=f"strategy_registry.{coverage_kind or 'source_target_sets'}",
                update_conflicts=update_conflicts,
            )
            summary["coverage_kind"] = coverage_kind
            summary["strategy_id"] = strategy_id
            return summary

        return {
            "strategy_id": strategy_id,
            "coverage_kind": coverage_kind,
            "skipped": True,
            "skip_reason": "unsupported coverage rule",
        }

    def preview_coverage_strategy(self, strategy, *, top_n: int = 10) -> dict:
        if getattr(strategy, "deprecated", False):
            return {
                "strategy_id": getattr(strategy, "strategy_id", ""),
                "skipped": True,
                "skip_reason": "deprecated",
            }
        layer_name = "true" if bool(getattr(strategy, "verdict")) else "false"
        if not self.has_layer(layer_name):
            return {
                "strategy_id": getattr(strategy, "strategy_id", ""),
                "skipped": True,
                "skip_reason": f"missing layer {layer_name!r}",
            }
        rule = getattr(strategy, "coverage_rule")
        strategy_id = str(getattr(strategy, "strategy_id"))
        coverage_kind = str(getattr(rule, "coverage_kind", ""))
        if hasattr(rule, "pair_indexes"):
            preview = self._preview_pair_index_iterable(
                (int(pair_index) for pair_index in getattr(rule, "pair_indexes")),
                layer_name=layer_name,
                source_id=strategy_id,
                source_kind=f"strategy_registry.{coverage_kind or 'pair_indexes'}",
                top_n=top_n,
            )
        elif hasattr(rule, "source_ids") and hasattr(rule, "target_ids"):
            preview = self.preview_source_target_block(
                layer_name,
                source_ids=getattr(rule, "source_ids"),
                target_ids=getattr(rule, "target_ids"),
                source_id=strategy_id,
                source_kind=f"strategy_registry.{coverage_kind or 'source_target_sets'}",
                top_n=top_n,
            )
        else:
            return {
                "strategy_id": strategy_id,
                "coverage_kind": coverage_kind,
                "skipped": True,
                "skip_reason": "unsupported coverage rule",
            }
        preview["strategy_id"] = strategy_id
        preview["coverage_kind"] = coverage_kind
        return preview

    def import_coverage_strategies(
        self,
        strategies: Sequence,
        *,
        verdict: bool | None = None,
        coverage_kinds: set[str] | None = None,
        strategy_ids: set[str] | None = None,
        max_strategies: int | None = None,
        update_conflicts: bool = True,
    ) -> dict:
        rows = []
        imported = 0
        for strategy in strategies:
            strategy_id = str(getattr(strategy, "strategy_id"))
            rule = getattr(strategy, "coverage_rule")
            coverage_kind = str(getattr(rule, "coverage_kind", ""))
            if verdict is not None and bool(getattr(strategy, "verdict")) is not verdict:
                continue
            if coverage_kinds is not None and coverage_kind not in coverage_kinds:
                continue
            if strategy_ids is not None and strategy_id not in strategy_ids:
                continue
            if max_strategies is not None and imported >= max_strategies:
                break
            rows.append(
                self.import_coverage_strategy(
                    strategy,
                    update_conflicts=update_conflicts,
                )
            )
            imported += 1
        return _summarize_strategy_import_rows(rows)

    def preview_coverage_strategies(
        self,
        strategies: Sequence,
        *,
        verdict: bool | None = None,
        coverage_kinds: set[str] | None = None,
        strategy_ids: set[str] | None = None,
        max_strategies: int | None = None,
        top_n: int = 10,
    ) -> dict:
        rows = []
        previewed = 0
        for strategy in strategies:
            strategy_id = str(getattr(strategy, "strategy_id"))
            rule = getattr(strategy, "coverage_rule")
            coverage_kind = str(getattr(rule, "coverage_kind", ""))
            if verdict is not None and bool(getattr(strategy, "verdict")) is not verdict:
                continue
            if coverage_kinds is not None and coverage_kind not in coverage_kinds:
                continue
            if strategy_ids is not None and strategy_id not in strategy_ids:
                continue
            if max_strategies is not None and previewed >= max_strategies:
                break
            rows.append(self.preview_coverage_strategy(strategy, top_n=top_n))
            previewed += 1
        return _summarize_strategy_import_rows(rows)

    def row_targets(
        self,
        layer_name: str,
        source_id: int,
        *,
        limit: int | None = None,
    ) -> list[int]:
        if source_id < 1 or source_id > self.law_count:
            raise ValueError(f"source_id must be in [1, {self.law_count}]; got {source_id}")
        start = (source_id - 1) * (self.law_count if self.include_self else self.law_count - 1)
        stop = start + (self.law_count if self.include_self else self.law_count - 1)
        targets: list[int] = []
        with self.layer(layer_name).open() as layer:
            for pair_index in layer.iter_set_bits(start=start, stop=stop):
                _, target_id = self.pair_index_to_ids(pair_index)
                targets.append(target_id)
                if limit is not None and len(targets) >= limit:
                    break
        return targets

    def row_summary(
        self,
        source_id: int,
        *,
        layers: Iterable[str] | None = None,
    ) -> dict:
        if source_id < 1 or source_id > self.law_count:
            raise ValueError(f"source_id must be in [1, {self.law_count}]; got {source_id}")
        layer_names = tuple(layers or self.layers)
        row_width = self.law_count if self.include_self else self.law_count - 1
        row_start = (source_id - 1) * row_width
        masks: dict[str, int] = {}
        counts: dict[str, int] = {}
        for layer_name in layer_names:
            with self.layer(layer_name).open() as layer:
                mask = layer.window_mask(row_start, row_width)
            masks[layer_name] = mask
            counts[layer_name] = _bit_count(mask)
        exact_known_mask = masks.get("true", 0) | masks.get("false", 0)
        return {
            "source_id": source_id,
            "row_width": row_width,
            "layer_counts": counts,
            "exact_known_count": _bit_count(exact_known_mask),
            "unknown_count": row_width - _bit_count(exact_known_mask),
        }

    def source_frontier(
        self,
        source_id: int,
        *,
        known_layers: Iterable[str] = ("true", "false"),
        limit: int = 20,
    ) -> dict:
        if limit < 0:
            raise ValueError("limit must be non-negative")
        if source_id < 1 or source_id > self.law_count:
            raise ValueError(f"source_id must be in [1, {self.law_count}]; got {source_id}")
        row_width = self.law_count if self.include_self else self.law_count - 1
        row_start = (source_id - 1) * row_width
        known_mask = 0
        for layer_name in known_layers:
            if not self.has_layer(layer_name):
                continue
            with self.layer(layer_name).open() as layer:
                known_mask |= layer.window_mask(row_start, row_width)
        unknown_mask = ((1 << row_width) - 1) & ~known_mask
        targets = []
        cursor_mask = unknown_mask
        while cursor_mask and len(targets) < limit:
            low_bit = cursor_mask & -cursor_mask
            slot = low_bit.bit_length() - 1
            targets.append(_row_slot_to_target_id(slot, source_id, include_self=self.include_self))
            cursor_mask ^= low_bit
        return {
            "source_id": source_id,
            "known_layers": list(known_layers),
            "unknown_count": _bit_count(unknown_mask),
            "targets": targets,
        }

    def target_sources(
        self,
        layer_name: str,
        target_id: int,
        *,
        limit: int | None = None,
    ) -> list[int]:
        if target_id < 1 or target_id > self.law_count:
            raise ValueError(f"target_id must be in [1, {self.law_count}]; got {target_id}")
        sources: list[int] = []
        with self.layer(layer_name).open() as layer:
            for source_id in range(1, self.law_count + 1):
                if not self.include_self and source_id == target_id:
                    continue
                if layer.get(self.ids_to_pair_index(source_id, target_id)):
                    sources.append(source_id)
                    if limit is not None and len(sources) >= limit:
                        break
        return sources

    def target_summary(
        self,
        target_id: int,
        *,
        layers: Iterable[str] | None = None,
    ) -> dict:
        target_map = self.target_map(target_id, layers=layers)
        exact_known_count = sum(1 for code in target_map["status_codes"] if code in (1, 2, 3))
        return {
            "target_id": target_id,
            "column_width": target_map["column_width"],
            "layer_counts": target_map["layer_counts"],
            "exact_known_count": exact_known_count,
            "unknown_count": target_map["column_width"] - exact_known_count,
        }

    def target_map(
        self,
        target_id: int,
        *,
        layers: Iterable[str] | None = None,
    ) -> dict:
        if target_id < 1 or target_id > self.law_count:
            raise ValueError(f"target_id must be in [1, {self.law_count}]; got {target_id}")
        layer_names = tuple(layers or self.layers)
        column_width = self.law_count if self.include_self else self.law_count - 1
        layer_counts = dict.fromkeys(layer_names, 0)
        counts = {
            "unknown": 0,
            "true": 0,
            "false": 0,
            "conflict": 0,
            "approx_true": 0,
            "approx_false": 0,
            "approx_both": 0,
        }
        status_codes = bytearray(column_width)
        with ExitStack() as stack:
            open_layers = {
                layer_name: stack.enter_context(self.layer(layer_name).open())
                for layer_name in layer_names
            }
            for slot in range(column_width):
                source_id = _target_slot_to_source_id(
                    slot,
                    target_id,
                    include_self=self.include_self,
                )
                pair_index = self.ids_to_pair_index(source_id, target_id)
                layer_status = {
                    layer_name: layer.get(pair_index)
                    for layer_name, layer in open_layers.items()
                }
                for layer_name, enabled in layer_status.items():
                    if enabled:
                        layer_counts[layer_name] += 1
                true_hit = layer_status.get("true", False)
                false_hit = layer_status.get("false", False)
                conflict_hit = layer_status.get("conflict", False) or (true_hit and false_hit)
                approx_true_hit = layer_status.get("approx_true", False)
                approx_false_hit = layer_status.get("approx_false", False)
                if conflict_hit:
                    code = 3
                    counts["conflict"] += 1
                elif true_hit:
                    code = 1
                    counts["true"] += 1
                elif false_hit:
                    code = 2
                    counts["false"] += 1
                elif approx_true_hit and approx_false_hit:
                    code = 6
                    counts["approx_both"] += 1
                elif approx_true_hit:
                    code = 4
                    counts["approx_true"] += 1
                elif approx_false_hit:
                    code = 5
                    counts["approx_false"] += 1
                else:
                    code = 0
                    counts["unknown"] += 1
                status_codes[slot] = code
        return {
            "target_id": target_id,
            "law_count": self.law_count,
            "include_self": self.include_self,
            "column_width": column_width,
            "code_format": "one byte per source slot, source order excludes target when include_self=false",
            "status_codes": bytes(status_codes),
            "counts": counts,
            "layer_counts": layer_counts,
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

    def exact_pair_counts(self, *, chunk_size: int = 8 * 1024 * 1024) -> dict:
        true_exists = self.has_layer("true")
        false_exists = self.has_layer("false")
        if not (true_exists or false_exists):
            return {
                "exact_known_count": 0,
                "exact_unknown_count": self.pair_count,
            }
        with ExitStack() as stack:
            true_layer = stack.enter_context(self.layer("true").open()) if true_exists else None
            false_layer = stack.enter_context(self.layer("false").open()) if false_exists else None
            byte_count = (self.pair_count + 7) // 8
            exact_known_count = 0
            for offset in range(0, byte_count, chunk_size):
                end = min(offset + chunk_size, byte_count)
                if true_layer is not None and false_layer is not None:
                    exact_known_count += sum(
                        _bit_count(true_byte | false_byte)
                        for true_byte, false_byte in zip(
                            true_layer._mmap[offset:end],
                            false_layer._mmap[offset:end],
                        )
                    )
                elif true_layer is not None:
                    exact_known_count += sum(
                        _bit_count(byte) for byte in true_layer._mmap[offset:end]
                    )
                elif false_layer is not None:
                    exact_known_count += sum(
                        _bit_count(byte) for byte in false_layer._mmap[offset:end]
                    )
            unused_bits = byte_count * 8 - self.pair_count
            if unused_bits:
                true_last = true_layer._mmap[byte_count - 1] if true_layer is not None else 0
                false_last = false_layer._mmap[byte_count - 1] if false_layer is not None else 0
                exact_known_count -= _bit_count((true_last | false_last) >> (8 - unused_bits))
        return {
            "exact_known_count": exact_known_count,
            "exact_unknown_count": self.pair_count - exact_known_count,
        }

    def layer_count(self, layer_name: str) -> int:
        with self.layer(layer_name).open() as layer:
            return layer.count()

    def rebuild_conflicts(self, *, chunk_size: int = 8 * 1024 * 1024) -> dict:
        if not (self.has_layer("true") and self.has_layer("false") and self.has_layer("conflict")):
            raise ValueError("rebuild_conflicts requires true, false, and conflict layers")
        started_at = time.perf_counter()
        conflict_count = 0
        true_layer = self.layer("true").open()
        false_layer = self.layer("false").open()
        conflict_layer = self.layer("conflict", writable=True).open()
        try:
            byte_count = conflict_layer.byte_count
            for offset in range(0, byte_count, chunk_size):
                end = min(offset + chunk_size, byte_count)
                true_chunk = true_layer._mmap[offset:end]
                false_chunk = false_layer._mmap[offset:end]
                conflict_chunk = bytearray(len(true_chunk))
                for index, (true_byte, false_byte) in enumerate(zip(true_chunk, false_chunk)):
                    value = true_byte & false_byte
                    conflict_chunk[index] = value
                    conflict_count += _bit_count(value)
                conflict_layer._mmap[offset:end] = conflict_chunk
            unused_bits = conflict_layer.byte_count * 8 - conflict_layer.bit_count
            if unused_bits:
                last_index = conflict_layer.byte_count - 1
                valid_mask = (1 << (8 - unused_bits)) - 1
                conflict_layer._mmap[last_index] &= valid_mask
        finally:
            true_layer.close()
            false_layer.close()
            conflict_layer.close()
        summary = {
            "source_id": "rebuild_conflicts",
            "source_kind": "bitset_and",
            "layer": "conflict",
            "conflict_count": conflict_count,
            "elapsed_seconds": time.perf_counter() - started_at,
            "created_at_unix": time.time(),
        }
        self.append_evidence_batch(summary)
        return summary

    def _preview_pair_index_iterable(
        self,
        pair_indexes: Iterable[int],
        *,
        layer_name: str,
        source_id: str,
        source_kind: str,
        top_n: int,
    ) -> dict:
        started_at = time.perf_counter()
        self._layer_record(layer_name)
        opposite_layer_name = _opposite_exact_layer(layer_name, self)
        read_count = 0
        newly_set_count = 0
        already_set_count = 0
        conflict_count = 0
        top_sources: Counter[int] = Counter()
        top_targets: Counter[int] = Counter()
        top_new_sources: Counter[int] = Counter()
        with self.layer(layer_name).open() as target_layer:
            opposite_layer = self.layer(opposite_layer_name).open() if opposite_layer_name else None
            try:
                for pair_index in pair_indexes:
                    eq1_id, eq2_id = self.pair_index_to_ids(pair_index)
                    read_count += 1
                    top_sources[eq1_id] += 1
                    top_targets[eq2_id] += 1
                    if target_layer.get(pair_index):
                        already_set_count += 1
                    else:
                        newly_set_count += 1
                        top_new_sources[eq1_id] += 1
                    if opposite_layer is not None and opposite_layer.get(pair_index):
                        conflict_count += 1
            finally:
                if opposite_layer is not None:
                    opposite_layer.close()
        return {
            "layer": layer_name,
            "source_id": source_id,
            "source_kind": source_kind,
            "read_count": read_count,
            "newly_set_count": newly_set_count,
            "already_set_count": already_set_count,
            "conflict_count": conflict_count,
            "top_sources": _counter_top(top_sources, top_n),
            "top_targets": _counter_top(top_targets, top_n),
            "top_new_sources": _counter_top(top_new_sources, top_n),
            "elapsed_seconds": time.perf_counter() - started_at,
        }

    def append_evidence_batch(self, record: dict) -> None:
        self._append_jsonl(self.store_dir / self.manifest["evidence"]["batch_log_path"], record)

    def append_pair_evidence(self, record: dict) -> None:
        self._append_jsonl(self.store_dir / self.manifest["evidence"]["pair_log_path"], record)

    def _resolve_pair_index(
        self,
        pair_index: int | None,
        eq1_id: int | None,
        eq2_id: int | None,
    ) -> int:
        if pair_index is not None:
            self.pair_index_to_ids(pair_index)
            return pair_index
        if eq1_id is None or eq2_id is None:
            raise ValueError("provide pair_index or both eq1_id and eq2_id")
        return self.ids_to_pair_index(eq1_id, eq2_id)

    def _layer_record(self, layer_name: str) -> dict:
        try:
            return self.manifest["layers"][layer_name]
        except KeyError as exc:
            raise KeyError(f"unknown layer {layer_name!r}; available: {self.layers}") from exc

    def _update_conflict_for_pair(self, pair_index: int) -> None:
        if not (self.has_layer("true") and self.has_layer("false") and self.has_layer("conflict")):
            return
        with (
            self.layer("true").open() as true_layer,
            self.layer("false").open() as false_layer,
            self.layer("conflict", writable=True).open() as conflict_layer,
        ):
            if true_layer.get(pair_index) and false_layer.get(pair_index):
                conflict_layer.set(pair_index)

    def _append_jsonl(self, path: Path, record: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def iter_pair_indexes(path: Path) -> Iterator[tuple[int, bytes]]:
    path = Path(path)
    with path.open("rb") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            stripped = raw_line.strip()
            if not stripped:
                continue
            try:
                if stripped.startswith(b"{"):
                    row = json.loads(stripped.decode("utf-8"))
                    pair_index = int(row["pair_index"])
                else:
                    pair_index = int(stripped)
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ValueError(f"invalid pair_index on line {line_number} of {path}") from exc
            yield pair_index, raw_line


def finite_model_equation_partition(
    *,
    equations_path: Path,
    model_table: Sequence[Sequence[int]],
) -> dict:
    table = tuple(tuple(int(value) for value in row) for row in model_table)
    magma = FiniteMagma(order=len(table), table=table)
    satisfied_ids: list[int] = []
    refuted_ids: list[int] = []
    started_at = time.perf_counter()
    for equation_id, equation_text in enumerate(read_equations(equations_path), start=1):
        equation = parse_equation(equation_text)
        if magma.satisfies(equation):
            satisfied_ids.append(equation_id)
        else:
            refuted_ids.append(equation_id)
    return {
        "model_order": magma.order,
        "satisfied_ids": satisfied_ids,
        "refuted_ids": refuted_ids,
        "satisfied_count": len(satisfied_ids),
        "refuted_count": len(refuted_ids),
        "elapsed_seconds": time.perf_counter() - started_at,
    }


def _verdict_from_layers(layer_status: dict[str, bool]) -> str:
    if layer_status.get("conflict") or (
        layer_status.get("true") and layer_status.get("false")
    ):
        return "conflict"
    if layer_status.get("true"):
        return "true"
    if layer_status.get("false"):
        return "false"
    if layer_status.get("approx_true") and layer_status.get("approx_false"):
        return "approx_conflict"
    if layer_status.get("approx_true"):
        return "approx_true"
    if layer_status.get("approx_false"):
        return "approx_false"
    return "unknown"


def _validate_layer_name(layer_name: str) -> None:
    if not layer_name:
        raise ValueError("layer name cannot be empty")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_")
    if any(character not in allowed for character in layer_name):
        raise ValueError(
            f"layer name must use lowercase ascii letters, digits, and underscores: {layer_name!r}"
        )


def _validate_eq_id(name: str, eq_id: int, law_count: int) -> None:
    if eq_id < 1 or eq_id > law_count:
        raise ValueError(f"{name} must be in [1, {law_count}]; got {eq_id}")


def _opposite_exact_layer(layer_name: str, store: ColumnarImplicationStore) -> str | None:
    if layer_name not in EXACT_VERDICT_LAYERS:
        return None
    opposite = "false" if layer_name == "true" else "true"
    return opposite if store.has_layer(opposite) else None


def _ids_to_mask(ids: Iterable[int]) -> int:
    mask = 0
    for eq_id in ids:
        mask |= 1 << (int(eq_id) - 1)
    return mask


def _source_target_row_mask(
    full_target_mask: int,
    source_id: int,
    *,
    law_count: int,
    include_self: bool,
) -> int:
    self_bit = source_id - 1
    if include_self:
        return full_target_mask & ~(1 << self_bit)
    lower = full_target_mask & ((1 << self_bit) - 1)
    upper = full_target_mask >> source_id
    return lower | (upper << self_bit)


def _row_slot_to_target_id(slot: int, source_id: int, *, include_self: bool) -> int:
    if include_self:
        return slot + 1
    target_id = slot + 1
    if target_id >= source_id:
        target_id += 1
    return target_id


def _target_slot_to_source_id(slot: int, target_id: int, *, include_self: bool) -> int:
    if include_self:
        return slot + 1
    source_id = slot + 1
    if source_id >= target_id:
        source_id += 1
    return source_id


def _counter_top(counter: Counter[int], top_n: int) -> list[dict]:
    if top_n <= 0:
        return []
    return [
        {"id": item_id, "count": count}
        for item_id, count in counter.most_common(top_n)
    ]


def _summarize_strategy_import_rows(rows: list[dict]) -> dict:
    imported_rows = [row for row in rows if not row.get("skipped")]
    skipped_rows = [row for row in rows if row.get("skipped")]
    return {
        "strategy_count": len(rows),
        "imported_count": len(imported_rows),
        "skipped_count": len(skipped_rows),
        "read_count": sum(int(row.get("read_count", 0)) for row in imported_rows),
        "newly_set_count": sum(int(row.get("newly_set_count", 0)) for row in imported_rows),
        "already_set_count": sum(int(row.get("already_set_count", 0)) for row in imported_rows),
        "conflict_count": sum(int(row.get("conflict_count", 0)) for row in imported_rows),
        "rows": rows,
    }


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
