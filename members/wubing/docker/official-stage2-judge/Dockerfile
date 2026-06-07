FROM ubuntu:24.04

ARG LEAN_VERSION=v4.30.0-rc2
ARG OFFICIAL_STAGE2_REPO=https://github.com/SAIRcompetition/equational-theories-lean-stage2.git
ARG OFFICIAL_STAGE2_COMMIT=6805e2323018fbd8a85f41ca09fc33d74d5a02a5
ARG http_proxy
ARG https_proxy
ARG all_proxy
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG ALL_PROXY

ENV ELAN_HOME=/root/.elan
ENV PATH=/root/.elan/bin:${PATH}
ENV PYTHONPATH=/workspace/src
ENV OFFICIAL_STAGE2_JUDGE_REPO=/opt/equational-theories-lean-stage2

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        git \
        python3 \
        zstd \
    && rm -rf /var/lib/apt/lists/*

RUN curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf \
    | sh -s -- -y --default-toolchain "leanprover/lean4:${LEAN_VERSION}" \
    && lean --version \
    && lake --version

RUN git clone "${OFFICIAL_STAGE2_REPO}" "${OFFICIAL_STAGE2_JUDGE_REPO}" \
    && cd "${OFFICIAL_STAGE2_JUDGE_REPO}" \
    && git checkout --detach "${OFFICIAL_STAGE2_COMMIT}" \
    && lake update \
    && lake exe cache get \
    && lake build JudgeMagma.Magma JudgeDecide.DecideBang JudgeFinOp.MemoFinOp JudgeSupport.Inspect

WORKDIR /workspace

COPY src/math_distill_stage2 /workspace/src/math_distill_stage2
COPY scripts/lean_certificates/verify_official_stage2_batch_worker.py /workspace/scripts/lean_certificates/verify_official_stage2_batch_worker.py

LABEL org.opencontainers.image.source="https://github.com/SAIRcompetition/equational-theories-lean-stage2" \
      org.opencontainers.image.revision="${OFFICIAL_STAGE2_COMMIT}" \
      org.opencontainers.image.title="math-distill-stage2-official-judge"

CMD ["python3", "/workspace/scripts/lean_certificates/verify_official_stage2_batch_worker.py", "--help"]
