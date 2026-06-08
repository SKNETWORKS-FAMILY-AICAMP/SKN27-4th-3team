FROM node:22-slim AS frontend-build

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend ./
RUN npm run build

FROM caddy:2.8-alpine

COPY ops/docker/Caddyfile.production /etc/caddy/Caddyfile
COPY --from=frontend-build /app/frontend/dist /srv/frontend
