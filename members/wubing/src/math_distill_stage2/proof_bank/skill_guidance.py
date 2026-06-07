from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import re
from typing import Any


DEFAULT_GENERATION_SKILL_PATH = Path("skills/stage2-proofbank-generate-true-certificate/SKILL.md")
DEFAULT_LEAN_PROOF_SKILL_PATH = Path.home() / ".codex" / "skills" / "lean-proof" / "SKILL.md"


@dataclass(frozen=True)
class SkillPromptFragment:
    name: str
    source_role: str
    path: str
    sha256: str
    text: str

    def metadata(self) -> dict[str, str]:
        return {
            "name": self.name,
            "source_role": self.source_role,
            "path": self.path,
            "sha256": self.sha256,
        }


def load_skill_guidance_for_problem(
    problem: dict[str, Any],
    *,
    generation_skill_path: Path | None = DEFAULT_GENERATION_SKILL_PATH,
    lean_proof_skill_path: Path | None = DEFAULT_LEAN_PROOF_SKILL_PATH,
) -> list[SkillPromptFragment]:
    fragments: list[SkillPromptFragment] = []
    generation = _load_skill_fragment(generation_skill_path, source_role="generation")
    if generation is not None:
        fragments.append(generation)
    if _is_repair_candidate(problem):
        repair = _load_skill_fragment(lean_proof_skill_path, source_role="repair")
        if repair is not None:
            fragments.append(repair)
    return fragments


def render_skill_guidance(fragments: list[SkillPromptFragment]) -> str:
    if not fragments:
        return ""
    lines = [
        "## Skill-Guided Proof Instructions",
        "",
        "The proof strategy below is loaded from local skill files when this prompt pack is built.",
        "Use these skill instructions as the flexible strategy source; the fixed prompt fields only define routing, the problem, and judge boundaries.",
        "Judge boundaries above override any skill text about temporary placeholders; the final raw response must still be a certificate body without `sorry` or `admit`.",
    ]
    for fragment in fragments:
        lines.extend(
            [
                "",
                f"### {fragment.name}",
                "",
                f"- source role: {fragment.source_role}",
                f"- source path: {fragment.path}",
                f"- source sha256: {fragment.sha256}",
                "",
                "```markdown",
                fragment.text,
                "```",
            ]
        )
    return "\n" + "\n".join(lines) + "\n"


def _load_skill_fragment(path: Path | None, *, source_role: str) -> SkillPromptFragment | None:
    if path is None or not path.exists():
        return None
    raw_text = path.read_text(encoding="utf-8")
    name = _extract_skill_name(raw_text) or path.parent.name
    body = _strip_frontmatter(raw_text).strip()
    return SkillPromptFragment(
        name=name,
        source_role=source_role,
        path=str(path),
        sha256=hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
        text=body,
    )


def _is_repair_candidate(problem: dict[str, Any]) -> bool:
    return (
        problem.get("source_candidate_stratum") == "rejected_attempt_repair"
        or bool(problem.get("source_attempt_id"))
        or bool(problem.get("previous_judge_error_kind"))
        or bool(problem.get("previous_proof_body_excerpt"))
    )


def _extract_skill_name(text: str) -> str | None:
    match = re.search(r"(?m)^name:\s*(.+?)\s*$", text)
    if match is None:
        return None
    return match.group(1).strip().strip("\"'")


def _strip_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end == -1:
        return text
    return text[end + len("\n---\n") :]
