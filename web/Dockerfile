FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy project files (build context should be repo root; use: -f web/Dockerfile .)
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY web ./web

# Install package with web extras
# Use a pretend version so hatch-vcs/setuptools-scm doesn't require a VCS (.git) during Docker build
# TODO extract version from hatch?
RUN export SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 SETUPTOOLS_SCM_PRETEND_VERSION_FOR_CATLEG=0.0.0 && pip install --upgrade pip && pip install --no-cache-dir ".[web]"

# Start the FastAPI app
CMD ["sh", "-c", "uvicorn web.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
