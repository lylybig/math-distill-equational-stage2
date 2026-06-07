from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class ImplicationGraph:
    adjacency: dict[int, tuple[int, ...]]
    edges: dict[tuple[int, int], dict]

    @classmethod
    def from_rows(cls, rows: list[dict]) -> "ImplicationGraph":
        adjacency: dict[int, set[int]] = {}
        edges: dict[tuple[int, int], dict] = {}
        for row in rows:
            lhs_id = int(row["lhs_id"])
            rhs_id = int(row["rhs_id"])
            adjacency.setdefault(lhs_id, set()).add(rhs_id)
            edges.setdefault((lhs_id, rhs_id), row)
        return cls(
            {node: tuple(sorted(targets)) for node, targets in adjacency.items()},
            edges,
        )

    def find_path(self, source: int, target: int) -> list[int] | None:
        if source == target:
            return [source]
        queue: deque[list[int]] = deque([[source]])
        seen = {source}
        while queue:
            path = queue.popleft()
            node = path[-1]
            for neighbor in self.adjacency.get(node, ()):
                if neighbor in seen:
                    continue
                next_path = [*path, neighbor]
                if neighbor == target:
                    return next_path
                seen.add(neighbor)
                queue.append(next_path)
        return None

    def find_edge_path(self, source: int, target: int) -> list[dict] | None:
        id_path = self.find_path(source, target)
        if id_path is None:
            return None
        return [self.edges[(left, right)] for left, right in zip(id_path, id_path[1:])]


@dataclass(frozen=True)
class FactIndex:
    rows: tuple[dict, ...]

    @classmethod
    def from_rows(cls, rows: list[dict]) -> "FactIndex":
        return cls(tuple(rows))

    def find_refutation(self, satisfied_id: int, refuted_id: int, finite_only: bool) -> dict | None:
        for row in self.rows:
            if finite_only and not row.get("finite"):
                continue
            if satisfied_id in row.get("satisfied_ids", ()) and refuted_id in row.get("refuted_ids", ()):
                return row
        return None
