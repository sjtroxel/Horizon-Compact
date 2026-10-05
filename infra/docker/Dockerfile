# Phase 1 §11. The index digest below carries linux/arm64 (Fargate runs ARM); checked 2026-10-05, python 3.13.16.
FROM python:3.13-slim@sha256:3dd7cc108ec1493442514f5c2a871af6af0ec31d768ff6e378a93340c3b3db5f
COPY --from=ghcr.io/astral-sh/uv:0.12.0 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project
COPY src ./src
COPY experiment ./experiment
RUN uv sync --locked --no-dev
ARG GIT_SHA
ENV PATH="/app/.venv/bin:$PATH" HC_EXPERIMENT_DIR=/app/experiment HC_GIT_SHA=$GIT_SHA
RUN useradd --uid 10001 --no-create-home hc
USER 10001
ENTRYPOINT ["hc"]
