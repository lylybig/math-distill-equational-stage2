#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WUBING_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

BASE_IMAGE="${BASE_IMAGE:-math-distill-stage2-official-judge:latest}"
WORKER_IMAGE="${WORKER_IMAGE:-judge-v2-worker:latest}"
REGISTRY="${REGISTRY:-}"
PUSH="${PUSH:-0}"
SKIP_BASE_BUILD="${SKIP_BASE_BUILD:-0}"
SAVE_TAR="${SAVE_TAR:-}"
PLATFORM="${PLATFORM:-linux/amd64}"
PULL_BASE_IMAGE="${PULL_BASE_IMAGE:-auto}"

BUILD_PLATFORM_ARGS=()
if [[ -n "${PLATFORM}" ]]; then
  BUILD_PLATFORM_ARGS=(--platform "${PLATFORM}")
fi

cd "${WUBING_ROOT}"

if [[ "${SKIP_BASE_BUILD}" != "1" ]]; then
  docker build \
    "${BUILD_PLATFORM_ARGS[@]}" \
    -f docker/official-stage2-judge/Dockerfile \
    -t "${BASE_IMAGE}" \
    .
else
  if [[ "${PULL_BASE_IMAGE}" == "auto" ]]; then
    if [[ "${BASE_IMAGE}" == */* ]]; then
      PULL_BASE_IMAGE=1
    else
      PULL_BASE_IMAGE=0
    fi
  fi
  if [[ "${PULL_BASE_IMAGE}" == "1" ]]; then
    docker pull "${BUILD_PLATFORM_ARGS[@]}" "${BASE_IMAGE}"
  fi
fi

docker build \
  "${BUILD_PLATFORM_ARGS[@]}" \
  -f docker/judge-v2-worker/Dockerfile \
  --build-arg "BASE_IMAGE=${BASE_IMAGE}" \
  -t "${WORKER_IMAGE}" \
  .

if [[ -n "${REGISTRY}" ]]; then
  BASE_NAME="${BASE_IMAGE##*/}"
  WORKER_NAME="${WORKER_IMAGE##*/}"
  docker tag "${BASE_IMAGE}" "${REGISTRY}/${BASE_NAME}"
  docker tag "${WORKER_IMAGE}" "${REGISTRY}/${WORKER_NAME}"

  if [[ "${PUSH}" == "1" ]]; then
    docker push "${REGISTRY}/${BASE_NAME}"
    docker push "${REGISTRY}/${WORKER_NAME}"
  fi
fi

if [[ -n "${SAVE_TAR}" ]]; then
  mkdir -p "$(dirname "${SAVE_TAR}")"
  docker save "${BASE_IMAGE}" "${WORKER_IMAGE}" -o "${SAVE_TAR}"
fi

docker image ls "${BASE_IMAGE%:*}" || true
docker image ls "${WORKER_IMAGE%:*}" || true
