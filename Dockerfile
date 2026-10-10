# Stage 1: Build
FROM python:3.11-slim AS builder

# Install system dependencies (keine Netzwerk‑abhängigkeiten)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python‑Abhängigkeiten
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Umbenennen, damit keine unnötigen Pakete geladen werden
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy nur die notwendigen Dateien aus der Build‑Stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY app /app/app

# Expose port
EXPOSE 5000

# Default command
CMD ["python", "app/main.py"]
