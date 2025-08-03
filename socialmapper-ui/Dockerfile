# Multi-stage build for optimal size and security
# Stage 1: Build stage
FROM node:18-alpine as builder

# Install build dependencies
RUN apk add --no-cache python3 make g++

# Set working directory
WORKDIR /app

# Copy package files for better layer caching
COPY package*.json ./
COPY tsconfig*.json ./

# Install dependencies with exact versions
RUN npm ci && \
    npm cache clean --force

# Copy source code
COPY . .

# Set build-time environment variables
ARG VITE_API_URL=http://localhost:8000
ARG VITE_APP_TITLE="SocialMapper"
ARG VITE_APP_VERSION="1.0.0"

# Build the application with production optimizations
RUN npm run build

# Stage 2: Production stage with nginx
FROM nginx:alpine

# Install runtime dependencies
RUN apk add --no-cache curl

# Remove default nginx config
RUN rm -rf /etc/nginx/conf.d/*

# Create non-root user for nginx
RUN adduser -D -H -u 1000 -s /sbin/nologin nginx-user

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create nginx cache and pid directories
RUN mkdir -p /var/cache/nginx /var/run/nginx && \
    chown -R nginx-user:nginx-user /usr/share/nginx/html /var/cache/nginx /var/run/nginx /var/log/nginx

# Add security headers configuration
RUN echo 'add_header X-Frame-Options "SAMEORIGIN" always;' >> /etc/nginx/conf.d/security.conf && \
    echo 'add_header X-Content-Type-Options "nosniff" always;' >> /etc/nginx/conf.d/security.conf && \
    echo 'add_header X-XSS-Protection "1; mode=block" always;' >> /etc/nginx/conf.d/security.conf && \
    echo 'add_header Referrer-Policy "strict-origin-when-cross-origin" always;' >> /etc/nginx/conf.d/security.conf && \
    echo 'add_header Content-Security-Policy "default-src '\''self'\''; script-src '\''self'\'' '\''unsafe-inline'\'' '\''unsafe-eval'\''; style-src '\''self'\'' '\''unsafe-inline'\''; img-src '\''self'\'' data: https:; font-src '\''self'\''; connect-src '\''self'\'' http://localhost:8000;" always;' >> /etc/nginx/conf.d/security.conf

# Use non-root user
USER nginx-user

# Expose port
EXPOSE 8080

# Health check with curl for better reliability
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Start nginx in foreground
CMD ["nginx", "-g", "daemon off;"]