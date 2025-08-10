# Multi-stage build for SocialMapper React UI

# Dependencies stage - cache dependencies separately
FROM node:20-alpine AS deps

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install production dependencies only
RUN npm install --only=production --no-audit --no-fund && \
    npm cache clean --force

# Build stage
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install all dependencies including devDeps for build
RUN npm install --no-audit --no-fund && \
    npm cache clean --force

# Copy source code
COPY . .

# Build arguments
ARG VITE_API_URL=/api
ARG VITE_APP_TITLE="SocialMapper Demo"
ARG VITE_APP_VERSION=latest
ARG VITE_MAPBOX_TOKEN=""
ARG NODE_ENV=production

# Set environment variables for build
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_APP_TITLE=$VITE_APP_TITLE
ENV VITE_APP_VERSION=$VITE_APP_VERSION
ENV VITE_MAPBOX_TOKEN=$VITE_MAPBOX_TOKEN
ENV NODE_ENV=$NODE_ENV

# Run type checking first
RUN npm run typecheck

# Build the app with optimizations
RUN npm run build

# Generate bundle size report and check build output sizes
RUN npx vite-bundle-visualizer --output /tmp/stats.html
RUN ls -la dist/assets/js/ dist/assets/css/ && echo "Build completed successfully with optimized assets"

# Production stage
FROM nginx:1.25-alpine

# Install curl for health checks and create non-root user if not exists
RUN apk add --no-cache curl tini && \
    rm -rf /var/cache/apk/*

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Adjust main nginx.conf for non-root runtime
RUN sed -i 's/^user .*/# user disabled for non-root runtime;/' /etc/nginx/nginx.conf && \
    sed -i 's#^pid .*;#pid /tmp/nginx.pid;#' /etc/nginx/nginx.conf && \
    sed -i 's#^error_log .*;#error_log /tmp/error.log warn;#' /etc/nginx/nginx.conf

# Copy built app from build stage with proper ownership
COPY --from=build --chown=nginx:nginx /app/dist /usr/share/nginx/html

# Copy bundle stats for analysis (optional, can be removed in production)
COPY --from=build --chown=nginx:nginx /tmp/stats.html /usr/share/nginx/html/bundle-stats.html

# Create necessary directories and set permissions
RUN mkdir -p /var/cache/nginx /var/log/nginx /tmp/nginx && \
    chown -R nginx:nginx /var/cache/nginx /var/log/nginx /tmp/nginx /etc/nginx/conf.d/ /usr/share/nginx/html && \
    chmod -R 755 /usr/share/nginx/html

# Create entrypoint script for runtime environment injection
RUN printf '#!/bin/sh\n# Add runtime environment injection for client-side config\ncat > /usr/share/nginx/html/config.js << "EOF"\nwindow.__RUNTIME_CONFIG__ = {\n  API_URL: "${API_URL:-/api}",\n  APP_VERSION: "${APP_VERSION:-unknown}",\n  ENVIRONMENT: "${ENVIRONMENT:-production}"\n};\nEOF\nexec "$@"\n' > /docker-entrypoint.sh && \
    chmod +x /docker-entrypoint.sh

# Switch to non-root user
USER nginx

# Expose port
EXPOSE 8080

# Add labels for better container management
LABEL maintainer="SocialMapper Team" \
      version="latest" \
      description="SocialMapper React UI" \
      org.opencontainers.image.source="https://github.com/socialmapper/socialmapper-ui"

# Health check with better timeout settings
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Use tini for proper signal handling
ENTRYPOINT ["/sbin/tini", "--", "/docker-entrypoint.sh"]

# Start nginx
CMD ["nginx", "-g", "daemon off;"]