# Frontend Dockerfile
FROM node:24-slim AS base

ENV PNPM_HOME="/pnpm" \
    PATH="/pnpm:${PATH}"

WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy package files
COPY frontend/package.json frontend/pnpm-lock.yaml* ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# Copy application code
COPY frontend/ ./

# Build application
RUN pnpm run build

# Create nginx config for serving static files
FROM nginx:alpine AS runner

COPY --from=base /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]