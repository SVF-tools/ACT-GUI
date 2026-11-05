# syntax=docker/dockerfile:1
# ACT-GUI workbench image: browser assets + FastAPI service + pinned ACT, one origin on port 8080.
# Build with scripts/docker_build.sh, which stages the pinned ACT commit as the "act" build context.

FROM node:22-bookworm-slim AS web
WORKDIR /src
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY tsconfig.json vite.config.ts ./
COPY visual_bench ./visual_bench
RUN npm run build

FROM python:3.12-slim-bookworm AS runtime
ARG TORCH_VERSION=2.11.0+cu128
ARG TORCHVISION_VERSION=0.26.0+cu128
ARG TORCH_INDEX=https://download.pytorch.org/whl/cu128
ARG GUROBIPY_VERSION=13.0.0
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
RUN pip install --index-url "$TORCH_INDEX" "torch==$TORCH_VERSION" "torchvision==$TORCHVISION_VERSION"
COPY requirements-runtime.txt /tmp/requirements-runtime.txt
RUN pip install -r /tmp/requirements-runtime.txt "gurobipy==$GUROBIPY_VERSION"

RUN useradd --create-home --uid 10001 actgui && mkdir -p /data && chown actgui /data
COPY --from=act --chown=actgui . /opt/act
WORKDIR /app
COPY fixtures ./fixtures
COPY engine_bridge ./engine_bridge
COPY visual_bench ./visual_bench
COPY --from=web /src/dist/web ./dist/web

ENV ACT_ROOT=/opt/act ACT_GUI_RECORDS=/data/records ACT_GUI_SECRETS=/data/secrets ACT_GUI_DEVICE=cpu
USER actgui
VOLUME /data
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/api/health', timeout=4)"
CMD ["python", "-m", "uvicorn", "visual_bench.server:app", "--host", "0.0.0.0", "--port", "8080"]
