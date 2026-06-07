#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════════════════
#  run_eval.sh — thin wrapper around run_eval.py
#
#  Adds:
#    • --background    Detach with nohup + log redirection; print PID + tail cmd
#    • --tail          Tail the log file of the previous --background launch
#    • --kill          Kill the previous --background launch
#
#  Everything else (--solver / --problems / --workers / --timeout / ...) is
#  passed through to scripts/run_eval.py.  See run_eval.py --help for full opts.
#
#  Examples:
#    # smoke (5 problems, 1 worker, 60s/题):
#    bash scripts/run_eval.sh --smoke
#
#    # default sample_200 baseline:
#    bash scripts/run_eval.sh --solver solvers/baseline_solver_v3e.py
#
#    # full 1669 contest, 32 workers, 30 min/题, detached:
#    bash scripts/run_eval.sh \
#        --solver   solvers/baseline_solver_v3e.py \
#        --problems third_party/equational-theories-lean-stage2/examples/problems/contest_1669.jsonl \
#        --workers  32 --timeout 1800 \
#        --output   results/baseline_solver_v3e_contest_1669.json \
#        --background
#
#    # check progress / tail log / kill:
#    bash scripts/run_eval.sh --tail results/baseline_solver_v3e_contest_1669.json
#    bash scripts/run_eval.sh --kill results/baseline_solver_v3e_contest_1669.json
# ════════════════════════════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

# ── Parse out the shell-only flags; pass the rest through ───────────────────
BACKGROUND=0
TAIL_TARGET=""
KILL_TARGET=""
PY_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --background)
            BACKGROUND=1; shift ;;
        --tail)
            TAIL_TARGET="$2"; shift 2 ;;
        --kill)
            KILL_TARGET="$2"; shift 2 ;;
        -h|--help)
            sed -n '4,30p' "$0"
            echo
            echo "─── Python script options (passed through to run_eval.py) ───"
            python3 "${SCRIPT_DIR}/run_eval.py" --help | sed -n '/^usage:/,$p' | tail -n +3
            exit 0 ;;
        *)
            PY_ARGS+=("$1"); shift ;;
    esac
done

# ── --tail / --kill modes: short-circuit ────────────────────────────────────
sidecar() {
    # given an OUTPUT path, return its sidecar log/pid path
    echo "${1}.${2}"
}

if [[ -n "${TAIL_TARGET}" ]]; then
    LOG="$(sidecar "${TAIL_TARGET}" log)"
    [[ -f "${LOG}" ]] || { echo "no log at ${LOG}" >&2; exit 1; }
    exec tail -f "${LOG}"
fi

if [[ -n "${KILL_TARGET}" ]]; then
    PIDF="$(sidecar "${KILL_TARGET}" pid)"
    [[ -f "${PIDF}" ]] || { echo "no pid file at ${PIDF}" >&2; exit 1; }
    PID="$(cat "${PIDF}")"
    if kill -0 "${PID}" 2>/dev/null; then
        kill "${PID}" && echo "killed PID ${PID}"
    else
        echo "PID ${PID} not running (stale pidfile)"
    fi
    rm -f "${PIDF}"
    exit 0
fi

# ── Extract --output (or --resume which implies --output) from PY_ARGS ──────
# so we know where to put sidecar files (.log / .pid).
OUTPUT=""
for ((i = 0; i < ${#PY_ARGS[@]}; i++)); do
    case "${PY_ARGS[$i]}" in
        --output|--resume)
            OUTPUT="${PY_ARGS[$((i+1))]}"
            break
            ;;
    esac
done

if [[ "${BACKGROUND}" = "1" && -z "${OUTPUT}" ]]; then
    # auto-name output so the .log/.pid sidecars are deterministic
    solver="solvers/baseline_solver_v3e.py"
    problems="third_party/equational-theories-lean-stage2/examples/problems/sample_200.json"
    for ((i = 0; i < ${#PY_ARGS[@]}; i++)); do
        [[ "${PY_ARGS[$i]}" == "--solver"   ]] && solver="${PY_ARGS[$((i+1))]}"
        [[ "${PY_ARGS[$i]}" == "--problems" ]] && problems="${PY_ARGS[$((i+1))]}"
    done
    solver_base="$(basename "${solver%.py}")"
    prob_base="$(basename "${problems}")"; prob_base="${prob_base%.*}"
    ts="$(date +%Y%m%d_%H%M%S)"
    OUTPUT="results/${solver_base}_${prob_base}_${ts}.json"
    mkdir -p "$(dirname "${OUTPUT}")"
    PY_ARGS+=(--output "${OUTPUT}")
fi

# ── Launch ─────────────────────────────────────────────────────────────────
if [[ "${BACKGROUND}" = "1" ]]; then
    LOG="$(sidecar "${OUTPUT}" log)"
    PIDF="$(sidecar "${OUTPUT}" pid)"
    nohup python3 -u "${SCRIPT_DIR}/run_eval.py" "${PY_ARGS[@]}" > "${LOG}" 2>&1 &
    PID=$!
    echo "${PID}" > "${PIDF}"
    cat <<EOF
[background] PID=${PID}
   log:  ${LOG}
   pid:  ${PIDF}
   out:  ${OUTPUT}

Tail with:    bash scripts/run_eval.sh --tail ${OUTPUT}
Kill with:    bash scripts/run_eval.sh --kill ${OUTPUT}
EOF
else
    exec python3 -u "${SCRIPT_DIR}/run_eval.py" "${PY_ARGS[@]}"
fi
