ARG BASE_IMAGE=math-distill-stage2-official-judge:latest
FROM ${BASE_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/workspace/src
ENV JUDGE_REPO=/opt/equational-theories-lean-stage2
ENV OFFICIAL_STAGE2_JUDGE_REPO=/opt/equational-theories-lean-stage2
ENV LEAN_BIN=/root/.elan/bin/lean
ENV LAKE_BIN=/root/.elan/bin/lake
ENV JUDGE_V2_WORKERS=4
ENV JUDGE_V2_DEFAULT_TIMEOUT_SECONDS=120
ENV JUDGE_V2_TIMEOUT_CAP_SECONDS=180
ENV JUDGE_V2_TIMEOUT_GRACE_SECONDS=30
ENV JUDGE_V2_CACHE_PATH=/var/lib/judge_v2/cache.sqlite
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-pip \
    && python3 -m pip install --no-cache-dir --break-system-packages \
        "fastapi==0.115.0" \
        "uvicorn[standard]==0.30.6" \
        "pydantic==2.9.0" \
    && rm -rf /var/lib/apt/lists/*

COPY src/judge_v2/ /workspace/src/judge_v2/

VOLUME /var/lib/judge_v2
EXPOSE 9001

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -fsS http://localhost:9001/health || exit 1

CMD ["python3", "-m", "uvicorn", "judge_v2.worker.app:app", "--host", "0.0.0.0", "--port", "9001"]
