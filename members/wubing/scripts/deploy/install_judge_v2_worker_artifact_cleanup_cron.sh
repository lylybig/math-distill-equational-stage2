#!/usr/bin/env bash
set -euo pipefail

RUN_USER="${SUDO_USER:-${USER:-$(id -un)}}"
RUN_HOME="$(getent passwd "${RUN_USER}" 2>/dev/null | cut -d: -f6 || true)"
RUN_HOME="${RUN_HOME:-${HOME}}"
DEFAULT_DATA_DIR="${RUN_HOME}/judge_v2_worker"

DATA_DIR="${DATA_DIR:-${DEFAULT_DATA_DIR}}"
ARTIFACT_DIR="${ARTIFACT_DIR:-${DATA_DIR}/artifacts}"
RETENTION_MINUTES="${RETENTION_MINUTES:-360}"
CRON_SCHEDULE="${CRON_SCHEDULE:-*/30 * * * *}"
LOG_PATH="${LOG_PATH:-${DATA_DIR}/artifact-cleanup.log}"
MARKER="judge-v2-worker-artifact-cleanup"

usage() {
  cat <<'EOF'
Usage:
  members/wubing/scripts/deploy/install_judge_v2_worker_artifact_cleanup_cron.sh

Optional KEY=VALUE arguments:
  DATA_DIR             default: invoking user's home/judge_v2_worker
  ARTIFACT_DIR         default: DATA_DIR/artifacts
  RETENTION_MINUTES    default: 360 (6 hours)
  CRON_SCHEDULE        default: */30 * * * *
  LOG_PATH             default: DATA_DIR/artifact-cleanup.log

Examples:
  # Keep artifacts for 6 hours and clean every 30 minutes.
  members/wubing/scripts/deploy/install_judge_v2_worker_artifact_cleanup_cron.sh

  # Keep artifacts for 24 hours.
  members/wubing/scripts/deploy/install_judge_v2_worker_artifact_cleanup_cron.sh \
    RETENTION_MINUTES=1440
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

for arg in "$@"; do
  case "${arg}" in
    DATA_DIR=*) DATA_DIR="${arg#*=}" ;;
    ARTIFACT_DIR=*) ARTIFACT_DIR="${arg#*=}" ;;
    RETENTION_MINUTES=*) RETENTION_MINUTES="${arg#*=}" ;;
    CRON_SCHEDULE=*) CRON_SCHEDULE="${arg#*=}" ;;
    LOG_PATH=*) LOG_PATH="${arg#*=}" ;;
    *)
      echo "ERROR: unknown argument: ${arg}" >&2
      usage >&2
      exit 2
      ;;
  esac
done

case "${RETENTION_MINUTES}" in
  ''|*[!0-9]*)
    echo "ERROR: RETENTION_MINUTES must be a positive integer." >&2
    exit 2
    ;;
esac
if [[ "${RETENTION_MINUTES}" -le 0 ]]; then
  echo "ERROR: RETENTION_MINUTES must be positive." >&2
  exit 2
fi

mkdir -p "${ARTIFACT_DIR}" "$(dirname "${LOG_PATH}")"
if [[ "$(id -u)" == "0" && "${RUN_USER}" != "root" ]]; then
  chown -R "${RUN_USER}:${RUN_USER}" "${DATA_DIR}" 2>/dev/null || true
fi

sq() {
  printf "'%s'" "$(printf '%s' "$1" | sed "s/'/'\\\\''/g")"
}

q_artifact_dir="$(sq "${ARTIFACT_DIR}")"
q_log_path="$(sq "${LOG_PATH}")"
cron_command="find ${q_artifact_dir} -mindepth 1 -maxdepth 1 -type d -mmin +${RETENTION_MINUTES} -exec rm -rf -- {} + >> ${q_log_path} 2>&1"
cron_line="${CRON_SCHEDULE} ${cron_command} # ${MARKER}"

CRONTAB_CMD=(crontab)
if [[ "$(id -u)" == "0" && "${RUN_USER}" != "root" ]]; then
  CRONTAB_CMD=(crontab -u "${RUN_USER}")
fi

tmp="$(mktemp)"
cleanup() {
  rm -f "${tmp}"
}
trap cleanup EXIT

"${CRONTAB_CMD[@]}" -l 2>/dev/null | grep -v "# ${MARKER}$" >"${tmp}" || true
printf '%s\n' "${cron_line}" >>"${tmp}"
"${CRONTAB_CMD[@]}" "${tmp}"

cat <<EOF
Installed cron cleanup for ${RUN_USER}:
  ${cron_line}

Artifact dir:
  ${ARTIFACT_DIR}

Retention:
  ${RETENTION_MINUTES} minutes
EOF
