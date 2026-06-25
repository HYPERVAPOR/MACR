# MACR reproducible experiment environment
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

WORKDIR /app

# Copy project metadata and lockfile first for better layer caching
COPY pyproject.toml uv.lock README.md ./

# Install dependencies (without the project itself)
RUN uv sync --frozen --no-install-project

# Copy source and experiment scripts
COPY src/ ./src/
COPY experiments/ ./experiments/
COPY tests/ ./tests/
COPY docs/ ./docs/

# Install the project
RUN uv sync --frozen

ENV PYTHONPATH=/app/src:/app
ENV MACR_TRACE_STORE=jsonl
ENV MACR_TRACE_DIR=/app/outputs/traces

# Default to an interactive shell; experiments are run explicitly
CMD ["bash"]
