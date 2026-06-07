# judge_v2 worker MVP

## Scope

This first v2 step adds an independent worker package under:

```text
members/wubing/src/judge_v2/
```

The worker does not import the legacy top-level `judge_service/server.py`. It dynamically loads the official Stage 2 `judge/verify.py` from `JUDGE_REPO` at runtime.

## Worker entrypoint

```bash
cd /workspace
PYTHONPATH=members/wubing/src \
JUDGE_REPO=/workspace/members/wubing/external/equational-theories-lean-stage2 \
JUDGE_V2_WORKERS=8 \
JUDGE_V2_CACHE_PATH=/workspace/artifacts/cache/judge_v2_worker.sqlite \
uvicorn judge_v2.worker.app:app --host 0.0.0.0 --port 9001
```

## Docker image

Worker image files:

- `members/wubing/docker/judge-v2-worker/Dockerfile`
- `members/wubing/docker/judge-v2-worker/README.md`
- `members/wubing/scripts/deploy/build_judge_v2_worker_image.sh`
- `members/wubing/scripts/deploy/deploy_judge_v2_worker_from_harbor.sh`
- `members/wubing/scripts/deploy/deploy_judge_v2_control_from_harbor.sh`
- `members/wubing/scripts/deploy/push_judge_v2_worker_to_harbor.sh`
- `members/wubing/scripts/deploy/smoke_judge_v2_worker.py`

Build and push:

```bash
REGISTRY=registry.company.local/math-distill \
PUSH=1 \
members/wubing/scripts/deploy/build_judge_v2_worker_image.sh
```

## Endpoints

- `GET /health`
- `GET /stats`
- `POST /verify`

`POST /verify` keeps the old worker request shape:

```json
{
  "problem": {"id": "true_5_2638", "eq1_id": 5, "eq2_id": 2638},
  "verdict": "true",
  "code": "exact ...",
  "timeout_seconds": 120
}
```

## Notes

- Cache keys include `problem.id`, `verdict`, `code`, and `service_rev`.
- `service_rev` includes official verifier hash, Lean version hash, and mathlib revision.
- This MVP is meant to run on `172:9001` before replacing any existing `:9000` worker.

## Local checks

```bash
PYTHONPATH=members/wubing/src .venv/bin/python -m pytest -q members/wubing/tests/judge_v2/test_worker_app.py
PYTHONPATH=members/wubing/src .venv/bin/python -m compileall -q members/wubing/src/judge_v2 members/wubing/tests/judge_v2
```

Result: worker unit tests passed, module compilation passed, and a temporary uvicorn process returned `GET /health` successfully.

Real Lean verification was not run on the local laptop in this pass because `lean --version` did not complete promptly in the current local elan environment. The intended first real smoke is on `10.220.69.172:9001` with a known-good Lean/Lake setup.

## 172 deployment smoke

The first deployed worker listens at:

```text
http://10.220.69.172:8889
```

Smoke command:

```bash
python3 members/wubing/scripts/deploy/smoke_judge_v2_worker.py \
  --base-url http://10.220.69.172:8889
```

Observed result after deployment:

- `GET /health`: ok, `workers_total=8`
- true fixture: `accepted / ACCEPTED`
- repeated true fixture: `accepted / ACCEPTED / cached=true`
- false witness fixture: `accepted / ACCEPTED`

## Control MVP

The control service now lives under:

```text
members/wubing/src/judge_v2/control/
```

Endpoints:

- `GET /health`
- `POST /verify`
- `POST /jobs`
- `GET /jobs`
- `GET /jobs/{job_id}`
- `GET /jobs/{job_id}/wait?timeout_seconds=...`

Local smoke with one backend:

```bash
PYTHONPATH=members/wubing/src \
JUDGE_V2_CONTROL_BACKENDS=http://10.220.69.172:8889 \
JUDGE_V2_CONTROL_DB=/tmp/judge_v2_control_smoke.sqlite \
.venv/bin/python -m uvicorn judge_v2.control.app:app --host 127.0.0.1 --port 19100
```

Observed result:

- `GET /health`: backend `10.220.69.172:8889` healthy
- `POST /verify`: accepted
- `POST /jobs` then `/jobs/{job_id}/wait`: accepted, backend `10.220.69.172:8889`

Deploy on 172 after rebuilding/pushing the current image:

```bash
bash deploy_judge_v2_control_from_harbor.sh
```

Default control address:

```text
http://10.220.69.172:8890
```
