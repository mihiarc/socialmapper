# Performance Testing Quick Start Guide

Get up and running with SocialMapper performance testing in minutes.

## Prerequisites

- Node.js 18+ (for Lighthouse CI)
- Docker and Docker Compose (for monitoring)
- k6 installed locally (optional, for local testing)

## 1. Quick Setup

### Install Dependencies

```bash
# Install k6 (macOS)
brew install k6

# Install k6 (Ubuntu/Debian)
curl -s https://api.github.com/repos/grafana/k6/releases/latest | \
jq -r '.assets[] | select(.name | contains("linux-amd64.tar.gz")) | .browser_download_url' | \
xargs -I {} curl -L {} | tar -xzC /usr/local/bin --strip-components=1 k6-*/k6

# Install Lighthouse CI
npm install -g @lhci/cli
```

### Environment Setup

```bash
export TEST_ENV=staging
export LOAD_PROFILE=load
```

## 2. Run Performance Tests

### Option A: Use the Automation Script (Recommended)

```bash
# Make script executable
chmod +x performance/scripts/run-performance-tests.sh

# Run all tests with default settings
./performance/scripts/run-performance-tests.sh

# Run with custom options
./performance/scripts/run-performance-tests.sh --env production --profile stress --parallel
```

### Option B: Run Tests Individually

#### k6 Load Tests
```bash
# Health endpoints
k6 run performance/k6/tests/health-endpoints.js

# Metadata endpoints  
k6 run performance/k6/tests/metadata-endpoints.js

# Comprehensive workflow
k6 run performance/k6/tests/comprehensive-api.js
```

#### Lighthouse CI Tests
```bash
cd socialmapper-ui

# Build the application
npm run build

# Run desktop tests
lhci autorun --config=../performance/lighthouse/lighthouserc.json

# Run mobile tests
lhci autorun --config=../performance/lighthouse/mobile-config.json
```

## 3. Start Monitoring Stack

```bash
cd performance/monitoring

# Start all monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

# View service status
docker-compose -f docker-compose.monitoring.yml ps
```

### Access Dashboards

- **Grafana Dashboard**: http://localhost:3001 (admin/admin123)
- **Prometheus Metrics**: http://localhost:9090
- **AlertManager**: http://localhost:9093

## 4. GitHub Actions Integration

Performance tests run automatically after deployments. To trigger manually:

```bash
# Using GitHub CLI
gh workflow run performance-testing.yml \
  --field environment=staging \
  --field load_profile=load \
  --field run_k6=true \
  --field run_lighthouse=true
```

Or use the GitHub web interface:
1. Go to Actions tab
2. Select "Performance Testing" workflow  
3. Click "Run workflow"
4. Configure options and run

## 5. Interpreting Results

### k6 Results
- **Response Time**: p95 should be under thresholds (see config)
- **Error Rate**: Should be < 1% for most endpoints
- **Throughput**: Should meet minimum RPS requirements

### Lighthouse Results  
- **Performance Score**: Target ≥ 80 (desktop), ≥ 75 (mobile)
- **Core Web Vitals**: LCP < 2.5s, FID < 100ms, CLS < 0.1
- **Resource Budgets**: Check bundle size limits

### Monitoring Alerts
- Green: All metrics within thresholds
- Yellow: Warning thresholds exceeded
- Red: Critical thresholds exceeded, immediate attention needed

## 6. Common Commands

```bash
# Run smoke test (quick verification)
k6 run --env LOAD_PROFILE=smoke performance/k6/tests/health-endpoints.js

# Run stress test
k6 run --env LOAD_PROFILE=stress performance/k6/tests/comprehensive-api.js

# Check monitoring stack
docker-compose -f performance/monitoring/docker-compose.monitoring.yml logs -f grafana

# Clean up monitoring
docker-compose -f performance/monitoring/docker-compose.monitoring.yml down -v
```

## Need Help?

- **Full Documentation**: See `/performance/docs/PERFORMANCE_TESTING_GUIDE.md`
- **Configuration**: Check `/performance/config/` for thresholds and budgets
- **Troubleshooting**: Common issues and solutions in the full guide
- **Team Support**: Contact the development team for specific questions

## Next Steps

1. **Customize Thresholds**: Adjust performance budgets in config files
2. **Add Custom Tests**: Create test scenarios for your specific use cases  
3. **Set Up Alerts**: Configure Slack/email notifications for your team
4. **Regular Audits**: Schedule periodic performance reviews