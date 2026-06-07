from __future__ import annotations

from math_distill_stage2.docker_images import OFFICIAL_STAGE2_JUDGE_IMAGE
from math_distill_stage2.lean_executor.base import LeanExecutionResult, LeanTask, run_lean_command


DEFAULT_LEAN_DOCKER_IMAGE = OFFICIAL_STAGE2_JUDGE_IMAGE


class DockerLeanExecutor:
    backend = "docker"

    def __init__(
        self,
        image: str = DEFAULT_LEAN_DOCKER_IMAGE,
        cpu_limit: str | None = "1",
        memory_limit: str | None = "512m",
        lean_image_digest: str | None = None,
    ) -> None:
        self.image = image
        self.cpu_limit = cpu_limit
        self.memory_limit = memory_limit
        self.lean_image_digest = lean_image_digest

    def execute(self, task: LeanTask) -> LeanExecutionResult:
        run_dir = task.certificate_path.parent.resolve()
        command = ["docker", "run", "--rm", "--network", "none"]
        if self.cpu_limit:
            command.extend(["--cpus", self.cpu_limit])
        if self.memory_limit:
            command.extend(["--memory", self.memory_limit])
        command.extend(
            [
                "-v",
                f"{run_dir}:/work:ro",
                self.image,
                "lean",
                f"/work/{task.certificate_path.name}",
            ]
        )
        return run_lean_command(
            command=command,
            task=task,
            backend=self.backend,
            lean_image=self.image,
            lean_image_digest=self.lean_image_digest,
            cpu_limit=self.cpu_limit,
            memory_limit=self.memory_limit,
        )
