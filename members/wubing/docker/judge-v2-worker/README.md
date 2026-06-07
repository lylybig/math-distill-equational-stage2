# judge-v2-worker image

This image contains the independent v2 judge worker and control services.

It is intentionally based on `math-distill-stage2-official-judge:latest`, so the heavy Lean/mathlib layers stay in the base image and the worker service layer stays small.

## Build

Build from `members/wubing` as Docker context:

```bash
cd members/wubing

docker build \
  -f docker/official-stage2-judge/Dockerfile \
  -t math-distill-stage2-official-judge:latest \
  .

docker build \
  -f docker/judge-v2-worker/Dockerfile \
  -t judge-v2-worker:latest \
  .
```

Or use the helper script from the repository root:

```bash
members/wubing/scripts/deploy/build_judge_v2_worker_image.sh
```

## Push to company registry

Recommended: use a temporary Docker login config so existing machine logins are not overwritten.

First find the Harbor project/path from the official judge base image. If the base image is:

```text
harbor.zetyun.cn/<project>/math-distill-stage2-official-judge:<tag>
```

then use the same `<project>` as `HARBOR_PROJECT`.

Push with:

```bash
HARBOR_USER='robot$titan+judge-v2-pusher' \
HARBOR_PASSWORD='temporary-password' \
HARBOR_PROJECT='<project>' \
IMAGE_TAG=20260601 \
PUSH=1 \
members/wubing/scripts/deploy/push_judge_v2_worker_to_harbor.sh
```

If the server cannot pull from the registry directly, export a tarball:

```bash
SAVE_TAR=/tmp/judge-v2-worker-images.tar \
members/wubing/scripts/deploy/build_judge_v2_worker_image.sh
```

## Run on 172

```bash
HARBOR_USER='robot$titan+judge-v2-pusher' \
HARBOR_PASSWORD='temporary-password' \
HARBOR_PROJECT='<project>' \
IMAGE_TAG=20260601 \
JUDGE_V2_WORKERS=8 \
members/wubing/scripts/deploy/deploy_judge_v2_worker_from_harbor.sh
```

Health check:

```bash
curl -fsS http://127.0.0.1:8889/health | python3 -m json.tool
```

Smoke verify:

```bash
python3 members/wubing/scripts/deploy/smoke_judge_v2_worker.py \
  --base-url http://127.0.0.1:8889
```

For the current 172 worker from another machine:

```bash
python3 members/wubing/scripts/deploy/smoke_judge_v2_worker.py \
  --base-url http://10.220.69.172:8889
```

## Run control on 172

After rebuilding and pushing the image with the current `src/judge_v2` contents, start the control service:

```bash
members/wubing/scripts/deploy/deploy_judge_v2_control_from_harbor.sh
```

By default this exposes:

```text
http://10.220.69.172:8890
```

and dispatches to:

```text
http://10.220.69.172:8889
```

For multiple workers:

```bash
members/wubing/scripts/deploy/deploy_judge_v2_control_from_harbor.sh \
  BACKENDS=http://10.220.69.172:8889,http://10.220.69.153:8889
```
