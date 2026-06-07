# Judge service container (China-friendly mirrors).
# Build from the stage2/ directory so the COPY paths resolve:
#   docker build -f judge_service/Dockerfile -t judge-service:latest .
#
# Image is ~4 GB once mathlib oleans are cached. Most of that is the
# precompiled mathlib build pulled by `lake exe cache get` — that step is
# unavoidable, but layered so a code change in judge_service/ doesn't
# trigger a re-fetch.
#
# Mirrors used (override with --build-arg if needed):
#   APT_MIRROR   : Debian apt mirror (default: 阿里云)
#   PIP_INDEX_URL: Python pip index  (default: 清华)

FROM python:3.11-slim

ARG APT_MIRROR=mirrors.aliyun.com
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

# ── apt 换源 ──
RUN set -eux; \
    if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i "s|deb.debian.org|${APT_MIRROR}|g; s|security.debian.org|${APT_MIRROR}|g" \
            /etc/apt/sources.list.d/debian.sources; \
    fi; \
    if [ -f /etc/apt/sources.list ]; then \
        sed -i "s|deb.debian.org|${APT_MIRROR}|g; s|security.debian.org|${APT_MIRROR}|g" \
            /etc/apt/sources.list; \
    fi

# Required: curl (elan installer + healthcheck), git (lake fetches mathlib),
# ca-certificates (HTTPS). build-essential is needed because some elan/lake
# operations call gcc/ld at first build.
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates git build-essential \
    && rm -rf /var/lib/apt/lists/*

# ── pip 换源 ──
RUN pip config set global.index-url "${PIP_INDEX_URL}" \
    && pip install --no-cache-dir --upgrade pip

# Quiet `lake` complaints about repo ownership inside the container.
RUN git config --global --add safe.directory '*'

# Install elan (Lean version manager) as root. Toolchain installed in the
# next layer once we know which version this repo pins.
ENV PATH=/root/.elan/bin:$PATH \
    ELAN_HOME=/root/.elan
RUN curl -sSfL https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh \
        -o /tmp/elan-init.sh \
    && sh /tmp/elan-init.sh -y --default-toolchain none --no-modify-path \
    && rm /tmp/elan-init.sh

WORKDIR /app/judge_repo

# ── Layer A: pin lean toolchain (cached unless lean-toolchain changes) ──
COPY third_party/equational-theories-lean-stage2/lean-toolchain ./
RUN TC="$(tr -d '[:space:]' < lean-toolchain)" \
    && elan toolchain install "$TC" \
    && elan default "$TC" \
    && lean --version && lake --version

# ── Layer B: fetch mathlib + prebuilt oleans (cached unless lakefile / manifest change) ──
# This is the slow + heavy layer (~3 GB download). Keep it isolated.
COPY third_party/equational-theories-lean-stage2/lakefile.lean \
     third_party/equational-theories-lean-stage2/lake-manifest.json \
     ./
RUN lake update \
    && lake exe cache get

# ── Layer C: build judge-owned lean modules ──
COPY third_party/equational-theories-lean-stage2/judge ./judge
RUN lake build \
        JudgeMagma.Magma \
        JudgeDecide.DecideBang \
        JudgeFinOp.MemoFinOp \
        JudgeSupport.Inspect

# ── Layer D: python service ──
WORKDIR /app
RUN pip install --no-cache-dir \
        "fastapi==0.115.0" \
        "uvicorn[standard]==0.30.6" \
        "pydantic==2.9.0"

COPY judge_service/ ./judge_service/

ENV JUDGE_REPO=/app/judge_repo \
    LEAN_BIN=/root/.elan/bin/lean \
    LAKE_BIN=/root/.elan/bin/lake \
    JUDGE_CACHE_PATH=/var/lib/judge/cache.sqlite \
    JUDGE_WORKERS=4 \
    JUDGE_DEFAULT_TIMEOUT_SECONDS=120 \
    JUDGE_TIMEOUT_CAP_SECONDS=180 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

VOLUME /var/lib/judge
EXPOSE 9000

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -fsS http://localhost:9000/health || exit 1

CMD ["uvicorn", "judge_service.server:app", "--host", "0.0.0.0", "--port", "9000"]
