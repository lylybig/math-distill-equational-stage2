#!/usr/bin/env bash
set -euo pipefail

HARBOR_REGISTRY="${HARBOR_REGISTRY:-harbor.zetyun.cn}"
HARBOR_USER="${HARBOR_USER:-robot\$titan+judge-v2-pusher}"
HARBOR_PASSWORD="${HARBOR_PASSWORD:-}"
HARBOR_PROJECT="${HARBOR_PROJECT:-titan}"
HARBOR_IMAGE_PREFIX="${HARBOR_IMAGE_PREFIX:-}"
IMAGE_TAG="${IMAGE_TAG:-20260601}"
IMAGE_REF="${IMAGE_REF:-}"

RUN_USER="${SUDO_USER:-${USER:-$(id -un)}}"
RUN_HOME="$(getent passwd "${RUN_USER}" 2>/dev/null | cut -d: -f6 || true)"
RUN_HOME="${RUN_HOME:-${HOME}}"
DEFAULT_DATA_DIR="${RUN_HOME}/judge_v2_control"
DEFAULT_BACKENDS="http://10.220.69.172:8889,http://10.220.69.153:8889,http://10.220.69.85:8889,http://10.220.69.89:8889"
HOST_PORT="${HOST_PORT:-8890}"
CONTAINER_PORT="${CONTAINER_PORT:-${HOST_PORT}}"
CONTAINER_NAME="${CONTAINER_NAME:-judge-v2-control-${HOST_PORT}}"
BACKENDS="${BACKENDS:-${DEFAULT_BACKENDS}}"
CONTROL_DISPATCHERS="${CONTROL_DISPATCHERS:-96}"
DATA_DIR="${DATA_DIR:-${DEFAULT_DATA_DIR}}"
DB_PATH="${DB_PATH:-/var/lib/judge_v2_control/control.sqlite}"
RESTART_POLICY="${RESTART_POLICY:-unless-stopped}"
NETWORK_MODE="${NETWORK_MODE:-bridge}"
HEALTH_RETRIES="${HEALTH_RETRIES:-20}"
HEALTH_INTERVAL_SECONDS="${HEALTH_INTERVAL_SECONDS:-1}"
DOCKER_BIN="${DOCKER_BIN:-}"

usage() {
  cat <<'EOF'
Usage on 172:
  bash deploy_judge_v2_control_from_harbor.sh

Required:
  HARBOR_PASSWORD        If omitted, the script prompts with hidden input.

Defaults:
  HARBOR_USER            robot$titan+judge-v2-pusher
  HARBOR_PROJECT         titan
  IMAGE_REF              harbor.zetyun.cn/titan/judge-v2-worker:20260601

Optional:
  HOST_PORT              default: 8890
  CONTAINER_PORT         default: same as HOST_PORT
  CONTAINER_NAME         default: judge-v2-control-$HOST_PORT
  BACKENDS               default: http://10.220.69.172:8889,http://10.220.69.153:8889,http://10.220.69.85:8889,http://10.220.69.89:8889
                         comma-separated worker URLs
  CONTROL_DISPATCHERS    default: 96
  DATA_DIR               default: invoking user's home/judge_v2_control
  DOCKER_BIN             default: auto; tries docker, then sudo docker
  NETWORK_MODE           default: bridge; use host to avoid Docker publishing issues
  HEALTH_RETRIES         default: 20
  HEALTH_INTERVAL_SECONDS default: 1
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
    IMAGE_REF=*) IMAGE_REF="${arg#*=}" ;;
    HOST_PORT=*) HOST_PORT="${arg#*=}" ;;
    CONTAINER_PORT=*) CONTAINER_PORT="${arg#*=}" ;;
    CONTAINER_NAME=*) CONTAINER_NAME="${arg#*=}" ;;
    BACKENDS=*) BACKENDS="${arg#*=}" ;;
    CONTROL_DISPATCHERS=*) CONTROL_DISPATCHERS="${arg#*=}" ;;
    DATA_DIR=*) DATA_DIR="${arg#*=}" ;;
    DB_PATH=*) DB_PATH="${arg#*=}" ;;
    RESTART_POLICY=*) RESTART_POLICY="${arg#*=}" ;;
    NETWORK_MODE=*) NETWORK_MODE="${arg#*=}" ;;
    HEALTH_RETRIES=*) HEALTH_RETRIES="${arg#*=}" ;;
    HEALTH_INTERVAL_SECONDS=*) HEALTH_INTERVAL_SECONDS="${arg#*=}" ;;
    DOCKER_BIN=*) DOCKER_BIN="${arg#*=}" ;;
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

if [[ -z "${DOCKER_BIN}" ]]; then
  if docker info >/dev/null 2>&1; then
    DOCKER_BIN="docker"
  elif command -v sudo >/dev/null 2>&1; then
    echo "Docker is not accessible as ${RUN_USER}; trying sudo docker." >&2
    if sudo -v && sudo docker info >/dev/null 2>&1; then
      DOCKER_BIN="sudo docker"
    else
      echo "ERROR: cannot access Docker daemon with docker or sudo docker." >&2
      exit 1
    fi
  else
    echo "ERROR: cannot access Docker daemon with docker or sudo docker." >&2
    exit 1
  fi
fi
echo "Using Docker command: ${DOCKER_BIN}"
echo "Using DATA_DIR: ${DATA_DIR}"
echo "Using BACKENDS: ${BACKENDS}"

docker_cmd() {
  # shellcheck disable=SC2086
  ${DOCKER_BIN} "$@"
}

if [[ -z "${IMAGE_REF}" ]]; then
  if [[ -z "${HARBOR_IMAGE_PREFIX}" ]]; then
    HARBOR_IMAGE_PREFIX="${HARBOR_REGISTRY}/${HARBOR_PROJECT}"
  fi
  IMAGE_REF="${HARBOR_IMAGE_PREFIX}/judge-v2-worker:${IMAGE_TAG}"
fi

DOCKER_CONFIG_DIR="$(mktemp -d)"
ORIGINAL_DOCKER_CONFIG="${DOCKER_CONFIG:-${HOME}/.docker}"
CURRENT_DOCKER_CONTEXT="${DOCKER_CONTEXT:-$(docker context show 2>/dev/null || true)}"
cleanup() {
  docker_cmd --config "${DOCKER_CONFIG_DIR}" logout "${HARBOR_REGISTRY}" >/dev/null 2>&1 || true
  rm -rf "${DOCKER_CONFIG_DIR}"
}
trap cleanup EXIT

if [[ -d "${ORIGINAL_DOCKER_CONFIG}/contexts" ]]; then
  cp -R "${ORIGINAL_DOCKER_CONFIG}/contexts" "${DOCKER_CONFIG_DIR}/contexts"
fi
if [[ -n "${CURRENT_DOCKER_CONTEXT}" && "${CURRENT_DOCKER_CONTEXT}" != "default" ]]; then
  printf '{"currentContext":"%s"}\n' "${CURRENT_DOCKER_CONTEXT}" >"${DOCKER_CONFIG_DIR}/config.json"
fi

printf '%s' "${HARBOR_PASSWORD}" | docker_cmd --config "${DOCKER_CONFIG_DIR}" login "${HARBOR_REGISTRY}" \
  -u "${HARBOR_USER}" \
  --password-stdin

docker_cmd --config "${DOCKER_CONFIG_DIR}" pull "${IMAGE_REF}"

if ! mkdir -p "${DATA_DIR}" 2>/dev/null; then
  echo "ERROR: cannot create DATA_DIR=${DATA_DIR}" >&2
  exit 1
fi
if [[ "${DOCKER_BIN}" == *"sudo"* || "$(id -u)" == "0" ]]; then
  sudo chown -R "${RUN_USER}:${RUN_USER}" "${DATA_DIR}" 2>/dev/null || true
fi

if docker_cmd ps -a --format '{{.Names}}' | grep -Fxq "${CONTAINER_NAME}"; then
  docker_cmd rm -f "${CONTAINER_NAME}"
fi

DOCKER_RUN_ARGS=(
  -d
  --name "${CONTAINER_NAME}"
  --restart "${RESTART_POLICY}"
  --health-cmd "curl -fsS http://127.0.0.1:${CONTAINER_PORT}/health || exit 1"
  --health-interval 30s
  --health-timeout 10s
  --health-start-period 30s
  --health-retries 3
  -e "JUDGE_V2_CONTROL_BACKENDS=${BACKENDS}"
  -e "JUDGE_V2_CONTROL_DB=${DB_PATH}"
  -e "JUDGE_V2_CONTROL_DISPATCHERS=${CONTROL_DISPATCHERS}"
  -v "${DATA_DIR}:/var/lib/judge_v2_control"
)
if [[ "${NETWORK_MODE}" == "host" ]]; then
  DOCKER_RUN_ARGS+=(--network host)
else
  DOCKER_RUN_ARGS+=(-p "${HOST_PORT}:${CONTAINER_PORT}")
fi

docker_cmd run "${DOCKER_RUN_ARGS[@]}" "${IMAGE_REF}" \
  python3 -m uvicorn judge_v2.control.app:app --host 0.0.0.0 --port "${CONTAINER_PORT}"

echo "Started ${CONTAINER_NAME} from ${IMAGE_REF}"
echo "Health:"
health_ok=0
for attempt in $(seq 1 "${HEALTH_RETRIES}"); do
  if health_body="$(curl -fsS "http://127.0.0.1:${HOST_PORT}/health" 2>/dev/null)"; then
    printf '%s\n' "${health_body}"
    health_ok=1
    break
  fi
  if [[ "${attempt}" != "${HEALTH_RETRIES}" ]]; then
    sleep "${HEALTH_INTERVAL_SECONDS}"
  fi
done
if [[ "${health_ok}" != "1" ]]; then
  echo
  echo "WARN: health check failed; inspect logs with: ${DOCKER_BIN} logs --tail 200 ${CONTAINER_NAME}" >&2
  exit 1
fi
echo
