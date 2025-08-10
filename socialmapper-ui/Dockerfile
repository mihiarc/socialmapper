# Multi-stage build for SocialMapper React UI

# Build stage
FROM node:20-alpine as build

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies (include devDeps for build tools like TypeScript and Vite)
RUN npm install --no-audit --no-fund && npm cache clean --force

# Copy source code
COPY . .

# Build arguments
ARG VITE_API_URL
ARG VITE_APP_TITLE
ARG VITE_APP_VERSION
ARG VITE_MAPBOX_TOKEN

# Set environment variables for build
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_APP_TITLE=$VITE_APP_TITLE
ENV VITE_APP_VERSION=$VITE_APP_VERSION
ENV VITE_MAPBOX_TOKEN=$VITE_MAPBOX_TOKEN

# Build the app (skip TypeScript typecheck)
RUN npx vite build

# Production stage
FROM nginx:1.25-alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Adjust main nginx.conf for non-root runtime
# - Comment out 'user' directive to silence warnings
# - Set pid to a writable location
RUN sed -i 's/^user .*/# user disabled for non-root runtime;/' /etc/nginx/nginx.conf \
    && sed -i 's#^pid .*;#pid /tmp/nginx.pid;#' /etc/nginx/nginx.conf

# Copy built app from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Ensure proper permissions on nginx paths (user already exists in base image)
RUN chown -R nginx:nginx /var/cache/nginx /var/log/nginx /etc/nginx/conf.d/ /usr/share/nginx/html

# Switch to non-root user
USER nginx

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]