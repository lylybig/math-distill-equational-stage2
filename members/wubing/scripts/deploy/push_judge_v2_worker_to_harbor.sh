#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../../.." && pwd)"

HARBOR_REGISTRY="${HARBOR_REGISTRY:-harbor.zetyun.cn}"
HARBOR_USER="${HARBOR_USER:-robot\$titan+judge-v2-pusher}"
HARBOR_PASSWORD="${HARBOR_PASSWORD:-}"
HARBOR_PROJECT="${HARBOR_PROJECT:-titan}"
HARBOR_IMAGE_PREFIX="${HARBOR_IMAGE_PREFIX:-}"
IMAGE_TAG="${IMAGE_TAG:-20260601}"
OFFICIAL_JUDGE_BASE_TAG="${OFFICIAL_JUDGE_BASE_TAG:-latest}"
BASE_IMAGE="${BASE_IMAGE:-}"
WORKER_IMAGE="${WORKER_IMAGE:-}"
SKIP_BASE_BUILD="${SKIP_BASE_BUILD:-}"
PUSH_BASE_IMAGE="${PUSH_BASE_IMAGE:-}"
PLATFORM="${PLATFORM:-linux/amd64}"
PULL_BASE_IMAGE="${PULL_BASE_IMAGE:-auto}"

usage() {
  cat <<'EOF'
Usage:
  members/wubing/scripts/deploy/push_judge_v2_worker_to_harbor.sh

  members/wubing/scripts/deploy/push_judge_v2_worker_to_harbor.sh \
    HARBOR_USER='robot$titan+judge-v2-pusher' HARBOR_PASSWORD=... HARBOR_PROJECT=titan

Required:
  HARBOR_PASSWORD        If omitted, the script prompts with hidden input.

Defaults:
  HARBOR_USER            robot$titan+judge-v2-pusher
  HARBOR_PROJECT         titan; Harbor project/path, e.g. the path segment used by
                         harbor.zetyun.cn/<project>/math-distill-stage2-official-judge

Optional:
  HARBOR_REGISTRY        default: harbor.zetyun.cn
  HARBOR_IMAGE_PREFIX    full image prefix; overrides HARBOR_REGISTRY/HARBOR_PROJECT
  IMAGE_TAG              default: 20260601
  OFFICIAL_JUDGE_BASE_TAG default: latest
  BASE_IMAGE             default:
                         harbor.zetyun.cn/titan/math-distill-stage2-official-judge:$OFFICIAL_JUDGE_BASE_TAG
  WORKER_IMAGE           default: judge-v2-worker:$IMAGE_TAG
  SKIP_BASE_BUILD        default: 1 when BASE_IMAGE is a registry image
  PULL_BASE_IMAGE        default: auto; explicitly docker pull BASE_IMAGE before build
  PUSH_BASE_IMAGE        default: 0 when BASE_IMAGE is a registry image
  PLATFORM               default: linux/amd64
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

for arg in "$@"; do
  case "${arg}" in
    HARBOR_REGISTRY=*) HARBOR_REGISTRY="${arg#*=}" ;;
    HARBOR_USER=*) HARBOR_USER="${arg#*=}" ;;
    HARBOR_PASSWORD=*) HARBOR_PASSWORD="${arg#*=}" ;;
    HARBOR_PROJECT=*) HARBOR_PROJECT="${arg#*=}" ;;
    HARBOR_IMAGE_PREFIX=*) HARBOR_IMAGE_PREFIX="${arg#*=}" ;;
    IMAGE_TAG=*) IMAGE_TAG="${arg#*=}" ;;
    OFFICIAL_JUDGE_BASE_TAG=*) OFFICIAL_JUDGE_BASE_TAG="${arg#*=}" ;;
    BASE_IMAGE=*) BASE_IMAGE="${arg#*=}" ;;
    WORKER_IMAGE=*) WORKER_IMAGE="${arg#*=}" ;;
    SKIP_BASE_BUILD=*) SKIP_BASE_BUILD="${arg#*=}" ;;
    PULL_BASE_IMAGE=*) PULL_BASE_IMAGE="${arg#*=}" ;;
    PUSH_BASE_IMAGE=*) PUSH_BASE_IMAGE="${arg#*=}" ;;
    PLATFORM=*) PLATFORM="${arg#*=}" ;;
    *)
      echo "ERROR: unknown argument: ${arg}" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "${HARBOR_PASSWORD}" ]]; then
  read -r -s -p "Harbor password for ${HARBOR_USER}: " HARBOR_PASSWORD
  echo
fi

if [[ -z "${HARBOR_IMAGE_PREFIX}" ]]; then
  if [[ -z "${HARBOR_PROJECT}" ]]; then
    echo "ERROR: set HARBOR_PROJECT or HARBOR_IMAGE_PREFIX." >&2
    usage >&2
    exit 2
  fi
  HARBOR_IMAGE_PREFIX="${HARBOR_REGISTRY}/${HARBOR_PROJECT}"
fi

if [[ -z "${BASE_IMAGE}" ]]; then
  BASE_IMAGE="${HARBOR_IMAGE_PREFIX}/math-distill-stage2-official-judge:${OFFICIAL_JUDGE_BASE_TAG}"
fi
if [[ -z "${WORKER_IMAGE}" ]]; then
  WORKER_IMAGE="judge-v2-worker:${IMAGE_TAG}"
fi
if [[ -z "${SKIP_BASE_BUILD}" ]]; then
  if [[ "${BASE_IMAGE}" == */* ]]; then
    SKIP_BASE_BUILD=1
  else
    SKIP_BASE_BUILD=0
  fi
fi
if [[ -z "${PUSH_BASE_IMAGE}" ]]; then
  if [[ "${BASE_IMAGE}" == "${HARBOR_IMAGE_PREFIX}/"* ]]; then
    PUSH_BASE_IMAGE=0
  else
    PUSH_BASE_IMAGE=1
  fi
fi

DOCKER_CONFIG_DIR="$(mktemp -d)"
ORIGINAL_DOCKER_CONFIG="${DOCKER_CONFIG:-${HOME}/.docker}"
CURRENT_DOCKER_CONTEXT="${DOCKER_CONTEXT:-$(docker context show 2>/dev/null || true)}"
cleanup() {
  docker --config "${DOCKER_CONFIG_DIR}" logout "${HARBOR_REGISTRY}" >/dev/null 2>&1 || true
  rm -rf "${DOCKER_CONFIG_DIR}"
}
trap cleanup EXIT

if [[ -d "${ORIGINAL_DOCKER_CONFIG}/contexts" ]]; then
  cp -R "${ORIGINAL_DOCKER_CONFIG}/contexts" "${DOCKER_CONFIG_DIR}/contexts"
fi
if [[ -n "${CURRENT_DOCKER_CONTEXT}" && "${CURRENT_DOCKER_CONTEXT}" != "default" ]]; then
  printf '{"currentContext":"%s"}\n' "${CURRENT_DOCKER_CONTEXT}" >"${DOCKER_CONFIG_DIR}/config.json"
fi

printf '%s' "${HARBOR_PASSWORD}" | docker --config "${DOCKER_CONFIG_DIR}" login "${HARBOR_REGISTRY}" \
  -u "${HARBOR_USER}" \
  --password-stdin

export DOCKER_CONFIG="${DOCKER_CONFIG_DIR}"

cd "${REPO_ROOT}"

REGISTRY="${HARBOR_IMAGE_PREFIX}" \
BASE_IMAGE="${BASE_IMAGE}" \
WORKER_IMAGE="${WORKER_IMAGE}" \
SKIP_BASE_BUILD="${SKIP_BASE_BUILD}" \
PLATFORM="${PLATFORM}" \
PULL_BASE_IMAGE="${PULL_BASE_IMAGE}" \
PUSH=0 \
"${SCRIPT_DIR}/build_judge_v2_worker_image.sh"

BASE_NAME="${BASE_IMAGE##*/}"
WORKER_NAME="${WORKER_IMAGE##*/}"
REMOTE_BASE_IMAGE="${HARBOR_IMAGE_PREFIX}/${BASE_NAME}"
REMOTE_WORKER_IMAGE="${HARBOR_IMAGE_PREFIX}/${WORKER_NAME}"

if [[ "${PUSH_BASE_IMAGE}" == "1" ]]; then
  docker --config "${DOCKER_CONFIG_DIR}" push "${REMOTE_BASE_IMAGE}"
fi
docker --config "${DOCKER_CONFIG_DIR}" push "${REMOTE_WORKER_IMAGE}"

cat <<EOF

Pushed:
  ${REMOTE_WORKER_IMAGE}
EOF
if [[ "${PUSH_BASE_IMAGE}" == "1" ]]; then
  cat <<EOF
  ${REMOTE_BASE_IMAGE}
EOF
fi
cat <<EOF
Use this on worker machines:
  IMAGE_REF=${REMOTE_WORKER_IMAGE}
EOF
