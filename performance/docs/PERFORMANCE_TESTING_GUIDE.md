# SocialMapper Performance Testing Guide

This comprehensive guide covers the performance testing infrastructure for the SocialMapper project, including k6 load testing, Lighthouse CI frontend auditing, and monitoring setup.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [k6 Load Testing](#k6-load-testing)
4. [Lighthouse CI Frontend Testing](#lighthouse-ci-frontend-testing)
5. [Performance Monitoring](#performance-monitoring)
6. [CI/CD Integration](#cicd-integration)
7. [Performance Budgets](#performance-budgets)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

## Overview

The SocialMapper performance testing infrastructure provides:

- **Automated Load Testing**: k6-based API endpoint testing with various load profiles
- **Frontend Performance Auditing**: Lighthouse CI for Core Web Vitals and performance metrics
- **Continuous Monitoring**: Prometheus + Grafana stack for real-time performance tracking
- **Regression Detection**: Automated alerts when performance degrades beyond thresholds
- **CI/CD Integration**: Performance tests run automatically after deployments

### Key Metrics Tracked

#### Backend Performance
- API response times (p95, p99, average)
- Request throughput (RPS)
- Error rates by endpoint
- Concurrent user handling

#### Frontend Performance  
- Core Web Vitals (LCP, FID, CLS)
- Lighthouse performance scores
- Page load times
- Bundle sizes and resource optimization

#### Infrastructure Performance
- CPU, memory, and disk usage
- Database performance metrics
- Cache hit rates
- Network latency

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GitHub        │    │   k6 Load       │    │   Lighthouse    │
│   Actions       │───▶│   Testing       │    │   CI Testing    │
│   Workflow      │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       ▼
         │              ┌─────────────────┐    ┌─────────────────┐
         │              │   Prometheus    │    │   Performance   │
         └─────────────▶│   Metrics       │◀───│   Results       │
                        │   Collection    │    │   Storage       │
                        └─────────────────┘    └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │   Grafana       │
                        │   Dashboard     │
                        │   & Alerting    │
                        └─────────────────┘
```

## k6 Load Testing

### Test Structure

The k6 tests are organized in `/performance/k6/tests/`:

- `health-endpoints.js` - Tests health check endpoints
- `metadata-endpoints.js` - Tests census variables, POI types, and location search
- `comprehensive-api.js` - Full workflow simulation across all endpoints

### Load Profiles

#### Smoke Test
```bash
k6 run --env LOAD_PROFILE=smoke performance/k6/tests/health-endpoints.js
```
- **VUs**: 1
- **Duration**: 30s
- **Purpose**: Quick functionality verification

#### Load Test (Default)
```bash
k6 run --env LOAD_PROFILE=load performance/k6/tests/comprehensive-api.js
```
- **VUs**: 10-50 (ramped)
- **Duration**: 9 minutes
- **Purpose**: Normal expected load simulation

#### Stress Test
```bash
k6 run --env LOAD_PROFILE=stress performance/k6/tests/comprehensive-api.js
```
- **VUs**: 50-150 (ramped)
- **Duration**: 16 minutes  
- **Purpose**: High load testing beyond normal capacity

#### Spike Test
```bash
k6 run --env LOAD_PROFILE=spike performance/k6/tests/comprehensive-api.js
```
- **VUs**: 10-200 (sudden spike)
- **Duration**: 2.5 minutes
- **Purpose**: Sudden traffic spike simulation

#### Soak Test
```bash
k6 run --env LOAD_PROFILE=soak performance/k6/tests/comprehensive-api.js
```
- **VUs**: 30 (sustained)
- **Duration**: 34 minutes
- **Purpose**: Extended testing for memory leaks and stability

### Running k6 Tests Locally

1. **Install k6**:
   ```bash
   # macOS
   brew install k6
   
   # Ubuntu/Debian
   sudo gpg -k
   sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
   echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
   sudo apt-get update
   sudo apt-get install k6
   ```

2. **Set Environment Variables**:
   ```bash
   export TEST_ENV=staging  # or production
   export LOAD_PROFILE=load
   ```

3. **Run Tests**:
   ```bash
   # Single test
   k6 run performance/k6/tests/health-endpoints.js
   
   # All tests with script
   chmod +x performance/scripts/run-performance-tests.sh
   ./performance/scripts/run-performance-tests.sh --env staging --profile load
   ```

### Custom Test Configuration

Create custom test configurations by modifying `/performance/k6/config/thresholds.js`:

```javascript
export const customThresholds = {
  http_req_duration: ['p(95)<300'], // 95% under 300ms
  http_req_failed: ['rate<0.005'],   // Error rate under 0.5%
  http_reqs: ['rate>150'],           // Minimum 150 RPS
};
```

## Lighthouse CI Frontend Testing

### Configuration Files

- **Desktop**: `/performance/lighthouse/lighthouserc.json`
- **Mobile**: `/performance/lighthouse/mobile-config.json` 
- **Budgets**: `/performance/lighthouse/budget.json`

### Running Lighthouse CI Locally

1. **Install Lighthouse CI**:
   ```bash
   npm install -g @lhci/cli
   ```

2. **Build Frontend**:
   ```bash
   cd socialmapper-ui
   npm run build
   ```

3. **Run Lighthouse Tests**:
   ```bash
   # Desktop tests
   lhci autorun --config=performance/lighthouse/lighthouserc.json
   
   # Mobile tests  
   lhci autorun --config=performance/lighthouse/mobile-config.json
   ```

### Performance Budgets

The Lighthouse CI configuration enforces performance budgets:

#### Desktop Budgets
- **Performance Score**: ≥ 80
- **First Contentful Paint**: ≤ 2.0s
- **Largest Contentful Paint**: ≤ 2.5s
- **Cumulative Layout Shift**: ≤ 0.1

#### Mobile Budgets (More Lenient)
- **Performance Score**: ≥ 75
- **First Contentful Paint**: ≤ 3.0s
- **Largest Contentful Paint**: ≤ 4.0s
- **Cumulative Layout Shift**: ≤ 0.1

### Resource Budgets

- **JavaScript**: ≤ 500KB
- **CSS**: ≤ 100KB
- **Images**: ≤ 2MB
- **Total**: ≤ 4MB

## Performance Monitoring

### Monitoring Stack Setup

1. **Start Monitoring Stack**:
   ```bash
   cd performance/monitoring
   docker-compose -f docker-compose.monitoring.yml up -d
   ```

2. **Access Services**:
   - **Grafana**: http://localhost:3001 (admin/admin123)
   - **Prometheus**: http://localhost:9090
   - **AlertManager**: http://localhost:9093

### Grafana Dashboard

The main performance dashboard includes:

- API response time trends
- Error rate monitoring
- Lighthouse score tracking
- Core Web Vitals visualization
- System resource utilization
- k6 test result trends

### Setting Up Alerts

1. **Configure Slack Webhook** (optional):
   ```bash
   export SLACK_WEBHOOK_URL="your-slack-webhook-url"
   ```

2. **Configure Email Alerts**:
   ```bash
   export SMTP_HOST="smtp.gmail.com"
   export SMTP_PORT="587"
   export ALERT_EMAIL_FROM="alerts@yourcompany.com"
   export CRITICAL_ALERT_EMAIL="team@yourcompany.com"
   ```

3. **Restart AlertManager**:
   ```bash
   docker-compose -f docker-compose.monitoring.yml restart alertmanager
   ```

## CI/CD Integration

### GitHub Actions Workflow

The performance testing workflow (`/.github/workflows/performance-testing.yml`) runs:

1. **Automatically**: After successful CI/CD deployment
2. **Manually**: Via workflow dispatch with custom parameters
3. **Scheduled**: Can be configured for regular performance audits

### Workflow Features

- **Parallel Execution**: k6 and Lighthouse tests run simultaneously
- **Multi-Environment Support**: Staging and production testing
- **Artifact Storage**: Results saved for 30 days
- **Slack Notifications**: Success/failure alerts
- **Performance Regression Detection**: Automatic failure on significant degradation

### Manual Trigger

```bash
# Via GitHub CLI
gh workflow run performance-testing.yml \
  --field environment=staging \
  --field load_profile=stress \
  --field run_k6=true \
  --field run_lighthouse=true
```

## Performance Budgets

### API Performance Budgets

| Endpoint Type | Target Response Time | Warning Threshold | Error Threshold |
|---------------|---------------------|-------------------|-----------------|
| Health Check  | 50ms               | 100ms             | 200ms           |
| Metadata      | 150ms              | 300ms             | 500ms           |
| Analysis      | 1000ms             | 2000ms            | 5000ms          |

### Frontend Performance Budgets

| Metric | Good | Needs Improvement | Poor |
|--------|------|-------------------|------|
| LCP    | ≤2.5s | ≤4.0s            | >4.0s |
| FID    | ≤100ms | ≤300ms          | >300ms |
| CLS    | ≤0.1  | ≤0.25            | >0.25 |

### Updating Budgets

1. **Modify Configuration**:
   - k6: `/performance/config/thresholds.js`
   - Lighthouse: `/performance/lighthouse/lighthouserc.json`
   - Monitoring: `/performance/config/performance-budgets.yaml`

2. **Test Locally**:
   ```bash
   ./performance/scripts/run-performance-tests.sh --env staging
   ```

3. **Commit Changes**: The new budgets take effect on the next workflow run

## Troubleshooting

### Common Issues

#### k6 Tests Failing

1. **Check API Availability**:
   ```bash
   curl -I https://staging-api.socialmapper.com/api/v1/health
   ```

2. **Verify Thresholds**:
   - Review `/performance/k6/config/thresholds.js`
   - Check if thresholds are too strict for current performance

3. **Inspect Test Results**:
   ```bash
   k6 run --out json=results.json performance/k6/tests/health-endpoints.js
   cat results.json | jq '.metrics'
   ```

#### Lighthouse CI Failing

1. **Check Build Process**:
   ```bash
   cd socialmapper-ui
   npm run build
   npm run preview
   ```

2. **Verify Budget Configuration**:
   - Review `/performance/lighthouse/budget.json`
   - Check if budgets are realistic for current build size

3. **Debug Performance Issues**:
   ```bash
   npx lighthouse http://localhost:3000 --view
   ```

#### Monitoring Stack Issues

1. **Check Container Status**:
   ```bash
   docker-compose -f performance/monitoring/docker-compose.monitoring.yml ps
   ```

2. **View Logs**:
   ```bash
   docker-compose -f performance/monitoring/docker-compose.monitoring.yml logs prometheus
   docker-compose -f performance/monitoring/docker-compose.monitoring.yml logs grafana
   ```

3. **Verify Metrics**:
   - Access Prometheus at http://localhost:9090
   - Check targets status at http://localhost:9090/targets

### Performance Regression Analysis

When performance degrades:

1. **Compare with Baseline**:
   - Check Grafana dashboards for trends
   - Compare current metrics with previous successful runs

2. **Identify Root Cause**:
   - API response time increases → Check backend changes
   - Frontend performance drops → Analyze bundle size changes
   - Infrastructure issues → Review system metrics

3. **Take Action**:
   - Optimize code based on findings
   - Adjust performance budgets if needed
   - Scale infrastructure if necessary

## Best Practices

### Test Design

1. **Realistic Load Patterns**:
   - Use representative user workflows
   - Include proper think time between requests
   - Test different user personas and usage patterns

2. **Comprehensive Coverage**:
   - Test all critical user journeys
   - Include edge cases and error conditions
   - Validate both happy path and failure scenarios

3. **Environment Consistency**:
   - Use production-like test environments
   - Maintain consistent test data
   - Control external dependencies

### Performance Optimization

1. **Set Realistic Budgets**:
   - Base budgets on user expectations
   - Consider device and network constraints
   - Update budgets as application evolves

2. **Continuous Monitoring**:
   - Monitor trends, not just point-in-time metrics
   - Set up proactive alerts
   - Regular performance audits

3. **Performance Culture**:
   - Include performance in code reviews
   - Make performance visible to all team members
   - Celebrate performance improvements

### Maintenance

1. **Regular Updates**:
   - Keep k6 and Lighthouse CI updated
   - Review and adjust thresholds quarterly
   - Update test scenarios as application evolves

2. **Documentation**:
   - Document performance requirements
   - Maintain runbooks for performance issues
   - Share knowledge across team members

3. **Automation**:
   - Automate as much testing as possible
   - Use CI/CD for consistent testing
   - Implement automated performance regression detection

---

For additional support or questions about performance testing, please refer to the project's main documentation or contact the development team.