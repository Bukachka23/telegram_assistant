FROM python:3.12-slim AS base

WORKDIR /app

# Install build deps (needed for some wheels on ARM64/Pi)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libffi-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy project files and install
COPY pyproject.toml README.md ./
COPY src/ src/

RUN pip install --no-cache-dir .

# Runtime stage — smaller image
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages from build stage
COPY --from=base /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=base /usr/local/bin /usr/local/bin

# Copy source (needed for python -m bot.main)
COPY src/ src/

# Add src to PYTHONPATH so `bot` package is importable
ENV PYTHONPATH=/app/src

# Volumes for config, secrets, vault, and Telethon session
VOLUME ["/app/data"]

CMD ["python", "-m", "bot.main"]
