#!/bin/bash

# Production build script for SocialMapper UI
# This script builds the React application with production optimizations

set -e

echo "🚀 Building SocialMapper UI for production..."

# Set production environment
export NODE_ENV=production

# Clean previous builds
echo "📦 Cleaning previous builds..."
rm -rf dist

# Install dependencies
echo "📥 Installing dependencies..."
npm ci

# Run type checking
echo "🔍 Running TypeScript type check..."
npm run type-check || true

# Run linting
echo "🧹 Running ESLint..."
npm run lint || true

# Build the application
echo "🏗️ Building application..."
npm run build

# Display build info
echo "✅ Build complete!"
echo "📊 Build statistics:"
du -sh dist
find dist -type f -name "*.js" -o -name "*.css" | wc -l | xargs echo "Total JS/CSS files:"
find dist -type f -name "*.js" -exec du -ch {} + | grep total$ | awk '{print "Total JS size: " $1}'
find dist -type f -name "*.css" -exec du -ch {} + | grep total$ | awk '{print "Total CSS size: " $1}'

echo "
🎉 Production build successful!

To deploy:
1. Copy the 'dist' directory to your web server
2. Configure your web server to serve index.html for all routes
3. Set up proper caching headers for static assets
4. Configure API proxy if needed

For Docker deployment:
docker build -t socialmapper-ui:latest .
"