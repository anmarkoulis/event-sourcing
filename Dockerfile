# syntax=docker/dockerfile:experimental
ARG PYTHON_VERSION="3.13.3"

FROM python:${PYTHON_VERSION}-slim-bookworm AS base-envs

# python
ENV PYTHONUNBUFFERED=1 \
    # prevents python creating .pyc files
    PYTHONDONTWRITEBYTECODE=1 \
    \
    # pip
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    \
    # paths
    # this is where our requirements + virtual environment will live
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

# Create virtual environment
RUN python -m venv $VENV_PATH

# Install uv globally
COPY ./uv-requirements.txt /tmp/uv-requirements.txt
RUN pip install -r /tmp/uv-requirements.txt --no-cache-dir

WORKDIR $PYSETUP_PATH

# Activate the virtual environment by setting environment variables
# This is equivalent to 'source $VENV_PATH/bin/activate'
ENV PATH="$VENV_PATH/bin:$PATH" \
    VIRTUAL_ENV="$VENV_PATH"

# APT robustness configuration (disable HTTP pipelining, avoid caches, add retries)
RUN set -eux; \
    printf 'Acquire::http::Pipeline-Depth "0";\nAcquire::http::No-Cache "true";\nAcquire::Retries "5";\n' > /etc/apt/apt.conf.d/99fixbadproxy


FROM base-envs AS base

RUN  apt-get update \
#  psycopg2 dependencies
&& apt-get install -y libpq5=15.10-0+deb12u1 --no-install-recommends \
&& apt-get install -y libpq-dev=15.10-0+deb12u1 --no-install-recommends \

&& apt-get install -y libcurl4-openssl-dev=7.88.1-10+deb12u12 --no-install-recommends \
&& apt-get install -y libssl-dev=3.0.17-1~deb12u2 --no-install-recommends \

# cleaning up unused files
&& apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
&& rm -rf /var/lib/apt/lists/*

FROM base-envs AS builder

RUN apt-get update \
# dependencies for building Python packages
&& apt-get install -y build-essential=12.9 --no-install-recommends \
# psycopg2 dependencies
&& apt-get install -y libpq5=15.10-0+deb12u1 --no-install-recommends \
&& apt-get install -y libpq-dev=15.10-0+deb12u1 --no-install-recommends \

&& apt-get install -y libcurl4-openssl-dev=7.88.1-10+deb12u12 --no-install-recommends \
&& apt-get install -y libssl-dev=3.0.17-1~deb12u2 --no-install-recommends \

# cleaning up unused files
&& apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
&& rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock* ./

FROM builder AS builder-production

WORKDIR $PYSETUP_PATH
# Use bash with proper variable expansion
RUN --mount=type=cache,target=/root/.cache/uv \
    /bin/bash -c 'uv sync'

FROM builder AS builder-local

RUN apt-get update \
&& apt-get install -y git=1:2.39.5-0+deb12u2 --no-install-recommends \
# cleaning up unused files
&& apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
&& rm -rf /var/lib/apt/lists/*

WORKDIR $PYSETUP_PATH
# hadolint ignore=DL3042
# Use bash with proper variable expansion
RUN --mount=type=cache,target=/root/.cache/uv \
    /bin/bash -c 'uv sync --all-extras'

COPY .pre-commit-config.yaml .
RUN git init . \
    && git config --global --add safe.directory "$PYSETUP_PATH" \
    && pre-commit install --install-hooks

FROM base AS production-no-files

RUN addgroup --system fastapi \
    && adduser --system --ingroup fastapi fastapi

COPY --chown=fastapi:fastapi ./compose/entrypoint /entrypoint
COPY --chown=fastapi:fastapi ./compose/start-production /start
COPY --chown=fastapi:fastapi ./scripts/initialize /initialize
COPY --chown=fastapi:fastapi ./scripts/migrate /migrate

COPY --chown=fastapi:fastapi ./compose/start-celeryworker /start-celeryworker
COPY --chown=fastapi:fastapi ./compose/start-celerybeat /start-celerybeat


RUN sed -i 's/\r$//g' /entrypoint \
  && chmod +x /entrypoint \
  && sed -i 's/\r$//g' /start \
  && chmod +x /start \
  && sed -i 's/\r$//g' /start-celeryworker \
  && chmod +x /start-celeryworker \
  && sed -i 's/\r$//g' /start-celerybeat \
  && chmod +x /start-celerybeat \
  && sed -i 's/\r$//g' /migrate \
  && chmod +x /migrate \
  && sed -i 's/\r$//g' /initialize \
  && chmod +x /initialize


USER fastapi

WORKDIR /app

ENV PATH="/opt/venv/bin:$PATH"

FROM production-no-files AS production

COPY --chown=fastapi:fastapi  --from=builder-production  $PYSETUP_PATH $PYSETUP_PATH

COPY --chown=fastapi:fastapi /src /app/src

ENTRYPOINT ["/entrypoint"]

FROM production-no-files AS local

# ignore last user being root as we only run
# this image for local development
# hadolint ignore=DL3002
USER root

RUN  apt-get update \
# Install git in order to be able to run pre-commit inside the container
&& apt-get install -y git=1:2.39.5-0+deb12u2 --no-install-recommends \
 # Install wget in order to retrieve hadolint
&& apt-get install -y wget2=1.99.1-2.2 --no-install-recommends \
# Install hadolint
&& wget2 -q -O /bin/hadolint https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64 \
&& chmod +x /bin/hadolint \
# cleaning up unused files
&& apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
&& rm -rf /var/lib/apt/lists/*

WORKDIR /app

# copy in our built venv
COPY --from=builder-local $PYSETUP_PATH $PYSETUP_PATH

# COPY  --from=builder-local /opt/venv /opt/venv
RUN git init . \
 && git config --global --add safe.directory /app
COPY  --from=builder-local  $PYSETUP_PATH/.git/hooks /.git/hooks
COPY  --from=builder-local  /root/.cache/pre-commit /root/.cache/pre-commit

COPY  ./compose/start-local /start

RUN sed -i 's/\r$//g' /start \
  && chmod +x /start


ENTRYPOINT ["/entrypoint"]
