FROM ubuntu:24.04

ARG LEAN_VERSION=v4.29.1
ARG http_proxy
ARG https_proxy
ARG all_proxy
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG ALL_PROXY

ENV ELAN_HOME=/root/.elan
ENV PATH=/root/.elan/bin:${PATH}

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        git \
        zstd \
    && rm -rf /var/lib/apt/lists/*

RUN curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf \
    | sh -s -- -y --default-toolchain "leanprover/lean4:${LEAN_VERSION}" \
    && lean --version
RUN lake --version

WORKDIR /workspace

CMD ["bash"]
