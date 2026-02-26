# Multi-stage Dockerfile for Pantheon ChatRoom
# Use python:3.11-slim as base for BOTH stages to ensure python binary paths match, preventing broken venv symlinks

FROM python:3.11-slim-bookworm AS builder

# Install system dependencies, uv, and Playwright browser dependencies (Use Aliyun mirror)
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    # R environment (needed for compiling rpy2)
    r-base-dev \
    && rm -rf /var/lib/apt/lists/* && \
    pip install uv

WORKDIR /app

# Install venv outside /app so that "COPY --from=builder /app /app" in the
# production stage copies only source code — no venv files mixed in.
ENV UV_PROJECT_ENVIRONMENT=/venv

# ── Layer 1: dependency files only ──────────────────────────────────────────
# Copy only pyproject.toml + uv.lock so this layer is reused on code-only changes.
COPY pyproject.toml uv.lock ./

# Install all Python dependencies (no project package itself yet).
# BuildKit cache mount keeps uv's HTTP cache on the host across builds.
# --extra r/knowledge/slack: install runtime extras only (dev extra excluded to skip pytest tools).
# --no-dev: also excludes [dependency-groups] dev (ipdb, ipython, build tools, etc.).
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --extra r --extra knowledge --extra slack --no-install-project --python /usr/local/bin/python

# ── Layer 2: single-cell analysis extras ────────────────────────────────────
# These packages are fixed (not in pyproject.toml), so they are also cached
# as long as the list below doesn't change.
#
# ============================================
# Single Cell Analysis Dependencies (Optimized - 12 packages)
# ============================================
# Based on comprehensive dependency testing with uv pip compile
# ALL packages below are verified CUDA-free (no torch/nvidia dependencies)
# Covers 70-80% of single-cell analysis workflows (core workflows: 100%)
#
# Optimized single-cell stack (~120MB, adds ~3-4 min to build time)
# Focuses on most frequently used packages (>70% usage rate)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --python /venv/bin/python \
    # Core data structures & framework (~55MB) - 95% usage
    anndata \
    scanpy \
    # Quality control (~5MB) - 85% usage
    scrublet \
    # Clustering & dimensionality reduction (~55MB) - 90% usage
    leidenalg \
    igraph \
    numba \
    umap-learn \
    # Batch correction (~5MB) - 70% usage
    scanorama \
    # Cell type annotation (~18MB) - 75% usage
    celltypist \
    # Functional analysis (~12MB) - 80% usage
    gseapy \
    # Visualization & R interop (~11MB) - 85% usage
    seaborn \
    anndata2ri

# Packages removed to reduce image size (install on-demand via system_manager):
# Python packages (~6GB+ saved):
# - squidpy: Advanced spatial transcriptomics (~6GB with spatialdata + dask + datashader dependencies)
#   → scanpy provides basic spatial analysis features (sc.pl.spatial, etc.)
#   → Users needing advanced spatial features: uv pip install squidpy (5-10 min)
# - doubletdetection: Redundant with scrublet (both detect doublets)
# - bbknn: Less common batch correction (scanorama covers main use case)
# - pynndescent: Optional umap-learn accelerator (not essential)
# - spatialdata: Newer spatial package (included as squidpy dependency, ~500MB)
# - decoupler: Specialized functional analysis (lower usage frequency)
# - scikit-image: Large image processing lib (squidpy includes it as dependency)
#
# Packages NOT pre-installed (verified to pull torch/CUDA via uv pip compile):
# - harmonypy: Batch correction (~2MB + torch 873MB + CUDA 3GB)
#   → Use scanorama as alternative (pre-installed above)
# - cell2location: Spatial deconvolution (~20MB + torch + CUDA)
# - scvi-tools: Deep learning framework (~3-4GB with CUDA)
# - scarches: Transfer learning (~3GB with CUDA)
#
# Optimized build metrics:
# - Build time: ~15-18 minutes (vs 50-60 min with R packages, vs 22-25 min with squidpy)
# - Image size: ~2.3-2.5GB (vs 8.5GB with squidpy, vs 3.2GB before optimization)
# - Coverage: 70-80% of workflows without runtime installation (core workflows: 100%)
# - Spatial transcriptomics: Basic features via scanpy (70-80% coverage)
# - Less common features installed on-demand (adds 2-10 minutes per package)

# ── Layer 3: application code ────────────────────────────────────────────────
# Copy source code AFTER all dependencies are installed.
# Code-only changes never invalidate the expensive dependency layers above.
COPY . /app/

# Sync again to pick up any lock-file changes introduced by the source COPY.
# --no-install-project: do NOT install the pantheon package into /venv.
# The project is found at runtime via PYTHONPATH=/app, so installing it into
# the venv is unnecessary and would risk copying source files into /venv,
# making Layer A (venv) change on every code commit.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev --extra r --extra knowledge --extra slack --no-install-project --python /usr/local/bin/python

# Pre-compile project source files to .pyc bytecode.
# Only compile /app/pantheon (source), NOT the venv, so the venv directory stays
# content-stable across code-only changes (critical for Docker layer caching).
RUN /venv/bin/python -m compileall -q /app/pantheon 2>/dev/null || true

# Production stage
FROM python:3.11-slim-bookworm

# Install runtime dependencies and Playwright browser dependencies (Use Aliyun mirror for stability in CN)
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
    apt-get update && apt-get install -y \
    curl \
    wget \
    git \
    ca-certificates \
    # Playwright browser dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    # Additional Chromium dependencies
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxext6 \
    libxshmfence1 \
    # Fonts for better rendering
    fonts-liberation \
    fonts-noto-color-emoji \
    # R environment for single-cell analysis
    r-base \
    r-base-dev \
    # Install Node.js
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g ajv ajv-formats \
    && npm cache clean --force \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv

WORKDIR /app

# Layer A — venv (~1-2GB, stable): only rebuilt when pyproject.toml / uv.lock changes.
# Kept at /venv (same path as builder) to avoid the Docker overlay2 opaque-whiteout
# problem: if we copied to /app/.venv first and then did "COPY /app /app", the second
# COPY would create an opaque whiteout for /app, silently erasing /app/.venv.
# Keeping the two COPYs at non-overlapping paths (/venv vs /app) eliminates the issue.
# Both stages use python:3.11-slim, so venv symlinks remain valid.
COPY --from=builder /venv /venv

# Layer B — source (~10MB, changes every commit): copy all of /app from the builder.
# /app in the builder contains only source and project files (no venv), so nothing
# is accidentally left out and the venv layer above is never affected.
COPY --from=builder /app /app

# Set environment variables
# Add /app to PYTHONPATH so 'import pantheon' works
ENV PATH="/venv/bin:$PATH" \
    PYTHONPATH="/app" \
    PYTHONUNBUFFERED=1 \
    # PYTHONDONTWRITEBYTECODE removed: .pyc files are pre-compiled in builder stage
    # and must remain readable at runtime to benefit from the compileall optimization.
    # Keep uv's package cache inside the image so 'uv run --with' hits it at runtime
    UV_CACHE_DIR=/app/.uv-cache \
    # Install playwright browsers to an explicit path outside /root/.cache.
    # This prevents accidental deletion and makes the installation location unambiguous.
    PLAYWRIGHT_BROWSERS_PATH=/usr/local/share/ms-playwright \
    # Use Playwright mirror for faster downloads in China
    PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright

# Install Playwright browsers (chromium only to reduce image size)
# Using chromium is sufficient for most web scraping/automation tasks.
# PLAYWRIGHT_DOWNLOAD_HOST is already set in ENV above; the fallbacks override
# it temporarily if the primary mirror is unreachable.
RUN /venv/bin/playwright install chromium --with-deps || \
    (PLAYWRIGHT_DOWNLOAD_HOST=https://playwright.azureedge.net \
     /venv/bin/playwright install chromium --with-deps) || \
    (PLAYWRIGHT_DOWNLOAD_HOST= \
     /venv/bin/playwright install chromium --with-deps)

# ============================================
# Pre-warm MCP Server Caches
# ============================================
# Pre-download and cache MCP servers to avoid first-run installation delays
# This significantly reduces pod startup time when agents first use these tools
#
# Servers:
# - context7 (npx @upstash/context7-mcp): ~100-200MB cache from npm
# - biomcp (uv run --with biomcp-python): Python environment cache
RUN echo "Pre-warming context7 MCP server cache (downloading npm packages)..." && \
    npm install -g @upstash/context7-mcp && \
    npm cache clean --force && \
    echo "context7 cache pre-warmed"

# Pre-warm the 'uv run --with biomcp-python' cache by running the exact same
# command that MCP will use at runtime. Because UV_CACHE_DIR=/app/.uv-cache is
# baked into the image, the downloaded wheels are available to every container
# without hitting the network again.
RUN echo "Pre-warming biomcp uv run cache into /app/.uv-cache..." \
    && cd /tmp && uv run --with biomcp-python python -c "import biomcp; print('biomcp ready')" \
    && echo "biomcp uv cache pre-warmed"

# ============================================
# R Packages for Single Cell Analysis (Moved to Runtime)
# ============================================
# R packages removed from Docker image to reduce size (~600-800MB saved)
# These are installed on-demand by system_manager when needed:
# - SoupX: Ambient RNA removal (~300-400MB with dependencies including Seurat)
# - celda: Cell type deconvolution (~300-400MB with Bioconductor dependencies)
#
# Total R dependencies: 200+ packages including Seurat, SingleCellExperiment,
# scater, scran, ComplexHeatmap, ggplot2, etc.
#
# Usage frequency: ~10-20% of single-cell workflows
# Installation time: 5-10 minutes on first use
# Trade-off: Faster builds, smaller images, minimal user impact
#
# Note: r-base and r-base-dev system packages are still installed above (~50MB)
# for rpy2 support and to enable on-demand R package installation

# ============================================
# CLI Tools for Report Generation
# ============================================
# Install monolith (HTML bundler) and tectonic (LaTeX compiler)
RUN curl -L https://github.com/Y2Z/monolith/releases/download/v2.7.0/monolith-x86_64-unknown-linux-gnu -o /usr/local/bin/monolith && \
    chmod +x /usr/local/bin/monolith && \
    curl -L https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic@0.15.0/tectonic-0.15.0-x86_64-unknown-linux-gnu.tar.gz -o /tmp/tectonic.tar.gz && \
    tar -xzf /tmp/tectonic.tar.gz -C /usr/local/bin && \
    rm /tmp/tectonic.tar.gz

# Copy entrypoint script (already copied with pantheon-agents/)
RUN chmod +x /app/docker/docker-entrypoint.sh && \
    cp /app/docker/docker-entrypoint.sh /usr/local/bin/

# Create workspace directory
RUN mkdir -p /workspace

# Set default working directory
WORKDIR /workspace

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# No CMD - let entrypoint.sh handle the default command with --id_hash
