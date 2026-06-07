from __future__ import annotations

from dataclasses import dataclass, replace
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import shlex
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence

from math_distill_stage2.docker_images import OFFICIAL_STAGE2_JUDGE_IMAGE
from math_distill_stage2.official_stage2_judge import ensure_official_stage2_problem_defaults


DEFAULT_OFFICIAL_STAGE2_JUDGE_IMAGE = OFFICIAL_STAGE2_JUDGE_IMAGE
CONTAINER_WORKER = "/workspace/scripts/lean_certificates/verify_official_stage2_batch_worker.py"
CONTAINER_JUDGE_REPO = "/opt/equational-theories-lean-stage2"
DEFAULT_REMOTE_JUDGE_V2_BASE_URLS = ("http://10.220.69.172:8890",)
DEFAULT_REMOTE_JUDGE_V2_BASE_URL = DEFAULT_REMOTE_JUDGE_V2_BASE_URLS[0]
DEFAULT_REMOTE_JUDGE_MAX_WORKERS = int(
    os.environ.get("STAGE2_REMOTE_JUDGE_MAX_WORKERS", "16")
)


@dataclass(frozen=True)
class OfficialVerificationInput:
    problem_id: str
    repeat_index: int
    problem: dict[str, Any]
    answer: dict[str, Any]
    code_sha256: str


@dataclass(frozen=True)
class DockerOfficialStage2BatchResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


VerifyFn = Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]]
BatchJudgeRequest = tuple[dict[str, Any], dict[str, Any]]


@dataclass(frozen=True)
class RemoteOfficialStage2BatchConfig:
    host: str
    repo: str
    workdir: str
    python: str = "python3"
    max_workers: int = 1
    cpu_limit: str | None = None
    memory_limit: str | None = None
    timeout_seconds: int | None = None
    lean_timeout_seconds: int | None = None
    max_code_length: int | None = None
    max_false_cert_bytes: int | None = None
    job_id: str | None = None
    ssh_executable: str = "ssh"
    scp_executable: str = "scp"


@dataclass(frozen=True)
class RemoteJudgeV2Config:
    base_url: str = DEFAULT_REMOTE_JUDGE_V2_BASE_URL
    max_workers: int = DEFAULT_REMOTE_JUDGE_MAX_WORKERS
    request_timeout_seconds: int | None = 30
    run_timeout_seconds: int | None = 600
    wait_timeout_seconds: float = 60.0
    poll_interval_seconds: float = 0.2
    lean_timeout_seconds: int | None = None


def extract_official_verification_input(record: dict[str, Any]) -> OfficialVerificationInput:
    problem_id = str(record.get("problem_id") or record.get("id") or "")
    if not problem_id:
        raise ValueError("record is missing problem_id/id")

    problem = record.get("problem")
    if problem is None:
        problem = _problem_from_flat_record(record, problem_id=problem_id)
    if not isinstance(problem, dict):
        raise ValueError("record.problem must be an object when present")
    problem = ensure_official_stage2_problem_defaults(problem)

    answer = record.get("answer") or record.get("judge_call")
    if not isinstance(answer, dict):
        raise ValueError("record is missing answer/judge_call object")

    code = answer.get("code")
    code_sha256 = hashlib.sha256(code.encode("utf-8")).hexdigest() if isinstance(code, str) else ""
    return OfficialVerificationInput(
        problem_id=problem_id,
        repeat_index=int(record.get("repeat_index") or 0),
        problem=dict(problem),
        answer=dict(answer),
        code_sha256=code_sha256,
    )


def run_docker_official_stage2_batch(
    *,
    input_path: Path,
    output_path: Path,
    artifact_dir: Path,
    image: str = DEFAULT_OFFICIAL_STAGE2_JUDGE_IMAGE,
    max_workers: int = 2,
    cpu_limit: str | None = None,
    memory_limit: str | None = None,
    timeout_seconds: int | None = None,
    lean_timeout_seconds: int | None = None,
    max_code_length: int | None = None,
    max_false_cert_bytes: int | None = None,
    resume: bool = False,
    summary_path: Path | None = None,
) -> DockerOfficialStage2BatchResult:
    input_path = input_path.resolve()
    output_path = output_path.resolve()
    artifact_dir = artifact_dir.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    if summary_path is not None:
        summary_path = summary_path.resolve()
        summary_path.parent.mkdir(parents=True, exist_ok=True)

    command = build_docker_official_stage2_batch_command(
        input_path=input_path,
        output_path=output_path,
        artifact_dir=artifact_dir,
        image=image,
        max_workers=max_workers,
        cpu_limit=cpu_limit,
        memory_limit=memory_limit,
        resume=resume,
        summary_path=summary_path,
        lean_timeout_seconds=lean_timeout_seconds,
        max_code_length=max_code_length,
        max_false_cert_bytes=max_false_cert_bytes,
    )
    completed = subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout_seconds,
    )
    return DockerOfficialStage2BatchResult(
        command=command,
        returncode=completed.returncode,
        stdout=completed.stdout or "",
        stderr=completed.stderr or "",
    )


def run_remote_official_stage2_batch(
    *,
    input_path: Path,
    output_path: Path,
    artifact_dir: Path,
    config: RemoteOfficialStage2BatchConfig,
) -> dict[str, Any]:
    """Run the existing Dockerized official judge batch script on a remote SSH host."""
    input_path = input_path.resolve()
    output_path = output_path.resolve()
    artifact_dir = artifact_dir.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)

    job_id = config.job_id or f"stage2-judge-{int(time.time())}-{uuid.uuid4().hex[:8]}"
    remote_base = _remote_join(config.workdir, job_id)
    remote_input = _remote_join(remote_base, input_path.name)
    remote_output = _remote_join(remote_base, output_path.name)
    remote_artifact_dir = _remote_join(remote_base, "artifacts")

    _run_checked(
        [
            config.ssh_executable,
            config.host,
            "mkdir -p "
            + " ".join(
                shlex.quote(path)
                for path in (remote_base, remote_artifact_dir, _remote_join(remote_base, "output"))
            ),
        ],
        timeout=config.timeout_seconds,
    )
    _run_checked(
        [config.scp_executable, str(input_path), f"{config.host}:{remote_input}"],
        timeout=config.timeout_seconds,
    )
    _run_checked(
        [
            config.ssh_executable,
            config.host,
            _remote_batch_shell_command(
                config=config,
                remote_input=remote_input,
                remote_output=remote_output,
                remote_artifact_dir=remote_artifact_dir,
            ),
        ],
        timeout=config.timeout_seconds,
    )
    _run_checked(
        [config.scp_executable, f"{config.host}:{remote_output}", str(output_path)],
        timeout=config.timeout_seconds,
    )

    rows = _read_jsonl(output_path)
    status_counts = Counter(str(row.get("status") or "") for row in rows)
    raw_results = [_raw_result_from_remote_row(row) for row in rows]
    return {
        "schema_version": 1,
        "total_count": len(rows),
        "accepted_count": status_counts.get("accepted", 0),
        "status_counts": dict(status_counts),
        "raw_results": raw_results,
        "output_path": str(output_path),
        "remote": {
            "host": config.host,
            "repo": config.repo,
            "workdir": config.workdir,
            "job_id": job_id,
            "remote_output": remote_output,
        },
    }


def make_remote_official_stage2_batch_judge(
    config: RemoteOfficialStage2BatchConfig,
    *,
    local_staging_root: Path | None = None,
) -> Callable[[list[BatchJudgeRequest]], list[dict[str, Any]]]:
    """Return an `import_responses` batch judge function backed by remote SSH."""

    def judge(requests: list[BatchJudgeRequest]) -> list[dict[str, Any]]:
        job_id = config.job_id or f"stage2-judge-{int(time.time())}-{uuid.uuid4().hex[:8]}"
        active_config = replace(config, job_id=job_id)
        if local_staging_root is None:
            with tempfile.TemporaryDirectory(prefix="stage2-remote-judge-") as tmp_dir:
                return _run_remote_batch_judge_in_dir(
                    requests,
                    config=active_config,
                    staging_dir=Path(tmp_dir),
                )
        staging_dir = local_staging_root / job_id
        staging_dir.mkdir(parents=True, exist_ok=True)
        return _run_remote_batch_judge_in_dir(
            requests,
            config=active_config,
            staging_dir=staging_dir,
        )

    return judge


def make_remote_judge_v2_batch_judge(
    config: RemoteJudgeV2Config,
) -> Callable[[list[BatchJudgeRequest]], list[dict[str, Any]]]:
    """Return an `import_responses` batch judge backed by judge-v2 control.

    judge-v2 exposes direct certificate verification via `/jobs`.
    """

    def judge(requests: list[BatchJudgeRequest]) -> list[dict[str, Any]]:
        indexed_requests = list(enumerate(requests))
        worker_count = max(1, int(config.max_workers))
        if worker_count == 1:
            return [
                _run_remote_judge_v2_one(
                    problem,
                    answer,
                    config=config,
                    index=index,
                )
                for index, (problem, answer) in indexed_requests
            ]
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            return list(
                executor.map(
                    lambda item: _run_remote_judge_v2_one(
                        item[1][0],
                        item[1][1],
                        config=config,
                        index=item[0],
                    ),
                    indexed_requests,
                )
            )

    return judge


def resolve_remote_judge_v2_base_urls(
    *,
    base_url: str | None = None,
    base_urls: str | Sequence[str] | None = None,
    environ: Mapping[str, str] | None = None,
) -> tuple[str, ...]:
    """Resolve judge-v2 control URL candidates by CLI/env/default precedence."""
    if base_url:
        return _normalize_remote_base_urls((base_url,))
    if base_urls:
        return _normalize_remote_base_urls(base_urls)

    active_environ = os.environ if environ is None else environ
    for name in (
        "STAGE2_REMOTE_JUDGE_V2_BASE_URLS",
        "STAGE2_REMOTE_JUDGE_BASE_URLS",
    ):
        env_base_urls = active_environ.get(name)
        if env_base_urls:
            return _normalize_remote_base_urls(env_base_urls)
    for name in (
        "STAGE2_REMOTE_JUDGE_V2_BASE_URL",
        "STAGE2_REMOTE_JUDGE_BASE_URL",
    ):
        env_base_url = active_environ.get(name)
        if env_base_url:
            return _normalize_remote_base_urls((env_base_url,))
    return DEFAULT_REMOTE_JUDGE_V2_BASE_URLS


def select_remote_judge_v2_base_url(
    base_urls: Sequence[str],
    *,
    request_timeout_seconds: int | None,
    health_check: Callable[[str, int | None], bool] | None = None,
) -> str:
    """Select the first healthy judge-v2 control endpoint."""
    candidates = _normalize_remote_base_urls(base_urls)
    if not candidates:
        raise ValueError("at least one remote judge-v2 base URL is required")
    checker = health_check or _remote_judge_v2_health_ok
    for base_url in candidates:
        if checker(base_url, request_timeout_seconds):
            return base_url
    raise RuntimeError("no healthy remote judge-v2 endpoint found: " + ", ".join(candidates))


def verify_official_stage2_records(
    records: Iterable[dict[str, Any]],
    *,
    output_path: Path,
    summary_path: Path | None = None,
    verify_fn: VerifyFn,
    resume: bool = False,
    max_workers: int = 1,
) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    seen_keys = _load_existing_keys(output_path) if resume else set()
    mode = "a" if resume else "w"
    status_counts: Counter[str] = Counter()
    error_code_counts: Counter[str] = Counter()
    written_count = 0
    pending_records = [
        record for record in records if not _record_seen(record, seen_keys=seen_keys)
    ]
    worker_count = max(1, int(max_workers))

    with output_path.open(mode, encoding="utf-8") as handle:
        if worker_count == 1:
            output_records = (_verify_one_record(record, verify_fn=verify_fn) for record in pending_records)
            for output_record in output_records:
                _write_output_record(handle, output_record)
                status_counts[str(output_record["status"])] += 1
                error_code_counts[str(output_record["error_code"])] += 1
                written_count += 1
        else:
            with ThreadPoolExecutor(max_workers=worker_count) as executor:
                output_records = executor.map(
                    lambda record: _verify_one_record(record, verify_fn=verify_fn),
                    pending_records,
                )
                for output_record in output_records:
                    _write_output_record(handle, output_record)
                    status_counts[str(output_record["status"])] += 1
                    error_code_counts[str(output_record["error_code"])] += 1
                    written_count += 1

    summary = {
        "schema_version": 1,
        "total_count": written_count,
        "accepted_count": status_counts.get("accepted", 0),
        "status_counts": dict(status_counts),
        "error_code_counts": dict(error_code_counts),
        "output_path": str(output_path),
        "max_workers": worker_count,
    }
    if summary_path is not None:
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def _run_remote_judge_v2_one(
    problem: dict[str, Any],
    answer: dict[str, Any],
    *,
    config: RemoteJudgeV2Config,
    index: int,
) -> dict[str, Any]:
    if answer.get("call") != "judge":
        return _remote_judge_v2_raw_result(
            job_id=None,
            status="malformed",
            error_code="REMOTE_JUDGE_V2_INVALID_ANSWER",
            message="answer.call must be judge",
            base_url=config.base_url,
        )
    verdict = str(answer.get("verdict") or "")
    code = answer.get("code")
    if verdict not in {"true", "false"} or not isinstance(code, str) or not code.strip():
        return _remote_judge_v2_raw_result(
            job_id=None,
            status="malformed",
            error_code="REMOTE_JUDGE_V2_INVALID_ANSWER",
            message="answer must include verdict=true|false and non-empty code",
            base_url=config.base_url,
            verdict=verdict or None,
        )

    payload: dict[str, Any] = {
        "problem": ensure_official_stage2_problem_defaults(problem),
        "verdict": verdict,
        "code": code,
    }
    if config.lean_timeout_seconds is not None:
        payload["timeout_seconds"] = max(1, int(config.lean_timeout_seconds))

    try:
        job = _remote_judge_v2_json_request(
            "POST",
            f"{config.base_url.rstrip('/')}/jobs",
            payload=payload,
            timeout=config.request_timeout_seconds,
        )
        job_id = str(job.get("job_id") or "")
        if not job_id:
            return _raw_result_from_judge_v2_detail(
                job,
                job_id=None,
                base_url=config.base_url,
                verdict=verdict,
            )
        detail = _wait_remote_judge_v2_job(config=config, job_id=job_id)
    except Exception as exc:  # noqa: BLE001
        return _remote_judge_v2_raw_result(
            job_id=None,
            status="error",
            error_code="REMOTE_JUDGE_V2_REQUEST_FAILED",
            message=f"{type(exc).__name__}: {exc}",
            base_url=config.base_url,
            verdict=verdict,
        )
    return _raw_result_from_judge_v2_detail(
        detail,
        job_id=job_id,
        base_url=config.base_url,
        verdict=verdict,
    )


def _wait_remote_judge_v2_job(
    *,
    config: RemoteJudgeV2Config,
    job_id: str,
) -> dict[str, Any]:
    deadline = (
        None
        if config.run_timeout_seconds is None
        else time.monotonic() + float(config.run_timeout_seconds)
    )
    while True:
        wait_timeout = max(0.1, float(config.wait_timeout_seconds))
        if deadline is not None:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return {"job_id": job_id, "status": "timeout", "result": None}
            wait_timeout = max(0.1, min(wait_timeout, remaining))
        query = urllib.parse.urlencode({"timeout_seconds": f"{wait_timeout:g}"})
        detail = _remote_judge_v2_json_request(
            "GET",
            f"{config.base_url.rstrip('/')}/jobs/{job_id}/wait?{query}",
            timeout=wait_timeout + (config.request_timeout_seconds or 0),
        )
        status = str(detail.get("status") or "")
        if status not in {"queued", "running"}:
            return detail
        time.sleep(max(0.05, float(config.poll_interval_seconds)))


def _raw_result_from_judge_v2_detail(
    detail: dict[str, Any],
    *,
    job_id: str | None,
    base_url: str,
    verdict: str,
) -> dict[str, Any]:
    remote_url = f"{base_url.rstrip('/')}/jobs/{job_id}" if job_id else None
    result = detail.get("result")
    if isinstance(result, dict):
        raw_result = dict(result)
        raw_result.setdefault("verdict", verdict)
        raw_result["remote_judge_v2"] = {
            "job_id": job_id,
            "url": remote_url,
            "job_status": detail.get("status"),
            "backend_url": raw_result.get("control_backend_url")
            or detail.get("backend_url"),
        }
        return raw_result

    status = str(detail.get("status") or "error")
    error = detail.get("error")
    message = error if isinstance(error, str) else str(detail)
    error_code = "REMOTE_JUDGE_V2_TIMEOUT" if status == "timeout" else "REMOTE_JUDGE_V2_NO_RESULT"
    return _remote_judge_v2_raw_result(
        job_id=job_id,
        status=status,
        error_code=error_code,
        message=message,
        base_url=base_url,
        verdict=verdict,
    )


def _remote_judge_v2_raw_result(
    *,
    job_id: str | None,
    status: str,
    error_code: str,
    message: str,
    base_url: str,
    verdict: str | None = None,
) -> dict[str, Any]:
    remote_url = f"{base_url.rstrip('/')}/jobs/{job_id}" if job_id else None
    return {
        "status": status,
        "error_code": error_code,
        "message": message,
        "stdout": "",
        "stderr": "" if status == "accepted" else message,
        "verdict": verdict,
        "artifact_path": remote_url,
        "direct_declarations": [],
        "axioms": [],
        "remote_judge_v2": {
            "job_id": job_id,
            "url": remote_url,
            "job_status": status,
            "backend_url": None,
        },
    }


def _remote_json_request(
    method: str,
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    timeout: int | float | None = None,
) -> dict[str, Any]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed with HTTP {exc.code}: {body}") from exc
    parsed = json.loads(body or "{}")
    if not isinstance(parsed, dict):
        raise RuntimeError(f"{method} {url} returned non-object JSON")
    return parsed


def _remote_judge_v2_json_request(
    method: str,
    url: str,
    *,
    payload: dict[str, Any] | None = None,
    timeout: int | float | None = None,
) -> dict[str, Any]:
    return _remote_json_request(method, url, payload=payload, timeout=timeout)


def _remote_judge_v2_health_ok(base_url: str, timeout: int | None) -> bool:
    try:
        payload = _remote_judge_v2_json_request(
            "GET",
            f"{base_url.rstrip('/')}/health",
            timeout=timeout,
        )
    except Exception:  # noqa: BLE001
        return False
    return payload.get("service") == "judge-v2-control" and payload.get("status") == "ok"


def _normalize_remote_base_urls(
    value: str | Sequence[str],
) -> tuple[str, ...]:
    if isinstance(value, str):
        raw_urls = value.split(",")
    else:
        raw_urls = list(value)
    urls: list[str] = []
    seen: set[str] = set()
    for raw_url in raw_urls:
        url = str(raw_url).strip().rstrip("/")
        if not url or url in seen:
            continue
        seen.add(url)
        urls.append(url)
    return tuple(urls)


def _run_remote_batch_judge_in_dir(
    requests: list[BatchJudgeRequest],
    *,
    config: RemoteOfficialStage2BatchConfig,
    staging_dir: Path,
) -> list[dict[str, Any]]:
    if not requests:
        return []
    input_path = staging_dir / "official_verify_input.jsonl"
    output_path = staging_dir / "official_verify_output.jsonl"
    artifact_dir = staging_dir / "artifacts"
    records = [
        {
            "problem_id": str(problem.get("id") or f"problem-{index:06d}"),
            "repeat_index": index,
            "problem": problem,
            "answer": answer,
        }
        for index, (problem, answer) in enumerate(requests)
    ]
    _write_jsonl(input_path, records)
    result = run_remote_official_stage2_batch(
        input_path=input_path,
        output_path=output_path,
        artifact_dir=artifact_dir,
        config=config,
    )
    raw_results = result["raw_results"]
    if len(raw_results) != len(requests):
        raise RuntimeError(
            f"remote official judge returned {len(raw_results)} result(s) for {len(requests)} request(s)"
        )
    return list(raw_results)


def _remote_batch_shell_command(
    *,
    config: RemoteOfficialStage2BatchConfig,
    remote_input: str,
    remote_output: str,
    remote_artifact_dir: str,
) -> str:
    command = [
        config.python,
        "scripts/lean_certificates/verify_official_stage2_batch.py",
        "--input",
        remote_input,
        "--output",
        remote_output,
        "--artifact-dir",
        remote_artifact_dir,
        "--max-workers",
        str(max(1, int(config.max_workers))),
    ]
    if config.cpu_limit:
        command.extend(["--cpus", config.cpu_limit])
    if config.memory_limit:
        command.extend(["--memory", config.memory_limit])
    if config.timeout_seconds is not None:
        command.extend(["--timeout-seconds", str(config.timeout_seconds)])
    if config.lean_timeout_seconds is not None:
        command.extend(["--lean-timeout-seconds", str(config.lean_timeout_seconds)])
    if config.max_code_length is not None:
        command.extend(["--max-code-length", str(config.max_code_length)])
    if config.max_false_cert_bytes is not None:
        command.extend(["--max-false-cert-bytes", str(config.max_false_cert_bytes)])
    quoted_command = " ".join(shlex.quote(part) for part in command)
    return f"cd {shlex.quote(config.repo)} && PYTHONPATH=src {quoted_command}"


def _run_checked(command: list[str], *, timeout: int | None) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "remote official judge command failed: "
            + " ".join(shlex.quote(part) for part in command)
            + f"\nstdout:\n{completed.stdout or ''}\nstderr:\n{completed.stderr or ''}"
        )
    return completed


def _remote_join(base: str, *parts: str) -> str:
    result = base.rstrip("/")
    for part in parts:
        result += "/" + str(part).strip("/")
    return result


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"remote official judge output not found: {path}")
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
            handle.write("\n")


def _raw_result_from_remote_row(row: dict[str, Any]) -> dict[str, Any]:
    raw_result = row.get("raw_result")
    if isinstance(raw_result, dict):
        return raw_result
    return {
        "status": str(row.get("status") or "malformed"),
        "error_code": str(row.get("error_code") or "REMOTE_BATCH_RESULT_ERROR"),
        "message": str(row.get("message") or "remote batch row did not include raw_result"),
        "verdict": row.get("verdict"),
        "stdout": "",
        "stderr": "",
        "artifact_path": row.get("artifact_path"),
        "direct_declarations": row.get("direct_declarations") or [],
        "axioms": row.get("axioms") or [],
    }


def build_docker_official_stage2_batch_command(
    *,
    input_path: Path,
    output_path: Path,
    artifact_dir: Path,
    image: str,
    max_workers: int,
    cpu_limit: str | None = None,
    memory_limit: str | None = None,
    resume: bool = False,
    summary_path: Path | None = None,
    lean_timeout_seconds: int | None = None,
    max_code_length: int | None = None,
    max_false_cert_bytes: int | None = None,
) -> list[str]:
    command = ["docker", "run", "--rm", "--network", "none"]
    if cpu_limit:
        command.extend(["--cpus", cpu_limit])
    if memory_limit:
        command.extend(["--memory", memory_limit])

    command.extend(
        [
            "-v",
            f"{input_path.parent.resolve()}:/input:ro",
            "-v",
            f"{output_path.parent.resolve()}:/output",
            "-v",
            f"{artifact_dir.resolve()}:/artifacts",
        ]
    )
    if summary_path is not None:
        command.extend(["-v", f"{summary_path.parent.resolve()}:/summary"])

    command.extend(
        [
            image,
            "python3",
            CONTAINER_WORKER,
            "--input",
            f"/input/{input_path.name}",
            "--output",
            f"/output/{output_path.name}",
            "--artifact-dir",
            "/artifacts",
            "--judge-repo",
            CONTAINER_JUDGE_REPO,
            "--max-workers",
            str(max_workers),
        ]
    )
    if summary_path is not None:
        command.extend(["--summary", f"/summary/{summary_path.name}"])
    if lean_timeout_seconds is not None:
        command.extend(["--lean-timeout-seconds", str(lean_timeout_seconds)])
    if max_code_length is not None:
        command.extend(["--max-code-length", str(max_code_length)])
    if max_false_cert_bytes is not None:
        command.extend(["--max-false-cert-bytes", str(max_false_cert_bytes)])
    if resume:
        command.append("--resume")
    return command


def _problem_from_flat_record(record: dict[str, Any], *, problem_id: str) -> dict[str, Any]:
    problem = {
        "id": problem_id,
        "eq1_id": record.get("eq1_id"),
        "eq2_id": record.get("eq2_id"),
        "equation1": record.get("equation1"),
        "equation2": record.get("equation2"),
    }
    for optional_key in ("proof_policy", "answer", "index", "difficulty"):
        if optional_key in record:
            problem[optional_key] = record[optional_key]
    return ensure_official_stage2_problem_defaults(problem)


def _verification_output_record(
    *,
    item: OfficialVerificationInput,
    raw_result: dict[str, Any],
    elapsed_seconds: float,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "problem_id": item.problem_id,
        "repeat_index": item.repeat_index,
        "status": str(raw_result.get("status") or ""),
        "error_code": str(raw_result.get("error_code") or ""),
        "message": str(raw_result.get("message") or ""),
        "verdict": raw_result.get("verdict"),
        "code_sha256": item.code_sha256,
        "elapsed_seconds": elapsed_seconds,
        "artifact_path": raw_result.get("artifact_path"),
        "direct_declarations": raw_result.get("direct_declarations") or [],
        "axioms": raw_result.get("axioms") or [],
        "raw_result": raw_result,
    }


def _verify_one_record(record: dict[str, Any], *, verify_fn: VerifyFn) -> dict[str, Any]:
    started = time.monotonic()
    try:
        item = extract_official_verification_input(record)
        raw_result = verify_fn(item.problem, item.answer)
        return _verification_output_record(
            item=item,
            raw_result=raw_result,
            elapsed_seconds=round(time.monotonic() - started, 6),
        )
    except Exception as exc:
        return {
            "schema_version": 1,
            "problem_id": str(record.get("problem_id") or record.get("id") or ""),
            "repeat_index": int(record.get("repeat_index") or 0),
            "status": "malformed",
            "error_code": "BATCH_RECORD_ERROR",
            "message": str(exc),
            "verdict": None,
            "code_sha256": "",
            "elapsed_seconds": round(time.monotonic() - started, 6),
            "artifact_path": None,
            "direct_declarations": [],
            "axioms": [],
            "raw_result": {},
        }


def _write_output_record(handle: Any, output_record: dict[str, Any]) -> None:
    handle.write(json.dumps(output_record, ensure_ascii=False, sort_keys=True))
    handle.write("\n")
    handle.flush()


def _verification_key(item: OfficialVerificationInput) -> str:
    return f"{item.problem_id}|{item.repeat_index}|{item.code_sha256}"


def _record_seen(record: dict[str, Any], *, seen_keys: set[str]) -> bool:
    if not seen_keys:
        return False
    try:
        return _verification_key(extract_official_verification_input(record)) in seen_keys
    except Exception:
        return False


def _load_existing_keys(output_path: Path) -> set[str]:
    if not output_path.exists():
        return set()
    keys: set[str] = set()
    with output_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            keys.add(
                f"{record.get('problem_id') or ''}|{int(record.get('repeat_index') or 0)}|{record.get('code_sha256') or ''}"
            )
    return keys
