# Production Deployment Checklist

Complete pre-deployment checklist for SocialMapper to ensure a smooth, secure, and reliable production deployment.

## Table of Contents

- [Pre-Deployment](#pre-deployment)
- [Security Hardening](#security-hardening)
- [Performance Optimization](#performance-optimization)
- [Monitoring Setup](#monitoring-setup)
- [Deployment Validation](#deployment-validation)
- [Post-Deployment](#post-deployment)
- [Incident Response](#incident-response)

---

## Pre-Deployment

### Environment Setup

- [ ] **Python version verified**
  - Python 3.11, 3.12, or 3.13 installed
  - Correct version available in PATH
  - Virtual environment activated

- [ ] **Dependencies installed**
  - All required packages from pyproject.toml installed
  - No conflicting package versions
  - Development dependencies excluded in production

- [ ] **Environment variables configured**
  - `CENSUS_API_KEY` set and valid
  - Optional variables configured (`MAPBOX_ACCESS_TOKEN`, etc.)
  - No hardcoded secrets in code
  - `.env` file excluded from version control

- [ ] **API keys validated**
  - Census API key tested and working
  - Rate limits understood and documented
  - Key rotation schedule established
  - Keys stored in secret management system

### Code Quality

- [ ] **Tests passing**
  ```bash
  pytest tests/ -v
  ```
  - All unit tests passing
  - Integration tests passing
  - No skipped critical tests

- [ ] **Code linted**
  ```bash
  ruff check .
  ruff format --check .
  ```
  - No linting errors
  - Code follows style guidelines
  - NumPy-style docstrings complete

- [ ] **Type checking passed**
  - No type errors
  - Type hints complete for public API

- [ ] **Dependencies audited**
  ```bash
  pip list --outdated
  pip-audit  # If available
  ```
  - No known security vulnerabilities
  - Dependencies up to date
  - License compliance verified

### Infrastructure

- [ ] **Deployment target prepared**
  - Server/container provisioned
  - Required resources allocated (CPU, memory, disk)
  - Network connectivity verified
  - Firewall rules configured

- [ ] **Cache directory configured**
  - Directory created and writable
  - Appropriate permissions set (755 for directory)
  - Sufficient disk space allocated (5-10GB recommended)
  - Backup/cleanup strategy defined

- [ ] **Database/storage ready** (if applicable)
  - Connection tested
  - Schema migrations applied
  - Backup strategy in place

---

## Security Hardening

### Secrets Management

- [ ] **API keys secured**
  - Stored in secret management service (AWS Secrets Manager, etc.)
  - Not present in code or version control
  - Access restricted to necessary services only
  - Audit logging enabled for secret access

- [ ] **Environment isolation**
  - Production secrets separate from development/staging
  - Secrets rotated regularly (90-day schedule recommended)
  - Emergency key rotation procedure documented

- [ ] **Access control configured**
  - Principle of least privilege applied
  - Role-based access control (RBAC) implemented
  - Service accounts used for automated processes
  - Multi-factor authentication enabled where possible

### Network Security

- [ ] **HTTPS/TLS enabled**
  - Valid SSL/TLS certificate installed
  - Strong cipher suites configured
  - Certificate auto-renewal configured
  - HTTP redirects to HTTPS

- [ ] **Firewall configured**
  - Only necessary ports open (e.g., 443 for HTTPS)
  - Source IP restrictions applied where possible
  - DDoS protection enabled
  - Intrusion detection configured

- [ ] **API rate limiting**
  - Rate limits configured to prevent abuse
  - Different limits for authenticated vs. unauthenticated requests
  - Rate limit exceeded responses documented
  - Rate limit monitoring in place

### Application Security

- [ ] **Input validation enabled**
  - All user inputs validated
  - Coordinate ranges validated
  - SQL injection prevention (parameterized queries)
  - XSS prevention for any web interfaces

- [ ] **Error handling secured**
  - Stack traces not exposed to users in production
  - Generic error messages for users
  - Detailed errors logged securely
  - Error tracking service configured (e.g., Sentry)

- [ ] **Dependencies scanned**
  - No known vulnerabilities (use `pip-audit` or Snyk)
  - Automated security scanning in CI/CD
  - Dependency update process defined

---

## Performance Optimization

### Configuration

- [ ] **Performance preset selected**
  ```python
  from socialmapper.performance import get_performance_config

  # Choose appropriate preset
  config = get_performance_config(preset='balanced')  # or 'fast', 'memory_efficient'
  ```
  - Preset matches infrastructure capacity
  - Custom overrides applied if needed
  - Configuration documented

- [ ] **Caching optimized**
  - Cache size appropriate for workload
  - Cache TTL configured (7 days default)
  - Cache eviction strategy defined
  - Cache hit rate monitored

- [ ] **Connection pooling configured**
  - Pool size matches expected concurrency
  - Connection timeouts set appropriately
  - Pool exhaustion handling configured
  - Connection reuse verified

### Resource Limits

- [ ] **Memory limits set**
  - Container/process memory limit configured
  - OOM killer behavior understood
  - Memory monitoring enabled
  - Memory leak detection in place

- [ ] **CPU limits set**
  - CPU limits appropriate for workload
  - CPU throttling monitored
  - Auto-scaling configured (if applicable)

- [ ] **Disk I/O optimized**
  - Fast storage used for cache (SSD recommended)
  - Disk space monitoring enabled
  - I/O throttling considered
  - Cache cleanup scheduled

### Load Testing

- [ ] **Load tests performed**
  - Expected peak load simulated
  - Response time acceptable under load
  - Resource usage measured
  - Bottlenecks identified and addressed

- [ ] **Stress tests performed**
  - Behavior under extreme load verified
  - Graceful degradation confirmed
  - Recovery from overload tested
  - Circuit breakers configured

---

## Monitoring Setup

### Health Checks

- [ ] **Health check endpoint implemented**
  ```python
  @app.route('/health')
  def health_check():
      return {'status': 'healthy', 'version': socialmapper.__version__}, 200
  ```
  - Returns 200 OK when healthy
  - Includes version information
  - Fast response time (<100ms)

- [ ] **Readiness check implemented**
  ```python
  @app.route('/ready')
  def readiness_check():
      # Check dependencies
      checks = {
          'census_api': check_census_api(),
          'cache': check_cache_writable()
      }
      all_ready = all(checks.values())
      return {'ready': all_ready, 'checks': checks}, 200 if all_ready else 503
  ```
  - Validates external dependencies
  - Returns 503 when not ready
  - Used by load balancers/orchestrators

### Logging

- [ ] **Structured logging configured**
  ```python
  import logging
  logging.basicConfig(
      level=logging.INFO,
      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  )
  ```
  - JSON format for easy parsing
  - Appropriate log levels used
  - Sensitive data redacted
  - Log rotation configured

- [ ] **Log aggregation enabled**
  - Logs shipped to centralized system (ELK, CloudWatch, etc.)
  - Log retention policy defined
  - Log search capability available
  - Alerts configured for errors

### Metrics

- [ ] **Performance metrics tracked**
  - Request count
  - Response time (p50, p95, p99)
  - Error rate
  - Cache hit rate
  - API call rate

- [ ] **Resource metrics tracked**
  - CPU usage
  - Memory usage
  - Disk I/O
  - Network I/O
  - Cache size

- [ ] **Business metrics tracked**
  - Isochrones generated
  - Census queries performed
  - Maps created
  - Geographic coverage

### Alerting

- [ ] **Critical alerts configured**
  - Service down
  - High error rate (>5%)
  - High response time (>5s)
  - Resource exhaustion (CPU/memory >90%)
  - API rate limit exceeded

- [ ] **Warning alerts configured**
  - Moderate error rate (>1%)
  - Elevated response time (>2s)
  - Resource usage high (>75%)
  - Cache hit rate low (<60%)

- [ ] **Alert routing configured**
  - On-call rotation defined
  - Escalation path documented
  - Alert fatigue prevention (deduplication, throttling)
  - Notification channels tested (PagerDuty, Slack, email)

---

## Deployment Validation

### Pre-Deployment Tests

- [ ] **Staging deployment successful**
  - Deployed to staging environment
  - All tests passed in staging
  - Performance acceptable in staging
  - Configuration matches production

- [ ] **Smoke tests defined**
  ```python
  def smoke_test():
      # Test core functionality
      iso = create_isochrone((45.5152, -122.6784), travel_time=15)
      assert iso['properties']['travel_time'] == 15

      blocks = get_census_blocks(polygon=iso)
      assert len(blocks) > 0

      census_data = get_census_data([blocks[0]['geoid']], ['population'])
      assert census_data.data
  ```
  - Core functions tested
  - Data retrieval verified
  - Response format validated

- [ ] **Rollback plan prepared**
  - Previous version tagged and accessible
  - Rollback procedure documented and tested
  - Database migration rollback (if applicable)
  - DNS/load balancer rollback ready

### Deployment Process

- [ ] **Deployment checklist followed**
  - Deployment window scheduled
  - Stakeholders notified
  - Change management approval obtained
  - Deployment steps documented

- [ ] **Blue-green/canary strategy** (if applicable)
  - Traffic gradually shifted to new version
  - Metrics monitored during rollout
  - Automatic rollback configured
  - Full rollout only after validation

- [ ] **Post-deployment smoke tests run**
  - All critical paths tested
  - Health checks passing
  - No increase in error rates
  - Response times within SLA

---

## Post-Deployment

### Validation

- [ ] **Functionality verified**
  - Core features working as expected
  - No regression in existing functionality
  - New features operational
  - Edge cases tested

- [ ] **Performance verified**
  - Response times within acceptable range
  - Cache hit rate normal
  - Resource usage stable
  - No memory leaks detected

- [ ] **Monitoring verified**
  - Metrics flowing to monitoring system
  - Alerts triggering appropriately
  - Dashboards updating
  - Logs being captured

### Documentation

- [ ] **Deployment documented**
  - Deployment date/time recorded
  - Version number documented
  - Configuration changes noted
  - Issues encountered and resolutions documented

- [ ] **Runbooks updated**
  - Operational procedures current
  - Troubleshooting guides updated
  - Contact information current
  - Architecture diagrams updated

- [ ] **User documentation updated**
  - API changes documented
  - Breaking changes highlighted
  - Migration guide provided (if applicable)
  - Examples updated

### Communication

- [ ] **Stakeholders notified**
  - Deployment completion communicated
  - Known issues disclosed
  - Monitoring links shared
  - Support contacts provided

- [ ] **Team briefed**
  - On-call team aware of changes
  - Known issues and workarounds communicated
  - Escalation path confirmed
  - Post-mortem scheduled (if issues occurred)

---

## Incident Response

### Preparation

- [ ] **Incident response plan documented**
  - Clear incident severity levels defined
  - Response procedures for each severity
  - Communication templates prepared
  - Post-mortem process defined

- [ ] **On-call rotation established**
  - Primary and secondary on-call assigned
  - Coverage for all timezones/hours
  - Handoff procedure defined
  - Backup contacts available

- [ ] **Troubleshooting resources prepared**
  - Common issues and solutions documented
  - Debug mode instructions available
  - Log access procedures documented
  - Escalation contacts listed

### Response Procedures

**Severity 1 - Critical (Service Down)**

1. [ ] Alert acknowledged within 5 minutes
2. [ ] Incident channel created (#incident-YYYY-MM-DD)
3. [ ] Incident commander assigned
4. [ ] Status page updated
5. [ ] Stakeholders notified
6. [ ] Diagnosis started
7. [ ] Mitigation/rollback initiated
8. [ ] Resolution confirmed
9. [ ] Post-mortem scheduled within 24 hours

**Severity 2 - High (Degraded Service)**

1. [ ] Alert acknowledged within 15 minutes
2. [ ] Issue investigated
3. [ ] Stakeholders notified if customer-facing
4. [ ] Fix planned and implemented
5. [ ] Resolution verified
6. [ ] Post-mortem optional

**Severity 3 - Medium (Minor Issues)**

1. [ ] Issue logged
2. [ ] Investigation scheduled
3. [ ] Fix prioritized in backlog
4. [ ] Resolution tracked

### Recovery

- [ ] **Service restoration verified**
  - Health checks passing
  - Error rates normal
  - Performance restored
  - Functionality confirmed

- [ ] **Root cause identified**
  - Detailed investigation completed
  - Timeline of events documented
  - Contributing factors identified
  - Similar issues checked

- [ ] **Post-mortem completed**
  - Incident timeline documented
  - Root cause analysis performed
  - Action items identified
  - Prevention measures planned
  - Learnings shared with team

---

## Common Issues Checklist

### API Connectivity

- [ ] Census API key valid and not expired
- [ ] Network connectivity to Census API
- [ ] Firewall allows outbound HTTPS (port 443)
- [ ] Rate limits not exceeded
- [ ] DNS resolution working

### Performance Issues

- [ ] Cache directory writable and has space
- [ ] Memory limits appropriate
- [ ] CPU not throttled
- [ ] Network bandwidth sufficient
- [ ] Database connections available (if applicable)

### Data Issues

- [ ] Coordinates within valid ranges
- [ ] Census data available for requested year
- [ ] GEOIDs valid and current
- [ ] Network data cached for area
- [ ] OSM data available for region

---

## Automated Checks

Create a deployment validation script:

```bash
#!/bin/bash
# deployment-check.sh

echo "SocialMapper Deployment Validation"
echo "===================================="

# Check Python version
python --version | grep -q "3.11\|3.12\|3.13" && echo "✓ Python version OK" || echo "✗ Python version incorrect"

# Check SocialMapper installed
python -c "import socialmapper; print(f'✓ SocialMapper {socialmapper.__version__} installed')" || echo "✗ SocialMapper not installed"

# Check environment variables
[ -n "$CENSUS_API_KEY" ] && echo "✓ CENSUS_API_KEY set" || echo "✗ CENSUS_API_KEY not set"

# Check cache directory
[ -d "/app/cache" ] && [ -w "/app/cache" ] && echo "✓ Cache directory OK" || echo "✗ Cache directory issue"

# Run smoke test
python -c "
from socialmapper import create_isochrone, get_census_blocks, get_census_data
iso = create_isochrone((45.5152, -122.6784), travel_time=15)
assert iso['properties']['travel_time'] == 15
blocks = get_census_blocks(polygon=iso)
assert len(blocks) > 0
print('✓ Smoke test passed')
" || echo "✗ Smoke test failed"

# Check health endpoint (if applicable)
curl -f http://localhost:8000/health > /dev/null 2>&1 && echo "✓ Health check OK" || echo "✗ Health check failed"

echo "===================================="
echo "Validation complete"
```

Run before and after deployment:

```bash
chmod +x deployment-check.sh
./deployment-check.sh
```

---

## Sign-Off

### Pre-Deployment Sign-Off

- [ ] Technical lead approval: _______________ Date: ______
- [ ] Security review completed: _______________ Date: ______
- [ ] Performance testing approved: _______________ Date: ______

### Post-Deployment Sign-Off

- [ ] Deployment successful: _______________ Date: ______
- [ ] Validation tests passed: _______________ Date: ______
- [ ] Monitoring confirmed: _______________ Date: ______

---

## Resources

- [Deployment Guide](DEPLOYMENT.md) - Detailed deployment instructions
- [API Reference](api-reference.md) - Complete API documentation
- [Performance Guide](performance.md) - Performance optimization
- [Security Guide](security.md) - Security best practices

---

**Version**: 0.9.0
**Last Updated**: 2025-11-05

---

## Notes

Use this section to record deployment-specific notes, configurations, or decisions:

```
Deployment Date: _______________
Environment: _______________
Configuration: _______________
Special Considerations: _______________
```
