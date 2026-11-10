# syntax=docker/dockerfile:1
# ACT-GUI website: VitePress build served by nginx. Build context is the repository root:
#   docker compose -f compose.site.yaml up -d --build
FROM node:22-bookworm-slim AS build
WORKDIR /repo
COPY site/package.json site/package-lock.json site/
RUN cd site && npm ci --no-audit --no-fund
COPY README.md AGENTS.md fuzzingGuide.gif ./
COPY docs docs
COPY visual_bench visual_bench
COPY engine_bridge engine_bridge
COPY site site
RUN cd site && npm run build

FROM nginx:1.27-alpine
COPY site/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /repo/site/.vitepress/dist /usr/share/nginx/html
